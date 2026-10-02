# Codebase Structure

**Analysis Date:** 2026-10-02

## Directory Layout

```
serpentrum/                          # repo root
├── serpentrum/                      # the installable PyMOL plugin package (first-party code)
│   ├── __init__.py                  # ENTRY: plugin registration + live-state anchor
│   ├── gui.py                       # GUI: PluginDialog (3-tab shell, composition root, bottom row)
│   ├── gui_setup.py                 # GUI: SetupTab (config form + persistence handlers)
│   ├── gui_game.py                  # GUI: GameTab (engine tick + HUD, largest file)
│   ├── gui_spectra.py               # GUI: SpectraTab (status/log/plot/table surface)
│   ├── gui_plot.py                  # GUI: QPainter IR plot widget + save route
│   ├── xtb_runner.py                # GUI: XtbRunController (async QProcess)
│   ├── pymol_bridge.py              # BRIDGE: the single pymol.cmd seam
│   ├── input.py                     # BRIDGE: KeySteerWizard (arrow-key steering)
│   ├── game_engine.py               # PURE: snake movement + rules + sweeps
│   ├── stacking.py                  # PURE: ring frames, rigid-body pi-stack math
│   ├── placement.py                 # PURE: 'stacked'-branch placement policy
│   ├── orientation.py               # PURE: edge-on frame + 4x4 TTT matrix builder
│   ├── spawn.py                     # PURE: pickup spawn policy + RNG
│   ├── generic_stack.py             # PURE: consent-gated generic upload stacking
│   ├── setloader.py                 # PURE: manifest -> molecule records (validate)
│   ├── molfile.py                   # PURE: SDF V2000 / mol2 reader + ring counter
│   ├── molecule_data.py             # PURE: JSON data loaders + structural validation
│   ├── setup_logic.py               # PURE: setup schema, defaults, validate, save/load
│   ├── budget_guard.py              # PURE: pre-launch atom-budget warnings
│   ├── xyzio.py                     # PURE: .xyz read/write + element validation
│   ├── xtbenv.py                    # PURE: xtb detect, argv, run dir, success contract
│   ├── xtb_run.py                   # PURE: xtb state machine, records, env merge
│   ├── spectra.py                   # PURE: g98/vibspectrum parse + broadening
│   ├── plot_logic.py                # PURE: paint-ready Scene builder
│   ├── spectra_ui.py                # PURE: Spectra display/label/row decisions
│   ├── hud_logic.py                 # PURE: Game HUD string/count builders
│   ├── help_text.py                 # PURE: single-sourced in-game help/hint strings
│   ├── cgo_build.py                 # PURE: CGO float-list builders (box, arrows)
│   └── data/                        # shipped demo data (JSON + SDF + attribution)
│       ├── manifest.json            # Set A molecule manifest
│       ├── stacking_pi_stack.json   # approved stacking interactions + citations
│       ├── benzene.sdf, naphthalene.sdf, anthracene.sdf,
│       ├── phenanthrene.sdf, biphenyl.sdf
│       └── DATA_SOURCES.md          # verified citations for shipped data
├── tests/                           # WSL python3.6 unittest suite (dev-side, not a plugin)
│   ├── run_gates.py                 # single gate entry point (syntax/purity/unittest/smoke/xtb)
│   ├── test_*.py                    # 47 unit + integration tests (pure layer + dev tools)
│   └── fixtures/                    # committed test data
│       ├── xtb/                     # g98.out, vibspectrum, logs, xyz fixtures
│       ├── molfile/                 # SDF/mol2 fixtures
│       └── calib_snake_52.xyz, calib_snake_104.xyz
├── smoke/                           # headless Windows PyMOL scripts (dev-side, not a plugin)
│   ├── NN_*_smoke.py                # required + informational smokes (01..14)
│   └── manual_*.py                  # real-GUI human-verify harnesses
├── tools/                           # dev-side helpers + checkers (not a plugin)
│   ├── check_purity.py              # AST purity/hygiene checker (gate 2)
│   ├── check_docs.py                # doc-vs-code audit harness (DOCS-04)
│   ├── audit_requirements.py        # requirements-ledger integrity checker (DOCS-05)
│   ├── winpath.py                   # WSL -> Windows path conversion
│   ├── build_demo_manifest.py       # one-off manifest builder
│   ├── build_calibration_snake.py   # deterministic calibration fixture builder
│   └── measure_calib_qprocess.py    # xtb wall-time calibration probe
├── .planning/                       # GSD workflow docs (read-only project context)
├── AGENTS.md                        # repo-wide hard rules
├── README.md                        # user-facing overview / install
├── spec.md                          # requirements (source of ROADMAP/REQUIREMENTS)
├── LICENSE                          # BSD 3-Clause
├── opencode.json                    # OpenCode config + permissions
├── test_wsl_winxtb.sh               # WSL -> Windows xtb invocation example
└── srp_spectra/, tmp/               # git-ignored runtime scratch (see Special Directories)
```

The repo also contains **symlinks** that are NOT first-party code and must not be explored
as part of the plugin: `pymol-src -> ../bioCHEMeleon/tmp/pymol-src` (PyMOL source),
`Pymol-script-repo -> ../bioCHEMeleon/Pymol-script-repo` (plugin corpus),
`xtb-6.7.1 -> /mnt/c/xtb-6.7.1` (the Windows xtb binary). All three are git-ignored.

## Directory Purposes

**`serpentrum/`:**
- Purpose: the installable plugin package added to PyMOL's plugin path.
- Contains: entry, GUI, bridge, and pure modules plus shipped `data/`.
- Key files: `serpentrum/__init__.py`, `serpentrum/gui.py`, `serpentrum/pymol_bridge.py`.

**`serpentrum/data/`:**
- Purpose: the DATA half of the game — never code constants for chemistry.
- Contains: `manifest.json` (Set A molecules), `stacking_pi_stack.json` (approved
  interactions + citations), five PubChem SDF files, `DATA_SOURCES.md`.
- Key files: `serpentrum/data/manifest.json`, `serpentrum/data/stacking_pi_stack.json`.

**`tests/`:**
- Purpose: WSL `python3.6` unit + integration tests for the PURE layer and dev tools.
- Contains: `run_gates.py` and 47 `test_*.py` files. No `__init__.py` (module discovery by
  filename under `-s tests`).
- Key files: `tests/run_gates.py`, `tests/test_purity_gates.py`, `tests/test_engine_*.py`,
  `tests/test_docs_audit.py`, `tests/test_audit_requirements.py`.

**`tests/fixtures/`:**
- Purpose: committed, verified input/expected data.
- Contains: xtb outputs (`tests/fixtures/xtb/g98.out`, `vibspectrum`, `xtbopt.xyz`),
  molfile samples, calibration snakes.

**`smoke/`:**
- Purpose: headless Windows-PyMOL scenario scripts for cmd-coupled behavior.
- Contains: 14 numbered `NN_*_smoke.py` plus 2 `manual_*.py` human-verify harnesses. No
  `__init__.py`.
- Key files: `smoke/01_skeleton_smoke.py` (template), `smoke/12_plot_smoke.py`,
  `smoke/14_release_e2e_smoke.py`.

**`tools/`:**
- Purpose: dev-only harness/helpers; run in WSL, never loaded by PyMOL.
- Contains: `check_purity.py`, `check_docs.py`, `audit_requirements.py`, `winpath.py`, and
  one-off builders/probes. No `__init__.py`.

**`.planning/`:**
- Purpose: GSD workflow source of truth (PROJECT/ROADMAP/STATE/REQUIREMENTS, research,
  phases). Read-only context for code work, not shipped code.

## Key File Locations

**Entry Points:**
- `serpentrum/__init__.py`: `__init_plugin__` + `run_plugin_gui` + `_anchor()`.
- `tests/run_gates.py`: the single gate runner (WSL + `--smoke` + `--xtb`).
- `tools/check_purity.py`: AST class/import/.exec_ checker.
- `smoke/01_skeleton_smoke.py`: the smoke template every scenario copies.

**Configuration:**
- `opencode.json`: OpenCode config + denied shell patterns (`pip*`, `apt*`, `conda*`, `rm*`).
- `AGENTS.md`: environment split, gates, plugin-path safety, purity classes.
- `.gitignore`: ignores symlinks, `tmp/`, `srp_spectra/`, secrets, caches.
- `serpentrum/data/manifest.json` + `stacking_pi_stack.json`: shipped game data schema.

**Core Logic:**
- `serpentrum/game_engine.py`: snake state machine (823 lines).
- `serpentrum/gui_game.py`: tick loop + HUD orchestration (1572 lines, largest file).
- `serpentrum/gui.py`: `PluginDialog` composition root + cross-tab launch pipeline +
  canonical 6-button bottom row.
- `serpentrum/pymol_bridge.py`: all `cmd.*` side effects.
- `serpentrum/xtb_runner.py`: async QProcess controller.
- `serpentrum/xtbenv.py` + `serpentrum/xtb_run.py`: xtb rules (PURE).
- `serpentrum/spectra.py` + `serpentrum/plot_logic.py` + `serpentrum/gui_plot.py`:
  parse → Scene → pixels.
- `serpentrum/help_text.py`: single-sourced in-game help/hint strings.

**Testing:**
- `tests/run_gates.py`: gate 1 (syntax+plugin-path safety), gate 2 (purity),
  gate 3 (scoped unittest), gate 4 (`--smoke`), gate 5 (`--xtb`).
- `tests/test_purity_gates.py`: enforces the classification/purity rules.
- `tests/fixtures/xtb/`: parse fixtures for `spectra.py`.

**Data / Attribution:**
- `serpentrum/data/DATA_SOURCES.md`: verified PubChem/DOI attributions.

## Naming Conventions

**Files (plugin package):**
- Pure logic modules: lowercase, descriptive noun (`game_engine.py`, `stacking.py`,
  `placement.py`, `spectra.py`, `xyzio.py`, `help_text.py`).
- GUI modules: `gui_<tab>_<role>.py` (`gui_setup.py`, `gui_game.py`, `gui_spectra.py`,
  `gui_plot.py`); the dialog shell is `gui.py`; the async runner is `xtb_runner.py`.
- Bridge modules: purpose-named (`pymol_bridge.py`, `input.py`).
- Test files: `test_<unit>.py`, grouped by plan (`test_engine_*.py`, `test_phase5_*.py`,
  `test_phase51_integration.py`, `test_phase52_integration.py`).
- Smoke files: `NN_<scenario>_smoke.py`; manual harnesses `manual_<scenario>_check.py`.
- Tools: `build_<thing>.py`, `measure_<thing>.py`, `check_<thing>.py`,
  `audit_<thing>.py`, or a single word (`winpath.py`).

**Files (data):**
- JSON: `manifest.json`, `stacking_pi_stack.json`.
- Molecules: `<molecule>.sdf` (lowercase common name).

**Functions:**
- Pure builders/composers return plain data: `build_scene`, `build_argv`,
  `build_run_input`, `box_cgo`, `mode_arrows`, `game_hint`.
- Validators return problem lists: `validate`, `validate_binary_path`.
- Predicates: `can_start`, `can_spawn`, `has_stack_entry`.
- Bridge verbs mirror PyMOL actions: `load_molecule`, `materialize`, `cleanup_srp`,
  `move_chain_delta`, `chain_atom_counts`.

**Classes:**
- GUI widgets: `<Purpose>Tab`, `<Purpose>Dialog`, `<Purpose>Panel`, `<Purpose>Widget`
  (`SetupTab`, `PluginDialog`, `SpectraPlotPanel`, `IrPlotWidget`).
- Controller: `<Tool>Controller` (`XtbRunController`).
- Wizard: `<Purpose>Wizard` (`KeySteerWizard`).

**Variables / constants:**
- `snake_case` locals; `UPPER_SNAKE` module constants (`XTB_OHESS`, `SRP_PREFIX`,
  `SPECTRA_RUN_KEYS`, `REQUIRED_SMOKES`, `CLASH_THRESHOLD_A`).
- Reserved object names: `srp_` prefix (`srp_head`, `srp_box`, `srp_seg_*`,
  `srp_mode_vec`, `srp_xtbopt`).

**Types:**
- `namedtuple` for immutable records (`Mode`, `Atom`, `Spectrum`, `Scene`); plain tuples
  for vectors; dicts for setup/records.

## Plugin-Path Safety (hard rules — enforced by gate 1)

The dev install points PyMOL's plugin loader at the **repo root**, so the loader's
`findPlugins` would autoload any top-level `.py` or package dir as a second plugin at GUI
startup. `tests/run_gates.py::gate_syntax_safety` (gate 1) enforces:

- **NO `__init__.py` in `tests/`, `smoke/`, or `tools/`** — checked by
  `SAFETY_DIRS = ('tests', 'smoke', 'tools')` (`tests/run_gates.py:52`).
- **NO top-level `*.py` at the repo root** — checked by `glob(ROOT/*.py)`. Root scripts
  must be `.sh` or live under `tools/`/`smoke/`/`tests/`.
- Gate 1 also runs `py_compile` over `serpentrum/`, `tools/`, `tests/`, `smoke/`
  (`WALK_DIRS`, `tests/run_gates.py:49`).

This is why `serpentrum/` is the only package directory: it is the intentionally-registered
plugin, and its `__init__.py` is the ENTRY module.

## Where to Add New Code

**New pure logic (math, parsing, policy, formatting):**
- Primary code: a new module under `serpentrum/` (defaults to PURE class automatically).
- Tests: `tests/test_<module>.py` (WSL `python3.6`, stdlib-only, no stubs).

**New GUI widget / tab surface:**
- Implementation: a new `gui_<name>.py` **and** add its path to `GUI_MODULES` in
  `tools/check_purity.py` (the allowlist entry must land deliberately — `check_tree` only
  walks existing files, so entries for not-yet-created files are inert).
- Use `from pymol.Qt import ...` only; never `from PyQt5 import ...`; never `pymol.cmd`.
- Wire cross-tab switching in `PluginDialog` (`serpentrum/gui.py`), not in the tab.

**New `cmd.*` access:**
- Add the function to `serpentrum/pymol_bridge.py` (the single seam). Do not import
  `pymol.cmd` from a GUI module. If a genuinely new BRIDGE module is needed, add it to
  `BRIDGE_MODULES` in `tools/check_purity.py`.

**New live state:**
- Add a field to `_SerpentrumState` in `serpentrum/__init__.py` and anchor it on
  `pmg_tk.startup._serpentrum`. Never use module-level globals.

**New xtb behavior:**
- Rules → `serpentrum/xtbenv.py` or `serpentrum/xtb_run.py` (PURE, WSL-testable);
  Qt wiring only → `serpentrum/xtb_runner.py`.

**New user-visible help/hint text:**
- Add the string/constant to `serpentrum/help_text.py` (PURE); render it verbatim in the
  GUI tab. Pin it with a test so `tools/check_docs.py` doc-vs-code audit stays honest.

**New shipped data:**
- `serpentrum/data/`, with verified attribution in `serpentrum/data/DATA_SOURCES.md` and
  structural validation in `serpentrum/molecule_data.py`.

**New headless scenario:**
- `smoke/NN_<scenario>_smoke.py` (copy the `smoke/01_skeleton_smoke.py` template:
  `flush=True` prints, no widget construction, no `__init__.py`, resolve ROOT by validating
  `serpentrum/__init__.py` candidates, verdict = flushed `SMOKE-OK` sentinels). Add to
  `REQUIRED_SMOKES` in `tests/run_gates.py` only if it must gate every run.

**New dev helper:**
- `tools/` with a shebang and a docstring; never import it from plugin code.

## Special Directories

**`serpentrum/__pycache__/`, `tests/__pycache__/`, `smoke/__pycache__/`:**
- Purpose: Python bytecode cache.
- Generated: Yes. Committed: No (`.gitignore` ignores `*.pyc`).

**`srp_spectra/`:**
- Purpose: default CWD-relative xtb artifact output dir (`run_<snake_id>/`), because PyMOL
  may be launched with the repo root as cwd.
- Generated: Yes. Committed: No (explicitly ignored in `.gitignore`).

**`tmp/`:**
- Purpose: git-ignored scratch — xtb staging/run dirs, worktrees for parallel execution.
- Generated: Yes. Committed: No.

**`3rd_party_lib/`:**
- Purpose: git-ignored location for any future user-approved vendored dependency.
- Generated: Yes. Committed: No.

**Symlinks (`pymol-src`, `Pymol-script-repo`, `xtb-6.7.1`):**
- Purpose: reference source corpora / the Windows xtb binary.
- Generated: No; external. Committed: No (git-ignored); must not be treated as
  first-party code.

---

*Structure analysis: 2026-10-02*
