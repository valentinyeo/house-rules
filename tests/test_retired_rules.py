"""This repo must not read as the live rule set.

SOFT-2819 retired house-rules.md into a pointer: Valentin's own lines live in vstack's
valentin-mode skill, the rest in pstack. An inner chat still described the old page as
current, and two copies of the same skill loaded from two repos. These checks keep the
retirement from silently reversing.
"""
import os
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SKILLS = REPO / "skills"
HOUSE_RULES = REPO / "house-rules.md"
MAX_POINTER_LINES = 12

# Phrases that present a file as the live rules instead of a pointer to where they went.
LIVE_RULES_PATTERNS = (
    r"wins over any other rules",
    r"house-rules\.md is the only place",
    r"read all of .*house-rules\.md",
    r"add (it|this|a rule) to house-rules\.md",
    r"the house rules are the",
)


def skill_names(root):
    return {p.name for p in root.iterdir() if p.is_dir()} if root.is_dir() else set()


def vstack_dir():
    raw = os.environ.get("VSTACK_DIR")
    path = Path(raw) if raw else REPO.parent / "vstack"
    return path if path.is_absolute() else Path.cwd() / path


class RetiredRulesTest(unittest.TestCase):
    def test_no_skill_lives_in_both_repos(self):
        vstack = vstack_dir()
        if not vstack.is_dir():
            self.skipTest(
                "no vstack checkout at %s: set VSTACK_DIR to the vstack repo (CI checks it out)" % vstack
            )
        both = sorted(skill_names(SKILLS) & skill_names(vstack / "skills"))
        self.assertEqual(both, [], "each skill has one home; vstack owns: %s" % ", ".join(both))

    def test_no_skill_presents_itself_as_the_live_rules(self):
        for path in sorted(SKILLS.glob("*/SKILL.md")):
            text = path.read_text()
            for pattern in LIVE_RULES_PATTERNS:
                self.assertIsNone(
                    re.search(pattern, text, re.I),
                    "%s: this repo is not the live rules; point at valentin-mode in vstack (%s)"
                    % (path.relative_to(REPO), pattern),
                )

    def test_house_rules_stays_a_pointer(self):
        lines = [line for line in HOUSE_RULES.read_text().splitlines() if line.strip()]
        self.assertLessEqual(
            len(lines), MAX_POINTER_LINES,
            "house-rules.md must stay a pointer to valentin-mode in vstack, not the rules",
        )


if __name__ == "__main__":
    unittest.main()
