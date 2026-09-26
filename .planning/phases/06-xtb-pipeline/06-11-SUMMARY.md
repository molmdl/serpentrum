---
phase: 06-xtb-pipeline
plan: 11
subsystem: infra
tags: [xtb, calibration, hessian, omp-threads, qprocess, wall-time]

# Dependency graph
requires:
  - phase: 06-xtb-pipeline (plan 06-07)
    provides: 06-CALIBRATION.md — measured 104-atom --ohess wall times + the three SC5 decision inputs
  - phase: 06-xtb-pipeline (plan 06-02)
    provides: xtb_run pure decision half (DEFAULT_RUN_KNOBS placeholder + build_env)
  - phase: 06-xtb-pipeline (plan 06-05)
    provides: XtbRunController.start extra_args/knobs default seams
  - phase: 05.2 (plan 5.2-09)
    provides: setup_logic shared-file wrap (ordering constraint for the shared edit)
provides:
  - "HESSIAN_WARNING literal carrying the MEASURED 104-atom wall times (calibrated, re-pinned)"
  - "DEFAULT_THREAD_ARG = ('-P', '4') argv-level default thread cap + controller consumption"
  - "DEFAULT_RUN_KNOBS finalized at {} (no default env overrides; OMP_STACKSIZE dispositioned not needed)"
  - "atom_budget default confirmed at 100"
affects: [07-spectra, budget_guard, setup warning UX]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Calibration-fed literal amendment: measured numbers replace extrapolation; the test pin diff IS the reviewable change"
    - "Argv-level resource cap (DEFAULT_THREAD_ARG) consumed by the controller's extra_args default; explicit caller overrides win"

key-files:
  created: []
  modified:
    - serpentrum/setup_logic.py
    - tests/test_setup_logic.py
    - serpentrum/xtb_run.py
    - tests/test_xtb_run.py
    - serpentrum/xtb_runner.py

key-decisions:
  - "HESSIAN_WARNING amended (not confirmed): measured 84-101 s at ~104 atoms contradicts the extrapolated '30-90 s' — the literal now carries measured numbers per 06-CALIBRATION.md decision input (a)"
  - "Default thread posture: argv-level '-P 4' cap (DEFAULT_THREAD_ARG), NOT an OMP env knob — ~18% user-perceived wall penalty buys 4 idle hardware threads for PyMOL (UI-jank pitfall); per decision input (b)"
  - "DEFAULT_RUN_KNOBS finalized at {}: no default env overrides; OMP_STACKSIZE dispositioned NOT NEEDED at the ~104-atom scale (no uncapped calibration run crashed)"
  - "atom_budget default STAYS 100: a 104-atom snake completes cleanly at ~1.7 min user-perceived, well inside warn-and-proceed (decision input (c))"

patterns-established:
  - "Calibration amendment: extrapolated warning copy + placeholder defaults are single literals swapped for measurements, with pins traveling alongside"

# Metrics
duration: 3 min
completed: 2026-09-26
---

# Phase 6 Plan 11: Calibration Apply Summary

**SC5's code half landed: HESSIAN_WARNING now carrying measured 104-atom wall times (84-101 s; ~5 min single-threaded) and the runner shipping a default '-P 4' argv thread cap — extrapolation replaced by measurement, all pins re-pinned, gates green**

## Performance

- **Duration:** 3 min
- **Started:** 2026-09-26T15:27:42Z
- **Completed:** 2026-09-26T15:30:31Z
- **Tasks:** 1
- **Files modified:** 5

## Accomplishments
- **HESSIAN_WARNING amended (decision input (a))** — the measured 104-atom range 84-101 s (uncapped/-P 4) straddled the extrapolated '30-90 s' window's top, so the literal was re-worded per 06-CALIBRATION.md's recommendation: keeps the '~N^3' framing and the ~100-atom anchor, ASCII, now reads measured numbers and the capped-run slowdown. Old→new literal:
  - OLD: `'hessian cost scales ~N^3; a ~100-atom snake may take 30-90 s'`
  - NEW: `'hessian cost scales ~N^3; a ~100-atom snake takes about 1-2 min on a typical 4-core/8-thread laptop (measured 84-101 s; thread-capped runs slower, up to ~5 min single-threaded)'`
- **Runner thread default decided (decision input (b))** — 'uncapped is fine' was NOT supported by the jank rationale; shipped `xtb_run.DEFAULT_THREAD_ARG = ('-P', '4')` (measured: 107.6 s capped vs 91.4 s uncapped user-perceived at 104 atoms = ~18% penalty, lower bound on interactive cost) and the controller's `start()` `extra_args` default now consumes it — explicit caller overrides still win. `DEFAULT_RUN_KNOBS` finalized at `{}` (a -P flag is not an OMP env knob; OMP_STACKSIZE dispositioned not needed — no uncapped run crashed in the sweep).
- **atom_budget stays 100 (decision input (c))** — no DEFAULTS change, no schema churn; the warning copy was the only thing calibration touched.
- Every pin traveled with its literal: test_setup_logic.py HESSIAN_WARNING pin re-pinned; test_xtb_run.py's 06-02 'uncapped until calibration' pin superseded by the finalized `{}` pin + a new DEFAULT_THREAD_ARG pin. budget_guard's drift-pin + launch line follow the amended literal automatically (no edit needed — verified by the full suite).

## Task Commits

1. **Task 1: Apply calibration decisions to literals + defaults + pins** - `6935436` (feat)

**Plan metadata:** (docs commit below)

## Files Created/Modified
- `serpentrum/setup_logic.py` — HESSIAN_WARNING literal + calibration citation comment (replaces PITFALLS-2 extrapolation rationale)
- `tests/test_setup_logic.py` — HESSIAN_WARNING pin re-pinned to the amended literal (test_constants_pinned)
- `serpentrum/xtb_run.py` — DEFAULT_RUN_KNOBS comment finalized (SC5 outcome), DEFAULT_THREAD_ARG = ('-P', '4') added with measurement citation, module docstring calibration cross-reference
- `tests/test_xtb_run.py` — test_default_run_knobs_uncapped → test_default_run_knobs_no_env_overrides (finalized {}) + test_default_thread_arg_capped added ('-P', '4')
- `serpentrum/xtb_runner.py` — conditional 2-line edit landed (argv cap chosen): start() extra_args default = (XTB_OHESS,) + xtb_run.DEFAULT_THREAD_ARG; docstring updated

## Decisions Made
All three flowed directly from 06-CALIBRATION.md's decision inputs (no re-measurement, per SC5 key_link):
1. **Amend the warning literal** — measured 84-101 s straddles the stated '30-90 s' window's top; doc explicitly recommends amendment with VERIFIED numbers (kept ~N^3 framing, ~100-atom anchor, ASCII, same sentence shape).
2. **Ship the '-P 4' argv cap** — doc recommends capping: 18% measured user-perceived penalty, 4 threads left for PyMOL; applied as DEFAULT_THREAD_ARG (argv-side, since xtb_run.build_env only accepts the three help-verified OMP env knobs) + the conditional controller touch. DEFAULT_RUN_KNOBS stays {} as the FINAL value.
3. **atom_budget stays 100** — doc argues to keep it with measured numbers (104-atom snake ~1.7 min user-perceived, inside warn-and-proceed).

## Deviations from Plan

None - plan executed exactly as written. All edits were the plan's pre-authorized conditional paths (the xtb_runner.py touch was explicitly allowed because the calibration decision picked an argv-level cap).

## Issues Encountered
None. Full gate suite green on first run after the edits (786 unittests — 785 baseline + 1 new DEFAULT_THREAD_ARG pin).

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- SC5 fully discharged: the shipped warning text and runner default are now measurement-derived (no undecided middle state).
- The grep '30-90' audit returns only the superseded-value citations in comments (historical context), consistent with the amendment.
- `Python3.6 -c "... print(xtb_run.DEFAULT_RUN_KNOBS)"` prints `{}` and `DEFAULT_THREAD_ARG` prints `('-P', '4')` — the decided values.
- Phase 7 consumers (spectra presenter) inherit a runner whose default launch is already thread-capped; no further action needed there.

## Verification Outputs
- `python3.6 tests/run_gates.py` → all gates green (786 tests, OK)
- `grep -rn "30-90" serpentrum/ tests/` → 2 hits, both superseded-value citations in comments
- `git diff --stat` → exactly the 5 frontmatter-listed files (63 insertions, 17 deletions)

---
*Phase: 06-xtb-pipeline*
*Completed: 2026-09-26*
