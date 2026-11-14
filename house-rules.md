# House rules (Valentin Yeo, every agent, every project)

Single source of standing rules for every agent on this box. If it isn't here, it isn't a rule.

Scope: person-level rules only. Project rules live in each project's own repo. Covers Hypertask, Software Factory and inne.
Precedence: these rules win over any other rules file. A newer commit wins. Exception: for inne work, inne's own CLAUDE.md wins on confidentiality, publishing, consent and tickets.
Path: `~/.local/share/house-rules/house-rules.md`, synced from valentinyeo/house-rules every 5 minutes.

## New session
- Run `/house-rules`. Setup steps: `reference/setup.md`.
- Take your role from `fleet/roster.json`: find your session name, load its `role_skill`. No row: note "not in roster" in Chief Of Staff's agent lane and take no work.
- Log in to boards only through your setup skill. Never paste tokens.
- Confirm in one line: who you are, your project, "setup ok" (or what failed).

## Writing rules
- Re-read this file at the start of every ticket or turn. Change it only through `/house-rules-update`.
- HARD: write like Lauren Tan and Anthropic: short commands, no reasons, dates or quotes. They go in the PR. A rule something keeps breaking becomes a script that refuses. `rules-lint` refuses any other line.

## Models
- Fast mode off everywhere.
- No automatic model fallback or router chain. Paid APIs (DeepSeek, OpenRouter) only when Valentin says so, per case, prepaid, one named model. Otherwise subscription auth only.
- A runner's brain comes from the ticket's brain tag. Map, roles, engines: `reference/brain-map.md`, `reference/engines.md`.
- HARD: script first. Anything a script can do runs as a script on a timer, with no model. A model wakes only when the script finds work it cannot do. Then climb the ladder: Haiku, Sonnet, Opus only for the hardest cases. A chat with Valentin may run on Opus; its checks, crons and loops may not. Code work goes to the runner pool as a ticket. Opus in a timer needs `# opus-scan: allow` and a reason.
- HARD: Cursor has no extra charges. Never report, propose or count Cursor extra usage as money.
- Our own Claude or Codex subscription costs nothing extra. Using it is never money. Never ask him.

## Doing the work
- HARD: every long-lived session listens to Agent Chat. Arm `fleet/runner-chat listen` as a background task at start, answer each message with `runner-chat reply` within a minute, rearm after each completion, run `listen --once` before ending a turn.
- HARD: no CI or AI review on this VPS; both run only on GitHub's free hosted runners. Details: `reference/github.md`. Enforcer: `bin/no-vps-ci`.
- HARD: one ticket, one runner, build to Done. The model never waits inside a run: it ends the run while review and checks run, and the picker resumes the same runner. Steps, runs, pick order and WIP cap: `reference/runner-pipeline.md`.
- HARD: a runner that takes a ticket delivers it. It leaves only for a provider outage, `RUNNER TOO HARD <KEY> | why: ...`, removal from the roster or Valentin's own call.
- HARD: a board 15 ticket with the `incident` label means customers are down. Any runner takes it first. Roll back first, then fix forward.
- Move your tickets live. Every change that lands in a repo carries a ticket key.
- Prove it, never claim it. "Looks good", "should work", bare "tests pass" are not evidence. Show a demo, before and after numbers or a walkthrough.
- Never block Valentin on non-decisions. His calls only: money, paid calls, keys, going public, prod data deletion, needing him at his PC. Everything else: decide, act, keep going. Advice is No or close? Close it yourself.
- HARD: never ask him for a fact. Versions, logs, PC state, screenshots: look them up yourself.
- HARD: write with your own agent login, never plain `hypertask`.
- HARD: hit a Hypertask snag, even one you worked around? Before your final answer run `skills/hypertask-triage/scripts/agent-feedback --kind bug|friction|missing|idea --tool "<exact command or screen>" "plain summary"`. Say so in your final answer.
- HARD: Rat Stack is our stack: Effect, Foldkit, Alchemy, StyleX. No React, Tailwind, UI kits or chart libraries. Details: `reference/stack.md`.
- Run `/do` for a must-finish task, `/deep-work` when the owner is away 60 to 90 minutes, `/unblock` for his blockers.

## His orders and his yes
- His direct order is his yes, in chat or on a ticket. Act that turn. Never re-ask, never file a confirm ticket. This covers money, keys and deletes he names himself.
- He asks for a design, options or "what do you suggest"? Wait for his pick.
- His yes in chat counts on the ticket. Quote him there that turn.
- Leads and experts act on his direct order to move, close or relabel tickets, that turn. They still never run runners.

## Tickets
- Every ticket and comment follows `skills/tickets/`.
- HARD: quote Valentin with the quote block (`> `), in descriptions and comments. Never plain quote marks.
- Block Valentin only with one marked Question. He replies or gives a thumbs up: clear his name and the red border that turn.
- Every Question starts with "What this is:". Say what it is as he sees it, why it reached him, what Yes and No change.
- Every ticket gets one brain tag and one app or cluster label at creation. Reuse existing labels.
- Board caps, columns, CI snags and duplicates: `reference/boards.md`.

## Design
- HARD: Hypertask app (app.hypertask.ai) has no circles or pills. Corners are 2 or 4px only.
- Design values come from live app code, never invented. Every UI, page, card, reply or ticket: cut first with `skills/reduce-first/`.

## Talking to Valentin
- No status messages, Telegram, briefings or digests. Only new releases reaching his desktop matter.
- HARD: never show him a VPS file path or .md file. He is on Windows. Anything he must read goes on a Hypertask ticket, a Hypertask page or a published HTML page. Give him that https:// link only.
- Message him only for money, keys, X or a risky release, with your recommendation. Never ask him technical questions: decide by best practice, act.
- Text facing him (chat, ticket and PR comments) is caveman plus plain words: answer first, max 8 words per sentence, no jargon, short bullets, max 5 lines in chat.
- Agent-to-agent talk goes in the agent lane (`vcc activity add`), never in people comments.
- Shipping and status updates use `/shipping-update`. Every ticket or PR you mention is a full clickable https:// link.
- Slack: reply only inside the starting thread.

## Managers
- Leads and experts own no runners. Report blockers to your own project's lead. Roles, pool, deadlocks: `reference/roster.md`.
- Managers run `/manager-shift` at every check-in.

## Valentin's alone
- Money, paid keys, deleting live or non-runner agents, and x.com/valentinyeo are Valentin's decisions only. His direct order on one of these is the yes. Dismantled runner logins are not his call: delete them.
- Money lock. Spends money or calls a paid service? Stop. Ask him one Question. No thumbs up, no merge, no flag switch, no launch. "Saves money" is still money. Leads never decide it. His direct order naming the spend is the thumbs up.
- x.com/valentinyeo is human-only: never post, reply, like, follow or DM there. x.com/hypertasks is not covered.

## Security
- Never print, commit or publish secrets. Every public repo has secret scanning and push protection on, from creation.
- Keys are cached 24 hours. Run `stack-key <name>` or `yeo-key <name>`. Key seems missing? Run `stack-key --list` first and retry once. Never tell Valentin a key is missing unless it is absent from the list.

## Releases
- HARD: Valentin asks for a flag switch? Do it that turn. His ask is the approval. Never ask him back.
- Every flag goes to Everyone. Only can't-undo harm waits at Owner + QA: charges money, leaks data, deletes for good, emails customers. Failed live check: roll back, flag stays on. Never switch Off or park a flag.
- Flag columns, flag links, changelog lines, in-app updates: `reference/flags.md`.

## Read X when Y

| Read | When |
|---|---|
| `reference/setup.md` | Session start, installing pstack or caveman |
| `reference/brain-map.md` | Picking a model, brain tag, helpers |
| `reference/engines.md` | Engine or plan switch, reviewer, pacing |
| `reference/runner-pipeline.md` | Runner picks, resumes or leaves a ticket; counting runs |
| `reference/boards.md` | Filing or cleaning tickets; CI snags; board caps |
| `reference/github.md` | Waiting on a PR, watching a run, CI |
| `reference/roster.md` | Runners, managers, deadlocks, identities |
| `reference/flags.md` | Flags, flag columns, changelogs, releasing |
| `reference/design.md` | Any design, UI build or report page |
| `reference/stack.md` | New app, frontend or framework choice |
| `skills/tickets/SKILL.md` | Writing any ticket or comment |
| `skills/figma-design/SKILL.md` | Any Figma work |
| `skills/solo-dev/SKILL.md` | You are the only developer on an app |
| `skills/lead/SKILL.md` | You are a fleet lead |
