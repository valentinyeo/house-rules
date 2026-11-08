# Gates: YPER4-1380 stopped runners on today's rules

OWNS: systemd/fleet-runner-tick.service, systemd/fleet-runner-tick.timer, bin/install-fleet-runner-tick.sh, fleet/drill, fleet/runner, fleet/legacy/README.md, GATES.md

- [ ] G1: User tick unit runs fleet/runner tick, not legacy ht-or-runner.
  CHECK: systemctl --user cat fleet-runner-tick.service 2>/dev/null || systemctl --user cat ht-or-runner-tick.service
  EXPECT: fleet/runner tick

- [ ] G2: dead-runner drill passes locally.
  CHECK: /home/valentin/projects/worktrees/infra-runner-3-yper4-1380/fleet/drill dead-runner
  EXPECT: dead-runner drill ok

- [ ] G3: PR open with ship-check pr green.
  CHECK: SHIP_REPO=valentinyeo/house-rules SHIP_BASE=main SHIP_CHECKOUT=/home/valentin/projects/worktrees/infra-runner-3-yper4-1380 /home/valentin/.agents/skills/ship/scripts/ship-check pr YPER4-1380
  EXPECT: ok

- [ ] G4: Merged to main and installed on VPS.
  CHECK: SHIP_REPO=valentinyeo/house-rules SHIP_BASE=main SHIP_CHECKOUT=/home/valentin/projects/worktrees/infra-runner-3-yper4-1380 /home/valentin/.agents/skills/ship/scripts/ship-check merged YPER4-1380
  EXPECT: ok

- [ ] G5: Live timer active and legacy bins gone.
  CHECK: systemctl --user is-active fleet-runner-tick.timer && test ! -e /home/valentin/.local/bin/ht-or-runner
  EXPECT: active

- [ ] G6: Ticket Done with ship-check done.
  CHECK: SHIP_REPO=valentinyeo/house-rules SHIP_BASE=main SHIP_CHECKOUT=/home/valentin/projects/worktrees/infra-runner-3-yper4-1380 /home/valentin/.agents/skills/ship/scripts/ship-check done YPER4-1380
  EXPECT: ok
