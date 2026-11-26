"""The worker brief quotes pstack's owner steps, so the quote must still match pstack.

VSTA-209: code workers skipped the slop-strip, the no-comments pass and the rebase before
self-proof, because the brief never named them. A quote that drifts is worse than no quote,
so each blockquote in the owner-steps section must appear word for word in the installed
pstack playbook. No pstack cache on the machine means the check skips.
"""
import os
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
BRIEF = ROOT / "docs/worker-brief.md"
PLAYBOOK = "skills/poteto-mode/playbooks/autopilot-full.md"
CACHE = Path(os.environ.get("PSTACK_CACHE", "~/.claude/plugins/cache/cursor-plugins/pstack")).expanduser()


def newest_playbook():
    versions = [p for p in CACHE.glob("*/" + PLAYBOOK) if p.is_file()] if CACHE.is_dir() else []
    if not versions:
        return None
    return max(versions, key=lambda p: [int(n) for n in re.findall(r"\d+", str(p))[:3]])


def quoted_paragraphs(text):
    section = text.split("Owner steps:", 1)
    if len(section) < 2:
        return []
    paragraphs, current = [], []
    for line in section[1].splitlines():
        if line.startswith(">"):
            current.append(line.lstrip(">").strip())
        elif current:
            paragraphs.append(" ".join(current))
            current = []
    if current:
        paragraphs.append(" ".join(current))
    return paragraphs


class WorkerBriefOwnerSteps(unittest.TestCase):
    def test_each_quote_matches_the_installed_playbook(self):
        playbook = newest_playbook()
        if playbook is None:
            self.skipTest(f"no pstack playbook under {CACHE}")
        text = " ".join(playbook.read_text().split())
        quotes = quoted_paragraphs(BRIEF.read_text())
        self.assertTrue(quotes, "worker brief lost the owner-steps quotes")
        for quote in quotes:
            with self.subTest(quote=quote[:60]):
                self.assertIn(" ".join(quote.split()), text)

    def test_brief_names_the_owner_steps_and_the_deslop_gap(self):
        brief = BRIEF.read_text()
        self.assertIn("skills/no-comments/SKILL.md", brief)
        self.assertIn("note \"deslop unavailable\" in the PR body and your final line", brief)
        self.assertIn("A missing deslop never stops the run", brief)


if __name__ == "__main__":
    unittest.main()
