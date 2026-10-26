# Design work and runners

Use the existing Hypertask runners. No separate design runners.

1. Problem ticket in UX needed (board 15). Valentin signs off the wireframe in UX Sign-off.
2. After his yes, file one small HTPR ticket per fix in board 15 Todo. Runners pick from there. Link the problem ticket.
3. Ticket body: the approved wireframe or screenshot, the rule, file:line, the acceptance line, and "UI change: Before / After / Why review by design lead."
4. One small PR per ticket. Follow the repo's AGENTS.md. Flags default per AGENTS.md; switching one needs Valentin's go.
5. The runner ships via /ship. Green PRs automerge. You do not poll CI.
6. When the PR has a preview, post the Before / After / Why table on the ticket. If it fails, say so on the ticket; the runner fixes it.
