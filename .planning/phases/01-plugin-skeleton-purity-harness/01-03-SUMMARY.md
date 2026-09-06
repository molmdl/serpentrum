---
phase: 01-plugin-skeleton-purity-harness
plan: 03
subsystem: testing
tags: [ast, purity-gates, py36, py-compile, unittest-discover, headless-pymol, cmd-exe, sentinel-asserts]

# Dependency graph
requires:
  - phase: 01-plugin-skeleton-purity-harness (01-01)
    provides: serpentrum entry module (stdlib-only module level, lazy pymol/Qt) and the scoped unittest discovery convention
provides:
  - tools/check_purity.py — AST purity/hygiene checker (INFRA-02): ENTRY-lazy / GUI-pymol.Qt-only / PURE-never rule table, PyQt5+numpy banned everywhere, .exec_() modeless gate, file:line output, CLI + importable check_tree()
  - tests/run_gates.py — single gate entry (INFRA-06): py_compile walk + plugin-path safety + purity + scoped unittest discover; flag-gated --smoke with sentinel-only verdicts
  - tests/test_purity_gates.py — checker self-test: 9 tempfile fixture cases + real-repo clean check
affects: [01-02 (gui.py must satisfy GUI allowlist), 01-04 (smoke/01_skeleton_smoke.py required by --smoke), 01-05 (--xtb flag owned there), all later phases (gates must stay green)]

# Tech tracking
tech-stack:
  added: [] # stdlib only: ast, py_compile, glob, subprocess, argparse
  patterns:
    - "AST-not-grep purity gates: grep cannot split module-level vs lazy imports and false-positives on docstrings; AST sees neither"
    - "Module-level = direct children of ast.Module.body only — never ast.walk for that rule"
    - "Sentinel-only smoke verdicts: exit codes through run-conda-pymol.bat are always 0; assert flushed SMOKE-OK/SMOKE-FAIL text"
    - "Default-strict PURE classification: new serpentrum/ modules are pure until added to GUI_MODULES deliberately"

key-files:
  created:
    - tools/check_purity.py
    - tests/run_gates.py
    - tests/test_purity_gates.py
  modified: []

key-decisions:
  - "Purity gate is AST-based (stdlib ast), not grep — grep false-positives on docstrings (bioCHEMeleon shipped that bug) and cannot distinguish module-level from lazy imports"
  - "GUI allowlist is an explicit set (GUI_MODULES = {'serpentrum/gui.py'}) — a new GUI module must be added deliberately; everything else defaults PURE"
  - "'from pymol import Qt' is NOT a pymol.Qt form — only pymol.Qt / pymol.Qt.* import paths satisfy the GUI allowance"

patterns-established:
  - "Single gate entry: python3.6 tests/run_gates.py [--smoke] — exit 0/1 aggregated with file:line failure messages"
  - "Safety gate bans root-level .py and __init__.py in tests/, smoke/, tools/ (dev plugin path IS the repo root; findPlugins autoloads them)"
  - "Self-test fixtures live under tempfile.mkdtemp cleaned via shutil.rmtree addCleanup (shell rm denied)"
  - "Negative round-trip protocol: inject known-bad scratch outside the repo proves gate scope; in-repo injections prove gates bite"

# Metrics
duration: 7 min
completed: 2026-09-06
---

# Phase 1 Plan 3: Purity Gate Harness Summary

**AST purity checker + `tests/run_gates.py` single entry (py_compile walk, plugin-path safety, scoped unittest, sentinel-only `--smoke`) proven to bite via negative round-trip**

## Performance

- **Duration:** 7 min
- **Started:** 2026-09-06T11:18:08Z
- **Completed:** 2026-09-06T11:25:12Z
- **Tasks:** 3
- **Files modified:** 3 (all created)

## Accomplishments

- `tools/check_purity.py` (216 lines, stdlib-only, py3.6): classifies `serpentrum/__init__.py` as ENTRY (pymol/pmg_tk lazy-only), `serpentrum/gui.py` as GUI (pymol.Qt-only allowlist), everything else under `serpentrum/` as PURE (default-strict); PyQt5/numpy banned everywhere; `.exec_()` calls flagged with file:line; docstring mentions provably never false-positive. Importable `check_tree(root)` + CLI exiting 0/1.
- `tests/run_gates.py` (202 lines, py3.6): gate 1 = py_compile walk over serpentrum/tools/tests/smoke + plugin-path safety (root-level `.py` and dev-dir `__init__.py` banned); gate 2 = purity via `check_tree`; gate 3 = subprocess `unittest discover -s tests -p "test_*.py" -v` (no `-t .`, no `capture_output=`); `--smoke` = cmd.exe headless PyMOL with required (`smoke/01_skeleton_smoke.py`, missing → explicit "created by plan 01-04" failure) + informational (never blocking) smokes, verdicts from flushed SMOKE-OK/SMOKE-FAIL sentinels only.
- `tests/test_purity_gates.py` (216 lines): 10 contract cases — all pass, including real-repo clean check that doubles as an in-gate tripwire (an injected real-package violation failed BOTH gate 2 and gate 3).
- Negative round-trip proved each gate bites: checker CLI exits 1 on `/tmp/opencode/p1neg` bad module (`serpentrum/bad.py:5`); scratch outside the repo leaves the runner green (scope proof); root-level `zz_scratch.py` → gate 1 failure naming findPlugins autoload risk; injected function-body `import numpy` → `serpentrum/__init__.py:49` violation; walrus test file → gate 1 SyntaxError with file:line.

## Task Commits

Each task was committed atomically:

1. **Task 1a: failing purity-gate fixture tests (TDD RED)** — `cbbf11d` (test)
2. **Task 1b: AST purity checker (TDD GREEN)** — `3b8b6d5` (feat)
3. **Task 2: gate runner** — `5dfce2d` (feat)
4. **Task 3: negative round-trip** — no commit (verification-only; zero file changes, working tree clean)

**Plan metadata:** (this commit) docs(01-03): complete purity gate harness plan

_TDD note: Task 1 followed RED→GREEN with separate test/feat commits._

## Files Created/Modified

- `tools/check_purity.py` — AST purity/hygiene checker (INFRA-02); CLI + importable check_tree()
- `tests/run_gates.py` — single gate entry: syntax walk + safety + purity + scoped unittest + `--smoke` (INFRA-06/INFRA-01)
- `tests/test_purity_gates.py` — checker self-test, 10 fixture/real-repo cases

## Decisions Made

- AST-based purity checking over grep — docstrings/comments are AST-invisible (case 2 proves zero false positives) and module-level vs lazy is structural.
- "Module level" implemented as direct children of `ast.Module.body` only; `ast.walk` is used solely for the anywhere/exec_ rules — walking Module.body transitively would misflag lazy imports (research-verified gotcha).
- GUI allowance accepts only `pymol.Qt` / `pymol.Qt.*` import paths; `from pymol import Qt` is a violation (strict reading of "Qt must go through pymol.Qt").
- `--smoke` required-set is exactly `('smoke/01_skeleton_smoke.py',)`; other `smoke/NN_*.py` scripts auto-discovered as informational so 01-05's dialog smoke plugs in without runner edits.
- No `--xtb` flag added (plan 01-05 owns it); no `__init__.py` created anywhere (safety gate 1 would correctly fail).

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- None blocking. Observations recorded: stderr/stdout stream interleaving in runner output is cosmetic (stderr summary flushes first); gate 3's `test_*.py` pattern means a non-`test_` bad-syntax file in tests/ is caught only by gate 1 — which it was (`tests/zz_bad_syntax.py`, line 2, SyntaxError), so coverage holds.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Default gates green on the current tree (13 tests OK, exit 0); `--smoke` correctly fails until 01-04 lands `smoke/01_skeleton_smoke.py`.
- 01-02's `serpentrum/gui.py` must import only via `from pymol.Qt import ...` (or `pymol.Qt.*`) and never call `.exec_()`, or gate 2 fails with file:line.
- 01-05 adds the `--xtb` flag to `tests/run_gates.py` (already the single entry point).

---
*Phase: 01-plugin-skeleton-purity-harness*
*Completed: 2026-09-06*
