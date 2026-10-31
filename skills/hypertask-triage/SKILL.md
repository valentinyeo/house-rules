---
name: hypertask-triage
description: Archive finished Hypertask tickets that need no product owner attention, so done columns show only what Valentin cares about. Use for /hypertask-triage, "archive the boring done tickets", "clean the flag columns". Board first; other Hypertask areas later. Any fleet.
---

# /hypertask-triage [board]

Valentin, 2026-10-31:
> archive all tickets on board 15 that are inconseuqtial from the flag columns so eveyrthing that is done that is not a new feature and low risk

> as a product owner non dev i don't enve know what it is or if it is interseting

Default board: your fleet's product board (Hypertask: 15). Software Factory: its own board.

## 1. Dry run
`~/.local/share/house-rules/skills/hypertask-triage/scripts/archive-done --board <id>`

It reads only finished columns (board 15: No Flag, Flag: Everyone, Done; other boards: Done).
It never touches Flag: Only Me + QA, Flag: Off or open columns.

Keep a ticket when any of these is true:
- It has an open blocking question.
- It is a new or changed feature: [FEATURE] or [IMPROVEMENT], or its flag kind is feature or improvement.
- It touches a risky area: money, billing, login, access, security, privacy, deletion, customer email, keys.

Archive the rest: error logs, agent call failures, bug fixes, infra, dependency upgrades.

## 2. Check the keeps and archives
Read the list. A wrong call? Fix the rule in the script, not by hand. Rerun.

## 3. Apply
Same command plus `--apply`. Writes go through vcc as your agent, never Valentin's login.
Each archived ticket gets an agent lane note with the reason. Undo: set status back to Normal.

## 4. Report to Valentin
Caveman, three lines:
- Archived N of M done tickets.
- Kept K, grouped by reason, each a full https link.
- Wrong calls fixed in the rule, if any.

Auto-archive on a timer comes later, after Valentin trusts the manual runs.
