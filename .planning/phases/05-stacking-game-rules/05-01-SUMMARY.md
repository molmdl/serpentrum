---
phase: 05-stacking-game-rules
plan: 01
subsystem: pure-core
tags: [molfile, ring-extraction, graph-cycles, stacking, ring_frame, python3.6, stdlib]

# Dependency graph
requires:
  - phase: 03-molecules-viewer-setup
    provides: molfile.py SDF/mol2 readers + find_ring_atoms 2-core (03-02); shipped demo Set A SDFs with sorted 2-core ring_atoms (03-05)
  - phase: 02-pure-core
    provides: stacking.ring_frame ring-walk-order contract + 0.15 A planarity tolerance (02-04)
provides:
  - molfile.ring_cycle(record) — pure canonical 6-ring extractor: ONE planar ring in ring-walk order, deterministic, [] when no 3..6-cycle exists
  - tests/test_ring_cycle.py — pins the 5 probe-verified canonical tuples + sorted-order-fails trap regression + determinism + acyclic case
affects: [05-stacking-game-rules (05-08 setloader stack_ring carry, 05-05 placement seam, 05-10 materialization), phase 6 xtb handoff]

# Tech tracking
tech-stack:
  added: []
  patterns: ["bounded-DFS simple-cycle enumeration over a 2-core (nb > start pruning)", "canonical cycle normalization: rotate-to-smallest + min-over-orientations (pins Newell-normal sign)"]

key-files:
  created: [tests/test_ring_cycle.py]
  modified: [serpentrum/molfile.py]

key-decisions:
  - "ring_cycle lives in molfile.py next to find_ring_atoms (graph algorithm on the same record; auto-classified PURE) — per research doc"
  - "Canonical rule = shortest length, then lexicographic minimum over all 2n rotation/reversal normalizations — fixes BOTH start atom and walk orientation so the ring_frame Newell normal is deterministic"
  - "Manifest/setloader ring_atoms (sorted 2-core) must NEVER feed ring_frame directly — regression-tested, not assumed"

patterns-established:
  - "Truth-then-trap test ordering: pin probe-verified canonical tuples from real shipped bytes, and separately assert the deprecated input (sorted 2-core) still fails for the documented reason"

# Metrics
duration: 8 min
completed: 2026-09-15
---

# Phase 5 Plan 01: ring_cycle — canonical planar 6-ring extractor

**`molfile.ring_cycle(record)` turns the manifest's sorted 2-core into ONE planar aromatic 6-ring in ring-walk order for all 5 shipped demo molecules — the mandatory G1 shim before any `stacking.ring_frame` call (sorted order spuriously fails planarity even for exactly-flat benzene at 1.133 Å).**

## Performance

- **Duration:** 8 min
- **Started:** 2026-09-15T18:30:03Z
- **Completed:** 2026-09-15T18:37:54Z
- **Tasks:** 2 (TDD RED + GREEN; no REFACTOR needed)
- **Files modified:** 2 (1 created, 1 modified)

## Accomplishments

- `ring_cycle(record)` implemented in `serpentrum/molfile.py` (PURE, stdlib, ~30 lines of logic): bounded-DFS simple-cycle enumeration (len ≤ 6) restricted to the `find_ring_atoms` 2-core, with `nb > start` pruning; canonical selection = shortest length, then lexicographic minimum over all 2n rotation/reversal normalizations.
- All 5 probe-verified canonical tuples byte-match `05-RESEARCH-core-integration.md`: benzene `(0, 1, 3, 5, 4, 2)`; naphthalene `(0, 1, 3, 7, 6, 2)`; anthracene `(0, 1, 5, 3, 2, 4)`; phenanthrene `(0, 1, 3, 5, 4, 2)`; biphenyl `(0, 2, 6, 10, 8, 4)`.
- The trap is proven, not assumed: `stacking.ring_frame(coords, find_ring_atoms(record))` RAISES ValueError for flat benzene (spurious 1.133 Å) and for biphenyl's 12-atom 90°-twisted 2-core, while `ring_frame(coords, ring_cycle(record))` passes the 0.15 Å planarity check for every demo molecule.
- Determinism pinned (repeat calls return identical lists; list type asserted); acyclic ethanol-like record returns `[]`.
- Biphenyl yields ONE planar phenyl ring (6 elements) — matching stacking.py's one-planar-ring contract.

## Task Commits

Each TDD phase was committed atomically:

1. **Task 1: RED — failing tests pinning the canonical cycles** — `f082da4` (test)
   - 12 tests; 10 fail with `AttributeError` (ring_cycle missing) — RED for the right reason; 2 trap-probe tests pass because they only exercise existing `find_ring_atoms` + `ring_frame`. Gates 1+2 green at this commit; gate 3 red BY DESIGN (TDD RED intermediate state).
2. **Task 2: GREEN — implement ring_cycle per the verified algorithm** — `5b1a384` (feat)
   - All 12 new tests pass; full gate suite green: 3/3 gates, 463 tests (451 baseline + 12 new).

## Files Created/Modified

- `serpentrum/molfile.py` — added `ring_cycle(record)` + `_canonical_cycle(cycle)` helper immediately after `find_ring_atoms`; no other function touched (`find_ring_atoms`, `gate_set`, readers unchanged).
- `tests/test_ring_cycle.py` — new pinning suite (12 tests): 5 canonical tuples, benzene sorted-fails/walk-passes trap regression, all-5 planarity pass, biphenyl planar-subring, determinism, acyclic ethanol `[]`. Imports `serpentrum.molfile` + `serpentrum.stacking` directly; zero stubs; real shipped SDF bytes.

## Decisions Made

- **`ring_frame` called as-is on `stacking.py`** — never modified (plan constraint); the shim lives entirely in molfile.
- **Canonical orientation rule includes the reversal minimization** — reversal flips the ring_frame Newell normal, so the tie-break must pin orientation, not just start atom (per research spec; verified in probes).
- **Algorithm verified BEFORE writing the test file** — a read-only probe reimplemented the spec's `dfs()/cycle` logic against the real SDFs and reproduced all 5 locked tuples plus the 1.133 Å benzene trap, so RED could never accidentally pass.

## Deviations from Plan

None — plan executed exactly as written. (The RED commit intentionally has gate 3 red, per the plan's explicit RED requirement: "confirm they FAIL (ImportError/AttributeError counts as RED)". Gates 1+2 were green at RED; all gates green at GREEN.)

## Issues Encountered

None. The pre-GREEN probe de-risked the canonical rule entirely; implementation passed all 12 tests on the first run and the full gate suite stayed green.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- G1 (ring extraction) is CLOSED. Plan 05-08 (setloader `stack_ring` carry) can now compute `ring_cycle` at load time and carry it on demo records; 05-05 (placement seam) and 05-10 (edge-on materialization) can index `record['stack_ring']` 1:1 into SDF coords. All `stacking.ring_frame` callers have a safe input source.
- Blockers/concerns: none new. Biphenyl's unstackability remains a DATA-02 open question owned elsewhere (this plan only proves the extracted ring is planar — required for the refuse-path demonstrator to assemble its frame).

---
*Phase: 05-stacking-game-rules*
*Completed: 2026-09-15*
