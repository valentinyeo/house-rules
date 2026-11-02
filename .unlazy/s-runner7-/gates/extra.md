# Gates: YPER4-773 policy proof

- [x] YPER4-773.deeper-policy-sync: All requested policy clauses survive real publication, with unrelated rules unchanged
  CHECK: python3 /home/valentin/.local/state/vcc-evidence/YPER4-773/verify-policy.py /home/valentin/.local/share/house-rules --live
  EXPECT: POLICY_LIVE_OK
  CWD: /home/valentin/.local/share/house-rules
  EVIDENCE: automatic-evidence=v1; definition-sha256=f7073b71723e80fe3b0a11141554d635e229793d1d6580c45c5fc0dcc0d65617; exit=0; EXPECT=matched; output-sha256=ffb4e6b882656da718a3f7fac5ba8be2111f51ecbedb9f91ae33575fdcb14349; output-bytes=442; shell=/bin/sh; cwd=/home/valentin/.local/share/house-rules; path=169277661364/28 entries

- [x] YPER4-773.sync-regressions: Existing cross-project sync behavior remains correct
  CHECK: python3 bin/test-inne-sync.py
  EXPECT: INNE_TESTS_OK
  CWD: /home/valentin/.local/share/house-rules
  EVIDENCE: automatic-evidence=v1; definition-sha256=b5aa9cbec8585c9a34ba2dcbb017432ef2e902c7d9e16892d55056302a18a6b5; exit=0; EXPECT=matched; output-sha256=28c686cf684f086f8cfd6846e3c98f01cacbae4c8edc8c38717acd298becca86; output-bytes=820; shell=/bin/sh; cwd=/home/valentin/.local/share/house-rules; path=169277661364/28 entries
