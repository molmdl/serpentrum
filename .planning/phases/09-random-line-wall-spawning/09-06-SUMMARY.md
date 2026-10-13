---
phase: 09-random-line-wall-spawning
plan: 06
subsystem: testing
tags: [integration, wall, crash, game-07, deterministic, seam-order, phase-9]

# Dependency graph
requires:
  - phase: 9-random-line-wall-spawning
    provides: wall.WallSpawner + wall_seed_from_setup + min_atom_clearance (09-01); game_engine set_wall/clear_wall + ('crashed','wall') leg (09-02)
  - phase: 5.3-randomized-pickup-spawning
    provides: spawn.PickupSpawner + the capture() controller seam (test_phase5_integration s1-s9)
provides:
  - "tests/test_phase5_integration.py s10: the seam-order integration pin between the pure Phase-9 halves (wall.py policy + engine wall) and the 09-07 GUI wiring"
  - "begin-no-wall invariant pin (first wall appears with mol 2) + one-live-wall replacement + the four derived wall clearances at every capture"
  - "walls + pickups + crash tick re-run byte-identically (GAME-07 end-to-end)"
affects: [09-07]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Integration pin mirrors the controller call order (_respawn order) so later GUI drift fails loudly"
    - "Derived-expectation discipline: every clearance/side computed from module constants + returned values; no hardcoded positions"
    - "Sanctioned fixed seed recorded in-test (4242/s9 precedent) after a handful of candidate search"
    - "Controlled non-vacuous suppression proof (fresh engine lands inside both radii; wall leg wins)"

key-files:
  created: []
  modified:
    - tests/test_phase5_integration.py

key-decisions:
  - "Scenario name is s10 (s9 is an EXISTING Phase-5.3 scenario name) -- new test method + one docstring sentence, s1-s9 untouched"
  - "Each capture runs the existing capture() resolution (placement.resolve + attach/reject) BEFORE the respawn seam, then the EXACT order note_resolution -> next_after -> build_pickup_seed + append -> next_wall -> set_wall"
  - "Fixed seed {'phase':'9','scenario':'s10','seed_tag':1} (first working draw; all captures PLACE and every next_wall is legal) -- recorded in-test per the 4242-class precedent"
  - "Raw sym-first seed['atoms'] 4-tuples fed UNPROJECTED to next_wall/min_atom_clearance (the integration proof of 09-01's x=[1]/y=[2] contract)"
  - "Crash-suppression asserted on the actual crash tick AND with a fresh controlled engine where the head lands inside both the pickup and wall radii -- non-vacuous"
  - "tol = 1e-9 for the derived clearance comparisons; s1-s9 + spawn.py + test_spawn.py byte-identical"

patterns-established:
  - "Controller-seam mirror: the test's capture/respawn order is the executable spec 09-07 implements"

# Metrics
duration: 25min
completed: 2026-10-13
---

# Phase 9 Plan 06: s10 Integration Scenario Summary

**Additive `test_s10_wall_spawn_pairing_and_crash`: a real set_a capture drive mirrors the `_respawn` seam order, proving synchronized next-mol + wall spawns with the owner's per-atom no-overlap clearance at every capture, begin-no-wall, one-live-wall replacement, `('crashed','wall')` completion with the snake intact, crash-suppresses-capture, and a byte-identical GAME-07 re-run.**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-10-13T04:14:00Z (approx)
- **Completed:** 2026-10-13T04:39:16Z
- **Tasks:** 2 (1 test scenario + 1 gates/drift sanity)
- **Files modified:** 1 (tests/test_phase5_integration.py); zero source edits

## Accomplishments
- `test_s10_wall_spawn_pairing_and_crash` appends the Phase-9 end-to-end scenario to the existing scenario class. On each of three captures it mirrors the controller seam order exactly: `capture()` resolution (05-13) -> `note_resolution` -> `next_after` -> `build_pickup_seed` + engine append/live-id bookkeeping -> `next_wall` -> `engine.set_wall` (the same order 09-07 seats at the success-branch tail of `_respawn_pickup`).
- All six per-resolution invariants asserted on DERIVED values: (i) a wall is live; (ii) the wall is replaced per spawn (exactly one live wall); (iii) every RAW fresh-seed atom is `>= WALL_MOL_CLEARANCE_A - tol` from the wall via `wall.min_atom_clearance` (the owner's per-atom no-overlap mandate, fed unprojected); (iv) both endpoints keep `WALL_BOX_MARGIN_A` from all four faces; (v) the head keeps `WALL_HEAD_CLEARANCE_A`; (vi) `set_wall` is state-only (the capture tick carries no wall-induced event).
- Begin-no-wall asserted at engine construction; the crash leg steers into the current wall midpoint and ends with the final event exactly `('crashed','wall')`, `result == 'crashed'`, `molecules_stacked == 3` (snake complete), no `('won',)`, `pending == []`, and a post-crash no-op step.
- Crash-suppresses-capture pinned both on the actual crash tick (no `('stacked',...)` after the crash) and with a controlled fresh engine whose next step lands inside both the pickup radius (0.7 A) and the wall radius (0.9 A) -- only the wall crash fires (non-vacuous).
- GAME-07 end-to-end: the entire drive (events, wall endpoint sequence, crash tick, result) re-runs byte-identically from fresh same-seed spawners/engine.
- s1-s9 unmodified; `serpentrum/` and `tests/test_spawn.py` byte-identical (`git diff --stat` empty for both).

## Task Commits

1. **Task 1+2: s10 scenario + gates/drift sanity** - `617a896` (test)

**Plan metadata:** (docs: complete plan -- this commit)

## Files Created/Modified
- `tests/test_phase5_integration.py` - added `from serpentrum import wall`; appended the s10 module-docstring sentence; added the `test_s10_wall_spawn_pairing_and_crash` method (+249/-1). No other lines changed.

## Decisions Made
- **Full capture resolution before the respawn seam:** the plan's seam list starts at `note_resolution`; the scenario runs the existing `capture()` seam (`placement.resolve` + `attach_segment`/`reject_pickup`) first, because that is what makes the snake real and keeps `molecules_stacked == captures`. The chosen seed guarantees all three captures PLACE (no `SKIP_NONPLANAR`/refusals).
- **Fixed seed `seed_tag: 1`:** found by scanning a handful of candidate tags; it yields three PLACE captures, a legal `next_wall` at every step, and a wall crash with no intermediate capture during the approach. Recorded in-test (the s9 :733 / 4242-class precedent); never derived.
- **Crash suppression proof:** because the live pickup is naturally held `>= WALL_MOL_CLEARANCE_A` from the wall, the actual crash tick rarely has the pickup also in range, so a controlled fresh-engine proof was added to make the ordering (wall leg precedes the pickup scan) non-vacuous.
- **`tol = 1e-9`** local constant for all derived clearance comparisons (per the plan's TOL contract); `min_atom_clearance` recomputes the exact geometry the policy validated.

## Deviations from Plan

None - no source-side issues surfaced; the test assembly follows the plan's sub-steps (a)-(e). The two choices above (running the full `capture()` resolution; adding the controlled suppression proof) are test-side enrichments within the plan's intent, not deviations from the wall/engine contracts.

## Issues Encountered
- An initial seed lookup used a different setup key (`tag` vs the prototype's `seed_tag`), which changed the canonical seed and produced `SKIP_NONPLANAR` outcomes; aligning the setup dict to the searched key resolved it. No product-code change was needed.

## User Setup Required
None - no external service configuration required.

## Next Phase Ready
- 09-07 (GUI wiring) now has an executable seam spec: `next_wall` runs AFTER the pickup materializes inside the same `_respawn_pickup` success branch, with the raw seed atoms and engine-live-minus-fresh live atoms, and `engine.set_wall` is the state-only swap. Any drift in call order or atom shape fails s10 loudly.
- Blocks/concerns: none. Wall constants remain feel-check drafts; s10 derives every bound from them, so the 09-09 retune cannot silently break the scenario.

---
*Phase: 09-random-line-wall-spawning*
*Completed: 2026-10-13*
