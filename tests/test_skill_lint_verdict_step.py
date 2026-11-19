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
