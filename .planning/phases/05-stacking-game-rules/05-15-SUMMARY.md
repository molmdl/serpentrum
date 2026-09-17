---
phase: 05-stacking-game-rules
plan: 15
subsystem: ui
tags: [pymol-plugin, pyqt5, game-lifecycle, completion-flow, model-A-signals]

# Dependency graph
requires:
  - phase: 05-stacking-game-rules
    provides: 05-06 last_run anchor field; 05-07 zoom_chain/chain_object_names bridge primitives; 05-09 completion_lines/breakdown_lines HUD builders; 05-11 pickup cleanup folded into _teardown_round; 05-13 stacked_history session accumulation
  - phase: 04-game-loop-input
    provides: model-A signal handoff template (04-06 start_requested); single _teardown_round (04-08, locked)
provides:
  - _present_completion (zoom + revealed counts + breakdown + last_run anchor + Get Spectra enable) on the shared win/crash path (GAME-09)
  - get_spectra_btn + spectra_requested model-A signal on GameTab
  - PluginDialog._on_spectra_requested -> tabs.setCurrentIndex(2)
  - reload-mid-run saved_cam fallback in _teardown_round
affects: [06-xtb-pipeline (last_run counts/chain_objects handoff), 07-spectra-ui (Spectra page content replaces placeholder; tab switch already wired)]

# Tech tracking
tech-stack:
  added: []
  patterns: [model-A tab-switch handoff (emit-only tab, dialog owns QTabWidget), completion presenter AFTER teardown (never a second teardown), presenter-only button enable with teardown reset]

key-files:
  created: []
  modified:
    - serpentrum/gui_game.py
    - serpentrum/gui.py

key-decisions:
  - "Presenter, not teardown: _present_completion runs AFTER _teardown_round from _end_run — zoom_chain strictly after unlock_camera (P5-3: set_view clobbers prior zooms)"
  - "last_run anchored in the presenter only; chain_object_names() is the completion-ONLY name read (never per-tick)"
  - "Get Spectra button lifecycle: disabled at construction + every _teardown_round; enabled ONLY in _present_completion"

patterns-established:
  - "GAME-09 completion sequence: verdict log -> _teardown_round -> _present_completion (identical for win and crash, locked decision 8)"
  - "Model-A spectra handoff: GameTab.spectra_requested -> PluginDialog owns setCurrentIndex(2) (locked decision 9, 04-06 template)"

# Metrics
duration: 8 min
completed: 2026-09-17
---

# Phase 5 Plan 15: Completion Presenter + Get Spectra Handoff Summary

**GAME-09 completion flow live: win and crash share one path — verdict log, single teardown (live pickups die, chain survives, camera unlocks), then a presenter that zooms the chain, reveals length + score + atoms, prints the STACK-04 breakdown, anchors last_run, and enables a model-A-wired Get Spectra button.**

## Performance

- **Duration:** 8 min
- **Started:** 2026-09-17T18:59:21Z
- **Completed:** 2026-09-17T19:08:03Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- `_end_run` gained the presenter step after the single teardown: `_present_completion` frames the surviving chain via `zoom_chain` (strictly after `unlock_camera` so the restored view cannot clobber it — P5-3/Pattern 4), logs `hud_logic.completion_lines` (score = molecules_stacked, length = segments + head, atoms revealed — GAME-04 counters hidden during play, GAME-09 revealed at completion), logs `hud_logic.breakdown_lines` over the session's `stacked_history` (STACK-04), anchors `last_run = {'result', 'molecules_stacked', 'atoms_total', 'chain_objects', 'snake_id'}` on `_serpentrum` for Phases 6/7, and enables Get Spectra.
- Get Spectra button lifecycle locked: disabled at construction and on every `_teardown_round` (so begin_game's teardown-first discipline re-disables it each round); enabled ONLY in the presenter.
- Model-A spectra switch (locked decision 9, the 04-06 template): `GameTab.spectra_requested` (class-level QtCore.Signal, emit-only) -> `PluginDialog._on_spectra_requested` -> `tabs.setCurrentIndex(2)`. GameTab never reaches its parent QTabWidget; the Spectra page stays a Phase-7 placeholder.
- Reload-mid-run hardening (research teardown_integration item 4): `_teardown_round`'s saved_cam pop falls back to the anchored `game_session` when the widget session is None — same pop semantics, same idempotent contract; the stale-camera-after-reload gap is closed.

## Task Commits

Each task was committed atomically:

1. **Task 1: completion presenter + button** — `b9f6aca` (feat)
2. **Task 2: PluginDialog model-A spectra switch** — `8ac8f51` (feat)

**Plan metadata:** pending (this commit)

## Files Created/Modified

- `serpentrum/gui_game.py` — `_present_completion`, `get_spectra_btn`, class-level `spectra_requested` signal, `_end_run` presenter call, `_teardown_round` button reset + anchor saved_cam fallback
- `serpentrum/gui.py` — `spectra_requested` connection + `_on_spectra_requested` slot (`setCurrentIndex(2)`)

## Decisions Made

None beyond plan-locked ones — the plan applied the already-locked decisions 8 (win/crash identical completion path) and 9 (model-A tab ownership) verbatim; the reload-mid-run fallback was item 6 of the plan (research teardown_integration item 4), executed as specified.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## Gate Results

- `python3.6 tests/run_gates.py` — green after each task (561 tests; gates 1-3 PASS)
- `python3.6 tests/run_gates.py --smoke` (run after each task; both gui_game.py and gui.py touched) — gate 4 PASS; all 7 REQUIRED smokes passed via flushed SMOKE-OK sentinels (01 SKELETON, 03 VIEWER-BRIDGE, 04 VIEWER-DEMO, 05 LOOP-CAMERA, 06 INPUT-WIZARD, 07 TRANSFORM, 08 EDGEON); smoke 02 informational non-blocking FAIL (known 01-05 dead end)
- Ordering audit: `_end_run` = verdict log -> `_teardown_round` -> `_present_completion`; `zoom_chain` call sits strictly after the unlock in call order
- Anchor audit: `last_run` written only in `_present_completion`; `chain_object_names()` read only there (completion-only); `grep -c "def _teardown_round"` = 1
- Button lifecycle audit: `setEnabled(False)` at construction (:234) + teardown step (g); `setEnabled(True)` only in the presenter

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 5 wave 7 (05-16: phase-closing gates + consolidated human-verify checkpoint) is next; the completion flow is human-verify-only beyond the headless gates (viewer zoom, HUD reveal, live GUI behavior).
- Phases 6/7 consume `_serpentrum.last_run` unchanged: counts (`molecules_stacked`, `atoms_total`) for the SPECTRA-06 pre-xtb re-check; `chain_objects` for the viewer-extraction .xyz handoff; `snake_id` for run bookkeeping. Phase 7 replaces ONLY the Spectra placeholder page content — the tab switch is already wired and needs no rework.

---
*Phase: 05-stacking-game-rules*
*Completed: 2026-09-17*
