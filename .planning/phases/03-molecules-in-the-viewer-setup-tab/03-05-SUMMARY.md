---
phase: 03-molecules-in-the-viewer-setup-tab
plan: 05
subsystem: data
tags: [pubchem, sdf, manifest, molfile, regression-test, demo-set-a]

# Dependency graph
requires:
  - phase: 03-02
    provides: serpentrum.molfile (read_sdf, count_rings, find_ring_atoms, gate_molecule)
  - phase: 02-05
    provides: serpentrum.molecule_data.load_manifest (v1 schema validation)
provides:
  - Demo Set A real data — 5 PubChem 3D SDF files (CIDs 241/931/8418/995/7095) in serpentrum/data/
  - serpentrum/data/manifest.json — v1 schema, 5 molecules, all values parsed-reality-derived
  - tools/build_demo_manifest.py — dev-side builder (abort-on-mismatch, idempotent)
  - tests/test_demo_data.py — skipUnless-guarded real-file regression suite (7 cases)
affects: [03-04 (setloader can now load the REAL set), Phase 5 (stacking consumes ring_atoms), Phase 8 (DATA-01 shipping sign-off)]

# Tech tracking
tech-stack:
  added: []
  patterns: [parsed-reality cross-check (abort on mismatch — no fabricated values), skipUnless-guarded real-file regression test]

key-files:
  created:
    - serpentrum/data/benzene.sdf
    - serpentrum/data/naphthalene.sdf
    - serpentrum/data/anthracene.sdf
    - serpentrum/data/phenanthrene.sdf
    - serpentrum/data/biphenyl.sdf
    - serpentrum/data/manifest.json
    - tools/build_demo_manifest.py
    - tests/test_demo_data.py
  modified: []

key-decisions:
  - "ring_atoms stores the full 2-core (all ring atoms via find_ring_atoms, sorted) per the plan task instruction; Phase 5's ring_frame needs ONE planar ring in ring order — documented as a Phase 5 readiness item"

patterns-established:
  - "Parsed-reality cross-check: build script aborts on any mismatch between parsed SDF values and DATA_SOURCES.md-verified metadata — zero fabricated values ever written"
  - "skipUnless-guarded real-file regression: test skips cleanly while data is absent, hard-passes once human-provided files exist"

# Metrics
duration: ~112 min (incl. context loading)
completed: 2026-09-10
---

# Phase 3 Plan 5: Demo Set A Data Summary

**5 PubChem 3D SDFs (CIDs 241/931/8418/995/7095) shipped + manifest.json built from parsed-reality cross-checks (atom counts 12/18/24/24/22, rings 1/2/3/3/2, charges 0) + real-file regression test closing the fixtures-first gap**

## Performance

- **Duration:** ~112 min (wall clock; includes context loading + verification)
- **Started:** 2026-09-10T16:37:19Z
- **Completed:** 2026-09-10T18:29:39Z
- **Tasks:** 2 (Task 1 human gate discharged; Task 2 agent-built)
- **Files modified:** 8 created (5 SDFs + manifest + build script + test)

## Accomplishments

- **Human gate discharged:** 5 verified public-domain PubChem 3D SDF files placed in serpentrum/data/ by the human (Task 1), programmatically verified by the agent (each contains V2000 + $$$$)
- **Manifest fully derived from parsed reality:** tools/build_demo_manifest.py parses each SDF via serpentrum.molfile, cross-checks atom counts (12/18/24/24/22) and cyclomatic ring counts (1/2/3/3/2) against DATA_SOURCES.md-verified metadata — aborts on any mismatch, never fabricates a value
- **Real-file regression test:** tests/test_demo_data.py proves the parser + <=3-ring gate against actual PubChem bytes (not just hand-written fixtures), closing the fixtures-first gap; 7 test cases, skipUnless-guarded for clean pre-checkpoint skipping
- **Full suite + gates green:** 433 tests pass (was 426 + 7 new), all 3 gates (syntax/path-safety, AST purity, unittest) PASS

## Task Commits

Each task was committed atomically:

1. **Task 1: Human SDF placement** — `7cc175e` (data: 5 PubChem 3D SDFs)
2. **Task 2: Manifest + build script + regression test** — `bd35bb6` (feat)

**Plan metadata:** `bd35bb6`→next (docs: complete plan)

## Files Created/Modified

- `serpentrum/data/benzene.sdf` — PubChem CID 241, C6H6, 12 atoms (human-provided)
- `serpentrum/data/naphthalene.sdf` — PubChem CID 931, C10H8, 18 atoms (human-provided)
- `serpentrum/data/anthracene.sdf` — PubChem CID 8418, C14H10, 24 atoms (human-provided)
- `serpentrum/data/phenanthrene.sdf` — PubChem CID 995, C14H10, 24 atoms (human-provided)
- `serpentrum/data/biphenyl.sdf` — PubChem CID 7095, C12H10, 22 atoms (human-provided)
- `serpentrum/data/manifest.json` — v1 schema, one set (set_a), 5 molecules with CID-cited source_id, all values parsed-reality-derived
- `tools/build_demo_manifest.py` — dev-side builder: parses 5 SDFs via molfile, cross-checks against DATA_SOURCES.md metadata, aborts on mismatch, writes manifest.json (idempotent)
- `tests/test_demo_data.py` — skipUnless-guarded real-file regression suite (7 cases: manifest structure, source metadata, per-molecule gate + value match, ring count map, ring_atoms validity, set membership)

## Decisions Made

- **ring_atoms stores the full 2-core (all ring atoms):** The plan task explicitly instructs `ring_atoms (molfile.find_ring_atoms — sorted)`. `find_ring_atoms` returns the 2-core (all ring atoms, sorted ascending): 6/10/14/14/12 atoms for the 5 molecules. The plan context notes "indices of ONE planar six-ring (consumed by stacking.ring_frame in Phase 5)" and stacking.py:50-51 documents "Biphenyl handles this by listing ONE ring's atoms in the manifest." These are in tension: `ring_frame` needs ONE ring in ring order (it has a planarity check that would fail on biphenyl's twisted 2-core). This plan follows the explicit task instruction (find_ring_atoms); Phase 5 must either extract one ring from the 2-core before calling `ring_frame`, or the manifest format must be refined. The manifest schema (>= 3 unique ints in range) and the regression test both pass with the 2-core. Documented as a Phase 5 readiness item.

## Deviations from Plan

None — plan executed exactly as written. All cross-checks passed on the first parse (no abort logic triggered): the 5 human-provided SDFs' parsed atom counts (12/18/24/24/22), charges (0), and cyclomatic ring counts (1/2/3/3/2) matched the DATA_SOURCES.md-verified metadata exactly.

## Issues Encountered

None. The human-provided SDFs were valid PubChem 3D-conformer V2000 records — each parsed cleanly as a single record, all passed the <=3-ring gate, and all had explicit hydrogens (organic + has_explicit_h = True).

## User Setup Required

None — the human checkpoint (Task 1) was discharged before this execution began. The 5 SDF files are public-domain PubChem data (US Gov/NCBI; acknowledgment requested, documented in DATA_SOURCES.md sec 1).

## Next Phase Readiness

- **setloader (03-04) can now load the REAL Demo Set A:** manifest.json + 5 SDFs are in place; `molecule_data.load_manifest` validates clean; the setloader's tmpdir-based tests already passed, and the real data path is now exercisable.
- **Phase 5 ring_frame readiness item:** The manifest's `ring_atoms` currently stores the full 2-core (all ring atoms, sorted) per the plan task instruction. `stacking.ring_frame` needs ONE planar ring's atoms IN RING ORDER (it computes a Newell normal over consecutive pairs and has a planarity tolerance of 0.15 A). For biphenyl specifically, the 2-core spans both twisted rings (non-planar) — `ring_frame` would raise ValueError. Phase 5 must extract ONE 6-membered ring (in bond order) from the 2-core before calling `ring_frame`, or the manifest's `ring_atoms` format must be refined to store one ring in ring order. This is a known design item, not a blocker — the manifest schema and regression test are correct as-is.
- **DATA_SOURCES.md stays DRAFT-headed:** full DATA-02/04 checklist sign-off is Phase 8-gated. This plan did NOT edit DATA_SOURCES.md or flip any approval status — the SDF placement is a file delivery, not an approval action.
- **stacking_pi_stack.json untouched:** the APPROVED pi-stack interaction (3.383/1.231 encoded 3.6 A @ 20 deg) remains as-is.

---
*Phase: 03-molecules-in-the-viewer-setup-tab*
*Completed: 2026-09-10*
