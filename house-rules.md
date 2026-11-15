# House rules

Standing rules for every agent that works for Valentin.

## Which rule wins

When two rules disagree, the higher one wins.

1. This file.
2. pstack.
3. Any other rule or skill.

## How to work

- Use pstack for all work. pstack is Lauren Tan's plugin at https://github.com/cursor/plugins/tree/main/pstack.
- Start every task with `poteto-mode`.
- Orchestrators run the Orchestrate playbook.
- The only exception is work that pstack does not cover.
- Start new Cloudflare work from the `joelhooks/rat-stack` template.

## Tickets

Hypertask is where work lives.

- Every unit of work starts and ends on a ticket.
- Keep the ticket on the orchestrator's own board or view, under the orchestrator's own login. The [board-identity](skills/board-identity/SKILL.md) skill sets that up.
- Move the ticket to the next column the moment its work moves. The board must always show the true stage.
- Put status and questions on the ticket, not in chat.

## Verifying a PR

- Every PR gets a pstack verifier before merge. The verifier is an agent that did not write the PR, from another model family. It runs the change like a user and posts `PASS`, `PASS+NOTES` or `FAIL` on the PR. pstack's Shipping playbook has the rest.
- A bot review or green CI is not a verdict.
- Run verifiers off the VPS (hypertask-vps), on a GitHub-hosted runner, Claude Code cloud or Codex cloud.
- Orchestrators may use Valentin's Codex, Claude and DeepSeek plans for verifiers, keys included. Use them in that order, skip the family that wrote the PR, and move to the next plan when one runs out. You do not need to ask.

## What Valentin decides

- Valentin decides money, keys, going public and deleting live data. Ask him once, with your pick. The verifier plans above are already granted.
- GitHub billing is Valentin's. When a check fails with "recent account payments have failed", the product PR waits. Never verify it on the VPS or merge around the check. Say it once on the ticket, then build the next unit.

## Enforced by scripts

Everything else is a check, not a rule. A script enforces it, so you do not need to remember it.

- `no-vps-ci` stops CI on the VPS.
- `secrets-guard` blocks secrets.
