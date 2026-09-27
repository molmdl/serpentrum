---
phase: 08-demo-data-docs-release-audit
plan: 06
subsystem: docs
tags: [help-text, imaginary-note, imaginary, tdd, pure, ascii, gate-D, docs-03]

requires:
  - phase: 08-demo-data-docs-release-audit
    provides: GATE D decision record (08-01-SUMMARY.md) — d2-option-b-two-tier negative-freq wording, d4-confirm-all help-text defaults
  - phase: 07-spectra-ui
    provides: spectra_ui pinned builders (freq_label/table_rows/run_status_lines) + the 07-01 co-location/test-family conventions
provides:
  - imaginary_note(freqs) — the GATE D owner-approved two-tier negative-frequency guidance line (PURE, TDD'd, ASCII)
  - serpentrum/help_text.py — GAME_FOCUS_HINT and CONTROLS_RECAP constants, Start-only SETUP_HINTS, state-driven game_hint/spectra_hint with loud ValueError contract
  - drift alarm: GAME_FOCUS_HINT proven equal to the live gui_game.py literal (08-09's rewiring update point)
affects: [08-09 (help/hint wiring), 08-03 (doc-vs-code audit pins), 08-07 (README wording consistency)]

tech-stack:
  added: []
  patterns:
    - "read-decision STEP 0: extract the owner verdict from the gate SUMMARY before writing literals"
    - "drift alarm: adjacent-string-literal reconstruction via tokenize to pin a PURE constant against its current GUI render site"
    - "negative pin: module source greps for a removed-control token (anti-reference) inside the test suite"

key-files:
  created: [serpentrum/help_text.py, tests/test_help_text.py]
  modified: [serpentrum/spectra_ui.py, tests/test_spectra_ui.py]

key-decisions:
  - "GATE D d2-option-b-two-tier implemented verbatim: <20i benign tier counts ALL imaginary modes; >=20i saddle tier WINS and counts ONLY the large imaginary modes; boundary -20.0 -> saddle (strict <)"
  - "Saddle-tier count semantics pinned by test case [-60.0, -3.0] -> 1 large (count matches the tier, not the whole imaginary set)"
  - "help_text imports NOTHING (not even stdlib) — purity gate 2 confirms PURE auto-classification with zero registration edits"

duration: 14 min
completed: 2026-09-28
---

# Phase 8 Plan 06: DOCS-03 Help-Text Pure Half Summary

**GATE D d2-option-b-two-tier imaginary_note shipped in spectra_ui (PURE, TDD'd, ASCII) plus a new help_text.py single-sourcing the canonical focus hint, Start-only setup hints, and state-driven game/spectra next-action hints — zero GUI edits.**

## GATE D Verdict (read-decision STEP 0 — recorded verbatim, 08-01-SUMMARY.md)

**(2) Negative-frequency wording — CHOSEN: `d2-option-b-two-tier` (owner, 2026-09-28):**

`imaginary_note(freqs)` (08-06 implements, spectra_ui.py, co-located after freq_label/table_rows; 08-09 renders in the Spectra log):

- No negative → `None`.
- Any freq < 0 with ALL imaginary modes `< 20.0` (strict):
  `'%d small imaginary mode(s) (<20i cm-1): soft inter-stack modes, physical for molecular stacks'`
- Any imaginary mode `>= 20.0`:
  `'%d large imaginary mode(s) (>=20i cm-1): possible saddle point - check the structure'`
- Boundary `-20.0` → the SADDLE line (strict `<` threshold). Count = number of imaginary modes. All ASCII. The ≥20i tier has never been observed here (wording owner-approved now).

**Count semantics (pin):** the benign tier counts ALL imaginary modes; the saddle tier counts ONLY the large (>=20i) imaginary modes — pinned by the test case `[-60.0, -3.0] -> '1 large ...'`.

**Related GATE D dispositions this plan honors / leaves UNWIRED:**

- **`hud_logic.idle_tip` stays UNWIRED** (d4 item 6, CONFIRMED at gate) — this plan wires nothing, creates no render sites; 08-09 owns wiring.
- **Help-text researched defaults CONFIRMED** as `d4-confirm-all` (all verbatim literals).
- **d1-option-c-staleness:** `'random'` stays deterministic records[0] (= benzene); the false 'head will be randomized at game start' success-text fix is 08-09's scope, NOT touched here.

## Performance

- **Duration:** 14 min
- **Started:** 2026-09-28T02:10Z (approx., worktree HEAD 8b9f3bd)
- **Completed:** 2026-09-28T02:21Z
- **Tasks:** 2/2 (both strict TDD: RED + GREEN commits each)
- **Files modified:** 4 (all in `files_modified` frontmatter; 424 insertions, **0 deletions**)

## Accomplishments

**Task 1 — `imaginary_note(freqs)` in spectra_ui.py** (7 tests, TestImaginaryNote):

- Empty/no-negative input → `None`; strict `< 20.0` benign tier; `>= 20.0` saddle tier wins; boundary `-20.0` → saddle; house `(s)` style kept for singular counts; ASCII hyphen / `cm-1` per table-header convention; ASCII-only sweep on both tiers.
- Co-located after `table_rows` per the 07-01 contract; **zero edits** to run_status_lines / freq_label / table_rows signatures or literals (all 20 pre-existing pinned tests stayed green).
- Docstring documents the contract: "One ASCII guidance line when any freq < 0, else None; wording/cutoffs owner-approved at GATE D (08-01)" — including that the >=20i tier is owner-approved-but-never-observed here (honest for unobserved large-|imag| values).

**Task 2 — `serpentrum/help_text.py`** (17 tests, new PURE module):

- `GAME_FOCUS_HINT` = the EXISTING gui_game.py:320-323 literal (canonical single source); **drift-alarm test** reconstructs adjacent source literals via `tokenize` and proves the constant equals the live GUI literal — 08-09 Task 1 replaces the GUI literal with a constant reference and updates this assertion in the same commit (comment left in the test).
- `CONTROLS_RECAP` pins the GAME-10 amended contract (180-degree-only turn veto; Pause/Resume, Restart and Get Spectra are buttons).
- `SETUP_HINTS['before_apply']` / `['after_apply']` — START-ONLY vocabulary; the removed preview control is referenced nowhere in the module (negative pin: the literal token count in help_text.py is 0).
- `game_hint` (5 states) + `spectra_hint` (4 states): exact-string pins per state; loud `ValueError` with the legal vocabulary on unknown states. `spectra_hint('pre_run')` and `('running')` re-export the gui_spectra.py:130-132 and :222-223 literals verbatim (single-sourced here; 08-09 rewires the sites without changing the pinned text).
- Module sweep asserts EVERY public string pure ASCII. help_text.py imports NOTHING — purity gate auto-classifies PURE, zero registration edits.

## Verification evidence

- `python3.6 -m unittest tests.test_spectra_ui -v` — 27 tests OK (7 new + all 07-01 pins green)
- `python3.6 -m unittest tests.test_help_text -v` — 17 tests OK
- `python3.6 tests/run_gates.py` — gate 1 (syntax + plugin-path) PASS, gate 2 (AST purity) PASS, gate 3 (scoped unittest discover, 840+ legacy plus 24 new) PASS; full run green after every task
- `grep -n "import" serpentrum/help_text.py` — only the docstring prose "Stdlib imports"; zero import statements
- `grep -c "Apply / Show in Viewer" serpentrum/help_text.py` → 0
- `git diff --stat 8b9f3bd..HEAD` → 4 files, 424 insertions, **0 deletions** — test_spectra_ui.py got ADDITIONS ONLY (the pinned 07-01 classes are byte-untouched)

## Task Commits

1. `fff57b7` — **test(08-06)**: TestImaginaryNote RED (7 failing tests, GATE D literals/cutoffs)
2. `73530b3` — **feat(08-06)**: imaginary_note GREEN in spectra_ui.py
3. `70e9903` — **test(08-06)**: test_help_text.py RED (17 tests, all fail on missing module)
4. `897bc23` — **feat(08-06)**: help_text.py GREEN (PURE module created)

**Plan metadata:** `docs(08-06)` commit follows this file (stages 08-06-PLAN.md + this SUMMARY only).

## Files Created/Modified

- `serpentrum/help_text.py` (created) — the DOCS-03 PURE text layer: constants, SETUP_HINTS, game_hint/spectra_hint
- `tests/test_help_text.py` (created) — 17 pins incl. tokenize-based drift alarm + removed-control negative pin
- `serpentrum/spectra_ui.py` (modified, +32/-0) — imaginary_note after table_rows
- `tests/test_spectra_ui.py` (modified, +53/-0) — TestImaginaryNote class appended; 07-01 pins untouched

## Decisions Made

- Implemented the GATE D d2-option-b-two-tier literals VERBATIM (no paraphrase); the two-tier count semantics (saddle tier counts only large modes) pinned by test rather than left implicit in the gate record.
- help_text.py carries zero imports (not even stdlib) — the strongest purity posture; gate 2 confirms PURE.
- The drift-alarm uses `tokenize` adjacent-literal reconstruction (not a brittle substring grep) so the split-source gui_game.py literal is compared as its joined value.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] help_text.py docstring/comment named the removed control by its exact literal**

- **Found during:** Task 2 GREEN verification
- **Issue:** the plan's hard verification is `grep -c "Apply / Show in Viewer" serpentrum/help_text.py == 0` — the module's provenance comments quoted that literal while explaining why the hint is Start-only (0 comments/literals may contain it, not just user-visible strings)
- **Fix:** reworded the two provenance spots to 'temp preview control'; behavior/wiring unchanged (comments only)
- **Files modified:** serpentrum/help_text.py
- **Verification:** grep count 0; 17 tests green; full gates green
- **Committed in:** 897bc23 (inside the Task 2 GREEN commit, before staging)

No other deviations — plan executed as written; exactly the 4 `files_modified` paths touched; zero GUI edits (08-09 owns wiring; no shared-file races with the wave).

## Issues Encountered

None — RED/GREEN cycles behaved as specified on the first pass after the Rule 1 wording fix; the tokenize drift-alarm matched the gui_game.py literal on first run.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- **08-09** can now wire: SETUP_HINTS at the SetupTab initial/_on_reset + success-join seams; game_hint at the four Game-tab state seams; spectra_hint(+imaginary_note output) at the Spectra status/log seams; the drift-alarm assertion update rides its Task 1 commit.
- **08-03** doc-vs-code audit can pin: the two-tier imaginary literals/count semantics, GAME_FOCUS_HINT/CONTROLS_RECAP, SETUP_HINTS Start-only vocab, the removed-control negative pin, and every game_hint/spectra_hint literal (all importable from one PURE module).
- No blockers carried forward. The >=20i saddle tier remains owner-approved-but-never-observed here — honest wording is pinned in docstring + tests.

---
*Phase: 08-demo-data-docs-release-audit*
*Completed: 2026-09-28*
