# HYCI-250 gates

Scope (from the ticket): DeepSeek runs time out waiting. Cap each model reply at 10 minutes, retry once, then end the run.
Waiting on checks ends the run in its check-wait state (picker resumes). Log the reason each run ends.
Repo: valentinyeo/house-rules (launcher and briefs are our own agent tools).

## g1-syntax
CHECK: `bash -n fleet/runner`
EXPECT: exit 0, no output

## g2-reply-cap
CHECK: `fleet/runner reply-cap-selftest`
EXPECT: `reply-cap self-test ok`
Proves: a chatty attempt is kept, a silent attempt is killed at the cap and returns 124, grandchildren die with it.

## g3-reason-logged
CHECK: `python3 fleet/runner-state.py --self-test`
EXPECT: `runner-state self-test ok`
Proves: "no model reply" classifies as FAULT with the stall reason, so run-ledger.jsonl carries the cause.

## g4-check-wait-rule
CHECK: `grep -l "Never wait inside a run" fleet/briefs/*.txt | wc -l`
EXPECT: 4 (infra, app, sf, ci)

## g5-ci
CHECK: the PR's pick workflow run on the pushed head
EXPECT: conclusion success (`self-test` job)

## g6-live
CHECK: after merge and house-rules-sync, from the live checkout `~/.local/share/house-rules`:
`grep -c REPLY_CAP fleet/runner` and `fleet/runner reply-cap-selftest`
EXPECT: count >= 1 and `reply-cap self-test ok` from the live path

## g7-board
CHECK: `vcc task view HYCI-250`
EXPECT: section Done, with the PR link and the evidence in the agent lane
