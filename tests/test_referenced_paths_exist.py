"""A live tool must not point at a repo file that is gone.

PR 530 deleted skills/hypertask-triage/scripts while fleet/solo-wake, fleet/pick, vcc and
systemd units still loaded it, so every board wake loop died silently on 14 Nov 2026.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CALLERS = ["fleet", "systemd", "bin", "scripts"]
REF = re.compile(r"(?:house-rules/|HERE\.parent / \"|ROOT / \")((?:skills|fleet|scripts|systemd|bin)/[A-Za-z0-9_./-]+)")


def caller_files():
    for top in CALLERS:
        base = ROOT / top
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts and path.suffix not in {".md", ".txt", ".json"}:
                yield path


def missing_refs():
    missing = []
    for path in caller_files():
        try:
            text = path.read_text()
        except UnicodeDecodeError:
            continue
        for ref in REF.findall(text):
            ref = ref.rstrip("/.")
            if "{" in ref or "*" in ref:
                continue
            if not (ROOT / ref).exists():
                missing.append(f"{path.relative_to(ROOT)} -> {ref}")
    return sorted(set(missing))


class ReferencedPathsExist(unittest.TestCase):
    def test_every_referenced_repo_path_exists(self):
        self.assertEqual(missing_refs(), [], "restore the file or move its callers in the same change")


if __name__ == "__main__":
    unittest.main()
