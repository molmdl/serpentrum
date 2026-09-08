---
phase: 02-pure-core-game-chemistry-logic
plan: 04
subsystem: chemistry-logic
tags: [stacking, pi-pi, newell-normal, rigid-body-transform, clash-gate, pure-python, py36, tdd]

# Dependency graph
requires:
  - phase: 01-plugin-skeleton-infra
    provides: purity gate (tools/check_purity.py, auto-classifies new serpentrum/ modules PURE), gate harness (tests/run_gates.py), committed xtb spike fixtures incl. dimer2.xyz
provides:
  - serpentrum/stacking.py: ring_frame (Newell normal + planarity + reference axis), place_pickup (deterministic azimuth=0 rigid-body pi-stack placement with lateral offset), check_clash (wall + atom gate), CLASH_THRESHOLD_A = 2.5
  - tests/test_stacking_math.py: 16 tests over the 9 specified behavior cases, anchored on the committed dimer2 fixture read IN PLACE
  - Proven phase success criterion 1: place_pickup at 3.4/0.0 reproduces the stored dimer geometry to ~1.4e-12 A (< 1e-6)
affects: [molecule_data (02-05 drives distance/lateral from stacking.json), game_engine (calls place_pickup + check_clash), phase-5 viewer connector (consumes R, t via cmd.transform_selection), later-wave integration test (file-driven distance)]

# Tech tracking
tech-stack:
  added: []   # stdlib math only — zero new dependencies
  patterns:
    - "Basis-composition rigid transform: R = B_tail . B_pick^T with right-handed orthonormal bases (r1, r2, n), basis vectors as columns; identity for coincident frames"
    - "Newell's method in the given ring-index order for an order-stable, degenerate-cross-product-free normal"
    - "azimuth=0 = pickup reference axis aligned to tail's projected reference axis (deterministic placement)"
    - "Evidence-based module constant (CLASH_THRESHOLD_A = 2.5) with rationale documented in-code, not a user setting"
    - "First-violation gate diagnostics: {'kind': 'wall'|'atom', 'pair': (i, j|None), 'distance': d}, wall test before atom test, inclusive box bounds"

key-files:
  created:
    - serpentrum/stacking.py
    - tests/test_stacking_math.py
  modified: []

key-decisions:
  - "CLASH_THRESHOLD_A = 2.5 A: sits between xtb's rcov bond-inference risk ceiling (~1.9-2.0 A) and the verified-safe 3.4 A dimer floor with >= 0.5 A margin both ways; module constant, not a user setting (v1)"
  - "azimuth=0 aligns the pickup's reference axis with the tail's projected reference axis — this is what makes the eclipsed dimer2 geometry exactly reproducible; normal sign is the caller's choice on tail_normal"
  - "Lateral offset direction: along ref (lateral_along_ref=True) or along cross(tail_normal, tail_ref); plane distance unchanged in both variants"
  - "Wall test before atom test; a coordinate exactly on a box boundary is legal (inclusive)"
  - "3.4 in the reproduction test is a fixture-derived TEST constant (dimer2's stored offset); the file-driven variant via molecule_data/stacking.json is a later-wave integration test"
  - "R returned row-major as placed = R.p + t; cmd.transform_selection matrix layout flagged OPEN in the docstring — Phase 5 must verify against editing.py before wiring"

patterns-established:
  - "PURE module shape: stdlib-math-only 3-vector tuple helpers (_sub/_add/_scale/_dot/_cross/_norm/_unit), zero numpy/pymol/Qt — purity checker auto-classification relied on and passed"
  - "Loud ValueError contracts with greppable message substrings ('ring needs >= 3 atoms', 'degenerate ring (normal length ...)', 'non-planar ring (max deviation ... A)')"

# Metrics
duration: 68min
completed: 2026-09-08
---

# Phase 2 Plan 4: Stacking Placement Math Summary

**Deterministic pi-stack placement math (`ring_frame`/`place_pickup`/`check_clash`) proven by exactly reproducing the committed dimer2 geometry (max error ~1.4e-12 A, R = identity, t = (0, 0, 3.4)) with a 2.5 A evidence-based clash gate.**

## Performance

- **Duration:** 68 min (01:01–02:09 UTC)
- **Started:** 2026-09-08T01:00:59Z
- **Completed:** 2026-09-08T02:09:13Z
- **Tasks:** 3/3
- **Files modified:** 2 created

## Accomplishments

- `ring_frame`: Newell normal in the given index order (order-stable), 0.15 A planarity tolerance, centroid -> first-ring-atom reference axis orthogonalized against the normal; loud ValueErrors for < 3 atoms, degenerate (collinear) rings, non-planar rings, degenerate reference axes. On dimer2 fragment 1's six carbons it returns the verified centroid (0.012766437, -0.454242937, ~0.0) and normal (0, 0, 1) within 1e-9.
- `place_pickup`: rigid transform R = B_tail . B_pick^T (+ t) with azimuth=0 reference-axis alignment and lateral-offset support (along ref, or along cross(normal, ref)); coincident frames give R = identity, which reduces the committed eclipsed-dimer placement to a pure +z translation. **THE reproduction test: placed fragment 1 == committed fragment 2 to max error 1.370e-12 A (criterion < 1e-6; the research probe reported 0.0 — both far under tolerance; the residue is fp noise from centroid-mean arithmetic).**
- `check_clash`: wall-first (inclusive bounds, worst-axis violation amount) then first-(i, j) atom scan against CLASH_THRESHOLD_A = 2.5 A. Legal 3.4 A stack passes; 1.5 A placement fires kind 'atom' at pair (0, 0); out-of-box fires kind 'wall' with the violation amount; boundary-inclusive.
- Rotated-pickup case proves azimuth determinism: a pickup rigidly rotated +90 deg about z lands exactly back on the canonical stack position (== fragment 2) with R ~ Rz(-90 deg) — rotation genuinely applied, planes parallel, azimuth aligned.

## Task Commits

Each task was committed atomically (TDD RED -> staged GREEN -> full GREEN):

1. **Task 1 (RED): failing frame + reproduction + clash tests** - `caa2223` (test)
2. **Task 2 (GREEN partial): ring_frame** - `9a990dc` (feat)
3. **Task 3 (GREEN): place_pickup + check_clash** - `7b5fe59` (feat)

**Plan metadata:** committed separately as `docs(02-04)` staging only this SUMMARY (STATE.md intentionally untouched — orchestrator owns it during parallel waves).

## Files Created/Modified

- `serpentrum/stacking.py` (305 lines) — PURE stdlib-math module: 3-vector tuple helpers, CLASH_THRESHOLD_A = 2.5 (rcov rationale in-code), PLANARITY_TOL_A = 0.15, ring_frame, _orthonormal_basis, place_pickup, check_clash
- `tests/test_stacking_math.py` (334 lines) — 16 tests over the 9 behavior cases; dimer2.xyz read IN PLACE via a self-contained inline parser (no xyzio import, per wave-1 rule; fixture untouched, zero copies)

## Decisions Made

- **Case-5 test assertion clarified (spec wording):** the behavior spec's "the placed atoms differ from the unrotated placement" is mathematically false under the spec's own azimuth=0 rule — a rigidly rotated pickup (same molecule, same conformer) aligns back onto the canonical position, so placed == fragment 2. The test asserts the consistent readings: R far from identity (|R - I|max = 1.0 — rotation actually happened), placed != rotated input (min moved distance 3.65 A), per-atom rigidity to the stack-axis target, placed normal parallel to tail normal (dot = 1.0 @1e-9), and the deterministic consequence placed == f2 (< 1e-6). No assertion weakened; fixed at Task 1 design time, so no separate test-fixup commit was needed.
- **Threshold kept a module constant** (2.5 A) with the rcov bond-inference rationale documented in-code, per the plan (not a user setting in v1).
- **Fixture-derived test constant:** STACK_D = 3.4 documented in the test module docstring as dimer2's stored offset; the file-driven variant (stacking.json via molecule_data, plan 02-05) is explicitly deferred to a later-wave integration test.
- **Fixture read in place** from `.planning/research/xtb-spike-fixtures/dimer2.xyz` — no copies made (verified: zero git changes under the fixtures dir).

## Deviations from Plan

None — plan executed exactly as written (the case-5 wording clarification above was applied when writing the tests, before the first commit, and is a spec-consistency fix rather than unplanned work).

Note on staged TDD gating: at Task 2 the plan's staged-commit design necessarily leaves the 10 placement/clash tests red, so `run_gates` gate 3 fails at that intermediate commit while gates 1–2 (syntax, purity) pass — exactly what Task 2's verify describes ("frame tests OK, placement/clash cases still failing; gates green (module purity + syntax)"). Final state: all gates green, exit 0.

## Issues Encountered

None. All 16 stacking tests passed on the first GREEN run with no assertion adjustments; the pre-verified constants (centroid, normal, hexagon planarity deviation 0.248 A, reproduction math) made RED-by-construction exact.

## Authentication Gates

None — no external services involved.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- `place_pickup`/`check_clash` contracts are frozen and fixture-proven; plan 02-05 (molecule_data) can wire `stacking.json`'s `distance_a`/`lateral_offset_a` straight into `place_pickup` (the loader's DRAFT 3.4 value exists to reproduce this fixture; the human approval track pins the final number — DATA-02).
- `game_engine` (wave B) calls `place_pickup` then `check_clash` for the refuse-and-skip fallback; the diagnostic dict shape is stable.
- **Open item carried for Phase 5:** the `cmd.transform_selection` matrix layout for consuming R/t is flagged OPEN in `place_pickup`'s docstring (ARCHITECTURE.md section 9); Phase 5 must verify against `editing.py:1946` before wiring.
- Later-wave integration test should chain xyzio -> stacking with the distance read from stacking.json (deliberately not done here — xyzio/molecule_data are parallel wave-1 plans not in this branch's history).

---
*Phase: 02-pure-core-game-chemistry-logic*
*Completed: 2026-09-08*
