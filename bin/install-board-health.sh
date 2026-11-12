#!/usr/bin/env bash
set -euo pipefail
repo=$(dirname "$(dirname "$(readlink -f "$0")")")
udir="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
install -d -m 755 "$udir" "$HOME/.local/state/board-health"
install -m 644 "$repo/systemd/ht-board-health.service" "$repo/systemd/ht-board-health.timer" "$udir/"
systemctl --user daemon-reload
systemctl --user enable --now ht-board-health.timer
systemctl --user is-active ht-board-health.timer
