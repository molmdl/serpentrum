---
phase: 02-pure-core-game-chemistry-logic
plan: 09
subsystem: testing
tags: [vibspectrum, turbomole, spectra-parsing, threshold-filter, synthetic-fixture, co2]

# Dependency graph
requires:
  - phase: 02-01
    provides: g98 parser core (Mode/Atom/Spectrum namedtuples, SpectraParseError, _to_int/_to_float/_fail helpers, 17 fixture copies incl. vibspectrum)
provides:
  - parse_vibspectrum_text / parse_vibspectrum (Turbomole fallback parser)
  - real_modes(spectrum, threshold=10.0) — |freq|-only trivial-mode filter
  - Synthetic CO2 vibspectrum fixture (8-row linear-molecule case)
  - Synthetic-fixture provenance/labeling rules (README.md)
affects: [02-12 (broaden + parse dispatcher), 02+ spectra consumers, phase-6 xtb pipeline]

# Tech tracking
tech-stack:
  added: []  # pure stdlib only, no new libraries
  patterns:
    - "Threshold-based trivial-mode filtering: abs(m.freq) >= threshold (never sign, never selection column, never hardcoded 5/6 count)"
    - "Uniform field indexing for variable-token-count rows: t[-3]=freq, t[-2]=intensity works for both 4-token trivial and 5-token real rows"
    - "Synthetic fixtures: clearly labeled, provenance cited in # comments, unknown values honestly omitted (never invented)"

key-files:
  created:
    - tests/test_spectra_vibspectrum.py
    - tests/fixtures/xtb/synthetic/co2_vibspectrum
    - tests/fixtures/xtb/synthetic/README.md
  modified:
    - serpentrum/spectra.py
    - tests/test_spectra_g98.py

key-decisions:
  - "Mode namedtuple stays 4-field (02-01 contract); symmetry/selection parsed for grammar validation but not stored"
  - "$end check runs before header check so empty/header-only input hits the missing-$end path (plan's loud-failure contract)"
  - "real_modes returns the SAME Mode objects (identity, not copies) — pure list comprehension filter"
  - "Synthetic CO2 fixture: 2593.38 asymmetric stretch honestly omitted (log intensity token is overflow '******')"

patterns-established:
  - "Threshold filter on |freq| only: linear molecules have 5 trivial modes, nonlinear 6 — a hardcoded count would silently corrupt linear molecules"
  - "Synthetic fixture labeling: # SYNTHETIC label + provenance citation in # comments + honest omission of unknown values"
  - "In-memory test corruption: malformed inputs built from fixture text at runtime, never by modifying fixture files on disk"

# Metrics
duration: 64 min
completed: 2026-09-08
---

# Phase 2 Plan 09: Vibspectrum Fallback Parser + Trivial-Mode Filter Summary

**Turbomole vibspectrum fallback parser + threshold-based trivial-mode filter (|freq| only) with a synthetic linear-CO2 fixture proving 5-trivial (not 6)**

## Performance

- **Duration:** 64 min
- **Started:** 2026-09-08T19:52:26Z
- **Completed:** 2026-09-08T20:56:30Z
- **Tasks:** 3
- **Files modified:** 5 (2 created tests + 2 created synthetic fixtures + 1 spectra.py + 1 g98 test fix)

## Accomplishments

- `parse_vibspectrum_text` / `parse_vibspectrum` appended to 02-01's g98-only module: parses the Turbomole-format vibspectrum file (78-mode dimer fixture) with uniform `t[-3]`/`t[-2]` field indexing for both 4-token trivial rows and 5-token real rows; all numeric conversions wrapped via existing `_to_int`/`_to_float` helpers (never bare ValueError)
- `real_modes(spectrum, threshold=10.0)` — pure `abs(m.freq) >= threshold` filter, order preserved, returns same Mode objects (identity); policy-verified against both the dimer (6 trivial, 72 real incl. 3 negative) and the synthetic CO2 (5 trivial, 3 real)
- Synthetic CO2 vibspectrum fixture: 8 rows transcribed from committed co2.log eigvals/intensities, 5 trivial + 3 real (degenerate 600.18 bend pair + intensity-exactly-0.00 symmetric stretch at 1424.95); 2593.38 asymmetric stretch honestly omitted (overflow `******`)
- 25 tests total: 8 happy-path (78-mode table, negatives, near-zero intensity, symmetry-a), 10 filter (dimer/CO2/threshold-parametrization/g98-no-op), 7 loud-failure (missing $end, bad header, garbage row, non-numeric, empty, comment tolerance)
- Full gate suite green on python3.6 (259 tests, 0 stubs)

## Task Commits

Each task was committed atomically:

1. **Task 1: vibspectrum parser + real-fixture tests** — `f08e681` (feat)
2. **Task 2: real_modes filter + synthetic CO2 fixture** — `083c9dc` (feat)
3. **Task 3: loud-failure tests** — `a971362` (test)

## Files Created/Modified

- `serpentrum/spectra.py` — Appended `parse_vibspectrum_text`, `parse_vibspectrum`, `real_modes` (no existing function modified)
- `tests/test_spectra_vibspectrum.py` — 341 lines: grammar + filter + CO2 + failure-mode tests
- `tests/fixtures/xtb/synthetic/co2_vibspectrum` — 8-row synthetic linear-CO2 Turbomole fixture
- `tests/fixtures/xtb/synthetic/README.md` — Provenance + labeling rules, dimer.xyz trap warning
- `tests/test_spectra_g98.py` — Fixed fixture-dir check to filter directories (Rule 3 deviation)

## Decisions Made

- **Mode stays 4-field:** The 02-01 Mode namedtuple (`index freq intensity vectors`) was not extended — the plan's explicit `Mode(index=mode, freq=freq, intensity=intensity, vectors=())` construction uses only 4 fields. Symmetry and selection are parsed (for grammar validation and correct `t[-3]`/`t[-2]` indexing) but not stored. The "symmetry 'a' on all real modes" test requirement is satisfied by verifying the fixture file directly (5-token rows carry 'a' in `t[1]`).
- **$end check before header check:** Implemented so that empty text and header-only text both hit the missing-$end path (matching the plan's loud-failure contract for case 5). For a wrong-header-but-valid-$end input, the $end check passes and the header check fires correctly.
- **real_modes returns same objects:** The filter is a list comprehension `[m for m in spectrum.modes if abs(m.freq) >= threshold]` — returns the same Mode objects (identity proven by `assertIs` in the g98 no-op test), not copies.
- **Comment tolerance test interpretation:** The plan says "prepend an extra '# anything' line to the fixture text" — prepending before the header would break the line-1 header check. The comment was inserted after the header (line 2), which tests the same invariant (comment lines within the file body are skipped) and is consistent with the synthetic fixture's structure (comments after the header).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed test_spectra_g98 fixture-dir check to filter directories**

- **Found during:** Task 2 (creating tests/fixtures/xtb/synthetic/ directory)
- **Issue:** The 02-01 test `test_fixture_dir_holds_exactly_the_17_file_set` used `sorted(os.listdir(FIXTURES))` which includes subdirectories. Adding the `synthetic/` subdir (required by the plan) caused the exact-listing assertion to fail with 18 entries instead of 17.
- **Fix:** Changed the check to filter directories: `files = [name for name in os.listdir(FIXTURES) if os.path.isfile(os.path.join(FIXTURES, name))]`. The test's intent (guard against trap FILES: dimer.xyz, hessian, xtbrestart) is fully preserved; only subdirectories are now allowed.
- **Files modified:** tests/test_spectra_g98.py (1 test method, 3 lines changed)
- **Verification:** `test_fixture_dir_holds_exactly_the_17_file_set` passes; all 17 file copies still verified byte-identical; full suite green
- **Committed in:** 083c9dc (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** The fix was necessary to add the plan-required synthetic/ directory without breaking the 02-01 suite. No scope creep — the test's trap-file guard intent is preserved.

## Issues Encountered

None — all three tasks executed cleanly. The co2.log provenance (eigvals lines 456-457, IR intensities header 545 / values 546-547, line 240 linear check) was re-verified against the committed file before transcribing the synthetic fixture.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- **Ready for 02-12:** `parse_vibspectrum` + `real_modes` are in place; 02-12 will add the line-shape convolution (`broaden`) and the parse dispatcher (auto-detect g98.out vs vibspectrum). The Mode/Spectrum contract and SpectraParseError pattern are established.
- **Ready for Phase 6:** The xtb pipeline can consume vibspectrum as a fallback when only `--ohess` g98.out is available, or as the standalone format when g98.out is absent.
- **No blockers.** The synthetic-fixture labeling pattern (SYNTHETIC + provenance + honest omission) is established for future synthetic test data.

---
*Phase: 02-pure-core-game-chemistry-logic*
*Completed: 2026-09-08*
