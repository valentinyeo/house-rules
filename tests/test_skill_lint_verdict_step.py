"""SOFT-2821: the skill-lint verdict step must not crash on an agent command with an unbalanced quote."""
import pathlib
import re
import shlex
import textwrap
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKFLOW = (ROOT / ".github/workflows/skill-lint.yml").read_text()


def load_normalize():
    match = re.search(r"^( *)def normalize\(command\):\n(?:\1 .*\n)+", WORKFLOW, re.M)
    assert match, "normalize() not found in skill-lint.yml"
    scope = {"shlex": shlex, "pathlib": pathlib}
    exec(textwrap.dedent(match[0]), scope)
    return scope["normalize"]


class VerdictStep(unittest.TestCase):
    def test_unbalanced_quote_does_not_crash(self):
        normalize = load_normalize()
        self.assertEqual(normalize("cat <<EOF\n# it's fine\nEOF"), ["cat <<EOF\n# it's fine\nEOF"])

    def test_plain_command_still_splits(self):
        self.assertEqual(load_normalize()("python3 -m unittest -v"), ["python3", "-m", "unittest", "-v"])


if __name__ == "__main__":
    unittest.main()
