# Phase 2: Pure Core — Game & Chemistry Logic — Research

**Researched:** 2026-09-06
**Domain:** eight stdlib-only pure modules (`spectra`, `xtbenv`, `xyzio`, `molecule_data`, `stacking`, `game_engine`, `setup_logic`, `cgo_build`) + python3.6 unittest suite against committed real xtb fixtures
**Confidence:** HIGH for all fixture-derived facts (every number below was probed today against the committed files); HIGH for test/gate conventions (Phase 1 code read); MEDIUM where explicitly flagged (remainder-block grammar, repro_oh invocation, engine tuning constants).

All fixture claims carry exact byte/line evidence gathered 2026-09-06 by running python3.6 probes against `.planning/research/xtb-spike-fixtures/` (see Sources). Nothing here is fabricated; chemistry *values* (the π-stack distance, citations) are NOT invented by this document — the dataset ships DRAFT and the human approval track pins them (FEATURES.md).

---

## Summary

Phase 2 builds the entire non-GUI brain of serpentrum: the spectra parser (written fixture-first against real xtb 6.7.1pre outputs), the xtb success contract and binary detection, the .xyz handoff I/O, the data-driven stacking loader + placement math, the 2D snake engine, setup defaults/validation, and pure CGO builders. Every module is stdlib-only (WSL python3.6.9 has **no numpy** — verified F22 in ARCHITECTURE.md) and lands under the existing Phase 1 purity gate, which auto-classifies new modules PURE.

The fixture characterization (R1) produced three load-bearing discoveries that shape the design: **(1)** the committed `dimer2.xyz` is an *eclipsed, pure z-translation* dimer — fragment 2 = fragment 1 + (0, 0, 3.4) **exactly** (max error 0.0 Å) — so the stacking test can assert bit-level reproduction of the stored geometry; **(2)** `repro_oh.log/.err` document a run that terminated *normally* (stderr "normal termination of xtb") but produced **no** Hessian/frequency output — hard proof the success contract's expected-files leg is load-bearing, not belt-and-braces; **(3)** the g98.out↔vibspectrum↔log index correspondence is proven with zero mismatches across all 72 real modes (vibspectrum mode k = g98 mode k−6 for the 26-atom dimer), which becomes a fixture test.

The engine-model contradiction (R4: research said "grid", GAME-05 says geometric) resolves to **continuous 2D coordinates**: GAME-05's "head-centroid vs chain segments", GAME-10's rigid pivot sweeps, and STACK-01's "placed geometry equals the cited distance" are all incompatible with grid quantization. The grid language in ARCHITECTURE.md is stale shorthand.

**Primary recommendation:** four plans in two waves — wave A (parallel, disjoint files): ① spectra parser + tests, ② xyzio + xtbenv, ③ molecule_data + stacking + clash gate; wave B: ④ game_engine + setup_logic + the pure integration test. All TDD; every module has a crisp input→output contract.

---

## 1. Fixture Inventory (R1)

Directory: `.planning/research/xtb-spike-fixtures/` (committed). All files CRLF-terminated unless noted. Files group into **four runs** + shared inputs:

| File | Size | What it is | Molecule / run | Parser target? |
|------|------|-----------|----------------|----------------|
| `phenol.xyz` | 15 ln / 717 B | input geometry, 13 atoms C₆H₆O, element order `CCCCCCHHHHHOH` (6C, 5 ring-H, O, O–H), comment "Optimized at B3LYP/6-31G* level"; count line has leading spaces (`    13`) — xtb accepts | phenol input (runs: ohess, repro_oh) | **xyzio round-trip** |
| `co2.xyz` | 5 ln | input, 3 atoms, linear CO₂ (C 0,0,0; O ±1.16,0,0), minimal formatting | CO₂ input (run: co2) | **xyzio round-trip** |
| `dimer2.xyz` | 28 ln | input, 26 atoms, phenol π-dimer; **fragment 2 = fragment 1 + (0,0,3.4) with max error 0.0**; comment "stacked phenol dimer 3.4A z-offset" | dimer input (run: dimer2) | **stacking reproduction + xyzio** |
| `dimer.xyz` | 8 ln | 6 atoms — **actually a CO₂ dimer** (2×C,O,O at z=0 and z=3.4) despite stale "phenol" comment; early spike artifact | CO₂ stacking spike | context only (comment is misleading — do not use as phenol data) |
| `bad.xyz` | 4 ln | 2 atoms, symbol `Xx` (invalid element) | failure-provoking input | **xyzio rejection test** |
| `ohess.log` | 747 ln | full `--ohess` log: opt + **Numerical Hessian** block + Frequency Printout; 39 eigvals (= 3×13−6) in two sections (lines 494, 637 "projected vibrational frequencies"); total energy −19.953114258312 Eh | phenol | context / cross-check |
| `repro_oh.log` | 640 ln | phenol run ending at "optimized geometry written to: xtbopt.xyz" → "finished run" — **NO Numerical Hessian block, NO frequency section** (grep-verified zero matches for "Numerical Hessian" and "vibrational frequenc"); final energy −19.954146097121 Eh; **stderr still says "normal termination of xtb"** | phenol (repro; exact flags UNVERIFIED — settings block doesn't echo them; behavior consistent with opt-only) | **success-contract test case** |
| `co2.log` | 639 ln | CO₂ `--ohess` log: settings line `linear (good luck)  true` (line 240); freq section: eigvals `0.00 ×5, 600.18, 600.18, 1424.95, 2593.38` (line 456-457); IR intensities `0.00 ×5, 68.70, 68.70, 0.00, ******` (line ~459) — **the 1424.95 symmetric stretch has intensity exactly 0.00**, and note the log's overflow token `******` for 2593.38 | CO₂ | **linear-molecule semantics + synthetic CO₂ vibspectrum derivation** |
| `dimer2.log` | 912 ln | dimer `--ohess` log; two eigval sections (78 values each, lines 573+ and ~765+), both equal `vibspectrum` freqs exactly (0 mismatches) | phenol dimer | **index-correspondence cross-check** |
| `bad.log` | 105 ln | citation banner then `[ERROR] Program stopped due to fatal error` (line 97): "reading geometry input 'bad.xyz' failed", "Cannot map symbol to atomic number", with file:line diagnostic (`...bad.xyz:3:1-2`, `Xx ... unknown element`); **no frequency section** | bad run | **parser loud-failure test input** |
| `ohess.err` `co2.err` `dimer2.err` `repro_oh.err` | 1 ln (27 B) each | `normal termination of xtb\r\n` | all four success runs | **xtbenv contract fixtures** |
| `bad.err` | 1 ln (29 B) | `abnormal termination of xtb\r\n` | bad run. **Exit code NOT recorded in fixtures** — 128 comes from PITFALLS 3 `[RUN]`; unit tests use synthetic rc values | **xtbenv contract fixture** |
| `g98.out` | 883 ln (884 CRLF split) | **the parser's primary target** — dimer run (26 atoms). Structure below | phenol dimer | **spectra.py** |
| `vibspectrum` | 82 ln | Turbomole-format fallback — dimer run, 78 rows = 6 trivial + 72 real | phenol dimer | **spectra.py fallback** |
| `hessian` | 1249 ln | Turbomole `$hessian`, 6084 = 78² values, 5 per line, row-major | phenol dimer | **NO — Anti-Pattern 5 (never parse/eigendecompose)** |
| `xtbhess.xyz` | 28 ln | run's input echo (26 atoms, comment " xtb: 6.7.1pre (5071a88)") | phenol dimer | xyzio format reference |
| `xtbopt.xyz` | 28 ln | optimized geometry, comment `energy: -39.914402395930 gnorm: 0.000144376846 xtb: 6.7.1pre (5071a88)` | phenol dimer | xyzio format reference |
| `xtbopt.log` | 196 ln | optimization trajectory (xyz frames with energy comments) | phenol dimer | context |
| `charges` | 26 ln | per-atom charges (%f per line) | phenol dimer | context |
| `wbo` | 30 ln | Wiberg bond orders (`i  j  value`) | phenol dimer | context |
| `xtbrestart` | 6 ln | binary restart file | phenol dimer | context |
| `xtbtopo.mol` | 57 ln | MOL V2000 topology ("26 26  0 … 999 V2000") | phenol dimer | context |

**Which files the parser consumes:** `g98.out` (primary: freq + intensity + per-atom vectors in one file), `vibspectrum` (freq/intensity fallback, no vectors). Logs are *not* parse targets (the "Frequency Printout" in logs is a bonus cross-check only — its `eigval` lines confirmed the fixture correspondence above). `hessian` is explicitly out (ARCHITECTURE Anti-Pattern 5).

### 1.1 g98.out exact grammar (probed line-by-line)

Whole file CRLF. Layout (1-based line numbers for the dimer fixture):

```
  1-5    " Entering Gaussian System" / banner / "Gaussian 98:" / "frequency output generated by the xtb code"
  7      " Standard orientation:"
  8-11   header: "Center Atomic Atomic Coordinates (Angstroms)" / "Number Number Type X Y Z" / dashes
  12-37  26 atom rows, 6 whitespace tokens each:
         center_index  atomic_number  type(0)  X  Y  Z        (coords %12.6f)
         ANs seen: 6=C, 1=H, 8=O.  Fragment 1 = rows 1-13, fragment 2 = rows 14-26.
  38     dashes (terminates atom block)
  39     " 1 basis functions   1 primitive gaussians"   (xtb filler — ignore)
  40     blank
  41-43  "Harmonic frequencies (cm**-1), IR intensities (km*mol⁻¹)," /
         "Raman scattering activities (A**4/amu)..." / "reduced masses (AMU), force constants..."
  44     mode-index line: 3 right-aligned ints, field starts (0-based) at 22, 45, 68
  45     symmetry line: "a" at 0-based 24, 47, 70 (trailing space on line)
  46     " Frequencies --   -31.9175               -23.0766               -18.1086"
  47     " Red. masses -- ..."
  48     " Frc consts  -- ..."
  49     " IR Inten    --     2.4191                 0.0072                 0.2541"
  50     " Raman Activ --"   (all 0.0000 — xtb computes no Raman)
  51     " Depolar     --"   (all 0.0000)
  52     " Atom AN      X      Y      Z        X      Y      Z        X      Y      Z"
  53-78  26 atom rows, 11 whitespace tokens each:
         atom_index  AN  x1 y1 z1  x2 y2 z2  x3 y3 z3        (vectors %7.2f, values |v| ≤ ~1)
  79-80  next block's mode-index (4 5 6) + symmetry lines
  ...
  851    last "Frequencies --" (modes 70 71 72: 3113.7215, 3519.9549, 3521.1843)
  852-883 last block body → EOF immediately after the last atom row. NOTHING follows.
```

**Block math (verified):** stride = 35 lines ("Frequencies" → next "Frequencies": 81−46); block = 2 (idx+sym) + 6 (`--` rows) + 1 (Atom AN header) + N atom rows. 24 blocks × 3 = 72 modes = 3×26−6 ✓. File ends at EOF after the final block — **the frequency section is terminated by end-of-file** (nothing else follows; the last block has exactly 34 lines after its header).

**Values (verified):** first three freqs −31.9175 / −23.0766 / −18.1086 (negatives present, matching vibspectrum modes 7-9); IR intensities: min 0.00030, **no exact 0.00000 among the 72 real modes** (the exact-zero IR case exists only in the CO₂ story — see §1.3); Raman/Depolar all zero; frequency span −31.9175 → 3521.1843 cm⁻¹.

**Parsing rules that survive this layout (recommended):**
- Read with `encoding='utf-8'` (the header contains UTF-8 `⁻¹`; fixtures verified UTF-8) and split lines with `str.splitlines()` — neutralizes CRLF and any trailing-newline absence.
- Never parse by fixed columns. For the six `--` rows: `line.split('--', 1)[1].split()` → token list; **the token count defines the block's column count** (3 normally, 1-2 in a remainder block). Cross-check all six rows have equal token counts.
- Mode-index / symmetry lines: optional; ignore content (column count comes from the Frequencies line).
- Atom rows: whitespace-split → `[idx, AN] + 3×ncols floats`; assert `len(tokens) == 2 + 3*ncols` and atom index runs 1..N in order.
- Atom block: whitespace-split rows of 6 tokens between the two dash lines after "Standard orientation:"; assert count == atom rows per block.
- Remainder block (N mod 3 ≠ 0): **UNVERIFIED against real fixtures** — this dimer has none (72 = 24×3). xtb/Gaussian convention says the last block simply has fewer columns; the token-count-driven rules above handle it structurally. Synthetic remainder-block test text must be built by truncating the 3-column pattern (planner note: keep one synthetic test, clearly labeled synthetic).

### 1.2 vibspectrum exact grammar (probed)

All 82 lines CRLF-terminated including `$end` (verified: 82 CRLF, 82 LF, split yields `[..., b'$end', b'']`).

```
  1   "$vibrational spectrum"
  2   "#  mode     symmetry     wave number   IR intensity    selection rules"
  3   "#                         cm**(-1)      (km*mol⁻¹)        IR     "
  4-9   trivial rows: tokens = [mode, freq, intensity, '-']  (4 tokens — symmetry column EMPTY)
        e.g. "     1                      -0.00         0.00000          - "
        note literal negative zero "-0.00" on rows 1-4, "0.00" on 5-6
  10+   real rows: tokens = [mode, symmetry, freq, intensity, selection]  (5 tokens)
        e.g. "     7        a            -31.92         2.41910         YES"
  82   "$end"
```

**Row counts (verified):** 78 rows = 6 trivial + 72 real for the 26-atom dimer (3N = 78 ✓). Frequencies: 5 decimals (g98 uses 4 — correspondence tolerance 1e-4/2). Selection rules across all rows: `YES ×58, NO ×14, '-' ×6` (trivial). Symmetry: `'a' ×72, empty ×6`. **Negative rows: modes 7, 8, 9 = −31.92, −23.08, −18.11** (real modes, selection YES/NO/YES — negatives are NOT trivial modes).

**Trivial-mode filter policy (fixture-supported):** a row is trivial iff `|freq| < threshold` (default ~10 cm⁻¹) — corroborated by empty symmetry + `'-'` selection. **Do NOT filter on selection-rule NO** — 14 real modes have `NO` with nonzero intensity (min 0.00026) and must stay in the table. **Do NOT hardcode "skip 6"** — CO₂ has 5 (PITFALLS 12.1; `co2.log:240`).

### 1.3 CO₂ / linear-molecule facts (from `co2.log`, since no CO₂ vibspectrum/g98.out was committed)

- Settings line: `linear (good luck)  true` (co2.log:240); `degrees of freedom 4` (line ~236).
- Frequency printout (co2.log:456-457): eigvals `0.00, 0.00, 0.00, 0.00, 0.00, 600.18, 600.18, 1424.95, 2593.38` — **5 trivial modes** (3N−5 = 4 real), **doubly-degenerate bend 600.18 ×2**.
- IR intensities (co2.log:459-460): `0.00 ×5, 68.70, 68.70, 0.00, ******` — **symmetric stretch 1424.95 cm⁻¹ has intensity exactly 0.00** (the required zero-intensity case); asymmetric stretch 2593.38 renders as overflow token `******` in the *log* format (a warning that xtb text fields can overflow — g98/vibspectrum %f fields are the safe parse targets).
- **Fixture gap (flag):** no CO₂ `g98.out`/`vibspectrum` was committed. Phase 2 options: (a) build a **synthetic CO₂ vibspectrum** in the test, constructed from the co2.log eigvals/intensities and clearly labeled synthetic (recommended — keeps the zero-intensity + 5-trivial tests honest without new Windows-xtb runs), or (b) optionally re-run `xtb.exe co2.xyz --ohess` and commit the real files (a legitimate stretch task — the xtb leg is proven by `tests/run_gates.py --xtb`, but it adds a Windows dependency to a WSL-only phase; default (a)).

### 1.4 Failure fixtures

- `bad.log`: 105 lines; `[ERROR] Program stopped due to fatal error` at line 97; cause "Cannot map symbol to atomic number" with `bad.xyz:3:1-2` diagnostic. Contains **no frequency section** → feeding it to `parse_g98` must raise loudly (the "corrupt fixture" of success criterion 2).
- `bad.err`: `abnormal termination of xtb\r\n`. Exit code not recorded in fixtures; PITFALLS 3 documents rc=128 `[RUN]`. The xtbenv unit tests therefore use **synthetic** rc values with the fixture stderr text.
- `repro_oh.log/.err`: the "silent wrong-invocation" case — stderr success, no frequency outputs anywhere. Exact invocation flags UNVERIFIED (settings block doesn't echo argv; log shape matches an opt-only run: ends at "optimized geometry written to: xtbopt.xyz", has zero "Numerical Hessian" / "vibrational frequenc" matches). Use as the canonical test case for the **expected-files leg** of the success contract.

### 1.5 Geometry facts for stacking (R3 anchor)

- `dimer2.xyz`: fragment 1 = atoms 1-13, fragment 2 = atoms 14-26, same element sequence (`CCCCCCHHHHHOH`). **fragment2 = fragment1 + (0,0,3.4) exactly** (max abs error 0.0 over all 13 atoms). All-atom centroid and C-ring centroid coincide in x,y between fragments; centroid-centroid distance = 3.4000 Å; ring-plane separation = 3.4000 Å. The committed "stacked" geometry is **eclipsed face-to-face (zero lateral displacement, zero azimuth rotation)** — the schema must still carry a lateral-offset field (Set A's eventual Janiak-pinned value is parallel-displaced; FEATURES.md flags the specific value UNVERIFIED until data-prep).
- Min **inter**-fragment atom distance in dimer2: 3.4000 Å (eclipsed C···C). Min **intra**-fragment (bond) distance: 0.9646 Å (O–H). PITFALLS 10 `[RUN]`: xtb optimized this dimer cleanly at 3.4 Å with zero spurious inter-molecular bonds.
- `phenol.xyz` ≈ dimer2 fragment 1 but NOT identical (max diff 0.0226 Å — dimer2's fragment is a slightly different conformer). Tests must use dimer2's own fragment 1 as the placement input, not phenol.xyz.

---

## 2. Proposed API — `serpentrum/spectra.py` (R2)

All names py3.6-safe; `collections.namedtuple` verified working on 3.6.9 (probed today). Dataclasses are banned (3.7+); `typing.NamedTuple` class syntax also works on 3.6 (probed) but plain `namedtuple` matches repo minimalism.

```python
# serpentrum/spectra.py  (PURE — stdlib only: collections, io-level opens, math)

Mode = namedtuple('Mode', 'index freq intensity vectors')
#   index:     int   — 1-based, xtb's own mode number (g98: sequential over blocks;
#                    vibspectrum: the file's mode column, incl. trivial rows)
#   freq:      float — cm^-1; negatives kept as negatives (imaginary display is UI's job)
#   intensity: float — km/mol (IR); may be 0.0
#   vectors:   list of (x, y, z) float tuples per atom — len == n_atoms;
#                    empty list () when parsed from vibspectrum (no vectors there)
Atom = namedtuple('Atom', 'atomic_number x y z')

Spectrum = namedtuple('Spectrum', 'n_atoms atoms modes')
#   atoms: list of Atom (from the g98 Standard-orientation block); [] for vibspectrum
#   modes: list of Mode, in file order

class SpectraParseError(ValueError):
    """Loud failure: message MUST contain the parser stage, 1-based line
    number(s) when applicable, and the offending line's first ~80 chars."""

def parse_g98_text(text):            # -> Spectrum
def parse_g98(path):                 # opens encoding='utf-8', delegates to _text
def parse_vibspectrum_text(text):    # -> Spectrum (atoms=[], vectors=() per Mode)
def parse_vibspectrum(path):
def real_modes(spectrum, threshold=10.0):   # -> list[Mode]; drops |freq| < threshold.
    # Applies to vibspectrum-derived spectra; for g98 spectra xtb already
    # projected trivial modes out (72 = 3N-6 verified) — filter is a no-op there
    # but harmless to run. Policy: threshold on |freq| ONLY; never on the
    # selection-rule column (14 real 'NO' rows have nonzero intensity — §1.2).
def broaden(modes, fwhm=16.0, x_min=0.0, x_max=None, n_points=800):
    # -> (xs, ys): stdlib-math Gaussian sum, y = sum(I_i * exp(-0.5*((x-f_i)/sigma)^2))
    # sigma = fwhm / (2*sqrt(2*ln(2)))  ≈ fwhm/2.35482
    # x_max default: max(3600.0, max(freq)+5*sigma) — clamps negatives' influence at
    # x>=0 to a negligible tail (exp(-11) at -31.9 with fwhm 16) — negatives are
    # NOT special-cased out; zero-intensity modes contribute exactly 0 by arithmetic.
```

**Parser spec (what line triggers what, in order)** — planner turns this directly into code + tests:

1. Split text via `splitlines()` (kills CRLF; handles missing trailing newline).
2. Atom block: find the line whose stripped form == `Standard orientation:`; expect the dashed header (3 lines) then rows of exactly 6 tokens until a dashed line. `n_atoms` = row count. Fewer than 3 atoms or malformed row → `SpectraParseError('atom block', lineno, line)`.
3. Frequency blocks: scan for lines starting with `' Frequencies --'` (leading space significant in fixture; use `line.startswith(' Frequencies --')` after verifying — fixture lines always carry the leading space). For each: `cols = line.split('--',1)[1].split()`; `ncols = len(cols)`; require 1 ≤ ncols ≤ 3. The next 5 lines must be `Red. masses --`, `Frc consts --`, `IR Inten --`, `Raman Activ --`, `Depolar --` (prefix match) each with `ncols` float tokens; then `' Atom AN'`-prefixed header; then exactly `n_atoms` rows of `2 + 3*ncols` tokens with sequential atom indices 1..n_atoms. Any violation → `SpectraParseError` with stage + line number + line excerpt.
4. Missing frequency section entirely (e.g. `bad.log`) → `SpectraParseError('no frequency section found', ...)` — the loud-failure contract.
5. Mode `index`: running count starting at 1 across blocks (matches vibspectrum real-mode numbering offset — see below).
6. vibspectrum: require line 1 == `$vibrational spectrum` and a final `$end`; rows are token lists of len 4 (trivial, symmetry='') or 5 (real); `mode=int(t[0])`, `symmetry=t[1] if len==5 else ''`, `freq=float(t[-3])`, `intensity=float(t[-2])`, `selection=t[-1]`. Handles `-0.00` negative-zero trivially (float). Missing `$end` or non-numeric fields → `SpectraParseError`.
7. **Index correspondence invariant (fixture test):** for the dimer fixtures, `len(vs_modes) == 3*n_atoms == 78`; `len(g98_modes) == 3*n_atoms - 6 == 72`; and for every j, `vs_modes[j+6].freq == approx(g98_modes[j].freq, abs=5e-5)` and `vs_modes[j+6].intensity == approx(g98_modes[j].intensity, abs=5e-5)` (verified today: **0 mismatches** across all 72 modes). The offset is `n_trivial = 3*n_atoms - len(g98_modes)` — computed, never hardcoded (6 nonlinear / 5 linear).

**Fixture test matrix for this module:**

| Test | Input | Assert |
|------|-------|--------|
| g98 happy path | `g98.out` | 26 atoms, 72 modes, first freq −31.9175, last 3521.1843, mode 1 vectors have 26 entries, negative freqs present, Raman ignored |
| vibspectrum happy path | `vibspectrum` | 78 modes, 6 trivial (`|freq|<10`), real-mode 7 = −31.92 @ 2.41910, vectors empty |
| index correspondence | both | 0 mismatches with +6 offset (computed n_trivial) |
| zero/near-zero intensity | vibspectrum + synthetic CO₂ | trivial rows intensity 0.00000 kept; 0.00026 near-zero row kept; synthetic CO₂ 1424.95 intensity exactly 0.0 contributes 0 to curve |
| negatives kept | g98 block 1 | −31.9175 present in table output; `broaden` over grid starting at 0 gives ~0 contribution from it (tail < 1e-4 of peak with fwhm 16) |
| linear molecule | synthetic CO₂ vibspectrum (from co2.log eigvals, labeled synthetic) | 5 trivial rows filtered, 4 real modes, degenerate 600.18 ×2 retained as separate rows |
| loud failure | `bad.log` text | raises `SpectraParseError` mentioning "frequency section" |
| loud failure (truncation) | g98 fixture text truncated mid-block | raises with line number |
| loud failure (vibspectrum) | fixture text with `$end` removed / garbage row | raises |
| remainder block | synthetic 4-mode text (3+1 columns), clearly synthetic | 4 modes parsed, last has 1 vector column |
| broaden | g98 modes | len(xs)==n_points; ys ≥ 0; peak location ≈ argmax intensity mode (364.42 @ 98.6 strongest low mode — assert peak within ±fwhm of 364) |

---

## 3. Proposed API — `serpentrum/stacking.py` + clash gate (R3)

**Deterministic rigid-body placement, pure python (no numpy — 3×3 tuples/lists).**

```python
# serpentrum/stacking.py  (PURE — stdlib math only)

Vec3 = tuple  # (x, y, z)

def ring_frame(atoms, ring_indices):
    """Deterministic orthonormal frame for a planar ring subset.
    Returns (centroid, normal_unit, inplane_ref_unit) or raises ValueError
    'non-planar ring (max deviation %.3f A)' if max |dot(p - c, n)| > 0.15.
    - normal: Newell's method over atoms in the given index order
      (order-stable, no degenerate cross products, pure arithmetic).
    - inplane reference axis: unit vector centroid -> FIRST ring atom,
      orthogonalized against normal. Defines azimuth=0. Same molecule in the
      same conformer => same frame in both fragments (verified on dimer2).
    - planarity tolerance 0.15 A: dimer2 rings are planar to ~1e-9; biphenyl
      handles this by listing ONE ring's atoms in the manifest."""

def place_pickup(pickup_atoms, pickup_ring_indices,
                 tail_centroid, tail_normal, tail_ref,
                 distance_a, lateral_offset_a, lateral_along_ref=True):
    """Place the pickup so that:
    - its ring centroid sits at tail_centroid + tail_normal*distance_a
      (+ lateral_offset_a * tail_ref when lateral_along_ref else a fixed
      perpendicular convention);
    - its ring plane is parallel to the tail's (normal -> tail_normal, SAME sign
      — stacking 'above' vs 'below' is the caller's sign choice on tail_normal);
    - azimuth = 0: pickup's in-plane reference axis aligns with the tail's
      projected reference axis (this is what makes dimer2 reproducible —
      the committed dimer is eclipsed).
    Returns (placed_atoms, R, t): placed_atoms as list of Vec3, R the 3x3
    rotation (tuple of 3 row-tuples), t the translation Vec3 — R and t are
    what the Phase-5 connector feeds cmd.transform_selection (matrix layout
    convention flagged OPEN in ARCHITECTURE.md §9 — verify in Phase 5).
    Frame math: build orthonormal bases E_tail=(r1,r2,n_tail),
    E_pick=(p1,p2,n_pick); R maps E_pick -> E_tail (row-composed 3x3);
    placed = R·(p - c_pick) + target_centroid."""

def check_clash(placed_atoms, existing_atoms, box_min, box_max,
                threshold_a=2.5):
    """STACK-05 pure half. Returns None if clear, else a diagnostic dict:
    {'kind': 'atom'|'wall', 'pair': (i, j), 'distance': d} — first violation.
    Atom test: min interatomic distance over placed×existing < threshold_a.
    Wall test: any placed coord outside [box_min, box_max] (inclusive)."""
```

**Threshold policy (2.5 Å, defensible from committed evidence):** the spurious-bond zone is bounded by xtb's rcov-sum bond inference — max for the demo elements ≈ C+H 1.07 Å, C+C 1.52 Å, C+O 1.42 Å, ×~1.3 tolerance ⇒ risk ceiling ≈ 1.9–2.0 Å (PITFALLS 10 mechanism). The verified-safe floor is the committed dimer's **3.4000 Å** minimum inter-fragment contact (`[RUN]` clean optimization, no cross-fragment bonds). 2.5 Å sits between with ≥0.5 Å margin both ways. It is a module constant (not a user setting in v1); Set B H-bonds (~2.6–2.7 Å, UNVERIFIED — FEATURES.md) would clear it if ever shipped.

**The reproduction test (success criterion 1):** read `dimer2.xyz`; split fragments; `ring_frame(f1, ring_indices=[0..5])` → (c, n, ref); `place_pickup(f1_coords, [0..5], c, n, ref, distance_a=3.4, lateral_offset_a=0.0)` → **assert max |placed[i] − f2[i]| < 1e-6 Å over all 13 atoms** (today's probe: the offset is exactly (0,0,3.4), so a correct implementation reproduces to float noise). Additionally assert `check_clash(placed, f1, box) is None` (the legal stack must pass its own gate) and that moving the pickup to 1.5 Å separation makes `check_clash` fire.

**Non-planar pickup:** manifest stores `ring_atoms` indices for ONE planar ring (biphenyl: one phenyl's 6 carbons). Non-aromatic molecule without entry → skipped at game level (STACK-03), never reaches placement.

---

## 4. Proposed API — `serpentrum/xtbenv.py` (R5)

```python
# serpentrum/xtbenv.py  (PURE — stdlib: os, shutil, tempfile)

XTB_OHESS = '--ohess'   # single module-level constant — Pitfall 1: never '-o --hess'
EXPECTED_FILES = ('g98.out', 'vibspectrum')   # what --ohess must produce for us
STDERR_SUCCESS = 'normal termination'
STDERR_FAILURE = 'abnormal termination'

RunVerdict = namedtuple('RunVerdict', 'ok problems')
#   problems: list of human-readable strings, one per failed contract leg

def evaluate_run(exit_code, stderr_text, expected_files, present_files):
    """Success contract (Pitfall 3): ok iff
       exit_code == 0  AND  STDERR_SUCCESS in stderr_text
       AND set(EXPECTED_FILES subset requested) ⊆ present_files.
    Caller passes expected_files (a sequence; may be ('g98.out','vibspectrum')
    or a subset e.g. ('vibspectrum',) when vectors aren't needed).
    Fixture-backed cases:
      ('normal termination of xtb', rc=0, both files) -> ok
      ('abnormal termination of xtb', rc=128 [synthetic rc; fixture bad.err],
       no files) -> problems: exit code, termination line, missing files
      ('normal termination of xtb', rc=0, NO files)  -> problems: missing files
        (the repro_oh story: stderr success is NOT sufficient — §1.4)"""

def validate_binary_path(path):
    """-> list of problem strings (empty = valid):
    exists, is a file, contains no quote characters (' or ")."""

def detect_binary(configured_path=None, which_fn=shutil.which):
    """Probe order (Pitfalls 3 / AGENTS rule):
    1. configured_path (if given): validate_binary_path; None/problems -> fall through
    2. which_fn('xtb.exe')   — Windows conda env
    3. which_fn('xtb')       — Linux
    Returns the resolved path string or None. Dependency-injected which_fn makes
    this testable WITHOUT xtb installed and WITHOUT mocking modules (pass a
    fake function; unittest.mock.patch('...which_fn') equally acceptable —
    mock of a callable seam is NOT a sys.modules stub and does not violate
    the zero-stub rule, which bans pymol/Qt sys.modules stubs)."""

def build_argv(exe_path, input_filename, extra_args=(XTB_OHESS,)):
    """-> [exe_path, input_filename] + list(extra_args). List args only (never a
    shell string — Pitfall 3.3 / security table); input_filename is a BARE
    relative name (cwd contract below); asserts no quote chars in any arg."""

def new_run_dir(base_dir):
    """-> fresh per-run directory path via tempfile.mkdtemp(prefix='srp_', dir=base_dir).
    The Phase-6 runner owns: writing snake.xyz INTO it, launching with cwd=it,
    copying g98.out/vibspectrum out, deleting it. Pure module provides the dir
    name contract only (Pitfall 3.1: never the session dir)."""
```

Consistency anchor: `tests/run_gates.py --xtb` (read in full) resolves the exe at `xtb-6.7.1/bin/xtb.exe` via the repo-root symlink, uses a `/mnt/c`-backed cwd + bare relative args, and asserts `'xtb version'` AND `'normal termination'` in captured output (run_gates.py:60-63, 184-258). xtbenv's constants and argv/cwd contract must not contradict those literals (`XTB_OHESS` is the invocation constant; the gate's `--version` probe is dev-side only).

**Unit tests without xtb installed (all WSL-native):** DI fake `which_fn` returning canned paths for 'xtb.exe'/'xtb'/None per platform scenario; `validate_binary_path` against tmpdir files (existing file / missing / path containing `"`); `evaluate_run` against the four `.err` fixture texts + synthetic rc values; `build_argv` exact list equality.

---

## 5. Proposed API — `serpentrum/xyzio.py` (R9)

Format facts proven by the committed fixtures (all accepted by xtb 6.7.1pre with normal termination): line 1 = atom count (leading whitespace tolerated — `phenol.xyz` has `    13`), line 2 = free-text comment, then per atom `Symbol X Y Z` whitespace-separated with arbitrary alignment (`dimer.xyz` rows are unaligned). Comment content is arbitrary ("Optimized at B3LYP/6-31G* level", "stacked phenol dimer 3.4A z-offset", " energy: -39.914402395930 gnorm: ...").

```python
# serpentrum/xyzio.py  (PURE — stdlib)

ELEMENT_SYMBOLS = frozenset({...})  # the 118 IUPAC symbols as a literal set
#   (plain data table, no citation needed; catches 'Xx' — the exact failure xtb
#    itself reports as "Cannot map symbol to atomic number" (bad.log:97-105) —
#    BEFORE spending an xtb run on it)

class XyzError(ValueError):
    """Loud failure: message carries line number + offending text."""

def write_xyz(elements, coords, comment=''):
    """-> text. Line 1: str(len(elements)); line 2: comment (newline-stripped);
    rows: '%-2s %15.8f %15.8f %15.8f' % (sym, x, y, z) — fixture-proven
    tolerance means any sane spacing works; pick one and round-trip it."""

def write_xyz_file(path, elements, coords, comment=''):

def read_xyz_text(text):
    """-> (comment, [(symbol, x, y, z)]). Validates: line 1 parses as int > 0;
    exactly that many atom rows; each row ≥ 4 tokens; symbol in ELEMENT_SYMBOLS;
    coords parse as float. Violations -> XyzError with line number."""

def read_xyz(path):   # encoding='utf-8'
```

**Tests:** round-trip the three real fixtures (`co2.xyz`, `phenol.xyz`, `dimer2.xyz`): read → write → read asserts identical symbols and floats (write re-serializes, so assert against re-read values; also assert read_xyz of the ORIGINAL fixture equals read_xyz of the rewritten one within 1e-8). `bad.xyz` → `XyzError` naming symbol `Xx` and line 3. Writer output structure: first line == str(n) (no padding needed — but note xtb tolerates padding either way), comment passthrough, row count. Elements/coords length mismatch → error.

---

## 6. Proposed API — `serpentrum/molecule_data.py` (R6)

Two JSON files, both inside the plugin package (plugin-path-safe: `serpentrum/` is itself the plugin package; data files are not `.py`, invisible to the purity walk and to findPlugins). Tests locate them via `os.path.join(os.path.dirname(serpentrum.__file__), 'data', ...)` — valid both under WSL test import and under `pmg_tk.startup.serpentrum` at runtime.

```
serpentrum/data/demos/manifest.json     # molecules (Phase 8 fills real Set A files)
serpentrum/data/demos/stacking.json     # interaction dataset (STACK-02)
```

**Schemas (v1, `schema_version: 1`):**

```json
// manifest.json
{"schema_version": 1,
 "sets": [{"id": "set_a", "name": "Aromatic pi-stack",
   "molecules": [{
     "id": "phenol", "name": "Phenol", "file": "phenol.xyz",
     "source_db": "PubChem", "source_id": "CID 996",
     "atom_count": 13, "charge": 0, "ring_count": 1,
     "ring_atoms": [0, 1, 2, 3, 4, 5],       // 0-based indices, ONE planar ring
     "set": "set_a"}]}]}
```

```json
// stacking.json  — values are DRAFT until the human track pins them (DATA-02).
// The distance 3.4 below reproduces the COMMITTED dimer2 fixture for testing;
// it is NOT a shipped chemistry claim (FEATURES.md: UNVERIFIED until pinned).
{"schema_version": 1,
 "interactions": [{
    "id": "pi_stack_pd", "mode": "pi_stack",
    "name": "pi-pi stacking (parallel-displaced)",
    "distance_a": 3.4, "lateral_offset_a": 0.0, "uncertainty_a": null,
    "citation": "janiak2000",
    "explanation": "Aromatic rings stack face-to-face, slightly offset.",
    "applies_to": {"sets": ["set_a"]},
    "status": "DRAFT"}],
 "citations": {"janiak2000": {"short": "Janiak 2000",
    "doi": "10.1039/b003010o", "approved": false}}}
```

The only DOI shown is the one FEATURES.md already verified live (Crossref + OpenAlex). The loader validates **structure only** (citation key resolves in `citations`; `approved` is data, not a loader opinion). No other chemistry value may be invented by code or tests — the DRAFT status + human track own the numbers.

```python
# serpentrum/molecule_data.py  (PURE — stdlib json/os)

DataError(ValueError)   # precise errors: "stacking.json interaction 0: missing key 'distance_a'"

def load_manifest(path)            # -> dict, validated (rules below)
def load_stacking(path)            # -> dict, validated
def shipped_interactions(data)     # -> [i for i in data['interactions'] if i['status'] == 'APPROVED']
                                   #     DRAFT entries stay loadable/testable but never "shipped"
def interaction_for(molecule, data)  # -> entry or None (STACK-03 refuse-and-skip input)
def validate_common(...)           # shared structural rules
```

**Validation rules (loader must reject with `DataError` + path + entry index):**
- manifest: required keys present and typed (`id`/`name`/`file`/`source_db`/`source_id` non-empty str; `atom_count` int > 0; `charge` int; `ring_count` int ≥ 1; `ring_atoms` list of unique ints < atom_count; `set` == parent set id); molecule ids unique; `file` exists under the manifest's dir (loader takes `base_dir`); `schema_version` == 1.
- stacking: `mode` non-empty str; `distance_a` float > 0 (0 < d ≤ 10 sanity); `lateral_offset_a` float ≥ 0; `status` in {'DRAFT','APPROVED'}; `citation` key resolves in `citations`; `applies_to.sets` non-empty list; ids unique.
- Synthetic valid/invalid files for tests are built in tmpdirs (`tempfile.mkdtemp`) — keeps the committed data pristine and exercises the error paths (missing key / bad type / unknown citation / duplicate id / nonexistent file).

**Demo-data approval track (starts NOW, human-gated):** pin real π-stack distance/offset from Janiak 2000 full text or a COD CIF → flip `status` to APPROVED + `approved: true` → human sign-off. Code side needs nothing more than the schema above (STACK-02's "validated data file, never code constants" is satisfied; the fixture-reproduction test consumes `distance_a` FROM the file, not from a Python constant).

---

## 7. Engine Model Resolution (R4)

**The contradiction, stated plainly:** ARCHITECTURE.md §2/§3 says "grid + snake state" / "grid positions"; REQUIREMENTS **GAME-05** says "segment-based collision: head-centroid vs chain segments"; **GAME-10** (locked) says rigid-chain pivot turns with swept-region collision refusal; **STACK-01** says placed geometry equals the cited distance. A grid contradicts all three: cell collision isn't centroid-vs-segment, pivot sweeps trace arcs (not cell steps), and quantizing placement would break the 3.4000 Å reproduction. **Resolution: continuous 2D coordinates (floats, Å) in the box's xy-plane.** The ARCHITECTURE "grid" wording is stale shorthand from before the GAME-10 turn-model decision; Pattern 3 ("engine-owns-truth") survives intact — only the coordinate system changes. Flag: update the wording when ARCHITECTURE.md is next touched (no code impact).

```python
# serpentrum/game_engine.py  (PURE — stdlib math only)

# Constants (module-level, tunable, documented):
SPEED_A_PER_S = 3.0        # constant speed (GAME-08); exact value = Phase-4 playtesting
TURN_DEGREES = 90.0        # pivot turns are quarter-turns on the 2D plane
TURN_TICKS = 6             # ticks to complete one rigid sweep (v1 coarse; pure math
                           # is tick-parameterized, animation polish is Phase-5 UI)
BODY_COLLISION_RADIUS_A = 2.0   # head-centroid vs chain-segment capsule radius
                               # MUST stay < stacking distance (3.4) minus margin,
                               # else the head "collides" with the segment just stacked
SEGMENT_SKIP_RECENT = 2    # exclude the last N segments from self-collision
PICKUP_RADIUS_A = 3.0      # head-vs-pickup capture distance (~stacking distance)

class GameEngine(object):
    """State (all plain data, deterministic, no RNG):
      head:      (x, y) float, z implicit 0
      heading:   unit vector, always one of 4 axis directions outside a sweep;
                 during a sweep: angle θ(t) interpolated
      segments:  list of segment records in chain order — each:
                 {'molecule_id', 'centroid': (x,y), 'atoms': [(sym, x, y, z)], 'atoms_n': int}
                 (stacked molecules are FROZEN rigid bodies — GAME-10 invariant;
                 rendering maps atoms from engine truth, ARCHITECTURE Pattern 3)
      pending:   deque of direction requests (max 1 buffered beyond current)
      sweeping:  None or {'start_heading', 'target_heading', 'swept_angle', 'total_ticks', 'tick'}
      counters:  molecules_stacked, atoms_total, pickups_remaining
      cap:       win cap (molecules), atom_budget
      paused, finished, result:  flags / 'crashed'|'won'|None
    """

    def request_direction(self, d):    # d in {'left','up','right','down'}
        # 180° rejection: dot(d_unit, heading_unit) < -0.5 -> ignored (locked: no reversal)
        # same-direction request ignored; perpendicular -> buffered (applied at sweep end)

    def start_sweep(self):
        """GAME-10 refusal pre-check BEFORE mutating state: sample K=TURN_TICKS+1
        intermediate angles of the WHOLE chain rotated rigidly about the head
        (each segment centroid + its atoms rotate; cheap: ≤ ~100 atoms × ~7 samples);
        run boundary + body + (remaining pickups stay put — only chain moves) checks
        at every sample. Any hit -> return refusal event, state unchanged (snake
        keeps moving forward on current heading). Else open sweep state."""

    def step(self, dt):
        """Advance one tick. paused -> no-op []. finished -> no-op [].
        - sweeping: advance sweep by one tick-share of TURN_DEGREES/TURN_TICKS;
          rotate chain rigidly about head (pure math); emit ('turning', progress).
          On completion: heading = target, sweeping = None, apply pending direction.
        - else: head += heading * SPEED*dt. Events in order:
          ('moved',) boundary hit -> ('crashed', 'boundary') [snake still complete — GAME-05]
          head vs segment capsules (segments[0..n-1-SEGMENT_SKIP_RECENT], point-to-
              segment distance < BODY_COLLISION_RADIUS_A) -> ('crashed', 'body')
          head within PICKUP_RADIUS_A of a live pickup -> ('stacked', pickup) — the
              CONTROLLER then runs stacking.place_pickup + check_clash; on clash it
              calls engine.reject_pickup(pickup) (STACK-05: refuse, pickup stays)
          molecules_stacked >= cap -> ('won',)
        Determinism: pure float math, fixed sample counts, no wall-clock, no RNG."""

    # pause(): paused = True (pure flag; timer stop is the GUI's job — Pitfall 9.3)
    # reject_pickup(pickup_id): increments its refusal count, emits ('refused', reason)
    # reset(...): full state rebuild from a setup dict (GAME-07 restart)
```

**Why not grid, one more time (for the plan's verification step):** GAME-05's literal words ("head-centroid vs chain segments") and STACK-01's "placed geometry equals the cited distance" are acceptance criteria; a grid fails both. This resolution is also the *simpler* implementation at serpentrum scale (≤ ~100 atoms).

**Boundary representation:** axis-aligned rectangle passed in as `box_min=(x0,y0), box_max=(x1,y1)` from setup_logic's preset; z-depth is display-only (bridge's concern). Head-vs-boundary: `head.x <= x0 or >= x1 or head.y <= y0 or >= y1` (with radius margin = BODY_COLLISION_RADIUS_A/2 — decide exact margin in the plan; test both inclusive/exclusive edges).

**Win cap + budget:** `cap` (molecules) triggers ('won',); `atom_budget` is a warning-level check (see setup_logic below), not a hard stop (SPECTRA-06 warns).

**Testing the engine (TDD):** deterministic scenarios with exact axis moves: crash into each wall; 180° rejection; sweep refusal when a wall/body/pickup intersects the swept arc (construct a chain near a wall, request the turn toward it); sweep completion rotates every segment centroid by exactly +90° about the head; stacked event fires at pickup radius; pause no-op; win at cap; counters exact. Use distances that avoid float equality issues (compare with `assertAlmostEqual`).

---

## 8. Proposed API — `serpentrum/setup_logic.py` (R7)

```python
# serpentrum/setup_logic.py  (PURE — stdlib json/math/random)

SCHEMA_VERSION = 1

DEFAULTS = {
    'schema_version': 1,
    'demo_set': 'set_a',
    'head_molecule': 'random',        # SETUP-04 default
    'box_preset': 'medium',           # SETUP-03; extents table below (module constant)
    'xtb_path': None,                 # SETUP-05: None = auto-detect (xtbenv.detect_binary)
    'win_cap_molecules': 10,          # SETUP-06 default (PROJECT decision ~10 mol / ~100 atoms)
    'atom_budget': 100,               # warning threshold (hessian ~N^3 — PITFALLS 2 table)
    'broadening_fwhm': 16.0,          # cm^-1; STACK.md §6: ~10-20 typical, user-tunable
    'speed': 3.0,                     # Å/s (mirrors game_engine constant)
}
BOX_PRESETS = {   # xy extents in Å; z-depth is display-only (bridge concern)
    'small': ((-12.0, -12.0), (12.0, 12.0)),
    'medium': ((-18.0, -18.0), (18.0, 18.0)),
    'large': ((-25.0, -25.0), (25.0, 25.0)),
}

def validate(setup):     # -> (errors: [str], warnings: [str])
    """errors: unknown demo_set/box_preset id; cap < 1 or > hard max (20);
    atom_budget < 1; xtb_path set but validate_binary_path() reports problems;
    schema_version != 1.
    warnings: cap > 10 molecules or projected atoms > 100 -> 'hessian cost scales
    ~N^3; a ~100-atom snake may take 30-90 s' (rationale: PITFALLS 2 measured
    13 atoms 0.28 s / 26 atoms 1.03 s hessian wall; N^3 extrapolation)."""

def save_setup(setup):   # -> text (json.dumps(sort_keys=True, indent=2)); validate first
def load_setup(text):    # -> dict or raises SetupError('schema_version 2 not supported')
def randomize_head(candidates, seed):   # -> chosen id via random.Random(seed).choice
    # NEVER the global random module (determinism + testability); Random(seed) is
    # reproducible on the same 3.6 build. candidates = validated molecule ids.
def new_setup():          # -> dict(DEFAULTS)  (copy — callers mutate freely)
```

**Phase-2 scope boundary (be precise):** schema exists + defaults + validate + save/load round-trip + seeded randomize, all unit-tested. **NOT in Phase 2:** any Qt wiring (Phase 3 setup tab), the 6-button row semantics (SETUP-07, Phase 8), educator file format polish/handling of corrupt user files UX (SETUP-08/Phase 8 — v1 `load_setup` raises; Phase 8 adds friendly handling). The win-cap atom-budget warning here is the pure half of SETUP-06/SPECTRA-06; the actual pre-xtb re-check lives in Phase 6's runner.

---

## 9. Proposed API — `serpentrum/cgo_build.py` (R8)

**Constants must be LOCAL literals** — verified from `pymol-src/modules/pymol/cgo.py` (whole file read; importing `pymol.cgo` would pull `from pymol import cmd` at its module level AND violate the purity gate):

| Constant | Value | Constant | Value | Constant | Value |
|---|---|---|---|---|---|
| `POINTS` | 0.0 | `STOP` | 0.0 | `SPHERE` | 7.0 |
| `LINES` | 1.0 | `NULL` | 1.0 | `CYLINDER` | 9.0 |
| `LINE_STRIP` | 3.0 | `BEGIN` | 2.0 | `LINEWIDTH` | 10.0 |
| `TRIANGLES` | 4.0 | `END` | 3.0 | `COLOR` | 6.0 |
| `TRIANGLE_STRIP` | 5.0 | `VERTEX` | 4.0 | `CONE` | 27.0 |

(cgo.py:21-65. **There is NO `VERSION` constant in `pymol/cgo.py`** — the research question's list included it in error; nothing to copy. If some day a CGO version header is needed, it does not come from this file.)

**Float-list layouts (verified from C source, not guessed):**
- `SPHERE`: opcode + 4 floats — `[x, y, z, radius]` (`CGO_SPHERE_SZ = 4`, CGO.h:96); needs a preceding `COLOR` triplet.
- `CYLINDER`: opcode + 13 floats — `[x1,y1,z1, x2,y2,z2, radius, r1,g1,b1, r2,g2,b2]` (`CGO_CYLINDER_SZ = 13`, CGO.h:100).
- `CONE`: opcode + **16** floats — `[x1,y1,z1, x2,y2,z2, r1, r2, cr1,cg1,cb1, cr2,cg2,cb2, cap1, cap2]` — **two radii** (base, tip) and **cap flags** (`CGO_CONE_SZ = 16`, CGO.h:143; write order verified CGO.cpp:916-943; caps read at CGO.cpp:5754-5756; `cCylCap`: None=0, Flat=1, Round=2 — Basis.h:41-46). Emit `cap=1` (Flat) for arrow tips.
- `LINES` block: `[BEGIN, LINES]` then per edge `[VERTEX, x,y,z, VERTEX, x,y,z]`, closed by `[END]`; `LINEWIDTH` precedes the block. Prior art for faces: `wizard/box.py:261-311` (TRIANGLE_STRIP + NORMAL + VERTEX quads) — box *edges* via LINES match STACK.md §3's boundary decision and need no normals.

```python
# serpentrum/cgo_build.py  (PURE — stdlib only; local float constants)

def box_cgo(min_corner, max_corner, color=(1.0, 0.4, 0.1), linewidth=2.0):
    """-> float list: [LINEWIDTH, w] + [BEGIN, LINES, COLOR, r,g,b] + 12 edges
    (8 corners, standard box edge pairs) + [END, STOP]. Pure geometry from the
    two corners; corners enumerated explicitly (no clever loops that reorder)."""

def mode_arrows(atoms, vecs, scale=1.0, color=(0.2, 0.6, 1.0),
                base_radius=0.06, length_a=1.2):
    """-> float list: per atom with a nonzero vector: CYLINDER shaft from p to
    p + v_hat*scale*length_a*0.7 (two colors = same), then CONE head from shaft
    end to p + v_hat*scale*length_a with (r_base=base_radius, r_tip=0.0, caps=1).
    CONE layout note: TWO radii + 6 color floats + 2 cap floats (§ above).
    Zero/near-zero vectors skipped (length < 1e-6). [COLOR, ...] header once."""

def spheres_cgo(points, radius, color):
    """-> float list for snake-head style spheres: per point [COLOR?, SPHERE, x,y,z,r]
    (COLOR once before the group is sufficient — verified convention in
    cgo.py's own RenderReader sphere handling)."""
```

**Unit tests without PyMOL (all pure list assertions):**
- `box_cgo`: starts with `[LINEWIDTH, 2.0]`; contains exactly one `BEGIN`,`LINES`,`END`,`STOP`; `VERTEX` count == 24 (12 edges × 2); every float is a float; corners match the 8 enumerations of (min,max).
- `mode_arrows`: per nonzero vector, exactly one CYLINDER (14 floats from opcode) + one CONE (17 floats from opcode); CONE's two radii slots hold (base_radius, 0.0); cap floats == 1.0, 1.0; total length == expected arithmetic.
- Round arithmetic: a unit-x vector with scale 1 → tip at (1.2, 0, 0) relative offsets.
- Cross-check: constants tuple equals the verified table above (guards against typo drift).

---

## 10. Test & Gate Conventions for New Code (R10)

Verified against Phase 1 code + summaries:

- **Discovery:** `python3.6 -m unittest discover -s tests -p "test_*.py" -v` — **never `-t .`** (fails on py3.6 non-package start dir; pinned in test_skeleton.py docstring and 01-01-SUMMARY.md).
- **Per-file preamble:** every test file repeats the sys.path self-insert (`sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))`) — `tests/` has **NO `__init__.py`** and must never get one (plugin-path safety, run_gates gate 1b).
- **Zero sys.modules stubs [INFRA-02]:** the ban is on stubbing pymol/Qt/numpy into `sys.modules`. `unittest.mock` **is available and acceptable** for callable seams — but the DI style above (`which_fn=shutil.which` parameter) is preferred over `mock.patch` where trivial. Fixture reads and tempfile writes need no mocks at all.
- **Purity:** `tools/check_purity.py` classifies every new `serpentrum/*.py` as **PURE automatically** (default-strict; classify() at check_purity.py:66-72). **No `GUI_MODULES`/`ENTRY` edits needed** — expect NONE for Phase 2. The `.exec_()` ban and banned-roots list (`pymol`, `pmg_tk`, `PyQt5`, `numpy` — check_purity.py:60) apply to function bodies too, so a "lazy numpy for convenience" in any pure module fails the gate (F22 makes this non-negotiable anyway).
- **Gates:** `python3.6 tests/run_gates.py` unchanged — gates 1 (syntax+safety), 2 (purity), 3 (scoped unittest) all auto-cover the new modules. Baseline confirmed green today (32 tests, all gates PASS). `--smoke`/`--xtb` legs unaffected by Phase 2 (no GUI, no new Windows contracts — xtbenv's contract is unit-tested pure; the Windows probe remains the Phase-6 runner's job).
- **AGENTS.md:** the gates/conventions section already describes default-PURE classification; new modules need **no AGENTS.md edits**. If the executor adds a genuinely new *convention* (e.g., fixture-path helper), document it in the plan summary, not AGENTS.md.
- **Fixture access from tests:** `FIXTURES = os.path.join(ROOT, '.planning', 'research', 'xtb-spike-fixtures')` where ROOT comes from the same self-insert path math. Fixtures are committed — reference in place, **do not copy** into tests/ (single source of truth; success criterion 2 names this directory explicitly).
- **py3.6 syntax discipline:** no dataclasses, no walrus, no f-string `=`; repo precedent uses `%`-formatting (AGENTS/STACK.md §Version Compatibility). `super()` zero-arg form; `collections.OrderedDict` unnecessary (3.6 dicts ordered, but don't rely on it for logic).

---

## 11. Pure Integration Test Design (R11)

One test module, `tests/test_integration_pure.py`, chaining all five data-producing modules in a single flow with **data flowing through**, not three parallel tests:

```
1. molecule_data.load_stacking(data/demos/stacking.json)
   -> entry.distance_a  (the distance comes FROM THE FILE — no constant in the test)
2. read dimer2.xyz (xyzio.read_xyz) -> fragments f1, f2 (split at index 13 —
   derived from manifest atom_count? No: dimer2 is a test artifact; split via
   len(read)==26 and assert 13/13 — documented as fixture knowledge)
3. stacking.ring_frame(f1, [0..5]) + stacking.place_pickup(..., entry.distance_a, 0.0)
   -> placed == f2 (max err < 1e-6)        [success criterion 1: math reproduces file]
4. xtbenv.evaluate_run(0, open('ohess.err').read(), ('g98.out','vibspectrum'),
                       ('g98.out','vibspectrum')) -> ok
   + the repro_oh case: same but present=() -> not ok        [criterion 3]
5. spectra.parse_g98(g98.out) -> n_atoms == len(placed)+len(f1) == 26
   (atom count flows from the stacking output through to the parser check)
   -> len(modes) == 3*26 - 6 == 72; index correspondence vs vibspectrum (+6)
6. xyzio.write_xyz on [f1 + placed] -> re-read -> 26 atoms, round-trip identical
```

**What makes it a real integration proof:** (a) the *distance* is read from the dataset file, so a schema/format regression breaks the chain; (b) the *placed atom count* from stacking becomes the expected `n_atoms` for the parser assertion, so the xyz/parse layers must agree; (c) the *xyzio round-trip* output feeds nothing but proves the handoff format the Phase-6 runner will write; (d) the *contract* evaluation consumes fixture bytes, tying xtbenv to the same run the parser's fixtures came from. Each stage consumes the previous stage's output — a break anywhere fails here even if unit tests pass.

---

## 12. Recommended Plan Breakdown (R12)

Four plans, two waves. All modules have crisp input→output contracts ⇒ **all TDD** (RED fixture/synthetic tests first, GREEN implementation). Executor estimates assume Phase-1 pace (avg 17 min/plan; parser plan is the heavy one).

| Plan | Contents | Tasks (2-3 each) | Files (disjoint) | Depends |
|------|----------|------------------|------------------|---------|
| **02-01 Spectra parser** (TDD, heaviest) | `spectra.py` full API | 1. RED: g98+vibspectrum fixture tests (happy paths, index correspondence, negatives, near-zero intensities) 2. GREEN: both parsers to fixture-exact behavior 3. broadening + loud-failure + synthetic remainder/CO₂ tests | `serpentrum/spectra.py`, `tests/test_spectra.py` | — |
| **02-02 xyzio + xtbenv** (TDD) | two small contract modules | 1. xyzio writer/reader + fixture round-trips + `bad.xyz` rejection 2. xtbenv success contract vs the four success `.err` + `bad.err` + repro_oh story + synthetic rc=128 3. xtbenv detection (DI which_fn) + argv/OHESS constant | `serpentrum/xyzio.py`, `serpentrum/xtbenv.py`, `tests/test_xyzio.py`, `tests/test_xtbenv.py` | — |
| **02-03 Data + stacking** (TDD) | schemas, loader, placement, clash gate | 1. JSON schemas + loader validation (synthetic valid/invalid tmpdirs) + DRAFT/APPROVED accessor 2. ring_frame + place_pickup with the dimer2 exact-reproduction test 3. check_clash (2.5 Å + box walls) tests | `serpentrum/molecule_data.py`, `serpentrum/stacking.py`, `serpentrum/data/demos/*.json`, `tests/test_molecule_data.py`, `tests/test_stacking.py` | — |
| **02-04 Engine + setup + integration** | state machine, schema logic, chain test | 1. engine step/direction/180°/collision/events (TDD) 2. pivot sweep + refusal pre-check + win/pause 3. setup_logic defaults/validate/save-load/randomize 4. `tests/test_integration_pure.py` chain | `serpentrum/game_engine.py`, `serpentrum/setup_logic.py`, `tests/test_game_engine.py`, `tests/test_setup_logic.py`, `tests/test_integration_pure.py` | 02-01..03 |

**Waves:** Wave A = 02-01 ∥ 02-02 ∥ 02-03 (disjoint files, parallelizable; if run concurrently, apply the AGENTS.md worktree protocol). Wave B = 02-04 (single plan — direct commit, no worktree needed).

**`cgo_build.py` placement:** small and independent — fold into 02-04 (its tests are trivial list assertions) or add to 02-02 if the executor has slack; either keeps files disjoint. Recommended: 02-04 task 3.5/own task (it also gives the engine plan a concrete bridge-facing artifact without touching pymol).

**Deferred out of Phase 2 (with reasoning):**
- **Turn-sweep animation polish** (smooth easing, partial-tick rendering) — pure math stays coarse (TURN_TICKS sampling); visual quality is Phase-5 gameplay + human-verify territory. Success criteria don't mention animation.
- **Real CO₂ `vibspectrum`/`g98.out` capture** — synthetic CO₂ fixture derived from `co2.log` eigvals is honest and labeled; a real re-capture needs the Windows xtb leg and belongs as an optional stretch task (or Phase-6 calibration byproduct), not a Phase-2 requirement.
- **Setup persistence edge cases** (corrupt user file UX, schema migration) — SETUP-08 ships in Phase 8; v1 `load_setup` raising loudly is correct for now.
- **Citation pinning + approval** — the human track (DATA-02) runs in parallel from Phase 2 onward; code needs only the DRAFT/APPROVED flag, which 02-03 delivers.
- **Engine speed tuning / pickup radius playtesting** — constants are module-level and documented; tuning happens in Phase 4/5 with the human in the loop.
- **`transform_selection` matrix convention for R/t** — stacking returns R,t; consuming them via cmd is Phase 5 (ARCHITECTURE §9 already flags the layout question).

---

## Open Questions (carry into planning/execution)

1. **g98 remainder-block grammar (N mod 3 ≠ 0)** — UNVERIFIED against real fixtures (the dimer has none; 72 = 24×3). Token-count-driven parsing handles it structurally; the synthetic test asserts our assumption. If Phase 6 ever captures a remainder-block g98.out, re-verify.
2. **repro_oh's exact invocation flags** — UNVERIFIED (settings block doesn't echo argv). Immaterial to the contract test (stderr + missing files are the facts), but if the human track re-runs fixtures, capture `--ohess` on CO₂ (option b in §1.3) at the same time.
3. **`transform_selection` matrix layout** (row/col-major, 4×4) for consuming stacking's R,t — ARCHITECTURE §9 LOW item; Phase 5 must read `editing.py:1946` before wiring.
4. **Exact engine tuning constants** (SPEED, BODY_COLLISION_RADIUS, PICKUP_RADIUS, box margin) — defensible bounds argued in §7 (radius < 3.4 stacking distance is the hard constraint); final feel = Phase 4/5 playtesting.
5. **vibspectrum intensity field overflow** (co2.log shows `******` in its *log* property printout) — the vibspectrum/g98 %f fields haven't been observed to overflow; if a future snake mode exceeds ~99999 km/mol, float() on `******` must raise SpectraParseError (add to loud-failure handling — cheap to include from day one).

## Sources

**Fixture probes (all 2026-09-06, this session — python3.6 one-liners against the committed files):**
- `.planning/research/xtb-spike-fixtures/` — g98.out (block stride 35 / columns / negatives / EOF termination), vibspectrum (82 CRLF lines / 78 rows / trivial grammar / −0.00), dimer2.xyz (f2 = f1 + (0,0,3.4), max err 0.0; min inter-fragment 3.4000 Å; min bond 0.9646 Å), phenol.xyz (13 atoms, element order), co2.xyz, dimer.xyz (CO₂-dimer-not-phenol discovery), bad.xyz/bad.log ([ERROR] line 97), bad.err + four success .err files (exact bytes), ohess.log (freq lines 494/637), repro_oh.log (NO Numerical Hessian / ends at xtbopt write / stderr normal termination), co2.log (line 240 linear; lines 455-460 eigvals+intensities incl. 0.00 and `******`), dimer2.log (eigvals ↔ vibspectrum ↔ g98 zero-mismatch correspondence), hessian (6084 = 78² values), xtbopt.xyz/xtbhess.xyz/charges/wbo/xtbtopo.mol/xtbopt.log (format reference).
- Correspondence probe: g98 72 freqs vs vibspectrum rows 7-78 → 0 mismatches (tolerance 1e-4); log eigvals (both sections, 78 each) → 0 mismatches.

**Code read (file:line verified today):**
- `pymol-src/modules/pymol/cgo.py:21-67` — all CGO constants (NO VERSION constant exists); `:79-156` (module imports `from pymol import cmd` at module level — why local constants are mandatory)
- `pymol-src/modules/pymol/wizard/box.py:255-311` — box CGO prior art (TRIANGLE_STRIP + NORMAL/VERTEX faces)
- `pymol-src/layer1/CGO.cpp:916-943` (CGOConev write order), `:5754-5756` (caps read); `pymol-src/layer1/CGO.h:96,100,143` (SPHERE_SZ 4, CYLINDER_SZ 13, CONE_SZ 16); `pymol-src/layer1/Basis.h:41-50` (cCylCap None/Flat/Round)
- `pymol-src/modules/pymol/importing.py:296-315` — load_cgo contract
- `tools/check_purity.py:53-72,135-138,156-170` — PURE default classification, banned roots, `.exec_()` gate
- `tests/run_gates.py:46-63,72-99,114-125,184-258` — gates 1/3/5, xtb probe contract, safety rules
- `tests/test_skeleton.py:1-19` — sys.path self-insert + discovery-pin conventions
- `.planning/phases/01-plugin-skeleton-purity-harness/01-01-SUMMARY.md` — test conventions, anchor, modeless record

**Project research (context, previously verified):**
- `.planning/research/ARCHITECTURE.md` F19-F23 (xtb flags, fixture practice, no-numpy F22), §2 component table, §5 build order, §7 Anti-Patterns 5-7, §9 open items
- `.planning/research/PITFALLS.md` 1 (`--ohess`), 2 (N³ timing table: 0.28 s @ 13 atoms / 1.03 s @ 26), 3 (cwd/stderr/exit-128 contract, `[RUN]`), 10 (3.4 Å clean-optimization evidence `[RUN]`, clash gate = game rule), 12 (trivial-mode counts 6 vs 5, negatives, zero-intensity, g98 vectors)
- `.planning/research/STACK.md` §3 (CGO entities), §5 (`--ohess` audit, detection order), §6 (broadening 10-20 cm⁻¹ typical), Version Compatibility (py3.6 syntax bans)
- `.planning/research/FEATURES.md` — 3.4 Å distance UNVERIFIED-until-pinned (Demo Sets table + known verification debt); Janiak 2000 DOI 10.1039/b003010o VERIFIED (Crossref/OpenAlex); STACK-02/03 semantics
- `.planning/REQUIREMENTS.md` GAME-05/08/10, STACK-01/02/05, SPECTRA-02/03/05/06, SETUP-05/06, INFRA-02; `.planning/ROADMAP.md` Phase 2 success criteria; `.planning/STATE.md` locked decisions

**Environment (probed today):** python3.6.9 — `collections.namedtuple` ✓, `typing.NamedTuple` class syntax ✓, `math` ✓, `shutil.which` ✓, `unittest.mock` ✓, `json`/`tempfile` ✓; baseline gates green (32 tests).

## RESEARCH COMPLETE
