# Testing Patterns

**Analysis Date:** 2026-09-27

## Test Framework

**Runner:** Python stdlib `unittest` ONLY. No pytest, no nose, no third-party test deps.

**Scoped discovery is mandatory** (`tests/run_gates.py:131-142`):
```bash
python3.6 -m unittest discover -s tests -p "test_*.py" -v
```
**Do NOT add `-t .`** — it fails on Python 3.6 because the start dir is deliberately not a package. (`tests/run_gates.py:16-19`, repeated in every test-file docstring.) Unscoped discovery would wander into `serpentrum/` and try to import `pymol` (unavailable in WSL).

**Run commands:**
```bash
python3.6 tests/run_gates.py            # default gates 1-3 (syntax + purity + unittest)
python3.6 tests/run_gates.py --smoke    # + gate 4: headless Windows PyMOL smokes
python3.6 tests/run_gates.py --xtb      # + gate 5: Windows xtb invoked from WSL
python3.6 -m unittest discover -s tests -p "test_xyzio.py" -v   # one file
```
Default gate battery runs **840 tests in ~3.0s** (verified: `Ran 840 tests in 2.998s / OK`).

**Tcl/Tcltest:** AGENTS.md mentions `tclsh`/`tcltest` availability, but there are **zero `.tcl` files** in first-party code (`serpentrum/`, `tests/`, `smoke/`, `tools/`). Not applicable.

**No assertion library beyond `unittest`**; 2,407 `self.assert*` calls, 53 `assertRaises`.

## Gate Battery (`tests/run_gates.py`, INFRA-06)

The single gate entry point. `ROOT` is resolved from the file's own location; `main()` `chdir`s to `ROOT` so subprocesses/cmd.exe inherit repo cwd.

**Gate 1 — syntax + plugin-path safety** (`gate_syntax_safety`, `run_gates.py:89-116`):
- `py_compile` walk (recursive) over `serpentrum/`, `tools/`, `tests/`, `smoke/`.
- Hard fails on any root-level `*.py` (the dev plugin path IS the repo root — `findPlugins` would autoload it as a plugin).
- Hard fails on `__init__.py` directly inside `tests/`, `smoke/`, `tools/` (`SAFETY_DIRS`).

**Gate 2 — purity (AST)** (`gate_purity`, `run_gates.py:119-128`): calls `tools/check_purity.check_tree(ROOT)`; any import-rule or `.exec_()` violation fails. Only files under `serpentrum/` are checked.

**Gate 3 — unittest** (`gate_unittest`, `run_gates.py:131-142`): subprocess `sys.executable -m unittest discover -s tests -p "test_*.py" -v`.

**Gate 4 — `--smoke`** (`gate_smoke`, `run_gates.py:161-198`): runs required headless Windows PyMOL smokes via `cmd.exe`. **Verdict = flushed `SMOKE-OK` sentinel present AND `SMOKE-FAIL` absent — NEVER exit codes** (exit codes through the `.bat` are always 0, even after a Qt C-abort; see `run_gates.py:155` and the smoke docstrings). A missing required smoke fails the gate. Informational smokes run if present but NEVER fail the gate.

**Gate 5 — `--xtb`** (`gate_xtb`, `run_gates.py:201-275`): direct WSL exec of the Windows `xtb.exe` via the repo-root symlink `xtb-6.7.1 -> /mnt/c/xtb-6.7.1`, with a `/mnt/c`-backed cwd and bare relative args (NO `cmd.exe`). Verdict asserts BOTH `'xtb version'` AND `'normal termination'` appear in output. Also sanity-checks `tools/winpath.to_windows_path(ROOT)` maps to `C:/...`.

**Exit code:** 0 when every default gate (and every required smoke, if `--smoke`) passes; 1 otherwise. A `=== GATE SUMMARY ===` block prints per-gate PASS/FAIL plus a `FAILURES (N)` list.

## Test File Organization

**Location:** separate `tests/` directory (NOT co-located).
**Naming:** `tests/test_<module_or_concern>.py`. **43 test files** (verified). Modules-by-test concentration: `molfile` (10 files' worth of coverage), `setloader`/`molecule_data`/`game_engine` (9 each), `stacking`/`spawn` (7 each).
**No `__init__.py`** in `tests/` (plugin-path safety; enforced by gate 1).
**Test classes:** `CamelCase`, almost always ending in `Test` (`TestWriteXyz`, `TestEvaluateRunFixtures`, `RealRepoCleanTest`, `TestEntryModule`).
**Footer:** every test file ends with `if __name__ == '__main__': unittest.main()` (verified: all 43).

**Per-file discovery docstring:** every test file opens with a docstring repeating the exact scoped discovery command and the `-t .` warning. Example `tests/test_xyzio.py:1-12`.

**Mandated sys.path self-insert** — 43/43 files (`tests/test_skeleton.py:8-11`, convention restated in every file):
```python
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import serpentrum  # noqa: E402
```
Imports after the insert carry `# noqa: E402` (112 occurrences).

## Test Structure

**Suite organization:** multiple focused `unittest.TestCase` subclasses per file, grouped by concern, each with a class docstring:
```python
class TestWriteXyz(unittest.TestCase):
    """Writer structure, row format, comment sanitization, validation."""
    def test_writer_structure_and_row_format(self):
        ...
class TestReadFixtures(unittest.TestCase):
    """Exact reads of the committed, xtb-accepted geometry fixtures."""
```
(`tests/test_xyzio.py:44,106`.)

**Setup/teardown:** `setUp` creates a `tempfile.mkdtemp` and registers cleanup via `self.addCleanup` (19 files with `setUp`, 20 `addCleanup` calls, 9 files using `tempfile`). **Never shell `rm`** (opencode.json denies it).
```python
def setUp(self):
    self.tmpdir = tempfile.mkdtemp(prefix='xyzio-rt-')
    self.addCleanup(shutil.rmtree, self.tmpdir, True)
```
(`tests/test_xyzio.py:197-199`.)

**Assertions:** `self.assertEqual/assertIn/assertAlmostEqual(delta=...)/assertRaises/assertTrue/assertFalse`. Float comparisons use `assertAlmostEqual(..., delta=1e-8)` or `places=8` (`tests/test_xyzio.py:213-219`). Multi-line assert messages pass a `name` label for parameterized loops (`test_xtbenv.py:52`).

**Helper functions over duplicated logic:** module-level private helpers used by many cases, e.g. `_assert_xyz_error(testcase, action, *needles)` (`tests/test_xyzio.py:31-41`) and `_err_text(name)` (`tests/test_xtbenv.py:38-41`).

## Mocking & Dependency Injection

**There is ZERO use of `unittest.mock` / `mock`** (0 matches across `tests/`). The project deliberately prefers **dependency injection with hand-written fakes**, because the "zero-stub rule" bans `sys.modules` stubbing of `pymol`/`Qt`.

**Pattern — injected callable fake** (`tests/test_xtbenv.py:139-155`):
```python
class _RecordingWhich(object):
    """Fake which_fn: records every query, returns canned answers.

    Dependency injection per plan 02-02 — NO xtb install needed and NO
    sys.modules stubs (the zero-stub rule bans pymol/Qt module stubbing;
    a plain injected callable is just a parameter).
    """
    def __init__(self, answers):
        self._answers = answers
        self.queries = []
    def __call__(self, name):
        self.queries.append(name)
        return self._answers.get(name)
```
Used as `xtbenv.detect_binary(configured_path=..., which_fn=fake)`.

**What to mock:** nothing via `mock`. **What to inject instead:** system-boundary callables (`which_fn`), and pure data (fixture bytes).
**What NOT to stub:** `pymol`/`pmg_tk`/`PyQt5` modules (banned). Consequently, **GUI and BRIDGE modules are never imported by WSL unit tests** — `tests/` imports only PURE modules (`molfile`, `setloader`, `molecule_data`, `game_engine`, `stacking`, `spawn`, `setup_logic`, `placement`, `orientation`, `hud_logic`, `xtbenv`, `xtb_run`, `xyzio`, `budget_guard`, `spectra`, `plot_logic`, `cgo_build`, `generic_stack`). GUI/BRIDGE behavior is pinned by headless smokes instead.

## Fixtures and Factories

**Two committed fixture roots, both read IN PLACE (no copies — parallel worktrees must see them):**

1. `tests/fixtures/` — project-owned:
   - `tests/fixtures/calib_snake_52.xyz`, `calib_snake_104.xyz` (calibration geometry).
   - `tests/fixtures/molfile/` — `acetate.sdf`, `benzene.mol2`, `benzene_naphthalene.sdf`, `benzene_noh.sdf`, `methane.sdf`.
   - `tests/fixtures/xtb/` — `g98.out`, `vibspectrum`, `xtbopt.xyz`, `phenol.xyz`, `co2.*`, `bad.*`, `dimer2.*`, etc.
   - `tests/fixtures/xtb/synthetic/` — clearly-labeled synthetic test artifacts with a provenance `README.md`. Rules (`tests/fixtures/xtb/synthetic/README.md`): every file states `# SYNTHETIC`, cites its source with line numbers, and **honestly omits unknown values rather than inventing them** (project "do NOT make up anything" rule).
2. `.planning/research/xtb-spike-fixtures/` — research-verified xtb output, read in place by `tests/test_xyzio.py:24`, `tests/test_xtbenv.py:32`, `tests/test_phase6_integration.py:63`. Fixture `.err` bytes are passed AS-IS (CRLF retained) to prove the substring-contract trap.

**No factory library / builder objects** — fixtures are committed real files; generated data uses `tempfile.mkdtemp`.

**Known trap documented in-code:** `tests/fixtures/xtb/dimer.xyz` is mislabeled (actually CO2, not phenol) — never mine it (`tests/fixtures/xtb/synthetic/README.md:32-36`).

## Smoke Tests (`smoke/`)

**13 numbered headless smokes:** `smoke/01_skeleton_smoke.py` through `smoke/13_mode_arrows_smoke.py`. The numbering-with-underscore name is what `run_gates.py --smoke` globs (`smoke/[0-9][0-9]_*.py`).

**10 REQUIRED smokes** (a missing one fails the gate — `run_gates.py:55-72`): `01_skeleton`, `03_viewer_bridge`, `04_demo_e2e`, `05_loop_camera`, `06_input`, `07_transform_sweep`, `08_stack_place`, `10_chain_count`, `12_plot`, `13_mode_arrows`. Informational (non-blocking): `02_dialog`, `09_qprocess`, `11_xtb_runner`.

**Invocation contract:** headless Windows PyMOL from WSL:
```bash
timeout 90 cmd.exe /c "C:\\src\\run-conda-pymol.bat -cq smoke\\01_skeleton_smoke.py"
```
(from repo root; cwd is `/mnt/c`-backed so `cmd.exe` inherits a `C:\` cwd; `SMOKE_TIMEOUT = 90`.)

**Sentinel protocol:** the `.bat` always exits 0, so verdicts are flushed text sentinels: `SMOKE-OK <TAG>` on success, `SMOKE-FAIL <stage>: ...` per failure, `SMOKE-END N failure(s)` otherwise. Every `print` carries `flush=True` because stdout is block-buffered when piped and unflushed prints are lost on abort (`smoke/01_skeleton_smoke.py:6-20`).

**Template (copied by every smoke, `smoke/01_skeleton_smoke.py:11-20`):**
- named step functions `s_<name>()` + a `check(name, fn)` runner that catches `Exception`, prints `SMOKE-FAIL`, appends to `FAILURES`.
- `flush=True` on every print.
- **NO widget construction** (headless C-abort is uncatchable) — images/data only.
- Never add `smoke/__init__.py`.
- **Never trust `__file__` under `-cq`** (it is PyMOL's launcher module, not the script) — resolve `ROOT` by validating candidates for `serpentrum/__init__.py` (`_resolve_root()`, copied verbatim across smokes).

**QApplication bootstrap requirement (load-bearing):** any smoke touching QPainter/fonts (`QFontMetrics`, `drawText`) MUST first adopt-or-create a `Q*Application`, because font access with no app silently hard-kills the process (no traceback). Pattern — `smoke/12_plot_smoke.py:103-112` stage 0:
```python
_APP = QtWidgets.QApplication.instance()
if _APP is None:
    _APP = QtWidgets.QApplication([])
print('STAGE0 APP', flush=True)
```
`smoke/02_dialog_smoke.py` and `smoke/12_plot_smoke.py` use this guard. `12_plot_smoke.py` stages: stage0 app, stage1 scene, stage2 PNG full, stage3 no labels, stage4 empty, stage5 options, cleanup.

**Manual (human-verify) harnesses — NOT smokes, never auto-run** (non-`NN_` name keeps them out of the gate glob):
- `smoke/manual_plot_check.py` — real Windows PyMOL GUI plot check (`run smoke\manual_plot_check.py`).
- `smoke/manual_wizard_keys_check.py` — arrow-key steering harness; stages demo set + KeySteerWizard and registers `srp_keys_off` to restore the prior wizard.

## Test Types

- **Unit tests:** the vast majority — pure logic (`game_engine`, `molfile`, `setloader`, `spectra`, `plot_logic`, `xyzio`, `xtbenv`, `xtb_run`, `budget_guard`, etc.), runnable in WSL with zero stubs. Example files: `tests/test_xyzio.py`, `tests/test_xtbenv.py`, `tests/test_plot_logic.py`, `tests/test_hud_logic.py`.
- **Integration tests (pure-core chain, ZERO stubs):** compose multiple shipped pure modules end-to-end on real fixture bytes — `tests/test_integration_pure_core.py`, `tests/test_phase5_integration.py`, `tests/test_phase51_integration.py`, `tests/test_phase52_integration.py`, `tests/test_phase6_integration.py`. Example chain in `test_phase6_integration.py:10-22`: `build_run_input -> xyzio round-trip -> budget_guard -> xtbenv.build_argv -> xtb_run state -> xtbenv.evaluate_run 3-leg contract -> record shape`.
- **Gate self-tests:** `tests/test_purity_gates.py` builds minimal `serpentrum/`-shaped trees under `tempfile.mkdtemp` and asserts exactly which violations the checker must report (or stay silent) — "the fixtures ARE the contract". Includes `RealRepoCleanTest.test_real_repo_clean` asserting the actual repo passes.
- **Headless Windows smokes:** viewer/GUI/Qt behavior (gate 4). No E2E browser/UI framework.
- **Real-GUI manual harnesses:** human-verify only.

## Common Patterns

**Error testing via typed domain exceptions:**
```python
def _assert_xyz_error(testcase, action, *needles):
    try:
        action()
    except xyzio.XyzError as exc:
        for needle in needles:
            testcase.assertIn(needle, message)
    else:
        testcase.fail('XyzError not raised (wanted message containing %r)' % (needles,))
```
(`tests/test_xyzio.py:31-41`.)

**Table-driven loops with a `name` label for shared failure output** (`tests/test_xtbenv.py:47-56`).

**Round-trip / fixed-point proofs** (writer output re-parses byte-identically) — `tests/test_xyzio.py:64-76,262-280`.

**Byte-exact fixture assertions** (`# SYNTHETIC`/provenance), asserting CRLF is retained (`assertIn('\r\n', text)`).

**Smoke staged pipelines with `check()` and sentinel epilogue** (`smoke/01_skeleton_smoke.py:112-130`).

## TDD Practice

The repo history shows a strict **RED / GREEN / REFACTOR** TDD rhythm for pure-core logic — commit subjects explicitly say "failing tests for X" (RED) followed by the implementation (GREEN):
- `test(07-06): failing tests for plot unit modes (absorbance/transmittance transforms)` → `feat(07-06): plot_logic unit modes ...`
- `test(07-02): failing tests for plot_logic (scene builder, nice ticks, presets, caption)` → `feat(07-02): plot_logic ...`
- `test(07-01): failing tests for spectra_ui ...` → `feat(07-01): spectra_ui ...`
- `test(06-01): failing tests for budget_guard ...`, `test(06-02): failing tests for xtb_run ...`
- `test(5.2-02): failing tests for generic_stack module ...`
- `merge: 5.1-03 hud_logic.speed_note builder (TDD)`

Tests are written against pure modules that need no `pymol`/`Qt` stubs — this purity is what makes the RED/GREEN loop runnable in ~3s under WSL `python3.6`. No coverage target is enforced; the gate demands all 840 tests pass.

---

*Testing analysis: 2026-09-27*
