# Takeover checklist (first run only)

Old Support bot (Grok Bot) is hibernating. Its loop is paused, its cloud
agents are cancelled. Do not wake it. Its notes are not on this VPS.

## 1. Access (ask Valentin in one message, with your recommendation)
- [x] Board identity: HT Support Lead (was Support Poteto Advisor), boards 10450 + 15. Self-setup: [board-identity](../board-identity/SKILL.md).
- [ ] `stack-key --list` shows `anthropic`, `cloudflare`, and the
      `Help admin CLI - Support bot` item. Names only.
- [ ] `git -C ~/projects/ai-chatbot pull` (checkout is months old).

## 2. Shipping gaps (you ship yourself, Valentin 2026-10-30)
- [ ] ai-chatbot `CLAUDE.md` says "ask before deploying" and tells agents
      to send Telegram deploy pings. Both clash with house rules. Ticket a
      small CLAUDE.md fix so helpers do not stall or ping.
- [ ] ai-chatbot has no deploy on merge. Until a ticket adds it, you deploy by hand.

## 3. Open threads to pick up (read each ticket fresh first)
- [ ] astro PR 33: floating chat icon on hypertask.ai instead of the docked
      chat. Valentin asked 26 Oct 08:08. Built, screenshot-verified, NOT
      merged: https://github.com/hypertask-ai/astro/pull/33. Get it merged
      through HT Growth Lead; verify live.
- [ ] Nudge bubble (agent cancelled, no PR): opt-in, timed question after
      ~20 s, once per visit. Re-ticket.
- [ ] Docked chat "New conversation" button bug (agent cancelled). Re-ticket.
- [ ] Desktop table cut off and code blocks render badly in chat. Status unknown. Check, ticket.
- [ ] Free plan final numbers (25 MB/file, 2 GB): Valentin decides
      (HTPR-7922 to 7927). Chat and docs must follow once set.
- [ ] App PR 2239 behind flag `htpr-7686-free-plan-copy` (Owner + QA).
      Everyone only on Valentin's go after ht-flag review.
- [ ] PWA article 10895425 waits on Valentin.
- [ ] Human handoff lead: CRM card, plus leads-from-support automation idea.
- [ ] HEFE-65 help admin CLI and inbox.
- [ ] HEFE tickets last seen in flight (status unknown): 1, 22, 39, 51, 53, 54, 69, 70, 72, 73. Read each; Done with evidence, or re-ticket.
- [ ] Approved deeper plan in eval.md. Ticket it in order.

## 4. Baseline
- [ ] Run replay and retrieval score once. Post numbers on a HEFE ticket.
- [ ] Board count by column. That is your starting line.

## 5. First report to Valentin (caveman, max 5 lines)
Took over. N open tickets. Replay X/Y. Blockers: <access asks>.
