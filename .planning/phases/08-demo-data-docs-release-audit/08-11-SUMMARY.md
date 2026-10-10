---
phase: 08-demo-data-docs-release-audit
plan: 11
subsystem: release-audit
tags: [gate-v, human-verify, data-approval, release-close, requirements-ledger, pymol, xtb]
status: complete

requires:
  - phase: 08-demo-data-docs-release-audit (08-02..08-10)
    provides: DRAFT DATA_SOURCES.md with the 3 content edits; 6-button row + persistence wiring; README/help/docs; smoke 14 RELEASE-E2E; doc-vs-code audit; 46-row evidence ledger
  - phase: 01..07 + 5.1/5.2/5.3
    provides: all 36 pre-Phase-8 requirements already Complete with human-certified evidence
provides:
  - The v1 release sign-off: owner verdict "approved" across all three GATE V sections (A data sign-off / B 6-button + educator round-trip / C release close incl. real xtb), recorded verbatim
  - APPROVED-headed serpentrum/data/DATA_SOURCES.md (governance evidence intact: UNVERIFIED quarantine, herringbone negative-evidence block, [JAN2000] SCOPE CAVEAT) with the coupled marker-pin flip in the same commit
  - 46/46 v1 requirements Complete (10 Phase-8 rows flipped; audit_requirements.py --release AUDIT-OK) + ROADMAP Phase 8 closed 13/13
  - Final full battery green: gates 1-3 (995 unittests) + --smoke (11 required SMOKE-OK incl. 14 RELEASE-E2E and 12 incl. STAGE6 LINES) + --xtb (normal termination)
affects: [v1 release (this gate IS the release act), v2 planning (ledger is the v1 baseline)]

tech-stack:
  added: []
  patterns:
    - "Single consolidated release gate: three sections presented at one blocking checkpoint:human-verify (merges the old 08-02/08-05/08-12 checkpoints)"
    - "Coupled literal flip: DATA_SOURCES.md DRAFT->APPROVED markers and the tests/test_stacking_dataset.py marker pin MUST land in the same commit (marker-pin trap)"
    - "Per-item approval accumulation across rounds (05-16/07-10 precedent): amendments produce a numbered fix list, only affected items re-run"
    - "Release sign-off date convention: planning-doc stamps are UTC git-commit dates, never the HKT local date (STATE.md:144)"

key-files:
  created:
    - .planning/phases/08-demo-data-docs-release-audit/08-11-SUMMARY.md
  modified:
    - serpentrum/data/DATA_SOURCES.md (DRAFT->APPROVED flip: header + STATUS LEGEND line + footer; everything else byte-identical)
    - tests/test_stacking_dataset.py (required-markers pin 'DRAFT' -> 'APPROVED', same commit as the doc flip)
    - .planning/REQUIREMENTS.md (10 Phase-8 rows Complete + checked; footer stamped with the release sign-off)
    - .planning/ROADMAP.md (Phase 8 ticked; Progress row 13/13 Complete with SC evidence)

key-decisions:
  - "A6 approved-wording literal approved AS PROPOSED by the owner; applied with UTC date 2026-10-10 (header '(APPROVED — 2026-10-10)', legend line, footer)"
  - "No width-fix amendment: Section B B13 height/clipping resolved by the debug-06 fixed-size dialog + two-column Setup (67c7943/cbe02d6); the conditional width fix correctly did not trigger"
  - "Offer dispositions: recorded GATE D defaults apply (SHA-256 of the 5 SDFs SKIP; second Janiak-2000 institutional-access attempt = prior decline stands; IUCr attribution-wording = offered/default recorded)"
  - "C10 dispositions confirmed as recorded at GATE D; Q2 items (atom budget + xtb threads) are now in-game features (08-12)"

# Metrics
duration: ~24min agent time (Task-1 staging ~13 min + Tasks 2-3 continuation ~11 min); owner walk-through + amendment rounds spanned 2026-10-01..2026-10-11
completed: 2026-10-10
---

# Phase 8 Plan 11: GATE V — Consolidated Verification + Release Close Summary

**v1 release signed off at the phase's single blocking human gate: owner verdict "approved" across all three sections; DATA_SOURCES.md flipped DRAFT→APPROVED with the coupled marker pin in one commit; the 46-row ledger flipped to 46/46 Complete (`--release` AUDIT-OK); full battery green (995 unittests, 11 required smokes incl. RELEASE-E2E + STAGE6 LINES, Windows xtb normal termination); ROADMAP Phase 8 closed 13/13.**

## Performance

- **Duration:** ~24 min agent time (Task 1 staging ~13 min, 2026-10-01; Tasks 2-3 continuation ~11 min, 2026-10-10 UTC) — owner walk-through + amendment rounds spanned 2026-10-01..2026-10-11 outside agent time
- **Started:** 2026-10-01T16:05:56Z (UTC, Task 1 staging); continuation resumed 2026-10-10T16:14:08Z (UTC) after the owner's "approved"
- **Completed:** 2026-10-10 (UTC)
- **Tasks:** 3/3 complete (Task 1 = the owner-approved checkpoint itself; Tasks 2-3 = the conditional close-out, executed on "approved")
- **Files modified:** 5 (DATA_SOURCES.md, test_stacking_dataset.py, REQUIREMENTS.md, ROADMAP.md, this SUMMARY)

## Accomplishments

- The v1 release act completed: the owner read, walked, and approved the full product live in real Windows PyMOL 2.5.0 across 2026-10-01..2026-10-11 (three sectioned rounds with amendment insertions in between), then typed "approved" — recorded verbatim here as the v1 release sign-off.
- The approval flip landed as ONE atomic commit (3fd30cf): the three DRAFT markers → the A6-approved APPROVED literal + the coupled `tests/test_stacking_dataset.py` marker pin (marker-pin trap honored), with §3 UNVERIFIED quarantine, the herringbone negative-evidence block, and the [JAN2000] SCOPE CAVEAT byte-identical.
- The requirements ledger closed: 10 Phase-8 rows flipped to Complete (table + checkboxes), DOCS-04/DOCS-05 human evidence cites the GATE V verdict + date, footer stamped with the release sign-off; `tools/audit_requirements.py --release` → AUDIT-OK (46/46 Complete, zero Pending, checkboxes agree, 136 evidence paths exist).
- The final full battery ran green from repo root: `run_gates.py` (gates 1-3, 995 unittests), `--smoke` (11 required smokes, verdict = flushed SMOKE-OK sentinels, incl. 14 RELEASE-E2E and 12 PLOT-RENDER with STAGE6 LINES), `--xtb` (gate 5, Windows xtb 6.7.1pre from WSL, "normal termination of xtb").
- ROADMAP closed Phase 8: checkbox ticked in the Phases list, Progress row 13/13 Complete with one-line evidence for all 5 success criteria.

## Precondition Verification (Task 1 staging gate — round 1, kept as evidence)

| # | Precondition | Result | Evidence |
|---|--------------|--------|----------|
| 1 | Default gate battery green | PASS | `python3.6 tests/run_gates.py` → 937 unittests OK (baseline at presentation); gates 1 (syntax + plugin-path safety), 2 (AST purity), 3 (scoped unittest) all PASS; "run_gates: all gates green" |
| 2 | 08-01..08-10 SUMMARYs present | PASS | 10 SUMMARY files on disk in the phase dir |
| 3 | DATA_SOURCES.md DRAFT-headed with 08-02 edits | PASS | line 1 `(DRAFT — NOT APPROVED)`; stale §1 NOTE rewritten to the 03-05 shipment fact; [COD4003564] carries `Chemistry of Materials 2020, 32 (12), 5162–5172` with the Crossref trail; 2026-09-27 license re-verification stamp |
| 4 | 6-button row in gui.py | PASS | Reset / Randomize / Save Setup / Load Setup / Cleanup model / Start, right-aligned, spec order |
| 5 | Smoke 14 registered | PASS | REQUIRED_SMOKES entry `smoke/14_release_e2e_smoke.py`; file on disk |
| 6 | Ledger Pending rows = the 10 Phase-8 rows | PASS | `tools/audit_requirements.py` default AUDIT-OK; `--release` FAIL naming exactly the 10 Phase-8 IDs (pre-approval state) |
| 7 | Coupled marker pin state | CONFIRMED | `tests/test_stacking_dataset.py` required list starts with `'DRAFT'` (the same-commit flip target for Task 2) |

## GATE V — Owner Verdict Record (verbatim)

**Verdict: "approved"** — typed by the owner 2026-10-11 (owner's local HKT date; UTC 2026-10-10 per the repo date convention, STATE.md:144 — planning-doc dates are UTC with git commit dates authoritative) after the resumed live walk-through in real Windows PyMOL 2.5.0; final launch console clean, the previously-known Selector-Error startup lines absent after the debug-06 fix. This is the v1 release sign-off (DATA-02/04, DOCS-02/05, and the phase's DOCS-05 human half).

### Section verdicts (walk-through rounds 2026-10-01..2026-10-11)

| Section | Scope | Owner verdict |
|---------|-------|---------------|
| **A** — DATA-02/04/DOCS-02 sign-off | Full DATA_SOURCES.md attribution document (per-molecule CID/formula/[VERIFIED] checklist, measured distances + COD IDs/DOIs/license quotes, per-source license blocks, §3 UNVERIFIED quarantine) incl. the D3-humanized dataset explanation | **approved** — whole-document data sign-off; A6 approved literal AS PROPOSED (applied verbatim, see below) |
| **B** — SETUP-07/08 6-button live pass + educator round-trip | 6-button row, Reset/Randomize/Save/Load round-trip, fresh-session Load reproduction, corrupt-schema + foreign-xtb-path handling, consent persistence, Cleanup srp_*-only, Start-only hint | **approved** — 6-button persistence + educator round-trip PASS; B14 tooltips PASS; B15 Performance visible PASS; B13 height OK after debug-06's fixed-size dialog + two-column Setup — no width-fix amendment needed |
| **C** — release-audit close incl. REAL xtb | Full release flow live: play-to-completion, stream/cancel/relaunch → `xtb finished: ok`, IR plot + PNG, table→mode vectors, README reproduce spot-check, restart hygiene, 46-row evidence ledger review | **approved** — cap-10 win evidenced by the 2026-10-01 log; Multiwfn-parity IR curve reproduced to 4.9e-9; C10 dispositions confirmed as recorded at GATE D, with the Q2 items now features |

**Amendment protocol across rounds:** all amendment-round fixes landed green during the paused/resumed gate (per-item approvals accumulate; never approve with a known-broken item) — see the ledger below. Final round: console clean, no open items.

## A6 approved literal (as applied, Task 2)

- Header line 1: `(DRAFT — NOT APPROVED)` → `(APPROVED — 2026-10-10)`
- STATUS LEGEND gains: `APPROVED = human sign-off recorded (Phase 8, GATE V 08-11).`
- Footer last line: `DRAFT — NOT APPROVED.` → `APPROVED 2026-10-10 (DATA-02 sign-off).`

The token `APPROVED` appears in all three (grep count = 3; `DRAFT — NOT APPROVED` count = 0). Everything else in the file is byte-identical — the §3 UNVERIFIED do-not-ship list, the herringbone negative-evidence block, and the [JAN2000] SCOPE CAVEAT survive approval as governance evidence. 2026-10-10 is the UTC date of the sign-off and of commit 3fd30cf (the owner typed the verdict during 2026-10-11 HKT = 2026-10-10 UTC).

## Offer / disposition record (Section A5 + C10 — FINAL)

| Item | Recorded default (GATE D) | Disposition at GATE V |
|------|---------------------------|----------------------|
| SHA-256 of the 5 SDFs | SKIP | **SKIP** — recorded default stands (owner blanket-approved) |
| Second Janiak 2000 institutional-access read attempt | OFFERED (prior decline stands if declined again) | **Prior decline stands** |
| IUCr attribution-wording (pyrene + herringbone entries) | OFFERED | **Offered/default recorded** (wording stays as shipped) |
| Selector-Error cosmetic noise | DEFERRED (07-10) | **Confirmed DEFERRED** — unaffected by today's clean launch (startup lines absent after debug-06) |
| hud_logic.idle_tip | UNWIRED | **Confirmed UNWIRED** |
| xtb_path persistence | save-as-is + normalize-on-load | **Confirmed** save-as-is + normalize-on-load |
| generic_stack_consent in shared files | CARRIED | **Confirmed CARRIED** in shared files |
| SETUP-08 v1 proof scope | one-machine two-session | **Confirmed** one-machine two-session proof, multi-machine = documented acceptance note |

**Amendments recorded alongside the dispositions:** atom budget + xtb threads are now in-game features (08-12); the debug-06 window quirk is RESOLVED 2026-10-10 (fixed-size dialog `67c7943`, two-column Setup `cbe02d6`, archived `e770513`); y-label epsilon units (`75cd278`); new 'intensity (km/mol)' discrete-sticks plot mode (quick-002, final commit `898030d`).

## Amendment-round ledger (all landed green during the paused/resumed gate)

| Round | Item | Commits |
|-------|------|---------|
| quick-001 | Biphenyl gameplay exclusion + README reconciliation (excluded from live gameplay pools since 2026-10-01, probe-proven always-clash; permanent refuse-path demonstrator; 4 stackable species in play) | `43d8cb0`/`4740335`/`271dfed`; 08-13's `054096c` |
| 08-12 insertion | Performance controls (atom budget + xtb threads spinboxes) + D2 honest completion label | `9efc8e6`/`e4bb291`/`53dd655`/`6dff796` |
| 08-13 insertion | Tooltips (13 controls + 6 buttons) + D3 humanized dataset explanation + D1 humanized README | `5c987d2`/`f6a3dc5`/`0c47d4c`/`054096c` |
| Mid-gate verification | Multiwfn-parity IR curve (reproduced to 4.9e-9) + README biphenyl concision | `5ece303`; `c9bbc06` |
| Mid-gate verification | Epsilon y-axis label | `75cd278` |
| debug-06 | Window move/resize quirk RESOLVED (fixed-size dialog + two-column Setup + height basis) | `67c7943`/`cbe02d6`/`e770513` (archive) |
| quick-002 | epsilon plot-mode rename + km/mol intensity discrete-sticks mode (final owner label amendment) | `2608cca`/`496d4e2`/`898030d` |

## Task Status

| Task | Name | Status |
|------|------|--------|
| 1 | GATE V — consolidated verification + release close (checkpoint:human-verify, blocking) | **APPROVED** by owner (verdict recorded verbatim above) |
| 2 | Approval flip + coupled test-pin edit + owner amendments (same commit) | **Complete** — commit 3fd30cf (no width fix: conditional branch correctly not triggered) |
| 3 | Post-approval close-out — ledger flip + final battery + roadmap close | **Complete** — commit 7e0ddc9 (audit + battery results below) |

## Task Commits

1. **Task 1: GATE V checkpoint staging + presentation** — `6c73e7b` (docs, 2026-10-02: preconditions green, checkpoint presented; owner walk-through + amendment rounds followed)
2. **Task 2: DATA_SOURCES.md approved — DATA-02/04/DOCS-02 sign-off (GATE V)** — `3fd30cf` (docs; doc flip + coupled marker pin in ONE commit, per the marker-pin trap)
3. **Task 3: release close-out — 46/46 v1 requirements Complete (phase 8 approved)** — `7e0ddc9` (docs; REQUIREMENTS.md 10-row flip + footer stamp, ROADMAP phase tick + 13/13 Progress row)
4. **Summary finalization** — this file, its own `docs(08-11): finalize GATE V summary — v1 release sign-off` commit

## Final battery results (Task 3, from repo root, 2026-10-10 UTC)

| Leg | Verdict | Detail |
|-----|---------|--------|
| `python3.6 tools/audit_requirements.py --release` | **AUDIT-OK** | 46/46 canonical IDs unique; 46 ID rows; 136 evidence paths exist; checkboxes agree 46/46; zero Pending rows |
| `python3.6 tests/run_gates.py` | **all gates green** | 995 unittests OK; gate 1 syntax + plugin-path safety PASS; gate 2 purity (AST) PASS; gate 3 scoped unittest PASS |
| `python3.6 tests/run_gates.py --smoke` | **all gates green** | gate 4 headless smokes (required) PASS — 11 flushed SMOKE-OK sentinels incl. `SMOKE-OK RELEASE-E2E` (smoke 14) and `SMOKE-OK PLOT-RENDER` (smoke 12, incl. STAGE6 LINES); informational 02 (known non-blocking offscreen dead-end) FAIL, 09/11 PASS. Verdict = flushed sentinels, never exit codes |
| `python3.6 tests/run_gates.py --xtb` | **all gates green** | gate 5 xtb probe PASS — Windows xtb 6.7.1pre invoked from WSL via the .exe with `/mnt/c`-backed cwd; asserts `normal termination of xtb` in output |

## Files Created/Modified

- `serpentrum/data/DATA_SOURCES.md` — APPROVED-headed attribution document (three-marker flip; quarantine + negative-evidence + scope-caveat intact) — 3fd30cf
- `tests/test_stacking_dataset.py` — required-markers pin `'DRAFT'` → `'APPROVED'` (same commit as the doc flip) — 3fd30cf
- `.planning/REQUIREMENTS.md` — 10 Phase-8 rows Complete + checked; DOCS-04/DOCS-05 cite the GATE V verdict + date; footer stamped 2026-10-10 — 7e0ddc9
- `.planning/ROADMAP.md` — Phase 8 ticked `[x]`; Progress row 13/13 Complete + 2026-10-10 + SC1..SC5 evidence — 7e0ddc9
- `.planning/phases/08-demo-data-docs-release-audit/08-11-SUMMARY.md` — this final record

## Decisions Made

- A6 approved literal applied exactly as approved (header/legend/footer), dated **2026-10-10 UTC** — the repo's date rule (STATE.md:144: planning-doc dates are UTC, git commit dates authoritative, dev shell is HKT; never stamp from the local date) reconciles the owner's local sign-off date (2026-10-11 HKT) with the UTC commit date; the SUMMARY records both so neither reading is lost.
- No width fix: B13 passed via the debug-06 fixed-size dialog + two-column Setup; the plan's conditional width-fix branch (gui.py setMinimumWidth raise) correctly did not trigger, so `serpentrum/gui.py` is untouched in Tasks 2-3.
- DOCS-04/DOCS-05 human-certified evidence cites the GATE V checkpoint verdict + date (verdict "approved" 2026-10-10), per the Task 3 spec; all other flipped rows carry dated GATE V verdict references.
- VERIFICATION.md (08-VERIFICATION.md) intentionally NOT created by this executor — the phase verifier runs after this continuation and owns it.

## Deviations from Plan

None — plan executed exactly as written. The conditional branches resolved exactly as the plan specified: Task 1 approved → Tasks 2-3 executed; the conditional width fix not triggered (resolved earlier via debug-06); no defect fixes were needed (the first post-flip battery run was green).

## Issues Encountered

None (informational smoke 02 FAIL is the documented non-blocking offscreen-dialog dead end — 01-05 disposition, not an issue).

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- **v1 is releasable.** All 46 v1 requirements Complete with human-certified evidence; the release sign-off is recorded verbatim above; the phase's 5 success criteria each have named evidence (ROADMAP Progress row).
- Phase 8 verification (the phase verifier + 08-VERIFICATION.md) is the next orchestrator step, then v1 final wrap (STATE.md project closure; any v2 planning starts from REQUIREMENTS.md's v2 section).
- Known accepted-as-is surface for any future release notes: Selector-Error zoom_noise cosmetic (07-10) DEFERRED; hud_logic.idle_tip UNWIRED; biphenyl excluded from live gameplay (quick-001) but loadable/viewable/CID-cited in the manifest; SET A geometry is crystalline-state-framed (SCOPE CAVEAT + consent-label disclosure, per the Phase 8 TODO discharge).

---
*Phase: 08-demo-data-docs-release-audit*
*Plan: 08-11 (GATE V)*
*Status: v1 release signed off 2026-10-10 (UTC) — owner verdict "approved" recorded verbatim*
