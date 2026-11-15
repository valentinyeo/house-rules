import os
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "bin/house-rules-sync"

GIT_ENV = {
    "GIT_AUTHOR_NAME": "Test",
    "GIT_AUTHOR_EMAIL": "test@example.com",
    "GIT_COMMITTER_NAME": "Test",
    "GIT_COMMITTER_EMAIL": "test@example.com",
}


def git(cwd, *args):
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        env={**os.environ, **GIT_ENV, "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null"},
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


class SyncTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.home = self.root / "home"
        self.home.mkdir()
        self.origin = self.root / "origin.git"
        self.writer = self.root / "writer"
        self.shared = self.root / "shared"
        self.orphans = self.root / "orphans"

        git(self.root, "init", "-q", "--bare", "-b", "main", str(self.origin))
        git(self.root, "init", "-q", "-b", "main", str(self.writer))
        (self.writer / "fleet").mkdir()
        (self.writer / "fleet/pick").write_text("original\n")
        (self.writer / "house-rules.md").write_text("rule one\n")
        git(self.writer, "add", "-A")
        git(self.writer, "commit", "-qm", "first")
        git(self.writer, "remote", "add", "origin", str(self.origin))
        git(self.writer, "push", "-q", "origin", "main")
        git(self.root, "clone", "-q", str(self.origin), str(self.shared))

    def tearDown(self):
        self.tmp.cleanup()

    def push_upstream(self, path, text, message="upstream"):
        (self.writer / path).write_text(text)
        git(self.writer, "add", "-A")
        git(self.writer, "commit", "-qm", message)
        git(self.writer, "push", "-q", "origin", "main")
        return git(self.writer, "rev-parse", "HEAD")

    def run_sync(self, **env):
        merged = {
            **os.environ,
            **GIT_ENV,
            "GIT_CONFIG_GLOBAL": "/dev/null",
            "GIT_CONFIG_SYSTEM": "/dev/null",
            "HOME": str(self.home),
            "HOUSE_RULES_DIR": str(self.shared),
            "HOUSE_RULES_ORPHANS": str(self.orphans),
            **env,
        }
        return subprocess.run(
            ["bash", str(SCRIPT)], env=merged, capture_output=True, text=True
        )

    def test_dirty_tracked_file_is_saved_and_pulled(self):
        head = self.push_upstream("fleet/pick", "upstream change\n")
        (self.shared / "fleet/pick").write_text("stray edit\n")

        r = self.run_sync()

        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(git(self.shared, "rev-parse", "HEAD"), head)
        self.assertEqual((self.shared / "fleet/pick").read_text(), "upstream change\n")
        patches = list(self.orphans.glob("*.patch"))
        self.assertEqual(len(patches), 1, r.stderr)
        self.assertIn("stray edit", patches[0].read_text())
        self.assertIn("rule one", (self.home / ".codex/AGENTS.md").read_text())

    def test_untracked_files_are_left_alone(self):
        head = self.push_upstream("house-rules.md", "rule two\n")
        (self.shared / "notes.txt").write_text("keep me\n")

        r = self.run_sync()

        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(git(self.shared, "rev-parse", "HEAD"), head)
        self.assertEqual((self.shared / "notes.txt").read_text(), "keep me\n")

    def test_failed_pull_exits_nonzero(self):
        git(self.shared, "remote", "set-url", "origin", str(self.root / "missing.git"))

        r = self.run_sync()

        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("pull from origin failed", r.stderr)
        self.assertFalse((self.home / ".codex/AGENTS.md").exists())

    def test_clean_tree_pulls_without_orphan_patch(self):
        head = self.push_upstream("house-rules.md", "rule three\n")

        r = self.run_sync()

        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(git(self.shared, "rev-parse", "HEAD"), head)
        self.assertFalse(self.orphans.exists())

    def test_main_failing_rules_lint_is_refused(self):
        lint = (REPO / "scripts/rules-lint").read_text()
        (self.writer / "scripts").mkdir()
        (self.writer / "scripts/rules-lint").write_text(lint)
        before = git(self.shared, "rev-parse", "HEAD")
        self.push_upstream("house-rules.md", "rule one\n- Never do X (2026-11-14, why: he said so).\n")

        r = self.run_sync()

        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("refused: origin/main fails rules-lint", r.stderr)
        self.assertEqual(git(self.shared, "rev-parse", "HEAD"), before)
        self.assertFalse((self.home / ".codex/AGENTS.md").exists())

        head = self.push_upstream("house-rules.md", "rule one\n- **Old:** Never do X.\n\n## Enforcement\n\n| Rule | Enforced by |\n| --- | --- |\n| Old | judgment |\n", "fix")
        r = self.run_sync()

        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(git(self.shared, "rev-parse", "HEAD"), head)


if __name__ == "__main__":
    unittest.main()
