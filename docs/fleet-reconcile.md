# Board reconcile

The board sync script, columns, leases and board 15 rules live in the `hypertask-work` skill in [vstack](https://github.com/valentinyeo/vstack/blob/main/skills/hypertask-work/SKILL.md).
Read [reconcile.md](https://github.com/valentinyeo/vstack/blob/main/skills/hypertask-work/reconcile.md) for the detail.

Every session runs the reconcile itself, for its own board: dry run first, then `--apply`.
No timer does it centrally. pstack has no central layer, so a session that wants its columns true
runs the skill's reconcile on its own board in its own run.
`~/.local/share/house-rules/fleet/reconcile` is a shim that execs the vstack copy, kept so a
worker or hook that already calls it still works.
