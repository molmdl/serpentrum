---
phase: 09-random-line-wall-spawning
plan: 08
subsystem: testing
tags: [smoke, headless-pymol, wall, cgo, bridge, crash, cleanup, gates, phase-9]

# Dependency graph
requires:
  - phase: 9-random-line-wall-spawning
    provides: "wall.WallSpawner + wall_seed_from_setup + min_atom_clearance (09-01); game_engine set_wall/clear_wall + ('crashed','wall') leg (09-02); pymol_bridge load_line_wall/delete_walls + WALL_NAME (09-05)"
  - phase: 8-polish-and-release
    provides: "tests/run_gates.py REQUIRED_SMOKES harness + the smoke/01 template conventions (flushed sentinels, _resolve_root, verdicts-never-exit-codes)"
provides:
  - "smoke/15_line_wall_smoke.py: the REQUIRED 12th headless smoke (6 flushed-sentinel stages) proving the wall viewer channel, delete-then-load replace, the controller capture seam (next_after -> build_pickup_seed append -> next_wall -> set_wall) with both viewer materializations, the ('crashed','wall') engine leg, delete_walls hygiene, and rebuild_scene wall sweeping"
  - "tests/run_gates.py REQUIRED_SMOKES registration (append-at-end hunk after smoke/14) — a missing required smoke now fails the gate"
affects: [09-07, 09-09]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "One mechanism per numbered smoke (07/13/14 precedent): walls get their own REQUIRED slot rather than mutating frozen release evidence"
    - "VERIFY-AT-EXECUTION guard for cmd.get_extent on a LINES-only CGO: _cgo_extent returns None on exception/malformed/non-finite/inverted, stage prints FALLBACK and falls back to name-presence"
    - "Controller-seam mirror in a smoke: the capture-resolution drive reproduces the exact 09-07 order and materializes both objects, so GUI drift (09-07) fails the headless battery"

key-files:
  created:
    - smoke/15_line_wall_smoke.py
  modified:
    - tests/run_gates.py

key-decisions:
  - "get_extent on the wall LINES CGO proved usable live (spans=30.000,25.000,10.000) — no fallback taken, but the guard stays in place for future PyMOL drift"
  - "STAGE3 seeds ONE pickup on the +x path (no steering), then exercises the full controller seam on the capture resolution; the wall policy's L2 leg gives the asserted per-atom clearance"
  - "STAGE5 counts srp_wall* BEFORE delete_walls and asserts singular + indexed forms gone, non-srp sentinel + srp_pickup_* survive (INFRA-04 class)"
  - "CGO-only smoke: literally zero 'QApplication' token in the file (grep clean), _resolve_root relative resolution, no widget construction, no new __init__.py"

patterns-established:
  - "Append-at-end REQUIRED_SMOKES registration: tuple entry + per-plan comment, SMOKE_TIMEOUT untouched, diff is the append hunk only"

# Metrics
duration: 21min
completed: 2026-10-14
---

# Phase 9 Plan 08: REQUIRED smoke 15 line-wall channel Summary

**`smoke/15_line_wall_smoke.py` (6 flushed-sentinel stages) proves the wall in real headless Windows PyMOL — load/replace extents, the controller capture seam producing a synchronized pickup + wall within `WALL_MOL_CLEARANCE_A`, the `('crashed','wall')` engine leg, `delete_walls` hygiene, and `rebuild_scene` wall sweeping — then registered as the 12th REQUIRED smoke with a full 12/12 green battery.**

## Performance

- **Duration:** ~21 min
- **Started:** 2026-10-14T00:00:00Z (approx)
- **Completed:** 2026-10-14T00:21:00Z
- **Tasks:** 2 (1 smoke + 1 registration/battery)
- **Files modified:** 2 (smoke/15_line_wall_smoke.py created, tests/run_gates.py +4 lines)

## Accomplishments

- **STAGE0 BANNER / STAGE1 WALL-LOADED:** `pb.load_line_wall((-20,-10),(10,15))` lands `srp_wall` public; `cmd.get_extent` reports xy spans exactly matching the endpoints (1e-3) and z span exactly 10.0 (the `(-BOX_DISPLAY_Z, +BOX_DISPLAY_Z)` band) — `spans=30.000,25.000,10.000`.
- **STAGE2 WALL-REPLACE:** `delete_object(WALL_NAME)` then a new `load_line_wall` MOVES the extent exactly to the new endpoints (`spans=20.000,45.000,10.000`) — the 07-09 replace contract.
- **STAGE3 WALL-SPAWN:** a real `set_a` drive captures the +x-path pickup, then mirrors the controller seam on the resolution: `PickupSpawner.next_after` -> `build_pickup_seed` + `engine.pickups.append` + live-id/counter bookkeeping -> `WallSpawner.next_wall` -> `engine.set_wall`; both `pb.materialize_pickup` and `pb.load_line_wall` run. Asserted `engine.wall is not None`, both names public, and `min_atom_clearance(engine.wall, seed['atoms']) = 93.1738 >= WALL_MOL_CLEARANCE_A (3.0)`.
- **STAGE4 WALL-CRASH:** a fresh engine driven head-first into `((3,-3),(3,3))` ends `result == 'crashed'`, final event `('crashed','wall')`, `finished` — in 4 ticks.
- **STAGE5 WALL-DELETE:** `srp_wall` + indexed `srp_wall_7` + a non-srp sentinel + `srp_pickup_tempsentry` staged; `delete_walls()` removes exactly the 2 `srp_wall*` names while the sentinel and pickup survive.
- **STAGE6 SCENECLR-WALL:** wall leftovers staged, then module-level `gui_game.rebuild_scene(setup, records_by_id)` leaves zero `srp_wall*` and a fresh `srp_box` + `srp_head` — the cleanup_srp-first order pin.
- **Registration + battery:** `REQUIRED_SMOKES` gains only the append-at-end hunk; `python3.6 tests/run_gates.py --smoke` is 12/12 required smokes SMOKE-OK (gate 4 PASS) and `python3.6 tests/run_gates.py` is green at 1041 tests.

## Task Commits

1. **Task 1+2: smoke 15 + REQUIRED_SMOKES registration** - `9a5c8ce` (feat)

**Plan metadata:** (docs: complete plan — this commit)

## Files Created/Modified

- `smoke/15_line_wall_smoke.py` - the 6-stage headless wall smoke (CGO-only, flushed sentinels, `SMOKE-OK LINE-WALL` verdict)
- `tests/run_gates.py` - REQUIRED_SMOKES append-at-end hunk after the smoke/14 entry (+4/-1; SMOKE_TIMEOUT untouched)

## Decisions Made

- **get_extent guard retained but not exercised:** the wall fence is a LINES-only CGO like smoke/13's `srp_mode_vec`; the direct `cmd.get_extent` call worked cleanly (finite, non-degenerate, exact spans), so no FALLBACK path fired. `_cgo_extent` still returns None on exception/malformed/non-finite/inverted results so any future PyMOL drift degrades to name-presence instead of a crash.
- **Deterministic initial pickup:** STAGE3 plants the first pickup at `(6.0, 0.0)` on the straight +x lane so a capture needs no steering; the spawner seam then runs unmodified on that resolution (the same order documented for 09-07).
- **No QApplication token at all:** the plan verification greps for the literal token; the file carries zero occurrences (comments reworded to "Qt app"), the smoke loads CGOs with no paint leg.

## Deviations from Plan

None - plan executed exactly as written. The `cmd.get_extent`-on-LINES-CGO VERIFY-AT-EXECUTION point resolved in the proven direction (usable), so the documented FALLBACK branch was implemented but never triggered; this is recorded here per the plan's "record any get_extent fallback honestly".

## Issues Encountered

None. The standalone smoke and the full battery ran green on the first attempt after the `QApplication`-token cleanup pass.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 9's viewer-channel evidence chain is complete: 09-01/09-02/09-05 are headless-proven by smoke/15 and WSL-proven by the 09-06 s10 scenario. 09-07 (GUI wiring) can be validated against the same seam the smoke mirrors; 09-09's wall-feel retune cannot silently break the smoke because the smoke asserts derived clearances/endpoints rather than hardcoded geometry.
- Blocks/concerns: none. All other smokes untouched; informational smoke/02 remains a pre-existing non-blocking FAIL, unrelated to this plan.

---
*Phase: 09-random-line-wall-spawning*
*Completed: 2026-10-14*
