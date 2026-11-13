# HYCI-355 gates

Scope: fleet/pick refuses a new-work ticket that cannot be built yet (waits on a person,
needs a key or access, needs a design, or is not startable), before any model starts; and a
replay tool shows the effect over the last 7 days. Repo valentinyeo/house-rules.

Ticket: https://app.hypertask.ai/detail/project-11514/355

## Gates

- G1 `fleet/pick --self-test` passes, including new assertions for the cannot-be-built hold.
- G2 A new-work ticket whose text asks for a key, access, Valentin, a paid service, his PC
  or a design hold gets "cannot be built yet: <what>" in the pick trace and in `--dry-run`,
  and no model is started for it.
- G3 The hold never applies to an incident, a ticket with an open PR, or a ticket a runner
  already holds in a building column.
- G4 A ticket that only mentions such words in passing (for example "paid plan" in a
  marketing ticket, "signed-in") is still offered.
- G5 `bin/replay-built [DAYS]` prints first runs, empty first runs, the before/after split
  and the count of empty first runs the hold would now catch, on the real ledger, and
  `--self-test` passes on a fixture ledger.
- G6 CI on the PR is green and the PR is merged to main.
- G7 The measured number (empty first runs in 7 days, and how many the hold now catches)
  is written in the ticket's agent lane, and the ticket is Done.

## Proof

Each gate: the command run and its output line, in the agent lane and in the final answer.
