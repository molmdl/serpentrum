---
phase: 06-xtb-pipeline
plan: 05
subsystem: infra
tags: [qprocess, pyqt5, qt5.12.9, xtb, gui-purity, spectra-run-record, cancel, async-runner]

# Dependency graph
requires:
  - phase: 06-xtb-pipeline plan 02
    provides: serpentrum/xtb_run.py (PURE decision half: state machine, resolve_status, build_env, SPECTRA_RUN_KEYS, new_spectra_run)
  - phase: 06-xtb-pipeline plan 03
    provides: smoke 09 live pins (connect-before-start binding, errorOccurred exists on Qt 5.12.9, kill->CrashExit cancel geometry)
  - phase: 02-pure-core-game-chemistry-logic
    provides: serpentrum/xtbenv.py (build_argv, new_run_dir, evaluate_run 3-leg contract, XTB_OHESS)
  - phase: 04-game-loop-input plan 05
    provides: GUI_MODULES allowlist edit precedent (gui_game.py)
provides:
  - serpentrum/xtb_runner.py — XtbRunController: single-owner async cancellable QProcess runner shell (thin GUI wiring over xtb_run + xtbenv)
  - check_purity GUI allowlist entry for serpentrum/xtb_runner.py (inert-first)
  - _serpentrum.spectra_run anchor attribute (frozen xtb_run.SPECTRA_RUN_KEYS record) + last_run 'snake_xyz' docstring extension
affects: [06-xtb-pipeline plans 06-08 (smoke 11), 06-09 (runner anchoring), Phase 7 spectra presentation]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "thin-GUI-shell: a GUI module wires Qt only; EVERY rule (guard, verdict, env, record shape) delegates to PURE xtb_run/xtbenv"
    - "connect-before-start: ALL QProcess signals wired before proc.start() (errorOccurred fires synchronously inside start)"
    - "every-terminal-branch discipline: single _on_finished resolves verdict -> copy-out -> anchor record -> spray-dir rmtree -> flag reset -> signal"
    - "keep-until-replaced artifacts: stable <temp>/srp_spectra/<snake_id> dir; next start() prefix-guarded-deletes the prior one"

key-files:
  created: [serpentrum/xtb_runner.py]
  modified: [tools/check_purity.py, serpentrum/__init__.py]

key-decisions:
  - "Controller instance is placed on the anchor by the CALLER (plan 06-09); this module touches zero module globals"
  - "Preflight failures (empty input, missing exe, argv ValueError) route through the same frozen-record path as a verdict failure — state never sticks at 'running'"
  - "errorOccurred fallback kept defensive via getattr(proc, 'errorOccurred', proc.error) even though smoke 09 proved errorOccurred exists"

patterns-established:
  - "inert-first allowlist: GUI_MODULES entry lands and gates/goes green BEFORE the module file exists (check_tree walks existing files only)"

# Metrics
duration: 6min
completed: 2026-09-26
---

# Phase 6 Plan 5: Runner Shell Summary

**XtbRunController: a 347-line thin Qt shell that turns xtb_run/xtbenv's pure decisions into an async, cancellable QProcess lifecycle — guarded start, verbatim-stderr 3-leg verdict, stable-dir copy-out with spray-dir deletion on every terminal branch, and a frozen `spectra_run` anchor record — plus its deliberate GUI allowlist entry (inert-first) and purity classification as GUI**

## Performance

- **Duration:** 6 min
- **Started:** 2026-09-26T14:21:23Z
- **Completed:** 2026-09-26T14:27:35Z
- **Tasks:** 2
- **Files modified:** 1 created, 2 modified

## Accomplishments

- `serpentrum/xtb_runner.py` committed: `XtbRunController(QtCore.QObject)` with signals `started`/`log_line(str)`/`run_finished(str, list)`; `start()` is a guarded no-op (`xtb_run.can_start` — no-double-runs) returning False + a log line; launches with cwd = a fresh `xtbenv.new_run_dir` spray dir, bare-relative `snake.xyz` argv via `xtbenv.build_argv`, env = system + `xtb_run.build_env` knob merge only; NEVER blocks on the child (signals only).
- ONE terminal branch (`_on_finished`): `xtbenv.evaluate_run` verdict over the spray-dir listing -> `xtb_run.resolve_status` (cancel flag wins) -> copy `g98.out`/`vibspectrum`/`xtbopt.xyz` + write `snake.xyz`/`xtb.log` into stable `<temp>/srp_spectra/<snake_id>` -> frozen `xtb_run.new_spectra_run` record onto `anchor.spectra_run` -> spray dir `shutil.rmtree` ALWAYS -> full flag/state reset -> `run_finished(status, problems)`. The `_on_error` FailedToStart path runs the same discipline, guarded so it no-ops when `finished` already owns the branch.
- Keep-until-replaced artifact policy (EQ-artifact-1): the NEXT `start()` prefix-guarded-deletes the prior stable dir (never rmtree's an arbitrary path — only under `<temp>/srp_spectra`).
- `tools/check_purity.py` GUI_MODULES gained the deliberate `serpentrum/xtb_runner.py` entry (comment cites 06-RESEARCH-runner Q2 + the 04-05 gui_game precedent) — landed inert-green BEFORE the module exists; `serpentrum/__init__.py` `_SerpentrumState` declares `spectra_run` with the frozen-key docstring and extends the `last_run` docstring with the `snake_xyz` key (plan 06-06 forward reference).

## Task Commits

Each task was committed atomically on branch `exec/06-05` (worktree protocol):

1. **Task 1: GUI allowlist entry (inert-first) + anchor attribute** - `8b6a40b` (feat)
2. **Task 2: XtbRunController implementation** - `22f4f6d` (feat)

## Files Created/Modified

- `serpentrum/xtb_runner.py` (347 lines, new) — the async QProcess runner shell; the ONLY pymol-family import is `pymol.Qt` (never pymol.cmd — the viewer is not its concern); py3.6 %-formatting; bounded 500-line log tail feeding the record's `xtb.log`; stderr accumulated VERBATIM (CRLF intact) for `evaluate_run`.
- `tools/check_purity.py` — GUI_MODULES entry + precedent-citing comment.
- `serpentrum/__init__.py` — `spectra_run = None` anchor attribute (frozen `xtb_run.SPECTRA_RUN_KEYS` docstring; written ONLY by the runner terminal branch; consumed by Phase 7) + `last_run` docstring 'snake_xyz' extension.

## Decisions Made

- Followed the plan's resolved decisions verbatim (EQ-app-1 single-app helper, EQ-runner-1 getattr error-signal fallback, EQ-artifact-1 copy-out-then-delete with keep-until-replaced stable dir, connect-before-start per the 06-03 live pin).
- `_ensure_app()` implemented as the module-level helper the plan prescribes; the controller never creates a second app in the real GUI.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Guard ordering: exe-falsy check placed before build_argv**

- **Found during:** Task 2 (writing start())
- **Issue:** The plan lists the `ValueError`-from-`build_argv` guard before the exe-falsy guard; `build_argv(None, ...)` does `'"' in arg` on None -> TypeError, escaping the guard entirely
- **Fix:** exe-falsy guard (`['xtb not found - set the xtb path on the Setup tab']`) now runs before `build_argv`; the ValueError guard catches the remaining quote-injection cases
- **Files modified:** serpentrum/xtb_runner.py
- **Verification:** AST purity green; code review of the guard chain
- **Committed in:** 22f4f6d

**2. [Rule 2 - Missing Critical] Post-start no-launch detection**

- **Found during:** Task 2 (start())
- **Issue:** smoke 09's live pin says `errorOccurred(FailedToStart)` fires SYNCHRONOUSLY inside `proc.start()`; the plan's start() ends "emit started(); return True" unconditionally — after a synchronous FailedToStart, start() would emit `started` and return True for a run already recorded FAILED
- **Fix:** after `proc.start()`, re-check `self._status != xtb_run.RUNNING` -> return False without emitting `started` (the error slot already ran the terminal discipline)
- **Files modified:** serpentrum/xtb_runner.py
- **Verification:** gates green; logic matches smoke 09's observed signal ordering
- **Committed in:** 22f4f6d

**3. [Rule 2 - Missing Critical] Null-guards in the copy-out branch**

- **Found during:** Task 2 (_on_finished)
- **Issue:** plan's literal `os.path.join(tempfile.gettempdir(), 'srp_spectra', self._snake_id)` TypeErrors if snake_id is None; writing `self._input_text` None likewise
- **Fix:** stable dir uses `self._snake_id or 'unknown'`; input write uses `self._input_text or ''`
- **Files modified:** serpentrum/xtb_runner.py
- **Verification:** gates green
- **Committed in:** 22f4f6d

**4. [Rule 3 - Blocking / grep-verification] Docstrings named banned APIs literally**

- **Found during:** Task 2 (running the plan's grep verifications)
- **Issue:** plan verification requires `grep -c "waitForFinished\|subprocess"` and `grep -c ".exec_("` on the runner to be 0; the first draft's docstrings referenced the banned API names in prose ("NO waitForFinished, NO subprocess"), which is AST-legal (docstrings are pure-text) but fails the plain-grep bar
- **Fix:** docstrings reworded to refer to the rule without the literal names ("no blocking wait calls on the child", "never a blocking exec-call (modeless rule)")
- **Files modified:** serpentrum/xtb_runner.py
- **Verification:** all three plan greps now count 0; gates green
- **Committed in:** 22f4f6d

---

**Total deviations:** 4 auto-fixed (1 bug, 2 missing-critical, 1 blocking verification)
**Impact on plan:** All fixes preserve the plan's exact semantics; the must-haves (thin shell, single terminal branch, anchor record, GUI purity) are unchanged. No scope creep.

## Issues Encountered

None beyond the deviations above.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **Plan 06-08 (smoke 11) unblocked for the runner half:** it owns the live behavior proof (success contract, cancel, no-double-run) against this controller, driving it through the QEventLoop mechanics smoke 09 pinned.
- **Plan 06-09 (runner anchoring):** the controller instance lands on `pmg_tk.startup._serpentrum` (the caller creates-or-reuses `anchor.spectra_runner`; plan 06-05's term for the anchor attribute is `spectra_run` for the record — the runner attribute name is 06-09's call).
- **Phase 7 consumers** read `spectra_run` paths verbatim (parse `g98.out` first, `vibspectrum` fallback) and must never reshape the record.
- Full suite stayed green UNMODIFIED (785 unittests); no `tests/` or `smoke/` edits — live proof is deliberately delegated to smoke 11.

---
*Phase: 06-xtb-pipeline*
*Completed: 2026-09-26*
