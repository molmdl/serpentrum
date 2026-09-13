---
phase: 04-game-loop-input
plan: 08
subsystem: gui
tags: [pymol, qt, game-loop, camera-lock, wizard, input, lifecycle, teardown, auto-pause]

# Dependency graph
requires:
  - phase: 04-03
    provides: "pymol_bridge.lock_camera/unlock_camera/move_head_delta/object_exists (locked-camera bridge)"
  - phase: 04-04
    provides: "serpentrum/input.py KeySteerWizard + install/set_active/teardown lifecycle"
  - phase: 04-05
    provides: "GameTab core (countdown, tick, elapsed, pause rebase, restart, _teardown_live_session)"
  - phase: 04-06
    provides: "PluginDialog game_tab registration + Start flow"
  - phase: 04-07
    provides: "route verdict APPROVED — wizard do_special route ships; game_input = .input (no fallback)"
provides:
  - "Full playable loop mechanically wired: GO! arms camera lock (GAME-02) + steering install (GAME-03) together before the first tick"
  - "_teardown_round — THE single teardown helper on every end path (begin_game/restart, _end_run crash, dialog close via shutdown()): timers -> epoch bump -> input teardown -> unlock_camera (Pitfall 9.2; no leaked mouse locks or orphaned wizards by construction)"
  - "Pause gates steering via game_input.set_active(False/True) with the wizard installed and the camera LOCKED throughout (research D5)"
  - "Q3 focus-stealing mitigation: PluginDialog.focusInEvent -> GameTab.request_auto_pause (status=='playing' guard, Pitfall G blockSignals)"
  - "Dialog-close teardown: PluginDialog.closeEvent -> GameTab.shutdown()"
affects: [Phase 4 (04-09 final verify), Phase 5 (stacking adds its pickup teardown into _teardown_round)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Single-teardown-helper discipline (Pitfall 9.2): every end path (crash, restart, dialog close) calls _teardown_round — idempotent, saved_cam popped so double-unlock is impossible by construction"
    - "Route-agnostic input seam: `from . import input as game_input` — the one-line swap point if a future verdict ever mandates the gui_input fallback (identical install/set_active/teardown signatures)"
    - "Arm-before-timers ordering (gameloop Q6): lock_camera + input.install BEFORE tick/elapsed timer.start so the first tick is already locked/steerable"
    - "Shared pause internals: _apply_pause_state(True/False) used by both _on_pause_toggled (button toggle) and request_auto_pause (focus event) with blockSignals around programmatic setChecked (Pitfall G)"

key-files:
  created: []
  modified:
    - serpentrum/gui_game.py
    - serpentrum/gui.py

key-decisions:
  - "Pause keeps BOTH the wizard installed (set_active(False) grab-and-no-op) AND the camera locked — gameloop research D5 + input research open-q 5 resolution; teardown only happens at round end"
  - "_end_run logs the verdict BEFORE tearing down so crash text stays visible in the info box while timers/input/camera die with the run"
  - "request_auto_pause guards on status=='playing' so focusInEvent firing during Start-click/countdown/idle/over is a no-op (focusInEvent fires on ANY dialog focus gain, including the Start click)"

patterns-established:
  - "Public shutdown() as the dialog-close hook funneling into the same _teardown_round — every end path reaches ONE helper"

# Metrics
duration: 6 min
completed: 2026-09-13
---

# Phase 4 Plan 08: Play Wiring Summary

**Play lifecycle fully wired: GO! arms the camera lock + steering wizard together before the first tick; ONE idempotent _teardown_round serves every end path (crash, restart, dialog close); pause gates steering with the wizard installed and camera locked; dialog focus gain auto-pauses mid-run; dialog close tears the round down — no leaked camera locks or orphaned wizards possible by construction.**

## Performance

- **Duration:** 6 min
- **Started:** 2026-09-13T19:38:40Z
- **Completed:** 2026-09-13T19:43:56Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- **GAME-02 + GAME-03 arm together at GO!** — `_begin_play` now runs `pymol_bridge.lock_camera()` (saved_cam stored on the session) and `game_input.install(engine.request_direction)` (handle stored on `self._input_handle`) BEFORE starting the tick/elapsed timers, so the first 100 ms tick is already locked and steerable (gameloop Q6 ordering; all on the GUI thread, no marshaling).
- **THE single teardown helper (Pitfall 9.2)** — `_teardown_live_session` renamed/extended to `_teardown_round`: stop both timers → bump epoch (kills stale singleShot chains) → `game_input.teardown(handle)` (accepts-and-ignores on the wizard route, uniform with the fallback) → `unlock_camera(sess.pop('saved_cam', None))` (pop makes double-unlock impossible) → blockSignals pause-button reset (Pitfall G). Call sites: `begin_game` (start/restart-first), `_end_run` (after logging the verdict), `shutdown()` (dialog-close hook).
- **Pause/resume gate steering without teardown** — internals extracted to `_apply_pause_state(True/False)`: pause branch adds `game_input.set_active(False)` (wizard stays installed, grabs-and-no-ops — arrows neither steer nor step movie frames); resume branch re-arms with `set_active(True)` AFTER the paused_accum rebase. Camera untouched during pause (research D5).
- **Q3 focus-stealing mitigation** — public `request_auto_pause()` (status=='playing' guard + blockSignals'd programmatic setChecked) reused via `_apply_pause_state(True)`; logs 'auto-paused (dialog took focus - click Resume, then the 3D viewer)'.
- **PluginDialog lifecycle hooks** — `focusInEvent` → `game_tab.request_auto_pause()`; `closeEvent` → `game_tab.shutdown()`; class docstring switching-contract paragraph updated.

## Task Commits

Each task was committed atomically:

1. **Task 1: GameTab play wiring — lock camera + install input at GO!, one teardown for every path** — `93171fa` (feat)
2. **Task 2: PluginDialog focus + close hooks** — `b8967f8` (feat)

**Plan metadata:** (see final commit below)

## Files Created/Modified

- `serpentrum/gui_game.py` — play lifecycle: `_begin_play` (lock → install → timers), `_teardown_round` (ONE helper), `_apply_pause_state`, `request_auto_pause`, `shutdown`; `_end_run` now tears down after logging the verdict; `from . import input as game_input` with the route swap-point comment
- `serpentrum/gui.py` — `PluginDialog.focusInEvent` + `closeEvent` hooks, docstring updates (34 insertions, no deletions)

## Gate + Smoke Results

- `python3.6 tests/run_gates.py`: **all gates green** (syntax + plugin-path safety PASS; purity AST PASS; 451 unittests PASS)
- `python3.6 tests/run_gates.py --smoke`: **all five sentinel smokes PASS** — SMOKE-OK SKELETON, VIEWER-BRIDGE, VIEWER-DEMO, LOOP-CAMERA (proves lock_camera/unlock_camera), INPUT-WIZARD (proves install/set_active/teardown). Smoke 02 (dialog) remains informational non-blocking FAIL (01-05 offscreen dead end, documented).

## Lifecycle Audit (grep-verified)

- Exactly ONE `pymol_bridge.lock_camera` call site (gui_game.py:243, `_begin_play`) and exactly ONE `pymol_bridge.unlock_camera` call site (gui_game.py:444, inside `_teardown_round`).
- Exactly ONE `game_input.teardown` call site (gui_game.py:440, inside `_teardown_round`).
- Every end path reaches `_teardown_round`: begin_game (:169), _on_restart (:402), _end_run (:414), shutdown (:419 → :421). No path stops timers without it.
- `set_active` appears exactly in the pause branch (:354) and resume branch (:361); camera is referenced nowhere in `_apply_pause_state`.
- `grep -c "def shutdown" gui_game.py` → 1; `grep -c "exec_(" gui.py` → 0 (modeless rule intact).

## Decisions Made

- Pause keeps BOTH the wizard installed (grab-and-no-op via set_active(False)) AND the camera locked — gameloop research D5 + input research open-q 5 resolution (tearing down on pause would double the set_wizard save/restore leak surface; unlocking would let the user rotate a frozen scene).
- `_end_run` logs the verdict BEFORE `_teardown_round` so crash text stays visible while round state dies.
- `request_auto_pause` guards on `status == 'playing'` because `focusInEvent` fires on ANY dialog focus gain (including the Start click) — countdown/idle/over states as documented no-ops.

## Deviations from Plan

None - plan executed exactly as written. (The plan's Task-1 note about a possible `gui_input` fallback import was historical context only — the 04-07 verdict approved the wizard route, so `from . import input as game_input` stands as written.)

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **The full playable loop now exists mechanically**; plan 04-09 owns the final live verdicts (camera immovable, steering mid-run, pause/restart behavior, no leaks, auto-pause on focus) via the phase-closing human-verify checkpoint.
- Phase 5 (stacking) will add pickup-object teardown INTO `_teardown_round` (the single helper is the designated extension point; do not add second teardown paths).
- Live behavior is 04-09's checkpoint domain (01-05: headless widget construction is a dead end; GUI verdicts are human-verify only).

---
*Phase: 04-game-loop-input*
*Completed: 2026-09-13*
