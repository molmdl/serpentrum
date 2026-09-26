---
phase: 07-spectra-ui
plan: 07
subsystem: ui
tags: [pymol, qt, plugin, spectra, xtb, gui, model-a]

# Dependency graph
requires:
  - phase: 06-xtb-pipeline
    provides: XtbRunController signals (started/log_line/run_finished), frozen spectra_run record vocabulary, 06-09 launch pipeline + placeholder behaviors to preserve
  - phase: 07-spectra-ui (07-01)
    provides: spectra_ui.run_status_lines (frozen verdict vocabulary)
  - phase: 07-spectra-ui (07-04)
    provides: XtbRunController.log_tail() accessor (reload early-line recovery seam), declared anchor.spectra_runner field
  - phase: 07-spectra-ui (07-05)
    provides: inert GUI_MODULES registration of serpentrum/gui_spectra.py (made live here)
provides:
  - serpentrum/gui_spectra.py SpectraTab — status QLabel, streaming QPlainTextEdit log (read-only, 500-block cap), contextual run/cancel button, runner slots, run_again_requested Signal, reflect_run_state
  - Live Spectra tab as dialog page 2 (the 06-09 placeholder page is gone; launch + signal contracts preserved)
  - Reload early-line recovery: replay_log(controller.log_tail()) BEFORE connecting log_line
  - PINNED layout indices for 07-08 (plot panel insert at 2) / 07-09 (table insert at 2)
affects: [07-08 (plot embed), 07-09 (table + vectors), 07-10 (consolidated checkpoint)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Model-A tab delegation: tab owns its surfaces + emit-only signals; the dialog owns all cross-tab orchestration (launch pipeline, connect-once guard, Get-Spectra re-enable, log_external feed)"
    - "Replay-before-connect: controller.log_tail() replay precedes the live log_line connect, closing the reload early-line hole"
    - "PINNED layout insert contract: later plans insert widgets at declared QVBoxLayout indices only, never append"

key-files:
  created:
    - serpentrum/gui_spectra.py
  modified:
    - serpentrum/gui.py

key-decisions:
  - "Status label renders the LATEST launch/verdict line (single-line set); the log panel holds the full history — 06-09's accumulating status label replaced with no information loss"
  - "run_finished lands on a DIALOG slot (_on_spectra_run_finished): Get-Spectra re-enable first, then tab terminal display — the tab never reaches up (model-A, locked decision 9)"

patterns-established:
  - "Tab-as-surface pattern: runner slots (started/log_line/run_finished display halves) live in the GUI tab module; the dialog keeps only connect-once guard + cross-tab legs"
  - "Pinned-insert layout contract: [0] status / [1] log (stretch 2) / [2] button row; 07-08 inserts plot at 2, 07-09 inserts table at 2 — final order status/log/table/plot/buttons"

# Metrics
duration: 12 min
completed: 2026-09-26
---

# Phase 7 Plan 7: Spectra-Tab Shell Summary

**Live SpectraTab replaces the 06-09 placeholder page: status label + 500-block streaming QPlainTextEdit + contextual Cancel/Run-again control, dialog-wired with log_tail replay-before-connect and every pinned 06-09 behavior preserved verbatim**

## Performance

- **Duration:** 12 min
- **Started:** 2026-09-26T18:29:47Z
- **Completed:** 2026-09-26T18:41:56Z
- **Tasks:** 2
- **Files modified:** 2 (1 created, 1 edited)

## Accomplishments
- `serpentrum/gui_spectra.py` (NEW, 206 lines): `SpectraTab(anchor_state, parent)` owns its three surfaces — word-wrapped status label, read-only `QPlainTextEdit` with `setMaximumBlockCount(500)` (research Q3; matches the controller's 500-line tail so memory stays flat), and a contextual run button ('no xtb run yet' disabled → 'Cancel xtb run' while running → 'Run again' terminal). Slots: `append_log_line`, `set_status_line`, `replay_log`, `on_runner_started` (06-09 pinned started text verbatim), `on_run_finished` (spectra_ui.run_status_lines vocabulary, verdict visible in BOTH surfaces), `reflect_run_state` (construction/reload initial render), `_on_run_button` (cancel direct on the anchor-owned controller; else emit `run_again_requested` — the tab never launches).
- `serpentrum/gui.py`: page 2 is now the live tab; `_build_spectra_placeholder`, `self.spectra_status/spectra_log/spectra_run_btn`, the placeholder slots, and the dead `_TAB_DEFS`/constants loop are all removed. `_connect_runner` rewritten around the tab: `replay_log(controller.log_tail())` BEFORE connecting `log_line` (closes the reload early-line hole), `log_line`/`started` straight to tab methods, `run_finished` to the new dialog slot `_on_spectra_run_finished` (Get-Spectra re-enable first — getattr-guarded, pinned — then the tab's terminal display).
- 06-09 pinned behaviors audited and preserved: `run_again_requested.connect(self._on_spectra_requested)` re-enters the FULL pipeline (re-read last_run, re-check counts, re-run guard, re-resolve binary, disarm — never `_launch_spectra_run` with stale values); `_on_spectra_requested` decision logic byte-equivalent with destinations rerouted via `_log_spectra_line` (`set_status_line` + `append_log_line` + `game_tab.log_external` mirror, EQ-ux-2 preserved); refuse/corrupt/binary lines verbatim; `setCurrentIndex(2)` still the first action; reserved bottom row untouched; dialog-scoped `_runner_connected` connect-once guard kept; reload recovery in `__init__` (`_connect_runner` + `reflect_run_state`) renders a live/terminal anchored controller immediately.
- Gates: 829 unittests + syntax/purity PASS; full `--smoke` leg 10/10 REQUIRED smokes PASS via flushed SMOKE-OK sentinels (incl. smoke 12 PLOT-RENDER + 13 MODE-ARROWS); informational 02 remains the documented non-blocking FAIL (offscreen route closed 01-05); informational 09/11 PASS.

## Task Commits

Each task was committed atomically:

1. **Task 1: SpectraTab — status, streaming log, run control, slots** - `37779b9` (feat)
2. **Task 2: gui.py — placeholder page replaced, delegation rewired, 06-09 behaviors audited** - `eb059fa` (feat)

**Plan metadata:** `8b4a3??` (docs: complete spectra-tab shell plan) — see final git log on branch `exec/07-07`.

## Files Created/Modified
- `serpentrum/gui_spectra.py` — SpectraTab GUI module: status/log/run-control surfaces, runner slots, `run_again_requested` signal, `reflect_run_state`, PINNED layout insert contract in docstrings
- `serpentrum/gui.py` — page 2 = live SpectraTab; `_connect_runner` replay-before-connect rewrite; new `_on_spectra_run_finished` dialog slot; `_log_spectra_line` destination reroute; `__init__` reload recovery + Run-again connect; all placeholder remnants removed

## Decisions Made
- Status label shows the LATEST line only (single-line `setText`): the 06-09 placeholder accumulated 12 lines in the label; the new tab keeps the full history in the log panel, so no information loss — status acts as the "current state" line, the log as the transcript. Implementations: `_log_spectra_line` sets both; `on_run_finished` sets status to the first verdict line and appends all lines to the log.
- `run_finished` is the ONE signal that lands on a dialog-owned slot rather than a tab method: the Get-Spectra re-enable is cross-tab orchestration the tab must not reach up for (model-A). The dialog slot re-enables FIRST, then calls `tab.on_run_finished`.

## Deviations from Plan

### Auto-fixed / audit-alignment edits (in-flight, zero-behavior-impact)

**1. [Rule 3 - Blocking] Docstring literal collisions with the plan's grep-audit**

- **Found during:** Task 1 + Task 2 self-verification
- **Issue:** My own audit scripts (stricter than the plan's) initially failed on DOCSTRING mentions: `self.parent()` and `.exec_(` literals in the gui_spectra module docstring, and `setCurrentIndex(2)` in the `_on_spectra_requested` docstring made the "exactly one" grep count 2 — the plan's audit greps raw source, so the literals had to go even though they documented the very rules being audited
- **Fix:** Reworded docstrings to avoid the audited literals ("no parent-widget lookups anywhere", "no blocking modal-run call", "The Spectra-tab switch stays FIRST"). Behavior unchanged; the AST-level first-statement assertion independently pins `setCurrentIndex(2)` as the first ACTION of `_on_spectra_requested`
- **Files modified:** serpentrum/gui_spectra.py, serpentrum/gui.py
- **Verification:** grep counts clean; AST assertions pass; gates green
- **Committed in:** `37779b9`, `eb059fa`

---

**Total deviations:** 1 class (audit-alignment docstring rewording) — zero functional impact, zero scope creep.

## Issues Encountered
None. Wave-3 base (f705689) already carried everything this plan needs: the inert GUI_MODULES entry (07-05), `log_tail()` (07-04), `run_status_lines` (07-01), the declared `spectra_runner` field.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- 07-08 can embed the SpectraPlotPanel in SpectraTab.__init__ between log and buttons (plot lands at index 2 per the pinned contract); 07-09 inserts the QTableWidget at index 2 — final order status[0]/log[1]/table[2]/plot[3]/buttons[4].
- Live behavior (launch/stream/cancel/relaunch + verdict display in the real GUI) is the 07-10 consolidated checkpoint's scope — this plan's bar was structural green + AST-verified wiring + preserved-behavior audit, all met.
- No blockers. Merge note for the orchestrator: zero file overlap with 07-06 (its `smoke/manual_plot_check.py` lives in a different worktree); `serpentrum/gui.py` and `serpentrum/gui_spectra.py` are exclusively this plan's.

---
*Phase: 07-spectra-ui*
*Completed: 2026-09-26*
