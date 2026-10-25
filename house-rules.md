# House rules (Valentin Yeo, every agent, every project)

Single source of standing rules for every agent on this box. If it isn't here, it isn't a rule.

Scope: person-level rules only. Project rules live in each project's own repo.
Precedence: these rules win over any other rules file. Newest dated rule wins.
Path: `~/.local/share/house-rules/house-rules.md` (synced from private repo valentinyeo/house-rules every 5 min).

## How to use this file
- Re-read this file at the start of every ticket or turn. (2026-10-25, why: running sessions miss new rules)
- When Valentin states a new standing person-level rule, append it here: small PR to valentinyeo/house-rules, merge it, tell no one else. (2026-10-25, why: say it once, cascades everywhere)
- Project-only rule? Put it in that project's repo rules file, not here. (2026-10-25, why: projects stay separate)
- One line per rule, with date and a why of 8 words max. (2026-10-25, why: short files get read)

## Models and harnesses
- Fast mode off everywhere: no fast models, flags or tiers. (2026-10-25, why: burns quota, Valentin said HARD)
- No ccr, DeepSeek or any model router; subscription auth only. (2026-10-25, why: no surprise bills or proxies)
- Model routing per pstack roles: Claude coding/bug-fix sonnet high, hardest/judgment opus medium, lookups haiku; Codex coding gpt-6.1-sol, judgment/review gpt-6-astra, lookups gpt-6-luna. (2026-10-25, why: right brain per job, less burn)
- Claude workers run alone, never spawn Codex helpers; extra parallel work = separate hax Codex sessions (max 10), each Codex-only on its own ticket. (2026-10-25, why: clean quotas, no cross-provider tangles)
- Grok cloud agents: grok-4.7 medium only, never fast, max 3, only inside /ship with a ticket link and an owning slot. (2026-10-25, why: cost cap)

## Talking to Valentin
- No status messages, Telegram, briefings or digests to Valentin. Only new releases reaching his desktop matter. (2026-10-25, why: he never asked for them)
- Message him only for money, keys, X or a risky release, always with your recommendation. (2026-10-25, why: he decides product, not tech)
- Report blockers to your own project's lead, never another project's manager. (2026-10-25, why: SF runners pinged Poteto instead of Mini Boss)
- Never ask him isolated technical or architecture questions; decide by best practice, state the decision with a one-line reason, act. (2026-10-25, why: "I want best practices, not my opinion")
- Human-facing text is caveman plus plain words: answer first, max 8 words per sentence, no jargon. Agent lane may be verbose. Drafts for outside people use normal sentences. (2026-10-25, why: product owner, ADHD reader)
- Every ticket or PR you mention to him is a full clickable https:// link. (2026-10-25, why: he clicks, never searches IDs)

## Valentin's alone
- Money, paid keys, deleting or revoking agents with the management key, and X are Valentin's decisions only. (2026-10-25, why: irreversible or costs money)
- X account is human-only: never post, reply, like, follow or DM. (2026-10-25, why: his public voice)

## Security
- Never print, commit or publish secrets. (2026-10-25, why: leaks are permanent)
- Every public repo has secret scanning and push protection on, from creation. (2026-10-25, why: leaked keys visible to anyone)

## Releases
- Releases reach his desktop through the app's in-app update; never hand-replace a running exe. (2026-10-25, why: updater is the tested path)
