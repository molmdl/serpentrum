---
phase: 02-pure-core-game-chemistry-logic
plan: 11
subsystem: demo data (interaction dataset + attribution document)
tags: [data, pi-stack, json-dataset, cod, janiak, attribution, data-sources, human-approval, decision-checkpoint, place-pickup-encoding, pure-python, py36]

# Dependency graph
requires:
  - phase: 02-pure-core-game-chemistry-logic (plan 05)
    provides: serpentrum/molecule_data.py — load_stacking (structural
      validation: schema_version 1, interaction field types/ranges,
      citation resolution, applies_to shape, status in {DRAFT,APPROVED}),
      shipped_interactions (DATA-02 conditional shipping gate), DataError
      (path + entry index + offending key). The dataset validates THROUGH
      this loader; molecule_data.py is NOT in this plan's files (never
      weaken the loader to fit the data).
provides:
  - serpentrum/data/stacking_pi_stack.json: THE shipped pi-stack
    interaction dataset (schema_version 1; one pi_stack_pd interaction,
    status APPROVED; distance_a 3.383 / lateral_offset_a 1.231 ->
    centroid-centroid 3.60 A at 20.0 deg off-normal; 3 verified citations
    all approved:true). Loads through molecule_data.load_stacking with
    zero DataErrors.
  - serpentrum/data/DATA_SOURCES.md: the DATA-04 draft attribution
    document (DRAFT-headed; PubChem CIDs; Janiak 2000 abstract-only
    status; COD measured stacks 3.555/3.570/3.580 A with licenses;
    herringbone negative evidence; UNVERIFIED list 3.3/3.4 A do-not-ship).
  - tests/test_stacking_dataset.py: 16 loader-validated, decision-agnostic
    dataset tests (pass in BOTH DRAFT and APPROVED states) + DATA_SOURCES
    marker checks + loader tamper-proofing (mangled copy rejected).
affects: [02-14-pure-integration, phase-8-data-prep, phase-8]

# Tech tracking
tech-stack:
  added: []   # zero — stdlib json/math/os/shutil/tempfile only
  patterns:
    - "Validated data file (never code constants): interactions + citations load through molecule_data.load_stacking; STACK-02 data-driven rule satisfied"
    - "place_pickup component encoding: distance_a = perpendicular (ring-normal) component, lateral_offset_a = in-plane component; composed centroid = sqrt(d^2+l^2), off-normal angle = atan2(l,d) (02-04 locked API)"
    - "Decision-agnostic tests: assert invariants (status in {DRAFT,APPROVED}; conditional shipping; geometry within tolerance) not chosen values — suite green before AND after the human checkpoint"
    - "Blocking human-decision checkpoint (DATA-02): no invented data ships without explicit human approval; status/value change is the ONLY route through the checkpoint"
    - "Tamper-proofing: copy the real file into a tempdir, delete a required key, assert load_stacking raises DataError naming the file + key — proves the real file passes because it is VALID, not because validation is absent"

key-files:
  created:
    - serpentrum/data/stacking_pi_stack.json
    - serpentrum/data/DATA_SOURCES.md
    - tests/test_stacking_dataset.py
  modified:
    - serpentrum/data/stacking_pi_stack.json   # Task 3: DRAFT->APPROVED + citation flags (option-a)

key-decisions:
  - "Human decision (option-a): ship 3.6 A centroid-centroid + 20 deg off-normal, encoded as distance_a 3.383 (=3.6*cos20) / lateral_offset_a 1.231 (=3.6*sin20) -> sqrt=3.60001 A, atan2=19.998 deg. Status flipped DRAFT -> APPROVED; all three citation approved flags -> true."
  - "Basis is fully verified: three CC0 COD CIFs measure 3.555 / 3.570 / 3.580 A centroid-centroid (all round to 3.6 A); Janiak 2000 abstract (10.1039/b003010o, verified via OpenAlex W2142594455) states parallel-displaced stacking, ~20 deg ring-normal angle, centroid-centroid up to 3.8 A."
  - "3.4 A remains UNVERIFIED and do-not-ship: Janiak full text is closed everywhere (Unpaywall no-copy, RSC 403); no accessible source states 3.3 or 3.4 A. Listed in DATA_SOURCES.md section 3."
  - "DATA_SOURCES.md stays DRAFT-headed: the md file's own DRAFT status is independent of the dataset status flip; full DATA-02/04 checklist sign-off completes in Phase 8 (data-prep track). The dataset is APPROVED; the attribution document is still DRAFT."
  - "Dataset lives at the contract-fixed path serpentrum/data/stacking_pi_stack.json (NOT serpentrum/data/demos/stacking.json); tests locate it via os.path.dirname(serpentrum.__file__)+data (plugin-runtime-safe). No leftover demos/ dir exists in this worktree."

patterns-established:
  - "DATA-02 human-decision checkpoint pattern: dataset ships DRAFT with recommended values, tests are decision-agnostic, a blocking checkpoint flips DRAFT->APPROVED; the test suite proves it stays green in both states"
  - "Composed-geometry-from-the-file test pattern: derive the headline chemistry value (centroid distance, angle) arithmetically from the file's own two component fields, never hardcode the chosen number"

# Metrics
duration: ~20min (across two agent sessions: initial Tasks 1-2 + checkpoint pause + this continuation)
completed: 2026-09-09
---

# Phase 02 Plan 11: Demo Data (pi-stack) Summary

**APPROVED pi-stack interaction dataset shipping 3.6 A centroid-centroid at 20 deg off-normal (option-a human decision), validated through the 02-05 loader, with a DRAFT DATA_SOURCES.md attribution doc and 16 decision-agnostic tests**

## Performance

- **Duration:** ~20 min (Tasks 1-2 by prior agent + blocking checkpoint pause + this continuation applying the decision)
- **Tasks:** 3 (2 auto + 1 checkpoint:decision, resolved by this continuation)
- **Files:** 3 created, 1 modified (the dataset, flipped DRAFT->APPROVED)
- **Tests added:** 16 (decision-agnostic: location, loader validation, derived geometry, citation integrity, shipping policy, DATA_SOURCES attribution, tamper-proofing)

## Accomplishments
- Materialized the shipped pi-stack interaction dataset `serpentrum/data/stacking_pi_stack.json` (schema_version 1; one `pi_stack_pd` interaction; 3 verified citations). Every number transcribed verbatim from 02-RESEARCH-demo-data.md (DOIs copied verbatim).
- Dataset validates through the real `molecule_data.load_stacking` loader (02-05) with zero DataErrors — STACK-02 "data-driven, never code constants" satisfied.
- Encoded the recommended geometry as the place_pickup component pair: `distance_a` 3.383 (perpendicular) / `lateral_offset_a` 1.231 (lateral) -> composed centroid-centroid `sqrt(3.383^2 + 1.231^2)` = 3.60 A at `atan2(1.231, 3.383)` = 20.0 deg off-normal (02-04 locked API).
- Drafted `DATA_SOURCES.md` (bioCHEMeleon/DATA-04 format): PubChem CIDs 241/931/8418/995/7095 (Phase-8 shipping); Janiak 2000 abstract-only status (full text closed everywhere); three measured CC0 COD stacks (3.555/3.570/3.580 A) with licenses; herringbone negative evidence for neat Set A; explicit UNVERIFIED list (3.3/3.4 A do-not-ship); precision footnote (~0.01-0.05 A, immaterial at 0.1 A rounding).
- 16 decision-agnostic tests asserting invariants (not chosen values): the suite is green in BOTH the DRAFT pre-checkpoint and APPROVED post-checkpoint states.
- **Human decision (option-a) applied:** status flipped DRAFT -> APPROVED; all three citation `approved` flags -> true; `distance_a` 3.383 / `lateral_offset_a` 1.231 kept (option-a keeps the recommended encoding). DATA-02 satisfied for the shipped distance.
- All gates green: 250 tests OK; run_gates.py exit 0 (3 gates PASS).

## Task Commits

Each task was committed atomically (Tasks 1-2 by the prior agent; Task 3 by this continuation):

1. **Task 1: DRAFT stacking dataset JSON + DATA_SOURCES.md** - `06ead54` (feat)
2. **Task 2: decision-agnostic dataset tests** - `0fa28f6` (test)
3. **Task 3 (continuation): approve option-a — status DRAFT->APPROVED + citation flags** - `e0e7b00` (feat)

**Plan metadata:** (pending — `docs(02-11): complete demo-data dataset plan (decision: option-a)`)

## Files Created/Modified
- `serpentrum/data/stacking_pi_stack.json` (22 lines) — the shipped pi-stack interaction dataset; schema_version 1; one APPROVED `pi_stack_pd` interaction (3.60 A @ 20 deg); 3 verified citations all approved. PURE json (plugin-path-safe, invisible to purity walk).
- `serpentrum/data/DATA_SOURCES.md` (133 lines) — DRAFT-headed attribution document; every DOI/CID/COD entry with license + verification status; UNVERIFIED do-not-ship list.
- `tests/test_stacking_dataset.py` (247 lines) — 16 decision-agnostic tests: dataset location, loader validation, derived geometry (computed from the file), citation integrity (closed DOI set), conditional shipping policy, DATA_SOURCES markers, loader tamper-proofing.

## Decisions Made

**BLOCKING HUMAN DECISION (checkpoint:decision) — RESOLVED: option-a (3.6 A + 20 deg, RECOMMENDED)**

- **Decision:** Ship 3.6 A centroid-centroid + 20 deg off-normal, encoded as `distance_a` 3.383 (= 3.6 * cos 20 deg) / `lateral_offset_a` 1.231 (= 3.6 * sin 20 deg) -> composed centroid-centroid `sqrt(3.383^2 + 1.231^2)` = 3.60001 A (rounds to 3.60) at `atan2(1.231, 3.383)` = 19.998 deg (within 0.5 deg of 20.0).
- **Status action:** interaction `status` flipped `DRAFT` -> `APPROVED`; `approved` set to `true` on ALL THREE citation entries (`janiak2000`, `cod4003564`, `cod2100607`).
- **Basis (all verified):**
  - COD 4003564 (phenanthrene-TCNB cocrystal, CC0) = 3.555 A centroid-centroid (interplanar 3.345, offset 1.204, 2.7 deg).
  - COD 2100607 (pyrene, 298 K) = 3.570 A (interplanar 3.472, offset 0.829, 0.0 deg).
  - COD 2100608 (pyrene, compressed) = 3.580 A (interplanar 3.478, offset 0.851).
  - All three round to 3.6 A.
  - Janiak 2000 abstract (DOI 10.1039/b003010o, verified via OpenAlex W2142594455): usual pi interaction is offset/slipped (parallel-displaced) stacking; ring-normal vs centroid-vector angle ~20 deg; centroid-centroid distances up to 3.8 A.
- **3.4 A remains UNVERIFIED and do-not-ship:** Janiak 2000 full text is closed everywhere (Unpaywall `has_repository_copy: false`, RSC 403); no accessible source states 3.3 or 3.4 A. Listed explicitly in DATA_SOURCES.md section 3 (Known UNVERIFIED items). A future institutional-access read could revisit this, but nothing ships on that basis now.
- **DATA_SOURCES.md stays DRAFT-headed:** the markdown attribution document's own DRAFT status is INDEPENDENT of the dataset's status flip. Full DATA-02/04 checklist sign-off (including the PubChem SDF files themselves, which are NOT part of this plan) completes in Phase 8 (data-prep track). The dataset interaction is APPROVED; the attribution document is still DRAFT.
- **Rejected alternatives (recorded for traceability):**
  - option-b (3.57 A exact, COD 2100607 single CIF value): traceability-maximal but bound to one structure/temperature point; discards phenanthrene-TCNB corroboration. Not chosen.
  - option-c (hold DRAFT pending institutional-access verification of 3.4 A): keeps the door open for the unverified candidate but ships nothing APPROVED now; DATA-02 sign-off would defer entirely to Phase 8. Not chosen.

## Deviations from Plan

None beyond the human decision (which WAS the planned checkpoint outcome). The plan executed exactly as written: Tasks 1-2 produced the DRAFT dataset + decision-agnostic tests; the blocking checkpoint paused for the human; this continuation applied option-a precisely as the plan's post-decision actions specified (keep 3.383/1.231; status -> APPROVED; all three citation approved -> true; nothing else changed). The decision-agnostic tests stayed green by construction.

No leftover `serpentrum/data/demos/stacking.json` existed in this worktree — the Task-1 contingency flag did not apply; only the two contract-fixed files (`stacking_pi_stack.json`, `DATA_SOURCES.md`) are present under `serpentrum/data/`.

## Issues Encountered
None — the decision-agnostic test design (asserting invariants, not chosen values) meant the post-decision status flip required zero test edits; the suite exercised the APPROVED shipping path (`shipped_interactions` returns the single entry) for the first time and passed.

## User Setup Required
None — no external service configuration. The dataset is a static JSON file loaded by pure-stdlib code. The only human action was the blocking decision itself (option-a), now resolved.

## Next Phase Readiness
- The shipped pi-stack interaction dataset is APPROVED and validated; `molecule_data.shipped_interactions` now returns the single `pi_stack_pd` entry for set_a (DATA-02 gate open for this interaction).
- 02-14 (pure integration) may consume the dataset through the loader; the `distance_a`/`lateral_offset_a` contract feeds `stacking.place_pickup` (02-04) directly.
- Phase 8 (data-prep) owns: full DATA_SOURCES.md checklist sign-off (DRAFT -> APPROVED for the attribution doc), the PubChem SDF files themselves, and any institutional-access revisit of the 3.4 A candidate.
- No blockers. The dataset path and schema are locked; the decision is recorded; 3.4 A is quarantined as UNVERIFIED.

---
*Phase: 02-pure-core-game-chemistry-logic*
*Completed: 2026-09-09*
