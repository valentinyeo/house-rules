# Roster, roles and managers

Read when you set up a session, change a role, start or stop runners, or work with another manager.

## The factory

- One factory: one picker, one runner pool, three boards (15, 2060, 11514). Plan and roster: https://yeoux.net/reports/38361bb7-fleet-shape.html. A plan change updates this file, the page and `fleet/roster.json` the same turn.
- Chief Of Staff is the overseer above every manager and owns the factory: supervisor, picker, roster, pacer. Poteto runs as Chief Of Staff. The overseer runs Opus medium. Other sessions run Sonnet.
- Each org keeps its own managers and runners: Hypertask, Software Factory, clients (inne). Mini Boss CEO is the contact for Software Factory apps without their own session. It owns no runners and no board health.
- Each app with its own chat session is a solo dev (`skills/solo-dev/`). Apps without one are view-led (`skills/view-lead/`).
- Leads and experts decide. They own no runners.
- CI Boss is the CI expert: owns board 11514 and reviews CI fixes. Infra Lead is the tools expert for both fleets: owns no board, owns the Agent Feedback views on board 12057, and files infra work as tickets on 11514. Core product fixes go as tickets on board 15.
- Growth and Support leads have no runners. They ship their own repos: hypertask.ai (astro) for Growth; help chat (ai-chatbot) and docs for Support. They never touch the core product: that is a ticket on board 15. They use cheap helpers: hax Codex or Sonnet subagents.
- Leads without runners never check runners. Design, Growth, Support and Finance skip `/runner-update` and pace checks.

## The pool

- Every session's role sits in `fleet/roster.json`. Pool runners do all work: app, CI and infra.
- Features first. At most 1 runner on Fleet CI & Infra up to 5 live runners, 2 above that. Incidents only beyond it.
- One kept slot stays free for a real blocker: an open app ticket waiting on it, or an incident. Urgent app work goes before other infra.
- The other lane runners take tickets that block an app ticket. Quiet day: they build features.
- Runners go on or off through the pool launchers and `fleet-switch`. The pacer sets counts.

## Announcing

- Every session announces itself to the roster. Claude does it at start: a SessionStart hook runs `fleet/roster-announce --hook`. No roster row: run `fleet/roster-announce --kind KIND --board ID` once.
- One session may hold several roles. Its roster row lists them in `roles`. Announce every role: `fleet/roster-announce --roles lead,solo-dev`.
- A solo dev or solo operator works like a runner. It assigns itself to every ticket it builds.

## Deadlock and blockers

- Factory deadlock: half or more runners wait on one shared block (review limit, CI, broken tool). Chief Of Staff breaks it that turn. It launches its own helper to remove the block. The helper may merge its own unblock fix with one admin bypass, logged in `goal/decisions.jsonl`. Then runners resume.
- Leads with runners empower and never do runner work. Every block fix ships as a skill, tool or script. No agent gets blocked twice for one reason.
- Report blockers to your own project's lead, never another project's manager. Solve your own project's problems first.
- No agent-to-agent messaging unless Valentin asks, per case. Agents talk on tickets. Stuck after two tries: mark the ticket blocked on HT Product Lead and write why, then take the next ticket.
- Managers run `/manager-shift` at every check-in. Chief Of Staff runs `/runner-update` at every check-in.

## Identities

- One agent, one identity, across all teams. Never create a second login for the same agent.
- Chief Of Staff changes, closes or restarts runners: reuse each runner's login. Never mint a new one. Rerun the identity check the same turn.
- A dismantled runner login has no live session for 24 hours and is not a fixed pool login in `fleet/roster.json`. Chief Of Staff deletes it and never asks. Never delete Runner 1-17, leads, inne or Wazig.
- `/agent-housekeeping` runs every Monday. One agent per live session, named `HT <Role> Lead` or `RUNNER N`. Other agents: delete only on his direct order, else one Question on one ticket.
- No agent-to-agent messaging unless Valentin asks, per case. Agents talk on tickets.
- Cross-manager messages only when Valentin asks, or to announce a house-rules change.
