---
phase: 09-random-line-wall-spawning
plan: 02
subsystem: core-engine
tags: [game-engine, wall-collision, head-only, referee-order, tdd, unittest, python36, pure-module]

# Dependency graph
requires:
  - phase: 02-foundation-pure-core (02-06 movement core, 02-10 collision/rules, 02-13 sweeps)
    provides: the step() referee skeleton (moved->boundary->body->stacked->won),
    _point_segment_distance_sq, the attach_segment state-only-write pattern,
    GAME-05 crash end-state shape
  - phase: 09-random-line-wall-spawning (research)
    provides: 09-RESEARCH-engine-policy.md C1 (state API) + C2 (collision
    semantics, referee slot, swept-immobility proof) — the executed authority
provides:
  - engine.wall state contract (None or float-coerced ((ax, ay), (bx, by)) pair)
  - set_wall / clear_wall state-only API (attach_segment pattern; no events)
  - additive wall=None keyword on GameEngine.__init__ AND reset (test seam)
  - WALL_COLLISION_RADIUS_A = 2.0 (independent constant name beside
    BODY_COLLISION_RADIUS_A — owner can retune wall feel without touching
    body feel)
  - the wall crash leg in step() slotted BETWEEN boundary and body:
    ('crashed', 'wall'), finished=True, result='crashed', pending=[],
    snake stays complete -> rides the existing generic crash->completion
    path with zero GUI edits
  - referee order moved -> boundary -> WALL -> body -> stacked -> won,
    pinned by precedence + crash-suppresses-capture tests
  - 16 new pins in tests/test_engine_wall.py (602 lines; every prior
    engine suite green UNMODIFIED)
affects: [09-03 (integration chain s10), 09-05 (GUI wiring: WallSpawner
next_wall -> engine.set_wall seam), 09-06 (full gates + owner
feel-check => wall radius retune surface)]

# Tech tracking
tech-stack:
  added: []   # stdlib math only — the engine stays PURE (no new deps)
  patterns:
    - "wall seams mirror attach_segment: controller-written state, engine
      never echoes its own state changes as step() events"
    - "all three crash legs (boundary/wall/body) stay textually parallel
      (append reason, finished=True, result='crashed', pending=[], return) —
      deliberately NOT unified into a helper"
    - "test geometry DERIVED from module constants (exact-radius
      constructions use game_engine.WALL_COLLISION_RADIUS_A, never a
      hardcoded 2.0) so a wall-feel retune moves tests with the value"

key-files:
  created:
    - tests/test_engine_wall.py
  modified:
    - serpentrum/game_engine.py

key-decisions:
  - "REFACTOR skipped: the plan permits a shared _finish_crash(reason)
    helper ONLY by refactoring the boundary/body legs in the same commit,
    which contradicts its harder 'ZERO other edits: no boundary/body leg
    changes' directive — parallel legs kept for traceability"
  - "WALL_COLLISION_RADIUS_A ships at 2.0 (same value as
    BODY_COLLISION_RADIUS_A, deliberate independent name);
    tests derive exact-radius geometry from the constant"
  - "wall binds HEAD ONLY at straight-motion moved ticks (sweeps
    early-return; the head is the pivot and never moves — completeness
    proof pinned by test_sweep_through_wall_no_crash)"

patterns-established:
  - "set_wall/clear_wall: the Phase-9 engine-seam style — state-only,
    float-coerced tuple pair, one-live-wall overwrite semantics"
  - "wall= ctor/reset test seam: additive keyword invisible to all
    existing pins (verified: no exhaustive __dict__/signature pins)"

# Metrics
duration: 18 min
completed: 2026-10-12
---

# Phase 9 Plan 02: Engine Wall State + Head-Only Wall Collision Summary

**Static line-wall as the run's lethal third hazard in the pure engine: `engine.wall` state (set_wall/clear_wall, float-coerced tuple pair, one-live-wall replace) plus a strict-`<` head-only crash leg `('crashed', 'wall')` slotted between boundary and body — referee order now moved → boundary → wall → body → stacked → won, with 16 new pins and every prior engine suite green unmodified.**

## Performance

- **Duration:** 18 min
- **Started:** 2026-10-12T18:42:09Z
- **Completed:** 2026-10-12T19:00:20Z
- **Tasks:** TDD RED → GREEN (REFACTOR skipped with rationale) — 2 commits
- **Files modified:** 2 (serpentrum/game_engine.py +96/−4; tests/test_engine_wall.py new, 602 lines)

## Accomplishments
- Wall state contract exact: `engine.wall` None default, float-coerced tuple pair, state-only writes (no events, the attach_segment pattern), clear/reset rebuild wall=None, and the additive `wall=None` keyword accepted by BOTH `__init__` and `reset` (test seam).
- HEAD-only wall crash in the GAME-05 class: post-move head within `WALL_COLLISION_RADIUS_A` (STRICT <, squared compare via the degenerate-safe `_point_segment_distance_sq`) emits `('crashed', 'wall')` with the byte-parallel boundary/body end-state — `finished=True`, `result='crashed'`, `pending=[]`, snake stays complete → spectra.
- Referee slot proven: boundary-over-wall and wall-over-body precedence on same-tick double collisions; crash tick suppresses capture (boundary-tie precedent); exactly-at-radius never crashes; degenerate zero-length wall is a point obstacle; chain-through and sweep-through never fire (early-return proof — the crash lands on the first post-sweep moved tick); wall=None is byte-identical to pre-Phase-9 streams; paused engine inert; win/reject paths untouched (G2 un-finish intact); wall immovable through moves+sweeps.

## Task Commits

Each TDD stage was committed atomically:

1. **RED — failing wall state + collision pins** - `ef84bc4` (test)
2. **GREEN — engine wall state + head-only wall crash leg** - `af2e0d1` (feat)
3. **REFACTOR** - skipped (see key-decisions; parallel crash legs are deliberate)

**Plan metadata:** see final docs commit (SUMMARY only; STATE.md/ROADMAP.md orchestrator-owned during the parallel wave).

## Files Created/Modified
- `serpentrum/game_engine.py` — `WALL_COLLISION_RADIUS_A` constant (:112) beside `BODY_COLLISION_RADIUS_A`; `wall` class-doc state entry; `wall=None` kwarg on `__init__`/`reset` (+ guarded float-coerced state rebuild); the crash leg in `step()` between the boundary (:—) and body blocks (strict `< WALL_COLLISION_RADIUS_A ** 2`); `set_wall`/`clear_wall` methods; module + step() docstring Phase-9 contracts.
- `tests/test_engine_wall.py` (NEW) — TestWallState, TestWallCrash, TestRefereeOrder (incl. the authoritative six-leg order pin), TestStrictEdge, TestHeadOnlyScope, TestLifecycleInvariants; 16 tests, 602 lines; exact-radius geometry derived from the module constant.

## Verification (all green in this worktree)

| Check | Result |
|---|---|
| `python3.6 -m unittest discover -s tests -p "test_engine_wall.py" -v` | **16 OK** |
| `test_engine_rules.py` | **28 OK UNMODIFIED** (boundary-over-body :302-323 intact; exactly-at-radius mirror holds) |
| `test_engine_core.py` | **17 OK UNMODIFIED** (additive kwarg invisible) |
| `test_engine_win_desync.py` | **7 OK UNMODIFIED** |
| `python3.6 tests/run_gates.py` | **all gates green** — syntax + plugin-path safety PASS, AST purity PASS, 1014 unittests OK |
| `grep -n WALL_COLLISION_RADIUS_A serpentrum/game_engine.py` | constant (:112) + collision leg (:742) + doc hits |
| `git diff --stat serpentrum/spawn.py serpentrum/placement.py` | **EMPTY** (engine-isolated half) |
| `git diff d02c030 -- pinned suites + spawn/placement` | **EMPTY** — zero edits outside the plan's files_modified |

Test count: 998 baseline (measured at branch point by direct run) + 16 wall pins = **1014**.

## Decisions Made
- **REFACTOR skipped** — the plan's optional `_finish_crash(reason)` helper requires refactoring the boundary/body legs in the same commit, contradicting the binding "ZERO other edits: no boundary/body leg changes"; the textual parallelism of the three crash legs is the traceability the plan's key_links demand.
- **Constant-derived test geometry** — exact-radius pins construct the wall at `post_move + game_engine.WALL_COLLISION_RADIUS_A` so a future owner wall-feel retune moves the tests with the value (5.1-06 derivation habit).
- **pending == [] post-crash asserted as state inspection only** (same posture as test_engine_rules — through the public API a crash tick's queue is already empty; the clear line is code-shape/turn-state hygiene).

## Deviations from Plan

None - plan executed exactly as written. (The optional REFACTOR leg was exercised exactly as the plan gates it: skipped, with the rationale recorded under Decisions Made.)

## Issues Encountered
- A stray-run-of-spaces docstring glitch (`default),         pickups`) slipped into the reset docstring during the GREEN edits; caught in pre-commit diff review and fixed before the GREEN commit — never landed in any commit.
- Baseline note (informational): the wave digest quoted "995 unittests" at the branch point, but a direct scoped run measures **998** pre-existing tests (verified by stashing the engine change: 998 pass + 16 wall-pin errors). The +3 is a digest staleness, not a code change — this plan touched only its two files_modified; gates recorded 1014 green.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Wave-2 ready: 09-03's integration chain s10 can drive `('crashed', 'wall')` end-to-end on the real-set_a chain; 09-05's GUI seam calls `engine.set_wall(wall)` (one-live-wall overwrite semantics already pinned); 09-06's owner feel-check can retune `WALL_COLLISION_RADIUS_A` as a single data line (tests move with the constant).
- No blockers. The crash payload rides the existing generic crash→completion path with zero GUI edits (payload-generic `'crashed into %s'` handler).

---
*Phase: 09-random-line-wall-spawning*
*Completed: 2026-10-12*
