---
name: overnight-update
description: >-
  Run for /overnight-update or when the owner asks what happened overnight /
  while they slept: the running manager's own domain only, as numbers plus one
  highlight block, caveman voice.
---
# Overnight update

Read-only. Never write to the board, GitHub, servers or sessions while gathering. Never print secrets.

## Scope: your domain only
- Report only the project you manage: your board, your repos, your app releases, your runners.
- Never report other managers or other projects. (2026-10-26, Valentin: "focus only on his domain")

## Window
- Default: owner's last message (or 20:00 local if unknown) until now, owner's time zone.

## Gather
1. Board: tickets moved to Done, new tickets, tickets waiting on the owner.
2. GitHub: merges to default branches, stuck PRs, CI state now.
3. Releases that reached the owner's devices. Failed deploys.
4. Your runners: active, idle, died. Quota hits. Any model id with "fast".

## Output
- Use the [shipping-update](../shipping-update/SKILL.md) shape. Window replaces "last 3 hours"; compare with the same window on the last 3 nights.
- Add "Needs you": one line per item, full https ticket link plus a pick. Or "nothing waits on you".
- No ticket for a broken item yet? File one first, then link it. (2026-10-26, Valentin: "each item needs ticket links")
