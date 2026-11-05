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

Valentin, 2026-11-06:
> if i am mentioned as the blocking person the tickets must be pristine

So the whole ticket is checked, not only the Question:
- Title and description: plain words, ticket shape, Valentin quoted in a `>` block.
- Every people comment (qa, question, done, mentions): ticket-lint rules. Robot status or bot review verdicts there belong in the agent lane.
- One open Question only.
`PRISTINE X of Y` counts tickets that break no rule. HIS-OK needs zero breaks.
Every other ticket gets the rewrite note: fix each flagged comment, then fix the origin.

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

## 6b. Sweep the Agent Blocked columns and cap every waiting column
`pileup-watch --apply` runs daily after blocker-review. Over a cap it files one urgent alarm ticket on board 4060. Clear the column that day.
Valentin, 2026-11-02:
> 99 tickets in agent blocked infrA? wtf is going ion there?

`blocker-review` ends with `PARKED` rows: every ticket parked over a day, and the column it belongs in.
Only real tool or server failures stay. Design goes to UX needed. Merged work goes to QA.
Waiting on a ticket or date goes home with a link. His call goes to Valentin Review with one Question.
Each `PARKED` row also gets the whole-ticket check, with its defects listed. Blocked tickets must be clean too.
Send the defect list to the board's lead, same as step 4.
The class is a regex guess. Read the ticket, move it with `blocker-review --clear T --to <id> --why "..."`.

## 6c. Flag tickets nobody can be working
Valentin, 2026-11-05:
> I see 20 tickets in progress. That's impossible. We don't have that many runners.

`~/.local/share/house-rules/skills/hypertask-triage/scripts/flow-check --board 15`
Also run it for 4060 and 11514.

A runner stays on one ticket until it ships. So:
- In Progress never holds more tickets than live runners. More? It prints `IMPOSSIBLE`.
- An In Progress ticket is fine only if its claimer is a live runner, it is that runner's newest claim, and its log moved in the last 3 hours.
- Otherwise: `DEAD-RUNNER` (no such runner session), `MOVED-ON` (runner claimed something newer), `STALE` (no log for 3h) or `NO-CLAIM`.
- QA over 24h: the runner left before the live proof.
- AI Review over 6h: nobody drives the PR.
- Agent Blocked over 24h, or more than 5 tickets: not being cleared.

It only reads. It flags; it moves nothing.
Report every flagged row to the board's lead, as full links in your reply.
The lead sends each ticket back to a runner or to its home column.
Same flag on the next run? The lead's sweep is broken. File that on board 4060.

## 6d. Count tickets with no brain tag
Every open ticket needs one brain tag: `brain-light`, `brain-medium`, `brain-hard` or `brain-extra-hard`.
The runner picks its brain from it. No tag means the medium brain by default.

flow-check prints `NO-BRAIN board N: X of Y open tickets have no brain tag`, split by column.
Done and flag columns are skipped. The full list is in its `--json` file.
It only counts. It tags nothing.
Report the count per board. Send the list to the board's lead to tag.
A board with no brain labels at all? File that once on board 4060.

## 6e. Flag tickets blocked by CI
CI Boss owns CI, on the fleet CI board https://app.hypertask.ai/project?id=11514.
CI Boss slow? Product tickets pile up behind it.
A CI-blocked ticket links one Urgent CI ticket in its log.

flow-check prints, per blocked ticket:
- `CI-WAIT`: CI ticket open, Urgent, In Progress, under 6 hours. Fine.
- `CI-SLOW`: CI ticket open over 6 hours, not Urgent, or not In Progress. CI Boss is behind.
- `CI-DONE`: CI ticket closed, but the ticket still waits. Its runner must resume.
- `CI-NO-TICKET`: CI failure blocker, no CI ticket. CI Boss never heard.
Then `CI-BLOCKED board N: X tickets wait on CI`.

Act on it:
- `CI-NO-TICKET`: file one Urgent ticket on 11514, labels CI and Hypertask CI. Or +1 the open one for the same check. Link it in the blocked ticket's agent lane.
- `CI-SLOW`: add a line in that CI ticket's agent lane. List the waiting tickets and hours.
- `CI-DONE`: tell the board lead which runner must resume.
- `CI-SLOW` again on the next run? File one Urgent alarm on 11514 for CI Boss.

## 7. Report to Valentin
Caveman:
- Archived N of M done tickets.
- Kept K, grouped by reason, each a full https link.
- Blockers: N wait on you, X cleared, Y badly written, notes posted. Pristine: X of N. Agent Blocked clean: X of N.
- Levers found, each with what it ends.
- Out of place: In Progress count against live runners, then counts per flag and column.
- No brain tag: X of Y open tickets, per board.
- Blocked by CI: X tickets, counts per CI flag, slow CI tickets as links.
- Wrong calls fixed in the rule, if any.

Auto-archive of done tickets on a timer comes later, after Valentin trusts the manual runs.
