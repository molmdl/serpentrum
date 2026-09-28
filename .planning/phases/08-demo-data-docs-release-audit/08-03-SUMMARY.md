---
phase: 08-demo-data-docs-release-audit
plan: 03
subsystem: testing
tags: [docs-audit, unittest, tdd, check_docs, gate-suite, python3.6, stdlib]

# Dependency graph
requires:
  - phase: 08-demo-data-docs-release-audit
    provides: final shipped corpus — post-08-07 README rewrite, post-08-06 help_text + post-08-09 GUI wiring, post-08-08 6-button bottom row
provides:
  - tools/check_docs.py — 7-family doc-vs-code audit (dual CLI/import, check_purity precedent)
  - tests/test_docs_audit.py — 23-test wrapper riding gate-3 unittest discovery (no run_gates.py edit)
  - permanent tamper-proof pins: vibe block, TBD/sECDpent absence, control literals, composed numeric claims, install route, path refs, claim bans
affects: [release-gate (DOCS-04 leg B reproduce-steps checkpoint), any future README/code/data edit]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Check functions take injected text/sources dicts -> tamper fixtures never touch the repo (both-direction testing)"
    - "Numeric tokens COMPOSED from imported/loaded sources of truth (setup_logic, molecule_data) — never hardcoded in the tool"
    - "Bare-number digit-guard regex (?<![\\d.])N(?![\\d]) so '6.0' cannot hide inside '16.0'"

key-files:
  created:
    - tools/check_docs.py
    - tests/test_docs_audit.py
  modified: []

key-decisions:
  - "Vibe block pinned byte-exact INCLUDING trailing spaces on lines 1/3 (the approved block by construction)"
  - "'Apply / Show in Viewer' pinned via the claim-ban list, not the literal list — the control is removed (08-08)"
  - "Focus hint pinned as the help_text.GAME_FOCUS_HINT reference in gui_game.py, never the bare literal (08-09 single-sourcing)"
  - "'animation' negation window kept tiny and explicit: same-sentence 'no ' or 'static' prefix only"

patterns-established:
  - "Audit tool pattern: per-family (ok, message) functions + run_all aggregator + flushed PASS/FAIL CLI with exit 0/1"
  - "Tamper-proof by construction: every live PASS test paired with a fixture FAIL test in the same class"

# Metrics
duration: 23 min
completed: 2026-09-28
---

# Phase 8 Plan 03: Doc-vs-Code Audit Harness Summary

**DOCS-04 leg A shipped: `tools/check_docs.py` + `tests/test_docs_audit.py` — 7 check families proving README/help claims match code and data reality on every gate run, tamper-proof by construction (23 wrapper tests, both directions proven)**

## Performance

- **Duration:** 23 min
- **Started:** 2026-09-28T02:41:42Z
- **Completed:** 2026-09-28T03:04:33Z
- **Tasks:** 1 TDD feature (RED + GREEN)
- **Files modified:** 2 created

## Accomplishments

- 7 check families live and green on the shipped corpus: vibe block (byte-exact lines 1-4), placeholders (zero TBD; zero sECDpent in README+spec.md), control literals (20 pins across gui/gui_setup/gui_game/gui_spectra/gui_plot/input), numeric claims (25 tokens composed from setup_logic + molecule_data-loaded stacking/manifest), install recipe, back-ticked path refs, claim bans
- Numeric drift is now a gate failure: any future edit to SPEED_TIERS, BOX_PRESETS, DEFAULTS, stacking geometry, manifest CIDs/atom counts or HESSIAN_WARNING without a matching README edit fails the default gate
- The removed 'Apply / Show in Viewer' control name can never reappear in README (claim-ban), and the post-08-08/09 literals are pinned; wizard prompt + all three tab names pinned
- Rides the default gate suite via gate-3 unittest discovery — `tests/run_gates.py` untouched; `python3.6 tools/check_docs.py` also runs standalone (7/7 PASS, exit 0)

## Task Commits

TDD cycle, two atomic commits:

1. **RED: failing audit wrapper** - `0c9f470` (test)
2. **GREEN: check_docs implementation** - `a609e2b` (feat)

**Plan metadata:** _this file's docs commit below_

## Files Created/Modified

- `tools/check_docs.py` — the audit tool: 7 per-family `(ok, message)` check functions with injectable text/sources; `collect_numeric_context()` composing expected tokens from `setup_logic` constants and `molecule_data`-loaded stacking/manifest; `run_all()` aggregator; CLI with flushed PASS/FAIL lines and exit 0/1; stdlib only, python3.6, %-formatting
- `tests/test_docs_audit.py` — 23 wrapper tests: one class per family, each pairing live PASS cases against the real repo with tamper FAIL fixtures (mutated in-test string corpora), plus the `run_all` integration test the gate runs

## Decisions Made

- **Vibe block pinned byte-exact including trailing spaces** on lines 1 and 3 — the current README's block is the approved one by construction (plan behavior item 1)
- **'Apply / Show in Viewer' is pinned through the claim-ban list, not the literal list** — 08-08 removed the control; Start (04-06 apply-first) is the only materialize route
- **Focus hint pinned as the `help_text.GAME_FOCUS_HINT` reference token** in gui_game.py, not the bare literal — 08-09 single-sourced the string into help_text.py
- **Bare-number digit guard** `(?<![\d.])N(?![\d])` for all pure-number tokens so e.g. `6.0` cannot false-pass inside `16.0` (broadening vs speed tier collision avoided)
- **'animation' allowlist window kept tiny/explicit**: same-sentence `no ` or `static` prefix only (the README static-vectors disclaimer shape); tested in both directions even though the live README contains no 'animation' today

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. RED failed as designed (`ModuleNotFoundError: check_docs`); GREEN passed all 23 tests first try; gates green first try (888 -> 911 unittests).

## Verification Evidence

- `python3.6 -m unittest tests.test_docs_audit -v` -> 23 tests, OK (live PASS + tamper FAIL both proven per family)
- `python3.6 tests/run_gates.py` -> all gates green (gate 1 syntax/path-safety, gate 2 AST purity, gate 3 scoped discovery: 911 unittests OK) — the audit runs via gate-3 discovery, no `run_gates.py` edit
- `python3.6 tools/check_docs.py` from repo root -> 7 per-check PASS lines + `check_docs: 7/7 checks PASS`, exit 0
- Manual tamper sanity (temp copy in /tmp, real README untouched): copy with `TBD` appended -> `placeholder ban hits: 'TBD' found in README.md` (rejected); copy with `Apply / Show in Viewer` -> `banned claim 'Apply / Show in Viewer' present` (rejected); real README re-checked green afterwards

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- DOCS-04 leg A is permanent and tamper-proof; the reproduce-steps leg (leg B) lives in the release UAT checklist (08-10/08-11 GATE V closing checkpoint)
- Solid base for 08-04+ phase-close plans: any docs/data/code drift now fails the default gate before human verification

---
*Phase: 08-demo-data-docs-release-audit*
*Completed: 2026-09-28*
