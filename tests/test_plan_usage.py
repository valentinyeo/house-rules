"""Behaviour of the in-process usage reader. One case per state, all from fake bars."""
import importlib.util
import json
from datetime import datetime, timezone
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
        "grok": None,
    })
    for name in ("claude", "codex", "grok"):
        assert got[name]["state"] == "unknown"
        assert got[name]["used_pct"] is None
        assert got[name]["pace_ratio"] is None


# Recorded from GetCurrentPeriodUsage. Strings are the proto JSON int64 form.
# No login, no account id. The period is exactly 7 days.
RECORDED_GROK = {
    "billingCycleStart": "1794672623669",
    "billingCycleEnd": "1795277423669",
    "planUsage": {
        "autoPercentUsed": 35.31365646719018,
        "totalPercentUsed": 35.31365646719018,
    },
    "enabled": True,
    "displayMessage": "You've used 35% of your included usage",
}
GROK_RESET = 1795277423669 / 1000
GROK_MID = GROK_RESET - (7 * 24 * 3600) / 2


def test_grok_recorded_period_reports_used_pace_and_reset():
    bars = pu.parse_grok_response(RECORDED_GROK, GROK_MID)
    got = pu.pools(now=GROK_MID, readings={"claude": None, "codex": None, "grok": bars})
    assert got["grok"]["used_pct"] == 35.3
    assert got["grok"]["pace_ratio"] == 0.706
    assert got["grok"]["state"] == "ON"
    assert got["grok"]["resets_at"] == GROK_RESET
    assert got["claude"]["state"] == "unknown"
    assert got["codex"]["state"] == "unknown"


def push(tmp_path, readings, now=NOW, calls=None, projects=None, send=None):
    sent = []

    def capture(message):
        if send is not None:
            send(message)
        sent.append(message)

    got = pu.alert(now=now, readings=readings, state_dir=str(tmp_path), send=capture,
                   calls=calls, projects_root=projects)
    return got, sent


def home_alerts():
    path = Path.home() / ".local/state/plan-usage/alerts.json"
    return path.read_bytes() if path.exists() else None


def test_over_pace_alerts_once_then_stays_quiet(tmp_path):
    # 70/50 = 1.40, over Claude's 1.15. Codex at 1.20 stays under 1.3.
    before = home_alerts()
    readings = {
        "claude": {"week": reading(70, 10080, 50)},
        "codex": {"week": reading(60, 10080, 50)},
        "grok": {"week": reading(40, 10080, 50)},
    }
    pace = pu.pools(now=NOW, readings=readings)["claude"]["pace_ratio"]
    first, sent = push(tmp_path, readings, calls=[])
    assert [item["family"] for item in first] == ["claude"]
    assert first[0]["title"] == "Plan burning too fast"
    assert f"{pace:.2f}x" in first[0]["body"]
    assert "Codex" not in first[0]["body"]
    second, sent = push(tmp_path, readings, now=NOW + 3600, calls=[])
    assert second == []
    assert len(sent) == 0
    third, _ = push(tmp_path, readings, now=NOW + 7200, calls=[])
    assert [item["family"] for item in third] == ["claude"]
    codex_dir = tmp_path / "codex"
    codex_dir.mkdir()
    codex, _ = push(codex_dir, {"codex": {"week": reading(70, 10080, 50)}}, calls=[])
    assert [item["family"] for item in codex] == ["codex"]
    assert "1.40x" in codex[0]["body"]
    assert home_alerts() == before


def test_usage_crossing_is_one_push_and_waits_out_the_quiet_period(tmp_path):
    # 85/80 = 1.0625, under 1.15, so only the 80% crossing speaks.
    first, _ = push(tmp_path, {"claude": {"week": reading(85, 10080, 80)}}, calls=[])
    assert len(first) == 1
    assert "crossed 80%" in first[0]["body"]
    assert "95%" not in first[0]["body"]
    # 96 crosses 95 inside the two-hour quiet time.
    held, _ = push(tmp_path, {"claude": {"week": reading(96, 10080, 90)}}, now=NOW + 600, calls=[])
    assert held == []
    later, _ = push(tmp_path, {"claude": {"week": reading(96, 10080, 90)}}, now=NOW + 7200, calls=[])
    assert len(later) == 1
    assert "crossed 95%" in later[0]["body"]
    assert "80%" not in later[0]["body"]


def test_falling_under_a_mark_drops_the_pending_alert(tmp_path):
    push(tmp_path, {"claude": {"week": reading(85, 10080, 80)}}, calls=[])
    push(tmp_path, {"claude": {"week": reading(96, 10080, 90)}}, now=NOW + 600, calls=[])
    push(tmp_path, {"claude": {"week": reading(50, 10080, 50)}}, now=NOW + 1200, calls=[])
    later, _ = push(tmp_path, {"claude": {"week": reading(50, 10080, 50)}}, now=NOW + 7200, calls=[])
    assert later == []


def stamp(ts):
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def assistant(model, slug, project, ts, kind="assistant"):
    return {
        "type": kind,
        "timestamp": stamp(ts),
        "slug": slug,
        "cwd": f"/work/{project}",
        "sessionId": slug,
        "requestedModel": "claude-sonnet-5",
        "message": {"role": kind, "model": model},
    }


def write_chat(root, project, entries):
    path = Path(root) / project / "session.jsonl"
    path.parent.mkdir(parents=True)
    path.write_text("".join(json.dumps(entry) + "\n" for entry in entries))


def test_fable_share_names_the_busiest_chats(tmp_path):
    # A Claude pace push must not swallow the Fable push.
    before = home_alerts()
    pace, _ = push(tmp_path, {"claude": {"week": reading(70, 10080, 50)}}, calls=[])
    assert [item["family"] for item in pace] == ["claude"]
    root = tmp_path / "projects"
    recent, old = NOW - 60, NOW - 7200
    write_chat(root, "alpha",
               [assistant("claude-fable-5", "alpha", "alpha-proj", recent) for _ in range(5)]
               + [assistant("claude-sonnet-5", "alpha", "alpha-proj", old) for _ in range(40)]
               + [assistant("claude-fable-5", "alpha", "alpha-proj", recent, kind="user") for _ in range(5)])
    write_chat(root, "bravo", [assistant("claude-fable-5", "bravo", "bravo-proj", recent) for _ in range(3)])
    write_chat(root, "charlie", [assistant("claude-fable-5", "charlie", "charlie-proj", recent) for _ in range(2)])
    write_chat(root, "delta", [assistant("claude-fable-5", "delta", "delta-proj", recent)])
    write_chat(root, "echo", [assistant("claude-sonnet-5", "echo", "echo-proj", recent) for _ in range(6)])
    calm = {"claude": {"week": reading(40, 10080, 50)}}
    got, _ = push(tmp_path, calm, now=NOW + 30, projects=str(root))
    assert [item["family"] for item in got] == ["fable"]
    body = got[0]["body"]
    assert got[0]["title"] == "Fable is burning Claude"
    assert "11 of 17" in body
    assert body.index("alpha-proj: alpha (5)") < body.index("bravo-proj: bravo (3)")
    assert body.index("bravo-proj: bravo (3)") < body.index("charlie-proj: charlie (2)")
    assert "delta" not in body
    assert "echo" not in body
    again, _ = push(tmp_path, calm, now=NOW + 90, projects=str(root))
    assert again == []
    assert home_alerts() == before


def test_a_call_split_across_reads_still_counts(tmp_path):
    path = tmp_path / "session.jsonl"
    pad = "x" * 100
    entry = assistant("claude-fable-5", "alpha", "hypertask", NOW - 60)
    path.write_text(json.dumps({"type": "user", "text": pad}) + "\n" + json.dumps(entry) + "\n")
    calls = pu.recent_calls(str(path), NOW - 3600, NOW, chunk=40)
    assert calls == [("claude-fable-5", "hypertask: alpha")]


def test_normal_pace_is_silent(tmp_path):
    # 57.5/50 = 1.15 and 65/50 = 1.30 are not over the lines. 3/10 is not over 30%.
    readings = {
        "claude": {"week": reading(57.5, 10080, 50)},
        "codex": {"week": reading(65, 10080, 50)},
        "grok": {"week": reading(40, 10080, 50)},
    }
    calls = [("claude-fable-5", "alpha")] * 3 + [("claude-sonnet-5", "beta")] * 7
    got, sent = push(tmp_path, readings, calls=calls)
    assert got == []
    assert sent == []
    assert pu.pools(now=NOW, readings=readings)["claude"]["pace_ratio"] == 1.15
    assert pu.pools(now=NOW, readings=readings)["codex"]["pace_ratio"] == 1.3


def test_failed_push_is_retried(tmp_path):
    readings = {"claude": {"week": reading(70, 10080, 50)}}

    def down(_message):
        raise OSError("down")

    failed, _ = push(tmp_path, readings, calls=[], send=down)
    assert failed == []
    retried, _ = push(tmp_path, readings, now=NOW + 60, calls=[])
    assert [item["family"] for item in retried] == ["claude"]


def test_alert_usage_and_timer_example():
    assert pu.main([]) == 2
    assert pu.main(["pools"]) == 2
    timer = (REPO / "systemd/plan-usage-alert.timer").read_text()
    service = (REPO / "systemd/plan-usage-alert.service").read_text()
    assert "OnCalendar=*:0/5" in timer
    assert "plan-usage-alert.service" in timer
    assert "plan_usage.py alert" in service
    for path in (REPO / "bin").glob("*.sh"):
        assert "plan-usage-alert" not in path.read_text()
