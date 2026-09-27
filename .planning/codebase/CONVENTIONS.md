# Coding Conventions

**Analysis Date:** 2026-09-27

## Language & Runtime Constraints

**Target interpreter:** Python 3.6.9 ONLY (`python3.6`; the WSL dev shell). All first-party Python must import and compile under 3.6. `tests/run_gates.py` `py_compile`-walks `serpentrum/`, `tools/`, `tests/`, `smoke/` on every gate run, so 3.7+ syntax fails hard.

**Empirically verified style (greps of the actual tree):**

- **`%`-formatting exclusively — ZERO f-strings.** `grep` for f-strings in `serpentrum/*.py` returns 0 real matches. Every formatted string uses `'... %s' % (value,)`. Examples: `serpentrum/xyzio.py:78`, `serpentrum/xtb_runner.py:362`. Module docstrings explicitly state "no f-strings" (`serpentrum/xyzio.py:28`, `serpentrum/xtbenv.py`).
- **No walrus operator** (`:=` — 3.8+): zero matches.
- **No type hints / annotations**: zero `def ... ->` in `serpentrum/*.py`. Runtime duck typing throughout.
- **No dataclasses**: `namedtuple` is the record idiom instead. See `serpentrum/plot_logic.py:27` (`Scene`), `serpentrum/spectra.py:29,34,36` (`Mode`, `Atom`, `Spectrum`), `serpentrum/xtbenv.py:48` (`RunVerdict = collections.namedtuple(...)`). `serpentrum/setup_logic.py:23` documents "no dataclasses/walrus".
- **`super(ClassName, self).__init__(...)`** explicit form, not bare `super()` — e.g. `serpentrum/xtb_runner.py:100`, `serpentrum/gui.py:75`.
- **`object` base is sometimes explicit**: `class _SerpentrumState(object)` (`serpentrum/__init__.py:22`).
- **`str`/`bytes` handling is 3.6-safe**: `bytes(self._proc.readAllStandardOutput()).decode('utf-8', 'replace')` (`serpentrum/xtb_runner.py:262`); `open(..., encoding='utf-8')` explicit everywhere.

## Purity Layers (the load-bearing architectural convention)

Every module under `serpentrum/` belongs to exactly one purity class enforced by `tools/check_purity.py` (AST-based, run as gate 2 of `tests/run_gates.py`). Classification is by path in the checker's `GUI_MODULES` / `BRIDGE_MODULES` / `ENTRY_MODULE` sets:

- **PURE** (default-strict): no `pymol`, `pmg_tk`, `PyQt5`, or `numpy` anywhere (module level OR function bodies). All math/parsing/logic modules: `serpentrum/xyzio.py`, `serpentrum/xtb_run.py`, `serpentrum/xtbenv.py`, `serpentrum/spectra.py`, `serpentrum/plot_logic.py`, `serpentrum/game_engine.py`, `serpentrum/molfile.py`, `serpentrum/setup_logic.py`, etc.
- **BRIDGE**: allows `pymol`/`pmg_tk` at any level; bans `PyQt5`/`numpy` anywhere and bans `.exec_()`. Exactly two modules: `serpentrum/pymol_bridge.py`, `serpentrum/input.py`.
- **GUI**: allows ONLY `pymol.Qt` / `pymol.Qt.*` import forms; any bare `pymol`/`pmg_tk` is a violation. In `GUI_MODULES`: `serpentrum/gui.py`, `serpentrum/gui_setup.py`, `serpentrum/gui_game.py`, `serpentrum/xtb_runner.py`, `serpentrum/gui_plot.py`, `serpentrum/gui_spectra.py`.
- **ENTRY**: `serpentrum/__init__.py`. Module level is stdlib-only; `pymol`/`pmg_tk` allowed ONLY lazily inside function bodies (see `_anchor()` / `__init_plugin__()` / `run_plugin_gui()`).

**Adding a module:** a new GUI or BRIDGE module MUST be deliberately added to `GUI_MODULES` / `BRIDGE_MODULES` in `tools/check_purity.py` (they carry inert-first comments for files not yet landed). Everything unrecognized defaults PURE. The `.exec_()` ban is global (modeless rule) — use `.show()` only.

**"Thin shell" rule:** GUI modules must not re-implement decisions. `serpentrum/xtb_runner.py:3` states "every RULE lives in serpentrum/xtb_run.py ... this module only wires Qt." `serpentrum/pymol_bridge.py:12` states the bridge is thin because pure logic already lives in `molfile`/`setloader`/`cgo_build`/`setup_logic`.

## Naming Patterns

**Files (modules):**
- `snake_case.py` under `serpentrum/`.
- Layer-suffix convention: `*_logic.py` = PURE decision half (`setup_logic.py`, `hud_logic.py`, `plot_logic.py`); `*_run.py` / `xtbenv.py` = PURE pure-core; `pymol_bridge.py` = the single cmd seam; `gui*.py` = GUI widgets (`gui.py`, `gui_setup.py`, `gui_game.py`, `gui_plot.py`, `gui_spectra.py`); `*_ui.py` = pure presentational helpers (`spectra_ui.py`).
- `input.py` is the BRIDGE keyboard wizard, imported aliased as `srp_input` to avoid shadowing the builtin (`smoke/manual_wizard_keys_check.py:59`).

**Functions/methods:** `snake_case`. Private helpers get a leading underscore (`_anchor`, `_line_error`, `_resolve_root`, `_stable_base`, `_fail_before_start`). There are 155 private defs across `serpentrum/`.

**Classes:** `CamelCase` (`XtbRunController`, `PluginDialog`, `KeySteerWizard`, `SetupTab`, `SpectraTab`). Exception classes end in `Error`.

**Constants:** `UPPER_SNAKE_CASE` module-level constants (83 across `serpentrum/`), frequently documented inline: `SRP_PREFIX`, `HESSIAN_WARNING`, `XTB_OHESS`, `EXPECTED_FILES`, `DEFAULT_THREAD_ARG`, `SPECTRA_RUN_KEYS`.

**PyMOL object names — `srp_` prefix reservation (hard rule):**
- `srp_` is RESERVED for game-generated PyMOL objects (`serpentrum/pymol_bridge.py:30-36,61`). Users must NOT name their own objects `srp_*`.
- `cleanup_srp()` deletes every `srp_*` object by name pattern and is a pure function of object names (fresh-process safe after `.pse` reload, INFRA-04).
- Canonical names: `BOX_NAME = 'srp_box'`, `HEAD_NAME = 'srp_head'` (`serpentrum/pymol_bridge.py:69-70`); further `srp_*` names are generated for game objects.
- `xtbenv.new_run_dir` uses `tempfile.mkdtemp(prefix='srp_', dir=base_dir)` so scratch dirs are identifiable (`serpentrum/xtbenv.py:207`).

**Test module naming:** `tests/test_<module_or_concern>.py`, matching the module under test (`test_xyzio.py`, `test_xtbenv.py`, `test_plot_logic.py`) or the concern (`test_purity_gates.py`, `test_integration_pure_core.py`, `test_phase6_integration.py`). 43 such files.

**Smoke naming:** `smoke/NN_name_smoke.py` with zero-padded `NN`. Manual (non-auto-run) harnesses deliberately drop the `NN_` prefix so `run_gates.py --smoke`'s `[0-9][0-9]_*.py` glob never picks them up: `smoke/manual_plot_check.py`, `smoke/manual_wizard_keys_check.py`.

## Import Organization

Observed ordering in `serpentrum/` modules:
1. stdlib (`import os`, `import shutil`, `import collections`, `import tempfile`)
2. blank line
3. third-party / viewer (`from pymol.Qt import QtCore` or `from pymol import cmd` in BRIDGE modules only)
4. blank line
5. intra-package relative imports (`from . import xtb_run`, `from . import xtbenv`)

Example: `serpentrum/xtb_runner.py:36-42`, `serpentrum/pymol_bridge.py:52-55`, `serpentrum/gui.py:16-28`.

In `tests/` and `smoke/`, the `sys.path.insert` self-insert precedes local imports; every import after it carries `# noqa: E402` (112 occurrences). Example `tests/test_xyzio.py:13-25`:
```python
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from serpentrum import xyzio  # noqa: E402
```
This self-insert is a mandated per-file convention (`tests/test_skeleton.py:8-11`).

**No path aliases** (no `setup.py`/`pyproject.toml` packaging, no `pytest.ini`).

## Error Handling

**Typed `ValueError` subclasses for domain errors** — one per pure subsystem:
- `serpentrum/xyzio.py:63` `XyzError(ValueError)` — message names the 1-based line number and quotes ~60 chars of the offending line.
- `serpentrum/molfile.py:50` `MolFileError(ValueError)`
- `serpentrum/setup_logic.py:138` `SetupError(ValueError)`
- `serpentrum/spectra.py:41` `SpectraParseError(ValueError)`
- `serpentrum/molecule_data.py:49` `DataError(ValueError)`

**Validation helpers return problem-string LISTS, not exceptions.** `xtbenv.validate_binary_path` and `xtbenv.evaluate_run` accumulate human-readable strings (`RunVerdict.problems`), one per failed check; empty list = valid. See `serpentrum/xtbenv.py:51-138`. This "accumulate all problems" idiom is preferred over fail-fast for user-facing validation.

**`raise ... from` is NOT used**; the code uses bare `raise X(...)` with descriptive `%`-formatted messages, often via a helper (`_line_error` in `xyzio.py`).

**Guarded no-ops over exceptions at API boundaries** — `XtbRunController.start()` returns `False` and routes through `_fail_before_start` instead of raising, so UI state never sticks at `'running'` (`serpentrum/xtb_runner.py:135-171`). Runner failures are recorded as data, not propagated.

**Subprocess error paths** (`serpentrum/xtb_runner.py`):
- Signals are connected BEFORE `proc.start()` (`xtb_runner.py:189-197`) because `errorOccurred(FailedToStart)` fires synchronously inside `start()`.
- Qt enum matching: `QtCore.QProcess.NotRunning`, `QtCore.QProcess.*` — never magic ints.
- stderr is accumulated VERBATIM (CRLF intact) and never pre-filtered; the 3-leg verdict (`xtbenv.evaluate_run`) checks exit code + `'normal termination'` + expected files, with `'abnormal termination'` tested BEFORE `'normal termination'` because the latter is a substring (`serpentrum/xtbenv.py:90-102`).
- `tests/run_gates.py:249-251` catches `OSError`/`TimeoutExpired` on the xtb exec.

**Cleanup guarantees:**
- Tests use `self.addCleanup(shutil.rmtree, root, True)` / `tempfile.mkdtemp` — 20 `addCleanup` calls across 19 `setUp`s. Never shell `rm` (opencode.json denies it).
- Runner deletes its spray dir on EVERY terminal branch with `shutil.rmtree(..., ignore_errors=True)`, and only after `finished()` (pre-finished rmtree is a WinError 32 race — `serpentrum/xtb_runner.py:328-332`).
- Guarded prefix check before any `rmtree` on user-set dirs: only delete under the resolved stable base (`_drop_prior_stable_dir`, `xtb_runner.py:227-250`).

## State Handling (single-instance anchor rule)

**Never store live plugin state in module globals.** The single anchor is `pmg_tk.startup._serpentrum`, created/returned by `serpentrum/__init__.py:_anchor()`. Module-global state would duplicate on Plugin-Manager `importlib.reload` or a second import name; `pmg_tk.startup` package attributes survive both. Live state fields include `dialog`, `controller`, `setup`, `game_session`, `records`, `stacking_data`, `last_run`, `spectra_run`, `spectra_runner` (all documented in `serpentrum/__init__.py:22-63`). GUI/runner modules read it via `getattr(anchor, '...', None)` guards (e.g. `serpentrum/gui.py:193,198,254`). `XtbRunController` explicitly "touches NO module globals" (`serpentrum/xtb_runner.py:102`).

**Modeless rule:** main dialog opens via `.show()` ONLY — never `.exec_()`; the AST checker fails any `.exec_()` (INFRA-05). See `serpentrum/__init__.py:84`.

## Docstrings & Comments

**Module docstrings are mandatory and verbose.** Nearly every `serpentrum/` module opens with a multi-paragraph triple-quoted docstring covering: purpose, purity class, pitfalls, research/plan provenance (IDs like `06-RESEARCH-runner.md Q2`, `PITFALLS.md:64`, `plan 04-05`), and the Python-3.6 statement. Examples: `serpentrum/xyzio.py:1-29`, `serpentrum/xtb_runner.py:1-34`, `serpentrum/pymol_bridge.py:1-50`, `serpentrum/xtbenv.py:1-26`.

**Function/method docstrings are the norm**, documenting contracts, parameters, return values, and failure modes. E.g. `xtbenv.evaluate_run` (`serpentrum/xtbenv.py:51-83`) enumerates every problem string.

**Comments are heavy and traceable.** They cite pitfall/plan/research IDs and explain WHY (not what): `# connect-before-start (BINDING, smoke 09 live pin)` (`xtb_runner.py:189`), `# bounded tail (_LOG_TAIL)` (`xtb_runner.py:282`), `# CRLF must be retained end-to-end` (`tests/test_xtbenv.py:50`). Assertion messages are inline diagnostics with `%`-formatting (`assert data[:4] == PNG_MAGIC, 'first bytes %r != PNG magic' % (...)` — `smoke/12_plot_smoke.py:98`).

**No `logging` module usage** anywhere in `serpentrum/`; **no `print()`** in `serpentrum/` (0 matches) — the GUI owns status reporting (`serpentrum/pymol_bridge.py:48`). Smokes/CLI tools print with `flush=True` only.

**No `if __name__ == '__main__'` in `serpentrum/`** — the package is import-only; entry is via PyMOL's loader.

## Function & Module Design

- **Small functions:** bridge functions are "<= ~15 lines" by policy (`serpentrum/pymol_bridge.py:49`).
- **Explicit returns** and documentation of return shape (often a tuple or namedtuple).
- **No class-level mutable defaults.**
- **Relative imports within the package** (`from . import ...`), absolute only in tests/smokes.
- **Constants module-level and immutable where possible**: `frozenset` for symbol sets and terminal-state sets (`serpentrum/xyzio.py:34`, `serpentrum/xtb_run.py:61`).

## UI / Qt Conventions

- Qt reaches code ONLY via `pymol.Qt` (never direct `PyQt5`).
- Widgets built in GUI modules; pure modules must remain Qt-free.
- Signal wiring lives in the dialog/shell (`serpentrum/gui.py:111-118,311-313`); tabs emit intent signals (`run_again_requested`) and never reach up to the parent `QTabWidget`.
- Connect-before-start; one terminal branch clears all flags and emits exactly one terminal signal (bioCHEMeleon discipline — `serpentrum/xtb_runner.py:284-341`).
- Every QWidget-touching headless smoke must first adopt-or-create a `QApplication` (font access with no app silently hard-kills the process) — `smoke/12_plot_smoke.py:103-112`.

## Commit Style

**Conventional Commits with phase-plan scope.** Live history:
- `feat(07-09): frequency table — every mode listed ...`
- `test(07-06): smoke 12 options leg ...`
- `docs(07): complete spectra-ui phase` (phase-only scope allowed for phase-level docs)
- `fix(07-10): sticks sweep before mode vectors ...`
- `chore: track oc stats` (non-phase chores omit scope)

Format: `<type>(<NN-MM>|<NN>): <lowercase description>`. Types in use: `feat`, `fix`, `docs`, `test`, `chore`. Merge commits: `merge: wave N exec/NN-MM into main (...)`. Planning docs under `.planning/` ARE committed (`commit_docs: true`, `.planning/config.json`).

---

*Convention analysis: 2026-09-27*
