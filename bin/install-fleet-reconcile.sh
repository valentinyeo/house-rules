#!/usr/bin/env bash
set -euo pipefail
repo=$(dirname "$(dirname "$(readlink -f "$0")")")
udir="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
[ -f "$HOME/.config/fleet/reconcile.env" ] || { echo 'Create ~/.config/fleet/reconcile.env with the agent HT_TOKEN first.' >&2; exit 1; }
install -d -m 755 "$udir"
install -m 644 "$repo/systemd/fleet-reconcile.service" "$repo/systemd/fleet-reconcile.timer" "$udir/"
systemctl --user daemon-reload
systemctl --user enable --now fleet-reconcile.timer
systemctl --user is-active fleet-reconcile.timer
