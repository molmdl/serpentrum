---
phase: 02-pure-core-game-chemistry-logic
plan: 12
subsystem: testing
tags: [spectra, gaussian-broadening, parse-dispatcher, index-correspondence, phenol, corrupt-fixture, loud-failure]

# Dependency graph
requires:
  - phase: 02-01
    provides: g98 parser core (Mode/Atom/Spectrum namedtuples, SpectraParseError with stage+line+excerpt, _to_float/_to_int/_fail/_excerpt helpers, 17 fixture copies incl. g98.out + bad.log + ohess.log + phenol.xyz + vibspectrum)
  - phase: 02-09
    provides: parse_vibspectrum_text/parse_vibspectrum (Turbomole fallback), real_modes threshold filter, synthetic CO2 8-row fixture (2593.38 honestly omitted)
provides:
  - broaden(modes, fwhm, x_min, x_max, n_points) — stdlib-math Gaussian sum; empty-modes pinned zero curve
  - parse_text(text) / parse(path) — unified format-sniffing dispatcher (vibspectrum/g98/unrecognized)
  - g98<->vibspectrum index-correspondence proof (offset=3N-len(g98_modes)=6, 0 mismatches over 72 modes at 0.01/1e-4)
  - Phenol-monomer eigval cross-check (ohess.log 39=3*13 projected freqs, 33=3N-6 real)
  - Loud-failure guarantee on every corrupt path (bad.log, truncated g98, ****** overflow in both formats)
affects: [phase-7 spectra tab (consumes broaden xs,ys directly), 02+ spectra consumers]

# Tech tracking
tech-stack:
  added: []  # pure stdlib math only (math.exp/sqrt/log), no numpy
  patterns:
    - "Gaussian broadening as pure stdlib-math sum: sigma = fwhm/(2*sqrt(2*ln2)) precomputed at import; grid computed at runtime, never hardcoded"
    - "Empty-modes pinned zero curve: broaden([]) returns (grid, [0.0]*n_points) — a silent spectrum plots as flat zero, never an exception"
    - "Content-sniffing parse dispatcher: first non-blank line == '$vibrational spectrum' -> vibspectrum; 'Standard orientation:' in text -> g98; else loud error"
    - "Index correspondence: offset = 3*N - len(g98_modes) computed from files (NEVER hardcoded); cross-checked against vibspectrum trivial-row count"
    - "Float-arithmetic-path matching in tests: expected values computed via dx*dx*inv_sigma_sq (same path as broaden), not (dx/sigma)**2 — exp amplifies 1-ULP differences for large exponents"

key-files:
  created:
    - tests/test_spectra_broadening.py
    - tests/test_spectra_robustness.py
  modified:
    - serpentrum/spectra.py

key-decisions:
  - "broaden() is pure stdlib math (no numpy — WSL python3.6.9 has none); 72 modes x 800 points is trivial"
  - "Default x_max = max(3600.0, max_freq + 5*sigma) — the 3600 floor keeps the plotted axis at the xtb display range; empty modes default to [x_min, 3600.0]"
  - "Negatives summed (not clipped): their in-grid tail at x=0 is negligible (exp(-11) at -31.9 with fwhm 16); the grid starting at 0.0 keeps influence below 1e-4 of peak"
  - "Zero-intensity modes contribute exactly 0 by arithmetic (0.0 * exp(...) = 0.0) — proven by exact list equality broaden([m1]) == broaden([m1, m0])"
  - "parse_text() dispatcher checks first non-blank line for vibspectrum, then 'Standard orientation:' anywhere for g98 — bad.log (neither marker) hits the unrecognized-format path, not the g98 parser"
  - "Index-correspondence tolerances 0.01/1e-4: 2x the vibspectrum 2-decimal freq rounding bound (0.005) and 2x the g98 4-decimal intensity rounding bound (5e-5) — 100-1000x tighter than any mode-mispairing error"
  - "No hardening needed: 02-01/02-09 already wrap ALL numeric conversions via _to_float/_to_int; float('******') surfaces as SpectraParseError, not ValueError"

patterns-established:
  - "broaden() zero-curve semantics: empty mode list -> (grid, [0.0]*n_points); never an exception"
  - "Runtime sigma computation in tests: always compute sigma = fwhm/(2*sqrt(2*ln2)) from the fwhm constant; never hardcode 6.794574 or 13.58915"
  - "Index-correspondence offset derivation: 3*N - len(g98_modes) computed from files, cross-checked against vibspectrum trivial-row count — two independent derivations agree"
  - "In-memory corrupt-variant tests: truncation and ****** overflow built from fixture text at runtime (splitlines/slice/replace); fixture files on disk never modified"

# Metrics
duration: 8 min
completed: 2026-09-09
---

# Phase 2 Plan 12: Spectra Completion (Broadening + Dispatcher + Loud Failures) Summary

**Gaussian broaden() (stdlib-math, empty-modes zero curve), unified parse_text()/parse() dispatcher, g98<->vibspectrum index-correspondence proof (72 modes, 0 mismatches), phenol ohess.log eigval cross-check (39=3*13), and loud SpectraParseError on every corrupt-fixture path — closing success criterion 2 across the phenol, CO2 and pi-stacked-dimer legs**

## Performance

- **Duration:** 8 min
- **Started:** 2026-09-09T02:48:36Z
- **Completed:** 2026-09-09T02:56:30Z
- **Tasks:** 3
- **Files modified:** 3 (serpentrum/spectra.py, tests/test_spectra_broadening.py, tests/test_spectra_robustness.py)

## Accomplishments
- **broaden()** — pure stdlib-math Gaussian sum: sigma = fwhm/(2*sqrt(2*ln2)) (16->6.794574, 32->13.58915); 800-point default grid spanning [0.0, max(3600.0, max_freq+5*sigma)]; empty modes -> pinned zero curve (grid, [0.0]*n_points); negatives summed (not clipped, tail <1e-4 of peak); zero-intensity modes contribute exactly 0 (arithmetic proof via exact list equality); raises ValueError on fwhm<=0 or n_points<2
- **Dimer curve anchors verified**: peak within ±fwhm of 1150.6639 (257.1018 km/mol global max); x=0 tail ratio 2.9e-5 (<1e-4); strongest low mode 364.42 @ 98.605 dominates its neighborhood
- **CO2 synthetic curve**: degenerate 600.18 pair (2x68.70=137.4) is the only intensity carrier; 1424.95 symmetric stretch is silent (intensity exactly 0.00, exact list equality with the pair alone); 2593.38 honestly absent
- **Unified parse_text()/parse()**: content-sniffing dispatcher routes vibspectrum/g98/unrecognized without silent guessing; bad.log hits the unrecognized-format path
- **Index correspondence**: offset = 3*26 - 72 = 6 (computed from files, cross-checked against vibspectrum trivial-row count); 0 mismatches over all 72 modes at freq 0.01 / intensity 1e-4; exact boundary case mode 53 (g98 0.0233 vs vibspectrum 0.02325 = 5e-5) passes the 1e-4 tolerance
- **Phenol eigval cross-check**: ohess.log's first projected-frequency block carries 39 = 3*13 eigvals (first 6 ≈0 trivial, remaining 33 = 3N-6 real, min 218.56); N=13 read from phenol.xyz; test-side line parsing (not a new parser)
- **Loud-failure guarantee**: bad.log (no frequency section), truncated g98 mid-atom-rows (line 480) and mid-header (line 470), and ****** overflow in both g98 and vibspectrum intensities all raise SpectraParseError (never bare ValueError) with stage + 1-based line number

## Task Commits

Each task was committed atomically:

1. **Task 1: Gaussian broadening (broaden) + broadening tests** — `550e514` (feat)
2. **Task 2: Unified parse dispatcher + index correspondence + phenol eigvals** — `03b0349` (feat)
3. **Task 3: Corrupt-fixture loud failures** — `523f6e4` (test)

**Plan metadata:** (pending — committed after this SUMMARY)

## Files Created/Modified
- `serpentrum/spectra.py` — appended broaden(), parse_text(), parse() (475 -> 510 lines); added `import math`; existing parse_g98/parse_vibspectrum behavior unchanged
- `tests/test_spectra_broadening.py` — 286 lines, 20 tests: grid shape, non-negativity, peak location (1150.6639), peak amplitude, strongest low mode (364.42), negative tail (<1e-4), zero-intensity exact-zero (list equality + arithmetic), CO2 synthetic (600.18 pair, silent 1424.95), fwhm=32 parameterization, empty-modes zero curve, ValueError guards
- `tests/test_spectra_robustness.py` — 372 lines, 23 tests: unified dispatcher (6), index correspondence (6), phenol eigvals (5), corrupt-fixture loud failures (6)

## Decisions Made
- **broaden() arithmetic path**: uses `dx * dx * inv_sigma_sq` (precomputed 1/sigma^2) rather than `(dx/sigma)**2` — both are mathematically equal but the former avoids a per-point division and matches the test's expected-value computation path (exp amplifies 1-ULP differences for large exponents)
- **parse_text() sniffing order**: vibspectrum checked first (first non-blank line == '$vibrational spectrum'), then g98 ('Standard orientation:' anywhere in text) — bad.log (neither marker) hits the unrecognized-format path before reaching either parser
- **No hardening needed**: verified that 02-01/02-09 already wrap all numeric conversions via _to_float/_to_int; float('******') surfaces as SpectraParseError with stage+line+excerpt, not as a bare ValueError. No code changes to the existing parsers were required.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed plan arithmetic error: "39 == 3*13-6"**
- **Found during:** Task 2 (phenol eigval cross-check)
- **Issue:** The plan states "39 eigvals == 3*13-6 for 13-atom phenol" but 3*13-6 = 33, not 39. The ohess.log projected-frequency block carries ALL 3N = 39 frequencies (including 6 trivial translation/rotation contaminants ≈0); the remaining 33 = 3N-6 are real vibrational modes. The plan conflated 3N (total projected) with 3N-6 (real vibrational).
- **Fix:** The test asserts the correct arithmetic: `len(eigvals) == 3 * N == 39` (all projected frequencies) and `len(eigvals[6:]) == 3 * N - 6 == 33` (real modes). The first-6-≈0 and remaining-33-positive checks are unchanged (they were correct in the plan).
- **Files modified:** tests/test_spectra_robustness.py
- **Verification:** test_ohess_first_block_has_3N_eigvals and test_ohess_real_mode_count_is_3N_minus_6 both pass; all 345 tests green
- **Committed in:** 03b0349 (Task 2 commit)

**2. [Rule 1 - Bug] Fixed test arithmetic path mismatch (exp ULP amplification)**
- **Found during:** Task 1 (zero-intensity arithmetic check at x=700)
- **Issue:** The test computed the expected value as `10*exp(-0.5*(200/sigma)**2)` but broaden() computes `intensity * exp(-0.5 * dx * dx * inv_sigma_sq)`. The two arithmetic paths differ by a 1-ULP rounding (division vs multiplication by precomputed inverse), which exp amplifies for large exponents (~7e-188 in this case): `7.18212087483094e-188 != 7.182120874830532e-188`.
- **Fix:** The test now computes the expected value using the exact same arithmetic path as broaden(): `dx = 200.0; inv_sigma_sq = 1.0/(sigma*sigma); expected = 10.0 * exp(-0.5 * dx * dx * inv_sigma_sq)`. This produces a bit-identical result.
- **Files modified:** tests/test_spectra_broadening.py
- **Verification:** test_zero_intensity_mode_arithmetic_at_x_700 passes with assertEqual (exact equality)
- **Committed in:** 550e514 (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (2 bugs — plan arithmetic error + test arithmetic-path mismatch)
**Impact on plan:** Both fixes necessary for correct test execution. No scope creep; the verified fixture facts (39 eigvals, first 6 ≈0, remaining 33 positive) were correct — only the plan's arithmetic notation was wrong.

## Issues Encountered
None — the existing 02-01/02-09 parser infrastructure (SpectraParseError, _to_float/_to_int wrappers, _fail helper) already handled all corrupt-failure paths; no hardening was needed for Task 3.

## User Setup Required
None — no external service configuration required.

## Next Phase Readiness
- **broaden() is ready for Phase-7 spectra tab**: the plot consumes broaden()'s (xs, ys) directly; default fwhm=16.0 matches the project-state locked decision (DEFAULTS broadening_fwhm 16.0)
- **parse()/parse_text() is ready for the Phase-6 xtb pipeline**: the runner can hand either g98.out or vibspectrum to a single entry point
- **All corrupt inputs fail loudly**: success criterion 2's "fails loudly on the corrupt fixture" is closed across the phenol (ohess.log eigvals), CO2 (synthetic vibspectrum), and pi-stacked-dimer (g98.out) legs
- **Prior spectra tests unbroken**: 02-01's 18 g98 tests and 02-09's 25 vibspectrum tests stay green; total suite 345 tests pass; all gates green (syntax/safety/purity/unittest)
- No blockers or concerns

---
*Phase: 02-pure-core-game-chemistry-logic*
*Completed: 2026-09-09*
