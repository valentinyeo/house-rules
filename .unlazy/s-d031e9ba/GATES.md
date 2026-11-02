# Gates: /ship

Scope: take this session's tickets end to end, live and verified.

- [x] YPER4-840.ticket: The ticket exists on the board
  CHECK: SHIP_REPO=valentinyeo/house-rules SHIP_BASE=main SHIP_CHECKOUT='/home/valentin/.local/share/house-rules' '/home/valentin/.agents/skills/ship/scripts/ship-check' ticket YPER4-840
  EXPECT: ticket ok
  CWD: /home/valentin/.local/share/house-rules
  EVIDENCE: automatic-evidence=v1; definition-sha256=1783ee4a5baedff6431c86e569ddf02710fb9b003d571cf0a4c7f5d5cfc0ae44; exit=0; EXPECT=matched; output-sha256=8d17ceac7d82fd2d508e2c28bd2fcf6931ed2b742384e96afd5c876e7c0ad828; output-bytes=10; shell=/bin/sh; cwd=/home/valentin/.local/share/house-rules; path=169277661364/28 entries

- [ ] YPER4-840.deeper: A Deeper: agent activity names the field, raw source, method and outside proof, and its proof gate is a runnable CHECK
  CHECK: SHIP_REPO=valentinyeo/house-rules SHIP_BASE=main SHIP_CHECKOUT='/home/valentin/.local/share/house-rules' '/home/valentin/.agents/skills/ship/scripts/ship-check' deeper YPER4-840
  EXPECT: deeper ok
  CWD: /home/valentin/.local/share/house-rules
  EVIDENCE: pending

- [ ] YPER4-840.pr: The PR is named HTPR-NNNN [TYPE] description
  CHECK: SHIP_REPO=valentinyeo/house-rules SHIP_BASE=main SHIP_CHECKOUT='/home/valentin/.local/share/house-rules' '/home/valentin/.agents/skills/ship/scripts/ship-check' pr YPER4-840
  EXPECT: title ok
  CWD: /home/valentin/.local/share/house-rules
  EVIDENCE: pending

- [ ] YPER4-840.merged: The PR is merged into production
  CHECK: SHIP_REPO=valentinyeo/house-rules SHIP_BASE=main SHIP_CHECKOUT='/home/valentin/.local/share/house-rules' '/home/valentin/.agents/skills/ship/scripts/ship-check' merged YPER4-840
  EXPECT: merged ok
  CWD: /home/valentin/.local/share/house-rules
  EVIDENCE: pending

- [ ] YPER4-840.deployed: The Production deployment for the merge is success
  CHECK: SHIP_REPO=valentinyeo/house-rules SHIP_BASE=main SHIP_CHECKOUT='/home/valentin/.local/share/house-rules' '/home/valentin/.agents/skills/ship/scripts/ship-check' deployed YPER4-840
  EXPECT: deployed ok
  CWD: /home/valentin/.local/share/house-rules
  EVIDENCE: pending

- [ ] YPER4-840.docs: Docs page change is merged and live on docs.hypertask.ai, or a No user-visible change reason is recorded
  CHECK: SHIP_REPO=valentinyeo/house-rules SHIP_BASE=main SHIP_CHECKOUT='/home/valentin/.local/share/house-rules' '/home/valentin/.agents/skills/ship/scripts/ship-check' docs YPER4-840
  EXPECT: docs ok
  CWD: /home/valentin/.local/share/house-rules
  EVIDENCE: pending

- [ ] YPER4-840.done: The ticket is in the done column its board names
  CHECK: SHIP_REPO=valentinyeo/house-rules SHIP_BASE=main SHIP_CHECKOUT='/home/valentin/.local/share/house-rules' '/home/valentin/.agents/skills/ship/scripts/ship-check' done YPER4-840
  EXPECT: done ok
  CWD: /home/valentin/.local/share/house-rules
  EVIDENCE: pending

- [ ] YPER4-840.cleaned: This session removed its worktree and branch for the ticket (/clean-up)
  CHECK: SHIP_REPO=valentinyeo/house-rules SHIP_BASE=main SHIP_CHECKOUT='/home/valentin/.local/share/house-rules' '/home/valentin/.agents/skills/ship/scripts/ship-check' cleaned YPER4-840
  EXPECT: cleaned ok
  CWD: /home/valentin/.local/share/house-rules
  EVIDENCE: pending

ABANDON: YPER4-840.deeper Fresh runner App request failed: gh: Not Found (HTTP 404) for valentinyeo/house-rules. Repository access requires approval; no implementation or release.

ABANDON: YPER4-840.pr Fresh runner App request failed: gh: Not Found (HTTP 404) for valentinyeo/house-rules. Repository access requires approval; no implementation or release.

ABANDON: YPER4-840.merged Fresh runner App request failed: gh: Not Found (HTTP 404) for valentinyeo/house-rules. Repository access requires approval; no implementation or release.

ABANDON: YPER4-840.deployed Fresh runner App request failed: gh: Not Found (HTTP 404) for valentinyeo/house-rules. Repository access requires approval; no implementation or release.

ABANDON: YPER4-840.docs Fresh runner App request failed: gh: Not Found (HTTP 404) for valentinyeo/house-rules. Repository access requires approval; no implementation or release.

ABANDON: YPER4-840.done Fresh runner App request failed: gh: Not Found (HTTP 404) for valentinyeo/house-rules. Repository access requires approval; no implementation or release.

ABANDON: YPER4-840.cleaned Fresh runner App request failed: gh: Not Found (HTTP 404) for valentinyeo/house-rules. Repository access requires approval; no implementation or release.
