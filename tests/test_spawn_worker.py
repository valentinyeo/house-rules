"""Tests for bin/spawn-worker: the only supported way to start a worker.

The script is a file, not a module, so it is imported by path. choose() is pure, so every
routing rule is tested without a reader, a network call or a worker start.
"""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "bin/spawn-worker"


def load():
    spec = importlib.util.spec_from_loader(
        "spawn_worker", importlib.machinery.SourceFileLoader("spawn_worker", str(SCRIPT)))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


sw = load()


def pool(used=None, pace=None, state="ON"):
    return {"used_pct": used, "pace_ratio": pace, "state": state}


UNKNOWN = pool(None, None, "unknown")


def pools(**families):
    return dict(families)


# The live shape of `token-ladder pools --json` on 2026-11-15.
EXAMPLE = json.loads("""
{"claude": {"used_pct": 75.0, "hours_left": 15.4, "resets_at": 1794762000.1,
            "state": "ON", "pace_ratio": 0.8257},
 "codex": {"used_pct": 100, "hours_left": 20.0, "resets_at": 1794778523,
           "state": "OFF", "pace_ratio": 1.1351},
 "grok": {"used_pct": null, "hours_left": null, "resets_at": null, "state": "unknown"}}
""")


# --- rule a: OFF is refused -------------------------------------------------------

def test_off_family_is_refused_for_auto():
    p = pools(deepseek=UNKNOWN, grok=pool(10, 0.4), codex=pool(100, 1.2, "OFF"), claude=pool(20, 0.3))
    assert sw.choose(p, "normal")[0] == "grok"


def test_off_family_pinned_is_refused_with_reason():
    p = pools(grok=pool(10, 0.4), codex=pool(99, 1.4, "OFF"), claude=pool(20, 0.3))
    with pytest.raises(sw.Refused) as err:
        sw.choose(p, "normal", "codex")
    assert "OFF" in str(err.value)
    assert "grok" in str(err.value)


# --- rule b: Claude is kept for orchestrators -------------------------------------

def test_claude_refused_over_80_pct():
    p = pools(grok=UNKNOWN, claude=pool(85, 0.5))
    with pytest.raises(sw.Refused) as err:
        sw.choose(p, "normal", "claude")
    assert "85% used" in str(err.value)
    assert "orchestrators" in str(err.value)


def test_claude_refused_over_pace_even_when_used_is_low():
    p = pools(grok=UNKNOWN, claude=pool(40, 1.1))
    with pytest.raises(sw.Refused) as err:
        sw.choose(p, "normal", "claude")
    assert "pace 1.10" in str(err.value)


def test_claude_allowed_under_the_ceiling_when_pinned():
    p = pools(grok=UNKNOWN, claude=pool(75, 0.8257))
    family, reason = sw.choose(p, "normal", "claude")
    assert family == "claude"
    assert "75% used" in reason


def test_claude_with_unknown_usage_cannot_be_proven_safe():
    p = pools(grok=UNKNOWN, claude=UNKNOWN)
    with pytest.raises(sw.Refused) as err:
        sw.choose(p, "normal", "claude")
    assert "usage unknown" in str(err.value)


# --- rule c: unknown usage is allowed, ranked last --------------------------------

def test_unknown_never_beats_a_known_healthy_family():
    p = pools(grok=UNKNOWN, codex=pool(50, 0.7), claude=pool(10, 0.2))
    assert sw.choose(p, "normal")[0] == "codex"


def test_unknown_is_picked_when_nothing_else_is_allowed():
    p = pools(grok=UNKNOWN, codex=pool(100, 1.5, "OFF"), claude=pool(95, 1.5))
    family, reason = sw.choose(p, "normal")
    assert family == "grok"
    assert "usage unknown" in reason


# --- rule d: lowest pace wins, TIE_ORDER settles ties -----------------------------

def test_lowest_pace_wins():
    p = pools(grok=pool(30, 1.2), codex=pool(20, 0.4), claude=pool(10, 0.2))
    assert sw.choose(p, "normal")[0] == "codex"
    p = pools(grok=pool(30, 0.3), codex=pool(20, 0.4), claude=pool(10, 0.2))
    assert sw.choose(p, "normal")[0] == "grok"


def test_tie_breaks_in_table_order():
    p = pools(grok=pool(30, 0.5), codex=pool(20, 0.5), claude=pool(10, 0.5))
    assert sw.choose(p, "normal")[0] == "grok"
    p = pools(deepseek=pool(30, 0.5), grok=UNKNOWN, codex=UNKNOWN, claude=pool(10, 0.5))
    assert sw.choose(p, "simple")[0] == "deepseek"


# --- rule e: a refused pin names the best alternative -----------------------------

def test_refused_pin_names_best_allowed_alternative():
    p = pools(grok=pool(30, 1.4), codex=pool(20, 0.4), claude=pool(90, 1.2))
    with pytest.raises(sw.Refused) as err:
        sw.choose(p, "normal", "claude")
    assert "best allowed alternative: codex" in str(err.value)


def test_refused_level_names_alternative():
    p = pools(deepseek=UNKNOWN, grok=pool(30, 0.4), codex=pool(20, 0.6), claude=pool(10, 0.2))
    with pytest.raises(sw.Refused) as err:
        sw.choose(p, "hard", "deepseek")
    assert "does not run hard" in str(err.value)
    assert "best allowed alternative: grok" in str(err.value)


def test_nothing_allowed_is_refused():
    p = pools(deepseek=pool(99, 1.5, "OFF"), grok=pool(99, 1.5, "OFF"),
              codex=pool(99, 1.5, "OFF"), claude=pool(99, 1.5))
    with pytest.raises(sw.Refused) as err:
        sw.choose(p, "hard", "grok")
    assert "no family is allowed" in str(err.value)


def test_unknown_family_and_level_are_refused():
    with pytest.raises(sw.Refused):
        sw.choose(EXAMPLE, "normal", "gemini")
    with pytest.raises(sw.Refused):
        sw.choose(EXAMPLE, "trivial")


# --- rule f: auto only hands work to Claude when nothing else is available --------

def test_example_picks_grok_for_normal_and_deepseek_for_simple():
    # claude is under the ceiling (75% < 80, 0.83 <= 0.9) yet must not take worker work
    # while grok is unknown; codex is OFF.
    assert sw.choose(EXAMPLE, "normal")[0] == "grok"
    assert "usage unknown" in sw.choose(EXAMPLE, "normal")[1]
    assert sw.choose(EXAMPLE, "simple")[0] == "deepseek"
    assert sw.choose(EXAMPLE, "hard")[0] == "grok"


def test_claude_never_wins_on_pace():
    # Claude has by far the best pace of all; worker work still goes elsewhere.
    p = pools(deepseek=pool(50, 0.6), grok=pool(50, 0.7), codex=pool(50, 0.8),
              claude=pool(20, 0.1))
    assert sw.choose(p, "normal")[0] == "deepseek"
    assert sw.choose(p, "simple")[0] == "deepseek"
    p = pools(deepseek=UNKNOWN, grok=pool(50, 0.7), codex=pool(50, 0.8), claude=pool(20, 0.1))
    assert sw.choose(p, "normal")[0] == "grok"


def test_claude_is_used_when_no_other_family_is_on_or_unknown():
    # grok and codex are OFF, deepseek has no line at all: nothing is ON or unknown.
    p = pools(grok=pool(100, 1.5, "OFF"), codex=pool(100, 1.5, "OFF"), claude=pool(30, 0.4))
    assert sw.choose(p, "normal")[0] == "claude"
    assert sw.choose(p, "hard")[0] == "claude"


def test_a_reported_unknown_beats_an_unreported_family():
    # The reader reports grok as unknown but has no line for deepseek.
    p = pools(grok=UNKNOWN, codex=pool(100, 1.5, "OFF"), claude=pool(95, 1.5))
    family, reason = sw.choose(p, "normal")
    assert family == "grok"
    assert "usage unknown" in reason


# --- data shape ------------------------------------------------------------------

def test_families_table_matches_the_contract():
    expected = {
        "deepseek": {"simple", "normal"},
        "grok": {"normal", "hard"},
        "codex": {"normal", "hard"},
        "claude": {"normal", "hard"},
    }
    assert {f: sw.FAMILIES[f]["levels"] for f in expected} == expected
    for family, spec in sw.FAMILIES.items():
        for level in spec["levels"]:
            assert "{brief}" in spec["cmd"][level], (family, level)
    assert sw.FAMILIES["codex"]["cmd"]["hard"][-2] == "--effort=high"
    assert sw.FAMILIES["codex"]["cmd"]["normal"][-2] == "--effort=medium"


def test_build_argv_substitutes_the_brief():
    argv = sw.build_argv("grok", "hard", "fix the bug")
    assert argv == ["/home/valentin/.local/bin/cursor-agent", "-p", "-f", "--model", "grok-4.7", "fix the bug"]


# --- CLI -------------------------------------------------------------------------

def run_cli(tmp_path, pools_json, *args, exit_code=0):
    reader = tmp_path / "token-ladder"
    reader.write_text("#!/usr/bin/env python3\nprint(%r)\n" % json.dumps(pools_json))
    reader.chmod(0o755)
    brief = tmp_path / "brief.md"
    brief.write_text("fix the failing test")
    env = {**os.environ, "TOKEN_LADDER": str(reader)}
    done = subprocess.run([sys.executable, str(SCRIPT), *args, str(brief)],
                          capture_output=True, text=True, env=env)
    assert done.returncode == exit_code, done.stdout + done.stderr
    return done


def test_cli_dry_run_prints_line_and_argv(tmp_path):
    done = run_cli(tmp_path, EXAMPLE, "--dry-run", "--level", "normal")
    assert "spawn-worker: grok normal" in done.stderr
    assert "usage unknown" in done.stderr
    assert "/home/valentin/.local/bin/cursor-agent" in done.stdout


def test_cli_refusal_exits_2(tmp_path):
    done = run_cli(tmp_path, EXAMPLE, "--dry-run", "--level", "hard", "--family", "codex",
                   exit_code=2)
    assert "refused" in done.stderr and "OFF" in done.stderr
    assert done.stdout == ""


def test_cli_reader_failure_refuses(tmp_path):
    reader = tmp_path / "token-ladder"
    reader.write_text("#!/bin/sh\necho 'no such plan' >&2\nexit 3\n")
    reader.chmod(0o755)
    brief = tmp_path / "brief.md"
    brief.write_text("work")
    done = subprocess.run([sys.executable, str(SCRIPT), "--level", "normal", str(brief)],
                          capture_output=True, text=True,
                          env={**os.environ, "TOKEN_LADDER": str(reader)})
    assert done.returncode == 2
    assert "no such plan" in done.stderr


def test_cli_missing_brief_refuses(tmp_path):
    done = subprocess.run([sys.executable, str(SCRIPT), "--level", "normal",
                           str(tmp_path / "nope.md")],
                          capture_output=True, text=True,
                          env={**os.environ, "TOKEN_LADDER": "/bin/false"})
    assert done.returncode == 2
    assert "cannot read brief" in done.stderr


def test_cli_exec_replaces_process_with_the_chosen_argv(tmp_path, monkeypatch, capsys):
    reader = tmp_path / "token-ladder"
    reader.write_text("#!/usr/bin/env python3\nprint(%r)\n" % json.dumps(EXAMPLE))
    reader.chmod(0o755)
    brief = tmp_path / "brief.md"
    brief.write_text("fix the failing test")
    monkeypatch.setenv("TOKEN_LADDER", str(reader))
    monkeypatch.setattr(sw, "READER", str(reader))
    calls = []
    monkeypatch.setattr(sw.os, "execvp", lambda prog, argv: calls.append((prog, argv)))
    assert sw.main(["--level", "normal", str(brief)]) == 0
    assert calls == [("/home/valentin/.local/bin/cursor-agent",
                      ["/home/valentin/.local/bin/cursor-agent", "-p", "-f", "--model", "grok-4.7", "fix the failing test"])]
    assert "spawn-worker: grok normal" in capsys.readouterr().err
