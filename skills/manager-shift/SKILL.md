---
name: manager-shift
description: Start, check and end every lead shift. Keep work on the board and one handover file; stop at 120k context tokens or four hours. Use at lead startup, every check-in, before taking more work, and before clearing context.
---
# Manager shifts

The board holds work. One file holds handover.
Never depend on an old conversation for decisions.
Apply this to every lead, including HT Product Lead.

## Start a shift

1. Load house rules and your role skill.
2. Keep your existing board identity and permissions.
3. Use the role slug and current session ID.
4. Run the shared check from the synced skill:

```bash
SHIFT="$HOME/.agents/skills/manager-shift/shift.py"
python3 "$SHIFT" start --role support --session "$SESSION_ID"
```

Use `product`, `support`, `design`, `growth`, or `finance`.
Other projects use their existing lead slug.
Never copy a different session's ID.
The command prints the previous handover when present.
Read it, then read current board replies.
Match old questions against replies before asking again.
Never clear another session or seize its shift.

## Check before every work batch

```bash
python3 "$SHIFT" check --role support --session "$SESSION_ID" --context "$CONTEXT_TOKENS"
```

Read total context size from your harness.
Use input context, including cache reads, not output.
A missing count is a blocker, not zero.
The count cannot decrease during one shift.
At 100k tokens, prepare handover.
At 120k tokens or four hours, stop work.
Exit `3` means handover required before more work.
Repeated wakes never restart the four-hour clock.

Respect the existing manager lease and grant receipt.
The shared check never changes pools or leases.
No automatic clearing or process termination.

## Keep managers quiet

- Runners write ticket comments and agent activity.
- Do not send routine tmux or session-mail pings.
- Managers read one digest every 30–60 minutes.
- Store the next digest time in the handover.
- Digest sources: own board, replies, claims, deployments.
- Cheap triage first: Codex; Haiku in Claude mode.
- Wake the manager only for a real decision.
- Urgent failures go on their ticket immediately.
- Mention your project's lead for urgent decisions.
- Never send status messages to Valentin.

Fast mode off.
For Claude shifts, default to Sonnet medium.
Spawn a fresh Opus worker for the hardest judgment.
Workers exit; their decisions go on tickets.
Follow existing rules for money, keys and X.

## End, clear and resume

1. Finish or hand off each action already running.
2. Put durable decisions and evidence on tickets.
3. Prepare a private UTF-8 handover file:

```markdown
## Role
Role name, project boards, current provider, session ID.
## Open work
Full ticket and PR links, current state, owners.
Active helpers, output paths, required checks, outstanding failures.
## Decisions
Pending questions with links; replies already acted upon.
Write none explicitly when nothing waits.
## Next actions
Three ordered actions with links and evidence paths.
## Last digest
Last read time, next read time, runner state.
```

4. Save it before clearing:

```bash
python3 "$SHIFT" end --role support --session "$SESSION_ID" --handover /private/path/draft.md
```

The tool atomically writes `~/poteto-handover/support-shift.md`.
No secrets, credentials, tokens or private customer data.
An incomplete handover leaves the shift active.
A closed shift refuses further work.
5. Clear only your own session with `/clear`.
6. Resume with a fresh session ID or generation.
   Some harnesses keep their ID after `/clear`.
   In that case append the new clear timestamp.
7. Run start, read handover, then current board.
   Do not load the previous full transcript.
8. Record one cycle receipt on the ticket.
   Include IDs, handover path, retained work and decisions.

## Verify rollout

Before rollout, get HT Product Lead agreement.
One consenting lead must run the complete cycle.
Compare open work and decisions before and after.
Any missing item fails the cycle.
Fixture tests cannot replace this live lead check.
