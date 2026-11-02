# Gates: /ship

Scope: take this session's tickets end to end, live and verified.

- [x] YPER4-773.ticket: The ticket exists on the board
  CHECK: SHIP_REPO=valentinyeo/house-rules SHIP_BASE=main SHIP_CHECKOUT='/home/valentin/.local/share/house-rules' '/home/valentin/.agents/skills/ship/scripts/ship-check' ticket YPER4-773
  EXPECT: ticket ok
  CWD: /home/valentin/.local/share/house-rules
  EVIDENCE: automatic-evidence=v1; definition-sha256=e4c40277b4fe437440ee6a0f524c10851f5a7a5dd0d7a2a916523f5ec3123724; exit=0; EXPECT=matched; output-sha256=8d17ceac7d82fd2d508e2c28bd2fcf6931ed2b742384e96afd5c876e7c0ad828; output-bytes=10; shell=/bin/sh; cwd=/home/valentin/.local/share/house-rules; path=169277661364/28 entries

- [x] YPER4-773.deeper: A Deeper: agent activity names the field, raw source, method and outside proof, and its proof gate is a runnable CHECK
  CHECK: SHIP_REPO=valentinyeo/house-rules SHIP_BASE=main SHIP_CHECKOUT='/home/valentin/.local/share/house-rules' '/home/valentin/.agents/skills/ship/scripts/ship-check' deeper YPER4-773
  EXPECT: deeper ok
  CWD: /home/valentin/.local/share/house-rules
  EVIDENCE: automatic-evidence=v1; definition-sha256=676a842ee0644f0c64c8788e57091a01455b2b06853c64191db5273a836f791c; exit=0; EXPECT=matched; output-sha256=6674e696cff81f5bf7a8a5f3c9e236afb4791fd65c11a54a18bcfac64933f18e; output-bytes=10; shell=/bin/sh; cwd=/home/valentin/.local/share/house-rules; path=169277661364/28 entries

- [x] YPER4-773.pr: The PR is named HTPR-NNNN [TYPE] description
  CHECK: SHIP_REPO=valentinyeo/house-rules SHIP_BASE=main SHIP_CHECKOUT='/home/valentin/.local/share/house-rules' '/home/valentin/.agents/skills/ship/scripts/ship-check' pr YPER4-773
  EXPECT: title ok
  CWD: /home/valentin/.local/share/house-rules
  EVIDENCE: automatic-evidence=v1; definition-sha256=13016a4db2858639cc8ce84a71213c5a67e5a9bb2a97b7d131f143518a1c2bdb; exit=0; EXPECT=matched; output-sha256=b4b6b783fb548aa09f58ea1a2bd31d80b127ee97a1a37246be5d678e4e890610; output-bytes=9; shell=/bin/sh; cwd=/home/valentin/.local/share/house-rules; path=169277661364/28 entries

- [x] YPER4-773.merged: The PR is merged into production
  CHECK: SHIP_REPO=valentinyeo/house-rules SHIP_BASE=main SHIP_CHECKOUT='/home/valentin/.local/share/house-rules' '/home/valentin/.agents/skills/ship/scripts/ship-check' merged YPER4-773
  EXPECT: merged ok
  CWD: /home/valentin/.local/share/house-rules
  EVIDENCE: automatic-evidence=v1; definition-sha256=cd33f660b4c6b396b62d040f2844f24608fafcc1130f02612b0eaf674cbbfd51; exit=0; EXPECT=matched; output-sha256=ad6e7de1bb5cd4424e2469c422d793e2ac116c569cacd42ba31547a2ad37c035; output-bytes=10; shell=/bin/sh; cwd=/home/valentin/.local/share/house-rules; path=169277661364/28 entries

- [ ] YPER4-773.deployed: The Production deployment for the merge is success
  CHECK: SHIP_REPO=valentinyeo/house-rules SHIP_BASE=main SHIP_CHECKOUT='/home/valentin/.local/share/house-rules' '/home/valentin/.agents/skills/ship/scripts/ship-check' deployed YPER4-773
  EXPECT: deployed ok
  CWD: /home/valentin/.local/share/house-rules
  EVIDENCE: pending

- [x] YPER4-773.docs: Docs page change is merged and live on docs.hypertask.ai, or a No user-visible change reason is recorded
  CHECK: SHIP_REPO=valentinyeo/house-rules SHIP_BASE=main SHIP_CHECKOUT='/home/valentin/.local/share/house-rules' '/home/valentin/.agents/skills/ship/scripts/ship-check' docs YPER4-773
  EXPECT: docs ok
  CWD: /home/valentin/.local/share/house-rules
  EVIDENCE: automatic-evidence=v1; definition-sha256=7a3c493c5715713c5f98d2ef10718b35466ee8edc1abe9e516d68720491fd00d; exit=0; EXPECT=matched; output-sha256=65b1e475743166f9f0e8ebfc1adcf466b3356349017c17638b07f5b5e267f32b; output-bytes=33; shell=/bin/sh; cwd=/home/valentin/.local/share/house-rules; path=169277661364/28 entries

- [ ] YPER4-773.done: The ticket is in the done column its board names
  CHECK: SHIP_REPO=valentinyeo/house-rules SHIP_BASE=main SHIP_CHECKOUT='/home/valentin/.local/share/house-rules' '/home/valentin/.agents/skills/ship/scripts/ship-check' done YPER4-773
  EXPECT: done ok
  CWD: /home/valentin/.local/share/house-rules
  EVIDENCE: pending

- [x] YPER4-773.cleaned: This session removed its worktree and branch for the ticket (/clean-up)
  CHECK: SHIP_REPO=valentinyeo/house-rules SHIP_BASE=main SHIP_CHECKOUT='/home/valentin/.local/share/house-rules' '/home/valentin/.agents/skills/ship/scripts/ship-check' cleaned YPER4-773
  EXPECT: cleaned ok
  CWD: /home/valentin/.local/share/house-rules
  EVIDENCE: automatic-evidence=v1; definition-sha256=5c2b6629a5e8c16e094e61774aacceb56d6bd2fb95064d21a8326ed57da296a6; exit=0; EXPECT=matched; output-sha256=3a34b1ddcf02269c18c32fbffde53ef938a12ec799ddfd56be6d6ad4fef5b438; output-bytes=11; shell=/bin/sh; cwd=/home/valentin/.local/share/house-rules; path=169277661364/28 entries

ABANDON: YPER4-773.deployed waiting for HT Product Lead: merged canonical rule sync is verified, but ship-check accepts only systemd-user-unit live proofs for repositories without releases/workflows; support must be added through the existing deployment-proof work.
ABANDON: YPER4-773.done waiting for HT Product Lead: deployment proof gate cannot certify rule-sync distribution; ticket remains In Progress, no guard bypass.
