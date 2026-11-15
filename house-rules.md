# house rules

every agent uses pstack for everything: poteto-mode for any task, the orchestrate playbook for orchestrators. the only exception is work pstack has nothing to say about. if any other rule or skill disagrees with pstack, pstack wins. only valentin's lines beat it.

hypertask is where work lives. every unit starts and ends on a ticket, on the orchestrator's own board or view, under its own login (board-identity sets it up). move the ticket to the next column the moment its work moves, so the board always shows the true stage. status and questions go on the ticket, not in chat.

new cloudflare work starts from the joelhooks/rat-stack template.

valentin's lines:
- every pr gets a pstack verifier before merge: an agent that did not write it, from another model family, runs the change like a user and posts PASS, PASS+NOTES or FAIL on the pr. a bot review or green ci is not a verdict.
- verifiers run off this server: a github-hosted runner, claude code cloud or codex cloud. orchestrators may use valentin's codex, claude and deepseek plans for them, keys included, in that order, and move on when one runs out. no need to ask.
- valentin decides money, keys, going public and deleting live data. ask him once, with your pick.
- github billing is valentin's. when a check fails with "recent account payments have failed", the product pr waits. never verify it on this server or merge around the check. say it once on the ticket, then build the next unit.

everything else is a check, not a rule:
- no-vps-ci stops ci on this server
- secrets-guard blocks secrets
