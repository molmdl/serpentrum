---
phase: 04-game-loop-input
plan: 03
subsystem: infra
tags: [pymol, cmd-seam, game-loop, locked-camera, ortho, cmd-translate, headless-smoke]

# Dependency graph
requires:
  - phase: 03-06
    provides: pymol_bridge BRIDGE module (BOX_NAME/HEAD_NAME, get_names('public_objects'), get_extent [[min],[max]], frame_scene one-shot boundary)
  - phase: 04-RESEARCH-gameloop
    provides: Q2 movement claims M1-M6 (translate camera=0, zero drift, get_object_ttt segfaults), Q3 LOCK/RESTORE recipes C1-C6, Q4 2D-plane P1-P3, pitfalls 1-14
provides:
  - pymol_bridge.move_head_delta(dx, dy, dz=0.0) — zero-drift atomic translate, camera=0 (model axes)
  - pymol_bridge.lock_camera() / unlock_camera(saved) — GAME-02 mechanism (ortho + zoom(srp_box) + button('none') x16; cmd.mouse() + set_view restore)
  - pymol_bridge.object_exists(name) — guarded srp_* scene checks
  - smoke/05_loop_camera_smoke.py — REQUIRED headless proof (sentinel SMOKE-OK LOOP-CAMERA)
affects: [04-05 (tick seam consumes move_head_delta), 04-08 (begin_play/teardown consume lock/unlock_camera), 04-09 (human-verify of mouse restore), Phase 5 (atomic coords stay engine truth for xtb handoff)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "locked camera: lock_camera saves {ortho, 18-float view}, locks via ortho-on + zoom(BOX_NAME) + button('none') x16; unlock via cmd.mouse() + ortho + set_view, None-guarded"
    - "per-tick movement: cmd.translate camera=0 (model axes) — atomic coords = engine truth; NEVER camera=1 (pitfall 4), NEVER set_object_ttt (display-only breaks xtb handoff), NEVER get_object_ttt (segfaults, M5)"

key-files:
  created:
    - smoke/05_loop_camera_smoke.py
  modified:
    - serpentrum/pymol_bridge.py
    - tests/run_gates.py

key-decisions:
  - "module docstring camera boundary updated: Phase 4 owns GAME-02 — ortho/set_view/button are legal in the bridge (the Phase-3 'zoom only' note was phase-scoped)"
  - "zero-drift smoke tolerance is 1e-5 not 1e-9: PyMOL stores atomic coords as C floats (32-bit); the probe's exact 1.5 was a pseudoatom at exactly 0.0, real-molecule coords carry float32 epsilon (~6e-8)"

patterns-established:
  - "camera lock/restore pair returns a saved dict and is idempotent via None guard — every teardown path calls unlock_camera"
  - "float32-aware smoke assertions: exact-value claims from pseudoatom probes need float32-epsilon tolerances on real molecules"

# Metrics
duration: 5min
completed: 2026-09-12
---

# Phase 4 Plan 03: Bridge Movement + Locked Camera Summary

**Game-loop cmd seams in pymol_bridge — zero-drift move_head_delta (translate camera=0), GAME-02 lock_camera/unlock_camera (ortho + zoom(srp_box) + 16x button('none'), cmd.mouse()/set_view restore), object_exists guard — machine-proven headless by new REQUIRED smoke SMOKE-OK LOOP-CAMERA**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-09-12T19:30:18Z
- **Completed:** 2026-09-12T19:34:24Z
- **Tasks:** 2
- **Files modified:** 3 (1 created, 2 modified)

## Accomplishments
- 4 game-loop bridge functions live at the only legal cmd seam, with gameloop-research-faithful contracts (M3 zero-drift, C1-C4 lock/restore, P3 dz=0)
- GAME-02's mechanism exists and is regression-protected as a REQUIRED smoke: zero-drift translate (5x0.3A=1.5A within float32 epsilon), ortho save/restore (C1), 18-float view round-trip (C2/VIEW_STABLE), 16 button('none') calls clean (C3)
- Required-smoke coverage now 01/03/04/05; both gate commands green, 433 unit tests green

## Task Commits

Each task was committed atomically:

1. **Task 1: Bridge movement + locked-camera functions** — `89f3f46` (feat)
2. **Task 2: Loop-camera smoke + required registration** — `fdae9a0` (test)

**Plan metadata:** see docs(04-03) commit (PLAN + SUMMARY only)

## Files Created/Modified
- `serpentrum/pymol_bridge.py` — move_head_delta, lock_camera, unlock_camera, object_exists + _LOCK_BUTTONS/_LOCK_MODS constants; module docstring camera paragraph updated (Phase 4 owns GAME-02)
- `smoke/05_loop_camera_smoke.py` — headless smoke, 6 steps (scene / move_zero_drift / lock_camera / unlock_camera / object_exists / cleanup), sentinel SMOKE-OK LOOP-CAMERA
- `tests/run_gates.py` — REQUIRED_SMOKES += smoke/05_loop_camera_smoke.py

## Decisions Made
- **Camera-boundary docstring:** the Phase-3 "one-shot zoom ONLY, NEVER ortho/set_view" note in the module docstring was phase-scoped; rewrote the camera paragraph to record that Phase 4 owns GAME-02 and ortho/set_view/button are now legal in the bridge (04-RESEARCH-gameloop Q3; 03-RESEARCH-viewer-bridge sec 5.2:359-363).
- **Zero-drift tolerance 1e-5:** plan said "within 1e-9 ... exactly 1.5 A". The probe-verified exactness (M3) used a pseudoatom at exactly 0.0; PyMOL stores atomic coords as C floats (32-bit), so real-molecule coords carry float32 epsilon — observed residual 6e-8 A over 5 ticks. 1e-5 is ~2 orders of magnitude above the float32 floor and ~8 below any real desync bug (camera-axes errors are Angstrom-scale). Documented inline in the smoke.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Smoke zero-drift tolerance 1e-9 -> 1e-5 (float32 coordinate storage)**
- **Found during:** Task 2 (smoke execution — move_zero_drift failed with dx=1.5000000596046448)
- **Issue:** Plan-mandated assertion `abs(dx - 1.5) < 1e-9` cannot hold on real molecules: PyMOL stores atomic coordinates as C floats (32-bit), so each translate rounds to float32. The probe M3's "exactly 1.5" was measured on a pseudoatom starting at exactly 0.0 (float32-exact).
- **Fix:** Tolerance relaxed to 1e-5 with an inline comment explaining the float32 floor and why the bound still catches real drift/desync bugs.
- **Files modified:** smoke/05_loop_camera_smoke.py
- **Verification:** SMOKE-OK LOOP-CAMERA flushed; y/z extents asserted bit-identical (no tolerance needed — dy=dz=0.0 exactly).
- **Committed in:** fdae9a0 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug — over-strict assertion incompatible with float32 coord storage)
**Impact on plan:** Assertion semantics unchanged (drift is still machine-proven ~1e8x below any gameplay-relevant error); no API or scope change.

## Issues Encountered
- None beyond the deviation above; first smoke run exposed it and it was fixed inline.

## User Setup Required
None — no external service configuration required.

## Next Phase Readiness
- Plan 04-05 can call `pymol_bridge.move_head_delta(dx, dy, 0.0)` per ('moved',) tick without further bridge edits.
- Plan 04-08 can call `lock_camera()` at _begin_play and `unlock_camera(saved)` from the single _teardown_round helper; the None guard makes double-teardown safe.
- Plan 04-09 human-verify owns the live mouse-drag restore verdict (no per-button read-back API exists in 2.5.0 — noted in the smoke's unlock step comment).
- C4 caveat for Help docs: cmd.mouse() restores button_mode DEFAULTS, not per-user customizations (acceptable for v1).

---
*Phase: 04-game-loop-input*
*Completed: 2026-09-12*
