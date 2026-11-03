import datetime as dt
import importlib.machinery
import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "skills/shipping-update/scripts/ci-wait"
loader = importlib.machinery.SourceFileLoader("ci_wait", str(SCRIPT))
spec = importlib.util.spec_from_loader("ci_wait", loader)
ciw = importlib.util.module_from_spec(spec)
loader.exec_module(ciw)

NOW = dt.datetime(2026, 11, 3, 12, 0, tzinfo=dt.timezone.utc)


def run(name, start, minutes, sha="abc1234", conclusion="success", attempt=1, status="completed", id=0):
    began = dt.datetime.fromisoformat(f"2026-11-03T{start}:00+00:00")
    return {
        "id": id, "name": name, "head_sha": sha, "head_branch": "production", "event": "push",
        "status": status, "conclusion": conclusion, "run_attempt": attempt,
        "created_at": began.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "updated_at": (began + dt.timedelta(minutes=minutes)).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def measure(runs, **kw):
    with patch.object(ciw, "runs_between", lambda *a: runs), \
         patch.object(ciw, "first_attempt", lambda repo, r: r):
        return ciw.measure("owner/repo", 2, 10, NOW, **kw)


class RestartTest(unittest.TestCase):
    def test_restart_is_its_own_wait(self):
        result = measure([run("CI Tests", "09:00", 8), run("Feature Flag Gate", "09:30", 5)])
        waits = [(s["wait_min"], s["restart"], s["runs"]) for s in result["samples"]]
        self.assertEqual(waits, [(8.0, False, ["CI Tests"]), (5.0, True, ["Feature Flag Gate"])])
        self.assertEqual(result["week"]["median"], 6.5)

    def test_runs_of_one_push_stay_one_wait(self):
        result = measure([run("CI Tests", "09:00", 8), run("Bugfix regression report", "09:02", 1)])
        self.assertEqual(len(result["samples"]), 1)
        self.assertEqual(result["samples"][0]["wait_min"], 8.0)

    def test_a_late_restart_never_stretches_the_first_wait(self):
        result = measure([
            run("PR Guards", "09:00", 1),
            run("Feature Flag Gate", "09:59", 1),
            run("Feature Flag Gate", "10:58", 1),
        ])
        self.assertEqual([s["wait_min"] for s in result["samples"]], [1.0, 1.0, 1.0])


class WatcherTest(unittest.TestCase):
    def test_after_release_health_watcher_is_left_out(self):
        result = measure([run("CI Tests", "09:00", 8), run("Prod Health Check + Auto-Rollback", "09:00", 27)])
        self.assertEqual(len(result["samples"]), 1)
        self.assertEqual(result["samples"][0]["wait_min"], 8.0)
        self.assertEqual(result["samples"][0]["runs"], ["CI Tests"])

    def test_health_watcher_alone_is_no_check_wait(self):
        result = measure([run("Prod Health Check + Auto-Rollback", "09:00", 25)])
        self.assertEqual(result["week"]["n"], 0)
        self.assertEqual(result["skipped"], 0)

    def test_cancelled_health_watcher_does_not_supersede_the_change(self):
        result = measure([run("CI Tests", "09:00", 8),
                          run("Prod Health Check + Auto-Rollback", "09:20", 2, conclusion="cancelled")])
        self.assertEqual(result["week"]["n"], 1)
        self.assertEqual(result["skipped"], 0)

    def test_extra_watchers_come_from_the_command_line(self):
        runs = [run("CI Tests", "09:00", 8), run("Live watch", "09:00", 30)]
        self.assertEqual(measure(runs, skip=("Live watch",))["samples"][0]["wait_min"], 8.0)


class RealCheckTest(unittest.TestCase):
    def test_slow_check_is_kept(self):
        result = measure([run("CI Tests", "09:00", 24), run("PR Guards", "09:00", 1)])
        self.assertEqual(result["samples"][0]["wait_min"], 24.0)
        self.assertEqual(result["week"]["within"], 0)

    def test_a_second_real_check_after_the_first_still_counts(self):
        result = measure([run("CI Tests", "09:00", 8), run("visual @ production", "09:04", 9)])
        self.assertEqual(result["samples"][0]["wait_min"], 13.0)
        self.assertEqual(result["samples"][0]["runs"], ["CI Tests", "visual @ production"])

    def test_skipped_run_does_not_stretch_the_wait(self):
        result = measure([run("CI Tests", "09:00", 8), run("UX Signoff Gate", "09:40", 0, conclusion="skipped")])
        self.assertEqual(result["samples"][0]["wait_min"], 8.0)

    def test_a_wait_where_everything_was_skipped_is_no_wait(self):
        result = measure([run("CI Tests", "09:00", 8), run("Feature Flag Gate", "09:30", 0, conclusion="skipped")])
        self.assertEqual([s["wait_min"] for s in result["samples"]], [8.0])
        self.assertEqual(result["week"]["n"], 1)

    def test_cancelled_push_is_superseded(self):
        result = measure([run("CI Tests", "09:00", 8), run("PR Guards", "09:00", 1, conclusion="cancelled")])
        self.assertEqual(result["samples"], [])
        self.assertEqual(result["skipped"], 1)

    def test_first_try_is_used_for_a_rerun(self):
        first = dict(run("CI Tests", "09:00", 6), id=1)
        second = dict(run("CI Tests", "09:00", 8, attempt=2), id=1)
        with patch.object(ciw, "runs_between", lambda *a: [second]), \
             patch.object(ciw, "first_attempt", lambda repo, r: first):
            result = ciw.measure("owner/repo", 2, 10, NOW)
        self.assertEqual(result["samples"][0]["wait_min"], 6.0)
        self.assertEqual(result["reran"], 1)


if __name__ == "__main__":
    unittest.main()
