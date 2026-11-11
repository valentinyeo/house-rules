#!/usr/bin/env bash
set -euo pipefail
repo=$(dirname "$(dirname "$(readlink -f "$0")")")
udir="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
install -d -m 755 "$udir"
install -m 644 "$repo/systemd/pr-snapshot.service" "$repo/systemd/pr-snapshot.timer" "$udir/"
systemctl --user daemon-reload
systemctl --user enable --now pr-snapshot.timer
systemctl --user is-active pr-snapshot.timer
