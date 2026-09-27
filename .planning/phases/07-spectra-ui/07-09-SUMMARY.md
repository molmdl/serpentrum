---
phase: 07-spectra-ui
plan: 09
subsystem: ui
tags: [pymol, qt, qtablewidget, cgo, spectra, xtb, mode-vectors]

# Dependency graph
requires:
  - phase: 07-spectra-ui
    provides: "07-01 pure seams (freq_label/table_rows/mode_arrow_primitives), 07-03 bridge seams (load_mode_arrows/load_xtbopt/zoom_mode_frame/delete_object/object_exists), 07-08 single-source Spectrum stored on the tab"
provides:
  - "SPECTRA-05 frequency table: every parsed mode listed via the shared freq_label convention (negatives '-31.9i', zero-intensity '%.4g' distinct) at the pinned layout index 2"
  - "row-click -> static mode vectors on the OPTIMIZED frame (srp_xtbopt): replace-per-click srp_mode_vec arrows (FROZEN cgo_build.mode_arrows, scale=1.0), once-per-record load + one-shot zoom (pitfall 14)"
  - "clear-line refusals for every degenerate state (no spectrum, missing xtbopt, vibspectrum-only parse, vanished srp_ objects)"
affects: [07-10-consolidated-human-verify, phase-8]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "single-source parse drives ALL surfaces: table row r <=> spectrum.modes[r] from the ONE 07-08 Spectrum (index desync structurally impossible)"
    - "once-per-record viewer overlay guards (snake_id-latched load + zoom) — never per click"

key-files:
  created: []
  modified: [serpentrum/gui_spectra.py]

key-decisions:
  - "Vectors draw on the OPTIMIZED frame (srp_xtbopt): g98 Standard-orientation == xtbopt within 1e-6 A (probe), game frame wrong by up to 0.14 A; status line states the frame explicitly (owner sign-off at 07-10)"
  - "Task-1 handler stub: cellClicked wired in Task 1 needs a safe _on_table_cell_clicked stub so any dialog construction (smoke 02) can't AttributeError before Task 2 implements the draw"

patterns-established:
  - "Spectrum-tab surfaces consume spectra_ui pure builders ONLY (no label/row re-derivation in the GUI)"
  - "viewer overlay lifecycle = snake_id latch + guarded deletes (object_exists) — srp_ objects may legitimately vanish mid-life (cleanup_srp/restart)"

# Metrics
duration: 1h 54m (incl. two full headless smoke legs + direct smoke 13 on Windows PyMOL)
completed: 2026-09-27
---

# Phase 7 Plan 9: Frequency Table + Row-Click Mode Vectors Summary

**SPECTRA-05 complete end-to-end: every parsed mode in a read-only QTableWidget (shared '-31.9i' / '%.4g' conventions), a row click drawing that mode's uniform-length displacement arrows on the optimized structure (srp_xtbopt) via the BRIDGE — replace-per-click, once-per-record load/zoom, clear-line refusals everywhere.**

## Performance

- **Duration:** 1h 54m (dominated by two full headless smoke legs + the direct smoke-13 re-run on Windows PyMOL via cmd.exe)
- **Started:** 2026-09-27T09:26:24Z
- **Completed:** 2026-09-27T11:20:49Z
- **Tasks:** 2/2
- **Files modified:** 1

## Accomplishments

- Frequency table at the pinned layout index 2 (stretch 2): 3 read-only columns, SelectRows/SingleSelection, populated ONLY from `self._spectrum` via `spectra_ui.table_rows` — negatives as '-31.9i', zero-intensity rows visibly distinct from tiny-but-nonzero; clears on every degenerate reset, never fabricates
- `_on_table_cell_clicked`: row r <=> `spectrum.modes[r]` (single-source 07-08 parse — no index desync surface) -> `mode_arrow_primitives` -> FROZEN `cgo_build.mode_arrows(scale=1.0)` -> `load_mode_arrows` as srp_mode_vec, delete-then-load (never accumulates); srp_xtbopt loads once per record (snake_id-guarded), `zoom_mode_frame` fires once per record (pitfall 14)
- Every refusal path is a clear status line: vibspectrum-only (no displacement vectors), missing xtbopt path, xtbopt load OSError; vanished srp_ objects tolerated via guarded deletes/zooms

## Task Commits

1. **Task 1: frequency table — widget, populate, pinned layout insert** — `4963f91` (feat)
2. **Task 2: row-click -> mode vectors on the optimized frame (once-per-record overlay)** — `f8bd312` (feat)

**Plan metadata:** the `docs(07-09): complete frequency table + mode vectors plan` commit (git log; task commits `4963f91` + `f8bd312` immediately precede it)

## Files Created/Modified

- `serpentrum/gui_spectra.py` — table widget + `_populate_table` + `_on_table_cell_clicked` + once-per-record guards `_xtbopt_snake_id`/`_zoomed_snake_id`; layout docstrings to FINAL order status[0]/log[1]/table[2]/plot[3]/buttons[4]; imports extended with `cgo_build` + `pymol_bridge` (GUI->BRIDGE precedent)

## Decisions Made

- **Task-1 click-handler stub** — the plan wires `cellClicked` in Task 1 but implements the handler in Task 2; a committed stub (`pass` + docstring) prevents a runtime AttributeError for any dialog construction in between (Rule 3-adjacent staging necessity, tracked below as a planned-staging note rather than a deviation).
- No other decisions — plan executed as written (frame interpretation, scale pin, guard shapes all verbatim from the plan/research).

## Deviations from Plan

None — plan executed exactly as written. (The Task-1 stub is the plan's own wiring order made runtime-safe; Task 2 replaced it verbatim with the planned handler.)

## Issues Encountered

- AST assertion script initially hit `ast.get_source_segment` (python3.8+; the binding shell is 3.6.9) — switched to lineno-based slicing; and the docstring's own "NO pymol.cmd / direct PyQt5 is banned" prose tripped naive greps, so the ad-hoc AST check targets actual imports/usage (gate 2 purity remains the authoritative check — PASS). No impact on shipped code.

## Gate Results

- `python3.6 tests/run_gates.py`: **all gates green** (gate 1 syntax + plugin-path safety PASS; gate 2 purity AST PASS; gate 3 scoped unittest **840 tests, OK**)
- `python3.6 tests/run_gates.py --smoke`: **all required smokes SMOKE-OK** (01/03/04/05/06/07/08/10/12/13; 12 = SMOKE-OK PLOT-RENDER, 13 = SMOKE-OK MODE-ARROWS); informational smoke 02 dialog FAIL is the known non-blocking 01-05 offscreen-Qt dead end, unchanged
- Direct smoke 13 from repo root (`cmd.exe /c C:\src\run-conda-pymol.bat -cq smoke\13_mode_arrows_smoke.py`): **flushed SMOKE-OK MODE-ARROWS** — the seams 07-09 consumes are unchanged
- Ad-hoc AST audit (python3.6): table constructed 3-column + NoEditTriggers + SelectRows, `cellClicked.connect(self._on_table_cell_clicked)` wired, `_populate_table` sources `spectra_ui.table_rows` only, handler references mode_arrow_primitives / cgo_build.mode_arrows / the three bridge seams with snake_id guards and scale=1.0 pinned — **AST-OK task1 / AST-OK task2**

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- SPECTRA-05 user path exists end-to-end; the LIVE click->vector behavior and the optimized-frame interpretation are the human-verify content of the **07-10 consolidated checkpoint (owner sign-off)** — if the owner amends the frame interpretation, the only edits are the handler's load target + its status line.
- Phase 7 at 9/10; only 07-10 (consolidated human-verify) remains.

---
*Phase: 07-spectra-ui*
*Completed: 2026-09-27*
