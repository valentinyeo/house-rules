import base64
import datetime as dt
import importlib.machinery
import importlib.util
import json
import os
import stat
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / "bin" / "ci-budget"
HOOK = ROOT / "hooks" / "ci-budget-session.py"
REPO = "acme/widgets"
BRANCH = "main"

FAKE_GH = textwrap.dedent("""\
    #!/usr/bin/env python3
    import json, os, sys
    fix = json.load(open(os.environ["CI_BUDGET_FIXTURE"]))
    if len(sys.argv) < 3 or sys.argv[1] != "api":
        sys.stderr.write("usage\\n")
        sys.exit(2)
    path = sys.argv[2]
    if path not in fix:
        sys.stderr.write("missing " + path + "\\n")
        sys.exit(1)
    body = fix[path]
    sys.stdout.write(body if isinstance(body, str) else json.dumps(body))
""")

CI_OK = textwrap.dedent("""\
    name: CI
    on:
      pull_request:
      push:
    concurrency:
      group: ci-${{ github.ref }}
      cancel-in-progress: true
""")

RELEASE_FAST = textwrap.dedent("""\
    name: auto-release
    on:
      push:
        branches: [main]
    concurrency:
      group: release-${{ github.ref }}
      cancel-in-progress: true
""")

RELEASE_OPEN = textwrap.dedent("""\
    name: auto-release
    on:
      push:
        branches: [main]
""")

LINT_EXPR = textwrap.dedent("""\
    name: Lint
    on:
      pull_request:
      push:
    concurrency:
      group: lint-${{ github.ref }}
      cancel-in-progress: ${{ github.event_name == 'pull_request' }}
""")

BUILD_FALSE = textwrap.dedent("""\
    name: Build
    on: push
    concurrency:
      group: build
      cancel-in-progress: false
""")


def b64(text):
    return {"encoding": "base64", "content": base64.b64encode(text.encode()).decode()}


def run_row(**kw):
    row = {
        "id": 1,
        "name": "CI",
        "path": ".github/workflows/ci.yml",
        "event": "pull_request",
        "status": "completed",
        "conclusion": "success",
        "head_branch": "feat",
        "head_sha": "abc",
        "created_at": "2026-11-15T12:00:00Z",
        "updated_at": "2026-11-15T12:10:00Z",
    }
    row.update(kw)
    return row


def release_row(start, minutes, run_id):
    began = dt.datetime.fromisoformat(f"2026-11-15T{start}:00+00:00")
    return {
        "id": run_id,
        "name": "auto-release",
        "path": ".github/workflows/auto-release.yml",
        "event": "push",
        "status": "completed",
        "conclusion": "success",
        "head_branch": BRANCH,
        "head_sha": f"sha{run_id}",
        "created_at": began.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "updated_at": (began + dt.timedelta(minutes=minutes)).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def checks(n, run_id=1):
    return [
        {
            "name": f"job-{i}",
            "conclusion": "success",
            "details_url": f"https://github.com/acme/widgets/actions/runs/{run_id}/job/{i}",
        }
        for i in range(n)
    ]


def fixture(workflows, releases, jobs, queued=(), in_progress=(), pending=()):
    pr = run_row()
    files = [
        {"name": path.rsplit("/", 1)[-1], "path": path, "type": "file"}
        for path in workflows
    ]
    data = {
        f"repos/{REPO}": {"default_branch": BRANCH},
        f"repos/{REPO}/actions/runs?per_page=20": {"workflow_runs": [pr]},
        f"repos/{REPO}/actions/runs?status=queued&per_page=100": {"workflow_runs": list(queued)},
        f"repos/{REPO}/actions/runs?status=in_progress&per_page=100": {"workflow_runs": list(in_progress)},
        f"repos/{REPO}/actions/runs?status=pending&per_page=100": {"workflow_runs": list(pending)},
        f"repos/{REPO}/contents/.github/workflows?ref={BRANCH}": files,
        f"repos/{REPO}/actions/runs/1/jobs?per_page=100&page=1": {
            "jobs": [{
                "name": "test",
                "conclusion": "success",
                "created_at": "2026-11-15T12:00:00Z",
                "started_at": "2026-11-15T12:02:00Z",
                "completed_at": "2026-11-15T12:05:00Z",
            }],
        },
        f"repos/{REPO}/actions/runs?event=pull_request&head_sha=abc&per_page=100&page=1": {
            "workflow_runs": [pr],
        },
        f"repos/{REPO}/commits/abc/check-runs?per_page=100&page=1": {"check_runs": checks(jobs)},
    }
    for path, text in workflows.items():
        data[f"repos/{REPO}/contents/{path}?ref={BRANCH}"] = b64(text)
        base = path.rsplit("/", 1)[-1]
        if base in ("auto-release.yml", "release.yml") or text.startswith("name: auto-release") or text.startswith("name: Release"):
            data[
                f"repos/{REPO}/actions/workflows/{base}/runs?branch={BRANCH}&event=push&per_page=20&status=success"
            ] = {"workflow_runs": releases}
    return data


def invoke(data, *args):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        fake = root / "gh"
        fake.write_text(FAKE_GH)
        fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
        fix = root / "fixture.json"
        fix.write_text(json.dumps(data))
        env = os.environ.copy()
        env["PATH"] = str(root) + os.pathsep + env.get("PATH", "")
        env["CI_BUDGET_FIXTURE"] = str(fix)
        env.pop("GH_TOKEN", None)
        env.pop("GITHUB_TOKEN", None)
        return subprocess.run(
            [str(BIN), *args], capture_output=True, text=True, env=env,
        )


def load_hook():
    loader = importlib.machinery.SourceFileLoader("ci_budget_session", str(HOOK))
    spec = importlib.util.spec_from_loader("ci_budget_session", loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


class BudgetTest(unittest.TestCase):
    def test_over_budget_exits_1_with_the_lines(self):
        data = fixture(
            {
                ".github/workflows/ci.yml": CI_OK,
                ".github/workflows/auto-release.yml": RELEASE_OPEN,
            },
            [release_row("10:00", 20, 100), release_row("11:00", 40, 101)],
            jobs=21,
            queued=[run_row(id=30, status="queued", conclusion=None, head_branch="feat",
                            created_at="2026-11-15T13:00:00Z", event="push")],
            in_progress=[run_row(id=20, status="in_progress", conclusion=None, head_branch="feat",
                                  created_at="2026-11-15T12:30:00Z", event="push")],
        )
        proc = invoke(data, REPO)
        self.assertEqual(proc.stderr, "")
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(proc.stdout.splitlines(), [
            "merge->release median 30.0 min > 15 (.github/workflows/auto-release.yml)",
            "merge->release p90 40.0 min > 15 (.github/workflows/auto-release.yml)",
            "PR check 21 jobs > 20 (.github/workflows/ci.yml)",
            "superseded run still running (.github/workflows/ci.yml)",
            "missing concurrency cancel-in-progress (.github/workflows/auto-release.yml)",
        ])

    def test_over_budget_json_includes_queue_wait(self):
        data = fixture(
            {
                ".github/workflows/ci.yml": CI_OK,
                ".github/workflows/auto-release.yml": RELEASE_OPEN,
            },
            [release_row("10:00", 20, 100), release_row("11:00", 40, 101)],
            jobs=21,
        )
        proc = invoke(data, REPO, "--json")
        self.assertEqual(proc.returncode, 1)
        report = json.loads(proc.stdout)
        self.assertFalse(report["ok"])
        self.assertEqual(report["queue_wait_minutes"], {"n": 1, "median": 2.0, "p90": 2.0})
        self.assertEqual(report["merge_to_release"][0]["median"], 30.0)
        self.assertEqual(report["pr_check_jobs"]["max"], 21)

    def test_in_budget_exits_0(self):
        data = fixture(
            {
                ".github/workflows/ci.yml": CI_OK,
                ".github/workflows/auto-release.yml": RELEASE_FAST,
            },
            [release_row("10:00", 14, 100), release_row("11:00", 15, 101)],
            jobs=20,
        )
        proc = invoke(data, REPO)
        self.assertEqual(proc.stderr, "")
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout, "")

    def test_missing_concurrency_is_flagged(self):
        data = fixture(
            {
                ".github/workflows/auto-release.yml": RELEASE_FAST,
                ".github/workflows/build.yml": BUILD_FALSE,
                ".github/workflows/ci.yml": "name: CI\non:\n  pull_request:\n",
                ".github/workflows/lint.yml": LINT_EXPR,
            },
            [release_row("10:00", 14, 100), release_row("11:00", 15, 101)],
            jobs=3,
        )
        proc = invoke(data, REPO)
        self.assertEqual(proc.stderr, "")
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(proc.stdout.splitlines(), [
            "missing concurrency cancel-in-progress (.github/workflows/build.yml)",
            "missing concurrency cancel-in-progress (.github/workflows/ci.yml)",
            "missing concurrency cancel-in-progress (.github/workflows/lint.yml)",
        ])


class SessionLineTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.count = self.root / "count"
        budget = self.root / "ci-budget"
        budget.write_text(textwrap.dedent(f"""\
            #!/usr/bin/env python3
            import pathlib, sys
            p = pathlib.Path({str(self.count)!r})
            n = int(p.read_text()) if p.exists() else 0
            p.write_text(str(n + 1))
            print("PR check 21 jobs > 20 (.github/workflows/ci.yml)")
            sys.exit(1)
        """))
        budget.chmod(budget.stat().st_mode | stat.S_IEXEC)
        os.environ["CI_BUDGET_BIN"] = str(budget)
        os.environ["CI_BUDGET_STATE"] = str(self.root / "state")
        self.mod = load_hook()

    def git_repo(self, origin):
        folder = self.root / "repo"
        folder.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=folder, check=True)
        subprocess.run(["git", "remote", "add", "origin", origin], cwd=folder, check=True)
        return folder

    def test_over_budget_line_is_cached_for_six_hours(self):
        folder = self.git_repo("git@github.com:valentinyeo/widgets.git")
        expected = (
            "CHECKS OVER BUDGET: PR check 21 jobs > 20 (.github/workflows/ci.yml). "
            "You own this repo's checks: fix them first (SOFT-2470)."
        )
        self.assertEqual(self.mod.budget_line(str(folder)), expected)
        self.assertEqual(self.mod.budget_line(str(folder)), expected)
        self.assertEqual(self.count.read_text(), "1")

    def test_expired_cache_runs_again(self):
        folder = self.git_repo("https://github.com/valentinyeo/widgets.git")
        cache = self.root / "state" / "valentinyeo__widgets"
        cache.parent.mkdir(parents=True)
        old = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=7)).isoformat()
        cache.write_text(json.dumps({"at": old, "code": 0, "stdout": ""}))
        self.assertIn("CHECKS OVER BUDGET:", self.mod.budget_line(str(folder)))
        self.assertEqual(self.count.read_text(), "1")

    def test_skips_out_of_bounds_and_other_owners(self):
        inne = self.git_repo("git@github.com:valentinyeo/inne.git")
        other = self.root / "other"
        other.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=other, check=True)
        subprocess.run(
            ["git", "remote", "add", "origin", "https://github.com/octocat/widgets.git"],
            cwd=other, check=True,
        )
        plain = self.root / "plain"
        plain.mkdir()
        self.assertEqual(self.mod.budget_line(str(inne)), "")
        self.assertEqual(self.mod.budget_line(str(other)), "")
        self.assertEqual(self.mod.budget_line(str(plain)), "")
        self.assertFalse(self.count.exists())

    def test_winner_is_not_out_of_bounds(self):
        folder = self.git_repo("https://github.com/valentinyeo/winner.git")
        self.assertIn("CHECKS OVER BUDGET:", self.mod.budget_line(str(folder)))
        self.assertEqual(self.count.read_text(), "1")


if __name__ == "__main__":
    unittest.main()
