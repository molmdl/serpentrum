---
phase: 05-stacking-game-rules
plan: 13
subsystem: ui
tags: [pymol, pyqt5, game-engine, stacking, placement-full-seam]

# Dependency graph
requires:
  - phase: 05-stacking-game-rules (plans 05-04/05-05/05-09/05-11/05-12)
    provides: reject-after-won un-finish (G2), pure placement.resolve seam, hud_logic STACK-04 builders, begin_game session/spawn state, the pure integration chain spec
provides:
  - GameTab._handle_stack_event - the Phase-5 connector resolving every ('stacked',) capture synchronously in one tick
  - 'stacked' + guarded 'won' branches in _handle_event
  - _respawn_pickup - one-spawn-per-resolution gate (controller extends engine pickups/live/remaining; the engine has no spawn API)
  - session['stacked_history'] populated with every capture outcome (STACK-04 per-pickup record)
affects: [05-14 turning rendering, 05-15 completion presenter (consumes stacked_history via hud_logic.breakdown_lines)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "GUI seam as line-by-line transcription of the pure integration-test helper (capture() -> _handle_stack_event, same order/calls)"
    - "Exception-guard discipline: reject only when a segment was NOT yet attached (an unconditional reject after attach would desync counters)"

key-files:
  created: []
  modified:
    - serpentrum/gui_game.py

key-decisions:
  - "Spawner takes heading NAME, engine stores vector: module helper _heading_name reverse-looks up game_engine.DIRS (exact axis match always holds under rigid 90-degree sweeps)"
  - "Resolution-time enrichment of the engine pickup record (stack_ring/has_stack_entry/set from records_by_id) inside the seam - ONE truth covering both begin_game-seeded and respawn-seeded pickups"
  - "Respawn gate runs after EVERY resolution (placed and skip/refuse) per the pinned 05-03 spawn policy - one spawn max per resolution, MAX_LIVE_PICKUPS-gated"
  - "Exception guard rejects the capture ONLY when no segment was attached (last-resort counter guard without post-attach desync risk)"

patterns-established:
  - "Viewer-read discipline in tick/event paths: zero get_model/get_extent/get_names anywhere in gui_game.py - placement decides in pure math from session/engine mirrors; bridge calls are transform/rename/materialize writes only"
  - "Object name flow spawn 'srp_pickup_<pid>' -> rename 'srp_seg_<n>' (1-based, len(engine.segments) after attach) entirely inside the srp_ prefix"

# Metrics
duration: 7 min
completed: 2026-09-17
---

# Phase 5 Plan 13: 'stacked' Capture Seam + 'won' Guard Summary

**The Phase-5 connector is live: every capture resolves synchronously in one tick - pure placement decides, the GUI only attaches/renames/logs, reject_pickup fires on every non-placed outcome (counters can never desync), and a clash-refused cap capture can no longer log a false YOU WIN.**

## Performance

- **Duration:** 7 min
- **Started:** 2026-09-17T18:16:34Z
- **Completed:** 2026-09-17T18:23:10Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments

- `_handle_stack_event`: the ('stacked', pickup) capture seam as a line-by-line GUI transcription of `tests/test_phase5_integration.py`'s `capture()` helper (SAME ORDER: skip -> tail -> place -> gate -> attach/reject), with resolution-time record enrichment and the locked 05-05 clash-gate existing-atom set (head + all segments + OTHER live pickups).
- Placed path: `engine.attach_segment` -> `orientation.matrix_rt(R, t)` viewer transform via `pymol_bridge.apply_matrix` -> rename `srp_pickup_<id>` to `srp_seg_<n>` (set_name, smoke-07-verified) -> `stacked_history` entry -> STACK-04 `hud_logic.pickup_block` line.
- Skip/refuse path: `engine.reject_pickup` ALWAYS (locked decision 13; the 05-04 un-finish lives here), `hud_logic.reason_text` reason line, `resume_note` on refusals, refused viewer object stays visible; whole body wrapped in try/except with the reject-`(id, 'error')` last-resort counter guard.
- `_respawn_pickup`: one-spawn-per-resolution gate honoring the 05-03 policy (MAX_LIVE_PICKUPS ceiling, deterministic `next_after`, controller extends the engine-owned pickups list/live ids/remaining counter, edge-on stick materialization, `live_pickup_names` bookkeeping).
- 'won' branch guarded by `engine.finished` so the un-finished clash-refused-cap-capture tick never logs YOU WIN; `resume_note` covers that case in the stacked branch instead.

## Task Commits

Each task was committed atomically:

1. **Task 1: the 'stacked' capture seam** - `09e47df` (feat)
2. **Task 2: seam-order conformance audit** - `c419ffa` (docs)

## Files Created/Modified

- `serpentrum/gui_game.py` - `_handle_stack_event` + `_respawn_pickup` + module helper `_heading_name`; 'stacked' and guarded 'won' branches in `_handle_event`; GameTab class docstring Phase-5 paragraph updated (stacked seam + history live).

## Decisions Made

- Heading-vector -> name reverse lookup (`_heading_name` over `game_engine.DIRS`): the spawner's contract takes heading names while the engine stores the unit vector; rigid 90-degree sweeps keep the heading exactly on an axis vector, so the exact match always holds during play.
- Resolution-time enrichment of the engine pickup record inside the seam (stack_ring/has_stack_entry/set from `records_by_id`) rather than mutating begin_game's seeding: one truth, covers both seed sites.
- Respawn after EVERY resolution (placed included), not only skip/refuse: begin_game spawns exactly one pickup, so placed-path respawn is required for any run beyond one segment; this matches the pinned 05-03 policy text ("success OR refusal").
- Exception guard rejects only when `attached` is False: an unconditional reject after a successful attach would roll counters back while the resident segment remains - the very desync the guard exists to prevent.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Heading type mismatch at the spawn seam**

- **Found during:** Task 1 (respawn gate)
- **Issue:** Plan text passes `engine.heading` to `spawner.next_after`, but the engine stores a unit vector and spawn.py raises ValueError on any non-name heading (contract is `'right'` etc.). A literal implementation would throw on EVERY respawn, routing captures into the exception guard.
- **Fix:** Added module helper `_heading_name(heading)` doing an exact reverse lookup over `game_engine.DIRS` (axis-exact under rigid 90-degree sweeps).
- **Files modified:** serpentrum/gui_game.py
- **Verification:** gates green; 561 unit tests pass; smoke set passes.
- **Committed in:** 09e47df

**2. [Rule 1 - Bug] Engine pickup records lack the skip-taxonomy keys**

- **Found during:** Task 1 (resolve call construction)
- **Issue:** `placement.resolve`/`resolve_skip` reads `has_stack_entry`, `set` and `stack_ring` off the pickup record itself; `begin_game`'s seed (plan 05-11, `spawn.build_pickup_seed` only) carries none of them, so every real capture would resolve SKIP_NO_ENTRY.
- **Fix:** The seam enriches a copy of `pickup_rec` from `records_by_id[molecule_id]` at resolution time (mirroring the test seam's `pickup_seed`); new respawn seeds also carry the three keys so engine records match the test shape.
- **Files modified:** serpentrum/gui_game.py
- **Verification:** gates green; seam call shape matches the pinned integration helper.
- **Committed in:** 09e47df

**3. [Rule 1 - Bug] Exception-guard reject could desync counters post-attach**

- **Found during:** Task 1 (exception guard)
- **Issue:** The plan mandates an unconditional `reject_pickup(id, 'error')` in the exception guard, but after a successful `attach_segment` the id is no longer live, so reject would roll counters back while the segment stays resident - a desync.
- **Fix:** Guard tracks an `attached` flag; reject only fires when no segment was attached (still "never leave a capture dangling").
- **Files modified:** serpentrum/gui_game.py
- **Verification:** grep audit - reject_pickup present in BOTH the skip/refuse path and the exception guard as required.
- **Committed in:** 09e47df

**4. [Rule 1 - Bug] chain_atoms shape for next_after**

- **Found during:** Task 1 (respawn gate argument assembly)
- **Issue:** The plan shorthand "chain_atoms=[a[1:3] flattened from segments' atoms]" contradicts spawn.py's documented contract (`(sym, x, y, z)` shape, head + segment atoms; leg 3 reads indices 1/2).
- **Fix:** Passed `head_atoms + all segment atoms` as full 4-tuples, per spawn.py's next_after docstring.
- **Files modified:** serpentrum/gui_game.py
- **Verification:** gates green; determinism of the spawner pinned by scenario 8 of the integration chain.
- **Committed in:** 09e47df

---

**Total deviations:** 4 auto-fixed (4 bug)
**Impact on plan:** All four reconcile the plan's prose with the pinned module contracts (spawn heading-name contract, engine-record key shape, counter-rollback semantics). No scope creep; the seam remains a pure transcription of the capture() helper.

## Issues Encountered

None - gates green on the first full run of each task (baseline 561 tests; smoke sentinels all flushed).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- 05-14 ('turning' rigid sweep rendering + head mirror + budget line) can build directly on this seam; 'turning' remains intentionally silent here per plan.
- `stacked_history` is populated with exactly the fields `hud_logic.breakdown_lines` consumes at completion (05-15 presenter input ready).
- Gate evidence for 05-16: `python3.6 tests/run_gates.py` green (561 tests); `python3.6 tests/run_gates.py --smoke` - all 7 REQUIRED smokes PASS via flushed SMOKE-OK sentinels (01,03,04,05,06,07,08); informational smoke 02 non-blocking FAIL (known offscreen dead end).

---
*Phase: 05-stacking-game-rules*
*Completed: 2026-09-17*
