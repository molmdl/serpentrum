---
phase: 03-molecules-in-the-viewer-setup-tab
plan: 01
subsystem: testing
tags: [ast, purity-gate, check_purity, bridge-class, allowlist, python3.6]

# Dependency graph
requires:
  - phase: 01-plugin-skeleton-purity-harness
    provides: AST purity checker (tools/check_purity.py) + fixture self-tests (tests/test_purity_gates.py)
provides:
  - "BRIDGE_MODULES allowlist class permitting pymol/pmg_tk at any level in serpentrum/pymol_bridge.py"
  - "GUI_MODULES extended with serpentrum/gui_setup.py (pymol.Qt allowed, bare pymol flagged)"
  - "7 new fixture cases (11-17) self-testing the BRIDGE + extended-GUI contracts"
affects: [03-06-pymol-bridge, 03-07-setup-tab, phase-4-game-loop, phase-5-stacking]

# Tech tracking
tech-stack:
  added: []
  patterns: [BRIDGE allowlist class parallel to GUI_MODULES for cmd-seam modules]

key-files:
  created: []
  modified:
    - tools/check_purity.py
    - tests/test_purity_gates.py

key-decisions:
  - "BRIDGE class: pymol/pmg_tk allowed at ANY level (module + bodies); PyQt5/numpy/exec_ banned — the first purity class permitting `from pymol import cmd`"
  - "gui_setup.py added to GUI_MODULES deliberately (per STATE.md decision 01-03) — pymol.Qt clean, bare pymol flagged at any level"
  - "4 of 7 RED guard-rail tests passed immediately under PURE (bans already hold) — expected, not a test error"

patterns-established:
  - "BRIDGE_MODULES allowlist: parallel to GUI_MODULES, for the single cmd-seam module the architecture reserves"
  - "Fixture-first TDD: RED tests encode new-class contracts before implementation; guard-rail tests prove bans survive the class change"

# Metrics
duration: 7min
completed: 2026-09-10
---

# Phase 3 Plan 01: Purity BRIDGE Class + gui_setup Allowlist Summary

**AST purity checker extended with BRIDGE_MODULES allowlist (pymol/pmg_tk any level) and GUI_MODULES += gui_setup.py — the first class permitting `from pymol import cmd`, unblocking all downstream Phase-3 cmd-seam modules**

## Performance

- **Duration:** 7 min
- **Started:** 2026-09-10T03:27:56Z
- **Completed:** 2026-09-10T03:35:03Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- BRIDGE_MODULES = {'serpentrum/pymol_bridge.py'} live: classify() returns 'BRIDGE'; _check_import_node allows pymol/pmg_tk at any level, bans PyQt5/numpy with message 'bridge module imports %r (banned anywhere)'
- GUI_MODULES deliberately extended to {'serpentrum/gui.py', 'serpentrum/gui_setup.py'} — gui_setup.py is GUI class (pymol.Qt clean, bare pymol flagged)
- .exec_() ban unchanged — covers BRIDGE too (the bridge builds no dialogs)
- 7 new fixture cases (11-17) self-test all BRIDGE + extended-GUI contracts; real repo still clean (neither new module exists yet); 390 tests + all 3 gates green

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): failing fixture cases for BRIDGE + extended GUI_MODULES** - `2cf6b5a` (test)
2. **Task 2 (GREEN): checker extension — BRIDGE_MODULES, classify, import rule, GUI_MODULES** - `490b323` (feat)

## Files Created/Modified
- `tools/check_purity.py` - Added BRIDGE_MODULES constant, classify() BRIDGE branch, _check_import_node BRIDGE rule, extended GUI_MODULES with gui_setup.py, updated module docstring classification table
- `tests/test_purity_gates.py` - Added 7 new fixture cases (11-17) encoding BRIDGE + extended-GUI contracts; updated class docstring; file now 342 lines (>= 280 min_lines)

## Decisions Made
- BRIDGE class allows pymol/pmg_tk at ANY level (module + bodies) — the cmd-seam. This is the researched recommendation (03-RESEARCH-viewer-bridge.md §3.2, 03-RESEARCH-setup-ui.md §5.2), adopted as a consolidated default decision per phase planning directives.
- PyQt5/numpy banned in BRIDGE at any level (Qt stays in GUI modules; numpy never needed in the bridge — pure modules do the math).
- .exec_() ban stays unchanged — it applies to EVERY class including BRIDGE (separate ast.Call walk, not governed by the BRIDGE import branch).
- gui_setup.py added to GUI_MODULES: pymol.Qt imports clean at any level; bare `from pymol import cmd` flagged at any level (mirrors gui.py's case-6 rule).

## Deviations from Plan

### Note on RED Phase Verification

**1. [Observation] 4 of 7 RED tests passed immediately (not all 7 failed)**
- **Found during:** Task 1 (RED phase verification)
- **Issue:** The plan's verification expected "exactly the 7 new cases fail." In practice, only 3 cases (11, 12, 16) failed — the ones encoding NEW contracts (BRIDGE allows pymol/pmg_tk; gui_setup allows pymol.Qt). The other 4 cases (13, 14, 15, 17) passed because they test bans (PyQt5, numpy, exec_, bare pymol) that already hold under the existing PURE class (pymol_bridge.py and gui_setup.py both fall to PURE before the extension).
- **Assessment:** This is expected and correct TDD behavior, not a bug. The 4 guard-rail tests prove that once the BRIDGE/GUI class is applied, these bans are preserved. They serve as regression protection: if a future change accidentally relaxes the PyQt5/numpy/exec_ ban in BRIDGE, these tests catch it.
- **No fix needed:** The tests are correctly written; the plan's expectation that all 7 would fail was overly strict. The 3 failing tests sufficiently validate the RED phase (new contracts not yet implemented).

---

**Total deviations:** 0 auto-fixed (1 observation documented)
**Impact on plan:** None — plan executed exactly as written; the RED/GREEN cycle completed successfully.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- BRIDGE class is live and self-tested: downstream wave-2+ plans (03-06 pymol_bridge.py, 03-07 gui_setup.py) can now legally create modules that import `pymol.cmd` under the gate
- Real repo still clean — listing not-yet-existing module paths in BRIDGE_MODULES/GUI_MODULES breaks nothing because check_tree walks only existing files
- Full gate suite green (390 tests, 3 gates)
- No blockers or concerns

---
*Phase: 03-molecules-in-the-viewer-setup-tab*
*Completed: 2026-09-10*
