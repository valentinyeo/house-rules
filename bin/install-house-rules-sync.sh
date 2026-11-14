#!/usr/bin/env bash
set -euo pipefail
repo=$(dirname "$(dirname "$(readlink -f "$0")")")
bindir="$HOME/.local/bin"
udir="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
install -d -m 755 "$bindir" "$udir"
install -m 755 "$repo/bin/house-rules-sync" "$bindir/house-rules-sync"
install -m 644 "$repo/systemd/house-rules-sync.service" "$repo/systemd/house-rules-sync.timer" "$udir/"
systemctl --user daemon-reload
systemctl --user enable --now house-rules-sync.timer
systemctl --user start house-rules-sync.service
systemctl --user is-active house-rules-sync.timer
printf '%s\n' 'HOUSE_RULES_SYNC_INSTALLED' 'Undo: systemctl --user disable --now house-rules-sync.timer'
