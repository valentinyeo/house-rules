---
name: tickets
description: Rules for writing Hypertask tickets and comments. Use before any ticket create, description edit or comment, for every lead, runner and script, any fleet, any brain.
---

# Tickets: two lanes

Valentin 2026-10-28: "description -> pospeak, comments pospeak, agent lane agent to agent discussion/talk/updates do what you want".

## Human lane
Title, description, `--kind question|qa|done`, @mention, reply.
- Run `pospeak` first. Caveman. Max 8 words per sentence.
- Answer first. Product-owner words.
- No paths, function names, logs, transcripts.
- Links full and clickable. Quote Valentin verbatim.
- Title = user-visible problem or outcome.
  Bad: "Chat sync audit: pane_missing drift". Good: "Chat messages missing after reload".
- Reread once. Over 8 words or a path? Rewrite.

## Ticket shape
Models: https://app.hypertask.ai/detail/project-15/7852 (open), https://app.hypertask.ai/detail/project-15/7846 (done).
**Problem** 2-4 bullets. **Fix** plain words. **Done when** checks anyone can do.
**Risk** worst case plus undo. **Decision** one marked Question, or "none".
**Result** when done: 3-4 bullets.

## Question comment
```
Question: **<yes/no question?>**
My recommendation: Yes|No.
Why: <one line>.
Yes: <what happens>
No: <what happens>
```
- One open Question per ticket. Mark it blocker. Retire old ones.
- Recommendation right under the question. Blank line between lines; single breaks merge.
- Context above: max 3 bullets. No outside links or precedents.
- Waiting on him? Point at that one Question comment.
- His 👍 = yes to your recommendation. Act.
- He answered? Clear both: `vcc task waiting-on T --user none` and blockerCommentId null.
Valentin 2026-10-29: "awful comments", "pospeak don't burr your recommendation", "thumbs up is enough to confirm if reocmmendation is yes", "remove th eblocker both from my name and from the comment red border".

## Done comment
Bold outcome. Proof in one line. "Nothing to decide." Change link.

## Agent lane
`vcc activity add T "<text>"`. Anything goes, verbose fine.
Claims, "Released", Next/Helpers/Branch/PR/Outputs lines, gates, resume, tmux, paths, logs, evidence.
Scripts and crons too: human summary in description, raw evidence in agent lane or attachment.

## Guards (scripts)
Valentin 2026-10-29: "still ignored on every ticket ... pls enforce this".
- `vcc` (Hypertask fleet) runs `scripts/ticket-lint` on human-lane text → exit 5. Question shape checked too.
- `vcc comment add T` with no kind, mention or reply → rerouted to `vcc activity add`.
- Only bypass: `VCC_VOICE_BYPASS="<reason>"`, machine evidence writers only, logged. Never for Questions.
- `scripts/ticket-lint` (vcc, ceo-ht, every board wrapper): 12-word hard cap, paths, code names, hashes, logs, robot lines. Edits check new lines only. Agent lane never checked.
- Server-side check: https://app.hypertask.ai/detail/project-4060/910.

## One spec, one runner
- One runner builds the whole spec, one session. Never split it.
- Then a fresh reviewer (spec + diff only). Then a verifier tests user flows end to end.
- Subtasks = that runner's checklist. Helpers only review, test or look up.
- Many small tickets only for independent bugs or polish.
- Max one open PR per runner. Open PRs never exceed runner count.
