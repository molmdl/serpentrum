---
phase: 06-xtb-pipeline
plan: "04"
subsystem: infra
tags: [pymol, pymol-bridge, atom-count, guard, spectra-cross-check, headless-smoke]

# Dependency graph
requires:
  - phase: 05-stacking-game-rules
    provides: chain_object_names() completion-only seam + frozen last_run handoff record (05-15)
  - phase: 03-viewer
    provides: pymol_bridge cmd-seam, cleanup_srp, get_model safety notes, manifest atom_count validation (setloader)
provides:
  - pymol_bridge.chain_atom_counts(names) — head-inclusive per-object atom counts via cmd.get_model, input-order, missing-object yields 0
  - REQUIRED gate smoke 10 (SMOKE-OK CHAIN-COUNT) cross-pinning the count channel to manifest atom_count values
  - REQUIRED_SMOKES entry making the SPECTRA-06 viewer count channel a permanent regression gate
affects: [06-09 launch cross-check, budget_guard desync warnings, SPECTRA-06, Phase 7 spectra handoff]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Viewer count channel: names from the FROZEN last_run record -> per-object counts via get_model; counts ONLY, never coords (EQ-xyz-1)"
    - "Missing-viewer-object-as-desync: 0 returned, documented, consumed by the guard as a WARNING signal instead of raising"

key-files:
  created:
    - smoke/10_chain_count_smoke.py
  modified:
    - serpentrum/pymol_bridge.py
    - tests/run_gates.py

key-decisions:
  - "EQ-xyz-1 (bridge half): counts-only seam — run-input xyz stays engine-atoms only (06-02/06-06); no coordinate export added"
  - "EQ-smoke-1: smoke 10 is REQUIRED (bridge-class, no xtb.exe dependency — same class as smokes 03-08); smokes 09/11 stay informational"
  - "Missing-object policy: return 0 (documented desync signal for plan 06-09 guard), never raise"

patterns-established:
  - "Count-channel contract: chain_object_names() (membership, from frozen record) + chain_atom_counts() (per-object counts, input order) = the viewer-side SPECTRA-06 cross-check input"
  - "Smoke manifest cross-pin: headless smokes assert viewer counts against in-place serpentrum/data/manifest.json atom_count (the setloader-validated field)"

# Metrics
duration: 3 min
completed: 2026-09-26
---

# Phase 6 Plan 04: Bridge Chain-Count Channel Summary

**Viewer-side atom-count seam `pymol_bridge.chain_atom_counts` for the SPECTRA-06 launch cross-check, pinned by a new REQUIRED headless smoke cross-checked against manifest atom_count values (benzene 12, naphthalene 18)**

## Performance

- **Duration:** 3 min
- **Started:** 2026-09-26T14:21:47Z
- **Completed:** 2026-09-26T14:25:06Z
- **Tasks:** 1/1
- **Files modified:** 3 (1 created, 2 modified)

## Accomplishments

- `chain_atom_counts(names)` appended to the Phase-5 completion-seams section of `serpentrum/pymol_bridge.py` (line 457, after `chain_object_names` at 443): per-name `cmd.get_model(name)` -> `len(model.atom)`; input-order preserving; a vanished object yields 0 (documented desync signal for the plan 06-09 guard) instead of raising. BRIDGE-legal: no Qt, no numpy, no `.exec_()`, no new module, no purity-allowlist edit.
- REQUIRED smoke `smoke/10_chain_count_smoke.py` (sentinel `SMOKE-OK CHAIN-COUNT`): bridge import under the loader-name path (smoke 01 pattern), loads benzene/naphthalene as `srp_head`/`srp_seg_0`, asserts `chain_object_names()` sort order and counts `[12]`/`[12, 18]`, cross-pins both counts against in-place `manifest.json` `atom_count` (the setloader-validated field), pins missing-object -> `[0]` without raising, and verifies `cleanup_srp()` removes exactly 2 srp_* objects.
- `tests/run_gates.py` `REQUIRED_SMOKES` gains `smoke/10_chain_count_smoke.py` with the Phase-6 attribution comment — the count channel is now a permanent required regression gate (missing or failing smoke fails the gate).

## Task Commits

Each task was committed atomically on branch `exec/06-04`:

1. **Task 1: bridge chain_atom_counts + REQUIRED smoke 10 + run_gates entry** — `d0f2bb1` (feat)

**Plan metadata:** see docs commit below (SUMMARY).

## Files Created/Modified

- `serpentrum/pymol_bridge.py` — appended `chain_atom_counts(names)` (BRIDGE class; get_model-safe reader; docstring names consumer SPECTRA-06 plan 06-09 + EQ-xyz-1 counts-only scope)
- `smoke/10_chain_count_smoke.py` — REQUIRED headless smoke, 6 named steps, flushed sentinels (template obligations from smoke 01)
- `tests/run_gates.py` — `REQUIRED_SMOKES` tuple append with `(Phase 6, plan 06-04 — bridge chain atom-count channel)` comment

## Decisions Made

- Followed the plan's resolved decisions verbatim: counts-only bridge seam (EQ-xyz-1 — no coordinate export; engine-atom xyz remains the single run-input truth from plans 06-02/06-06); smoke 10 REQUIRED (bridge-class, no xtb.exe dependency); missing-object returns 0 as a documented desync signal.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. All verification passed first attempt:

- `python3.6 tests/run_gates.py` — green (gate 1 syntax+safety PASS, gate 2 purity PASS, gate 3 unittest PASS; 785 tests OK, full suite unmodified)
- `timeout 90 cmd.exe /c "C:\src\run-conda-pymol.bat -cq smoke\10_chain_count_smoke.py"` — all 6 steps `SMOKE-STEP OK`, flushed sentinel `SMOKE-OK CHAIN-COUNT` present
- `python3.6 tests/run_gates.py --smoke` — smoke 10 reported as REQUIRED and PASSING (`note: smoke smoke/10_chain_count_smoke.py: PASS (sentinel SMOKE-OK)` + `SMOKE-OK CHAIN-COUNT`); all 8 previously-required smokes still PASS; gate 4 PASS, all gates green
- `grep -n "def chain_atom_counts" serpentrum/pymol_bridge.py` — exactly one definition (line 457), placed after `chain_object_names` (line 443)

(Pre-existing, non-blocking: informational smoke 02 dialog reports FAIL (non-blocking) — unrelated to this plan; informational smoke 09 qprocess PASS.)

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- The viewer-side count channel for SPECTRA-06 exists and is regression-gated: plan 06-09 (launch cross-check) can now read names from the frozen `last_run` record and count via `chain_atom_counts`, comparing the head-inclusive sum against the run-input count; a 0 from a vanished object surfaces as a guard desync WARNING, never a launch crash.
- No coordinate export was added — engine-atom xyz (plans 06-02/06-06) remains the single run-input truth.
- Executed in isolated worktree `tmp/exec-06-04` on branch `exec/06-04` (parallel-wave protocol); ready for orchestrator merge.

---
*Phase: 06-xtb-pipeline*
*Completed: 2026-09-26*
