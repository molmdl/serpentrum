---
phase: 08-demo-data-docs-release-audit
plan: 08
subsystem: ui
tags: [setup-07, setup-08, gui, pyqt5, persistence, source-pins, python3.6]

# Dependency graph
requires:
  - phase: 08-demo-data-docs-release-audit
    provides: GATE D decision record (08-01) — d1-option-c-staleness + owner round-2 head-combo directive; randomize_setup/normalize_loaded (08-05)
  - phase: 04-game-loop-input
    provides: byte-identical Start route contract (04-06), request_auto_pause hook (04-08)
  - phase: 03-molecules-in-the-viewer-setup-tab
    provides: SetupTab collect/apply round-trip, friendly error-surface split, browse-dialog precedents
provides:
  - Canonical 6-button bottom action row in gui.py (SETUP-07: Reset/Randomize/Save Setup/Load Setup/Cleanup model/Start, spec order, right-aligned)
  - SETUP-08 GUI half: Save/Load flows through save_setup/load_setup/merge_defaults/normalize_loaded with friendly double-surface errors, auto-pause-before-modal, anchor writes
  - GATE D round-2 owner directive shipped: head combo populates at demo-set SELECTION and upload browse-load, no Apply required
  - tests/test_gui_pins.py — 7 permanent source-text pins (row contract, single Start switch, modeless ban, temp-row removal, eager-population pin)
affects: [08-09 (stale Apply-status-clause text fix — its scope now matches a smaller surface), 08-11 GATE V (6-button live pass + educator round-trip + width measure)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Modal-before-pause hook: PluginDialog injects setup_page.game_pause_request = game_tab.request_auto_pause (attribute, not signal); handlers call a getattr-guarded _pause_gameplay() before any modal (PITFALLS Pitfall 5)"
    - "Eager-population pattern: read-only setloader load at selection time for display data; the same load args as the Apply path, no materialize, no validation UI"
    - "Raw-source grep audits must never find the audited literal in docstrings (07-07 lesson re-applied): modeless-ban docstring text avoids the token itself"

key-files:
  created:
    - tests/test_gui_pins.py (7 source-text pins)
  modified:
    - serpentrum/gui.py (6-button row, setup_page retained, pause hook)
    - serpentrum/gui_setup.py (4 new handlers, eager head combo, temp row removed, docstrings refreshed)
    - serpentrum/gui_plot.py (docstring literal scrub)
    - serpentrum/input.py (docstring literal scrub)
    - serpentrum/pymol_bridge.py (docstring literal scrub)

key-decisions:
  - "Load flow concludes with collect_state() so the anchor always mirrors exactly what the widgets display (Pitfall E closed; unknown loaded head ids degrade to Random in the ANCHOR too, honestly, with an advisory note)"
  - "Switching to Upload resets the head combo to Random-only until the browse load/split succeeds (staleness guard within the owner directive's spirit)"

patterns-established:
  - "Bottom-row semantics live in the page; the dialog owns only widgets, layout, wiring and cross-tab hooks (row/handlers split per 08-RESEARCH-persistence Q1 ownership table)"
  - "Source-pin test class for GUI contracts that headless construction cannot verify"

# Metrics
duration: 19min
completed: 2026-09-28
---

# Phase 8 Plan 8: 6-Button Bottom Row GUI Wiring Summary

**The spec-reserved SETUP-07 bottom action row landed: six right-aligned dialog buttons (Reset/Randomize/Save Setup/Load Setup/Cleanup model/Start) wired to four new SetupTab handlers plus the reused Cleanup/Start paths, SETUP-08's Save/Load GUI half through the pure persistence helpers with friendly double-surface errors and pause-before-modal, the GATE D round-2 eager head-combo directive shipped, and the entire contract pinned by permanent source-text tests — 888 unittests + all 11 required smokes green.**

## GATE D items implemented (read-decision record)

- **`d1-option-c-staleness` consumed:** `_on_randomize` delegates to 08-05's `randomize_setup` — FULL-setup scope (head + box + win cap + speed + fwhm), consent/environment keys untouched, concrete values only.
- **Owner round-2 directive shipped:** selecting the demo set repopulates the head combo immediately (read-only `setloader.load_demo_set` with the exact Apply-path args via `_eager_populate_demo`, no materialize); a successful upload browse-load repopulates from upload records (`_on_browse_upload`); the post-Apply repopulation at `_on_apply` stays unchanged; pinned by `test_populate_head_combo_called_outside_on_apply`.
- **Randomize × eager-population interaction verified in code:** `randomize_setup` writes a concrete head id drawn from the very candidates the head combo displays; `apply_state`'s findData therefore always matches and the combo shows the randomized head as itself — the Random-fallback snap never triggers on that path (the plan's NOTE confirmed by reading `apply_state`'s head branch).

## Performance

- **Duration:** 19 min
- **Started:** 2026-09-27T18:29:29Z
- **Completed:** 2026-09-27T18:48:31Z
- **Tasks:** 3/3
- **Files modified:** 5 (+1 created)

## Accomplishments

- gui.py: reserved Phase-1 QHBoxLayout now holds the six spec-ordered buttons, right-aligned via the preserved leading `addStretch(1)`; `setup_page` promoted to `self.setup_page`; pause hook injected (`self.setup_page.game_pause_request = self.game_tab.request_auto_pause`); Start route byte-identical (04-06) with `setCurrentIndex(1)` count == 1.
- gui_setup.py: `_on_reset` (explicit new_setup assignment — Pitfall A), `_on_randomize` (pause → candidates from the head combo → randomize_setup → anchor write → apply_status line), `_on_save_setup` (pause → collect → save_setup → getSaveFileName with `serpentrum_setup.json` default → .json append → friendly write errors), `_on_load_setup` (pause → read → load_setup loud-wrap → merge_defaults → normalize_loaded → validate → apply_state + concluding collect_state anchor write — Pitfall E); eager demo/upload head-combo population per the owner directive.
- Phase-3 temporary button row removed (widgets, layout row, wiring) with `_on_apply`/`_on_cleanup`/`_on_start` surviving as the internal paths the bottom row drives; every docstring refreshed so the removed control's name survives nowhere (`grep -rc 'Apply / Show in Viewer' serpentrum/ == 0` per-file).
- tests/test_gui_pins.py (7 pins): label order, single Start switch, zero blocking-modal tokens across `serpentrum/*.py`, removed-control zero-name, dangling-attribute zero, internal-path survival, eager-population-outside-`_on_apply`.

## Task Commits

1. **Task 1: Bottom row in gui.py** — `846eddb` (feat)
2. **Task 2: SetupTab handlers + eager head combo** — `6305b84` (feat)
3. **Task 3: Temp-row removal + docstrings + source-pin test + gates** — `41f157a` (feat)

**Plan metadata:** docs commit for this SUMMARY follows.

## Files Created/Modified

- `serpentrum/gui.py` — 6-button row placed + wired; `self.setup_page`; pause-hook injection; docstring updated (row landed), Start-switch docstring literal rephrased (raw-grep count)
- `serpentrum/gui_setup.py` — 4 new handlers, `_pause_gameplay`, `_head_candidates`, `_eager_populate_demo`, `_on_source_changed`/`_on_browse_upload` eager population, temp row removed, docstrings refreshed
- `tests/test_gui_pins.py` — NEW (the plan's permanent contract test)
- `serpentrum/gui_plot.py`, `serpentrum/input.py`, `serpentrum/pymol_bridge.py` — docstring literal scrub only (see Deviations)

## Decisions Made

- **Load concludes with `collect_state()`** (the plan's first Pitfall-E option): the anchor always holds exactly what the widgets show. Consequence: a loaded unknown head id (e.g. upload-derived on a fresh machine) degrades to Random in the anchor too, alongside the advisory 'head molecule not in this set - Random used' — honest, reproducible, and consistent with house collect/apply round-trip semantics.
- **Upload selection resets the head combo to Random-only** until the browse load/split succeeds: leaving the previous set's names visible between selection and successful load would be a staleness bug of the class the directive exists to kill.
- **Read-error during Load double-surfaces** (QMessageBox + status) even though the plan's words said status-only: the module's own documented split (:14-21 docstring, one-shot blocking errors → QMessageBox) demands it and `_on_apply` is the precedent; no plan intent changed.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Scrubbed 3 pre-existing docstring `exec_` literals so the plan's grep verification could pass**

- **Found during:** Task 3 (pin test design / final verification)
- **Issue:** The plan's verification requires `grep -c "exec_" serpentrum/*.py == 0`, but `serpentrum/gui_plot.py:22`, `serpentrum/input.py:56` and `serpentrum/pymol_bridge.py:6` contained the literal inside docstrings that DESCRIBE the modeless ban (present since Phases 3-7). The verification was unsatisfiable as written with those literals in place; 07-07-SUMMARY records exactly this lesson ("the plan's audit greps raw source, so the literals had to go").
- **Fix:** Reworded the three docstring lines to reference the modeless/blocked-modal gate without the token (meaning preserved: static QFileDialog convenience carries no blocking call token; bridge builds no dialogs).
- **Files modified:** `serpentrum/gui_plot.py`, `serpentrum/input.py`, `serpentrum/pymol_bridge.py` (docstrings only; zero behavior change — these files are outside the plan's `files_modified` frontmatter, which is why this is logged as a deviation)
- **Verification:** `grep -c "exec_" serpentrum/*.py` reports 0 for every file; AST purity gate still green; the new `TestModelessBan` pin now guards the whole `serpentrum/*.py` surface permanently
- **Committed in:** `41f157a` (part of Task 3)

**2. [Rule 1 - Bug latent] Upload-selection head-combo staleness guard**

- **Found during:** Task 2 (owner-directive implementation)
- **Issue:** With eager population, choosing Set A fills the head combo with set ids; switching to 'Upload...' without a successful browse-load would leave those (now unrelated) ids visible and selectable — the same "options must match the current source" class the directive fixes.
- **Fix:** `_on_source_changed` resets the combo to Random-only on switching to Upload; the browse handler repopulates on successful load/split.
- **Files modified:** `serpentrum/gui_setup.py`
- **Verification:** gates green; behavior pinned conceptually by `TestEagerHeadPopulation` (call-site presence) — live verdict belongs to GATE V
- **Committed in:** `6305b84` (part of Task 2)

---

**Total deviations:** 2 auto-fixed (1 blocking-verification docstring scrub, 1 latent-bug staleness guard)
**Impact on plan:** Both necessary for the plan's own verification/owner directive to hold. The docstring scrub touches 3 files outside `files_modified` — docstring-only, zero behavior change.

## Issues Encountered

- `grep -c "setCurrentIndex(1)" == 2` after Task 1's first gate run: the PluginDialog docstring mentioned the literal (the exact 07-07-SUMMARY trap). Rephrased the docstring before the Task 1 commit; count is 1.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **GATE V (08-11)** owns every live verdict for this plan: 6-button live pass, Reset/Randomize/Save/Load/Cleanup/Start walk-through, educator round-trip reproducibility, width clipping check (`setMinimumWidth(450)` deliberately untouched — GATE V's conditional task owns any bump), and the eager head-combo UX.
- **08-09** should note its stale-clause scope shrank: the temp-row removal here means its 'head will be randomized at game start' fix now lives against the bottom-row Start flow only.
- Suite baseline: 888 unittests (was 881; +7 pins). All required smokes SMOKE-OK (01/03/04/05/06/07/08/10/12/13/14); smoke 02 informational FAIL unchanged (01-05 dead end).

---
*Phase: 08-demo-data-docs-release-audit*
*Completed: 2026-09-28*
