---
phase: 04-game-loop-input
plan: 05
subsystem: ui
tags: [pymol, qt, qtimer, game-tab, hud, countdown, tick-loop, epoch-guard, anchor-persistence]

# Dependency graph
requires:
  - phase: 04-01
    provides: "check_purity GUI_MODULES entry for serpentrum/gui_game.py (pre-registered)"
  - phase: 04-02
    provides: "hud_logic (format_elapsed, remaining_text) + GameEngine.molecules_remaining property"
  - phase: 04-03
    provides: "pymol_bridge move_head_delta / object_exists / place_head / HEAD_NAME"
  - phase: 03-07
    provides: "anchor pattern on pmg_tk.startup._serpentrum (setup dict write-back precedent)"
provides:
  - "GameTab(QWidget): epoch-guarded 3-2-1-GO! countdown via recursive singleShot"
  - "100 ms movement tick driving engine.step(0.1) + pymol_bridge.move_head_delta (GAME-01/GAME-08)"
  - "1 Hz wall-clock-delta elapsed label + molecules-remaining label + read-only info box (GAME-07)"
  - "pause/resume with paused_accum rebase (Pitfall 9.3) + deterministic restart (GAME-07)"
  - "_SerpentrumState.game_session anchor field (reload-safe session dict)"
  - "seams for plan 04-06 (begin_game entry) and plan 04-08 (lock_camera + input install/teardown)"
affects: [04-06, 04-07, 04-08, 04-09, Phase 5]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Single-authority epoch: teardown bumps self._epoch; begin_game records session['epoch'] AFTER the bump; every singleShot closes over the epoch at schedule time (Pitfall 9.1)"
    - "Two distinct Qt-parent-owned QTimers (100 ms tick + 1 Hz elapsed) — die with the widget on reload (Pitfall 8)"
    - "Anchored session dict (engine + epoch + start_time + paused_accum + status) on _serpentrum.game_session (Pitfall 7)"
    - "Delta-based elapsed from wall clock (time.time() - start_time - paused_accum), never accumulated tick counts (Pitfall 5)"
    - "blockSignals around programmatic pause-button reset (Pitfall G)"
    - "GUI -> bridge-only viewer-command access (zero cmd. tokens in the GUI module)"

key-files:
  created:
    - serpentrum/gui_game.py
  modified:
    - serpentrum/__init__.py

key-decisions:
  - "Corrected epoch design (no double increment): the research sketch bumped the epoch in both _teardown_live_session AND begin_game; this plan applies the plan-mandated single-authority form — teardown bumps, begin_game records AFTER the bump"
  - "Elapsed computed from engine.head (engine truth, drift-free) — last moved event is informational; the bridge delta derives from engine state (gameloop M3)"
  - "'won' event handler kept with a comment that it is unreachable in Phase 4 (pickups=None); Phase 5 makes it live"
  - "Elapsed timer also stop()/start()ed on pause so the label freezes visually; the paused_accum rebase keeps the wall-clock math correct either way"

patterns-established:
  - "GameTab session lifecycle: begin_game -> (teardown-first, head recentre, engine seed, anchor write, countdown) -> _begin_play -> tick/elapsed -> _end_run"
  - "Same-instance timer stop()/start() on pause/resume — never a second QTimer (Pitfall 9.1 double-timer variant)"

# Metrics
duration: 18min
completed: 2026-09-13
---

# Phase 4 Plan 05: Game Tab HUD + Tick Loop GUI Half Summary

**GameTab(QWidget) with epoch-guarded 3-2-1 countdown, 100 ms engine tick wired through pymol_bridge.move_head_delta, delta-based elapsed/remaining HUD labels, pause/restart — plus the reload-safe _serpentrum.game_session anchor field**

## Performance

- **Duration:** 18 min
- **Started:** 2026-09-13T18:02:51Z
- **Completed:** 2026-09-13T18:20:46Z
- **Tasks:** 2
- **Files modified:** 2 (1 created, 1 modified)

## Accomplishments
- Created `serpentrum/gui_game.py` (389 lines, GUI purity class): the full researched GameTab — countdown label (28 pt), read-only rolling info box, elapsed label, molecules-remaining label, checkable Pause toggle, Restart button, hint label; two DISTINCT Qt-parent-owned QTimers (100 ms tick + 1 Hz elapsed); epoch-guarded recursive singleShot 3-2-1-GO! countdown; session lifecycle begin_game -> _begin_play -> _on_tick -> _end_run; deterministic restart; seams marked for plans 04-06 and 04-08
- Added `game_session = None` to `_SerpentrumState` in `serpentrum/__init__.py` with the documented lifecycle — first-anchor-creation-only, survives Plugin-Manager reload (Pitfall 7), GameTab is the sole writer
- All gates green: gate 1 syntax walk (py_compile of gui_game.py), gate 2 AST purity clean for the GUI class (pymol.Qt only, relative imports exempt, zero blocking modal calls), gate 3 full suite 451/451
- All grep contracts clean: zero `cmd.` call-form tokens in gui_game.py (the bridge owns viewer commands); both QTimers parented to self; game_session declared in __init__.py + written in begin_game
- Structural self-review passed: single-authority epoch (exactly one `self._epoch += 1` site, in _teardown_live_session), teardown-first in begin_game, head recentre guard, move_head_delta seam, hud_logic consumption, %-formatting only (python3.6)

## Task Commits

Each task was committed atomically:

1. **Task 1: game_session anchor field in __init__.py** — `4b893a2` (feat)
2. **Task 2: GameTab module — widgets, session lifecycle, countdown, tick, pause/restart** — `d6d2ff8` (feat)

**Plan metadata:** `docs(04-05)` commit below (PLAN + SUMMARY only; STATE.md/ROADMAP.md untouched — orchestrator-owned in this parallel wave)

## Files Created/Modified
- `serpentrum/gui_game.py` — GameTab(QWidget): the GAME-01/07/08 engine-and-display core; consumes game_engine (step/pause/resume/molecules_remaining), hud_logic (format_elapsed/remaining_text), pymol_bridge (object_exists/place_head/move_head_delta), setup_logic (BOX_PRESETS)
- `serpentrum/__init__.py` — `_SerpentrumState.game_session = None` anchor field with the lifecycle comment (mirrors the 03-07 setup-dict anchor pattern)

## Decisions Made
- **Corrected epoch design (plan-mandated):** the HUD research sketch bumped the epoch in BOTH `_teardown_live_session` and `begin_game` (double increment). Implementation uses the plan's corrected single-authority form: teardown is the only bump site; begin_game records `session['epoch'] = self._epoch` AFTER the teardown bump, so the countdown chain's `scheduled` always equals the session epoch until the next teardown. Verified: exactly one `self._epoch += 1` in the module.
- **Bridge delta from engine truth:** `_on_tick` captures `old = engine.head` before `step`, then derives `(nx, ny)` from `engine.head` after the event loop and calls `pymol_bridge.move_head_delta(nx - old[0], ny - old[1], 0.0)` — drift-free per gameloop research M3; the `('moved', ...)` payload is used only as a flag.
- **Elapsed timer frozen on pause:** the tick timer AND the elapsed timer both stop()/start() in `_on_pause_toggled` (same instances — never a second timer), so the label freezes visually during pause; resume still applies the `paused_accum += now - pause_time` rebase (Pitfall 9.3) so the math is exact either way.
- **'won' handler retained as dead code with comment:** unreachable in Phase 4 (engine seeded `pickups=None`), kept for Phase 5 per the plan's scope guard.

## Deviations from Plan

None - plan executed exactly as written. (The corrected epoch design was prescribed by the plan itself — "the research sketch increments twice; do NOT copy that" — so it is not a deviation.)

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- `begin_game(setup)` is the documented entry point for plan 04-06 (PluginDialog wires the Start button + tab switch); the pause/restart/status surfaces need no restructuring for the dialog integration
- Two clearly-marked seams for plan 04-08: `_begin_play` gets `pymol_bridge.lock_camera()` + input install; `_end_run` gets the full `_teardown_round` camera/input teardown
- GAME-01 countdown+movement mechanics, GAME-07 HUD/pause/restart, and GAME-08 fixed-dt constant speed all have their GUI half in place; live GUI verdicts are human-verify only (01-05 dead end — no headless widget construction), landing in plans 04-07/04-09
- Phase 5 impact: `'won'` handler + `remaining_text(engine.molecules_remaining)` become dynamic with pickups — zero rewiring needed

---
*Phase: 04-game-loop-input*
*Completed: 2026-09-13*
