---
phase: 06-xtb-pipeline
plan: 03
subsystem: infra
tags: [qprocess, pyqt5, qt5.12.9, xtb, headless, smoke, gate-event-loop, cancel]

# Dependency graph
requires:
  - phase: 02-pure-core-game-chemistry-logic
    provides: serpentrum.xtbenv (detect_binary / STDERR_SUCCESS contract, PURE headless-safe)
  - phase: 01-plugin-skeleton-purity-harness
    provides: smoke template obligations (check() runner, _resolve_root, flushed sentinels)
provides:
  - smoke/09_qprocess_smoke.py — the roadmap's Phase-6 QProcess-in-conda gate, discharged against the REAL Windows conda PyMOL + REAL xtb.exe
  - live-pin: errorOccurred attribute EXISTS on PyQt5 Qt 5.12.9 (research open question 5 settled)
  - live-pin: errorOccurred(FailedToStart) fires SYNCHRONOUSLY inside proc.start() — every runner signal must be connected BEFORE start()
  - live-pin: kill-cancellation geometry + timings for plans 06-05/06-08
affects: [06-xtb-pipeline runner plans 06-05, 06-08, pyqt5-signal-ordering]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "connect-before-start: all QProcess signals wired before proc.start() via _wait_run(begin=...)"
    - "informational-first smoke: [0-9][0-9] glob-found, non-blocking in run_gates --smoke (Q7 promotion policy)"

key-files:
  created: [smoke/09_qprocess_smoke.py]
  modified: []

key-decisions:
  - "Responsiveness tick proved on dimer2 (not co2): co2 --ohess completes in 89 ms end-to-end, racing any pre-scheduled timer"
  - "EQ-runner-1 settled: errorOccurred is present under Qt 5.12.9; getattr proc.error fallback never exercised"
  - "FailedToStart enum is 0, so a bare proc.error()==FailedToStart check is vacuous before start — the smoke asserts the signal fired AND rejects UnknownError"

patterns-established:
  - "_wait_run(QtCore, proc, timeout_ms, begin): QEventLoop + finished/error -> loop.quit + safety singleShot, begin() called after connects (synchronous errorOccurred cannot be missed)"
  - "per-step PROBE lines (elapsed ms, exit codes) are the gate's evidence trail"

# Metrics
duration: 9min
completed: 2026-09-26
---

# Phase 6 Plan 3: QProcess-in-conda Gate Smoke Summary

**Headless QProcess gate smoke green against the real Windows conda PyMOL (Qt 5.12.9) and real xtb.exe — signal ordering, timer-during-run, kill->CrashExit cancel, and synchronous-error-signal semantics now live-pinned for the runner plans**

## Performance

- **Duration:** 9 min
- **Started:** 2026-09-26T13:23:35Z
- **Completed:** 2026-09-26T13:32:16Z
- **Tasks:** 2
- **Files modified:** 1 created, 0 modified

## Accomplishments

- `smoke/09_qprocess_smoke.py` committed and green: six steps (availability -> resolve -> version-run -> responsiveness-during-run -> kill/cancel -> error-path probe) all pass against the REAL environment — `SMOKE-OK QPROCESS` flushed as the sentinel verdict.
- Run command (from repo root): `timeout 120 cmd.exe /c "C:\src\run-conda-pymol.bat -cq smoke\09_qprocess_smoke.py"`.
- **Key PROBE lines from the green run (2026-09-26):**
  - `PROBE QT: 5.12.9, has QProcess=True, app=QCoreApplication`
  - `PROBE XTB_EXE: C:\xtb-6.7.1\bin\xtb.exe` (env unset, `detect_binary(None)` -> None on this machine, fallback hit — EQ-binary-1 path list exercised)
  - `PROBE ERR_SIGNAL_ATTR: errorOccurred` — **research open question 5 settled**: `errorOccurred` EXISTS on PyQt5 Qt 5.12.9; the `getattr(proc, 'errorOccurred', proc.error)` defensive pattern connects the modern signal
  - `PROBE VERSION elapsed_ms: 17` (221 ms cold on the first run)
  - `PROBE RUN elapsed_ms: 825 tick_at_ms: 298 tick_state: 2` — QTimer fired at 298 ms while state was Running (2) during a dimer2 `--ohess` (default threads; probe C was 2848 ms with OMP_NUM_THREADS=2)
  - `PROBE KILL elapsed_ms: 305 exitcode: 62097 exitstatus: 1 state_at_finished: 0` — exact probe-B reproduction: kill at ~300 ms -> finished(code=62097, CrashExit=1), state NotRunning immediately, no g98.out/vibspectrum in the run dir
  - `PROBE ERR_PATH attr: errorOccurred err_signal: 0 proc.error(): 0 state: 0` — nonexistent exe surfaces FailedToStart (0) via the error signal, process never left NotRunning, nothing crashed
- **New live facts for 06-05/06-08 to reuse:**
  1. `errorOccurred(FailedToStart)` is emitted **synchronously during `proc.start()`** — connecting the error signal after start misses it entirely (empirically pinned by this smoke's first run: loop only quit via the 10 s safety timeout with `err: None`). The runner MUST connect started/finished/error/readyRead before start.
  2. `QProcess.ProcessError.FailedToStart == 0` is also the `error()` default before start — a bare `proc.error()` equality check is vacuous; keep the signal record.
  3. co2 `--ohess` is 89 ms end-to-end through QProcess here — too fast to host any timer-during-run assertion.
- Gates: `python3.6 tests/run_gates.py` green (755 unittests, syntax walk, purity); `python3.6 tests/run_gates.py --smoke` green, quoting the informational line verbatim from gate output:
  - `note: informational smoke smoke/09_qprocess_smoke.py: PASS`

## Task Commits

1. **Task 1: Write smoke/09_qprocess_smoke.py on the probe mechanics** - `6d5955f` (test)
2. **Task 2: Record gate status + handoff note** - this SUMMARY (docs commit below)

## Files Created/Modified

- `smoke/09_qprocess_smoke.py` (360 lines, new) — probe-level QProcess mechanics smoke. Template obligations honored: named steps + check() runner, flush=True everywhere, _resolve_root() candidate validation, NO widgets, no `waitForFinished`, no `subprocess`, sentinel-only verdict. Output is smoke-only: zero `serpentrum/` or `tests/` modifications (verified by `git status`).

## Decisions Made

- Step-4 responsiveness fixture switched co2 -> dimer2 (see deviation 1): the truth "timer responsiveness DURING a run" requires a multi-second run; co2's 89 ms wall makes the assertion impossible to satisfy deterministically.
- Error-path assertion hardened to require the recorded signal (or FailedToStart observed) and explicitly reject `UnknownError` — because `FailedToStart == 0` equals the pre-start `error()` default.
- Binary resolution order kept exactly per plan: `SRP_XTB_PATH` env -> `xtbenv.detect_binary(None)` -> `C:\xtb-6.7.1\bin\xtb.exe`; failure raises naming all probes (never an opaque QProcess FailedToStart).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug / timing race] Responsiveness step could not pass on co2**

- **Found during:** Task 1 (first real smoke run — this is precisely what the gate is for)
- **Issue:** Plan prescribed co2.xyz + a pre-scheduled tick; the real co2 `--ohess` completed in **89 ms** end-to-end (`PROBE CO2 elapsed_ms: 89 tick_at_ms: None`), so ANY pre-scheduled timer (the plan's probe-calibrated 300 ms, my first 100 ms) lands after the run — the "tick fired while Running" assertion is unprovable on this fixture.
- **Fix:** Step 4 now uses the plan's own kill-step fixture dimer2 (26 atoms, ~0.8-2.8 s) with the probe-geometry 300 ms tick; success-contract assertions (finished 0/NormalExit) unchanged. co2 retains no step.
- **Files modified:** smoke/09_qprocess_smoke.py
- **Verification:** `PROBE RUN elapsed_ms: 825 tick_at_ms: 298 tick_state: 2` — tick at 298 ms, state Running.
- **Committed in:** 6d5955f

**2. [Rule 1 - Bug] Error-path step missed the synchronous `errorOccurred` emission**

- **Found during:** Task 1 (first real smoke run)
- **Issue:** `_wait_run` connected `finished`/`error` AFTER `proc.start()`. On the nonexistent-exe probe, Qt emitted `errorOccurred(FailedToStart)` **synchronously inside start()** — the post-start connect never saw it (`err: None`, loop ended via the 10 s safety timeout, and the step passed only vacuously: `FailedToStart == 0` equals the pre-start `error()` default).
- **Fix:** `_wait_run(QtCore, proc, timeout_ms, begin)` now connects all signals, then runs `begin()` (the actual `proc.start`), then `exec_()`; used by all four run steps. Assertions hardened (signal record or observed FailedToStart + explicit `UnknownError` rejection + NotRunning state).
- **Files modified:** smoke/09_qprocess_smoke.py
- **Verification:** `PROBE ERR_PATH attr: errorOccurred err_signal: 0 proc.error(): 0 state: 0`; full sentinel `SMOKE-OK QPROCESS`.
- **Committed in:** 6d5955f

---

**Total deviations:** 2 auto-fixed (2 timing/bug)
**Impact on plan:** Both fixes are correctness necessities discovered by the real-environment run the plan mandates; mechanisms pinned are exactly what 06-05/06-08 must obey. No scope creep.

## Issues Encountered

None beyond the two deviations above (each found and fixed within the same smoke iteration).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **Plans 06-05 and 06-08 are UNBLOCKED:** their `depends_on` on this plan is satisfied by the flushed `SMOKE-OK QPROCESS`. Their executors must see the sentinel before starting (run the smoke from repo root as quoted above).
- Handoff facts the runner must honor: connect-before-start (deviation 2 is binding — the runner's error path dies opaquely otherwise), kill->CrashExit + NotRunning-immediately (cancel path), no waitForFinished anywhere, dimer2 geometry for timer assertions.
- Smoke stays INFORMATIONAL per EQ-smoke-1 (research Q7: promote to required only after it proves stable); it gates plans via depends_on, not via REQUIRED_SMOKES.

---
*Phase: 06-xtb-pipeline*
*Completed: 2026-09-26*
