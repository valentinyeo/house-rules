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

## 4. Take blockers off Valentin
Valentin, 2026-11-02:
> it should include a review of the tickets that i am the blocker on and evaluate if the blocker is justified and if it is is the blocker sticking to hteh /house-rules for ticket wrigint and if it isn't place the comment in the ticket to ask the lead or agent to write thet icket properly and to review what caused this ticket to be written badly and ideally fix the origin

> rewrite /hypertask-triage so it does this next time by itself?

`~/.local/share/house-rules/skills/hypertask-triage/scripts/blocker-review --boards 15,4060 --apply`

It reads his inbox tab "Blocked by you" plus every Valentin Review column.
It also runs by itself daily at 07:30 Berlin (timer `blocker-review`, log `~/.local/state/blocker-review.log`). Run it by hand on every triage too.

Verdicts, from the newest Question on the ticket:
- CLEAR: the script clears it itself. He answered and it is not money, keys or his hands. Or no Question exists. Or it asks him to switch a flag Off.
- ANSWERED: he replied, but it is money, keys or his hands. A note tells the lead to act on his reply.
- NOT-HIS: no his-call words. A regex guess: read the ticket, then clear it yourself.
- HIS-BADLY-WRITTEN: his call, but breaks `skills/tickets/`. A note asks for a rewrite and an origin fix.
- HIS-OK: leave it.

Clear = agent-lane note, his name off, ticket back to its home column (board 15: Bugs, Features or Improvements by title and label; 4060: Backlog).
Tickets on another lead's board are listed as "left for <lead>". That lead runs this step on its turn.

## 5. Read every NOT-HIS and ANSWERED row
Do not stop at the script. Read each one:
- His own ticket asked for it? That is his yes. Clear it.
- He said Yes already, or the runner's own advice is No? Clear or close it.
- Waits on other work, not on him? Clear it.
- Old, and he said he does not know what it is? Archive it.
- Real money, keys, going public, deleting customer data, his hands? Keep.

Clear by hand: `blocker-review --clear <ticket> --to home|archive|<section id> --why "<reason>"`.
Same reason twice? Add the class to `skills/unblock/learned.md`. When a script can see it, add it to `drift()` in blocker-review too.

## 6. Look for levers
Group what stays with him by class: keys, money, publishing, at his PC.
Several in one class? Propose one fix that ends the class. Examples: one page with every key step for one sitting, a one-time setup, a standing small budget.
Only money, keys and going public need his yes. Build the rest.

## 6b. Sweep the Agent Blocked columns
Valentin, 2026-11-02:
> 99 tickets in agent blocked infrA? wtf is going ion there?

`blocker-review` ends with `PARKED` rows: every ticket parked over a day, and the column it belongs in.
Only real tool or server failures stay. Design goes to UX needed. Merged work goes to QA.
Waiting on a ticket or date goes home with a link. His call goes to Valentin Review with one Question.
The class is a regex guess. Read the ticket, move it with `blocker-review --clear T --to <id> --why "..."`.

## 7. Report to Valentin
Caveman:
- Archived N of M done tickets.
- Kept K, grouped by reason, each a full https link.
- Blockers: N wait on you, X cleared, Y badly written, notes posted.
- Levers found, each with what it ends.
- Wrong calls fixed in the rule, if any.

Auto-archive of done tickets on a timer comes later, after Valentin trusts the manual runs.
