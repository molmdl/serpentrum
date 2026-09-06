---
phase: 01-plugin-skeleton-purity-harness
plan: 05
subsystem: testing
tags: [xtb, wsl, windows, pyqt5, qt-offscreen, path-conversion, gates, smoke, unittest]

# Dependency graph
requires:
  - phase: 01-plugin-skeleton-purity-harness
    provides: run_gates.py gate runner (01-03), PluginDialog 3-tab shell (01-02), headless smoke template + _resolve_root pattern (01-04)
provides:
  - "--xtb gate: Windows xtb invocable from WSL, asserted on 'xtb version' + 'normal termination'"
  - "tools/winpath.py: tested WSL->Windows path conversion (C:/ and C:\\ forms, strict /mnt/<drive> validation)"
  - "tests/test_winpath.py: 19 conversion-rule tests (happy paths + all ValueError cases)"
  - "smoke/02_dialog_smoke.py: offscreen QApplication experiment — EMPIRICALLY A DEAD END for widget construction"
affects: [phase-2 spectra parser (xtb success contract), phase-6 xtb pipeline, phase-3 setup tab (xtb path env), 01-06 gate docs]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Direct WSL exec of Windows exes: WSL-style exe path + /mnt/c-backed cwd + bare relative args, no cmd.exe"
    - "winpath conversion boundary: harness/dev-side only; plugin runtime never converts paths"
    - "Informational smokes: no-sentinel abort is reported as non-blocking FAIL, never a silent pass"

key-files:
  created:
    - tools/winpath.py
    - tests/test_winpath.py
    - smoke/02_dialog_smoke.py
  modified:
    - tests/run_gates.py

key-decisions:
  - "Offscreen dialog mechanism is a DEAD END: QApplication([]) constructs fine under QT_QPA_PLATFORM=offscreen, but PluginDialog construction kills the process silently (no sentinel, rc 0 through the .bat) — the smoke stays as the documented experiment; the authoritative dialog verdict remains the 01-06 human-verify checkpoint"
  - "--xtb asserts on output content ('xtb version' AND 'normal termination') even though direct-exec exit codes are meaningful — one contract for all Windows legs"
  - "winpath validates strictly and raises ValueError on non-/mnt paths — never silently mangles"

patterns-established:
  - "Windows exe probe pattern: subprocess.run([exe_path, args], cwd=ROOT) with WSL-style exe path, /mnt/c cwd, bare relative args"
  - "Gate-added conversion sanity: winpath.to_windows_path(ROOT).startswith('C:/') proves the repo lives on /mnt/c before Windows legs run"

# Metrics
duration: 6min
completed: 2026-09-06
---

# Phase 1 Plan 5: Offscreen dialog smoke + xtb probe gate + winpath helper Summary

**INFRA-01 completed: `--xtb` gate proves Windows xtb 6.7.1pre runs from WSL (version + normal termination asserted), tested WSL→Windows path rules in tools/winpath.py, and the offscreen-dialog open question is answered empirically — QApplication works, widget construction does not (documented dead end).**

## Performance

- **Duration:** 6 min
- **Started:** 2026-09-06T12:53:49Z
- **Completed:** 2026-09-06T13:00:10Z
- **Tasks:** 3
- **Files modified:** 4

## Accomplishments

- **Task 1** — `tools/winpath.py`: `to_windows_path` (C:/ form) + `to_windows_backslash` (C:\ form), strict `/mnt/<drive>` validation (ValueError on `/home/...`, relative paths, `C:\...`, bare `/mnt`, 2-letter drives, non-str); docstring pins the boundary: harness/dev-side ONLY, plugin runtime never converts paths. `tests/test_winpath.py`: 19 tests covering happy paths, every error case, and input immutability — all green under python3.6.
- **Task 2** — `tests/run_gates.py` gained flag `--xtb` + gate 5: resolves `xtb-6.7.1/bin/xtb.exe` (clear failure if missing), exercises `winpath.to_windows_path(ROOT)` sanity (repo must map to `C:/...`), then direct WSL exec `subprocess.run([exe, '--version'], cwd=ROOT, ...)` (research-verified pattern — NO cmd.exe), verdict = `'xtb version'` AND `'normal termination'` in output, with the direct-exec rc captured. Negative paths verified to fail loudly (missing exe; garbage output → last 20 lines dumped).
- **Task 3** — `smoke/02_dialog_smoke.py`: the experimental offscreen spike (QT_QPA_PLATFORM before any Qt import; `_resolve_root()` from 01-04; plugin imported under loader name; QApplication-first; asserts 3 tabs Setup/Game/Spectra + title 'serpentrum' + modeless). **Empirical verdict: dead end.** `QApplication([])` constructs OK under offscreen (new verified fact), but `PluginDialog()` construction kills the process silently — no SMOKE-FAIL, no sentinel, rc 0 through the .bat. Runner semantics confirmed: 01 (required) green; 02 reported `FAIL (non-blocking)` in notes, gate stays green — the failure is never a silent pass.

## Task Commits

Each task was committed atomically:

1. **Task 1: tools/winpath.py + tests/test_winpath.py** — `aaee371` (feat)
2. **Task 2: Wire --xtb gate into tests/run_gates.py** — `2e7a988` (feat)
3. **Task 3: smoke/02_dialog_smoke.py (informational)** — `eb64ad9` (feat)

**Plan metadata:** (this commit)

## Files Created/Modified

- `tools/winpath.py` — pure WSL→Windows path conversion, strict validation, boundary documented
- `tests/test_winpath.py` — 19 conversion-rule tests, zero stubs
- `tests/run_gates.py` — +96 lines: `--xtb` flag, gate 5 (exe resolution, winpath sanity, direct-exec probe, content verdict), summary integration
- `smoke/02_dialog_smoke.py` — offscreen dialog experiment with SMOKE-ATTEMPT tracing (shows exactly where an abort lands)

## Decisions Made

- **Offscreen = dead end (recorded, not chased):** QApplication-first under `QT_QPA_PLATFORM=offscreen` is NOT sufficient for headless widget construction in PyMOL 2.5.0's Qt 5.12.9 build — dialog construction aborts the process with no message. Per plan, the smoke remains as the documented experiment; later phases must NOT promote it to a required gate; dialog assertions stay with the 01-06 human-verify checkpoint.
- **Content-based verdict for --xtb:** assert `'xtb version'` + `'normal termination'` regardless of the (meaningful, captured) child exit code — consistent with the harness-wide "never trust exit codes on Windows legs" rule.
- **Strict winpath validation:** non-`/mnt` inputs raise ValueError; the helper never guesses or partially converts (e.g. `C:\already` is rejected, not round-tripped).

## Deviations from Plan

None - plan executed exactly as written. (The offscreen dead-end is one of the two anticipated outcome paths in the plan's Task 3, not a deviation.)

## Issues Encountered

- During the negative-path probe of gate 5 (pre-commit sanity), a test harness typo (tuple instead of string for `XTB_EXE_REL`) raised a TypeError in `os.path.join` — probe-only mistake, fixed in the probe; no product code affected.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- INFRA-01 is fully wired as runnable gates: default (syntax/safety + purity + unittest), `--smoke` (required 01 green; 02 informational), `--xtb` (green: `xtb version 6.7.1pre (5071a88)` + normal termination, rc 0).
- Ready for 01-06 (final plan of Phase 1): AGENTS.md gate docs + full gate run + human-verify checkpoint (install, single instance, modeless).
- For later phases: the offscreen route is closed — headless dialog assertions are impossible in this build; do not spend time on Qt-offscreen spikes again.
- Phase 2 spectra work can rely on the verified xtb probe pattern (`subprocess.run([exe, ...], cwd=/mnt/c-dir, PIPE)` with content-based success contract).

---
*Phase: 01-plugin-skeleton-purity-harness*
*Completed: 2026-09-06*
