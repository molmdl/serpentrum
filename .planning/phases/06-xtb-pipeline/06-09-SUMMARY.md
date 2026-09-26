---
phase: 06-xtb-pipeline
plan: 09
subsystem: ui
tags: [qt, pymol.Qt, xtb, spectra, launch-pipeline, budget-guard, async-runner]

# Dependency graph
requires:
  - phase: 05-stacking-game-rules
    provides: frozen last_run record ({'result','molecules_stacked','atoms_total','chain_objects','snake_id'}) + model-A spectra_requested signal (05-15)
  - phase: 06-xtb-pipeline (06-01/06-04/06-05/06-06)
    provides: budget_guard PURE re-check, XtbRunController + anchor.spectra_run record, GameTab.log_external + last_run['snake_xyz']
provides:
  - user-reachable Get Spectra launch pipeline in PluginDialog._on_spectra_requested (counts re-check -> guard warnings -> binary resolve -> disarm -> async start)
  - Phase-6 Spectra placeholder control surface (status label, bounded log, contextual Cancel/Run-again button) wired to the runner's signals
  - create-or-reuse anchor.spectra_runner ownership with dialog-scoped _runner_connected once-guard
affects: [07-spectra-display, 06-12-checkpoint]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Launch API interposed inside the model-A composition-root slot (signal contract untouched; the SLOT extends, never the signal)"
    - "Dialog-scoped runner-wiring guard (_runner_connected): anchor-owned controller outlives the dialog; reload reconnects the NEW dialog's slots fresh"
    - "Two-channel logging (EQ-ux-2): every launch/verdict line -> spectra status area AND game_tab.log_external; runner log_line stream -> spectra log only"

key-files:
  created: []
  modified:
    - serpentrum/gui.py

key-decisions:
  - "Run-again re-enters the FULL pipeline via _on_spectra_requested (setCurrentIndex(2) is a no-op on that page) so every re-check holds on every relaunch; NEVER _launch_spectra_run with stale values (SC4)"
  - "Cancel-leg status compare uses the 'running' literal (mirrors xtb_run.RUNNING) instead of importing the pure state module the plan did not sanction for the GUI"
  - "Status label soft-capped at 12 lines (oldest dropped) so repeated launches cannot grow it unboundedly; log area bounded via document maximumBlockCount=200"

patterns-established:
  - "Placeholder-surface pattern continued: Phase-6 affordances ship as a replaceable placeholder page; Phase 7 replaces page CONTENT while signal + launch contracts survive"

# Metrics
duration: 10min
completed: 2026-09-26
---

# Phase 6 Plan 09: Launch Pipeline Summary

**Get Spectra now runs the full Phase-6 pipeline — head-inclusive counts re-check, budget_guard warnings logged before launch, SETUP-05 binary resolution, Get-Spectra disarm, async XtbRunController start on a fresh %TEMP% run dir — surfaced on a temporary Spectra placeholder page (status label, bounded streaming log, contextual Cancel/Run-again button) with every refuse path emitting a specific clear line.**

## Performance

- **Duration:** 10 min
- **Started:** 2026-09-26T15:26:46Z
- **Completed:** 2026-09-26T15:36:27Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments

- `_on_spectra_requested` interposed with the complete launch pipeline (SPECTRA-02/06): `setCurrentIndex(2)` stays FIRST (model-A / locked decision 9 — the signal contract is untouched, only the slot extends), then anchor guard (`'plugin state unavailable - reopen the plugin'`) -> `last_run`/`snake_xyz` refuse (`'no completed snake to run - play a game to completion first (Get Spectra activates on win or crash)'`) -> head-inclusive counts via `xyzio.read_xyz_text` (`atoms_engine = len(atoms)`; `last_run['atoms_total']` head-excluded, never used) with `XyzError` surfacing verbatim as `'run input is corrupt: <exc>'` (SC3) -> viewer cross-check via `pymol_bridge.chain_atom_counts` over the frozen `chain_objects` -> `budget_guard.launch_counts_line` + `launch_budget_warnings` logged BEFORE any launch (SC4, EQ-guard-2 log-lines-only) -> `xtbenv.detect_binary(setup['xtb_path'])` with the configured-path user seam (None -> `'xtb not found - set the xtb path on the Setup tab (auto-detect found nothing)'`, Get Spectra stays enabled) -> disarm Get Spectra (launch API owns the disarm, Q5 re-entrancy) -> async launch.
- `_launch_spectra_run` create-or-reuses `anchor.spectra_runner` (`xtb_runner.XtbRunController(anchor)`, narrow ownership, no module-level state), wires signals once via the dialog-scoped `_runner_connected` guard (NOT anchor-scoped: reload builds a new dialog that reconnects fresh), and starts the run with `tempfile.gettempdir()` evaluated INSIDE Windows PyMOL plus the frozen record's `snake_id`; a refused `start()` re-enables Get Spectra + notes `'xtb run did not start (see log)'`.
- `_build_spectra_placeholder` (EQ-ux-1): status `QLabel` (wordwrap, initial hint + 'complete a game, then press Get Spectra on the Game tab', soft-capped at 12 lines), read-only `QTextBrowser` log bounded to 200 blocks, and a contextual `QPushButton` ('Cancel xtb run' while running / 'Run again' on any terminal branch, disabled until first launch). Runner slots: `started` -> `'xtb running... (async - the dialog stays responsive)'` + arm cancel; `log_line` -> stream into the log; `run_finished(status, problems)` -> `'xtb finished: %s'` (+ problems joined '; '), re-enable Get Spectra, flip button to Run again (SC2). Run-again re-enters the FULL pipeline (never stale values); every launch/verdict line also mirrors into the game info box via `game_tab.log_external` (EQ-ux-2).

## Task Commits

Each task was committed atomically:

1. **Task 1: Placeholder page rebuild — status, log, Cancel/Run-again** — `fafa579` (feat)
2. **Task 2: Launch pipeline interpose in `_on_spectra_requested`** — `e4ccf40` (feat)

**Plan metadata:** `pending` (docs: complete launch pipeline plan)

## Files Created/Modified

- `serpentrum/gui.py` — sole file in scope: `_build_spectra_placeholder`, `_log_spectra_line` (two-channel, 12-line cap), `_connect_runner` + runner slots (`_on_runner_started`, `_on_runner_log_line`, `_on_run_finished`), `_on_spectra_run_button`, extended `_on_spectra_requested` (6 pipeline legs), `_launch_spectra_run`; anchor stored as `self._anchor` (was previously only forwarded, never stored); module imports gained `tempfile` (stdlib) + intra-package `budget_guard/pymol_bridge/setup_logic/xtb_runner/xtbenv/xyzio` (relative imports are purity-exempt) + `pymol.Qt.QtCore` (AlignRight).

## Decisions Made

Beyond the plan-locked ones, two deliberate in-scope mechanics:

- **No `addStretch(1)` in the new page layout** — the cancel/run-again button is right-aligned via `QVBoxLayout.addWidget(btn, 0, QtCore.Qt.AlignRight)` so the plan's `grep addStretch(1)` audit keeps the reserved bottom row (and the pre-existing generic-placeholder rows) byte-identical; requires `QtCore` (pymol.Qt, purity-legal).
- **Shared `_NO_SNAKE_LINE` module constant** — the identical refuse text is used by the launch pipeline's step 2 and the Run-again button's no-snake leg, so the two SEAMs can never drift (hud_test drift-pin precedent).

## Deviations from Plan

None - plan executed exactly as written.

(The `self._anchor = anchor_state` store in `__init__` and the `_STATUS_MAX_LINES` soft cap are spelled out by the plan's own pipeline (`self._anchor.setup`, `self._anchor.last_run`, `self._anchor.spectra_runner`) / bounded-line requirements — implementation, not deviation.)

## Issues Encountered

None. One self-inflicted verification hiccup: an AST order-check initially flagged `setCurrentIndex(2)` placement because it forgot the method docstring counts as `body[0]`; the check, not the code, was wrong (re-ran with docstring skip -> pass).

## Gate Results

- `python3.6 tests/run_gates.py` — green after Task 1 and after Task 2 (gates 1-3 PASS each time); final re-run green.
- Full suite: `python3.6 -m unittest discover -s tests` = **785 tests, OK** — baseline unmodified (no test edits anywhere in this plan).
- AST audits (passed): `PluginDialog` defines `_build_spectra_placeholder`, `_connect_runner`, `_on_spectra_run_button`, `_on_run_finished`; zero `.exec_()` calls; `_on_spectra_requested` calls `_launch_spectra_run` and references `budget_guard` + `detect_binary` + `chain_atom_counts` + `read_xyz_text`; `setCurrentIndex(2)` is the first executable statement; `_launch_spectra_run` uses `XtbRunController`, `tempfile.gettempdir()`, `anchor.spectra_runner`.
- Grep audits (passed): `grep -c "exec_"` == 0; `grep -c "spectra_requested.connect"` == exactly 1 (GameTab connect line unchanged); `grep -n "addStretch(1)"` shows the reserved bottom row `:117` untouched (only pre-existing generic-placeholder rows `:106/:108` alongside); no `/mnt/c` at runtime (one docstring mention of the anti-pattern only).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Live end-to-end GUI behavior (launch / cancel / relaunch in the real viewer) belongs to the **06-12 checkpoint** — this plan's bar was structural green + AST-verified wiring, and both hold.
- **06-12 / Phase 7 consumers:** `anchor.spectra_run` (frozen key set `xtb_run.SPECTRA_RUN_KEYS`) is written by the controller's terminal branch; the Spectra placeholder page CONTENT is replaceable wholesale — the runner signal contract (`started`, `log_line`, `run_finished`) and `_launch_spectra_run` survive.
- For the 06-12 human run: Get Spectra arms ONLY after a completed game (presenter-only enable, 05-15); over-budget default win snakes log warn-and-proceed lines (never a block); cancel mid-run resolves as `'xtb finished: cancelled'` + 'Run again'.

---
*Phase: 06-xtb-pipeline*
*Completed: 2026-09-26*
