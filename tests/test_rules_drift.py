import os
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "bin/rules-drift"


class RulesDriftTest(unittest.TestCase):
    def run_script(self, *args, env=None):
        merged = {**os.environ, **(env or {})}
        return subprocess.run(
            [os.environ.get("PYTHON", "python3"), str(SCRIPT), *args],
            cwd=REPO,
            env=merged,
            capture_output=True,
            text=True,
        )

    def test_self_check_passes(self):
        r = self.run_script("--self-check")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("self-check PASS", r.stdout)

    def test_house_rules_clean(self):
        r = self.run_script("--house-rules")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("clean", r.stdout)

    def test_house_rules_refuses_retired_pool_line(self):
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
            f.write("CI Boss runners ht-ci-runner-1 run codex only\n")
            path = f.name
        try:
            r = self.run_script("--house-rules", env={"HOUSE_RULES_MD": path})
            self.assertEqual(r.returncode, 1, r.stdout)
            self.assertIn("ht-ci-runner", r.stdout)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
