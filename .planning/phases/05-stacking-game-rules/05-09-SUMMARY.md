---
phase: 05-stacking-game-rules
plan: 09
subsystem: ui
tags: [hud, info-box, STACK-04, pure-module, unittest, python3.6]

# Dependency graph
requires:
  - phase: 05-stacking-game-rules (plan 05-05)
    provides: placement.py outcome-code constants (SKIP_NO_ENTRY..REFUSE_ATOM) imported by reason_text
  - phase: 02-pure-core
    provides: molecule_data.load_stacking / setloader.default_stacking_path (validated shipped dataset access)
  - phase: 04-game-loop-input (plan 04-02)
    provides: hud_logic.py PURE module + test_hud_logic.py pin conventions (format_elapsed/remaining_text)
provides:
  - "hud_logic.pickup_block(name, interaction, citation_short) — dataset-composed per-pickup info line (interaction name, stored plane gap, composed centroid distance @ off-normal angle, verbatim explanation, citation short-code)"
  - "hud_logic.skip_text / reason_text — placement outcome-code -> stable educator-readable literals"
  - "hud_logic.budget_text — count-free budget advisory (GAME-04 counts hidden during play)"
  - "hud_logic.completion_lines — completion summary with counts revealed (GAME-09/SPECTRA-06)"
  - "hud_logic.breakdown_lines — end-of-run stacked/refusal grouping in first-appearance order"
  - "hud_logic.idle_tip — round-robin VERBATIM dataset explanations; resume_note — G2 un-finish line"
affects: [05-stacking-game-rules (05-11 begin_game idle tips, 05-13/05-14 event branches, 05-15 completion presenter), 07-spectra-ui]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "One taxonomy, two consumers: placement.py owns outcome-code string constants; hud_logic imports them for display text (never redefined)"
    - "Composer-not-author: hud_logic composes info-box lines from dataset fields VERBATIM (explanation newline-collapsed); zero authored chemistry"

key-files:
  created:
    - tests/test_hud_content.py
  modified:
    - serpentrum/hud_logic.py

key-decisions:
  - "REFUSE_ATOM renders 'placement clashes' (detail appended only when present) so breakdown_lines reuse the same literal without clash data"
  - "budget_text is a module-level constant with an explicit no-digit pin (GAME-04 counts stay hidden during play)"
  - "resume_note(name) accepts the pickup name for call-site symmetry but deliberately does not render it (run-state fact, not chemistry)"

patterns-established:
  - "Dataset-composed display: composed = sqrt(d^2 + l^2), angle = degrees(atan2(l, d)) derived at render time from the interaction dict (3.60 A @ 20.0 deg for the shipped pi_stack_pd entry)"
  - "Breakdown grouping: stacked by name, refusals by (outcome, name), groups in first-appearance order"

# Metrics
duration: 6 min
completed: 2026-09-16
---

# Phase 5 Plan 09: HUD Content Builders Summary

**STACK-04 info-box content as seven PURE hud_logic builders — dataset-composed pickup lines (3.60 A @ 20.0 deg composed from the shipped pi_stack_pd entry), placement-code-driven skip reasons, count-free budget advisory, completion/breakdown/idle/resume lines — with 24 format-pinning tests against the real shipped dataset; the 04-02 format_elapsed/remaining_text pins are byte-identical.**

## Performance

- **Duration:** 6 min
- **Started:** 2026-09-16T18:54:03Z
- **Completed:** 2026-09-16T19:00:30Z
- **Tasks:** 1
- **Files modified:** 2

## Accomplishments

- All seven STACK-04 builders implemented append-only in `serpentrum/hud_logic.py` (PURE, stdlib `math` + `from . import placement` for the outcome-code constants — one taxonomy, two consumers)
- `pickup_block` renders the shipped dataset end-to-end: interaction name, stored 3.38 A plane gap, composed centroid 3.60 A @ 20.0 deg off-normal, VERBATIM explanation (newline-collapsed), `Janiak 2000` short-code — verified against the real `stacking_pi_stack.json`
- Every placement.py outcome code (SKIP_NO_ENTRY, SKIP_NOT_APPROVED, SKIP_MODE, SKIP_NO_RING, SKIP_NONPLANAR, REFUSE_WALL, REFUSE_ATOM) maps to a stable educator-readable literal; `budget_text` is pinned digit-free (GAME-04); `completion_lines` reveals counts only at completion (GAME-09/SPECTRA-06)
- 24 new pins green alongside the untouched 13-pin `test_hud_logic.py`; full gates green (545 tests)

## Task Commits

1. **Task 1 (RED): HUD content builder pins** - `03bc616` (test)
2. **Task 1 (GREEN): hud_logic builders** - `32a9032` (feat)

## Files Created/Modified

- `serpentrum/hud_logic.py` — STACK-04 builders appended (pickup_block, skip_text, budget_text, completion_lines, breakdown_lines, idle_tip, resume_note, reason_text); existing 04-02 display helpers untouched
- `tests/test_hud_content.py` — 24 format pins on the real shipped dataset (composed 3.60 A @ 20.0 deg formula, code->text mapping, count-free budget line, breakdown grouping/order, round-robin tips)

## Decisions Made

- REFUSE_ATOM's literal is `'placement clashes'` with the clash detail appended only when present — `breakdown_lines` history entries carry no clash detail, so the breakdown reuse of the literal renders the bare form (pinned both ways).
- `budget_text()` is a constant (no parameters) with an explicit "no digit anywhere in the string" test pin — the GAME-04 hidden-counts rule is enforced as a test, not a comment.
- `resume_note(name)` keeps the `name` parameter (call-site symmetry with the other pickup-scoped builders) but deliberately never renders it: the G2 un-finish note is a run-state fact, not molecule-level chemistry.
- Unknown outcome codes degrade to `'unclassified outcome <code>'` rather than raising — the info box must never crash a live run on a future code.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Plan's claim "the shipped explanation contains a newline" is false**

- **Found during:** Task 1 (writing the RED pins)
- **Issue:** The plan states "(the shipped explanation contains a newline)" — verified against the real `stacking_pi_stack.json`, the shipped `explanation` string contains NO newline (single-line JSON string).
- **Fix:** The newline-collapse behavior is still implemented (dataset text may gain newlines at edit time) and pinned via a synthetic interaction dict carrying a `\n` (`test_newlines_in_explanation_collapse_to_spaces`); the real-dataset pin asserts the rendered line equals the dataset explanation with `.replace('\n', ' ')` applied, so the pin stays correct if a newline is ever added. No data file was touched (human-approved, no-fabrication rule).
- **Files modified:** tests/test_hud_content.py (implementation of the note, not the dataset)
- **Verification:** All 24 pins green, including the synthetic-newline collapse case and the real-dataset exact-format case
- **Committed in:** 03bc616 (RED) / 32a9032 (GREEN)

---

**Total deviations:** 1 auto-fixed (1 plan/data mismatch handled by pinning the behavior synthetically)
**Impact on plan:** None — builder behavior and pins match the plan's intent exactly; no scope creep.

## Issues Encountered

None — the dataset values (3.383 / 1.231) compose to exactly the pinned 3.60 A / 20.0 deg on first run; gates green on first run.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- The GUI consumers are unblocked: 05-11 (`begin_game` idle tips via `idle_tip`), 05-13/05-14 (`'stacked'`/`'refused'`/`'budget_warning'` branches via `pickup_block`/`reason_text`/`budget_text`), 05-15 (completion presenter via `completion_lines` + `breakdown_lines` + `resume_note`).
- No blockers. The info box remains a dumb rolling log (research verdict) — these builders are the only content surface the GUI event branches call.

---
*Phase: 05-stacking-game-rules*
*Completed: 2026-09-16*
