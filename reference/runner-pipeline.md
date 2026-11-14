# Runner pipeline

Read when you run, pick, resume or leave a ticket as a pool runner, or when you review how runs are counted.

## One ticket, one runner

A runner keeps a ticket from build to Done. Steps, all by the same runner:

1. Build: opens the PR.
2. Review rounds: a Review run, then a Fix run, repeated until clean. The runner pauses while review and checks run, about 10 to 15 minutes.
3. Merge: a per-PR script, no model. It merges once review and checks pass and updates the branch if behind. A clash wakes the runner for a Fix run. No merge robot, no shared queue.
4. QA: live check.
5. Done.

The model never waits inside a run. It ends the run while review and checks run. The picker resumes the same runner on red (Fix) or after the merge (QA). Software Factory apps with a release on merge: `fleet/sf-release-watch` checks the release names the ticket, then Done.

## Runs

- A run is one runner start to its stop. Every model run on a ticket counts, the reviewer's too.
- One ticket usually takes 3 to 5 runs: Build, review rounds, QA. Merge is a script step, not a run.
- Fine runs: Build, Review, Fix (a review finding, a real red check or a merge clash), QA, Outage (provider down, resume), Too hard (brain up one step), Valentin's own call. Every other run is a violation.
- Fixes stay small and at the cause. Never a new robot, gate or flow without Valentin's yes.

## Ready and picking

- A pickable ticket is one-run ready: one deliverable, one done line, one brain tag, not blocked, no open Valentin call.
- A runner never takes a new ticket while it owns one in In Progress, AI Review or QA. Exception: its ticket waits on something outside the runner 30+ minutes. Then it takes one more. The first wins every pick. Max 2.
- Pick order: orphaned pipeline tickets, Urgent new work, the PR queue, new work.
- New work is shared equally between boards 15 and 2060, then across apps within a board: the app with the fewest tickets in work and runs in 24 hours goes first. Then the priority field: Urgent, High, Medium, Low.
- WIP cap (shared pool only; solo devs are uncapped): work being built never outnumbers live runners. That counts building columns plus open PRs. At or over the cap, no new work starts. Runners take incidents, own tickets, orphans and PRs. Blocking or Urgent Fleet CI & Infra tickets still go out. An idle rest without a blocker lasts 2 hours. Paused work returns to its starting runner.
- Temporarily stopped runners keep their tickets. Only permanently removed roster slots become orphans.
- CI blocks the PR? File it per the CI snag rule in `reference/boards.md`.
- A ticket in Not now is parked by Valentin. Runners never take it. Board 2060 has the column, before Todo. Add it to any board that needs one.

## Leaving a ticket

- A runner that takes a ticket delivers it.
- Valid leaves only: provider outage (API error, 5xx, rate limit, quota, model unreachable: the same runner resumes, or after 30 minutes the same brain on another plan), TOO HARD, runner removed from the roster, Valentin's own call (Valentin Review plus one Question, the runner keeps ownership).
- Too hard: leave only as `RUNNER TOO HARD <KEY> | why: ...`. The brain tag goes up one step and a stronger runner takes it. Extra-hard goes to its lead.
- Runners end on one listed state. An unknown state is a fault. Waiting on a person is not a state. That ticket goes to its lead. A third park in six hours stops offers.
- Chief Of Staff prevents excess runs. A script reads every run. For any leave that is not valid it wakes one Sonnet fixer at a time that fixes the cause at its source and writes one line to `goal/decisions.jsonl`. One fixer per ticket per day. There is no factory stop.

## Incident lane

A board 15 ticket with the `incident` label means app.hypertask.ai is down or badly broken for customers. Any runner takes it first, whatever it holds, on grok-4.7 high.

1. Roll back first, then fix forward.
2. Merge a green fix without waiting on the queue.
3. Post a short people comment when live is healthy.

A Fleet CI & Infra (11514) ticket with the `incident` label means the release pipeline is broken. It takes the same lane with `fleet/briefs/release-stop.txt`.

## Solo devs and roles

- Solo devs drain their whole view, overnight too. Client solo devs drain their own whole board. Idle 15 minutes with an open ticket: `fleet/solo-wake` wakes the session and names the next ticket.
- Multi Bot Opus Runner writes tickets first. It files Multi Bot work unassigned in Todo. It builds only hard tickets or ones Valentin waits on live.
