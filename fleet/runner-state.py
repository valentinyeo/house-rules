#!/usr/bin/env python3
"""Map one runner ending to one listed state (YPER4-1384).

    fleet/runner-state.py --classify --final LINE --rc N --elapsed SEC --stop MARK --waited SEC --ticket KEY
    fleet/runner-state.py --pick-fail --runner N --note LINE --wip TEXT --ledger PATH
    fleet/runner-state.py --self-test

An unknown state is a fault. flag approval is not a state. Waiting on a person is not a state.
Any other RUNNER IDLE line is WAIT_CHECK.
The launcher writes `state` on run-ledger.jsonl. fleet-watch reads that field.
"""
import json
import re
import sys
from pathlib import Path

STATES = (
    "BUILDING",
    "OWN_PR",
    "WAIT_CHECK",
    "IDLE_NO_TICKET",
    "IDLE_CAP",
    "IDLE_PACER",
    "IDLE_LOAD",
    "PROVIDER_BUSY",
    "PARKED",
    "STOPPED",
    "FAULT",
)
WAIT_LIMIT = 30 * 60
TICKET = re.compile(r"\b((?:HTPR|HYFA|IGSH|HYCI)-\d+)\b")
DONE = re.compile(r"\b(?:INFRA |CI )?RUNNER DONE\b")
HUMAN = re.compile(r"\bvalentin\b|flag approval", re.I)
WAIT = re.compile(r"ci-blocked|checks pending|awaiting checks|\bCI pending\b|\brecheck\b", re.I)
OWN = re.compile(r"\bOWN_PR\b|own PR", re.I)
PARKED_LINE = re.compile(r"(?:^|\s)PARKED\s+\S+")
STALL = re.compile(r"no model reply|reply cap|reply stalled", re.I)
TICKET_WAIT = re.compile(r"waits on|waiting on|parked on|BlockedBy", re.I)
# Live proof that needs Valentin's PC or the check phone, while it is off (IGSH-1923, IGSH-1925, HYCI-256, 11 Nov night).
PC_WAIT = re.compile(r"\b(?:desktops?|laptops?|PC|phone|computer)\b[^.;]{0,40}\b(?:disconnected|unavailable|unreachable|offline|cannot be reached)"
                     r"|\b(?:disconnected|unavailable|unreachable|offline)\b[^.;]{0,20}\b(?:desktops?|laptops?|PC|phone)\b", re.I)


def _out(state, result, park="", waits="", detail=""):
    if state not in STATES:
        raise RuntimeError(f"unlisted state {state}")
    return {"state": state, "result": result, "park": park, "waits": waits, "detail": detail[:500]}


def classify(final, rc, elapsed, stop, waited, ticket, overload=False):
    """One ending. `park` is lead, waits, or empty. `waits` is comma-separated ticket keys.

    `overload` is the launcher's read of the run log: the provider refused the work (HYCI-255). That is a rest, not a crash.
    """
    line = (final or "").strip()
    mark = (stop or "").strip().lower()
    if mark == "pacer":
        return _out("IDLE_PACER", "STOPPED", detail="pacer stop")
    if mark:
        return _out("STOPPED", "STOPPED", detail=mark[:80])
    if DONE.search(line):
        return _out("BUILDING", "DONE", detail=line[:160])
    if PARKED_LINE.search(line):
        return _out("PARKED", "PARKED", detail=line[:160])
    # The provider overloaded: nothing was built and nothing is broken, so the ticket must not read as a fault (HYCI-255).
    if overload and not line:
        return _out("PROVIDER_BUSY", "PROVIDER_BUSY", detail="provider busy: the inference service is overloaded")
    # A capped run is the model's fault, not the ticket's: the reason lands in the ledger and fleet/pick hands the ticket
    # back to the next run (HYCI-250).
    if line and STALL.search(line):
        return _out("FAULT", "FAIL", detail=line[:160])
    if line and PC_WAIT.search(line):
        return _out("PARKED", "PARKED", park="pc", detail=line[:160])
    if line and HUMAN.search(line):
        why = "unknown state: flag approval is not a state" if re.search(r"flag approval", line, re.I) else "unknown state: waiting on a person is not a state"
        return _out("FAULT", "FAULT", park="lead", detail=why)
    if line and WAIT.search(line):
        if waited is not None and int(waited) >= WAIT_LIMIT:
            return _out("FAULT", "FAULT", detail="WAIT_CHECK exceeded 30 min")
        return _out("WAIT_CHECK", "WAIT_CHECK", detail=line[:160])
    if line and OWN.search(line):
        return _out("OWN_PR", "DONE", detail=line[:160])
    if line and TICKET_WAIT.search(line):
        keys = [k for k in TICKET.findall(line) if k != ticket]
        if keys:
            return _out("PARKED", "PARKED", park="waits", waits=",".join(dict.fromkeys(keys)), detail=line[:160])
    if line and re.search(r"IDLE_NO_TICKET|no eligible ticket|no free ticket", line, re.I):
        return _out("IDLE_NO_TICKET", "IDLE_NO_TICKET", detail=line[:300])
    if line and re.search(r"\bIDLE_CAP\b|wip:.*closed", line, re.I):
        return _out("IDLE_CAP", "IDLE_CAP", detail=line[:300])
    if line and re.search(r"\bIDLE_LOAD\b|not green", line, re.I):
        return _out("IDLE_LOAD", "IDLE_LOAD", detail=line[:160])
    if line and re.search(r"\bRUNNER IDLE\b", line):
        if waited is not None and int(waited) >= WAIT_LIMIT:
            return _out("FAULT", "FAULT", detail="WAIT_CHECK exceeded 30 min")
        return _out("WAIT_CHECK", "WAIT_CHECK", detail=line[:160])
    if int(rc) == 124 or int(elapsed) >= 3 * 3600 - 10:
        return _out("FAULT", "FAIL", detail="timeout: hit the 3h run limit")
    if not line and (int(rc) != 0 or int(elapsed) < 120):
        return _out("FAULT", "FAIL", detail="crash or run ended before it started")
    if line:
        return _out("FAULT", "FAULT", park="lead", detail="unknown state")
    return _out("FAULT", "FAULT", park="lead", detail="unknown state")


def classify_pick(note, wip):
    """No ticket was picked. The detail carries the picker's not-counted breakdown."""
    text = " ".join(p.strip() for p in (note or "", wip or "") if p and p.strip())
    low = text.lower()
    if "not green" in low or "load5=" in low:
        state = "IDLE_LOAD"
    elif "pacer" in low and "wip:" not in low:
        state = "IDLE_PACER"
    elif "wip:" in low and "closed" in low:
        state = "IDLE_CAP"
    else:
        state = "IDLE_NO_TICKET"
    if "not counted" not in text:
        text = (text + " not counted: (none reported)").strip()
    return _out(state, state, detail=text[:500])


def append_ledger(path, row):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(row, separators=(",", ":")) + "\n")


def _arg(name, default=""):
    if name in sys.argv:
        i = sys.argv.index(name)
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return default


def self_test():
    human = classify("RUNNER IDLE waiting on Valentin flag approval", 0, 600, "", 0, "HTPR-1")
    assert human["state"] == "FAULT" and human["park"] == "lead", human
    assert "unknown state" in human["detail"] and "flag approval" in human["detail"], human
    assert classify("RUNNER IDLE waits on Valentin for a flag", 0, 600, "", 0, "HTPR-1")["park"] == "lead"
    done = classify("INFRA RUNNER DONE HYCI-1 Done", 0, 400, "", 0, "HYCI-1")
    assert done["state"] == "BUILDING" and done["result"] == "DONE" and done["park"] == ""
    assert classify("PARKED HYCI-9", 0, 30, "", 0, "HYCI-9")["state"] == "PARKED"
    busy = classify("", 1, 30, "", 0, "HYCI-1", overload=True)
    assert busy["state"] == "PROVIDER_BUSY" and busy["result"] == "PROVIDER_BUSY" and busy["park"] == "", busy
    assert "provider busy" in busy["detail"], busy
    assert classify("", 1, 30, "", 0, "HYCI-1")["state"] == "FAULT", "without the overload read it is still a crash"
    assert classify("RUNNER IDLE checks pending", 0, 400, "", 0, "HYCI-1", overload=True)["state"] == "WAIT_CHECK", \
        "a run that got its own final line keeps that ending"
    stall = classify("RUNNER IDLE no model reply for 600s twice, run ended", 124, 700, "", 0, "HYCI-1")
    assert stall["state"] == "FAULT" and stall["result"] == "FAIL" and "no model reply" in stall["detail"], stall
    assert stall["park"] == ""
    wait = classify("RUNNER IDLE ci-blocked HYCI-117", 0, 400, "", 10, "HYCI-1")
    assert wait["state"] == "WAIT_CHECK" and wait["park"] == ""
    late = classify("RUNNER IDLE checks pending", 0, 400, "", WAIT_LIMIT, "HYCI-1")
    assert late["state"] == "FAULT" and late["park"] == "" and "30 min" in late["detail"]
    parked = classify("RUNNER IDLE HYCI-160 BlockedBy HYCI-188", 0, 400, "", 0, "HYCI-160")
    assert parked["state"] == "PARKED" and parked["park"] == "waits" and parked["waits"] == "HYCI-188"
    assert classify("RUNNER IDLE driving own PR to live", 0, 400, "", 0, "HTPR-1")["state"] == "OWN_PR"
    assert classify("", 1, 10, "", 0, "HTPR-1")["result"] == "FAIL"
    idle_checks = classify("CI RUNNER IDLE PR 3074 checks", 0, 400, "", 0, "HYCI-182")
    assert idle_checks["state"] == "WAIT_CHECK" and idle_checks["park"] == "", idle_checks
    idle_review = classify("CI RUNNER IDLE HYCI-171 waiting Codex re-review and gate on 50020e7977", 0, 400, "", 0, "HYCI-171")
    assert idle_review["state"] == "WAIT_CHECK" and idle_review["park"] == "", idle_review
    assert classify("RUNNER IDLE something new", 0, 400, "", 0, "HTPR-1")["state"] == "WAIT_CHECK"
    pc = classify("RUNNER IDLE IGSH-1923 desktop disconnected; live proof pending", 0, 400, "", 0, "IGSH-1923")
    assert pc["state"] == "PARKED" and pc["park"] == "pc", pc
    assert classify("RUNNER IDLE IGSH-1925 live-proof unavailable; laptops disconnected", 0, 400, "", 0, "IGSH-1925")["park"] == "pc"
    assert classify("RUNNER IDLE HYCI-256 PC connection unavailable", 0, 400, "", 0, "HYCI-256")["park"] == "pc"
    assert classify("RUNNER IDLE something new", 0, 400, "", WAIT_LIMIT, "HTPR-1")["state"] == "FAULT"
    assert classify("", 0, 400, "pacer", 0, "")["state"] == "IDLE_PACER"
    cap = classify_pick("none: wip: 4 of 4, new work closed (not counted: waiting 2)", "")
    assert cap["state"] == "IDLE_CAP" and "not counted: waiting 2" in cap["detail"]
    none = classify_pick("none: no free ticket the pool may take", "wip: 1 of 5, new work open (not counted: blocked 4)")
    assert none["state"] == "IDLE_NO_TICKET" and "not counted: blocked 4" in none["detail"]
    bare = classify_pick("none: no free ticket", "")
    assert bare["state"] == "IDLE_NO_TICKET" and "not counted:" in bare["detail"]
    day = [
        classify("INFRA RUNNER DONE HYCI-1 Done", 0, 500, "", 0, "HYCI-1"),
        classify("RUNNER IDLE own PR", 0, 500, "", 0, "HTPR-2"),
        classify("RUNNER IDLE recheck 2026-11-08T10:00:00Z", 0, 500, "", 0, "HYCI-3"),
        classify_pick("none: no free ticket", "not counted: filter 3"),
        classify_pick("none: wip: 2 of 2, new work closed (not counted: cap 2)", ""),
        classify("", 0, 500, "pacer", 0, ""),
        classify("RUNNER IDLE not green", 0, 500, "", 0, "HTPR-4"),
        classify("", 1, 40, "", 0, "HYCI-2", overload=True),
        classify("PARKED HTPR-5", 0, 40, "", 0, "HTPR-5"),
        classify("", 0, 500, "manual", 0, ""),
        classify("RUNNER IDLE waiting on Valentin flag approval", 0, 500, "", 0, "HTPR-6"),
    ]
    assert {row["state"] for row in day} == set(STATES), sorted(row["state"] for row in day)
    assert all(row["state"] in STATES for row in day)
    runner = Path(__file__).with_name("runner").read_text()
    assert 'grep -q "RUNNER IDLE"' not in runner
    assert "unknown state" in runner and "flag approval" in runner
    print("runner-state self-test ok")


def main():
    if "--self-test" in sys.argv:
        self_test()
        return
    if "--pick-fail" in sys.argv:
        row = classify_pick(_arg("--note"), _arg("--wip"))
        row.update({"ts": __import__("datetime").datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "runner": int(_arg("--runner", "0")), "ticket": "", "engine": "", "model": "",
                    "reason": _arg("--note")[:300]})
        ledger = _arg("--ledger")
        if ledger:
            append_ledger(ledger, row)
        print(json.dumps(row))
        return
    if "--classify" in sys.argv:
        row = classify(_arg("--final"), int(_arg("--rc", "0")), int(_arg("--elapsed", "0")),
                       _arg("--stop"), int(_arg("--waited", "0")), _arg("--ticket"),
                       overload=_arg("--overload", "0") == "1")
        print(json.dumps(row))
        return
    sys.exit("usage: fleet/runner-state.py --classify | --pick-fail | --self-test")


if __name__ == "__main__":
    main()
