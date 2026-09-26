---
phase: 06-xtb-pipeline
plan: 06
subsystem: ui
tags: [pymol-plugin, pyqt5, xtb, handoff-seam, xyz, completion-flow, SPECTRA-02]

# Dependency graph
requires:
  - phase: 05-stacking-game-rules
    provides: 05-15 frozen last_run five-key consumption contract + _present_completion anchor site; session['head_atoms'] pure mirror (05-11) maintained through moves/sweeps
  - phase: 06-xtb-pipeline
    provides: 06-02 xtb_run.build_run_input (head-first, engine-order segment atoms, xyzio.write_xyz, ValueError on head None)
  - phase: 05.2-generic-stacking
    provides: 5.2-09 wrap ordering gui_game.py shared-file discipline (5.2-06 consent edits landed first)
provides:
  - last_run['snake_xyz']: head-inclusive engine-atom run-input xyz text anchored at completion (single write, engine alive, reload-safe, never a PyMOL re-read - EQ-xyz-1)
  - explicit snake_xyz None data state when session['head_atoms'] is None (the launch API's refuse path)
  - GameTab.log_external(msg) public info-box channel for the Phase-6 launch API
affects: [06-xtb-pipeline plans 06-09 (launch API consumes snake_xyz + log_external), 06-10 (integration chain), 06-12 (live atom-count consistency checkpoint), 07-spectra-ui]

# Tech tracking
tech-stack:
  added: []
  patterns: [explicit value-branch over exception-driven flow at a contract seam (no try/except theater), additive extension of a frozen anchor record, public-wrapper line channel to keep GUI privates private]

key-files:
  created: []
  modified:
    - serpentrum/gui_game.py

key-decisions:
  - "snake_xyz assembled in _present_completion from the session/engine atom truth while the engine is still alive - NEVER re-read from PyMOL (05-RESEARCH-core-integration:151)"
  - "head_atoms None is an explicit data state (snake_xyz = None), not an exception path: build_run_input's ValueError never fires at the seam; the 06-09 launch API refuses with a clear log line"
  - "the 05-15 frozen last_run contract is EXTENDED additively: the five existing keys byte-unchanged, 'snake_xyz' appended; presenter-only Get Spectra enable untouched (AST-asserted exactly once)"

patterns-established:
  - "EQ-xyz-1 completion seam: head_atoms FIRST then engine-order seg['atoms'] -> build_run_input -> anchored record key"
  - "log_external: one-line non-reason info-box lines from EXTERNAL stages (the _log coalescer break is correct because the run is over)"

# Metrics
duration: 4 min
completed: 2026-09-26
---

# Phase 6 Plan 6: snake_xyz Handoff + log_external Channel Summary

**_present_completion now anchors the launch-ready SPECTRA-02 handoff: `last_run['snake_xyz']` holds the head-inclusive engine-atom xyz run-input text (built by `xtb_run.build_run_input` from the pure head mirror + live segment atoms, never re-read from PyMOL), with an explicit `None` refusal state, and GameTab gains the public `log_external` info-box channel for the Phase-6 launch API.**

## Performance

- **Duration:** 4 min
- **Started:** 2026-09-26T14:21:22Z
- **Completed:** 2026-09-26T14:25:22Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- EQ-xyz-1 seam wired in `_present_completion` (gui_game.py): `head_atoms = session['head_atoms'] if session is not None else None`; when available, `snake_xyz = xtb_run.build_run_input(head_atoms, [seg['atoms'] for seg in engine.segments], 'run_%d' % session['epoch'])` — head atoms FIRST, then each segment's live `(sym, x, y, z)` atoms in engine order (game_engine keeps them fresh per tick, :519-552); else the explicit branch sets `snake_xyz = None` (no try/except theater — `build_run_input`'s ValueError for a None head mirror never fires; the 06-09 launch API refuses on None with a clear line).
- The 05-15 frozen `last_run` contract EXTENDED additively: `'snake_xyz': snake_xyz` appended to the anchored dict literal with the five existing keys byte-unchanged (`result`, `molecules_stacked`, `atoms_total`, `chain_objects`, `snake_id`; AST-asserted exact ordered key list). Get Spectra lifecycle untouched — `setEnabled(True)` still occurs exactly once, presenter-only (AST-asserted); `atoms_total` and the HUD completion lines are untouched (snake_xyz is the head-inclusive truth; the HUD label stays as pinned by test_hud_content.py).
- Docstring item (d) of `_present_completion` extended: the record now carries `snake_xyz` — assembled HERE while the engine is alive, consumed by the Phase-6 runner, None when the head mirror was unavailable, NEVER a PyMOL re-read (05-RESEARCH-core-integration:151).
- New public `GameTab.log_external(msg)` after `_log`/`_log_reason`: wraps `_log` (the coalescer break is correct — these are non-reason messages and the run is over); the Phase-6 launch API (gui.py `_on_spectra_requested`, plan 06-09) surfaces launch counts/warnings/verdicts without reaching into privates.
- Module import `from . import xtb_run` added alongside the pure-sibling imports (purity-legal: GUI may import PURE modules; gate-2 purity PASS).

## Task Commits

Each task was committed atomically:

1. **Task 1: snake_xyz assembly + log_external in gui_game.py** — `616daec` (feat)

**Plan metadata:** pending (this commit)

## Files Created/Modified

- `serpentrum/gui_game.py` — `_present_completion` snake_xyz assembly + `last_run['snake_xyz']` anchor (+docstring item d), `from . import xtb_run` import, new public `GameTab.log_external`. Nothing else touched (no consent code, no teardown/presenter ordering changes, no `__init__.py` — single-writer rule: plan 06-05 owns it).

## Decisions Made

None beyond plan-locked ones — the plan applied the already-verified seam facts verbatim (05-RESEARCH:151 no-re-read rule; build_run_input contract from 06-02; the explicit None branch over exception flow).

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. (Note: line numbers in the plan's context (1289-1333) reflect pre-wave-1 gui_game.py; the method now sits at :1363 after the merged 5.2 wrap — purely informational, zero code impact.)

## Gate Results

- `python3.6 tests/run_gates.py` — green: syntax walk PASS, plugin-path safety PASS, AST purity PASS (gui_game pinned GUI with the new PURE sibling import exempt), 785 unittests OK (all pinned tests untouched-green: test_phase5_integration chain, test_hud_content completion-lines/SPECTRA-budget pins, 5.2 consent pins).
- AST assertion heredoc (the plan's Task-1 step 5) — PASS: `snake_xyz` name + `'snake_xyz'` dict key + `build_run_input` call inside `_present_completion`; exact ordered last_run key list = frozen-five + snake_xyz; `get_spectra_btn.setEnabled(True)` exactly once inside `_present_completion`; `GameTab.log_external` exists and wraps `self._log`; module-level `from . import xtb_run` present.
- `git diff --stat` — exactly `serpentrum/gui_game.py | 44 +++---...`, 41 insertions, 3 deletions. No other file modified.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 06-09 (launch API in gui.py) can now consume `last_run['snake_xyz']` and post its counts/warnings/refuse lines via `GameTab.log_external` — both seams exist with defined data states (xyz text OR None, never an exception).
- The 06-10 integration chain and the 06-12 checkpoint's live atom-count consistency step have their completion-side data source; `build_run_input`'s parseable-output guarantee sits on its own 06-02 pins.
- `serpentrum/__init__.py` last_run docstring update is plan 06-05's (same wave, single-writer rule) — merge-order note for the orchestrator only, no action here.

---
*Phase: 06-xtb-pipeline*
*Completed: 2026-09-26*
