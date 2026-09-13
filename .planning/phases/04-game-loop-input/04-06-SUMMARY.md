---
phase: 04-game-loop-input
plan: 06
subsystem: ui
tags: [pymol, qt, signal-slot, tab-switch, game-loop, start-flow, gui]

# Dependency graph
requires:
  - phase: 03-07
    provides: "SetupTab form + temp-button precedent + gui.py registration contract (page 0, reserved bottom row)"
  - phase: 04-05
    provides: "GameTab (gui_game.py) with begin_game(setup) + anchored game_session"
  - phase: 04-RESEARCH-hud
    provides: "Q1 model A: SetupTab emits start_requested(setup); PluginDialog owns setCurrentIndex(1) because self.tabs lives there"
provides:
  - "SetupTab temp Start button: apply-then-emit start_requested(setup) with failure suppression"
  - "_on_apply boolean contract (False on all three modal paths, True on materialized success)"
  - "PluginDialog._on_start_requested: setCurrentIndex(1) + game_tab.begin_game(setup) — GAME-01 transition wired end-to-end"
  - "GameTab registered as page 1; page order fixed Setup -> Game -> Spectra"
affects: [04-07, 04-08, 04-09, Phase 8]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Qt-idiomatic signal/slot decoupling: child tab emits, parent dialog owns the tab switch (HUD research Q1 model A)"
    - "Apply-first Start: a failed apply (validation/load/bridge modal) suppresses start_requested — play always begins on a materialized scene"
    - "bool success contract on a formerly void Qt slot (_on_apply): Qt ignores the return for direct connects; _on_start consumes it"

key-files:
  created: []
  modified:
    - serpentrum/gui_setup.py
    - serpentrum/gui.py

key-decisions:
  - "Signal model A (HUD research Q1): SetupTab emits start_requested(setup); PluginDialog owns setCurrentIndex(1) — GameTab never reaches up to its parent QTabWidget"
  - "Start applies FIRST: GAME-01 always plays on a materialized scene (box + head exist); a failed apply suppresses the emit"
  - "Temp Start lives INSIDE the Setup tab btn_row (Phase-3 precedent); the Phase-8 canonical 6-button bottom row stays byte-identical"

patterns-established:
  - "start_requested(setup) signal: child-tab -> dialog -> game-tab handoff pattern for tab switches"
  - "apply-then-emit with boolean suppression: reuses _on_apply as the gate for session start"

# Metrics
duration: 7min
completed: 2026-09-13
---

# Phase 4 Plan 06: Start-Flow Dialog Wiring Summary

**Temporary Setup-tab Start button with apply-then-emit `start_requested(setup)` signal, and PluginDialog page-1 GameTab registration wiring `setCurrentIndex(1)` + `begin_game(setup)` — the GAME-01 transition**

## Performance

- **Duration:** 7 min
- **Started:** 2026-09-13T18:53:30Z
- **Completed:** 2026-09-13T19:00:50Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- SetupTab gains a temporary Start button (btn_row: Apply / Cleanup / Start, Phase-3 temp-button precedent) driven by `_on_start`: applies the current configuration FIRST (validate + setloader + materialize), then emits `start_requested(setup)` with the post-apply dict — a failed apply suppresses the emit, so GAME-01 always plays on a materialized scene
- `_on_apply` now returns a boolean (False on all three modal paths — validation errors, load errors, bridge errors; True on materialized success) — Qt ignores the return on direct connects, and `_on_start` consumes it
- PluginDialog registers GameTab as page 1 (`self.game_tab`, page order fixed Setup → Game → Spectra), reduces `_TAB_DEFS` to the Spectra placeholder only, and connects `setup_page.start_requested` to `_on_start_requested` (`setCurrentIndex(1)` + `game_tab.begin_game(setup)`) — the Qt-idiomatic model-A decoupling from HUD research Q1
- Reserved Phase-8 bottom row byte-identical; find_existing untouched; modeless `.show()` discipline held (zero `.exec_()` anywhere); exactly 3 `addTab` calls
- All gates green: syntax + plugin-path safety + AST purity + 451 tests on every commit

## Task Commits

Each task was committed atomically:

1. **Task 1: SetupTab Start button + start_requested signal + apply-returns-bool** — `fe74ef2` (feat)
2. **Task 2: gui.py page-1 GameTab registration + Start slot** — `9c5373d` (feat)

**Plan metadata:** see `docs(04-06): complete start-flow dialog wiring plan` (this commit)

## Files Created/Modified
- `serpentrum/gui_setup.py` — `start_requested = QtCore.Signal(object)` class attribute (temp Phase-4 signal); `start_btn` in `_build_widgets`/`_build_layout`/`_wire_signals`; `_on_apply` returns bool on all four return points; new `_on_start` handler (apply-then-emit); module + class docstrings updated for the three temp buttons
- `serpentrum/gui.py` — module + class docstrings updated (pages 0-1 live, page 2 placeholder); `from .gui_game import GameTab`; `_TAB_DEFS` reduced to Spectra only; GameTab registered as page 1 with `self.game_tab`; `start_requested` → `_on_start_requested` slot (`setCurrentIndex(1)` + `begin_game(setup)`)

## Decisions Made
- **Signal model A (HUD research Q1):** SetupTab emits `start_requested(setup)`; PluginDialog owns the tab switch because `self.tabs` lives there — GameTab never reaches up to its parent QTabWidget (fragile). Followed the researched recommendation verbatim.
- **Apply-first Start:** the Start button applies the full configuration first (the 03-07 Apply path — validate → setloader → materialize) and emits the post-apply setup dict; any modal error path suppresses the emit. This makes GAME-01's "click Start → head moves" always run on a materialized scene.
- **Boolean contract on `_on_apply`:** previously void; now returns True/False so `_on_start` can gate the emit without duplicating the apply logic. Existing callers: none (signal-connected only; Qt ignores return values).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] SetupTab class docstring still said "two temporary buttons"**
- **Found during:** Task 1 (docstring updates)
- **Issue:** the plan mandated updating only the module docstring's temp-button sentence; the class docstring's "two temporary buttons (Apply / Show in Viewer, Cleanup)" sentence would have become factually wrong
- **Fix:** updated the class docstring sentence to "three temporary buttons (Apply / Show in Viewer, Cleanup, Start)"
- **Files modified:** serpentrum/gui_setup.py
- **Verification:** doc-only; grep shows no remaining "two temporary" claim
- **Committed in:** fe74ef2 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 doc-correctness bug)
**Impact on plan:** Trivial doc-hygiene alongside the mandated module-docstring update. No scope creep.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- GAME-01's transition is wired end-to-end: Setup-tab Start → apply (materialized scene) → `start_requested(setup)` → tab switch to Game → `GameTab.begin_game(setup)` → epoch-guarded 3-2-1 countdown
- Scope guards held: no camera/input/auto-pause wiring (04-08 owns), no closeEvent, no head randomization flip ('random' keeps the Phase-3 records[0] placeholder), no new bridge/engine calls
- Reserved Phase-8 bottom row byte-identical; page order fixed Setup → Game → Spectra; Spectra placeholder untouched
- Grep contracts green: zero `exec_(`, zero `from pymol import` in both edited GUI modules; addTab count == 3; wiring trace end-to-end
- Live behavior (tab actually switches on click, countdown runs) is human-verify in plan 04-09 per the 01-05 decision
- **Ready for 04-07-PLAN.md** (CHECKPOINT: early keys human-verify — the failure-cheap input spike)

---
*Phase: 04-game-loop-input*
*Completed: 2026-09-13*
