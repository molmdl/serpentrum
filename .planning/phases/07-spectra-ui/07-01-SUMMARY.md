---
phase: 07-spectra-ui
plan: 01
subsystem: ui
tags: [spectra, pure-logic, tdd, python3.6, xtb, g98, vibspectrum, ir-spectrum]

# Dependency graph
requires:
  - phase: 06-xtb-pipeline
    provides: frozen spectra_run record vocabulary (xtb_run.DONE/FAILED/CANCELLED, SPECTRA_RUN_KEYS) — 06-02 handoff contract
  - phase: 02-name (spectra core)
    provides: spectra.py Mode/Spectrum/Atom namedtuples, parse_g98/parse_vibspectrum/real_modes; frozen cgo_build.mode_arrows consumer contract
provides:
  - serpentrum/spectra_ui.freq_label — THE single imaginary-convention frequency formatter ('-31.9i', ASCII minus) for the whole Spectra UI
  - serpentrum/spectra_ui.table_rows — every-mode (index, freq_label, '%.4g' intensity) rows, zero-intensity rows kept distinct from tiny-but-nonzero
  - serpentrum/spectra_ui.mode_arrow_primitives — total 1-based mode -> (atoms, vectors) selector (None, never an exception) for frozen cgo_build.mode_arrows
  - serpentrum/spectra_ui.run_status_lines — verdict lines built solely from the frozen record vocabulary (never re-scans log text)
affects: [07-02 (plot_logic imports NO formatter by coordination), 07-07..07-09 (GUI wiring consumes these builders), any future plot caption printing a frequency]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Pure-half module per GUI family: every string/index decision lives in serpentrum/spectra_ui.py (PURE, auto-classified, no registration) so GUI modules 07-07..07-09 stay thin wiring"
    - "Single shared formatter discipline: freq_label exists exactly once; plot half (07-02) deliberately imports no formatter"

key-files:
  created:
    - serpentrum/spectra_ui.py
    - tests/test_spectra_ui.py
  modified: []

key-decisions:
  - "freq_label home = spectra_ui.py; ASCII hyphen-minus pinned in code (REQUIREMENTS keeps U+2212 as prose display convention) — 07-RESEARCH-qt-plot.md [TRAIN] 2 glyph risk"
  - "Intensity label precision '%.4g': keeps 0.00026-class vibspectrum values visible; exact 0.0 renders '0' (SPECTRA-05 zero-intensity distinction)"
  - "table_rows accepts Spectrum OR bare Mode iterable (real_modes() returns a list, not a Spectrum) — plan's own test spec required the dual input"
  - "run_status_lines output shape: ['xtb finished: %s'] + optional 'problems: p1; p2' line — derived only from frozen record vocabulary, never log re-scan"

patterns-established:
  - "Cross-half coordination documented in module docstring: plot_logic.py (07-02) imports no frequency formatter; future plot frequency text MUST import freq_label"
  - "Accepted-limitation docstring block: missing co2 g98 fixture documented in-module (linear g98 leg = smoke-only behind --xtb), no invented fixture"

# Metrics
duration: 7min
completed: 2026-09-26
---

# Phase 07 Plan 01: Spectra UI Pure Half Summary

**PURE Spectra-UI builders TDD'd in python3.6: the single imaginary-convention freq_label ('-31.9i' ASCII), every-mode table_rows with '%.4g' intensity labels, a total mode_arrow_primitives selector (None never exception), and run_status_lines pinned to the frozen 06-02 record vocabulary.**

## Performance

- **Duration:** 7 min
- **Started:** 2026-09-26T17:42:23Z
- **Completed:** 2026-09-26T17:49:33Z
- **Tasks:** 2 (TDD RED + GREEN)
- **Files modified:** 2 created, 0 modified

## Accomplishments

- The ONE imaginary-convention frequency formatter exists exactly once, in `serpentrum/spectra_ui.freq_label` — negative freqs render '-31.9i' (ASCII hyphen-minus), non-negatives plain '%.1f'; the module docstring pins the coordination rule that any future plot frequency text must import it (07-RESEARCH-qt-plot.md pitfall 10 drift risk dead at the source).
- `table_rows` lists every spectrum mode in file order — negatives and zero-intensity included — with '%.4g' intensity labels that keep the 0.00026 class distinct from exact zero ('0'); proven end-to-end on the committed g98 fixture (72 rows) and the synthetic co2 vibspectrum (exactly one '0' row: the IR-inactive symmetric stretch).
- `mode_arrow_primitives` is total: returns (atoms, vectors) as plain float tuples for a valid 1-based index, and None — never an exception — for vibspectrum parses, empty atom lists, and out-of-range indices; fixture-pinned against g98 mode 1 and mode 5 element-wise.
- `run_status_lines` builds verdict text solely from the frozen record vocabulary (xtb_run.DONE/FAILED/CANCELLED imported, never re-pinned); the never-re-scan-the-log rule is pinned by a test whose record carries a nonexistent 'log_path'.
- Gates: 812 unittests green (796 baseline + 16 new), syntax/plugin-path/purity gates green.

## Task Commits

Each task was committed atomically:

1. **Task 1: RED — failing tests for spectra_ui** — `42b7cea` (test)
2. **Task 2: GREEN — implement serpentrum/spectra_ui.py** — `6b30e29` (feat)

## Files Created/Modified

- `serpentrum/spectra_ui.py` (created, 140 lines) — PURE Spectra-UI builders: freq_label, table_rows, mode_arrow_primitives, run_status_lines; stdlib + `from . import xtb_run` only; auto-classified PURE (no check_purity registration). Docstrings carry the shared-formatter coordination note and the accepted no-co2-g98-fixture limitation.
- `tests/test_spectra_ui.py` (created, 187 lines) — fixture-anchored pins: house header (sys.path self-insert, no __init__.py, %-formatting); g98.out anchors probed pre-write (modes 1-3 = -31.9175/-23.0766/-18.1086; peak = 1150.6639 @ 257.1018); co2 vibspectrum end-to-end zero-intensity leg.

## Decisions Made

- **table_rows input duality (deviation 1 below):** the plan's test spec calls `table_rows(spectra.real_modes(spec))` while its implementation spec iterates `spectrum.modes`; real_modes() returns a list. Resolved by accepting both input shapes (documented in the function docstring) — the plan's own test text is the pinned behavior.
- All other behaviors followed the plan as specified (ASCII minus, '%.4g', status-line shape, None-totality).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] str.isascii() is Python 3.7+; the binding gate is python3.6**

- **Found during:** Task 1 (RED — writing TestFreqLabel.test_ascii_only)
- **Issue:** The plan's test spec asserts `.isascii()` on formatter output; `str.isascii` does not exist on python3.6 (module-level probe confirmed) — the test file would fail to run on the binding interpreter for a spurious reason, not the intended ImportError RED.
- **Fix:** Added a module-level `_is_ascii(text)` helper (`all(ord(ch) < 128 ...)`) in the test file with a comment naming the 3.7+/3.6 split; kept an explicit `assertNotIn(u'\u2212', ...) ` pin for the U+2212 glyph. Semantics identical to the plan's intent.
- **Files modified:** tests/test_spectra_ui.py
- **Verification:** RED surfaced as the intended ImportError; GREEN suite runs clean on python3.6 (16/16).
- **Committed in:** 42b7cea (Task 1 RED commit)

**2. [Rule 1 - Bug] Plan spec self-inconsistent: table_rows(spectra.real_modes(spec)) vs iterating spectrum.modes**

- **Found during:** Task 2 (GREEN — test_co2_vibspectrum_end_to_end failed with AttributeError: 'list' object has no attribute 'modes')
- **Issue:** `spectra.real_modes()` returns a plain list of Mode (spectra.py:402-418), not a Spectrum; the plan's implementation one-liner `[(...) for m in spectrum.modes]` cannot serve the plan's own end-to-end test call.
- **Fix:** `table_rows` accepts a Spectrum (iterates `.modes`) or a bare Mode iterable (`modes = spectrum.modes if hasattr(spectrum, 'modes') else spectrum`); docstring documents both accepted shapes and why.
- **Files modified:** serpentrum/spectra_ui.py
- **Verification:** test_co2_vibspectrum_end_to_end green; all 16 file tests + full 812-test gate green.
- **Committed in:** 6b30e29 (Task 2 GREEN commit)

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug)
**Impact on plan:** Both auto-fixes were necessary to make the plan's own pinned tests executable on the binding python3.6 interpreter; no scope creep, no changed behaviors beyond what the plan's test text already pinned.

## Issues Encountered

None beyond the deviations above — fixture anchors (g98 modes 1-3, peak mode, co2 real-mode triple) probed and confirmed before test-writing, so RED/GREEN cycled without rework.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `serpentrum/spectra_ui.py` is ready for consumption by 07-02 (plot_logic — imports no formatter by coordination), 07-07 (status-line slot rewiring: replaces the 06-09 placeholder's inline join), and 07-09 (table widget rows + row-click arrow primitives).
- The accepted fixture gap stands: the linear-molecule (co2) g98 leg remains smoke-only behind the real-xtb `--xtb` gate; if a later wave runs real co2 through xtb it may elect to commit a genuine co2 g98.out fixture and strengthen these pins.
- Merge note for orchestrator: this branch touches ONLY `serpentrum/spectra_ui.py` + `tests/test_spectra_ui.py` (disjoint from the wave's other plans); no STATE.md edit (orchestrator-owned this wave).

---
*Phase: 07-spectra-ui*
*Completed: 2026-09-26*
