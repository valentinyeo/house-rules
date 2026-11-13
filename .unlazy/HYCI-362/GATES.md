# HYCI-362 gates

Scope: a runner slot the pacer turns on must actually run. `fleet/runner` counts a slot as live only while a
`fleet/runner N --loop` process exists, kills a session that outlived its loop and starts a fresh loop; `fleet-watch`
flags a slot that is on with no loop. Repos: valentinyeo/house-rules (loop + tick cadence), valentinyeo/poteto-2-advisor
(fleet-watch).

CHECK 1: `fleet/runner top-up` counts loops, not tmux sessions.
PROOF: `pgrep -n loop_pid` in `fleet/runner`; `grep -n 'live=0' -A3 fleet/runner` shows the count loop; no
`tmux list-sessions` count left in `top-up`.

CHECK 2: a session with no loop is killed and a fresh loop started, and `start_one` does the same.
PROOF: `fleet/runner loop-selftest` green in CI (`.github/workflows/pick.yml`), which asserts a dead slot gets a
`new-session` and a live slot is left alone.

CHECK 3: a stopped slot is never restarted (stop-N or PAUSED).
PROOF: same self-test, case 2: stop-2 present, no new-session for slot 2.

CHECK 4: a slot turned on starts within 5 minutes.
PROOF: `systemd/fleet-runner-tick.timer` OnCalendar is `*:0/2`; live check after merge:
`systemctl --user list-timers fleet-runner-tick.timer` shows the 2-minute cadence.

CHECK 5: fleet-watch flags a slot that is on but has no loop.
PROOF: `grep -n 'no runner loop' bin/fleet-watch` in poteto-2-advisor; a slot in `loops` map absent from `loops.values()`
lands in class `down: slot on, no runner loop`; that class exits non-zero and is printed in `latest.txt`.

CHECK 6: both PRs green on their own required checks, merged, and the fix live.
PROOF: PR links in the ticket agent lane; after merge `~/.local/share/house-rules/fleet/runner status` prints
`on but no loop: N` for a dead slot and none for a live one; `~/.local/state/fleet-watch/latest.txt` carries the new class
only when a real slot is dead.
