# Runner pipeline

Read when you run, pick, resume or leave a ticket as a pool runner, or when you review how runs are counted.

## One owner per ticket

The owner is a role. It carries one ticket and its PR from build to Done. Only the owner pushes, rebases or retargets the branch. A fresh agent takes each round with the prior report and branch. Steps:

1. Build: opens the PR.
2. Verify: a GitHub hosted check, from a model family other than the author's, posts a verdict on the current head. A new push needs a new verdict.
3. Fix: a finding, a FAIL or a merge clash goes to a fresh agent.
4. Merge: a per-PR script, no model. It merges on a pass at the current head and updates the branch if behind. No merge robot, no shared queue.
5. QA: live check.
6. Done.

The model never waits inside a run. It ends the run while review and checks run. The picker starts a fresh agent on red (Fix) or after the merge (QA). Software Factory apps with a release on merge: `fleet/sf-release-watch` checks the release names the ticket, then Done.

## Runs

- A run is one agent start to its stop. Every model run on a ticket counts, the reviewer's too.
- One ticket usually takes 3 to 5 runs: Build, review rounds, QA. Merge is a script step, not a run.
- Fine runs: Build, Verify, Fix (a finding, a real red check or a merge clash), QA, a retry by cause, Too hard (brain up one step), Valentin's own call.
- Fixes stay small and at the cause. Never a new robot, gate or flow without Valentin's yes.

## Ready and picking

- A pickable ticket is one-run ready: one deliverable, one done line, one brain tag, not blocked, no open Valentin call.
- An agent owns one ticket at a time.
- Pick order: orphaned pipeline tickets, Urgent new work, the PR queue, new work.
- New work is shared equally between boards 15 and 2060, then across apps within a board: the app with the fewest tickets in work and runs in 24 hours goes first. Then the priority field: Urgent, High, Medium, Low.
- WIP cap (shared pool only; solo devs are uncapped): work being built never outnumbers live runners. That counts building columns plus open PRs. At or over the cap, no new work starts. Runners take incidents, own tickets, orphans and PRs. Blocking or Urgent Fleet CI & Infra tickets still go out. An idle rest without a blocker lasts 2 hours.
- A stopped agent's ticket goes to a fresh agent with the prior report and branch.
- CI blocks the PR? File it per the CI snag rule in `reference/boards.md`.
- A ticket in Not now is parked by Valentin. Runners never take it. Board 2060 has the column, before Todo. Add it to any board that needs one.

## Leaving a ticket

- The owner role delivers its ticket. Replace a stalled or looping agent. Judge it by pushes and PR activity, not status text.
- Retry by cause: smaller scope after a context or memory limit, same kickoff after a dropped connection or provider outage, a different model after a tool error. After two retries, drop the unit and replan.
- Too hard: leave only as `RUNNER TOO HARD <KEY> | why: ...`. The brain tag goes up one step and a stronger runner takes it. Extra-hard goes to its lead.
- Valentin's own call: Valentin Review plus one Question. The owner keeps the ticket.
- Waiting on a person is not a state. That ticket goes to its lead.

## Incident lane

A board 15 ticket with the `incident` label means app.hypertask.ai is down or badly broken for customers. Any runner takes it first, whatever it holds, on grok-4.7 high.

1. Roll back first, then fix forward.
2. Merge a green fix without waiting on the queue.
3. Post a short people comment when live is healthy.

A Fleet CI & Infra (11514) ticket with the `incident` label means the release pipeline is broken. It takes the same lane with `fleet/briefs/release-stop.txt`.

## Solo devs and roles

- Solo devs drain their whole view, overnight too. Client solo devs drain their own whole board. Idle 15 minutes with an open ticket: `fleet/solo-wake` wakes the session and names the next ticket.
- Multi Bot Opus Runner writes tickets first. It files Multi Bot work unassigned in Todo. It builds only hard tickets or ones Valentin waits on live.
