---
phase: 06-xtb-pipeline
plan: 01
subsystem: api
tags: [spectra-06, budget-guard, pure-layer, xtb, launch-recheck, tdd]

# Dependency graph
requires:
  - phase: 02-schema-setup
    provides: setup_logic.HESSIAN_WARNING literal (reused verbatim, SETUP-06/SPECTRA-06 wording parity)
  - phase: 05-stacking-game-rules
    provides: last_run record contract (molecules_stacked head-excluded, chain_objects head-included)
provides:
  - serpentrum/budget_guard.py — PURE SPECTRA-06 launch re-check: launch_budget_warnings + launch_counts_line
  - tests/test_budget_guard.py — 13-test behavior matrix + HESSIAN_WARNING drift-pin
affects: [06-09 launch API (logs these lines verbatim), 06-11 HESSIAN_WARNING literal amendment (flows through the drift-pin)]

# Tech tracking
tech-stack:
  added: []
  patterns: [warn-and-proceed guard as pure data function; desync-as-warning (never refusal); errors-are-data with bool-is-int trap guard]

key-files:
  created: [serpentrum/budget_guard.py, tests/test_budget_guard.py]
  modified: []

key-decisions:
  - "Warn-and-proceed, never block: a default WIN snake (130-260 atoms) legitimately exceeds atom_budget=100; blocking would make the shipped win path un-runnable (game_engine.py:726-731 freezes molecules_stacked AT cap)"
  - "Molecule leg is counts+desync ONLY — never a cap comparison (incl-head vs cap would always warn on wins); atom budget is the sole hessian-warning trigger"
  - "HESSIAN_WARNING reused verbatim from setup_logic; drift-pinned so plan 06-11's literal amendment flows through"

patterns-established:
  - "Guard-as-builder: pure (ints in) -> [one-line warning strings out]; GUI merely logs the output verbatim"
  - "Viewer desync = warning line + proceed: the run input is engine truth; a stale scene is cosmetic"
  - "Drift-pin literals via assertIn on the setup_logic constant (test_xtbenv.py:298 precedent)"

# Metrics
duration: 15 min
completed: 2026-09-26
---

# Phase 6 Plan 01: budget_guard Summary

**PURE SPECTRA-06 pre-launch atom-budget re-check — `launch_budget_warnings`/`launch_counts_line` as pure (ints)->[warning lines] functions reusing `setup_logic.HESSIAN_WARNING` verbatim, warn-and-proceed by structural necessity, never blocking and never raising**

## Performance

- **Duration:** ~15 min
- **Completed:** 2026-09-26
- **Tasks:** 2/2 (RED, GREEN)
- **Files modified:** 2 (both created)

## Accomplishments

- `serpentrum/budget_guard.py` (PURE, 139 lines): `launch_budget_warnings(molecules_stacked, molecules_view, atoms_engine, atoms_view, atom_budget)` returns one-line warning strings — clean run -> `[]`, over-budget -> exactly one HESSIAN_WARNING-carrying line with revealed head-inclusive counts, desyncs -> warning lines (order pinned: desyncs first, hessian last), garbage inputs -> single 'unavailable' line; NEVER raises, NEVER blocks.
- `launch_counts_line(molecules_stacked, atoms_engine, atom_budget)` renders the head-inclusive launch counts line with 'unavailable' rendering for non-numeric atoms.
- Count conventions pinned in the module docstring: molecules_stacked EXCLUDES head (guard adds +1), atoms_engine is the head-inclusive true xtb input size (last_run atoms_total is head-excluded), molecule leg is counts+desync only because win freezes `molecules_stacked` exactly AT the cap.
- 13-test behavior matrix incl. HESSIAN_WARNING drift-pin (assertIn on the setup_logic literal — test_xtbenv.py:298 precedent).

## Task Commits

1. **Task 1: RED — failing tests for budget_guard** - `3605363` (test)
2. **Task 2: GREEN — implement serpentrum/budget_guard.py** - `5b0fccb` (feat)

## Files Created/Modified

- `serpentrum/budget_guard.py` — PURE SPECTRA-06 launch re-check (stdlib + `from . import setup_logic` only; %-formatting; python3.6)
- `tests/test_budget_guard.py` — 13 tests: clean/over-budget/at-budget/desync-molecule/desync-atoms/3-line-order/unavailable-inputs/bool-trap/None-view-skip/no-budget + counts-line format/none + drift-pin

## Decisions Made

None beyond the plan's resolved decisions — implemented exactly as specified (warn-and-proceed, molecule-leg-desync-only, HESSIAN_WARNING verbatim reuse).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] `_is_count(molecules_stacked)` guard in the molecule-desync condition and 'unavailable' fallback in `launch_counts_line`**

- **Found during:** Task 2 (GREEN implementation)
- **Issue:** The plan's literal desync condition `_is_count(molecules_view) and molecules_view != molecules_stacked + 1` raises `TypeError` if a caller ever passes `molecules_stacked=None` (e.g. malformed last_run record), violating the plan's own pinned invariant "NEVER blocks and NEVER raises". `launch_counts_line`'s `%d` formatting had the same hole.
- **Fix:** Added `_is_count(molecules_stacked)` to the guard conjunction and an 'unavailable' render branch in `launch_counts_line`. No pinned test behavior changed (all 13 tests specify well-formed molecule inputs; the extra branch only affects inputs the plan's contract covers under the never-raises invariant).
- **Files modified:** serpentrum/budget_guard.py
- **Verification:** 13/13 new tests pass; full gates green (768 tests, all previously-green suites unchanged)
- **Committed in:** `5b0fccb` (part of the GREEN commit)

---

**Total deviations:** 1 auto-fixed (1 missing critical null-check)
**Impact on plan:** Defensive hardening inside the plan's own never-raises invariant. No scope creep.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 06-09 (launch API) can log `launch_budget_warnings`/`launch_counts_line` output verbatim with zero formatting logic of its own; the caller-side argument wiring (molecules_view from `len(last_run['chain_objects'])`, atoms_engine from `xyzio.read_xyz_text(snake_xyz)`, atoms_view from `bridge.chain_atom_counts(...)`) is documented in the module docstring.
- Plan 06-11's HESSIAN_WARNING literal amendment flows through automatically via the drift-pin (`assertIn(setup_logic.HESSIAN_WARNING, line)`) — no edit needed here.
- Full WSL gates green: `python3.6 tests/run_gates.py` -> 768 tests OK (755 baseline + 13 new); gates 1/2/3 PASS (new module auto-classified PURE).

---
*Phase: 06-xtb-pipeline*
*Completed: 2026-09-26*
