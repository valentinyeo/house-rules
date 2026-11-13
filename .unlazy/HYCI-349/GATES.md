# HYCI-349 Pi Codex login dead since 9 Nov, renew it

Scope: renew Pi's Codex login on this machine and stop it dying again when the Codex CLI
rotates the shared refresh token. Repo: valentinyeo/house-rules (fleet/pi-login, fleet/runner).

## Gates

1. **Root cause named with the exact error.** `pi --print --provider openai-codex` printed
   `OAuth refresh failed ... (401) ... "code": "invalid_refresh_token"` before the fix.
   Proof: command output kept in the agent lane comment.
2. **Pi Codex logs in again.** `pi auth check --provider openai-codex` prints `ready`, and a real
   Pi Codex run answers: `pi --print --model openai-codex/gpt-6-luna "..."` returns its text.
3. **The fix is a script, not a paste.** `fleet/pi-login` renews Pi's openai-codex entry from the
   Codex CLI login, backs up the old store, never prints a token, and refuses an expired or
   wrong-account source. Proof: `fleet/pi-login --self-test` ok.
4. **The launcher heals itself.** A pi-codex down mark no longer stays until a human logs in:
   the next pick runs `fleet/pi-login` and goes back to Pi. Proof: `fleet/runner harness-selftest` ok.
5. **Shipped.** One PR in valentinyeo/house-rules, merged to main, live copy in
   ~/.local/share/house-rules matches main (`git -C ... rev-parse HEAD`).
6. **The mark from 9 Nov is gone** and the pool's codex picks run in Pi again. Proof: mark file
   absent, `fleet/yield` shows pi-codex runs after a pick.

Not in scope, named so the ticket is honest: a day of Pi Codex runs and the Pi Codex line on the
harness page (HYCI-344 builds that page).
