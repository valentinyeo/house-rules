import importlib.machinery
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
TICKETS = ROOT / "skills/tickets"
LINT = TICKETS / "scripts/ticket-lint"
FIXTURES = json.loads((TICKETS / "writing-fixtures.json").read_text(encoding="utf-8"))["cases"]


def load_lint(path):
    loader = importlib.machinery.SourceFileLoader("writing_rules_test", str(path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


class WritingRulesTest(unittest.TestCase):
    def test_shared_fixtures_through_real_cli(self):
        for case in FIXTURES:
            with self.subTest(case=case["id"]), tempfile.TemporaryDirectory() as tmp:
                args = [sys.executable, str(LINT)]
                if case.get("shape"):
                    args.append("--shape")
                if "old" in case:
                    old = Path(tmp) / "old.txt"
                    old.write_text(case["old"], encoding="utf-8")
                    args.extend(["--old", str(old)])
                result = subprocess.run(args + ["-"], input=case["text"], text=True, capture_output=True)
                self.assertEqual(result.returncode, 0 if case["accepted"] else 1, result.stderr)
                if "refusal" in case:
                    self.assertIn(case["refusal"], result.stderr)

    def test_rule_list_is_authoritative(self):
        with tempfile.TemporaryDirectory() as tmp:
            tickets = Path(tmp) / "tickets"
            (tickets / "scripts").mkdir(parents=True)
            lint = tickets / "scripts/ticket-lint"
            shutil.copyfile(LINT, lint)
            rules = json.loads((TICKETS / "writing-rules.json").read_text(encoding="utf-8"))
            rules["maxWords"] = 2
            rules["technicalKinds"].append({"pattern": "forbidden-example", "flags": "", "name": "fixture rule"})
            (tickets / "writing-rules.json").write_text(json.dumps(rules), encoding="utf-8")
            module = load_lint(lint)
            self.assertTrue(any("max 2" in hit for hit in module.lint("Messages stay after reload.")))
            self.assertTrue(any("fixture rule" in hit for hit in module.lint("forbidden-example")))
            self.assertEqual(module.lint("Messages stay."), [])

    def test_auditor_uses_the_same_new_refusals(self):
        loader = importlib.machinery.SourceFileLoader(
            "ticket_check_test", str(ROOT / "skills/hypertask-triage/scripts/ticket-check"))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        audit = importlib.util.module_from_spec(spec)
        loader.exec_module(audit)
        self.assertIn("plain quote marks", audit.lint_text('Valentin said "Keep it simple."'))
        self.assertIn("code name", audit.lint_text("Use htpr-8255-kanban-cleanup."))
        self.assertEqual(audit.lint_text('<blockquote><p>Valentin said "Keep it simple."</p></blockquote>'), set())


if __name__ == "__main__":
    unittest.main()
