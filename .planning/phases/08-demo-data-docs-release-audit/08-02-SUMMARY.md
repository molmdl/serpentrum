---
phase: 08-demo-data-docs-release-audit
plan: 02
subsystem: data
tags: [demo-data, setloader, manifest, pubchem, cod, crossref, unittest]

requires:
  - phase: 03-molecules-in-viewer-setup
    provides: Demo Set A shipped at plan 03-05 (human-placed PubChem SDFs, builder-verified manifest); setloader.load_demo_set production entry point
  - phase: 05-stacking-game-rules
    provides: 05-01 ring_cycle shim (biphenyl yields ONE planar 6-ring in ring order)
provides:
  - DATA-01 mechanical proof as a permanent gate test (TestLoadDemoSetEndToEnd over the real load_demo_set seam)
  - DATA_SOURCES.md carrying the three prescribed content edits with verification trails, still DRAFT-headed for GATE V
affects: [08-11 GATE V consolidated human approval, DATA-02, DATA-04, DOCS-02]

tech-stack:
  added: []
  patterns:
    - "End-to-end regression test over the EXACT production entry-point kwargs (no re-implementation of the load seam)"
    - "No-fabrication documentation: every added fact cites an in-repo artifact (03-05) or a Crossref research trail (08-RESEARCH-data.md 2026-09-27)"

key-files:
  created: []
  modified:
    - tests/test_demo_data.py
    - serpentrum/data/DATA_SOURCES.md

key-decisions:
  - "TestLoadDemoSetEndToEnd gates on the real setloader.load_demo_set call (data_dir, set_id='set_a', stacking_path=stacking_pi_stack.json) — byte-for-byte the dialog's seam, per plan reprimand against guesswork"
  - "Regression-proof framing: the test documents that a FAILURE is a real finding — assertions must never be weakened to make it pass"

patterns-established:
  - "DATA-01 coherent-shipping proof = permanent unittest over production loader (zero errors, 5 records, has_stack_entry True, 6-atom stack_ring)"

duration: 5min
completed: 2026-09-27
---

# Phase 8 Plan 2: Demo-pack completion Summary

**Demo pack end-to-end load proof locked in as a permanent gate test, plus the three Crossref/shipment-verified DATA_SOURCES.md content edits — doc still DRAFT-headed for GATE V, manifest byte-identical.**

## Performance

- **Duration:** 5 min
- **Started:** 2026-09-27T17:52Z
- **Completed:** 2026-09-27T17:56Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- `TestLoadDemoSetEndToEnd` added to `tests/test_demo_data.py`: calls the EXACT production entry point (`setloader.load_demo_set(data_dir, set_id='set_a', stacking_path='stacking_pi_stack.json')`, signature read from source — not guessed) and asserts with per-assertion messages: `errors == []`, `len(records) == 5`, every record `has_stack_entry is True`, every `stack_ring` has exactly 6 atoms. Green on first run (the seam was verified green 2026-09-27 in 08-RESEARCH-data.md — a pass was the expected outcome, a failure would have been a real regression finding).
- DATA_SOURCES.md edit 1 (stale §1 NOTE): the false "ship in a later phase (Phase 8 …)" text replaced with the factual shipment record — five PubChem 3D SDFs (CIDs 241/931/8418/995/7095) human-placed and builder-verified at plan 03-05 (2026-09-11); manifest.json generated from parsed reality by `tools/build_demo_manifest.py` (aborts on any mismatch).
- DATA_SOURCES.md edit 2 ([COD4003564] vol/pages): "(vol/pages to be added at data-prep from the DOI record.)" replaced with the Crossref-verified citation *Chemistry of Materials* 2020, 32 (12), 5162–5172, DOI line kept metabolized, trail parenthetical added ("vol/pages verified via api.crossref.org/works/10.1021/acs.chemmater.0c01184, 2026-09-27").
- DATA_SOURCES.md edit 3 (§1 license note): live re-verification date stamped ("Re-verified live 2026-09-27"; PubChem docs pages still 404, NCBI policy page used) with the evidence pointer to 08-RESEARCH-data.md; policy substance unchanged.
- Untouched as prescribed: [JAN2000] SCOPE CAVEAT, herringbone negative-evidence block, §3 UNVERIFIED list, §4 precision note. Header/legend/footer all still read `DRAFT — NOT APPROVED` (grep count ≥ 2: `DRAFT — NOT APPROVED` appears on header line 1 and footer; STATUS LEGEND lines intact).
- Audit chain green: `python3.6 tools/build_demo_manifest.py` printed success and left `serpentrum/data/manifest.json` BYTE-IDENTICAL (`git diff --stat` empty — no finding); `python3.6 tests/run_gates.py` fully green (syntax + plugin-path safety + AST purity + scoped unittest discovery, 11 tests in test_demo_data incl. the 4 new end-to-end assertions).

## Task Commits

Each task was committed atomically:

1. **Task 1: Add TestLoadDemoSetEndToEnd** — `5960567` (test)
2. **Task 2: Three DATA_SOURCES.md content edits + audit chain** — `620cb97` (docs)

**Plan metadata:** `(pending)` (docs: complete demo-pack completion plan)

## Files Created/Modified

- `tests/test_demo_data.py` — new `TestLoadDemoSetEndToEnd` class (4 tests; skipUnless-guarded on SDFs + manifest + stacking dataset presence, same hygiene as the existing suite).
- `serpentrum/data/DATA_SOURCES.md` — three content edits (+15/−8 lines); still DRAFT-headed; contains no new unverified claims.

## Decisions Made

- Followed the plan exactly: production-kwargs call synthesized only after reading `serpentrum/setloader.py`'s real signature (`data_dir=None, set_id='set_a', stacking_path=None`); test uses absolute repo-root-anchored paths via `__file__` so it is cwd-independent (consistent with the file's existing `_DATA_DIR` pattern).
- No subTest-loop for the load: one `setUpClass` production load shared by all assertions — keeps the test a faithful "one dialog load" proof rather than four independent loads.

## Deviations from Plan

None — plan executed exactly as written. The new test passed on its first run (the expected regression-proof outcome), so no failure findings to report.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- DATA-01's coherent-shipping proof is now a permanent gate test (any future demo-pack change that breaks the production load path fails the default gate suite, not just an ad-hoc probe).
- DATA_SOURCES.md carries all three prescribed content edits with verification trails and is DRAFT-headed — ready for GATE V (plan 08-11) to present the final document + audit evidence + itemized approval checklist for the consolidated human DATA-02/04/DOCS-02 sign-off. Reminder from 08-RESEARCH-data.md: the approval-flip task in 08-11 must also update the coupled `'DRAFT'` marker pin in `tests/test_stacking_dataset.py` (red-suite trap if forgotten).
- No fabricated content: every added fact cites an in-repo artifact (03-05) or the Crossref trail (api.crossref.org/works/10.1021/acs.chemmater.0c01184, HTTP 200, recorded 2026-09-27).

---
*Phase: 08-demo-data-docs-release-audit*
*Completed: 2026-09-27*

