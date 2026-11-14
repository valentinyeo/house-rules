# HYCI-408 Refused board write: runner retakes the same ticket each minute

Scope: a runner whose board writes were refused must leave the pool after one run, never loop.
The refusal must end as a fault that names the guard, the ticket must go to its lead, and the same
runner must never retake it until the guard clears. Repo: valentinyeo/house-rules (fleet/runner-state.py,
fleet/runner). The guard itself (vcc identity / ship-identity) lives in hypertask-ai/hypertask.

## Gates

1. **Every recorded refusal on 8 and 9 Nov is a fault that names the guard.** Replay the exact reason
   strings the ledger kept for HTPR-7766 (`board-write-blocked`, `identity-guard-blocked`,
   `board-write-guard`, `authorization-blocked`, `board-write authorization blocked`,
   `failed-QA-routing-blocked`) through `fleet/runner-state.py --classify`. Each is `FAULT` with
   `park: lead` and a detail naming the guard. Proof: a `--self-test` block built from those strings
   and its passing output.
2. **The replay gives at most 3 runs.** A run classified `FAULT` with `park: lead` moves the ticket to
   its lead on the same run (`fleet/park --lead`), so the picker offers it to nobody afterwards. The
   synthetic replay in gate 1 shows run 1 is the last run, which is 1 run, not 165.
3. **A real wait is not read as a refusal.** `RUNNER IDLE checks pending`, `RUNNER IDLE recheck ...`,
   `RUNNER IDLE blocked by HYCI-140` and a plain `RUNNER IDLE` stay on their current states
   (`WAIT_CHECK` / `PARKED`). Proof: self-test asserts those states are unchanged.
4. **The launcher hands it to the lead in one run.** `fleet/runner` maps `park: lead` to
   `fleet/park <TICKET> --lead --why "<detail>"`; the detail names the guard. Proof: the mapping line
   is read from `fleet/runner` by the self-test, and `fleet/park --lead` sets the lead as the waiting
   person (tested by `fleet/park --self-test`).
5. **Tests pass on the one PR.** `python3 fleet/runner-state.py --self-test` and
   `python3 fleet/tool-gate.py --self-test` pass locally and in the repo's `pick` workflow.
6. **Live after merge.** The live copy `~/.local/share/house-rules/fleet/runner-state.py` contains the
   new rule (`git rev-parse HEAD` matches main) and classifies a refusal as `FAULT`/`lead` on the host.

## Gates on the same ticket in hypertask-ai/hypertask (the guard itself)

7. **The guard names a runner session as its own runner, not as Valentin.** `ship-identity` resolves a name
   that carries a runner slot (`ht-or-runner-5`, `cursor-grok-runner-5 (Cursor Grok RUNNER 5)`) to
   `RUNNER 5` and `runner-5-agent-token`. A literal token still wins; a slot with no token, `SPEED RUNNER`
   and `runner` still fall back. Proof: `.claude/skills/ship/scripts/ship-identity.test.sh` passes.
8. **vcc accepts that write and refuses every other.** `SHIP_SESSION_NAME=ht-or-runner-5` writing as
   `RUNNER 5` is allowed; the same name writing as `RUNNER 6` or as Valentin is still refused before any
   board call. Proof: the new cases in `.claude/skills/vcc/bin/vcc.test.sh`, run in `ship-scripts-tests`.
9. **Live after merge.** `~/.agents/skills/ship/scripts/ship-identity` (the live link) resolves
   `SHIP_SESSION_NAME=ht-or-runner-5` to `RUNNER 5` on the host.

## Not in scope, named so the ticket is honest

The guard and the loop fix are two repos, so two small PRs on this one ticket. The refusal text `vcc: ...
has no board login; refusing to write as ...` stays for a session whose name names no runner or a
different runner: that is still correct.
