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

## Output: caveman, very little text, mostly numbers
- Use /caveman voice. Max about 10 lines. No prose paragraphs, no per-manager lines.
- Line 1: window.
- Then numbers, one per line: Done, merges, releases (with latest version), runners, CI.
- One highlight block (a `>` quote) with the single most important thing.
- Broke: one line, or skip if nothing broke.
- Needs you: one line per item, full https link plus a pick. Or "nothing waits on you".
- Never invent numbers. Mark a guess as a guess. Name a source that failed.
