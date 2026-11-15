"""Behaviour of ticket-board: each event's hypertask calls, recorded by a fake CLI."""

import json
import os
import stat
import subprocess
import sys
import textwrap
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BOARD = REPO / "bin" / "ticket-board"

FAKE = textwrap.dedent("""\
    #!/usr/bin/env python3
    import json, os, sys
    args = sys.argv[1:]
    if args[:1] == ["--token"] and len(args) >= 2:
        args = args[2:]
    open(os.environ["CALLS"], "a").write(json.dumps(args) + "\\n")
    if "context" in args:
        print(json.dumps({"connected_agent": {"id": "self-agent"}}))
    elif "get" in args:
        print(json.dumps({"tasks": [{"assignees": [
            {"type": "agent", "agentId": "other-agent"},
            {"type": "user", "id": 6},
            {"type": "agent", "agentId": "self-agent"},
        ]}]}))
    elif "view" in args and "list" in args:
        page = json.loads(os.environ.get("VIEWS", '{"views": [], "total": 0}'))
        print(json.dumps(page))
    else:
        print("{}")
    """)


class BoardTests(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = Path(tempfile.mkdtemp())
        self.calls = self.tmp / "calls"
        self.calls.write_text("")
        fake = self.tmp / "hypertask"
        fake.write_text(FAKE)
        fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
        self.env = {k: v for k, v in os.environ.items() if k != "HYPERTASK_TOKEN"}
        self.env["PATH"] = str(self.tmp) + os.pathsep + self.env.get("PATH", "")
        self.env["CALLS"] = str(self.calls)

    def run_board(self, *args, token=None, event_name=None, payload=None):
        env = dict(self.env)
        if token:
            env["HYPERTASK_TOKEN"] = token
        if payload is not None:
            path = self.tmp / "event.json"
            path.write_text(json.dumps(payload))
            env["GITHUB_EVENT_PATH"] = str(path)
            env["GITHUB_EVENT_NAME"] = event_name or ""
        done = subprocess.run(
            [sys.executable, str(BOARD), *args],
            capture_output=True, text=True, env=env,
        )
        lines = [json.loads(line) for line in self.calls.read_text().splitlines() if line]
        return done, lines

    def test_worker_start_moves_to_doing_and_keeps_one_agent(self):
        done, lines = self.run_board("apply", "--event", "start", "--ticket", "SOFT-1")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn(["--json", "task", "get", "SOFT-1"], lines)
        self.assertIn(["task", "update", "SOFT-1", "--section", "Doing"], lines)
        self.assertIn(["task", "unassign", "SOFT-1", "--agent", "other-agent"], lines)
        self.assertIn(["task", "assign", "SOFT-1", "--self"], lines)
        self.assertNotIn(["task", "unassign", "SOFT-1", "--agent", "self-agent"], lines)
        joined = json.dumps(lines)
        self.assertNotIn('"--assignee", 6', joined)
        self.assertNotIn("--clear-assignees", joined)

    def test_pull_request_open_moves_to_ai_review(self):
        payload = {"action": "opened", "pull_request": {
            "title": "SOFT-2446: board moves tickets itself",
            "head": {"ref": "soft-2446-board-moves"},
            "body": "",
            "merged": False,
        }}
        done, lines = self.run_board(
            "apply-github", token="test-token", event_name="pull_request", payload=payload,
        )
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(lines, [["task", "update", "SOFT-2446", "--section", "AI Review"]])

    def test_verifier_pass_moves_to_valentin_review(self):
        payload = {"action": "completed", "check_run": {
            "name": "pstack-verifier",
            "conclusion": "success",
            "pull_requests": [{"head": {"ref": "feat/soft-9-fix"}, "title": "unrelated"}],
        }}
        done, lines = self.run_board(
            "apply-github", token="test-token", event_name="check_run", payload=payload,
        )
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(lines, [["task", "update", "SOFT-9", "--section", "Valentin Review"]])

    def test_merge_moves_to_done(self):
        payload = {"action": "closed", "pull_request": {
            "title": "Ship it",
            "head": {"ref": "main"},
            "body": "Closes SOFT-3",
            "merged": True,
        }}
        done, lines = self.run_board(
            "apply-github", token="test-token", event_name="pull_request", payload=payload,
        )
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(lines, [["task", "update", "SOFT-3", "--section", "Done"]])

    def test_close_moves_to_todo_and_clears_assignees(self):
        payload = {"action": "closed", "pull_request": {
            "title": "SOFT-4: drop this",
            "head": {"ref": "soft-4-drop"},
            "body": "",
            "merged": False,
        }}
        done, lines = self.run_board(
            "apply-github", token="test-token", event_name="pull_request", payload=payload,
        )
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(
            lines,
            [["task", "update", "SOFT-4", "--section", "Todo", "--clear-assignees"]],
        )

    def test_missing_token_skips_without_calling_hypertask(self):
        payload = {"action": "opened", "pull_request": {
            "title": "SOFT-5", "head": {"ref": "x"}, "merged": False,
        }}
        done, lines = self.run_board(
            "apply-github", event_name="pull_request", payload=payload,
        )
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn("HYPERTASK_TOKEN is not set", done.stdout)
        self.assertEqual(lines, [])

    def test_failed_verifier_does_not_move(self):
        payload = {"check_run": {
            "name": "pstack-verifier",
            "conclusion": "failure",
            "pull_requests": [{"head": {"ref": "soft-8-fix"}}],
        }}
        done, lines = self.run_board(
            "apply-github", token="test-token", event_name="check_run", payload=payload,
        )
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(lines, [])

    def test_pass_comment_moves_to_valentin_review(self):
        payload = {"action": "created", "issue": {
            "title": "SOFT-7: thing", "pull_request": {"url": "https://example.test/1"},
        }, "comment": {"body": "PASS+NOTES\nlooks good"}}
        done, lines = self.run_board(
            "apply-github", token="test-token", event_name="issue_comment", payload=payload,
        )
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(lines, [["task", "update", "SOFT-7", "--section", "Valentin Review"]])

    def test_other_worker_start_claims_through_the_same_command(self):
        raw = json.dumps({"tool_name": "Bash", "tool_input": {
            "command": "cursor-agent -p -f --model grok-4.7 'SOFT-6: fix the gate'",
        }})
        env = dict(self.env)
        done = subprocess.run(
            [sys.executable, str(BOARD), "claim-command"],
            input=raw, capture_output=True, text=True, env=env,
        )
        lines = [json.loads(line) for line in self.calls.read_text().splitlines() if line]
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn(["task", "update", "SOFT-6", "--section", "Doing"], lines)
        self.assertIn(["task", "assign", "SOFT-6", "--self"], lines)

    def test_spawn_worker_command_is_not_claimed_twice(self):
        raw = json.dumps({"tool_name": "Bash", "tool_input": {
            "command": "spawn-worker --level normal --ticket SOFT-6 brief.md",
        }})
        done = subprocess.run(
            [sys.executable, str(BOARD), "claim-command"],
            input=raw, capture_output=True, text=True, env=self.env,
        )
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(self.calls.read_text(), "")

    def test_ensure_view_creates_poteto_once(self):
        self.env["VIEWS"] = json.dumps({"views": [{"title": "Multi Bot", "slug": "multi-bot"}], "total": 1})
        done, lines = self.run_board(
            "ensure-view", "--name", "poteto", "--agent", "2f26726a-ab85-4e39-954c-1f1634227bb6",
        )
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn([
            "view", "create", "--project", "2060", "--title", "poteto",
            "--visibility", "Public", "--assignee", "2f26726a-ab85-4e39-954c-1f1634227bb6",
        ], lines)

    def test_spawn_worker_claims_the_ticket_before_the_worker_starts(self):
        import importlib.machinery
        import importlib.util
        loader = importlib.machinery.SourceFileLoader(
            "spawn_worker_ticket", str(REPO / "bin" / "spawn-worker"))
        spec = importlib.util.spec_from_loader("spawn_worker_ticket", loader)
        sw = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sw)
        reader = self.tmp / "token-ladder"
        reader.write_text(
            "#!/usr/bin/env python3\nimport json; print(json.dumps("
            "{'deepseek': {'used_pct': 0, 'pace_ratio': 0, 'state': 'ON'}}))\n")
        reader.chmod(reader.stat().st_mode | stat.S_IEXEC)
        brief = self.tmp / "brief.md"
        brief.write_text("do the work")
        started = []

        def execvp(prog, argv):
            if "Doing" not in self.calls.read_text():
                raise AssertionError("worker started before the ticket moved")
            started.append(prog)

        sw.os.execvp = execvp
        sw.READER = str(reader)
        old_path = os.environ.get("PATH")
        old_reader = os.environ.get("TOKEN_LADDER")
        os.environ["PATH"] = self.env["PATH"]
        os.environ["CALLS"] = str(self.calls)
        os.environ["TOKEN_LADDER"] = str(reader)
        os.environ.pop("HYPERTASK_TOKEN", None)
        try:
            code = sw.main(["--level", "simple", "--ticket", "SOFT-1", str(brief)])
        finally:
            if old_path is None:
                os.environ.pop("PATH", None)
            else:
                os.environ["PATH"] = old_path
            if old_reader is None:
                os.environ.pop("TOKEN_LADDER", None)
            else:
                os.environ["TOKEN_LADDER"] = old_reader
        self.assertEqual(code, 0)
        self.assertTrue(started)
        lines = [json.loads(line) for line in self.calls.read_text().splitlines() if line]
        self.assertIn(["task", "update", "SOFT-1", "--section", "Doing"], lines)
        self.assertIn(["task", "assign", "SOFT-1", "--self"], lines)

    def test_ensure_view_refuses_other_boards(self):
        for board in ("15", "4060"):
            self.calls.write_text("")
            done, lines = self.run_board(
                "ensure-view", "--name", "poteto", "--agent", "agent-1", "--project", board,
            )
            self.assertEqual(done.returncode, 2, board)
            self.assertEqual(lines, [])


if __name__ == "__main__":
    unittest.main()
