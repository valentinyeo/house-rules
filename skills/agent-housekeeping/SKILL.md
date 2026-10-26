---
name: agent-housekeeping
description: Weekly cleanup check of Hypertask agents and boards for Team Hypertask. Lists every agent and board, flags agents with no live user or no activity for 7 days, writes an inventory file and files one ticket with the proposed removals. Never revokes or archives anything. Use every Monday, when Valentin says "agent housekeeping", or when there are too many agents or boards.
---

# Agent housekeeping

Read only. Never revoke, archive, rename or delete an agent or board. Only Valentin can say yes, and he says it on the ticket. Never print a token.

## Rules

- Each live session has one agent. Lead sessions are named `HT <Role> Lead`. Runner sessions are named `RUNNER N`. The session name slug must match a token file in `~/.config/hypertask-agents/credentials/sessions/`, which ship-identity uses.
- An agent is flagged when it has no live user, or no ticket activity for 7 days.
- A live user is one of these: a live Claude session with a matching token file, a live hax runner, a user systemd timer or service that reads its token, or a webhook process.
- A board is flagged when it has no members, or no update for 30 days, or 0 open tickets.

## Steps

1. List the agents: `ht GET "/mcp/admin/agents?limit=200"`, then follow `nextCursor`. Also list `hypertask --json context` all_agents, because legacy agents only show there.
2. List the boards: `ht GET "/mcp/projects?limit=100"`. For each board, read every task with `hypertask --json tasks list --project <id>`. Count the open tickets, find the last update, and count the open tickets per agent assignee (use `assignees[].agent.id`).
3. Find the live users:
   - Names of live Claude sessions: `~/.claude/sessions/<pid>.json` where the pid is alive and `nameSource` is `user`.
   - Hax runners: the `SHIP_SESSION_NAME` and `CEO_AGENT` values in each runner's environment.
   - Timers and scripts: `systemctl --user list-timers --all`, plus grep `~/.local/bin` and `~/.local/lib/hypertask` for token file names.
   - Match each token file to an agent id by decoding only the payload `agentId`. Never print the token.
4. Classify each agent:
   - KEEP: it has a live user.
   - REMOVE: it has no live user and no activity for 7 days, or it is a duplicate, a test agent or a replaced name. State the risk, such as open tickets to reassign or a timer to stop first.
   - ASK: anything unclear, including Grok Bot bots that may be hibernating.
5. Classify each board:
   - KEEP: active.
   - ARCHIVE: empty, a test board, or no members and idle.
   - ASK: idle but still holds cards in review.
6. Write `~/poteto-handover/agent-inventory-<YYYY-MM-DD>.md`. It holds the counts, a table per class with ids and reasons, how the data was built, and what is unproven. Last week's file shows what changed.
7. File one ticket on YPER4 called "Agent housekeeping <date>: proposed removals". List the REMOVE and ARCHIVE items, each with a one-line reason and its risk. List the ASK questions. Link the inventory file. Assign it to Valentin, in Valentin Review. If last week's ticket is still open, add a comment to it instead of filing a new one.
8. Stop there. Revoke or archive only the items Valentin approves on the ticket, and only in a later run that he asks for. After a revoke, delete that agent's local token file and its link.

## Watch out

- The API has no team field on boards. Group boards by the agents they share, because an agent can only be on boards of one team. Say which boards are not proven.
- Token-file read times are a weak signal. Bulk scans touch many files at the same minute.
- Agents of other teams are listed separately and are not counted.
