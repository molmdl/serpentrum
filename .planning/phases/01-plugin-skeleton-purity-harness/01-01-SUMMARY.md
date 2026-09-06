---
phase: 01-plugin-skeleton-purity-harness
plan: 01
subsystem: infra
tags: [pymol-plugin, pyqt5, single-instance, anchor, lazy-import, unittest, python3.6, modeless]

# Dependency graph
requires:
  - phase: none
    provides: first phase — greenfield package skeleton
provides:
  - "serpentrum/ plugin package: anchored single-instance entry module (__init_plugin__, run_plugin_gui, _anchor)"
  - "tests/test_skeleton.py: zero-stub import + entry-API proof, first green WSL python3.6 test"
  - "Test conventions: sys.path self-insert per test file, discovery without `-t .`, no tests/__init__.py"
affects: [01-02-dialog-shell, 01-03-purity-gates, 01-04-headless-smokes, 01-05, 01-06, all later phases loading serpentrum]

# Tech tracking
tech-stack:
  added: none (stdlib only: unittest, os, sys)
  patterns:
    - "Anchor-on-pmg_tk.startup: live state lives on pmg_tk.startup._serpentrum, never module globals (survives reload + double import)"
    - "Zero-stub module level: entry module is stdlib-only; pymol imported inside __init_plugin__, Qt lazily inside run_plugin_gui"
    - "Modeless discipline: .show() / .raise_() / .activateWindow(), never .exec_()"
    - "Test discovery: python3.6 -m unittest discover -s tests -p \"test_*.py\" -v (no -t . on py3.6)"

key-files:
  created:
    - serpentrum/__init__.py
    - tests/test_skeleton.py
  modified: []

key-decisions:
  - "Anchor live state on pmg_tk.startup._serpentrum (loader's own plugin namespace, guaranteed present before any plugin runs) — survives importlib.reload and duplicate imports under second names (Pitfall 7 / INFRA-03)"
  - "run_plugin_gui calls PluginDialog.find_existing() before constructing — gui.py is owned by plan 01-02; the call is safe because it only executes at menu-click time (never at import/test/compile time)"
  - "tests/ deliberately has NO __init__.py and the repo root stays free of top-level .py files (plugin-path safety: the dev plugin path IS the repo root)"

patterns-established:
  - "Module-level purity: nothing at module scope except docstring + defs; all runtime deps imported inside function bodies"
  - "Every test file repeats the sys.path self-insert (bioCHEMeleon pattern), recorded in the test docstring"
  - "Plugin loads as pmg_tk.startup.serpentrum — smoke assertions must key on that sys.modules name, not pymol.plugins.startup (alias only)"

# Metrics
duration: 3 min
completed: 2026-09-06
---

# Phase 1 Plan 1: Plugin Skeleton Summary

**Anchor-based single-instance plugin entry (state on `pmg_tk.startup._serpentrum`) with lazy Qt import, proven stdlib-only by a zero-stub python3.6 unittest**

## Performance

- **Duration:** 3 min
- **Started:** 2026-09-06T11:09:38Z
- **Completed:** 2026-09-06T11:12:10Z
- **Tasks:** 2
- **Files modified:** 2 created

## Accomplishments
- `serpentrum/` package created with the anchored entry module: `_anchor()` state holder on `pmg_tk.startup`, `__init_plugin__(app=None)` menu registration, `run_plugin_gui()` with lazy Qt import and reuse/adopt-before-construct dialog logic
- First green WSL test: 3 unittest cases prove zero-stub importability (no pymol/Qt/pmg_tk in `sys.modules`), entry API presence, and deferred anchor
- Plugin-path safety conventions in place from commit one: no `tests/__init__.py`, no top-level `.py` at repo root

## Task Commits

Each task was committed atomically:

1. **Task 1: Create serpentrum package + anchored entry module** - `2a1c72b` (feat)
2. **Task 2: Create zero-stub entry-module test (first green WSL test)** - `0dfeb66` (test)

## Files Created/Modified
- `serpentrum/__init__.py` - Entry module: `_anchor()` / `__init_plugin__()` / `run_plugin_gui()`; module level is stdlib-only (45 lines)
- `tests/test_skeleton.py` - Zero-stub purity proof + entry API + deferred-anchor tests (43 lines); records the test conventions in its docstring

## Verification Results

- `python3.6 -m py_compile serpentrum/__init__.py tests/test_skeleton.py` → rc 0
- `python3.6 -m unittest discover -s tests -p "test_*.py" -v` → 3 tests, OK, rc 0
- `grep -c "^import pymol\|^from pymol\|^import pmg_tk" serpentrum/__init__.py` → 0 matches
- Post-import `sys.modules` scan: no `pymol`, `pymol.Qt`, `PyQt5*`, `pmg_tk*` (stdlib-only module level confirmed)
- All frontmatter key_links present: `addmenuitemqt('serpentrum'`, `pmg_tk.startup._serpentrum`, `from .gui import PluginDialog`

## Decisions Made
- Anchor on `pmg_tk.startup` (research §2.3 sketch used nearly verbatim) — the loader's own plugin namespace is permanent in `sys.modules` and untouched by child-module reload
- Called `PluginDialog.find_existing()` in `run_plugin_gui` now, deferring its definition to plan 01-02 — safe because the lazy import only executes at menu-click time (py_compile never runs it; smokes never call `run_plugin_gui`)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Wave 2 plans (01-02 dialog shell ∥ 01-03 purity gates ∥ 01-04 headless smokes) can proceed — all load or inspect this module
- **For 01-02:** `serpentrum/gui.py` must define `PluginDialog` with a `find_existing()` classmethod (scan `QApplication.topLevelWidgets()` for an instance of the class) — `run_plugin_gui` already calls it
- **For 01-03/01-04:** purity gate should extend to all `serpentrum/*.py`; smokes must key assertions on `pmg_tk.startup.serpentrum` (not the `pymol.plugins.startup` alias)
- Test discovery command is pinned in the test docstring: never add `-t .` (fails on python3.6 with a non-package start dir)

---
*Phase: 01-plugin-skeleton-purity-harness*
*Completed: 2026-09-06*
