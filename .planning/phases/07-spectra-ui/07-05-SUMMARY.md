---
phase: 07-spectra-ui
plan: 05
subsystem: ui
tags: [pymol.Qt, QPainter, QImage, PNG, plot, spectra, purity-allowlist]

# Dependency graph
requires:
  - phase: 07-spectra-ui (plan 07-02)
    provides: "plot_logic pure half — Scene contract, build_scene, size_presets, mode_caption (merged wave 1)"
  - phase: 02-pure-core-game-chemistry-logic
    provides: "spectra.parse_g98 + broaden contract + g98.out fixture (26 atoms / 72 modes / 3 imaginary)"
provides:
  - serpentrum/gui_plot.py — IrPlotWidget (set_scene/set_show_labels/paintEvent), module-level paint_scene seam, SpectraPlotPanel (size combo + labels toggle + save button + status_cb), render_image route-A save
  - smoke/12_plot_smoke.py — REQUIRED guarded-app renderer regression (sentinel SMOKE-OK PLOT-RENDER)
  - GUI_MODULES single-writer registration: gui_plot.py (live) + gui_spectra.py (inert for 07-07)
  - AGENTS.md renderer-smoke QApplication-guard rule
affects: [07-spectra-ui plans 07-06 (human verify), 07-08 (SpectraTab embeds SpectraPlotPanel), 08 (help/export)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Route A save: ONE paint_scene(painter, rect, scene, show_labels) seam serves paintEvent AND the PNG save — identical scene, identical look (no QWidget.grab())"
    - "QFontMetrics-driven margins + volume.py tick-label dodge; NEVER fixed-35px assumptions"
    - "Guarded headless renderer: QApplication.instance() or QApplication([]) before ANY font-touching paint (probe RUN A hard-kill)"
    - "GUI_MODULES inert-first single-writer registration across a phase"

key-files:
  created: [serpentrum/gui_plot.py, smoke/12_plot_smoke.py]
  modified: [tools/check_purity.py, AGENTS.md, tests/run_gates.py]

key-decisions:
  - "Route A (QImage re-render at 2x via the shared seam) ships; route B (QWidget.grab()) demoted to a single non-shipped comment"
  - "v1 adjustment surface = size-preset combo + 'Show axis labels' toggle ONLY (no FWHM control, no zoom/pan)"
  - "gui_spectra.py registered INERT in the same single-writer edit so 07-07 needs no allowlist edit"

# Metrics
duration: 10 min
completed: 2026-09-26
---

# Phase 7 Plan 05: Spectra IR Plot Widget Summary

**Data-in QPainter IR plot (IrPlotWidget + SpectraPlotPanel) with one paint_scene seam serving screen and 2x route-A PNG save identically, regression-pinned by a REQUIRED guarded-QApplication headless smoke.**

## Performance

- **Duration:** 10 min
- **Started:** 2026-09-26T17:55:02Z
- **Completed:** 2026-09-26T18:04:40Z
- **Tasks:** 3/3
- **Files modified:** 3 created (gui_plot.py, smoke/12_plot_smoke.py) + 3 edited (check_purity.py, AGENTS.md, run_gates.py)

## Accomplishments

- `serpentrum/gui_plot.py` (338 lines, GUI class): module-level `paint_scene(painter, rect, scene, show_labels=True)` seam with antialiasing ON, QFontMetrics margins, volume.py tick dodge, clipped `QPolygonF` curve; `IrPlotWidget` (minimum 320x260, sizeHint 600x200, update()-only repaints); `SpectraPlotPanel` with the exact v1 cut (size-preset combo via addItem(label, data), 'Show axis labels' toggle default ON, 'Save Plot (PNG)' with getSaveFileName static + cancel guard + `.png` append + status_cb reporting); `render_image(scene, logical_size, scale=2, show_labels)` in the research-verified shape. Empty (None) scene paints axes frame + the pinned 'run a calculation to plot a spectrum' hint.
- `smoke/12_plot_smoke.py` REQUIRED: stage 0 guarded app construct (the load-bearing probe RUN A finding); stage 1 real-scene from g98 (72 modes / 3 imaginary / 800 points); stage 2 render->temp PNG with magic bytes + reload 1600x1000; stage 3 axis-off leg; stage 4 empty-scene leg; all sentinels flushed — **SMOKE-OK PLOT-RENDER** (57 990-byte full PNG).
- Single-writer purity registration: GUI_MODULES gains `gui_plot.py` (live) AND `gui_spectra.py` (inert — 07-07 creates the file against the already-present entry); gates stayed green inert-first.
- AGENTS.md rulebook now carries the renderer-smoke app-guard rule (fonts with no Q*Application silently hard-kill the process).

## Task Commits

Each task was committed atomically:

1. **Task 1: GUI_MODULES single-writer registration + AGENTS.md app-guard note** — `e1d7dae` (feat)
2. **Task 2: gui_plot.py — IrPlotWidget + paint_scene seam + SpectraPlotPanel + render_image** — `f6ee16f` (feat)
3. **Task 3: REQUIRED smoke 12 + REQUIRED_SMOKES tuple edit** — `52cd9ba` (test)

**Plan metadata:** (see final docs commit below) (docs: complete plan)

## Files Created/Modified

- `serpentrum/gui_plot.py` — SPECTRA-03 plot widget + panel + save route (GUI class, pymol.Qt only)
- `smoke/12_plot_smoke.py` — REQUIRED headless renderer smoke (guarded app; images only, no widgets)
- `tools/check_purity.py` — GUI_MODULES + gui_plot.py + inert gui_spectra.py with per-plan comments
- `AGENTS.md` — renderer-smoke QApplication-guard bullet after the smoke one-liner
- `tests/run_gates.py` — REQUIRED_SMOKES + smoke/12_plot_smoke.py with plan-07-05 comment

## Decisions Made

- Bottom/left margins widened from the plan's shorthand formula (`bottom = fm.height()+6`) to `2*fm.height()+8` / `left = fm.height()+4 + max y-label width + 2*fcw` so the x title row and the rotated y title can never clip — the plan's own non-clip intent (volume.py precedents) over its literal constants.
- Without labels (toggle OFF) margins collapse to small insets (6/4/12) so the toggle visibly gains plot area.
- `grab()` appears exactly once, inside a single `#` comment line (route-B demotion); AST-verified.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Margin shorthand would clip axis titles**
- **Found during:** Task 2 (gui_plot.py paint_scene)
- **Issue:** Plan's margin formula `bottom = fm.height()+6` leaves room for the tick-label row only; the same paint_scene must also draw the centered x title below the ticks (and a rotated y title left of the y labels), which the shorthand would clip — contradicting the plan's "margins computed from QFontMetrics so labels never clip" must-have.
- **Fix:** `bottom = 2*fm.height()+8` and `left = fm.height()+4 + max(y-tick label width) + 2*averageCharWidth` when show_labels; small insets otherwise.
- **Files modified:** serpentrum/gui_plot.py
- **Verification:** smoke 12 stage 2 renders the full labeled scene to a valid 1600x1000 PNG (57 990 bytes) headlessly.
- **Committed in:** f6ee16f (part of task commit)

**2. [Rule 2 - Missing Critical] Tiny-rect guard**
- **Found during:** Task 2
- **Issue:** A degenerate widget rect (<10 px) would produce a negative-width plot rect and map values into an inverted region (still safe in Qt, but garbage pixels).
- **Fix:** early return in paint_scene when the plot rect is <10 px on either axis.
- **Files modified:** serpentrum/gui_plot.py
- **Verification:** gates + smoke green.
- **Committed in:** f6ee16f (part of task commit)

---

**Total deviations:** 2 auto-fixed (1 bug, 1 missing critical)
**Impact on plan:** Both within the stated must-have intent (non-clipping, never-crash). No scope creep.

### Plan-status corrections applied (orchestrator-supplied)

- Probe `smoke/tmp_research_07_plot_probe.py` verified absent (Task 3 step 4 confirm-only; never resurrected).
- Orchestrator context claimed REQUIRED_SMOKES held only smokes 10 + 13; the actual tuple holds all Phase 1-6 smokes (01, 03, 04, 05, 06, 07, 08, 10) + 13. Editing per plan (insert 12 before 13) left all prior REQUIRED smokes intact; the full --smoke leg ran 10 required launches.

## Issues Encountered

None — smoke 12 passed on first headless run; all gates first-try green.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- 07-06 (human verify) can now exercise the panel in a real GUI: on-screen look, size-combo reflow, PNG open-in-viewer ([TRAIN] 3/5 items plus the PNG-viewer human check from the research).
- 07-08 SpectraTab embeds `SpectraPlotPanel` data-in (set_scene + status_cb) with zero coupling to the runner; the inert `gui_spectra.py` allowlist entry (07-07) is already live in GUI_MODULES.
- Gate results for continuity: **829 unittests green** (unchanged from wave-1 baseline — GUI module is AST-gated only), **REQUIRED smokes 10/10 PASS** (01, 03-08, 10, 12 PLOT-RENDER, 13 MODE-ARROWS) + informational 09/11 PASS, 02 informational non-blocking FAIL (known offscreen-route closure).

---
*Phase: 07-spectra-ui*
*Completed: 2026-09-26*
