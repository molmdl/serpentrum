---
phase: 02-pure-core-game-chemistry-logic
plan: 14
subsystem: testing
tags: [integration-test, pure-core, stacking, spectra, xtbenv, xyzio, gates, purity, r10-audit]

# Dependency graph
requires:
  - phase: 02-02 (spectra g98 parser + xtbenv)
    provides: parse_g98/parse_vibspectrum + evaluate_run success contract
  - phase: 02-03 (xyzio)
    provides: write_xyz/read_xyz .xyz handoff I/O
  - phase: 02-04 (stacking math + clash gate)
    provides: ring_frame/place_pickup/check_clash (criterion 1)
  - phase: 02-05 (molecule_data)
    provides: load_stacking (dataset-driven distance, STACK-02)
  - phase: 02-07 (setup_logic)
    provides: BOX_PRESETS (the setup->engine seam boundary box)
  - phase: 02-11 (vibspectrum + real_modes)
    provides: parse_vibspectrum + trivial-mode offset correspondence
  - phase: 02-12 (broaden + dispatcher + robustness)
    provides: unified parse dispatcher + loud-failure hardening
  - phase: 02-13 (rigid-pivot turn sweeps)
    provides: engine rules (full-suite member)
provides:
  - "Cross-module pure-core integration proof: one chain where each stage consumes the previous stage's real output"
  - "Full Phase-2 suite (383 tests) green under tests/run_gates.py with zero sys.modules stubs"
  - "AGENTS.md R10 audit record (no drift -- unchanged)"
  - "The four Phase-2 success criteria proven testably true end-to-end"
affects: [03-gui-wiring, 05-connector, 06-xtb-pipeline, phase-transition]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Single-chain integration test: data flows stage-to-stage (dataset distance -> placement -> parser n_atoms -> contract bytes -> xyz round-trip); a regression in any module OR data schema breaks the chain even when every unit test passes"
    - "Seam assertions: the placed atom count from stacking becomes the spectra parser's expected n_atoms (len(tail)+len(placed) == parser.n_atoms); the xyz handoff format the parser fixtures came from round-trips"

key-files:
  created:
    - "tests/test_integration_pure_core.py (348 lines, 6 stages + clash-gate contrast, 7 ordered test methods)"
  modified: []

key-decisions:
  - "Integration test is DECISION-AGNOSTIC on dataset values: reads (distance_a, lateral_offset_a) from the shipped stacking_pi_stack.json and derives expected_centroid = sqrt(d^2+l^2) FROM THE FILE -- would still pass if the human re-pinned the APPROVED values"
  - "R10 audit: no AGENTS.md drift -- the 8 Phase-2 pure modules are default-PURE (covered by existing gate bullets); fixture-path conventions belong in plan SUMMARYs, not AGENTS.md (per research R10 §10)"
  - "Stage-5 'intensity <= 1e-4' means the intensity DIFFERENCE between vibspectrum and g98 for corresponding modes (max observed 5e-05), not the intensity value itself (modes carry large intensities, e.g. 2.4191 km/mol)"

patterns-established:
  - "Integration-chain test: setUp builds the whole chain once; ordered test_stageN methods consume real downstream outputs so a seam regression cascades into a downstream failure, not a silent pass"
  - "The boundary box for integration clash checks is derived FROM setup_logic.BOX_PRESETS['medium'] (the real setup->engine seam), extended with a display-only z range"

# Metrics
duration: 5 min
completed: 2026-09-09
---

# Phase 2 Plan 14: Pure-Core Integration Chain Summary

**Single-chain integration test proving dataset->xyz->stacking->xtb-contract->spectra->xyz round-trip, full 383-test suite green under gates, zero stubs, AGENTS.md R10-audited (no drift)**

## Performance

- **Duration:** 5 min
- **Started:** 2026-09-09T17:23:58Z
- **Completed:** 2026-09-09T17:29:50Z
- **Tasks:** 2 (1 committed, 1 audit-only)
- **Files modified:** 1 created (AGENTS.md audited, unchanged)

## Accomplishments

- **One integration chain, not parallel tests:** data flows stage to stage -- the stacking distance is read FROM the shipped data file, the placed atom count becomes the spectra parser's expected n_atoms, the xtb contract consumes the same run's fixture bytes, and the xyz handoff format round-trips. A regression in any module or data schema breaks the chain even when every unit test passes.
- **Phase criterion 1 (stacking) proven end-to-end:** `place_pickup(3.4, 0.0)` reproduces the committed dimer2 fragment 2 within 1e-6 A over all 13 atoms; `check_clash` clears the legal 3.4 A stack and fires on a 1.5 A placement. The dataset-driven `place_pickup(d, l)` lands the ring centroid at `sqrt(d^2+l^2)` within 1e-4 A at ~20 deg off-normal.
- **Phase criterion 3 (xtb contract) on fixture bytes:** `evaluate_run` returns ok for ohess (success+files), NOT ok for repro_oh (success, NO files -- the load-bearing case), NOT ok for bad (abnormal termination).
- **Phase criterion 2 (spectra) cross-module:** parser n_atoms == 26 == len(tail)+len(placed); 72 == 3N-6 g98 modes; 78 == 3N vibspectrum modes; freq/intensity correspondence at the computed offset 6.
- **Phase criterion 4 (gates) green:** full 383-test suite passes under `tests/run_gates.py` (gate 1 syntax+plugin-path, gate 2 AST purity, gate 3 scoped unittest); zero `sys.modules[` stubs in tests/; all `serpentrum/` modules stdlib-only PURE (`check_purity.py` exit 0).

## Task Commits

Each task was committed atomically:

1. **Task 1: tests/test_integration_pure_core.py -- the cross-module chain** - `0e435d8` (test)
2. **Task 2: Full-suite green + zero-stub audit + AGENTS.md R10 audit** - audit-only, NO commit (AGENTS.md unchanged -- expected R10 outcome)

**Plan metadata:** (pending — see final commit below)

## Files Created/Modified

- `tests/test_integration_pure_core.py` - The cross-module integration chain (348 lines, 6 stages + clash-gate contrast). setUp builds the whole chain once from the shipped dataset + fixtures; 7 ordered `test_stageN` methods assert each stage's contract while consuming the previous stage's real output. Documented at the top with the four R11 integration-proof points.
- `AGENTS.md` - Audited against research R10 (§10); NO edit (no drift detected).

## Decisions Made

- **Integration test decision-agnostic on dataset values.** Reads `(distance_a, lateral_offset_a)` from `serpentrum/data/stacking_pi_stack.json` and derives `expected_centroid = sqrt(d^2+l^2)` FROM THE FILE. Never hardcodes 3.383/1.231/3.6. Would still pass if the human re-pinned the APPROVED values (the test asserts the file and the math agree, not a specific chemistry value).
- **R10 audit: no AGENTS.md drift.** Verified all four R10 claims hold on the finished tree: (a) `check_purity.py` exits 0 (every serpentrum/*.py classifies PURE/entry-lazy/GUI-allowlist automatically); (b) the discovery command convention is unchanged and green (run_gates gate 3); (c) the zero-stub rule is intact (no `sys.modules[` in tests/); (d) no genuinely new convention emerged that AGENTS.md contradicts. Per R10 §10, fixture-path conventions and plan-level decisions live in plan SUMMARYs, not AGENTS.md.
- **Stage-5 intensity assertion = the DIFFERENCE.** The plan's stage-5 text "intensity <= 1e-4" means `abs(vibspectrum.intensity - g98.intensity) <= 1e-4` for corresponding modes (probed: max observed 5e-05), NOT the intensity value itself (real modes carry large intensities, e.g. 2.4191 km/mol).

## Deviations from Plan

None - plan executed exactly as written.

### Notes on the verification greps

The plan's verification lists `grep -rln "numpy|pymol|pmg_tk|PyQt5" serpentrum/*.py -> no matches`. A naive grep DOES match every pure module's docstring (each asserts "no pymol/pmg_tk/PyQt5/numpy anywhere" -- a self-description, not an import). The authoritative check is the AST-based `tools/check_purity.py` (gate 2 of run_gates.py), which correctly distinguishes module-level imports from lazy/inside-function imports and applies the GUI allowlist. It exits 0 = clean. The eight Phase-2 pure modules (molecule_data, setup_logic, spectra, stacking, xtbenv, xyzio, cgo_build, game_engine) have zero actual pymol/pmg_tk/PyQt5/numpy imports; `__init__.py` (entry, lazy imports inside functions) and `gui.py` (GUI allowlist, `from pymol.Qt import`) are the documented exceptions. This is the expected state, not a deviation.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

**Phase 2 is complete.** All 14 plans (02-01..02-14) have SUMMARYs. The pure core is proven as ONE system:

### Phase-2 Success Criteria Checklist

- [x] **(1) Stacking data-driven + dimer2 reproduction.** `place_pickup(3.4, 0.0)` reproduces the committed dimer2 fragment 2 within 1e-6 A over all 13 atoms (an eclipsed pure z-translation); `check_clash` clears the legal 3.4 A stack and fires on 1.5 A. The dataset-driven `place_pickup(d, l)` from the shipped APPROVED file lands the ring centroid at `sqrt(d^2+l^2)` within 1e-4 A at ~20 deg. (proven in test_stage3a/3b; unit tests in 02-04).
- [x] **(2) Spectra parser on real fixtures incl. negatives + zero-intensity + loud corrupt failure.** g98 72 modes == 3N-6, vibspectrum 78 == 3N, correspondence at computed offset 6 (proven in test_stage5). Negatives (dimer modes 7-9 are negative REAL modes), zero-intensity (14 real 'NO' rows), and loud corrupt failure (bad.log/truncation/`******` overflow) are covered by 02-12 robustness unit tests; the integration chain confirms the parser consumes the same run's g98.out/vibspectrum the contract fixtures came from.
- [x] **(3) xtb contract + detection pure-tested.** `evaluate_run` returns ok for ohess (success+files), NOT ok for repro_oh (success, NO files -- stderr success alone is not success), NOT ok for bad (abnormal termination) (proven in test_stage4; binary detection + argv + run-dir contracts unit-tested in 02-02).
- [x] **(4) Full suite green, zero stubs, stdlib-only.** 383 tests pass under `tests/run_gates.py` (gates 1/2/3 PASS); zero `sys.modules[` stubs in tests/; all `serpentrum/` modules stdlib-only PURE (`check_purity.py` exit 0) (INFRA-02).

### Ready for Phase 3+

- The pure core (stacking, xyzio, spectra, xtbenv, molecule_data, setup_logic, cgo_build, game_engine) is proven as one system and ready to wire into the live game (Phases 3-7).
- The `place_pickup` return `(placed_atoms, R, t)` is the contract Phase 5's connector feeds `cmd.transform_selection` (matrix layout convention flagged OPEN in stacking.py -- verify in Phase 5 against editing.py).
- The xyz handoff format (`write_xyz`/`read_xyz`, 8-decimal round-trip within 1e-8) is the proven Phase-6 runner format.

### Blockers/Concerns

None. Phase 2 complete; ready for phase-transition verification.

---
*Phase: 02-pure-core-game-chemistry-logic*
*Completed: 2026-09-09*
