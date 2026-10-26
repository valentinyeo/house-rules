# Handing work to runners

You write tickets. Hypertask runners (`ht-runners` Claude panes, `ht-hax-runner-N`)
ship them with /ship: claim, PR, CI, merge, deploy, live proof, Done.
No separate Support runners. Same fleet, same guards.

## Tickets stay on HEFE (Valentin, 2026-10-26)
- Support, help-chat and docs tickets stay on the support board 10450 (HEFE). Never move them to board 15.
- Runners pull from 10450 too: https://app.hypertask.ai/detail/project-4060/810 . Until it ships, ask HT Product Lead to assign a runner.
- One HEFE ticket holds the customer problem, evidence, eval numbers and the code work.

## Every runner ticket must contain
- The customer evidence.
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
- No CI polling. ai-chatbot and docs automerge on green; hypertask-ai/hypertask and astro do not (the runner merges after checks). Look once at the next check-in.
- No pushing a runner mid-ticket. Comment on the ticket instead.
- astro (hypertask.ai) belongs to HT Growth Lead. Ticket it, tag them.


## Runners, board and GitHub (from HT Product Lead, 2026-10-26)
- Each lead's tickets stay on its own board: support 10450 (HEFE), marketing 2108 (MARK), product 15 and 4060. Never move them to another board.
- Runners pull from all lead boards: https://app.hypertask.ai/detail/project-4060/810 . Until that ships, HT Product Lead assigns a runner.
- Every ticket gets a reused Title Case label.
- Runner blockers on your tickets come to HT Product Lead. Never message runners mid-ticket except to answer them.
- hypertask-ai/hypertask has no automerge. The runner merges after required checks pass, deploys and proves it live. You check the ticket once later.
- GitHub quota is shared and scarce. Never poll gh or Actions. At most one gh read per check-in.
- Board writes only through vcc as your own agent identity. Never Valentin's token.
- After 23:00 London you start no new loops. Runners keep running.
