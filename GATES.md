# YPER4-1386 gates

## pick-gate
CHECK: `python3 fleet/tool-gate.py --self-test`
EXPECT: `fleet/tool-gate self-test ok`

## broken-picker-drill
CHECK: `python3 fleet/drill broken-picker`
EXPECT: `broken-picker pass`

## ci-workflow
CHECK: `grep -q tool-gate fleet/../.github/workflows/pick.yml`
EXPECT: `tool-gate`
