# Testing Patterns

**Analysis Date:** 2026-10-02

## Test Framework

**Runner:** Python stdlib `unittest` ONLY. No pytest, no nose, no third-party test deps. `tests/` has **47 test files** and **233 `TestCase` classes**; ~**2,576 `self.assert*`** calls (1,305 `assertEqual`, 263 `assertAlmostEqual`, 214 `assertIn`, 179 `assertTrue`, 110 `assertFalse`, 69 `assertIsNone`, 68 `assertIsNotNone`, 55 `assertRaises`, 54 `assertNotIn`, 51 `assertIs`, 46 `assertIsInstance`, etc.).

**Scoped discovery is mandatory** (`tests/run_gates.py:135-146`):
```bash
python3.6 -m unittest discover -s tests -p "test_*.py" -v
```
**Do NOT add `-t .`** — it fails on Python 3.6 because the start dir is deliberately not a package. Unscoped discovery would wander into `serpentrum/` and try to import `pymol` (unavailable in WSL).

**Run commands:**
```bash
python3.6 tests/run_gates.py            # default gates 1-3 (syntax + safety + purity + unittest)
python3.6 tests/run_gates.py --smoke    # + gate 4: headless Windows PyMOL smokes
python3.6 tests/run_gates.py --xtb      # + gate 5: Windows xtb invoked from WSL
python3.6 -m unittest discover -s tests -p "test_xyzio.py" -v   # one file
```
Default battery runs **937 tests in ~4.4s** (verified 2026-10-02: `Ran 937 tests in 4.427s / OK`, `run_gates: all gates green`).

**Tcl/Tcltest:** `tclsh` (Tcl 8.5/8.6) is available in WSL for `tcltest` pure-layer unit tests, but there are **zero `.tcl` files** in first-party code (`serpentrum/`, `tests/`, `smoke/`, `tools/`). Not applicable to the current tree.

**Gate gates from AGENTS.md:** every phase runs the gate battery from the repo root in WSL before committing.

## Gate Battery (`tests/run_gates.py`, INFRA-06)

The single gate entry point. `ROOT` is resolved from the file's own location; `main()` `chdir`s to `ROOT` so subprocesses/cmd.exe inherit repo cwd.

**Gate 1 — syntax + plugin-path safety** (`gate_syntax_safety`, `run_gates.py:93-120`):
- `py_compile` walk (recursive) over `serpentrum/`, `tools/`, `tests/`, `smoke/`.
- Hard fails on any root-level `*.py` (the dev plugin path IS the repo root — `findPlugins` would autoload it as a plugin).
- Hard fails on `__init__.py` directly inside `tests/`, `smoke/`, `tools/` (`SAFETY_DIRS`).

**Gate 2 — purity (AST)** (`gate_purity`, `run_gates.py:123-132`): calls `tools/check_purity.check_tree(ROOT)`; any import-rule or `.exec_()` violation fails. Only files under `serpentrum/` are checked.

**Gate 3 — unittest** (`gate_unittest`, `run_gates.py:135-146`): subprocess `sys.executable -m unittest discover -s tests -p "test_*.py" -v`.

**Gate 4 — `--smoke`** (`gate_smoke`, `run_gates.py:165-202`): runs required headless Windows PyMOL smokes via `cmd.exe`. **Verdict = flushed `SMOKE-OK` sentinel present AND `SMOKE-FAIL` absent — NEVER exit codes** (exit codes through the `.bat` are always 0, even after a Qt C-abort; `run_gates.py:159-161`). A missing required smoke fails the gate. Informational smokes run if present but NEVER fail the gate.

**Gate 5 — `--xtb`** (`gate_xtb`, `run_gates.py:205-279`): direct WSL exec of the Windows `xtb.exe` via the repo-root symlink `xtb-6.7.1 -> /mnt/c/xtb-6.7.1`, with a `/mnt/c`-backed cwd and bare relative args (NO `cmd.exe`). Verdict asserts BOTH `'xtb version'` AND `'normal termination'` appear. Also sanity-checks `tools/winpath.to_windows_path(ROOT)` maps to `C:/...`.

**Exit code:** 0 when every default gate (and every required smoke, if `--smoke`) passes; 1 otherwise. A `=== GATE SUMMARY ===` block prints per-gate PASS/FAIL plus a `FAILURES (N)` list.

## Test File Organization

**Location:** separate `tests/` directory (NOT co-located).
**Naming:** `tests/test_<module_or_concern>.py`. **47 test files** (verified 2026-10-02). Examples: `tests/test_xyzio.py`, `tests/test_xtbenv.py`, `tests/test_plot_logic.py`, `tests/test_engine_core.py`, `tests/test_engine_turns.py`, `tests/test_spectra_broadening.py`, `tests/test_purity_gates.py`, `tests/test_gui_pins.py`, `tests/test_docs_audit.py`, `tests/test_audit_requirements.py`.
**No `__init__.py`** in `tests/` (plugin-path safety; enforced by gate 1).
**Test classes:** `CamelCase`, almost always ending in `Test` (`TestWriteXyz`, `TestEvaluateRunFixtures`, `RealRepoCleanTest`, `TestEntryModule`, `TestBottomRowContract`, `TestModelessBan`, `TestRunAllIntegration`).
**Footer:** every test file ends with `if __name__ == '__main__': unittest.main()` (verified: 47/47).

**Per-file discovery docstring:** every test file opens with a docstring repeating the exact scoped discovery command and the `-t .` warning, plus python3.6/%-formatting/purity notes. Examples `tests/test_xyzio.py:1-12`, `tests/test_skeleton.py:1-12`, `tests/test_audit_requirements.py:1-14`.

**Mandated sys.path self-insert** — 47/47 files (`tests/test_skeleton.py:13-19`):
```python
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import serpentrum  # noqa: E402
```
Imports after the insert carry `# noqa: E402` (158 occurrences across tests/smoke/tools). Tests importing `tools/` add a second insert (see `tests/test_docs_audit.py:24-28`).

**Pure-module import rule:** `tests/` imports ONLY PURE modules (19 distinct: `budget_guard`, `cgo_build`, `game_engine`, `generic_stack`, `help_text`, `hud_logic`, `molecule_data`, `molfile`, `orientation`, `placement`, `plot_logic`, `setloader`, `setup_logic`, `spawn`, `spectra`, `stacking`, `xtb_run`, `xtbenv`, `xyzio`). **GUI and BRIDGE modules are never imported by WSL unit tests** — GUI/BRIDGE behavior is pinned by source-text scans and headless smokes instead.

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

**Setup/teardown:** `setUp` creates a `tempfile.mkdtemp` and registers cleanup via `self.addCleanup` (21 `addCleanup` calls). **Never shell `rm`** (opencode.json denies it).
```python
def setUp(self):
    self.tmpdir = tempfile.mkdtemp(prefix='xyzio-rt-')
    self.addCleanup(shutil.rmtree, self.tmpdir, True)
```
(`tests/test_xyzio.py:197-199`; `tests/test_xtbenv.py:154-156`.)

**`setUpClass`** is used for one-time fixture loading (38 occurrences), e.g. `tests/test_docs_audit.py:79-82` reads all control-file sources once:
```python
@classmethod
def setUpClass(cls):
    cls.sources = dict((rel, _read(rel)) for rel in check_docs.CONTROL_FILES)
```

**Assertions:** `self.assertEqual/assertIn/assertAlmostEqual(...)/assertRaises/assertTrue/assertFalse/assertIsNone`. Float comparisons use `assertAlmostEqual(..., delta=1e-8)` or `places=8` (265 delta/places uses). Multi-line assert messages pass a `name` label for parameterized loops.

**Helper functions over duplicated logic:** module-level private helpers used by many cases (60 `^def _` helpers across tests), e.g. `_assert_xyz_error(testcase, action, *needles)` (`tests/test_xyzio.py:31-41`), `_err_text(name)` (`tests/test_xtbenv.py`), `_read(relpath)` (`tests/test_gui_pins.py:49-51`).

**Conditional skips:** 3 `skipUnless`/`skipIf` guards, used to skip cleanly until real data lands — e.g. `tests/test_demo_data.py` skips while the 5 PubChem SDFs + manifest are absent and hard-passes once they exist.

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

**What to mock:** nothing via `mock`. **What to inject instead:** system-boundary callables (`which_fn`, an `exists` predicate) and pure data (fixture bytes/text). `tests/test_docs_audit.py:165-175` injects an `_exists` callable into `check_docs.check_paths`; the docs-audit checks take injectable `text`/`sources` params so tamper fixtures never touch the repo.

**What NOT to stub:** `pymol`/`pmg_tk`/`PyQt5` modules (banned). Consequently GUI/BRIDGE behavior is pinned by headless smokes (gate 4) and source-text scans, never imported in WSL unit tests.

## Fixtures and Factories

**Two committed fixture roots, both read IN PLACE (no copies — parallel worktrees must see them):**

1. `tests/fixtures/` — project-owned:
   - `tests/fixtures/calib_snake_52.xyz`, `calib_snake_104.xyz` (calibration geometry).
   - `tests/fixtures/molfile/` — `acetate.sdf`, `benzene.mol2`, `benzene_naphthalene.sdf`, `benzene_noh.sdf`, `methane.sdf`.
   - `tests/fixtures/xtb/` — `g98.out`, `vibspectrum`, `xtbopt.xyz`, `phenol.xyz`, `co2.*`, `bad.*`, `dimer2.*`, `ohess.*`, `repro_oh.*`, etc.
   - `tests/fixtures/xtb/synthetic/` — clearly-labeled synthetic test artifacts with a provenance `README.md`. Rules: every file states `# SYNTHETIC`, cites its source with line numbers, and **honestly omits unknown values rather than inventing them** (project "do NOT make up anything" rule).
2. `.planning/research/xtb-spike-fixtures/` — research-verified xtb output, read in place by `tests/test_xyzio.py:24`, `tests/test_xtbenv.py`, `tests/test_phase6_integration.py`. Fixture `.err` bytes are passed AS-IS (CRLF retained) to prove the substring-contract trap.

**In-test string fixtures:** docs/tooling tests embed markdown/README fixtures built by mutating real text at test time and inject them into the checker, NEVER touching the live file — `tests/test_docs_audit.py` (tamper fixtures), `tests/test_audit_requirements.py:51-70` (`_build(statuses, boxes, evidence)` embedded ledger markdown), `tests/test_purity_gates.py` (builds minimal `serpentrum/`-shaped trees under `tempfile.mkdtemp`).

**No factory library / builder objects** — fixtures are committed real files; generated data uses `tempfile.mkdtemp`.

**Known trap documented in-code:** `tests/fixtures/xtb/dimer.xyz` is mislabeled (actually CO2, not phenol) — never mine it (`tests/fixtures/xtb/synthetic/README.md`; restated in `tests/test_xyzio.py:8-11`).

## Source-Text Pins (GUI/BRIDGE testing without a QApplication)

Because headless widget construction is a dead end (decision 01-05; smoke 02 re-probed dead 2026-09-28), GUI contracts are pinned as SOURCE TEXT read with `open().read()` and asserted with `assertIn`/`assertNotIn`/`.count()`:

- `tests/test_gui_pins.py` — 6-button bottom-row labels appear in spec order (`gui.py`), exactly one `setCurrentIndex(1)`, zero blocking-modal tokens across `serpentrum/*.py` (token written split `'ex' + 'ec_'` so the test file stays clean), removed temp-row control named nowhere, internal paths survive, eager head-population call-site.
- `tests/test_hud_content.py` — counts call forms (`stack_mode_note(`, `generic_consent_note(`, `speed_note(`) exactly once; `_gui_game_source()` helper (house source-scan pattern from plans 5.1-05/5.2-06).
- `tests/test_help_text.py` — pure `help_text` module content.

## Smoke Tests (`smoke/`)

**14 numbered headless smokes:** `smoke/01_skeleton_smoke.py` through `smoke/14_release_e2e_smoke.py`. The numbering-with-underscore name is what `run_gates.py --smoke` globs (`smoke/[0-9][0-9]_*.py`).

**11 REQUIRED smokes** (a missing one fails the gate — `run_gates.py:55-76`): `01_skeleton`, `03_viewer_bridge`, `04_demo_e2e`, `05_loop_camera`, `06_input`, `07_transform_sweep`, `08_stack_place`, `10_chain_count`, `12_plot`, `13_mode_arrows`, `14_release_e2e`. Informational (non-blocking): `02_dialog`, `09_qprocess`, `11_xtb_runner`.

**Invocation contract:** headless Windows PyMOL from WSL:
```bash
timeout 90 cmd.exe /c "C:\\src\\run-conda-pymol.bat -cq smoke\\01_skeleton_smoke.py"
```
(from repo root; cwd is `/mnt/c`-backed so `cmd.exe` inherits a `C:\` cwd; `SMOKE_TIMEOUT = 90`.)

**Sentinel protocol:** the `.bat` always exits 0, so verdicts are flushed text sentinels: `SMOKE-OK <TAG>` on success, `SMOKE-FAIL <stage>: ...` per failure, `SMOKE-END N failure(s)` otherwise. Every `print` carries `flush=True` because stdout is block-buffered when piped and unflushed prints are lost on abort (`smoke/01_skeleton_smoke.py`, `smoke/14_release_e2e_smoke.py:6-44`).

**Template (copied by every smoke):**
- named step functions `s_<name>()` + a `check(name, fn)` runner that catches `Exception`, prints `SMOKE-FAIL`, appends to `FAILURES` (`smoke/14_release_e2e_smoke.py:88-93`).
- `flush=True` on every print.
- **NO widget construction** (headless C-abort is uncatchable) — images/data and module seams only.
- Never add `smoke/__init__.py`.
- **Never trust `__file__` under `-cq`** (it is PyMOL's launcher module, not the script) — resolve `ROOT` by validating candidates for `serpentrum/__init__.py` (`_resolve_root()`, copied verbatim across smokes; `smoke/14_release_e2e_smoke.py:51-68`).

**QApplication bootstrap requirement (load-bearing):** any smoke touching QPainter/fonts (`QFontMetrics`, `drawText`) MUST first adopt-or-create a `Q*Application`, because font access with no app silently hard-kills the process (no traceback). Pattern — `smoke/14_release_e2e_smoke.py:128-138` stage 0:
```python
_APP = QtWidgets.QApplication.instance()
if _APP is None:
    _APP = QtWidgets.QApplication([])
print('STAGE0 APP', flush=True)
```
`smoke/12_plot_smoke.py` stages: stage0 app, stage1 scene, stage2 PNG full, stage3 no labels, stage4 empty, stage5 options, cleanup. `smoke/14_release_e2e_smoke.py` stages: stage0 app, stage1 setup records, stage2 materialize, stage3 scripted win, stage4 xyz handoff, stage5 spectra tail, stage6 PNG, stage7 setup round-trip, stage8 cleanup.

**Manual (human-verify) harnesses — NOT smokes, never auto-run** (non-`NN_` name keeps them out of the gate glob, `run_gates.py:171`):
- `smoke/manual_plot_check.py` — real Windows PyMOL GUI plot check.
- `smoke/manual_wizard_keys_check.py` — arrow-key steering harness; stages demo set + KeySteerWizard and registers `srp_keys_off` to restore the prior wizard.

## Test Types

- **Unit tests:** the vast majority — pure logic (`game_engine`, `molfile`, `setloader`, `spectra`, `plot_logic`, `xyzio`, `xtbenv`, `xtb_run`, `budget_guard`, `stacking`, `spawn`, `orientation`, `placement`, `hud_logic`, `help_text`, `cgo_build`, `generic_stack`, etc.), runnable in WSL with zero stubs. Example files: `tests/test_xyzio.py`, `tests/test_xtbenv.py`, `tests/test_plot_logic.py`, `tests/test_hud_logic.py`, `tests/test_engine_core.py`.
- **Integration tests (pure-core chain, ZERO stubs):** compose multiple shipped pure modules end-to-end on real fixture bytes — `tests/test_integration_pure_core.py`, `tests/test_phase5_integration.py`, `tests/test_phase51_integration.py`, `tests/test_phase52_integration.py`, `tests/test_phase6_integration.py`. Example chain (`test_phase6_integration.py`): `build_run_input -> xyzio round-trip -> budget_guard -> xtbenv.build_argv -> xtb_run state -> xtbenv.evaluate_run 3-leg contract -> record shape`. `test_integration_pure_core.py:38-53` documents stages 1-6 with the stack dataset read FROM the shipped JSON, not a code constant.
- **Gate self-tests:** `tests/test_purity_gates.py` builds minimal `serpentrum/`-shaped trees under `tempfile.mkdtemp` and asserts exactly which violations the checker must report (or stay silent) — "the fixtures ARE the contract". Includes `RealRepoCleanTest.test_real_repo_clean` asserting the actual repo passes.
- **Docs/tooling audits:** `tests/test_docs_audit.py` drives `tools/check_docs.py` in BOTH directions (live repo passes; tamper fixtures rejected) across 7 check families. `tests/test_audit_requirements.py` drives `tools/audit_requirements.py` with embedded ledgers built from an independent hardcoded 46-ID list. The final `TestRunAllIntegration` leg rides the default gate-3 discovery.
- **Source-text pins:** `tests/test_gui_pins.py`, `tests/test_hud_content.py`, `tests/test_help_text.py` — GUI contracts without a QApplication.
- **Headless Windows smokes:** viewer/GUI/Qt behavior (gate 4). No E2E browser/UI framework.
- **Real-GUI manual harnesses:** human-verify only.

**Test file → concern map (47 files):** engine behavior (`test_engine_core/rules/speed/tail_follow/turn_veto_ghost/turns/win_desync`, `test_generic_stack`, `test_ring_cycle`, `test_stack_parallelism`), parsing/IO (`test_xyzio`, `test_molfile`, `test_xtbenv`, `test_xtb_run`, `test_spectra_*`, `test_plot_logic`, `test_winpath`), data (`test_molecule_data`, `test_setloader*`, `test_stacking_*`, `test_demo_data`, `test_orientation`, `test_placement`, `test_spawn`, `test_budget_guard`, `test_cgo_build`, `test_setup_logic`), UI text (`test_hud_*`, `test_help_text`, `test_gui_pins`), and meta/tooling (`test_skeleton`, `test_purity_gates`, `test_integration_*`, `test_phase*_integration`, `test_docs_audit`, `test_audit_requirements`).

## Coverage

**Requirements:** None enforced. No `coverage.py` config, no `.coveragerc`, no threshold. The gate demands all 937 tests pass.

**View Coverage:**
```bash
# not configured in this repo
```

## Common Patterns

**Error testing via typed domain exceptions** (`tests/test_xyzio.py:31-41`):
```python
def _assert_xyz_error(testcase, action, *needles):
    try:
        action()
    except xyzio.XyzError as exc:
        message = str(exc)
        for needle in needles:
            testcase.assertIn(needle, message)
    else:
        testcase.fail('XyzError not raised (wanted message containing %r)'
                      % (needles,))
```

**Table-driven loops with a `name` label for shared failure output** (`tests/test_xtbenv.py`).

**Round-trip / fixed-point proofs** (writer output re-parses byte-identically) — `tests/test_xyzio.py:64-76,262-280`; `test_integration_pure_core.py` stage 6 asserts 1e-8 equality.

**Byte-exact fixture assertions** asserting CRLF is retained (`assertIn('\r\n', text)`).

**Tamper-direction testing** (prove the check bites): every docs/ledger check has a paired FAIL-direction test that injects a mutated fixture, e.g. `test_one_character_tamper_fails` (`tests/test_docs_audit.py:45-49`).

**Smoke staged pipelines with `check()` and sentinel epilogue** (`smoke/14_release_e2e_smoke.py:364-382`).

**`skipUnless` guarded real-data tests** (`tests/test_demo_data.py`) that skip cleanly pre-data and hard-pass post-data.

## TDD Practice

The repo history shows a strict **RED / GREEN / REFACTOR** TDD rhythm for pure-core logic — commit subjects explicitly say "failing tests for X" (RED) followed by the implementation (GREEN):
- `test(08-10): add failing tests for requirements-ledger audit tool` → `feat(08-10): implement requirements-ledger integrity checker (DOCS-05)`
- `test(08-03): add failing doc-vs-code audit wrapper` → `feat(08-03): implement check_docs doc-vs-code audit harness`
- `test(07-06): failing tests for plot unit modes ...` → `feat(07-06): plot_logic unit modes ...`
- `test(07-02): failing tests for plot_logic ...` → `feat(07-02): plot_logic ...`
- `test(06-01): failing tests for budget_guard ...`, `test(06-02): failing tests for xtb_run ...`
- `merge: 5.1-03 hud_logic.speed_note builder (TDD)`

Tests are written against pure modules that need no `pymol`/`Qt` stubs — this purity is what makes the RED/GREEN loop runnable in ~4.4s under WSL `python3.6`.

---

*Testing analysis: 2026-10-02*
