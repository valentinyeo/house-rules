# Fleet add-on: Hypertask (HT Product Lead)

- Repo: hypertask-ai/hypertask (public). Branch off and merge to `production`; merge deploys app.hypertask.ai.
- Boards: 15 Hypertask Product (app work, flag columns are the finish line), 11514 Fleet CI & Infra (runner, CI and infra work).
- Board writes: `vcc` only. People comments `--kind qa|question|done`; agent talk `vcc activity add`.
- Runners: one shared pool via `fleet/pick` and `fleet/runner` (tmux `ht-or-runner-N`). Load limits only.
- Each turn: read `~/.local/state/fleet-watch/latest.txt` first; idle fleet is the biggest blocker. Written every 15 min by `fleet-watch` (house-rules).
- Pick order: urgent 15, urgent 11514, rest of 15, rest of 11514.
- All agent feedback, app and agent tools, lands on board 12057 HT Agent Feedback (HTFE), never board 15. Filed with `skills/hypertask-triage/scripts/agent-feedback`. HT Product Lead owns and drains it. (2026-11-05, why: "we def need to own the agent stuff")
- Freeze exceptions: `~/.config/fleet/infra-first-allow`, one key per line.
- Flags: `.claude/skills/ship/scripts/ht-flag`. Switches need Valentin's yes, except the failure Off.
- Focus now: drain open PRs, then lift the freeze. Cut AI and Vercel cost (HTPR-8100, YPER4-876). Then cut checks and skills (YPER4-865).
