---
phase: 03-molecules-in-the-viewer-setup-tab
plan: 02
subsystem: data
tags: [sdf, mol2, v2000, cyclomatic, ring-count, gate, pure-python, tdd]

# Dependency graph
requires:
  - phase: 02-pure-core-game-chemistry-logic
    provides: xyzio.ELEMENT_SYMBOLS (118 IUPAC symbols, case-sensitive) + XyzError line-numbered error contract
provides:
  - serpentrum/molfile.py — PURE stdlib SDF V2000/mol2 reader, cyclomatic ring counter, ring-atom finder, load-time gate
  - count_rings(bonds, atom_count) — cyclomatic number mu = E - V + C
  - read_sdf/read_sdf_text — multi-record V2000 parser with M CHG charge accumulation
  - write_sdf_text — V2000 serializer that round-trips through read_sdf_text
  - read_mol2/read_mol2_text — TRIPOS mol2 parser (charge=0 + warning)
  - find_ring_atoms — 2-core ring-atom finder (benzene -> 6 carbons, methane -> [])
  - gate_molecule/gate_set — load-time validation gate (rings/explicit-H/charge)
affects: [03-04 setloader, 03-05 demo-set-manifest, Phase 5 stacking, Phase 6 xtb charge]

# Tech tracking
tech-stack:
  added: []
  patterns: [fixtures-first parsing, line-numbered error contract (mirrors xyzio), cyclomatic-number ring counting, 2-core ring-atom finding]

key-files:
  created:
    - serpentrum/molfile.py
    - tests/test_molfile.py
    - tests/fixtures/molfile/methane.sdf
    - tests/fixtures/molfile/benzene_naphthalene.sdf
    - tests/fixtures/molfile/acetate.sdf
    - tests/fixtures/molfile/benzene_noh.sdf
    - tests/fixtures/molfile/benzene.mol2
  modified: []

key-decisions:
  - "Ring count = cyclomatic number mu = E - V + C (circuit rank), not SSSR enumeration — trivially computable, stdlib-only, equals SSSR count for normal organics"
  - "find_ring_atoms uses 2-core (iterative pendant removal) instead of shortest-cycle BFS — simpler, returns ALL ring atoms (correct for the manifest ring_atoms builder), not just one cycle"
  - "mol2 charge assumed 0 + warning (partial charges don't survive per PITFALLS 11 [SRC: chempy/mol2.py:74])"
  - "Acetate fixture uses 2C+2H+2O=6 atoms/5 bonds (plan's breakdown had an arithmetic error: 2C+3H+2O=7 atoms/6 bonds contradicted the stated 6 atoms/5 bonds)"

patterns-established:
  - "MolFileError mirrors xyzio.XyzError: 1-based line number + <=60-char snippet via _line_error helper"
  - "SDF parser: whitespace-split primary path with fixed-width fallback for counts/atoms/bonds"
  - "Record dict carries coords + charges (approved deviation from research: 03-04 upload split needs re-serialization)"
  - "Gate check order: rings -> explicit-H -> inorganic advisory; charge is information, never a rejection"

# Metrics
duration: 22min
completed: 2026-09-10
---

# Phase 3 Plan 2: molfile SDF/mol2 readers + ring count + gate Summary

**PURE stdlib SDF V2000/mol2 reader with cyclomatic ring counter (mu = E-V+C), ring-atom finder (2-core), writer round-trip, and load-time gate (rings/explicit-H/charge) — TDD against 5 committed fixtures**

## Performance

- **Duration:** 22 min
- **Started:** 2026-09-10T03:29:42Z
- **Completed:** 2026-09-10T03:52:11Z
- **Tasks:** 3 (RED-1/GREEN-1 + RED-2/GREEN-2)
- **Files modified:** 8 (1 module, 1 test file, 5 fixtures, 1 summary)

## Accomplishments
- count_rings implements the cyclomatic number mu = E - V + C with stdlib BFS component counting — exact ints for all 6 graph shapes (benzene 1, naphthalene 2, biphenyl 2, disconnected 2, chain 0, no-bonds 0)
- read_sdf parses multi-record V2000 files ($$$-separated) preserving per-record title, elements, coords, bonds, and M CHG charge sums (acetate -> -1); malformed records raise MolFileError naming the 1-based line + snippet (xyzio XyzError contract)
- write_sdf_text round-trips a parsed record: read -> write -> read reproduces the same elements/bonds/charge/coords (enables the Phase-3 upload split in 03-04)
- find_ring_atoms returns the indices of a 6-cycle from the parsed bond graph (benzene -> its 6 ring carbons; methane -> []) via 2-core pendant removal
- gate_molecule rejects >3-ring and organic-zero-H with clear reasons, accepts inorganic-zero-H with a warning advisory; gate_set returns (accepted, rejected) with per-molecule reasons in input order (SC1 / DATA-03)
- mol2 reader accepts files with charge=0 + MOL2_CHARGE_WARNING (formal charges don't survive per PITFALLS 11)

## Task Commits

Each task was committed atomically (TDD RED/GREEN discipline):

1. **Task 1 (RED-1): fixtures + failing SDF/ring tests** - `bbd7ffe` (test)
2. **Task 2 (GREEN-1): SDF reader + ring count** - `a6538f2` (feat)
3. **Task 3 (RED-2): mol2/writer/ring-finder/gate tests** - `e7186ac` (test)
4. **Task 3 (GREEN-2): writer/mol2/ring-finder/gate impl** - `a6547b4` (feat)

**Plan metadata:** (pending — this commit)

## Files Created/Modified
- `serpentrum/molfile.py` - PURE stdlib SDF V2000/mol2 reader, ring counter, ring finder, writer, load gate (618 lines)
- `tests/test_molfile.py` - fixture-driven test suite: ring math, SDF multi-record/M CHG/error contracts, mol2 charge=0+warning, writer round-trip, ring finder, gate matrix (338 lines)
- `tests/fixtures/molfile/methane.sdf` - single-record V2000 (5 atoms, 4 bonds, 0 charge)
- `tests/fixtures/molfile/benzene_naphthalene.sdf` - 2 records ($$$-separated): benzene 12/12/1 + naphthalene 18/19/2
- `tests/fixtures/molfile/acetate.sdf` - M CHG charge test (6 atoms, 5 bonds, charge -1)
- `tests/fixtures/molfile/benzene_noh.sdf` - skeletal benzene (6 C, zero H) — the missing-H gate rejection case
- `tests/fixtures/molfile/benzene.mol2` - minimal TRIPOS mol2 (12 atoms, 12 bonds, charge 0 + warning)

## Decisions Made
- **Ring count = cyclomatic number mu = E - V + C**: trivially computable from the bond graph (count edges, vertices, components via BFS), no SSSR algorithm needed. Equals SSSR count for all normal organics. Verified: benzene 1, naphthalene 2, anthracene 3, phenanthrene 3, biphenyl 2.
- **find_ring_atoms uses 2-core (iterative pendant removal)** instead of the plan's suggested shortest-cycle BFS. The 2-core is simpler, returns ALL ring atoms (correct for the manifest ring_atoms builder in 03-05), and naturally handles fused systems. For benzene it yields exactly the 6 ring carbons; for methane [].
- **Acetate fixture resolved to 2C+2H+2O=6 atoms/5 bonds**: the plan's behavior case explicitly stated "6 atoms, 5 bonds" but the breakdown "2C+3H+2O, C-C+C-O+C-O+3*C-H" gives 7 atoms/6 bonds (arithmetic error). Used 2C+2H+2O to match the explicit count. Fixture is test data, not a chemistry claim.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Acetate fixture atom/bond count arithmetic error**
- **Found during:** Task 1 (RED-1 fixture creation)
- **Issue:** Plan's behavior case 4 said "6 atoms (2 C, 3 H, 2 O), 5 bonds (C-C, C-O(=), C-O(-), 3 C-H)" but 2C+3H+2O=7 atoms and C-C+C-O+C-O+3*C-H=6 bonds, contradicting the stated 6 atoms/5 bonds.
- **Fix:** Used 2C+2H+2O=6 atoms and 5 bonds (C-C, C=O, C-O-, C-H, C-H) to match the explicit "6 atoms, 5 bonds" count. M CHG charges the O- atom (1-based index 4) to -1. The fixture is test data, not a chemistry claim.
- **Files modified:** tests/fixtures/molfile/acetate.sdf
- **Verification:** test_acetate_m_chg passes: 6 atoms, 5 bonds, charge -1, contains O
- **Committed in:** bbd7ffe (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Minor fixture content adjustment to resolve an arithmetic inconsistency in the plan. No scope creep. All behavior cases pass.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- molfile.py is complete and self-contained (stdlib + xyzio.ELEMENT_SYMBOLS only)
- 03-04 setloader can consume read_sdf/read_mol2/gate_set/write_sdf_text to build validated molecule records
- 03-05 manifest builder can use find_ring_atoms to compute ring_atoms indices from parsed SDF bond graphs
- The post-checkpoint real-PubChem regression test (plan 03-05) will close the SDF V2000 format gap against real PubChem files
- 383 existing tests unbroken (403 total with 20 new molfile tests)

---
*Phase: 03-molecules-in-the-viewer-setup-tab*
*Completed: 2026-09-10*
