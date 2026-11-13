#!/usr/bin/env bash
set -euo pipefail
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
repo=$(dirname "$(dirname "$(readlink -f "$0")")")
udir="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
install -d -m 755 "$udir"
install -m 644 "$repo/systemd/sf-release-watch.service" "$repo/systemd/sf-release-watch.timer" "$udir/"
systemctl --user daemon-reload
systemctl --user enable --now sf-release-watch.timer
systemctl --user is-active sf-release-watch.timer
