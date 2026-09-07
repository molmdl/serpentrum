---
phase: 02-pure-core-game-chemistry-logic
plan: 02
subsystem: xtb-bridge
tags: [xtb, success-contract, binary-detection, argv, dependency-injection, unittest, py36, stdlib-only]

# Dependency graph
requires:
  - phase: 01-plugin-skeleton-purity-harness
    provides: gates harness (tests/run_gates.py), purity checker classification (default-PURE), test conventions (sys.path self-insert, scoped discovery), committed xtb spike fixtures at .planning/research/xtb-spike-fixtures/
provides:
  - serpentrum/xtbenv.py: 3-leg xtb success contract evaluator (evaluate_run -> RunVerdict with one problem string per failed leg)
  - validate_binary_path (accumulating problems: empty/missing/directory/quotes) + detect_binary (probe order configured -> xtb.exe -> xtb, DI which_fn)
  - build_argv (list argv with --ohess, quote rejection) + new_run_dir (srp_ per-run temp dir contract)
  - constants XTB_OHESS / EXPECTED_FILES / STDERR_SUCCESS / STDERR_FAILURE anchored to run_gates.py gate 5 literals
affects: [02-04 pure integration test, phase-06 xtb runner, setup_logic xtb_path validation (SETUP-05)]

# Tech tracking
tech-stack:
  added: [] # stdlib only (collections, os, shutil, tempfile)
  patterns:
    - "DI which_fn seam (default shutil.which): detection tested with recording fakes — zero xtb install, zero sys.modules stubs"
    - "Failure-literal-before-success-literal substring ordering ('abnormal termination' contains 'normal termination')"
    - "Fixtures read IN PLACE from .planning/research/xtb-spike-fixtures/ (no copies; parallel-worktree-safe)"

key-files:
  created:
    - serpentrum/xtbenv.py
    - tests/test_xtbenv.py
  modified: []

key-decisions:
  - "STDERR_FAILURE is checked BEFORE STDERR_SUCCESS in evaluate_run — 'abnormal termination' contains 'normal termination' as a substring, so success-first ordering misclassifies bad runs (proven by committed bad.err bytes)"
  - "Exit-code problem rendered with %s (not %d) so a None rc (killed process) yields 'exit code None != 0' instead of a TypeError"
  - "Quote characters rejected in BOTH validate_binary_path and build_argv — they would break list-argv safety downstream"
  - "Probe order locked: validated configured path wins, then which_fn('xtb.exe') (Windows conda env), then which_fn('xtb') (Linux)"

patterns-established:
  - "Contract-evaluator pattern: ok bool + one human-readable problem per failed leg (exit / stderr / files)"
  - "Constants-guard test pins literals shared with tests/run_gates.py gate 5 against typo drift"

# Metrics
duration: 11 min
completed: 2026-09-08
---

# Phase 2 Plan 02: xtb Success Contract + Binary Detection Summary

**Pure `xtbenv` module: 3-leg run-success evaluator proven against the committed .err fixture bytes (repro_oh story encoded), DI-based `xtb.exe`/`xtb` detection, list-argv builder with locked `--ohess`, and the `srp_` per-run-dir contract — 23 tests, zero stubs, stdlib-only.**

## Performance

- **Duration:** 11 min (629 s)
- **Started:** 2026-09-07T19:12:04Z
- **Completed:** 2026-09-07T19:22:33Z
- **Tasks:** 3/3
- **Files modified:** 2 created (serpentrum/xtbenv.py, tests/test_xtbenv.py)

## Accomplishments
- `evaluate_run`: ok iff exit 0 AND `'normal termination'` on stderr AND expected files present; one human-readable problem per failed leg. The repro_oh story (stderr success but zero output files) is rejected with exactly one files-only problem — **phase success criterion 3 encoded as a test**.
- `detect_binary`: probe order configured -> `xtb.exe` (Windows conda env) -> `xtb` (Linux) -> None through an injected `which_fn`; invalid configured paths fall through. Tests run with no xtb installed and no sys.modules stubs.
- `build_argv` returns a LIST `[exe, input, '--ohess']` (+ extras in order) and raises ValueError on any quote character; `new_run_dir` creates `srp_`-prefixed dirs under the caller's base (never the session dir).
- All five committed `.err` fixtures read IN PLACE (no copies made by this plan); CRLF bytes passed as-is to prove the substring check tolerates `\r\n`.

## Task Commits

Each task was committed atomically:

1. **Task 1: success-contract evaluator vs committed .err fixtures** - `0446097` (feat)
2. **Task 2: validate_binary_path + detect_binary (injected which_fn)** - `ee9e2e5` (feat)
3. **Task 3: build_argv + new_run_dir + full verification** - `ddaf10d` (feat)

## Files Created/Modified
- `serpentrum/xtbenv.py` (207 lines) — PURE stdlib module: constants, RunVerdict, evaluate_run, validate_binary_path, detect_binary, build_argv, new_run_dir
- `tests/test_xtbenv.py` (309 lines) — 23 tests: fixture-driven contract cases, DI detection cases, argv/run-dir/constants cases

## Decisions Made
- **Failure literal checked first in the stderr leg:** the naive "ok iff `'normal termination' in stderr`" reading misclassifies `abnormal termination of xtb` as success (substring containment). The plan's own fixture tests (bad.err -> 3 problems; leg independence -> 1 problem) define the ground truth; implementation and docstring now pin failure-first ordering.
- **`%s` for the exit-code problem string** so a None rc (timeout kill) renders readably instead of raising.
- **Quote rejection duplicated in validate_binary_path and build_argv** (defense in depth on the list-argv safety contract).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] 'abnormal termination' substring masquerades as success**

- **Found during:** Task 1 (first test run — 2 of 7 tests failed)
- **Issue:** `STDERR_SUCCESS in stderr_text` is True for `abnormal termination of xtb` because it contains `normal termination` ("ab**normal termination**") — bad runs would be classified as successes, breaking the bad.err fixture case (expected 3 problems, got 2) and leg independence.
- **Fix:** Reordered the stderr leg to test `STDERR_FAILURE` before `STDERR_SUCCESS`, documented in the function docstring and inline comment.
- **Files modified:** serpentrum/xtbenv.py
- **Verification:** bad.err -> 3 problems (exit / abnormal termination / missing files); leg independence -> exactly 1 problem per single-leg failure; full suite + gates green.
- **Committed in:** 0446097 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** The fix is required for the contract to match the plan's own fixture tests; no scope creep.

## Issues Encountered
None beyond the Rule 1 fix above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- `serpentrum/xtbenv` is import-safe and PURE; 02-04's `test_integration_pure.py` can chain `evaluate_run` against the fixture bytes as designed (research §11 step 4).
- The Phase-6 runner consumes this exact surface: `detect_binary` -> `new_run_dir` -> `build_argv` -> subprocess -> `evaluate_run`; the cwd contract (bare `snake.xyz` written into the run dir) is documented in `build_argv`/`new_run_dir` docstrings.
- Note for SETUP-05: `setup_logic.validate` should call `xtbenv.validate_binary_path` for `xtb_path` problems (API returns a problem list, not a bool).
- Verification evidence: `python3.6 -m unittest discover -s tests -p "test_xtbenv.py" -v` -> 23 OK; full discovery -> 55 OK; `python3.6 tests/run_gates.py` -> exit 0 (syntax+safety, purity, unittest all PASS); `python3.6 tools/check_purity.py` -> clean.

---
*Phase: 02-pure-core-game-chemistry-logic*
*Completed: 2026-09-08*
