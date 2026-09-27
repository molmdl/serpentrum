---
phase: 07-spectra-ui
plan: 06
subsystem: ui
tags: [pymol.Qt, QPainter, plot, spectra, human-verify, owner-amendment, unit-modes]

# Dependency graph
requires:
  - phase: 07-spectra-ui (plan 07-05)
    provides: "gui_plot IrPlotWidget/paint_scene seam/SpectraPlotPanel/render_image + REQUIRED smoke 12"
  - phase: 07-spectra-ui (plan 07-02)
    provides: "plot_logic pure half — Scene contract, build_scene, size_presets, Y_MAX_FLOOR, nice_ticks"
provides:
  - smoke/manual_plot_check.py — real-GUI plot human-verify harness (PLOT-CHECK-STAGED), now with the round-2 checklist
  - plot_logic.UNIT_MODES + scene_with_unit — pure absorbance (arb., peak=1, Beer-Lambert proportionality) / transmittance (arb., T=10^-A) display transforms
  - gui_plot paint_scene/render_image extended: invert_x (descending wavenumber), invert_y (vertical flip), line_color (r,g,b; None = pinned default #1f4fff)
  - SpectraPlotPanel amended: appearance row (unit/color/x-dir combos + invert-y + labels toggles) + size/save row; exact preset pin (min AND max) fixes the round-1 shrink defect
  - smoke 12 STAGE5 OPTIONS — route-A parity regression for the full option space
affects: [07-spectra-ui plans 07-08..07-10 (SpectraTab embed lives on the amended panel), 08 (help/export surfaces)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Base-scene pattern: panels keep the BASE intensity Scene; displayed Scene is derived per-change via pure scene_with_unit (recompute lives ONLY in the PURE half)"
    - "Exact-size preset pin: setMinimumSize + setMaximumSize to the same (w,h) — deterministic grow AND shrink in a layout; window stays resizable, plot stays preset-sized"
    - "Inverted-axis tick iteration: REVERSE the tick list when the axis flips so drawn pixel positions still ascend and the last-pixel label dodge works unchanged"
    - "Route-A parity contract: render_image forwards the FULL on-screen option state (unit/color/invert) — PNG == screen for any combination"

key-files:
  created: []
  modified: [serpentrum/plot_logic.py, serpentrum/gui_plot.py, tests/test_plot_logic.py, smoke/12_plot_smoke.py, smoke/manual_plot_check.py]

key-decisions:
  - "Owner amendment (checkpoint round 1, 2026-09-26): y-unit modes intensity/absorbance (arb.)/transmittance (arb.), x-direction ascending/descending, y-invert toggle, curve colors blue/red/black — ALL defaults preserve the approved round-1 look; no new REQ ID (SPECTRA-03 v1 surface expansion, 5.3/06-12 precedent)"
  - "Absorbance rationale: xtb IR intensities proportional to absorbance via Beer-Lambert linearity; normalized to peak=1, arbitrary units, honestly labeled '(arb.)'; transmittance = 10^(-A) of the normalized absorbance — no invented physics"
  - "Round-1 defect c (sticky size after shrink) fixed by the exact min/max preset pin, not by layout policy knobs"
  - "Unknown unit modes raise ValueError — loud, never a silent passthrough of the wrong unit"

# Metrics
duration: 11 min (round-2 continuation)
completed: 2026-09-26
---

# Phase 7 Plan 06: Plot Human-Verify Harness Summary

**Real-GUI plot check harness staged (201fd8d), checkpoint round 1 partial-PASS with one defect; owner amendments applied — pure unit-mode transforms (absorbance/transmittance), x-direction/y-invert/line-color options with full PNG parity, and the exact-preset pin that fixes the sticky-size defect; harness re-staged for round 2.**

## Performance

- **Duration:** 11 min (round-2 continuation; round-1 harness task executed in an earlier wave)
- **Started:** 2026-09-27T06:34:10Z
- **Completed:** 2026-09-27T06:45:15Z
- **Tasks:** Task 1 done (harness, 201fd8d); Task 2 = BLOCKING checkpoint — round 1 returned a conditional verdict + four owner directives; the amended panel now awaits round-2 owner re-verification
- **Files modified:** 5 (plot_logic.py, gui_plot.py, test_plot_logic.py, 12_plot_smoke.py, manual_plot_check.py)

## Checkpoint Round 1 Verdict (2026-09-26)

Owner response (verbatim interpretation by the orchestrator):

- **a, b, d, e, f PASS** — curve/labels legible, ascending x axis accepted as-is for now, label toggle works, save works, PNG opens outside PyMOL.
- **c DEFECT** — after switching to a larger preset, switching back to a smaller preset did NOT auto-shrink the plot (manual resize needed).
- **g** unremarked (no defect reported).

Owner amendments (all four applied as binding directives):

1. **Axis inversions covered both ways:** x-direction option (ascending default / descending) AND y-invert option (off default) — defaults unchanged = the approved look.
2. **Unit modes:** y unit selectable — 'IR intensity (km/mol)' (default, unchanged) / 'absorbance (arb.)' / 'transmittance (arb.)', transforms in PURE plot_logic.
3. **Line color:** blue (default) / red / black, flowing through render_image (route-A PNG parity).
4. **Size-shrink fix (defect c):** exact min+max pin per preset — grow AND shrink automatic.

## This Continuation's Commits

1. **RED: TestUnitModes** — `1c811d1` (test) — 7 failing tests for UNIT_MODES/scene_with_unit (24 file tests, 1 failure + 6 errors before GREEN).
2. **GREEN: plot_logic unit modes** — `d4d5e3b` (feat) — UNIT_MODES table + scene_with_unit with Beer-Lambert-documented transforms; one in-cycle fix (mode→label lookup reversed) corrected before commit.
3. **GUI options + defect-c fix** — `8768577` (feat) — paint_scene/render_image invert_x/invert_y/line_color; IrPlotWidget option state + setters; panel two-row layout with base-scene derivation; exact min/max preset pin at construction and on change.
4. **Smoke 12 STAGE5 + round-2 checklist** — `d29c9a3` (test) — options parity leg (transmittance + both inverts + red) flushes a valid PNG; manual harness checklist gains steps h–k.

**Plan metadata:** docs commit below.

## Accomplishments

- Pure unit transforms: `scene_with_unit(scene, mode)` — absorbance normalized to peak = 1 (xtb IR intensities proportional to absorbance via Beer-Lambert linearity; arbitrary units, honestly '(arb.)'); transmittance T = 10^(−A) of the normalized absorbance, T in (0, 1], peaks down at 0.1; zero curve stays zeros (no division-by-zero); ValueError on unknown modes; all non-y Scene fields pass through UNCHANGED (y_max/y_ticks recompute under the build_scene policy).
- GUI options with defaults preserving the approved look: unit combo, color combo (blue = `None` → the pinned `#1f4fff` QPen EXACTLY; red/black via fromRgbF), 'x: ascending'/'x: descending', 'Invert y axis', plus the existing labels toggle; inverted axes iterate ticks REVERSED so the pixel label dodge works unchanged.
- Route-A parity: `render_image`/`paint_scene` signatures carry the full option state — the saved PNG matches ANY on-screen combination (unit, color, both inverts, labels).
- Defect c fixed: `SpectraPlotPanel._on_size_changed` pins BOTH minimum and maximum size to the preset — grow AND shrink automatic; the plot is EXACTLY the chosen preset and extra window space becomes margin (window still resizable). Same pin applied at construction for the default preset.

## Files Created/Modified

- `serpentrum/plot_logic.py` — UNIT_MODES + scene_with_unit (pure unit transforms, Beer-Lambert rationale in the docstrings)
- `serpentrum/gui_plot.py` — extended paint seam, widget option state, two-row panel, exact-size pin, option-state save parity
- `tests/test_plot_logic.py` — TestUnitModes (7 tests; unittest baseline 829 → 836)
- `smoke/12_plot_smoke.py` — STAGE5 OPTIONS (unit/color/invert parity regression); STAGE0..STAGE5 + SMOKE-OK PLOT-RENDER verified on Windows PyMOL
- `smoke/manual_plot_check.py` — round-2 re-verification checklist (steps h–k added); PLOT-CHECK-STAGED

## Decisions Made

- **Owner amendment recorded (no new REQ ID):** SPECTRA-03's v1 surface expanded from 'size + axis-label toggle' to unit modes / x-direction / y-invert / line color — owner-directive expansion with defaults identical to the approved round-1 look (5.3/06-12 amendment precedent).
- **Transmittance honest labeling:** T = 10^(-A) of the NORMALIZED absorbance — the docstrings state exactly what was computed (no invented physics); the y-invert option restores the journal look (peaks up) if wanted.
- **Unknown unit modes raise ValueError** (loud contract — a silent passthrough in the wrong unit would be a correctness bug for a chemistry plot).
- **'blue' maps to line_color=None** so the pinned default QPen (`#1f4fff`) is preserved byte-exactly rather than approximated by an r,g,b tuple.

## Deviations from Plan

The amendments themselves are owner directives, not deviations. One in-cycle bug was fixed before its commit (never shipped):

**1. [Rule 1 - Bug] mode→label lookup reversed in scene_with_unit**
- **Found during:** GREEN task (scene_with_unit implementation)
- **Issue:** `dict(UNIT_MODES)[mode]` maps label→mode, not mode→label — KeyError on 'absorbance'/'transmittance'
- **Fix:** `dict((m, label) for label, m in UNIT_MODES)[mode]`
- **Files modified:** serpentrum/plot_logic.py
- **Verification:** file suite green + the verification probe `1.0 0.1 transmittance (arb.)`
- **Committed in:** d4d5e3b (the GREEN commit itself)

## Issues Encountered

None beyond the above in-cycle fix.

## Next Phase Readiness

- SpectraPlotPanel has the full amended option surface with PNG parity — 07-08's SpectraTab embed inherits it untouched.
- Gates re-verified on the amended surface: 836 unittests green; `python3.6 tests/run_gates.py` green; `--smoke` 10/10 required PASS with smoke 12 STAGE0..STAGE5.
- **BLOCKING:** checkpoint round 2 pending — the owner re-verifies the amended panel via `run smoke\manual_plot_check.py` (steps h–k are the amendment rounds; k covers the defect-c fix and option-state PNG parity). The checkpoint is NOT resolved by the executor.

---
*Phase: 07-spectra-ui*
*Completed: 2026-09-26*
