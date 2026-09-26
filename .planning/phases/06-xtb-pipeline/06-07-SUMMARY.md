---
phase: 06-xtb-pipeline
plan: "07"
subsystem: infra
tags: [xtb, calibration, wall-time, qprocess, hessian, fixtures]

requires:
  - phase: 06-xtb-pipeline
    provides: gate-5 WSL direct-exec xtb pattern; smoke-09 QProcess probe mechanics (06-03); Q6 calibration method (06-RESEARCH-runner)
provides:
  - Deterministic fixture builder (tools/build_calibration_snake.py) tiling the committed dimer2 motif
  - Committed calibration fixtures calib_snake_52.xyz / calib_snake_104.xyz (round-trip verified)
  - Measured 104-atom --ohess wall times (16-run WSL sweep + 2 QProcess-timed runs): 84-101 s uncapped/-P 4, up to ~281 s at -P 1
  - 06-CALIBRATION.md: VERIFIED vs ASSUMED split, OMP_STACKSIZE verdict (not needed), three decision inputs for plan 06-11 (HESSIAN_WARNING literal, DEFAULT_RUN_KNOBS -P 4 cap, atom_budget=100 stays)
affects: [06-11 (guard/runner decision literals), phase-07 (spectra runtime expectations)]

tech-stack:
  added: []
  patterns:
    - "Deterministic derived-geometry fixture builder: tile a committed xtb-accepted motif by its centroid delta, round-trip-assert before commit — never hand-edited geometry"
    - "Calibration run hygiene: fresh per-run dir, bare relative argv, last-`total:` wall-time block parse, `omp threads : N` header echo, substring success detection with `abnormal termination` excluded (combined stdout/stderr redirect can interleave the literal mid-line)"

key-files:
  created:
    - tools/build_calibration_snake.py
    - tools/measure_calib_qprocess.py
    - tests/fixtures/calib_snake_52.xyz
    - tests/fixtures/calib_snake_104.xyz
    - .planning/phases/06-xtb-pipeline/06-CALIBRATION.md
  modified: []

key-decisions:
  - "QProcess pair interpreted as best-CAPPED (-P 4) vs uncapped (the sweep winner), giving 06-11 the most decision-relevant user-perceived comparison"
  - "OMP_STACKSIZE dispositioned: not needed at ~104 atoms (no uncapped crash in any of 18 runs)"
  - "Recommend -P 4 default cap (DEFAULT_RUN_KNOBS): ~18% user-perceived wall penalty vs uncapped, leaves 4 threads for PyMOL rendering (jank rationale PITFALLS.md:333,348)"
  - "HESSIAN_WARNING '30-90 s' literal must be amended: capped runs reach ~5 min at -P 1; uncapped measured 84-101 s"
  - "atom_budget default stays 100 (warn-and-proceed; measured 104-atom run is ~1.5-1.8 min user-perceived)"

duration: 34 min
completed: 2026-09-26
---

# Phase 6 Plan 07: ~104-atom --ohess Calibration (SC5) Summary

**104-atom capped snake `--ohess` wall time measured (not extrapolated): 84-101 s uncapped/-P 4 and 91-108 s user-perceived via QProcess; OMP_STACKSIZE unnecessary; three decision inputs committed for plan 06-11.**

## Performance

- **Duration:** 34 min (sweep ~22 min dominated by 8 104-atom runs)
- **Started:** 2026-09-26T14:33:21Z
- **Completed:** 2026-09-26T15:07:11Z
- **Tasks:** 2
- **Files modified:** 5 created, 0 modified (no serpentrum/ changes)

## Accomplishments

- **SC5's extrapolation replaced by measurements.** 16-run WSL direct-exec sweep (52/104 atoms x default/-P 1/-P 2/-P 4 x 2 repeats) plus 2 QProcess-timed headless-PyMOL runs; every run exited 0 with the `normal termination of xtb` contract literal and the full `g98.out`/`vibspectrum` file set.
- **Measured table committed** in `06-CALIBRATION.md`: 104 atoms = 6.7 s (52 atoms default) scaled to 84.1/90.1 s uncapped, 99.9/100.8 s at -P 4, 137.8/153.4 s at -P 2, 268.1/280.9 s at -P 1; QProcess user-perceived 104 atoms = 91.423 s uncapped, 107.588 s at -P 4.
- **OMP_STACKSIZE verdict: NOT NEEDED** — no uncapped run crashed anywhere (adopt-only-on-crash rule dispositioned at the 104-atom scale).
- **Decision inputs for 06-11 recorded:** amend the `HESSIAN_WARNING` 30-90 s literal (capped runs reach ~5 min); ship a `-P 4` default cap in `DEFAULT_RUN_KNOBS` (~18% user-perceived penalty buys 4 free threads against UI jank); `atom_budget=100` stays.

## Task Commits

1. **Task 1: Deterministic fixture builder + committed fixtures** — `2bac8d3` (feat)
2. **Task 2: Wall-time sweep + QProcess-timed runs + 06-CALIBRATION.md** — `2e4ece9` (docs)

## Files Created/Modified

- `tools/build_calibration_snake.py` — deterministic tiler: reads dimer2.xyz via `xyzio.read_xyz`, computes the inter-layer centroid delta (|3.4000| Å, sanity-bounded to [3.0, 4.0]), builds N-layer stacks (N=4,8), round-trip-asserts via `xyzio.read_xyz_text`, writes the fixtures.
- `tests/fixtures/calib_snake_52.xyz` — 4 phenol layers, 52 atoms.
- `tests/fixtures/calib_snake_104.xyz` — 8 phenol layers, 104 atoms (the ~100-atom capped snake).
- `tools/measure_calib_qprocess.py` — headless QProcess calibration probe (smoke-09 mechanics: one ensured app, QEventLoop + safety singleShot, `QElapsedTimer` walls, defensive error signal, smoke-09 exe candidate list); runs the 104-atom fixture at -P 4 and uncapped, asserts the 3-leg contract, prints `CALIB-OK QPROCESS` sentinel.
- `.planning/phases/06-xtb-pipeline/06-CALIBRATION.md` — measurement authority consumed by plan 06-11 (method, tables, VERIFIED/ASSUMED, OMP_STACKSIZE verdict, decision inputs).

## Decisions Made

1. **QProcess pair = best-CAPPED vs uncapped.** The plan said "BEST thread setting from the sweep (and once uncapped)"; the sweep winner was uncapped itself, so the QProcess pair measured `-P 4` (best explicitly-capped setting = the candidate shipped cap) vs uncapped — the most decision-relevant comparison for 06-11's DEFAULT_RUN_KNOBS choice. Documented in 06-CALIBRATION.md.
2. **Success detection keyed on substring minus `abnormal termination`.** Measured artifact: under `> log.txt 2>&1` the stderr contract literal can be emitted mid-line against buffered stdout; anchored grep would false-negative. QProcess runs see a clean literal on the stderr channel.
3. **Success bound interpretation:** `-P 4` recommended as the shipped default cap despite uncapped being fastest headless — the jank rationale (PITFALLS.md:333,348) concerns rendering starvation during interactive use; an 18% headless penalty is the lower bound on that trade.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Worktree lacks the `xtb-6.7.1` symlink**

- **Found during:** Task 2 (sweep setup)
- **Issue:** git worktrees do not carry git-ignored files; the repo-root `xtb-6.7.1` symlink (to `/mnt/c/xtb-6.7.1`) exists in the main checkout but not in `tmp/exec-06-07/`, so `<worktree>/xtb-6.7.1/bin/xtb.exe` did not exist.
- **Fix:** Created the symlink in the worktree (`ln -s /mnt/c/xtb-6.7.1 xtb-6.7.1`). It is git-ignored (`.gitignore` line `xtb-6.7.1`) so nothing stray was staged; identical target to the main-checkout symlink.
- **Files modified:** none tracked (untracked, git-ignored symlink)
- **Verification:** probe run `52_Pdef` completed rc=0 with `omp threads : 8` echo and 6.7 s wall before the sweep.

**2. [Rule 1 - Bug] Anchored `normal termination` detection false-negatived on combined redirects**

- **Found during:** Task 2 (sweep result parsing — 11/16 runs showed norm=0 despite rc=0)
- **Issue:** with `> log.txt 2>&1`, xtb's stderr literal is emitted mid-line against buffered stdout (e.g. `Some symmetry elements maynormal termination of xtb`), so `grep '^normal termination of xtb'` missed it.
- **Fix:** re-scored all 16 logs with substring detection + separate `abnormal termination` check (never present); recorded the artifact in 06-CALIBRATION.md so future sweeps don't repeat the mistake. (The QProcess path is unaffected: stdout/stderr are separate channels.)
- **Files modified:** `tmp/xtb_runs/calib/results.csv` (git-ignored), detection documented in 06-CALIBRATION.md
- **Verification:** all 16 runs scored normal termination with zero abnormal matches; consistent with rc=0 and the present `g98.out`/`vibspectrum` output sets.
- **Committed in:** `2e4ece9` (within the 06-CALIBRATION.md method note)

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug)
**Impact on plan:** Both were environment/detection mechanics; no scope change, no serpentrum/ edits, results unaffected.

## Issues Encountered

- None beyond the deviations above; the 104-atom run-to-run spread at `-P 1`/`52` repeats (e.g. 23.7 vs 34.0 s at 52 atoms/-P 1) is ordinary machine jitter and both repeats are committed in the table.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **Plan 06-11 is unblocked:** it can amend `HESSIAN_WARNING` + ship `DEFAULT_RUN_KNOBS` directly from 06-CALIBRATION.md without re-running anything (success criterion met).
- No blockers or concerns carried forward. Raw sweep logs remain inspectable at `tmp/xtb_runs/calib/` (git-ignored).

---
*Phase: 06-xtb-pipeline*
*Completed: 2026-09-26*
