# Coding Conventions

**Analysis Date:** 2026-10-02

## Language & Runtime Constraints

**Target interpreter:** Python 3.6.9 ONLY (`python3.6`, the WSL Ubuntu dev shell). All first-party Python must import and compile under 3.6. Gate 1 of `tests/run_gates.py` `py_compile`-walks `serpentrum/`, `tools/`, `tests/`, `smoke/` on every run, so any 3.7+ syntax fails hard. `3.6` also has f-strings, but this repo does NOT use them.

**Empirically verified style (greps of the current tree, 2026-10-02):**

- **`%`-formatting exclusively — ZERO f-strings.** A word-boundary grep for real f-strings in `serpentrum/*.py` returns only false positives (`'f') %`, `'F'` element symbols). Every formatted string uses `'... %s' % (value,)`. Examples: `serpentrum/xyzio.py:78`, `serpentrum/xtb_runner.py:362`. Module docstrings explicitly state "no f-strings" (`serpentrum/xyzio.py:28`, `serpentrum/xtbenv.py`, `serpentrum/xtb_runner.py:34`).
- **No walrus operator** (`:=`, 3.8+): zero matches in `serpentrum/*.py`.
- **No type hints / annotations**: zero `def ... ->` in `serpentrum/*.py`. Runtime duck typing throughout.
- **No dataclasses**: `namedtuple` is the record idiom instead — `Scene` (`serpentrum/plot_logic.py:27`), `Mode`/`Atom`/`Spectrum` (`serpentrum/spectra.py:29-36`), `RunVerdict` (`serpentrum/xtbenv.py:48`). `serpentrum/setup_logic.py` docstring documents "no dataclasses/walrus".
- **`super(ClassName, self).__init__(...)` explicit form**, not bare `super()` — 7 uses, 0 bare: `serpentrum/gui.py:78`, `serpentrum/gui_setup.py:89`, `serpentrum/gui_game.py:278`, `serpentrum/gui_plot.py:274,347`, `serpentrum/gui_spectra.py:114`, `serpentrum/xtb_runner.py:100`.
- **Explicit `object` base** where relevant: `class _SerpentrumState(object)` (`serpentrum/__init__.py`), and test fakes like `_RecordingWhich(object)`.
- **3.6-safe `str`/`bytes` handling**: `bytes(self._proc.readAllStandardOutput()).decode('utf-8', 'replace')` (`serpentrum/xtb_runner.py:262`); `open(..., encoding='utf-8')` explicit everywhere.

## Purity Classes (the load-bearing architectural convention)

Every module under `serpentrum/` belongs to exactly one purity class enforced by `tools/check_purity.py` (AST-based, gate 2 of `tests/run_gates.py`). Classification is by path in `GUI_MODULES` / `BRIDGE_MODULES` / `ENTRY_MODULE`:

- **PURE** (default-strict): no `pymol`, `pmg_tk`, `PyQt5`, or `numpy` anywhere (module level OR function bodies). All math/parsing/logic modules: `serpentrum/xyzio.py`, `serpentrum/xtb_run.py`, `serpentrum/xtbenv.py`, `serpentrum/spectra.py`, `serpentrum/plot_logic.py`, `serpentrum/game_engine.py`, `serpentrum/molfile.py`, `serpentrum/setup_logic.py`, `serpentrum/hud_logic.py`, `serpentrum/spectra_ui.py`, etc.
- **BRIDGE** (exactly 2 modules): `serpentrum/pymol_bridge.py`, `serpentrum/input.py`. Allows `pymol`/`pmg_tk` at any level; bans `PyQt5`/`numpy` anywhere and bans `.exec_()`.
- **GUI** (6 modules): `serpentrum/gui.py`, `serpentrum/gui_setup.py`, `serpentrum/gui_game.py`, `serpentrum/xtb_runner.py`, `serpentrum/gui_plot.py`, `serpentrum/gui_spectra.py`. Allows ONLY `pymol.Qt` / `pymol.Qt.*` import forms; any bare `pymol`/`pmg_tk` is a violation. `PyQt5`/`numpy` banned.
- **ENTRY**: `serpentrum/__init__.py`. Module level is stdlib-only; `pymol`/`pmg_tk` allowed ONLY lazily inside function bodies (`_anchor()`, `__init_plugin__()`, `run_plugin_gui()`).

**Adding a module:** a new GUI or BRIDGE module MUST be deliberately added to `GUI_MODULES` / `BRIDGE_MODULES` in `tools/check_purity.py` (entries carry inert-first comments for files not yet landed). Everything unrecognized defaults PURE. The `.exec_()` ban is global (**modeless rule**) — use `.show()` only.

**"Thin shell" rule:** GUI/bridge modules must not re-implement decisions. `serpentrum/xtb_runner.py:3` states "every RULE lives in `serpentrum/xtb_run.py` ... this module only wires Qt." `serpentrum/pymol_bridge.py:12` states the bridge is thin because pure logic already lives in `molfile`/`setloader`/`cgo_build`/`setup_logic`/`xtb_run`. `serpentrum/gui_plot.py:4` similarly consumes namedtuples built by PURE `plot_logic` and NEVER recomputes.

**Commit-time purity gate:** before committing in WSL, run `python3.6 tests/run_gates.py` (default: syntax walk + plugin-path safety + AST purity + scoped unittest discovery) from the repo root. `--smoke` adds headless Windows PyMOL smokes; `--xtb` adds the Windows-xtb-from-WSL probe.

## Plugin-Path Safety (hard rules)

The dev install points PyMOL's plugin loader at the repo root, so:

- **NO `__init__.py`** in `tests/`, `smoke/`, or `tools/` (`SAFETY_DIRS`, `tests/run_gates.py:52`).
- **NO top-level `*.py`** at the repo root (`tests/run_gates.py:105-110`) — `findPlugins` would autoload it as a plugin at GUI startup.

Gate 1 enforces both. The current tree has none.

## Naming Patterns

**Files (modules):**
- `snake_case.py` under `serpentrum/` (29 modules).
- Layer-suffix convention: `*_logic.py` = PURE decision half (`setup_logic.py`, `hud_logic.py`, `plot_logic.py`); `xtbenv.py` / `xtb_run.py` = PURE pure-core; `pymol_bridge.py` = the single cmd seam; `gui*.py` = GUI widgets (`gui.py`, `gui_setup.py`, `gui_game.py`, `gui_plot.py`, `gui_spectra.py`); `*_ui.py` = pure presentational helpers (`spectra_ui.py`).
- `input.py` is the BRIDGE keyboard wizard, imported aliased as `srp_input` to avoid shadowing the builtin (`smoke/manual_wizard_keys_check.py:59`).

**Functions/methods:** `snake_case`. Private helpers get a leading underscore (`_anchor`, `_line_error`, `_resolve_root`, `_stable_base`, `_fail_before_start`, `_read`, `_method_body`).

**Classes:** `CamelCase` (`XtbRunController`, `PluginDialog`, `KeySteerWizard`, `SetupTab`, `SpectraTab`, `IrPlotWidget`, `SpectraPlotPanel`). Exception classes end in `Error` (`XyzError`, `MolFileError`, `SetupError`, `SpectraParseError`, `DataError`).

**Constants:** `UPPER_SNAKE_CASE` module-level constants, frequently documented inline: `SRP_PREFIX`, `HESSIAN_WARNING`, `XTB_OHESS`, `EXPECTED_FILES`, `DEFAULT_THREAD_ARG`, `SPECTRA_RUN_KEYS`, `ROW_FORMAT`, `ELEMENT_SYMBOLS` (`frozenset`), `_LOG_TAIL`.

**PyMOL object names — `srp_` prefix reservation (hard rule):**
- `srp_` is RESERVED for game-generated PyMOL objects (`serpentrum/pymol_bridge.py`). Users must NOT name their own objects `srp_*` (PyMOL has no undo — PITFALLS.md F17).
- `cleanup_srp()` deletes every `srp_*` object by name pattern and is a pure function of object names (fresh-process safe after `.pse` reload, INFRA-04) — see the survival assertion in `smoke/14_release_e2e_smoke.py:347-361`.
- Canonical names: `BOX_NAME = 'srp_box'`, `HEAD_NAME = 'srp_head'`.
- `xtbenv.new_run_dir` uses `tempfile.mkdtemp(prefix='srp_', dir=base_dir)` so scratch dirs are identifiable.

**Test module naming:** `tests/test_<module_or_concern>.py` — matches the module under test (`test_xyzio.py`, `test_xtbenv.py`, `test_plot_logic.py`) or the concern (`test_purity_gates.py`, `test_integration_pure_core.py`, `test_gui_pins.py`, `test_docs_audit.py`). **47 such files.**

**Smoke naming:** `smoke/NN_name_smoke.py` with zero-padded `NN`. Manual (non-auto-run) harnesses deliberately drop the `NN_` prefix so `run_gates.py --smoke`'s `[0-9][0-9]_*.py` glob never picks them up: `smoke/manual_plot_check.py`, `smoke/manual_wizard_keys_check.py`.

## Code Style

**Formatting:** no `black`/`ruff`/`flake8` config and no `.prettierrc`; style is enforced by convention + the gates. Observed: single quotes for strings, 4-space indent, lines wrapped ~79-95 cols, module-level constants separated by blank lines from imports.

**Linting:** no ESLint/pylint config; `# noqa: E402` is used on post-`sys.path` imports (158 occurrences across `tests/`, `smoke/`, `tools/`). AST purity is the real semantic linter.

## Import Organization

Observed ordering in `serpentrum/` modules:
1. stdlib (`import os`, `import shutil`, `import collections`, `import tempfile`)
2. blank line
3. viewer (`from pymol.Qt import QtCore` in GUI, `from pymol import cmd` in BRIDGE only)
4. blank line
5. intra-package relative imports (`from . import xtb_run`, `from . import xtbenv`, `from .gui_setup import SetupTab`)

Example: `serpentrum/xtb_runner.py:36-42`, `serpentrum/gui.py:16-28`, `serpentrum/pymol_bridge.py:52-55`.

In `tests/`, `smoke/`, and `tools/`, the `sys.path.insert` self-insert precedes local imports; every import after it carries `# noqa: E402`. Example `tests/test_xyzio.py:13-25`:
```python
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from serpentrum import xyzio  # noqa: E402
```
This self-insert is a mandated per-file convention (`tests/test_skeleton.py:8-11`). Tests importing `tools/` modules insert both `REPO_ROOT` and `REPO_ROOT/tools` (`tests/test_docs_audit.py:24-28`, `tests/test_audit_requirements.py:20-24`).

**No path aliases** (no `setup.py`/`pyproject.toml` packaging, no `pytest.ini`).

## Error Handling

**Typed `ValueError` subclasses for domain errors** — one per pure subsystem:
- `XyzError(ValueError)` — `serpentrum/xyzio.py:63`; message names the 1-based line number and quotes ~60 chars of the offending line via `_line_error`.
- `MolFileError(ValueError)` — `serpentrum/molfile.py:50`
- `SetupError(ValueError)` — `serpentrum/setup_logic.py:146`
- `SpectraParseError(ValueError)` — `serpentrum/spectra.py:41`
- `DataError(ValueError)` — `serpentrum/molecule_data.py:49`

**Validation helpers return problem-string LISTS, not exceptions.** `xtbenv.validate_binary_path` and `xtbenv.evaluate_run` accumulate human-readable strings (`RunVerdict.problems`), one per failed check; empty list = valid (`serpentrum/xtbenv.py:51-138`). This "accumulate all problems" idiom is preferred over fail-fast for user-facing validation.

**`raise ... from` is NOT used**; the code uses bare `raise X(...)` with descriptive `%`-formatted messages, often via a helper (`_line_error` in `xyzio.py`).

**Guarded no-ops over exceptions at API boundaries** — `XtbRunController.start()` returns `False` and routes through `_fail_before_start` instead of raising, so UI state never sticks at `'running'` (`serpentrum/xtb_runner.py:135-171`). Runner failures are recorded as data, not propagated.

**Subprocess error paths** (`serpentrum/xtb_runner.py`):
- Signals are connected BEFORE `proc.start()` (`xtb_runner.py:189-197`) because `errorOccurred(FailedToStart)` fires synchronously inside `start()`.
- Qt enum matching: `QtCore.QProcess.NotRunning`, `QtCore.QProcess.*` — never magic ints.
- stderr is accumulated VERBATIM (CRLF intact) and never pre-filtered; the 3-leg verdict (`xtbenv.evaluate_run`) checks exit code + `'normal termination'` + expected files, with `'abnormal termination'` tested BEFORE `'normal termination'` because the latter is a substring.
- `tests/run_gates.py:249-255` catches `OSError`/`TimeoutExpired` on the xtb exec.

**Cleanup guarantees:**
- Tests use `self.addCleanup(shutil.rmtree, root, True)` / `tempfile.mkdtemp` (21 `addCleanup` calls). Never shell `rm` (opencode.json denies it).
- Runner deletes its spray dir on EVERY terminal branch with `shutil.rmtree(..., ignore_errors=True)`, and only after `finished()` (pre-finished rmtree is a WinError 32 race — `serpentrum/xtb_runner.py:328-332`).
- Guarded prefix check before any `rmtree` on user-set dirs: only delete under the resolved stable base (`_drop_prior_stable_dir`, `xtb_runner.py:227-250`).

## Logging

**Framework:** none in `serpentrum/`. Zero `import logging` and zero `print()` in `serpentrum/*.py` — the GUI owns status reporting (`serpentrum/pymol_bridge.py:48`). Log messages are data lines assembled by pure `hud_logic.py` builders and rendered by the GUI. Smokes and CLI tools print with `flush=True` only (mandatory: stdout is block-buffered when piped, and unflushed prints are lost on a Qt C-abort).

## Comments

**When to Comment:** comments are heavy and traceable — they cite pitfall/plan/research IDs and explain WHY (not what): `# connect-before-start (BINDING, smoke 09 live pin)` (`xtb_runner.py:189`), `# bounded tail (_LOG_TAIL)` (`xtb_runner.py:282`), `# CRLF must be retained end-to-end` (`tests/test_xtbenv.py:50`).

**Docstrings:** mandatory and verbose at module level. All 29 `serpentrum/*.py` modules open with a multi-paragraph triple-quoted docstring covering purpose, purity class, pitfalls, research/plan provenance (IDs like `06-RESEARCH-runner.md Q2`, `PITFALLS.md:64`, `plan 04-05`), and the Python-3.6 statement. Examples: `serpentrum/xyzio.py:1-29`, `serpentrum/xtb_runner.py:1-34`, `serpentrum/pymol_bridge.py:1-50`, `serpentrum/xtbenv.py:1-26`, `serpentrum/gui.py:1-14`. Function/method docstrings are the norm, documenting contracts, parameters, return values, and failure modes (e.g. `xtbenv.evaluate_run`).

**Assertion messages** are inline diagnostics with `%`-formatting: `assert data[:4] == PNG_MAGIC, 'first bytes %r != PNG magic' % (data[:4],)` (`smoke/14_release_e2e_smoke.py:308`).

**No `if __name__ == '__main__'` in `serpentrum/`** — the package is import-only; entry is via PyMOL's loader. Test files, smokes, and tools DO use it.

## Function Design

- **Small functions:** bridge functions are "<= ~15 lines" by policy (`serpentrum/pymol_bridge.py:49`).
- **Explicit returns** and documentation of return shape (often a tuple or namedtuple).
- **No class-level mutable defaults.**
- **Relative imports within the package** (`from . import ...`), absolute only in tests/smokes/tools.
- **Constants module-level and immutable where possible**: `frozenset` for symbol sets and terminal-state sets (`serpentrum/xyzio.py:34`).

## Module Design

**Exports:** modules expose plain functions/classes; no `__all__` declarations observed. Package entry (`serpentrum/__init__.py`) exports `_anchor`, `__init_plugin__`, `run_plugin_gui` and lazy-imports `pymol`/`pmg_tk` inside functions.

**State anchor (single-instance rule):** never store live plugin state in module globals. The single anchor is `pmg_tk.startup._serpentrum`, created/returned by `serpentrum/__init__.py:_anchor()`. Module-global state would duplicate on Plugin-Manager `importlib.reload` or a second import name; `pmg_tk.startup` package attributes survive both. Live state fields include `dialog`, `controller`, `setup`, `game_session`, `records`, `stacking_data`, `last_run`, `spectra_run`, `spectra_runner`. GUI/runner modules read it via `getattr(anchor, '...', None)` guards (e.g. `serpentrum/gui.py`).

**Barrel files:** none — `tests/`, `smoke/`, `tools/` have no `__init__.py` by hard rule; `serpentrum/` has exactly one (`__init__.py`, the ENTRY module).

## UI / Qt Conventions

- Qt reaches code ONLY via `pymol.Qt` (never direct `PyQt5`).
- Widgets built in GUI modules; pure modules remain Qt-free.
- Signal wiring lives in the dialog/shell (`serpentrum/gui.py`); tabs emit intent signals and never reach up to the parent `QTabWidget`.
- Connect-before-start; one terminal branch clears all flags and emits exactly one terminal signal (`serpentrum/xtb_runner.py:284-341`).
- **Modeless rule:** main dialog opens via `.show()` ONLY — never `.exec_()`; the AST checker fails any `.exec_()` (INFRA-05), and `tests/test_gui_pins.py` source-pins the literal token out of the tree.
- Every QWidget/QPainter/font-touching headless smoke must first adopt-or-create a `QApplication` (font access with no app silently hard-kills the process, no traceback) — `smoke/12_plot_smoke.py:103-112`, `smoke/14_release_e2e_smoke.py:128-138`.

## Verify Before Commit (gates)

From the repo root in WSL:
```bash
python3.6 tests/run_gates.py          # Gate 1 syntax+safety, Gate 2 AST purity, Gate 3 scoped unittest
python3.6 tests/run_gates.py --smoke  # + Gate 4 headless Windows PyMOL smokes
python3.6 tests/run_gates.py --xtb    # + Gate 5 Windows xtb invoked from WSL
```

## Commit Style

**Conventional Commits with phase-plan scope.** Current-history types: `docs` (125), `feat` (65), `test` (38), `chore` (25), `fix` (18), `merge` (12). Live examples:
- `feat(08-10): implement requirements-ledger integrity checker (DOCS-05)`
- `test(08-10): add failing tests for requirements-ledger audit tool`
- `feat(08-09): Spectra done-state hint + GATE D imaginary_note log line`
- `docs(08-11): GATE V checkpoint prepared — preconditions green, awaiting owner sign-off`
- `feat(quick-001): exclude set_a biphenyl from head selection (combo filter + gameplay fallback)`
- `docs(quick-001): complete remove-biphenyl-from-gameplay-spawn-pool quick task`
- `chore: track oc stats` (non-phase chores omit scope)
- `merge: 5.1-03 hud_logic.speed_note builder (TDD)`

Format: `<type>(<NN-MM>|<NN>|<quick-NNN>): <lowercase description>`. Types in use: `feat`, `fix`, `docs`, `test`, `chore`. Planning docs under `.planning/` ARE committed (`commit_docs: true`, `.planning/config.json`).

## Code & UI Standards (spec.md constraints)

Code must be efficient, traceable, clean, and safe; the repo must be structured. UI must be simple and user-friendly, with clear but sufficient in-game explanation. Do NOT make up anything — all claims and citations must be verified.

---

*Convention analysis: 2026-10-02*
