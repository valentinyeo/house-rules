"""The skill-lint verdict step's command matcher (SOFT-2821, SOFT-2802).

Commands below are copied from real verifier traces: vstack PR 134, job 135616572179 (head 8507974), where the
verifier ran both required commands with output plumbing and the old exact matcher forced FAIL.
"""
import os
import pathlib
import re
import shlex
import tempfile
import textwrap
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKFLOW = (ROOT / ".github/workflows/skill-lint.yml").read_text()

REQUIRED_TESTS = "python3 -m unittest discover -s ../lint-source/tests -p test_skill_lint.py -v"
REQUIRED_LINT = ("python3 ../lint-source/scripts/skill-lint --base 4b50954e945c73241e337da7877e34fbbc4874fb "
                 "--pstack ../pstack-source/pstack/skills --house-rules ../catalog/house-rules.md --catalog ../catalog/skills")


def load_normalize():
    match = re.search(r"^( *)SEPARATORS = .*?(?=^\1missing = )", WORKFLOW, re.M | re.S)
    assert match, "matcher block not found in skill-lint.yml"
    scope = {"shlex": shlex, "pathlib": pathlib}
    exec(textwrap.dedent(match[0]), scope)
    return scope["normalize"]


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


class Matcher(unittest.TestCase):
    def setUp(self):
        self.normalize = load_normalize()

    def same(self, required, actual):
        return self.normalize(required) == self.normalize(actual)

    def test_pr134_trace_commands_count(self):
        self.assertTrue(self.same(REQUIRED_TESTS, REQUIRED_TESTS + " 2>&1 | tail -30"))
        self.assertTrue(self.same(REQUIRED_LINT, REQUIRED_LINT + '; echo "exit=$?"'))

    def test_cd_into_this_dir_is_dropped(self):
        self.assertTrue(self.same(REQUIRED_TESTS, f"cd {os.getcwd()} && {REQUIRED_TESTS}"))

    def test_other_commands_do_not_count(self):
        self.assertFalse(self.same(REQUIRED_TESTS, REQUIRED_TESTS.replace("-v", "-q")))
        self.assertFalse(self.same(REQUIRED_TESTS, "echo " + REQUIRED_TESTS))
        self.assertFalse(self.same(REQUIRED_LINT, REQUIRED_LINT + " | sed s/FAIL/PASS/"))
        with tempfile.TemporaryDirectory() as other:
            self.assertFalse(self.same(REQUIRED_TESTS, f"cd {other} && {REQUIRED_TESTS}"))

    def test_unbalanced_quote_does_not_crash(self):
        for text in ("cat <<EOF\n# it's fine\nEOF", "echo it's"):
            self.assertIsInstance(self.normalize(text), list)
            self.assertFalse(self.same(REQUIRED_TESTS, text))

    def test_plain_command_still_splits(self):
        self.assertEqual(self.normalize("python3 -m unittest -v"), ["python3", "-m", "unittest", "-v"])


if __name__ == "__main__":
    unittest.main()
