# House rules

Rules for every agent on Valentin's projects. Run `/pstack:poteto-mode` for every task; orchestrators use its Orchestrate playbook. These rules beat pstack. pstack beats every other rule and skill.

## Work

- **Tickets:** Start and end every unit on a Hypertask ticket, on your own board or view, under your own login (`/board-identity`). Move the ticket the moment its work moves. Put status and questions on the ticket, not in chat.
- **Cloudflare:** Start new Cloudflare work from `joelhooks/rat-stack`.
- **Secrets:** Never write a secret into a file, commit, ticket or chat.
- **Open source:** Create new repos public. Make one private only when Valentin says so or it holds client, money or personal data, and state that reason.

## Verify and ship

- **Verifier:** Give every PR a pstack verifier before merge. It comes from another model family than the author, runs the change like a user, and posts `pstack-verifier: PASS|PASS+NOTES|FAIL @ <sha>`. Green CI or a bot review is not a verdict.
- **Verifier per repo:** Build each repo's own verifier and app driver. Make `pstack-verifier` a required check once it posts a real verdict.
- **Where work runs:** Run agents, builds, focused tests and app or phone driving on this server. Run the full suite, CI, reviews and verifiers on GitHub-hosted runners. Never add a self-hosted runner.
- **Models:** Set up reviewers and verifiers yourself on Valentin's plans: Codex, then Grok, then DeepSeek. Keep Claude for orchestrators. Move on when one runs out. Use DeepSeek Flash, never Pro.
- **Runner keys:** Give a repo's GitHub review and verifier runners Valentin's plan logins yourself with `ci-key-set`. Never ask him first.
- **DeepSeek via Pi:** Run DeepSeek through Pi on the OpenCode Go plan, never the OpenCode app.
- **Billing block:** Billing blocks only private repos on Valentin's personal account; run `billing-blocks OWNER/REPO` before you blame it. A blocked PR waits: never verify it here or merge around it. Say so once on the ticket.

## Valentin decides

- **His calls:** Ask Valentin before new spend, rotating or deleting keys, making an existing repo public or deleting live data. Ask once, with your pick.

## Changing these rules

- **Changes:** Change this file only through `/house-rules-update`.

## Enforcement

| Rule | Enforced by |
| --- | --- |
| Tickets | not yet |
| Cloudflare | not yet |
| Secrets | `secrets-guard` hook |
| Open source | `repo-public-default` hook |
| Verifier | not yet |
| Verifier per repo | not yet |
| Where work runs | `no-vps-ci` |
| Models | judgment |
| Runner keys | `ci-key-set` script |
| DeepSeek via Pi | `deepseek-via-pi` hook |
| Billing block | `billing-blocks` script, `billing-claim-guard` hook |
| His calls | judgment |
| Changes | `rules-lint` required on main |
