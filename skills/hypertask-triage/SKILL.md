---
name: hypertask-triage
description: Board health loop for fleet chiefs. One scorecard (board-health) must print GREEN; every red line names its owner and fix. Also archives finished tickets and reviews every ticket waiting on Valentin. Use for /hypertask-triage, "board health", "is the board healthy", "archive the boring done tickets", "clean the flag columns". Any fleet.
---

# /hypertask-triage [board]

Valentin, 2026-10-31:
> archive all tickets on board 15 that are inconseuqtial from the flag columns so eveyrthing that is done that is not a new feature and low risk

> as a product owner non dev i don't enve know what it is or if it is interseting

Default board: your fleet's product board (Hypertask: 15). Software Factory: its own board.

## How often to run it
Two layers. The script runs on a timer, the chief session works what it cannot fix.
- Script, every hour at :05: timer `ht-board-health` runs `board-health --fix --apply` for 15 and 4060, `--apply` for 11514, and a read-only run for 2060 and each Software Factory view scope. Safe fixes happen even when no chief is awake. Output: `~/.local/state/board-health/last-<scope>.log` (`/` becomes `-`). Alarms bump at most once a day.
- Chief session, every hour at :20: read the last logs, work each red line. The script runs at :05, so the log is fresh by :20. A session cron dies with its session, so check `CronList` at every shift start and recreate it when missing: `CronCreate` cron `20 * * * *`, prompt `/hypertask-triage step 0: read ~/.local/state/board-health/last-*.log, work every red line, rerun board-health until GREEN`. Never more often: runners take about an hour per ticket.
- Full clean-up (steps 1 to 7): once a day at 08:00 London, a second session cron `0 8 * * *`, prompt `/hypertask-triage`. The blocker check also runs alone at 07:30.
- Right away after big changes: a runner restart or a batch of merges.

## 0. Board health: loop until GREEN
Valentin, 2026-11-06:
> the outcome of the skill is to force the chief of staff to fix all of this, and make sure that the system is running smoothly

`~/.local/share/house-rules/skills/hypertask-triage/scripts/board-health --board 15 --fix --apply`
Run it for every scope you own. A scope is a board, or a board view one lead owns.
- Hypertask: 15, 4060, 11514.
- Software Factory: 2060 (Mini Boss CEO), plus views `2060/multi-bot`, `2060/postbox`, `2060/multi-bot-android`.
- A view lead or solo dev runs `board-health --scope 2060/postbox`. It scores only that view's tickets and PRs.
Scopes live in `scripts/scopes.json`: board, view, lead, alarm board, repos and workers.
New lead, view, solo dev or runner pool? Add it there the same turn. Both caps read the same worker list.
Worker kinds: a tmux pool (`ht-or-runner-` = Runner N), one exact session (solo dev `postbox` = Postbox Dev), a runner state file, or always-on (HT Design Builder).

`--fix` runs the safe fixes first, then scores. Each gets an agent-lane note. Board 15 and 4060 only, except the queue fix below.

Free the queue (YPER4-1371): a runner holds one ticket until live. `board-health --board <15|2060|4060|11514> --plan --only queue` lists every ticket a worker holds in a column nobody builds in (Bugs, Features, Improvements, Backlog, Todo, UX needed, UX Sign-off, Later (parked)) and writes nothing. `--fix --only queue` unassigns them, one agent-lane note each. Agent Blocked, Valentin Review and building columns keep their holds. Workers come from all four fleet boards, so app runners holding board 4060 Backlog tickets count. Postbox Dev, Multiprompt Android Dev and HT Design Builder are exempt (view leads and specialist). Boards 2060 and 11514 run it by hand only.
- Merged ticket before QA: moves to QA (board 15).
- No PR in AI Review, or PR closed: back to its home column.
- No brain tag: brain-medium.
- Worker assigned two tickets being built: keeps its most recent, unassigned from the rest.
- QA ticket already in the live production deploy: ready-to-close note. The runner checks live, then Done.
Never hand-write a one-off fix script. A fix that is missing goes into `plan_fixes` in board-health.

The assignee is the one record of who owns a ticket. Unassign a worker and its double clears at once.
Workers: the scope's workers in `scopes.json`, one ticket each.
- Tickets being built (In Progress or Doing, plus AI Review) never outnumber workers.
- Open PRs never outnumber workers. Each open PR sits on a ticket a live worker is building. See 6i.
- Merged tickets waiting for the live check (QA) have their own cap: 15 on board 15.
- Every ticket being built has one live assigned worker. No worker holds two.
- No live runner idles while orphans or queued tickets wait.
  `idle` red? The board lead runs `/runner-update` and `/runner-list` that turn. It looks at each idle pane and names why.
  Each idle runner takes an orphan first, then the queue. A `stale` ticket means its runner idles too.
The scorecard checks those plus steps 4 to 6f: wait limits, Agent Blocked, brain tags, CI, pristine blockers, chatter.

Each line is `OK`, `RED` or `ESCALATE`. A red line names its owner and the fix.
The brain line names which tool wrote the untagged tickets. Fix that tool, not only the tickets.
Each line shows "Was N, now M" since the last run. `TREND` shows tickets being built, in QA and total problems against the last run.
- You are not done until it prints `BOARD-HEALTH board N: GREEN`. Exit code 1 means red.
- Work the reds in order, top first. Then rerun.
- Your own lines (fleet chief, Chief Of Staff): fix them now.
- A lead's or CI Boss's line: one agent-lane note on its alarm ticket, with the tickets. Never do runner work yourself.
- Red over a day prints `ESCALATE`. `--apply` files or bumps one Urgent "Board health" alarm on 4060.
- Same line red on three runs in a row? The owner's loop is broken. Fix that loop's skill or script, not the tickets.
- The steps below are the detail behind each line. Run one when its line is red.

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
The same run holds the backlog cap on Fleet CI (11514) and Fleet Infra (4060): at most 2 open tickets per live pool runner. Over it, the oldest tickets untouched 7 days are archived with a note. Incident, busy, open-PR, waiting, security, alarm and app-blocking tickets are never archived.
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
House rule, CI snag (2026-11-06): one Fleet CI ticket per CI problem on 11514. Search first, +1 the existing one; new ticket only if none and the board is under its cap. `vcc` enforces it through `filing-gate`.
The app ticket stays on its board, linked BlockedBy that CI ticket, and waits. App sessions never fix CI.
Fix ships: CI Boss's `ci-unblock-waiters` posts a continue note in the app ticket's agent lane and clears the wait.

flow-check prints, per blocked ticket:
- `CI-WAIT`: CI ticket open, Urgent, In Progress, under 6 hours. Fine.
- `CI-SLOW`: CI ticket open over 6 hours, not Urgent, or not In Progress. CI Boss is behind.
- `CI-DONE`: CI ticket closed, but the ticket still waits. Its runner must resume.
- `CI-NO-TICKET`: CI failure blocker, no CI ticket. CI Boss never heard.
- `CI-NO-LINK`: a CI ticket is named in the log, but no BlockedBy link. `ci-unblock-waiters` will never wake it.
Then `CI-BLOCKED board N: X tickets wait on CI`.

Act on it:
- `CI-NO-TICKET`: search 11514 first and +1 the open ticket for the same problem. New Urgent ticket (labels CI and Hypertask CI) only if none and the board is under its cap; `filing-gate` refuses the rest. Link the app ticket BlockedBy it: `vcc task link <app ticket> <CI ticket> --type BlockedBy`.
- `CI-NO-LINK`: add that BlockedBy link.
- `CI-DONE`: the wait did not clear. Tell CI Boss its `ci-unblock-waiters` missed it, and the board lead which runner resumes.
- `CI-SLOW`: add a line in that CI ticket's agent lane. List the waiting tickets and hours.
- `CI-SLOW` again on the next run? File one Urgent alarm on 11514 for CI Boss.
- `CI-BOSS-QUIET`: no CI Boss note on the blocking CI tickets for 6 hours. CI Boss is likely not running. Tell Chief Of Staff, who restarts leads.

Who can write on 11514: Chief Of Staff and CI Boss. The shared vcc login can tag there, but its agent lane says "Task not found".
Can't write there? Post the CI list in each blocked product ticket's agent lane. Then hand it to Chief Of Staff.

## 6h. Find tickets in the wrong column
Valentin, 2026-11-06:
> a bunch of tickets that are in AI review, but really the feature is already in the app ... the runner just forgot to move it

`~/.local/share/house-rules/skills/hypertask-triage/scripts/wrong-status --board 15`
Also 4060, 11514, and Software Factory 2060. board-health shows it as the `status` line.

It reads every GitHub PR link on each work ticket and asks GitHub for the newest PR's state.
- `MERGED-NOT-MOVED`: PR merged, ticket still before merge. Board 15: move to QA for the live proof. Other boards: merged means released; check it live, then Done.
- `PR-CLOSED`: PR closed unmerged, none open. Back to its home column.
- `NO-PR`: in AI Review with no PR. Back to its home column, or add the PR link.
It only reads. The board lead moves them, as its agent, with the reason in the agent lane.
Same runner forgets twice? Fix its ship step, not the ticket.

## 6i. Keep the PR queue no longer than the workers
Valentin, 2026-11-07:
> the hyper task PRQ is currently 35. That should not be possible. If every runner stays on the ticket until it's live, there should not be no backlog in the queue.

`~/.local/share/house-rules/skills/hypertask-triage/scripts/pr-queue --scope 15`
board-health shows it as the `prq` line. Owner: the scope's lead.
It reads open PRs on the scope's repos. It finds each PR's ticket by the key in its title or branch.
The ticket's real board and view decide the scope, never the PR author or branch name.
- `OK`: a live worker is assigned and the ticket is being built.
- `ORPHAN`: no live worker on it. Hand the ticket to an idle runner; the PR comes with it.
- `NOT-A-WORKER`: a lead or advisor holds it. Hand it to a runner.
- `WRONG-COLUMN`: a live worker has it, but it sits in the queue. Move it to the building column.
- `DUPLICATE`: an older PR for the same ticket. Close it, link the newer one.
- `TICKET-CLOSED`: the ticket is done or archived. Close the PR, or reopen the ticket.
- `STALE-TICKET`: the ticket is in QA but its PR is open. Back to AI Review.
- `PARKED`: the ticket waits in Agent Blocked, Valentin Review or UX. Clear the wait.
- `NO-TICKET`: no ticket key. File or link one.
- `BOT`: dependabot. CI Boss's, not counted against workers.
It only reads. Closing PRs stays with the lead, as its own GitHub identity.
Same line red three runs in a row? The runner picker skips the PR queue. Fix `fleet/pick` in house-rules.

## 6f. Keep tickets clean: count chatter and fix its origin
Valentin, 2026-11-06:
> Every bot has currently this problem that agent chatter is just out of control ... force the chief of staff for each of the departments to run this skill and then get active fixing the house rules that caused the agent chatter on the ticket.

`~/.local/share/house-rules/skills/hypertask-triage/scripts/ticket-check --board 15 --alarm-board 4060`
Run it for each board your fleet writes on.

It lints every new ticket and people comment from the last 24 hours, with ticket-lint.
It splits the breaks by origin:
- `ORIGIN code`: a job or app code writes it. Fix the code. Add the count to its owner ticket, or file one.
- `ORIGIN agent`: an agent login wrote it. Find the skill or rule that told it to. Fix that with `/house-rules-update`, plus a lint or tool refusal. A longer note is not a fix.
- `ORIGIN personal`: Valentin's own login. Find the tool using it. Move it to an agent login.
Never fix the tickets one by one. Fix what writes them.
10 or more agent items: it files one Urgent "Chatter" alarm on the alarm board, or bumps the open one.
The fleet chief owns that alarm until the next count is under 10.

## 6g. Keep agent logins in sync with runners
Valentin, 2026-11-06:
> runners create new agent identities, but they do not frequently release the old ones

Valentin, 2026-11-08:
> why would e keep a round a dismantled runner idenitty. of course deletion!!!!!!!!

`~/.local/share/house-rules/skills/hypertask-triage/scripts/agent-identities`
board-health runs it on board 15 as the `identities` line. Owner: Chief Of Staff.

Per runner pool it compares active logins with live runner sessions on this server.
- `EXTRA`: logins with no live session.
- `DUPLICATE`: one name, more than one active login. One agent, one identity.
- Pools on another server (inne) are listed, not judged.
Fix: `board-health --board 15 --fix` (hourly timer) runs `agent-identities --apply`. It deletes EXTRA logins after 24 hours, unless a live process uses them. Never the Runner N pool or inne. Log: `~/.local/state/agent-housekeeping/deleted-<date>.json`.
Duplicates: delete the unused one yourself, per `/agent-housekeeping`. No ticket, no Question.
Changed the runner count, or restarted runners? Reuse each runner's login. Never mint a new one. Rerun this check the same turn.

## 7. Report to Valentin
Caveman:
- Archived N of M done tickets.
- Kept K, grouped by reason, each a full https link.
- Blockers: N wait on you, X cleared, Y badly written, notes posted. Pristine: X of N. Agent Blocked clean: X of N.
- Levers found, each with what it ends.
- Out of place: In Progress count against live runners, then counts per flag and column.
- No brain tag: X of Y open tickets, per board.
- Blocked by CI: X tickets, counts per CI flag, slow CI tickets as links.
- Chatter: X bad items, split code, agent and personal. Top writer each, and the rule you changed.
- Agent logins: extra and duplicate counts per pool.
- PR queue: open PRs against workers per scope, counts per verdict, orphan PRs as links.
- Wrong calls fixed in the rule, if any.

Auto-archive of done tickets on a timer comes later, after Valentin trusts the manual runs.
