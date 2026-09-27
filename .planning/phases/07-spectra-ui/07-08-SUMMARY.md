---
phase: 07-spectra-ui
plan: 08
subsystem: ui
tags: [pymol, qt, spectra, ir-plot, gui, pure-seam]

# Dependency graph
requires:
  - phase: 06-xtb-pipeline
    provides: frozen spectra_run record (xtb_run.SPECTRA_RUN_KEYS / DONE-FAILED-CANCELLED) + stable artifact paths (SRP_SPECTRA_DIR || <cwd>/srp_spectra)
  - phase: 07-spectra-ui (07-02/05/06/07)
    provides: plot_logic.build_scene, human-approved SpectraPlotPanel (embedded AS-IS), SpectraTab shell with pinned layout indices
provides:
  - SpectraTab plot feed — run_finished / reload -> record_spectrum_paths -> spectra.parse -> plot_logic.build_scene (live fwhm) -> panel.set_scene
  - spectra_ui.record_spectrum_paths pure helper (g98-first display precedence, degenerate-matrix testable)
  - self._spectrum single-source parse retained for 07-09's table/vector reuse
affects: [07-09 table+vectors (consumes self._spectrum / self._spectrum_note + insert-index-2 contract), 07-10 consolidated human-verify]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Pure selection seam: record->(paths, source) in spectra_ui; filesystem checks + parse stay in the GUI tab (degenerate matrix unit-testable)"
    - "Live-read runtime constants: fwhm from anchor.setup with setup_logic.DEFAULTS fallback at populate time (never re-pinned; 06-09 atom_budget precedent)"

key-files:
  created: []
  modified:
    - serpentrum/gui_spectra.py
    - serpentrum/spectra_ui.py
    - tests/test_spectra_ui.py

key-decisions:
  - "record_spectrum_paths is pure selection ONLY (no os.path.isfile) — existence checks stay in the tab so the whole degenerate matrix is unit-testable"
  - "reflect_run_state inherits the plot refresh through on_run_finished -> _refresh_from_record (single code path; no double-parse on reload)"

patterns-established:
  - "Degenerate-record rule: failed/cancelled/None-path/missing-file/corrupt-file -> empty plot + clear status line; nothing fabricated, nothing crashes (Phase-6 SC3)"

# Metrics
duration: 9 min
completed: 2026-09-27
---

# Phase 7 Plan 08: SpectraTab Plot Embed & Record→Scene Feed Summary

**The human-approved SpectraPlotPanel is live inside the Spectra tab: a finished 'ok' run parses the record's g98 (vibspectrum fallback, live-fwhm Scene build) and the player's broadened IR spectrum appears on the tab — SPECTRA-03's on-screen half is wired.**

## Performance

- **Duration:** 9 min
- **Started:** 2026-09-27T09:04:22Z
- **Completed:** 2026-09-27T09:13:12Z
- **Tasks:** 2/2
- **Files modified:** 3

## Accomplishments

- **Panel embedded AS-IS** — `SpectraPlotPanel(self, status_cb=self.set_status_line)` constructed in `_build_widgets`, added at the pinned layout index 2 (stretch 3; status[0] / log[1] / PANEL[2] / buttons[3]); the 07-09 insert-table-at-2 contract preserved in both docstrings. Zero changes to the human-approved `gui_plot.py`.
- **Record→Scene feed with guards** — `_populate_spectrum(record)`: g98-first parse (it alone carries vectors + atom block), vibspectrum fallback filtered through `spectra.real_modes` with the explicit `'showing vibspectrum - no displacement vectors available (table only)'` status note; `SpectraParseError`/`OSError`/`ValueError` caught → empty plot + `'spectrum could not be read: <exc>'` line; fwhm read LIVE from `anchor.setup['broadening_fwhm']` with `setup_logic.DEFAULTS` (16.0) fallback on absent/invalid — never re-pinned.
- **Wiring** — `on_run_finished` now calls `_refresh_from_record(record)` after the (byte-identical) status/button updates; `reflect_run_state`'s terminal branch inherits the refresh through the same call, so a plugin reload / dialog reopen after a completed 'ok' run repopulates the plot from the anchored record. Degenerate terminal records reset `self._spectrum = None` + `set_scene(None)`.
- **Pure seam** — `spectra_ui.record_spectrum_paths(record)` → `(g98_path, vibspectrum_path, source)` ('g98' / 'vibspectrum' / 'none'), filesystem-free; `TestRecordSpectrumPaths` pins the ok / fallback / degenerate / empty-dict matrix (836 → 840 unittests).
- **Single-source parse** — `self._spectrum` (+`self._spectrum_note`) retained on the tab for 07-09's table/vector reuse; index desync structurally impossible (research Q4d).

## Task Commits

Each task was committed atomically:

1. **Task 1: embed SpectraPlotPanel + populate flow + guards** — `a87873f` (feat)
2. **Task 2: record_spectrum_paths pure seam + tab rewire** — `3d784a7` (feat)

**Plan metadata:** see final docs commit (`docs(07-08)`).

## Files Created/Modified

- `serpentrum/gui_spectra.py` — panel embed + `_populate_spectrum`/`_refresh_from_record` feed + guards + layout pin (index 2, stretch 3); today section of both docstrings updated
- `serpentrum/spectra_ui.py` — `record_spectrum_paths` pure helper + docstring entry
- `tests/test_spectra_ui.py` — `TestRecordSpectrumPaths` (4 cases)

## Decisions Made

- **`record_spectrum_paths` is filesystem-free** — pure selection only; `os.path.isfile` existence checks stay in the tab (plan-pinned). Keeps the degenerate matrix (ok / g98-missing-but-vibs / both-None / empty dict) unit-testable without fixtures.
- **Reload repopulates through the single `on_run_finished` path** — `reflect_run_state`'s terminal branch already delegates there; `_refresh_from_record` was hung off that one slot rather than duplicating a populate call (avoids a double parse).
- **`_spectrum_note` pre-staged for 07-09** — the vibspectrum fallback note is stored so the table plan can echo it without re-deriving.

## Deviations from Plan

None - plan executed exactly as written. (`gui_plot.py` untouched per the 07-06 approval; `gui.py` untouched per the single-writer note.)

## Issues Encountered

None — gates green first pass; the only hiccup was my own AST smoke check matching the docstring's "NO pymol.cmd" sentence, resolved by tightening the check to import/use tokens.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **07-09 unblocked** — consumes `self._spectrum` (Spectrum namedtuple; vibspectrum fallback carries `atoms=[]`/empty vectors, note in `self._spectrum_note`); layout insert-at-index-2 contract documented in both gui_spectra docstrings.
- **Live-run human-verify pending** — the real `run_finished → plot appears` leg (plus Save Plot through the embedded panel) is scheduled for the 07-10 consolidated checkpoint, as planned. Gate state for that leg: 840 unittests + all required smokes (incl. 12 PLOT-RENDER, 13 MODE-ARROWS) green at `3d784a7`.
- No blockers.

---
*Phase: 07-spectra-ui*
*Completed: 2026-09-27*
