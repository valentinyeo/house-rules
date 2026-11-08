#!/usr/bin/env python3
"""Factory SLO watches for fleet-watch (YPER4-1385). Files or +1s one checks-board ticket per class per day.

Drill harness: missing-check.json with status drill-review means a required review stayed silent; fleet-watch files once.

    fleet/slo-watch.py [--file-ci] [--dry-run]

Reads ~/.local/state/fleet-switch by default (FLEET_WATCH_STATE). Emit one JSON line per breach on stdout; exit 1 when any fire.
"""
import json
import os
import re
import subprocess
import sys
import time

FSW = os.environ.get("FLEET_WATCH_STATE") or os.path.expanduser("~/.local/state/fleet-switch")
S = os.environ.get("FLEET_WATCH_RUNNER_STATE") or os.path.expanduser("~/.local/state/ht-or-runners")
ALLOC = os.environ.get("FLEET_PICK_ALLOCATION") or os.path.expanduser("~/.local/state/pacing/allocation.json")
CI_BOARD = "11514"
NOW = time.time()
DRY = "--dry-run" in sys.argv
FILE_CI = "--file-ci" in sys.argv
TICKET = re.compile(r"\b(HTPR|HYFA|IGSH|YPER4|HYCI)-([0-9]+)\b")
RUNNER_STATES = {"BUILDING", "OWN_PR"}

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


def file_incident(title, body, labels, klass):
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
    r = ci_vcc("task", "create", "--project", CI_BOARD, "--title", title, "--description-file", path,
                "--priority", "urgent", "--labels", labels, "--section", "Backlog")
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
    if file_incident(title, body, "CI,Hypertask CI,incident,brain-medium", "missing-check"):
        if not DRY:
            rec["reported"] = True
            json.dump(rec, open(path, "w"))
    return "slo missing-check: drill-review silent"


def required_contexts():
    rules = gh_out(["api", "repos/hypertask-ai/hypertask/rules/branches/production", "--jq", ".required_status_checks"])
    if rules.returncode != 0:
        return None
    try:
        body = json.loads(rules.stdout)
    except ValueError:
        return None
    ctx = body.get("checks") or []
    return [c.get("context") or c for c in ctx if isinstance(c, dict)] or list(ctx)


def watch_missing_check():
    drill = watch_missing_drill_review()
    if drill:
        return drill
    ctxs = required_contexts()
    if ctxs is None:
        return "slo missing-check: rules unreadable"
    got = gh_out(["pr", "list", "-R", "hypertask-ai/hypertask", "--state", "open", "--base", "production",
                "--json", "number,statusCheckRollup"])
    if got.returncode != 0:
        return "slo missing-check: open PRs unreadable"
    try:
        prs = json.loads(got.stdout)
    except ValueError:
        return "slo missing-check: open PRs unreadable"
    need = set(ctxs)
    for pr in prs:
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
        file_incident(title, body, "CI,Hypertask CI,incident,brain-medium", "missing-check")
        if not DRY:
            json.dump(rec, open(waitf, "w"))
        return f"slo missing-check: PR #{pr['number']} missing {miss}"
    return None


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
            last[row["runner"]] = row
    if not last:
        return None, None
    live = sum(1 for r in last.values() if (r.get("state") or "") in RUNNER_STATES)
    return live, len(last)


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
    file_incident(title, body, "CI,Hypertask CI,incident,brain-medium", "building-share")
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
    file_incident(title, body, "CI,Hypertask CI,incident,brain-medium", "pacer-stop")
    return "slo pacer: allocation stale"


def main():
    breaches = [b for b in (watch_missing_check(), watch_building_share(), watch_pacer()) if b]
    for b in breaches:
        print(b)
    sys.exit(1 if breaches else 0)


if __name__ == "__main__":
    main()
