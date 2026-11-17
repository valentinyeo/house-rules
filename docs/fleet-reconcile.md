# Reconcile board 2060

`fleet/reconcile` reads board 2060 and GitHub.
Default runs print plans without moving tickets.
`--section Doing` limits a dry run.
`--apply` moves tickets and writes agent-log entries.
Owners and assignees stay unchanged.

## Column rules

Earlier rows take priority.

| Fact | Column |
| --- | --- |
| Already Valentin Review or Done | Keep |
| Ticket touched within two hours | Keep |
| Fresh lease with a live local PID | Doing |
| Open PR, checks running, red, or missing | Checks |
| Open PR, checks green | AI Review |
| Every matching PR merged, current-head PASS | Done |
| Merged PR without current-head PASS | AI Review |
| No live lease or matching PR | Todo |

A passing open PR waits in AI Review.
Searches include both fleet owners across repositories.
Exact ticket keys and board links match.
Closed, unmerged PRs count as no PR.
Read failures print UNKNOWN and prevent that move.
Fresh foreign-host leases also prevent moves.
Stale leases expire after fifteen minutes.

PASS requires a structured `verify-verdict` comment.
The comment must name the current PR head.
The base `.verify/policy.json` controls trusted verifier identities.
Author and verifier model families must differ.
The verdict must link successful GitHub-hosted verification.
The run must match head and approved workflow.
Missing policy means no accepted PASS.
Plain PASS prose and green checks cannot qualify.

## Worker leases

Spawn helpers wrap the worker command.
Add this one line at worker launch.

```sh
fleet/lease "$KEY" run -- worker-command worker-arguments
```

The wrapper records the worker PID.
It renews every sixty seconds.
It removes the lease when that worker ends.
`fleet/runner` watches each launched attempt automatically.
Other launchers can watch an existing worker.

```sh
fleet/lease "$KEY" watch --pid "$WORKER_PID" &
```

Manual lifecycle commands remain available.

```sh
fleet/lease "$KEY" start --pid "$WORKER_PID"
fleet/lease "$KEY" beat --pid "$WORKER_PID"
fleet/lease "$KEY" end --pid "$WORKER_PID"
```

Leases live in `~/.local/state/fleet/leases/<KEY>.json`.
Each contains `pid`, `host`, `started`, and `last_beat`.
Timestamps use Unix seconds.
Atomic writes prevent partial JSON reads.
A live worker cannot replace another worker's lease.
Repeated starts retain the original start time.
Repeated ends are harmless.
`FLEET_LEASE_DIR` overrides the directory for tests.

## Server timer

The supplied timer runs every fifteen minutes.
Installation enables real board moves.
Keep installation for the approved release.

The service uses `~/.local/share/house-rules/fleet/reconcile`.
Its environment comes from `~/.config/fleet/reconcile.env`.
That file supplies the agent's `HT_TOKEN`.
Use mode `0600` for the environment file.
`SHIP_SESSION_NAME` defaults to Poteto in the service.
Override it alongside the matching agent token.
GitHub access uses the server's `gh` login.

After release approval, install the timer.

```sh
bin/install-fleet-reconcile.sh
```

The installer installs supplied user-service files.
Runs serialize through the board-specific lock.

## Self-test

`rules-lint` runs the focused self-test.

```sh
python3 fleet/reconcile --self-test
```
