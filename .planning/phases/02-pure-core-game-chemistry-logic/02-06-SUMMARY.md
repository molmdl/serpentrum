---
phase: 02-pure-core-game-chemistry-logic
plan: 06
subsystem: game-engine (movement core)
tags: [snake-engine, continuous-2d, constant-speed, direction-queue, determinism, pure-python, py36, tdd, game08]

# Dependency graph
requires:
  - phase: 01-plugin-skeleton-purity-harness
    provides: run_gates harness + AST purity gate, test conventions (sys.path
      self-insert preamble, discovery without `-t .`, no __init__.py in tests/),
      py3.6 syntax discipline, plugin-path safety
provides:
  - serpentrum/game_engine.py movement core: SPEED_A_PER_S=3.0 (GAME-08) + DIRS
    map, GameEngine with continuous-2D head, unit-vector heading, step(dt)
    emitting ('moved', (x, y)) at exactly 0.3 A per 0.1 s tick, request_direction
    (ValueError on unknown names; 180/same rejected via dot thresholds; max-1
    buffer), pause/resume/reset (GAME-07), segments state seam with defensive
    copying
  - tests/test_engine_core.py: 17 deterministic tests (motion grid, queue rules,
    pending-inert, pause, reset, two-engine determinism, seam copying)
  - Forward-compatibility contract: 02-06's suite never calls step() while a
    request is pending, so 02-13's turn application at step start cannot break it
affects: [02-10-collisions-rules, 02-13-turn-sweeps, 02-14-pure-integration,
  phase-4-gameplay, phase-5-ui, phase-8]

# Tech tracking
tech-stack:
  added: []   # zero imports — pure arithmetic only; no new libraries
  patterns:
    - "Engine-owns-truth (Pattern 3): plain-data state; rendering maps from engine state"
    - "Pending-inert queue: request_direction only buffers; step() never touches pending (02-13 applies turns at step START)"
    - "Dot-threshold direction rules vs CURRENT heading: < -0.5 reject (180), > 0.5 reject (same), else max-1 buffer"
    - "Segments as a test seam with defensive copying (engine never shares/mutates caller data; unknown keys carried through)"
    - "__init__ delegates to reset() — single state builder, deterministic restart (GAME-07)"

key-files:
  created:
    - serpentrum/game_engine.py
    - tests/test_engine_core.py
  modified: []

key-decisions:
  - "Unknown heading names raise ValueError in __init__/reset (consistent with request_direction's invalid-name contract; unpinned by plan — chose loud validation)"
  - "pending is a plain list (max-1 buffer; collections.deque unnecessary at size 1)"
  - "_copy_segments rebuilds each record as dict(seg) + fresh 'atoms' list, carrying unknown keys — forward-compatible with 02-10's record extensions"
  - "Module has ZERO imports: the dot product is manual arithmetic; no math/trig needed in the movement core"
  - "Buffer-full rule isolated with a 'down' request (perpendicular); the literal 'left' case-6 wording pinned separately as a 180-while-buffered rejection"

patterns-established:
  - "TDD RED (ImportError) -> GREEN atomic commits scoped test(02-06)/feat(02-06)"
  - "Suite-level forward-compatibility convention: never step() with non-empty pending (02-06 -> 02-13)"
  - "Coordinate convention: continuous 2D floats in the box xy-plane; z display-only inside segment atom records"

# Metrics
duration: 7 min
completed: 2026-09-08
---

# Phase 2 Plan 06: Engine Movement Core Summary

**Continuous-2D snake movement core: constant-speed step (3.0 A/s -> exact 0.3 A/tick) emitting ('moved', pos), max-1 direction queue with 180-degree rejection (pending deliberately inert), pause/resume/deterministic reset, and a defensively-copied segments test seam — zero imports, fully deterministic.**

## Performance

- **Duration:** 7 min
- **Started:** 2026-09-08T00:31:30Z
- **Completed:** 2026-09-08T00:38:16Z
- **Tasks:** 2/2
- **Files modified:** 2 created (458 lines total)

## Accomplishments
- `serpentrum/game_engine.py` (198 lines): movement core per the pinned design — SPEED_A_PER_S + DIRS constants, GameEngine with head/heading/segments/pending/paused state, step/request_direction/pause/resume/reset, segments test seam
- `tests/test_engine_core.py` (260 lines): 17 tests covering all 11 pinned behavior cases plus segments-seam copying, heading-follows-vector motion, and invalid-heading loudness
- Forward-compatibility rule honored: no test ever calls step() while pending is non-empty, so 02-13's step-start turn application cannot break this suite

## Task Commits

Each task was committed atomically (TDD plan: RED + GREEN):

1. **Task 1 (RED): failing movement/queue/pause tests** - `46365ad` (test) — 17 cases, ImportError on `serpentrum.game_engine` confirmed as the RED state
2. **Task 2 (GREEN): implement the movement core** - `b6a4c73` (feat) — all 17 engine-core tests + 112-test full suite + gates green

## Files Created/Modified
- `serpentrum/game_engine.py` - Movement core: DIRS map, SPEED_A_PER_S=3.0, GameEngine (step/request_direction/pause/resume/reset/_copy_segments), segments state seam; stdlib-only PURE, zero imports
- `tests/test_engine_core.py` - Deterministic behavior suite: motion grid, queue rules, pending-inert, pause/reset, two-engine determinism, seam copying

## Verification Results

- `python3.6 -m unittest discover -s tests -p "test_engine_core.py" -v` -> 17 tests OK
- `python3.6 -m unittest discover -s tests -p "test_*.py" -v` -> 112 tests OK
- `python3.6 tests/run_gates.py` -> gates 1 (syntax+plugin-path), 2 (purity AST), 3 (unittest) all PASS, exit 0
- `python3.6 tools/check_purity.py` -> clean (game_engine.py auto-classified PURE)
- `grep -nE "import (random|time)" serpentrum/game_engine.py` -> no matches (determinism)
- `grep -nE "BOUNDARY_MARGIN_A|BODY_COLLISION_RADIUS_A|PICKUP_RADIUS_A|TURN_TICKS|TURN_DEGREES|SEGMENT_SKIP_RECENT|attach_segment|reject_pickup|finished|result" serpentrum/game_engine.py` -> no matches (scope guard: none of 02-10/02-13's surface leaked)
- Artifact min_lines: game_engine.py 198 (>= 90), test_engine_core.py 260 (>= 110)

## Decisions Made
- **ValueError on unknown heading names in __init__/reset** — the plan pinned ValueError for request_direction's invalid names but not for the constructor's heading; chose the same loud contract for consistency (movement-core input validation, not 02-10 surface)
- **pending is a plain list** — max-1 buffer needs no deque; order trivially preserved
- **_copy_segments carries unknown record keys through** — dict(seg) + fresh 'atoms' list means 02-10 can extend segment records without touching the copy logic
- **Zero module imports** — dot-product rules are manual multiply-add; no math/trig needed, keeping the module trivially pure

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added ValueError validation for unknown heading names in the constructor/reset**

- **Found during:** Task 2 (GREEN implementation)
- **Issue:** The pinned design says heading is "resolved through DIRS" but did not specify behavior for an invalid heading name (a bare dict lookup would raise an opaque KeyError)
- **Fix:** reset() validates `heading in DIRS` and raises ValueError with the valid names listed, mirroring request_direction's contract; pinned by `test_invalid_heading_name_raises`
- **Files modified:** serpentrum/game_engine.py, tests/test_engine_core.py
- **Verification:** engine-core suite green; gates green
- **Committed in:** b6a4c73 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 missing critical — minor input-validation consistency)
**Impact on plan:** No scope creep; the addition is movement-core validation inside this plan's file scope.

## Issues Encountered

- **Plan-text inconsistency in behavior case 6 (resolved without behavior change):** the plan describes request_direction('left') while 'up' is pending as "buffer full — 'left' is perpendicular", but 'left' vs the CURRENT heading 'right' is a 180-degree reversal (dot = -1.0). The expected output is identical either way (False; pending stays ['up']). The suite covers both readings: `test_buffer_full_rejects_perpendicular` uses 'down' (genuinely perpendicular, isolating the buffer-full rule per the stated intent) and `test_180_rejected_even_while_buffer_full` pins the literal 'left' wording (180 rule fires). No engine code change was needed.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- 02-10 (collisions/rules) can extend the constructor with keyword args (box/pickups/cap/budget are intentionally absent) and grow the chain via the segments seam; segment records already carry molecule_id/centroid/atoms/atoms_n
- 02-13 (turn sweeps) owns applying pending at step start; the pending-inert step branch and the suite's never-step-while-pending convention guarantee those tests stay valid across that change
- request_direction's reference is the CURRENT heading; 02-13 switches it to the sweep target while sweeping (documented in the method docstring)
- SPEED_A_PER_S is the single tunable pending Phase-4 playtesting; setup_logic's 'speed' default mirrors it

---
*Phase: 02-pure-core-game-chemistry-logic*
*Completed: 2026-09-08*
