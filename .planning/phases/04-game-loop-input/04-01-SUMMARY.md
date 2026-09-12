---
phase: 04-game-loop-input
plan: 01
subsystem: infra
tags: [purity-gate, ast, check_purity, bridge-class, gui-class, phase-4-preregistration]

# Dependency graph
requires:
  - phase: 03-molecules-viewer-setup
    provides: "BRIDGE purity class live (03-01 decision); gui_setup.py GUI allowlist precedent"
provides:
  - "baseline classification for serpentrum/input.py as BRIDGE before the file exists"
  - "baseline classification for serpentrum/gui_game.py as GUI before the file exists"
  - "five fixture tests pinning both classifications so reclassification fails loudly"
affects: [04-04 input.py creation, 04-05 gui_game.py creation, Phase 5 (any later bridge/GUI additions)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Pre-registration: allowlist entries for not-yet-created module paths (inert — check_tree walks existing files only)"

key-files:
  created: []
  modified:
    - tools/check_purity.py
    - tests/test_purity_gates.py

key-decisions:
  - "serpentrum/input.py pre-registered as BRIDGE (KeySteerWizard steering: pymol.wizard + cmd, never Qt — 04-RESEARCH-input.md placement table)"
  - "serpentrum/gui_game.py pre-registered as GUI (Game tab HUD: pymol.Qt only — 04-RESEARCH-hud.md Q5)"

patterns-established:
  - "Parallel-wave enablement: purity allowlist entries land in a dedicated Wave-1 plan so independent Wave-2 plans create their modules with zero gate edits"

# Metrics
duration: 4min
completed: 2026-09-12
---

# Phase 4 Plan 01: Purity-Class Pre-Registration Summary

**Pre-registered `serpentrum/input.py` as BRIDGE (pymol.wizard + cmd) and `serpentrum/gui_game.py` as GUI (pymol.Qt only) in the AST purity gate, pinned by five fixture tests — Wave-2 plans 04-04/04-05 can now create their modules fully parallel with zero gate collisions.**

## Performance

- **Duration:** 4 min
- **Started:** 2026-09-12T19:28:38Z
- **Completed:** 2026-09-12T19:32:44Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- `BRIDGE_MODULES` gains `serpentrum/input.py`; module-docstring classification table + comments updated (check_tree walks existing files only, so the entry is inert until 04-04 lands the module).
- `GUI_MODULES` gains `serpentrum/gui_game.py`; same inertness noted in comment — RealRepoCleanTest stays green before and after the file lands.
- Five fixture tests (cases 23–27, mirroring 11–14/16–17) pin both classifications; a future accidental reclassification fails loudly.
- `check_purity.classify(...)` provably returns `BRIDGE` for input.py and `GUI` for gui_game.py; full gate run green (433 + 5 = 438 tests... all default gates green).

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend purity allowlists for input.py (BRIDGE) and gui_game.py (GUI)** - `6825268` (feat)
2. **Task 2: Fixture tests pinning the two new classifications** - `488a49d` (test)

## Files Created/Modified

- `tools/check_purity.py` — allowlist entries + docstring table/comment updates for the two Phase-4 module paths; NO logic changes (classify/check_tree/BANNED_ROOTS untouched).
- `tests/test_purity_gates.py` — five new fixture cases (23–27) in the existing make_tree() pattern; docstrings cite plan 04-01 and the responsible research section.

## Decisions Made

None beyond plan scope — followed the plan verbatim. Both classifications derive directly from STATE.md decision 03-01 (BRIDGE class semantics) plus the two Phase-4 research docs cited in-line.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. First attempt to anchor the test-file edit on a non-unique substring failed (expected edit-tool ambiguity); re-anchored on the class boundary and applied cleanly.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Wave-2 plans 04-04 (input.py) and 04-05 (gui_game.py) can create their modules and pass gate 2 with NO further check_purity.py edits — the stated success criterion of this plan.
- RealRepoCleanTest pinned green: when the module files land, their legal import shapes are exactly those proven by fixture cases 23–27.

---
*Phase: 04-game-loop-input*
*Completed: 2026-09-12*
