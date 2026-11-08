Verbatim copies of the runner launchers and pickers that fleet/pick and fleet/runner replace (YPER4-1371).
Rollback only. Nothing here is run by the new fleet. Each file keeps its original name; the two poteto-cursor files come from the poteto-cursor state folder (run-1.sh, prompt-1.md).
Rollback: copy the file back to ~/.local/bin (or the poteto-cursor state folder) and point the tick timer at it. Live tick unit is fleet-runner-tick (bin/install-fleet-runner-tick.sh); legacy ht-or-runner-tick is retired.
ci-pick and infra-pick are not copied here: they live in git repos (ci-boss, infra-lead) and keep their history.
