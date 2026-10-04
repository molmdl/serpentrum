---
phase: 08-demo-data-docs-release-audit
plan: 12
subsystem: ui
tags: [xtb, thread-cap, setup-schema, gui, qspinbox, source-pins, d2-label-fix, python3.6]

# Dependency graph
requires:
  - phase: 08-demo-data-docs-release-audit
    provides: gui_setup collect/apply/handler seams + bottom-row flow (08-08), DOCS-03 status-hint contract (08-09), randomize_setup carried-key contract (08-05)
  - phase: 06-xtb-pipeline
    provides: DEFAULT_THREAD_ARG ('-P', '4') calibration pin + the controller.start extra_args caller-override mechanism (06-05/06-11)
  - phase: 03-molecules-in-the-viewer-setup-tab
    provides: SetupTab 7-section layout + _on_cap_changed hessian-label pattern (03-07); merge_defaults backcompat seam (02-07/5.1-02)
provides:
  - 'xtb_threads' additive setup key (DEFAULTS 4, whole number >= 1, absent key passes + merges to 4, no schema bump) + the pinned validate literal 'xtb_threads %r must be a whole number >= 1'
  - PURE xtb_run.thread_arg seam: valid int >= 1 -> ('-P', '<n>'); anything else -> the pinned DEFAULT_THREAD_ARG ('-P', '4') (06-CALIBRATION argv byte-identical when the key is missing)
  - Performance QGroupBox on the Setup tab (atom budget 1..9999, xtb threads 1..256) fully wired through collect/apply/Save/Load/Reset/Randomize; hessian label now fires on cap > 10 OR budget > 100 (exact validate parity)
  - Launch argv seam: gui.py _launch_spectra_run builds extra_args from the anchored setup via thread_arg (runner + runner pins UNTOUCHED)
  - D2 fix: completion line reads 'atoms: N (stacked molecules, head excluded)' — never claims to be the xtb run input size
affects: [08-13 (tooltips + docs — Performance rows get tooltip text there), GATE V resumption (live B-eyeball of the two new rows; B3 EXPECT atom_budget: 100 after Reset preserved), 08-14 release audit]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Additive setup-key recipe (5.2-01 precedent, re-applied end-to-end): DEFAULTS entry -> validate leg -> merge_defaults backcompat -> GUI widget write/restore in collect_state/apply_state under _loading -> argv-side PURE producer (thread_arg) -> launch consumes the key, randomize_setup carries it UNCHANGED"
    - "Spinbox range is a UI constraint only: validate() keeps no hard max for atom_budget/xtb_threads, so a hand-edited legal-but-out-of-range value clamps at apply_state and the next collect_state normalizes it (the speed-combo house fallback semantics)"
    - "Raw-source grep audits must never find the audited literal in docstrings (07-07/08-08 lesson, applied TWICE here): gui.py prose avoids the thread_arg call-form token so grep -c == 1 holds; hud/test prose avoids the exact 'spectra input size' phrase so the D2 grep audit is empty"

key-files:
  created: []
  modified:
    - serpentrum/setup_logic.py (DEFAULTS xtb_threads: 4; validate leg after atom_budget + docstring error list; randomize_setup docstring carried-key mention)
    - serpentrum/xtb_run.py (thread_arg directly below the UNCHANGED DEFAULT_THREAD_ARG pin)
    - serpentrum/gui_setup.py (Performance widgets/layout/wiring; _on_cap_changed OR-ext; collect_state widget writes + docstring; apply_state restores; Eight-section docstrings)
    - serpentrum/gui.py (from . import xtb_run; _launch_spectra_run extra_args seam + docstring)
    - serpentrum/hud_logic.py (completion_lines fourth-line label + honest docstring)
    - tests/test_setup_logic.py (TestXtbThreads class; EXPECTED_DEFAULTS + len-9 double-backcompat pin rework)
    - tests/test_xtb_run.py (TestThreadArg matrix; DEFAULT_THREAD_ARG pin :131 untouched)
    - tests/test_gui_pins.py (TestPerformanceControls source-scan pins)
    - tests/test_hud_content.py (both completion-line pins re-labeled, same commit as hud_logic)

key-decisions:
  - "Owner insertion Q2 implementation split: validate() is the LOUD half (whole number >= 1, edit/load time), thread_arg is the SILENT argv-side fallback (defensive, PURE) — a hand-edited bad key errors visibly on the Setup status line but can never build a broken argv"
  - "No SCHEMA_VERSION bump for xtb_threads (5.2-01 consent precedent): absent key = 4 via merge_defaults, so every pre-08-12 setup file loads byte-identically and the launch argv degrades to the pinned '-P 4' cap"
  - "D2 is display-only: the engine counter (head-EXCLUDED atoms_total), the gui_game call site, and the head-inclusive launch counts line (budget_guard.launch_counts_line) are all untouched — only the completion LABEL stops claiming to be the xtb input size"
  - "commit split kept exactly per plan: RED = test files only (spec updates + new classes), GREEN = code files only; coupled existing-pin rework rode the RED test commit so GREEN stayed code-only"

patterns-established:
  - "New setup knob end-to-end: schema -> validation -> backcompat merge -> GUI round-trip -> argv producer, each half pinned"
  - "completion/hud labels name EXACTLY what the number counts; the consumer-facing definition lives on ONE surface (Spectra tab launch counts line)"

# Metrics
duration: 24min
completed: 2026-10-04
---

# Phase 8 Plan 12: Performance Controls + D2 Completion-Line Label Fix Summary

**Owner insertion Q2 shipped mid-GATE-V: the xtb thread count and atom budget are now in-game settable via a new Performance group (TDD'd 'xtb_threads' setup key, whole number >= 1 with absent-key backcompat; PURE thread_arg seam feeding the launch's extra_args so argv stays byte-identical to the pinned '-P 4' calibration cap whenever the key is missing), the hessian warning now fires on budget > 100 too, and the D2 completion line honestly reads 'atoms: N (stacked molecules, head excluded)' — 948 unittests + all 3 gates green, runner/engine untouched.**

## Performance

- **Duration:** 24 min
- **Started:** 2026-10-04T08:45:34Z
- **Completed:** 2026-10-04T09:09:10Z
- **Tasks:** 3 (Task 1 TDD: RED + GREEN)
- **Files modified:** 9 (5 source + 4 test files)

## Accomplishments

- **Task 1 (TDD):** `xtb_threads` setup key + PURE `thread_arg` seam. RED commit (9efc8e6) specified the full contract — DEFAULTS pin 4 / no schema bump, absent-key backcompat, the exact `xtb_threads %r must be a whole number >= 1` literal over the 0/-1/'4'/2.5/bool-trap matrix, no hard max, randomize carry pin, and the thread_arg valid/fallback matrix — failing with 2 failures + 6 errors exactly on the missing seams. GREEN commit (e4bb291) made all 109 module tests pass first try; full/default gate battery green.
- **Task 2:** Performance GUI group + launch argv seam (53dd655). Two spinboxes (Atom budget 1..9999, xtb threads 1..256) in a new Performance QGroupBox between Win cap and Speed (5.1-04 sibling-section pattern); both widget-written in collect_state, restored in apply_state under the _loading guard with DEFAULTS fallbacks — Save/Load/Reset/Randomize pick both keys up with ZERO handler edits. `_on_cap_changed` extended (not renamed): the hessian label now shows on win cap > 10 OR atom budget > 100, byte-identical HESSIAN_WARNING, exact parity with validate's warning leg. `_launch_spectra_run` builds `extra_args = XTB_OHESS + thread_arg(setup['xtb_threads'])` — the documented caller-override mechanism; xtb_runner.py needs zero edits and all 06 runner pins stay green.
- **Task 3 (D2):** Honest completion-line label (6dff796), coupled pin edit in ONE commit (marker-pin discipline). Fourth line now reads `'atoms: %d (stacked molecules, head excluded)'` (e.g. `atoms: 79 (stacked molecules, head excluded)`); the other three lines byte-identical; the true head-inclusive run input keeps rendering on the Spectra tab's launch counts line. Engine counter pins (test_phase5_integration) untouched and green.
- **Plan-level:** all 9 changed files are exactly the plan's files_modified list; frozen files (DATA_SOURCES.md, test_stacking_dataset.py, xtb_runner.py, ROADMAP, .planning/STATE.md, refusal fixtures, 08-11 committed state) verified untouched by diff; `grep -rn "spectra input size" | grep -v budget_guard` is EMPTY; `grep -c "xtb_run.thread_arg" serpentrum/gui.py` == 1; DEFAULT_THREAD_ARG value pin byte-exact.

## Task Commits

Each task was committed atomically (TDD split for Task 1):

1. **Task 1 RED: xtb_threads + thread_arg failing tests** - `9efc8e6` (test)
2. **Task 1 GREEN: xtb_threads setup key + PURE thread_arg seam** - `e4bb291` (feat)
3. **Task 2: Performance group + launch extra_args seam** - `53dd655` (feat)
4. **Task 3: D2 completion-line label (coupled pins)** - `6dff796` (fix)

**Plan metadata:** this summary's docs commit (docs: complete plan)

## Decisions Made

- **Validation-vs-fallback split:** validate() rejects loudly at edit/load time (whole number >= 1, bool-is-int trapped, no hard max); thread_arg silently degrades anything unusable to the pinned ('-P', '4') so argv construction can never fail. A missing key never produces an error AND never changes argv — pre-08-12 behavior is byte-identical everywhere.
- **Spinbox ranges are UI-only constraints** (1..9999 / 1..256): validate has no hard max, so a hand-edited legal-but-out-of-range value clamps at apply_state and the next collect_state normalizes it (the documented speed-combo house fallback semantics).
- **Existing-pin rework rode the RED commit:** EXPECTED_DEFAULTS gained `xtb_threads: 4` and the 5.2 consent backcompat test was widened to double-backcompat (a pre-5.2 file lacks BOTH additive keys; len==9 stays truthful; merged threads pinned to DEFAULTS), keeping GREEN strictly code-only — the plan's commit split honored exactly.
- **Docstring wording constrained by the plan's own grep audits** (two applications of the established 07-07/08-08 raw-source-audit lesson): gui.py prose avoids the literal thread_arg call-form so `grep -c == 1` stays exactly 1, and D2 prose avoids the exact "spectra input size" phrase so the plan's empty-grep audit holds.

## Deviations from Plan

### Worded-to-audit prose (plan-internal consistency; no behavior effect)

**1. [Rule 1 - audit literal] gui.py docstring avoids the thread_arg token + '-P' literal**
- **Found during:** Task 2 (launch seam docstring)
- **Issue:** the plan's docstring sketch ("via xtb_run.thread_arg ... DEFAULT_THREAD_ARG ('-P','4')") would re-trip the plan's own verifications (`grep -c "xtb_run.thread_arg" gui.py == 1` — grep's `.` is a regex wildcard — and the new no-inline-'-P' pin) with a second occurrence.
- **Fix:** prose reads "via xtb_run's PURE thread_arg seam" and "the shipped '-P 4' cap"; the code line remains the ONLY match (verified: grep -c == 1, Python literal count == 1, no "'-P'" substring).
- **Files modified:** serpentrum/gui.py
- **Verification:** Task 2 verify battery (test_gui_pins green incl. the new pins; gates green)
- **Committed in:** 53dd655

**2. [Rule 1 - audit literal] D2 prose avoids the exact "spectra input size" phrase**
- **Found during:** Task 3 (completion_lines docstring + test comment)
- **Issue:** the plan's docstring sketch contains "spectra input size", which would re-trip the plan's `grep -rn "spectra input size" ... | grep -v budget_guard (empty)` audit after the fix removed it from the label.
- **Fix:** docstring/comment now say "xtb run input size" / "head-inclusive xtb run input"; the full meaning (fourth line = stacked-only count; the true input renders on the Spectra tab's launch counts line) is preserved.
- **Files modified:** serpentrum/hud_logic.py, tests/test_hud_content.py
- **Verification:** plan-level grep audit EMPTY; test_hud_content green; gates green
- **Committed in:** 6dff796

**3. [Rule 3 - coupled pin] Existing test pins reworked in the RED commit**
- **Found during:** Task 1 (RED)
- **Issue:** adding an 11th DEFAULTS key would break two EXISTING pins in the GREEN commit (EXPECTED_DEFAULTS full-dict equality; the consent class's len==9 "9 OLD keys" construction), forcing test edits into the code-side commit against the plan's explicit file split.
- **Fix:** both pin reworks rode the RED test commit — EXPECTED_DEFAULTS gained `xtb_threads: 4`; test_missing_key_merges_to_off became the double-backcompat pin (excludes BOTH additive keys, len==9 truthful, asserts merged threads == DEFAULTS). RED = tests-only, GREEN = code-only, matching the plan's commit specifications exactly.
- **Files modified:** tests/test_setup_logic.py
- **Verification:** RED failed exactly on the missing seams (2 failures + 6 errors); GREEN green first try
- **Committed in:** 9efc8e6 (part of the RED commit)

**4. [coupled literal] _build_layout docstring "7 QGroupBox sections" -> "8"**
- **Issue:** the plan named the class-docstring "Seven -> Eight" change; the same counting literal lives in _build_layout's docstring and would have gone stale.
- **Fix:** single-word coupled edit in the same Task 2 commit.
- **Committed in:** 53dd655

---

**Total deviations:** 4 (2 audit-literal wordings, 1 coupled-pin rework placement, 1 coupled docstring count)
**Impact on plan:** Zero behavior deviations — all four are pin-coupling or audit-instrument compliance, keeping the plan's own verification commands literally true. No scope creep.

## Issues Encountered

- **Setup tab grew by two rows (B13-class, gate-visible):** the Performance group adds ~2 form rows under the 07-10 dialog height cap; content scrolls within the tab when needed. The live-GUI eyes check belongs to the resumed GATE V (no --smoke legs in-plan per the plan's own scope). No restructure performed (07-10 height-cap machinery untouched by directive).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **08-13 (tooltips + docs) can proceed:** the Performance rows intentionally carry NO tooltips here (08-13's job); `atom_budget_spin` / `threads_spin` are the widget handles it will attach text to, and the new xtb_threads key must appear in 08-13's docs surfaces.
- **GATE V resumption unaffected and unblocked:** the 08-11 committed state, DATA_SOURCES.md, and test_stacking_dataset.py are untouched; smoke 14 flows the new key automatically (new_setup + validate + save/load round-trip); the paused gate's B3 EXPECT survives because Reset assigns `new_setup()` explicitly and apply_state paints 100/4 (then collect_state widget-writes both — the 08-08 Pitfall A contract held).
- **Backcompat:** every pre-08-12 setup file loads, validates, and launches byte-identically (merge_defaults fills 4; thread_arg degrades to the pinned cap).
- **Blockers/concerns:** none. Engine, runner, bridge, and all frozen fixtures untouched; full default battery green on the final tree.

---
*Phase: 08-demo-data-docs-release-audit*
*Completed: 2026-10-04*
