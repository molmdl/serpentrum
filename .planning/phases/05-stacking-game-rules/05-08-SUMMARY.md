---
phase: 05-stacking-game-rules
plan: 08
subsystem: api
tags: [setloader, stack_ring, ring_cycle, stacking, molfile, pure-module]

# Dependency graph
requires:
  - phase: 05-stacking-game-rules (plan 05-01)
    provides: molfile.ring_cycle — canonical ONE-ring 6-cycle extractor in ring-walk order
  - phase: 03-molecules-setup (plans 03-04/03-05)
    provides: setloader._build_record/load_demo_set/load_upload, '__upload__' skip-policy keying, manifest ring_atoms (sorted 2-core)
provides:
  - stack_ring computed at load time on every accepted demo record (canonical 6-cycle in ring-walk order, locked decision 5)
  - tests/test_setloader_stack_ring.py — carry-through pins for demo + upload records and the 1:1 indices alignment contract
affects: [05-05 placement seam (stack_ring skip condition), 05-10/05-11 head+pickup materialization and begin_game (stack_ring indexes atoms 1:1), 05-13 tail frames (ring_frame(seg atoms, seg stack_ring))]

# Tech tracking
tech-stack:
  added: []
  patterns: [load-time attachment of derived ring data on records — engine copies/sweeps carry unknown keys through, so the attachment survives the whole game]

key-files:
  created: [tests/test_setloader_stack_ring.py]
  modified: [serpentrum/setloader.py]

key-decisions:
  - "stack_ring computed AFTER gate/mismatch checks in load_demo_set — only accepted molecules pay the ring_cycle cost"
  - "uploads omit stack_ring BY DESIGN (not computed) — the skip policy keys on the absent ring (locked decisions 5 + 7)"

patterns-established:
  - "_build_record optional-key pattern: keyword default None + 'if not None: record[key] = list(value)' (ring_atoms precedent, now stack_ring)"

# Metrics
duration: 5min
completed: 2026-09-16
---

# Phase 5 Plan 08: setloader stack_ring carry on demo records Summary

**Demo records now ship with the canonical placement ring at load time: `_build_record` carries `stack_ring = molfile.ring_cycle(...)` (the ONE-ring 6-cycle in ring-walk order) on every accepted Set A record, while uploads stay ring-less by design — the dataset-side indexing contract that placement and tail frames consume is complete.**

## Performance

- **Duration:** 5 min
- **Started:** 2026-09-16T18:53:20Z
- **Completed:** 2026-09-16T18:58:20Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Every accepted demo record carries `stack_ring` — a list of exactly 6 ints equal to the plan-05-01-pinned canonical cycle per molecule (benzene (0,1,3,5,4,2); naphthalene (0,1,3,7,6,2); anthracene (0,1,5,3,2,4); phenanthrene (0,1,3,5,4,2); biphenyl (0,2,6,10,8,4)), computed from the SAME parsed record `_build_record` consumes (bonds + coords from one parse = the 1:1 indices alignment contract).
- Upload records NEVER carry `stack_ring` (single SDF, multi-record split, and mol2 paths pinned) — `__upload__` skip-policy keying intact; research skip-taxonomy row 4 stays reserved for future non-upload sets without 6-rings.
- `ring_atoms` (the manifest's sorted 2-core) coexists alongside `stack_ring` on demo records; validation order and error strings untouched (test_setloader.py green unmodified, 521 baseline tests pass).

## Task Commits

Each task was committed atomically:

1. **Task 1: stack_ring carry in _build_record + wiring** — `3d8d49f` (feat)
2. **Task 2: pinning tests** — `e80b03f` (test)

**Plan metadata:** `docs(05-08)` commit follows this SUMMARY.

## Files Created/Modified
- `serpentrum/setloader.py` — `_build_record` gains `stack_ring=None` keyword (same pattern as `ring_atoms=None`); `load_demo_set` computes `molfile.ring_cycle(record)` after gate/mismatch checks and passes it through; `load_upload` passes nothing (omission by design); module + function docstrings updated (record-key list, algorithm step 4, alignment contract).
- `tests/test_setloader_stack_ring.py` — 8 pinning tests: zero-error shipped-set load; six-int list shape + uniqueness; canonical tuple per molecule id; indices alignment vs re-parsed coords/elements (max(stack_ring)+1 <= len(coords)); ring_atoms/stack_ring coexistence + subset check; upload ring-absence on single SDF (built from fixture bytes in a tempdir), multi-record split, and mol2 paths.

## Decisions Made
- `stack_ring` is computed AFTER the gate and manifest cross-verification checks (only accepted molecules pay the cost; rejected molecules never reach ring extraction) — placed as step 4 of load_demo_set's pipeline, per plan.
- Upload omission is non-computation, not post-hoc deletion: `load_upload` never calls `ring_cycle`, so the absent ring is both the skip signal and zero wasted work.

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness
- 05-05 placement seam can key skip row 4 ("no planar aromatic 6-ring found") on the absent `stack_ring`; 05-10/05-11 can index `record['stack_ring']` 1:1 into parsed coords for head/pickup materialization; 05-13 tail frames recompute `ring_frame(seg atoms, seg stack_ring)` — engine unknown-key passthrough means the load-time attachment survives copies and sweeps.
- No blockers; gates green throughout (521 → 529 tests).

---
*Phase: 05-stacking-game-rules*
*Completed: 2026-09-16*
