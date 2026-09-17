---
phase: 05-stacking-game-rules
plan: 14
subsystem: gameplay
tags: [pymol, game-engine, rigid-sweep, turn-rendering, hud, cmd.rotate]

# Dependency graph
requires:
  - phase: 05-stacking-game-rules (plans 05-07, 05-09, 05-11, 05-13)
    provides: pymol_bridge.sweep_chain primitive, hud_logic.budget_text builder, session head_atoms/last_turn_delta mirror keys, 'stacked' capture seam ordering
  - phase: 02-pure-core-game-chemistry-logic (plans 02-06, 02-13)
    provides: game_engine._rotate_xy primitive, sweeping dict contract (angle_signed/total_ticks), TURN_TICKS=6, ('turning', frac) event surface
provides:
  - GAME-10 viewer half: each ('turning',) tick rigidly sweeps srp_head + all srp_seg_* about the head pivot via ONE pymol_bridge.sweep_chain call (angle_signed/TURN_TICKS, sign from the engine)
  - Pure head_atoms mirror tracked exactly through sweeps (same delta, same _rotate_xy primitive) - controller truth stays == viewer truth for tail frames + clash gate
  - Sweep-final tick rendered via stored session['last_turn_delta'] (engine clears sweeping before the event list is handled)
  - 'budget_warning' count-free advisory branch (GAME-04 hidden counts preserved)
affects: [05-15 completion presenter, 05-16 phase-closing gates/human-verify, phase-6 spectra handoff]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "One bridge cmd call per ('turning',) tick (Pattern 5 perf discipline); engine owns ALL sweep math/time, GUI renders only"
    - "Final-clear event-contract: store last_turn_delta on every mid-sweep tick so the final tick (engine.sweeping already None) still rotates the same +/-15 degrees step"
    - "Pure mirror rotation in the GUI via the engine's own _rotate_xy primitive - no invented second rotation math"

key-files:
  created: []
  modified: [serpentrum/gui_game.py]

key-decisions:
  - "'turning' stays log-silent: the sweep renders in the viewer only (existing 10 Hz chattiness policy)"
  - "Budget advisory payload (atoms_total) deliberately never rendered during play - GAME-04 hidden counts"
  - "Pivot origin read from engine.head per tick (the sweep pivot IS the head; head never moves mid-sweep)"

patterns-established:
  - "Engine-event -> single-bridge-call rendering: _handle_turn_event is the second per-tick render seam (after 'moved' -> move_head_delta)"
  - "Store-and-reuse of engine sweep state across the final-tick state clear"

# Metrics
duration: 20min
completed: 2026-09-17
---

# Phase 05 Plan 14: Turning Sweep Rendering Summary

**GAME-10 viewer half: each ('turning',) tick sweeps the whole chain rigidly about the head pivot via ONE sweep_chain cmd call (sign from the engine), with the pure head_atoms mirror rotated in lockstep; budget advisory logs a count-free line.**

## Performance

- **Duration:** ~20 min
- **Started:** 2026-09-17 ~18:10 UTC
- **Completed:** 2026-09-17T18:32:39Z
- **Tasks:** 2/2
- **Files modified:** 1 (serpentrum/gui_game.py)

## Accomplishments
- 'turning' branch replaced the deliberate silence: per tick, delta = engine.sweeping['angle_signed']/total_ticks (+/-15 deg) while sweeping is open; the final tick (engine clears sweeping inside _advance_sweep BEFORE the event list is dispatched) reuses session['last_turn_delta'] stored on every mid-sweep tick.
- ONE pymol_bridge.sweep_chain(delta, engine.head) call per tick - cmd.rotate('z', delta, 'srp_head or srp_seg_*', camera=0, origin=[hx, hy, 0]): the head pivots in place (Pattern 2, ring normal follows the chain), the whole chain sweeps as a rigid body, no per-object loops or matrices.
- The pure session['head_atoms'] mirror rotates by the SAME delta with the engine's own game_engine._rotate_xy about (head[0], head[1]) - z and sym preserved exactly as _advance_sweep does for segments, so controller truth == viewer truth for the next tail frame and the clash gate.
- 'budget_warning' branch: self._log(hud_logic.budget_text()) - count-free advisory once per run; the atoms_total payload is deliberately not displayed (GAME-04).

## Task Commits

Each task was committed atomically:

1. **Task 1: 'turning' branch - bridge sweep + head mirror** - `c9c216a` (feat)
2. **Task 2: 'budget_warning' advisory branch** - `eae2939` (feat)

## Files Created/Modified
- `serpentrum/gui_game.py` - `_handle_event` gained 'turning' (via new `_handle_turn_event`) and 'budget_warning' branches; docstrings updated; `import math` added. Only file modified.

## Verification Results

- `python3.6 tests/run_gates.py` - PASS (gate 1 syntax+plugin-path, gate 2 purity AST, gate 3 unittest: 561/561 OK), run before EVERY commit.
- `python3.6 tests/run_gates.py --smoke` - PASS, required smokes by flushed SMOKE-OK sentinels (never exit codes): 01 SKELETON, 03 VIEWER-BRIDGE, 04 VIEWER-DEMO, 05 LOOP-CAMERA, 06 INPUT-WIZARD, 07 TRANSFORM, 08 EDGEON - all SMOKE-OK. Smoke 02 (offscreen dialog) informational FAIL, non-blocking as known. Run again before Task 2's commit (gui_game touched).
- Grep audits: exactly ONE sweep_chain call site in gui_game (line 616; only other hits are docstring/comment); no new QTimer/singleShot in the turning branch; budget_text call site present; no `str(ev[1])` rendering of the budget payload.
- Perf-discipline audit: the turning branch issues exactly ONE cmd call (via sweep_chain) and one pure list comprehension per tick - no viewer reads, no object rebuilds.
- Engine contract respected: no collision re-checking (pre-checked at sweep open), no second timer (the sweep tick IS the movement tick), sweeping-state reads only (angle_signed/total_ticks, public state).

## Decisions Made
None beyond the plan - followed the locked GAME-10 split (engine owns all sweep math/time; GUI adds one rotation call per tick) and the locked GAME-04 hidden-counts policy exactly as specified.

## Deviations from Plan

None - plan executed exactly as written. (Both plan tasks were implemented in one working-tree pass, then split into the two atomic per-task commits: the 'budget_warning' branch was temporarily held back for Task 1's commit and re-applied for Task 2's - the shipped tree and history match the plan's intent exactly.)

## Issues Encountered
None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Ready for 05-15 (completion presenter + Get Spectra activation): the full engine event surface is now consumed by _handle_event ('turn_refused', 'turning', 'stacked', 'crashed', 'budget_warning', 'won'); the completed snake in the viewer is rigidly correct post-sweep for the completion reframe.
- 05-16 human-verify should visually confirm the sweep: 6 x 15 deg rigid steps, head spinning in place, no drift (measured sweep drift 3.7e-06 A per 90 deg is below any visible threshold; mirror/engine truth identical by construction).

---
*Phase: 05-stacking-game-rules*
*Completed: 2026-09-17*
