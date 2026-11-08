# Gates: YPER4-1381 old runner pools removed

OWNS: fleet/dead-parts-scan.py, fleet/drill, bin/remove-old-runner-pools.sh, fleet/legacy/README.md, skills/lead/ht.md

- [ ] G1: Scan lists live old timers before removal.
  CHECK: /home/valentin/projects/worktrees/infra-runner-2-yper4-1381/fleet/dead-parts-scan.py | grep -c timer-enabled
  EXPECT: ^[1-9]

- [ ] G2: Removal script leaves the host clean.
  CHECK: /home/valentin/projects/worktrees/infra-runner-2-yper4-1381/bin/remove-old-runner-pools.sh
  EXPECT: remove-old-runner-pools ok

- [ ] G3: dead-parts drill passes on the live host.
  CHECK: /home/valentin/projects/worktrees/infra-runner-2-yper4-1381/fleet/drill dead-parts
  EXPECT: dead-parts pass

- [ ] G4: Fleet runner tick still schedules.
  CHECK: systemctl --user is-active fleet-runner-tick.timer
  EXPECT: active

- [ ] G5: PR open and bound.
  CHECK: SHIP_REPO=valentinyeo/house-rules SHIP_BASE=main SHIP_CHECKOUT=/home/valentin/projects/worktrees/infra-runner-2-yper4-1381 /home/valentin/.agents/skills/ship/scripts/ship-check pr YPER4-1381
  EXPECT: pass

- [ ] G6: Merged to main.
  CHECK: SHIP_REPO=valentinyeo/house-rules SHIP_BASE=main SHIP_CHECKOUT=/home/valentin/projects/worktrees/infra-runner-2-yper4-1381 /home/valentin/.agents/skills/ship/scripts/ship-check merged YPER4-1381
  EXPECT: pass

- [ ] G7: Ticket Done.
  CHECK: SHIP_REPO=valentinyeo/house-rules SHIP_BASE=main SHIP_CHECKOUT=/home/valentin/projects/worktrees/infra-runner-2-yper4-1381 /home/valentin/.agents/skills/ship/scripts/ship-check done YPER4-1381
  EXPECT: pass
