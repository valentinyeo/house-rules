#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import tempfile
import unittest


spec = importlib.util.spec_from_file_location("inne_sync", Path(__file__).with_name("inne-sync.py"))
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)
ROOT = Path(__file__).resolve().parent.parent


class SyncTests(unittest.TestCase):
    def test_filter_real_rules(self):
        original = (ROOT / "house-rules.md").read_text()
        result = sync.filtered(original)
        self.assertNotIn("Path:", result)
        self.assertNotIn("hypertask-vps it already auto-loads", result)
        self.assertNotIn("run `/setup-runner` as a runner", result)
        self.assertNotIn("Board login only", result)
        between = result.split("## Between managers\n")[1].split("\n## ")[0]
        self.assertNotIn("Poteto", between)
        self.assertNotIn("/runner-update", between)
        for heading in ["Models and harnesses", "Talking to Valentin", "Valentin's alone", "Security", "Releases"]:
            section = original.split(f"## {heading}\n")[1].split("\n## ")[0]
            self.assertIn(section, result)
        self.assertIn("3. Install or verify caveman", result)

    def test_copy_atomic_idempotent_and_local_skill(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "export"
            sync.publish(ROOT, target)
            current = target / "current"
            first = current.resolve()
            self.assertEqual((current / "house-rules.md").read_text(), sync.filtered((ROOT / "house-rules.md").read_text()))
            skill = (current / "skills/house-rules/SKILL.md").read_text()
            self.assertIn("Read all of `~/.local/share/house-rules/house-rules.md`", skill)
            self.assertIn("Never run git pull", skill)
            self.assertNotIn("git -C", skill)
            sync.publish(ROOT, target)
            self.assertEqual(current.resolve(), first)
            self.assertEqual((current / "house-rules.md").stat().st_mode & 0o777, 0o644)
            self.assertEqual(current.resolve().stat().st_mode & 0o777, 0o755)

    def test_secrets_leave_previous_copy_untouched(self):
        secrets = [
            "gh" + "p_" + "aB3" * 14,
            "github_" + "pat_" + "aB3" * 20,
            "sk" + "-proj-" + "aB3" * 20,
            "sk" + "_live_" + "aB3" * 12,
            "AK" + "IA" + "A1" * 8,
            "xox" + "b-" + "1234567890-abcdefghij",
            "-----BEGIN " + "OPENSSH PRIVATE KEY-----",
            "api_key=" + "aB3" * 14,
            "123456789:" + "AA" + "aB3" * 12,
        ]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            (source / "skills/house-rules").mkdir(parents=True)
            skill = source / "skills/house-rules/SKILL.md"
            skill.write_text("safe skill\n")
            rules = source / "house-rules.md"
            rules.write_text("# House rules\nSafe rules\n")
            target = root / "export"
            sync.publish(source, target)
            original = (target / "current").resolve()
            for secret in secrets:
                for path in [rules, skill]:
                    rules.write_text("# House rules\nSafe rules\n")
                    skill.write_text("safe skill\n")
                    path.write_text(path.read_text() + secret)
                    with self.subTest(path=path.name, kind=secrets.index(secret)):
                        with self.assertRaisesRegex(ValueError, "Secret pattern detected"):
                            sync.publish(source, target)
                        self.assertEqual((target / "current").resolve(), original)
                        self.assertEqual((target / "current/house-rules.md").read_text(), "# House rules\nSafe rules\n")


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(SyncTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    print("INNE_TESTS_OK")
