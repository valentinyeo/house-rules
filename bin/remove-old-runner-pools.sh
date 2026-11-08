#!/usr/bin/env bash
set -euo pipefail
repo=$(dirname "$(dirname "$(readlink -f "$0")")")
scan="$repo/fleet/dead-parts-scan.py"
udir="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
home="${HOME:?}"

stop_timer() {
  systemctl --user disable --now "$1" 2>/dev/null || true
  systemctl --user stop "$1" 2>/dev/null || true
  systemctl --user reset-failed "$1" 2>/dev/null || true
}

for t in runner-dispatch.timer runner9-htpr-7736-priority-push.timer fleet-idle-watch.timer; do
  stop_timer "$t"
done
while read -r line; do
  for word in $line; do
    if [[ "$word" =~ ^runner-pickup@[0-9]+\.timer$ ]] || [[ "$word" == fleet-idle-watch.timer ]] || [[ "$word" == runner-dispatch.timer ]] || [[ "$word" == runner9-htpr-7736-priority-push.timer ]]; then
      stop_timer "$word"
    fi
  done
done < <(systemctl --user list-timers --all --no-pager --plain 2>/dev/null)

for base in ci-runner-tick infra-runner-tick ht-hax-runner-keeper agent-fleet-watch ht-fleet-guard ht-fleet-share \
  runner-pickup@ fleet-subscription-lanes ht-drain-watch ht-night-watch ht-practice-watch ht-or-runner-tick \
  runner-dispatch runner9-htpr-7736-priority-push fleet-idle-watch; do
  rm -f "$udir/${base}.service" "$udir/${base}.timer"
done
rm -f "$udir/timers.target.wants/runner-dispatch.timer" \
  "$udir/timers.target.wants/fleet-idle-watch.timer" \
  "$udir/timers.target.wants/runner9-htpr-7736-priority-push.timer"
rm -f "$udir/timers.target.wants"/runner-pickup@*.timer 2>/dev/null || true

for name in ht-or-runner ht-or-runner-pick pr-drain-pick mb-pick mp-pick fleet-idle-watch ci-pick infra-pick; do
  rm -f "$home/.local/bin/$name"
done
rm -f "$home/projects/ci-boss/bin/ht-ci-runner" "$home/projects/ci-boss/bin/ci-pick" \
  "$home/projects/infra-lead/bin/infra-pick" "$home/projects/infra-lead/bin/infra-runner"
rm -f "$home/.local/state/vcc-evidence/HTPR-7736/push-at-reopen.py"

stamp=$(date -u +%Y%m%dT%H%M%SZ)
archive="$home/.local/state/archive-old-runner-pools-${stamp}.tar.gz"
(
  cd "$home/.local/state"
  dirs=()
  for d in ci-runners infra-runners ht-hax-runners ht-claude-runners; do
    [[ -d "$d" ]] && dirs+=("$d")
  done
  if ((${#dirs[@]})); then
    tar czf "$archive" "${dirs[@]}"
    echo "archived state: $archive"
  fi
)

systemctl --user daemon-reload
while read -r line; do
  for word in $line; do
    if [[ "$word" =~ ^runner-pickup@[0-9]+\.timer$ ]] || [[ "$word" == fleet-idle-watch.timer ]]; then
      stop_timer "$word"
    fi
  done
done < <(systemctl --user list-timers --all --no-pager --plain 2>/dev/null)
systemctl --user daemon-reload

remaining=$("$scan" | head -20)
if [[ -n "$remaining" ]]; then
  echo "remove-old-runner-pools: still present:" >&2
  echo "$remaining" >&2
  exit 1
fi
echo "remove-old-runner-pools ok"
