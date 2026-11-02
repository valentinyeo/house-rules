# Fleet add-on: Hypertask (HT Product Lead)

- Repo: hypertask-ai/hypertask (public). Branch off and merge to `production`; merge deploys app.hypertask.ai.
- Boards: 15 Hypertask Product (app work, flag columns are the finish line), 4060 Fleet Infra (runner and CI work).
- Board writes: `vcc` only. People comments `--kind qa|question|done`; agent talk `vcc activity add`.
- Runners: Claude panes in tmux `ht-runners`; hax Codex `ht-hax-runner-N` (`ht-hax-runner status`, `top-up`). Codex never braked; load limits only.
- Each turn: read `~/.local/state/fleet-idle/latest.txt` first; idle fleet is the biggest blocker. Written every 15 min by `fleet-idle-watch` (hypertask-poteto).
- Pick order: urgent 15, urgent 4060, rest of 15, rest of 4060.
- Feedback: open `ai-feedback` tickets on board 15 are yours to sort and drain (cap 20 in `pileup-watch`). Agents file them with `skills/hypertask-triage/scripts/agent-feedback`.
- Freeze exceptions: `~/.config/fleet/infra-first-allow`, one key per line.
- Flags: `.claude/skills/ship/scripts/ht-flag`. Switches need Valentin's yes, except the failure Off.
- Focus now: drain open PRs, then lift the freeze. Cut AI and Vercel cost (HTPR-8100, YPER4-876). Then cut checks and skills (YPER4-865).
