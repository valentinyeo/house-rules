# Brain map

Read when you pick a model, launch a runner, set a brain tag or hand a task to a helper.

## Brain per ticket

Every runner, any harness, takes its brain from the ticket's brain tag. No tag: the medium brain. Skip means the runner leaves that ticket.

| Harness | Light | Medium | Hard | Extra-hard |
|---|---|---|---|---|
| Codex | Terra medium | Sol medium | Sol high | Sol high |
| Anthropic | Sonnet medium | Sonnet medium | Opus or Sonnet high | Opus 5.5 medium or high |
| DeepSeek | 4.1 Flash low or medium | 4.1 Flash high | skip | skip |
| Vercel pass (DeepSeek) | 4.1 Flash low | 4.1 Flash low | skip | skip |
| Grok | skip | grok-4.7 | grok-4.7 high | skip |

- Extra-hard runs on Codex Sol high. Claude Opus runs it only on his order. Other engines skip it.
- Composer is removed.
- App runners `ht-or-runner-1..10` use the `ht-or-runner-pick` brain rows, not the Codex ladder below.

## Codex ladder (both fleets)

- Runner runs gpt-6.1-sol medium: plans, reviews, decides.
- Code edits go to a helper: `hax --provider=codex --model=gpt-6.1-terra --effort=medium -p "<task>"`.
- Lookups, logs, summaries: `--model=gpt-6-luna --effort=low`.
- Sol high only for hard bugs, security, money.
- Delegate by default. Helpers run in background.

## Claude workers

- Spawn a fresh worker for each independent task. Brief it with the goal, the evidence that proves it done, the paths it may write and the actions it must not take.
- Claude workers may use Codex helpers: terra medium for code, luna low for lookups. Helpers are sub agents, not runners. Claude keeps plans, checks and merges.
- Extra parallel work: separate hax Codex sessions, as many as server load allows, each Codex-only on its own ticket.

## Choosing a tag

Choose per `~/projects/poteto-2-advisor/brain-rules.md`.

- Light: tiny fix, one file.
- Medium: default, normal work.
- Hard: hard bug, security, money, many systems.
- Extra-hard: rare, auth or security plus money. Runners skip it.
- Unsure between medium and hard: medium. Never two tags. Never blank.

## Pstack roles

- Code, bug-fix and judgment: Sonnet high. Opus medium only for the hardest tasks. Lookups: Haiku. Set in `~/.claude/rules/pstack-models.md`.
- Say "DeepSeek 4.1 Flash", never "V4.1".
