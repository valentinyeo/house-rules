import importlib.util
import json
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RUN = REPO / "scripts/verifier/run.py"
WORKFLOW = REPO / ".github/workflows/pstack-verifier.yml"
SHA = "a" * 40
OTHER = "b" * 40


def load():
    spec = importlib.util.spec_from_file_location("pstack_verifier_run", RUN)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


V = load()


def ground(exits=None, bins=None):
    exits = exits or [0, 0, 0, 0]
    return {
        "commands": [
            {"cmd": cmd, "exit": code, "summary": "ok"}
            for cmd, code in zip(V.REQUIRED_COMMANDS, exits)
        ],
        "bin_scripts": bins or [],
    }


def answer(commands=None, bins=None, rules=None, mismatch="", notes=None):
    return {
        "commands": commands if commands is not None else [
            {"cmd": cmd, "exit": 0, "summary": "ok"} for cmd in V.REQUIRED_COMMANDS
        ],
        "bin_scripts": bins if bins is not None else [],
        "rules": rules if rules is not None else [],
        "goal_mismatch": mismatch,
        "notes": notes if notes is not None else [],
    }


class VerifierContractTest(unittest.TestCase):
    def test_pi_command_is_the_owner_command(self):
        self.assertEqual(
            V.pi_command("BRIEF"),
            [
                "npx", "-y", "@earendil-works/pi-coding-agent@1.5.2",
                "-p",
                "--provider", "opencode-go",
                "--model", "deepseek-v4.1-flash",
                "--thinking", "medium",
                "BRIEF",
            ],
        )

    def test_login_variable_is_opencode_api_key(self):
        self.assertEqual(V.LOGIN_VAR, "OPENCODE_API_KEY")

    def test_first_line(self):
        self.assertEqual(V.first_line("PASS", SHA), "pstack-verifier: PASS @ %s" % SHA)
        self.assertEqual(V.first_line("PASS+NOTES", SHA), "pstack-verifier: PASS+NOTES @ %s" % SHA)
        self.assertEqual(V.first_line("FAIL", SHA), "pstack-verifier: FAIL @ %s" % SHA)
        with self.assertRaises(V.VerifierError):
            V.first_line("OK", SHA)
        with self.assertRaises(V.VerifierError):
            V.first_line("PASS", "abc")

    def test_claude_trailer_is_not_same_family(self):
        message = "Add a verifier\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n"
        body = "\n".join([
            "## Why",
            "",
            "Every pull request needs a verifier. DeepSeek Flash does the run through Pi.",
            "A pull request whose commit trailer or body names DeepSeek or Pi as its author fails closed.",
            "",
        ])
        self.assertFalse(V.same_family([message], body))

    def test_deepseek_trailer_is_same_family(self):
        message = "Change\n\nCo-Authored-By: DeepSeek <deepseek@example.com>\n"
        self.assertTrue(V.same_family([message], "## Why\n\nA claude change.\n"))

    def test_pi_trailer_is_same_family(self):
        message = "Change\n\nCo-Authored-By: Pi Coding Agent <pi@example.com>\n"
        self.assertTrue(V.same_family([message], ""))

    def test_author_model_deepseek_is_same_family(self):
        self.assertTrue(V.same_family([], "author-model: deepseek\n"))
        self.assertFalse(V.same_family([], "author-model: claude\n"))

    def test_body_wrote_phrase_is_same_family(self):
        self.assertTrue(V.body_says_same_family("This change was written by DeepSeek.\n"))
        self.assertTrue(V.body_says_same_family("Pi authored the patch.\n"))
        self.assertFalse(V.body_says_same_family("The verifier runs DeepSeek Flash through Pi.\n"))

    def test_clean_answer_passes(self):
        verdict, reason, _notes, rules = V.combine(ground(), answer(), False, [])
        self.assertEqual(verdict, "PASS")
        self.assertEqual(reason, "")
        self.assertEqual(rules, [])

    def test_bootstrap_is_pass_notes(self):
        verdict, _reason, _notes, _rules = V.combine(ground(), answer(), True, [])
        self.assertEqual(verdict, "PASS+NOTES")

    def test_failed_command_fails_even_if_the_model_says_zero(self):
        verdict, reason, _notes, _rules = V.combine(ground([0, 0, 1, 0]), answer(), False, [])
        self.assertEqual(verdict, "FAIL")
        self.assertIn("command failed", reason)

    def test_omitted_command_fails(self):
        reported = [{"cmd": cmd, "exit": 0, "summary": "ok"} for cmd in V.REQUIRED_COMMANDS[:-1]]
        verdict, reason, _notes, _rules = V.combine(ground(), answer(commands=reported), False, [])
        self.assertEqual(verdict, "FAIL")
        self.assertIn("command not run", reason)

    def test_unexplained_rule_change_fails(self):
        rules = [{"quote": "every pr gets a verifier", "change": "meaning", "why_covers": False}]
        verdict, reason, _notes, _rules = V.combine(ground(), answer(rules=rules), False, [])
        self.assertEqual(verdict, "FAIL")
        self.assertIn("house rule", reason)

    def test_explained_rule_change_is_notes(self):
        rules = [{"quote": "every pr gets a verifier", "change": "meaning", "why_covers": True}]
        verdict, _reason, _notes, kept = V.combine(ground(), answer(rules=rules), False, [])
        self.assertEqual(verdict, "PASS+NOTES")
        self.assertEqual(kept, ["every pr gets a verifier"])

    def test_goal_mismatch_fails(self):
        verdict, reason, _notes, _rules = V.combine(ground(), answer(mismatch="the diff adds a runner"), False, [])
        self.assertEqual(verdict, "FAIL")
        self.assertIn("stated goal", reason)

    def test_notes_are_pass_notes(self):
        verdict, _reason, notes, _rules = V.combine(ground(), answer(notes=["look at the table"]), False, [])
        self.assertEqual(verdict, "PASS+NOTES")
        self.assertIn("look at the table", notes)

    def test_bad_json_fails_closed(self):
        with self.assertRaises(V.VerifierError):
            V.extract_json("no verdict here")
        found = V.extract_json('prose\n```json\n{"commands": [], "rules": []}\n```\n')
        self.assertEqual(found["commands"], [])

    def test_secret_is_redacted(self):
        self.assertNotIn("sk-live", V.redact("token sk-live-secret", "sk-live-secret"))
        text = V.comment_text("FAIL", SHA, "missing login", [])
        self.assertTrue(text.startswith("pstack-verifier: FAIL @ %s\n" % SHA))
        self.assertNotIn("sk-", text)

    def test_one_comment_per_sha(self):
        comments = [
            {"id": 1, "body": "pstack-verifier: FAIL @ %s\n\nold\n" % OTHER},
            {"id": 2, "body": "pstack-verifier: PASS @ %s\n\nkept\n" % SHA},
        ]
        self.assertEqual(V.comment_id_for_sha(comments, SHA), 2)
        self.assertIsNone(V.comment_id_for_sha(comments, "c" * 40))

    def test_same_family_comment_says_same_family(self):
        text = V.comment_text("FAIL", SHA, "same family", [])
        self.assertTrue(text.startswith("pstack-verifier: FAIL @ %s\n" % SHA))
        self.assertIn("same family", text.splitlines())

    def test_refuses_to_run_off_github(self):
        self.assertFalse(V.require_actions({}))
        self.assertTrue(V.require_actions({"GITHUB_ACTIONS": "true"}))

    def test_workflow_contract(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("pull_request:", text)
        self.assertNotIn("pull_request_target", text)
        self.assertNotIn("self-hosted", text)
        self.assertIn("contents: read", text)
        self.assertIn("pull-requests: write", text)
        self.assertIn("checks: write", text)
        self.assertIn("runs-on: ubuntu-latest", text)
        self.assertIn("name: pstack-verifier", text)
        self.assertIn("OPENCODE_API_KEY", text)
        self.assertIn('python3 "$VERIFIER_DIR/run.py"', text)
        self.assertNotIn("opencode-ai", text)
        self.assertNotIn("api.deepseek.com", text)
        self.assertIn("scripts/verifier", text)

    def test_brief_placeholders_render(self):
        template = (REPO / "scripts/verifier/brief.md").read_text(encoding="utf-8")
        rendered = V.render_brief(template, {
            "HEAD_DIR": "/tmp/head",
            "HEAD_SHA": SHA,
            "WHY_FILE": "/tmp/why",
            "DIFF_FILE": "/tmp/diff",
            "COMMANDS": "\n".join(V.REQUIRED_COMMANDS),
            "BIN_COMMANDS": "(none)",
        })
        self.assertNotIn("{{", rendered)
        self.assertIn("python3 scripts/rules-lint --self-test", rendered)
        self.assertIn(SHA, rendered)

    def test_bin_plan_picks_self_test(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script = root / "bin"
            script.mkdir()
            target = script / "demo"
            target.write_text("#!/bin/sh\n# --self-test\n", encoding="utf-8")
            planned, notes = V.bin_plan(root, ["bin/demo"])
            self.assertEqual(planned[0]["cmd"], "bin/demo --self-test")
            self.assertEqual(notes, [])
            with self.assertRaises(V.VerifierError):
                V.bin_plan(root, ["bin/has space"])


if __name__ == "__main__":
    unittest.main()
