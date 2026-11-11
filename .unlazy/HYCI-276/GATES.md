# Gates: HYCI-276 Board health: board 15 red over a day

Scope: board 15's `ci` red line only. The other red lines (shipped, orphans, outside, overdue,
pristine, idle, prq) are board 15 owner actions (HT Product Lead, Chief Of Staff) and are handed
back in the agent lane, not claimed here. The earlier run's pick/park loop fix shipped in
valentinyeo/house-rules#361 and #363.

Why this line: a ticket's only real CI block is a BlockedBy relation. A Done CI ticket left linked
never stops blocking, and a CI ticket named only in the agent log is not a block at all, yet the
scorecard reports both, so the `ci` line can never go green. Nothing clears either one.

## G1 Ticket read and owned

- Claim kept: launcher claim `tmux attach -t ht-or-runner-8 (Cursor Grok RUNNER 8)`; ticket read
  with its comments and full agent log; no earlier code change exists for it.
- Manual: yes. Evidence in the agent lane of HYCI-276.

## G2 The ci score counts only real blocks

- A log-only mention of a Done CI ticket is no longer a CI block; a relation to a Done CI ticket is.
- CHECK: `cd /home/valentin/projects/worktrees/runner-8-hyci-276 && python3 skills/hypertask-triage/scripts/board-health --self-test`
- EXPECT: exit 0 and `SELF-TEST` pass line.

## G3 A safe fix clears a stale CI link and adds a missing one

- `--plan --only links` writes nothing and names each action; `--fix --only links` unlinks a Done
  CI ticket and links an open one that was only mentioned.
- CHECK: the same self-test covers both plans (pure functions, no writes).
- EXPECT: pass.

## G4 PR open and merged

- One small PR to valentinyeo/house-rules, required checks green, merged.
- Manual: PR link in the agent lane.

## G5 Board 15's ci line is OK on a fresh scorecard

- After the merged fix runs, a fresh `board-health --board 15` prints `OK  ci`.
- CHECK: `cd /home/valentin/projects/worktrees/runner-8-hyci-276 && python3 skills/hypertask-triage/scripts/board-health --board 15 | grep -E "^(OK|RED|ESCALATE) +ci "`
- EXPECT: a line starting with `OK` and the ci invariant.

## G6 Ticket ends in a legal column

- Remaining red lines named with their owners in the agent lane; the ticket leaves In Progress.
- Manual: yes.
