#!/usr/bin/env bash
set -euo pipefail
repo=$(dirname "$(dirname "$(readlink -f "$0")")")
udir="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
install -d -m 755 "$udir"
install -m 644 "$repo/systemd/solo-wake.service" "$repo/systemd/solo-wake.timer" "$udir/"
systemctl --user daemon-reload
systemctl --user enable --now solo-wake.timer
systemctl --user is-active solo-wake.timer
