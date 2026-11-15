# house rules

every agent uses pstack for everything: poteto-mode for any task, the orchestrate playbook for orchestrators. the only exception is work pstack has nothing to say about. if any other rule or skill disagrees with pstack, pstack wins. only valentin's lines beat it.

hypertask is where work lives. every unit starts and ends on a ticket, on the orchestrator's own board or view, under its own login (board-identity sets it up). move the ticket to the next column the moment its work moves, so the board always shows the true stage. status and questions go on the ticket, not in chat.

new cloudflare work starts from the joelhooks/rat-stack template.

valentin's lines:
- every pr gets a pstack verifier before merge: an agent that did not write it, from another model family, runs the change like a user and posts PASS, PASS+NOTES or FAIL on the pr. a bot review or green ci is not a verdict.
- this server is lauren's laptop: orchestrators, workers writing code, a focused test while fixing (pstack tdd), driving the app or the qa phone like a user, benchmarks, git, boards, keys. github-hosted runners are her cloud: the full test suite, ci, reviews and the pstack verifier. no self-hosted runner, ever.
- orchestrators set their reviewers and verifiers up themselves on valentin's deepseek, codex and claude plans, keys included, in that order, and move on when one runs out. claude is allowed for workers and checks. other plans go first while claude usage is high, so orchestrators keep headroom. on deepseek, always flash, never pro. no need to ask anyone.
- valentin decides money, keys, going public and deleting live data. ask him once, with your pick. a design pick is never his: build your own pick, he judges it live. a ticket labelled needs-design gets 2-3 figma variants (figma-design skill) shown to him first; no build starts before he has seen them.
- a public repo starts with `new-public-repo`, never github's template or fork button. no commit carries a real email. agents switch on github's "keep my email addresses private" for valentin themselves.
- github billing is valentin's. when a check fails with "recent account payments have failed", the product pr waits. never verify it on this server or merge around the check. say it once on the ticket, then build the next unit.

what enforces each line (pstack /correct: a check beats a sentence; drop a line once its mistake can't happen):

| line | enforced by |
| --- | --- |
| pstack for everything | nothing, judgment call |
| tickets, own login, true column | nothing yet |
| rat-stack for new cloudflare work | nothing yet |
| a pstack verifier on every pr | nothing yet; a required `pstack-verifier` check once the shared verifier workflow works |
| server is the laptop, github is the cloud | `no-vps-ci` kills runners and review units every 5 minutes |
| money, keys, public, deleting live data | nothing, judgment call |
| no design pick in his blockers | `ticket-lint` refuses a Question that asks him to pick a look or option |
| needs-design shown before build | nothing yet |
| no merge around a failed check | house-rules main: `rules-lint` required, admins included; product repos: nothing yet |
| no real email in a public repo | `new-public-repo` refuses to push one; per repo, a ci check on commit emails |
| no secrets anywhere | `secrets-guard` hook |
