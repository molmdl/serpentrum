---
phase: 09-random-line-wall-spawning
plan: 01
subsystem: game-policy
tags: [wall, spawner, deterministic, crc32, random, purity, geometry]

# Dependency graph
requires:
  - phase: 5.3-randomized-pickup-spawning
    provides: spawn.py canonical crc32 seed_from_setup + PickupSpawner conventions (untouched)
provides:
  - "serpentrum/wall.py: pure seeded WallSpawner policy (isolated wall RNG stream, 4 clearance legs, None-on-exhaustion)"
  - "wall_seed_from_setup: crc32(pickup_seed|'wall-v1') derived, isolated seed"
  - "min_atom_clearance: shared per-atom point-segment helper (both repo atom shapes)"
affects: [09-02, 09-03, 09-04, 09-06, 09-07, 09-09]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Separate derived RNG stream (crc32 salt) isolates a new feature's draws from the pickup stream by construction"
    - "Owner-tunable constants in ONE table; test expectations derived from the module's own constants"
    - "Local clamped-projection point-segment math kept self-contained (engine keeps its own copy)"

key-files:
  created:
    - serpentrum/wall.py
    - tests/test_wall.py
  modified: []

key-decisions:
  - "Wall policy lives in a NEW module (wall.py), spawn.py stays byte-identical (5.3 SC4 zero-edit isolation contract)"
  - "Wall seed = crc32('%d|%s' % (pickup_seed, 'wall-v1')) -- isolated stream, chains through the pickup seed (GAME-07)"
  - "3 seeded draws per attempt in pinned order (anchor x, anchor y, theta); consumed on every attempt regardless of outcome"
  - "No grid-scan fallback: a wall is a bonus obstacle, so WALL_MAX_DRAWS exhaustion returns None (caller keeps the previous wall)"
  - "L3 uses the EFFECTIVE head clearance (cmp follows the module table) so the wall_head_clearance_a override can block all candidates"

patterns-established:
  - "Derived-stream isolation: a second feature salts the canonical seed rather than sharing the RNG"
  - "Atom-shape contract: sym-first 4-tuples read x=[1]/y=[2]; bare 2-/3-tuples read x=[0]/y=[1]"

# Metrics
duration: 9min
completed: 2026-10-13
---

# Phase 9 Plan 01: Pure Wall Spawner Summary

**Pure `serpentrum/wall.py` seeded WallSpawner: isolated crc32 wall RNG stream, 3-draw pinned-order sampling, four clearance legs (box-margin, per-atom new-mol, head, live-mol), None-on-exhaustion; spawn.py byte-identical.**

## Performance

- **Duration:** 9 min
- **Started:** 2026-10-12T20:06:00Z (approx)
- **Completed:** 2026-10-12T20:15:11Z
- **Tasks:** 2 (TDD RED + GREEN; no REFACTOR needed)
- **Files modified:** 2 created

## Accomplishments
- `serpentrum/wall.py` (auto-PURE, stdlib math/random/zlib + `spawn.seed_from_setup` only) with the single owner-tunable constants table, `wall_seed_from_setup`, `WallSpawner` (read-only effective-value properties + `next_wall`), and the public `min_atom_clearance` helper.
- 16 pins in `tests/test_wall.py` (7 groups) — every expectation derived from the module's own constants, so an owner retune cannot silently break the suite.
- Isolation proven: walls never rotate the pickup stream (TestStreamIsolation drives a PickupSpawner interleaved with wall draws vs alone); `git diff --stat serpentrum/spawn.py` empty; `test_spawn.py` 41 green unmodified.

## Task Commits

Each task was committed atomically:

1. **Task 1: failing wall pins (RED)** - `979e082` (test)
2. **Task 2: WallSpawner policy + derived stream (GREEN)** - `bf4f9d4` (feat)

**Plan metadata:** (docs: complete plan — this commit)

_Note: no REFACTOR commit — no obvious cleanup surfaced (the implementation was already factored)._

## Files Created/Modified
- `serpentrum/wall.py` - the pure seeded random line-wall policy (constants table, seed derivation, `_point_segment_distance_sq`, `min_atom_clearance`, `WallSpawner.next_wall`)
- `tests/test_wall.py` - 16 tests across TestSeed / TestDeterminism / TestStreamIsolation / TestGeometry / TestExhaustion / TestCtorKwargs / TestMinAtomClearance

## Decisions Made
- L3 compares against `self._wall_head_clearance` (the EFFECTIVE value) rather than the bare `WALL_HEAD_CLEARANCE_A` literal, so the `wall_head_clearance_a` ctor override can block every candidate (TestExhaustion's observable). Default equals the table constant.
- Degenerate-box guard (`(x1-x0) < 2*margin` either axis) consumes ZERO draws; TestExhaustion asserts rng-state unchanged on the (0,0)-(5,5) box and changed on the (0,0)-(13,13) near-threshold box.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Non-observable "draws proceed" assertion for the near-threshold box**
- **Found during:** Task 1 (test design)
- **Issue:** The plan's `test_degenerate_box_returns_none` asks for the (0,0)-(13,13) box to show "normal behavior (draws proceed)", but with default length the geometry cannot fit any wall in the 1 A shrunk interval, so the return value is None for BOTH the degenerate and non-degenerate boxes — no observable difference from the return alone.
- **Fix:** Made the distinction observable at the RNG-state level: the (0,0)-(5,5) box returns None with the rng state UNCHANGED (guard short-circuits, zero draws), while the (0,0)-(13,13) box returns None with the rng state ADVANCED (draw loop ran). This directly pins the guard/draw-accounting contract the plan described.
- **Files modified:** tests/test_wall.py
- **Verification:** `test_degenerate_box_returns_none` green; rng-state equality/inequality assertions pass.
- **Committed in:** `979e082` (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Cosmetic test-observability refinement only; the implementation matches the plan exactly. No scope creep.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- The wall policy is ready for the engine collision leg (09-02), the GUI wiring that spawns walls with the next mol (09-06), the DBG gap consumer (09-07), and the closing feel-check (09-09).
- `min_atom_clearance` is the shared per-atom point-segment source (production feeds RAW atom shapes).
- Blocks/concerns: none. Wall constants are feel-check drafts; names/seams are firm for a single-edit retune.

---
*Phase: 09-random-line-wall-spawning*
*Completed: 2026-10-13*
