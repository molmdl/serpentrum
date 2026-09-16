---
phase: 05-stacking-game-rules
plan: 10
subsystem: viewer (bridge + setup GUI)
tags: [pymol, transform_selection, edge-on, pi-stack, smoke-test, stacking]

# Dependency graph
requires:
  - phase: 05-stacking-game-rules (plans 05-01/05-02/05-05/05-07)
    provides: molfile.ring_cycle (canonical planar ring in walk order);
      orientation.edge_on_m16 / edge_on_atoms / matrix_rt (verified TTT
      layout); placement.tail_frame / attempt_place (pure controller seam);
      pymol_bridge.apply_matrix (Phase-5 bridge primitives, append-only)
provides:
  - head materializes EDGE-ON at Apply — transform BEFORE place_head
    extent-centering (locked 03-08 + 04-07 presentation decision landed)
  - pymol_bridge.materialize_pickup: pickup spawns edge-on at its spawn
    centroid from a caller-supplied m16, rendered as sticks (GAME-03)
  - REQUIRED smoke 08: probe F replicated end-to-end headless through the
    shipping code path — dataset-driven placement lands at 3.6000 A
    ring-centroid distance with pure coords == viewer coords
affects: [05-11 (begin_game spawn/materialize), 05-13 (stacked capture seam),
  05-16 (phase-closing gates), Phase 5 success criterion 1]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Caller-composed m16: bridge NEVER parses SDFs — pure layer (molfile
      + orientation) builds the transform, bridge only forwards to
      cmd.transform_selection"
    - "Edge-on FIRST ordering: orientation transform before extent-based
      centering (materialize head; Pattern 1 of 05-RESEARCH-pymol-mechanics)"
    - "Graceful degradation: records without stack_ring -> head_m16=None
      (flat head), never blocks Apply"

key-files:
  created:
    - smoke/08_stack_place_smoke.py
  modified:
    - serpentrum/pymol_bridge.py
    - serpentrum/gui_setup.py
    - tests/run_gates.py

key-decisions:
  - "materialize gains optional head_m16=None kwarg (backward compatible:
    gui_game/smokes calling materialize(setup, records) unchanged)"
  - "gui_setup._on_apply re-calls pymol_bridge._select_head_record (pure-
    with-respect-to-cmd) to pick the SAME record materialize will, then
    computes edge_on_m16 via molfile+orientation ONLY when stack_ring
    exists; any failure -> head_m16=None (flat head) rather than blocking"
  - "3.6000-pin: dataset sqrt(3.383^2+1.231^2)=3.60000694 — smoke asserts
    pure exactness vs the dataset value (<=1e-6) plus the 4-dp claim
    '%.4f'=='3.6000', instead of the plan's impossible literal 1e-6 pin"

patterns-established:
  - "materialize_pickup(path, name, m16): load + ONE transform + show
    sticks; the pickup-side twin of the head materialize path"
  - "Probe-replication smokes: ship the research probe as REQUIRED
    regression through shipping entry points, never re-spike"

# Metrics
duration: 20 min
completed: 2026-09-16
---

# Phase 5 Plan 10: Edge-on Materialization Summary

**Head and pickups materialize edge-on (locked 03-08/04-07 presentation) and a dataset-driven pi-stack placement machine-verifies 3.6000 A ring-centroid distance in real headless PyMOL — pure coords == viewer coords through the shipping code path.**

## Performance

- **Duration:** 20 min
- **Started:** 2026-09-16T18:53:38Z
- **Completed:** 2026-09-16T19:13:39Z
- **Tasks:** 2
- **Files modified:** 3 (+1 created)

## Accomplishments
- `pymol_bridge.materialize(setup, records, head_m16=None)` applies the pure edge-on matrix to the head via `cmd.transform_selection` AFTER `load_molecule` and BEFORE `place_head` extent-centering — the extent being centered is the canonical one (Pattern 1 ordering, 05-RESEARCH-pymol-mechanics). The 04-07 user remark (head displayed flat rings -> pickups would contact via hydrogen edge) is resolved at the Apply path.
- `pymol_bridge.materialize_pickup(path, name, m16)` spawns a pickup edge-on at its caller-composed spawn centroid as STICKS (`cmd.load(zoom=0)` + transform + `cmd.show('sticks')`); bridge stays parse-free — m16 = `orientation.matrix_rt(R_edge, centroid, pre)` composed by the caller.
- `gui_setup._on_apply` computes `head_m16` purely (`molfile.read_sdf` + `orientation.edge_on_m16` over the record's `stack_ring`) and passes it to materialize; records without `stack_ring` (uploads; demo records pre-05-08) or any parse/frame failure degrade to `head_m16=None` rather than blocking Apply — sibling-branch-safe on purpose (05-08 merges the key in parallel).
- REQUIRED smoke 08 replicates probe F END-TO-END with REAL data (benzene.sdf + APPROVED `pi_stack_pd`: 3.383/1.231 A): `SMOKE-OK EDGEON` (viewer z-extent == pure 4.297 A), `SMOKE-OK PLACE360` (pure distance exact vs `sqrt(3.383^2+1.231^2)` <=1e-6; viewer distance 3.6000 A <=1e-3; sorted/rounded pure == viewer coords <=5e-3), `SMOKE-OK PICKUPS` (spawn materializer exists + ring centroid lands at the composed spawn centroid).

## Task Commits

Each task was committed atomically:

1. **Task 1: edge-on head materialization + pickup materializer** - `b9818ad` (feat)
2. **Task 2: REQUIRED smoke 08 — real-data edge-on + placement end-to-end** - `4631a45` (test)

## Files Created/Modified
- `serpentrum/pymol_bridge.py` - materialize head_m16 option + materialize_pickup
- `serpentrum/gui_setup.py` - _on_apply computes head_m16 purely, passes it
- `smoke/08_stack_place_smoke.py` - REQUIRED edge-on + placement smoke (created)
- `tests/run_gates.py` - smoke 08 added to REQUIRED_SMOKES

## Decisions Made
- Head-m16 computation lives in the GUI (caller), NOT the bridge — preserves the "bridge never parses SDFs" discipline; `_select_head_record` is called twice (once from gui_setup, once inside materialize) because it is pure-with-respect-to-cmd, making the choice provably identical.
- `materialize` keeps a backward-compatible signature (`head_m16=None` default) — existing callers (`gui_game` re-center, smokes 03/04) are untouched.
- The 3.6000 pin asserts the dataset-derived value, not the literal 3.6000 (see deviation 1).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Pure 3.6000 pin replaced with dataset-exact assertion**

- **Found during:** Task 2 (smoke 08 PLACE360 step)
- **Issue:** Plan step (b) says "Assert pure placed-vs-tail ring-centroid distance == 3.6000 within 1e-6". The dataset encoding itself does not satisfy this: `sqrt(3.383^2 + 1.231^2) = 3.60000694` — off from 3.6000 by 6.9e-6, so the literal assertion fails mathematically. The research's own probe F2 used `abs(d - expected) < 1e-3` with `expected = sqrt(3.383^2 + 1.231^2)`.
- **Fix:** Smoke asserts (i) pure distance EXACT vs the dataset-derived value within 1e-6 (the placement math is exact), and (ii) the 4-decimal claim via `'%.4f' % dist == '3.6000'` (the phase success-criterion wording "lands at the cited 3.6000 A"). Viewer checks keep the plan's 1e-3 tolerances unchanged.
- **Files modified:** smoke/08_stack_place_smoke.py (documented in the module docstring's 3.6000-PIN NOTE)
- **Verification:** SMOKE-OK PLACE360 flushes; pure-vs-dataset error measured <1e-6.
- **Committed in:** 4631a45 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 plan-pin bug)
**Impact on plan:** The pin change makes the smoke honest about floating-point reality without weakening any check — dataset exactness (1e-6) + 4-dp claim + viewer tolerances are all strictly as strong-or-stronger than the plan's intent. No scope creep.

## Issues Encountered
None — gates green on first run for both tasks; smoke 08 passed EDGEON/PLACE360/PICKUPS on the first Windows-PyMOL run.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Sibling 05-08 (setloader `stack_ring` carry) merges in this wave and makes the gui_setup head-m16 path fully live (today's guard degrades to flat head with no `stack_ring` — designed and expected).
- 05-11 (begin_game spawn/materialize) consumes `materialize_pickup` + `matrix_rt(R_edge, spawn, pre)` composition directly (smoke 08 PICKUPS step is the reference pattern).
- The phase-level "placed distance == cited value" success claim is now machine-verified in the REAL viewer through the shipping code path (STACK-01 viewer proof; G5 viewer half + G7 part 2 complete).

---
*Phase: 05-stacking-game-rules*
*Completed: 2026-09-16*
