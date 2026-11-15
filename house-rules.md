# House rules

Rules for every agent on Valentin's projects. Run `/pstack:poteto-mode` for every task. These rules beat pstack. pstack beats every other rule and skill.

## Work

- **Tickets:** Start and end every unit on a Hypertask ticket, on your own board or view, under your own login (`/board-identity`). Move the ticket the moment its work moves. Put status and questions on the ticket.
- **Cloudflare:** Start new Cloudflare work from `joelhooks/rat-stack`.
- **Secrets:** Never write a secret into a file, commit, ticket or chat.

## Verify and ship

- **Verifier:** Give every PR a pstack verifier before merge. It comes from another model family than the author, runs the change like a user, and posts `pstack-verifier: PASS|PASS+NOTES|FAIL @ <sha>`. Green CI or a bot review is not a verdict.
- **Verifier per repo:** Build each repo's own verifier and app driver. Make `pstack-verifier` a required check once it posts a real verdict.
- **Where work runs:** Run agents, builds, focused tests and app or phone driving on this server. Run the full suite, CI, reviews and verifiers on GitHub-hosted runners. Never add a self-hosted runner.
- **Models:** Set up reviewers and verifiers yourself on Valentin's plans: Codex, then Claude, then DeepSeek. Move on when one runs out. Use DeepSeek Flash, never Pro.
- **Billing block:** A check that fails with "recent account payments have failed" means the PR waits. Never verify it here or merge around it. Say so once on the ticket and build the next unit.

## Valentin decides

- **His calls:** Ask Valentin before money, keys, going public or deleting live data. Ask once, with your pick.

## Changing these rules

- **Changes:** Change this file only through `/house-rules-update`.

## Enforcement

| Rule | Enforced by |
| --- | --- |
| Tickets | not yet |
| Cloudflare | not yet |
| Secrets | `secrets-guard` hook |
| Verifier | not yet |
| Verifier per repo | not yet |
| Where work runs | `no-vps-ci` |
| Models | judgment |
| Billing block | not yet |
| His calls | judgment |
| Changes | `rules-lint` required on main |
