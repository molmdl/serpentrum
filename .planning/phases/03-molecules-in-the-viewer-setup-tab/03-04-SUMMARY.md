---
phase: 03-molecules-in-the-viewer-setup-tab
plan: 04
subsystem: data
tags: [sdf, mol2, setloader, manifest-verification, gate, upload, pure-module, tdd]

# Dependency graph
requires:
  - phase: 02 (Pure Core)
    provides: molecule_data.load_manifest/load_stacking/interaction_for (manifest + stacking schemas)
  - phase: 03-02 (molfile)
    provides: molfile.read_sdf/read_mol2/gate_set/write_sdf_text (SDF/mol2 parsing + gate + split)
provides:
  - setloader.load_demo_set(data_dir, set_id, stacking_path) -> (records, errors)
  - setloader.load_upload(path, stacking_path) -> (records, errors)
  - setloader._build_record shared constructor (has_stack_entry via interaction_for)
  - setloader.package_data_dir() + default_stacking_path() path helpers
  - Molecule record shape: {id, name, file, record_index, elements, atom_count, charge, ring_count, has_explicit_h, has_stack_entry, set, source, warnings, [ring_atoms]}
affects: [03-06 (pymol_bridge), 03-07 (gui_setup), Phase 5 (STACK-03 skip-policy)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "PURE loader module pattern: setloader is stdlib-only (os/tempfile), unit-tested under WSL python3.6 with zero stubs"
    - "(records, errors) contract: both loaders return a tuple; errors are human-readable strings, empty = all good"
    - "__upload__ sentinel keying: uploaded molecules get set='__upload__' matching NO interaction -> has_stack_entry=False (STACK-03)"
    - "Multi-record SDF split: accepted records written via molfile.write_sdf_text into srp_upload_ tempdir as loadable single-record files"

key-files:
  created:
    - serpentrum/setloader.py
    - tests/test_setloader.py
  modified:
    - serpentrum/molecule_data.py

key-decisions:
  - "__upload__ sentinel for skip-policy keying (no formula/name matching — uploaded benzene must NOT inherit set_a's stacking entry)"
  - "Tempdir lifecycle: srp_upload_* tempdirs left to OS /tmp cleanup (documented, acceptable for Phase 3)"
  - "Verification order in load_demo_set: read_sdf (1 record) -> gate_set -> manifest cross-check -> build (gate before cross-check so gate failures are errors, not silent skips)"
  - "Gate reason used as-is for upload error strings (gate_molecule already formats '<name>: <detail>')"

patterns-established:
  - "Loader modules are PURE (stdlib only) — testable under WSL python3.6 without pymol stubs"
  - "File/parse failures become error entries, never exceptions escaping the public API"
  - "TDD RED/GREEN discipline: RED-1 (demo tests) -> GREEN-1 (demo impl) -> RED-2 (upload tests) -> GREEN-2 (upload impl)"

# Metrics
duration: 10 min
completed: 2026-09-10
---

# Phase 3 Plan 4: setloader Summary

**PURE setloader module: demo-set manifest cross-verification + upload gating with multi-record SDF split and __upload__ skip-policy keying**

## Performance

- **Duration:** 10 min
- **Started:** 2026-09-10T04:17:37Z
- **Completed:** 2026-09-10T04:27:15Z
- **Tasks:** 3 (TDD: RED-1, GREEN-1 + docstring, RED-2 + GREEN-2)
- **Files modified:** 3 (2 created, 1 docstring-only edit)

## Accomplishments

- Demo-set loader with manifest cross-verification: load_demo_set parses every manifest molecule's SDF, gates it, and verifies atom_count/charge/ring_count against parsed reality — mismatches exclude the molecule with a precise error naming its id (SC1 demo leg)
- Upload loader with per-record gating: load_upload routes by extension (.sdf/.mol2), gates each record, and splits multi-record SDFs into PyMOL-loadable single-record files in one srp_upload_ tempdir (DATA-03 + SC1 upload leg)
- Skip-policy keying locked: demo records (set='set_a') get has_stack_entry=True via interaction_for; upload records (set='__upload__') get False — STACK-03 input ready for Phase 5
- molecule_data.py docstring fixed: stale data/demos/* paths updated to real shipped names (data/manifest.json, data/stacking_pi_stack.json)

## Task Commits

Each task was committed atomically (TDD RED/GREEN discipline):

1. **Task 1 (RED-1): failing demo-path tests** — `fccfcff` (test)
2. **Task 2 (GREEN-1): demo-set loader + manifest verification** — `6e7b400` (feat)
3. **Task 2 (cont): molecule_data docstring fix** — `0416da0` (docs)
4. **Task 3 (RED-2): failing upload-path tests** — `afcd99b` (test)
5. **Task 3 (GREEN-2): upload path with gate + multi-record split** — `4004da9` (feat)

## Files Created/Modified

- `serpentrum/setloader.py` — PURE module: load_demo_set, load_upload, _build_record, package_data_dir, default_stacking_path (323 lines)
- `tests/test_setloader.py` — 14 test cases: demo happy path, manifest mismatches (ring_count/atom_count/charge), multi-record rejection, gate failure, set filter, upload single/multi SDF, rejection reason, mol2 warning, unsupported extension, missing file (511 lines)
- `serpentrum/molecule_data.py` — docstring-only fix: data/demos/manifest.json -> data/manifest.json, data/demos/stacking.json -> data/stacking_pi_stack.json

## Decisions Made

- **`__upload__` sentinel for skip-policy keying:** Uploaded molecules get `set='__upload__'` which matches NO interaction in the stacking dataset, so `interaction_for` returns None -> `has_stack_entry=False`. This reuses the existing `interaction_for` mechanism without inventing a new lookup. An uploaded benzene does NOT inherit set_a's stacking entry (no formula/name matching).
- **Verification order in load_demo_set:** read_sdf (must be 1 record) -> gate_set -> manifest cross-checks -> build. The gate runs before cross-checks so a gate-failing demo molecule is an error, not a silent skip.
- **Gate reason as upload error string:** `gate_molecule` already formats its reason as `'<name>: <detail>'`, so upload rejection errors use the gate reason directly — no reformatting needed. Titles are pre-set to the upload name (title or `upload_<idx>`) before gating so the name is correct even for blank-title records.
- **Tempdir lifecycle:** `srp_upload_*` tempdirs are left to OS /tmp cleanup. Documented in the module docstring; acceptable for Phase 3 (small single-record SDF files).

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- setloader.load_demo_set and load_upload are ready for 03-06 (pymol_bridge) and 03-07 (gui_setup) to consume via the (records, errors) contract
- The molecule record shape is locked: {id, name, file, record_index, elements, atom_count, charge, ring_count, has_explicit_h, has_stack_entry, set, source, warnings} + demo records carry ring_atoms
- The __upload__ skip-policy keying is test-proven: Phase 5 can rely on has_stack_entry=False for uploaded molecules (STACK-03 refuse-and-skip)
- Demo Set A data files (SDF + manifest.json) still need to arrive via 03-05's human gate before SC1's "Demo Set A loads" can be human-verified with real PubChem SDFs

---
*Phase: 03-molecules-in-the-viewer-setup-tab*
*Completed: 2026-09-10*
