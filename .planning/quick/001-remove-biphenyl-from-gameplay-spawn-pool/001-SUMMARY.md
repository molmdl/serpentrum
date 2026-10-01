---
phase: quick-001
plan: 001
subsystem: gameplay-balance
tags: [spawn-pool, head-selection, biphenyl, game-rules]
requires: [02-pure-core, 03-molecules-viewer, 5.3-randomized-pickup-spawning]
provides:
  - "set_a biphenyl excluded from the gameplay pickup spawn pool (spawner self-filter)"
  - "set_a biphenyl excluded from head selection (combo filter + gameplay fallback)"
  - "Phase-8 follow-up note (docs/release-audit re-scoping)"
affects: [08-demo-data-docs-release-audit]
tech-stack:
  added: []
  patterns:
    - "GAMEPLAY_EXCLUDED_MOLS: single-source (set, id) exclusion constant in the PURE spawn policy; the spawner self-filters at construction (single choke point), every caller inherits"
key-files:
  created:
    - ".planning/quick/001-remove-biphenyl-from-gameplay-spawn-pool/PHASE8-NOTE.md"
  modified:
    - "serpentrum/spawn.py"
    - "serpentrum/gui_game.py"
    - "serpentrum/gui_setup.py"
    - "serpentrum/setup_logic.py"
    - "tests/test_spawn.py"
    - "tests/test_gui_pins.py"
decisions:
  - "Filter INSIDE PickupSpawner (single choke point) rather than at the gui_game call-site, so tests and future callers inherit the exclusion"
  - "Viewer materialize path NOT routed through the exclusion: biphenyl stays loadable + viewable from the manifest"
metrics:
  duration: "~10 min"
  completed: "2026-10-01"
---

# Quick Task 001: Remove biphenyl from the gameplay spawn pool — Summary

**One-liner:** Set-aware `GAMEPLAY_EXCLUDED_MOLS` exclusion in the pure spawn policy drops the always-clashing set_a biphenyl from the pickup serve pool (spawner self-filter) and from head selection (combo filter + `effective_head_id` fallback), while the manifest/viewer/refusal-test fixtures stay byte-identical.

## What was delivered

1. **Spawn-pool exclusion (pure core).** `spawn.GAMEPLAY_EXCLUDED_MOLS = (('set_a', 'biphenyl'),)` + `is_gameplay_excluded(record)` (set-aware (set, id) keying — upload id-collisions unaffected). `PickupSpawner.__init__` self-filters the serve order BEFORE any rng draw, so GAME-07 seed-stream determinism is preserved for the surviving 4-record pool.
2. **Head-selection exclusion.** `spawn.effective_head_id(setup, records)` PURE pre-pass: `'random'`/eligible/unknown/upload ids pass through; a stale saved `head_molecule='biphenyl'` degrades to the FIRST eligible record (anchored order = benzene). `gui_setup._populate_head_combo` skips excluded records (single seam: display, `_head_candidates`/Randomize, and `collect_state` all inherit; stale JSON degrades to Random via the apply_state findData miss). `gui_game._build_head_state` resolves through `spawn_mod.effective_head_id` upstream of the **untouched** `pymol_bridge._select_head_record`.
3. **Amendments + follow-up.** Dated 2026-10-01 owner-approved comments in spawn.py / setup_logic.py (refuse path now TEST-only); `PHASE8-NOTE.md` records the 08-* docs/release-audit follow-up obligations (zero phase-8 files touched, per owner directive).

## Verification

- `python3.6 tests/run_gates.py` — full default battery green **all three commits** (931 unittests; +8 new pins vs. the pre-task 923).
- Refusal fixtures unchanged + green: `tests.test_placement` (incl. TestBiphenylRefusal), `tests.test_phase5_integration` (incl. test_s4), `tests.test_demo_data` — 57 tests OK, zero diff.
- Behavioral spot-proof (headless, pure): spawner over the 5 demo records → `pool_size == 4`; 8 seeded spawns serve `benzene, naphthalene, anthracene, phenanthrene` cyclically, never biphenyl; `effective_head_id({'head_molecule': 'biphenyl'}, records) == 'benzene'`.
- Viewer contract intact: `git diff serpentrum/pymol_bridge.py` empty; biphenyl still in the manifest (test_demo_data green).
- Scope guard: `git status` shows only the plan's `files_modified`.

## Deviations from Plan

1. **[Rule 2 — Missing Critical] `test_spawn.py` module docstring count.** The plan specified adding the "12. Exclusion" docstring entry in Task 1 but did not mention updating the "Eleven pin groups" count or adding a Task-2 entry for `TestEffectiveHeadId`. Amended: "Twelve" → "Thirteen" pin groups + a "13. Head resolver" entry, so the docstring stays truthful.
2. **[Rule 2 — Missing Critical] `gui_game._build_head_state` docstring.** It claimed the head record is selected "the SAME way materialize does" — no longer accurate once the gameplay pre-pass intercepts. One sentence added noting the quick-001 pre-pass; behavior untouched.

No bugs, blockers, authentication gates, or architectural decisions encountered. The plan's stale figure of "840 baseline" unittests refers to the Phase-7-close count; the actual pre-task baseline was 923 (Phase 8 plans landed in between) and the final gate count is 931 — the deltas from this task are exactly the +8 new pins.

## Commits

| Task | Commit | Message |
| ---- | ------ | ------- |
| 1 | 43d8cb0 | feat(quick-001): exclude set_a biphenyl from the pickup spawn pool |
| 2 | 4740335 | feat(quick-001): exclude set_a biphenyl from head selection (combo filter + gameplay fallback) |
| 3 | 271dfed | docs(quick-001): refuse-demonstrator amendment comment + Phase-8 follow-up note |

## Follow-ups

- **Phase 8 (recorded in `PHASE8-NOTE.md`):** re-scope any 08-* docs/release-audit language presenting biphenyl as playable/stackable; re-word the STACK-05 "refuse demonstrator" (now TEST-only: "permanent refuse-path demonstrator in the test suite; excluded from live gameplay pools since 2026-10-01"); optionally note the demo set offers 4 stackable species (+ uploads).
- **Post-execution optional (not run here):** the full `--smoke` battery — smoke/04 exercises only the data path (manifest → setloader → materialize → head switch → cleanup_srp), never the gameplay spawn pool, and is unaffected by design.
