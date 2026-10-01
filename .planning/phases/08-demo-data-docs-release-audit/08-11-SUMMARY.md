---
phase: 08-demo-data-docs-release-audit
plan: 11
subsystem: release-audit
tags: [gate-v, human-verify, data-approval, release-close, requirements-ledger, pymol, xtb]
status: checkpoint-presented

requires:
  - phase: 08-demo-data-docs-release-audit (08-02..08-10)
    provides: DRAFT DATA_SOURCES.md with the 3 content edits; 6-button row + persistence wiring; README/help/docs; smoke 14 RELEASE-E2E; doc-vs-code audit; 46-row evidence ledger
  - phase: 01..07 + 5.1/5.2/5.3
    provides: all 36 pre-Phase-8 requirements already Complete with human-certified evidence
provides:
  - The GATE V checkpoint presentation (Section A data sign-off / B 6-button + educator round-trip / C full release flow with real xtb)
  - Precondition evidence for the orchestrator-presented owner walk-through
  - (conditional, post-approval) APPROVED DATA_SOURCES.md + coupled marker-pin flip + 46/46 Complete ledger + final battery + ROADMAP close
affects: [v1 release (this gate IS the release act)]

tech-stack:
  added: []
  patterns:
    - "Single consolidated release gate: three sections presented at one blocking checkpoint:human-verify (merges the old 08-02/08-05/08-12 checkpoints)"
    - "Coupled literal flip: DATA_SOURCES.md DRAFT->APPROVED markers and the tests/test_stacking_dataset.py marker pin MUST land in the same commit (marker-pin trap)"
    - "Per-item approval accumulation across rounds (05-16/07-10 precedent): amendments produce a numbered fix list, only affected items re-run"

key-files:
  created:
    - .planning/phases/08-demo-data-docs-release-audit/08-11-SUMMARY.md
  modified: []  # conditional on owner approval (Task 2: DATA_SOURCES.md + test_stacking_dataset.py [+ gui.py if width fix]; Task 3: REQUIREMENTS.md + ROADMAP.md [+ README.md amendment if confirmed])

key-decisions: []  # owner verdicts recorded verbatim here post-gate

# Metrics (partial — checkpoint round 1)
duration: ~13min (Task 1 preparation; total TBD at close)
completed: pending GATE V owner verdict (round-1 presentation 2026-10-01)
---

# Phase 8 Plan 11: GATE V — Consolidated Verification + Release Close Summary

**GATE V presented with ALL preconditions green (937 unittests, gates 1-3 PASS; ledger default-green naming exactly the 10 Phase-8 Pending rows; DRAFT-headed attribution doc with 08-02 edits intact and the coupled 'DRAFT' marker pin confirmed at test_stacking_dataset.py:201; 6-button row + smoke 14 registered) — the sectioned A/B/C owner walk-through is now in the orchestrator's hands; Tasks 2-3 are CONDITIONAL on the owner's "approved".**

## Performance (partial)

- **Duration:** ~13 min (Task 1 precondition verification + presentation; Tasks 2-3 TBD)
- **Started:** 2026-10-01T16:05:56Z (UTC)
- **Checkpoint presented:** 2026-10-01 (UTC)
- **Tasks:** 0/3 complete (Task 1 = the checkpoint itself, awaiting owner verdict)
- **Files modified:** 1 (this SUMMARY)

## Precondition Verification (Task 1 staging gate)

| # | Precondition | Result | Evidence |
|---|--------------|--------|----------|
| 1 | Default gate battery green | PASS | `python3.6 tests/run_gates.py` → 937 unittests OK; gates 1 (syntax + plugin-path safety), 2 (AST purity), 3 (scoped unittest) all PASS; "run_gates: all gates green" |
| 2 | 08-01..08-10 SUMMARYs present | PASS | 10 SUMMARY files on disk in the phase dir |
| 3 | DATA_SOURCES.md DRAFT-headed with 08-02 edits | PASS | line 1 `(DRAFT — NOT APPROVED)`; footer line 183 `DRAFT — NOT APPROVED.`; stale §1 NOTE rewritten to the 03-05 shipment fact (:23-26); [COD4003564] carries `Chemistry of Materials 2020, 32 (12), 5162–5172` (:115) with the Crossref trail (:118); 2026-09-27 license re-verification stamp (:48) |
| 4 | 6-button row in gui.py | PASS | gui.py:151-166 — Reset / Randomize / Save Setup / Load Setup / Cleanup model / Start, addStretch(1) first (right-aligned, spec.md:21-26 order); `setMinimumWidth(450)` at gui.py:80 |
| 5 | Smoke 14 registered | PASS | `tests/run_gates.py:76` REQUIRED_SMOKES entry `smoke/14_release_e2e_smoke.py`; file on disk |
| 6 | Ledger Pending rows = the 10 Phase-8 rows | PASS | `tools/audit_requirements.py` default: AUDIT-OK (46/46, checkboxes agree, 136 evidence paths exist); `--release`: FAIL naming exactly `DATA-01, DATA-02, DATA-04, DOCS-01, DOCS-02, DOCS-03, DOCS-04, DOCS-05, SETUP-07, SETUP-08` |
| 7 | Coupled marker pin state | CONFIRMED | `tests/test_stacking_dataset.py:201` required list starts with `'DRAFT'` (the same-commit flip target for Task 2) |

## Task Status

| Task | Name | Status |
|------|------|--------|
| 1 | GATE V — consolidated verification + release close (checkpoint:human-verify, blocking) | **PRESENTED to orchestrator** — awaiting owner walk-through |
| 2 | CONDITIONAL — approval flip + coupled test-pin edit + owner amendments (same commit) | blocked on Task 1 verdict |
| 3 | CONDITIONAL — ledger flip + final battery (`--release` green, full gates + `--smoke` + `--xtb`) + roadmap close | blocked on Task 1 verdict |

## GATE V — checkpoint content presented (verbatim structure)

The orchestrator presents three sections in real Windows PyMOL 2.5.0 (repo-root plugin, fresh session, SRP_DEBUG=1 optional; live observation is the verdict, .bat exit codes never trusted):

- **SECTION A — DATA-02/04/DOCS-02 sign-off:** A1 read/accept the final DATA_SOURCES.md edits as factual; A2 itemized attribution checklist (02-RESEARCH-demo-data.md §7 residue) whole-document approval; A3 audit evidence acceptance (byte-identical manifest re-run, green gates incl. TestLoadDemoSetEndToEnd, 2026-09-27 live re-verification); A4 DATA-04 no-CSD/CCDC-redistribution confirm; A5 offers (IUCr wording blessing / second Janiak institutional-access read — recorded default: offered, prior decline stands / SHA-256 of the 5 SDFs — recorded default SKIP); A6 APPROVED-wording LITERAL approve-or-amend: header `(APPROVED — <UTC date>)`, STATUS LEGEND gains `APPROVED = human sign-off recorded (Phase 8, GATE V 08-11)`, footer `APPROVED <UTC date> (DATA-02 sign-off).` — the token `APPROVED` must appear in all three.
- **SECTION B — SETUP-07/08 live pass:** B1 6-button row presence/order/clipping; B2 Reset restores all defaults (Set A/medium/Random cap 10/normal); B3 post-Reset Save JSON carries `atom_budget: 100`/`broadening_fwhm: 16.0` (Pitfall A); B4 Randomize concrete values; B5 Save default name + `.json` enforce; B6 fresh-session Load reproduces everything; B7 Start apply-first; B8 mid-game Save auto-pauses then resumes cleanly; B9 corrupt JSON / schema_version 2 friendly modal; B10 foreign xtb path normalize-to-auto-detect note; B11 consent persistence; B12 Cleanup only `srp_*`; B13 width no-clip check; plus SETUP_HINTS['before_apply'] Start-only hint visible and no removed 'Apply / Show in Viewer' anywhere.
- **SECTION C — release-audit close:** C1 env (SRP_SPECTRA_DIR default `<cwd>/srp_spectra`); C2 play-to-completion cap-3-class win; C3 REAL xtb leg (live progress, responsive dialog, honest cancel text, `xtb finished: ok` on re-run, ~1-2 min); C4 IR plot + PNG opens outside PyMOL; C5 table row click → mode vectors on srp_xtbopt; C6 README Install reproduce + in-game hints (controls recap, focus hint, negative-frequency line); C7 SIGN-OFF A (data confirmatory — crystalline-state framing TODO STATE.md:118 discharged); C8 SIGN-OFF B (46-row evidence ledger acceptance); C9 restart hygiene; C10 recorded dispositions confirm-or-amend (Selector-Error DEFERRED; hud_logic.idle_tip UNWIRED; xtb_path save-as-is + normalize-on-load; generic_stack_consent CARRIED; SETUP-08 one-machine two-session proof + multi-machine acceptance note).

**Amendment protocol:** numbered fix list → targeted fixes (each re-running gates) → re-run ONLY affected items; per-item approvals accumulate (05-16/07-10 precedent); never approve with a known-broken item.

## Orchestrator directive item folded into the gate (quick-001 reconciliation)

README.md line 57 currently presents biphenyl's orthogonal-rings clash refusal as a **live gameplay behavior** — stale since quick-001 (2026-10-01) excluded biphenyl from the pickup spawn pool + head selection (probe-proven always-clash; the dataset/manifest and TDD/smoke fixtures KEEP it). The checkpoint therefore includes a wording-confirmation item; proposed replacement text (owner may amend):

> "Biphenyl stays in the demo manifest (loadable, viewable, CID-cited) but is excluded from live gameplay pools (pickup spawns + head selection) since 2026-10-01: its orthogonal rings clash at the set geometry (probe-proven always-clash), so it ships as the permanent refuse-path demonstrator in the test suite - the designed 'no invented chemistry' example. In play, the demo set offers 4 stackable species (+ uploads)."

On confirmation this lands as its own `docs(08-11)` commit (or folded into Task 2's amendment commit). Historical 08-*/.planning records stay as-written (verification records).

## Offer / disposition record (defaults per GATE D; owner confirms or amends at the gate)

| Item | Recorded default | Owner verdict |
|------|------------------|---------------|
| IUCr attribution-wording blessing (pyrene + herringbone entries) | OFFERED | _pending_ |
| Second Janiak 2000 institutional-access read attempt | OFFERED (prior decline stands if declined again) | _pending_ |
| SHA-256 of the 5 SDFs | SKIP | _pending_ |
| Selector-Error cosmetic noise | DEFERRED | _pending_ |
| hud_logic.idle_tip | UNWIRED | _pending_ |
| xtb_path persistence | save-as-is + normalize-on-load | _pending_ |
| generic_stack_consent in shared files | CARRIED | _pending_ |
| SETUP-08 proof scope | one-machine two-session (multi-machine = documented acceptance note) | _pending_ |

## Owner Verdict Record (verbatim)

_awaiting orchestrator-returned verdicts per section (A / B / C, incl. the README:57 wording item) — recorded verbatim here on continuation._

## Files Created/Modified

- `.planning/phases/08-demo-data-docs-release-audit/08-11-SUMMARY.md` — this record (checkpoint-presentation state)

## Decisions Made

None yet — GATE V is the owner's act; the executor made no decisions (precondition verification only).

## Deviations from Plan

None - plan executed exactly as written so far (Task 1 staged and presented without self-approval).

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 8 closes (and v1 is releasable) only after: owner "approved" on all sections → Task 2 (APPROVED flip + coupled marker-pin in ONE commit, plus README:57 wording and any width fix/amendments) → Task 3 (10-row ledger flip to Complete, `audit_requirements.py --release` green = zero Pending, full battery `run_gates.py` + `--smoke` incl. smoke 14 RELEASE-E2E + `--xtb` green, ROADMAP Phase 8 ticked 11/11 with the 5 SC evidence lines).
- If NOT approved: numbered gaps recorded here; nothing partially flipped (governance invariant).

---
*Phase: 08-demo-data-docs-release-audit*
*Status: GATE V checkpoint presented 2026-10-01 (UTC) — awaiting owner sign-off*
