"""Behaviour of the in-process usage reader. One case per state, all from fake bars."""
import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "bin/plan_usage.py"
NOW = 1_700_000_000


def load():
    spec = importlib.util.spec_from_loader(
        "plan_usage", importlib.machinery.SourceFileLoader("plan_usage", str(SCRIPT)))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pu = load()


def reading(used, minutes, gone_pct):
    hours_left = (minutes / 60.0) * (1 - gone_pct / 100.0)
    return pu.window(used, NOW + hours_left * 3600, minutes, NOW)


def test_known_reading_reports_used_and_pace():
    got = pu.pools(now=NOW, readings={
        "claude": {"week": reading(40, 10080, 50), "five_hour": reading(10, 300, 20)},
        "codex": {"week": reading(55, 10080, 50), "five_hour": reading(12, 300, 40)},
    })
    assert got["claude"]["state"] == "ON"
    assert got["claude"]["used_pct"] == 40
    assert got["claude"]["pace_ratio"] == 0.8
    assert got["codex"]["state"] == "ON"
    assert got["codex"]["used_pct"] == 55
    assert got["codex"]["pace_ratio"] == 1.1
    assert got["grok"]["state"] == "unknown"
    assert got["grok"]["used_pct"] is None
    assert got["grok"]["pace_ratio"] is None


def test_over_limit_is_off():
    got = pu.pools(now=NOW, readings={
        "claude": {"week": reading(96, 10080, 80), "five_hour": reading(10, 300, 20)},
        "codex": {"week": reading(20, 10080, 40), "five_hour": reading(97, 300, 50)},
    })
    assert got["claude"]["state"] == "OFF"
    assert got["claude"]["used_pct"] == 96
    assert got["claude"]["pace_ratio"] == 1.2
    assert got["codex"]["state"] == "OFF"
    assert got["codex"]["used_pct"] == 97
    assert got["codex"]["pace_ratio"] == 1.94


def test_unknown_when_there_are_no_numbers():
    got = pu.pools(now=NOW, readings={
        "claude": None,
        "codex": {},
        "grok": {"week": reading(10, 10080, 50)},
    })
    for name in ("claude", "codex", "grok"):
        assert got[name]["state"] == "unknown"
        assert got[name]["used_pct"] is None
        assert got[name]["pace_ratio"] is None
