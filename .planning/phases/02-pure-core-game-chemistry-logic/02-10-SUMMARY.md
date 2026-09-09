---
phase: 02-pure-core-game-chemistry-logic
plan: 10
subsystem: game-engine
tags: [game-engine, collision, polyline-edges, pickup-capture, counters, pure-stdlib, continuous-2d]

# Dependency graph
requires:
  - phase: 02-06
    provides: movement core (GameEngine continuous-2D state, constant-speed step(), direction queue, pause/resume/reset, segments state seam)
provides:
  - AABB boundary crash (BOUNDARY_MARGIN_A, all 4 walls, inclusive) with finished/result end-of-run state
  - Polyline-edge self-collision (head-centroid vs chain edges, SEGMENT_SKIP_RECENT neck exemption, strict <)
  - _point_segment_distance_sq module-level helper (reusable by 02-13's swept body leg)
  - Pickup capture/attach/reject STACK-05 seam ('stacked' event, ('refused', id, reason) return, atoms-carrying records)
  - Win-at-cap ('won') and once-per-run atom-budget warning ('budget_warning') counters
  - Collision/rules constants block (BODY_COLLISION_RADIUS_A, SEGMENT_SKIP_RECENT, PICKUP_RADIUS_A, BOUNDARY_MARGIN_A, SWEEP_PICKUP_CLEARANCE_A)
affects: [02-13 (rigid-pivot turn sweeps — reuses _point_segment_distance_sq, BOUNDARY_MARGIN_A, SWEEP_PICKUP_CLEARANCE_A, crash-clears-pending), Phase-4/5 controller (STACK-05 seam: 'stacked' -> place -> attach_segment/reject_pickup)]

# Tech tracking
tech-stack:
  added: []
  patterns: [polyline-edge collision (head-centroid vs chain segment-centroid edges with clamped projection), STACK-05 controller seam (capture-in-step -> controller-place -> attach-or-reject), once-per-run warning flag (_budget_warned), counter-NEUTRAL attach vs counter-ROLLING reject]

key-files:
  created: [tests/test_engine_rules.py]
  modified: [serpentrum/game_engine.py]

key-decisions:
  - "Polyline-edge model (head-centroid vs chain edges built from segment centroids) is AUTHORITATIVE — GAME-05's literal wording; per-atom sphere checks not used"
  - "BOUNDARY_MARGIN_A = 1.0 = BODY_COLLISION_RADIUS_A / 2 is the ONE margin name everywhere (HEAD_WALL_MARGIN_A retired); 02-13's boundary leg reuses it"
  - "BODY_COLLISION_RADIUS_A = 2.0 MUST stay < 3.4 A (committed dimer2 stacking distance) minus margin, else the head collides with the segment just stacked"
  - "reject_pickup RETURNS ('refused', pickup_id, reason) canonical 3-tuple — step() events can't be emitted from controller-called methods"
  - "Pickup records carry 'atoms' (REQUIRED) — 02-13's swept pickup leg consumes atom positions at atom-level clearance"
  - "Win checked AFTER capture on same tick (molecules_stacked >= cap); never fires on a crash tick (crash stops processing first)"
  - "Budget warning is WARNING-LEVEL (once per run, never a hard stop); the hard pre-xtb re-check is Phase 6's runner"

patterns-established:
  - "Event order per research §7: ('moved',) -> boundary -> ('crashed','boundary') -> body -> ('crashed','body') -> pickup -> ('stacked',pickup) -> ('budget_warning',atoms_total) -> ('won',)"
  - "Crash stops all later event processing for the tick and clears the pending queue (turn-state hygiene for 02-13)"
  - "Finished engine (crashed/won) no-ops on every later step() returning []"
  - "Constructor extends with keyword args + None defaults so 02-06's tests never break (they never pass the new args)"

# Metrics
duration: 26 min
completed: 2026-09-08
---

# Phase 02 Plan 10: Engine Collisions + Rules Summary

**AABB boundary crash, polyline-edge self-collision with neck exemption, pickup capture/attach/reject STACK-05 seam, and win-cap/budget counters layered on the 02-06 movement core — all pure stdlib float math**

## Performance

- **Duration:** 26 min
- **Started:** 2026-09-08T19:59:09Z
- **Completed:** 2026-09-08T20:25:15Z
- **Tasks:** 3
- **Files modified:** 2

## Accomplishments
- Boundary crash (GAME-05): AABB + BOUNDARY_MARGIN_A=1.0 on all four walls, inclusive at the margin-adjusted walls; crashed engine is inert with pending cleared
- Self-collision (GAME-05, AUTHORITATIVE polyline-edge model): head-centroid vs chain edges built from segment centroids, SEGMENT_SKIP_RECENT=2 neck exemption, strict < BODY_COLLISION_RADIUS_A=2.0; module-level _point_segment_distance_sq helper reusable by 02-13
- Pickup capture/attach/reject (STACK-05): 'stacked' event with atoms-carrying records, attach_segment (counter-NEUTRAL frozen GAME-10 record), reject_pickup (counter rollback + canonical ('refused', id, reason) return)
- Win-at-cap ('won') and once-per-run budget warning ('budget_warning') with exact counters (molecules_stacked, atoms_total, pickups_remaining)
- Event ordering per research §7 verified: crash stops all later processing; win/budget checked after capture on same tick

## Task Commits

Each task was committed atomically:

1. **Task 1: Boundary collision (AABB + BOUNDARY_MARGIN_A) + crash semantics** - `90ad833` (feat)
2. **Task 2: Polyline-edge self-collision (head-centroid vs chain edges, skip recent 2)** - `2b41237` (feat)
3. **Task 3: Pickup capture/attach/reject + score/win-cap/atom-budget counters + win event** - `8d958ba` (feat)

## Files Created/Modified
- `serpentrum/game_engine.py` - Extended with collision rules (boundary + body), pickup capture/attach/reject, win-cap/budget counters, constants block, _point_segment_distance_sq helper (473 lines total, PURE stdlib-only)
- `tests/test_engine_rules.py` - 27 deterministic scenario tests covering boundary (4 walls, inclusive edge, just-inside, box-None, crashed-inert), body (exact-tick crash, neck exemption proof, strict <, precedence, too-few-segments), pickup (capture, attach, no-capture, exactly-radius, no-refire, reject+recapture, at-most-one), win/budget (win-at-cap, budget-once-per-run, reset-clears-flag), event ordering (move+capture, crash-stops-all, full stacked->budget->won) (597 lines)

## Decisions Made
- Polyline-edge model (head-centroid vs chain edges built from segment centroids) is AUTHORITATIVE — GAME-05's literal wording; per-atom sphere checks (a superseded draft variant) are NOT used
- BOUNDARY_MARGIN_A = 1.0 = BODY_COLLISION_RADIUS_A / 2 is the ONE margin name everywhere; HEAD_WALL_MARGIN_A is retired; 02-13's boundary leg reuses it
- BODY_COLLISION_RADIUS_A = 2.0 MUST stay < 3.4 A (committed dimer2 stacking distance) minus margin — constraint comment documented in the constants block
- reject_pickup RETURNS ('refused', pickup_id, reason) canonical 3-tuple — step() events cannot be emitted from controller-called methods, so the controller logs the returned tuple
- Win checked AFTER capture on the same tick (molecules_stacked >= cap); never fires on a crash tick (crash stops processing first)
- Budget warning is WARNING-LEVEL (once per run via _budget_warned flag, never a hard stop); the hard pre-xtb re-check is Phase 6's runner
- SWEEP_PICKUP_CLEARANCE_A = 2.5 defined here (this plan owns the constants block) for 02-13's swept pickup leg — same rationale as 02-04 check_clash's 2.5 A inter-fragment threshold

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] reject_pickup double-rollback guard**
- **Found during:** Task 3 (reject_pickup implementation)
- **Issue:** The plan specifies reject_pickup unconditionally rolls back counters. If called for a pickup that was never captured (still live), this would produce negative counters — a correctness bug on controller misuse.
- **Fix:** Added a guard: if the pickup id is already in live_pickup_ids (never captured or already rejected), the counters are NOT rolled back, but the refusal count is still tracked and the canonical ('refused', pickup_id, reason) tuple is still returned. The normal flow (reject after capture) is unaffected — the guard only fires on misuse.
- **Files modified:** serpentrum/game_engine.py
- **Verification:** test_reject_then_recapture passes (normal flow); guard is defensive only
- **Committed in:** 8d958ba (Task 3 commit)

---

**Total deviations:** 1 auto-fixed (1 missing critical)
**Impact on plan:** Defensive guard prevents negative counters on controller misuse. No scope creep — the normal STACK-05 flow (capture -> reject -> recapture) is unaffected.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Collision/rules half of the engine is complete; 02-06's movement core contract is unbroken (17 tests green, untouched)
- _point_segment_distance_sq module-level helper is ready for 02-13's swept pre-check body leg
- BOUNDARY_MARGIN_A and SWEEP_PICKUP_CLEARANCE_A constants are defined and ready for 02-13's boundary and pickup sweep legs
- Crash-clears-pending behavior is in place for 02-13's turn-state hygiene
- STACK-05 controller seam ('stacked' -> place -> attach_segment/reject_pickup) is ready for the Phase-4/5 controller
- No blockers or concerns

---
*Phase: 02-pure-core-game-chemistry-logic*
*Completed: 2026-09-08*
