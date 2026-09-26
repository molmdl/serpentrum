---
phase: 06-xtb-pipeline
plan: 08
subsystem: infra
tags: [qprocess, pyqt5, qt5.12.9, xtb, headless, smoke, runner-contract, cancel, no-double-run, failedtostart]

# Dependency graph
requires:
  - phase: 06-xtb-pipeline (plan 06-03)
    provides: smoke 09 live pins — connect-before-start (synchronous errorOccurred), kill->CrashExit geometry, dimer2 timer margins, binary candidate list
  - phase: 06-xtb-pipeline (plan 06-05)
    provides: serpentrum.xtb_runner XtbRunController (the controller under test) + xtb_run frozen SPECTRA_RUN_KEYS record
  - phase: 01-plugin-skeleton-purity-harness
    provides: smoke template obligations + pmg_tk.startup.serpentrum loader-name identity mechanics (smoke 01)
provides:
  - smoke/11_xtb_runner_smoke.py — live proof of the XtbRunController contract against the REAL xtb.exe (success contract, cancel, no-double-run, responsiveness, start-failure path); sentinel SMOKE-OK XTB-RUNNER; informational in run_gates --smoke
  - verified FACT: bad-exe start() returns False AND emits run_finished('failed', [...]) SYNCHRONOUSLY inside start() (the 06-05 synchronous-FailedToStart re-check) — no event-loop wait possible or needed
  - verified FACT: restart after completion AND after cancel both return True (SC2 guard release, headless level)
affects: [06-xtb-pipeline plans 06-09..06-12 (GUI wiring, calibration, promotion decision), phase-07 spectra presenter (record consumer), pyqt5-signal-ordering]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "_wait_controller(timeout_ms, begin): connect ctrl.run_finished -> record+loop.quit BEFORE begin() (connect-before-start is binding), safety singleShot, events via the loop only"
    - "synchronous-failure step: connect run_finished, call start(), assert the record IMMEDIATELY after return — no loop (the signal already fired inside start())"
    - "spray-leak scan: baseline-diff of srp_-prefixed %TEMP% entries, 'srp_spectra' root excluded (it is the artifact policy, not spray)"
    - "per-step per-snake stable-dir pre-clean, prefix-guarded to smoke11_* ids — repeated smoke runs stay self-contained while stable dirs remain left-in-place after each step"

key-files:
  created: [smoke/11_xtb_runner_smoke.py]
  modified: []

key-decisions:
  - "Restart-after-completion cleanup uses dimer2 + singleShot(300, cancel) — deterministic 'cancelled'; co2 (~76-90 ms wall here) races any pre-scheduled cancel timer (smoke-09 deviation-1 fact)"
  - "Follow-up-after-cancel accepts terminal 'ok' OR 'cancelled' for the tiny co2 run — start() returning True is the guard-release assertion; the 89 ms race is not the subject"
  - "Bad-exe step asserts the ACTUAL 06-05 contract (returns False + synchronous 'failed'), connected before start, no event loop — see Deviation 1"
  - "Smoke stays INFORMATIONAL per EQ-smoke-1; promotion decided at 06-12"

patterns-established:
  - "Controller smoke step mapping: arun_success_contract -> SC1/SC3, cancel_path + no_double_run_guard -> SC2, responsiveness_tick -> SC1 (headless async-ness; in-GUI responsiveness remains the 06-12 human checkpoint)"

# Metrics
duration: 5min
completed: 2026-09-26
---

# Phase 6 Plan 8: Runner Contract Smoke Summary

**Controller-contract smoke green end-to-end against the REAL xtb.exe — co2 success contract (status 'ok', frozen record, stable artifacts, spray dir deleted), cancel with no fakable success, no-double-run guard, 305 ms responsiveness tick while 'running', and the bad-exe path proven as returns-False + synchronous run_finished('failed') — the runner's live verification before any GUI wiring**

## Performance

- **Duration:** 5 min
- **Started:** 2026-09-26T15:28:14Z
- **Completed:** 2026-09-26T15:33:18Z
- **Tasks:** 1
- **Files modified:** 1 created, 0 modified (zero serpentrum/ changes, verified by git status)

## Accomplishments

- `smoke/11_xtb_runner_smoke.py` committed and green: all 8 steps pass against the real Windows conda PyMOL (Qt 5.12.9) + real xtb.exe — `SMOKE-OK XTB-RUNNER` flushed as the sentinel verdict.
- Run command (from repo root): `timeout 300 cmd.exe /c "C:\src\run-conda-pymol.bat -cq smoke\11_xtb_runner_smoke.py"`.
- **Key PROBE lines from the green run (2026-09-26):**
  - `PROBE QT: 5.12.9, has QProcess=True, app=QCoreApplication`
  - `PROBE RUNNER module: pmg_tk.startup.serpentrum.xtb_runner status0: None` — loader-name identity + controller on the `pmg_tk.startup._serpentrum` anchor (never module globals)
  - `PROBE XTB_EXE: C:\xtb-6.7.1\bin\xtb.exe` (env unset, `detect_binary(None)` -> None on this machine, verified fallback hit — EQ-binary-1 path list exercised)
  - `PROBE ARUN elapsed_ms: 90 status: ok problems: []` — REAL co2 --ohess through the controller: started fired, log lines streamed, anchor record = frozen `SPECTRA_RUN_KEYS` with 'ok' + all five paths non-None; stable `srp_spectra/smoke11_ok/` holds snake.xyz/xtb.log/g98.out/vibspectrum/xtbopt.xyz
  - `PROBE SPRAY leftover: []` — the mkdtemp('srp_') spray dir was deleted at the terminal branch
  - `PROBE RESTART started: True cleanup_status: cancelled` — SC2: start returns True after completion (kill at 300 ms -> cancelled)
  - `PROBE TICK elapsed_ms: 614 tick_at_ms: 306 status_at_tick: running final: cancelled` — QTimer fired while `ctrl.status() == 'running'` mid dimer2 run (headless async-ness)
  - `PROBE CANCEL elapsed_ms: 314 status: cancelled` + `PROBE AFTER_CANCEL started: True final: ok` — cancel contract AND SC2 restart-after-cancel
  - `PROBE GUARD first: True second: False guard_log: [..., 'an xtb run is already active - cancel or wait for it to finish', ...] cleanup: cancelled`
  - `PROBE BADEXE returned: False raised: None signal: {'status': 'failed', 'problems': ['xtb could not be started: Process failed to start: The system cannot find the file specified.']} ctrl.status: 'failed'` — pitfall-9 surface-never-die proof, synchronously inside start()
- Cancel stable dir holds snake.xyz + xtb.log but NO g98.out/vibspectrum/xtbopt.xyz (record paths None) — a killed run can never masquerade as success (probe-B fact re-verified at the controller level).
- Gates: `python3.6 tests/run_gates.py` green (785 unittests, syntax walk, purity); `python3.6 tests/run_gates.py --smoke` green, quoting the informational line verbatim:
  - `note: informational smoke smoke/11_xtb_runner_smoke.py: PASS`

## Task Commits

1. **Task 1: Write + run the runner contract smoke** - `768b0cf` (test)

## Files Created/Modified

- `smoke/11_xtb_runner_smoke.py` (559 lines, new) — 8 named steps + check() runner, flush=True everywhere, _resolve_root() candidate validation, NO widgets, no waitForFinished, no subprocess, new-style .connect() only, sentinel-only verdict. Output is smoke-only: zero `serpentrum/` or `tests/` modifications.

## Decisions Made

- Restart-after-completion cleanup switch co2 -> dimer2 (deviation 2): co2 completes in ~76-90 ms here, racing any pre-scheduled cancel timer; dimer2 + singleShot(300, cancel) makes the cleanup branch deterministic.
- Follow-up-after-cancel: terminal status asserted as 'ok' OR 'cancelled' — the SC2 subject is start() returning True, not the 89 ms race outcome (second run happened to finish 'ok').
- Bad-exe step written against the ACTUAL 06-05 contract after reading serpentrum/xtb_runner.py (deviation 1 in plan-text-vs-code terms — no code change): returns False + synchronous run_finished('failed'), asserted immediately after start() with no event loop.
- Spray-leak scan excludes the 'srp_spectra' root: it shares the 'srp_' prefix but IS the keep-until-replaced artifact policy, not spray (deviation 3 — my own first-run scan bug).

## Deviations from Plan

### Contract discrepancy (plan text vs actual controller behavior — recorded per orchestrator instruction)

**Plan step 8 text:** "assert it does NOT raise and terminates in 'failed' quickly (run_finished status 'failed' ...); state is terminal afterwards" — phrased like a normal async wait.
**ACTUAL 06-05 contract** (verified in serpentrum/xtb_runner.py:155-181, 310-330 and live): for a bad exe, `errorOccurred(FailedToStart)` fires SYNCHRONOUSLY inside `proc.start()`, `_on_error` runs the full terminal discipline and emits `run_finished('failed', [...])` BEFORE `start()` returns, and `start()` then returns **False** (its post-start `self._status != xtb_run.RUNNING` re-check). The smoke therefore connects `run_finished` BEFORE `start()` and asserts the record immediately — no QEventLoop is entered for this step (nothing more arrives). The plan's intent (does-not-raise, 'failed', terminal) is fully satisfied; the mechanics are synchronous, not just "quick".

### Auto-fixed Issues

**1. [Rule 1 - Bug] Spray-leak scan falsely flagged the stable artifact root**

- **Found during:** Task 1 (first real smoke run)
- **Issue:** `_srp_entries` matched every 'srp_'-prefixed %TEMP% entry; `srp_spectra` (the stable artifact root created by the first terminal copy-out) starts with 'srp_' and was flagged as a leaked spray dir -> `SMOKE-FAIL arun_success_contract` on a controller that behaved correctly.
- **Fix:** exclude the literal 'srp_spectra' root from the scan (it is the artifact policy under test, not spray); docstring explains the distinction.
- **Files modified:** smoke/11_xtb_runner_smoke.py
- **Verification:** `PROBE SPRAY leftover: []` + full `SMOKE-OK XTB-RUNNER`.
- **Committed in:** 768b0cf

**2. [Rule 1 - Bug / timing race] Restart-after-completion cleanup could not use co2**

- **Found during:** Task 1 (design time, applying the smoke-09 deviation-1 live pin)
- **Issue:** Plan step 4 says "cancel it immediately ... and wait for 'cancelled'" after the post-completion second start; co2's ~76-90 ms wall makes a deterministic 'cancelled' label unreachable for a timer-scheduled cancel.
- **Fix:** the restart step uses dimer2 + `QTimer.singleShot(300, ctrl.cancel)` (kill lands mid-run); the guard-release assertion (start() True) is unchanged.
- **Files modified:** smoke/11_xtb_runner_smoke.py
- **Verification:** `PROBE RESTART started: True cleanup_status: cancelled`.
- **Committed in:** 768b0cf

---

**Total deviations:** 2 auto-fixed (both correctness/timing, discovered by the real-environment runs the plan mandates) + 1 plan-text contract discrepancy recorded (no fix needed — asserted the actual contract)
**Impact on plan:** Every assertion the plan's truths demanded is proven; only the mechanics of two steps were adapted to verified Qt/xtb timing. No scope creep.

## Issues Encountered

None beyond the deviations above (each found and fixed within the same smoke iteration). Related observation for the record: smoke 09's `timeout` key in `_srp_entries` family is untouched — no controller or purity issues surfaced.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **Runner track SC1/SC2/SC3 mechanics are headless-proven at the controller level** before any GUI wiring: success contract, cancel-with-no-fake-success, no-double-run + guard release on every terminal branch, responsiveness tick, clean start-failure path. The only remaining unverified surface is in-GUI responsiveness/UX (the 06-12 human checkpoint).
- Smoke 11 + smoke 09 together form the runner track's committed, re-runnable regression pair.
- Consumer facts for plans 06-09..06-11: connect the bad-exe listener BEFORE start() (synchronous emission); start() returning False means the terminal branch ALREADY ran (do not wait for another signal); co2-vs-dimer2 timing pins for any further timer assertions.
- Smoke stays INFORMATIONAL per EQ-smoke-1 (promotion decision at 06-12); it currently passes inside the 90 s gate timeout (~30 s wall here including PyMOL startup and all real xtb runs).
- Note: `note: informational smoke smoke/02_dialog_smoke.py: FAIL (non-blocking)` is pre-existing (the 01-05 offscreen-dialog dead end) and unrelated to this plan; gate remains green.

---
*Phase: 06-xtb-pipeline*
*Completed: 2026-09-26*
