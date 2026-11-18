import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/pick-verifier-model"


class PickVerifierModelTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.event = Path(self.temp.name) / "event.json"

    def run_picker(self, body, env=None, args=None):
        self.event.write_text(json.dumps({"pull_request": {"body": body}}))
        environment = {k: v for k, v in os.environ.items() if k != "GITHUB_EVENT_PATH"}
        environment.update(env or {"GITHUB_EVENT_PATH": str(self.event)})
        return subprocess.run([str(SCRIPT)] + (args or []), capture_output=True, text=True, env=environment)

    def test_self_test(self):
        result = self.run_picker("", args=["--self-test"])
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_non_deepseek_author_gets_deepseek(self):
        result = self.run_picker("## Why\nx\n\nAuthor model: anthropic/claude-sonnet\n")
        self.assertEqual((result.returncode, result.stdout), (0, "deepseek-v4.1-flash\n"))

    def test_deepseek_author_gets_glm(self):
        result = self.run_picker("Author model: deepseek/deepseek-v4.1-flash")
        self.assertEqual(result.stdout, "glm-5.3-flash\n")

    def test_every_author_counts(self):
        result = self.run_picker("Author model: deepseek/a\nAuthor model: openai/b\nAuthor model: glm/c")
        self.assertEqual(result.stdout, "kimi-k3\n")

    def test_missing_declaration_fails_with_message(self):
        for body in ("", None, "Author: me", "Author model: deepseek-v4.1-flash"):
            with self.subTest(body=body):
                result = self.run_picker(body)
                self.assertEqual(result.returncode, 1)
                self.assertEqual(result.stdout, "")
                self.assertIn("Author model: <family>/<model>", result.stderr)

    def test_all_verifier_families_authored_fails(self):
        result = self.run_picker("Author model: deepseek/a\nAuthor model: glm/b\nAuthor model: kimi/c")
        self.assertEqual(result.returncode, 1)
        self.assertIn("every verifier family", result.stderr)

    def test_missing_event_path_fails(self):
        result = self.run_picker("", env={"UNRELATED": "1"})
        self.assertEqual(result.returncode, 1)
        self.assertIn("GITHUB_EVENT_PATH", result.stderr)

    def test_event_without_pull_request_fails(self):
        self.event.write_text("{}")
        result = subprocess.run([str(SCRIPT), "--event", str(self.event)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)


if __name__ == "__main__":
    unittest.main()
