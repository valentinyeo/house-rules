---
name: tickets
description: Rules for writing Hypertask tickets and comments. Use before any ticket create, description edit or comment, for every lead, runner and script, any fleet, any brain.
---

# Ticket writing: two lanes

## Human lane
Ticket title, description, and comments with `--kind question|qa|done`.
Also any comment that @mentions a person.
Valentin 2026-10-28: "description -> pospeak, comments pospeak, agent lane agent to agent discussion/talk/updates do what you want".
- Run `pospeak` on every description and people comment before posting.
- Caveman + pospeak. Max 8 words per sentence.
- Answer first. Product-owner words.
- No file paths, function names, logs or transcript paths.
- Links in full and clickable.
- Mention a person with a real mention, never a plain name. A plain name sends no notification.
  The CLI has no mention option yet (https://app.hypertask.ai/detail/project-15/8268). Until then put this in the comment text:
  `<span data-type="mention" class="mention" data-id="Full Name" data-label="name-<userId>" data-mention-suggestion-char="@">Full Name</span>`
  Get `<userId>` from `creatorId` in `hypertask comments list <ticket>`, or from an existing mention on the ticket.
  Read the comment back; `name-<userId>` must be in it.
  Valentin 2026-11-02: "why hast he cli no guidance and toosl for mentioning".
- Title says the user-visible problem or outcome.
  Bad: "Chat sync audit: pane_missing drift".
  Good: "Chat messages missing after reload".

## Ticket shape (human lane)
Models: https://app.hypertask.ai/detail/project-15/7852 (open), https://app.hypertask.ai/detail/project-15/7846 (done).
- **Title:** what changes for the user. No code words.
- **Problem:** 2 to 4 short bullets. Quote Valentin if he asked, in a quote block (`> `), never plain quote marks.
- **Fix:** what we do, plain words.
- **Done when:** checks anyone can confirm.
- **Risk:** worst case, plus the undo.
- **Decision:** one marked Question, or "none".
- **Now** (top line while he must act): state today plus his one decision. Rewrite it when the state changes.
  Valentin 2026-10-29: "it took me a long time to fdiguore what was wonated of me".
- **Result** (when done): what happened, 3 to 4 bullets.
- **One problem per ticket.** Two bugs that can be fixed apart? Two tickets. Link them under "Not in this ticket".
- **Every noun is something he sees.** Name the app and the screen. No hub, server, setup, checks, exception, delivery.
  Valentin 2026-10-30 on IGSH-1169: "ticket is badly written".

## Brain tag (required on every ticket)
When you create or edit a ticket, set exactly one label:
- `brain-light`: tiny fix, rename, one file, obvious one-liner.
- `brain-medium`: default. Normal feature, bug, design apply.
- `brain-hard`: hard bug, security, money or billing, many systems.
- `brain-extra-hard`: rare. Auth or account integrity, or security plus money. Runners skip it.

Rules:
1. Always pick one. Never leave it blank.
2. Unsure? `brain-medium`.
3. Never more than one `brain-*` label.
4. Keep all other labels. Only add or replace the `brain-*` one.
5. Never invent other brain names.

Valentin, 2026-11-06:
> Brain tag (required on every new ticket)

Check: `skills/hypertask-triage/scripts/flow-check --board <id>` prints the NO-BRAIN count.

## Question comment
One open Question per ticket. Mark it as the blocker. Retire older ones.
Only Chief Of Staff and the ticket's board lead (scopes.json) may write it or make Valentin the waiting person.
A runner that cannot go on sets the waiting person to its lead or Chief Of Staff and adds an agent-lane note with
what it tried. Lead first, Chief Of Staff after 2 hours or when no live lead. The vcc wrapper refuses a runner
and a Question outside his call classes (`blocker-review --gate`, one definition with `blocker-review`).
Valentin, 2026-11-07:
> When I'm the blocker, an AI, Claude Opus 5.5, needs to become active and actually try to unblock it as themselves. If they fail and I'm literally the only instance that can unblock it, the AI writes a proper comment with an easy to understand summary and a recommended action.
```
What this is: <4 to 8 short pospeak lines>
Question: **<yes/no question?>**
My recommendation: Yes|No.
Why: <one line>.
Yes: <what happens>
No: <what happens>
```
- Recommendation sits right under the question, never buried.
- Blank line between each line. Single line breaks merge into one paragraph.
- No outside links, sources or product precedents in a Question.
  Valentin 2026-10-29 on a 20-line question: "awful comments".
- His 👍 on the Question confirms your recommendation. Act on it.
  Valentin 2026-10-29: "thumbs up is enough to confirm if reocmmendation is yes".
- Waiting on him always points at one marked Question comment.
- Ask only when his answer can act today. No "once X is live" questions.
- Money asks state the amount. "Saves money" alone is not a question he can answer.
- Retire a Question when the work moves on: PR merged, already live, premise gone.
  Clear his name and the red border, then post a fresh Question only if he must decide again.
- After his yes, say the one step he does, if any. "Nothing to do" is a step.
- Never ask him for a rule exception, a test place or a tool permission. That goes to your own lead.
- Before any Question, check `skills/unblock/learned.md`. Listed there? Decide it yourself.
- Need his yes later? Post a fresh Question in that comment. Never link back to an old one.
  Valentin 2026-10-29: "still have blockers without mention of what comment contains the blocking question".
- "What this is:" comes first, in pospeak. He decides from it alone.
  Say what the thing is, as he sees it in the app.
  Say why it reached him: which of his calls (money, key, going public).
  Say what Yes and No each change for him. Explain every term once.
  Valentin 2026-11-02:
  > my problem is that i dont understand waht the tickets want from me most of the time i need to be spoken to in /pospeak with enough context to make the decisoin
- He answered? Clear the blocker at once, both parts:
  his name (`vcc task waiting-on T --user none`)
  and the red comment border (blockerCommentId null).
  Valentin 2026-10-29: "remove th eblocker both from my name and from the comment red border".

## Done comment
Bold outcome first. Proof in one line. "Nothing to decide." Change link.

## Agent lane
`vcc activity add`, or a plain comment with no `--kind` and no @mention, posted from an agent login.
Under Valentin's own login a plain comment is a people comment in his name. Never post agent notes that way. No agent login on the board (for example board 339)? Skip the note and keep it local (YPER4-944).
Anything goes: agent-to-agent talk, status, claims, handoffs.
Claims, "Released", `Next:`/`Helpers:`/`Branch/PR:`/`Outputs:`, gates,
resume commands and tmux lines go here, never in the human lane.
Verbose is fine here. Paths, logs, evidence, transcript refs go here.

## Scripts too
Audit scripts and crons follow the same rule.
Human summary in the description.
Raw evidence in an agent-lane comment or attachment.

## Before posting
Reread the human-lane text once.
Sentence over 8 words, or has a path? Rewrite it.
Dev words out: caret, composer, rail, deploy, commit, branch, flag key. Say what he sees.

## Guard
- Write files with the file tool, then read the token and run `hypertask` in a separate command.
`scripts/ticket-lint` checks human-lane text before it posts.
It bounces: sentences over 12 words, paths, file names,
code names, commit hashes, logs, robot status lines.
A Question also bounces when it costs money and names no amount,
or when it only matters "once" something else happens.
`blocker-sweep.py` reports STALE when a marked Question outlived its work.
Edits check only new lines. Agent lane is never checked.
Every board write wrapper runs it (ceo-ht does). No bypass.
No wrapper? Raw `hypertask` writes too: run `ticket-lint <file>` first, by hand.
Valentin 2026-10-29: "still ignored on every ticket ... pls enforce this".

## One spec, one runner
Never split a feature spec across runners.
One runner builds the whole spec, one session.
Then a fresh reviewer (spec + diff only) checks it.
A verifier tests the user flows end to end.
Subtasks under a feature are that runner's checklist.
Helpers only review, test or look up. Never build part of a feature.

Too big for one run? Split it before it is picked, never across runners at once. Each part is its own one-run ticket with one Done when line, linked BlockedBy the part before it, so one runner takes one part at a time. `ticket-ready` marks a ticket Not Ready when it has several deliverables, and `fleet/pick` skips it until the ticket is split or shortened (house rules, 14 Nov, HYCI-396).
Many small tickets only for independent bugs or polish.
Max one open PR per runner. Open PRs never exceed runner count.
