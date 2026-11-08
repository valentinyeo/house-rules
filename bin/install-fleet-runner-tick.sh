#!/usr/bin/env bash
set -euo pipefail
repo=$(dirname "$(dirname "$(readlink -f "$0")")")
udir="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
install -d -m 755 "$udir"
install -m 644 "$repo/systemd/fleet-runner-tick.service" "$repo/systemd/fleet-runner-tick.timer" "$udir/"
systemctl --user disable --now ht-or-runner-tick.timer 2>/dev/null || true
rm -rf "$udir/ht-or-runner-tick.service.d" 2>/dev/null || true
systemctl --user daemon-reload
systemctl --user enable --now fleet-runner-tick.timer
rm -f "$HOME/.local/bin/ht-or-runner" "$HOME/.local/bin/ht-or-runner-pick"
systemctl --user is-active fleet-runner-tick.timer
echo "fleet-runner-tick installed; legacy ~/.local/bin/ht-or-runner pickers removed if present"
