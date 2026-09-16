---
phase: 05-stacking-game-rules
plan: 04
subsystem: game-logic
tags: [game_engine, reject_pickup, win-desync, tdd, unittest, pure-core]

# Dependency graph
requires:
  - phase: 02-pure-core
    provides: GameEngine rules/seams (capture, counters, win-at-cap, reject_pickup canonical tuple) and the test-pinned referee event order moved->boundary->body->stacked->budget->won
provides:
  - "reject_pickup un-finishes a WON run when the rollback drops molecules_stacked below cap (gap G2 closed, additive)"
  - "Pinned contract: crashed runs are NEVER un-finished by reject_pickup"
  - "tests/test_engine_win_desync.py — 7 new pins (un-finish, cap variants, crash guard, no-op borders, resume play)"
affects: [05-09 (resume_note HUD line), 05-12 (pure integration un-finish scenario), 05-13 (GameTab 'won' guard), gui_game clash-reject seam]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Won-rollback un-finish keyed on post-rollback counter < cap (counter-keyed, not pickup-keyed)"

key-files:
  created:
    - tests/test_engine_win_desync.py
  modified:
    - serpentrum/game_engine.py

key-decisions:
  - "Rejecting the cap-reaching capture un-finishes ONLY when molecules_stacked < cap after rollback; only 'won' results ever un-finish"
  - "cap< rollback guard kept despite being unreachable via public API (single rollback always satisfies it) — defensive semantics for hand-forced states"

patterns-established:
  - "End-of-run reversal is engine-side and additive: step()'s pinned event order is never weakened to fix controller-order desyncs — the rollback method repairs finished/result instead"

# Metrics
duration: 8 min
completed: 2026-09-15
---

# Phase 5 Plan 04: Engine Additive Fix — Reject-After-Won Un-Finish Summary

**Additive `reject_pickup` un-finish branch closing the win-vs-clash desync (gap G2): rejecting a cap-reaching capture now resumes play by clearing finished/result when the rollback drops below cap; crashed runs stay terminal; Phase-2 referee event order byte-identical.**

## Performance

- **Duration:** 8 min
- **Started:** 2026-09-15T18:30:47Z
- **Completed:** 2026-09-15T18:38:35Z
- **Tasks:** 2
- **Files modified:** 2 (1 created, 1 modified)

## Accomplishments

- Gap G2 closed with the narrowest additive change (6-line guarded branch in `reject_pickup` + docstring paragraph); `step()`, `start_sweep`, `_advance_sweep`, `attach_segment`, and all constants untouched (`grep -c "events.append(('won',))"` still exactly 1)
- 7 new pins in `tests/test_engine_win_desync.py`: same-tick stacked+won reproduction, cap=1/cap=2 rollback variants (cap-reaching and earlier captures both un-finish — the un-finish keys on the counter), crash-stays-finished (live and captured pickup variants), unfinished-run no-op border, and resume-play (re-capture/refires won on the next tick)
- Full gates green: 458 tests (451 baseline + 7 new), zero regressions in the pinned Phase-2 suites (test_engine_core/rules/turns unmodified)

## Task Commits

Each task was committed atomically (TDD RED → GREEN):

1. **Task 1 RED: won-rollback un-finish tests** - `ea1c69d` (test)
2. **Task 2 GREEN: additive reject_pickup un-finish branch** - `ea61607` (feat)

No REFACTOR commit needed — the additive branch is already minimal and matches the plan-specified code verbatim.

## Files Created/Modified

- `tests/test_engine_win_desync.py` — G2 desync pins: won-rollback un-finish posts the run back to live (finished=False, result=None, pickup re-armed, counters rolled back); crashed runs never un-finish; step() resumes after un-finish
- `serpentrum/game_engine.py` — `reject_pickup` gained the guarded un-finish branch (finished and result=='won' and molecules_stacked < cap → clear both) plus a docstring paragraph documenting the semantics

## Decisions Made

- **Un-finish keyed on the post-rollback counter, not on which pickup reached the cap.** Rejecting an earlier capture in a won cap=2 run also un-finishes (2→1 < 2); the guard reads `molecules_stacked < cap`, so semantics follow the win condition exactly.
- **The `< cap` recheck stays even though a single public-API rollback always satisfies it** ('won' fires at the exact tick the counter reaches cap; one rollback always yields cap−1 or less). It is defensive semantics: a hand-forced over-cap or cap=0 state whose post-rollback counter still satisfies the win condition must NOT un-finish. Documented in the test module and the reject_pickup docstring.
- **Crashed runs never un-finish**, but counter rollback still happens on a post-crash reject (existing pinned contract) — only the finished/result repair is suppressed.

## Deviations from Plan

None - plan executed exactly as written. (The RED commit intentionally carried 4 failing new tests; gates 1/2 were green and gate 3 failed only on the 4 new pins, exactly as the plan's `<verify>` specified — standard TDD RED state, not a gate regression.)

## Issues Encountered

None. The RED phase failed on exactly the 4 expected pins (tests 1, 2a, 2b, 5); the GREEN implementation passed all 7 on the first run and the full suite stayed green.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- The G2 seam is ready for consumers: `gui_game`'s clash-reject path can call `reject_pickup(rec['id'], 'clash')` after a cap-reaching capture and the engine resumes; `_on_tick`'s finished-funnel will correctly skip `_end_run` (key_links contract). Plan 05-13's 'won' guard (`if engine.finished:`) and plan 05-09's `resume_note` HUD line now have their engine-side contract pinned.
- Plan 05-12 (pure integration chain) can pin the win-refusal un-finish scenario directly against this behavior.
- No blockers.

---
*Phase: 05-stacking-game-rules*
*Completed: 2026-09-15*
