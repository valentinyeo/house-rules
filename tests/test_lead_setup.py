import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "skills/board-identity/check.py"
spec = importlib.util.spec_from_file_location("lead_setup", SCRIPT)
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)


class LeadSetupTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.repo = self.home / "projects/hypertask"
        self.remote = self.home / "remote.git"
        self.git("init", "--bare", "--initial-branch=main", str(self.remote))
        self.git("clone", str(self.remote), str(self.repo))
        self.git("-C", str(self.repo), "config", "user.email", "test@example.invalid")
        self.git("-C", str(self.repo), "config", "user.name", "Test")
        self.commit("first")
        self.git("-C", str(self.repo), "push", "-u", "origin", "HEAD")
        self.token = self.home / ".config/hypertask-agents/credentials/sessions/ht-design-lead-agent-token"
        self.token.parent.mkdir(parents=True)
        self.token.write_text("private-fixture-token")
        self.token.chmod(0o600)
        self.context = {"connected_agent": {"displayName": "HT Design Lead"}, "projects": [{"id": 15}]}

    def git(self, *args):
        return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout.strip()

    def commit(self, text):
        (self.repo / "file").write_text(text)
        self.git("-C", str(self.repo), "add", "file")
        self.git("-C", str(self.repo), "commit", "-m", text)

    def advance_remote(self, text):
        writer = self.home / "writer"
        self.git("clone", str(self.remote), str(writer))
        self.git("-C", str(writer), "config", "user.email", "test@example.invalid")
        self.git("-C", str(writer), "config", "user.name", "Test")
        (writer / "file").write_text(text)
        self.git("-C", str(writer), "add", "file")
        self.git("-C", str(writer), "commit", "-m", text)
        self.git("-C", str(writer), "push")
        self.git("-C", str(self.repo), "fetch")

    def check(self, name="HT Design Lead", context=None):
        original = setup.run

        def command(*args, env=None):
            if args[0] == "hypertask":
                self.assertEqual(args, ("hypertask", "--json", "context"))
                self.assertEqual(env["HYPERTASKS_JWT_TOKEN"], "private-fixture-token")
                return json.dumps(self.context if context is None else context)
            return original(*args, env=env)

        output = io.StringIO()
        with patch.dict(os.environ, {"HOME": str(self.home), "SHIP_SESSION_NAME": name}), \
                patch.object(setup, "run", side_effect=command), contextlib.redirect_stdout(output):
            result = setup.main()
        self.assertNotIn("private-fixture-token", output.getvalue())
        return result, output.getvalue()

    def test_clean_lead_passes_without_modifying_checkout(self):
        before = self.git("-C", str(self.repo), "rev-parse", "HEAD")
        code, output = self.check()
        self.assertEqual(code, 0)
        self.assertIn("identity: PASS HT Design Lead; boards 15", output)
        self.assertIn("repo hypertask: PASS clean, fast-forwardable", output)
        self.assertIn("runners: PASS Hypertask fleet; HTPR 15", output)
        self.assertIn("setup: PASS", output)
        self.assertEqual(self.git("-C", str(self.repo), "rev-parse", "HEAD"), before)
        self.assertEqual(self.git("-C", str(self.repo), "status", "--porcelain"), "")

    def test_behind_is_fast_forwardable_without_pull(self):
        before = self.git("-C", str(self.repo), "rev-parse", "HEAD")
        self.advance_remote("remote next")
        self.assertEqual(self.check()[0], 0)
        self.assertEqual(self.git("-C", str(self.repo), "rev-parse", "HEAD"), before)

    def test_ahead_and_diverged_are_refused(self):
        self.commit("local next")
        self.assertEqual(self.check()[0], 1)
        self.advance_remote("different remote next")
        self.assertEqual(self.check()[0], 1)

    def test_tracked_and_untracked_changes_are_preserved_and_refused(self):
        (self.repo / "file").write_text("unsaved work")
        self.assertEqual(self.check()[0], 1)
        self.assertEqual((self.repo / "file").read_text(), "unsaved work")
        (self.repo / "file").write_text("first")
        (self.repo / "new-file").write_text("untracked work")
        self.assertEqual(self.check()[0], 1)
        self.assertEqual((self.repo / "new-file").read_text(), "untracked work")

    def test_missing_token_and_unsafe_permissions_are_refused(self):
        self.token.chmod(0o644)
        self.assertEqual(self.check()[0], 1)
        self.token.unlink()
        self.assertEqual(self.check()[0], 1)

    def test_wrong_identity_and_missing_board_are_refused(self):
        self.assertEqual(self.check(context={**self.context, "connected_agent": {"displayName": "Other Lead"}})[0], 1)
        code, output = self.check(context={**self.context, "projects": []})
        self.assertEqual(code, 1)
        self.assertIn("required boards missing: 15", output)

    def test_flat_link_to_role_token_is_supported(self):
        nested = self.token.parent / "design" / self.token.name
        nested.parent.mkdir()
        self.token.rename(nested)
        self.token.symlink_to(nested.relative_to(self.token.parent))
        self.assertEqual(self.check()[0], 0)

    def test_bad_context_is_redacted(self):
        with patch.object(setup, "run", return_value="private-fixture-token"):
            self.assertEqual(self.check()[0], 1)

    def test_unknown_session_never_reads_another_identity(self):
        with patch.object(setup, "check_identity", side_effect=AssertionError("must not read")):
            code, output = self.check(name="RUNNER 17")
        self.assertEqual(code, 1)
        self.assertIn("use the lead's own named session", output)

    def test_missing_checkout_is_refused(self):
        with patch.object(setup, "ROLES", {"HT Design Lead": ("ht-design-lead", {15}, ("absent",), "fleet")}):
            self.assertEqual(self.check()[0], 1)

    def test_context_failure_does_not_echo_credentials(self):
        with patch.object(setup, "check_identity", side_effect=subprocess.CalledProcessError(
                1, ["hypertask"], stderr="private-fixture-token")):
            self.assertEqual(self.check()[0], 1)

    def test_all_four_roles_have_correct_board_and_runner_paths(self):
        expected = {"HT Support Lead": ({10450, 15}, "HEFE 10450"),
                    "HT Design Lead": ({15}, "HTPR 15"),
                    "HT Growth Lead": ({2108, 15}, "MARK 2108"),
                    "HT Finance Lead": ({2462}, "No finance runners")}
        for name, (boards, route) in expected.items():
            slug, actual_boards, repos, runners = setup.ROLES[name]
            self.assertEqual(actual_boards, boards)
            token = self.token.with_name(f"{slug}-agent-token")
            token.write_text("private-fixture-token")
            token.chmod(0o600)
            for repo in repos:
                path = self.home / "projects" / repo
                if not path.exists():
                    self.git("clone", str(self.remote), str(path))
            code, output = self.check(name=name, context={"connected_agent": {"displayName": name},
                                                        "projects": [{"id": b} for b in boards]})
            self.assertEqual(code, 0, output)
            self.assertIn(route, output)
