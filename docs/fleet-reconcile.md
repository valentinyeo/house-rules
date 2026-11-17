# Reconcile board 2060

`fleet/reconcile` reads board 2060 and GitHub.
Default runs print plans without moving tickets.
`--section Doing` limits a dry run.
`--apply` previews first, then permits five moves.
`--limit N` changes that per-run cap.
Exceeding the cap refuses every move.
Any UNKNOWN also refuses every move.
Each move writes an agent-log entry.
Owners and assignees stay unchanged.

## Column rules

Earlier rows take priority.

| Fact | Column |
| --- | --- |
| Already Valentin Review, Done, or Not now | Keep |
| Any column outside this table | Keep |
| Ticket touched within two hours | Keep |
| Fresh lease with a live local PID | Doing |
| Open PR, checks running, red, or missing | Checks |
| Open PR, checks green | AI Review |
| Every matching PR merged, current-head PASS | AI Review, live proof pending |
| Merged PR without current-head PASS | AI Review |
| No live lease or matching PR | Todo |

A passing open PR waits in AI Review.
Merged work waits there for live proof.
This script never moves work into Done.
Searches include both fleet owners across repositories.
PR ownership requires one structural link.
The title or branch contains the ticket key.
An anchored `Ticket:` line also qualifies.
An exact Hypertask ticket URL qualifies anywhere.
Other body mentions establish no ownership.
Branch discovery scans both owners, including merged PRs.
Date partitions avoid GitHub search truncation.
Malformed keys report UNKNOWN without stopping other tickets.
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
Installation enables capped board moves after preview.
The current backlog may exceed the default cap.
Such runs refuse writes until reviewed separately.
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
An overlapping run reports SKIP and succeeds.
Apply rechecks tickets and PR facts after preview.
Changed tickets skip that run.

## Self-test

`rules-lint` runs the focused self-test.

```sh
python3 fleet/reconcile --self-test
```

## Column rename compatibility

Building aliases Doing. Verifier aliases AI Review.
Checks keeps its existing meaning.
The sync reads board sections before planning moves.
Destinations prefer Building and Verifier when available.
Existing names remain valid during the staged rename.
Protected columns and the two-hour grace remain unchanged.
Merged work still waits for live proof.
