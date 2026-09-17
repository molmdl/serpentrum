---
phase: 05-stacking-game-rules
plan: 12
subsystem: testing (pure integration chain)
tags: [game-engine, placement, spawn, stacking, integration-test, win-crash-refuse-skip, determinism]

# Dependency graph
requires:
  - phase: 05-stacking-game-rules (plans 05-03/05-04/05-05/05-08)
    provides: spawn.PickupSpawner / build_pickup_seed (pinned spawn policy,
      G3); engine reject-after-won un-finish (G2); placement.resolve pure
      controller seam (skip taxonomy / tail-growth policy / clash gate /
      outcome contract); setloader records WITH stack_ring (G1 carry-through)
provides:
  - tests/test_phase5_integration.py — the executable specification of the
    GUI 'stacked' controller seam: capture() mirrors 05-RESEARCH
    engine_contracts call order exactly (the plan-05-13 coding spec)
  - Real-data proof of all five Phase-5 success criteria's pure halves:
    win at cap, complete-snake crashes (boundary + body), cited-geometry
    stacking (3.6000 A), refuse/skip policy, G2 un-finish
  - 8 scenario pins: win-at-cap, boundary crash, body crash, biphenyl
    refuse, upload skip, win-refusal un-finish, sweep-rotated tail frame,
    spawn byte-determinism
affects: [05-13 (GameTab 'stacked' capture seam — codes capture() as a
  method), 05-14/05-15 (assume the proven pure behaviors), 05-16
  (phase-closing gates)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "capture(engine, pickup_rec, state): resolve -> attach_segment /
      reject_pickup in ONE test helper that IS the plan-05-13 coding
      spec (02-14 pattern: the GUI plan implements exactly what the test
      proves)"
    - "pickup_seed: spawn.build_pickup_seed + carried record extras
      (stack_ring / has_stack_entry / set survive engine copies as
      unknown keys)"
    - "Real placement chain minted by scripted captures, then re-seeded
      via the constructor test-seam for body-collision (plan-sanctioned
      fallback) — proves placement geometry reaches the collision model"

key-files:
  created:
    - tests/test_phase5_integration.py
  modified: []

key-decisions:
  - "Scenario 1 hand-places pickup centroids on the straight head path
    (plan's explicit 'spawner or hand-placed' allowance): spawner laterals
    (up to +/-6.0 A) can exceed the 3.0 A capture radius and would hang a
    no-turn scripted run; exact capture timing is load-bearing for the
    counter pins. Spawner determinism itself is pinned separately (S8)"
  - "S6 (un-finish): asserts engine.state AFTER step and BEFORE the seam's
    reject via an inline loop — ordering is load-bearing (won fires on the
    stacked tick per the test-pinned referee order)"
  - "S6 also pins the documented re-capture behavior (research open Q4):
    a re-armed pickup inside the 3.0 A capture radius re-captures/re-wins
    on subsequent ticks, and every repetition rides the same
    win/refuse/un-finish seam without refreezing the run"

patterns-established:
  - "Integration-chain tests drive the engine with drive(engine, state,
    max_ticks, stop=...) running capture() per ('stacked',) event, exactly
    as _on_tick's 'stacked' branch will — the tail-centroid-3D snapshot is
    taken pre-capture for distance pins"
  - "Gate box comes from the engine (engine.box_min/box_max) + the
    display_z parameter, never a module constant — S2 proves this via the
    small preset"

# Metrics
duration: ~80 min executor time (two sessions; ~8h interruption between)
completed: 2026-09-17
---

# Phase 5 Plan 12: Pure Integration Chain Test Summary

**Pure integration chain proven end-to-end on real shipped data: win at cap with exact counters + 3.6000 Å stacking pins, complete-snake boundary/body crashes, biphenyl refuse, upload skip, the G2 win-refusal un-finish, sweep-consistent growth, byte-identical spawn determinism — 8 scenarios, 561 tests green, zero product-code changes**

## Performance

- **Duration:** ~80 min executor time (session 1: probe-verification + scenarios 1-7 green; session 2: S6 structure fix + gates + commit; interrupted ~8h between)
- **Started:** 2026-09-16T19:23:46Z
- **Completed:** 2026-09-17T03:25:42Z
- **Tasks:** 1
- **Files modified:** 1 (created)

## Accomplishments
- `tests/test_phase5_integration.py` — the pure integration chain (records -> spawner -> engine -> placement -> attach/reject) pinned across 8 scenarios with ZERO stubs and REAL shipped data (setloader demo set + stacking dataset + molfile + orientation.edge_on_atoms). The module-level `capture()` helper mirrors 05-RESEARCH-core-integration.md engine_contracts clause-by-clause and IS the plan-05-13 coding spec.
- **S1 win at cap:** cap=3, three straight-path captures; `molecules_stacked == 3`, `atoms_total == 54 == sum(atoms_n)`, event order `[moved, stacked, won]` on the final tick, `finished/result == won`; every tail->placed ring-centroid distance == `sqrt(3.383^2 + 1.231^2)` == 3.6000 within 1e-6 (STACK-01 tied to engine counters in one chain).
- **S2/S3 complete-snake crashes:** boundary (small preset ±12) and body (constructor test-seam re-seed of a REAL 4-segment placement chain) both set `finished/result == crashed` with segments preserved (centroids + atom payloads bit-equal) and `step()` a no-op `[]` afterwards.
- **S4 biphenyl refuse:** REFUSE_ATOM over a real naphthalene tail; `reject_pickup` roll-back + re-arm + refusal-count pins; the 90.00° two-ring fact documented as a DATA observation (permanent refuse-path demonstrator, recorded NOT fixed).
- **S5 upload skip:** upload-shaped capture -> SKIP_NO_ENTRY, counters net zero, refusal tracked (`__upload__` keying).
- **S6 un-finish:** cap=1 with the only pickup clash-bound; `won` asserted AFTER step/BEFORE reject (load-bearing order), then `reject_pickup` un-finishes (counters below cap -> `finished False / result None`) and the head resumes moving; repeated re-captures of the re-armed pickup ride the same seam.
- **S7 sweep interplay + S8 determinism:** post-sweep growth direction == pre-sweep direction rotated by the sweep angle (dot > 0.99, planarity invariant); spawner output sequences reproduce byte-identically across a full scenario-1-shaped run.
- Full gates green: 561 tests (553 baseline + 8 new), syntax + plugin-path safety + AST purity.

## Task Commits

1. **Task 1: pure integration scenarios** - `6dc11b7` (test)

**Plan metadata:** `docs(05-12): complete pure integration chain plan` (this doc)

## Files Created/Modified
- `tests/test_phase5_integration.py` - The pure integration chain: 8 scenarios (win/crash x2/refuse/skip/un-finish/sweep/determinism) across the shared `build_fixture()` + `capture()` controller-seam spec.

## Decisions Made
- **Scenario 1 hand-placed centroids on the straight path** (plan's explicit "spawner or hand-placed" allowance). Rationale: exact capture timing is load-bearing for the counter pins, and the spawner's seeded laterals (up to ±6.0 Å) can exceed the 3.0 Å capture radius. Spawner determinism itself is pinned separately (S8 byte-identity), so the GAME-07 restart contract is still proven at the spawn seam.
- **S6 ordering assertions via an inline loop** (not the `drive()` helper): the 'won' state must be asserted AFTER `step()` returns the `[moved, stacked, won]` list but BEFORE the seam's `reject_pickup` runs — order is load-bearing and a generic driver would hide it.
- **S6 also pins repeated re-capture behavior** (research open Q4): re-armed pickups stay put; a clash-bound re-armed pickup inside capture radius re-captures/re-wins on subsequent ticks, and every repetition rides the same win/refuse/un-finish seam. This behavior is the engine truth, not a test artifact.

## Deviations from Plan

None — plan executed as written. The only judgment calls were the plan's own explicit allowances (hand-placed scenario-1 centroids; the S3 constructor test-seam fallback after the scripted two-90° loop-back was computed unreachable on the medium box), both documented above and in the test docstrings.

## Issues Encountered
- **S6 test-structure iteration (3 commits-equivalent in-session)**: the first draft's final `assertFalse(engine.finished)` fought the engine's re-capture truth (re-armed biphenyl inside capture radius re-wins on the resumed tick). Resolved by folding the whole resume window into one loop that runs the seam on every re-capture and asserts per-repetition un-finish — the test now asserts honest engine semantics per research open Q4.
- **No product bugs found.** Every observed engine behavior (re-capture of re-armed pickups, un-finish guards, event order) matched the pinned contract in `game_engine.py` docstrings and `tests/test_engine_rules.py`/`test_engine_win_desync.py`.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- **Ready for plan 05-13** (GameTab 'stacked' capture seam): the plan's coding spec is `capture()` in this file — the identical call order, existing-atom set, and attach/reject symmetry, plus the mid-run pickup append seam (engine has no spawn API; the controller extends `engine.pickups` / `live_pickup_ids` / `pickups_remaining` itself, proven in S7).
- **05-14/05-15** can assume the proven pure behaviors: win-at-cap counters + 3.6000 Å placements, complete-snake crash outcome, refuse/skip reason codes (REFUSE_ATOM, SKIP_NO_ENTRY), sweep-consistent stacking, and spawn byte-determinism.
- **No product-bug flags to carry forward.** The biphenyl 90° two-ring finding remains a DATA observation only (shipped conformer); the refuse path absorbs it by design.

---
*Phase: 05-stacking-game-rules*
*Completed: 2026-09-17*
