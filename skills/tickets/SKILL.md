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
- Title says the user-visible problem or outcome.
  Bad: "Chat sync audit: pane_missing drift".
  Good: "Chat messages missing after reload".

## Ticket shape (human lane)
Models: https://app.hypertask.ai/detail/project-15/7852 (open), https://app.hypertask.ai/detail/project-15/7846 (done).
- **Title:** what changes for the user. No code words.
- **Problem:** 2 to 4 short bullets. Quote Valentin if he asked.
- **Fix:** what we do, plain words.
- **Done when:** checks anyone can confirm.
- **Risk:** worst case, plus the undo.
- **Decision:** one marked Question, or "none".
- **Result** (when done): what happened, 3 to 4 bullets.

## Question comment
One open Question per ticket. Mark it as the blocker. Retire older ones.
```
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
  Valentin 2026-10-29: "still have blockers without mention of what comment contains the blocking question".
- Context above the question: max 3 bullets, plain words.
  Valentin 2026-10-29: "pospeak don't burr your recommendation".
- He answered? Clear the blocker at once, both parts:
  his name (`vcc task waiting-on T --user none`)
  and the red comment border (blockerCommentId null).
  Valentin 2026-10-29: "remove th eblocker both from my name and from the comment red border".

## Done comment
Bold outcome first. Proof in one line. "Nothing to decide." Change link.

## Agent lane
`vcc activity add`, or a plain comment with no `--kind` and no @mention.
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

## One spec, one runner
Never split a feature spec across runners.
One runner builds the whole spec, one session.
Then a fresh reviewer (spec + diff only) checks it.
A verifier tests the user flows end to end.
Subtasks under a feature are that runner's checklist.
Helpers only review, test or look up. Never build part of a feature.
Many small tickets only for independent bugs or polish.
Max one open PR per runner. Open PRs never exceed runner count.
