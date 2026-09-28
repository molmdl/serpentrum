---
phase: 08-demo-data-docs-release-audit
plan: 09
subsystem: ui
tags: [help-text, hints, imaginary-note, docs-03, gate-D, gui, ascii, single-source]

requires:
  - phase: 08-demo-data-docs-release-audit
    provides: 08-06 PURE help_text.py + spectra_ui.imaginary_note (d2/d4 GATE D literals); 08-08 bottom-row rewrite of gui_setup (six handlers, eager head population); GATE D record d1-option-c-staleness (08-01)
  - phase: 07-spectra-ui
    provides: Spectra tab seams (set_status_line / append_log_line / _populate_spectrum) and layout freeze caps
  - phase: 04-game-loop-input
    provides: GameTab hint_label widget + the four state-flip sites
provides:
  - Game tab: state-driven hint_label at all five lexical state sites (idle/countdown/GO!-playing/paused/resumed/over), focus hint single-sourced to help_text.GAME_FOCUS_HINT
  - Setup tab: SETUP_HINTS['before_apply'] at construction + post-construction render + post-Reset; SETUP_HINTS['after_apply'] as the final success-join clause
  - Setup: GATE D d1-option-c-staleness honesty fix — the FALSE game-start randomization clause replaced by concrete head naming ('head: <records[0].name>')
  - Spectra tab: done-state next-action hint on every successful populate; GATE D two-tier imaginary_note log line beside the mode caption; pre-run status single-sourced
  - Updated drift alarm: focus-hint now pinned as constant-reference-present AND inline-literal-absent in gui_game.py
affects: [08-03 (doc-vs-code audit pins the wiring), 08-10/08-11 (release audit)]

tech-stack:
  added: []
  patterns:
    - "text-into-existing-labels only: zero new widgets, zero layout churn across all three tabs"
    - "drift-alarm flip: pin the single-source REFERENCE present and the legacy LITERAL absent in the same commit as the rewiring (gate never red)"
    - "honesty fix: replace an over-claiming clause with the concrete resolved value, never a softened claim"

key-files:
  created: []
  modified: [serpentrum/gui_game.py, serpentrum/gui_setup.py, serpentrum/gui_spectra.py, tests/test_help_text.py]

key-decisions:
  - "Spectra done-hint render: successful populate lands spectra_hint('done'); the vibspectrum-fallback advisory keeps precedence when present (pre-08-09 footnote behavior preserved)"
  - "Countdown hint renders at begin_game's 'countdown' entry (where session['status'] is set), not inside _begin_play — _begin_play owns only the GO! → 'playing' flip"
  - "Stale randomize clause replaced by 'head: <name>' from records[0] (the deterministic 'random' resolution), guarded on non-empty records"

patterns-established:
  - "Every rendered help string imports from help_text/spectra_ui; GUI modules never re-derive wording"
  - "Status-line seam discipline: one writer (set_status_line / status_label.setText) per tab, hints keyed by existing state vocabulary"

duration: ~7h 43m wall-clock (git author times; ~15 min active work — a multi-hour host-sleep gap sits between the Task 2 verify and the Task 3 commit)
completed: 2026-09-28
---

# Phase 8 Plan 09: DOCS-03 Help Wiring Summary

**State-driven next-action hints wired into Game/Setup/Spectra from the 08-06 PURE string module, the GATE D two-tier negative-frequency line rendered in the Spectra log, the focus hint single-sourced with its coupled drift-alarm edit in one commit, and the FALSE game-start-randomization clause replaced by concrete head naming — text-into-existing-labels only, zero layout churn.**

## GATE D record honored (08-01-SUMMARY.md)

- **d1-option-c-staleness:** the 'head will be randomized at game start' clause is FALSE ('random' resolves deterministically to records[0] via `pymol_bridge._select_head_record`) — replaced with `'head: %s' % records[0]['name']`, guarded on non-empty records. No new randomization claim introduced; the literal is absent everywhere in source (comments included).
- **d2-option-b-two-tier:** `spectra_ui.imaginary_note([m.freq for m in spectrum.modes])` appends exactly one log line beside the mode caption; `None` appends nothing. Sanity-verified against `tests/fixtures/xtb/g98.out` (72 modes, 3 imaginary → non-None saddle-tier line).
- **d4-confirm-all:** every rendered string traces to help_text/spectra_ui constants; zero inline invented help text.

## Performance

- **Duration:** ~7h 43m wall-clock (2026-09-27T18:55:24Z start → 2026-09-28T02:38:07Z end; git author times a5c2313→02:57:57+08, be84e90→03:00:36+08, 4d59dc3→10:37:25+08 expose the host-sleep gap; active work ~15 min)
- **Tasks:** 3/3
- **Files modified:** 4 (exactly the `files_modified` frontmatter set)

## Accomplishments

**Task 1 — Game tab hint wiring + coupled test edit (ONE commit, gate never red):**

- `from . import help_text` added; `hint_label` construction single-sourced to `help_text.GAME_FOCUS_HINT`; `help_text.game_hint(state)` setTexts at all five lexical state sites: `_set_idle_state` (idle), `begin_game`'s countdown entry (countdown), `_begin_play` GO! (playing), `_apply_pause_state` both branches (paused / resumed→playing), `_present_completion` (over). Zero new widgets; countdown/info-box/HUD text untouched.
- `tests/test_help_text.py` drift alarm rewritten in the SAME commit: asserts `help_text.GAME_FOCUS_HINT` reference present in gui_game.py source AND the raw literal absent (as a joined string literal) — strengthened past the plan's minimum (the plan asked only for the reference check; the literal-absence leg makes partial rewiring red).

**Task 2 — Setup tab hints + stale-clause honesty fix:**

- `SETUP_HINTS['before_apply']` is the status-label construction literal, the post-construction render (re-applied after `__init__`'s `apply_state`/_refresh_status cascade), and the post-Reset status. `SETUP_HINTS['after_apply']` appended as the FINAL success-join part; modal/failure paths keep their error statuses.
- The FALSE randomization clause replaced by concrete head naming; all other success-join parts ('Box + head materialized', stacking/dataset notes, absorbed C2, xtb clauses, warnings) byte-identical.

**Task 3 — Spectra done-hint + imaginary_note log line:**

- Successful `_populate_spectrum` lands `help_text.spectra_hint('done')` (table-click + Save Plot guidance) via the existing `set_status_line` seam; the vibspectrum-fallback advisory keeps precedence. `spectra_ui.imaginary_note` over the populated spectrum's freqs appends one log line beside the `mode_caption` append. Pre-run initial status single-sourced to `spectra_hint('pre_run')` (08-06 pins prove byte-identity); the 06-09-pinned 'xtb running...' literal stays inline for the audit. Layout freeze honored: zero new widgets, zero height/order changes (log 110px, table 150px, order [0]-[4] FINAL).

## Verification evidence

- `python3.6 tests/run_gates.py` — gate 1 (syntax + plugin-path) PASS, gate 2 (AST purity) PASS, gate 3 (scoped discover) PASS; **888 unittests OK** after every task and at completion
- `python3.6 -m unittest tests.test_help_text -v` — 17 tests OK (updated drift alarm included)
- `grep -c "exec_" serpentrum/*.py` — 0 matches project-wide
- `grep -c "Apply / Show in Viewer" serpentrum/*.py` — 0 matches
- `grep -c "head will be randomized" serpentrum/gui_setup.py` — 0 (comments included)
- `git diff --stat 0a7d909..HEAD` — ONLY gui_game.py, gui_setup.py, gui_spectra.py, tests/test_help_text.py (+22 lines in gui_spectra, none layout-affecting)
- Headless sanity (import-level, no widgets): fixture g98 parses to 72 modes / 3 imaginary; `imaginary_note` non-None; all wiring callsites present in source

## Task Commits

1. `a5c2313` — **feat(08-09)**: Game tab state-driven hints + coupled focus-hint drift-alarm edit (gui_game.py + tests/test_help_text.py, one commit per plan)
2. `be84e90` — **feat(08-09)**: Setup tab before/after-apply hints + stale randomize-clause honesty fix (gui_setup.py)
3. `4d59dc3` — **feat(08-09)**: Spectra done-state hint + GATE D imaginary_note log line (gui_spectra.py)

**Plan metadata:** `docs(08-09)` commit follows this file (stages 08-09-PLAN.md + this SUMMARY only).

## Files Created/Modified

- `serpentrum/gui_game.py` (+30/-14) — help_text import, construction constant, game_hint at five state sites
- `serpentrum/gui_setup.py` (+31/-4) — help_text import, before_apply at three seams, after_apply final clause, stale-clause fix
- `serpentrum/gui_spectra.py` (+22/-4) — help_text import, done-hint, imaginary_note log line, pre_run single-source
- `tests/test_help_text.py` (+27/-10→rewritten test) — drift alarm flipped to reference-present/literal-absent

## Decisions Made

- The countdown hint renders at begin_game's `'countdown'` session-state entry rather than inside `_begin_play` (the plan bullet named `_begin_play`; `_begin_play` only fires at GO!, so the countdown→playing flip pair lives at the two actual state-flip sites — documented inline).
- The vibspectrum-fallback advisory keeps precedence over the done-hint (the more specific de-feature note must not be hidden by generic guidance).
- Drift alarm strengthened beyond plan minimum: literal-absence leg (via the existing tokenize helper) makes any partial rewiring red.
- All entailments stay inside the plan's stated scope; files touched exactly match `files_modified`, so the parallel-wave sibling plans face no collision.

## Deviations from Plan

None — plan executed exactly as written (no auto-fixes were needed; gates were green after each task on the first pass).

## Issues Encountered

None. Note: git author timestamps show a multi-hour wall-clock gap between Task 2's verify and Task 3's commit (host sleep, not work); active work per task was minutes.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- **08-03 doc-vs-code audit** can now pin the render sites in addition to the 08-06 strings: game_hint callsites in gui_game.py, SETUP_HINTS render sites in gui_setup.py, spectra_hint/imaginary_note callsites in gui_spectra.py, and the gui_setup stale-clause absence.
- **08-10/08-11 (release audit)** inherits: all DOCS-03 surfaces live; removed-control tokens absent project-wide; gates at 888 unittests green.
- No blockers carried forward. Owner-approved surfaces (countdown lines, HUD row, plot panel, panel order/heights) untouched.

---
*Phase: 08-demo-data-docs-release-audit*
*Completed: 2026-09-28*
