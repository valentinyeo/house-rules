"""Routing and fixture-backed CLI tests for bin/spawn-worker."""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "bin/spawn-worker"
NOW = 1_800_000_000


def load():
    spec = importlib.util.spec_from_loader(
        "spawn_worker", importlib.machinery.SourceFileLoader("spawn_worker", str(SCRIPT)))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


sw = load()


def pool(used=None, hours=None, state="ON", pace=None):
    return {"used_pct": used, "resets_at": NOW + hours * 3600 if hours is not None else None,
            "hours_left": hours, "pace_ratio": pace, "state": state}


UNKNOWN = pool(state="unknown")
EXAMPLE = {"claude": pool(85, 48), "codex": pool(100, 20, "OFF"), "grok": UNKNOWN}


class RoutingTests(unittest.TestCase):
    def setUp(self):
        self.clock = patch("time.time", return_value=NOW)
        self.clock.start()
        self.addCleanup(self.clock.stop)

    def test_off_family_is_refused_for_auto(self):
        p = {"deepseek": UNKNOWN, "grok": pool(10, 48),
             "codex": pool(100, 12, "OFF"), "claude": pool(85, 48)}
        self.assertEqual(sw.choose(p, "normal")[0], "grok")

    def test_off_pin_names_reason_and_alternative(self):
        p = {"grok": pool(10, 48), "codex": pool(99, 12, "OFF")}
        with self.assertRaisesRegex(sw.Refused, "OFF.*best allowed alternative: grok"):
            sw.choose(p, "normal", "codex")

    def test_claude_spare_room_beats_unknown_grok(self):
        p = {"grok": UNKNOWN, "claude": pool(3, 48)}
        self.assertEqual(sw.choose(p, "normal")[0], "claude")
        self.assertTrue(sw.claude_allowed(p))

    def test_claude_at_85_percent_is_refused(self):
        for hours in (48, 12):
            with self.subTest(hours=hours):
                p = {"grok": UNKNOWN, "claude": pool(85, hours)}
                self.assertFalse(sw.claude_allowed(p))
                with self.assertRaisesRegex(sw.Refused, "85% used.*orchestrators"):
                    sw.choose(p, "normal", "claude")
                self.assertEqual(sw.choose(p, "normal")[0], "grok")

    def test_claude_at_50_percent_12_hours_before_reset_is_allowed(self):
        p = {"grok": UNKNOWN, "claude": pool(50, 12)}
        self.assertTrue(sw.claude_allowed(p))
        self.assertEqual(sw.choose(p, "normal")[0], "claude")

    def test_claude_reserve_tracks_elapsed_week(self):
        p = {"claude": pool(40, 120)}
        self.assertFalse(sw.claude_allowed(p))
        with self.assertRaisesRegex(sw.Refused, "orchestrators"):
            sw.choose(p, "normal", "claude")
        p["claude"] = pool(40, 48)
        self.assertTrue(sw.claude_allowed(p))

    def test_claude_reserve_boundary_is_strict(self):
        self.assertTrue(sw.claude_allowed({"claude": pool(39.9, 84)}))
        self.assertFalse(sw.claude_allowed({"claude": pool(40, 84)}))
        self.assertFalse(sw.claude_allowed({"claude": pool(0, 168)}))

    def test_claude_last_day_exception_and_boundaries(self):
        self.assertTrue(sw.claude_allowed({"claude": pool(69.9, 23.9)}))
        self.assertTrue(sw.claude_allowed({"claude": pool(70, 23.9)}))
        self.assertFalse(sw.claude_allowed({"claude": pool(76, 24)}))

    def test_claude_unknown_usage_is_refused(self):
        for reading in (UNKNOWN, pool(3), pool(None, 48)):
            with self.subTest(reading=reading):
                p = {"claude": reading}
                self.assertFalse(sw.claude_allowed(p))
                with self.assertRaisesRegex(sw.Refused, "usage unknown"):
                    sw.choose(p, "normal", "claude")

    def test_invalid_numbers_cannot_prove_claude_room(self):
        for field, value in (("used_pct", "bad"), ("used_pct", -1), ("used_pct", 101),
                             ("used_pct", float("nan")), ("resets_at", float("inf"))):
            with self.subTest(field=field, value=value):
                reading = {**pool(3, 48), field: value}
                self.assertFalse(sw.claude_allowed({"claude": reading}))
                self.assertEqual(sw.choose({"claude": reading, "grok": UNKNOWN}, "normal")[0], "grok")

    def test_claude_off_is_refused_even_with_room(self):
        p = {"claude": pool(3, 48, "OFF")}
        self.assertFalse(sw.claude_allowed(p))
        with self.assertRaisesRegex(sw.Refused, "OFF"):
            sw.choose(p, "normal", "claude")

    def test_highest_expiring_room_wins_not_lowest_pace(self):
        p = {"grok": pool(30, 12, pace=1.2), "codex": pool(20, 48, pace=0.4),
             "claude": pool(85, 48)}
        self.assertEqual(sw.choose(p, "normal")[0], "grok")
        p["codex"] = pool(20, 6, pace=1.4)
        self.assertEqual(sw.choose(p, "normal")[0], "codex")

    def test_known_usage_needs_reset_but_not_pace(self):
        self.assertEqual(sw.choose({"grok": UNKNOWN, "codex": pool(50, 48)}, "normal")[0], "codex")
        p = {"grok": pool(20, pace=0.1), "codex": pool(50, 48)}
        self.assertEqual(sw.choose(p, "normal")[0], "codex")

    def test_rank_uses_reset_timestamp_not_stale_hours_left(self):
        p = {"grok": pool(20, 48), "codex": pool(20, 12)}
        p["grok"]["hours_left"] = 1
        p["codex"]["hours_left"] = 100
        self.assertEqual(sw.choose(p, "normal")[0], "codex")

    def test_score_denominator_is_at_least_one_hour(self):
        p = {"grok": pool(50, 0), "codex": pool(20, 0.5)}
        self.assertEqual(sw.choose(p, "normal")[0], "codex")
        p["grok"] = pool(50, -1)
        self.assertEqual(sw.choose(p, "normal")[0], "codex")

    def test_equal_scores_follow_table_order(self):
        p = {"grok": pool(60, 24), "codex": pool(20, 48), "claude": pool(85, 48)}
        self.assertEqual(sw.choose(p, "normal")[0], "grok")
        p["deepseek"] = pool(60, 24)
        self.assertEqual(sw.choose(p, "normal")[0], "deepseek")

    def test_reported_unknown_beats_unreported_family(self):
        family, reason = sw.choose(EXAMPLE, "normal")
        self.assertEqual(family, "grok")
        self.assertIn("usage unknown", reason)
        self.assertEqual(sw.choose(EXAMPLE, "simple")[0], "deepseek")

    def test_unknown_never_beats_known_healthy_family(self):
        p = {"grok": UNKNOWN, "codex": pool(50, 48), "claude": pool(85, 48)}
        self.assertEqual(sw.choose(p, "normal")[0], "codex")

    def test_claude_competes_with_known_families(self):
        p = {"deepseek": pool(50, 168), "grok": pool(50, 120),
             "codex": pool(50, 96), "claude": pool(3, 48)}
        self.assertEqual(sw.choose(p, "normal")[0], "claude")
        self.assertEqual(sw.choose(p, "hard")[0], "claude")
        self.assertEqual(sw.choose(p, "simple")[0], "claude")

    def test_metered_never_beats_on_codex(self):
        p = {"codex": pool(20, 48), "deepseek-api": pool(0, 1)}
        self.assertEqual(sw.choose(p, "normal")[0], "codex")
        with self.assertRaisesRegex(sw.Refused, "subscription.*codex"):
            sw.choose(p, "normal", "deepseek-api")

    def test_unknown_subscription_blocks_metered(self):
        p = {"grok": UNKNOWN, "deepseek-api": pool(0, 1)}
        self.assertEqual(sw.choose(p, "normal")[0], "grok")
        with self.assertRaisesRegex(sw.Refused, "subscription"):
            sw.choose(p, "normal", "deepseek-api")

    def test_unreported_subscription_blocks_metered(self):
        p = {"grok": pool(100, 48, "OFF"), "codex": pool(100, 48, "OFF"),
             "claude": pool(85, 48)}
        self.assertEqual(sw.choose(p, "normal")[0], "deepseek")

    def test_all_subscriptions_off_uses_deepseek_api(self):
        p = {family: pool(100, 48, "OFF") for family in ("deepseek", "grok", "codex", "claude")}
        self.assertEqual(sw.choose(p, "normal")[0], "deepseek-api")
        self.assertEqual(sw.choose(p, "simple")[0], "deepseek-api")
        self.assertEqual(sw.choose(p, "normal", "deepseek-api")[0], "deepseek-api")

    def test_no_suitable_family_is_refused(self):
        p = {family: pool(100, 48, "OFF") for family in ("deepseek", "grok", "codex", "claude", "deepseek-api")}
        with self.assertRaisesRegex(sw.Refused, "no family is allowed"):
            sw.choose(p, "normal")
        with self.assertRaisesRegex(sw.Refused, "no family is allowed"):
            sw.choose(p, "hard", "grok")

    def test_refused_level_names_best_suitable_alternative(self):
        p = {"deepseek": UNKNOWN, "grok": pool(30, 24), "codex": pool(20, 48), "claude": pool(85, 48)}
        with self.assertRaisesRegex(sw.Refused, "does not run hard.*best allowed alternative: grok"):
            sw.choose(p, "hard", "deepseek")

    def test_unknown_family_and_level_are_refused(self):
        with self.assertRaises(sw.Refused):
            sw.choose(EXAMPLE, "normal", "gemini")
        with self.assertRaises(sw.Refused):
            sw.choose(EXAMPLE, "trivial")

    def test_build_argv_uses_requested_models(self):
        self.assertEqual(sw.build_argv("grok", "hard", "fix the bug"),
                         ["/home/valentin/.local/bin/cursor-agent", "-p", "-f", "--model", "grok-4.7", "fix the bug"])
        for level, model in (("simple", "haiku"), ("normal", "sonnet"), ("hard", "sonnet")):
            self.assertEqual(sw.build_argv("claude", level, "fix"), ["claude", "-p", "--model", model, "fix"])
        for level in ("simple", "normal"):
            self.assertEqual(sw.build_argv("deepseek-api", level, "fix"),
                             ["/home/valentin/.npm-global/bin/pi", "-p", "--provider", "deepseek",
                              "--model", "deepseek-v4.1-flash", "--thinking", "medium", "fix"])
        self.assertIn("--effort=high", sw.build_argv("codex", "hard", "fix"))
        self.assertIn("--effort=medium", sw.build_argv("codex", "normal", "fix"))


class CliTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.tmp = Path(directory.name)
        self.fixture = self.tmp / "readings.json"
        self.brief = self.tmp / "brief.md"
        self.brief.write_text("fix the failing test")

    def run_cli(self, readings, *args, exit_code=0, brief=True):
        self.fixture.write_text(json.dumps(readings))
        cmd = [sys.executable, str(SCRIPT), *args]
        if brief:
            cmd.append(str(self.brief))
        done = subprocess.run(cmd, capture_output=True, text=True,
                              env={**os.environ, "PLAN_USAGE_FIXTURE": str(self.fixture)})
        self.assertEqual(done.returncode, exit_code, done.stdout + done.stderr)
        return done

    def test_dry_run_prints_line_and_argv(self):
        done = self.run_cli(EXAMPLE, "--dry-run", "--level", "normal")
        self.assertIn("spawn-worker: grok normal", done.stderr)
        self.assertIn("usage unknown", done.stderr)
        self.assertIn("/home/valentin/.local/bin/cursor-agent", done.stdout)

    def test_refusal_exits_2(self):
        done = self.run_cli(EXAMPLE, "--dry-run", "--level", "hard", "--family", "codex", exit_code=2)
        self.assertIn("refused", done.stderr)
        self.assertIn("OFF", done.stderr)
        self.assertEqual(done.stdout, "")

    def test_rank_needs_no_brief_or_level(self):
        done = self.run_cli(EXAMPLE, "--rank", brief=False)
        self.assertIn("1. grok", done.stdout)
        self.assertIn("usage unknown", done.stdout)
        self.assertIn("codex", done.stdout)
        self.assertIn("OFF", done.stdout)
        self.assertIn("orchestrators", done.stdout)
        self.assertIn("deepseek-api", done.stdout)
        self.assertIn("subscription", done.stdout)
        self.assertEqual(done.stderr, "")

    def test_rank_matches_choice_and_reports_score(self):
        self.clock = patch("time.time", return_value=NOW)
        self.clock.start()
        self.addCleanup(self.clock.stop)
        p = {"grok": UNKNOWN, "claude": pool(3, 48)}
        self.fixture.write_text(json.dumps(p))
        with patch.dict(os.environ, {"PLAN_USAGE_FIXTURE": str(self.fixture)}), \
                patch("sys.stdout") as stdout, patch.object(sw.os, "execvp") as execute:
            self.assertEqual(sw.main(["--rank", "--level", "normal"]), 0)
        output = "".join(call.args[0] for call in stdout.write.call_args_list)
        self.assertIn("1. claude", output)
        self.assertIn("97% room", output)
        self.assertIn("48.0h", output)
        self.assertIn("2.021", output)
        self.assertEqual(sw.choose(p, "normal")[0], "claude")
        execute.assert_not_called()

    def test_rank_and_dry_run_choose_claude_with_expiring_room(self):
        p = {"claude": {"used_pct": 3, "resets_at": time.time() + 48 * 3600, "state": "ON"},
             "grok": UNKNOWN}
        ranked = self.run_cli(p, "--rank", "--level", "normal", brief=False)
        self.assertTrue(ranked.stdout.startswith("1. claude [subscription]"))
        chosen = self.run_cli(p, "--dry-run", "--level", "normal")
        self.assertIn("spawn-worker: claude normal", chosen.stderr)
        self.assertIn("'sonnet'", chosen.stdout)

    def test_rank_all_refused_still_exits_zero(self):
        p = {family: pool(100, 48, "OFF") for family in ("deepseek", "grok", "codex", "claude", "deepseek-api")}
        done = self.run_cli(p, "--rank", "--level", "normal", brief=False)
        self.assertIn("refused", done.stdout)
        self.assertNotIn("1. ", done.stdout)

    def test_rank_simple_shows_unsuitable_families(self):
        done = self.run_cli(EXAMPLE, "--rank", "--level", "simple", brief=False)
        self.assertIn("1. deepseek", done.stdout)
        self.assertIn("does not run simple", done.stdout)

    def test_reader_failure_refuses(self):
        self.fixture.write_text("{")
        done = subprocess.run([sys.executable, str(SCRIPT), "--level", "normal", str(self.brief)],
                              capture_output=True, text=True,
                              env={**os.environ, "PLAN_USAGE_FIXTURE": str(self.fixture)})
        self.assertEqual(done.returncode, 2)
        self.assertIn("not valid JSON", done.stderr)

    def test_missing_brief_refuses(self):
        self.brief.unlink()
        done = self.run_cli(EXAMPLE, "--level", "normal", exit_code=2)
        self.assertIn("cannot read brief", done.stderr)

    def test_start_requires_level_and_brief(self):
        for args in (("--level", "normal"), ()):
            with self.subTest(args=args):
                done = self.run_cli(EXAMPLE, *args, exit_code=2, brief=False)
                self.assertIn("required", done.stderr)

    def test_empty_brief_refuses(self):
        self.brief.write_text(" ")
        done = self.run_cli(EXAMPLE, "--level", "normal", exit_code=2)
        self.assertIn("empty", done.stderr)

    def test_exec_replaces_process_with_chosen_argv(self):
        self.fixture.write_text(json.dumps(EXAMPLE))
        with patch.dict(os.environ, {"PLAN_USAGE_FIXTURE": str(self.fixture)}), \
                patch.object(sw.os, "execvp") as execute, patch("sys.stderr"):
            self.assertEqual(sw.main(["--level", "normal", str(self.brief)]), 0)
        execute.assert_called_once_with(
            "/home/valentin/.local/bin/cursor-agent",
            ["/home/valentin/.local/bin/cursor-agent", "-p", "-f", "--model", "grok-4.7", "fix the failing test"])


if __name__ == "__main__":
    unittest.main()
