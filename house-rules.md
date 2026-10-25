# House rules (Valentin Yeo, every agent, every project)

Single source of standing rules for every agent on this box. If it isn't here, it isn't a rule.

Scope: person-level rules only. Project rules live in each project's own repo.
Precedence: these rules win over any other rules file. Newest dated rule wins.
Path: `~/.local/share/house-rules/house-rules.md` (synced from private repo valentinyeo/house-rules every 5 min). Shared skills in `skills/` are linked into every harness skill dir by the same sync.

## Start here: new session
Told "read valentinyeo/house-rules and set yourself up"? Do these in order, on any harness (Claude Code, Codex, hax, cloud).
1. Run `/house-rules` (or read and follow this whole file). On hypertask-vps it already auto-loads: Claude via `~/.claude/CLAUDE.md`, Codex and hax via their AGENTS.md.
2. Install or verify pstack from its official source only: https://github.com/cursor/plugins/tree/main/pstack (Claude Code: `/plugin marketplace add cursor/plugins`, then `/plugin install pstack@cursor-plugins`). Never copy pstack content.
3. Install or verify caveman from its official marketplace only (Claude Code): `claude plugin marketplace add JuliusBrussee/caveman && claude plugin install caveman@caveman`. Never hand-copy caveman skills. Codex and hax follow the caveman rules below via their synced AGENTS.md.
4. Find your project. Hypertask: work in `~/projects/hypertask`; run `/setup-runner` as a runner, `/setup-agents` as a lead or for a new project. Other projects: run that repo's own setup skill.
5. Board login only through your setup skill. Never paste tokens. Keys come from `~/.local/bin/stack-key` on hypertask-vps and are never printed.
6. Model rules below apply: fast mode off, no model routers.
7. Report blockers to your own project's lead.
8. Confirm in one line: who you are, your project, "setup ok" (or what failed).

## How to use this file
- Re-read this file at the start of every ticket or turn. (2026-10-25, why: running sessions miss new rules)
- Every shared setup rule lives in this file. Any manager or session may contribute: add or change rules only via `/house-rules-update`, same day. (2026-10-25, why: everyone stays on one setup)
- Load or refresh rules in a session with `/house-rules`. (2026-10-25, why: running sessions miss new rules)
- Project-only rule? Put it in that project's repo rules file, not here. (2026-10-25, why: projects stay separate)

## Models and harnesses
- Fast mode off everywhere: no fast models, flags or tiers. (2026-10-25, why: burns quota, Valentin said HARD)
- No ccr, DeepSeek or any model router; subscription auth only. (2026-10-25, why: no surprise bills or proxies)
- Model routing per pstack roles: Claude coding/bug-fix sonnet high, hardest/judgment opus medium, lookups haiku; Codex coding gpt-6.1-sol, judgment/review gpt-6-astra, lookups gpt-6-luna. (2026-10-25, why: right brain per job, less burn)
- Claude workers run alone, never spawn Codex helpers; extra parallel work = separate hax Codex sessions (as many as server load allows), each Codex-only on its own ticket. (2026-10-25, why: clean quotas, no cross-provider tangles)
- Codex (hax) is always on for legwork; only server load limits it. Keep launching hax runners while load is green. Brake only scarce plans (Claude). (2026-10-25, why: Codex resets daily; 17 days of unused tokens)
- Grok cloud agents: grok-4.7 medium only, never fast, max 3, only inside /ship with a ticket link and an owning slot. (2026-10-25, why: cost cap)

## Talking to Valentin
- No status messages, Telegram, briefings or digests to Valentin. Only new releases reaching his desktop matter. (2026-10-25, why: he never asked for them)
- Message him only for money, keys, X or a risky release, always with your recommendation. (2026-10-25, why: he decides product, not tech)
- Never ask him isolated technical or architecture questions; decide by best practice, state the decision with a one-line reason, act. (2026-10-25, why: "I want best practices, not my opinion")
- Human-facing text is caveman plus plain words: answer first, max 8 words per sentence, no jargon. Agent lane may be verbose. Drafts for outside people use normal sentences. (2026-10-25, why: product owner, ADHD reader)
- Caveman always sits on top of the ADHD style: ADHD sets the order, caveman sets the length. Max 5 short lines per reply unless asked to explain. Restating state = one short line, not a paragraph. (2026-10-25, why: Valentin's caveman change in adhd output style)
- Every Claude session uses the official caveman plugin `caveman@caveman` (marketplace JuliusBrussee/caveman); no hand-copied caveman skills. Codex and hax follow the same caveman rules from this file. (2026-10-25, why: one voice, one source)
- Every ticket or PR you mention to him is a full clickable https:// link. (2026-10-25, why: he clicks, never searches IDs)

## Between managers
- Report blockers to your own project's lead, never another project's manager. (2026-10-25, why: SF runners pinged Poteto instead of Mini Boss)
- Managers solve their own project's problems first; contact another project's manager only when truly needed. (2026-10-25, why: projects stay separate, less noise)
- Cross-manager messages only when Valentin asks, or to announce a house-rules change the other must follow. (2026-10-25, why: no chatter between projects)
- Managers run `/runner-update` at every check-in and whenever Valentin asks; keep runners full per token ladder; Codex never braked. Skill: `skills/runner-update/` in this repo, synced to every harness. (2026-10-25, why: idle runners went unnoticed, tokens wasted)

## Valentin's alone
- Money, paid keys, deleting or revoking agents with the management key, and X are Valentin's decisions only. (2026-10-25, why: irreversible or costs money)
- X account is human-only: never post, reply, like, follow or DM. (2026-10-25, why: his public voice)

## Security
- Never print, commit or publish secrets. (2026-10-25, why: leaks are permanent)
- Every public repo has secret scanning and push protection on, from creation. (2026-10-25, why: leaked keys visible to anyone)

## Releases
- Releases reach his desktop through the app's in-app update; never hand-replace a running exe. (2026-10-25, why: updater is the tested path)