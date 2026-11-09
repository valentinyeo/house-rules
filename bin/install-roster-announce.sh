#!/usr/bin/env bash
# Add the roster-announce SessionStart hook to Claude Code (HYCI-214). Idempotent.
# Codex needs a trusted hash per hook and hax has no hooks: those sessions are recorded by fleet/roster-check --record.
set -euo pipefail
repo=$(dirname "$(dirname "$(readlink -f "$0")")")
python3 - "$HOME/.claude/settings.json" "$repo/fleet/roster-announce --hook" <<'PY'
import json, sys
path, cmd = sys.argv[1], sys.argv[2]
s = json.load(open(path))
starts = s.setdefault("hooks", {}).setdefault("SessionStart", [])
if any("roster-announce --hook" in h.get("command", "") for e in starts for h in e.get("hooks", [])):
    print("roster-announce hook already installed")
else:
    starts.append({"matcher": "startup|resume", "hooks": [{"type": "command", "command": cmd, "timeout": 5}]})
    open(path, "w").write(json.dumps(s, indent=2) + "\n")
    print("roster-announce hook installed")
PY
