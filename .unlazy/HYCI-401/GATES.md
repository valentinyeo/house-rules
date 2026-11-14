# HYCI-401 gates — Rat Stack slices unlinked: each pick burns an empty run

Scope: teach `fleet/pick` to hold a Rat Stack slice while a lower slice of the same parent is still open, so
no runner is offered a later slice before the slice it needs has shipped. Repo: valentinyeo/house-rules
(`fleet/pick`). Branch `runner-8/hyci-401`.

## Gates

G1 — A slice is held when a lower slice of its parent is open.
  Proof: `fleet/pick --self-test` case `slice_self_test` holds SOFT-2208 (slice 3) while SOFT-2197 (slice 1) is open,
  and the hold names the earlier slice.

G2 — The hold lifts when every lower slice is done.
  Proof: same self-test: with SOFT-2197 done, SOFT-2208 is offered.

G3 — An explicit "Slice N of M" marker in the title or description wins over the parent order.
  Proof: same self-test: a title "Slice 4 of 9" on a ticket whose parent list places it first is still held while
  slice 3 is open.

G4 — No new board read unless a family has two or more open slices in the snapshot.
  Proof: same self-test: a lone slice makes no `hypertask` call (parent read counter stays 0); a family with two
  open slices reads its parent once and caches it.

G5 — The whole existing picker test suite still passes.
  Proof: `fleet/pick --self-test` prints ok with the previous count plus the new slice checks.

G6 — Shipped.
  Proof: PR open against valentinyeo/house-rules, required checks green, merged, and the new line present on main.

## Evidence
(filled as each gate is proved)

G1 PROVED — `fleet/pick --self-test` `slice_self_test`: SOFT-2208 held with "slice: needs SOFT-2197 first".
G2 PROVED — same test: with 2197 and 2203 done, SOFT-2208 goes out; SOFT-2214 held on SOFT-2208.
G3 PROVED — same test: a ticket marked "Slice 4 of 9" whose plan place is first is held on SOFT-2203.
G4 PROVED — same test: a lone slice of its family makes 0 `hypertask` calls; a family with two open slices reads the
  parent once and keeps it in `~/.local/state/fleet-pick/slices.json` for 6 hours.
G5 PROVED — `fleet/pick --self-test` ok (135 ticket outcomes, 22 PR outcomes, 38 wait-gate checks, slice holds).
LIVE DATA (read only, real boards, snapshot 420 tickets): HTPR-9127 has 44 open slices; the plan read from the parent
  gives all 44 in order and 43 are now held on HTPR-9186 (slice 1), which stays offered. Before this change all 44
  were offered, one empty run each.
G6 — PR against valentinyeo/house-rules, checks, merge.
