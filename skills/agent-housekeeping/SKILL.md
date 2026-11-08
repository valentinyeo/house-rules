---
name: agent-housekeeping
description: Weekly cleanup of Hypertask agents and boards for Team Hypertask. Lists every agent and board, deletes dismantled runner logins itself, flags other agents with no live user or no activity for 7 days, and writes an inventory file. Use every Monday, when Valentin says "agent housekeeping", "remove old agents", or when there are too many agents or boards.
---

# Agent housekeeping

Never print a token.

Valentin, 2026-11-08:
> i declared about 500 times if i give a direct order why would that not be a YES already
> why would e keep a round a dismantled runner idenitty. of course deletion!!!!!!!!

So:
- Dismantled runner logins: delete them yourself. No ticket, no Question.
- Anything else Valentin orders removed, in chat or on a ticket: his order is the yes. Do it that turn. Never file a confirm ticket.
- Other agents and boards, with no order from him: one Question on one ticket.

## Rules

- Each live session has one agent. Lead sessions are named `HT <Role> Lead`. Runner sessions are named `RUNNER N`. The session name slug must match a token file in `~/.config/hypertask-agents/credentials/sessions/`, which ship-identity uses.
- Dismantled runner login: a per-fleet runner login (CI, Infra, CEO, Hax, Multi Bot, MP Runner and similar) with no live session for 24 hours and no live process using it.
- Never delete: the shared pool logins Runner 1-17, leads, experts, solo devs, specialists, anything in `fleet/roster.json` that has a live session, inne agents, Wazig agents.
- Duplicate names: keep the login a live session or token file uses. Delete the rest.
- A live user is one of these: a live Claude session with a matching token file, a live hax runner, a user systemd timer or service that reads its token, or a webhook process.
- A board is flagged when it has no members, or no update for 30 days, or 0 open tickets.

## Steps

1. Delete dismantled runner logins: `~/.local/share/house-rules/skills/hypertask-triage/scripts/agent-identities --apply`. It deletes logins extra for 24 hours and logs each to `~/.local/state/agent-housekeeping/deleted-<date>.json`. The hourly `board-health --board 15 --fix` runs it too.
2. List the agents: `ht GET "/mcp/admin/agents?limit=100"`, then follow `nextCursor`.
3. List the boards: `ht GET "/mcp/projects?limit=100"`. For each board, count open tickets, the last update, and open tickets per agent assignee.
4. Find the live users:
   - Live Claude sessions: `~/.claude/sessions/<pid>.json` where the pid is alive, plus `tmux ls`.
   - Hax runners: the `SHIP_SESSION_NAME` and `CEO_AGENT` values in each runner's environment.
   - Timers and scripts: `systemctl --user list-timers --all`, plus grep `~/.local/share/house-rules/fleet`, `~/projects/*/bin` and `~/.local/bin` for token file names.
   - Match each token file to an agent id by decoding only the payload `agentId`. Never print the token.
5. Delete by hand what step 1 cannot see: dismantled runner duplicates and runner pools it does not know. Path: `ht DELETE /mcp/agents/<id>` (Valentin's saved CLI login, admin only). Grep launchers first; a live user keeps its login. Log each to the same state file.
6. Write `~/poteto-handover/agent-inventory-<YYYY-MM-DD>.md` with counts, what you deleted, and what is left with reasons.
7. Other agents or boards to remove, with no order from Valentin: one Question on one ticket on YPER4, Valentin Review. Last week's ticket still open? Comment there.

## Watch out

- Delete keeps comments with the author name. It drops board memberships and ticket assignments. Those tickets go back to the queue.
- The first delete of a new kind: check one of its old comments still shows afterwards.
- After a delete, its local token file is dead. Leave the file; the secrets guard owns that folder.
- Agents of other teams are listed separately and are not counted.
