---
phase: 05-stacking-game-rules
plan: 11
subsystem: gui
tags: [pymol, qt, game-loop, pickups, spawn, edge-on, head-mirror, teardown, stacking]

# Dependency graph
requires:
  - phase: 04-08
    provides: "_teardown_round as THE single teardown helper (the designated extension point); arm-before-timers play lifecycle"
  - phase: 05-02
    provides: "orientation.py edge_on_atoms/edge_on_m16/edge_on_frame + the verified matrix_rt TTT composer (G5)"
  - phase: 05-03
    provides: "spawn.py PickupSpawner/seed_from_setup/build_pickup_seed (deterministic seeded spawn policy, G3)"
  - phase: 05-06
    provides: "records + stacking_data anchored on _serpentrum by gui_setup apply (G4 source)"
  - phase: 05-08
    provides: "setloader demo records carrying stack_ring (canonical ONE-ring cycle)"
  - phase: 05-10
    provides: "pymol_bridge.materialize_pickup/delete_pickups/apply_matrix + the Apply-path edge-on materialization contract"
provides:
  - "begin_game consumes the anchored records: deterministic first pickup via PickupSpawner(crc32 setup seed) -> build_pickup_seed -> GameEngine(pickups=[seed]), materialized edge-on as sticks (srp_pickup_<pid>) before the countdown"
  - "Pure head-atom mirror == viewer truth: edge-on atoms extent-centered like place_head, per-tick translated by the SAME delta passed to move_head_delta"
  - "Restart pose reset: _reset_head_viewer re-applies edge_on_m16 to srp_head before place_head (sweeps rotate atomic coords, so every begin_game restores the canonical pose)"
  - "_teardown_round step (f): pattern-delete srp_pickup_* folded INTO the ONE helper (locked decision 8); chain objects (srp_head/srp_seg_*) survive - the GAME-09 'viewer clears' semantics"
  - "Session additions on _serpentrum.game_session: head_atoms/head_stack_ring/records_by_id/spawner/stacked_history/live_pickup_names/last_turn_delta (the 05-13 capture seam + 05-14 sweep consume them)"
affects: [05-13 (capture seam uses spawner/records_by_id/head_atoms/session keys), 05-14 (turn sweep mirrors last_turn_delta), 05-15 (completion inherits teardown's pickup clearing), Phase 6/7 (chain handoff)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Mirror == viewer by construction: every viewer transform applied by the bridge is replicated in PURE math (edge_on + extent-center for the head; matrix_rt(R, centroid, pre) split into mirror atoms + seed for pickups) - zero readback, zero drift"
    - "Engine-seeded-then-materialized pickups: the spawner/engine seed is the truth; begin_game materializes the SAME record/centroid afterward so viewer and engine can never disagree"
    - "Single-teardown extension (locked decision 8): Phase-5 additions go INTO _teardown_round, never a second helper"

key-files:
  created: []
  modified:
    - serpentrum/gui_game.py

key-decisions:
  - "Pickup teardown is a pattern delete of srp_pickup_* inside _teardown_round (after camera unlock, before the blockSignals button reset), NOT per-name deletion from live_pickup_names - idempotent and reload-safe like unlock_camera, and on the _end_run path it runs before the completion presenter (GAME-09 ordering)"
  - "Records without stack_ring (uploads) get an identity-rotation + extent-center fallback for BOTH the atom mirror and the pickup m16 (the plan's demo-only atoms_by_id would KeyError the spawner on upload-only games; the pinned spawn policy says uploads spawn and are skipped at capture, so the fallback preserves policy without changing it)"
  - "spawner.first takes the heading NAME 'right', not the unit vector the plan sketched - spawn.py's _DIRS-keyed contract is the authority (call what exists)"
  - "Skipped the plan's dead fetch of stacking_data into an unused local; its consumer (the 05-13 'stacked' seam) reads _anchor.stacking_data directly"

patterns-established:
  - "_reset_head_viewer(records_by_id, setup) as the begin_game pose-reset seam: apply_matrix(edge_on_m16) THEN place_head, guarded by object_exists and degraded to bare place_head for records without stack_ring (Apply path parity)"
---

# Phase 5 Plan 11: GameTab Begin-Game Wiring Summary

**begin_game now consumes the anchored records end-to-end: the head pose is reset edge-on, the first pickup spawns deterministically (crc32 setup seed) and lands in the engine AND the viewer with provably identical coordinates (0.0 Angstrom mirror deltas), restart reproduces the exact same scene, and every end path pattern-deletes srp_pickup_* through the single _teardown_round helper while the chain survives.**

## Performance

- **Duration:** 22 min
- **Started:** 2026-09-16T19:30:22Z
- **Completed:** 2026-09-16T19:52:40Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments

- **Deterministic pickup seeding (G3 + G4 consumption)** — `_build_engine` reads `_anchor.records`, builds origin-centered atom mirrors for every record, constructs `spawn_mod.PickupSpawner(records, box, spawn_mod.seed_from_setup(setup), atoms_by_id)`, spawns the FIRST pickup, and seeds `GameEngine(pickups=[build_pickup_seed(...)])`. Two rebuilds of the same setup produce byte-identical (id, molecule_id, centroid) — restart determinism holds; no records anchored degrades to pickups=None with a logged notice (degraded but non-crashing).
- **Head mirror == viewer (G5 apply)** — `_build_head_state` selects the head record the SAME way materialize does (`pymol_bridge._select_head_record`), computes `orientation.edge_on_atoms`, and extent-centers in pure math replicating `place_head` exactly; `_reset_head_viewer` re-applies `edge_on_m16` to srp_head before `place_head` so Restart restores the canonical pose; `_on_tick`'s moved branch translates `session['head_atoms']` by the SAME (dx, dy) passed to `move_head_delta`. WSL sanity pass: head extent-center residual < 1e-12, moved-mirror delta exact.
- **Pickup materialization edge-on as sticks** — begin_game (after session creation, before the countdown) composes `orientation.matrix_rt(R_edge, (cx, cy, 0.0), pre)` per engine seed and calls `pymol_bridge.materialize_pickup(record['file'], 'srp_pickup_%s' % pid, m16)`, tracks names in `session['live_pickup_names']`, then ONE-SHOT `frame_scene()` (03-06 contract, never per-tick). Verified numerically: engine seed atoms vs the exact m16 transform of parsed coords differ by 0.000e+00 Angstrom; mirror atoms + centroid vs seed also 0.000e+00 Angstrom (benzene pick_0001 at (8.0, -3.0) on the default setup).
- **Pickup teardown INTO the single helper (locked decision 8)** — `_teardown_round` step (f): `pymol_bridge.delete_pickups()` pattern-deletes `srp_pickup_*` after the camera unlock and before the blockSignals pause-button reset; srp_head/srp_seg_* untouched, so on the `_end_run` path (teardown BEFORE the completion presenter) un-stacked pickups die and the snake stays complete — the GAME-09 'viewer clears' semantics. Camera audit invariants intact: exactly one lock_camera + one unlock_camera call site; four teardown call sites byte-identical; `_begin_play`/`_apply_pause_state`/`request_auto_pause` byte-identical.

## Task Commits

Each task was committed atomically:

1. **Task 1: begin_game — head mirror, spawn, seed, materialize** — `4d2b685` (feat)
2. **Task 2: teardown pickup cleanup (INTO the single helper)** — `b4ae5e0` (feat)

**Plan metadata:** (see final docs commit)

## Files Created/Modified

- `serpentrum/gui_game.py` (+254/-21 net over the two tasks) — module docstring Phase-5 status; imports (`os`, `molfile`, `orientation`, `placement`, `spawn as spawn_mod`); module-level pure helpers `_extent_offset`/`_extent_center`/`_read_record`; begin_game rewrite (records consumption, session Phase-5 keys, pickup materialize loop, one-shot framing); `_build_engine` returns `(engine, extras)`; new helpers `_build_head_state`/`_reset_head_viewer`/`_mirror_atoms`/`_pickup_m16`; `_on_tick` moved-branch mirror translate; `_teardown_round` step (f) + class/teardown docstring updates.

## Gate + Smoke Results

- `python3.6 tests/run_gates.py`: **all gates green** at baseline (553 tests), after Task 1, and after Task 2 (syntax + plugin-path safety PASS; purity AST PASS; 553 unittests PASS).
- `python3.6 tests/run_gates.py --smoke` (run after EACH task — REQUIRED because gui_game touched): **all 7 REQUIRED smokes PASS by sentinel verdict** — SMOKE-OK SKELETON, VIEWER-BRIDGE, VIEWER-DEMO, LOOP-CAMERA, INPUT-WIZARD, TRANSFORM, EDGEON. Smoke 02 (dialog) remains the documented informational non-blocking FAIL (01-05 offscreen dead end). Verdict taken from flushed SMOKE-OK sentinels, never exit codes.
- Lifecycle grep audit (after Task 2): one `pymol_bridge.lock_camera` call site (:461, `_begin_play`), one `pymol_bridge.unlock_camera` (:676, `_teardown_round`), one `game_input.teardown` (:672, `_teardown_round`), one `pymol_bridge.delete_pickups` (:677, `_teardown_round`) — all inside their locked homes; four `_teardown_round()` call sites unchanged.
- Pure-half sanity pass (WSL, stubbed Qt bridge): deterministic first spawn (benzene, pick_0001, (8.0, -3.0)) reproduced identically across rebuilds; engine-seed atoms == viewer m16 transform == mirror+centroid to 0.0 Angstrom; no-records path degrades cleanly.

## Decisions Made

- Pickup teardown is one PATTERN delete (`cmd.delete('srp_pickup_*')`) inside `_teardown_round`, not per-name deletion from `live_pickup_names` — idempotent, independent of session state (works for reload-mid-run), exactly like `unlock_camera`; and because engines claim pickups without renaming viewer objects until 05-13, the pattern also catches claimed-but-unrenamed strays at run end.
- `_reset_head_viewer` degrades to the old bare `place_head` for records without stack_ring (upload heads) — byte-parity with the Apply path's `head_m16=None` behavior, so upload-only first-person games keep playing.
- `_build_engine` returns `(engine, extras)` rather than owning session mutation: the session is born in begin_game (single construction site for the anchored dict); extras folds straight into it.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] spawner.first heading argument type**

- **Found during:** Task 1 (begin_game wiring)
- **Issue:** The plan sketched `spawner.first((0.0, 0.0), (1.0, 0.0))`, but the shipped `spawn.PickupSpawner._spawn` requires a heading NAME (`if heading not in _DIRS: raise ValueError`) — executing the plan literally crashed with `ValueError: unknown heading: (1.0, 0.0)`.
- **Fix:** Call `spawner.first((0.0, 0.0), 'right')` — semantically identical to the plan's intent (the engine's fresh heading is 'right'); comment added at the call site.
- **Files modified:** serpentrum/gui_game.py
- **Verification:** sanity pass spawns the first pickup (benzene, pick_0001, (8.0, -3.0)); full gates green.
- **Committed in:** 4d2b685 (Task 1 commit)

**2. [Rule 2 - Missing Critical] atoms/m16 fallback for records without stack_ring (uploads)**

- **Found during:** Task 1 (atoms_by_id construction)
- **Issue:** The plan builds `atoms_by_id` for demo records WITH stack_ring only. The pinned spawn policy (spawn.py docstring) cycles uploads through exactly like demo records, and the spawner REQUIRES every record id in atoms_by_id (its KeyError is the loud caller-bug signal) — an upload-only game would crash at `spawner.first()`. Upload molecule files may also be .mol2 (read_sdf would raise).
- **Fix:** `_mirror_atoms` + `_pickup_m16` fall back to identity-rotation + extent-center pre-shift for records without stack_ring (stored pose centered at the spawn point — the place_head-equivalent pose), and `_read_record` routes `.mol2` exactly like `setloader.load_upload`. Demo records keep the edge-on path unchanged. No spawn-policy behavior change.
- **Files modified:** serpentrum/gui_game.py
- **Verification:** gates green; demo-set mirror equality still exact (0.0 Angstrom); upload fallback is a pure-math code path (verified by review + the same _extent_center math the head mirror uses).
- **Committed in:** 4d2b685 (Task 1 commit)

**3. [Rule 2 - Missing Critical] skipped the plan's dead stacking_data fetch**

- **Found during:** Task 1 (_build_engine)
- **Issue:** The plan line `stacking_data = getattr(self._anchor, 'stacking_data', None)` has no consumer in this plan — keeping it is dead code against repo cleanliness standards.
- **Fix:** Not fetched; `_build_engine`'s docstring documents that the 05-13 'stacked' seam reads `_anchor.stacking_data` directly (the anchor already carries it from 05-06).
- **Files modified:** serpentrum/gui_game.py (docstring only)
- **Verification:** gates green.
- **Committed in:** 4d2b685 (Task 1 commit)

---

**Total deviations:** 3 auto-fixed (1 blocking, 2 missing critical)
**Impact on plan:** All fixes were required for the plan to run at all (heading argument) or to not regress the promoted upload path (fallbacks); the dead-fetch skip is cleanliness-only. No scope creep; no policy changes.

## Issues Encountered

None beyond the deviations above (both surfaced by executing the plan, both fixed in-task).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **05-13 (capture seam)** has everything it needs: `session['stacked_history']`/`live_pickup_names`/`records_by_id`/`head_atoms`/`head_stack_ring`/`spawner` exist and are anchored; engine capture claims ('stacked' events) already fire (counters move; placement/rename/HUD await the seam).
- **05-14 (turn sweep)** inherits `last_turn_delta` (initialized 0.0) and the head mirror it must rotate alongside the sweep.
- **05-15 (completion)** inherits the teardown-side 'viewer clears' semantics for free; only the presenter (reframe/length/score/Get-Spectra enable) remains.
- Known intermediate state (by design, wave 3): an engine-claimed pickup keeps its `srp_pickup_*` viewer object visible until 05-13 renames/relocates it; `_teardown_round`'s pattern delete now catches such strays at run end.
- Live gameplay behavior (camera, steering, pickups as sticks in the real viewer) remains 05-16's human-verify domain.

---
*Phase: 05-stacking-game-rules*
*Completed: 2026-09-16*
