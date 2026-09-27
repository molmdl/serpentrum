---
phase: 08-demo-data-docs-release-audit
plan: 05
subsystem: testing
tags: [setup-persistence, tdd, pure, python3.6, seed-determinism, xtb]

# Dependency graph
requires:
  - phase: 08-demo-data-docs-release-audit
    provides: GATE D decision record (08-01) — d1-option-c-staleness verdict
  - phase: 5.1-game-speed-difficulty
    provides: merge_defaults backcompat seam, SPEED_TIERS table
  - phase: 02-pure-core
    provides: setup_logic validate/save/load/randomize_head foundations
provides:
  - setup_logic.randomize_setup(setup, candidates, seed=None) — seeded FULL-setup concrete randomizer (Randomize button's pure half)
  - setup_logic.normalize_loaded(merged, path_problems_fn) — xtb-path load portability policy
  - XTB_PATH_NORMALIZED_NOTE — the exact house wording for the friendly status note
  - TestRandomizeSetup (8 tests) + TestNormalizeLoaded (5 tests) pinning both contracts
affects: [08-08 (GUI wiring of Randomize + Load Setup), 08-09 (staleness text fix — NOT owed here), GATE V educator round-trip (08-11)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Read-decision pattern: executor reads the GATE D SUMMARY first and implements the recorded verdict verbatim (option id + key set quoted below)"
    - "Dependency-injection purity: filesystem judgment enters pure code only via an injected problems fn (normalize_loaded), mirroring the _xtb_path_problems delegation"
    - "Validate rule referencing instead of magic-number restating: RANDOMIZE_WIN_CAP_MIN/MAX derive from validate()'s pinned 1..20 range"

key-files:
  created: []
  modified:
    - serpentrum/setup_logic.py (randomize_setup + RANDOMIZE_* bounds + normalize_loaded + XTB_PATH_NORMALIZED_NOTE)
    - tests/test_setup_logic.py (+13 tests; all pre-existing 68 pins unmodified)

key-decisions:
  - "GATE D verdict d1-option-c-staleness implemented as-is: FULL-setup randomize scope (head + box + win cap + speed + fwhm), consent/env keys never touched"
  - "broadening_fwhm choices are DEFAULTS-scaled (16.0 x 0.5..1.5) rather than uniform floats — concrete, validate-clean, typical-linewidth values"
  - "speed drawn from SPEED_TIERS VALUES (never a synthesized number) so the result is always a named tier"

patterns-established:
  - "Randomize writes CONCRETE values only (Pitfall D): a saved file reproduces exactly what the user saw — 'random' never written back into the dict"
  - "Normalize-on-load policy for environment-specific keys: save as-is, rewrite-to-None + friendly note on load (GATE D default #1)"

# Metrics
duration: 5min
completed: 2026-09-28
---

# Phase 8 Plan 5: TDD Pure Persistence Helpers Summary

**Seed-deterministic FULL-setup randomizer and xtb-path load normalization in setup_logic, implementing the GATE D d1-option-c-staleness verdict via the read-decision pattern — SETUP-08's pure half, zero new imports, 852-test suite green.**

## GATE D verdict implemented (read-decision record)

- **Option id:** `d1-option-c-staleness` (owner, 2026-09-28 — 08-01-SUMMARY.md, round 2).
- **Owner words (verdict, verbatim):** `"1=c-staleness for item 1"`.
- **Contract mapping (quoted from 08-01-SUMMARY.md):** "08-05 implements: `randomize_setup(setup, candidates, seed=None)` writes CONCRETE values for ALL of: `head_molecule` (via existing `randomize_head` seam, from candidates), `box_preset` (from BOX_PRESETS), `win_cap_molecules` (validate-legal range), `speed` (a SPEED_TIERS value), `broadening_fwhm` (validate-legal range). Consent key NEVER touched. Seed-deterministic (private random.Random)."
- **Key set implemented (exactly the verdict):** head_molecule, box_preset, win_cap_molecules, speed, broadening_fwhm. Untouched by contract: schema_version, demo_set, atom_budget, xtb_path, generic_stack_consent (+ any unknown extra keys pass through).
- **NOT owed here:** the stale-clause text fix ("head will be randomized at game start") is 08-09 scope per the same verdict record — this plan touched no GUI text.
- **normalize_loaded note wording** comes from GATE D default #1 (CONFIRMED row): `'xtb path not found on this machine - using auto-detect'` (ASCII), saved as module constant `XTB_PATH_NORMALIZED_NOTE`.

## Performance

- **Duration:** ~5 min
- **Started:** 2026-09-27T18:15:32Z (UTC host clock)
- **Completed:** 2026-09-27T18:20:33Z (UTC host clock)
- **Tasks:** 2/2 (both strict TDD: RED commit then GREEN commit)
- **Files modified:** 2

## Accomplishments

- `randomize_setup(setup, candidates, seed=None)`: FULL-setup concrete randomizer per the GATE D verdict — head via the existing `randomize_head` seam (concrete candidate, never `'random'` — Pitfall D guard), box_preset from `BOX_PRESETS`, win_cap within validate's pinned 1..20 (module constants derived from validate's rule, no restated magic numbers), speed = one of `SPEED_TIERS` values, fwhm = DEFAULTS-scaled validate-clean value; one private `random.Random(seed)`; consent + environment keys never touched; input never mutated; `seed=None` entropy path.
- `normalize_loaded(merged, path_problems_fn)`: xtb-path portability policy — None path untouched (DI fn not consulted), valid path untouched, foreign path rewritten to None with the exact house note; returns `(merged, note)`; input never mutated; DI fn called exactly once; setup_logic stays PURE (zero new imports).
- TDD discipline visible in history: both helpers landed as RED (AttributeError-confirmed) → GREEN (full suite) commit pairs.

## Task Commits

1. **Task 1 RED:** failing `TestRandomizeSetup` (8 tests) — `40330af` (test)
2. **Task 1 GREEN:** `randomize_setup` implementation — `c30d2a7` (feat)
3. **Task 2 RED:** failing `TestNormalizeLoaded` (5 tests) — `9a79bb6` (test)
4. **Task 2 GREEN:** `normalize_loaded` implementation — `e72a963` (feat)

**Plan metadata:** (docs commit for PLAN + this SUMMARY follows)

## Files Created/Modified

- `serpentrum/setup_logic.py` — added `RANDOMIZE_WIN_CAP_MIN/MAX`, `RANDOMIZE_FWHM_FACTORS`, `randomize_setup()`, `XTB_PATH_NORMALIZED_NOTE`, `normalize_loaded()`; imports unchanged (json, random, intra-package xtbenv)
- `tests/test_setup_logic.py` — added `TestRandomizeSetup` (8 tests) + `TestNormalizeLoaded` (5 tests); all pre-existing classes (TestDefaults/EXPECTED_DEFAULTS, TestSaveLoadRoundTrip, TestLoadSetupErrors, TestMergeDefaults, TestRandomizeHead, XtbPathUnificationTest, validate matrix, consent suite) unmodified

## Decisions Made

- `broadening_fwhm` concrete choices = `DEFAULTS['broadening_fwhm'] * factor` (0.5/0.75/1.0/1.25/1.5 → 8/12/16/20/24 cm^-1): validate pins only `> 0`, so typical-linewidth scaled values keep results concrete and honest rather than arbitrary uniform floats.
- Win-cap bounds declared as `RANDOMIZE_WIN_CAP_MIN/MAX` (1..20) derived from validate's pinned range rather than restated literals at the draw site; validate() itself untouched (no second validation authority).
- `normalize_loaded` returns a fresh-dict tuple in all branches (uniform purity) and does NOT consult the DI fn for a None path (pinned by test; avoids a pointless filesystem touch).

## Deviations from Plan

None — plan executed exactly as written. (One transient placeholder line was typed and immediately removed during test authoring, before any test run or commit; never entered history.)

## Issues Encountered

None. RED phases produced exactly the expected AttributeError failures (8 + 5); GREEN phases passed on first run; gates green (852 unittests, syntax/plugin-path safety, AST purity).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- 08-08 (GUI wiring) can now wire Randomize -> `randomize_setup` and Load Setup step 5 -> `normalize_loaded` exactly as the research flow prescribes (08-RESEARCH-persistence.md Q2 Load flow, steps 5-7).
- 08-09 owes the stale Apply/Start status-clause text fix (GATE D verdict record) — independent of this plan.
- No blockers. Suite baseline: 852 unittests (was 840; +13 here, -1 rounding of prior count).

---
*Phase: 08-demo-data-docs-release-audit*
*Completed: 2026-09-28*
