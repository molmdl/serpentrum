---
phase: 03-molecules-in-the-viewer-setup-tab
plan: 03
subsystem: infra
tags: [xtb-path, validation, unification, purity, setup-logic, relative-import]

# Dependency graph
requires:
  - phase: 02-pure-core
    provides: xtbenv.validate_binary_path (02-02) — the canonical xtb-path rules; setup_logic._xtb_path_problems (02-07) — the local mirror being unified
provides:
  - "Single-source xtb-path validator: setup_logic._xtb_path_problems delegates to xtbenv.validate_binary_path (zero drift)"
  - "Cross-check test (XtbPathUnificationTest) pinning the delegation across the full input matrix + literal message lock"
affects: [03-07-setup-tab, 06-xtb-pipeline]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Single-source validation rules via intra-package relative delegation (purity-exempt): when two pure modules share identical rules, one delegates to the other instead of carrying a parallel copy"

key-files:
  created: []
  modified:
    - serpentrum/setup_logic.py
    - tests/test_setup_logic.py

key-decisions:
  - "Relative intra-package import `from .xtbenv import validate_binary_path` (purity-exempt) — keeps the package-internal dependency explicit over a stdlib-side re-import"
  - "Kept _xtb_path_problems as a thin named wrapper (not inlined into validate()) so the concern is documented and tests can pin the delegation directly"
  - "Removed the now-unused `import os` (was only used by the old local body) — clean, no dead imports"

patterns-established:
  - "Intra-package delegation for shared pure validation rules: relative import is purity-exempt (check_purity.py); one canonical implementation, callers delegate"

# Metrics
duration: 4 min
completed: 2026-09-10
---

# Phase 3 Plan 03: Unify xtb Path Validation Summary

**setup_logic._xtb_path_problems now delegates to xtbenv.validate_binary_path (single source of the xtb-path rules, zero drift) — discharges the 02-02-SUMMARY.md:109 Phase-2 handoff note**

## Performance

- **Duration:** 4 min
- **Started:** 2026-09-10T03:55:08Z
- **Completed:** 2026-09-10T03:58:52Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Eliminated the dual-implementation drift risk: `setup_logic._xtb_path_problems` is now a thin delegator (`return validate_binary_path(path)`) to the single canonical implementation in `serpentrum.xtbenv.validate_binary_path`. Phase 2 carried a local mirror only because `xtbenv` was a parallel wave-1 plan that might not exist in the worktree — that constraint is gone.
- Message contract byte-identical: the pre-existing `TestValidateXtbPath` / `TestValidateErrorMatrix` in `test_setup_logic.py` stayed green UNMODIFIED (46 → 48 tests). That unmodified matrix IS the byte-identity proof for `validate()`.
- New `XtbPathUnificationTest` pins the unification directly: asserts `_xtb_path_problems == validate_binary_path` across the full input matrix (None, `''`, non-str, missing path, directory, quoted path, real file) and locks the historical `"'<path>' does not exist"` literal against accidental rewording.
- Stale "parallel wave-1 plan / keep in sync" docstring rationale removed; module + function docstrings now state the unification (Phase 3, per 02-02-SUMMARY.md:109).
- `setup_logic` stays PURE: the relative intra-package import is purity-exempt (`check_purity.py`); the AST purity gate passes green.

## Task Commits

Each task was committed atomically:

1. **Task 1: delegate _xtb_path_problems to xtbenv.validate_binary_path + docstring update** - `c3d3f78` (refactor)
2. **Task 2: cross-check test pinning the unification across the full input matrix** - `bb7c6c2` (test)

**Plan metadata:** pending (docs commit below)

## Files Created/Modified
- `serpentrum/setup_logic.py` - `_xtb_path_problems` now delegates to `xtbenv.validate_binary_path`; module + function docstrings updated to state the unification; removed unused `import os`; added `from .xtbenv import validate_binary_path`
- `tests/test_setup_logic.py` - Appended `XtbPathUnificationTest` (2 tests: full-matrix cross-check + missing-path literal pin); pre-existing classes untouched; added `import serpentrum.xtbenv as xtbenv`

## Decisions Made
- **Relative intra-package import** (`from .xtbenv import validate_binary_path`) chosen over a stdlib-side re-import — keeps the package-internal dependency explicit. Both modules are PURE stdlib so either is legal, but relative is the documented convention for package-internal deps.
- **Kept `_xtb_path_problems` as a named thin wrapper** (not inlined into `validate()`) so the concern is self-documenting and tests can pin the delegation by name. `validate()` still calls `_xtb_path_problems(xtb_path)` unchanged.
- **Removed the now-unused `import os`** — it was only referenced inside the old local `_xtb_path_problems` body; leaving a dead import would violate the AGENTS.md "clean and safe" standard. (Minor cleanup, documented as a deviation below.)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Removed now-unused `import os`**
- **Found during:** Task 1 (delegate _xtb_path_problems)
- **Issue:** After replacing the local `_xtb_path_problems` body with `return validate_binary_path(path)`, the module-level `import os` became dead code (it was only used by `os.path.exists` / `os.path.isfile` in the old body). A dead import violates the AGENTS.md "clean and safe" code standard and would trip linters.
- **Fix:** Removed `import os` from the module-level imports; updated the module docstring's stdlib-import parenthetical from "(json/math/random/os)" to "(json/random stdlib + one intra-package import)" — also correcting a pre-existing inaccuracy (the docstring had always listed `math`, which was never imported).
- **Files modified:** serpentrum/setup_logic.py
- **Verification:** Full suite 385 tests green; purity gate PASS; the docstring now accurately reflects the direct imports.
- **Committed in:** c3d3f78 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking/cleanup)
**Impact on plan:** Minor cleanup intrinsic to the delegation (the old body was `os`'s only consumer). No scope creep — `validate()`, `save_setup`, `load_setup`, `randomize_head`, `DEFAULTS`, `BOX_PRESETS` all untouched as the plan required.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- SETUP-05 groundwork complete: the Setup-tab plan (03-07) can rely on `validate()` and `xtbenv.detect_binary` agreeing about what a valid xtb path is BY CONSTRUCTION (both consume `validate_binary_path`).
- The ownership split is unchanged and documented (03-RESEARCH-upload-gate.md §7.2): `validate()` owns "is the setup dict valid?"; `detect_binary` owns "what exe do I actually run?". This plan unified only the shared RULES, not the concerns.
- No blockers. Full gate suite green in the worktree (385 tests, run_gates exit 0, purity PASS).

---
*Phase: 03-molecules-in-the-viewer-setup-tab*
*Completed: 2026-09-10*
