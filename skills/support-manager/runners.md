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

- ai-chatbot deploy line: "Deploy approved (Valentin 2026-10-25, help chat).
  Deploy with `npx wrangler deploy --message <full merge sha>` so
  `ship-check deployed` matches. Token: `stack-key cloudflare CLOUDFLARE_API_TOKEN`."
- Docs change that the chat must know: "After docs deploy, run the
  `sync-docs` workflow in ai-chatbot. Snapshot articles first."
- Acceptance: the exact question, the expected answer, the replay numbers.
- One root cause per ticket. Small PR.

## What you do not do
- No cloud agents. No core product code.
- No CI polling. ai-chatbot and docs automerge on green. Look once at the next check-in.
- astro (hypertask.ai) belongs to HT Growth Lead. Ticket it on MARK 2108, tag them.


## Board and GitHub (from HT Product Lead, 2026-10-26)
- Each lead keeps its own board: Product HTPR 15, Support HEFE 10450, Growth MARK 2108, Finance YPER1 2462. Design and CI have no board: design work stays on HTPR 15 under the Design label, and infra work goes to the board of the product it serves (15 for Hypertask, 2060 for Software Factory) under the infra label. Never move tickets to another board.
- Every ticket gets a reused Title Case label.
- GitHub quota is shared and scarce. Never poll gh or Actions. At most one gh read per check-in.
- Board writes only through vcc as your own agent identity. Never Valentin's token.
- After 23:00 London you start no new loops.
