# Engines and plans

Read when you launch or switch an engine, review code, or touch a subscription plan.

## Engines

- Fast mode is off everywhere.
- SF solo sessions `postbox` and `multiprompt-android` also run hax DeepSeek 4.1 Flash on OpenCode Go. Desktop `multiprompt` stays Codex.
- Vercel pass (team Hypertaskai, $30 a month, $150 credit; first cycle prorated: $20 and $100; 14 Nov to 5 Dec) runs DeepSeek 4.1 Flash for pool runners as engine `vercel`. Pi only, provider `vercel-ai-gateway`, model `deepseek/deepseek-v4.1-flash`, its own scoped key, no hax, no fallback to any other plan. It stops at the credit. Same brain rows and skips as OpenCode Go. Keep it apart from the OpenCode Go Pi config.
- Grok cloud agents: grok-4.7 medium only, never fast, max 3, only inside `/ship` with a ticket link and an owning slot.
- The triage session may use Claude (Opus) for ~/projects/triage and its 08:00, 12:00 and 16:00 brief runs.
- Scheduled briefs, unblocker and triage run on Sonnet.
- Cursor has no extra charges. At 100% of its week it stops until the reset. Never report, propose or count Cursor extra usage as money.

## Code review

Code review runs only on GitHub's free hosted runners, never on this VPS. Two reviewers: Codex while it has room, else Claude. Claude review is a GitHub Action (`.github/workflows/claude-review.yml` in hypertask-ai/hypertask): one parallel run per PR, concurrency group `review-<pr>` with cancel-in-progress, no daily cap, no queue. It runs on the Claude subscription through the `CLAUDE_CODE_OAUTH_TOKEN` repo secret, uses `pull_request` (never `pull_request_target`), skips fork and Dependabot PRs, and publishes the `ai-review` and `claude-review` statuses itself. Codex review runs in OpenAI's GitHub connector. The gate only requests it from Actions: running Codex inside an Actions job needs an OpenAI auth secret, which is Valentin's call. Every switch is logged to `goal/decisions.jsonl`. The gate reads one switch, an open issue labelled `review-switch`, written by the runner app. It never reads a date. `bin/no-vps-ci` switches off any VPS review unit or process and refuses any `standin` unit or script.

## Pacing

- The budget wins over runner count. Each plan burns at most its even share: room left over time to reset.
- One runner is the floor, for incidents and hard work.
- Plans may under-burn. Plans ahead of pace rest until they catch up. Total is what behind-pace plans carry. Machine load also caps it.
- Claude must never run out: leads need it. Claude runners only under 80% used. Over 60% with reset 5+ days away: none. Last 24 hours before Claude reset: keep leads' projected burn plus 3 points, the rest goes to runners.
- Resets are never automatic. Only Valentin presses them.
- Inne subscriptions are out of scope.
- The pacer sets runner counts. Nobody else tops up.
