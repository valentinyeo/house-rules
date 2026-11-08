#!/usr/bin/env python3
"""List live old runner-pool parts still enabled or present (YPER4-1381).

Prints one path or unit name per line. Empty output means the host is clean.
"""
import os
import subprocess
import sys
from pathlib import Path

HOME = Path.home()
UDIR = Path(os.environ.get("XDG_CONFIG_HOME", HOME / ".config")) / "systemd/user"
HERE = Path(__file__).resolve().parent
REPO = HERE.parent

RETIRED_TIMER_NAMES = frozenset(
    {
        "runner-dispatch.timer",
        "runner9-htpr-7736-priority-push.timer",
        "fleet-idle-watch.timer",
    }
)
RETIRED_TIMER_PREFIXES = ("runner-pickup@",)
RETIRED_UNIT_BASENAMES = (
    "ci-runner-tick",
    "infra-runner-tick",
    "ht-hax-runner-keeper",
    "agent-fleet-watch",
    "ht-fleet-guard",
    "ht-fleet-share",
    "runner-pickup@",
    "fleet-subscription-lanes",
    "ht-drain-watch",
    "ht-night-watch",
    "ht-practice-watch",
    "ht-or-runner-tick",
)
RETIRED_LOCAL_BIN = (
    "ht-or-runner",
    "ht-or-runner-pick",
    "pr-drain-pick",
    "mb-pick",
    "mp-pick",
    "fleet-idle-watch",
    "ci-pick",
    "infra-pick",
)
RETIRED_PATH_MARKERS = (
    "hypertask-dispatch",
    "runner-pickup/runner-pickup",
    "ht-hax-runner",
    "ht-claude-runners",
    "company-skills/kit/bin/hypertask-dispatch",
    "/fleet/legacy/",
)
LIVE_BIN_PATHS = (
    Path.home() / "projects/ci-boss/bin/ht-ci-runner",
    Path.home() / "projects/ci-boss/bin/ci-pick",
    Path.home() / "projects/infra-lead/bin/infra-pick",
    Path.home() / "projects/infra-lead/bin/infra-runner",
)
ONE_OFF = HOME / ".local/state/vcc-evidence/HTPR-7736/push-at-reopen.py"


def enabled_timers():
    r = subprocess.run(
        ["systemctl", "--user", "list-timers", "--all", "--no-pager", "--plain"],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        return []
    out = []
    for ln in r.stdout.splitlines():
        timer = ""
        for part in ln.split():
            if part.endswith(".timer"):
                timer = part
        if timer:
            out.append(timer)
    return out


def timer_enabled(name):
    r = subprocess.run(["systemctl", "--user", "is-enabled", name], capture_output=True, text=True)
    return r.returncode == 0 and (r.stdout or "").strip() == "enabled"


def read_unit_exec(timer_name):
    svc = timer_name.replace(".timer", ".service")
    if svc.endswith("@"):
        return ""
    path = UDIR / svc
    if not path.is_file():
        path = UDIR / timer_name.replace(".timer", ".service")
    try:
        text = path.read_text()
    except OSError:
        return ""
    for ln in text.splitlines():
        if ln.startswith("ExecStart="):
            return ln.split("=", 1)[1].strip()
    return ""


def path_exists(exec_line):
    if not exec_line:
        return None
    exp = os.path.expandvars(exec_line.replace("%h", str(HOME)))
    exp = exp.split()[0]
    if exp.startswith("/"):
        return Path(exp).exists()
    return None


def scan():
    found = []
    seen = set()

    def add(item):
        if item not in seen:
            seen.add(item)
            found.append(item)

    for timer in enabled_timers():
        base = timer
        if not timer_enabled(base):
            continue
        if base in RETIRED_TIMER_NAMES or any(base.startswith(p) for p in RETIRED_TIMER_PREFIXES):
            add(f"timer-enabled:{base}")
            continue
        exec_line = read_unit_exec(base)
        if exec_line:
            for marker in RETIRED_PATH_MARKERS:
                if marker in exec_line:
                    add(f"timer-retired-exec:{base}")
                    break
            else:
                missing = path_exists(exec_line)
                if missing is False:
                    add(f"timer-missing-exec:{base}")

    if UDIR.is_dir():
        for name in RETIRED_UNIT_BASENAMES:
            for suffix in (".service", ".timer"):
                path = UDIR / f"{name}{suffix}"
                if path.is_file():
                    add(f"unit-file:{path}")

    lbin = HOME / ".local/bin"
    for name in RETIRED_LOCAL_BIN:
        path = lbin / name
        if path.exists():
            add(f"local-bin:{path}")

    for path in LIVE_BIN_PATHS:
        if path.is_file():
            add(f"repo-bin:{path}")

    if ONE_OFF.is_file():
        add(f"one-off:{ONE_OFF}")

    return found


def main():
    for line in scan():
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
