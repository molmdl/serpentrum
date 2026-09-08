# Synthetic Fixtures

Every file in this directory is **synthetic** — built for unit tests, never
a measurement or a shipped chemistry value. Synthetic fixtures are clearly
labeled with `# SYNTHETIC` comment lines and their provenance is cited
inline in the file's own `#` comments.

## Provenance rules

1. Every synthetic file must state `SYNTHETIC` in a `#` comment near the
   top.
2. The source (which committed fixture/log it was transcribed from, with
   line numbers) must be cited in `#` comments.
3. If a value is **unknown** (e.g. an overflow token `******` in the
   source log), the corresponding mode/row must be **honestly omitted** —
   never replaced with an invented stand-in number. An invented chemistry
   value is forbidden by the project's "do NOT make up anything" rule
   (AGENTS.md / spec.md).
4. Synthetic fixtures are **not** byte-identical to any source file — they
   are test artifacts transcribed from source data.

## Files

- `co2_vibspectrum` — 8-row synthetic Turbomole vibspectrum for linear CO2,
  transcribed from `.planning/research/xtb-spike-fixtures/co2.log`
  (eigvals lines 456-457, IR intensities header 545 / values 546-547).
  5 trivial modes + 3 real (doubly-degenerate 600.18 bend pair + the
  intensity-exactly-0.00 symmetric stretch at 1424.95). The 2593.38
  asymmetric stretch is honestly omitted (its log intensity token is the
  overflow `******`).

## Trap warning: dimer.xyz

`tests/fixtures/xtb/dimer.xyz` is **mislabeled** — it is actually a CO2
dimer, not a phenol dimer. Never mine it for phenol data. This synthetic
directory is the correct route for CO2-specific test cases.
