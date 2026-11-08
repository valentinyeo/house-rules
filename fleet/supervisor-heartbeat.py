#!/usr/bin/env python3
"""Post a supervisor heartbeat to the outside Cloudflare watch (HYCI-189).

    fleet/supervisor-heartbeat.py [--id production|drill] [--dry-run] [--self-check]

Fleet-watch invokes bin/fleet-supervisor-alarm each tick. Token once per run from yeo-key or env.
"""
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_URL = "https://fleet-supervisor-watch.ancient-glitter-9ac9.workers.dev/heartbeat"
CONFIG = os.path.expanduser("~/.local/state/fleet-watch/supervisor-heartbeat.json")
WATCH = os.environ.get("FLEET_WATCH_STATE") or os.path.expanduser("~/.local/state/fleet-watch")
LOCAL_HB = os.path.join(WATCH, "heartbeat")
YEO_KEY = os.path.expanduser("~/.local/bin/yeo-key")


def load_config():
    try:
        return json.load(open(CONFIG))
    except (OSError, ValueError):
        return {}


def bearer():
    tok = os.environ.get("FLEET_SUPERVISOR_HEARTBEAT_TOKEN", "").strip()
    if tok:
        return tok
    r = subprocess.run(
        [YEO_KEY, "Fleet Supervisor Heartbeat", "HEARTBEAT_TOKEN"],
        capture_output=True,
        text=True,
        timeout=90,
    )
    if r.returncode == 0:
        got = (r.stdout or "").strip()
        if got:
            return got
    token_file = os.path.join(WATCH, "heartbeat.token")
    try:
        return open(token_file).read().strip()
    except OSError:
        return ""


def target_url(heartbeat_id):
    cfg = load_config()
    base = os.environ.get("FLEET_SUPERVISOR_HEARTBEAT_URL") or cfg.get("url") or DEFAULT_URL
    sep = "&" if "?" in base else "?"
    return f"{base}{sep}id={urllib.parse.quote(heartbeat_id)}"


def touch_local():
    os.makedirs(WATCH, exist_ok=True)
    open(LOCAL_HB, "w").write(f"{int(time.time())}\n")


def post(heartbeat_id, dry=False):
    tok = bearer()
    if not tok:
        return False, "no heartbeat token (yeo-key Fleet Supervisor Heartbeat HEARTBEAT_TOKEN)"
    url = target_url(heartbeat_id)
    req = urllib.request.Request(
        url,
        data=b"ok",
        method="POST",
        headers={"Authorization": f"Bearer {tok}", "User-Agent": "fleet-supervisor-alarm", "Content-Type": "text/plain"},
    )
    if dry:
        return True, f"would POST {url}"
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            code = resp.getcode()
    except urllib.error.HTTPError as e:
        return False, f"heartbeat HTTP {e.code}"
    except (urllib.error.URLError, TimeoutError) as e:
        return False, f"heartbeat failed: {e}"
    if code not in (200, 204):
        return False, f"heartbeat HTTP {code}"
    touch_local()
    return True, "ok"


def self_check():
    alarm = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bin", "fleet-supervisor-alarm")
    if not os.path.isfile(alarm):
        return False, "bin/fleet-supervisor-alarm missing"
    if os.environ.get("FLEET_SUPERVISOR_DRILL") == "1":
        return True, "drill self-check"
    if not bearer():
        return False, "no heartbeat token configured"
    return True, "fleet-supervisor-alarm present"


def main():
    args = sys.argv[1:]
    dry = "--dry-run" in args
    if "--self-check" in args:
        ok, msg = self_check()
        print(msg, file=sys.stderr)
        raise SystemExit(0 if ok else 1)
    hid = "production"
    for i, a in enumerate(args):
        if a == "--id" and i + 1 < len(args):
            hid = args[i + 1]
    ok, msg = post(hid, dry=dry)
    if not ok:
        print(msg, file=sys.stderr)
        raise SystemExit(1)
    if dry:
        print(msg)


if __name__ == "__main__":
    main()
