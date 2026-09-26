---
phase: 06-xtb-pipeline
plan: 10
subsystem: testing
tags: [xtb, integration, unittest, contract-testing, fixture-bytes]

# Dependency graph
requires:
  - phase: 06-xtb-pipeline plans 01/02
    provides: budget_guard (warn-and-proceed launch re-check), xtb_run (state machine, build_run_input, new_spectra_run), xyzio round-trip
  - phase: 02-xtb-contract plan 02
    provides: xtbenv.evaluate_run 3-leg contract, build_argv list-argv + quote rejection, EXPECTED_FILES
provides:
  - Executable seam-pin for the Phase-6 pure integration chain (input -> guard -> launch -> state -> contract -> record)
  - No-fake-success proof for the killed-run case (probe-B state reconstructed synthetically)
  - Warn-and-proceed pin for the over-budget win snake with head-inclusive counts
affects: [06-11 default-knob edit, Phase 7 spectra presenter, any future refactor of xtb_run/budget_guard/xtbenv/xyzio]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "House integration-suite pin (02-14 / 05-12 pattern): composition bugs surface as failing scenarios on shipped product code with zero stubs, fixtures read IN PLACE from .planning/research/xtb-spike-fixtures/"

key-files:
  created: [tests/test_phase6_integration.py]
  modified: []

key-decisions:
  - "Merged wave-1/2 module behavior treated as TRUTH where plan scenario text was written against wave-1 designs (unavailable-line wording, evaluate_run problem strings, launch_counts_line rendering) — the suite pins ACTUAL behavior; no serpentrum/ module was touched"

patterns-established:
  - "Phase-6 integration chain pin: build_run_input -> read_xyz_text -> launch_budget_warnings/launch_counts_line -> can_start/build_argv -> evaluate_run -> resolve_status -> new_spectra_run, in GUI/controller call order"

# Metrics
duration: 3min
completed: 2026-09-26
---

# Phase 6 Plan 10: Integration Chain Summary

**Phase-6 pure integration chain pinned in 10 scenarios on real fixture bytes: engine-shaped atoms -> run input xyz -> budget guard -> launch argv -> state machine -> 3-leg contract -> frozen Phase-7 record, with killed-run no-fake-success proven in both halves (cancel-wins resolution AND files-leg contract failure).**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-09-26T15:27:09Z
- **Completed:** 2026-09-26T15:29:40Z
- **Tasks:** 1/1
- **Files modified:** 1 (tests/test_phase6_integration.py, new, 274 lines)

## Accomplishments

- 10-scenario suite (`python3.6 -m unittest discover -s tests -p "test_phase6_integration.py" -v` — all pass) pinning the exact module composition GUI plan 06-09 and controller plan 06-05 implement, BEFORE GUI work relies on the seams.
- Happy path (real co2.xyz head + synthetic segment -> 5 head-inclusive atoms) and a 210-atom synthetic win snake (win AT the cap) both flow input -> guard -> argv -> contract -> record with the guard warning-and-proceeding, never blocking.
- Killed-run scenario reconstructs the live probe-B facts synthetically (06-RESEARCH-runner Q4: rc 62097, run dir holds only `.xtboptok`, `snake.xyz`, `xtbopt.log`) and asserts BOTH no-fake-success halves: `resolve_status(True, anything) == 'cancelled'` AND `evaluate_run(62097, success_err_text, EXPECTED_FILES, partial_files).ok is False` with exactly the exit + missing-files problems.
- Desync / unavailable / quote-rejection / abnormal-stderr-trap / record-shape guard rails pinned: every pre-existing test (785 -> 795) stays green UNMODIFIED; full `run_gates` green.

## Task Commits

Each task was committed atomically:

1. **Task 1: Integration scenario suite** - `c053ad9` (test)

**Plan metadata:** see `docs(06-10)` commit (SUMMARY).

## Files Created/Modified

- `tests/test_phase6_integration.py` - Phase-6 pure integration chain pin (house header, fixtures in place, zero stubs)

## Decisions Made

- Pinned the ACTUAL merged wave-1/2 behavior where the plan's scenario sketch was wave-1-draft-shaped (see Deviations/Reconciliations): the merged code is truth per the orchestrator's reality-check directive; no `serpentrum/` module was modified.

## Deviations from Plan

No code-level auto-fixes were needed (every scenario passed on first write against the merged modules). The following **plan-vs-code reconciliations** were applied while writing the pin suite (test file only; behavior unchanged):

**1. Plan-vs-code reconciliation: unavailable-line wording (budget_guard 06-01 auto-fix)**

- **Found during:** Task 1 (TestDesyncChain.test_garbage_inputs_unavailable_line)
- **Plan said:** "exactly the 'unavailable' line"
- **Merged code truth:** `'spectra input atom count unavailable - budget re-check skipped'` (budget_guard.py:96-98)
- **Resolution:** Pinned length-1 + `'unavailable'` + `'budget re-check skipped'`; same shape as the existing 06-01 unit tests, no literal drift.

**2. Plan-vs-code reconciliation: launch_counts_line rendering**

- **Plan said:** line "mentions '2 molecules' and '5 atoms'"
- **Merged code truth:** `'spectra input: 2 molecules (incl. head), 5 atoms (budget 100)'` (budget_guard.py:132-139) — substring assertions suffice; both plan-mentioned fragments present, head-inclusive +1 rendering confirmed.

**3. Plan-vs-code reconciliation: killed-run problem strings**

- **Plan said:** `any('exit code' in p)` and `any('missing expected output' in p)`
- **Merged code truth** (xtbenv.evaluate_run): `'exit code 62097 != 0'` + `'missing expected output file(s): g98.out, vibspectrum'` — stderr leg passes on the success fixture bytes, so exactly 2 problems; additionally pinned `len(problems) == 2` for a stronger no-fake-success statement.

**4. Plan-vs-code reconciliation: build_argv ValueError coverage**

- Plan sketched the input-filename quote case; quote rejection applies to ANY argv token (xtbenv.py:186-191), so the scenario also pins a quoted exe-path argument — same contract, both legs.

---

**Total deviations:** 0 code-level; 4 plan-vs-code reconciliations (test-pin shape only)
**Impact on plan:** None on scope; the merged modules' actual contracts are what got pinned, which is the plan's stated purpose.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- The Phase-6 seam contract is executable: any drift in `xtb_run` / `budget_guard` / `xtbenv` / `xyzio` (e.g. the 06-11 DEFAULT_RUN_KNOBS literals edit, or the HESSIAN_WARNING amendment) now fails this suite before GUI wiring relies on it.
- The suite covers the PURE halves of the five phase success criteria (SC1 input/argv contract; SC2 cancel/relaunch matrix; SC3 contract legs + quote guard; SC4 warn-and-proceed guard semantics; SC5 threshold behavior via the budget line). Live-QProcess halves belong to the 06-03/06-08 smokes.
- No blockers.

---
*Phase: 06-xtb-pipeline*
*Completed: 2026-09-26*
