---
phase: 04-game-loop-input
plan: 02
subsystem: ui
tags: [python3.6, tdd, pure-module, hud, unittest]

requires:
  - phase: 03-molecules-in-the-viewer-setup-tab
    provides: GameEngine (Pure, cap / molecules_stacked attrs, deterministic reset), test conventions (sys.path self-insert, no stubs, assertEqual/AlmostEqual style), purity-gate machinery
provides:
  - serpentrum/hud_logic.py (PURE, stdlib-only): format_elapsed(seconds) -> 'M:SS' (floor fractional, clamp negatives); remaining_text(value) -> 'Remaining: N' | 'Remaining: -'
  - GameEngine.molecules_remaining: read-only property, cap - molecules_stacked, None-safe, reset-aware
  - tests/test_hud_logic.py: 13 unit tests (RED-first TDD)
affects: [04-05 (GameTab wiring consumes hud_logic.format_elapsed + engine.molecules_remaining), phase 5 HUD updates]

tech-stack:
  added: []
  patterns:
    - "HUD display math extracted from GUI widgets into a PURE stdlib module so it stays WSL-testable while the widgets stay human-verify-only (01-05 dead end honored)"

key-files:
  created:
    - serpentrum/hud_logic.py
    - tests/test_hud_logic.py
  modified:
    - serpentrum/game_engine.py

key-decisions:
  - "molecules_remaining lives on the engine (04-RESEARCH-hud.md Q4) — GUI does zero arithmetic; Phase 5 capture flips it dynamic with no HUD rewiring"
  - "Engine property adds NO timing/wall-clock (04-RESEARCH-gameloop.md Q5/S3) — elapsed is GUI-owned by design"

duration: ~10 min
completed: 2026-09-13
---

# Phase 4 Plan 02: HUD Pure Display Helpers Summary

**Extracted the Game tab's two display calculations (elapsed 'M:SS' formatting, molecules-remaining label) into a WSL-testable PURE module, plus a read-only `molecules_remaining` engine property — all TDD (RED → GREEN), 446 tests green including the pre-existing 433.**

## Performance

- **Duration:** ~10 min
- **Started:** 2026-09-13
- **Completed:** 2026-09-13
- **Tasks:** 1 feature (TDD RED → GREEN cycle)
- **Files modified:** 3 (2 created, 1 modified)

## Accomplishments

- `hud_logic.format_elapsed(seconds)` — closes GAME-07's elapsed-display math: 'M:SS' with fractional seconds floored (75.9 → '1:15') and negatives clamped to '0:00' (a tick landing before `start_time` can never render negative).
- `hud_logic.remaining_text(value)` — 'Remaining: N' / 'Remaining: -', None-safe for the `cap=None` case the engine permits.
- `GameEngine.molecules_remaining` — read-only property, `cap - molecules_stacked` / None when cap is None, survives `reset()` semantics; the pure engine owns the arithmetic so GameTab (plan 04-05) consumes it with zero GUI-side math.
- All 13 new tests RED-then-GREEN; full default gate run green (446 tests; purity gate auto-classifies `hud_logic.py` PURE with no violation line).

## Task Commits

TDD cycle, committed atomically:

1. **RED: failing tests for HUD pure display helpers** — `9687ed9` (test)
2. **GREEN: implement helpers + engine property** — `ad0023f` (feat)

**Plan metadata:** `docs(04-02): complete hud pure helpers plan` (see below)

## Files Created/Modified

- `serpentrum/hud_logic.py` — PURE stdlib-only module: `format_elapsed` + `remaining_text` with the pinned case semantics (floor, clamp, '%d:%02d', None-safe)
- `serpentrum/game_engine.py` — added read-only `molecules_remaining` property after the reset/counters section; nothing else touched
- `tests/test_hud_logic.py` — 13 tests across TestFormatElapsed (6), TestRemainingText (3), TestEngineMoleculesRemaining (4), mirroring test_engine_core.py conventions (sys.path self-insert, no stubs, python3.6 %-formatting)

## Decisions Made

- Property placement on `GameEngine` per 04-RESEARCH-hud.md Q4 (keeps `cap - molecules_stacked` arithmetic in the WSL-testable pure layer; HUD reads it directly).
- No timing/wall-clock added to the engine (04-RESEARCH-gameloop.md Q5/S3 binding) — the property is pure derived arithmetic.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. RED failed exactly as predicted (`ImportError: cannot import name 'hud_logic'`); GREEN passed first try; gates green (446 tests = prior 433 + 13 new).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 04-05 (GameTab) can now consume `hud_logic.format_elapsed(...)` in `_on_elapsed_tick`, `hud_logic.remaining_text(...)` + `engine.molecules_remaining` in `_update_remaining` — with zero GUI-side math and zero untestable arithmetic.
- Ready for 04-03-PLAN.md (wave 1 sibling: input spike) / 04-05 (Game tab HUD assembly).

---
*Phase: 04-game-loop-input*
*Completed: 2026-09-13*
