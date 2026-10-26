# Design work and runners

Use the existing Hypertask runners. No separate design runners.

1. Problem ticket in UX needed (board 15). Valentin signs off the wireframe in UX Sign-off.
2. After his yes, file one small HTPR ticket per fix in board 15 Todo. Runners pick from there. Link the problem ticket.
3. Ticket body: the approved wireframe or screenshot, the rule, file:line, the acceptance line, and "UI change: Before / After / Why review by design lead."
4. One small PR per ticket. Follow the repo's AGENTS.md. Flags default per AGENTS.md; switching one needs Valentin's go.
5. The runner ships via /ship and merges after required checks pass. You do not poll CI.
6. Before the runner merges, post the Before / After / Why table on the ticket. A blocking finding goes in a `Question:` to the runner, not a PR edit.
7. After UX Sign-off, the approved ticket moves to Features with label "Design" (reuse it) so runners pick it up.

## Done proof (all on the ticket)
- Before and after screenshots of the same screen in Light, Dark and AMOLED, at desktop 1440 wide and phone 390x844. From production after deploy, QA account 985, headless.
- Visual Regression diff PNGs attached. Any unexpected diff fails the review.
- ui-patterns lint baseline count not raised. Paste the before and after count.
- Layout-lock specs green on the merged commit.
Done only with all of it.

## Runners, board and GitHub (from HT Product Lead, 2026-10-26)
- Hypertask runners self-pull only board 15 (Bugs, Features) and board 4060 (Backlog). They never watch HEFE (10450) or MARK (2108).
- Code work becomes a board 15 or 4060 ticket with a reused Title Case label, or goes to HT Product Lead to assign.
- Runner blockers on your tickets come to HT Product Lead. Never message runners mid-ticket except to answer them.
- hypertask-ai/hypertask has no automerge. The runner merges after required checks pass, deploys and proves it live. You check the ticket once later.
- GitHub quota is shared and scarce. Never poll gh or Actions. At most one gh read per check-in.
- Board writes only through vcc as your own agent identity. Never Valentin's token.
- After 23:00 London you start no new loops. Runners keep running.
