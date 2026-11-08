# YPER4-1382

house-rules-retired-pools:
  CHECK: python3 /home/valentin/projects/worktrees/runner-2-yper4-1382/bin/rules-drift --house-rules
  EXPECT: clean

rules-drift-self-check:
  CHECK: python3 /home/valentin/projects/worktrees/runner-2-yper4-1382/bin/rules-drift --self-check
  EXPECT: PASS

rules-drift-unit:
  CHECK: cd /home/valentin/projects/worktrees/runner-2-yper4-1382 && python3 -m unittest tests.test_rules_drift -v
  EXPECT: OK

fleet-drill-rule-drift:
  CHECK: /home/valentin/projects/worktrees/runner-2-yper4-1382/fleet/drill rule-drift
  EXPECT: pass
