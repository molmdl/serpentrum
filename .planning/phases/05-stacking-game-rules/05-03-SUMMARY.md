---
phase: 05-stacking-game-rules
plan: 03
subsystem: pure-core
tags: [python3.6, tdd, pure-module, spawn-policy, crc32, determinism, unittest]

requires:
  - phase: 02-pure-core-game-chemistry-logic
    provides: GameEngine pickup record contract (id/centroid/atoms/atoms_n REQUIRED, 02-13 sweep pickup leg), BOX_PRESETS, randomize_head private-random.Random(seed) precedent, SWEEP_PICKUP_CLEARANCE_A 2.5 A
  - phase: 03-molecules-in-the-viewer-setup-tab
    provides: setloader.load_demo_set / default_stacking_path (anchored records incl. '__upload__' skip keying)
provides:
  - serpentrum/spawn.py (PURE, stdlib math/zlib/random): PickupSpawner — seeded, cyclic, clearance-validated spawn policy (gap G3)
  - seed_from_setup(setup): process-stable zlib.crc32 canonical-string seed (restart determinism)
  - build_pickup_seed(record, pid, centroid, atoms): the engine pickup dict feeder for GameEngine(pickups=...)
  - tests/test_spawn.py: 14 pins (determinism, bounds, clearances, cycle-wrap, pid/counter advance, seed shape, exhaustion)
affects: [05-11 (gui_game begin_game seeds GameEngine(pickups=...) and materializes srp_pickup_* objects from these results), 05-12 (pure integration chain consumes spawn seeds)]

tech-stack:
  added: []
  patterns:
    - "Private random.Random(seed) per stateful object (never the global random module) — extends the setup_logic.randomize_head precedent from one-shot draws to a stateful spawner"
    - "Seed via zlib.crc32 of a canonical sorted '%s=%r' string — NEVER hash() (PYTHONHASHSEED randomizes str hashes per process); cross-process stability pinned by a subprocess test"
    - "Spawn-policy state (cycle index, pid counter) advances ONLY on a returned spawn — exhaustion (None) replays the same record + pid next call"

key-files:
  created:
    - serpentrum/spawn.py
    - tests/test_spawn.py
  modified: []

key-decisions:
  - "PINNED POLICY in spawn.py docstring: one new spawn per resolution, MAX_LIVE_PICKUPS=4 ceiling, cyclic records wrap, lookahead 8.0 + seeded lateral ±6.0 @ 0.1 quantization, margins 3.5/5.0/3.0-atom/6.0, 32 seeded retries then deterministic grid scan (step 2.0, x-major/y-minor, first legal), crc32 seed, uploads spawn and skip at capture"
  - "Chain atoms use the engine (sym, x, y, z) shape; clearance math is xy-only (z is display-only, display side of the 2D game plane)"
  - "Heading names mirrored privately (_DIRS) — spawn.py stays fully decoupled from game_engine (no engine/orientation/molfile imports; caller passes atoms_by_id)"

duration: ~7 min
completed: 2026-09-15
---

# Phase 5 Plan 03: Deterministic Seeded Pickup Spawn Policy Summary

**Closed gap G3 with a PURE `PickupSpawner` (seeded via process-stable crc32, cyclic record order, lookahead+lateral candidates validated against wall/head/chain-atom/live-pickup clearances, 32-retry + deterministic grid-scan fallback, bounded by a 4-pickup live ceiling) plus the `build_pickup_seed` engine-contract feeder — 14 TDD pins, full gates green (465 tests).**

## Performance

- **Duration:** ~7 min
- **Started:** 2026-09-15T18:33:53Z
- **Completed:** 2026-09-15T18:39:52Z
- **Tasks:** 1 feature (TDD RED → GREEN cycle)
- **Files modified:** 2 (2 created, 0 modified)

## Accomplishments

- `PickupSpawner.first/next_after` — one new spawn per resolution: candidate = head + heading·8.0 + perp·(seeded lateral in ±6.0 Å, 0.1-quantized), validated against four legs (wall margin 3.5 Å shrunk box, head-centroid ≥ 5.0 Å, chain-ATOM ≥ 3.0 Å using the candidate-translated origin-centered atoms of the cycle-current record — keeps the engine's 2.5 Å sweep pickup-leg satisfiable near fresh spawns, live-pickup-centroid ≥ 6.0 Å). Up to 32 seeded draws, then a deterministic grid-scan fallback (step 2.0, x-major/y-minor, first legal), else `None` with NO state advance (same record + same pid replayed next call).
- Cyclic molecule order: records in anchored list order, wrapping forever (set_a's 5 species vs cap default 10 requires reuse — probe-verified clash-safe); uploads cycle exactly like demo records (honest STACK-03 pedagogy — skip at capture is the controller's job, not the spawner's).
- `seed_from_setup(setup)` — `zlib.crc32` over the canonical sorted `'%s=%r'` string; cross-process stability pinned by a real subprocess test (NEVER `hash()` — PYTHONHASHSEED would break GAME-07 restart determinism).
- `can_spawn(live_count)` — the MAX_LIVE_PICKUPS = 4 ceiling gate so refusal-lingering pickups cannot accumulate unbounded.
- `build_pickup_seed(record, pid, centroid, atoms)` — the exact engine pickup dict (`id`/`molecule_id`/`centroid`/copied translated atoms/`atoms_n`), decoupled: spawn.py imports nothing from game_engine/orientation/molfile.

## Task Commits

TDD cycle, committed atomically:

1. **Task 1 RED: failing tests for the spawn policy pins** — `62cd565` (test)
2. **Task 2 GREEN: implement serpentrum/spawn.py** — `e20b894` (feat)

**Plan metadata:** see below (docs: complete spawn policy plan)

## Files Created/Modified

- `serpentrum/spawn.py` — PURE spawn policy: PickupSpawner, seed_from_setup, build_pickup_seed, pinned policy constants (MAX_LIVE_PICKUPS=4, LOOKAHEAD_A=8.0, LATERAL ±6.0 @ 0.1, margins 3.5/5.0/3.0/6.0, MAX_DRAWS=32, GRID_STEP_A=2.0)
- `tests/test_spawn.py` — 14 tests across 6 classes (seed stability incl. subprocess, determinism, geometry/clearances, cycle+ids+gate, pickup-seed contract, exhaustion/no-advance), built on real set_a demo records + origin-centered synthetic atoms

## Decisions Made

- Kept spawn.py fully decoupled: private `_DIRS` mirror of the four axis headings instead of importing game_engine (plan mandate); caller supplies `atoms_by_id` so no molfile/setloader imports either.
- Perpendicular convention fixed as CCW `(-uy, ux)` — a single documented convention captured in the seed stream is all determinism needs; pinned by the 'right'→ahead (x > 0) test.
- Chain atoms and candidate atoms use the engine's `(sym, x, y, z)` shape (xy compared; z is display-only) so gui_game can pass engine segment atoms directly (research: engine seeds carry atoms + unknown keys through).

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. RED verified as ImportError on `serpentrum.spawn`; GREEN passed all 14 tests on the first implementation run; full gate suite green immediately after (gate 3 was red only between the RED and GREEN commits, the expected TDD shape — commit `62cd565` precedent: `9687ed9`).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Ready for 05-11 (gui_game begin_game): `spawner = PickupSpawner(records, *BOX_PRESETS[preset], seed_from_setup(setup), atoms_by_id)` → `first()` seeds, each capture resolution ('stacked' success OR refusal) calls `next_after(head, heading, chain_atoms, live_centroids)` gated by `can_spawn(len(live))`; `build_pickup_seed` output feeds `GameEngine(pickups=...)` (extra carried keys like `stack_ring` survive engine copies).
- The one-spawn-per-resolution policy and the 4-live ceiling mean restart with the same setup reproduces the identical spawn stream — GAME-07 determinism extends across processes via crc32.
- No blockers for sibling plans; this plan touched only its two declared files.

---
*Phase: 05-stacking-game-rules*
*Completed: 2026-09-15*
