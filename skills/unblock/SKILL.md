---
name: unblock
description: Assisted unblock of Valentin's Hypertask blockers. Clears what agents may decide, makes the rest one-glance decisions, presses the owning lead on badly written tickets, and encodes each cleared class so it never blocks him again. Use for /unblock, "unblock me", "blocker count", "what am I blocking", or any lead turn that runs the blocker sweep.
---

# /unblock

Valentin, 2026-10-30: "I want basically an assisted unblock".
Goal: every ticket left on him is a real decision he can take in one read.

## 0. Poteto mode first
Run only in a session started with `/pstack:poteto-mode`. Every run, no exceptions.
The model cannot invoke it (disable-model-invocation). Leads put it first in their launch prompt.
Not in poteto mode? Stop and tell the owner lead to restart the session with it.
Valentin, 2026-10-30: "the whole skill of /unblock should start with /pstack:poteto-mode".

## 1. List
`python3 ~/.local/share/house-rules/skills/tickets/scripts/blocker-sweep.py 15 4060 2060`
Add any board in the inbox Decisions split: https://app.hypertask.ai/inbox?split=Decisions
Write the count. It is the "before" number.
STALE lines are already decided by the sweep: clear them without a full read.

## 2. Read each one
Ticket, marked Question, last 5 comments, bound PR state (`gh pr view`).
Owner lead: board 15 HT Product Lead; 4060 Infra Lead; 2060 and SF boards Mini Boss CEO.

## 3. Classify (first match wins)
| Class | Test | Do |
|---|---|---|
| Stale | PR merged, already live, premise gone, or ANSWERED/STALE/NO-QUESTION in the sweep | Clear it. Tell the runner the next step. |
| Not his | House rule "Never block Valentin on non-decisions", or a line in `learned.md` | Decide per the recommendation. Clear it. |
| His | Money, paid calls, keys, going public, prod data deletion, needs him at his PC | Keep. Go to step 5. |

Clear = agent-lane comment with the reason, then `vcc task waiting-on T --user none` (boards 15, 4060) or plain `hypertask` (2060).
The red border (blockerCommentId) has no CLI yet. Note it in the agent lane.
Until https://app.hypertask.ai/detail/project-15/8200 ships, cleared tickets stay in his Decisions inbox. Only his own reply removes them. Say so in the report.
ANSWERED with a question from him? It waits on the lead now. Point the lead at it.

## 4. Stop it coming back
For every Stale or Not his ticket, name the cause in one line:
- Runner asked a non-decision: add the class to `learned.md` (one line, dated, his quote if any).
- Tool or infra error made the block: file it in Agent Blocked Infra for the owner lead.
- Question left open after the work moved on: press the lead (step 6).
Same cause twice? Build the check (lint rule, wrapper refusal), not more text.

## 5. Quality gate on what stays
Ticket: run `skills/tickets/scripts/ticket-lint` on the description and the Question.
Then check by eye against `skills/tickets/SKILL.md`:
- One problem. Plain nouns he sees in the app.
- Shape: Now, Problem, Fix, Done when, Risk, Decision.
- Description and Question agree (no "Decision: none" with an open Question).
Question:
- One yes/no. Recommendation right under it. Why in one line.
- Yes and No each say what happens next.
- Money asks state the amount.
- After his yes, the next comment says the one step he does, if any.
- He can answer without research. "What this is:" explains every term.
Fails and you can fix the facts in under 5 minutes? Research it yourself. Give him the answer in the report.
Otherwise press the lead to rewrite (step 6). Never rewrite runner tickets yourself past that.

## 6. Press the lead
One ticket per lead per run: board 4060 for HT Product Lead, 2060 for Mini Boss CEO.
Leads are agents under Valentin's login, so they cannot be assigned.
Point Mini Boss at it: `session-say projects "<ticket link>" --from <you>`.
HT Product Lead refuses session messages. It reads 4060 on its own.
Title: "Ticket quality: N blockers on Valentin badly written".
One bullet per ticket: link, which rule broke, what good looks like.
Ask the lead to fix the runner's skill or wrapper, not only the ticket.
Agents talk only on tickets. No direct messages.

## 7. Report
Caveman. Before and after count.
- Cleared: link plus one-line reason.
- His calls left: link, the question in plain words, my recommendation, what Yes and No mean.
- Leads pressed: ticket links.
- New lines in `learned.md`.
