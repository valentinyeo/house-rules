#!/usr/bin/env python3
"""Factory SLO watches for fleet-watch (YPER4-1385). Files or +1s one checks-board ticket per class per day.

Drill harness: missing-check.json with status drill-review means a required review stayed silent; fleet-watch files once.

    fleet/slo-watch.py [--file-ci] [--dry-run]

Reads ~/.local/state/fleet-switch by default (FLEET_WATCH_STATE). Emit one JSON line per breach on stdout; exit 1 when any fire.
"""
import datetime
import json
import os
import re
import subprocess
import sys
import time

FSW = os.environ.get("FLEET_WATCH_STATE") or os.path.expanduser("~/.local/state/fleet-switch")
S = os.environ.get("FLEET_WATCH_RUNNER_STATE") or os.path.expanduser("~/.local/state/ht-or-runners")
ALLOC = os.environ.get("FLEET_PICK_ALLOCATION") or os.path.expanduser("~/.local/state/pacing/allocation.json")
# the factory serves Valentin's own tools, so its SLO breaches go to Software Factory under the infra label
FACTORY_BOARD = "2060"
FACTORY_LABELS = "CI,Hypertask CI,infra,incident,brain-medium"
NOW = time.time()
DRY = "--dry-run" in sys.argv
FILE_CI = "--file-ci" in sys.argv
TICKET = re.compile(r"\b(HTPR|HYFA|IGSH|SOFT|HYCI)-([0-9]+)\b")
RUNNER_STATES = {"BUILDING", "OWN_PR", "WAIT_CHECK"}
OPEN_MAX = 3 * 3600
START_LINE = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z) start$")
END_LINE = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z) end$")
PICK_LINE = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z) pick: (\S+)")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import runner_state as rs
except ImportError:
    rs = None


def stamp():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def note(msg):
    print(msg, file=sys.stderr)
    if DRY:
        return
    os.makedirs(FSW, exist_ok=True)
    with open(f"{FSW}/log.txt", "a") as f:
        f.write(f"{stamp()} fleet-watch: {msg}\n")


def ci_vcc(*args):
    env = dict(os.environ, SHIP_SESSION_NAME="Chief Of Staff", PATH=os.path.expanduser("~/.local/bin") + ":" + os.environ.get("PATH", ""))
    return subprocess.run(["vcc", *args], capture_output=True, text=True, env=env, timeout=300)


def gh_out(args):
    tok = subprocess.run([os.path.expanduser("~/.local/bin/gh-app-token")], capture_output=True, text=True).stdout.strip()
    env = dict(os.environ)
    if tok:
        env["GH_TOKEN"] = tok
    return subprocess.run(["gh", *args], capture_output=True, text=True, env=env, timeout=120)


def dedupe_key(klass):
    return f"{FSW}/slo-{klass}.json"


def deduped(klass):
    path = dedupe_key(klass)
    try:
        last = json.load(open(path)).get("at", 0)
    except (OSError, ValueError):
        last = 0
    return NOW - last < 86400


def mark(klass):
    if DRY:
        return
    os.makedirs(FSW, exist_ok=True)
    json.dump({"at": NOW}, open(dedupe_key(klass), "w"))


def file_incident(title, body, klass):
    if deduped(klass):
        note(f"slo {klass}: open ticket covers it; +1 was recent")
        return False
    if DRY:
        note(f"slo {klass}: would file {title}")
        mark(klass)
        return True
    if not FILE_CI:
        note(f"slo {klass}: breach {title} (no --file-ci)")
        return False
    path = f"{FSW}/slo-{klass}.html"
    os.makedirs(FSW, exist_ok=True)
    open(path, "w").write(body)
    r = ci_vcc("task", "create", "--project", FACTORY_BOARD, "--title", title, "--description-file", path,
                "--priority", "urgent", "--labels", FACTORY_LABELS, "--section", "Todo")
    note(f"slo {klass}: filed {title}" if r.returncode == 0 else f"slo {klass}: file failed {(r.stderr or r.stdout)[-120:]}")
    if r.returncode == 0:
        mark(klass)
        return True
    return False


def watch_missing_drill_review():
    """drill-review: required status stayed silent on a green PR (harness + live)."""
    path = f"{FSW}/missing-check.json"
    try:
        rec = json.load(open(path))
    except (OSError, ValueError):
        return None
    if rec.get("status") != "drill-review":
        return None
    age = int(rec.get("age_min") or 0)
    if age < 30 or rec.get("reported"):
        return None
    body = (
        "<h2>Problem</h2><ul><li>An open PR is green except one required review.</li>"
        f"<li>The review stayed silent for {age} minutes.</li></ul>"
        "<h2>Fix</h2><ul><li>Post the missing review request or ask for the review.</li></ul>"
        "<h2>Done when</h2><ul><li>The required check shows green.</li></ul>"
        "<h2>Risk</h2><ul><li>None.</li></ul><h2>Decision</h2><p>None.</p>")
    title = "Green PR waits on a silent review"
    if file_incident(title, body, "missing-check"):
        if not DRY:
            rec["reported"] = True
            json.dump(rec, open(path, "w"))
    return "slo missing-check: drill-review silent"


def open_prs():
    """Open app pull requests from the shared copy when it is fresh, else live. None when neither works (HYCI-278)."""
    snapshot = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pr-snapshot")
    try:
        shared = subprocess.run([sys.executable, snapshot, "read", "--max-age", "900"],
                                capture_output=True, text=True, timeout=60)
        body = json.loads(shared.stdout) if shared.returncode == 0 else None
        if isinstance(body, dict) and isinstance(body.get("prs"), list):
            kept = [pr for pr in body["prs"] if pr.get("baseRefName") == "production"]
            if kept:
                return kept
    except (OSError, ValueError, subprocess.SubprocessError):
        pass
    got = gh_out(["pr", "list", "-R", "hypertask-ai/hypertask", "--state", "open", "--base", "production",
                  "--json", "number,baseRefName,statusCheckRollup"])
    if got.returncode != 0:
        return None
    try:
        live = json.loads(got.stdout)
    except ValueError:
        return None
    return live if isinstance(live, list) else None


def required_contexts():
    """Required check names on production. The rules endpoint returns a list of rules; the names sit in the
    required_status_checks rule's parameters."""
    rules = gh_out(["api", "repos/hypertask-ai/hypertask/rules/branches/production"])
    if rules.returncode != 0:
        return None
    try:
        body = json.loads(rules.stdout)
    except ValueError:
        return None
    return [c["context"] for r in body if isinstance(r, dict) and r.get("type") == "required_status_checks"
            for c in (r.get("parameters") or {}).get("required_status_checks") or [] if c.get("context")]


def watch_missing_check():
    drill = watch_missing_drill_review()
    if drill:
        return drill
    ctxs = required_contexts()
    if ctxs is None:
        return "slo missing-check: rules unreadable"
    prs = open_prs()
    if not prs:
        return "slo missing-check: open PRs unreadable"
    need = set(ctxs)
    for pr in prs:
        if pr.get("baseRefName", "production") != "production":
            continue
        roll = pr.get("statusCheckRollup") or []
        by = {c.get("name") or c.get("context"): c.get("state") for c in roll if isinstance(c, dict)}
        if not by:
            continue
        missing = [n for n in need if by.get(n) not in ("SUCCESS", "SKIPPED")]
        okish = [c for c in roll if (c.get("state") or "") in ("SUCCESS", "SKIPPED")]
        if not okish or not missing:
            continue
        waitf = f"{FSW}/missing-pr-{pr['number']}.json"
        try:
            rec = json.load(open(waitf))
        except (OSError, ValueError):
            rec = {"first": NOW}
        if NOW - rec["first"] < 30 * 60:
            continue
        miss = ", ".join(missing[:3])
        body = (
            "<h2>Problem</h2><ul><li>An open PR waits on a required check.</li>"
            f"<li>PR number {pr['number']}.</li><li>Missing: {miss}.</li></ul>"
            "<h2>Fix</h2><ul><li>Run or request the missing check.</li></ul>"
            "<h2>Done when</h2><ul><li>Every required check is green.</li></ul>"
            "<h2>Risk</h2><ul><li>None.</li></ul><h2>Decision</h2><p>None.</p>")
        title = f"Green PR waits on missing check"
        file_incident(title, body, "missing-check")
        if not DRY:
            json.dump(rec, open(waitf, "w"))
        return f"slo missing-check: PR #{pr['number']} missing {miss}"
    return None


def _stamp(value):
    return datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)


def open_ticket_run(text, now):
    """A ticket run is open when the log shows pick + start, no later end, and the start is under 3 hours old."""
    last_s = last_e = last_pick = None
    for line in (text or "").splitlines():
        picked = PICK_LINE.match(line)
        if picked:
            last_pick = picked.group(2)
            continue
        started = START_LINE.match(line)
        if started:
            last_s = started.group(1)
            continue
        ended = END_LINE.match(line)
        if ended:
            last_e = ended.group(1)
    if not last_s or not last_pick or last_pick == "nothing":
        return False
    if last_e and last_e >= last_s:
        return False
    if isinstance(now, str):
        now = _stamp(now)
    age = (now - _stamp(last_s)).total_seconds()
    return 0 <= age < OPEN_MAX


def share_of(last, stopped, running):
    """last maps runner id to a state. A pacer-stopped runner counts only while a ticket run is open."""
    stopped = {int(r) for r in (stopped or ())}
    running = {int(r) for r in (running or ())}
    pool = {}
    for rid, state in (last or {}).items():
        rid = int(rid)
        if rid in stopped and rid not in running:
            continue
        pool[rid] = state or ""
    for rid in running:
        pool.setdefault(rid, "BUILDING")
    if not pool:
        return None, None
    live = sum(1 for rid, state in pool.items() if rid in running or state in RUNNER_STATES)
    return live, len(pool)


def stopped_runners(state_dir):
    found = set()
    try:
        names = os.listdir(state_dir)
    except OSError:
        return found
    for name in names:
        if not name.startswith("stop-") or not name[5:].isdigit():
            continue
        try:
            mark = open(os.path.join(state_dir, name), errors="replace").read(80).strip().lower()
        except OSError:
            continue
        if mark.startswith("pacer"):
            found.add(int(name[5:]))
    return found


def running_runners(state_dir, now):
    found = set()
    for n in range(1, 40):
        path = os.path.join(state_dir, f"runner-{n}.log")
        try:
            with open(path, errors="replace") as fh:
                fh.seek(0, os.SEEK_END)
                fh.seek(max(0, fh.tell() - 100000))
                text = fh.read()
        except OSError:
            continue
        if open_ticket_run(text, now):
            found.add(n)
    return found


def ledger_building_share():
    path = os.path.join(S, "run-ledger.jsonl")
    try:
        text = open(path, errors="replace").read()[-262144:]
    except OSError:
        return None, None
    last = {}
    for line in text.splitlines():
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if row.get("runner"):
            last[int(row["runner"])] = row.get("state") or ""
    if not last:
        return None, None
    now = datetime.datetime.now(datetime.timezone.utc)
    return share_of(last, stopped_runners(S), running_runners(S, now))


def watch_building_share():
    recf = f"{FSW}/building-share.json"
    try:
        rec = json.load(open(recf))
    except (OSError, ValueError):
        rec = {"low_since": None}
    hour = time.gmtime(NOW).tm_hour
    if hour < 6 or hour >= 22:
        json.dump({"low_since": None}, open(recf, "w"))
        return None
    live, total = ledger_building_share()
    if live is None or total < 3:
        return None
    share = live / total
    if share >= 0.70:
        rec["low_since"] = None
    elif rec.get("low_since") is None:
        rec["low_since"] = NOW
    json.dump(rec, open(recf, "w"))
    if rec.get("low_since") is None or NOW - rec["low_since"] < 30 * 60:
        return None
    pct = int(share * 100)
    body = (
        "<h2>Problem</h2><ul>"
        f"<li>Only {pct} percent of runners are building.</li>"
        "<li>The goal is 70 percent for 30 minutes.</li></ul>"
        "<h2>Fix</h2><ul><li>Find why runners are idle and unblock them.</li></ul>"
        "<h2>Done when</h2><ul><li>Building share stays at or above 70 percent.</li></ul>"
        "<h2>Risk</h2><ul><li>False alarms when the pool is paused.</li></ul><h2>Decision</h2><p>None.</p>")
    title = f"Building share under 70 percent"
    file_incident(title, body, "building-share")
    return f"slo building: {pct}% of {total} runners building"


def watch_pacer():
    try:
        at = float(json.load(open(ALLOC)).get("at", 0))
    except (OSError, ValueError):
        at = 0
    if at and NOW - at < 3600:
        return None
    body = (
        "<h2>Problem</h2><ul><li>Pacer numbers are over an hour old.</li>"
        "<li>The pool may be on the wrong runner count.</li></ul>"
        "<h2>Fix</h2><ul><li>Restart the pacer timer or fix bin/pacer.</li></ul>"
        "<h2>Done when</h2><ul><li>allocation.json is fresh.</li></ul>"
        "<h2>Risk</h2><ul><li>None.</li></ul><h2>Decision</h2><p>None.</p>")
    title = "Pacer numbers stale over one hour"
    note(f"pacer: allocation {'missing' if not at else int((NOW - at) // 60)}m old")
    file_incident(title, body, "pacer-stop")
    return "slo pacer: allocation stale"


def self_test():
    assert callable(file_incident) and callable(watch_pacer)
    assert "BUILDING" in RUNNER_STATES and "WAIT_CHECK" in RUNNER_STATES
    log = "\n".join([
        "2026-11-08T09:00:00Z end",
        "2026-11-08T09:42:34Z pick: HTPR-7553 cursor composer-2.5 medium (own)",
        "2026-11-08T09:42:34Z start",
    ])
    assert open_ticket_run(log, "2026-11-08T09:50:00Z")
    assert not open_ticket_run("2026-11-08T09:42:34Z pick: nothing to start\n", "2026-11-08T09:50:00Z")
    assert not open_ticket_run("2026-11-08T01:00:00Z pick: HTPR-1 x\n2026-11-08T01:00:00Z start\n", "2026-11-08T09:50:00Z")
    idle = {1: "IDLE_CAP", 2: "IDLE_CAP", 3: "IDLE_CAP", 4: "IDLE_CAP", 5: "IDLE_CAP", 7: "IDLE_CAP"}
    assert share_of(idle, {7}, set()) == (0, 5), "a paused runner is not in the pool"
    live, total = share_of(idle, {7}, {1, 3, 4, 5})
    assert (live, total) == (4, 5) and live / total >= 0.70
    one, five = share_of({i: "IDLE_CAP" for i in range(1, 6)}, set(), {1})
    assert one / five < 0.70
    assert share_of({7: "IDLE_CAP"}, {7}, set()) == (None, None)
    print("fleet/slo-watch self-test ok")


def print_share():
    live, total = ledger_building_share()
    if live is None or not total or live / total < 0.70:
        print(f"building share {live}/{total} under 70")
        return 1
    print(f"building share {live}/{total} meets 70")
    return 0


def main():
    if "--self-test" in sys.argv:
        self_test()
        return
    if "--share" in sys.argv:
        sys.exit(print_share())
    breaches = [b for b in (watch_missing_check(), watch_building_share(), watch_pacer()) if b]
    for b in breaches:
        print(b)
    sys.exit(1 if breaches else 0)


if __name__ == "__main__":
    main()
