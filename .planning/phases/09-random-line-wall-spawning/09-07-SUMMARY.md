---
phase: 09-random-line-wall-spawning
plan: 07
subsystem: ui
tags: [gui, wall, spawner, source-scan-pins, teardown, pymol]

# Dependency graph
requires:
  - phase: 09-random-line-wall-spawning
    provides: "09-01 wall.WallSpawner + wall_seed_from_setup + min_atom_clearance; 09-02 engine.set_wall/wall; 09-04 hud_logic.debug_wall_trace; 09-05 pymol_bridge.load_line_wall/delete_walls"
provides:
  - "Phase 9 GUI wall wiring: wall_mod import, _build_engine WallSpawner construction, begin_game session 'wall_spawner' key, _respawn_pickup success-tail wall seam, _teardown_round delete_walls line"
  - "TestWallWiring source-scan pins (counts, win-tick guard, teardown seat, absence)"
affects: [09-08, 09-09]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Wall seam at the shared _respawn_pickup SUCCESS-BRANCH TAIL (both capture-tail + cooldown-resume inherit the same-time pairing via the can_spawn gate)"
    - "Win-tick guard `if engine.finished: return` placed ONLY on the wall half (pickup half untouched)"
    - "33c13e7 debug discipline: trace inputs computed unconditionally, only the self._log call session['debug']-gated; raw sym-first 4-tuples feed both next_wall and min_atom_clearance (no (x,y) projection)"
    - "House source-scan pin pattern (TestGuiSpawnCallSites/_method_body body-slice) for gui seam durability"

key-files:
  created: []
  modified:
    - serpentrum/gui_game.py
    - tests/test_hud_content.py

key-decisions:
  - "WallSpawner constructed at exactly one site (_build_engine) receiving the SAME (box_min, box_max) tuple shape as PickupSpawner -- never a flattened (x0,y0,x1,y1) call (would misbind box_max<-y0, seed<-x1)"
  - "Wall seam lives inside _respawn_pickup's success-branch tail, never at the two _respawn_pickup call sites"
  - "Win-tick guard is NOT retrofitted onto the pickup half (its materialize is harmless; walls are not swept there)"
  - "no-records runs leave session['wall_spawner'] None (box-only parity)"

patterns-established:
  - "Wall swap sequence pinned: next_wall -> None keeps old wall -> set_wall + delete_walls + load_line_wall"

# Metrics
duration: 3min
completed: 2026-10-13
---

# Phase 9 Plan 07: GUI Wall Wiring Summary

**Session-anchored WallSpawner wired into the GUI: the wall swaps exactly with each successful next-mol spawn inside `_respawn_pickup`'s success tail (win-tick-guarded), debug-traced with unconditionally computed inputs, and cleared at `_teardown_round` beside pickups.**

## Performance

- **Duration:** 3 min
- **Started:** 2026-10-13T18:21:03Z
- **Completed:** 2026-10-13T18:24:24Z
- **Tasks:** 3
- **Files modified:** 2

## Accomplishments
- `TestWallWiring` source-scan pins added (RED first): 5 `==1` call-count pins (`wall_mod.WallSpawner(`, `wall_mod.wall_seed_from_setup(`, `next_wall(`, `load_line_wall(`, `debug_wall_trace(`), 3 body-slice pins (`_respawn_pickup` contains `engine.finished`; `_teardown_round` contains `delete_walls(`; `_build_engine` contains `wall_mod.WallSpawner(`), and 2 absence pins (`min_head_dist_a`, `REFUSE_WALL`).
- `gui_game.py` wired: `from . import wall as wall_mod`; `_build_engine` constructs the `WallSpawner` beside the `PickupSpawner` with the SAME `(x0,y0)`/`(x1,y1)` box tuple shape, seeded via the distinct `wall_seed_from_setup` stream (no-records -> None); `begin_game` session dict carries `'wall_spawner'`; `_respawn_pickup` success tail runs the win-tick guard then `next_wall(head, seed atoms, other-live atoms)` on raw sym-first 4-tuples, then `set_wall`/`delete_walls`/`load_line_wall` and the unconditionally-computed `debug_wall_trace`; `_teardown_round` calls `delete_walls()` beside `delete_pickups()`.
- Zero edits at the two `_respawn_pickup` call sites, `_handle_stack_event`, `_on_tick`, or `rebuild_scene`; no new HUD lines (silent default play).

## Task Commits

Each task was committed atomically (TDD RED then GREEN):

1. **Task 1: TestWallWiring pins (RED)** - `93173f0` (test)
2. **Task 2: gui_game wiring (GREEN)** - `850727c` (feat)

**Plan metadata:** the `docs(09-07): complete ... plan` commit on branch `exec/09-07` (this plan's final commit)

_Note: Task 3 was the full verification pass (gates + smokes) rolled into the GREEN commit boundary; no separate REFACTOR commit was needed._

## Files Created/Modified
- `serpentrum/gui_game.py` - wall_mod import; `_build_engine` WallSpawner construction + extras key; `begin_game` `'wall_spawner'` session key; `_respawn_pickup` success-tail wall seam; `_teardown_round` `delete_walls()` line
- `tests/test_hud_content.py` - additive `TestWallWiring` class (9 pins + absence assertions), zero edits to existing classes

## Decisions Made
- Wall seam at the shared success-branch tail: placement there makes both respawn call sites inherit the same-time pairing, and the earlier `can_spawn` gate protects against a same-tick double invocation.
- `engine.finished` guard placed at the seam head only (win-tick guard); the pickup half is deliberately left unguarded (its materialize is swept by teardown; walls are not).
- Raw sym-first `(sym, x, y, z)` 4-tuples feed both `next_wall` and `min_atom_clearance` with NO `(x, y)` projection -- s10 (09-06) feeds the same raw shape.
- `wall_id` ordinal = `engine.molecules_stacked` (1:1 with captures; zero new session state).

## Deviations from Plan

None - plan executed exactly as written. The plan's near-complete Task-2 code block was transcribed with local-variable names adapted to the real seam (`seed`/`record`/`centroid`/`engine.pickups`), as the plan's NOTES (i)/(ii) direct.

## Issues Encountered
None - gates (1050 unittests, +9 net-new) and all 11 required smokes passed on the first full battery run; informational smoke 02 remains a known non-blocking FAIL (decision 01-05), informational 09/11 PASS.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- The GUI wall feature seat is complete and pinned; ready for 09-08 (the sibling worktree registers smoke 15) and 09-09 merge/close.
- No blockers. STATE.md/ROADMAP.md updates are orchestrator-owned (worktree protocol).

---
*Phase: 09-random-line-wall-spawning*
*Completed: 2026-10-13*
