"""Every workflow that runs on code events must cancel its old runs.

Rule: old runs cancel when newer code arrives. A workflow needs a top-level
`concurrency:` block with a non-empty `group` that repeats across runs of the same
change, and `cancel-in-progress: true`.

The group may only use values that stay the same when new code arrives on the same
branch or PR (ALLOWED_GITHUB, `inputs.*`, `vars.*`). Anything else is rejected, so a
per-commit or per-run value (github.sha, github.run_id, github.event.after,
github.event.pull_request.head.sha, ...) fails even when it sits next to a ref.

  python3 tests/test_workflow_concurrency.py            run the tests
  python3 tests/test_workflow_concurrency.py --lint DIR print offenders in DIR/*.yml and *.yaml, exit 1 on any

Needs PyYAML (`python3 -m pip install pyyaml`); without it the script exits with an error.
"""
import re
import sys
import unittest
from pathlib import Path

try:
    import yaml
except ImportError:  # never skip the lint quietly: a missing parser must fail loudly
    sys.exit("workflow-concurrency needs PyYAML: run `python3 -m pip install pyyaml`")

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
# Every trigger that fires when code changes. schedule, workflow_dispatch and the
# issue/comment/release events do not run per commit, so they need no cancelling.
TRIGGERS = ("pull_request", "pull_request_target", "push", "merge_group", "workflow_call", "workflow_run")

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


# `github.*` values that are the same for every run of the same branch or PR.
ALLOWED_GITHUB = {
    "ref", "ref_name", "head_ref", "base_ref", "workflow", "repository", "event_name",
    "event.number", "event.pull_request.number",
    "event.pull_request.head.ref", "event.pull_request.base.ref",
    "event.workflow_run.head_branch", "event.merge_group.base_ref",
}
# A merge queue run gets its own ref (gh-readonly-queue/<branch>/pr-N-<sha>), so ref-like
# values never repeat there.
MERGE_QUEUE_UNSTABLE = {"ref", "ref_name", "head_ref"}
SAFE_FUNCTIONS = {"format", "contains", "startswith", "endswith", "join"}
KEYWORDS = {"true", "false", "null"}
TOKEN = re.compile(r"[a-z_][\w-]*(?:\s*\.\s*[\w*-]+)*(\s*\()?")


def unstable_parts(group, on=()):
    """Names in `group` that may differ between two runs of the same change (empty list = fine).

    Allow-list: only ALLOWED_GITHUB, `inputs.*`, `vars.*` and a few string functions pass. Anything
    else (github.sha, github.run_id, github.event.after, github.event.pull_request.head.sha,
    toJSON(...), a bare `github`, a computed `[...]` index, an unknown context) is returned.
    """
    allowed = set(ALLOWED_GITHUB)
    if "merge_group" in on:
        allowed -= MERGE_QUEUE_UNSTABLE
    if group.count("${{") != group.count("}}"):
        return ["unbalanced ${{ }}"]
    bad = []
    for expr in re.findall(r"\$\{\{(.*?)\}\}", group, re.S):
        expr = expr.lower()
        expr = re.sub(r"\[\s*'([^']*)'\s*\]", r".\1", expr)  # github['sha'] is github.sha
        expr = re.sub(r"'(?:[^']|'')*'", "''", expr)  # string literals are not names
        if "[" in expr:
            bad.append("computed index in " + expr.strip())
        for m in TOKEN.finditer(expr):
            name = re.sub(r"\s+", "", m.group(0).rstrip("( \t")).strip()
            parts = name.split(".")
            if m.group(1):  # function call
                if name not in SAFE_FUNCTIONS:
                    bad.append(name + "()")
            elif name in KEYWORDS:
                continue
            elif parts[0] == "github" and len(parts) > 1 and ".".join(parts[1:]) in allowed:
                continue
            elif parts[0] in ("inputs", "vars") and len(parts) > 1 and "*" not in name:
                continue
            else:
                bad.append(name)
    return sorted(set(bad))


def group_repeats(group, on=()):
    """True when `group` is a non-empty string that can match an older run of the same change."""
    if not isinstance(group, str) or not group.strip():
        return False
    return not unstable_parts(group, on)


def cancels_old_runs(data):
    """True when top-level `concurrency:` has a repeating group and cancel-in-progress is exactly true."""
    block = data.get("concurrency")
    return (isinstance(block, dict) and block.get("cancel-in-progress") is True
            and group_repeats(block.get("group"), triggers(data)))


def problems(directory):
    out = []
    if not Path(directory).is_dir():
        return ["%s: not a directory" % directory]
    paths = sorted(Path(directory).glob("*.y*ml"))
    if not paths:
        return ["%s: no workflow files found" % directory]
    for path in paths:
        try:
            data = load(path.read_text(encoding="utf-8"))
        except (yaml.YAMLError, ValueError) as err:
            out.append("%s: cannot parse workflow (%s)" % (path.name, str(err).splitlines()[0]))
            continue
        on = triggers(data)
        if on and not cancels_old_runs(data) and path.name not in ALLOWED_MISSING:
            block = data.get("concurrency")
            group = block.get("group") if isinstance(block, dict) else None
            why = unstable_parts(group, on) if isinstance(group, str) else []
            out.append("%s: runs on %s but has no top-level concurrency with a repeating group and cancel-in-progress: true%s"
                       % (path.name, "/".join(sorted(on)),
                          " (group uses per-run or per-commit values: %s)" % ", ".join(why) if why else ""))
    return out


def stale_exemptions(directory, allowed=None):
    """Allow-list entries to drop: the file is gone or already cancels old runs."""
    out = []
    for name in sorted(ALLOWED_MISSING if allowed is None else allowed):
        path = Path(directory) / name
        if not path.is_file():
            out.append("%s: file is gone; drop it from ALLOWED_MISSING" % name)
        elif cancels_old_runs(load(path.read_text(encoding="utf-8"))):
            out.append("%s: already cancels old runs; drop it from ALLOWED_MISSING" % name)
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

    def test_group_must_be_present_and_non_empty(self):
        no_group = WITH_BLOCK.replace("  group: x-${{ github.event.pull_request.number || github.ref }}\n", "")
        self.assertFalse(self.ok(no_group))
        for value in ("''", "'  '", "~", "[a]"):
            self.assertFalse(self.ok(WITH_BLOCK.replace("x-${{ github.event.pull_request.number || github.ref }}", value)), value)

    OLD = "x-${{ github.event.pull_request.number || github.ref }}"

    def group_ok(self, value, on=None):
        text = WITH_BLOCK.replace(self.OLD, value)
        if on:
            text = text.replace("  pull_request:\n  push:\n    branches: [main]\n", on)
        return self.ok(text)

    def test_per_run_values_fail(self):
        for value in ("github.run_id", "github.run_number", "github.run_attempt"):
            self.assertFalse(self.group_ok("x-${{ %s }}" % value), value)
            self.assertFalse(self.group_ok("x-${{ github.ref }}-${{ %s }}" % value), value)

    def test_per_commit_values_fail_even_beside_a_ref(self):
        for value in ("github.sha", "github.workflow_sha", "github.event.after", "github.event.before",
                      "github.event.pull_request.head.sha", "github.event.pull_request.base.sha",
                      "github.event.pull_request.merge_commit_sha", "github.event.pull_request.updated_at",
                      "github.event.head_commit.id", "github.event.head_commit.timestamp",
                      "github.event.repository.pushed_at", "github.event.merge_group.head_sha",
                      "github.event.merge_group.base_sha", "github.event.workflow_run.head_sha",
                      "github.event.workflow_run.id", "github.event.workflow_run.run_attempt",
                      "github.event.workflow_run.run_number", "github.event.check_suite.head_sha",
                      "github.event.commits", "github.event.pull_request", "github.event", "github",
                      "github.event.pull_request.head.repo.pushed_at"):
            self.assertFalse(self.group_ok("x-${{ %s }}" % value), value)
            self.assertFalse(self.group_ok("x-${{ github.ref }}-${{ %s }}" % value), value)
            self.assertFalse(self.group_ok("x-${{ github.event.pull_request.number || %s }}" % value), value)

    def test_per_commit_value_in_the_old_false_pass_cases_fails(self):
        for value in ("x-${{ github.sha }}-${{ github.ref }}", "${{ github.event.pull_request.head.sha }}",
                      "x-${{ github.head_ref || github.sha }}", "x-${{ github.sha }}-${{ inputs.pr-number }}"):
            self.assertFalse(self.group_ok(value), value)

    def test_hidden_spellings_of_a_per_commit_value_fail(self):
        for value in ("x-${{ github['sha'] }}", "x-${{ github['event']['after'] }}", "x-${{ GitHub.SHA }}",
                      "x-${{ github . sha }}", "x-${{ github.event.pull_request.head['sha'] }}",
                      "x-${{ github[inputs.key] }}", "x-${{ github.event.commits[0].id }}",
                      "x-${{ github.* }}", "x-${{ format('{0}', github.sha) }}",
                      "x-${{ toJSON(github.event) }}", "x-${{ toJSON(github.ref) }}", "x-${{ fromJSON('1') }}",
                      "x-${{ hashFiles('**') }}", "x-${{ runner.name }}", "x-${{ env.X }}", "x-${{ secrets.X }}",
                      "x-${{ steps.a.outputs.b }}", "x-${{ needs.a.result }}", "x-${{ matrix.a }}",
                      "x-${{ inputs }}", "x-${{ inputs.* }}", "x-${{ github.ref }}-${{ github.sha"):
            self.assertFalse(self.group_ok(value), value)

    def test_group_that_repeats_passes(self):
        for value in ("x", "x-${{ github.ref }}", "x-${{ github.ref_name }}",
                      "x-${{ github.head_ref || github.ref }}", "x-${{ github.event.pull_request.number }}",
                      "x-${{ github.event.number || github.ref }}", "x-${{ github.workflow }}-${{ github.ref }}",
                      "x-${{ github.event.pull_request.head.ref }}", "x-${{ inputs.pr-number }}-${{ inputs.mode }}",
                      "x-${{ vars.NAME }}", "x-${{ github.event_name == 'push' && github.ref || 'other' }}",
                      "x-${{ github['ref'] }}", "x-${{ format('{0}-{1}', github.workflow, github.ref) }}",
                      "x-${{ github.repository }}-${{ github.base_ref }}"):
            self.assertTrue(self.group_ok(value), value)

    def test_names_inside_string_literals_do_not_count(self):
        self.assertTrue(self.group_ok("x-${{ github.ref == 'github.sha' && github.ref || github.ref }}"))
        self.assertTrue(self.group_ok("literal github.sha text ${{ github.ref }}"))

    def test_merge_queue_runs_need_a_value_that_repeats_in_the_queue(self):
        merge = "  merge_group:\n"
        self.assertFalse(self.group_ok("x-${{ github.ref }}", merge))
        self.assertFalse(self.group_ok("x-${{ github.ref_name }}", merge))
        self.assertFalse(self.group_ok("x-${{ github.head_ref }}", merge))
        self.assertFalse(self.group_ok("x-${{ github.event.merge_group.head_sha }}", merge))
        self.assertTrue(self.group_ok("x-${{ github.event.merge_group.base_ref }}", merge))
        self.assertTrue(self.group_ok("x", merge))

    def test_every_code_trigger_needs_the_block(self):
        for trigger in TRIGGERS:
            text = "on:\n  %s:\njobs: {}\n" % trigger
            self.assertEqual(triggers(load(text)), {trigger}, trigger)
            self.assertFalse(cancels_old_runs(load(text)), trigger)
            self.assertTrue(cancels_old_runs(load(text + "concurrency: {group: g, cancel-in-progress: true}\n")), trigger)

    def test_triggers_that_are_not_per_commit_need_nothing(self):
        for trigger in ("schedule", "workflow_dispatch", "issues", "issue_comment", "release", "repository_dispatch"):
            self.assertEqual(triggers(load("on:\n  %s:\njobs: {}\n" % trigger)), set(), trigger)

    def test_pull_request_target_and_merge_group_without_block_are_reported(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "t.yml").write_text("on: pull_request_target\njobs: {}\n")
            (d / "m.yml").write_text("on:\n  merge_group:\njobs: {}\n")
            (d / "r.yml").write_text("on:\n  workflow_run:\n    workflows: [a]\njobs: {}\n")
            got = problems(d)
        self.assertEqual(len(got), 3, got)
        self.assertTrue(got[0].startswith("m.yml: runs on merge_group"))
        self.assertTrue(got[1].startswith("r.yml: runs on workflow_run"))
        self.assertTrue(got[2].startswith("t.yml: runs on pull_request_target"))

    def test_report_names_the_per_commit_value(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "w.yml").write_text("on: push\nconcurrency:\n  group: x-${{ github.sha }}-${{ github.ref }}\n"
                                     "  cancel-in-progress: true\njobs: {}\n")
            got = problems(d)
        self.assertEqual(len(got), 1, got)
        self.assertIn("github.sha", got[0])

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

    def test_missing_or_empty_directory_fails(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(len(problems(Path(d) / "nope")), 1)
            self.assertEqual(len(problems(d)), 1)
            (Path(d) / "notes.txt").write_text("x")
            self.assertEqual(len(problems(d)), 1)

    def test_repo_workflows(self):
        self.assertEqual(problems(WORKFLOWS), [])

    def test_allow_list_entries_are_not_stale(self):
        self.assertEqual(stale_exemptions(WORKFLOWS), [])

    def test_stale_exemptions_are_reported(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "fixed.yml").write_text(WITH_BLOCK)
            (d / "still-missing.yml").write_text(WITHOUT_BLOCK)
            got = stale_exemptions(d, {"fixed.yml", "still-missing.yml", "gone.yml"})
        self.assertEqual(len(got), 2, got)
        self.assertTrue(got[0].startswith("fixed.yml: already cancels"))
        self.assertTrue(got[1].startswith("gone.yml: file is gone"))


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--lint":
        bad = problems(sys.argv[2])
        print("\n".join(bad) or "workflow-concurrency ok")
        sys.exit(1 if bad else 0)
    unittest.main()
