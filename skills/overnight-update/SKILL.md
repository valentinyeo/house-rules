---
name: overnight-update
description: >-
  Run for /overnight-update or when the owner asks what happened overnight /
  while they slept: each manager's night in one line, what shipped, what broke,
  what waits on the owner.
---
# Overnight update

Read-only. Never write to the board, GitHub, servers or sessions while gathering. Never print secrets.

## Window
- Default: owner's last message (or 20:00 local if unknown) until now, owner's time zone.
- Say the window in the first line.

## Inputs (defaults for Valentin's setup)
- Runner host: hypertask-vps (ssh from his desktop). Managers live in tmux sessions there.
- Managers: every manager or control session on the host (e.g. HT Product Lead, Mini Boss CEO / Software Factory manager, board managers). Find them by session and pane title; list any you could not map.
- Boards: Hypertask (HTPR project 15, YPER4 project 4060, IGSH project 2060, plus any board a manager owns).
- Repos: hypertask-ai org on GitHub. App releases: Wazig and Multiprompt (releases reaching his devices count as the real "updates").

## Steps
1. Per manager: read its pane scrollback and session log for the window. Capture what it decided, shipped, got stuck on, and asked the owner. Quote nothing long.
2. Board: tickets moved to Done in the window (from move history, not current column), new tickets, tickets now blocked or waiting on the owner. Flag state per Done ticket: everyone, owner-only, or dark.
3. GitHub: merges to default branches in the window, open PRs stuck (conflict, red checks, idle 2h+), production CI state now.
4. Releases: any new app build or deploy that reached users or the owner's devices. Failed deploys.
5. Fleet health: runners or managers that died, restarted or sat idle 1h+ in the window; rate limits or quota hits; any model id with "fast" (hard rule: fast off).
6. Owner queue: every question or approval a manager or agent left for the owner, with link.

## Output
- Owner voice rules apply (Valentin: caveman + pospeak, full clickable links, short).
- Line 1: window, and the one thing that matters most.
- Then one line per manager: shipped / stuck / asked.
- Then numbers: Done (by flag bucket), merges, releases.
- Then what broke, if anything.
- End with what needs the owner, each with a pick and one-line risk. Say "nothing waits on you" when true.
- Label inference. Name any source that failed. Never invent numbers. Quiet night = say so in one line.
