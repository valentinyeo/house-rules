#!/usr/bin/env python3
"""Map one runner ending to one listed state (YPER4-1384).

    fleet/runner-state.py --classify --final LINE --rc N --elapsed SEC --stop MARK --waited SEC --ticket KEY
    fleet/runner-state.py --pick-fail --runner N --note LINE --wip TEXT --ledger PATH
    fleet/runner-state.py --refs --repo DIR --ticket KEY
    fleet/runner-state.py --progress --repo DIR --before FILE --after FILE
    fleet/runner-state.py --self-test

An unknown state is a fault. flag approval is not a state. Waiting on a person is not a state.
Any other RUNNER IDLE line is WAIT_CHECK.
`RUNNER TOO HARD <KEY> | why: ...` is state TOO_HARD, the one valid leave a runner chooses itself (2026-11-13): fleet/park --too-hard
raises the ticket's brain tag one step and a stronger runner takes it. fleet/valid-leaves.json lists every valid leave; `leave_verdict`
reads it (bin/excess-run-watch and bin/heavy-tickets in poteto-2-advisor read the same file).
The launcher writes `state` on run-ledger.jsonl. fleet-watch reads that field.
"""
import json
import os
import re
import subprocess
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
    "TOO_HARD",
    "STOPPED",
    "FAULT",
)
# A ticket that keeps ending on its own waiting line is stuck after this much waiting, not before (HYCI-343): one PR's
# required checks on this repo take 20 to 60 minutes, so the 30-minute line turned every healthy wait into a FAULT and made the
# run counts and the factory breaker read waits as waste. The picker's wait gate caps a hold at the same 6 hours.
WAIT_LIMIT = 6 * 3600
TICKET = re.compile(r"\b((?:HTPR|HYFA|IGSH|SOFT|HYCI)-\d+)\b")
DONE = re.compile(r"\b(?:INFRA |CI )?RUNNER DONE\b")
HUMAN = re.compile(r"\bvalentin\b|flag approval", re.I)
WAIT = re.compile(r"ci-blocked|checks pending|awaiting checks|\bCI pending\b|\brecheck\b", re.I)
OWN = re.compile(r"\bOWN_PR\b|own PR", re.I)
PARKED_LINE = re.compile(r"(?:^|\s)PARKED\s+\S+")
TOO_HARD_LINE = re.compile(r"(?:^|\s)RUNNER TOO HARD\s+\S+")
STALL = re.compile(r"no model reply|reply cap|reply stalled", re.I)
TICKET_WAIT = re.compile(r"waits on|waiting on|parked on|BlockedBy", re.I)
# Live proof that needs Valentin's PC or the check phone, while it is off (IGSH-1923, IGSH-1925, HYCI-256, 11 Nov night).
PC_WAIT = re.compile(r"\b(?:desktops?|laptops?|PC|phone|computer|Windows)\b[^.;]{0,40}\b(?:disconnected|unavailable|unreachable|offline|cannot be reached)"
                     r"|\b(?:disconnected|unavailable|unreachable|offline)\b[^.;]{0,20}\b(?:desktops?|laptops?|PC|phone)\b", re.I)


# 14 Nov (HYCI-388, HTPR-9106 run 8): a run that pushed a PR fix ended, as the brief orders, on "RUNNER IDLE checks pending on PR 3468".
# That ending was counted as an invalid leave ("waited on checks") although the one-run hold (fleet/pick) and bin/pr-merger own that wait.
# While the one-run hold is live (one-run.on), a wait line that names a PR is tagged "script owns:", which valid-leaves.json skips.
ONE_RUN_FLAG = Path(os.environ.get("FLEET_ONE_RUN_FLAG", Path.home() / ".local/state/fleet/one-run.on"))
PR_WAIT = re.compile(r"\bPR\s*#?\d+\b", re.I)


def _wait_detail(line):
    """Detail of a WAIT_CHECK ending. A wait on a named PR while the one-run hold is live is a script's wait, not a runner's leave."""
    text = line[:160]
    if PR_WAIT.search(line) and ONE_RUN_FLAG.exists():
        return ("script owns: " + text)[:160]
    return text


def _out(state, result, park="", waits="", detail=""):
    if state not in STATES:
        raise RuntimeError(f"unlisted state {state}")
    return {"state": state, "result": result, "park": park, "waits": waits, "detail": detail[:500]}


ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
REDACTIONS = [
    (re.compile(r"\b(Bearer|Basic)\s+[A-Za-z0-9._~+/=-]{6,}", re.I), r"\1 [redacted]"),
    (re.compile(r"eyJ[A-Za-z0-9_-]{10,}(?:\.[A-Za-z0-9_-]+){0,2}"), "[redacted-jwt]"),
    (re.compile(r"\b(?:sk|pk|ghp|gho|ghs|github_pat|xox[a-z]|AKIA|op)[-_A-Za-z0-9]{12,}"), "[redacted-key]"),
    (re.compile(r"((?:api[_-]?key|token|secret|passw(?:or)?d|authorization|refresh_token|access_token)[\"']?\s*[:=]\s*[\"']?)[^\s\"',;]{4,}", re.I), r"\1[redacted]"),
    (re.compile(r"[A-Za-z0-9+/_=-]{40,}"), "[redacted-long]"),
]


def redact(text):
    """The saved tail of a failed run: no ANSI, no key-like strings, lines cut to 300 characters."""
    out = []
    for line in ANSI_RE.sub("", text).splitlines():
        for rx, sub in REDACTIONS:
            line = rx.sub(sub, line)
        out.append(line[:300])
    return "\n".join(out) + ("\n" if out else "")


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
    if TOO_HARD_LINE.search(line):
        return _out("TOO_HARD", "TOO_HARD", park="bump", detail=line[:300])
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
            return _out("FAULT", "FAULT", detail="WAIT_CHECK exceeded 6 h")
        return _out("WAIT_CHECK", "WAIT_CHECK", detail=_wait_detail(line))
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
            return _out("FAULT", "FAULT", detail="WAIT_CHECK exceeded 6 h")
        return _out("WAIT_CHECK", "WAIT_CHECK", detail=_wait_detail(line))
    if int(rc) == 124 or int(elapsed) >= 3 * 3600 - 10:
        return _out("FAULT", "FAIL", detail="timeout: hit the 3h run limit")
    if not line and (int(rc) != 0 or int(elapsed) < 120):
        if int(elapsed) < 120:
            return _out("FAULT", "FAIL", detail="crash or run ended before it started")
        return _out("FAULT", "FAIL", detail=f"run died mid-work: no final line after {int(elapsed)}s (rc {int(rc)})")
    if line:
        return _out("FAULT", "FAULT", park="lead", detail="unknown state")
    return _out("FAULT", "FAULT", park="lead", detail="unknown state")


VALID_LEAVES = Path(os.environ.get("FLEET_VALID_LEAVES", Path(__file__).resolve().with_name("valid-leaves.json")))


def leave_verdict(state, detail="", registry=None):
    """("skip" | "valid" | "invalid", id, label) for one run's ending, read from fleet/valid-leaves.json. A run that ended in a
    building state, an idle state or on a script-run wait is no leave at all (skip). The first valid leave whose states and detail
    pattern both match wins; every other ending is invalid, and from the ticket's second run on it wakes a fixer."""
    reg = registry if registry is not None else json.loads(VALID_LEAVES.read_text())
    low = (detail or "").lower()
    if state in reg["skip"] or (reg.get("skip_detail") and re.search(reg["skip_detail"], low)):
        return "skip", "", ""
    for v in reg["valid"]:
        if state in v["states"] and (not v.get("detail") or re.search(v["detail"], low)):
            return "valid", v["id"], v["label"]
    return "invalid", state.lower(), reg["invalid"].get(state, "Unlisted ending")


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


def ticket_refs(repo, ticket):
    """{branch: sha} for every local branch and origin branch whose name carries the ticket key (case blind). Cheap: one
    for-each-ref call. HYCI-343: a run that pushed commits and then waited for CI ended WAIT_CHECK and counted as empty;
    the launcher snapshots these before and after the run to write `progress`. The ticket key, not the runner number, ties
    a branch to a run: git identities on the runner checkouts do not match the ledger's runner numbers."""
    key = (ticket or "").lower()
    if not key:
        return {}
    r = subprocess.run(["git", "-C", repo, "for-each-ref", "--format=%(objectname) %(refname)", "refs/heads", "refs/remotes/origin"],
                       capture_output=True, text=True)
    out = {}
    for line in r.stdout.splitlines():
        sha, _, ref = line.partition(" ")
        name = re.sub(r"^refs/(?:heads|remotes/origin)/", "", ref)
        if key in name.lower() and name != "HEAD":
            out[name] = sha
    return out


def _count(repo, rev_range):
    r = subprocess.run(["git", "-C", repo, "rev-list", "--count", rev_range], capture_output=True, text=True)
    try:
        return int(r.stdout.strip())
    except ValueError:
        return None


def base_ref(repo):
    """The branch new work is measured against. hypertask's default branch is production; its origin/main is an old lineage,
    so every new ticket branch looked 8 or 9 commits ahead of it (HYCI-354, 13 Nov: a branch made at the tip of production,
    with no commit, counted progress 8)."""
    for ref in ("origin/production", "origin/main", "main"):
        if subprocess.run(["git", "-C", repo, "rev-parse", "--verify", "-q", ref], capture_output=True).returncode == 0:
            return ref
    return None


def progress_count(repo, before, after):
    """Commits pushed to branches named for the ticket, plus branches that went away, between two ticket_refs snapshots.
    A new branch counts its commits ahead of the base branch (capped at 50; 1 when the count cannot be read; 0 when the branch
    sits on the base with no commit). A moved branch counts the commits the move added, or 1 when history was rewritten.
    A removed branch counts 1 (the PR merged and its branch was deleted)."""
    total = 0
    base = base_ref(repo)
    for name, sha in after.items():
        old = before.get(name)
        if old == sha:
            continue
        if old is None:
            n = _count(repo, f"{base}..{sha}") if base else None
            total += 1 if n is None else min(n, 50)
        else:
            n = _count(repo, f"{old}..{sha}")
            total += min(max(n or 1, 1), 50)
    total += sum(1 for name in before if name not in after)
    return total


PR_URL = re.compile(r"https://github\.com/([\w.-]+/[\w.-]+)/pull/(\d+)")


def _epoch(iso):
    import datetime as dt
    return dt.datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()


def _pr_created(repo, num):
    r = subprocess.run(["gh", "api", f"repos/{repo}/pulls/{num}", "--jq", ".created_at"], capture_output=True, text=True, timeout=30)
    created = r.stdout.strip() if r.returncode == 0 else ""
    # A push to a PR the run did not open (SOFT-1952, 13 Nov: a CI fix on a PR from hours before) is progress too: the newest
    # commit time counts as well. Paginated: one line per page, ISO times sort as text.
    c = subprocess.run(["gh", "api", "--paginate", f"repos/{repo}/pulls/{num}/commits", "--jq", ".[-1].commit.committer.date"],
                       capture_output=True, text=True, timeout=30)
    last = max([x for x in c.stdout.split() if x] or [""]) if c.returncode == 0 else ""
    return max(created, last)


def pr_progress(text, since, created=_pr_created):
    """PRs the run's own output links that GitHub says were opened at or after `since` (epoch seconds), at most 3 looked up.
    progress_count only reads the repo the picker named, so a ticket built in another repo (HYCI-361, 13 Nov: a PR on
    yeoux-site) ended WAIT_CHECK with progress 0 and counted as an empty run: a false alarm for the canary fixer and the
    factory breaker. The run's final message names the PR it opened; the PR's own created_at proves it was this run's."""
    seen, n = set(), 0
    for repo, num in PR_URL.findall(text):
        if (repo, num) in seen or len(seen) >= 3:
            continue
        seen.add((repo, num))
        try:
            when = _epoch(created(repo, num))
        except (ValueError, subprocess.SubprocessError):
            continue
        if when >= since - 60:
            n += 1
    return n


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


PARK_WHY = re.compile(r"park|block|wait|\bred\b|fail|cannot|can't|nothing|untouched|already|duplicate|checks|ci\b|hand|slice|step", re.I)
PARK_NOISE = re.compile(r"^(?:parked [A-Z]+-\d+|detail |connection lost|retry attempt|chat listen|the (?:runner )?chat listener|gates:|blocker:|decisions?:|warning:)", re.I)
# the runner's own words after the key on the final line: `PARKED HTPR-2 why: the PR is red` (whitespace required, a glued suffix is not a reason)
PARKED_INLINE = re.compile(r"^PARKED\s+[A-Z]{2,6}-\d+\s+[|:\-]*\s*(?P<why>\S.*)$")


def park_reason(text, limit=160):
    """Why a run ended PARKED, in the model's own words (13 Nov: 28 PARKED rows, none with a reason, so nobody could say why).
    The text after the key on the final `PARKED KEY why` line, else the last line before it that reads like a reason, markdown
    stripped. Lines the harness prints (`Warning:` banners, listener and retry noise) are never the runner's reason, and a run with
    no words of its own gets "" (reason unset): HYCI-388, 13 Nov, SOFT-1966's reason was Claude's sign-in banner, HYCI-404's said
    "no reason written", and the next picker could not tell a real block from noise."""
    lines = [re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", l).strip() for l in (text or "").splitlines()]
    end = next((i for i in range(len(lines) - 1, -1, -1) if PARKED_LINE.search(lines[i]) and lines[i].startswith("PARKED")), None)
    if end is None:
        return ""
    inline = PARKED_INLINE.match(lines[end])
    if inline and not PARK_NOISE.match(inline["why"]):
        return re.sub(r"[*`#]+", "", inline["why"]).strip()[:limit]
    cleaned = []
    for l in lines[:end]:
        l = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", l)
        l = re.sub(r"[*`#]+", "", l)
        l = re.sub(r"^(?:[-+]|\d+\.)\s+", "", l).strip()
        if l and not PARK_NOISE.match(l):
            cleaned.append(l)
    cleaned = cleaned[-10:]
    if not cleaned:
        return ""
    why = next((l for l in reversed(cleaned) if PARK_WHY.search(l)), cleaned[-1])
    return why[:limit]


def self_test():
    log = ("\x1b[1mwork\x1b[0m\n- Boundary fix pushed. Nothing deployed.\n- Parked pending [CI repair](https://x/y/390).\n"
           "- Demo removal remains.\n\nPARKED SOFT-1\n")
    assert park_reason(log) == "Parked pending CI repair.", park_reason(log)
    assert park_reason("PARKED HTPR-1\n") == "", "a bare PARKED line leaves the reason unset (HYCI-404, 13 Nov)"
    assert park_reason("1. **Why:** the PR is red.\nConnection lost, reconnecting (attempt 1)...\nPARKED HTPR-2The chat listener stopped.\n") == "Why: the PR is red.", \
        "noise lines are skipped and a glued suffix on the PARKED line does not matter"
    assert park_reason("no final line here") == "", "no PARKED line: nothing to add"
    banner = ("Warning: this sign-in can end at any time from now until 2026-11-16. Renewing it does not move that date. "
              "Run claude auth login now, or use claude setup-token for unattended jobs.\nPARKED SOFT-1966\n")
    assert park_reason(banner) == "", "SOFT-1966 (13 Nov): the sign-in banner is not the runner's reason"
    assert park_reason("- the PR is red and I cannot fix it.\n" + banner) == "the PR is red and I cannot fix it.", "a real line before the banner still wins"
    assert park_reason("PARKED HTPR-3 why: **checks** red on PR 9") == "why: checks red on PR 9", "the runner's own text on the PARKED line is the reason"
    assert park_reason("PARKED HTPR-3 | waits on HYCI-9") == "waits on HYCI-9" and park_reason("PARKED HTPR-3The chat listener stopped.") == ""
    assert park_reason("PARKED HTPR-3 Warning: sign-in ends soon") == "", "a banner glued behind the key is still not a reason"
    assert len(park_reason("x" * 400 + " parked\nPARKED K-1")) == 160
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
    early = classify("", 1, 10, "", 0, "HYCI-1")
    assert "before it started" in early["detail"], "a run under 2 min keeps the early-death label"
    mid = classify("", 1, 1500, "", 0, "HYCI-1")
    assert mid["result"] == "FAIL" and "before it started" not in mid["detail"] and "1500s" in mid["detail"], "a long run that died is not 'before it started'"
    assert classify("RUNNER IDLE checks pending", 0, 400, "", 0, "HYCI-1", overload=True)["state"] == "WAIT_CHECK", \
        "a run that got its own final line keeps that ending"
    stall = classify("RUNNER IDLE no model reply for 600s twice, run ended", 124, 700, "", 0, "HYCI-1")
    assert stall["state"] == "FAULT" and stall["result"] == "FAIL" and "no model reply" in stall["detail"], stall
    assert stall["park"] == ""
    wait = classify("RUNNER IDLE ci-blocked HYCI-117", 0, 400, "", 10, "HYCI-1")
    assert wait["state"] == "WAIT_CHECK" and wait["park"] == ""
    late = classify("RUNNER IDLE checks pending", 0, 400, "", WAIT_LIMIT, "HYCI-1")
    assert late["state"] == "FAULT" and late["park"] == "" and "6 h" in late["detail"]
    healthy = classify("RUNNER IDLE checks pending", 0, 400, "", 40 * 60, "HYCI-1")
    assert healthy["state"] == "WAIT_CHECK", "a 40-minute check cycle is a wait, not a fault"
    parked = classify("RUNNER IDLE HYCI-160 BlockedBy HYCI-188", 0, 400, "", 0, "HYCI-160")
    assert parked["state"] == "PARKED" and parked["park"] == "waits" and parked["waits"] == "HYCI-188"
    assert classify("RUNNER IDLE driving own PR to live", 0, 400, "", 0, "HTPR-1")["state"] == "OWN_PR"
    assert classify("", 1, 10, "", 0, "HTPR-1")["result"] == "FAIL"
    idle_checks = classify("CI RUNNER IDLE PR 3074 checks", 0, 400, "", 0, "HYCI-182")
    assert idle_checks["state"] == "WAIT_CHECK" and idle_checks["park"] == "", idle_checks
    idle_review = classify("CI RUNNER IDLE HYCI-171 waiting Codex re-review and gate on 50020e7977", 0, 400, "", 0, "HYCI-171")
    assert idle_review["state"] == "WAIT_CHECK" and idle_review["park"] == "", idle_review
    assert classify("RUNNER IDLE something new", 0, 400, "", 0, "HTPR-1")["state"] == "WAIT_CHECK"
    import tempfile
    global ONE_RUN_FLAG
    saved_flag = ONE_RUN_FLAG
    with tempfile.TemporaryDirectory() as td:
        ONE_RUN_FLAG = Path(td) / "one-run.on"
        wline = "RUNNER IDLE checks pending on PR 3468 until 2026-11-14T00:19:00Z"
        off = classify(wline, 0, 1200, "", 0, "HTPR-9106")
        assert off["state"] == "WAIT_CHECK" and not off["detail"].startswith("script owns"), "one-run hold off: a plain wait"
        ONE_RUN_FLAG.write_text("")
        on = classify(wline, 0, 1200, "", 0, "HTPR-9106")
        assert on["state"] == "WAIT_CHECK" and on["detail"].startswith("script owns: "), on
        assert leave_verdict(on["state"], on["detail"], json.loads(VALID_LEAVES.read_text()))[0] == "skip", "a script-owned wait is no leave"
        nopr = classify("RUNNER IDLE checks pending", 0, 400, "", 0, "HYCI-1")
        assert not nopr["detail"].startswith("script owns"), "no PR named: still the runner's wait"
    ONE_RUN_FLAG = saved_flag
    pc = classify("RUNNER IDLE IGSH-1923 desktop disconnected; live proof pending", 0, 400, "", 0, "IGSH-1923")
    assert pc["state"] == "PARKED" and pc["park"] == "pc", pc
    assert classify("RUNNER IDLE IGSH-1925 live-proof unavailable; laptops disconnected", 0, 400, "", 0, "IGSH-1925")["park"] == "pc"
    assert classify("RUNNER IDLE HYCI-256 PC connection unavailable", 0, 400, "", 0, "HYCI-256")["park"] == "pc"
    assert classify("RUNNER IDLE Windows offline; live verification pending", 0, 400, "", 0, "IGSH-1")["park"] == "pc"
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
        classify("RUNNER TOO HARD HTPR-7 | why: touches billing and auth together", 0, 500, "", 0, "HTPR-7"),
    ]
    assert {row["state"] for row in day} == set(STATES), sorted(row["state"] for row in day)
    assert all(row["state"] in STATES for row in day)
    hard = classify("RUNNER TOO HARD HTPR-7 | why: touches billing and auth together", 0, 500, "", 0, "HTPR-7")
    assert hard["state"] == "TOO_HARD" and hard["park"] == "bump" and "billing" in hard["detail"], hard
    assert classify("CI RUNNER TOO HARD HYCI-7 | why: needs a stronger model", 0, 500, "", 0, "HYCI-7")["state"] == "TOO_HARD"
    assert classify("RUNNER IDLE too hard", 0, 500, "", 0, "HYCI-7")["state"] == "WAIT_CHECK", "only the listed line is the valid leave"
    reg = json.loads(VALID_LEAVES.read_text())
    v = lambda state, detail="": leave_verdict(state, detail, reg)[:2]
    assert v("BUILDING") == ("skip", "") and v("IDLE_CAP") == ("skip", ""), "building and idle endings are no leave"
    assert v("WAIT_CHECK", "sf-wait: SOFT-1 pr: PR open") == ("skip", ""), "a script-run wait is no leave"
    assert v("WAIT_CHECK", "RUNNER IDLE checks pending") == ("invalid", "wait_check"), "waited on checks is invalid"
    assert v("PARKED", "PARKED HTPR-1 | why: Checks running. Not live yet.") == ("invalid", "parked")
    assert v("FAULT", "unknown state") == ("invalid", "fault") and v("FAULT", "crash or run ended before it started") == ("invalid", "fault")
    assert v("TOO_HARD", "RUNNER TOO HARD HTPR-7 | why: x") == ("valid", "too_hard")
    assert v("PROVIDER_BUSY", "provider busy: the inference service is overloaded") == ("valid", "provider")
    assert v("FAULT", "API error 503 from the provider") == ("valid", "provider"), "a 5xx is the provider, not the runner"
    assert v("WAIT_CHECK", "CI RUNNER IDLE HYCI-226 pr-title MCP 502 recheck 08:05 UTC") == ("invalid", "wait_check"), "a number is not an outage"
    assert v("PARKED", "RUNNER IDLE HTPR-9105 parked waiting on HTPR-9106 (same 504 timeout fix)") == ("invalid", "parked")
    assert v("FAULT", "HTTP 529 overloaded") == ("valid", "provider") and v("FAULT", "status: 503") == ("valid", "provider")
    assert v("PARKED", "PARKED HTPR-2 | why: Valentin Review plus one Question; money") == ("valid", "valentin")
    assert v("STOPPED", "removed from the roster") == ("valid", "removed") and v("STOPPED", "manual") == ("invalid", "stopped")
    assert set(reg["invalid"]) <= set(STATES) and set(reg["skip"]) <= set(STATES), "the registry names listed states only"
    assert all(s in STATES for x in reg["valid"] for s in x["states"])
    dirty = "\x1b[31mErr 401\x1b[0m\nAuthorization: Bearer abcDEF123456789xyz\nsecret=hunter2hunter2\nk sk-abcdefghijklmnop1234\njwt eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.sig\n"
    clean = redact(dirty)
    assert "Err 401" in clean and "\x1b" not in clean, clean
    for leak in ("abcDEF123456789xyz", "hunter2hunter2", "sk-abcdefghijklmnop1234", "eyJhbGci"):
        assert leak not in clean, (leak, clean)
    runner = Path(__file__).with_name("runner").read_text()
    assert 'grep -q "RUNNER IDLE"' not in runner
    assert "unknown state" in runner and "flag approval" in runner
    import tempfile
    tmp = tempfile.mkdtemp()
    git = lambda *a: subprocess.run(["git", "-C", tmp, "-c", "user.email=t@t", "-c", "user.name=t", *a], capture_output=True, text=True, check=True)
    git("init", "-q", "-b", "main")
    Path(tmp, "f").write_text("a")
    git("add", "f")
    git("commit", "-q", "-m", "base")
    git("update-ref", "refs/remotes/origin/main", "HEAD")
    key = "HYCI-77"
    before = ticket_refs(tmp, key)
    assert before == {} and progress_count(tmp, before, ticket_refs(tmp, key)) == 0, "no branch, no progress"
    git("checkout", "-q", "-b", "runner-3/hyci-77-fix")
    for i in range(2):
        Path(tmp, "f").write_text(f"b{i}")
        git("commit", "-q", "-am", f"c{i}")
    git("checkout", "-q", "-b", "runner-3/htpr-1-other")
    Path(tmp, "f").write_text("z")
    git("commit", "-q", "-am", "other ticket")
    after = ticket_refs(tmp, key)
    assert set(after) == {"runner-3/hyci-77-fix"}, after
    assert progress_count(tmp, before, after) == 2, "a new branch counts its commits ahead of origin/main"
    # default branch production: origin/main is an old lineage, so work is measured against origin/production
    git("checkout", "-q", "--orphan", "oldmain")
    Path(tmp, "f").write_text("old")
    git("commit", "-q", "-am", "old lineage")
    git("update-ref", "refs/remotes/origin/main", "oldmain")
    git("update-ref", "refs/remotes/origin/production", "main")
    git("branch", "-q", "runner-3/hyci-78-idle", "main")
    assert progress_count(tmp, {}, {"runner-3/hyci-78-idle": "main"}) == 0, "a new branch at the tip of production pushed nothing"
    assert progress_count(tmp, {}, ticket_refs(tmp, key)) == 2, "two commits ahead of production"
    git("update-ref", "-d", "refs/remotes/origin/production")
    git("update-ref", "refs/remotes/origin/main", "main")
    git("checkout", "-q", "-f", "runner-3/htpr-1-other")
    git("branch", "-q", "-D", "oldmain", "runner-3/hyci-78-idle")
    assert progress_count(tmp, after, after) == 0, "nothing moved: no progress, a run that only waited"
    git("checkout", "-q", "runner-3/hyci-77-fix")
    Path(tmp, "f").write_text("c")
    git("commit", "-q", "-am", "c2")
    assert progress_count(tmp, after, ticket_refs(tmp, key)) == 1, "one more commit on the branch"
    fake = {("o/r", "26"): "2026-11-13T11:27:59Z", ("o/r", "9"): "2026-11-13T09:00:00Z"}
    look = lambda repo, num: fake.get((repo, num), "")
    since = _epoch("2026-11-13T11:11:37Z")
    assert pr_progress("[PR](https://github.com/o/r/pull/26) x", since, look) == 1, "a PR opened during the run is progress"
    fake[("o/r", "30")] = "2026-11-13T11:30:00Z"  # an older PR whose newest commit landed during the run: _pr_created returns the later time
    assert pr_progress("see https://github.com/o/r/pull/30", since, look) == 1, "a push to an existing PR is progress"
    assert pr_progress("see https://github.com/o/r/pull/9", since, look) == 0, "an older PR is not this run's"
    assert pr_progress("no link, or https://github.com/o/r/pull/77", since, look) == 0, "an unknown PR counts nothing"
    git("checkout", "-q", "main")
    git("branch", "-q", "-D", "runner-3/hyci-77-fix")
    assert progress_count(tmp, ticket_refs(tmp, key) or {"runner-3/hyci-77-fix": "x"}, {}) == 1, "a removed branch counts one"
    assert ticket_refs(tmp, "") == {} and ticket_refs("/nonexistent", key) == {}
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
    if "--refs" in sys.argv:
        for name, sha in sorted(ticket_refs(_arg("--repo"), _arg("--ticket")).items()):
            print(f"{sha} {name}")
        return
    if "--progress" in sys.argv:
        def snap(path):
            try:
                return {l.split(" ", 1)[1]: l.split(" ", 1)[0] for l in Path(path).read_text().splitlines() if " " in l}
            except OSError:
                return {}
        print(progress_count(_arg("--repo"), snap(_arg("--before")), snap(_arg("--after"))))
        return
    if "--pr-progress" in sys.argv:
        try:
            body = Path(_arg("--log")).read_text(errors="replace")
        except OSError:
            body = ""
        print(pr_progress(re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", body), float(_arg("--since", "0") or 0)))
        return
    if "--park-reason" in sys.argv:
        try:
            body = Path(_arg("--log")).read_text(errors="replace")
        except OSError:
            body = ""
        print(park_reason(body))
        return
    if "--redact" in sys.argv:
        sys.stdout.write(redact(sys.stdin.read()))
        return
    if "--classify" in sys.argv:
        row = classify(_arg("--final"), int(_arg("--rc", "0")), int(_arg("--elapsed", "0")),
                       _arg("--stop"), int(_arg("--waited", "0")), _arg("--ticket"),
                       overload=_arg("--overload", "0") == "1")
        print(json.dumps(row))
        return
    sys.exit("usage: fleet/runner-state.py --classify | --pick-fail | --refs | --progress | --park-reason | --redact | --self-test")


if __name__ == "__main__":
    main()
