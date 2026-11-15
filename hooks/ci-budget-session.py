#!/usr/bin/env python3
"""Session-start line when this checkout's checks are over the SOFT-2470 budget.

valentin-mode-load calls budget_line(cwd). This file does not edit ~/.claude.
See hooks/ci-budget-install.md.
"""
import datetime as dt
import json
import os
import re
import subprocess
import sys
from pathlib import Path

# Repo names matching this pattern are out of bounds for the check.
BAD_REPO = re.compile(r"(?i)(?<![a-z])(inne|vwo)(?![a-z])")
TTL = 6 * 60 * 60


def state_dir():
    return Path(os.environ.get("CI_BUDGET_STATE", Path.home() / ".local/state/ci-budget"))


def resolve_bin():
    override = os.environ.get("CI_BUDGET_BIN")
    if override:
        return override
    here = Path(__file__).resolve().parent.parent / "bin" / "ci-budget"
    if here.is_file():
        return str(here)
    home = Path.home() / ".local/share/house-rules/bin/ci-budget"
    if home.is_file():
        return str(home)
    return "ci-budget"


def origin_repo(cwd):
    if not cwd or not os.path.isdir(cwd):
        return None
    try:
        inside = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--is-inside-work-tree"],
            capture_output=True, text=True, timeout=5,
        )
        url = subprocess.run(
            ["git", "-C", cwd, "remote", "get-url", "origin"],
            capture_output=True, text=True, timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if inside.returncode != 0 or url.returncode != 0:
        return None
    remote = url.stdout.strip().rstrip("/")
    match = re.search(r"github\.com[:/]([^/]+)/([^/]+)$", remote)
    if not match or match.group(1).lower() != "valentinyeo":
        return None
    name = re.sub(r"\.git$", "", match.group(2))
    if BAD_REPO.search(name):
        return None
    return f"{match.group(1)}/{name}"


def sentence(stdout):
    items = "; ".join(line for line in (stdout or "").splitlines() if line.strip())
    if not items:
        return ""
    return (
        f"CHECKS OVER BUDGET: {items}. "
        "You own this repo's checks: fix them first (SOFT-2470)."
    )


def read_cache(path):
    try:
        data = json.loads(path.read_text())
        at = dt.datetime.fromisoformat(data["at"])
    except (OSError, json.JSONDecodeError, KeyError, ValueError):
        return None
    if at.tzinfo is None:
        at = at.replace(tzinfo=dt.timezone.utc)
    age = (dt.datetime.now(dt.timezone.utc) - at).total_seconds()
    if age < 0 or age > TTL:
        return None
    return data


def write_cache(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload))
    tmp.replace(path)


def run_budget(repo):
    try:
        proc = subprocess.run(
            [resolve_bin(), repo],
            capture_output=True, text=True, timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None, ""
    return proc.returncode, proc.stdout


def budget_line(cwd):
    repo = origin_repo(cwd)
    if not repo:
        return ""
    cache = state_dir() / repo.replace("/", "__")
    cached = read_cache(cache)
    if cached is None:
        code, stdout = run_budget(repo)
        if code is None:
            return ""
        cached = {
            "at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "code": code,
            "stdout": stdout,
        }
        write_cache(cache, cached)
    if cached.get("code") == 0:
        return ""
    return sentence(cached.get("stdout") or "")


def main():
    cwd = os.getcwd()
    if not sys.stdin.isatty():
        raw = sys.stdin.read()
        if raw.strip():
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                payload = None
            if isinstance(payload, dict) and payload.get("cwd"):
                cwd = payload["cwd"]
    line = budget_line(cwd)
    if line:
        print(line)


if __name__ == "__main__":
    main()
