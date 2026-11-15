#!/usr/bin/env python3
"""Live plan usage for spawn-worker. One reading per family, called in-process.

Spawn-worker ranks on this shape and nothing else:

    used_pct     percent of the limiting window already used, or None
    pace_ratio   used share / share of the window elapsed, or None
    hours_left   hours until that window resets, or None
    resets_at    unix time of that reset, or None
    state        "ON", "WARN", "OFF", or "unknown"

"unknown" means there are no numbers. Pace is None when under 10% of the window
has elapsed; spawn-worker ranks by used_pct and resets_at, not pace. OFF is 95%
used on either window. WARN is 80% used, or used running ahead of the window
once 80% of it has elapsed.

Claude, Codex and Grok are read live. Grok is Cursor's current billing
period: the interactive /usage command calls GetCurrentPeriodUsage, and there
is no usage subcommand. This reader makes that same call with the stored
Cursor login. The login is never logged or returned.
Account emails, client names and ssh hosts are not stored here. When
~/.config/plan-usage/accounts.json exists, credential and session paths are
read from it. config/plan-usage.example.json shows the shape with example.invalid.

PLAN_USAGE_FIXTURE, when set, is a JSON file of finished readings for tests.
Leave it unset outside tests.

`plan_usage.py alert` posts to ntfy when a family runs ahead of pace, or when
used_pct crosses 80 or 95. Claude's pace line is 1.15. Codex and Grok use 1.3.
One push per family per two hours. A Fable model that made more than 30% of
the last hour of Claude calls is a separate push and names its three busiest
chats. State is kept in ~/.local/state/plan-usage/. NTFY_TOPIC overrides the
topic. The command never prints a token.
"""
import fcntl
import glob
import json
import math
import os
import re
import selectors
import signal
import subprocess
import sys
import time
import urllib.request
from datetime import datetime

POOL_WARN_PCT = 80
POOL_OFF_PCT = 95
CLAUDE_FIVE_HOUR_OFF_PCT = 95
PACE_MIN_ELAPSED_PCT = 10
WEEK_MINUTES = 10080
FIVE_HOUR_MINUTES = 300
ACCOUNTS_PATH = os.path.expanduser("~/.config/plan-usage/accounts.json")


class UsageError(Exception):
    """The readings file or the accounts file cannot be used. Never carries a secret."""


def unknown_pool():
    return {"used_pct": None, "hours_left": None, "resets_at": None,
            "state": "unknown", "pace_ratio": None}


def iso_to_ts(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()


def window(used, resets_at, minutes, now):
    """One usage bar. used is a percent. resets_at is unix time."""
    if used is None or resets_at is None:
        return {"used": None, "resets_at": None, "hours_left": None, "time_gone": None}
    if resets_at <= now:
        used, resets_at = 0.0, resets_at + minutes * 60
    hours_left = (resets_at - now) / 3600
    time_gone = max(0.0, min(100.0, 100 * (1 - hours_left * 60 / minutes)))
    return {"used": round(used, 1), "resets_at": resets_at, "hours_left": round(hours_left, 1),
            "time_gone": round(time_gone, 1)}


def pace_of(bar):
    """used / time_gone, the same ratio the old pools command published."""
    used, gone = bar.get("used"), bar.get("time_gone")
    if type(used) not in (int, float) or not math.isfinite(used) or not 0 <= used <= 100:
        return None
    if type(gone) in (int, float) and math.isfinite(gone) and 0 < gone <= 100:
        return round(used / gone, 4)
    return None


def pool_state(week, five_hour, now, five_hour_off_pct=None):
    """The limiting window for one family. No numbers means unknown."""
    windows, short_capped = [], False
    for bar, minutes in ((week, WEEK_MINUTES), (five_hour, FIVE_HOUR_MINUTES)):
        bar = dict(bar or {})
        reset = bar.get("resets_at")
        if reset is not None:
            if reset <= now:
                period = minutes * 60
                bar = window(0, reset + (int((now - reset) // period) + 1) * period, minutes, now)
            else:
                bar["hours_left"] = round((reset - now) / 3600, 1)
                if bar.get("time_gone") is not None:
                    bar["time_gone"] = max(0, min(100, 100 * (1 - (reset - now) / (minutes * 60))))
        if bar.get("used") is not None:
            windows.append(bar)
            if minutes == FIVE_HOUR_MINUTES and five_hour_off_pct is not None and bar["used"] >= five_hour_off_pct:
                short_capped = True
    if not windows:
        return unknown_pool()
    state = "ON"
    if short_capped or any(bar["used"] >= POOL_OFF_PCT for bar in windows):
        state = "OFF"
    elif any(bar["used"] >= POOL_WARN_PCT or ((bar.get("time_gone") or 0) >= POOL_WARN_PCT and
                                              bar["used"] >= bar["time_gone"]) for bar in windows):
        state = "WARN"
    limiting = max(windows, key=lambda bar: bar["used"])
    ratios = [pace_of(bar) for bar in windows
              if (bar.get("time_gone") or 0) >= PACE_MIN_ELAPSED_PCT]
    return {"used_pct": limiting["used"], "hours_left": limiting.get("hours_left"),
            "resets_at": limiting.get("resets_at"), "state": state,
            "pace_ratio": max((ratio for ratio in ratios if ratio is not None), default=None)}


def pool_from_bars(name, raw, now):
    if not isinstance(raw, dict):
        return unknown_pool()
    five_off = CLAUDE_FIVE_HOUR_OFF_PCT if name == "claude" else None
    return pool_state(raw.get("week"), raw.get("five_hour"), now, five_off)


def derive(readings, now):
    if not isinstance(readings, dict):
        raise UsageError("usage readings must be a JSON object")
    return {
        "claude": pool_from_bars("claude", readings.get("claude"), now),
        "codex": pool_from_bars("codex", readings.get("codex"), now),
        "grok": pool_from_bars("grok", readings.get("grok"), now),
    }


def load_accounts():
    if not os.path.exists(ACCOUNTS_PATH):
        return {}
    try:
        with open(ACCOUNTS_PATH) as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        raise UsageError("accounts file is not valid JSON")
    if not isinstance(data, dict):
        raise UsageError("accounts file must be a JSON object")
    return data


def account_section(accounts, name):
    section = accounts.get(name) if isinstance(accounts, dict) else None
    return section if isinstance(section, dict) else {}


def read_claude(now, accounts):
    path = os.path.expanduser(
        account_section(accounts, "claude").get("credentials") or "~/.claude/.credentials.json")
    try:
        with open(path) as handle:
            token = json.load(handle)["claudeAiOauth"]["accessToken"]
        request = urllib.request.Request(
            "https://api.anthropic.com/api/oauth/usage",
            headers={"Authorization": "Bearer " + token,
                     "anthropic-beta": "oauth-2025-04-20"})
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.load(response)
        five_hour = payload.get("five_hour") or {}
        week = payload.get("seven_day") or {}
        return {
            "five_hour": window(five_hour.get("utilization"),
                                five_hour.get("resets_at") and iso_to_ts(five_hour["resets_at"]),
                                FIVE_HOUR_MINUTES, now),
            "week": window(week.get("utilization"),
                           week.get("resets_at") and iso_to_ts(week["resets_at"]),
                           WEEK_MINUTES, now),
        }
    except Exception:
        return None


def _find_key(obj, key):
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for value in obj.values():
            found = _find_key(value, key)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for value in obj:
            found = _find_key(value, key)
            if found is not None:
                return found
    return None


def read_codex_logs(sessions):
    """Newest rate_limits sample by the event timestamp, not by file mtime.

    Several sessions write at once, so the newest file can hold an older sample.
    """
    files = sorted(glob.glob(os.path.join(sessions, "*/*/*/*.jsonl")),
                   key=os.path.getmtime, reverse=True)
    best = None
    for path in files[:40]:
        try:
            with open(path, "rb") as handle:
                handle.seek(max(0, os.path.getsize(path) - 400_000))
                tail = handle.read().decode("utf-8", "ignore").splitlines()
        except OSError:
            continue
        for line in reversed(tail):
            if '"rate_limits"' not in line:
                continue
            try:
                event = json.loads(line)
                limits = _find_key(event, "rate_limits")
                stamp = iso_to_ts(event["timestamp"])
            except (ValueError, KeyError, TypeError, AttributeError):
                continue
            if not isinstance(limits, dict) or not any(limits.get(slot) for slot in ("primary", "secondary")):
                continue
            if best is None or stamp > best[0]:
                best = (stamp, limits)
            break
    return best


def parse_codex_response(response):
    """Normalize account/rateLimits/read. Ignore unrelated per-model pools."""
    if not isinstance(response, dict) or response.get("error") is not None:
        raise ValueError("rate limits request failed")
    result = response.get("result") or {}
    if not isinstance(result, dict):
        raise ValueError("invalid Codex response")
    many = result.get("rateLimitsByLimitId") or {}
    if not isinstance(many, dict):
        raise ValueError("invalid Codex limits map")
    limits = many.get("codex") or result.get("rateLimits") or {}
    if not isinstance(limits, dict) or limits.get("limitId") not in (None, "codex"):
        raise ValueError("no Codex rate limits")
    out = {}
    for slot in ("primary", "secondary"):
        bar = limits.get(slot)
        if not isinstance(bar, dict):
            continue
        values = [bar.get(key) for key in ("usedPercent", "resetsAt", "windowDurationMins")]
        if not all(type(value) in (int, float) and math.isfinite(value) for value in values) or values[2] <= 0:
            raise ValueError("invalid Codex window")
        out[slot] = dict(zip(("used_percent", "resets_at", "window_minutes"), values))
    if not any(out.get(slot) for slot in ("primary", "secondary")):
        raise ValueError("no Codex rate limits")
    return out


def probe_codex(timeout=20):
    """Read account limits without starting a thread or making a model call."""
    deadline = time.monotonic() + timeout
    with subprocess.Popen(
            ["codex", "app-server", "--listen", "stdio://"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            start_new_session=True) as proc:
        try:
            def send(message):
                proc.stdin.write((json.dumps(message) + "\n").encode())
                proc.stdin.flush()

            send({"method": "initialize", "id": 1, "params": {
                "clientInfo": {"name": "plan_usage", "title": "Plan usage", "version": "1"}}})
            with selectors.DefaultSelector() as selector:
                selector.register(proc.stdout, selectors.EVENT_READ)
                pending, initialized, received = b"", False, 0
                while True:
                    left = deadline - time.monotonic()
                    if left <= 0 or not selector.select(left):
                        raise TimeoutError("Codex probe timed out")
                    chunk = os.read(proc.stdout.fileno(), 65536)
                    if not chunk:
                        raise ValueError("Codex app-server closed")
                    received += len(chunk)
                    if received > 1_000_000:
                        raise ValueError("Codex response too large")
                    pending += chunk
                    while b"\n" in pending:
                        line, pending = pending.split(b"\n", 1)
                        try:
                            message = json.loads(line)
                        except ValueError:
                            continue
                        if not isinstance(message, dict):
                            continue
                        if message.get("id") == 1 and not initialized:
                            if message.get("error") is not None:
                                raise ValueError("Codex initialize failed")
                            initialized = True
                            send({"method": "initialized", "params": {}})
                            send({"method": "account/rateLimits/read", "id": 2})
                        elif message.get("id") == 2 and initialized:
                            return time.time(), parse_codex_response(message)
        finally:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            proc.wait()


def codex_window(bar):
    """One Codex window, whether the log used snake_case or the API used camelCase."""
    if not isinstance(bar, dict):
        return None
    if "window_minutes" in bar or "used_percent" in bar:
        used, reset, minutes = bar.get("used_percent"), bar.get("resets_at"), bar.get("window_minutes")
    else:
        used, reset, minutes = bar.get("usedPercent"), bar.get("resetsAt"), bar.get("windowDurationMins")
    if not all(type(value) in (int, float) and math.isfinite(value) for value in (used, reset, minutes)):
        return None
    if minutes <= 0:
        return None
    return {"used_percent": used, "resets_at": reset, "window_minutes": minutes}


def read_codex(now, accounts):
    sessions = os.path.expanduser(
        account_section(accounts, "codex").get("sessions") or "~/.codex/sessions")
    try:
        best = read_codex_logs(sessions)
        if best is None or now - best[0] >= 600:
            try:
                probe = probe_codex()
                if best is None or probe[0] > best[0]:
                    best = probe
            except (OSError, ValueError, TypeError, AttributeError):
                if best is None:
                    return None
        if not best:
            return None
        _stamp, limits = best
        out = {}
        for slot in ("primary", "secondary"):
            bar = codex_window(limits.get(slot) if isinstance(limits, dict) else None)
            if not bar:
                continue
            minutes = bar["window_minutes"]
            key = "week" if minutes >= 1440 else "five_hour"
            out[key] = window(bar["used_percent"], bar["resets_at"], minutes, now)
        return out or None
    except Exception:
        return None


def cursor_auth_path(accounts):
    """Where the Cursor CLI stores its login. Same paths as getAuthFilePath."""
    override = account_section(accounts, "grok").get("credentials")
    if isinstance(override, str) and override:
        return os.path.expanduser(override)
    home = os.path.expanduser("~")
    if os.name == "nt":
        base = os.environ.get("APPDATA") or os.path.join(home, "AppData", "Roaming")
        return os.path.join(base, "Cursor", "auth.json")
    if sys.platform == "darwin":
        return os.path.join(home, ".cursor", "auth.json")
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(home, ".config")
    return os.path.join(base, "cursor", "auth.json")


def _epoch_seconds(value):
    """Proto JSON sends int64 timestamps as millisecond strings."""
    if isinstance(value, str) and value.lstrip("-").isdigit():
        value = int(value)
    if type(value) not in (int, float) or not math.isfinite(value):
        return None
    if abs(value) > 10_000_000_000:
        value = value / 1000.0
    return value


def grok_percent(plan):
    """Included-usage percent, the number the /usage screen prints."""
    if not isinstance(plan, dict):
        return None
    percent = plan.get("totalPercentUsed", plan.get("total_percent_used"))
    if type(percent) in (int, float) and math.isfinite(percent):
        return percent
    used = plan.get("includedSpend", plan.get("included_spend"))
    limit = plan.get("limit")
    if type(used) in (int, float) and type(limit) in (int, float) and math.isfinite(used) and limit > 0:
        return used / limit * 100.0
    return None


def parse_grok_response(payload, now):
    """One Cursor billing period. The live period is 7 days, so it is the week bar."""
    if not isinstance(payload, dict):
        return None
    plan = payload.get("planUsage") or payload.get("plan_usage")
    used = grok_percent(plan)
    resets_at = _epoch_seconds(payload.get("billingCycleEnd", payload.get("billing_cycle_end")))
    if used is None or resets_at is None:
        return None
    return {"week": window(used, resets_at, WEEK_MINUTES, now)}


def read_grok(now, accounts):
    path = cursor_auth_path(accounts)
    try:
        with open(path) as handle:
            token = json.load(handle).get("accessToken")
        if not isinstance(token, str) or not token:
            return None
        base = os.environ.get("CURSOR_API_ENDPOINT") or "https://api2.cursor.sh"
        request = urllib.request.Request(
            base.rstrip("/") + "/aiserver.v1.DashboardService/GetCurrentPeriodUsage",
            data=b"{}",
            method="POST",
            headers={
                "Authorization": "Bearer " + token,
                "Content-Type": "application/json",
            })
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.load(response)
        return parse_grok_response(payload, now)
    except Exception:
        return None


def live_readings(now):
    accounts = load_accounts()
    return {
        "claude": read_claude(now, accounts),
        "codex": read_codex(now, accounts),
        "grok": read_grok(now, accounts),
    }


def load_fixture(path):
    try:
        with open(path) as handle:
            data = json.load(handle)
    except OSError as exc:
        raise UsageError(f"cannot read usage fixture: {exc.strerror or exc}")
    except ValueError:
        raise UsageError("usage fixture is not valid JSON")
    if not isinstance(data, dict):
        raise UsageError("usage fixture must be a JSON object")
    return data


def pools(now=None, readings=None):
    """Finished readings for claude, codex and grok.

    readings, when passed, are raw week and five_hour bars. Tests use that.
    PLAN_USAGE_FIXTURE is a finished reading and is returned as-is.
    """
    now = time.time() if now is None else now
    if readings is not None:
        return derive(readings, now)
    fixture = os.environ.get("PLAN_USAGE_FIXTURE")
    if fixture:
        return load_fixture(fixture)
    return derive(live_readings(now), now)


ALERT_FAMILIES = ("claude", "codex", "grok")
PACE_OVER = {"claude": 1.15}
PACE_OVER_DEFAULT = 1.3
USED_MARKS = (80, 95)
ALERT_GAP = 7200
FABLE_SHARE = 0.30
DEFAULT_STATE_DIR = os.path.expanduser("~/.local/state/plan-usage")
DEFAULT_NTFY_TOPIC = "valentin-vps-pKVwzApRPTep"
CLAUDE_PROJECTS = os.path.expanduser("~/.claude/projects")
TOPIC_NAME = re.compile(r"[A-Za-z0-9_-]{1,64}")


def number(value):
    return type(value) in (int, float) and math.isfinite(value)


def pace_limit(family):
    return PACE_OVER.get(family, PACE_OVER_DEFAULT)


def family_reasons(family, reading, prev):
    reading = reading or {}
    prev = prev or {}
    reasons = []
    pace = reading.get("pace_ratio")
    used = reading.get("used_pct")
    if number(pace) and pace > pace_limit(family):
        reasons.append({"kind": "pace", "pace": pace})
    prev_used = prev.get("used_pct")
    if number(used):
        for mark in USED_MARKS:
            if used >= mark and not (number(prev_used) and prev_used >= mark):
                reasons.append({"kind": "used", "mark": mark})
    return reasons


def merge_pending(pending, crosses, used):
    """Keep a crossing that landed inside the quiet period.

    The stored used percent would hide it on the next run, so the 95% mark
    would never send if it was crossed within two hours of the 80% push.
    A mark already fallen back under is dropped.
    """
    kept, seen = [], set()
    items = pending if isinstance(pending, list) else []
    for reason in items + list(crosses):
        if not isinstance(reason, dict) or reason.get("kind") != "used":
            continue
        mark = reason.get("mark")
        if mark not in USED_MARKS or mark in seen:
            continue
        if number(used) and used < mark:
            continue
        seen.add(mark)
        kept.append({"kind": "used", "mark": mark})
    return kept


def format_family(family, reasons, used):
    name = family.capitalize()
    parts = []
    paces = [reason["pace"] for reason in reasons if reason["kind"] == "pace"]
    if paces:
        parts.append(f"{name} is burning at {max(paces):.2f}x its pace.")
    marks = [reason["mark"] for reason in reasons if reason["kind"] == "used"]
    if marks:
        shown = " and ".join(f"{mark}%" for mark in marks)
        used_bit = f" ({used:.0f}% used)" if number(used) else ""
        parts.append(f"{name} crossed {shown}{used_bit}.")
    return " ".join(parts)


def evaluate_family(family, reading, prev, now):
    prev = prev if isinstance(prev, dict) else {}
    reading = reading if isinstance(reading, dict) else {}
    used = reading.get("used_pct")
    stored_used = used if number(used) else prev.get("used_pct")
    fresh = family_reasons(family, reading, prev)
    crosses = [reason for reason in fresh if reason["kind"] == "used"]
    pace = [reason for reason in fresh if reason["kind"] == "pace"]
    pending = merge_pending(prev.get("pending"), crosses, stored_used)
    sent_at = prev.get("sent_at") if number(prev.get("sent_at")) else 0
    quiet = {"used_pct": stored_used, "sent_at": sent_at, "pending": pending}
    due = pending + pace
    if not due or now - sent_at < ALERT_GAP:
        return None, quiet, quiet
    message = {"family": family, "title": "Plan burning too fast",
               "body": format_family(family, due, stored_used)}
    sent = {"used_pct": stored_used, "sent_at": now, "pending": []}
    return message, quiet, sent


def is_fable(model):
    return isinstance(model, str) and "fable" in model.lower()


def fable_burn(calls):
    """The Fable model, if any, that made more than 30% of these calls."""
    if not calls:
        return None
    by_model = {}
    for model, chat in calls:
        if not isinstance(model, str) or not isinstance(chat, str):
            continue
        chats = by_model.setdefault(model, {})
        chats[chat] = chats.get(chat, 0) + 1
    best = None
    counted = sum(sum(chats.values()) for chats in by_model.values())
    if not counted:
        return None
    for model, chats in by_model.items():
        if not is_fable(model):
            continue
        count = sum(chats.values())
        if count / counted <= FABLE_SHARE:
            continue
        if best is not None and count <= best["count"]:
            continue
        top = sorted(chats.items(), key=lambda item: (-item[1], item[0]))[:3]
        best = {"count": count, "total": counted, "chats": top}
    return best


def evaluate_fable(calls, prev, now):
    prev = prev if isinstance(prev, dict) else {}
    sent_at = prev.get("sent_at") if number(prev.get("sent_at")) else 0
    quiet = {"sent_at": sent_at}
    burn = fable_burn(calls)
    if burn is None or now - sent_at < ALERT_GAP:
        return None, quiet, quiet
    pct = 100 * burn["count"] / burn["total"]
    chats = ", ".join(f"{label} ({count})" for label, count in burn["chats"])
    body = (f"Fable made {pct:.0f}% of Claude calls in the last hour "
            f"({burn['count']} of {burn['total']}). Top Fable chats: {chats}.")
    return {"family": "fable", "title": "Fable is burning Claude", "body": body}, quiet, {"sent_at": now}


def plain(text, limit):
    return "".join(ch for ch in text if ch.isprintable())[:limit].strip()


def chat_label(entry, path):
    cwd = entry.get("cwd")
    project = os.path.basename(cwd) if isinstance(cwd, str) else ""
    slug = entry.get("slug")
    if isinstance(slug, str) and slug.strip():
        name = slug.strip()
    else:
        session = entry.get("sessionId")
        if isinstance(session, str) and session.strip():
            name = session.strip()[:8]
        else:
            name = os.path.splitext(os.path.basename(path))[0][:8]
    name, project = plain(name, 60), plain(project, 40)
    if project and name:
        return f"{project}: {name}"
    return name or project or "chat"


def assistant_model(entry):
    message = entry.get("message")
    if isinstance(message, dict):
        model = message.get("model")
        if isinstance(model, str) and model:
            return model
    model = entry.get("model")
    return model if isinstance(model, str) and model else None


def call_from_line(line, path, since, now):
    if '"assistant"' not in line or '"model"' not in line:
        return None, None
    try:
        entry = json.loads(line)
    except ValueError:
        return None, None
    if not isinstance(entry, dict) or entry.get("type") != "assistant":
        return None, None
    stamp = entry.get("timestamp")
    if not isinstance(stamp, str):
        return None, None
    try:
        ts = iso_to_ts(stamp)
    except (ValueError, TypeError, AttributeError):
        return None, None
    if not since <= ts <= now:
        return ts, None
    model = assistant_model(entry)
    if not model:
        return ts, None
    return ts, (model, chat_label(entry, path))


def recent_calls(path, since, now, chunk=8_000_000):
    """Assistant calls with since <= timestamp <= now, reading from the end."""
    try:
        handle = open(path, "rb")
    except OSError:
        return []
    calls = []
    with handle:
        pos = os.fstat(handle.fileno()).st_size
        suffix = ""
        while pos > 0:
            take = min(chunk, pos)
            pos -= take
            handle.seek(pos)
            text = handle.read(take).decode("utf-8", "ignore") + suffix
            parts = text.split("\n")
            if pos > 0:
                suffix = parts[0]
                parts = parts[1:]
            else:
                suffix = ""
            oldest, found = None, []
            for line in parts:
                ts, call = call_from_line(line, path, since, now)
                if ts is None:
                    continue
                oldest = ts if oldest is None else min(oldest, ts)
                if call is not None:
                    found.append(call)
            calls = found + calls
            if oldest is not None and oldest <= since:
                break
    return calls


def scan_calls(root, now, hour=3600):
    since = now - hour
    calls = []
    if not root:
        return calls
    for path in glob.glob(os.path.join(root, "*", "*.jsonl")):
        try:
            if os.path.getmtime(path) < since:
                continue
        except OSError:
            continue
        calls.extend(recent_calls(path, since, now))
    return calls


def load_state(path):
    try:
        with open(path) as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def save_state(path, data):
    temporary = path + ".tmp"
    with open(temporary, "w") as handle:
        json.dump(data, handle, indent=2)
        handle.write("\n")
    os.chmod(temporary, 0o600)
    os.replace(temporary, path)


def send_ntfy(message):
    topic = os.environ.get("NTFY_TOPIC") or DEFAULT_NTFY_TOPIC
    if not TOPIC_NAME.fullmatch(topic or ""):
        raise UsageError("NTFY_TOPIC is not a single topic name")
    title = message["title"].replace("\r", " ").replace("\n", " ")
    request = urllib.request.Request(
        "https://ntfy.sh/" + topic,
        data=message["body"].encode("utf-8"),
        method="POST",
        headers={"Title": title, "Priority": "high", "Content-Type": "text/plain; charset=utf-8"})
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            response.read()
    except Exception:
        raise OSError("ntfy push failed") from None


def alert(now=None, readings=None, state_dir=None, send=None, projects_root=None, calls=None):
    """Post due warnings. `calls` skips the transcript scan. Returns pushes that landed."""
    now = time.time() if now is None else now
    state_dir = state_dir or os.environ.get("PLAN_USAGE_STATE_DIR") or DEFAULT_STATE_DIR
    deliver = send or send_ntfy
    if calls is None:
        calls = scan_calls(projects_root or CLAUDE_PROJECTS, now)
    usage = pools(now=now, readings=readings)
    try:
        os.makedirs(state_dir, mode=0o700, exist_ok=True)
    except OSError:
        raise UsageError("cannot create alert state directory") from None
    delivered = []
    state_path = os.path.join(state_dir, "alerts.json")
    with open(os.path.join(state_dir, "alerts.lock"), "a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        state = load_state(state_path)
        planned = []
        for family in ALERT_FAMILIES:
            message, quiet, sent = evaluate_family(family, usage.get(family), state.get(family), now)
            state[family] = quiet
            if message:
                planned.append((family, message, sent))
        message, quiet, sent = evaluate_fable(calls, state.get("fable"), now)
        state["fable"] = quiet
        if message:
            planned.append(("fable", message, sent))
        # Quiet state first, so a failed push keeps the pending crossing and the old time.
        save_state(state_path, state)
        for key, message, sent in planned:
            try:
                deliver(message)
            except UsageError:
                raise
            except Exception:
                return delivered
            state[key] = sent
            save_state(state_path, state)
            delivered.append(message)
    return delivered


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv != ["alert"]:
        sys.stderr.write("usage: plan_usage.py alert\n")
        return 2
    try:
        delivered = alert()
    except UsageError as exc:
        sys.stderr.write(f"plan-usage: {exc}\n")
        return 1
    for message in delivered:
        sys.stdout.write(message["body"] + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
