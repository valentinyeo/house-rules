"""Every workflow that runs on pull_request, push or workflow_call must cancel its old runs.

Rule: old runs cancel when newer code arrives. A workflow needs a top-level
`concurrency:` block with `cancel-in-progress: true`.

  python3 tests/test_workflow_concurrency.py            run the tests
  python3 tests/test_workflow_concurrency.py --lint DIR print offenders in DIR/*.yml, exit 1 on any
"""
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
TRIGGERS = ("pull_request", "push", "workflow_call")

# Workflows exempt for now, each with the reason and the ticket that removes it.
ALLOWED_MISSING = {
    # SOFT-2691 / PR #603 rewrites this file; add the block there, then delete this entry.
    "fleet-reconcile-verifier.yml",
}


def triggers(text):
    """Trigger names in the top-level `on:` key (block, inline list or scalar form)."""
    found = set()
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = re.match(r"^on:\s*(.*)$", line)
        if not m:
            continue
        inline = re.sub(r"#.*", "", m.group(1)).strip()
        if inline:
            found.update(re.findall(r"[a-z_]+", inline))
            break
        for nxt in lines[i + 1:]:
            if nxt and not nxt[0].isspace() and not nxt.startswith("#"):
                break
            k = re.match(r"^  ([a-z_]+):", nxt)
            if k:
                found.add(k.group(1))
        break
    return found & set(TRIGGERS)


def cancels_old_runs(text):
    """True when the top-level `concurrency:` block sets cancel-in-progress: true."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if not re.match(r"^concurrency:", line):
            continue
        for nxt in lines[i + 1:]:
            if nxt and not nxt[0].isspace() and not nxt.startswith("#"):
                break
            if re.match(r"^\s+cancel-in-progress:\s*true\s*(#.*)?$", nxt):
                return True
    return False


def problems(directory):
    out = []
    for path in sorted(Path(directory).glob("*.yml")):
        text = path.read_text(encoding="utf-8")
        on = triggers(text)
        if on and not cancels_old_runs(text) and path.name not in ALLOWED_MISSING:
            out.append("%s: runs on %s but has no top-level concurrency with cancel-in-progress: true"
                       % (path.name, "/".join(sorted(on))))
    return out


WITH_BLOCK = """name: x
on:
  pull_request:
  push:
    branches: [main]
concurrency:
  group: x-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true
jobs:
  a:
    runs-on: ubuntu-latest
"""
WITHOUT_BLOCK = WITH_BLOCK.replace(
    "concurrency:\n  group: x-${{ github.event.pull_request.number || github.ref }}\n  cancel-in-progress: true\n", "")


class WorkflowConcurrencyTest(unittest.TestCase):
    def test_block_present_passes(self):
        self.assertTrue(cancels_old_runs(WITH_BLOCK))

    def test_block_missing_fails(self):
        self.assertFalse(cancels_old_runs(WITHOUT_BLOCK))

    def test_cancel_false_fails(self):
        self.assertFalse(cancels_old_runs(WITH_BLOCK.replace("cancel-in-progress: true", "cancel-in-progress: false")))

    def test_job_level_block_does_not_count(self):
        text = WITHOUT_BLOCK + "    concurrency:\n      group: g\n      cancel-in-progress: true\n"
        self.assertFalse(cancels_old_runs(text))

    def test_trigger_forms(self):
        self.assertEqual(triggers(WITH_BLOCK), {"pull_request", "push"})
        self.assertEqual(triggers("on: [push, pull_request]\njobs:\n"), {"push", "pull_request"})
        self.assertEqual(triggers("on: push\njobs:\n"), {"push"})
        self.assertEqual(triggers("on:\n  workflow_call:\n    inputs:\n      a:\n        type: string\njobs:\n"), {"workflow_call"})
        self.assertEqual(triggers("on:\n  schedule:\n    - cron: '0 * * * *'\njobs:\n"), set())

    def test_scheduled_only_workflow_is_not_checked(self):
        self.assertFalse(triggers("on:\n  schedule:\n    - cron: '0 * * * *'\njobs:\n"))

    def test_repo_workflows(self):
        self.assertEqual(problems(WORKFLOWS), [])

    def test_allow_list_entries_still_exist(self):
        for name in ALLOWED_MISSING:
            self.assertTrue((WORKFLOWS / name).is_file(), "%s gone: drop it from ALLOWED_MISSING" % name)


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--lint":
        bad = problems(sys.argv[2])
        print("\n".join(bad) or "workflow-concurrency ok")
        sys.exit(1 if bad else 0)
    unittest.main()
