---
name: runner-update
description: Runner status and top-up for a project manager. Use when asked for "runner update", "/runner-update" or runner status, and at every manager check-in. Counts your project's Claude Code and hax (Codex) runners, checks server load, fixes gaps, then reports problems first and green in short lines.
---

# /runner-update

Check [manager-shift](../manager-shift/SKILL.md) before this work batch.

Your job as manager: check the shared runner pool and fix gaps (`reference/roster.md`). Report only after you act.

You start no runners (Design, Growth or Finance lead)? Stop here. Do not count runners.

## 1. Count your project's runners only

| Project | Claude Code runners | hax (Codex) runners |
|---|---|---|
| Hypertask | tmux `ht-or-runner-N` via `fleet/runner`; `fleet/pick` offers tickets | same pool; `fleet/runner status` |
| Software Factory | sessions `ceo-runner-6..10` | sessions `hax-runner-1..10`; `~/projects/ceo/bin/hax-runner <n>` |
| Other | read your project's setup skill or RUNNER.md | same |

For each runner: active (working a ticket now) or idle. For every idle one, name the reason (no tickets, load hold, login failed, dead pane, stuck prompt). Look at the pane (`tmux capture-pane -p -t <target> | tail -20`); don't guess.

## 2. Check the load

- `~/.local/state/vps-load/status`: `add` = room to launch, `hold` = full.

## 3. Act

- Launching = your project's own launcher (table above). No add-runner skill needed.
- While load says `add`, `fleet-switch` adds pool runners. Never revive retired per-lane launchers.
- Restart dead or stuck runners. Unstick panes waiting on a prompt.
- Idle for "no tickets"? Get tickets written or groomed. That is your gap to close.
- Cross-check with `/hypertask-triage` step 0: its `idle`, `orphans` and `stale` lines must be OK when you finish.

## 4. Report
First line, always: the output of `~/.local/share/house-rules/fleet/yield` (runs against built per plan). A RED plan comes before anything else, with what you did about it. Runner counts are motion, not results.

Use the [shipping-update](../shipping-update/SKILL.md) shape. Add one "Runners" section: claude X/Y, hax X/Y on one line, then every runner in the [runner-list](../runner-list/SKILL.md) format. Idle ones carry their reason and what you did.

Never say "0 hax by design". Zero hax is a gap: say why and what you did.
