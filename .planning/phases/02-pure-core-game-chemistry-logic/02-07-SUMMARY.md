---
phase: 02-pure-core-game-chemistry-logic
plan: 07
subsystem: setup-schema
tags: [setup, schema, validation, json, seeded-random, unittest, py36, stdlib-only]

# Dependency graph
requires:
  - phase: 01-plugin-skeleton-purity-harness
    provides: gates harness (tests/run_gates.py), AST purity auto-classification (default-PURE), test conventions (sys.path self-insert, scoped discovery, no tests/__init__.py), py3.6 bool-is-int awareness
provides:
  - serpentrum/setup_logic.py: SCHEMA_VERSION, DEFAULTS (9 keys), BOX_PRESETS, KNOWN_SETS, HESSIAN_WARNING, SetupError
  - new_setup() -> fresh dict(DEFAULTS) copy; validate(setup) -> (errors, warnings) with per-key errors + single N-cubed hessian warning
  - save_setup(setup) -> sorted-key indented JSON (validates first; errors -> SetupError); load_setup(text) -> dict (corrupt JSON / foreign schema / non-dict -> SetupError, v1 loud-fail)
  - randomize_head(candidates, seed) -> random.Random(seed).choice (private seeded RNG, never global random)
affects: [Phase-3 setup tab (Qt wiring), Phase-4 GameEngine box extents, Phase-6 xtb runner (SPECTRA-06 runtime warning re-check), Phase-8 educator share-a-setup flow (SETUP-07/08)]

# Tech tracking
tech-stack:
  added: [] # stdlib only (json, os, random)
  patterns:
    - "Private seeded RNG per call (random.Random(seed)) — never the global random module; seed-to-seed isolation proven by interleaved-call test"
    - "Local path-rule mirror of a parallel-plan module (_xtb_path_problems duplicates xtbenv.validate_binary_path rules locally because xtbenv is a parallel wave-1 plan not importable here; 'keep in sync' comment; unify later)"
    - "validate() returns (errors, warnings) as data — never raises for invalid input; errors are precise per-key strings in a documented order"
    - "Single warning fired once when EITHER cap>10 OR budget>100 (not one per trigger)"

key-files:
  created:
    - serpentrum/setup_logic.py
    - tests/test_setup_logic.py
  modified: []

key-decisions:
  - "SCHEMA_VERSION=1; v1 ships Set A only (KNOWN_SETS=('set_a',)); load_setup raises loudly on foreign schema_version (friendly UX deferred to Phase 8 SETUP-08)"
  - "xtb_path rules kept in a LOCAL _xtb_path_problems helper (same exists/is-file/no-quote rules as xtbenv.validate_binary_path) because xtbenv is a parallel wave-1 plan and may not exist in this worktree — comment marks it 'keep in sync with serpentrum/xtbenv.py; a later wave may unify'"
  - "randomize_head uses random.Random(seed).choice — a fresh private RNG instance per call; import random at module level is the necessary module import, with ZERO global random.choice/random.seed calls (the key_links pattern random.Random(seed) is satisfied)"
  - "_is_number helper guards the py3.6 bool-is-int trap (isinstance(True,int) is True) so a bool setup value is rejected as a non-number, not silently coerced"
  - "validate never raises — _is_number guards every numeric comparison so a non-numeric cap/budget/speed/fwhm produces an error string instead of a TypeError"
  - "save_setup treats warnings as advisory (a high cap/budget still serializes); only errors block save"

patterns-established:
  - "Setup schema is a flat dict of scalars/None — shallow dict(DEFAULTS) copy suffices for new_setup (no nested mutables)"
  - "Validation result is (errors: [str], warnings: [str]) data, not exceptions — callers branch on the lists"

# Metrics
duration: 12 min
completed: 2026-09-08
---

# Phase 2 Plan 07: Setup Logic Summary

**Pure `setup_logic` module: documented DEFAULTS + BOX_PRESETS, per-key `validate` with the single exact N-cubed hessian warning, save/load JSON round-trip, and seed-deterministic `randomize_head` via private `random.Random` — 46 tests, stdlib-only, zero stubs.**

## Performance

- **Duration:** 12 min (738 s)
- **Started:** 2026-09-08T18:22:13Z
- **Completed:** 2026-09-08T18:34:31Z
- **Tasks:** 2/2
- **Files modified:** 2 created (serpentrum/setup_logic.py, tests/test_setup_logic.py)

## Accomplishments
- `validate` produces precise per-key error strings (schema_version, demo_set, box_preset, win_cap_molecules 1..20, atom_budget >=1, xtb_path, speed>0, broadening_fwhm>0, head_molecule non-empty str) in the documented order and NEVER raises — every numeric comparison is guarded by the bool-safe `_is_number` helper so non-numeric input yields an error string, not a TypeError.
- The single N-cubed hessian-cost warning fires EXACTLY ONCE when EITHER `win_cap_molecules > 10` OR `atom_budget > 100` (both over -> still one warning), with the pinned message `'hessian cost scales ~N^3; a ~100-atom snake may take 30-90 s'` — the pure half of SETUP-06 / SPECTRA-06.
- `save_setup`/`load_setup` round-trip a setup dict identically as sorted-key indented JSON; corrupt JSON, non-dict payloads, and foreign schema_version each raise a precise `SetupError` (v1 loud-fail; friendly UX is Phase 8).
- `randomize_head` is seed-deterministic via a private `random.Random(seed)` instance per call — two same-seed calls always agree and an intervening different-seed call never perturbs a seed's result (proven by an interleaved-call test). Zero global-`random` RNG calls.
- `new_setup()` returns a fresh `dict(DEFAULTS)` copy; mutating a returned dict never touches the module-level DEFAULTS (copy semantics proven).

## Task Commits

Each task was committed atomically:

1. **Task 1: defaults, box presets, validate() with the N-cubed warning** - `3b7b8c0` (feat)
2. **Task 2: save/load round-trip + seeded randomize + full verification** - `9d733a6` (feat)

**Plan metadata:** (see final commit below)

## Files Created/Modified
- `serpentrum/setup_logic.py` (265 lines) — PURE stdlib module: SCHEMA_VERSION, DEFAULTS, BOX_PRESETS, KNOWN_SETS, HESSIAN_WARNING, SetupError, new_setup, _is_number, _xtb_path_problems, validate, save_setup, load_setup, randomize_head
- `tests/test_setup_logic.py` (364 lines) — 46 tests: defaults shape/copy semantics, full error matrix (incl. bool-trap), xtb_path matrix, warning matrix, never-raises, save/load round-trip + sorted-key JSON, load error cases, seeded determinism + private-RNG isolation

## Decisions Made
- **Local `_xtb_path_problems` mirror rather than importing `xtbenv`:** `xtbenv` is a parallel wave-1 plan and may not exist in this worktree; the exists/is-file/no-quote rules are duplicated locally with a "keep in sync with serpentrum/xtbenv.py; a later wave may unify" comment. This is exactly the plan's `key_links` instruction.
- **`import random` at module level + `random.Random(seed)` usage:** the key_links pattern `random\.Random\(seed\)` requires the literal `random.Random(seed)` in source, which in turn requires the `random` module import. The grep verification (`^import random|random.choice|random.seed`) matches ONLY the `import random` line — there are zero global `random.choice`/`random.seed` calls. This is the correct, required interpretation of "no global-random usage (only random.Random(seed) instances)".
- **Warnings are advisory for `save_setup`:** a setup with cap>10 or budget>100 still serializes (it is valid, just slow); only `validate` errors block save.
- **`load_setup` validates schema_version only:** per the pinned design, v1 does not full-validate a loaded dict — the caller runs `validate()` on the untrusted result. A dedicated test (`test_load_does_not_full_validate`) pins this boundary.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- `serpentrum/setup_logic` is import-safe and PURE; Phase 3's setup tab can edit a `new_setup()` dict and call `validate()` for live error/warning display, and Phase 4's `GameEngine(box_min, box_max)` consumes `BOX_PRESETS[preset]` directly.
- Phase 6's runner re-checks the N-cubed warning at runtime (SPECTRA-06 runtime half) — the exact `HESSIAN_WARNING` literal here is the shared anchor.
- Phase 8's educator share-a-setup flow (SETUP-07/08) builds on `save_setup`/`load_setup`; the v1 loud-fail `SetupError`s here are the precise exceptions Phase 8 will wrap in friendly UX.
- Unify `_xtb_path_problems` with `xtbenv.validate_binary_path` in a later wave (both implement identical rules; the local copy exists only because xtbenv is a parallel plan).
- Verification evidence: `python3.6 -m unittest discover -s tests -p "test_setup_logic.py" -v` -> 46 OK; full discovery -> 213 OK; `python3.6 tests/run_gates.py` -> exit 0 (syntax+safety, purity, unittest all PASS); `python3.6 tools/check_purity.py` -> clean; global-random grep -> only the `import random` line (no `random.choice`/`random.seed`).

---
*Phase: 02-pure-core-game-chemistry-logic*
*Completed: 2026-09-08*
