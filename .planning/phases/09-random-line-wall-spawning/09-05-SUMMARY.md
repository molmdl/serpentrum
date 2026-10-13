---
phase: 09-random-line-wall-spawning
plan: 05
subsystem: viewer-bridge
tags: [pymol, cgo, bridge, wall, purity, phase-9]

# Dependency graph
requires:
  - phase: 09-random-line-wall-spawning
    provides: cgo_build.wall_cgo (09-03 pure 4-edge LINES builder) + engine 2D wall endpoints (09-04)
provides:
  - "pymol_bridge.load_line_wall — thin CGO-load seam (engine 2D (x,y) @ +/-BOX_DISPLAY_Z -> named srp_wall CGO)"
  - "pymol_bridge.delete_walls — idempotent srp_wall* pattern delete for _teardown_round + cleanup_srp recovery"
  - "WALL_NAME / DEFAULT_WALL_COLOR / DEFAULT_WALL_LINEWIDTH constants"
affects: [09-07, 09-08]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "CGO channel thin-seam: pure builder in cgo_build, cmd-calling load/delete only in the BRIDGE, no gameplay math in the bridge"
    - "Pattern-delete hygiene: 'srp_wall*' (no exists-guard) mirrors delete_pickups; swept by cleanup_srp / .pse recovery (INFRA-04)"

key-files:
  created: []
  modified: [serpentrum/pymol_bridge.py]

key-decisions:
  - "Wall name 'srp_wall' singular-object precedent (srp_box/srp_head/srp_mode_vec); policy-agnostic name= kwarg mirrors load_mode_arrows"
  - "Delete pattern 'srp_wall*' (NOT 'srp_wall_*') so both the singular and any future indexed srp_wall_<n> form die; pattern delete has no exists-guard (guard is for single-name deletes only)"
  - "Replace semantics live in the CALLER (delete-then-load) per the 07-09 load_mode_arrows contract — the bridge function itself is one load"
  - "DEFAULT_WALL_COLOR (1.0, 0.0, 0.0) pure red (hazard, maximally distant from the warm-orange box); DEFAULT_WALL_LINEWIDTH 3.0 (e8b3a9d human-verified visibility floor)"

patterns-established:
  - "Bridge correctness for the wall channel is headless-proven by smoke 15 (09-08), NOT WSL unit tests — the module does module-level `from pymol import cmd` and is not importable under WSL python3.6"

# Metrics
duration: ~7min
completed: 2026-10-13
---

# Phase 9 Plan 05: Bridge Wall Channel Summary

**Thin PyMOL bridge wall channel — `load_line_wall` reads engine-owned 2D (x, y) endpoints, derives the display z band via ±BOX_DISPLAY_Z (the load_box precedent) and loads one named `srp_wall` CGO; `delete_walls` is the idempotent `srp_wall*` pattern-delete teardown/recovery primitive.**

## Performance

- **Duration:** ~7 min
- **Started:** 2026-10-13T04:16:14Z
- **Completed:** 2026-10-13
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments
- Added the Phase 9 wall viewer channel to `serpentrum/pymol_bridge.py`: `WALL_NAME = 'srp_wall'`, `DEFAULT_WALL_COLOR = (1.0, 0.0, 0.0)`, `DEFAULT_WALL_LINEWIDTH = 3.0`, `load_line_wall(...)`, `delete_walls()`.
- `load_line_wall` turns the engine's 2D endpoints into a floor-to-ceiling fence: `cgo_build.wall_cgo((p1[0], p1[1], -BOX_DISPLAY_Z), (p2[0], p2[1], BOX_DISPLAY_Z), color, linewidth)` loaded with `cmd.load_cgo(..., name, zoom=0)`, returns `name`. The on-screen projection under the locked camera equals the 2D collision segment; the z band keeps it reading as a wall from any post-unlock angle.
- `delete_walls()` does `cmd.delete('srp_wall*')` — pattern delete, idempotent by construction, no exists-guard; covers `srp_wall` and any indexed `srp_wall_<n>` form; safe on a fresh scene and swept again by `cleanup_srp` on restart/.pse recovery (INFRA-04).
- Zero new imports (`cmd`, `cgo_build`, `BOX_DISPLAY_Z` already module-level) and zero edits to any existing seam (`load_box` / `delete_pickups` / `delete_object` / `cleanup_srp` untouched).

## Task Commits

The plan specifies a single wave-2 commit for the whole channel (Task 1 code + Task 2 scope sanity):

1. **Task 1 + 2: wall viewer channel — constants + load_line_wall + delete_walls** - `9b00adc` (feat)

**Plan metadata:** (docs commit created after this SUMMARY)

## Files Created/Modified
- `serpentrum/pymol_bridge.py` - +40 lines, 0 deletions: Phase 9 wall channel (3 constants + 2 thin cmd-calling functions) added symbol-anchored after `load_mode_arrows` (the CGO-load seam).

## Decisions Made
- **Name/pattern:** `'srp_wall'` singular-object precedent; delete pattern `'srp_wall*'` (not `'srp_wall_*'`) so both naming forms are swept. Policy-agnostic `name=` kwarg mirrors `load_mode_arrows` — the accumulating-walls alternative would name-arg `srp_wall_<n>`, still swept.
- **Replace contract in the caller:** `load_line_wall` performs exactly one load; delete-then-load replace semantics stay with the caller (07-09 `load_mode_arrows` contract).
- **No exists-guard on the pattern delete:** guarded deletes are for SINGLE names (`delete_object`); pattern-deletes are idempotent by construction (the `delete_pickups` template).
- **Colors/width:** pure red `(1.0, 0.0, 0.0)` = hazard, maximally distant from the warm-orange box; linewidth 3.0 = the e8b3a9d human-verified visibility floor (box-parity thickness).
- **No gameOver-seams:** walls are static CGOs; zero wall calls per movement tick (the one-call-per-tick budget untouched); `srp_wall*` matches no chain wildcard (`'srp_head or srp_seg_*'`).

## Channel contract (frozen iteration surface)

- `load_line_wall(p1_xy, p2_xy, color=DEFAULT_WALL_COLOR, linewidth=DEFAULT_WALL_LINEWIDTH, name=WALL_NAME) -> name`
- `delete_walls() -> None` (`cmd.delete('srp_wall*')`)
- Constants: `WALL_NAME='srp_wall'`, `DEFAULT_WALL_COLOR=(1.0,0.0,0.0)`, `DEFAULT_WALL_LINEWIDTH=3.0`
- Viewer-read discipline: **zero gameplay math in the bridge** — endpoints in, CGO out; the engine owns the 2D truth and the bridge owns only the display z band (`±BOX_DISPLAY_Z`).

## Where correctness is proven

`pymol_bridge.py` is **NOT WSL-unit-testable** — it does module-level `from pymol import cmd` (module docstring :12-19). Its correctness for this channel is therefore proven **headless in Windows PyMOL by the 09-08 smoke 15**, whose STAGE1/2/5/6 exercise exactly these two functions (load + pattern-delete, z-band derivation, idempotent teardown). WSL gates here prove only syntax + purity + the untouched unit suite.

## Deviations from Plan

None - plan executed exactly as written. The code block was transcribed verbatim; the channel was committed as the single wave-2 commit named in the objective (Task 1 and Task 2 share `9b00adc`, per the plan's "Single wave-2 commit" directive rather than one commit per task).

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Iteration surface for **09-07** (GUI caller: `_teardown_round` calls `delete_walls()`; the wall-load caller stores/ignores the returned name) and **09-08** (smoke 15) is frozen.
- Zero purity/allowlist/registry churn — `pymol_bridge` remains BRIDGE-class, no `tools/check_purity.py` edits needed.
- Gates: `python3.6 tests/run_gates.py` green — 1040 unittests, gate 1 (syntax + plugin-path safety) PASS, gate 2 (AST purity) PASS, gate 3 (scoped unittest discover) PASS. Test count unchanged at 1040 (nothing imports the new channel yet).

---
*Phase: 09-random-line-wall-spawning*
*Completed: 2026-10-13*
