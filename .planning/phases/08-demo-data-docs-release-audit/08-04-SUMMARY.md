---
phase: 08-demo-data-docs-release-audit
plan: 04
subsystem: testing
tags: [release-audit, smoke, e2e-chain, pymol, game-engine, xyzio, g98-fixture, png-save, setup-roundtrip]

# Dependency graph
requires:
  - phase: 02-pure-core
    provides: game_engine.GameEngine (dt-parameterized step), xyzio codec, setup_logic save/load
  - phase: 05-stacking
    provides: spawn.build_pickup_seed + engine attach_segment capture seam
  - phase: 06-xtb-pipeline
    provides: xtb_run.build_run_input (EQ-xyz-1 handoff), EQ-smoke-1 fixture disposition
  - phase: 07-spectra-ui
    provides: gui_plot.render_image route-A save, plot_logic.build_scene, smoke-12 template
provides:
  - smoke/14_release_e2e_smoke.py — REQUIRED headless chain proof: setup -> scripted win -> complete handoff -> fixture spectra -> IR plot -> PNG save -> setup round-trip, one run
  - 11/11 required smokes in the --smoke battery
affects: [08-05-plus (release audit/human checkpoint cites smoke 14 as the mechanical chain proof), DOCS-05]

# Tech tracking
tech-stack:
  added: []
  patterns: [engine-led scripted win via attach_segment capture seam, fixture-tailed REQUIRED e2e (real hessian reserved for human checkpoint)]

key-files:
  created: [smoke/14_release_e2e_smoke.py]
  modified: [tests/run_gates.py]

key-decisions:
  - "Spectra tail uses committed g98 fixture (26 atoms/72 modes/3 imaginary); real hessian stays out of REQUIRED battery per 06-12 EQ-smoke-1 (84-101 s real runs race the global 90 s SMOKE_TIMEOUT)"
  - "Handoff stage calls xtb_run.build_run_input directly (the EQ-xyz-1 seam gui_game anchors + gui.py:167 re-parses) rather than approximating the xyz by hand"
  - "Scripted win calls engine.attach_segment on ('stacked',) events — the counter-neutral controller seam shared by gui_game and the pure integration suite; placement gate provenance stays with smokes 08/10 + pure tests"

patterns-established:
  - "Chain-proof smoke: one REQUIRED smoke walks every release flow leg via module seams; leg-level proofs stay in their own smokes, the new artifact is the chaining only"

# Metrics
duration: 10 min
completed: 2026-09-27
---

# Phase 8 Plan 04: Release E2E Chain Smoke Summary

**smoke/14_release_e2e_smoke.py — the DOCS-05 mechanical chain proof: one REQUIRED headless run walking setup -> scripted pure-engine win -> head-inclusive xyz handoff -> fixture-g98 spectra tail -> route-A PNG save -> SETUP-08 pure setup round-trip -> cleanup, registered in REQUIRED_SMOKES with the full gate battery green (11/11 required smokes).**

## Performance

- **Duration:** ~10 min
- **Started:** 2026-09-27T17:52:43Z
- **Completed:** 2026-09-27T18:02:54Z
- **Tasks:** 2/2
- **Files modified:** 2 (1 created, 1 modified)

## Accomplishments

- The one genuinely new DOCS-05 artifact exists: every release flow leg was already proven somewhere EXCEPT the chaining (08-RESEARCH-release-audit.md §1); smoke 14 now walks the whole chain in a single headless run and flushes `SMOKE-OK RELEASE-E2E` in ~15 s (90 s SMOKE_TIMEOUT untouched).
- Stage contracts pinned verbatim from the trace: STAGE3 win at tick 26 (2 stacked, 42 engine atoms, 5 viewer-mirrored head moves); STAGE4 xyz handoff round-trips 54 atoms (12 head + 42 engine, comment `'serpentrum snake smoke14_run'` — the exact gui.py:167 cross-check shape); STAGE5 the smoke-12 fixture contract (26 atoms/72 modes/3 imaginary); STAGE6 route-A PNG 57203 bytes, magic bytes + reload 1600x1000, temp file removed in-stage (EQ-artifact-1 hygiene, no SRP_SPECTRA_DIR needed).
- SETUP-08 round-trip exercised in-chain: save_setup -> load_setup (raising contract) -> merge_defaults -> validate zero-error, and `loaded == setup` exact dict reproduction (box/head/cap/speed).
- Registered as the 11th REQUIRED smoke; `python3.6 tests/run_gates.py` (syntax/purity/unittest) and `--smoke` both green; 11/11 required SMOKE-OK, zero SMOKE-FAIL lines; `git diff` on run_gates.py shows ONLY the tuple append.

## Task Commits

Each task was committed atomically:

1. **Task 1: smoke/14_release_e2e_smoke.py — 9-stage release chain** - `2dadfba` (test)
2. **Task 2: register smoke 14 as REQUIRED + full battery run** - `1096edc` (feat)

## Files Created/Modified

- `smoke/14_release_e2e_smoke.py` — created; 9-stage headless release chain (app guard -> setup load -> materialize -> scripted win -> xyz handoff -> fixture spectra -> PNG save -> setup round-trip -> cleanup), house smoke template obligations throughout (resolve_root, flush=True, no widget construction, sentinel verdicts)
- `tests/run_gates.py` — modified; REQUIRED_SMOKES append at tuple end with per-plan comment (historical order and SMOKE_TIMEOUT=90 untouched)

## Decisions Made

- **Fixture spectra tail in the REQUIRED smoke** — real hessian runs (84-101 s @104 atoms, 06-CALIBRATION) race/exceed the global per-smoke 90 s timeout and the owner dispositioned real-xtb legs INFORMATIONAL at 06-12 (EQ-smoke-1); the live real flow is reserved for the phase-closing human checkpoint (DOCS-05/GATE V).
- **Shipped seams only, no lookalikes** — build_run_input for the handoff (EQ-xyz-1), spawn.build_pickup_seed for pickup records, engine.attach_segment as the capture-consumer seam, gui_plot.render_image route A for the save; the pure engine's step(0.1) is the shipped cadence (QTimer 100 ms, gui_game.py:88-90).
- **Direct attach_segment (not full placement.resolve) in the scripted win** — the plan's "keep the script simple" directive; placement/tail-frame/clash provenance is covered by smoke 08 + the pure integration suite, and the smoke asserts the engine/counter/handoff contracts, not re-solved geometry.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] script missed the engine's capture consumer seam**

- **Found during:** Task 1 (first headless run of smoke 14)
- **Issue:** the raw event loop asserted `len(engine.segments) == 2` but the pure engine's `('stacked',)` capture is counter-only — appending the frozen segment is the controller's job (gui_game._handle_stack_event / the pure suite's capture() helper), so segments stayed 0 and the stage failed with `AssertionError('segments 0 != 2')`.
- **Fix:** consume `('stacked', pickup)` events in the scripted loop with `engine.attach_segment(molecule_id, centroid, atoms)` — the documented counter-neutral seam (game_engine.py:749+), documented inline in the smoke.
- **Files modified:** smoke/14_release_e2e_smoke.py
- **Verification:** rerun flushes all 9 stage lines + SMOKE-OK RELEASE-E2E (fixed inside the Task-1 commit `2dadfba`).
- **Commit:** 2dadfba

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** The fix makes the scripted win match the shipped controller contract; no scope creep.

## Issues Encountered

- None beyond the deviation above. Full battery (default gates + --smoke) passed first run after registration; informational smoke 02's dialog-GUI FAIL is pre-existing, non-blocking, and unrelated.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- DOCS-05's mechanical chain proof is in place and gate-enforced; the release audit / phase-closing human checkpoint (real xtb live flow, 46-ID evidence table) can cite smoke 14 as the headless chain proof with its verbatim STAGE lines as evidence.
- No blockers. STATE.md intentionally untouched (orchestrator-owned during the parallel wave).

---
*Phase: 08-demo-data-docs-release-audit*
*Completed: 2026-09-27*
