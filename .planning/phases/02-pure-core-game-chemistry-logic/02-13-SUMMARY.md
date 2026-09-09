---
phase: 02-pure-core-game-chemistry-logic
plan: 13
subsystem: game-engine
tags: [game-engine, rigid-pivot, sweep, rotation, collision-refusal, atom-level, pure-python, py36, game-10]

# Dependency graph
requires:
  - phase: 02-06
    provides: movement core (head/heading/segments state, request_direction 180-rejection vs current heading + max-1 buffer, step() forward movement, pause/resume/reset, DIRS, SPEED_A_PER_S)
  - phase: 02-10
    provides: collision/rules layer (_point_segment_distance_sq, BOUNDARY_MARGIN_A, BODY_COLLISION_RADIUS_A, SEGMENT_SKIP_RECENT, PICKUP_RADIUS_A, SWEEP_PICKUP_CLEARANCE_A, pickups with 'atoms', crash-clears-pending, finished/result)
provides:
  - "Rigid-pivot turn-sweep machinery: _rotate_xy helper, TURN_DEGREES=90.0 / TURN_TICKS=6 constants"
  - "start_sweep(direction) with the 7-sample 3-leg (boundary/body/pickup) swept-region pre-check — refuses with ('turn_refused', reason) and zero state mutation"
  - "_sweep_check_safe (boundary centroids vs MARGIN-adjusted box; body head-vs-rotated-polyline-edges reusing 02-10's exact model; pickup rotated-chain-atoms vs live-pickup-atoms < 2.5 A, head excluded)"
  - "_advance_sweep + step() sweep branch: whole chain rotates rigidly about the head over 6 ticks (15 deg/tick), ABSOLUTELY from the start pose each tick (drift-free to 1e-9), z/sym preserved; forward motion paused"
  - "Pending applied exactly once at the START of the step after sweep completion (refusals fall through to forward motion, never retried)"
  - "request_direction sweep-level 180 enforcement (vs sweep target, newest-wins) — static first-kept rule unchanged when not sweeping"
  - "reset() epoch safety (clears sweeping + pending)"
affects: [02-14-pure-integration (turn input -> request_direction -> step() sweeps), Phase-4/5 controller (key binding -> request_direction; rendering maps sweep state)]

# Tech tracking
tech-stack:
  added: []  # stdlib math only — no new dependencies (pure module)
  patterns:
    - "Rigid-body rotation about a pivot (the head): whole chain (centroids + atom x/y) rotates; z and symbol preserved so pairwise stacking geometry stays frozen"
    - "7-sample swept-region pre-check (K = TURN_TICKS + 1): build rotated poses in LOCAL variables, never write to engine state; refuse on first hit with zero mutation"
    - "Absolute-per-tick rotation: capture start_centroids/start_atoms at sweep open, re-derive each tick from the start pose (no cross-tick float drift -> final pose exact to cos/sin quality, 1e-9)"
    - "Two deliberately-unified-NOT request-buffering policies: static (first-kept, buffer-full reject) vs sweep (newest-wins, max 1)"
    - "Sweep-level 180 enforcement: judge requests against the sweep TARGET (the heading that will be in effect), not the current heading"

key-files:
  created:
    - tests/test_engine_turns.py  # 610 lines: rotation-helper sanity, 3-leg refusals, head exclusion, sweep progression, sweep-level 180, chaining, epoch safety
  modified:
    - serpentrum/game_engine.py   # +_rotate_xy, TURN constants, start_sweep, _sweep_check_safe, _advance_sweep, step() sweep/pending branches, request_direction sweep branch, sweeping state

key-decisions:
  - "start_sweep returns (opened, events) — a 2-tuple — so the ('turn_refused', reason) event is observable in direct calls (the plan said both 'return True/False' and 'emit (turn_refused, reason)'; the tuple realizes both faithfully without a side-channel)"
  - "Boundary leg uses STRICT 'strictly beyond' (a centroid exactly at the margin wall is INSIDE) — distinct from 02-10's inclusive forward-velocity crash at the head; matches the plan's 'strictly beyond' wording and shown arithmetic"
  - "Sweep rotates ABSOLUTELY from the start pose each tick (start_centroids/start_atoms captured at open) — drift-free at 1e-9, required by the plan's tight assertAlmostEqual delta"
  - "Pending applied exactly once at the NEXT step's start (revision-pinned timing) — NOT at sweep completion; the research sec-7 sketch said 'apply pending at completion' but the plan explicitly overrode it"
  - "Two request-buffering policies deliberately NOT unified (static first-kept vs sweep newest-wins) per the plan's 'intentional in-sweep override' note"
  - "Pickup leg is atom-level at SWEEP_PICKUP_CLEARANCE_A=2.5 A (matching 02-04 check_clash); PICKUP_RADIUS_A=3.0 is 02-10's capture radius and is deliberately NOT the sweep clearance; head excluded (pivot, not a chain atom)"

patterns-established:
  - "Swept-region refusal pre-check: sample K=TURN_TICKS+1 poses, 3 legs, zero-mutation refusal with reason-tagged events"
  - "Absolute-per-tick rotation for drift-free exactness in multi-tick animations"

# Metrics
duration: 22 min
completed: 2026-09-09
---

# Phase 2 Plan 13: Rigid-Pivot Turn Sweeps Summary

**GAME-10 rigid chain pivot: whole-chain rotation about the head over 6 ticks with a 7-sample 3-leg (boundary/body/pickup) refusal pre-check, sweep-level 180 enforcement, and exactly-once pending timing — pure stdlib math, stacking geometry frozen**

## Performance

- **Duration:** 22 min
- **Started:** 2026-09-09T02:43:42Z
- **Completed:** 2026-09-09T03:06:16Z
- **Tasks:** 2
- **Files modified:** 2 (serpentrum/game_engine.py, tests/test_engine_turns.py)

## Accomplishments

- **Rigid chain pivot (GAME-10):** a turn rotates the ENTIRE chain (centroids + atom x/y) as a rigid body about the head over TURN_TICKS=6 ticks (15 deg/tick). Rotation is ABSOLUTE from the start pose each tick (start_centroids/start_atoms captured at sweep open) so floating-point error does not accumulate — the final pose is exact to 1e-9. z and symbol are preserved (rotation is about the vertical axis through the head; the 2D game plane is xy), so pairwise stacking geometry stays frozen ("stacking geometry immutable at all times").
- **3-leg swept-region refusal pre-check:** before any mutation, `start_sweep` samples K=TURN_TICKS+1=7 poses of the whole chain rotated about the head and refuses on the first hit — boundary (rotated centroids strictly beyond the BOUNDARY_MARGIN_A-adjusted box), body (head vs rotated polyline edges, 02-10's exact model: same edge set, `_point_segment_distance_sq`, BODY_COLLISION_RADIUS_A, STRICT <), pickup (rotated chain ATOMS vs live pickup ATOMS < SWEEP_PICKUP_CLEARANCE_A=2.5 A, atom-level matching 02-04's clash threshold; head excluded as the invariant pivot). Any hit emits `('turn_refused', reason)` with ZERO state mutation (heading, segments, sweeping, pending all unchanged).
- **Sweep-level 180 enforcement + exactly-once pending timing:** while sweeping, `request_direction` judges against the sweep's TARGET heading (180/same ignored; perpendicular buffered, newest-wins max 1 — an intentional in-sweep override of the static first-kept rule). Sweep ticks pause forward motion (no `('moved',)` events) and emit `('turning', tick/total)`; pending is applied exactly once at the START of the step after completion (never inside the completion tick); a refused chained request is consumed and that same tick falls through to forward motion (never retried). `reset()` wipes all turn state (epoch safety).
- **Prior suites untouched and green:** test_engine_core.py (02-06, 44→ keep) and test_engine_rules.py (02-10) are unmodified; the forward-compatibility convention (never step while pending) held — both pass alongside the 31 new turns tests (75 engine trio total, 333 full suite).

## Task Commits

Each task was committed atomically:

1. **Task 1: start_sweep 3-leg pre-check + sweep-level request semantics** — `40f4d29` (feat)
2. **Task 2: sweep progression in step + pending timing + epoch safety** — `33ea085` (feat)

## Files Created/Modified

- `serpentrum/game_engine.py` — added `import math`, `TURN_DEGREES`/`TURN_TICKS` constants, `_rotate_xy` helper, `sweeping` state field (init in reset), `start_sweep` + `_sweep_check_safe` (7-sample 3-leg pre-check), `_advance_sweep` (absolute-per-tick rotation), `step()` sweep branch + pending-application-at-start, `request_direction` sweep-level 180 branch. Stays PURE stdlib-only (gates green).
- `tests/test_engine_turns.py` — 610 lines, 31 tests: rotation-helper sanity (incl. z-preservation-by-caller), 3-leg refusals (boundary/body/pickup with shown arithmetic), head exclusion, positive controls, sweep-level request semantics, rotation exactness over a full sweep (1e-9, z preserved), mid-sweep pose, forward-motion paused, CW turn, sweep-level 180 (down ignored / left buffered), chained-turn net-180, newest-wins, refused-chained falls through, pending applied exactly once, reset epoch safety (mid-sweep + stale-pending).

## Decisions Made

- **`start_sweep` returns `(opened, events)`** (a 2-tuple) rather than a bare bool, so the `('turn_refused', reason)` event is observable in direct calls. The plan said both "return True/False" and "emit ('turn_refused', reason)"; the tuple realizes both faithfully without a hidden side-channel attribute. `opened` is the bool the plan named; `events` carries the reason-tagged refusal (empty on success). Documented in the method docstring.
- **Boundary leg is STRICT "strictly beyond"** (a centroid exactly at the margin wall is inside), matching the plan's "strictly beyond" wording. This is distinct from 02-10's inclusive forward-velocity crash (where the head AT the wall crashes) — the swept pre-check is a centroid-level sampled approximation; the head's own forward movement still uses 02-10's inclusive crash.
- **Absolute-per-tick rotation** (capture start pose at sweep open, re-derive each tick) chosen over incremental rotation to stay drift-free at the plan's tight 1e-9 delta. Incremental 6×15° composition would drift above 1e-9.
- **Pending timing = next-step start** (revision-pinned), NOT at sweep completion. The research §7 sketch said "apply pending at completion" but the plan explicitly overrode this; sweep completion sets heading=target and clears sweeping but does NOT touch pending — a chained turn is attempted at the next step's start by the same rule.
- **Two buffering policies deliberately NOT unified** (static first-kept vs sweep newest-wins), per the plan's "intentional in-sweep override; do not unify" note.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected the plan's boundary-refusal arithmetic typo**

- **Found during:** Task 1 (boundary-refusal test)
- **Issue:** The plan's boundary-refusal test stated the rotated centroid position as `(4.0, 10.0)` and reasoned "10.0 > y1 - BOUNDARY_MARGIN_A = 2.0 - 1.0 = 1.0 -> refuse". The correct rotated position is `(4.0, 6.0)`: centroid (10,0) has offset (6,0) from head (4,0); rotating offset (6,0) by +90° gives (0,6); position = head + offset = (4,0)+(0,6) = (4,6). The plan's "(4,10)" erroneously added the offset's x-component (6) instead of its rotated y-component to the head. The refusal CONCLUSION is unchanged (6.0 > wall 1.0 → refuse 'boundary'), so the specified behavior is correct; only the plan's illustrative arithmetic was wrong.
- **Fix:** Implemented the correct rotation geometry (`_rotate_xy` + `_sweep_check_safe` produce (4,6) and refuse on 6.0 > 1.0). Wrote the test's shown arithmetic correctly (position (4,6); "6.0 > 1.0") and added a dedicated `_rotate_xy` non-origin-center test asserting (4,6). No assertion weakened.
- **Files modified:** tests/test_engine_turns.py
- **Verification:** `test_boundary_refusal_centroid_leg` and `test_rotate_about_non_origin_center` pass; full suite (333) + gates green.
- **Committed in:** 40f4d29 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug — plan arithmetic typo; behavior correct as specified)
**Impact on plan:** Cosmetic arithmetic correction in test comments + one extra helper test. No scope creep; the implemented behavior exactly matches the plan's specified contract.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required. Pure stdlib module; no new dependencies.

## Next Phase Readiness

- **02-14 (pure integration)** can wire turn input (key binding) → `request_direction` → `step()` sweeps, and render the sweep state (`sweeping` dict, `('turning', frac)` events). The engine now owns the full turn/collision/capture truth.
- **Phase 4/5 controller** can map arrow keys to `request_direction` and read `sweeping`/heading for rendering; sweep animation polish (easing, partial-tick rendering) is Phase 5 (the pure math stays coarse at TURN_TICKS samples by design).
- **No blockers.** The forward-compatibility convention (02-06/02-10 never step while pending) held; both prior suites are green and unmodified.
- **Minor note for future:** the swept boundary leg is centroid-level at 7 samples (v1 sampled approximation); Phase 5 may add atom-level boundary samples / finer sampling if playtesting demands (the pickup leg is already atom-level at 2.5 A).

---
*Phase: 02-pure-core-game-chemistry-logic*
*Completed: 2026-09-09*
