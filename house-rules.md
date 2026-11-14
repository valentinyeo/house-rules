# house rules

orchestrators run the pstack orchestrate playbook. if any other rule or skill disagrees with it, the playbook wins. only valentin's lines beat it.

hypertask is where work lives. every unit starts and ends on a ticket, on the orchestrator's own board or view, under its own login (board-identity sets it up). move the ticket to the next column the moment its work moves, so the board always shows the true stage. status and questions go on the ticket, not in chat.

new cloudflare work starts from the joelhooks/rat-stack template.

valentin's lines:
- every review and verifier runs on github's free hosted runners. no orchestrator starts a reviewer or verifier on this server.
- valentin decides money, keys, going public and deleting live data. ask him once, with your pick.

everything else is a check, not a rule:
- no-vps-ci stops ci on this server
- secrets-guard blocks secrets
- the pacer picks which plan each worker runs on
