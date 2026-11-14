# Boards and columns

Read when you file, move, label or clean tickets, or run a board loop.

## Boards

- Board 15 is Hypertask. Board 2060 is Software Factory. Board 11514 (HYCI) is Fleet CI & Infra, the one fleet board. Board 4060 is archived and folded into 11514.
- CI and infra tickets for both fleets live on 11514, never 15 or 2060. CI tickets carry labels CI and Hypertask CI. CI Boss owns the board. Pool runners build them in the CI lane.
- Fleet CI & Infra: file every real problem. No filing cap. Search first. +1 the open ticket for the same problem.
- The board stays small: at most 2 open tickets per live pool runner. Over it, the oldest tickets untouched 7 days are archived with a note. Incident, busy, open-PR, waiting, security and app-blocking tickets stay.
- Software Factory apps are low risk. Tickets filed by Valentin or the design lead ship without his yes, chat and sidebar included. Wrong change: roll back.

## CI snag

A CI snag blocks an app ticket? Every fleet, session and runner:

1. File one Fleet CI & Infra ticket per CI problem on 11514. Search first. Same problem exists? Add a +1 and a link, never a copy.
2. The app ticket stays on its own board. Link it BlockedBy the CI ticket. It waits there.
3. App sessions never fix CI themselves. Pool runners fix it in the CI lane.
4. Fix ships: the app ticket gets a continue note in its agent lane, never a people comment.

## Columns

- Every waiting column has a cap. Over the cap: one urgent alarm ticket, its owner clears it the same day.
- Agent Blocked holds only broken tools or servers. Design: UX needed. His call: Valentin Review plus one Question. Waits on a ticket or date: home column with a link. Merged: QA.
- Hypertask runs `skills/hypertask-triage/scripts/pileup-watch` daily. Other fleets pass their own caps.
- Tickets in work (In Progress, Doing, AI Review, QA) never outnumber workers. Only Valentin Review waits outside the count. The assignee is the owner.
- Each fleet chief runs `/hypertask-triage` step 0 every turn until `board-health` prints GREEN: Chief Of Staff, Mini Boss CEO, inne Chief of Staff. Safe fixes run with `--fix`, never one-off scripts. Chatter from agents: fix the rule or code behind it that day. Never fix tickets one by one.

## Duplicates and labels

- Search duplicates before filing and at each ticket start. Duplicate: close it that turn with "Duplicate of <link>". Shipped and live: Done that turn.
- Every lead turn runs `skills/hypertask-triage/scripts/board-dupes <boards>` and clears every pair.
- Tag every ticket with its app or cluster label at creation. Reuse existing tags. Tags in Title Case. Check old tickets too.
- Every label cluster has a board view filtered by that label. The board manager creates it the same day.
- Agent Blocked holds only broken tools or servers. A tool or infra error goes to Agent Blocked Infra and your own lead.
- Drafts for outside people use normal sentences, not caveman.
