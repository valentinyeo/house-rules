#!/usr/bin/env bash
set -euo pipefail
repo=$(dirname "$(dirname "$(readlink -f "$0")")")
udir="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
install -d -m 755 "$udir"
install -m 644 "$repo/systemd/fleet-drill.service" "$repo/systemd/fleet-drill.timer" "$udir/"
systemctl --user daemon-reload
systemctl --user enable --now fleet-drill.timer
systemctl --user is-active fleet-drill.timer
echo "fleet-drill timer installed"
