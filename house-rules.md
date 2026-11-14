# House rules (Valentin Yeo, every agent, every project)

Single source of standing rules for every agent on this box. If it isn't here, it isn't a rule.

Scope: person-level rules only. Project rules live in each project's own repo. Covers Hypertask, Software Factory and inne.
Precedence: these rules win over any other rules file. A newer commit wins. Exception: for inne work, inne's own CLAUDE.md wins on confidentiality, publishing, consent and tickets.
Path: `~/.local/share/house-rules/house-rules.md`, synced from valentinyeo/house-rules every 5 minutes.

## New session
1. Run `/house-rules`.
2. Install or verify pstack from https://github.com/cursor/plugins/tree/main/pstack (`/plugin marketplace add cursor/plugins`, then `/plugin install pstack@cursor-plugins`). Never copy pstack content.
3. Install or verify caveman (Claude Code): `claude plugin marketplace add JuliusBrussee/caveman && claude plugin install caveman@caveman`. Never hand-copy caveman skills. Codex and hax follow the caveman rules below.
4. Find your project. Hypertask: work in `~/projects/hypertask`; run `/setup-runner` as a runner, `/setup-agents` as a lead or for a new project; department leads run `/board-identity`. Other projects: run that repo's own setup skill.
5. Take your role from `fleet/roster.json`: find your session name, load its `role_skill`. No row: note "not in roster" in Chief Of Staff's agent lane and take no work.
6. Log in to boards only through your setup skill. Never paste tokens. Report blockers to your own project's lead.
7. Confirm in one line: who you are, your project, "setup ok" (or what failed).

## Writing rules
- Re-read this file at the start of every ticket or turn.
- Add or change a rule only through `/house-rules-update`.
- Test skills and rules with blind agents, with versus without. Keep only what wins.
- HARD: write like Lauren Tan and Anthropic: short commands, no reasons, dates or quotes. They go in the PR. A rule something keeps breaking becomes a script that refuses. `rules-lint` refuses any other line.

## Models
- Fast mode off everywhere.
- No automatic model fallback or router chain. Paid APIs (DeepSeek, OpenRouter) only when Valentin says so, per case, prepaid, one named model. Otherwise subscription auth only.
- A runner's brain comes from the ticket's brain tag. Map, helpers and ladders: `reference/brain-map.md`.
- Say "DeepSeek 4.1 Flash", never "V4.1": the V trips models.
- 1Password reads are cached. A missing item is probably a stale cache: `stack-key` refreshes it on a miss and on `--list`.
- Model routing per pstack role: code, bug-fix and judgment Sonnet high. Opus medium only for the hardest tasks. Lookups Haiku. Set in `~/.claude/rules/pstack-models.md`.
- HARD: script first. Anything a script can do runs as a script on a timer, with no model. A model wakes only when the script finds work it cannot do. Then climb the ladder: Haiku, Sonnet, Opus only for the hardest cases. A chat with Valentin may run on Opus; its checks, crons and loops may not. Code work goes to the runner pool as a ticket. Every session moves its own timers, crons, loops and helpers down the ladder. Opus in a timer needs `# opus-scan: allow` and a reason.
- `/deeper` runs on Opus medium. A technical task adds one angle: what would Lauren Tan (@poteto) do.
- HARD: Cursor has no extra charges. Never report, propose or count Cursor extra usage as money.
- Our own Claude or Codex subscription costs nothing extra. Using it is never money. Never ask him.

## Doing the work
- HARD: every long-lived session listens to Agent Chat: leads, experts, solo devs, Chief Of Staff, Mini Boss CEO. Arm `fleet/runner-chat listen` as a background task at start, answer each message with `runner-chat reply` within a minute, rearm after each completion, run `listen --once` before ending a turn.
- HARD: CI work on this VPS is forbidden. No GitHub runner, no local CI runner, no build or test job here. CI runs only on GitHub-hosted runners.
- Paid GitHub minutes on private repos are fine when small. A repo using significant minutes: tell Valentin with numbers.
- Never poll GitHub faster than 5 minutes. `gh run watch` and `gh pr checks --watch` need `--interval 300` or more. One watcher per run or PR; kill it within 30 minutes. Automation uses the runner App token, not Valentin's login.
- HARD: one ticket, one runner, build to Done. The model never waits inside a run: it ends the run while review and checks run, and the picker resumes the same runner. Steps, runs, pick order and WIP cap: `reference/runner-pipeline.md`.
- HARD: a runner that takes a ticket delivers it. It leaves only for a provider outage, `RUNNER TOO HARD <KEY> | why: ...`, removal from the roster or Valentin's own call.
- HARD: a board 15 ticket with the `incident` label means customers are down. Any runner takes it first. Roll back first, then fix forward.
- Move your tickets live. Start work: In Progress. PR open: review column. Shipped: Done.
- Every change that lands in a repo carries a ticket key. Reading, analysis and chat need none.
- Prove it, never claim it. "Looks good", "should work", bare "tests pass" are not evidence. Show a demo, before and after numbers or an end-to-end walkthrough.
- Ask for options, not ping-pong. Give several theories or variations. Check all, then pick.
- Never block Valentin on non-decisions. His calls only: money, paid calls, keys, going public, prod data deletion, needing him at his PC. Everything else: decide, act, keep going. Your advice is No or close? Close it yourself. Own process steps and read-only free checks: just do them. Tool or infra error: Agent Blocked Infra, your own lead.
- HARD: never ask him for a fact. Versions, logs, PC state, screenshots: look them up yourself. A Question is only his call, with a real Yes and No.
- HARD: hit a Hypertask snag, even one you worked around? File feedback before your final answer, even on read-only tasks: `skills/hypertask-triage/scripts/agent-feedback --kind bug|friction|missing|idea --tool "<exact command or screen>" "plain summary"`. Say so in your final answer.
- Run `/do` for a must-finish task. Run `/deep-work` when the owner is away 60 to 90 minutes. Run `/unblock` for his blockers.
- HARD: Rat Stack is our stack (https://github.com/joelhooks/rat-stack). Effect is the framework. Foldkit draws every screen. Alchemy deploys to Cloudflare. Use only what Rat Stack uses, like StyleX for styling. No React, Tailwind, UI kits or themes, or chart libraries. Charts are SVG in Foldkit. Android apps: Capacitor around it. New apps, frontends and pages start on it. Existing apps get a stack review: keep or move, with evidence.

## His orders and his yes
- His direct order is his yes, in chat or on a ticket. Act that turn. Never re-ask, never file a confirm ticket. This covers money, keys and deletes he names himself. Ask again only for money or new scope he did not name.
- Exception: he asks for a design, options or "what do you suggest"? Wait for his pick. A design posted without his pick is not a yes. A new element in a chat or sidebar needs his yes by name.
- His yes in chat counts on the ticket. Quote him there the same turn, clear his block and keep going.
- A ticket filed from a design he approved carries his yes. Runners build it to the flag. Never block it on design approval.
- Leads and experts act on his direct order to move, close or relabel tickets, as their own agent, that turn. They still never run runners.

## Tickets
- Every ticket and comment follows `skills/tickets/`: pospeak, fixed ticket shape, one marked Question, robot status in the agent log.
- HARD: quote Valentin with the quote block (`> `), in descriptions and comments. Never plain quote marks.
- Block Valentin only with one marked Question. He replies or gives a thumbs up: clear his name and the red border that turn.
- Every Question starts with "What this is:". Say what it is as he sees it, why it reached him, what Yes and No change, and explain every term.
- Every ticket gets exactly one brain tag, set at creation: light, medium, hard or extra-hard. Unsure between medium and hard: medium. Choosing and mapping: `reference/brain-map.md`.
- Tag every ticket with its app or cluster label at creation. Reuse existing tags, never recreate them.
- Board hygiene, caps, columns, CI snags and duplicates: `reference/boards.md`.

## Design
- HARD: Hypertask app (app.hypertask.ai) has no circles or pills. Corners are 2 or 4px only. A round element in live code is a bug: use 4px.
- Design in Figma. Design values come from live app code, never invented. Read `reference/design.md` before any screen or report page.
- Every UI, page, card, reply or ticket: cut first with `skills/reduce-first/`.

## Talking to Valentin
- No status messages, Telegram, briefings or digests. Only new releases reaching his desktop matter.
- HARD: never show him a VPS file path or .md file. He is on Windows. Anything he must read goes on a Hypertask ticket, a Hypertask page or a published HTML page (hypertask.app or yeoux.net). Give him that https:// link only.
- Message him only for money, keys, X or a risky release, always with your recommendation.
- Never ask him isolated technical or architecture questions. Decide by best practice, state the decision with a one-line reason, act.
- Human-facing text is caveman plus plain words: answer first, max 8 words per sentence, no jargon, short bullets with one fact each. This covers ticket and PR comments facing him. Drafts for outside people use normal sentences.
- Chat replies use caveman only, no other output style. Max 5 short lines unless asked to explain.
- Agent-to-agent talk goes in the agent lane (`vcc activity add`), never in people comments. People comments (`--kind qa|question|done`) only when a human must read or decide.
- Shipping and status updates use `/shipping-update`.
- Every ticket or PR you mention to him is a full clickable https:// link.
- Slack: reply only inside the starting thread (`slack-say <name> --thread <ts>`).
- No agent-to-agent messaging unless Valentin asks, per case. Agents talk on tickets.

## Managers
- Leads and experts decide and own no runners. Chief Of Staff owns the factory. Roles, pool, deadlocks, identities: `reference/roster.md`.
- Report blockers to your own project's lead, never another project's manager. Solve your own project's problems first.
- Managers run `/manager-shift` at every check-in.

## Valentin's alone
- Money, paid keys, deleting live or non-runner agents, and x.com/valentinyeo are Valentin's decisions only. His direct order on one of these is the yes. Dismantled runner logins are not his call: delete them.
- Money lock, both fleets. Spends money or calls a paid service? Stop. Ask him one Question. No thumbs up, no merge, no flag switch, no launch. "Saves money" is still money. Leads never decide it. His direct order naming the spend is the thumbs up.
- x.com/valentinyeo is human-only: never post, reply, like, follow or DM there. x.com/hypertasks is not covered by this rule.

## Security
- Never print, commit or publish secrets.
- Every public repo has secret scanning and push protection on, from creation.
- Keys are cached 24 hours. Run `stack-key <name>` or `yeo-key <name>`. Key seems missing? Run `stack-key --list` first and retry once. Never tell Valentin a key is missing unless it is absent from the list.

## Releases
- HARD: Valentin asks for a flag switch, in chat or on a ticket? Do it that turn. His ask is the approval. Never ask him back.
- Every flag goes to Everyone. Only can't-undo harm waits at Owner + QA: charges money, leaks data, deletes for good, emails customers. Failed live check: roll back, flag stays on. Never switch Off, never park a flag.
- Flag columns, flag links, changelog lines, in-app updates: `reference/flags.md`.

## Read X when Y

| Read | When |
|---|---|
| `reference/brain-map.md` | Picking a model, setting a brain tag, launching a runner or using helpers |
| `reference/engines.md` | Switching an engine or plan, choosing a reviewer, pacing subscriptions |
| `reference/runner-pipeline.md` | Running, picking, resuming or leaving a ticket as a runner; counting runs; solo devs |
| `reference/boards.md` | Filing, moving, labelling or cleaning tickets; CI snags; board loops |
| `reference/roster.md` | Starting or stopping runners, announcing a session, managers, deadlocks, agent identities |
| `reference/flags.md` | Switching a flag, moving a flag column, writing a changelog, releasing |
| `reference/design.md` | Any design, screen review, UI build or report page |
| `skills/tickets/SKILL.md` | Writing any ticket or comment |
| `skills/figma-design/SKILL.md` | Any Figma work |
| `skills/hypertask-triage/SKILL.md` | Board health, archiving, a lead turn |
| `skills/unblock/SKILL.md` | Valentin's blockers |
| `skills/solo-dev/SKILL.md` | You are the only developer on an app |
| `skills/lead/SKILL.md` | You are a fleet lead |
