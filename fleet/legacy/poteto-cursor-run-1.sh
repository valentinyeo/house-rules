#!/bin/bash
set -u
export PATH="/home/valentin/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
export SHIP_SESSION_NAME="RUNNER 11"
cd /home/valentin/projects/hypertask
LOG="/home/valentin/.local/state/poteto-cursor/worker-1.log"
while :; do
  [ -f "/home/valentin/.local/state/poteto-cursor/STOP-1" ] && { sleep 300; continue; }
  echo "$(date -u +%FT%TZ) start cursor runner 1 as RUNNER 11" | tee -a "$LOG"
  out=$(timeout 3h /home/valentin/.local/bin/cursor-agent -p --output-format text --model grok-4.7-medium -f --trust --approve-mcps --workspace /home/valentin/projects/hypertask "$(cat /home/valentin/.local/state/poteto-cursor/prompt-1.md)" 2>&1 | tee /dev/tty)
  tail -c 400 <<<"$out" >> "$LOG"
  echo "$(date -u +%FT%TZ) end" | tee -a "$LOG"
  if grep -q "CURSOR IDLE" <<<"$out"; then sleep 600; else sleep 30; fi
done
