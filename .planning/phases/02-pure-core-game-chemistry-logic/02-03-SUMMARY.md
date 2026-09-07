---
phase: 02-pure-core-game-chemistry-logic
plan: 03
subsystem: chemistry-io
tags: [xyz-format, file-io, element-validation, xtb-handoff, round-trip, stdlib-only, python3.6]

# Dependency graph
requires:
  - phase: 01-foundation (repo skeleton, gates)
    provides: tests/ discovery conventions, purity gate (tools/check_purity.py), run_gates.py harness, committed xtb-spike fixtures under .planning/research/xtb-spike-fixtures/
provides:
  - serpentrum/xyzio.py — ELEMENT_SYMBOLS (118 case-sensitive IUPAC symbols), XyzError, write_xyz, write_xyz_file, read_xyz_text, read_xyz
  - Round-trip proof that the snake->xtb handoff format preserves all four committed geometries (symbols exact, coords <= 1e-8, comments exact, second write byte-identical)
  - Pre-xtb element validation (bad.xyz 'Xx' rejected with line number before any xtb run is wasted)
affects: [02-xxtbenv/runner plans (writes snake input, reads xtbopt.xyz), stacking (dimer2 placement math consumes parsed atoms), spectra plans (consume fixture geometries), phase-6 runner]

# Tech tracking
tech-stack:
  added: [] # zero new libraries — PURE stdlib module with zero imports
  patterns:
    - "XyzError carries 1-based line number + ~60-char offending-line snippet"
    - "Writer is a fixed point: %15.8f re-serialization of parsed 8-decimal values is byte-identical"
    - "Fixtures read IN PLACE from .planning/research/xtb-spike-fixtures/ (parallel-worktree-safe; no copies)"

key-files:
  created:
    - serpentrum/xyzio.py
    - tests/test_xyzio.py
  modified: []

key-decisions:
  - "Case-sensitive element matching ('Cl' yes, 'CL'/'cl' no) mirrors xtb's own 'Cannot map symbol to atomic number' failure mode"
  - "Writer validates only structure (length mismatch, row != 3); symbol validity is enforced on READ, so any written frame parses back or raises loudly"
  - "Comment sanitization replaces each \\r/\\n char with a single space (a raw newline would corrupt the frame)"
  - "Blank lines between atom rows are ignored on read; extra NON-empty rows beyond the declared count are rejected"

patterns-established:
  - "Error messages always start 'line N:' for reader failures — bad data points at the exact row"
  - "Round-trip tolerance 1e-8 with byte-identical second write as the fixed-point proof"

# Metrics
duration: 11min
completed: 2026-09-07
---

# Phase 2 Plan 3: .xyz Handoff I/O Summary

**Pure xyzio writer/reader with 118-symbol case-sensitive validation; all four committed xtb-accepted geometries (co2, phenol, dimer2, xtbopt) round-trip with exact comments/symbols, coords within 1e-8, and a byte-identical fixed-point second write.**

## Performance

- **Duration:** 11 min
- **Started:** 2026-09-07T19:12:01Z
- **Completed:** 2026-09-07T19:22:32Z
- **Tasks:** 2/2
- **Files modified:** 2 created

## Accomplishments
- `serpentrum/xyzio.py`: PURE stdlib module (zero imports at all) — `ELEMENT_SYMBOLS` frozenset of all 118 IUPAC symbols (case-sensitive), `XyzError(ValueError)` naming the 1-based line + ~60-char snippet, `write_xyz` (count line, newline-sanitized comment, `'%-2s %15.8f %15.8f %15.8f'` rows), `write_xyz_file` (utf-8), `read_xyz_text`/`read_xyz` handling leading-space count lines (phenol `'    13'`), arbitrary comments (incl. xtbopt's `' energy: ...'` with leading space), unaligned rows, and blank-line tolerance
- Structural validation raises before any geometry is used: non-int count, non-positive count, fewer rows (expected-vs-found named), extra non-empty rows, <4 tokens, non-float coords, unknown symbol — every message starts `line N:`
- `tests/test_xyzio.py`: 22 tests — writer structure + direct row-format string assertions, comment sanitization, exact fixture reads (co2 3 atoms, phenol 13 with committed element order, dimer2 26), bad.xyz `'Xx'` rejection at line 3, all inline rejections, per-fixture round-trips, cross-consistency, and byte-identical fixed-point proof

## Task Commits

Each task was committed atomically:

1. **Task 1: xyzio module — writer, reader, validation + unit tests** - `bf33c98` (feat)
2. **Task 2: fixture round-trips (co2, phenol, dimer2, xtbopt) + full verification** - `060f957` (feat)

## Files Created/Modified
- `serpentrum/xyzio.py` — the snake->xtb handoff format: writer/reader pair with element-symbol validation (PURE, stdlib-only, zero imports, py3.6 syntax)
- `tests/test_xyzio.py` — writer/reader unit tests + in-place fixture round-trips + bad.xyz rejection (sys.path self-insert, no `__init__.py`)

## Decisions Made
- Element symbols matched case-sensitively (118 symbols, 'Cl' valid; 'CL'/'cl' rejected) — mirrors xtb's own failure mode "Cannot map symbol to atomic number" so rejection happens BEFORE an expensive xtb run
- Writer validates structure only (element/coord length mismatch, row not 3-long -> XyzError); symbol validity is a reader concern, so anything written round-trips or raises loudly
- Comment sanitization: each `\r`/`\n` replaced by a single space (so `\r\n` becomes two spaces — content is arbitrary, only newline-freedom matters)
- Read: blank lines ignored anywhere in the atom block; extra NON-empty rows beyond the declared count rejected; fewer rows error names expected-vs-found and cites line 1 (the false declaration)
- Fixtures read IN PLACE from `.planning/research/xtb-spike-fixtures/` (committed → present in every worktree); `tests/fixtures/xtb/` copies from plan 02-01 deliberately NOT used (later-wave plans); dimer.xyz never touched (mislabeled CO2 dimer)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required

None - no external service configuration required.

## Verification

- `python3.6 -m unittest discover -s tests -p "test_xyzio.py" -v` → OK (22 tests)
- `python3.6 -m unittest discover -s tests -p "test_*.py" -v` → OK (54 tests: 22 xyzio + 32 pre-existing skeleton/purity/winpath)
- `python3.6 tests/run_gates.py` → all gates green (syntax+plugin-path safety, AST purity, scoped unittest)
- `python3.6 tools/check_purity.py` → clean (xyzio.py auto-classified PURE)
- Fixtures read IN PLACE only — `git status` shows no new files under `.planning/research/`

## Next Phase Readiness
- xyzio is ready for the runner-side plans: snake geometry → `write_xyz_file` (xtb input), xtb output → `read_xyz('xtbopt.xyz')`; element validation fires before any subprocess
- `read_xyz` returns `(comment, [(symbol, x, y, z), ...])` — the tuple shape later consumers (stacking placement math, game engine) can consume directly
- No blockers; wave-1 sibling plans (spectra, molecule_data/stacking) untouched — this plan imported no sibling modules per parallelism rules

---
*Phase: 02-pure-core-game-chemistry-logic*
*Completed: 2026-09-07*
