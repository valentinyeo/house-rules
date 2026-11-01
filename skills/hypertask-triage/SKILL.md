---
name: hypertask-triage
description: Archive finished Hypertask tickets that need no product owner attention, and review every ticket waiting on Valentin (his call or not, written the house way or not). Use for /hypertask-triage, "archive the boring done tickets", "clean the flag columns". Board first; other Hypertask areas later. Any fleet.
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

## 4. Review Valentin's blockers
Valentin, 2026-11-02:
> it should include a review of the tickets that i am the blocker on and evaluate if the blocker is justified and if it is is the blocker sticking to hteh /house-rules for ticket wrigint and if it isn't place the comment in the ticket to ask the lead or agent to write thet icket properly and to review what caused this ticket to be written badly and ideally fix the origin

`~/.local/share/house-rules/skills/hypertask-triage/scripts/blocker-review [--boards 15,4060,2060]`

It reads his inbox tab "Blocked by you" plus every Valentin Review column.
Per ticket it prints a verdict and the broken rules:
- NOT-HIS: no house-rules "his call" class (money, keys, going public, prod data deletion, at his PC, product). Clear it per `/unblock`.
- HIS-BADLY-WRITTEN: his call, but the shape, the marked Question or the plain words break `skills/tickets/`.
- HIS-OK: leave it.

The verdict is a regex guess. Read each NOT-HIS ticket before clearing it.
Then rerun with `--apply`: every flagged ticket gets one agent-lane note for its agent and lead.
The note asks for a rewrite, one proper Question, and a fix at the origin (skill, wrapper, prompt).
A rerun posts nothing new until the defects change.
Same cause on several tickets? Fix that origin yourself, or file it for the owning lead.

## 5. Report to Valentin
Caveman, four lines:
- Archived N of M done tickets.
- Kept K, grouped by reason, each a full https link.
- Blockers: N wait on you, X not your call, Y badly written, notes posted.
- Wrong calls fixed in the rule, if any.

Auto-archive on a timer comes later, after Valentin trusts the manual runs.
