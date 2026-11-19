# YPER4-1386 gates

## pick-gate
CHECK: `python3 fleet/tool-gate.py --self-test`
EXPECT: `fleet/tool-gate self-test ok`

## ci-workflow
CHECK: `grep -q tool-gate .github/workflows/rules-lint.yml`
EXPECT: `tool-gate`
