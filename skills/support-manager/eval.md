# Eval: is the help chat right?

Score each answer right / wrong / out-of-date / no-answer.
Fix root causes in this order: docs, retrieval, then prompt. Prompt last.

## Tools (ai-chatbot repo)
- `npm run replay`: replays `eval/replay-v0.jsonl` (also runs in CI).
  Replay traffic carries `X-Eval-Token` = EVAL_INGEST_SECRET so it is marked
  `is_eval` and stays out of the admin inbox.
- `npm run score:retrieval`: retrieval hit rate, plus `eval/retrieval-typos.jsonl`.
- Live retrieval check: `https://help.hypertask.ai/api/chat/debug-rag?q=...`.
- Baseline 25 Oct 2026: retrieval 10/18 on 100 live articles; after fixes
  18/19. Treat any drop as a regression.

## After every live change
1. Same replay set, before and after. Paste both numbers on the ticket.
2. Ask the changed question live on help.hypertask.ai. Screenshot.
3. Check time to first token did not get worse (worker logs `model_ttft`).
4. Pricing and Free plan answers still match app code.

## Approved next step (deeper plan, not yet built)
Ticket each as its own HEFE ticket when ready:
- replay-v1: ~50 real-shaped cases; recall@5, answer score, TTFT.
- Plan facts read from app code, not typed into prompts.
- Hybrid retrieval: D1 FTS5 + Vectorize.
- Answer contract: cite the article, one clear next step (CTA).
- Docs auto-sync on docs merge (today manual).
- CI eval gate: block merge when replay drops.
