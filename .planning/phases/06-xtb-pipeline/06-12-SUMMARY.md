---
phase: 06-xtb-pipeline
plan: 12
subsystem: infra
tags: [xtb, qprocess, gates, human-checkpoint, phase-close]

# Dependency graph
requires:
  - phase: 06-xtb-pipeline (plans 06-01..06-11)
    provides: the complete launch/cancel/relaunch pipeline — budget_guard, xtb_run state machine, XtbRunController, launch pipeline, spectra placeholder tab, calibration-applied literals
  - phase: 05.2 (plan 5.2-09)
    provides: shared-file ordering for setup_logic/gui edits; the blocking human-verify checkpoint model (numbered steps, per-step EXPECT, verdict table)
provides:
  - "final gate verdicts on the completed phase tree (default + --smoke + --xtb)"
  - "the ONE blocking live human-verify checkpoint of the pipeline in real Windows PyMOL (launch / cancel / relaunch / failures / head-inclusive counts)"
  - "EQ decisions record for Phase 6 + Phase-7 handoff notes (spectra_run keys, artifact paths, runner signal vocabulary, deferred UI scope)"
affects: [07-spectra, phase wrap-up, REQUIREMENTS close-out]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Phase-closing gate triplet: default + --smoke + --xtb legs recorded verbatim before the blocking checkpoint"
    - "5.2-09 checkpoint model reused: per-step EXPECT lines referencing symbols, verdict table, per-item approvals accumulate"

key-files:
  created:
    - .planning/phases/06-xtb-pipeline/06-12-SUMMARY.md
  modified: []

key-decisions:
  - "EQ-smoke-1: smokes 09/11 stay INFORMATIONAL by default (depend on the local xtb.exe fallback list); REQUIRED promotion only on explicit owner instruction"
  - "EQ-checkpoint-1: the live checkpoint covers the pipeline + placeholder affordances; Spectra PLOT/TABLE/LOG-PANEL verdicts DEFERRED to Phase 7"

patterns-established:
  - "Phase close = gates task + ONE blocking checkpoint + conditional fix/finalize task; SUMMARY drafted at gates, finalized at owner approval"

# Metrics
duration: ~5 min (Task 1 gates round)
completed: 2026-09-26 (pending checkpoint approval — Task 3 finalizes)
---

# Phase 6 Plan 12: Phase-Close Gates + Checkpoint Summary

**Full gate suite green on the completed Phase-6 tree (796 unittests, 8/8 required smokes incl. the new 10_chain_count, Windows xtb probe PASS) — the phase now awaits the ONE blocking live feel-check in real Windows PyMOL before close-out**

## Performance

- **Duration (Task 1 so far):** ~5 min
- **Started:** 2026-09-26T16:33:34Z
- **Completed:** PENDING (Task 2 checkpoint + Task 3 finalization)
- **Tasks:** 1 of 3 complete (Task 1 gates; Task 2 = BLOCKING human-verify; Task 3 = finalize)
- **Files modified:** 1 (this SUMMARY)

## Task-1 Gate Results (FINAL — recorded 2026-09-26T16:33-16:45Z)

### Leg 1: `python3.6 tests/run_gates.py` — GREEN
- **796 tests ran, OK** (3.101 s)
- gate 1: syntax + plugin-path safety — PASS
- gate 2: purity (AST) — PASS
- gate 3: unittest (scoped discover) — PASS
- `run_gates: all gates green`
- **Count delta:** 796 vs the **785** phase-entry baseline (06-11-SUMMARY: 786 = 785 + 1 DEFAULT_THREAD_ARG pin; the merged 06-10 10-scenario `test_phase6_integration.py` suite contributes the other 10) → **+11 vs 785**. Longer-horizon anchor: 755 at Phase-6 entry (06-03-SUMMARY) → **+41 across the phase**.

### Leg 2: `python3.6 tests/run_gates.py --smoke` — GREEN
- 796 tests OK (2.891 s), then headless smoke battery:
- REQUIRED smokes — **8/8 PASS** via flushed SMOKE-OK sentinels:
  - `smoke/01_skeleton_smoke.py`: PASS (`SMOKE-OK SKELETON`)
  - `smoke/03_viewer_bridge_smoke.py`: PASS (`SMOKE-OK VIEWER-BRIDGE`)
  - `smoke/04_demo_e2e_smoke.py`: PASS (`SMOKE-OK VIEWER-DEMO`)
  - `smoke/05_loop_camera_smoke.py`: PASS (`SMOKE-OK LOOP-CAMERA`)
  - `smoke/06_input_smoke.py`: PASS (`SMOKE-OK INPUT-WIZARD`)
  - `smoke/07_transform_sweep_smoke.py`: PASS (`SMOKE-OK TRANSFORM`)
  - `smoke/08_stack_place_smoke.py`: PASS (`SMOKE-OK EDGEON`)
  - `smoke/10_chain_count_smoke.py`: PASS (`SMOKE-OK CHAIN-COUNT`)
- Informational smokes:
  - `smoke/02_dialog_smoke.py`: FAIL (non-blocking) — the KNOWN dead end (01-05: no offscreen dialog testing; recorded in STATE.md Blockers)
  - `smoke/09_qprocess_smoke.py`: PASS (informational — EQ-smoke-1: stays informational by default)
  - `smoke/11_xtb_runner_smoke.py`: PASS (informational — same disposition)
- gate 4: headless smokes (required) — PASS
- `run_gates: all gates green`

### Leg 3: `python3.6 tests/run_gates.py --xtb` — GREEN
- 796 tests OK (3.193 s), then the Windows-xtb-from-WSL probe:
- `xtb gate: winpath sanity /mnt/c/Users/nglok/Desktop/WORKDIR/molmdl/serpentrum -> C:/Users/nglok/Desktop/WORKDIR/molmdl/serpentrum`
- `xtb gate: * xtb version 6.7.1pre (5071a88) compiled by 'Marcel@Raven' on 2024-07-23 (rc=0)`
- `xtb gate: normal termination of xtb`
- gate 5: xtb probe (Windows from WSL) — PASS
- `run_gates: all gates green`

**Zero fixes needed — the merged phase tree (waves 1-3 merged via `exec/06-08`/`09`/`10`/`11` branches) is gate-green across all three legs on first run.**

## SC5 cross-check (no live step — verified by artifacts)

- **06-CALIBRATION.md (06-07):** 104-atom `--ohess` wall 84-101 s uncapped / -P 4 on the calibration machine; QProcess user-perceived 91.4-107.6 s; OMP_STACKSIZE dispositioned NOT NEEDED (no uncapped run crashed); atom_budget STAYS 100.
- **06-11-SUMMARY.md:** HESSIAN_WARNING literal carries the measured numbers ('about 1-2 min ... measured 84-101 s; thread-capped runs slower, up to ~5 min single-threaded'); DEFAULT_THREAD_ARG = ('-P','4') shipped; '30-90' audit shows only superseded-value citations.

## Task Commits

1. **Task 1: Final full-gates pass on the completed phase tree** - `(see below)` (docs)

**Plan metadata:** (Task 3 finalization commit — pending checkpoint approval)

## Checkpoint — PENDING (Task 2)

The blocking human-verify of the launch / cancel / relaunch / failure pipeline in real Windows PyMOL is presented to the owner (12 steps, per-step EXPECT lines, PASS/FAIL verdict table). The verdict table lands HERE after Task 2 approval:

| Step | Covers | Verdict |
|------|--------|---------|
| 1..12 | (per plan how-to-verify) | PENDING |

## EQ Decisions Record — PENDING (Task 3)

To be recorded at close-out from 06-RESEARCH-runner.md / 06-RESEARCH-guard.md and the plan context: EQ-xyz-1, EQ-guard-1, EQ-guard-2, EQ-desync-1, EQ-omp-1, EQ-artifact-1, EQ-binary-1, EQ-smoke-1, EQ-ux-1/2, EQ-checkpoint-1.

## Phase-7 Handoff Notes — PENDING (Task 3)

spectra_run record keys, stable artifact paths (%TEMP%\srp_spectra\<snake_id>\), runner signal vocabulary (started / log_line / run_finished), placeholder-widgets-are-temporary note.

## Deviations from Plan

None so far — Task 1 executed exactly as written (no gate failures, no fixes).

## Issues Encountered

None (Task 1).

## Next Phase Readiness

PENDING the checkpoint: on approval, Phase 6 closes and Phase 7 (spectra presenter: plot/table/log-panel over the placeholder) inherits the recorded handoff.

---
*Phase: 06-xtb-pipeline*
*Completed: PENDING checkpoint approval (2026-09-26, Task 1 gates recorded)*
