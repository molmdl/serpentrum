---
phase: 09-random-line-wall-spawning
plan: 03
subsystem: viewer-geometry
tags: [cgo, lines, pure-builder, wall, pymol, tdd]

# Dependency graph
requires:
  - phase: 09-random-line-wall-spawning
    provides: "09-RESEARCH-viewer-bridge.md sec.1.1/2.1 (box_cgo template, fence geometry, locked p1-bottom/p2-top argument shape, pinned edge order, LINES-only decision) + the pre-v1 serpentrum/cgo_build.py box builder + local opcode-constant contract (GATE V verified, module auto-PURE)"
provides:
  - "wall_cgo(p1, p2, color, linewidth) pure CGO builder -- a 42-float 4-edge vertical LINES fence from two OPPOSITE corners (p1 = one endpoint's BOTTOM 3D corner, p2 = the other endpoint's TOP 3D corner)"
  - "TestWallCgo regression pins (6 tests): 42-float structure, all-floats, pinned vertex order recovered through the UNMODIFIED _OPERANDS mini interpreter, single-header color/linewidth propagation, box_cgo-parity builder defaults, generic asymmetric z band + horizontal + degenerate zero-length walls"
affects: [09-05 bridge (load_line_wall feeds wall_cgo with +-BOX_DISPLAY_Z + pure-red DEFAULT_WALL_* constants), 09-08 REQUIRED smoke 15 (WALL-LOADED/WALL-REPLACE extent assertions), Phase 9 closing human feel-check (wall visibility)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "corner-args fence derivation: p1=(x1,y1,z_bot) + p2=(x2,y2,z_top) -> four fence corners; box_cgo's single-header LINES protocol reused verbatim -- only the edge count differs (12 -> 4)"

key-files:
  created: []
  modified:
    - serpentrum/cgo_build.py
    - tests/test_cgo_build.py

key-decisions:
  - "Argument shape locked by the planner (bridge research 2.4 note), NOT revisited here: p1 = (x1, y1, z1) one endpoint's BOTTOM corner, p2 = (x2, y2, z2) the OTHER endpoint's TOP corner; the BRIDGE owns the +-BOX_DISPLAY_Z call (load_box precedent, pymol_bridge.py:104-105)"
  - "Edge order pinned: (p1_bot->p2_bot), (p2_bot->p2_top), (p2_top->p1_top), (p1_top->p1_bot) -- a parallelogram of 4 LINES edges"
  - "Builder defaults mirror box_cgo's kwargs exactly (color=(1.0, 0.4, 0.1), linewidth=2.0); the pure-red (1.0, 0.0, 0.0) / 3.0 constants live in the BRIDGE (09-05), not here"
  - "LINES-only output -- no TRIANGLE_STRIP, no new opcodes, no pymol.cgo import -- so the stream parses under the existing test mini interpreter with ZERO harness changes"
  - "REFACTOR phase skipped (plan-sanctioned): the ~40-line builder mirrors box_cgo's idioms exactly; a shared emitter helper would touch the frozen box surface for zero behavioral gain"

patterns-established:
  - "Wall fence stream = [LINEWIDTH, w, BEGIN, LINES, COLOR, r, g, b] + N x [VERTEX, x,y,z, VERTEX, x,y,z] + [END, STOP] -- identical float protocol to box_cgo (42 floats at N=4)"

# Metrics
duration: 6 min
completed: 2026-10-12
---

# Phase 9 Plan 3: wall_cgo Builder Summary

**Pure 42-float wall_cgo CGO builder -- a floor-to-ceiling 4-edge LINES fence between two opposite corners whose locked-camera projection equals the engine's 2D wall collision segment; parses under the unmodified mini CGO interpreter.**

## Performance

- **Duration:** 6 min (369 s)
- **Started:** 2026-10-12T19:36:39Z (UTC)
- **Completed:** 2026-10-12T19:42:48Z (UTC; dev shell is HKT -- git commit dates authoritative per repo convention)
- **Tasks:** 1 TDD feature (RED -> GREEN; REFACTOR skipped, plan-sanctioned)
- **Files modified:** 2

## Accomplishments

- `wall_cgo(p1, p2, color, linewidth)` added beside `box_cgo` in `serpentrum/cgo_build.py` (module stays auto-PURE: stdlib only, zero new imports, zero new opcodes, existing local constants only)
- Emits exactly **42 floats**: 8-float header `[LINEWIDTH, w, BEGIN, LINES, COLOR, r, g, b]` + 4 edge blocks `[VERTEX, ax, ay, az, VERTEX, bx, by, bz]` in the pinned parallelogram order + `[END, STOP]` trailer -- the box_cgo float protocol with 4 edges instead of 12
- `TestWallCgo` (6 tests) proves LINES-stream compatibility with **ZERO harness changes**: the untouched `_OPERANDS` mini interpreter recovers the 8 pinned vertices in the pinned order; color/linewidth ride the single header; defaults match box_cgo's kwargs; asymmetric z bands ([-3, 7]), horizontal (dy=0) and degenerate zero-length walls all build valid streams
- Scoped suite 21 -> 27 green with prior classes UNMODIFIED; full default gate sweep green at **1004 unittests** (998 baseline + 6 new); AST purity gate green (zero allowlist edits)

## Task Commits

Each TDD phase was committed atomically:

1. **RED: failing TestWallCgo structure + interpreter pins** -- `dfc05bd` (test)
2. **GREEN: pure wall_cgo 4-edge LINES fence builder** -- `c625189` (feat)
3. REFACTOR: skipped (see key-decisions)

**Plan metadata:** `docs(09-03)` commit (this SUMMARY's own commit)

## Files Created/Modified

- `serpentrum/cgo_build.py` -- `wall_cgo` builder beside `box_cgo` (def at :137); module docstring public-builders list gains the wall_cgo entry ("Four public builders", :41); +78/-2
- `tests/test_cgo_build.py` -- additive `TestWallCgo` class (122 lines, min_lines 60 satisfied; zero edits to `_OPERANDS`/`_interpret_cgo`/`_vertex_triples` or any pre-existing class)

## Decisions Made

None beyond the plan's locked contracts -- implemented exactly as specified (all locked decisions honored verbatim; see key-decisions frontmatter for the record: corner-args shape, pinned edge order, box-parity defaults with pure-red deferred to the bridge, LINES-only for zero harness changes, REFACTOR skipped).

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- **Plan verification bullet `grep -n "TRIANGLE\|pymol" serpentrum/cgo_build.py` says "ZERO hits" -- literally unachievable at baseline.** The pre-existing module docstrings/comments and the verified constant table legitimately contain both words (12 baseline hit lines: the "WHY LOCAL CONSTANTS (not `from pymol import cgo`)" traceability doc, the value-collision note, and the `TRIANGLES`/`TRIANGLE_STRIP` constant definitions with their cgo.py line citations), and the plan's own implementation section *requires* a wall_cgo docstring sentence naming TRIANGLE_STRIP (added at :163-164). The parenthetical intent -- "(LINES-only, no pymol import)" -- was verified substantively instead:
  1. zero added `import`/`from` lines in the diff (module still imports only stdlib `math`);
  2. wall_cgo emits only the LINES-family opcodes -- proven by the 6 new tests parsing through the UNMODIFIED interpreter, whose `_OPERANDS` table has no 5.0 (TRIANGLE_STRIP) entry, so any filled-triangle emission would fail every parse test;
  3. gate 2 (AST purity) green: pymol/Qt/numpy nowhere in cgo_build.py.
  Hits are documentation vocabulary, not usage. No code change needed.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `wall_cgo` is ready for the 09-05 bridge: `load_line_wall` passes `(p1_xy[0], p1_xy[1], -BOX_DISPLAY_Z)` / `(p2_xy[0], p2_xy[1], BOX_DISPLAY_Z)` plus the pure-red `DEFAULT_WALL_COLOR = (1.0, 0.0, 0.0)` / `DEFAULT_WALL_LINEWIDTH = 3.0` constants (decided there, not here)
- The z band comes from the corner args (no hardcoded +-5), so the bridge's display-depth call is all a wall needs to span floor-to-ceiling like the box
- For smoke 15 (09-08): `cmd.get_extent` on a LINES-only CGO remains the research-flagged verify-at-execution point (bridge research sec.3.2); the pure WSL pins here (exact 42 floats, pinned vertices) are the fallback evidence
- Test baseline moved 998 -> 1004 across this plan (+6). No blockers.

---
*Phase: 09-random-line-wall-spawning*
*Completed: 2026-10-12 (UTC)*
