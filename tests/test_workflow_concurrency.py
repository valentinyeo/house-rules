"""Every workflow that runs on pull_request, push or workflow_call must cancel its old runs.

Rule: old runs cancel when newer code arrives. A workflow needs a top-level
`concurrency:` block with `cancel-in-progress: true`.

  python3 tests/test_workflow_concurrency.py            run the tests
  python3 tests/test_workflow_concurrency.py --lint DIR print offenders in DIR/*.yml and *.yaml, exit 1 on any

Needs PyYAML (`python3 -m pip install pyyaml`); without it the script exits with an error.
"""
import sys
import unittest
from pathlib import Path

try:
    import yaml
except ImportError:  # never skip the lint quietly: a missing parser must fail loudly
    sys.exit("workflow-concurrency needs PyYAML: run `python3 -m pip install pyyaml`")

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
TRIGGERS = ("pull_request", "push", "workflow_call")

# Workflows exempt for now, each with the reason and the ticket that removes it.
ALLOWED_MISSING = {
    # SOFT-2691 / PR #603 rewrites this file; add the block there, then delete this entry.
    "fleet-reconcile-verifier.yml",
}


def load(text):
    """Parse a workflow. A file that is not a YAML mapping is an error, never a pass."""
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError("workflow is not a YAML mapping")
    return data


def triggers(data):
    """Watched trigger names from the top-level `on:` key (string, list or mapping form).

    YAML 1.1 reads the bare key `on` as the boolean True, so look up both.
    """
    on = data[True] if True in data else data.get("on")
    if isinstance(on, str):
        names = {on}
    elif isinstance(on, (list, dict)):
        names = {str(n) for n in on}
    else:
        names = set()
    return names & set(TRIGGERS)


def cancels_old_runs(data):
    """True when the top-level `concurrency:` mapping sets cancel-in-progress to exactly true."""
    block = data.get("concurrency")
    return isinstance(block, dict) and block.get("cancel-in-progress") is True


def problems(directory):
    out = []
    paths = sorted(Path(directory).glob("*.y*ml"))
    for path in paths:
        try:
            data = load(path.read_text(encoding="utf-8"))
        except (yaml.YAMLError, ValueError) as err:
            out.append("%s: cannot parse workflow (%s)" % (path.name, str(err).splitlines()[0]))
            continue
        on = triggers(data)
        if on and not cancels_old_runs(data) and path.name not in ALLOWED_MISSING:
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
    def ok(self, text):
        return cancels_old_runs(load(text))

    def test_block_present_passes(self):
        self.assertTrue(self.ok(WITH_BLOCK))

    def test_block_missing_fails(self):
        self.assertFalse(self.ok(WITHOUT_BLOCK))

    def test_cancel_false_fails(self):
        self.assertFalse(self.ok(WITH_BLOCK.replace("cancel-in-progress: true", "cancel-in-progress: false")))

    def test_cancel_string_or_expression_fails(self):
        for value in ("'true'", "${{ github.ref != 'refs/heads/main' }}"):
            self.assertFalse(self.ok(WITH_BLOCK.replace("cancel-in-progress: true", "cancel-in-progress: " + value)))

    def test_job_level_block_does_not_count(self):
        text = WITHOUT_BLOCK + "    concurrency:\n      group: g\n      cancel-in-progress: true\n"
        self.assertFalse(self.ok(text))

    def test_inline_flow_mapping_passes(self):
        text = WITHOUT_BLOCK.replace("jobs:", "concurrency: {group: g, cancel-in-progress: true}\njobs:")
        self.assertTrue(self.ok(text))

    def test_four_space_indentation(self):
        four = WITH_BLOCK.replace("\n  ", "\n    ")
        self.assertEqual(triggers(load(four)), {"pull_request", "push"})
        self.assertTrue(self.ok(four))
        bad = WITHOUT_BLOCK.replace("\n  ", "\n    ")
        self.assertEqual(triggers(load(bad)), {"pull_request", "push"})
        self.assertFalse(self.ok(bad))

    def test_trigger_forms(self):
        self.assertEqual(triggers(load(WITH_BLOCK)), {"pull_request", "push"})
        self.assertEqual(triggers(load("on: [push, pull_request]\njobs: {}\n")), {"push", "pull_request"})
        self.assertEqual(triggers(load("on:\n  - pull_request\n  - schedule\njobs: {}\n")), {"pull_request"})
        self.assertEqual(triggers(load("on: push\njobs: {}\n")), {"push"})
        self.assertEqual(triggers(load("'on': push\njobs: {}\n")), {"push"})
        self.assertEqual(triggers(load("on:\n  workflow_call:\n    inputs:\n      a:\n        type: string\njobs: {}\n")), {"workflow_call"})
        self.assertEqual(triggers(load("on:\n  schedule:\n    - cron: '0 * * * *'\njobs: {}\n")), set())

    def test_scheduled_only_workflow_is_not_checked(self):
        self.assertFalse(triggers(load("on:\n  schedule:\n    - cron: '0 * * * *'\njobs: {}\n")))

    def test_problems_reads_yml_and_yaml_and_bad_files(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "a.yml").write_text("name: a\non:\n    pull_request:\njobs: {}\n")
            (d / "b.yaml").write_text("name: b\non: [push]\njobs: {}\n")
            (d / "c.yml").write_text("name: c\non: pull_request\nconcurrency: {group: c, cancel-in-progress: true}\njobs: {}\n")
            (d / "d.yml").write_text("on: [unclosed\n")
            got = problems(d)
        self.assertEqual(len(got), 3, got)
        self.assertTrue(got[0].startswith("a.yml: runs on pull_request"))
        self.assertTrue(got[1].startswith("b.yaml: runs on push"))
        self.assertTrue(got[2].startswith("d.yml: cannot parse workflow"))

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
