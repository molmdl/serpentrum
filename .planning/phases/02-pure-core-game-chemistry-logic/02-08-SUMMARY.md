---
phase: 02-pure-core-game-chemistry-logic
plan: 08
subsystem: rendering (pure CGO construction)
tags: [cgo, geometry, box-edges, mode-arrows, spheres, pure-python, py36, local-constants, float-list, bridge-facing]

# Dependency graph
requires:
  - phase: 01-plugin-skeleton-purity-harness
    provides: run_gates harness + AST purity gate, test conventions (sys.path
      self-insert preamble, discovery without `-t .`, no __init__.py in tests/),
      py3.6 syntax discipline, plugin-path safety
provides:
  - serpentrum/cgo_build.py: 15 LOCAL CGO opcode constants (float literals from
    verified cgo.py:21-65; NO VERSION; LOCAL because pymol.cgo imports
    `from pymol import cmd` at module level — purity violation)
  - box_cgo(min, max, color, linewidth) -> 106-float 12-edge LINES stream
    (STACK.md §3 displayed boundary; explicitly enumerated c000..c111 corners)
  - mode_arrows(atoms, vecs, scale, color, base_radius, length_a) -> CYLINDER(14)
    + CONE(17) per nonzero vector (SPECTRA-05 static displacement arrows;
    v_hat normalized before scaling; 0.7 shaft fraction; <1e-6 skipped;
    CONE two-radii + flat caps)
  - spheres_cgo(points, radius, color) -> [COLOR] + [SPHERE,x,y,z,r] per point
    + [STOP] (GAME-03 head rendering)
  - tests/test_cgo_build.py: 21 structural tests via mini CGO-stream interpreter
    (opcode→operand-count walk) + exact arithmetic checks
affects: [02-14-pure-integration, phase-5-ui, phase-8]

# Tech tracking
tech-stack:
  added: []   # zero — stdlib math only; no new libraries
  patterns:
    - "Local CGO constants (Pattern: never import pymol.cgo — it pulls cmd at module level; use verified float literals)"
    - "CGO stream = flat float list; opcodes and operands interleaved; value collisions (4.0=VERTEX/TRIANGLES) resolved by single-interpretation mapping in the test interpreter"
    - "Mini CGO interpreter in tests: walk (opcode, operand_count) pairs — no PyMOL needed for structural verification"
    - "CONE layout: opcode + 16 floats (two radii base/tip + two color triplets + two cap flags); flat caps = 1.0"
    - "Direction normalization BEFORE scaling: v_hat = v/|v|, then shaft_end = p + v_hat*scale*length_a*0.7, tip = p + v_hat*scale*length_a"

key-files:
  created:
    - serpentrum/cgo_build.py
    - tests/test_cgo_build.py
  modified: []

key-decisions:
  - "Constants are LOCAL float literals (not imported from pymol.cgo) because pymol/cgo.py executes `from pymol import cmd` at module level (cgo.py:79-156), which would violate INFRA-02 purity AND drag the GUI runtime into pure-land"
  - "NO VERSION constant defined — verified pymol/cgo.py has none; the research question's list included it in error; its absence is asserted in tests"
  - "box_cgo emits LINES edges (not TRIANGLE_STRIP faces) per STACK.md §3 boundary decision — edges need no normals"
  - "CONE uses flat caps (1.0) for arrow tips — cCylCap Flat=1, Basis.h:41-46"
  - "Mini interpreter maps each opcode VALUE to a single operand count, resolving value collisions (e.g. 4.0→VERTEX not TRIANGLES) because our builders only emit one interpretation per value"
  - "box_cgo total = 106 floats (8 header + 96 vertex + 2 footer); plan stated 90 (arithmetic error: forgot VERTEX opcodes in edge count) — implemented correct 106 per positional test checks"
  - "Empty spheres_cgo = 5 floats ([COLOR,r,g,b,STOP]); plan stated 4 (forgot STOP) — implemented correct 5"

patterns-established:
  - "CGO builder pattern: pure function → flat float list → verified by mini interpreter (no PyMOL needed)"
  - "Explicit corner enumeration for box edges (no loops that could reorder); standard edge order: bottom rect, top rect, verticals"

# Metrics
duration: ~15min
completed: 2026-09-09
---

# Phase 02 Plan 08: CGO Build Summary

**Pure CGO float-list builders (box edges, vibrational mode arrows, spheres) with 15 LOCAL opcode constants — no pymol.cgo import, verified by a mini CGO-stream interpreter**

## Performance

- **Duration:** ~15 min
- **Tasks:** 2
- **Files modified:** 2 (both created)
- **Tests added:** 21 (9 constants/box + 12 mode_arrows/spheres)

## Accomplishments
- 15 LOCAL CGO opcode constants as float literals matching verified cgo.py:21-65 (NO VERSION constant; NO pymol.cgo import — purity preserved)
- box_cgo: 12-edge LINES stream from two corners, explicitly enumerated c000..c111, each corner appears exactly 3 times (106 floats)
- mode_arrows: CYLINDER(14) shaft + CONE(17, two radii + flat caps) per nonzero displacement vector; direction normalized before scaling; vectors < 1e-6 skipped
- spheres_cgo: COLOR header + [SPHERE, x,y,z,r] per point + STOP
- Mini CGO-stream interpreter in tests: walks (opcode, operand_count) pairs, resolves value collisions, asserts no trailing garbage / unknown opcodes
- All gates green (188 tests total); purity clean; stdlib `math` only

## Task Commits

Each task was committed atomically:

1. **Task 1: local CGO constants + box_cgo builder + structural tests** - `722d5b5` (feat)
2. **Task 2: mode_arrows + spheres_cgo + full verification** - `887d0c5` (feat)

**Plan metadata:** (pending — `docs(02-08): complete plan`)

## Files Created/Modified
- `serpentrum/cgo_build.py` (235 lines) — 15 local CGO constants, box_cgo, mode_arrows, spheres_cgo; stdlib math only; PURE
- `tests/test_cgo_build.py` (406 lines) — mini CGO interpreter + 21 structural/arithmetic tests

## Decisions Made
- **Local constants (not pymol.cgo):** pymol/cgo.py executes `from pymol import cmd` at its module level (cgo.py:79-156); importing it would violate INFRA-02 purity and drag the GUI runtime into pure-land. Constants are verified float literals.
- **No VERSION constant:** verified pymol/cgo.py has none; research question listed it in error; absence asserted in tests.
- **LINES edges for box (not faces):** per STACK.md §3 boundary decision; edges need no normals.
- **CONE flat caps (1.0):** cCylCap Flat=1 (Basis.h:41-46) for arrow tips.
- **Mini interpreter single-interpretation mapping:** each opcode VALUE maps to one operand count in the test interpreter, resolving intrinsic CGO value collisions (4.0=VERTEX/TRIANGLES, 3.0=END/LINE_STRIP) because our builders emit only one interpretation per value.

## Deviations from Plan

### Plan Arithmetic Corrections (no code deviation — plan text errors)

**1. box_cgo total length: plan said 90, actual is 106**
- **Found during:** Task 1 (test writing)
- **Issue:** Plan stated "Total length = 4 + 12*7 + 2 = 90 floats" — the "12*7" counted each edge as 7 floats but each edge is actually [VERTEX, x,y,z, VERTEX, x,y,z] = 8 floats (two VERTEX opcodes). The "4" header also didn't match the 8-float header [LINEWIDTH, w, BEGIN, LINES, COLOR, r, g, b] required by the plan's own positional checks (floats[2]==BEGIN, floats[3]==LINES, floats[4]==COLOR, floats[5:8]==color).
- **Fix:** Implemented the correct 106-float stream (8 header + 96 vertex + 2 footer) per the positional checks, which are self-consistent and authoritative.
- **Verification:** `test_structure_and_length` asserts `len(stream) == 106` and all positional indices; interpreter parses cleanly.

**2. Empty spheres_cgo length: plan said 4, actual is 5**
- **Found during:** Task 2 (test writing)
- **Issue:** Plan stated "empty points -> [COLOR, ..., STOP] length 4" but [COLOR, r, g, b, STOP] = 5 floats (forgot to count STOP).
- **Fix:** Implemented correct 5-float empty stream; `test_empty_points` asserts `len(stream) == 5`.
- **Verification:** Interpreter parses cleanly; record count asserts 0 SPHERE records.

---

**Total deviations:** 2 plan-text arithmetic corrections (no code deviations — plan's structural specifications were followed; only the stated totals had arithmetic errors)
**Impact on plan:** Zero scope creep. The builders match the plan's positional/structural specifications exactly; only the plan's stated total-length numbers were corrected to match reality.

## Issues Encountered
None — the CGO value-collision issue (multiple opcodes sharing the same float value) was anticipated by the plan and resolved cleanly with the single-interpretation interpreter mapping.

## User Setup Required
None — no external service configuration required. Pure stdlib module.

## Next Phase Readiness
- cgo_build.py is the bridge-facing PURE half of the rendering stack; the Phase-5 GUI connector will pass these float lists to `cmd.load_cgo`.
- All three builders return plain float lists verifiable without PyMOL — the mini interpreter proves structural correctness.
- No blockers. The CONE/CYLINDER/SPHERE layouts are C-source verified and locked.
- Forward: 02-14 pure integration may compose these builders with other Phase-2 modules; the float-list contract is stable.

---
*Phase: 02-pure-core-game-chemistry-logic*
*Completed: 2026-09-09*
