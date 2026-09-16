---
phase: 05-stacking-game-rules
plan: 06
subsystem: wiring/anchors
tags: [anchor-state, setloader, stacking-dataset, gui_setup, locked-decision-10]

# Dependency graph
requires:
  - phase: 03-molecules-in-the-viewer-setup-tab
    provides: setloader (default_stacking_path, load_demo_set/load_upload stacking_path kwarg), SetupTab._on_apply flow, anchored setup dict + init-once rule (03-07)
  - phase: 02-pure-core-game-chemistry-logic
    provides: molecule_data.load_stacking validated loader, stacking_pi_stack.json shipped APPROVED dataset
  - phase: 05-stacking-game-rules research
    provides: 05-RESEARCH-gui-lifecycle records gap (open question 4) + anchor-fields recommendation
provides:
  - _SerpentrumState fields records/stacking_data/last_run (reload-surviving anchor; None-until-written writer model)
  - SetupTab Apply loads records WITH the stacking dataset (has_stack_entry=True for set_a) and anchors records + stacking_data on pmg_tk.startup._serpentrum
  - last_run documented handoff field for the 05-15 completion presenter
affects: [05-08 setloader stack_ring carry, 05-09 hud_logic STACK-04 builders, 05-11 GameTab begin_game, 05-13..05-15 lifecycle, Phases 6/7 spectra handoff]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Anchor-and-load split: setloader returns only records+errors; the caller separately loads + anchors the tiny static dataset dict it needs"

key-files:
  created: []
  modified:
    - serpentrum/__init__.py
    - serpentrum/gui_setup.py

key-decisions:
  - "records + stacking_data (+ future last_run) anchor on _serpentrum, NEVER module globals, NEVER the scalar-only setup dict (locked decision 10)"
  - "Dataset dict loaded fresh by _on_apply (guarded try/except -> None + status note): setloader returns only records+errors; on dataset-carrier failure the skip policy degrades to SKIP_NO_ENTRY, which is correct"

patterns-established:
  - "Anchor writes on successful Apply: records/stacking_data default None at anchor creation; writers set them on success (same model as game_session)"

# Metrics
duration: 4min
completed: 2026-09-15
---

# Phase 5 Plan 06: Anchors & records wiring Summary

**SetupTab Apply now loads records WITH the stacking dataset (has_stack_entry=True for set_a) and anchors records + stacking_data + the pre-declared last_run handoff field on the reload-surviving _serpentrum state — closing wiring gap G4.**

## Performance

- **Duration:** 4 min
- **Started:** 2026-09-15T19:32:16Z
- **Completed:** 2026-09-15T19:36:24Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- `_SerpentrumState` gained three documented anchor fields — `records` (live setloader records for begin_game pickups + info content), `stacking_data` (APPROVED-interaction source for the skip policy and STACK-04 content), `last_run` (completed-run handoff for the Spectra stage, None until plan 05-15 writes it)
- Both `_on_apply` load paths pass `stacking_path=setloader.default_stacking_path()` — demo `set_a` records now carry `has_stack_entry=True` (verification probe prints `[True, True, True, True, True]`)
- On successful load, records + stacking_data anchor on `pmg_tk.startup._serpentrum`; the dataset dict is loaded fresh via `molecule_data.load_stacking` guarded by try/except (DataError, IOError -> None plus a status-label note), so a dataset-carrier failure degrades the skip policy to SKIP_NO_ENTRY correctly
- Bool return contract, Start flow, and widgets unchanged; both files keep their purity classes

## Task Commits

Each task was committed atomically:

1. **Task 1: anchor fields on _SerpentrumState** - `93bfbae` (feat)
2. **Task 2: gui_setup loads + anchors the dataset** - `16d78fe` (feat)

**Plan metadata:** (this SUMMARY committed as `docs(05-06): complete anchors+wiring plan`)

## Files Created/Modified

- `serpentrum/__init__.py` - three anchor fields (records, stacking_data, last_run) with established-style docstring comments appended after game_session; init-once logic untouched (03-07 rule preserved); entry-module purity unchanged (plain class attributes, no imports added)
- `serpentrum/gui_setup.py` - `from . import molecule_data`; both `setloader.load_upload`/`load_demo_set` calls now pass `stacking_path=setloader.default_stacking_path()`; new anchor block after the load-errors check writes `self._anchor.records` / `self._anchor.stacking_data` on success; `stacking_note` advisory folded into the existing status-message parts

## Decisions Made

- Anchoring is writer-model: fields default None at anchor creation (every anchor creation, per the existing class-attribute pattern); `_on_apply` success overwrites them. This mirrors the locked game_session model and keeps the 03-07 init-once rule intact.
- The dataset dict is loaded a second time by `_on_apply` rather than threading it back out of setloader: setloader's public contract returns only (records, errors); the file is tiny and static, so a fresh guarded load is deliberate and keeps setloader/molecule_data untouched (environment rule: call as-is).

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. Gates green on first pass for both tasks; all REQUIRED smokes passed via flushed SMOKE-OK sentinels; informational smoke 02 (offscreen dialog) reported its known non-blocking FAIL (offscreen route closed, 01-05 decision).

## Gate Results

- `python3.6 tests/run_gates.py` — PASS (syntax + plugin-path safety, AST purity, scoped unittest 451 tests OK), run before each commit
- `python3.6 tests/run_gates.py --smoke` — PASS: SMOKE-OK sentinels for 01 SKELETON, 03 VIEWER-BRIDGE, 04 VIEWER-DEMO, 05 LOOP-CAMERA, 06 INPUT-WIZARD; smoke 02 informational FAIL (non-blocking, expected), run after each task
- WSL probe: `setloader.load_demo_set(stacking_path=setloader.default_stacking_path())` -> `[True, True, True, True, True]`
- Grep audits: `stacking_path` present at gui_setup.py:445, :450, :472; anchor writes at :477/:478

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 05-08 (setloader stack_ring carry on demo records) can proceed — records are anchored and dataset-aware
- Plan 05-11 (GameTab begin_game) can now read `anchor.records` + `anchor.stacking_data` after Apply AND after Restart-without-Apply (anchor survives reload by construction)
- Plan 05-15 (completion presenter) has the documented `last_run` field to write
- No blockers.

---
*Phase: 05-stacking-game-rules*
*Completed: 2026-09-15*
