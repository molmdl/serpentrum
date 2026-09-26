---
phase: 07-spectra-ui
plan: 02
subsystem: ui
tags: [plot, ir-spectrum, gaussian-broadening, nice-ticks, pure-logic, tdd, python3.6]

# Dependency graph
requires:
  - phase: 02-pure-core-game-chemistry-logic
    provides: spectra.broaden (committed, fixture-pinned Gaussian broadener), g98.out fixture anchors
  - phase: 07-spectra-ui (research)
    provides: 07-RESEARCH-qt-plot.md — pure/GUI split design, pitfall 5 (y-axis zero-range), [TRAIN] 2 (ASCII glyphs), [TRAIN] 4 (axis convention)
provides:
  - serpentrum/plot_logic.py — paint-ready Scene builder (the ONLY thing 07-05's paint_scene consumes)
  - nice_ticks (1/2/2.5/5 x 10^n selection, step-precision labels, total over degenerate inputs)
  - Y_MAX_FLOOR = 1.0 pinning the empty-spectrum zero-curve case to a sane axis
  - size_presets pure data (medium/large/wide) + imaginary-mode mode_caption
affects: [07-05 (gui_plot renderer), 07-08 (spectra tab wiring fwhm live from setup_logic), 07-06/07-10 checkpoints (axis-convention sign-off)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Pure-builder/thin-GUI split (hud_logic pattern): Scene carries (value, label) tick pairs so paint maps values to pixels with zero recompute"
    - "y_max = max(peak * 1.1, Y_MAX_FLOOR) — headroom + floor so the pinned zero curve never yields a zero-range axis"

key-files:
  created:
    - serpentrum/plot_logic.py
    - tests/test_plot_logic.py
  modified: []

key-decisions:
  - "Y_MAX_FLOOR = 1.0 km/mol — empty/silent spectrum gets a 0..1 axis, never a zero-range blowup"
  - "Ascending wavenumber axis ships in v1 (owner-signable convention; descending is a v2 data-only flip, no reverse_x flag built)"
  - "NO frequency formatter in plot_logic — the single shared imaginary formatter is spectra_ui.freq_label (07-01); the v1 plot shows no raw frequencies"
  - "NO FWHM control / zoom / pan in v1 — adjustments = size presets + axis-label toggle only"

patterns-established:
  - "Scene as paint-ready data contract: 12-field namedtuple (xs ys x_min x_max y_max x_ticks y_ticks x_label y_label n_modes n_imaginary fwhm)"
  - "nice_ticks totality: hi <= lo returns a single tick at lo; labels carry the STEP's decimal count, never the values'"

# Metrics
duration: 7 min
completed: 2026-09-26
---

# Phase 7 Plan 02: Plot-logic pure half Summary

**PURE `plot_logic.py`: a paint-ready Scene over `spectra.broaden` (12 fields incl. precomputed (value,label) ticks, floored y_max, ASCII labels), classic 1/2/2.5/5x10^n nice-tick selection, v1 size presets, and an imaginary-mode caption — TDD'd, 17 fixture-anchored tests, full gates green (813 unittests).**

## Performance

- **Duration:** 7 min
- **Started:** 2026-09-26T17:42:16Z
- **Completed:** 2026-09-26T17:48:56Z
- **Tasks:** 2 (RED, GREEN)
- **Files modified:** 2 created, 0 existing modified

## Accomplishments

- `serpentrum/plot_logic.py` (161 lines, PURE — auto-classified, no registration): `Scene` namedtuple, `build_scene` (broaden wrapper + `Y_MAX_FLOOR = 1.0` + tick/label assembly), `nice_ticks`, `size_presets`, `mode_caption`.
- `tests/test_plot_logic.py` (238 lines): 17 tests — fixture scene (72 modes, 3 imaginary, peak within ±fwhm of 1150.6639), empty-scene floor pins, tick-selection matrix (500-step anchor, 2.5-step with 1-decimal labels, subunit 0.2, zero-range, negative-low), preset/caption sanity, live-fwhm passthrough, ValueError surfacing.
- Probes: `Y_MAX_FLOOR, size_presets()[0]` -> `1.0 ('medium (640x400)', (640, 400))`; fixture scene -> `72 3 3600.0 8`; purity grep (`exec_|import pymol|from pymol|import numpy`) -> 0.

## Task Commits

Each task was committed atomically (TDD RED → GREEN):

1. **Task 1: RED — failing tests for plot_logic** - `42c12de` (test)
2. **Task 2: GREEN — implement serpentrum/plot_logic.py** - `cf84423` (feat)

**Plan metadata:** recorded below (docs: complete plan)

## Files Created/Modified
- `serpentrum/plot_logic.py` — PURE plot half: Scene namedtuple, build_scene, nice_ticks, size_presets, mode_caption, Y_MAX_FLOOR
- `tests/test_plot_logic.py` — fixture-driven scene anchors + tick matrix + preset/caption tests

## Decisions Made

- Plan-pinned decisions implemented verbatim: Y_MAX_FLOOR = 1.0; tick targets x=8/y=5; Scene field list; preset list (medium default first); ascending-axis v1 (no reverse_x flag); no FWHM control in v1; no frequency formatter in this module (cross-half coordination with spectra_ui.freq_label).
- Execution-level: adopted the 02-12-verified amplitude anchor (0.9 x PEAK_INTEN) in place of the plan's 250.0 literal — see Deviations.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Peak-amplitude test anchor corrected 250.0 -> 0.9 x PEAK_INTEN (244.2 bound)**

- **Found during:** Task 2 (GREEN — test_peak_localization)
- **Issue:** The plan pinned `scene.ys[argmax] >= 250.0`, but the verified fixture arithmetic caps the broadened peak lower for this grid: step = 3600/799 ~ 4.506 cm-1, worst-case argmax misalignment = half step (~2.25 cm-1), and a Gaussian at sigma 6.794574 (fwhm 16) retains only ~0.946 of its center amplitude there (~243). Measured argmax amplitude: 249.12. The plan's 250.0 literal is unattainable; the implementation (a literal broaden wrapper) was correct.
- **Fix:** Changed the threshold to the same anchored form the committed broaden suite uses (test_spectra_broadening.py TestBroadenPeakAmplitude): `>= 0.9 * PEAK_INTEN`, with the grid-step/Gaussian-retention derivation documented inline in the test.
- **Files modified:** tests/test_plot_logic.py
- **Verification:** Full file suite green; full gates green (813 tests).
- **Committed in:** cf84423 (part of GREEN commit)

**2. [Rule 3 - Blocking] `str.isascii()` replaced by a python3.6-compatible helper**

- **Found during:** Task 1 (RED — test authoring)
- **Issue:** The plan specifies `both .isascii()` for the axis-label assertions, but `str.isascii()` only exists in python >= 3.7 and the binding WSL gate is python3.6 — the test file would not even import under the gate.
- **Fix:** Added a module-level `_is_ascii()` helper (`all(ord(ch) < 128 for ch in text)`) in the test file; the assertion semantics are identical (pure ASCII check).
- **Files modified:** tests/test_plot_logic.py
- **Verification:** File suite runs and passes under python3.6.9.
- **Committed in:** 42c12de (part of RED commit)

### Plan corrections applied (orchestrator-verified, no work performed)

**3. Task 2 step 8 (probe deletion) was a NO-OP:** `smoke/tmp_research_07_plot_probe.py` is already absent on base commit 33fe3ec (the untracked research throwaway was already cleaned). Verified via `ls smoke/` before and after — nothing to remove. Its probe evidence is preserved verbatim in 07-RESEARCH-qt-plot.md and will be superseded by the REQUIRED smoke 12 (plan 07-05).

---

**Total deviations:** 2 auto-fixed (1 bug in plan's numeric anchor, 1 blocking python3.6 incompatibility) + 1 orchestrator-supplied no-op correction.
**Impact on plan:** Both fixes preserve plan semantics exactly (threshold anchored to verified arithmetic; ASCII check identical). No scope creep.

## Issues Encountered

None beyond the deviations above — RED failed with the expected ImportError; GREEN passed on first run after the anchor correction.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `Scene` is the pinned contract for plan 07-05's `gui_plot.paint_scene` (value->pixel mapping only; paint never recomputes — pitfall 2 honored by construction).
- `build_scene(modes, fwhm=...)` is ready for plan 07-08's tab to pass `setup_logic.DEFAULTS['broadening_fwhm']` read LIVE (never re-pinned here).
- Owner-signable items queued for the 07-06/07-10 checkpoints: ascending-axis convention (descending is a v2 data-only flip) and the no-FWHM v1 scope.
- No blockers or concerns.

---
*Phase: 07-spectra-ui*
*Completed: 2026-09-26*
