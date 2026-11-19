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
    match = re.search(r"found = re\.findall\(r'(.+?)', answer, re\.M\)", WORKFLOW)
    assert match, "VERDICT regex not found in skill-lint.yml"
    return re.compile(match[1], re.M)


class VerdictLine(unittest.TestCase):
    def last(self, answer):
        found = load_verdict_regex().findall(answer)
        return found[-1] if found else None

    def test_house_rules_620_answer_with_a_status_line_first(self):
        # house-rules#620 head 366433c: the answer opened with a status line, its VERDICT line came later.
        self.assertEqual(self.last("pstack-verifier: PASS @ head\n\nVERDICT: PASS+NOTES\n\nnotes"), "PASS+NOTES")

    def test_first_line_verdict_and_none(self):
        self.assertEqual(self.last("VERDICT: FAIL\nwhy"), "FAIL")
        self.assertIsNone(self.last("Looks good. PASS"))
        self.assertIsNone(self.last("VERDICT: PASSING"))


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
