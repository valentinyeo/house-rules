# HYCI-276 gates

Ticket: Board health: board 15 red over a day (board 11514, Runner 11).
Scope: board 15 stays red because fleet/pick keeps re-dispatching the board-health alarm to runners, who cannot fix
lead-owned lines. Runner 9 parked HYCI-276 to the board lead four times between 14:11 and 20:19, and it came back
each time. fleet/pick skips a ticket only when it waits on a person (`waitingOnUserId`), not when it waits on an
agent lead (`waitingOnAgentId`), which is what `fleet/park --lead` sets. Fix that, so the alarm reaches the fleet
chief instead of a runner slot.

## G1 scope
CHECK: the ticket's own agent log shows repeated runner claims after lead parks.
EXPECT: four Runner 9 claim + park pairs on HYCI-276 within six hours.

## G2 the waiting flag honours a lead wait
CHECK: `grep -n 'waitingOnAgentId' fleet/pick`
EXPECT: one hit, in `slim()`, inside the `waiting` field.

## G3 picker self-test
CHECK: `python3 fleet/pick --self-test`
EXPECT: exit 0, `self-test ok`.

## G4 PR and CI
CHECK: `gh pr view <n> -R valentinyeo/house-rules --json title,state`
EXPECT: title names HYCI-276, state MERGED, no required check red.

## G5 the picker leaves a lead-parked ticket alone after merge
CHECK: on the merged main, the lead-parked HYCI-276 is not returned for Runner 11.
EXPECT: the pick's stderr reason does not hand out HYCI-276.

## G6 ticket leaves In Progress
CHECK: `vcc task get HYCI-276`
EXPECT: section Backlog, Runner 11 unassigned, waiting person the board lead.

## G7 evidence
EXPECT: exact command output for G3, G4, G5 quoted in the agent lane.
