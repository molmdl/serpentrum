---
phase: 08-demo-data-docs-release-audit
plan: 13
subsystem: ui
tags: [tooltips, help_text, setToolTip, student-register, docs-audit, check_docs, README, pi-stack-explanation, biphenyl, quick-001, python3.6]

# Dependency graph
requires:
  - phase: 08-demo-data-docs-release-audit
    provides: Performance group rows atom_budget_spin + threads_spin with DEFAULTS['xtb_threads'] = 4 (08-12); the dialog-owned 6-button bottom row (08-08); the help_text single-source module + GAME_FOCUS_HINT drift-alarm precedent (08-06/08-09)
  - phase: 08-demo-data-docs-release-audit
    provides: the 7-family doc-vs-code audit (check_docs.py + test_docs_audit.py, 08-03) that pins every byte-exact README token this plan had to keep
  - phase: 05-stacking-game-rules-complete
    provides: the shipped stacking_pi_stack.json interactions[0] record + dynamic HUD renders of PI_STACK_PD['explanation'] (08-11-adjacent seams)
provides:
  - help_text.SETUP_TOOLTIPS (13 keys = the exact Setup widget-attribute names) + help_text.BUTTON_TOOLTIPS (6 bottom-row roles): student-register, ASCII, facts only from setup_logic constants + shipped behavior; key sets pinned exhaustively + ASCII sweep extended + gui_setup/gui drift alarms (missing key = unexplained control = fail)
  - All 13 Setup controls + all 6 dialog-owned buttons tooltip-wired adjacently to construction, one greppable line each (grep -c == 13 / == 6)
  - D3: interactions[0].explanation replaced with the humanized playing-cards text (owner draft adopted verbatim; every numeric/citation field byte-identical; jargon fields/formulas/COD list dropped); rendered verbatim by HUD stack lines + hud_logic.idle_tip with zero test edits
  - D1: README humanized at the four owner-flagged sites (L24 deps promise, L38 08-12 surface named, L39 'xtb threads default 4' token + reader-first runtime sentence, L57 stacking paragraph in the D3 register with the quick-001 biphenyl truth, L59 post-approval attribution wording)
  - tools/check_docs.py: 'xtb_threads' composed context + 'xtb threads default %d' drift token (compose-don't-hardcode) — threads-default drift now fails the default gate
affects: [GATE V resumption (Section A blesses the dataset text + tooltip register; live hover checks are gate-owned there), 08-14 release audit + UAT reproduce-steps leg, any future add/drop of a Setup control or bottom-row button (key-set pins fail loudly)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Tooltip single-source recipe (GAME_FOCUS_HINT precedent generalized to dicts): PURE help_text dict keyed by widget-ATTRIBUTE name (Setup) or button ROLE (buttons) -> GUI wires QWidget.setToolTip adjacently to construction, ONE greppable line per widget (no loop/getattr indirection) -> key-set pins + ASCII sweep + fragment drift alarms in the SAME commit"
    - "Documentation-text change with ZERO same-commit test edits is safe when the contract is 'render verbatim, never re-derive': no test pins the literal, all renders are dynamic (tests/test_hud_content reads PI_STACK_PD['explanation']), and the full gate battery proves the coupling before commit"
    - "README humanization under audit: rewrite prose around the byte-exact composed tokens (hessian tail consumed wholesale inside a reader-first sentence), add new numbers ONLY as composed tokens (xtb threads default 4 from DEFAULTS), and re-run check_docs 7/7 + test_docs_audit tamper fixtures before committing"

key-files:
  created: []
  modified:
    - serpentrum/help_text.py (SETUP_TOOLTIPS + BUTTON_TOOLTIPS after SETUP_HINTS; Contents docstring entries; single-source contract note)
    - serpentrum/gui_setup.py (13 tooltip wires adjacent to construction; _build_widgets docstring records the single-line greppable convention)
    - serpentrum/gui.py (from . import help_text; 6 button wires; module docstring note)
    - tests/test_help_text.py (SETUP_TOOLTIP_KEYS/BUTTON_TOOLTIP_KEYS pins; TestTooltips; ASCII sweep extension; two drift alarms with fragment-not-in-source pins)
    - serpentrum/data/stacking_pi_stack.json (ONLY interactions[0].explanation changed; every other field byte-identical)
    - README.md (L24/L38/L39/L57/L59 humanization + quick-001 biphenyl reconciliation)
    - tools/check_docs.py (collect_numeric_context 'xtb_threads'; expected_numeric_tokens threads token)

key-decisions:
  - "Task 1 executed as the plan's TDD option: RED 5c987d2 (key-set pins + sweep + drift alarms, failing 2F+4E exactly on the missing dicts/wiring) before GREEN f6a3dc5 (help_text dicts + 13+6 wires) keeps the contract and the implementation in reviewable atomic commits"
  - "D3 draft adopted VERBATIM from the plan (owner-authored): the text lands before Section A, the owner blesses the final wording at the resumed GATE V - same review round that owns the live hover checks"
  - "Tooltip facts sourced ONLY from setup_logic constants and shipped behavior (box 35/55/85, speed 3.0/6.0/7.5/9.0, cap 1-20/10, budget 100, threads 4, the molfile <=-3-ring acceptance rule, randomize_setup consent/environment carry, normalize_loaded foreign-path fallback, cleanup_srp srp_*-only) - zero invented numbers"
  - "7 of the 13 tooltip wires exceed the GUI modules' informal 79-col style (up to ~93 chars): mandated by the plan's own `grep -c 'setToolTip(help_text.SETUP_TOOLTIPS' == 13` verify, which requires the contiguous substring on single lines; no gate enforces column width (checked run_gates + check_purity)"

patterns-established:
  - "Hover help for every interactive control is part of the shipped UI contract now: adding a Setup control or bottom-row button without a tooltip entry FAILS tests.test_help_text (key-set equality, both directions)"
  - "In-game science prose and README prose share ONE register (D3 dataset sentence <=> L57 paragraph): the same story, the same honest framing, byte-different but factually identical"

# Metrics
duration: 20min
completed: 2026-10-04
---

# Phase 8 Plan 13: Student Tooltips + D3 Dataset Explanation + D1 README Summary

**Owner-directed mid-GATE-V insertion part 2 shipped: every one of the 13 Setup controls and all 6 bottom-row buttons now carry student hover tooltips single-sourced from a new PURE help_text dict pair (key sets pinned exhaustively + fragment drift alarms, TDD RED->GREEN), the in-game pi-stack explanation reads as a playing-cards sentence instead of a component/formula dump (only the explanation value changed; HUD renders dynamic so zero test edits were needed), and the README is humanized for students/educators with the quick-001 biphenyl reconciliation (excluded from live gameplay since 2026-10-01, permanent test-suite refuse-path demonstrator, 4 stackable species in play) plus a new composed 'xtb threads default 4' audit token - 953 unittests + all 3 gates green, every frozen file verified untouched.**

## Performance

- **Duration:** 20 min
- **Started:** 2026-10-04T09:32:13Z
- **Completed:** 2026-10-04T09:52:20Z
- **Tasks:** 3 (Task 1 TDD: RED + GREEN)
- **Files modified:** 7 (4 source + 1 test + 1 data + 1 docs + 1 tool)

## Accomplishments

- **Task 1 (TDD, RED 5c987d2 -> GREEN f6a3dc5):** student hover tooltips. RED pinned the full contract first: the exact 13-key SET and 6-key KEY lists (a missing key = an unexplained control = fail; an extra key = unreferenced text = fail), the ASCII sweep extension, and the gui_setup/gui drift alarms (dict reference must be in source; a distinctive fragment of a Setup tooltip and one of a Button tooltip are pinned TO the dict then banned inline) - failing 2 failures + 4 errors exactly on the missing seams. GREEN added SETUP_TOOLTIPS + BUTTON_TOOLTIPS to help_text.py (student register, ASCII, facts only from setup_logic constants + shipped behavior; Contents docstring updated) and wired all 13 Setup widgets adjacently to construction + all 6 dialog-owned bottom-row buttons in gui.py (new `from . import help_text`). Coverage verified: `grep -c` == 13 / == 6; all 22 module tests green; purity classes unchanged (gate 2).
- **Task 2 (D3, 0c87d4c):** interactions[0].explanation replaced with the owner's humanized draft (two flat rings face-to-face but slightly offset like playing cards slid apart; planes 3.38 A / centers 3.60 A apart; herringbone honesty + serpentrum/data/DATA_SOURCES.md pointer; idealized game approximation framing; Janiak 2000 rule-of-thumb measured on crystalline metal complexes). Every other field byte-identical (id/mode/name/distance_a 3.383/lateral_offset_a 1.231/citation/status verified programmatically); dropped the component-field talk (distance_a/lateral_offset_a), the sqrt/atan2 formulas, and the per-entry COD list. Zero same-commit test edits needed - no test pins the literal (verified by grep across tests/); 142 tests across the coupled modules green (hud_content, demo_data, molecule_data, stacking_dataset).
- **Task 3 (D1, 054096c):** README humanized at the four owner-flagged sites: L24 deps promise now reader-facing; L38 Setup control list names the 08-12 Performance surface; L39 adds `xtb threads default 4` to the canonical-values sentence and rewrites the runtime claim reader-first with the measured hessian tail kept BYTE-EXACT inside it, plus the modest-PC threads advice; L57 rewritten in the SAME register as the D3 text (playing-cards story, the two verbatim composed tokens `a 3.383 A plane gap plus a 1.231 A lateral offset` / `a 3.60 A centroid-centroid distance at 20.0 deg off-normal`, herringbone honesty, Janiak 2000 scope) with the biphenyl sentence replaced by the quick-001 truth and L59 flipped to post-approval wording (human-approved at the v1.0 release review; stale gate phrase gone). check_docs.py gained the composed xtb_threads context + drift token in the SAME commit - all 7/7 audit families PASS, all 23 tamper-fixture tests green (incl. the '3.60 A centroid-centroid' and '6.0 (default)' substrings), every banned literal at zero.
- **Plan-level:** all 7 changed files are exactly the plan's files_modified list; frozen files (serpentrum/data/DATA_SOURCES.md, tests/test_stacking_dataset.py, ROADMAP, .planning/STATE.md, all refusal fixtures, 08-11 committed state) verified untouched by `git diff 35c4d71..HEAD --stat`; gate battery (`python3.6 tests/run_gates.py`, default only - NO --smoke, the resumed GATE V owns live hover checks) green after EVERY task; test baseline moved 948 -> 953 (+5: key-set x2 + values + 2 drift alarms).

## Task Commits

Each task was committed atomically (TDD split for Task 1, per the plan's named option):

1. **Task 1 RED: tooltip contract + ascii sweep pins** - `5c987d2` (test)
2. **Task 1 GREEN: student hover tooltips - help_text content + Setup/button wiring** - `f6a3dc5` (feat)
3. **Task 2: humanize the in-game pi-stack explanation (D3)** - `0c87d4c` (docs)
4. **Task 3: humanize README + biphenyl reconciliation (D1)** - `054096c` (docs)

**Plan metadata:** this summary's docs commit (docs: complete plan)

## Files Created/Modified

- `serpentrum/help_text.py` - the DOCS-03 PURE single-source module; now also owns SETUP_TOOLTIPS (13) + BUTTON_TOOLTIPS (6)
- `serpentrum/gui_setup.py` - Setup tab; all 13 controls tooltip-wired adjacently to construction
- `serpentrum/gui.py` - dialog shell; imports help_text; all 6 bottom-row buttons wired
- `tests/test_help_text.py` - key-set pins, values pins, ASCII sweep extension, two fragment drift alarms
- `serpentrum/data/stacking_pi_stack.json` - the shipped stacking dataset; ONLY interactions[0].explanation changed (D3)
- `README.md` - humanized deps promise / Usage / stacking paragraph (biphenyl truth) / attribution wording
- `tools/check_docs.py` - xtb_threads composed context + drift token

## Decisions Made

- **TDD split for Task 1** (the plan allowed either one feat commit or RED/GREEN): the key-set pins and drift alarms are the contract; landing them RED-first meant the failing state proved they bite (2 failures + 4 errors on exactly the missing dicts + missing GUI references), and the GREEN commit could stay strictly content + wiring.
- **D3 draft adopted verbatim**: the plan's text is owner-authored and the resumed GATE V Section A blesses it; tightening before that review would add churn without authority.
- **Tooltip facts sourced only from shipped truth**: box half-widths, speed tiers, win-cap range/default, atom budget 100, threads 4 come from setup_logic constants; the >3-ring upload rejection from molfile's own documented rule; randomize's consent/environment carry, Save/Load's foreign-path auto-detect fallback, and cleanup's srp_*-only semantics from their shipped implementations - nothing invented, per the do-not-make-up constraint.
- **Single-line greppable wiring over 79-col aesthetics**: the plan's own verify (`grep -c == 13`) requires the contiguous `setToolTip(help_text.SETUP_TOOLTIPS` substring per line, and 7 attribute names are long enough that single-line calls run up to ~93 chars; no gate enforces column width (checked run_gates.py + check_purity.py before deciding).

## Deviations from Plan

### Audit-instrument compliance (plan-internal consistency; no behavior effect)

**1. [audit literal] gui_setup._build_widgets docstring must not contain the wiring token**
- **Found during:** Task 1 (GREEN, pre-commit verification)
- **Issue:** the docstring note documenting the single-line convention quoted the contiguous pattern itself, making the plan's `grep -c "setToolTip(help_text.SETUP_TOOLTIPS"` verify count 14 instead of 13 (grep counts lines, and docstrings are lines too - the 07-07/08-08 raw-source-audit lesson).
- **Fix:** docstring reworded to describe the pattern in prose ("setToolTip followed immediately by the SETUP_TOOLTIPS dict reference") without the literal contiguous token; verified grep -c == 13.
- **Files modified:** serpentrum/gui_setup.py
- **Verification:** grep-count verify == 13; tests.test_help_text green; gates green
- **Committed in:** f6a3dc5 (pre-commit fix, never left the working tree in the broken state)

---

**Total deviations:** 1 (audit-literal wording)
**Impact on plan:** Zero behavior deviations; the fix keeps the plan's own verification commands literally true. No scope creep.

## Issues Encountered

- **Live hover checks are NOT in this plan by design**: the plan's verification battery is the default gates only (NO --smoke); real-GUI tooltip eyeballing belongs to the resumed GATE V, which also owns the Section A blessing of the D3 text and the tooltip wording register. Nothing blocking on the WSL side.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All three owner-directed items (Q1 tooltips, D3 dataset text, D1 README) landed BEFORE the resumed GATE V verdict, as directed; the gate's Section A review now has concrete text to bless (byte-stable since commit 0c87d4c for the dataset, 054096c for the README).
- The tooltip key-set pins and the xtb-threads audit token are now drift-guarded: any future Setup-surface change or DEFAULTS threads drift fails the default gate.
- GATE V resumption should re-run its full checklist including live hover coverage of the 13 Setup controls + 6 buttons (the L1-4 vibe block, all keep-tokens, and banned literals re-verified green here).

---
*Phase: 08-demo-data-docs-release-audit*
*Completed: 2026-10-04*
