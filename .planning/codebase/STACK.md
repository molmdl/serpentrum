# Technology Stack

**Analysis Date:** 2026-10-02

## Languages

**Primary:**
- Python 3.6-targeted source — all first-party code: `serpentrum/` (29 modules), `tools/` (7 scripts), `tests/` (47 `test_*.py` files + `run_gates.py`), `smoke/` (14 numbered + 2 manual scripts). Syntax is constrained to **python3.6** on purpose: no f-strings, no walrus operator, no dataclasses (%-formatting throughout). Enforced by `py_compile` in `tests/run_gates.py` gate 1.
- Bash — `test_wsl_winxtb.sh` (4 lines: `cd tmp/xtb_test` then exec the Windows `xtb.exe` on `phenol.xyz --ohess`).

**Secondary:**
- Tcl — Not detected in first-party code. `tclsh` is available in the WSL dev shell per `AGENTS.md` for syntax checks/`tcltest`, but no `*.tcl` files exist anywhere in the tree. The plugin is Tk-free (Qt only).
- C/C++ — Not detected in first-party code (no `*.c`/`*.cpp`). PyMOL's C layer is only referenced through its Python API in `serpentrum/pymol_bridge.py` and `serpentrum/input.py`.

**Runtime Python version note:** The Windows conda PyMOL runtime is Python **3.9** (compiled bytecode under `serpentrum/__pycache__/*.cpython-39.pyc`; `tools/measure_calib_qprocess.py` docstring: "the conda runtime is 3.9"). The WSL dev/test interpreter is `python3.6` (3.6.9). Source is written to the 3.6 subset so both interpret it.

## Runtime

**Environment — the WSL/Windows split (load-bearing):**
- **Dev/test:** WSL Ubuntu, `python3.6` (3.6.9) for syntax checks and pure-layer unit tests only. No `pip`/`apt`/`conda` installs (denied in `opencode.json`). `tclsh` (Tcl 8.5/8.6) also available.
- **Plugin runtime:** PyMOL 2.5.0 in a **Windows conda env**, loaded as `pmg_tk.startup.serpentrum`. Windows PyMOL cannot resolve WSL `/mnt/c/...` paths.
- **Bridge:** Headless Windows PyMOL runs from WSL via `cmd.exe /c C:\src\run-conda-pymol.bat -cq <script>` (the `.bat` and `setenv.bat` live outside the repo, at `C:\src`). See `tests/run_gates.py:78` (`SMOKE_BAT = 'C:\\src\\run-conda-pymol.bat'`).

**Package Manager:**
- None for first-party Python deps. No `requirements.txt`, `package.json`, `setup.py`, `pyproject.toml`, `Cargo.toml`, or `go.mod` (verified absent).
- Lockfile: None (intentional — the dependency set is fixed by what `pymol-open-source` ships).
- External binaries are obtained out-of-band (xtb zip download; symlinked at the repo root, git-ignored).

## Frameworks

**Core:**
- **PyMOL open-source 2.5.0** — host application, molecular engine, OpenGL viewer, plugin API (`pymol.cmd`, `pymol.wizard`, `pymol.plugins`). The only runtime. Referenced in `serpentrum/__init__.py` (`addmenuitemqt`), `serpentrum/pymol_bridge.py` (`from pymol import cmd`), `serpentrum/input.py` (`from pymol.wizard import Wizard`).
- **Qt (PyQt5 via `pymol.Qt`)** — GUI. Imported exclusively as `from pymol.Qt import QtWidgets, QtCore, QtGui` (never `from PyQt5 import`, so a PySide2 fallback stays possible). See `serpentrum/gui.py`, `serpentrum/gui_setup.py`, `serpentrum/gui_game.py`, `serpentrum/gui_plot.py`, `serpentrum/gui_spectra.py`, `serpentrum/xtb_runner.py`. Provides `QTimer` (game loop), `QProcess` (async xtb), `QPainter`/`QWidget` (spectra plot), `QFileDialog`, `QTableWidget`.

**Testing:**
- **`unittest`** (stdlib) — all 47 test files under `tests/` use `import unittest`. No pytest anywhere. Discovered scoped by `tests/run_gates.py` gate 3 (`python -m unittest discover -s tests -p "test_*.py" -v`; `-t .` deliberately omitted — fails on 3.6 with a non-package start dir). `unittest.mock` used for stubbing.
- **`tcltest`** — named in `AGENTS.md` as available for pure-layer Tcl tests; no Tcl tests exist in the current tree.

**Build/Dev:**
- No build system. "Build" = `py_compile` syntax walk + AST purity check + unittest discovery, all orchestrated by `tests/run_gates.py`.
- `tools/check_purity.py` — AST-based import-purity checker (INFRA-02). Classifies every `serpentrum/*.py` as ENTRY / GUI / BRIDGE / PURE (`tools/check_purity.py:95-103`) and bans `pymol`/`pmg_tk`/`PyQt5`/`numpy` imports per class; also bans `.exec_()` calls everywhere (modeless rule).
- `tools/winpath.py` — WSL `/mnt/<drive>` → Windows path string conversion, dev/harness side only (`to_windows_path` forward-slash, `to_windows_backslash` for `cmd.exe`).
- `tools/build_demo_manifest.py` — parses the shipped PubChem SDFs via `serpentrum.molfile`, aborts on any mismatch, writes `serpentrum/data/manifest.json` (idempotent).
- `tools/build_calibration_snake.py` — deterministic builder for `tests/fixtures/calib_snake_{52,104}.xyz`.
- `tools/measure_calib_qprocess.py` — headless QProcess wall-time calibration probe (runs under Windows PyMOL via the `.bat`).
- `tools/check_docs.py` — doc-vs-code audit harness (docs release gate); imports PURE modules only.
- `tools/audit_requirements.py` — requirements-ledger integrity checker (DOCS-05), regex/`os` stdlib only.

## Key Dependencies

**Critical:**
- **PyMOL 2.5.0** (`pymol-open-source`) — the plugin host. Ships PyQt5 and numpy. `README.md` states the build is "anaconda build or equivalent". Version pinned by `AGENTS.md`/`spec.md` (`spec.md:64`).
- **PyQt5** — bundled with PyMOL's Qt GUI; imported only through the `pymol.Qt` facade (`pymol/Qt/__init__.py` tries PyQt5 first, falls back to PySide2).
- **numpy** — a PyMOL build dependency, therefore available at runtime; however see the purity rule below.

**Infrastructure:**
- **xtb 6.7.1pre** (Windows x86_64 build, download `xtb-6.7.1pre-windows-x86_64.zip` per `README.md`; verified version string "xtb version 6.7.1pre ..." in `tests/run_gates.py:275`). External executable, **not** a Python dependency — invoked as a subprocess/QProcess. `--ohess` outputs expected by the pipeline: `g98.out` (primary parser target incl. mode vectors) and `vibspectrum` (`serpentrum/xtbenv.py:39`), plus `xtbopt.xyz` copied out by the runner (`serpentrum/xtb_runner.py:304`).
- The repo-root symlink `xtb-6.7.1 -> /mnt/c/xtb-6.7.1` (git-ignored) is a **dev-side** access path; the Windows runtime reaches the exe at user-configured path or `C:\xtb-6.7.1\bin\xtb.exe`.

**Dependency policy (hard rule):**
- Allow **only what `pymol-open-source` ships** (PyQt5 via `pymol.Qt`, numpy). Any additional Python library requires explicit user approval and either local user install or vendoring into `./3rd_party_lib/` (git-ignored) with its license noted (`spec.md:81-82`, `AGENTS.md`, `README.md:23-24`). `matplotlib`, `scipy`, `Pmw`/Tkinter, and direct `PyQt5` imports are explicitly rejected in `.planning/research/STACK.md`.
- Purity enforcement makes this mechanical: `tools/check_purity.py`'s `BANNED_ROOTS = ('pymol', 'pmg_tk', 'PyQt5', 'numpy')` (`check_purity.py:89`). **PURE** modules (the default class) may import none of them; **GUI** modules may import `pymol.Qt` only (no numpy); **BRIDGE** modules may import `pymol`/`pmg_tk` but not PyQt5/numpy. Test-only dev dependencies are not added.

**Stdlib-only by construction:**
- PURE modules use only the standard library — `math`, `json`, `os`, `random`, `collections`, `tempfile`, `shutil`, `copy`, `zlib` (see `serpentrum/molecule_data.py`, `serpentrum/spectra.py`, `serpentrum/stacking.py`, `serpentrum/spawn.py`, `serpentrum/xtbenv.py`, `serpentrum/xtb_run.py`). `serpentrum/help_text.py` has zero imports (verbatim text layer). This lets the pure layer unit-test on WSL `python3.6` with zero `sys.modules` stubs.

## Configuration

**Environment:**
- **`SRP_XTB_PATH`** — optional explicit xtb executable path (dev/smoke seam; probed first by `smoke/09_qprocess_smoke.py` and `serpentrum/gui_setup.py` via `xtbenv.detect_binary`).
- **`SRP_SPECTRA_DIR`** — user-settable artifacts root for kept spectra; default `<cwd>/srp_spectra` (`serpentrum/xtb_runner.py:59-60`). The directory is git-ignored (`.gitignore`).
- **`SRP_DEBUG`** — when `'1'`, enables live-debug tracing in `serpentrum/hud_logic.py` and `serpentrum/gui_game.py` (`hud_logic.debug_capture_trace`, `debug_event_trace`).
- **`OMP_NUM_THREADS` / `MKL_NUM_THREADS` / `OMP_STACKSIZE`** — the only xtb env knobs accepted (`serpentrum/xtb_run.py:88`); no-defaults policy `DEFAULT_RUN_KNOBS = {}` (`xtb_run.py:71`). The default thread cap is applied ARGV-side instead: `DEFAULT_THREAD_ARG = ('-P', '4')` (`xtb_run.py:81`).
- Windows conda env is entered via an external `setenv.bat`; headless runs stage through `C:\src\run-conda-pymol.bat`.

**Tool-permission config — `opencode.json` (repo root):**
- Denies `rm *` and `rg *`; makes `pip*`, `pip3*`, `apt*`, `conda*`, `wget*`, `curl*`, `mv*`, `python*`, `npm*`, and `git push/pull/merge/rebase/reset/checkout` "ask".
- Reads allow all except `*.env*` (ask).
- Also configures GSD agent models (not runtime code). A backup copy `opencode.json.glm5.3f` sits beside it.

**Ignore config — `.gitignore`:**
- Third-party symlink trees: `xtb-6.7.1`, `Pymol-script-repo`, `pymol-src`, `vmd-ref` (v2 reference), `3rd_party_lib/` (all git-ignored).
- `*.env`, `*.pyc`, `*.npy`, `*.npz`, `**/secrets.toml`, `**/auth.json`, `tmp`, `*.zip`, `cache`, `**/cache/**`, and `srp_spectra/` (CWD-default spectra artifacts).

**Plugin-path safety (config-by-absence):**
- The dev install points PyMOL's plugin loader at the repo root, so there must be **no top-level `*.py`** at the repo root and **no `__init__.py`** in `tests/`, `smoke/`, or `tools/` (enforced by `tests/run_gates.py` gate 1). This is why helper scripts self-insert the repo root on `sys.path` instead of being packages (`tools/build_demo_manifest.py`).

## Platform Requirements

**Development:**
- WSL Ubuntu with `python3.6` (3.6.9) and `tclsh`; the repo must live on a `/mnt/<drive>` mount (the `--xtb` gate asserts the root maps to `C:/...`, `tests/run_gates.py:227-234`).
- `cmd.exe` reachable from WSL for the Windows PyMOL smoke legs and for the xtb `.exe`.

**Production:**
- PyMOL 2.5.0 (Windows conda env; PyMOL Plugin Manager install of the `serpentrum/` package, or dev install by adding the repo path).
- Windows xtb `xtb.exe` (6.7.1pre tested) at a user-configured path or auto-detected via `shutil.which('xtb.exe')` then `shutil.which('xtb')` (`serpentrum/xtbenv.py:141-167`).

---

*Stack analysis: 2026-10-02*
