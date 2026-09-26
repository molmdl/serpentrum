---
phase: 06-xtb-pipeline
plan: 02
subsystem: infra
tags: [xtb, qprocess, state-machine, env-knobs, xyz, unit-tested, pure-module]

# Dependency graph
requires:
  - phase: 02-pure-core-game-chemistry-logic
    provides: xtbenv (evaluate_run/build_argv/new_run_dir contract), xyzio fixture-proven round-trip, the DI zero-stub test precedent
  - phase: 05-stacking
    provides: head/session atom truth (05-RESEARCH:151 — engine atoms, never PyMOL re-reads)
provides:
  - serpentrum/xtb_run.py — PURE runner decision half: can_start/TERMINAL_STATES no-double-run guard, resolve_status cancel-wins mapping, build_env OMP knob merge, build_run_input snake-xyz assembler, SPECTRA_RUN_KEYS/new_spectra_run record shape, DEFAULT_RUN_KNOBS = {}
  - tests/test_xtb_run.py — 17 tests pinning the state machine, cancel mapping, env merge, xyz assembly/round-trip, frozen record shape
affects: [06-05 runner controller (consumes every rule here), 06-06 handoff wiring (calls build_run_input), 06-07 calibration (feeds 06-11 DEFAULT_RUN_KNOBS edit), Phase 7 spectra consumer (parses SPECTRA_RUN_KEYS paths)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Runner decision rules as pure functions consumed by a thin Qt shell (02-02 xtbenv DI precedent)"
    - "Status strings double as state-machine states ('idle'|None/'running'/'ok'/'failed'/'cancelled'); record shape frozen as DATA before GUI code exists"

key-files:
  created:
    - serpentrum/xtb_run.py
    - tests/test_xtb_run.py
  modified: []

key-decisions:
  - "EQ-omp-1 shipped: DEFAULT_RUN_KNOBS = {} (uncapped until 06-CALIBRATION.md; plan 06-11 owns the one-literal default edit)"
  - "EQ-xyz-1 shipped: run input assembled at completion from engine/session atoms; build_run_input raises ValueError on head_atoms None; viewer never a coordinate source"
  - "EQ-artifact-1 shipped: SPECTRA_RUN_KEYS = ('snake_id','status','problems','input_path','g98_path','vibspectrum_path','xtbopt_path','log_path') — xtbopt_path preserved for Phase 7's optimized-frame overlay"
  - "Cancel WINS: resolve_status(True, anything) == 'cancelled' — a killed run's lingering 'normal termination' stderr must never read as success"

patterns-established:
  - "KNOWN_ENV_KNOBS allowlist: only help-verified keys (xtb --help:229-231) pass; unknown keys raise ValueError — the no-invented-knobs rule enforced as code"

# Metrics
duration: 4 min
completed: 2026-09-26
---

# Phase 6 Plan 02: xtb_run (runner pure half) Summary

**Frozen the xtb runner's every decision rule as WSL-testable pure functions — no-double-run state machine, cancel-wins status mapping, help-verified OMP env-knob merge, head-first snake-xyz assembler, and the Phase-7 `spectra_run` record shape as data — so the 06-05 Qt controller ships as a thin shell adding zero rules of its own.**

## Performance

- **Duration:** 4 min
- **Started:** 2026-09-26T13:21:32Z
- **Completed:** 2026-09-26T13:24:41Z
- **Tasks:** 2/2 (TDD: RED -> GREEN)
- **Files modified:** 2 (both created)

## Accomplishments

- Run state machine pinned exhaustively: `can_start` admits only None/'idle'/terminal states (never 'running', never unknown), `TERMINAL_STATES` is the frozenset {ok, failed, cancelled} — the bioCHEMeleon terminal-branch discipline.
- Cancel semantics frozen: `resolve_status(True, ...)` == 'cancelled' regardless of contract verdict (killed runs may carry a lingering 'normal termination' in partially captured stderr — they must never read as success); otherwise 'ok'/'failed' from `xtbenv.evaluate_run`'s verdict.
- Env-knob contract enforced: `build_env` merges ONLY the three help-verified OMP knobs (xtb --help:229-231), stringifies values, rejects empties/unknowns with ValueError, never mutates its input; `DEFAULT_RUN_KNOBS = {}` ships uncapped per EQ-omp-1 (plan 06-11 owns the post-calibration default edit).
- Handoff seam shipped: `build_run_input` assembles head-first + segments-in-engine-order xyz text via `xyzio.write_xyz` with a newline-safe 'serpentrum snake <id>' comment; round-trip proven against the real committed co2.xyz fixture; None head raises ValueError (caller owns the refuse path).
- Phase-7 handoff frozen before any GUI code exists: `SPECTRA_RUN_KEYS` 8-key tuple + `new_spectra_run` exact initial dict (status 'running', problems [], all paths None — including xtbopt_path for the optimized-frame overlay decision).

## Task Commits

Each task was committed atomically (TDD pattern):

1. **Task 1: RED — failing tests for xtb_run** — `f7c1d62` (test)
2. **Task 2: GREEN — implement serpentrum/xtb_run.py** — `4996dd9` (feat)

**Plan metadata:** `docs(06-02)` commit follows this summary.

## Files Created/Modified

- `serpentrum/xtb_run.py` — PURE module (179 lines; stdlib + `from . import xyzio` only): state constants, TERMINAL_STATES frozenset, can_start, resolve_status, KNOWN_ENV_KNOBS, build_env, DEFAULT_RUN_KNOBS, build_run_input, SPECTRA_RUN_KEYS, new_spectra_run.
- `tests/test_xtb_run.py` — 17 unittest tests (189 lines; house sys.path self-insert header, no __init__.py): state-machine matrix, terminal set, cancel-wins + contract mappings, env merge copy/mutation/stringify/unknown/empty pins, DEFAULT_RUN_KNOBS pin, xyz assembly order/comment/none-head/multi-segment + co2.xyz fixture round-trip, SPECTRA_RUN_KEYS + new_spectra_run exact-shape pins.

## Decisions Made

- Followed the plan's resolved decisions verbatim (EQ-omp-1, EQ-xyz-1, EQ-artifact-1, status-string state duality) — no new decisions were needed during execution.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. RED confirmed ImportError on missing module (one discovery error, as designed for module-absent RED); GREEN passed all 17 tests on first run with full gates green.

## Verification

- `python3.6 -m unittest discover -s tests -p "test_xtb_run.py" -v` -> **17 tests OK** (was ImportError at RED).
- `python3.6 tests/run_gates.py` -> **all gates green**: gate 1 syntax + plugin-path safety PASS, gate 2 purity (AST) PASS, gate 3 unittest PASS; suite at **772 tests OK** (baseline 755 + 17 new; no existing module touched).
- Plan pin: `python3.6 -c "...xtb_run.can_start('running'), xtb_run.resolve_status(True, True), xtb_run.DEFAULT_RUN_KNOBS"` prints exactly `False cancelled {}`.
- must_haves: all 5 truths pinned by named tests; both artifacts exceed min_lines (179 / 189 LOCs vs 110); key_links live (`write_xyz` called with 'serpentrum snake ' comment; `SPECTRA_RUN_KEYS` exported for 06-05/Phase-7 consumers).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- 06-05 (xtb_runner Qt controller) can now stay a thin shell: every guard/mapping/merge/assembly/record rule is a tested pure function here or in xtbenv.
- 06-06 wires `build_run_input` into the completion handoff (`last_run['snake_xyz']`); 06-07 calibration produces the data 06-11 needs to potentially change the ONE `DEFAULT_RUN_KNOBS` literal.
- No blockers.

---
*Phase: 06-xtb-pipeline*
*Completed: 2026-09-26*
