# 06-CALIBRATION — measured `--ohess` wall times (SC5)

**Measured:** 2026-09-26 (plan 06-07)
**Machine:** Intel Core i7-1065G7 @ 1.30 GHz (4 cores / 8 hardware threads; xtb default `omp threads : 8`), WSL2 (Ubuntu) side and Windows conda PyMOL 2.5.0 side of the same host
**Binary:** xtb 6.7.1pre at `C:\xtb-6.7.1\bin\xtb.exe` (WSL path `/mnt/c/xtb-6.7.1/bin/xtb.exe` via the repo-root `xtb-6.7.1` symlink)
**Fixtures:** `tests/fixtures/calib_snake_52.xyz` (4 phenol layers) and `tests/fixtures/calib_snake_104.xyz` (8 phenol layers) — deterministically built by `tools/build_calibration_snake.py` from the committed, xtb-accepted `dimer2.xyz` motif (inter-layer centroid delta |3.4000| Å, asserted in [3.0, 4.0] Å). No hand-edited geometry.

This document REPLACES SC5's "~100-atom 30-90 s" extrapolation (PITFALLS.md:71) with measurements. Plan 06-11 consumes the three decision inputs at the bottom WITHOUT re-running any experiment.

## Method

1. **WSL direct-exec sweep** (gate-5 pattern, `tests/run_gates.py` + `test_wsl_winxtb.sh`): per run, fresh dir `tmp/xtb_runs/calib/<label>/`, fixture copied in as `snake.xyz`, then
   `timeout 600 <root>/xtb-6.7.1/bin/xtb.exe snake.xyz --ohess [-P N] > log.txt 2>&1`
   with cwd = that dir (the dir is /mnt/c-backed). Wall time = the `total:` block's `* wall-time:` line (each stage has a wall-time block; the LAST `total:` block is the run total); thread echo = the header `omp threads : N` line. 2 fixtures x 4 thread settings (default, -P 1, -P 2, -P 4) x 2 repeats = 16 serial runs. An external bash `date` envelope was also recorded (incl. exe spawn; within 0.1 s of the xtb-reported total everywhere — WSL-side spawn overhead is negligible).
2. **QProcess-timed in-plugin runs** (`tools/measure_calib_qprocess.py`, run via `timeout 900 cmd.exe /c "C:\src\run-conda-pymol.bat -cq tools\measure_calib_qprocess.py"`): `QElapsedTimer` around the whole `QProcess` run inside headless conda PyMOL — the TRUE USER-PERCEIVED wall incl. PyMOL-side startup overhead (probe pattern, 06-RESEARCH-runner.md Q6). 104-atom fixture, once at `-P 4` (best measured CAPPED setting) and once uncapped (the sweep winner), serially. Both runs asserted: finished (0, NormalExit), stderr contains the contract literal, `g98.out` + `vibspectrum` present.
3. **Success detection caveat (measured today):** under `> log.txt 2>&1` on WSL, xtb's stderr `normal termination of xtb` can be emitted mid-line against buffered stdout (e.g. `Some symmetry elements maynormal termination of xtb`). Detection therefore keyed on the `normal termination of xtb` substring with `abnormal termination` checked separately (never seen). In QProcess runs stdout/stderr arrive on separate channels and the literal is clean — this artifact is a redirection artifact of the sweep only, not an xtb/QProcess defect.

## Measured wall-time table (xtb-reported `total:` * wall-time)

| atoms | threads (argv) | omp echo | rep 1 (s) | rep 2 (s) | normal termination | source |
|-------|----------------|----------|-----------|-----------|--------------------|--------|
| 52 | (default) | 8 | 6.726 | 6.293 | yes / yes | `tmp/xtb_runs/calib/52_Pdef_r*/log.txt` |
| 52 | `-P 1` | 1 | 23.738 | 33.991 | yes / yes | `52_P1_r*` |
| 52 | `-P 2` | 2 | 14.442 | 15.059 | yes / yes | `52_P2_r*` |
| 52 | `-P 4` | 4 | 9.049 | 11.751 | yes / yes | `52_P4_r*` |
| 104 | (default) | 8 | 84.132 | 90.062 | yes / yes | `104_Pdef_r*` |
| 104 | `-P 1` | 1 | 268.063 | 280.921 | yes / yes | `104_P1_r*` |
| 104 | `-P 2` | 2 | 137.770 | 153.446 | yes / yes | `104_P2_r*` |
| 104 | `-P 4` | 4 | 100.752 | 99.888 | yes / yes | `104_P4_r*` |

**QProcess-timed user-perceived wall (104 atoms, headless conda PyMOL, QElapsedTimer):**

| atoms | threads | wall (s) | stderr head | source |
|-------|---------|----------|-------------|--------|
| 104 | `-P 4` | 107.588 | `normal termination of xtb` | PROBE WALL-MS P4 |
| 104 | (default, uncapped) | 91.423 | `normal termination of xtb` | PROBE WALL-MS uncapped |

All 18 runs: exit 0, NormalExit, the `normal termination of xtb` contract literal present, `g98.out` + `vibspectrum` written; ZERO `abnormal termination`. Compare with prior [RUN] points: phenol 13 atoms 0.67 s, dimer 26 atoms 1.75 s (06-RESEARCH-runner Q6).

## VERIFIED vs ASSUMED

**VERIFIED (measured today):**
- 104-atom capped snake completes `--ohess` headless with normal termination on BOTH the WSL direct-exec path and the in-conda QProcess path, at every thread setting tried (uncapped/1/2/4).
- 104-atom wall time on THIS machine: **84-101 s** uncapped or `-P 4`; **100-153 s** at `-P 2`; **268-281 s** (~4.5-4.7 min) at `-P 1`. QProcess user-perceived adds ~2-7 s over the WSL xtb total (91.4 s vs 84-90 s uncapped; 107.6 s vs 100 s at -P 4).
- 52-atom wall time: 6.3-6.7 s uncapped up to 23.7-34.0 s at -P 1.
- Default `-P` (no flag) = all 8 hardware threads on this machine; the `-P N` argv knob echoes `omp threads : N` exactly as documented (06-RESEARCH-runner Q6).
- The last-`total:`-block parse and the `omp threads` header echo are stable across all 16 sweep logs.
- Uncapped OMP does NOT crash at 104 atoms; no stack overflow anywhere in the sweep.

**ASSUMED (still unmeasured / machine-dependent):**
- Absolute times port to other machines only as order-of-magnitude (different core counts; here 8 HT on a 1.3 GHz mobile quad).
- The exact hessian scaling exponent: from the 26->52->104 wall-time doublings on this machine, wall grows ~3.7x (26->52, ~N^1.9) then ~13-14x (52->104 uncapped, ~N^2.7 - N^2.8) — consistent with the ~N^3 cost MODEL at the 100-atom scale, but it remains a model fitted to few points, not a law.
- Warning copy must therefore avoid promising a tight time bound (see decision input (a)).

## OMP_STACKSIZE verdict

**NOT NEEDED at the ~104-atom scale.** No uncapped run crashed: all 8 default-thread runs (4 sweep + repeats, incl. the 104-atom pair at 84-90 s) plus the QProcess uncapped run (91.4 s) terminated normally with no stack fault. The `[TRAIN]` LOW hypothesis (PITFALLS.md:431, xtb help:229-231) is dispositioned for this size: do NOT set `OMP_STACKSIZE` by default (it is an unverified knob and unnecessary at the shipped scale; revisit only if an uncapped run on a real machine crashes — the same adoption rule stated in the plan).

## Decision inputs for plan 06-11

**(a) HESSIAN_WARNING literal vs measurements.** The current literal `'hessian cost scales ~N^3; a ~100-atom snake may take 30-90 s'` (`serpentrum/setup_logic.py:118-119`, drift-pinned by `tests/test_setup_logic.py`) UNDERSTATES capped runs: measured 104-atom wall is 84-101 s uncapped/-P 4 (top of the claimed range on a 1.3 GHz 8-thread machine), 100-153 s at -P 2, and ~4.5-4.7 MINUTES at -P 1. Recommended amendment (06-11 owns the literal + re-pinning the tests): state the measured uncapped scale "about 1-2 minutes on a typical 4-core/8-thread laptop (measured 84-101 s)" and note that thread-capped runs are slower (up to ~5 min single-threaded) rather than a tight 30-90 s promise. All numbers above are VERIFIED on the calibration machine; the "typical laptop" generalisation is ASSUMED.

**(b) DEFAULT_RUN_KNOBS / -P default.** Measured cost of capping on this 8-thread machine: -P 4 costs ~18% wall vs uncapped in user-perceived time (107.6 s vs 91.4 s) while leaving 4 hardware threads for PyMOL rendering — directly addressing the UI-jank pitfall (PITFALLS.md:333,348: uncapped xtb grabs all cores and can stall the GUI). -P 2 costs ~63%. -P 1 nearly quadruples+ the wall (280+ s). **Recommended: ship a default cap of `-P 4`** (or `max(2, cores/2)` computed at runtime) in `DEFAULT_RUN_KNOBS` ('uncapped is fine' is NOT supported by the jank rationale; the 18% headless penalty is a lower bound on interactive cost since the headless probe has no render loop competing). 06-11 applies this; this document provides the numbers, not the code.

**(c) atom_budget default.** **STAYS at 100.** A 104-atom snake (a full default win-cap chain incl. head is routinely 104-260 atoms; 06-RESEARCH-guard Q2) completes cleanly at ~1.7 min user-perceived — well inside the warn-and-proceed regime. No schema churn (06-RESEARCH-guard Q7 preference for constants over schema keys): the budget is a warning threshold, and the warning text is the only thing calibration touches (input (a)).

## Raw artifacts (git-ignored)

- Sweep logs + `results.csv`: `tmp/xtb_runs/calib/<52_Pdef_r1 .. 104_P4_r2>/log.txt` (16 dirs)
- Sweep driver: `tmp/sweep.sh`
- QProcess probe: `tools/measure_calib_qprocess.py` (committed); its raw output lives in the plan's execution record (PROBE WALL-MS lines quoted above)
