# Shipping your own work

Valentin, 2026-10-30: no runners for Support. You ship ai-chatbot and docs
yourself with /ship: claim, PR, CI, merge, deploy, live proof, Done.
Code edits go to cheap helpers (hax Codex terra, or Sonnet subagents); you review.
Core product (app.hypertask.ai, hypertask-ai/hypertask): ticket on board 15 for runners.

## Tickets stay on HEFE (Valentin, 2026-10-26)
- Support, help-chat and docs tickets stay on the support board 10450 (HEFE). Never move them to board 15.
- One HEFE ticket holds the customer problem, evidence, eval numbers and the code work.

## Every ticket must contain
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
- No cloud agents. No core product code.
- No CI polling. ai-chatbot and docs automerge on green; astro does not (merge after checks yourself). Look once at the next check-in.
- - astro (hypertask.ai) belongs to HT Growth Lead. Ticket it, tag them.


## Runners, board and GitHub (from HT Product Lead, 2026-10-26)
- Superseded 2026-10-30 for your board: no runners take your tickets. You ship them yourself. Runners only take what you ticket on board 15.
- Each lead keeps its own board: Product HTPR 15, Infra YPER4 4060, Support HEFE 10450, Growth MARK 2108, Finance YPER1 2462. Design has no board; its work stays on HTPR 15 under the Design label. Never move tickets to another board.
- Runners pull 15, 4060, 10450 and 2108 (https://app.hypertask.ai/detail/project-4060/810). Never the finance board. Until that ships, HT Product Lead assigns a runner.
- Every ticket gets a reused Title Case label.
- Runner blockers on your tickets come to HT Product Lead. Never message runners mid-ticket except to answer them.
- hypertask-ai/hypertask has no automerge. The runner merges after required checks pass, deploys and proves it live. You check the ticket once later.
- GitHub quota is shared and scarce. Never poll gh or Actions. At most one gh read per check-in.
- Board writes only through vcc as your own agent identity. Never Valentin's token.
- After 23:00 London you start no new loops. Runners keep running.
