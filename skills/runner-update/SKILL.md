---
name: runner-update
description: Runner status and top-up for a project manager. Use when asked for "runner update", "/runner-update" or runner status, and at every manager check-in. Counts your project's Claude Code and hax (Codex) runners, checks the token ladder and server load, fixes gaps, then reports problems first and green in short lines.
---

# /runner-update

Check [manager-shift](../manager-shift/SKILL.md) before this work batch.

Your job as manager: keep your project's runners full. Report only after you act.

You start no runners (Design, Growth or Finance lead)? Stop here. Do not count runners or read the ladder.

## 1. Count your project's runners only

| Project | Claude Code runners | hax (Codex) runners |
|---|---|---|
| Hypertask | tmux `ht-runners` panes titled `RUNNER N` / `SPEED RUNNER` | sessions `ht-hax-runner-N`; `~/.local/bin/ht-hax-runner status` |
| Software Factory | sessions `ceo-runner-6..10` | sessions `hax-runner-1..10`; `~/projects/ceo/bin/hax-runner <n>` |
| Other | read your project's setup skill or RUNNER.md | same |

For each runner: active (working a ticket now) or idle. For every idle one, name the reason (no tickets, load hold, ladder brake, login failed, dead pane, stuck prompt). Look at the pane (`tmux capture-pane -p -t <target> | tail -20`); don't guess.

## 2. Check the limits

- `~/.local/bin/token-ladder status`: Claude, Codex, Grok pools.
- `~/.local/state/token-ladder/codex-signals.md`: reset expiries, Codex promo days. Resets in hand = push harder.
- `~/.local/state/vps-load/status`: `add` = room to launch, `hold` = full.

## 3. Act

- Launching = your project's own launcher (table above). No add-runner skill needed.
- Codex (hax) is never braked. Only server load limits it. While load says `add`, start hax runners up to target (Hypertask: `ht-hax-runner top-up`; SF: `hax-runner <n>`).
- Claude runners follow the ladder. Claude is scarce: brake only Claude.
- Restart dead or stuck runners. Unstick panes waiting on a prompt.
- Idle for "no tickets"? Get tickets written or groomed. That is your gap to close.

## 4. Report

Use the [shipping-update](../shipping-update/SKILL.md) shape. Add one "Runners" section: claude X/Y, hax X/Y, each idle one with its reason and what you did.

Never say "0 hax by design". Zero hax is a gap: say why and what you did.
