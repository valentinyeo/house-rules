#!/usr/bin/env bash
set -euo pipefail
[ "$(id -u)" = 0 ] || { echo 'Run with sudo on Hetzner' >&2; exit 1; }
repo=$(cd "$(dirname "$0")/.." && pwd)
source=/home/valentin/.local/state/house-rules-inne-source
if [ ! -e "$source" ]; then
  runuser -u valentin -- bash -c 'umask 077; git -c credential.helper="!/home/valentin/.local/bin/gh auth git-credential" clone -q https://github.com/valentinyeo/house-rules.git "$1"' bash "$source"
fi
chmod 700 "$source"
install -d -m 755 /opt/house-rules-inne/bin /opt/house-rules-inne/skills/house-rules /etc/systemd/system/skills-sync.service.d
install -m 644 "$repo"/bin/{inne-sync.py,test-inne-sync.py,link-inne.py} /opt/house-rules-inne/bin/
install -m 644 "$repo/house-rules.md" /opt/house-rules-inne/
install -m 644 "$repo/skills/house-rules/SKILL.md" /opt/house-rules-inne/skills/house-rules/
install -m 644 "$repo"/systemd/house-rules-inne.{service,timer} /etc/systemd/system/
install -m 644 "$repo/systemd/skills-sync-house-rules.conf" /etc/systemd/system/skills-sync.service.d/house-rules.conf
systemctl daemon-reload
systemctl start house-rules-inne.service
runuser -u inne -- python3 /opt/house-rules-inne/bin/link-inne.py
systemctl enable --now house-rules-inne.timer
printf '%s\n' 'INNE_INSTALLED' 'Undo: sudo systemctl disable --now house-rules-inne.timer'
