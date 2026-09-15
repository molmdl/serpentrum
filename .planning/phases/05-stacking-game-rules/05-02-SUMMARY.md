---
phase: 05-stacking-game-rules
plan: 02
subsystem: pure-math
tags: [orientation, ttt-matrix, transform_selection, edge-on, ring-frame, pure-python, py36, tdd]

# Dependency graph
requires:
  - phase: 01-plugin-skeleton-purity-harness
    provides: purity gate (tools/check_purity.py auto-classifies new serpentrum/ modules PURE), gate harness (tests/run_gates.py)
  - phase: 02-pure-core-game-chemistry-logic
    provides: serpentrum/stacking.py ring_frame (deterministic centroid + Newell normal + in-plane ref basis)
  - phase: 03-molecules-in-the-viewer-setup-tab
    provides: serpentrum/molfile.py read_sdf (elements/coords/bonds records) + the 5 shipped demo Set-A SDFs; LOCKED edge-on presentation decision (03-08, reiterated 04-07)
provides:
  - serpentrum/orientation.py: matrix_rt (the ONE verified 16-float TTT composer, y = R.(x+pre) + t), mat_vec3, edge_on_frame, edge_on_atoms, edge_on_m16 — pure stdlib-only (G5 pure half)
  - tests/test_orientation.py: 11 pins — probe-A1 layout fixture float-for-float, pivot idiom (A2), edge-on invariants + research z-span anchors for all 5 demo molecules
  - Unit-pinned proof that post-edge-on z-spans match the research 'best' column (benzene 4.2972 ... phenanthrene 7.1436), keeping BOX_DISPLAY_Z = 5.0 valid
affects: [05-10 edge-on materialization (head + pickups consume edge_on_m16 at load), 05-07 bridge primitives (apply_matrix forwards matrix_rt output to cmd.transform_selection), 05-05 placement (place_pickup inputs on canonicalized atoms), all phase-5 stacking plans (edge-on lands BEFORE any stacking — locked decision 3)]

# Tech tracking
tech-stack:
  added: []   # stdlib only (imports: serpentrum.stacking) — zero new dependencies
  patterns:
    - "Single verified matrix composer: matrix_rt is the ONLY 16-float TTT builder (pitfall P5-8); pre = -pivot + post = +pivot IS the pivot idiom"
    - "Edge-on canonicalization as a pure pre-rotation applied once at load: basis rows (n, u, v) with v = cross(n, u) guarantee determinant +1 (pure rotation, never a reflection); u = LONGER-span in-plane axis chosen by data, not hardcoded"
    - "Spans computed over ALL atoms (H atoms extend beyond ring carbons — benzene span is 4.297z/4.962y while its ring diameter is 2.79)"

key-files:
  created:
    - serpentrum/orientation.py
    - tests/test_orientation.py
  modified: []

key-decisions:
  - "Azimuth rule (planner-pinned): LONGER in-plane ring axis -> +y (the visible screen axis carrying the dataset's lateral offset), SHORTER -> +z; worst post-edge-on z-extent stays phenanthrene 7.1436 A < 2*BOX_DISPLAY_Z = 10.0 A, so BOX_DISPLAY_Z = 5.0 holds (locked decision 4; only the constant would ever change, not this rule)"
  - "Basis rows (normal, u, v) with v = cross(normal, u): mat_vec3 maps n -> +x, u -> +y, v -> +z and det(R) = +1 unconditionally (right-handed basis), so no per-molecule sign special-casing"
  - "Per-ring-atom on-plane pin relaxed from plan-literal 1e-9 to 1e-3: real PubChem 3D SDFs deviate up to 8.1e-5 A from the ring mean plane (phenanthrene worst of five); 1e-3 keeps >10x margin over observed noise and 3 orders below the 0.15 A planarity admission bound"
  - "Ring tuples pinned in the test from ring_extraction_spec's verified canonical cycles (benzene (0,1,3,5,4,2) ... biphenyl (0,2,6,10,8,4)) — NOT imported from molfile.ring_cycle (parallel sibling plan 05-01 owns molfile.py in this wave); edge_on_frame takes ring_indices as a parameter so the implementation needs no ring_cycle import either"

patterns-established:
  - "G5 pure-module shape: imports ONLY serpentrum.stacking (intra-package relative import), plain 3-tuple floats, python3.6 %-formatting — auto-classified PURE with zero check_purity registration"
  - "Test file repeats the sys.path self-insert + real-data-in-place pattern (no fixture copies, no sys.modules stubs); ring_cycle substitution documented in the test docstring for the wave merge"

# Metrics
duration: 11min
completed: 2026-09-15
---

# Phase 5 Plan 02: Orientation Matrix & Edge-On Canonicalization Summary

**Pure stdlib orientation module: the verified 16-float TTT composer (`matrix_rt`, layout y = R.(x+pre) + t) plus the edge-on canonicalization (normal -> +x, longer in-plane axis -> +y, shorter -> +z, ring centroid -> origin), unit-pinned against the probe-A1 fixture and the research z-span anchors for all five demo molecules (z-spans 4.2972 / 5.5474 / 6.7697 / 7.1436 / 4.3173 A — all inside the 2e-3 pin on the probe-F 'best' column, keeping BOX_DISPLAY_Z = 5.0 valid).**

## Performance

- **Duration:** 11 min
- **Started:** 2026-09-15T18:30:28Z
- **Completed:** 2026-09-15T18:42:25Z
- **Tasks:** 2/2 (TDD: RED test cycle + GREEN implementation)
- **Files modified:** 2 (both new)

## Accomplishments
- `serpentrum/orientation.py` (G5 pure half): `matrix_rt` — the ONE 16-float TTT composer PyMOL 2.5.0 `transform_selection` accepts (layout verified by headless probes A1/A2 at <= 1.2e-07 A, source editing.py:1962-1988); `mat_vec3`; `edge_on_frame` (pure basis math on `stacking.ring_frame`); `edge_on_atoms` / `edge_on_m16` (pure application + the one-shot viewer matrix).
- `tests/test_orientation.py` (11 tests, zero stubs, real SDFs read in place): probe-A1 fixture float-for-float; pre-translation bottom-row slots; A2 pivot idiom rotating (3,0,0) about (1,0,0) to (1,2,0); normal -> +x within 1e-9; pre == neg(centroid) within 1e-12; ring centroid -> origin within 1e-9; ring atoms on the yz plane; z-span anchors + z-span <= y-span; symbol preservation + benzene ±2.149 z-band; m16 == matrix_rt composition.
- Measured post-edge-on spans (all atoms, Angstrom): benzene y 4.9618 / z 4.2972; naphthalene 7.0789 / 5.5474; anthracene 9.2068 / 6.7697; phenanthrene 8.1222 / 7.1436; biphenyl 9.1984 / 4.3173 — z columns match the research table's 'best'/'long-axis' columns exactly; observation: biphenyl's x-span is 4.3172 (its second ring sits at 90 degrees, so that ring's extent lands along the chain axis +x) — expected, uncovered by any pin, and harmless (chain axis has no display bound).

## Task Commits

Each task was committed atomically (TDD RED -> GREEN):

1. **Task 1 (RED): failing orientation matrix + edge-on pinning tests** - `4778b58` (test)
2. **Task 2 (GREEN): pure orientation module implementation (+ 1e-3 planarity-pin fix)** - `f2e0d15` (feat)

**Plan metadata:** `docs(05-02): complete orientation plan` (this commit)

_No REFACTOR commit — the module is small, single-purpose, and clean as written._

## Files Created/Modified
- `serpentrum/orientation.py` — PURE module (stdlib only, imports only `serpentrum.stacking`): matrix_rt / mat_vec3 / edge_on_frame / edge_on_atoms / edge_on_m16; docstring records the verified matrix verdict + planner-pinned azimuth rule + BOX_DISPLAY_Z rationale
- `tests/test_orientation.py` — 11 pinning tests over the probe-A1 fixture, pivot idiom, and all 5 demo molecules via molfile.read_sdf

## Decisions Made
- Azimuth rule recorded in the module docstring as locked (longer in-plane axis -> +y / visible lateral; shorter -> +z; worst z-extent phenanthrene 7.1436 A keeps BOX_DISPLAY_Z = 5.0 valid).
- Basis construction rows (n, u, v), v = cross(n, u): unconditional +1 determinant (pure rotation) with no per-molecule sign branches; spans over ALL atoms, not ring atoms only.
- Ring tuples pinned in the test file directly (isolation: sibling plan 05-01 owns molfile.py in this parallel wave; `edge_on_frame` takes `ring_indices` as a parameter so the implementation never imports `ring_cycle`). Documented in the test docstring for the wave merge — no behavior difference, same verified tuples (05-01's `ring_cycle` pins the identical list).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Per-ring-atom on-plane tolerance 1e-9 unreachable for real SDFs — relaxed to 1e-3**
- **Found during:** Task 2 (GREEN run: 5 subtest failures, one per molecule)
- **Issue:** The plan pins "every ring atom's normal coordinate ~= 0 within 1e-9" after edge-on. The shipped PubChem 3D SDFs are not exactly planar: ring atoms deviate up to ~8.1e-5 A from the ring mean plane (benzene 3.3e-5, naphthalene 5.0e-5, anthracene 5.0e-5, phenanthrene 8.1e-5, biphenyl 3.0e-5), so a 1e-9 pin can never hold on real data.
- **Fix:** Pin relaxed to `abs(x) <= 1e-3` with an in-test justification comment (>10x margin over observed noise; 3 orders below ring_frame's 0.15 A planarity admission bound; ~2000x below in-plane ring extents). The stronger plan invariants are unaffected and pass at full strictness: normal -> +x within 1e-9, pre == neg(centroid) within 1e-12, ring-CENTROID at origin within 1e-9 (means cancel the out-of-plane noise).
- **Files modified:** tests/test_orientation.py
- **Verification:** 11/11 orientation tests pass; full run_gates green (462 tests, 451 baseline + 11 new)
- **Committed in:** f2e0d15 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** The plan's load-bearing pins are all intact (A1 fixture exact, pivot idiom exact, normal/centroid invariants at 1e-9/1e-12, z-span anchors within 2e-3); only the physically unreachable per-atom planarity tolerance was data-grounded. No scope creep.

## Issues Encountered
- Plan text labels two different matrices "RotZ(90)": Task 1.1's literal matrix ((0,1,0),(-1,0,0),(0,0,1)) matches its pinned 16-float list exactly (a direction-free layout pin — the 1/(-1) entries just occupy slots [1]/[4]), while Task 1.2's "+90 deg ... gives (1, 2, 0)" requires the true +90 CCW matrix ((0,-1,0),(1,0,0),(0,0,1)) — the exact matrix probe A1/A2 used in `tmp/p5_pymol_probe.py` (verified end-to-end at <= 2.4e-07 A). Resolved by pinning both literals precisely as written (test names/comments distinguish them, including the probe's exact matrix for the pivot idiom). All plan-pinned numbers hold; no plan edit needed.
- RED-phase gates: `run_gates` gates 1-2 (syntax, purity) pass throughout; gate 3 failed only at the intentional RED commit (ImportError on the missing module — the established 02-04 TDD precedent); all three gates green at the final state.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- `edge_on_m16(elements, coords, ring_indices)` is ready to be applied ONCE at load for head + pickups (05-10 materialization + 05-07 bridge `apply_matrix`); `place_pickup` on canonicalized atoms then degenerates to near-translation (STACK-01 determinism property), so the tail frame needs no viewer queries (research Pattern 1).
- Watch at wave merge: 05-01's `molfile.ring_cycle` pins the same canonical tuples used here — tests stay self-contained; a later plan may switch test imports to `ring_cycle` for cross-validation, but this is optional, not required.
- No blockers. BOX_DISPLAY_Z stays 5.0 per this plan's verified z-span numbers.

---
*Phase: 05-stacking-game-rules*
*Completed: 2026-09-15*
