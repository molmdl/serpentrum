---
phase: 08-demo-data-docs-release-audit
plan: 10
subsystem: testing
tags: [traceability, requirements-ledger, audit-tool, tdd, docs-05, python3.6]

requires:
  - phase: 07-spectra-ui
    provides: 07-VERIFICATION.md must_haves|Status|Evidence format model; human-certified checkpoint records (01-06 through 07-10) cited as the Evidence human tier
  - phase: 08-demo-data-docs-release-audit (08-02..08-09)
    provides: the artifacts Phase-8 rows cite (test_demo_data.py TestLoadDemoSetEndToEnd, check_docs.py + test_docs_audit.py, smoke 14, help_text.py wiring, tests/test_gui_pins.py)
provides:
  - tools/audit_requirements.py — TDD'd ledger integrity checker (4 checks + --release; 46 canonical IDs hardcoded; 136 cited paths verified)
  - tests/test_audit_requirements.py — 16 fixture-driven tests (embedded fixtures, never the live file)
  - REQUIREMENTS.md Evidence column — 3-tier citations (mech/code/human) for all 46 v1 IDs
  - Checkbox reconciliation: 36-row sweep, 7 historical mismatches flipped; 10 Phase-8 rows stay Pending for GATE V (08-11)
affects: [08-11 GATE V close (--release mode asserts the final 10 flips), any future ledger edit (count drift now fails loudly)]

tech-stack:
  added: []
  patterns:
    - "Ledger-integrity tool with hardcoded canonical-ID list (count drift fails loudly, Pitfall 8)"
    - "Evidence citations = 3-tier (mech / code / human) per requirement row, mirroring 07-VERIFICATION at requirement granularity"
    - "Conservative path-token rule: '/'-bearing tokens need a known suffix or dir prefix; prose (GATE V, dates, '11 of 11') is never path-checked"

key-files:
  created:
    - tools/audit_requirements.py
    - tests/test_audit_requirements.py
  modified:
    - .planning/REQUIREMENTS.md (Evidence column + 7 checkbox flips + footer note; zero Status-cell changes)

key-decisions:
  - "Evidence cites checkpoints, GATE V gets none of the unrun work: Phase-8 rows (human tier) cite 'GATE V (08-11) approval' with NO invented date; pre-Phase-8 human tiers cite the recorded approval dates verbatim (01-06 2026-09-06 through 07-10 2026-09-26)"
  - "Fixture independence: the test's canonical 46-ID list is hardcoded a SECOND time in the test file, so a wrong edit to the tool's list fails the tests, not just the ledger"
  - "release mode is opt-in (--release), default mode allows the 10 Phase-8 Pending rows — single-ownership of the flip stays with GATE V (08-11)"

duration: 11 min
completed: 2026-09-28
---

# Phase 8 Plan 10: Requirements Ledger (DOCS-05 traceability half + TDD integrity tool) Summary

**DOCS-05's traceability half done: all 46 v1 requirement IDs now carry a 3-tier Evidence citation in REQUIREMENTS.md, the 36-row checkbox reconciliation is applied (7 historical mismatches flipped), and a TDD'd integrity tool (tools/audit_requirements.py) mechanically keeps the ledger honest — count drift and evidence rot now fail loudly.**

## Performance

- **Duration:** 11 min
- **Started:** 2026-09-28T03:10:22Z
- **Completed:** 2026-09-28T03:21:32Z
- **Tasks:** 3
- **Files modified:** 3 (2 created, 1 edited)

## Accomplishments

- `tools/audit_requirements.py` (GREEN after strict RED): 4 checks — ids-unique / row-count / evidence-paths / checkbox-agreement — plus `--release` no-pending mode reserved for GATE V (08-11). The 46 canonical IDs are hardcoded so the stale-'44' count-drift class fails loudly. Live run: 4/4 green, 136 cited paths verified; `--release` names exactly the 10 Phase-8 rows.
- Evidence column in `REQUIREMENTS.md`: every one of the 46 rows carries mech (test/smoke/tool) + code (source file) + human (checkpoint, verdict, date) tiers. Phase-8 rows cite the GATE V (08-11) closing checkpoint without inventing dates; Phase-2 partial data approval (2026-09-10) explicitly noted as partial for DATA-02.
- Checkbox reconciliation: flipped SETUP-01, STACK-06, INFRA-01/02/03/05/06 (the exact 7 the live audit named — matching 08-RESEARCH-release-audit's prediction); the 10 Phase-8 rows stay `[ ]` + Pending. Footer note stamps the reconciliation.
- Gates re-run green after the ledger edit: 927 unittests, gates 1-3 all PASS.

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: Failing tests for the audit tool** — `792085b` (test)
2. **Task 1 GREEN: tools/audit_requirements.py** — `0dc615e` (feat)
3. **Task 2: Evidence column, all 46 rows** — `439a471` (docs)
4. **Task 3: Checkbox reconciliation + footer note** — `f0e3ada` (docs)

## Files Created/Modified

- `tools/audit_requirements.py` — CLI+import dual (check_purity.py precedent), stdlib-only, py3.6: `run_checks(md_text, repo_root, release=False)` → `[(name, ok, message), ...]`; `main()` prints flushed PASS/FAIL lines, exit 0/1, `--release` flag. No tools/__init__.py.
- `tests/test_audit_requirements.py` — 16 tests on embedded fixtures: Fixture A (historical 7-mismatch shape), Fixture B (reconciled + one bad Evidence path), edge cases (unknown status named, duplicate ID, 45-row count drift, prose tokens never path-checked), CLI exit-code tests.
- `.planning/REQUIREMENTS.md` — Evidence column (46 rows), 7 checkbox flips, reconciliation footer note; zero Status-cell changes (`git diff` shows only row extensions).

## Decisions Made

- **Evidence honesty:** Phase-8 rows' human tier cites "GATE V (08-11) approval" with *no* date (the checkpoint hasn't run); pre-Phase-8 human tiers cite recorded dates verbatim from the phase summary corpus (01-06 2026-09-06 / 03-08 2026-09-12 / 04-07 2026-09-13 / 04-09 2026-09-14 / 05-16 2026-09-18..20 / 5.1-06 2026-09-25 / 5.2-09 2026-09-26 / 06-12 2026-09-26 / 07-06+07-10 2026-09-26 / Phase-2 pi-stack 2026-09-10).
- **Fixture independence:** the test hardcodes the canonical 46-ID list a second time, so a wrong edit to the tool's list fails the test suite, not merely the live run.
- **Path-token conservatism:** only tokens with `/` AND (known suffix OR known dir prefix) are disk-checked — prose like "GATE V (08-11) approval", "11 of 11", "(2026-09-26)" is never falsely flagged.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. The deliberate mid-plan state (default mode green while `--release` reports the 10 Pending rows, exit 1) is the designed boundary — GATE V (08-11) alone flips those rows and takes `--release` green.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- GATE V (08-11, the only human-verify checkpoint) owns: flipping the 10 Phase-8 rows to Complete + `[x]`, then `python3.6 tools/audit_requirements.py --release` as the mechanical close-out leg (must report zero Pending).
- Any future edit to REQUIREMENTS.md is now guarded: `python3.6 tools/audit_requirements.py` must stay green (evidence paths, count, uniqueness, checkbox agreement).
- No blockers carried forward.

---
*Phase: 08-demo-data-docs-release-audit*
*Completed: 2026-09-28*
