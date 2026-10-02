# Architecture

**Analysis Date:** 2026-10-02

## Pattern Overview

**Overall:** Pure-core / game-engine with a thin PyMOL + Qt bridge layer, enforced by an AST purity gate.

The architecture is a strict-layered PyMOL plugin split into four module classes that are
**machine-enforced** by `tools/check_purity.py` (run as gate 2 by `tests/run_gates.py`).
Dependency direction is `PURE ← BRIDGE ← GUI/ENTRY`. Pure modules do all math and data
parsing; bridge modules are the only code that calls `pymol.cmd`; GUI modules are the only
code that imports Qt (via `pymol.Qt`, never bare `PyQt5`).

**Key Characteristics:**
- Module class is decided by path in `tools/check_purity.py` (`classify()`), not by
  convention — a new file defaults to the strictest class (PURE) unless deliberately added
  to `GUI_MODULES` / `BRIDGE_MODULES`.
- `serpentrum/__init__.py` is the ENTRY module: stdlib-only at module level, with
  `pymol`/`pmg_tk` imported lazily inside function bodies only (`_anchor()`,
  `__init_plugin__()`, `run_plugin_gui()`).
- The `serpentrum/` package is the installable plugin; dev dirs (`tests/`, `smoke/`,
  `tools/`) are not plugin modules and are never purity-checked.
- Live state anchors on `pmg_tk.startup._serpentrum`, never module globals (reload safety).
- Modeless rule: the main dialog opens via `.show()` only; `.exec_()` is an AST failure.
- All game PyMOL objects live under the reserved `srp_` name prefix; cleanup is by name
  pattern (`pymol_bridge.cleanup_srp`), fresh-process-safe.
- User-visible help/hint strings are single-sourced in the PURE `help_text.py` (DOCS-03);
  GUI modules render them verbatim and never re-derive wording.

## Layers

**ENTRY (`serpentrum/__init__.py`):**
- Purpose: register the plugin menu item and create/show the single modeless dialog.
- Location: `serpentrum/__init__.py`
- Contains: `_anchor()`, `__init_plugin__(app=None)`, `run_plugin_gui()`, the
  `_SerpentrumState` class.
- Depends on: stdlib only at module level; `pymol.plugins.addmenuitemqt` lazily;
  `serpentrum.setup_logic` and `serpentrum.gui` lazily.
- Used by: PyMOL's plugin loader (loads as `pmg_tk.startup.serpentrum`).

**PURE (all other `serpentrum/*.py` not listed as GUI/BRIDGE):**
- Purpose: engine, geometry, parsing, formatting, data loading, decision logic.
- Location: `serpentrum/game_engine.py`, `stacking.py`, `placement.py`,
  `orientation.py`, `plot_logic.py`, `spectra.py`, `spectra_ui.py`, `budget_guard.py`,
  `generic_stack.py`, `setup_logic.py`, `spawn.py`, `molfile.py`, `xyzio.py`,
  `molecule_data.py`, `setloader.py`, `hud_logic.py`, `help_text.py`, `cgo_build.py`,
  `xtb_run.py`, `xtbenv.py`.
- Contains: plain Python functions/classes returning data (tuples, dicts, namedtuples).
- Depends on: stdlib (`math`, `json`, `os`, `random`, `copy`, `collections`) + relative
  intra-package imports of other PURE modules. **Zero** `pymol`/`pmg_tk`/`PyQt5`/`numpy`.
- Used by: GUI modules, bridge modules, and the WSL unit tests.

**GUI (`pymol.Qt` only):**
- Purpose: Qt widgets, dialog shell, tabs, timers, async QProcess runner.
- Location: `serpentrum/gui.py`, `gui_setup.py`, `gui_game.py`, `gui_spectra.py`,
  `gui_plot.py`, `xtb_runner.py`.
- Contains: `PluginDialog` (`gui.py`), `SetupTab`, `GameTab`, `SpectraTab`,
  `SpectraPlotPanel`/`IrPlotWidget`, `XtbRunController`.
- Depends on: `pymol.Qt` (allowlisted), PURE modules, BRIDGE module `pymol_bridge`.
  `pymol.cmd` is banned here; all viewer access goes through the bridge.
- Used by: `serpentrum/__init__.py` (lazily).

**BRIDGE (`pymol`/`pmg_tk` allowed at any level):**
- Purpose: the single `cmd.*` seam + keyboard steering wizard.
- Location: `serpentrum/pymol_bridge.py`, `serpentrum/input.py`.
- Contains: object load/materialize/move/transform/camera/cleanup functions
  (`pymol_bridge`); `KeySteerWizard` + `install`/`set_active`/`teardown` (`input.py`).
- Depends on: `pymol.cmd` / `pymol.wizard` at module level; PURE modules for data.
  Qt and numpy are banned.
- Used by: GUI modules.

## Module Classification (exact, from `tools/check_purity.py`)

| Class | Files | Import rule |
|-------|-------|-------------|
| ENTRY | `serpentrum/__init__.py` | `pymol`/`pmg_tk` lazily in function bodies only; `PyQt5`/`numpy` never |
| GUI | `serpentrum/gui.py`, `gui_setup.py`, `gui_game.py`, `gui_spectra.py`, `gui_plot.py`, `xtb_runner.py` | `pymol.Qt` / `pymol.Qt.*` only; any other `pymol*`/`pmg_tk` anywhere is a violation |
| BRIDGE | `serpentrum/pymol_bridge.py`, `serpentrum/input.py` | `pymol`/`pmg_tk` allowed at any level; `PyQt5`/`numpy` never |
| PURE (default) | every other `.py` under `serpentrum/` | `pymol`/`pmg_tk`/`PyQt5`/`numpy` never, anywhere |

The allowlists are `GUI_MODULES` (`tools/check_purity.py:72-74`) and `BRIDGE_MODULES`
(`tools/check_purity.py:84`). Everything else is PURE by default-strict classification.
`.exec_()` calls are banned in every class (`tools/check_purity.py:200-207`).

## Data Flow

**Game loop (main Qt thread, 100 ms tick):**

1. `SetupTab` (`serpentrum/gui_setup.py`) collects the setup dict and emits
   `start_requested(setup)`; the canonical 6-button bottom row lives in
   `PluginDialog` (`serpentrum/gui.py:149-171`) and calls the page's handlers.
2. `PluginDialog._on_start_requested` (`serpentrum/gui.py:173-183`) switches to tab 1 and
   calls `GameTab.begin_game(setup)`.
3. `GameTab` (`serpentrum/gui_game.py`) tears down any prior round, builds the
   round-robin spawner via `serpentrum/spawn.py`, seeds `GameEngine(pickups=...)`, and runs
   the epoch-guarded 3-2-1 countdown via `QtCore.QTimer.singleShot`.
4. `_begin_play` locks the 2D camera (through `pymol_bridge`), installs the
   `KeySteerWizard` from `serpentrum/input.py`, and starts the 100 ms movement tick.
5. Each tick: `game_engine.step()` (PURE) emits events (`moved`/`stacked`/`crashed`/`won`).
   `pymol_bridge.move_chain_delta` translates head + `srp_seg_*` together (train-follow).
6. On a capture: `serpentrum/placement.py::resolve()` (PURE policy) →
   `serpentrum/stacking.py::place_pickup()` (PURE rigid-body math) →
   `serpentrum/orientation.py::matrix_rt()` (PURE 4×4 float layout) →
   `pymol_bridge` applies it via `cmd.transform_selection`.
7. CGO graphics float-lists come from `serpentrum/cgo_build.py` (PURE box edges and
   vibrational-mode arrows) and are handed to `pymol_bridge` → `cmd.load_cgo`.
8. HUD strings/labels are composed by `serpentrum/hud_logic.py` (PURE) and
   `serpentrum/help_text.py` (PURE); widgets live in `GameTab`.
9. On win/crash: `_teardown_round` restores the prior wizard and camera, then builds the
   `last_run` handoff record — including head-inclusive `snake_xyz` via
   `xtb_run.build_run_input` (`serpentrum/xtb_run.py`) — and anchors it on
   `_serpentrum.last_run`, then emits `spectra_requested`.

**Spectra pipeline (async, QProcess):**

1. `GameTab.spectra_requested` → `PluginDialog._on_spectra_requested`
   (`serpentrum/gui.py:185-273`): switches to tab 2, guards the anchor/`last_run`/`snake_xyz`,
   counts atoms via `xyzio.read_xyz_text`, cross-checks viewer counts via
   `pymol_bridge.chain_atom_counts`, logs `budget_guard` lines (warn-and-proceed), resolves
   the binary via `xtbenv.detect_binary`.
2. `_launch_spectra_run` (`serpentrum/gui.py:275-306`): create-or-reuse the anchored
   `XtbRunController` (`serpentrum/xtb_runner.py`) on `_serpentrum.spectra_runner`;
   `_connect_runner` replays `controller.log_tail()` then connects
   `started`/`log_line`/`run_finished`.
3. `XtbRunController.start(...)`: guard via `xtb_run.can_start`; fresh spray dir via
   `xtbenv.new_run_dir` (under `tempfile.gettempdir()`); writes `snake.xyz`; argv via
   `xtbenv.build_argv` (`snake.xyz --ohess -P 4`); launches `QProcess` with `cwd` = spray
   dir and merged env knobs (`xtb_run.build_env`). `readyRead` streams `log_line`.
4. Terminal branch (every path): `xtbenv.evaluate_run` 3-leg verdict (exit 0 + stderr
   `normal termination` + expected files present) → `xtb_run.resolve_status` (cancel wins)
   → copy artifacts into the stable dir (`_stable_base()`: `SRP_SPECTRA_DIR` env or
   `<cwd>/srp_spectra`) → delete spray dir → `xtb_run.new_spectra_run` writes
   `_serpentrum.spectra_run` → emit `run_finished(status, problems)`.
5. `SpectraTab.on_run_finished` (`serpentrum/gui_spectra.py`): parse via
   `spectra.parse_g98` (PURE, fallback `parse_vibspectrum`) → broaden via
   `spectra.broaden` → build a paint-ready `Scene` via `plot_logic.build_scene` (PURE) →
   hand to `SpectraPlotPanel` (`serpentrum/gui_plot.py`) whose `paint_scene` maps pixels.
6. Frequency table rows and mode-arrow selectors come from `serpentrum/spectra_ui.py`
   (PURE); selected mode → `cgo_build.mode_arrows` → `pymol_bridge` loads the `srp_`
   CGO overlay.

**xtb subprocess lifecycle:**

- Rules live in PURE modules: `xtbenv.py` (binary detect, argv, run dir, 3-leg success
  contract) and `xtb_run.py` (state machine, cancel→status mapping, env-knob merge,
  record shape `SPECTRA_RUN_KEYS`).
- The Qt shell is `xtb_runner.py` (`XtbRunController : QtCore.QObject`): signals-only, no
  polling/blocking; `cancel()` = `proc.kill()`; a `_LOG_TAIL = 500` bounded in-memory log.
- Artifacts dir: `SRP_SPECTRA_DIR` env var, default `<cwd>/srp_spectra`; the per-run
  subdir is `<snake_id>` and is keep-until-replaced. Scratch spray dirs stay under
  `tempfile.gettempdir()`.
- `serpentrum/xtb_runner.py` is GUI-classed (only `pymol.Qt`); it never imports `pymol.cmd`.

## Key Abstractions

**`_SerpentrumState` (live-state anchor):**
- Purpose: single-instance storage surviving `importlib.reload` and double-import.
- Location: defined in `serpentrum/__init__.py:22-63`; stored at
  `pmg_tk.startup._serpentrum`.
- Fields: `dialog`, `controller`, `setup`, `game_session`, `records`,
  `stacking_data`, `last_run`, `spectra_run`, `spectra_runner`.
- Pattern: `_anchor()` creates the object only when missing; all UI reads/writes go through
  the anchor passed down from `run_plugin_gui` → `PluginDialog` → tabs. Never module globals.

**`GameEngine`:**
- Purpose: authoritative grid/snake/score/budget state.
- Location: `serpentrum/game_engine.py` (823 lines).
- Pattern: engine owns truth; PyMOL coordinates are a projection, never read back except at
  the spectra handoff. Emits event tuples consumed by `GameTab`.

**`Scene` namedtuple:**
- Purpose: paint-ready plot data (curve points, ticks, labels, counts, fwhm).
- Location: `serpentrum/plot_logic.py`; built by `build_scene`.
- Pattern: PURE computes all numbers; `gui_plot.paint_scene` only maps to pixels.

**`XtbRunController`:**
- Purpose: async single-owner xtb process controller.
- Location: `serpentrum/xtb_runner.py:76`.
- Pattern: anchored (not module-level) instance so reload cannot duplicate it; Qt signals
  `started`, `log_line(str)`, `run_finished(str, list)`.

**`PluginDialog` (composition root):**
- Purpose: dialog shell, tab switch orchestration, cross-tab launch pipeline, canonical
  bottom action row.
- Location: `serpentrum/gui.py:37`.
- Pattern: tabs never reach up to their parent; the dialog owns all `QTabWidget` switches,
  the xtb launch flow, and the 6-button row (`Reset`/`Randomize`/`Save Setup`/`Load Setup`/
  `Cleanup model`/`Start`). **Note:** the original research proposed a separate
  `controller.py`; the shipped code has NO `controller.py` — `PluginDialog` and `GameTab`
  fill that role.

**`pymol_bridge` (single cmd seam):**
- Purpose: the only module (besides `input.py`) that calls `pymol.cmd`.
- Location: `serpentrum/pymol_bridge.py`; reserved prefix constant `SRP_PREFIX = 'srp_'`;
  canonical names `BOX_NAME='srp_box'`, `HEAD_NAME='srp_head'`, `MODE_VEC_NAME='srp_mode_vec'`,
  `XTBOPT_NAME='srp_xtbopt'`.
- Pattern: thin — no parsing/gating (that is `molfile`/`setloader`'s PURE job).
  `cleanup_srp()` (`pymol_bridge.py:129`) is a pure function of object names (no state
  args), so it works in a fresh process after `.pse` reload.

**`help_text` (single-sourced user text):**
- Purpose: every testable help/hint string (DOCS-03), rendered verbatim by GUI tabs.
- Location: `serpentrum/help_text.py`.
- Pattern: `GAME_FOCUS_HINT`, `CONTROLS_RECAP`, `SETUP_HINTS`, `game_hint(state)` — GUI
  never re-derives wording; pinned by the doc-vs-code audit (`tools/check_docs.py`).

## Entry Points

**Plugin registration:**
- Location: `serpentrum/__init__.py`
- Triggers: PyMOL's plugin loader imports the module (as `pmg_tk.startup.serpentrum`) and
  calls `__init_plugin__(app)` (`serpentrum/__init__.py:70-75`).
- Responsibilities: register `addmenuitemqt('serpentrum', run_plugin_gui)`.

**GUI launch:**
- Location: `serpentrum/__init__.py:78-86`
- Triggers: the Plugins-menu item.
- Responsibilities: `_anchor()` → lazily import `PluginDialog` → adopt an existing orphan
  (`PluginDialog.find_existing()`) or construct one → `.show()` + `raise_()` +
  `activateWindow()` (modeless).

**Smoke scripts (executable scenarios):**
- Location: `smoke/*.py` — numbered `smoke/01_skeleton_smoke.py` … `smoke/14_release_e2e_smoke.py`
  plus manual harnesses `smoke/manual_plot_check.py`, `smoke/manual_wizard_keys_check.py`.
- Triggers: `tests/run_gates.py --smoke` via
  `cmd.exe /c C:\src\run-conda-pymol.bat -cq smoke\NN_*.py`.
- Responsibilities: headless Windows-PyMOL verification. Verdict = flushed `SMOKE-OK`
  sentinels only, never exit codes. `REQUIRED_SMOKES` in `tests/run_gates.py:55-75`
  is smokes 01, 03, 04, 05, 06, 07, 08, 10, 12, 13, 14; other numbered smokes and manual
  harnesses are informational (run, never fail the gate).

**Dev tools (not plugin):**
- Location: `tools/build_demo_manifest.py`, `tools/build_calibration_snake.py`,
  `tools/measure_calib_qprocess.py`, `tools/winpath.py`, `tools/check_purity.py`,
  `tools/check_docs.py` (DOCS-04 doc-vs-code audit), `tools/audit_requirements.py`
  (DOCS-05 requirements-ledger integrity).

## Error Handling

**Strategy:** Errors are DATA in the PURE layer, surfaced as strings/records to the GUI.

**Patterns:**
- Pure validators return problem lists rather than raising (`setup_logic.validate`,
  `budget_guard`), except parsers which raise typed errors carrying line numbers
  (`xyzio.XyzError`, `molfile.MolFileError`, `molecule_data.DataError`,
  `spectra.SpectraParseError`).
- GUI catches parser errors and shows a verdict line; no fabricated success.
- All viewer calls are `getattr`-guarded so a reload-stripped anchor never crashes a launch.
- The xtb success contract is a strict 3-leg conjunction
  (`xtbenv.evaluate_run`): exit 0 AND stderr `normal termination` AND expected files
  present. A killed/cancelled run cannot read as success.

## Cross-Cutting Concerns

**Logging:** GUI-level streaming; `XtbRunController` emits `log_line` and keeps a bounded
500-line tail (`_LOG_TAIL`) with `log_tail()` replay for late/reloading tabs. `GameTab`
has a read-only rolling info box fed by `hud_logic` builders and `log_external`; the
Spectra launch pipeline mirrors lines into it (`gui.py:_log_spectra_line`).

**Validation:** `setup_logic.validate` (per-key errors + hessian warning),
`setloader` (manifest cross-verification and gate enforcement), `molfile` (parse + gate),
`molecule_data` (structural JSON validation), `budget_guard` (pre-launch re-check).
Doc/requirements drift is caught by `tools/check_docs.py` and
`tools/audit_requirements.py`.

**Authentication:** Not applicable (desktop plugin; no network/auth).

**Determinism:** `setup_logic.randomize_head` uses a private `random.Random(seed)`;
`spawn` uses a private seeded RNG; fixtures are git-committed.

---

*Architecture analysis: 2026-10-02*
