# Board 2060 caller migration

Prepare callers before renaming live columns.
Keep old aliases until the follow-up PR.
No columns renamed. No deployments. No merges.

Canonical order: Todo, Building, Checks, Verifier, Valentin Review, Done.

- PR opened -> Checks.
- checks green -> Verifier.
- merged -> Verifier pending live proof. current-head PASS, merged, and live proof -> Done.

`fleet/workflow_columns.py` defines names and verdict handling.
`fleet/pr-merge` updates columns during its existing timer.
`fleet/park` sends Software Factory PRs to Checks.
`sf-release-watch` also requires the current-head verdict.
Other boards retain their own column names.

`soft-2446-callers.json` inventories every supplied path.
The real vstack source is `~/.local/share/vstack`.
`~/projects/vstack` contains the older, moved toolkit.
Most listed host scripts have no tracked source.
The fleet command comes from `hypertask-ai/agent-worker`.
The report source now lives at `bin/pr-table.py`.
Copy that file only after merging this PR.
The retired Multiprompt picker gets a restoration patch.
Never activate that retired picker during migration.
Wazig board 4874 retains its current column names.
GitHub check names remain unchanged.
Historical backups remain unchanged on the server.

Reproduction, before fixes:

```text
python3 -m unittest tests.test_workflow_columns -v
FAILED (failures=5, errors=1)
Building tickets disappeared from solo-wake candidates.
Verifier without a PR returned no warning.
Picker omitted Building, Checks and Verifier.
```

Real server observation, before any column rename:

```text
hypertask --json section list --project 2060
Todo 4351, Doing 4352, Checks 38278,
AI Review 27310, Valentin Review 32313, Done 22848
```

Real tool run, against the live board:

```text
python3 skills/solo-dev/scripts/parked-review --board 2060 --hours 1
SUMMARY board 2060 AI Review, Checks, Verifier: 36 parked over 1h
exit 1: existing stale tickets reported, as designed
```

Focused regression after fixes:

```text
python3 -m unittest tests.test_workflow_columns tests.test_ticket_ownership -v
Ran 18 tests
OK
pr-merge: SOFT-2446 Doing -> AI Review
pr-merge: SOFT-2446 Building -> Verifier
```

Break attempts:

1. Old and new columns coexist. Prefer new.
2. Stale, forged, or later FAIL verdict. Refuse Done.
3. No checks, red checks, or human review. Preserve gates.

GitHub runs the regressions and DeepSeek Flash verifier.
Full test suites run only on GitHub-hosted runners.
Feature map and verification-skill tests: not applicable.
This changes automation and instructions, without app screens.

After every caller PR merges, rename board columns separately.
Then remove aliases in one follow-up wave.
The user explicitly excluded that removal here.

Historical rule notes moved from edited lines:

```text
(2026-11-02, why: IGSH-1353 sat there with "Decision: None")
(2026-11-02, why: "fix the origin of tickets not being moved")
```

Additional break attempts failed before correction:

```text
Missing checks plus PASS: merged != wait
Successful rerun: Checks != Verifier
```

Both now pass the focused regression.

Main advanced during verification through PR #589.
It removed archived board 11514 from fleet operations.
Rebased this branch and preserved that cleanup.
HYCI tickets now share board 2060's column contract.
The missing-check guard now covers HYCI too.
The upstream board-archive regressions still pass locally.
