"""The skill-lint verdict step (SOFT-2821, SOFT-2802).

Commands below are copied from real verifier traces: vstack PR 134, job 135616572179 (head 8507974), where the
verifier ran both required commands with output plumbing and the old exact matcher forced FAIL.
"""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKFLOW = (ROOT / ".github/workflows/skill-lint.yml").read_text()

REQUIRED_TESTS = "python3 -m unittest discover -s ../lint-source/tests -p test_skill_lint.py -v"
REQUIRED_LINT = ("python3 ../lint-source/scripts/skill-lint --base 4b50954e945c73241e337da7877e34fbbc4874fb "
                 "--pstack ../pstack-source/pstack/skills --house-rules ../catalog/house-rules.md --catalog ../catalog/skills")


def load_verdict_regex():
    match = re.search(r"match = re\.search\(r'(.+?)', answer\)", WORKFLOW)
    assert match, "VERDICT regex not found in skill-lint.yml"
    return re.compile(match[1])


class VerdictLine(unittest.TestCase):
    """SOFT-2802: the verdict is the first line of the answer, as the brief asks. Quoted or fenced
    verdict lines further down never count, so they can neither flip a FAIL nor fake a PASS."""

    def first(self, answer):
        found = load_verdict_regex().search(answer)
        return found[1] if found else None

    def test_first_line_only(self):
        self.assertEqual(self.first("VERDICT: PASS+NOTES\n\nnotes"), "PASS+NOTES")
        self.assertEqual(self.first("VERDICT: FAIL\nquoted:\nVERDICT: PASS"), "FAIL")
        self.assertEqual(self.first("VERDICT: PASS\nquoted:\nVERDICT: FAIL"), "PASS")
        self.assertIsNone(self.first("status line\nVERDICT: PASS"))
        self.assertIsNone(self.first("format:\n```\nVERDICT: PASS\n```"))
        self.assertIsNone(self.first("VERDICT: PASSING"))

    def test_run_verifier_uses_the_same_rule(self):
        flag = re.search(r"--verdict-pattern '(.+?)'", WORKFLOW)[1]
        self.assertEqual(flag, load_verdict_regex().pattern)
        for answer in ("VERDICT: PASS", "\nVERDICT: PASS", "  VERDICT: PASS", "status\nVERDICT: PASS", "```\nVERDICT: PASS\n```"):
            self.assertEqual(bool(re.search(flag, answer)), self.first(answer) is not None, answer)


class RequiredCommands(unittest.TestCase):
    """The workflow runs both required commands as its own CI steps, so a verifier's shell wrappers
    (`| tail`, `; echo`, `|| true`) can neither hide a failure nor force a false FAIL (SOFT-2802)."""

    def test_both_required_commands_run_as_ci_steps(self):
        self.assertIn("python3 -m unittest discover -s lint-source/tests -p test_skill_lint.py -v", WORKFLOW)
        self.assertIn('bash "$RUNNER_TEMP/skill-lint-command"', WORKFLOW)

    def test_verdict_does_not_depend_on_the_verifier_trace(self):
        self.assertNotIn("missing", WORKFLOW.split("Post current-head verdict")[1].split("upload-artifact")[0])

if __name__ == "__main__":
    unittest.main()
