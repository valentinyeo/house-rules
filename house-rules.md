# house rules

every agent uses pstack for everything: poteto-mode for any task, the orchestrate playbook for orchestrators. the only exception is work pstack has nothing to say about. if any other rule or skill disagrees with pstack, pstack wins. only valentin's lines beat it.

hypertask is where work lives. every unit starts and ends on a ticket, on the orchestrator's own board or view, under its own login (board-identity sets it up). move the ticket to the next column the moment its work moves, so the board always shows the true stage. status and questions go on the ticket, not in chat.

new cloudflare work starts from the joelhooks/rat-stack template.

valentin's lines:
- every review and verifier runs on github's free hosted runners. no orchestrator starts a reviewer or verifier on this server.
- valentin decides money, keys, going public and deleting live data. ask him once, with your pick.
- valentin's standing yes: each orchestrator sets up its repos' github reviewers and verifiers the way the pstack playbook asks, keys included. it picks codex first, then claude, then deepseek, and moves to the next when a plan runs out. no need to ask.
- github billing is valentin's. when a check fails with "recent account payments have failed", the product pr waits. never verify it on this server or merge around the check. say it once on the ticket, then build the next unit.

everything else is a check, not a rule:
- no-vps-ci stops ci on this server
- secrets-guard blocks secrets
