---
phase: 07-spectra-ui
plan: 10
subsystem: ui
tags: [pymol, qt, human-verify, gates, smoke, xtb, phase-close]

# Dependency graph
requires:
  - phase: 07-spectra-ui
    provides: "07-01..07-09 complete Spectra tab: pure seams, tab UI, plot panel (route-A PNG), record->Scene feed, every-mode frequency table, row-click mode vectors on srp_xtbopt"
  - phase: 06-xtb-pipeline
    provides: "Get Spectra launch pipeline (06-09), async runner, artifacts dir contract (SRP_SPECTRA_DIR), 06-12 owner-approved live checkpoint"
provides:
  - "Phase-7 headless proof COMPLETE: 840 unittests + 10/10 REQUIRED smokes (incl. 12 PLOT-RENDER, 13 MODE-ARROWS w/ g98=xtbopt assertion) + --xtb contract, all green first try"
  - "Phase-7 live proof COMPLETE: consolidated owner checkpoint APPROVED round 2 (2026-09-26) — SPECTRA-01/03/04/05 human-certified end-to-end"
  - "BOTH sign-offs recorded: optimized-frame interpretation (vectors on srp_xtbopt) APPROVED; [TRAIN] discharges a-f ALL approved"
affects: [phase-7-verifier, phase-8]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "phase-close house shape (05-16/06-12 lineage): full gate battery -> consolidated human-verify with numbered steps -> defect rounds -> recorded verdict + fix dispositions"
    - "checkpoint fix loop kept to the GU-enforceable surface: defect ONE (dialog height) -> single fix commit -> gates re-verified -> re-present"

key-files:
  created: [.planning/phases/07-spectra-ui/07-10-SUMMARY.md]
  modified: [serpentrum/gui_spectra.py, serpentrum/gui.py]

key-decisions:
  - "Round-1 defect fix = scroll caps, NOT plot/edit restructuring: log setMaximumHeight(110), table setMaximumHeight(150) (both widgets scroll natively), dialog screen-height cap max(560, 0.92*available); the 07-06 approved exact-preset plot sizing left byte-untouched"
  - "Selector-Error zoom noise (srp_mode_vec absent at zoom_mode_frame time) recorded as a DEFERRED v1 cosmetic note, NOT fixed — owner approved with the noise visible"
  - "Optional small-imaginary-frequency guidance line NOT built; owner raised no objection at the checkpoint — stays a deferred optional UX item"

patterns-established:
  - "consolidated checkpoint verdict recorded verbatim (owner words + BOTH sign-off items + restart-hygiene observation) — verifier hand-off per house flow"
  - "benign console noise (Qt DPI warning, guarded-zoom selector noise) distinguished from defects and dispositioned explicitly, never silently swept"

# Metrics
duration: gates task ~20 min + 2 checkpoint rounds (owner-side live sessions) + fix continuation ~15 min (estimates)
completed: 2026-09-26
---

# Phase 7 Plan 10: Phase-Closing Gates + Consolidated Human-Verify Summary

**Phase 7 CLOSED: full gate battery green first try (840 unittests, 10/10 REQUIRED smokes, --xtb contract) and the consolidated live checkpoint APPROVED round 2 (2026-09-26, owner verbatim "approved, well done") with BOTH sign-offs — SPECTRA-01/03/04/05 human-certified in real Windows PyMOL; one round-1 defect (dialog too tall) fixed by scroll caps + screen-height dialog cap (e91c7ad); [TRAIN] items all discharged.**

## Performance

- **Duration:** gates ~20 min (all green first try) + continuation fix ~15 min + 2 owner checkpoint rounds (estimates)
- **Started:** 2026-09-26 (gates leg, HEAD da618f4)
- **Completed:** 2026-09-26 (round-2 approval)
- **Tasks:** 2/2
- **Files modified:** 2 source (the r1 fix) + 2 planning (this summary, STATE.md)

## Accomplishments

- **Task 1 — full gate battery GREEN first try, no fixes needed** (HEAD da618f4): default gates 840 tests OK (gates 1-3 PASS); `--smoke` 10/10 REQUIRED PASS; `--xtb` contract PASS
- **Task 2 — consolidated human-verify APPROVED round 2** after one defect round: owner ran the full live flow in real Windows PyMOL (SRP_DEBUG=1; Get Spectra -> live streaming -> cancel -> Run again -> completion -> plot/table/PNG -> row-click vectors) and typed "approved, well done"
- **Both sign-offs given:** (8) optimized-frame interpretation APPROVED (vectors on srp_xtbopt); (9) all six [TRAIN] discharges approved (a-f)
- **Phase 7 at 10/10 — CLOSED**; SPECTRA-01/03/04/05 delivered end-to-end

## Task Commits

1. **Task 1: full gate battery** — NO commit (all green first try; plan: "No commit unless fixes were needed")
2. **Task 2: consolidated human-verify checkpoint** — round 1 defect -> continuation fix `e91c7ad` (fix(07-10): checkpoint r1 — compact Spectra tab (scrolling log/table) + screen-height dialog cap (owner directive)) -> round 2 APPROVED

**Plan metadata:** this SUMMARY is committed with `docs(07-10): phase-7 closing checkpoint APPROVED — Phase 7 complete`

## Gate Results (verbatim summaries)

- **`python3.6 tests/run_gates.py` (default):** all gates green — gate 1 syntax walk + plugin-path safety PASS; gate 2 purity AST PASS; gate 3 scoped unittest **840 tests, OK**
- **`python3.6 tests/run_gates.py --smoke`:** **10/10 REQUIRED PASS** via flushed SMOKE-OK sentinels — 01 SKELETON, 03 VIEWER-BRIDGE, 04 VIEWER-DEMO, 05 LOOP-CAMERA, 06 INPUT-WIZARD, 07 TRANSFORM, 08 EDGEON, 10 CHAIN-COUNT, 12 PLOT-RENDER, 13 MODE-ARROWS; informational 09/11 PASS; informational 02 non-blocking FAIL = the known 01-05 offscreen-Qt dead end (unchanged, never blocking)
- **`python3.6 tests/run_gates.py --xtb`:** PASS — xtb 6.7.1pre version line + 'normal termination of xtb' contract (gate 5)
- Post-fix re-run (after e91c7ad): 840 unittests green + all required smokes SMOKE-OK — re-verified before re-presenting the checkpoint

## Checkpoint Verdicts

### Round 1 (2026-09-26) — ONE defect

Owner verdict: **"window too long, reduce the height of plugin window"** — the Spectra page's table+plot made the dialog exceed the screen.

**Fix (e91c7ad, GUI layout only):**
- SpectraTab log panel capped `setMaximumHeight(110)` — QPlainTextEdit scrolls natively, 500-block tail and streaming unaffected
- Frequency table capped `setMaximumHeight(150)` — QTableWidget scrolls natively, row clicks unaffected
- PluginDialog screen-height cap: `max(560, int(availableGeometry.height * 0.92))` (gui.py)
- The 07-06-approved exact-preset plot behavior left **untouched**; stretch still hands the plot the leftover space

Per house failure-handling rule: never approve with a known-broken step -> defect fixed, gates re-verified, checkpoint re-presented.

### Round 2 (2026-09-26) — APPROVED

Owner verbatim: **"approved, well done"** (full live flow in real Windows PyMOL with SRP_DEBUG=1).

**Sign-off (8) — optimized-frame interpretation: APPROVED.** Mode vectors drawn on the OPTIMIZED structure (srp_xtbopt), not the game frame — as researched (g98 == xtbopt within 1e-6 A; game frame wrong by up to 0.14 A).

**Sign-off (9) — [TRAIN] discharges: ALL APPROVED.**
| Item | Disposition |
| --- | --- |
| a — ascending x-axis | approved |
| b — ASCII label legibility | approved |
| c — readability at default size | approved |
| d — tab-switch repaint | approved |
| e — log streaming smoothness | approved |
| f — zoom framing of molecule+arrows | approved |

**[TRAIN] item 7 (g98==xtbopt generality):** NOTED — asserted by smoke 13's always-on re-assertion (<1e-3 A); one-fixture origin recorded here (see Known Limitations). **[TRAIN] item 1 (QWidget.grab()):** MOOT — route A (single paint_scene seam for screen + 2x QImage PNG) shipped in 07-05, grab() demoted to a non-shipped comment.

**Step 10 (restart hygiene) — implicitly exercised:** the owner's console showed srp_mode_vec swept by begin_game on a new round and the guarded zoom re-framing — degraded state handled without crash.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Dialog exceeded screen height after the 07-09 table landed (checkpoint round-1 defect)**
- **Found during:** Task 2, checkpoint round 1 (owner report)
- **Issue:** Spectra tab's tall table+plot made PluginDialog exceed the user's screen
- **Fix:** scroll caps on log (110) + table (150); dialog screen-height cap `max(560, 0.92*available)`; plot sizing untouched
- **Files modified:** serpentrum/gui_spectra.py, serpentrum/gui.py
- **Verification:** gates re-run green (840 unittests + all required smokes); round 2 owner APPROVED
- **Committed in:** `e91c7ad`

---

**Total deviations:** 1 auto-fixed (1 bug surfaced at the human checkpoint — the plan's own failure-handling route)
**Impact on plan:** None beyond the approved scope — fix confined to the GU-adjacent layout surface; no behavior, API, or requirement changes.

## Issues Encountered

None beyond the round-1 defect (handled above) — gates green first try; no auth gates; no blocking discoveries.

## Deferred / Cosmetic Notes (owner-visible, recorded — NOT fixed now)

1. **Selector-Error zoom noise (DEFERRED v1 cosmetic):** `Selector-Error: Invalid selection name "srp_mode_vec"` / `'srp_xtbopt or srp_mode_vec'` prints when `zoom_mode_frame` fires with only srp_xtbopt present (arrows not yet drawn at first load). The guard means the zoom still succeeds on srp_xtbopt; zero functional impact. Candidate cosmetic improvement: zoom only on 'srp_xtbopt' when srp_mode_vec is absent. Owner approved **with** the noise visible -> recorded, not fixed.
2. **Qt `QWindowsWindow::setGeometry` warning (benign):** fires once on first dialog show — Qt/Windows DPI negotiation; window correctly respects the new screen-height cap. No action.
3. **Optional small-imaginary-frequency guidance line (deferred optional UX):** the 07-01-era owner flag (one status line when min(freq) < 0 — 'N small imaginary mode(s) < 20i cm^-1: soft inter-stack modes, physical for molecular stacks') was NOT built; the owner raised no objection at the checkpoint. Stays a pending-todo deferred item; large |imag| (>~50i) would warrant a stronger warning if ever observed.

## Known Limitations (recorded)

- **No co2 g98 fixture:** the linear-molecule g98 table/vector leg is smoke-only behind `--xtb` real runs.
- **Zero-intensity coverage is unit-level** (synthetic tuples + synthetic co2 vibspectrum).
- **g98==xtbopt generality** rests on one fixture + smoke 13's always-on re-assertion (<1e-3 A).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **Phase 7 CLOSED at 10/10 with both owner sign-offs recorded** — ready for `/gsd-verify-phase` (verifier hand-off per house flow; REQUIREMENTS/ROADMAP rows are orchestrator-owned).
- Next: Phase 8 (Demo Data, Docs & Release Audit) — TBD planning; Phase-8-gated items already on the pending-todos list (full DATA_SOURCES.md sign-off, Janiak 2000 scope check, Save/Load buttons, deferred edge-biased spawns, deferred zoom cosmetic, optional imaginary-mode guidance line).

---
*Phase: 07-spectra-ui*
*Completed: 2026-09-26*
