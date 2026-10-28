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
