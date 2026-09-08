---
phase: 02-pure-core-game-chemistry-logic
plan: 05
subsystem: data
tags: [json, data-validation, loader, stacking, demo-data, stdlib, python36, error-handling]

# Dependency graph
requires:
  - phase: 01-plugin-skeleton-purity-harness
    provides: purity gate (auto-PURE classification), scoped unittest discovery + test conventions, run_gates harness
  - phase: 02-pure-core-game-chemistry-logic research
    provides: authoritative v1 schemas (R6) + demo-data research (doi 10.1039/b003010o verified; 3.4 A is fixture-reproduction-only)
provides:
  - serpentrum/molecule_data.py: DataError, load_manifest, load_stacking (full structural validation), shipped_interactions (APPROVED-only), interaction_for (set-based first-match/None)
  - proven v1 manifest + stacking schemas (the exact shapes a later data-prep plan writes into serpentrum/data/demos/)
  - 39 tmpdir tests incl. the verbatim research error message and the bool-is-int trap proofs
affects: [02-04-stacking-placement (consumes distance_a from the file), demo-data prep plan (creates serpentrum/data/demos/), DATA-02 human approval track, STACK-03 refuse-and-skip, phase 8 integration]

# Tech tracking
tech-stack:
  added: []   # stdlib json/os only
  patterns:
    - "Indexed DataError messages: '<file basename> <entry kind> <index>: <problem>' (file-level: '<file basename>: <problem>')"
    - "Explicit bool rejection in every int/number validator (py3.6 isinstance(True, int) trap)"
    - "Structural-only validation: citation key must resolve in citations; 'approved' is data, not a loader opinion"
    - "DRAFT/APPROVED gating lives in the data file; shipped_interactions() is the shipping gate (DATA-02 code side)"
    - "Synthetic tmpdir JSON documents for tests; serpentrum/data/ stays pristine"

key-files:
  created:
    - serpentrum/molecule_data.py
    - tests/test_molecule_data.py
  modified: []

key-decisions:
  - "Loaders take the JSON FILE path; base_dir for molecule 'file' existence is os.path.dirname(path) (path contract tested: directory arg is a loud DataError)"
  - "distance_a 3.4 in the test schema exists ONLY to reproduce the committed dimer2 fixture (fragment2 = fragment1 + (0,0,3.4)); it is not a shipped chemistry claim — the demo-data research recommends 3.6 for shipping, human's call (DATA-02)"
  - "Validation is structural only: no chemistry-truth checking in the loader; 'unknown citation' means key-not-in-table, nothing more"
  - "Status matching is case-sensitive ('draft' is a typo, not a status); distance sanity ceiling 0 < d <= 10.0 A is a module constant (MAX_DISTANCE_A)"
  - "interaction_for does NOT filter by status — it is the STACK-03 lookup; callers gate on APPROVED for shipping"

patterns-established:
  - "DataError indexed-message pattern for educator-facing data debugging"
  - "_is_int/_is_number helpers with explicit bool exclusion (reusable trap-proof validator idiom)"
  - "json-round-trip deep copy + mutate-per-test document builder in tmpdir tests"

# Metrics
duration: 10 min
completed: 2026-09-08
---

# Phase 2 Plan 05: Validated Demo-Data Loader Summary

**Structurally validated JSON loaders for the molecule manifest + stacking-interaction datasets (STACK-02: stacking data is a data file, never code constants), with indexed DataError messages, APPROVED-only shipping accessors (DATA-02 code side), and set-based interaction lookup (STACK-03 input).**

## Performance

- **Duration:** 10 min
- **Started:** 2026-09-08T00:31:22Z
- **Completed:** 2026-09-08T00:41:03Z
- **Tasks:** 2/2
- **Files modified:** 2 created (752 + 120 insertions)

## Accomplishments
- `serpentrum/molecule_data.py` (362 lines, PURE, stdlib json/os): `DataError` + `load_manifest` + `load_stacking` with full structural validation (Task 1), then `shipped_interactions` + `interaction_for` (Task 2)
- Every rejection case from the plan matrix proven: schema_version, missing keys (exact phrasing `missing key '<name>'`), bad types, the py3.6 bool-is-int trap (`atom_count: true` rejected), ring_atoms (>= 3, unique, in-range, bool entries), ring_count 0, set mismatch, duplicate molecule/interaction ids, missing molecule file under the manifest dir, distance range 0 < d <= 10, negative offset/uncertainty, case-sensitive DRAFT/APPROVED, unknown + malformed citation entries, empty applies_to.sets
- The research's literal error message reproduces VERBATIM: `stacking.json interaction 0: missing key 'distance_a'` (asserted with assertEqual)
- Shipped-shape proof: both research documents load together from one tmpdir and the placement distance is READ from the file (`assertEqual(distance_a, 3.4)` — the committed dimer2 fixture value; DRAFT, not a shipped claim)
- No `serpentrum/data/` files created (verified absent) — shipped data files are a later plan's deliverable using this proven schema

## Task Commits

Each task was committed atomically:

1. **Task 1: DataError + load_manifest + load_stacking with full validation** - `0d0ad59` (feat)
2. **Task 2: accessors (shipped_interactions, interaction_for) + shipped-shape proof + gates** - `019d7e5` (feat)

## Files Created/Modified
- `serpentrum/molecule_data.py` - PURE stdlib loader module: DataError, load_manifest, load_stacking, shipped_interactions, interaction_for
- `tests/test_molecule_data.py` - 39 tests: valid round-trips, full rejection matrix, path contract, DRAFT/APPROVED semantics, first-match lookup, shipped-shape proof

## Decisions Made
- Loaders take the JSON file PATH (not dir); `base_dir` derived via `os.path.dirname(path)`; passing a directory is a loud DataError
- Structural-only validation: citation key must RESOLVE in `citations`; `approved` is data, not a loader opinion (no chemistry truth judged)
- 3.4 A test distance reproduces the committed dimer2 fixture for testing; NOT a shipped chemistry claim (DATA-02 owns the shipping value; research recommends 3.6)
- Case-sensitive status matching; `MAX_DISTANCE_A = 10.0` sanity ceiling as a module constant
- `interaction_for` returns the first file-order match regardless of status; shipping decisions gate on APPROVED separately

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added tests for planned-but-unlisted validation rules**
- **Found during:** Task 1
- **Issue:** The task's action list requires several validation behaviors (invalid JSON text -> DataError, non-dict top level -> DataError, schema_version bool rejection, ring_atoms bool entries, distance_a bool, negative uncertainty_a, citation `approved` non-bool) that were not enumerated in the plan's rejection-matrix test list — untested loader rules would be unproven contracts
- **Fix:** Added 9 tests covering exactly those rules (plus a directory-argument loud-error test proving the path contract's negative side)
- **Files modified:** tests/test_molecule_data.py
- **Verification:** all 39 module tests pass; gates green
- **Committed in:** 0d0ad59 (Task 1) / 019d7e5 (Task 2)

---

**Total deviations:** 1 auto-fixed (test-coverage completeness for rules the plan itself mandates; no behavior beyond the plan's action list)
**Impact on plan:** No scope creep — every added test proves a rule stated in the task's `<action>` section.

## Issues Encountered
None - both loaders and accessors passed their full verification batteries on first run.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Plan 02-04 (placement math) can consume `distance_a`/`lateral_offset_a` from a validated stacking dataset — the shipped-shape proof test (`test_distance_flows_from_the_file`) documents the file-driven contract its integration test builds on
- The demo-data prep plan creates `serpentrum/data/demos/manifest.json` + `stacking.json` using EXACTLY the schema proven here (research §6 content maps in at data-prep without altering numbers)
- DATA-02 human approval track: pin the value in the data file, flip `status` to APPROVED + `approved: true`; `shipped_interactions()` then ships it — no code change needed
- STACK-03 refuse-and-skip consumes `interaction_for` (None -> skip molecule)
- Wave-1 note: module imports stdlib only; no Phase-2 sibling modules imported (parallelism-safe)

---
*Phase: 02-pure-core-game-chemistry-logic*
*Completed: 2026-09-08*
