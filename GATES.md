# YPER4-1386 gates

- [x] pick-gate: fleet tool-gate self-test passes
  CHECK: python3 fleet/tool-gate.py --self-test
  EXPECT: fleet/tool-gate self-test ok
  EVIDENCE: automatic-evidence=v1; definition-sha256=ff31028e52f954ee1d0cb72da33f22d5a088e9ffcee2d9cea6009936ed1bbcf0; exit=0; EXPECT=matched; output-sha256=83d3b581eb24cb5844fb2ff06450275fb991783b363a356ebd46fb8221a56431; output-bytes=29; shell=/bin/sh; cwd=/tmp/w2858; path=834cdd566399/12 entries

- [x] broken-picker-drill: the broken-picker drill passes on a sandbox copy
  CHECK: python3 fleet/drill broken-picker
  EXPECT: broken-picker pass
  EVIDENCE: automatic-evidence=v1; definition-sha256=274f7fc29da7a196992a03a233df18767d086f236581cc942c2899bd2385cc2f; exit=0; EXPECT=matched; output-sha256=7386b234be4153b234767fa0e2342062b214817b05efd770353eb5d168587bcf; output-bytes=26; shell=/bin/sh; cwd=/tmp/w2858; path=834cdd566399/12 entries

- [x] ci-workflow: the rules-lint workflow calls tool-gate
  CHECK: grep -o tool-gate .github/workflows/rules-lint.yml
  EXPECT: tool-gate
  EVIDENCE: automatic-evidence=v1; definition-sha256=68287de37a549b80850ebb13392d6b96317b92818b7c83b4bba6b487c9c6c8c9; exit=0; EXPECT=matched; output-sha256=a514d55f7265d83e92402730d2511a27a25b0d0bcd797d725cd6415deed7b33a; output-bytes=10; shell=/bin/sh; cwd=/tmp/w2858; path=834cdd566399/12 entries
