---
phase: 05-stacking-game-rules
plan: 07
subsystem: bridge
tags: [pymol-2.5.0, transform_selection, cmd.rotate, rigid-sweep, headless-smoke, G7]

# Dependency graph
requires:
  - phase: 04-game-loop-input
    provides: pymol_bridge thin-seam discipline, moved-tick bridge precedent (move_head_delta camera=0), probe M5 (get_object_ttt segfault)
  - phase: 03-molecules-in-viewer
    provides: load_molecule/cleanup_srp seams, proven get_names('public_objects') type
provides:
  - apply_matrix — thin cmd.transform_selection forwarder for pure-layer m16 (placement + edge-on orientation)
  - sweep_chain — ONE cmd.rotate per ('turning',) tick, explicit origin + camera=0 (rigid chain sweep, GAME-10 rendering)
  - zoom_chain, chain_object_names — completion framing + chain listing (GAME-09)
  - delete_pickups, rename_pickup — pickup lifecycle at capture/teardown (STACK-01)
  - REQUIRED smoke 07 (TRANSFORM/SWEEP/COMPLETION sentinels) pinning probes A1/B/C/G as live regression
affects: [05-10 edge-on materialization, 05-13 stacked capture, 05-14 turning sweep, 05-15 completion presenter]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Bridge placements: pure layer builds m16, bridge only forwards (TTT layout: y = R.(x+pre) + t)"
    - "Sweep = ONE cmd.rotate per tick with MANDATORY origin=[hx,hy,0] + camera=0; selection INCLUDES srp_head"
    - "Completion ordering: unlock_camera FIRST, then zoom_chain (set_view clobbers prior zooms, P5-3)"

key-files:
  created: [smoke/07_transform_sweep_smoke.py]
  modified: [serpentrum/pymol_bridge.py, tests/run_gates.py]

key-decisions:
  - "rename_pickup ships cmd.set_name (bog-standard naming.py, unprobed in research) — smoke 07 is its live verification; documented fallback = delete + load + apply_matrix"

patterns-established:
  - "Gp7 part 1 seams: every Phase-5 bridge function <= ~15 lines, docstring pins its own pitfall (origin=, camera=0, no get_object_ttt, zoom-after-unlock)"
  - "Smoke 07: INLINE 16-float probe-A1 fixture (no orientation import) so the RAW TTT layout stays pinned independent of plan 05-02's branch"

# Metrics
duration: 8 min
completed: 2026-09-15
---

# Phase 5 Plan 07: Bridge Primitives (Placement, Sweep, Completion) Summary

**Six verified-mechanism cmd seams wired into pymol_bridge (apply_matrix / sweep_chain / zoom_chain / delete_pickups / rename_pickup / chain_object_names), proven live by REQUIRED headless smoke 07 replicating probes A1 (1.2e-07 Å A1 fixture), B (6-tick rigid 90° sweep) and C/G (completion ops).**

## Performance

- **Duration:** 8 min
- **Started:** 2026-09-15T19:32:10Z
- **Completed:** 2026-09-15T19:40:13Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- G7 part 1 bridge primitives exist as thin cmd forwarders (matrix math stays in the pure layer); every docstring pins its own pitfall: TTT layout + get_object_ttt segfault ban (P5-2), MANDATORY origin=/camera=0 (P5-4), zoom AFTER unlock_camera (P5-3), pattern-delete scope (G4)
- sweep_chain rotates srp_head + all srp_seg_* rigidly about an explicit head pivot in ONE cmd.rotate per tick — CCW-positive sign matching engine _rotate_xy (probe B: <5e-07 Å distortion, ~0.4 ms/10 objects)
- REQUIRED smoke 07 registered in REQUIRED_SMOKES — the A1 matrix regression, rigid multi-tick sweep, and completion ops are now gate-required live proofs in headless Windows PyMOL (no re-spiking; mechanisms used as researcher-verified)
- Full gate green: `python3.6 tests/run_gates.py --smoke` → 7/7 required smokes pass

## Task Commits

Each task was committed atomically on branch `exec/05-07`:

1. **Task 1: bridge primitives** - `b556046` (feat)
2. **Task 2: REQUIRED smoke 07 + gate registration** - `a581e30` (test)

**Plan metadata:** (docs commit below, staged SUMMARY only)

## Files Created/Modified
- `serpentrum/pymol_bridge.py` — appended Phase-5 section: apply_matrix, sweep_chain, zoom_chain, delete_pickups, rename_pickup, chain_object_names (95 lines incl. pitfall docstrings)
- `smoke/07_transform_sweep_smoke.py` — REQUIRED headless smoke: TRANSFORM (inline probe-A1 RotZ90+t fixture, atom mapping ≤1e-4 Å), SWEEP (6×15° per-tick calls, centroids +90° CCW ≤1e-3, diameters unchanged ≤1e-3), COMPLETION (rename/list/zoom/pickup-delete), sentinel-flushed style of smoke 05
- `tests/run_gates.py` — smoke 07 added to REQUIRED_SMOKES tuple

## Decisions Made
- rename_pickup ships `cmd.set_name` (the bog-standard naming.py API, not probed during research): smoke 07's COMPLETION step verifies it live in the real runtime; the documented fallback (delete + load fresh + apply composed matrix) ships in the docstring only — no dead code
- Smoke 07 builds the probe-A1 m16 as an INLINE 16-float literal instead of importing `orientation.py` (plan 05-02, separate branch in this parallel wave) — the smoke pins the RAW TTT layout, which is exactly what a 05-02 bug would have to preserve
- Sweep verification uses the real per-tick pattern (SIX `sweep_chain(15.0, (0,0))` calls for a 90° turn) rather than one 90° rotate — matches what plan 05-14's ('turning',) tick consumer will do

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Stray non-ASCII artifact typed into smoke draft**
- **Found during:** Task 2 (smoke 07 authoring, self-review before first run)
- **Issue:** a two-character artifact corrupted an assert line in s_completion
- **Fix:** corrected the line before any gate/smoke run
- **Files modified:** smoke/07_transform_sweep_smoke.py
- **Verification:** `python3.6 -m py_compile` + full gate + headless smoke all green
- **Committed in:** a581e30 (Task 2 commit)

**2. [Rule 3 - Blocking] pymol_bridge.py read from main checkout instead of worktree before first edit**
- **Found during:** Task 1 (context loading)
- **Issue:** style-reference files were first read via the main-checkout path (same commit 58fe359); worktree rules require all repo work via tmp/exec-05-07
- **Fix:** re-read the file from the worktree path before editing; all subsequent reads/edits/commands worked from the worktree only
- **Files modified:** none (process correction only)
- **Verification:** all commits land on exec/05-07 (`git log --oneline` inside worktree)
- **Committed in:** n/a

---

**Total deviations:** 2 auto-fixed (1 bug — caught pre-commit, 1 process blocker)
**Impact on plan:** None on scope or behavior; plan executed verbatim otherwise.

## Issues Encountered
None — smoke 07 passed all three sentinels on the first headless run, and the full --smoke gate stayed green end-to-end (smoke 02 remains the known non-blocking informational FAIL from 01-05's offscreen dead end).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Unlocked consumers: 05-10 (edge-on materialization via apply_matrix), 05-13 ('stacked' capture via apply_matrix + rename_pickup), 05-14 ('turning' sweep rendering via sweep_chain), 05-15 (completion presenter via zoom_chain + chain_object_names + delete_pickups)
- The bridge contract is pinned live by a gate-required smoke, so later plans can wire gui_game against it without viewer re-verification
- Note this is G7 part 1 only: `place_object`-style SRP-segment attach helpers, if wanted as named seams, belong to the consumer plans (research lists capturing via rename as the shipping path)

---
*Phase: 05-stacking-game-rules*
*Completed: 2026-09-15*
