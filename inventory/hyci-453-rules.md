# HYCI-453 rule inventory

One row per rule group in `house-rules.md` as of 987454b (8865 words). Line numbers are from that file.

Disposition codes:

- a: a script already enforces it. PR A cuts the prose that restates the script.
- b: only one role needs it. PR B moves it to that role's skill.
- c: history, date, quote or reason. PR A deletes it. The PR body keeps it.
- d: judgment. Stays in the core.
- e: reference fact. PR B moves it to `reference/<topic>.md`.

| Lines | Rule | Disposition | PR B target | System part this rule exists for |
|---|---|---|---|---|
| 3-8 | Header, scope, precedence, path | d, c (dates) | core | the rules file itself |
| 11-20 | Start here: new session | d | core, trimmed | session setup, `/house-rules` |
| 23-27 | Re-read, one place, test rules | d | core | the rules file itself |
| 25-26 | Load via `/house-rules`; project-only rules elsewhere | c (duplicate) | cut | none |
| 28 | HARD: write like Lauren and Anthropic | d | core, 40 words | `rules-lint` |
| 31 | Fast mode off | d | core | none (judgment) |
| 32 | No fallback or router chain | a | core, one line | token-ladder hook |
| 33 | Brain map per harness | e | `reference/brain-map.md` | `fleet/runner`, `fleet/pick`, `ht-or-runner-pick` |
| 34 | SF solo sessions on DeepSeek | e | `reference/brain-map.md` | `fleet/runner` |
| 35 | Vercel Token Pass | e | `reference/engines.md` | pacer plan `vercel`, `fleet/pick` |
| 36 | Say "DeepSeek 4.1 Flash" | d | core, one line | none (model quirk) |
| 37 | 1Password reads cached | d | core, one line | `stack-key` |
| 38 | pstack model routing | d | core | `~/.claude/rules/pstack-models.md` |
| 39 | HARD: script first | d | core | `fleet/opus-scan`, `bin/fleet-watch-tick` |
| 40 | Review picks reviewer by script | e | `reference/engines.md` | `bin/review-switch` |
| 41 | Codex ladder, helpers | e | `reference/brain-map.md` | hax helpers |
| 42 | `/deeper` on Opus medium | b | `skills/deeper/` | `/deeper` skill |
| 43 | Claude workers alone; Codex helpers | e | `reference/engines.md` | hax helpers |
| 44 | Pace every subscription | e | `reference/pacer.md` | `bin/pacer` |
| 45 | Triage session may use Claude | e | `reference/engines.md` | triage briefs |
| 46 | HARD: Cursor has no extra charges | d | core | pacer lists Grok additional usage as none |
| 47 | Grok cloud agents cap | e | `reference/engines.md` | `/ship` |
| 50 | HARD: every long-lived session listens to Agent Chat | a | core, one line | `fleet/runner-chat` |
| 51 | HARD: no CI on this VPS | a | core, one line | `bin/no-vps-ci` |
| 52 | Paid GitHub minutes fine | d | core, one line | none |
| 53 | GitHub polling no faster than 5 minutes | d | core, one line | none |
| 54 | HARD: one ticket, one runner, to Done | a | `reference/runner-pipeline.md` | `fleet/pick`, `fleet/runner`, `fleet/sf-release-watch` |
| 55 | What a run is, valid runs | a | `reference/runner-pipeline.md` | `bin/kpi-watch`, `bin/excess-run-watch`, `fleet/valid-leaves.json` |
| 56 | One-run-ready tickets | a | `reference/runner-pipeline.md` | `ticket-ready`, `fleet/pick`, `filing-gate` |
| 57 | One runner, one ticket; pick order; WIP cap | a | `reference/runner-pipeline.md` | `fleet/pick` |
| 58 | Missing priorities filled hourly | a (cut in A) | none | `prio-scan` |
| 59 | Keep one runner and model until Done | a (cut in A) | none | `fleet/ticket_owner.py`, `fleet/park` |
| 61 | Not now column | a | `reference/boards.md` | `fleet/pick` |
| 62 | HARD: no factory stop; prevent excess runs | a | `reference/runner-pipeline.md` | `bin/excess-run-watch` |
| 63 | HARD: a runner that takes a ticket delivers it | a | `reference/runner-pipeline.md` | `fleet/valid-leaves.json` |
| 64 | TOO HARD hand-off | a | `reference/runner-pipeline.md` | `fleet/runner-state.py`, `fleet/park --too-hard` |
| 65 | Live incident lane | a | `reference/runner-pipeline.md` | `fleet/pick` step 0, `fleet/briefs/incident.txt` |
| 66 | Move tickets live | d | core | `vcc` |
| 67 | Every change carries a ticket key | a | core, one line | ticket-key workflow |
| 68 | Prove it, never claim it | d | core | none (judgment) |
| 69 | Design QA vs Figma | d | `skills/figma-design/` | none (judgment) |
| 70 | Ask for options | d | core, one line | none (judgment) |
| 71 | Design proposals carry Figma link | d | `skills/figma-design/` | none |
| 72 | Leads act on his direct order | d | core | none |
| 73-76 | His direct order and his yes | d | core, merged to three lines | none (judgment) |
| 77 | Software Factory apps low risk | d | `reference/boards.md` | none |
| 78 | Tickets follow `skills/tickets/` | a | core, one line | `ticket-lint` |
| 79 | HARD: quote Valentin with the quote block | d | core | `ticket-lint` |
| 80 | One marked Question | a | `skills/tickets/` | `blocker-sweep.py` |
| 81 | Question starts with "What this is:" | a | `skills/tickets/` | `ticket-lint` |
| 82 | Never block Valentin on non-decisions | d | core | none |
| 83 | Runners end on a listed state | a | `reference/runner-pipeline.md` | `fleet/runner-state.py` |
| 84 | Solo devs drain their view | b, a | `skills/solo-dev/` | `fleet/solo-wake` |
| 85 | Multi Bot Opus Runner | b | `reference/boards.md` | `take` in `fleet/roster.json` |
| 86 | Several roles in one session | a | `reference/roster.md` | `fleet/roster-announce`, `vcc` |
| 87 | Every session announces itself | a | `reference/roster.md` | `fleet/roster-announce`, `fleet/roster-check` |
| 88 | Our subscription costs nothing extra | d | core, one line | `ticket-lint` |
| 89 | HARD: never ask him for a fact | a | core | `agent-identity-guard`, `ticket-lint` |
| 90 | HARD: file Hypertask snag feedback | a | core | `agent-feedback` |
| 91 | No column piles up | a | `reference/boards.md` | `pileup-watch` |
| 92 | Fleet CI and Infra filing | a | `reference/boards.md` | `filing-gate` |
| 93 | Keep the board clean, duplicates | a | `skills/hypertask-triage/` | `board-dupes` |
| 94 | Fleet chiefs run triage until GREEN | a, b | `skills/hypertask-triage/` | `board-health`, `ticket-check` |
| 95 | Self-maintenance board stays small | a | `reference/boards.md` | `pileup-watch` backlog cap |
| 96 | `/unblock` | b | `skills/unblock/` | `/unblock` skill |
| 97 | `/do` for must-finish tasks | d | core, one line | `/do` skill |
| 98 | `/deep-work` | d | core, one line | `/deep-work` skill |
| 99 | HARD: Rat Stack | d | core | `fleet/stack-scan` |
| 100 | Tag every ticket with app label | a | `skills/tickets/` | `filing-gate`, `vcc` |
| 101 | One brain tag per ticket | a | `skills/tickets/` | `vcc`, `bin/brain-tagger` |
| 102 | Label cluster has a board view | b | `reference/boards.md` | board manager |
| 105-109 | Figma, design system, Impeccable | d | `skills/figma-design/` | `ds-check.py` |
| 110 | Reduce first | d | `skills/reduce-first/` | page-words check |
| 111-112 | Live values, no circles or pills | a | `skills/figma-design/` | `ds-check.py` |
| 113-117 | Design scoping, one platform, one file, screencast | d | `skills/figma-design/` | none |
| 118 | Report pages show data only | a | `skills/report-page/` | `bin/page-words` |
| 121-126 | Status messages, VPS paths, message him rules | d | core, merged | none (judgment) |
| 127-130 | Caveman and bullets in comments and chat | d | core, merged to two lines | none |
| 131 | Shipping updates use `/shipping-update` | d | core, one line | `fleet/yield` |
| 132 | Caveman plugin | c (duplicate of setup step 3) | cut | none |
| 133-134 | Full links; Slack threads | d | core | `slack-say` |
| 137 | Chief Of Staff and managers | b | `skills/lead/` | none |
| 138 | `/manager-shift` | b | `skills/manager-shift/` | `/manager-shift` skill |
| 139 | No agent-to-agent messaging | d | core | none |
| 140-141 | HARD: factory plan, one shared pool | e | `reference/roster.md` | `fleet/roster.json`, `fleet/pick` lanes |
| 142 | Kept slot | a (cut in A) | `reference/runner-pipeline.md` | `fleet/pick`, `fleet-watch` |
| 143-144 | CI tickets on board 11514; CI snag | a | `reference/boards.md` | `ci-unblock-waiters` |
| 145 | Leads empower, never do runner work | b | `skills/lead/` | none |
| 146-148 | Report blockers to own lead | d, c (duplicates) | core, one line | none |
| 149 | `/runner-update` | b | `skills/runner-update/` | pacer |
| 150 | Factory deadlock | b | `skills/lead/` | `factory-watch` |
| 151 | Infra Lead | b | `reference/roster.md` | none |
| 152-153 | Growth and Support leads | b | `skills/lead/` | none |
| 154 | `/agent-housekeeping` | b | `skills/agent-housekeeping/` | `agent-identities` |
| 155-156 | One agent, one identity | a | `skills/agent-housekeeping/` | `agent-identities --apply` |
| 159-161 | Valentin's alone | d | core, substance kept | none |
| 164-166 | Security | d | core | secret scanning, `stack-key` |
| 169-170 | In-app update; prod logs read-only | d | core | none |
| 171 | Agents switch flags themselves | c (duplicate of 176) | cut | none |
| 172-173 | Flag link, flag column | a | `reference/flags.md` | `flag-links`, `flag-columns` |
| 174 | SF changelog line names its ticket | a | `reference/flags.md` | release check |
| 175-177 | Flag goes to Everyone; exceptions | d | `reference/flags.md` | none |

## Rules that only manage another script or robot

These rules exist to describe, feed or police a script. If the script goes, the rule goes. This list is for Valentin to decide. This change deletes none of the machinery.

| Rule (old line) | Script or robot it manages | What deleting it would simplify |
|---|---|---|
| 58 missing priorities | `prio-scan` | one hourly job |
| 56 one-run-ready | `ticket-ready`, its Sonnet fixer | a gate in `fleet/pick`, a fixer |
| 62, 63 excess runs, valid leaves | `bin/excess-run-watch`, Sonnet fixer, `valid-leaves.json` | a watcher, a fixer, a state file |
| 55 run definition, violations | `bin/kpi-watch`, Run Log page | a KPI and its alarm |
| 83 runner end states | `fleet/runner-state.py` | a state machine |
| 84 solo wake | `fleet/solo-wake` | a timer |
| 87 roster announce | `fleet/roster-announce`, `roster-check` | a hook and a check |
| 94 fleet chiefs run triage | `board-health`, `ticket-check` | a scorecard loop |
| 91, 95 column caps | `pileup-watch` | two caps and daily alarms |
| 96 `/unblock` | the unblock skill and `blocker-sweep.py` | a skill |
| 142 kept slot | `fleet/pick` kept-slot lane, `fleet-watch` | a lane |
| 150 factory deadlock | `factory-watch`, `chief-brief` RUNNERS BUILDING | a watcher |
| 40 review switch | `bin/review-switch` timer | a timer and a label |
| 44 pacer | `bin/pacer` | the pacing loop |
| 156, 154 agent identities | `agent-identities`, `agent-housekeeping` | an hourly job |
| 92, 93 filing and dupes | `filing-gate`, `board-dupes` | two gates |
| 144 CI snag waiters | `ci-unblock-waiters` | a waiter job |
| 172, 173 flag links and columns | `flag-links`, `flag-columns` | two hourly jobs |
| 101 brain tag | `bin/brain-tagger`, `brain-rules-refresh` | a tagger and a weekly refresh |
