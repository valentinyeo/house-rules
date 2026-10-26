# Handing work to runners

You write tickets. Hypertask runners (`ht-runners` Claude panes, `ht-hax-runner-N`)
ship them with /ship: claim, PR, CI, merge, deploy, live proof, Done.
No separate Support runners. Same fleet, same guards.

## Why tickets go on board 15, not only HEFE
`runner-dispatch` picks only board 15 (Bugs, Todo) and 4060 (Backlog).
It never reads HEFE (10450). So:
1. HEFE ticket = the customer problem, evidence and eval numbers. You own it.
2. Code work = one HTPR ticket on board 15 Todo, linked both ways.
3. When the HTPR ticket is Done, you re-run the eval and close HEFE.
If Valentin approves routing HEFE directly (see takeover.md, fix B), drop step 2.

## Every runner ticket must contain
- Link to the HEFE ticket and the customer evidence.
- Repo line and ship prefix, exact:

| Repo | Prefix for `ship-gates` and every `ship-check` |
|---|---|
| ai-chatbot | `SHIP_REPO=valentinyeo/ai-chatbot SHIP_BASE=master SHIP_CHECKOUT=$HOME/projects/ai-chatbot SHIP_WORKER=.` (worker at repo root; confirm ship-check accepts `.` on the first ticket) |
| docs | `SHIP_REPO=hypertask-ai/docs SHIP_BASE=main SHIP_CHECKOUT=$HOME/projects/HypertaskDocs` |
| astro | `SHIP_REPO=hypertask-ai/astro SHIP_BASE=feature/v2-homepage SHIP_CHECKOUT=$HOME/projects/hypertask-astro` |

- ai-chatbot deploy line: "Deploy approved (Valentin 2026-10-25, help chat).
  Deploy with `npx wrangler deploy --message <full merge sha>` so
  `ship-check deployed` matches. Token: `stack-key cloudflare CLOUDFLARE_API_TOKEN`."
- Docs change that the chat must know: "After docs deploy, run the
  `sync-docs` workflow in ai-chatbot. Snapshot articles first."
- Acceptance: the exact question, the expected answer, the replay numbers.
- One root cause per ticket. Small PR.

## What you do not do
- No coding, no PRs of your own, no cloud agents.
- No CI polling. Automerge merges on green. Look once at the next check-in.
- No pushing a runner mid-ticket. Comment on the ticket instead.
- astro (hypertask.ai) belongs to HT Growth Lead. Ticket it, tag them.
