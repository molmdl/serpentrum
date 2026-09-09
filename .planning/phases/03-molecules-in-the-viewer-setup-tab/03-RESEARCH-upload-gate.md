# Phase 3 (Upload-Validation-Gate + DATA half) — Research

**Researched:** 2026-09-10
**Domain:** Pure-Python SDF V2000 / mol2 parsing, ring-count gate (cyclomatic number),
explicit-H / formal-charge validation (Pitfall 11), demo Set A data flow, xtb path wiring
**Confidence:** HIGH for ring-count math + xtb detection + manifest schema (verified from
in-repo code/tests/research); MEDIUM for SDF V2000 format details (format is [TRAIN] but
charge-fidelity base is [SRC]-verified via PITFALLS.md 11); LOW for demo-file availability
(human-gated, network-rejected)

This research covers the **DATA / loader half** of Phase 3: the upload-validation gate
(rings / explicit-H / charge), the demo Set A data flow through `molecule_data`, and the
xtb path auto-detect wiring. The **Setup-tab UI half** is covered by the sibling research
`03-RESEARCH-setup-ui.md` (read FIRST; this doc builds on it and does not contradict it).

**Repo-only constraint:** all claims are verified from in-repo sources. chempy/mol.py and
chempy/mol2.py ARE in the repo (`pymol-src/modules/chempy/`) but per instruction I cite
PITFALLS.md 11's [SRC] claims as the verified base and do NOT read chempy itself. SDF V2000
format details beyond what PITFALLS.md verifies are marked [TRAIN].

---

## Summary

The upload-validation gate is a PURE-stdlib module that parses SDF V2000 (and mol2 with a
charge caveat), counts rings via the **cyclomatic number μ = E − V + C** (the circuit rank —
trivially computable from the bond graph, no SSSR algorithm needed), checks for explicit
hydrogens, and sums formal charges from SDF `M  CHG` records. All five Demo Set A molecules
pass the ≤3-ring gate with cyclomatic counts 1/2/3/3/2 (verified math below). The gate
produces a molecule record carrying `charge`, `ring_count`, `has_explicit_h`, and a
`has_stack_entry` flag keyed by set-id against the stacking dataset (uploaded molecules get
`set='__upload__'` → no interaction matches → skip-at-pickup per STACK-03). The xtb path
wiring is ALREADY BUILT: `xtbenv.detect_binary` probes `xtb.exe` then `xtb` (test-proven),
and `setup_logic._xtb_path_problems` is a local mirror of `xtbenv.validate_binary_path` that
Phase 3 should unify. The one hard blocker: **Demo Set A has no shipped SDF files or
manifest.json** (only DATA_SOURCES.md + stacking_pi_stack.json exist in `serpentrum/data/`);
since network access is rejected, the human must provide the 5 PubChem SDF files via a
`checkpoint:human-action`.

**Primary recommendation:** Create `serpentrum/molfile.py` (PURE — SDF/mol2 readers + gate,
parallel to `xyzio.py`'s line-numbered error style). Use cyclomatic number μ = E − V + C for
ring counting. Accept mol2 with charge=0 + warning (formal charges don't survive per
PITFALLS 11). Key uploaded molecules as `set='__upload__'` for the skip-policy. Unify
`setup_logic._xtb_path_problems` to call `xtbenv.validate_binary_path`. Ship a
`checkpoint:human-action` for the 5 demo SDF files + draft manifest.json.

---

## 1. Verified SDF / mol2 Parsing Facts (in-repo source pointers)

### 1.1 Charge fidelity — the PITFALLS.md 11 verified base (HIGH confidence)

PITFALLS.md Pitfall 11 (lines 267-285) verifies, with `[SRC]` pointers into the in-repo
PyMOL source tree:

| Format | Formal charges | Source pointer (via PITFALLS.md) |
|--------|---------------|----------------------------------|
| **SDF** | Formal charges **survive** via `M  CHG` records | `[SRC: chempy/mol.py:74-81]` |
| **mol2** | **Partial charges only** — formal charges do NOT survive | `[SRC: chempy/mol2.py:74]` |

PITFALLS.md 11 recommendation (line 278): **"Prefer SDF over mol2 for the demo library
(formal-charge fidelity + simpler parsing); document the choice in DATA_SOURCES.md."**

PITFALLS.md 11 also verifies (line 271): `cmd.h_add` (`[SRC: pymol/editing.py:1216]`) is
"geometric-rule-based and unreliable for arbitrary organics" — the policy is **do NOT
auto-add H** (reject or demand pre-protonated file). `[SRC: PITFALLS.md:270-271,275,278]`

### 1.2 Multi-record SDF — `$$$$` separator (HIGH confidence)

The sibling research (03-RESEARCH-setup-ui.md §2.1, line 79) establishes: **"One
multi-record SDF is the upload unit (SDF carries multiple `$$$$`-delimited records);
directory-upload is a Phase 8 enhancement."** This is the locked upload-unit decision.
`[SRC: 03-RESEARCH-setup-ui.md:79]`

### 1.3 SDF V2000 format details (MEDIUM confidence — [TRAIN] base, consistent with 1.1)

The V2000 format is a stable MDL standard (since 1995). The format details below are
[TRAIN] but are consistent with PITFALLS.md 11's [SRC]-verified `M  CHG` claim. The parser
MUST be tested against real fixture files (PITFALLS 1/12 fixtures-first rule) — see §8.

**[TRAIN] V2000 record structure (single record):**
```
Line 1:  molecule name (title) — free text
Line 2:  program/timestamp line — free text
Line 3:  comment — free text
Line 4:  counts line — "aaabbblllfffcccsssxxxrrrpppiiimmmvvvvvv"
         aaa = atom count (3 chars), bbb = bond count (3 chars), rest = metadata
         (version flag "V2000" at end of line)
Lines 5..(4+aaa):  atom block — one line per atom:
         "xxxxx.xxxxyyyyy.yyyyzzzzz.zzzz aaaddcccssshhhbbbvvvHHHrrriiimmmnnneee"
         x/y/z = float coords; aaa = element symbol (cols ~31-34, left-justified)
Lines (5+aaa)..(4+aaa+bbb):  bond block — one line per bond:
         "111222tttsssxxxrrrccc"
         111 = first atom (1-based), 222 = second atom (1-based), ttt = bond type
         (1=single, 2=double, 3=triple, 4=aromatic)
Properties block:  "M  CHGnnn aaa vvv aaa vvv ..." lines (formal charges)
         nnn = count of charge pairs; aaa = atom index (1-based); vvv = charge (signed int)
         Multiple M  CHG lines may appear; charges accumulate. Absent → total charge 0.
         Other M  lines (M  STY, M  RAD, etc.) may appear — parse M  CHG only.
"$$$$"  record separator — everything between two $$$$ is one record.
```

**[TRAIN] mitigation:** write the reader against committed test fixtures (hand-written
V2000 records — see §8) that exercise: single record, multi-record (`$$$$`), `M  CHG`
(positive/negative/multiple), explicit H present/absent, 1/2/3 rings. The exact column
widths should be verified against a real PubChem SDF once the human provides one
(checkpoint:human-action). A whitespace-split fallback for the counts line and atom rows
handles real-world spacing variation; the element symbol is the critical field for the
gate (H detection) and is reliably parseable by whitespace split of the atom row.

### 1.4 mol2 format policy (HIGH confidence — based on 1.1)

mol2 carries **partial charges only** (PITFALLS 11, `[SRC: chempy/mol2.py:74]`). There is
no formal-charge field in standard mol2. **Policy for the gate:**
- **Accept mol2 uploads** (don't reject — users may have mol2 files).
- **Assume charge = 0** (no formal charge information available).
- **Emit a warning**: "mol2 does not preserve formal charges; charge assumed 0. Use SDF
  for ionic species." (Surface via the status QLabel — see sibling research §4.2.)
- The ≤3-ring gate and explicit-H gate still apply to mol2 (bond block is parseable).

This is consistent with PITFALLS 11's "prefer SDF" recommendation: SDF is the
first-class format (demo library ships as SDF); mol2 is accepted-but-warned for uploads.

`[SRC: PITFALLS.md:271,278]`

### 1.5 The established error contract — xyzio.py line-numbered XyzError (HIGH confidence)

`serpentrum/xyzio.py` is the precedent for format readers in this repo. Its contract
(`xyzio.py:63-78`):
- `XyzError(ValueError)` — message names the **1-based line number** and quotes the first
  ~60 chars of the offending line: `"line 3: unknown element symbol 'Xx' (Xx 0.0 0.0 0.0)"`
- `_line_error(lineno, text, message)` helper builds the canonical error.
- `_SNIPPET_MAX = 60` — how much of the offending line to quote.
- Element symbols validated case-sensitively against `ELEMENT_SYMBOLS` (all 118 IUPAC,
  `xyzio.py:34-53`).

**The SDF/mol2 reader MUST follow this same error style** — a `MolFileError(ValueError)`
with line-number + snippet, parallel to `XyzError`. The element-symbol set can be reused
from `xyzio.ELEMENT_SYMBOLS` (import is intra-package → purity-exempt per
`check_purity.py:75-78`). `[SRC: serpentrum/xyzio.py:34-78]`

---

## 2. Ring-Count Definition + Per-Demo-Molecule Cyclomatic Math

### 2.1 Definition: cyclomatic number (circuit rank) μ = E − V + C (HIGH confidence)

**"≤3 rings" means: the cyclomatic number (circuit rank) of the molecular bond graph is ≤3.**

The cyclomatic number μ = E − V + C counts the number of **independent cycles** (the
dimension of the cycle space). It equals the size of the SSSR (Smallest Set of Smallest
Rings) — so "count of SSSR rings" = μ. There is NO need to enumerate SSSR (which requires a
ring-perception algorithm); just count edges, vertices, and connected components.

**Why cyclomatic number (not SSSR, not ring-membership):**

| Definition | What it counts | Computation | Correct for fused rings? | Multi-component safe? |
|---|---|---|---|---|
| **Cyclomatic μ = E−V+C** | Independent cycles (= SSSR size) | Trivial: count E, V, C | Yes (naphthalene=2) | Yes (via C term) |
| SSSR enumeration | A specific set of rings | Complex algorithm (DFS/BFS) | Yes | Yes | 
| Ring-membership | Atoms in any ring | Atoms, not rings | N/A (wrong unit) | N/A |

SSSR COUNT = cyclomatic number for all normal organic molecules (they differ only in
pathological bridged systems, which the demo set doesn't contain). So **μ is the right,
simple, stdlib-computable definition.** `[TRAIN]` graph theory (standard, stable since
~1860; the formula μ = E−V+C is the circuit rank).

**Pure-stdlib computation:**
1. Build adjacency from the bond block (0-based atom indices).
2. Count V = number of atoms (from atom block), E = number of bonds (from bond block).
3. Count C = connected components via BFS/DFS or union-find on the adjacency (O(V+E)).
4. μ = E − V + C.

No numpy, no RDKit, no external library — just sets and a BFS. This is consistent with the
pure-layer discipline (`game_engine.py`, `stacking.py` are stdlib-only; `check_purity.py`
auto-classifies new modules PURE). `[SRC: serpentrum/game_engine.py:49 (import math only);
serpentrum/stacking.py:36 (import math only); tools/check_purity.py:60 (BANNED_ROOTS)]`

### 2.2 Cyclomatic math for the 5 Demo Set A molecules (HIGH confidence — verified arithmetic)

All 5 molecules are aromatics with C-C bond graphs. H atoms are pendant (leaves) and do not
affect cycle count (each H adds 1 vertex + 1 edge → net zero to μ). The math uses the
heavy-atom (carbon) skeleton; including H gives the same μ.

| Molecule | Formula | V (C atoms) | E (C-C bonds) | C (components) | μ = E−V+C | ≤3? |
|----------|---------|-------------|---------------|----------------|-----------|-----|
| Benzene | C6H6 | 6 | 6 (ring) | 1 | 6−6+1 = **1** | ✓ |
| Naphthalene | C10H8 | 10 | 11 (2 fused rings, 1 shared edge: 6+6−1) | 1 | 11−10+1 = **2** | ✓ |
| Anthracene | C14H10 | 14 | 16 (3 linear-fused: 6+5+5) | 1 | 16−14+1 = **3** | ✓ |
| Phenanthrene | C14H10 | 14 | 16 (3 angular-fused: 6+5+5, same bond count as anthracene) | 1 | 16−14+1 = **3** | ✓ |
| Biphenyl | C12H10 | 12 | 13 (2 rings + 1 inter-ring bond: 6+6+1) | 1 | 13−12+1 = **2** | ✓ |

**All five pass the ≤3-ring gate.** ✓

**Bond-count derivation for fused systems:** each 6-ring contributes 6 edges; each fusion
(shared edge) subtracts 1. Naphthalene: 6+6−1 = 11. Anthracene/phenanthrene: 6+6+6−1−1 = 16
(two shared edges, one between each adjacent ring pair). Biphenyl: 6+6+1 = 13 (no shared
edge; the inter-ring single bond connects the two rings into one component).

**Multi-component graph question (biphenyl):** Biphenyl's two rings are connected by a
single C-C bond, making the graph ONE connected component (C=1). μ = 13−12+1 = 2. If the two
rings were truly disconnected (no bond), C=2, E=12, V=12, μ = 12−12+2 = 2 — **the same
answer.** The C term correctly accounts for components: a disconnected graph with K rings
across its components has μ = (sum of per-component cycles). **The cyclomatic number
handles multi-component graphs correctly by construction.** `[TRAIN]` graph theory.

**Cross-check with FEATURES.md:** FEATURES.md line 187 states "Ring counts: 1/2/3/3(±2) —
within the ≤3-ring constraint ✓" for the 5 demo molecules. The cyclomatic counts (1/2/3/3/2)
match this (the "(±2)" annotation refers to biphenyl's 2). `[SRC: FEATURES.md:187]`

---

## 3. Gate Rule Spec (Rings / Explicit-H / Charge)

### 3.1 The three gate checks (HIGH confidence — based on PITFALLS 11 + DATA-03)

The gate runs at **load time** (before molecules enter the scene). It applies to BOTH demo
set molecules AND uploads. A molecule that fails ANY check is **rejected with a clear
reason** (SC1: "uploads exceeding 3 rings are rejected with a clear reason").

| Check | Rule | Rejection reason | Source |
|-------|------|-----------------|--------|
| **Rings** | cyclomatic μ ≤ 3 | "<name>: has <μ> rings (limit is 3)" | DATA-03, PROJECT.md scope |
| **Explicit H** | organic molecule (contains C/N/O) with zero H → reject | "<name>: no explicit hydrogens found — provide a pre-protonated file (auto-H is not used per policy)" | PITFALLS 11a |
| **Charge** | declared total charge from SDF `M  CHG` sum (absent → 0); mol2 → 0 + warning | Not a rejection — charge is INFORMATION carried on the record for Phase 5/6 | PITFALLS 11b |

### 3.2 Explicit-H rule — precise definition (HIGH confidence)

**PITFALLS 11a (line 275):** "every demo/user molecule must (a) contain explicit H (reject
or demand a pre-protonated file — do NOT auto-add)."

**Rule:** After parsing the atom block, count H atoms (element symbol 'H' in
`ELEMENT_SYMBOLS`). If the molecule contains C, N, or O (organic) AND has zero H atoms →
**reject.** Rationale: an organic molecule with C/N/O and zero H is almost certainly a
skeletal structure missing explicit hydrogens — the common failure mode PITFALLS 11 warns
about (xtb runs on wrong electron count, silently).

**Warn-vs-reject boundary:**
- Organic (has C/N/O) + zero H → **REJECT** (almost certainly missing-H; the demo set and
  educational use case expect pre-protonated files).
- Organic + has H → **ACCEPT** (passes the gate).
- Inorganic (no C/N/O, e.g. a metal complex) + zero H → **WARN but accept** (legitimate
  inorganic without H; rare in the educational scope but not a missing-H indicator). The
  warning: "<name>: no hydrogens — verify this is correct for an inorganic molecule."
- Any molecule + has H → **ACCEPT.**

**Demo Set A confirmation:** all 5 demo molecules are PubChem 3D conformers with explicit H
(DATA_SOURCES.md §1: benzene C6H6 = 12 atoms = 6C+6H; all formulas include H). All pass the
explicit-H check. `[SRC: DATA_SOURCES.md:28-38; PITFALLS.md:270-275]`

### 3.3 Charge handling — where charge lives for Phase 5/6 (HIGH confidence)

**PITFALLS 11b (lines 271, 277):** "xtb needs the total molecular charge (`--chrg`); default
0 is wrong for ionic groups. Compute snake total charge as the sum of loaded molecule
charges; pass `--chrg <sum>` only when non-zero."

**SDF charge:** sum all `M  CHG` atom-charge values across all `M  CHG` lines in the record.
Absent `M  CHG` → total charge = 0. This is the **declared total formal charge** (an int).

**mol2 charge:** formal charges do NOT survive (PITFALLS 11, `[SRC: chempy/mol2.py:74]`).
Assume 0. Warn.

**Where charge lives:** on the molecule record (see §4) as `charge: int`. Phase 5 aggregates
snake total charge = sum of stacked molecule charges. Phase 6 passes `--chrg <sum>` to xtb
when non-zero. Phase 6 also does the post-hoc electron-count sanity check (PITFALLS 11b,
line 276: assert xtb log electron count matches hand-computed valence count).

`[SRC: PITFALLS.md:271,276-277]`

### 3.4 Gate is load-time only; skip-policy is pickup-time (HIGH confidence)

**Two distinct gates at two distinct phases:**
- **Load-time gate (Phase 3, this research):** rings ≤3, explicit-H, charge parsing. A
  molecule failing this is REJECTED — it never enters the scene. This is DATA-03's
  "size-gated (≤3 rings)" + Pitfall 11's H/charge hygiene.
- **Pickup-time skip (Phase 5, STACK-03):** a molecule WITHOUT a stacking dataset entry is
  loaded into the scene (visible as a pickup) but SKIPPED at pickup — not stacked, with the
  info box stating why. This is DATA-03's "uploaded molecules without stacking dataset
  entries follow the skip policy (STACK-03)."

Phase 3 sets the `has_stack_entry` flag on the record; Phase 5 consumes it. Phase 3 does
NOT implement the skip logic — only the flag. `[SRC: REQUIREMENTS.md:42 (STACK-03),59
(DATA-03); ROADMAP.md:89 (SC1),123 (Phase 5 SC5)]`

---

## 4. Molecule Record + Skip-Policy Keying Design

### 4.1 The molecule record (HIGH confidence — coordinated with game_engine + molecule_data)

The gate produces a **molecule record** (a dict) for each accepted molecule. The record
bridges the parsed SDF data to the downstream consumers (viewer load, head-molecule
dropdown, engine, xtb charge aggregation). Design constrained by:
- `game_engine.py` segment/pickup records: `{'molecule_id', 'centroid', 'atoms',
  'atoms_n'}` (atoms = `[(sym, x, y, z)]` tuples).
- `molecule_data.py` manifest molecule: `{'id', 'name', 'file', 'source_db', 'source_id',
  'atom_count', 'charge', 'ring_count', 'ring_atoms', 'set'}`.
- `interaction_for(molecule, data)` needs `molecule['set']` to match
  `interaction['applies_to']['sets']`.

**Proposed gate molecule record:**
```python
{
    'id': str,               # demo: manifest id (e.g. 'benzene');
                             # upload: derived from SDF title or 'upload_0', 'upload_1', ...
    'name': str,             # demo: manifest name; upload: SDF title line or id
    'file': str,             # demo: manifest file ref (e.g. 'benzene.sdf');
                             # upload: the uploaded file path
    'record_index': int,     # 0-based index within a multi-record SDF (0 for single/demo)
    'elements': [str],       # element symbols per atom (for Phase 6 electron-count check)
    'atom_count': int,       # len(elements)
    'charge': int,           # declared total formal charge (M CHG sum for SDF; 0 for mol2)
    'ring_count': int,       # cyclomatic number (computed from bond graph)
    'has_explicit_h': bool,  # True if any 'H' in elements
    'has_stack_entry': bool, # interaction_for(record, stacking_data) is not None
    'set': str,              # demo: 'set_a' (from manifest); upload: '__upload__'
    'source': str,           # 'demo' or 'upload'
}
```

**Not on the record (by design):**
- `coords` — the bridge extracts geometry via `cmd.load` + `get_model` (ARCHITECTURE.md §4
  data flow step 2), NOT from the gate's parse. The gate parses coords only to count atoms
  and validate; the bridge re-reads from the loaded PyMOL object (single source of truth).
- `bonds` — the gate parses bonds only for ring counting; the bond list is not needed
  downstream (the engine works on centroids + atom tuples, not bond graphs).
- `ring_atoms` — needed by `stacking.ring_frame()` for demo molecules (provided by the
  MANIFEST, not the gate). Uploaded molecules are skip-at-pickup (no stacking placement),
  so they don't need `ring_atoms`. The gate does NOT produce `ring_atoms`.

`[SRC: serpentrum/game_engine.py:168-169 (segment record shape); serpentrum/molecule_data.py:137-181
(manifest molecule validation); serpentrum/molecule_data.py:346-362 (interaction_for);
ARCHITECTURE.md:237-241 (data flow: cmd.load → get_model → engine)]`

### 4.2 Skip-policy keying — set-id based (HIGH confidence)

**Question:** how does an uploaded molecule get its `has_stack_entry` status?

**Answer:** `interaction_for(molecule, stacking_data)` matches `molecule['set']` against
`interaction['applies_to']['sets']` (`molecule_data.py:346-362`). It does NOT match by
molecule id, name, or formula — **the keying is by SET ID.**

- **Demo molecules:** `set = 'set_a'` (from the manifest). The stacking dataset
  (`stacking_pi_stack.json`) has `applies_to: {sets: ['set_a']}`. So
  `interaction_for({'set': 'set_a'}, stacking_data)` returns the `pi_stack_pd` entry →
  `has_stack_entry = True`. ✓
- **Uploaded molecules:** assigned `set = '__upload__'` (a synthetic set id). No
  interaction in the stacking dataset has `'__upload__'` in its `applies_to.sets`, so
  `interaction_for({'set': '__upload__'}, stacking_data)` returns `None` →
  `has_stack_entry = False` → **skip-at-pickup per STACK-03.** ✓

This is the minimal, correct keying: it reuses the existing `interaction_for` mechanism
without inventing a new lookup. The `__upload__` sentinel is explicit and debuggable. All
uploaded molecules in v1 are skip-at-pickup (no stacking dataset entry exists for user
uploads — the dataset only covers `set_a`).

**Why not match by formula/name?** The stacking dataset keys on SET, not on individual
molecules. An uploaded benzene (formula C6H6) would match the manifest's benzene by
formula, but the stacking interaction applies to ALL molecules in `set_a`, not to a
specific molecule. Matching uploads to set_a by formula would INCORRECTLY give uploads a
stacking entry they shouldn't have (the interaction is for the curated demo set, not
arbitrary user files). The `__upload__` sentinel correctly isolates uploads.

`[SRC: serpentrum/molecule_data.py:346-362 (interaction_for); serpentrum/data/stacking_pi_stack.json:13
(applies_to: {sets: ['set_a']}); REQUIREMENTS.md:42 (STACK-03),59 (DATA-03)]`

### 4.3 Demo vs upload record construction paths

| Path | Source | set | has_stack_entry | ring_atoms | ring_count |
|------|--------|-----|-----------------|------------|------------|
| Demo | manifest.json (molecule_data.load_manifest) | 'set_a' (from manifest) | True (interaction_for matches) | from manifest (for stacking) | manifest-declared; gate VERIFIES |
| Upload | SDF/mol2 file (molfile reader) | '__upload__' | False (no interaction matches) | not needed (skip-at-pickup) | gate COMPUTES (cyclomatic) |

For demo molecules, the gate should **verify** the manifest's declared `ring_count` by
computing the cyclomatic number from the SDF bond graph and asserting they match. For
uploads, the gate **computes** `ring_count` (no declared value to verify against).

---

## 5. Manifest Schema Requirements (HIGH confidence)

### 5.1 What manifest.json MUST contain (from molecule_data._validate_molecule)

`molecule_data.load_manifest(path)` validates this exact schema (verified by reading
`molecule_data.py:137-217` and `test_molecule_data.py:36-58`):

```json
{
  "schema_version": 1,
  "sets": [
    {
      "id": "set_a",
      "name": "Aromatic pi-stack",
      "molecules": [
        {
          "id": "benzene",
          "name": "Benzene",
          "file": "benzene.sdf",
          "source_db": "PubChem",
          "source_id": "CID 241",
          "atom_count": 12,
          "charge": 0,
          "ring_count": 1,
          "ring_atoms": [0, 1, 2, 3, 4, 5],
          "set": "set_a"
        }
      ]
    }
  ]
}
```

**Validation rules (from `_validate_molecule`, `molecule_data.py:137-181`):**
- `schema_version`: int == 1 (bools rejected — py3.6 trap).
- `sets`: non-empty list of set objects.
- Set: `id` (non-empty str), `name` (non-empty str), `molecules` (non-empty list).
- Molecule: `id` (non-empty str, **unique across the whole manifest**), `name` (non-empty
  str), `file` (non-empty str, **must exist in the manifest's directory**), `source_db`
  (non-empty str), `source_id` (non-empty str), `atom_count` (int > 0, bools rejected),
  `charge` (int, bools rejected), `ring_count` (int >= 1, bools rejected), `ring_atoms`
  (list of >= 3 **unique** int indices in `[0, atom_count)`, bools rejected), `set` (**must
  equal the parent set id**).

**Critical:** `file` references are resolved against `os.path.dirname(path)` — the
manifest's OWN directory (`molecule_data.py:178-181`). So SDF files must be in the same
directory as manifest.json.

`[SRC: serpentrum/molecule_data.py:137-217; tests/test_molecule_data.py:36-58 (VALID_MANIFEST)]`

### 5.2 The stacking dataset file — path/naming discrepancy (MEDIUM confidence — coordination item)

**Discrepancy:** The pure-core research (02-RESEARCH-pure-core.md:364-365) and
`molecule_data.py` docstring (lines 8-10) expect the stacking file at
`serpentrum/data/demos/stacking.json`. The **actual shipped file** is
`serpentrum/data/stacking_pi_stack.json` (different name, NO `demos/` subdirectory).

The loaders take a PATH argument (they don't hardcode the location), so this is NOT a code
bug — but Phase 3's `load_demo_set` caller must pass the correct path. Options:
1. Rename `stacking_pi_stack.json` → `demos/stacking.json` (matches research/docstring).
2. Keep `stacking_pi_stack.json` at `data/` and update the docstring.
3. Pass whatever path is correct at runtime (loaders are path-agnostic).

**Recommendation:** Option 2 or 3 — the `stacking_pi_stack.json` name is more descriptive
(suggests future per-mode files), and the loaders are path-agnostic. Phase 3's caller
resolves the path via `os.path.join(os.path.dirname(serpentrum.__file__), 'data',
'stacking_pi_stack.json')`. Update the `molecule_data.py` docstring to match. The manifest
(if shipped) would go at `serpentrum/data/manifest.json` (or `demos/manifest.json` — human
decision, but keep it next to the stacking file for consistency).

`[SRC: serpentrum/data/ (directory listing: DATA_SOURCES.md + stacking_pi_stack.json only);
molecule_data.py:8-10 (docstring expects demos/); 02-RESEARCH-pure-core.md:364-365]`

### 5.3 What the stacking dataset currently provides (HIGH confidence)

`serpentrum/data/stacking_pi_stack.json` (22 lines, APPROVED status) contains ONE
interaction:
- `id: 'pi_stack_pd'`, `mode: 'pi_stack'`, `distance_a: 3.383`, `lateral_offset_a: 1.231`
- `applies_to: {sets: ['set_a']}` — applies to ALL set_a molecules
- `status: 'APPROVED'` (human-approved per the DATA-02 track)
- `citation: 'janiak2000'` (DOI 10.1039/b003010o, approved: true)

This means ALL demo molecules (set_a) share ONE stacking interaction. Uploaded molecules
(set='__upload__') have NO interaction → skip-at-pickup. The `distance_a` and
`lateral_offset_a` are consumed by `stacking.place_pickup` (Phase 5).

`[SRC: serpentrum/data/stacking_pi_stack.json (full file); serpentrum/molecule_data.py:333-362
(shipped_interactions, interaction_for)]`

---

## 6. Demo Set A Data Flow — Shipping Options + Human-Approval Items

### 6.1 Current state: NO structure files, NO manifest (HIGH confidence)

`serpentrum/data/` contains ONLY:
- `DATA_SOURCES.md` (133 lines — provenance + license, DRAFT status)
- `stacking_pi_stack.json` (22 lines — the stacking interaction, APPROVED)

There is **NO manifest.json, NO SDF files, NO `demos/` subdirectory.** DATA_SOURCES.md §1
(lines 23-26) explicitly states: "The PubChem 3D SDF files themselves are NOT part of this
plan — they ship in a later phase (Phase 8, the molecule-geometry/data-prep track)."

The 5 demo CIDs (benzene 241, naphthalene 931, anthracene 8418, phenanthrene 995, biphenyl
7095) are VERIFIED public-domain PubChem records (DATA_SOURCES.md §1; verification record
in 02-RESEARCH-demo-data.md §2.4), but the SDF FILES are not in the repo.

`[SRC: serpentrum/data/ (directory listing); DATA_SOURCES.md:23-26; 02-RESEARCH-demo-data.md:84-94]`

### 6.2 The three options (per the objective's framing)

| Option | Description | Network needed? | SC1 satisfied? | AGENTS.md compliant? |
|--------|-------------|-----------------|----------------|---------------------|
| (a) Agent fetches 5 SDFs from PUG REST | Phase 3 execution downloads from `pubchem.ncbi.nlm.nih.gov/rest/pug/...` | YES — **REJECTED by user** | Yes | **NO** — network access rejected; no-fabrication |
| (b) Human provides SDF files manually | Human places 5 SDFs + manifest.json before/during Phase 3 (`checkpoint:human-action`) | NO | Yes (once files arrive) | YES — human action, no agent fabrication |
| (c) Upload-only Phase 3 | Skip demo-set load; exercise only the upload path | NO | **NO** — violates "choose Demo Set A" (SC1) | YES but scope-incomplete |

### 6.3 Recommendation: Option (b) — human provides SDF files via checkpoint:human-action (HIGH confidence)

**Rationale:**
- Option (a) is **rejected** by the user's no-network constraint. The agent cannot fetch
  files. Even if the plan includes a fetch step, execution would fail without network
  access. Network feasibility is an [ASSUMPTION] to record, not to test.
- Option (c) **violates SC1** ("User can choose Demo Set A from the dropdown... and its
  molecules load into the scene"). The roadmap explicitly lists SC1 as a Phase 3 success
  criterion.
- Option (b) is the only path that satisfies SC1 without network access: the human
  provides the 5 verified PubChem SDF files (CIDs 241/931/8418/995/7095, already verified
  in DATA_SOURCES.md §1) and a draft manifest.json. The plan includes a
  `checkpoint:human-action` task.

**Under AGENTS.md's no-fabrication rule:** the agent does NOT create SDF files (that would
be fabricating molecular geometry data). The human provides real PubChem SDFs. The agent
CAN create manifest.json from the verified metadata in DATA_SOURCES.md (atom counts,
charges, ring counts, ring_atoms indices — these are derivable from the known structures,
not fabricated). BUT `load_manifest` requires `file` references to EXIST on disk
(`molecule_data.py:178-181`), so the manifest can't be loaded until the SDFs arrive.

**Plan structure recommendation:**
1. Build `molfile.py` (SDF reader + gate) — PURE, unit-tested with **hand-written test
   fixtures** (see §8). No external data needed.
2. Build the demo-set load path (`load_demo_set(set_id)`) — calls `molecule_data.load_manifest`
   + `molecule_data.load_stacking` + `molfile.read_sdf` + gate. Unit-tested with synthetic
   tmpdir manifests + fixture SDFs (the test_molecule_data.py precedent: synthetic tmpdir
   documents, `test_molecule_data.py:99-117`).
3. `checkpoint:human-action`: human places the 5 PubChem SDF files + manifest.json into
   `serpentrum/data/`. Until this checkpoint is met, the demo-set load can only be tested
   with fixtures, not with the real PubChem SDFs. SC1's "Demo Set A loads" can only be
   human-verified after the checkpoint.
4. The upload path (`load_upload(path)`) is fully testable WITHOUT the checkpoint — it
   reads any user SDF/mol2 through the gate.

**What the human provides (the checkpoint deliverable):**
- 5 PubChem 3D SDF files: `benzene.sdf` (CID 241), `naphthalene.sdf` (CID 931),
  `anthracene.sdf` (CID 8418), `phenanthrene.sdf` (CID 995), `biphenyl.sdf` (CID 7095).
  Downloaded from `https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{CID}/SDF?record_type=3d`
  (URL in DATA_SOURCES.md:16). These are public-domain US-government data.
- (Optionally) a manifest.json — OR the agent creates it from DATA_SOURCES.md metadata
  once the SDFs are present (the agent can compute ring_atoms indices from the SDF bond
  graph after parsing).

`[SRC: DATA_SOURCES.md:12-38 (CIDs + formulas + atom counts); AGENTS.md (no-fabrication rule);
02-RESEARCH-demo-data.md:84-94 (verification record); ROADMAP.md:89 (SC1)]`

---

## 7. xtb Detection Wiring Contract (SETUP-05) (HIGH confidence)

### 7.1 detect_binary ALREADY handles both 'xtb' and 'xtb.exe' (test-proven)

`xtbenv.detect_binary(configured_path=None, which_fn=shutil.which)` (`xtbenv.py:141-167`)
probes in this order:
1. `configured_path` (if given): `validate_binary_path`; valid → return immediately; invalid
   → fall through.
2. `which_fn('xtb.exe')` — Windows conda env first.
3. `which_fn('xtb')` — Linux fallback.
4. `None` when nothing resolves.

**Test-proven** (`test_xtbenv.py:207-251`, `TestDetectBinary`):
- `test_valid_configured_path_wins_without_probing`: configured valid → returned, no probe.
- `test_invalid_configured_path_falls_through_to_which`: configured missing/dir → falls
  through to `which_fn`.
- `test_windows_conda_env_probed_before_linux`: `xtb.exe` probed BEFORE `xtb`
  (`fake.queries == ['xtb.exe', 'xtb']`).
- `test_nothing_found_returns_none`: returns `None` when nothing found.

**Runtime behavior:** The plugin runs inside Windows PyMOL → `shutil.which` runs under
Windows → `shutil.which('xtb.exe')` finds `C:\xtb-6.7.1\bin\xtb.exe` IF it's on PATH.
**[ASSUMPTION]** (untested from WSL — can't invoke cmd.exe per constraint): whether xtb.exe
is on the Windows PATH is environment-dependent. The tests use dependency-injected
`which_fn` fakes, so they DON'T test the real `shutil.which` on Windows. If xtb is NOT on
PATH, auto-detect returns None → the user must set a manual path in the Setup tab.

`test_wsl_winxtb.sh` invokes xtb as `${CWD}/xtb-6.7.1/bin/xtb.exe` (a RELATIVE path from
the repo root), NOT via PATH lookup — confirming xtb is at `xtb-6.7.1/bin/xtb.exe` relative
to the repo, but NOT necessarily on PATH. **Mitigation:** the Setup tab's status label
should show the detected path (or "xtb not found — set a manual path or add xtb to PATH")
after `detect_binary` runs. Phase 3 doesn't launch xtb (Phase 6 does), so Phase 3 only
needs the detection + status display.

`[SRC: serpentrum/xtbenv.py:141-167; tests/test_xtbenv.py:207-251; test_wsl_winxtb.sh:4]`

### 7.2 Two validators for one setting — ownership split

There are TWO validators with IDENTICAL rules:

| Validator | Location | Purpose | When it runs |
|-----------|----------|---------|-------------|
| `setup_logic._xtb_path_problems(path)` | `setup_logic.py:100-127` | Static validation of the setup dict (is the path well-formed?) | `validate(setup)` — on Apply, on field change |
| `xtbenv.validate_binary_path(path)` | `xtbenv.py:113-138` | Canonical path validation (same rules) | Called by `detect_binary` at runtime |

Both check: (a) empty/None/non-str → 'xtb path is empty'; (b) missing → 'does not exist';
(c) directory → 'not a file'; (d) quotes → 'quote character(s)'.

**Why two?** `setup_logic.py:113-115` docstring: "Kept local (not imported from
serpentrum.xtbenv) because xtbenv is a PARALLEL wave-1 plan and may not exist in this
worktree; keep in sync with serpentrum/xtbenv.py — a later wave may unify the two."

Phase 2 is COMPLETE — both modules now exist in the same package. **Phase 3 should unify:**
`setup_logic._xtb_path_problems` should call `xtbenv.validate_binary_path` (import is
intra-package → purity-exempt). The `02-02-SUMMARY.md:109` note confirms: "Note for
SETUP-05: `setup_logic.validate` should call `xtbenv.validate_binary_path` for `xtb_path`
problems." This eliminates the "keep in sync" drift risk.

**Ownership split (the single wiring contract):**
- `setup_logic.validate(setup)` → **owns "is the setup dict valid?"** — checks `xtb_path`
  via `xtbenv.validate_binary_path` (unified). Static, no xtb install needed. Returns
  `(errors, warnings)`.
- `xtbenv.detect_binary(configured_path, which_fn)` → **owns "what exe do I actually
  run?"** — validates the configured path (same rules), falls through to auto-detect if
  invalid/None. Dynamic, probes the filesystem. Returns a path string or None.
- **These are DIFFERENT concerns** (validate checks well-formedness; detect resolves the
  actual binary). Both are needed; they share `validate_binary_path` to avoid rule drift.

`[SRC: serpentrum/setup_logic.py:100-127; serpentrum/xtbenv.py:113-167;
02-02-SUMMARY.md:109]`

### 7.3 The single SETUP-05 wiring contract for Phase 3

1. **Setup tab UI** (sibling research §2.1, line 82): `QLineEdit` + `QCheckBox`
   ("auto-detect") + `QPushButton` ("Browse…").
   - Checkbox checked → field disabled, `setup['xtb_path'] = None` (auto-detect).
   - Checkbox unchecked → field enabled; Browse opens `QFileDialog.getOpenFileName` for the
     exe. Manual path overrides detection.
2. **`setup_logic.validate(setup)`** (unified): if `xtb_path` is not None, calls
   `xtbenv.validate_binary_path(xtb_path)` → problems appended to errors. If None
   (auto-detect), no validation (the path will be resolved at runtime).
3. **Bridge/Apply** (sibling research §6.3): when materializing the setup, optionally call
   `xtbenv.detect_binary(configured_path=setup['xtb_path'])` to resolve the actual exe path
   and show it in the status label. Phase 3 does NOT launch xtb (Phase 6); it only needs
   detection + status display.
4. **Not found**: `detect_binary` returns None → status label shows "xtb not found — set a
   manual path or add xtb to PATH." This is advisory in Phase 3 (no xtb launch); it becomes
   a blocking error in Phase 6.

`[SRC: 03-RESEARCH-setup-ui.md:82 (widget design); serpentrum/setup_logic.py:181-183
(validate xtb_path); serpentrum/xtbenv.py:141-167 (detect_binary)]`

---

## 8. Module Decomposition Recommendation (MEDIUM confidence — design inference)

### 8.1 All new gate/parsing code is PURE (auto-classified by check_purity.py)

`tools/check_purity.py:66-72` classifies any `.py` under `serpentrum/` that is NOT
`__init__.py` (ENTRY) and NOT in `GUI_MODULES` as PURE — banning pymol/pmg_tk/PyQt5/numpy
anywhere. New parsing/gate modules are automatically PURE. No purity-checker change needed
for the DATA half (unlike the UI half, which needs the BRIDGE class per sibling research §5).

`[SRC: tools/check_purity.py:55,60,66-72]`

### 8.2 Recommendation: new `serpentrum/molfile.py` (parallel to xyzio.py)

**Create `serpentrum/molfile.py`** (PURE — stdlib only) containing:

```
serpentrum/molfile.py
├── MolFileError(ValueError)     # line-numbered error, parallel to XyzError
├── read_sdf_text(text) -> [MolRecord]
│     # Parse multi-record SDF V2000 (split on $$$$).
│     # Per record: title, atom block (elements + coords), bond block (bonds),
│     # M  CHG records (formal charges). Returns list of parsed records.
├── read_sdf(path) -> [MolRecord]
│     # File wrapper for read_sdf_text.
├── read_mol2_text(text) -> [MolRecord]
│     # Parse mol2 (@<TRIPOS>ATOM, @<TRIPOS>BOND). charge=0 + warning flag
│     # (formal charges don't survive per PITFALLS 11).
├── read_mol2(path) -> [MolRecord]
├── count_rings(bonds, atom_count) -> int
│     # Cyclomatic number μ = E − V + C. Build adjacency, count components via BFS.
│     # bonds = [(i, j), ...] (0-based). atom_count = V. E = len(bonds).
├── sum_formal_charges(m_chg_records) -> int
│     # Sum of M  CHG atom-charge values. Absent → 0.
├── gate_molecule(record) -> (ok: bool, reason: str or None)
│     # The 3 checks: rings ≤ 3, explicit-H (organic + zero H → reject),
│     # charge is information (not a rejection).
├── gate_set(records) -> (accepted: [MolRecord], rejected: [(record, reason)])
│     # Apply gate_molecule to a list. Returns accepted + per-molecule rejection reasons.
└── MolRecord (dict or namedtuple)
      # {id, name, file, record_index, elements, atom_count, charge,
      #  ring_count, has_explicit_h, has_stack_entry, set, source}
```

**Why a new module (not extend molecule_data or xyzio):**
- `molecule_data.py` is a JSON loader for the manifest + stacking dataset. Extending it
  with SDF/mol2 binary-format parsing would mix concerns (JSON validation vs molecular
  format parsing) and bloat the module.
- `xyzio.py` is the .xyz reader/writer. SDF/mol2 are different formats with different
  structure (atom blocks, bond blocks, property records). A separate `molfile.py` is
  cleaner than overloading xyzio.
- The gate (rings/H/charge) is tightly coupled to the parsing (it needs the parsed bond
  graph + element list). Keeping parse + gate in one module is cohesive.

**The bridge (`pymol_bridge.py`, per sibling research §5.2) calls molfile:**
```python
# In pymol_bridge.load_upload(path):
records, parse_errors = molfile.read_sdf(path)  # or read_mol2
accepted, rejected = molfile.gate_set(records)
# For each accepted record: set has_stack_entry via interaction_for,
#   cmd.load(path, name), cmd.create copy into srp_* namespace.
# For each rejected: collect (name, reason) for the QMessageBox.
```

`[SRC: serpentrum/xyzio.py (precedent for format readers); serpentrum/molecule_data.py
(JSON loader, separate concern); tools/check_purity.py:66-72 (PURE auto-classification);
03-RESEARCH-setup-ui.md:177 (bridge surface)]`

### 8.3 Fixtures-first testing (PITFALLS 1/12) — test_molecule_data.py precedent

PITFALLS 1/12 (lines 300, 357): "write the parser to match reality, not documentation"
and "Loading arbitrary user SDF/mol2 without checks → parser exceptions crash the dialog."
The fixtures-first rule: tests against fixture FILES, not synthetic strings, where format
risk exists.

**test_molecule_data.py precedent** (`test_molecule_data.py:91-117`): uses synthetic tmpdir
JSON documents (built as Python dicts, written to tmpdir via `_write`). This is acceptable
for JSON (simple, schema defined in-repo). For SDF/mol2, the format is external and complex
— **fixture FILES are more important.**

**Recommendation for molfile.py tests:**
- Commit **hand-written V2000 SDF test fixtures** under `tests/fixtures/` (NOT under
  `serpentrum/data/` — that's for shipped data). These are TEST DATA (code), not chemistry
  claims. Minimal valid V2000 records exercising:
  - Single-record SDF (methane CH4 — 1 C, 4 H, 0 rings, 0 charge).
  - Multi-record SDF (benzene + naphthalene in one file, `$$$$` separated).
  - `M  CHG` records (e.g. acetate CH3COO⁻ — charge -1 on one O).
  - Missing-H case (benzene without H — skeletal, should be REJECTED by the gate).
  - 3-ring case (anthracene — should PASS; a 4-ring case like pyrene should be REJECTED).
- The fixtures are hand-written to match the V2000 spec ([TRAIN] format knowledge — but
  the structures are well-known: methane, benzene, naphthalene, anthracene are
  textbook molecules, not fabricated chemistry).
- Once the human provides real PubChem SDFs (§6.3 checkpoint), ADD a regression test that
  parses the real benzene.sdf and verifies the gate accepts it (the real-file integration
  test that the fixtures-first rule ultimately wants).
- mol2 tests: hand-write a minimal mol2 fixture (e.g. benzene.mol2) and verify charge=0 +
  warning.

**Why hand-written fixtures are acceptable for SDF (unlike xtb output):** PITFALLS 1/12's
fixtures-first rule is critical for xtb output (the format is complex, under-documented,
and the parser must match real bytes). For SDF V2000, the format is a stable, well-specified
standard (MDL, since 1995). Hand-written fixtures that match the spec are sufficient for
unit testing; the real-file regression test (post-checkpoint) closes the gap.

`[SRC: PITFALLS.md:300 (fixtures-first),357 (SDF check rule); tests/test_molecule_data.py:91-117
(tmpdir precedent); PITFALLS.md:278 (prefer SDF — simpler parsing)]`

### 8.4 Rejected decomposition alternatives

| Alternative | Why rejected |
|---|---|
| Extend `molecule_data.py` with SDF parsing | Mixes JSON validation with binary format parsing; bloats the module; `molecule_data` is about the shipped DATA FILES, not uploaded user files |
| Extend `xyzio.py` with SDF parsing | xyzio is the `.xyz` specialist; SDF/mol2 have different structure (bond blocks, property records); overloading xyzio muddies its single-format focus |
| Put the gate in `pymol_bridge.py` | The gate is PURE logic (no cmd calls); the bridge is the cmd-seam (BRIDGE class). Purity separation: gate in PURE module, bridge calls it. |
| Put the gate in `setup_logic.py` | setup_logic owns the setup DICT (defaults/validation/save/load); the gate owns molecule FILE parsing. Different data, different concerns. |
| Separate `upload_gate.py` for the gate | The gate is thin (3 checks on parsed data) and tightly coupled to the parser. One module (`molfile.py`) is simpler. Split only if the gate grows complex (e.g. skip-policy coordination needs molecule_data). |

---

## 9. Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Ring counting | SSSR enumeration algorithm | Cyclomatic number μ = E−V+C | SSSR COUNT = cyclomatic number for all normal organics; no ring-perception algorithm needed — just count E, V, C |
| SDF parsing | Custom format from scratch | V2000 spec + xyzio.py error style | The format is standard; follow xyzio's line-numbered error contract; test against fixtures |
| Charge from SDF | Parse atom-by-atom valence | Sum `M  CHG` records | PITFALLS 11 [SRC]-verified: M CHG carries formal charges; sum them → total charge |
| Connected components | Custom graph library | BFS/DFS on adjacency (stdlib sets) | O(V+E) with basic Python; no numpy needed |
| xtb path validation | New validator | `xtbenv.validate_binary_path` (unify) | Already exists; `setup_logic._xtb_path_problems` is a stale mirror — unify in Phase 3 |
| xtb binary detection | New probe logic | `xtbenv.detect_binary` (already built) | Test-proven probe order (xtb.exe → xtb); dependency-injected which_fn for WSL testing |

---

## 10. Common Pitfalls (Phase 3 specific)

### Pitfall A: Trusting mol2 formal charges
**What goes wrong:** mol2 files have a charge column, but it's PARTIAL charges (floats),
not formal charges. Using them as formal charges → wrong `--chrg` for xtb.
**Why:** PITFALLS 11 [SRC: chempy/mol2.py:74] — mol2 carries partial charges only.
**How to avoid:** Gate assumes charge=0 for mol2 + warning. SDF `M  CHG` is the only
source of formal charges.
`[SRC: PITFALLS.md:271]`

### Pitfall B: Auto-adding H with cmd.h_add
**What goes wrong:** A user uploads a skeletal SDF (no H). Auto-adding H via `cmd.h_add`
produces wrong structures that look fine → wrong electron count → garbage spectra.
**Why:** PITFALLS 11 — `cmd.h_add` is geometric-rule-based, unreliable for arbitrary
organics.
**How to avoid:** The gate REJECTS organic molecules with zero H. Never call `cmd.h_add`.
Demand a pre-protonated file.
`[SRC: PITFALLS.md:270-271,275]`

### Pitfall C: Ring-count definition mismatch
**What goes wrong:** Using "number of 6-membered rings" or "ring-membership count" instead
of cyclomatic number → naphthalene counts as 1 (one fused system) instead of 2, or biphenyl
counts wrong.
**Why:** Different definitions give different counts for fused/disconnected systems.
**How to avoid:** Use cyclomatic number μ = E−V+C. Verified: 1/2/3/3/2 for the 5 demo
molecules. SSSR count = cyclomatic number for normal organics.
`[TRAIN]` graph theory (stable).

### Pitfall D: Manifest file-existence check blocks testing
**What goes wrong:** `molecule_data.load_manifest` requires `file` references to exist on
disk (`molecule_data.py:178-181`). A draft manifest.json can't be loaded until the SDFs
arrive.
**Why:** The loader validates file existence as part of structural validation.
**How to avoid:** Unit-test the demo-set load path with synthetic tmpdir manifests + fixture
SDFs (the test_molecule_data.py precedent). The real PubChem SDFs arrive via the
checkpoint:human-action.

### Pitfall E: Two xtb-path validators drifting
**What goes wrong:** `setup_logic._xtb_path_problems` and `xtbenv.validate_binary_path`
have identical rules but are separate copies. If one is updated and the other isn't, they
drift → inconsistent validation.
**Why:** setup_logic kept a local copy during Phase 2 parallel development.
**How to avoid:** Phase 3 unifies: `setup_logic._xtb_path_problems` calls
`xtbenv.validate_binary_path`. Per `02-02-SUMMARY.md:109`.
`[SRC: setup_logic.py:113-115; 02-02-SUMMARY.md:109]`

---

## 11. State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|---|---|---|---|
| `setup_logic._xtb_path_problems` (local mirror) | Should call `xtbenv.validate_binary_path` | Phase 3 (unify now that both exist) | Eliminates drift risk; 02-02-SUMMARY.md:109 note |
| `serpentrum/data/demos/stacking.json` (expected path) | `serpentrum/data/stacking_pi_stack.json` (actual) | Phase 2 data-prep | Path discrepancy; loaders are path-agnostic; Phase 3 caller resolves correct path |
| Demo SDFs ship in Phase 8 | Phase 3 needs them for SC1 | ROADMAP Phase 3 vs DATA_SOURCES.md §1 | Human-action checkpoint required; upload path works without them |

---

## 12. Open Questions

1. **SDF V2000 exact column widths** — [TRAIN] knowledge; the format is fixed-width but
   real-world files (PubChem) may vary slightly. **Mitigation:** write the parser with
   whitespace-split fallback for counts line + atom rows; the element symbol (critical for
   H detection) is reliably parseable. Verify against a real PubChem SDF once the human
   provides one (checkpoint:human-action). **Confidence: MEDIUM.**

2. **xtb.exe on Windows PATH** — [ASSUMPTION] untested from WSL. `test_xtbenv.py` uses
   injected `which_fn` fakes, not real `shutil.which`. If xtb is NOT on PATH,
   auto-detect returns None. **Mitigation:** Setup tab shows detected path / "not found"
   status; user can set a manual path. **Confidence: MEDIUM.**

3. **Demo Set A data availability timing** — the 5 SDF files + manifest.json don't exist
   yet. The human must provide them before SC1 ("Demo Set A loads") can be verified.
   **Recommendation:** `checkpoint:human-action` in the plan; upload path is built and
   tested independently. **Confidence: LOW** (human-gated).

4. **manifest.json vs ring_atoms indices** — the manifest requires `ring_atoms` (indices of
   ONE planar ring, for `stacking.ring_frame`). For demo molecules, these must be correct
   (e.g. benzene's 6 ring carbons). The agent can compute them from the SDF bond graph
   (find a 6-cycle in the carbon skeleton) OR the human provides them in the manifest.
   **Recommendation:** the agent computes ring_atoms from the parsed SDF (a simple cycle
   search on the carbon subgraph) and writes them into the manifest; the human verifies.
   **Confidence: MEDIUM.**

5. **Data file path/naming** — should the stacking file be renamed to match the research
   docstring (`demos/stacking.json`), or should the docstring be updated to match the actual
   file (`stacking_pi_stack.json`)? **Recommendation:** keep the actual name; update the
   docstring; Phase 3 caller resolves the path. **Confidence: MEDIUM.**

---

## 13. Sources

### Primary (HIGH confidence — in-repo code/tests)
- `serpentrum/xtbenv.py:113-167` — `validate_binary_path`, `detect_binary` (probe order)
- `serpentrum/setup_logic.py:48-58,100-127,130-206` — DEFAULTS, `_xtb_path_problems`, `validate`
- `serpentrum/molecule_data.py:137-217,333-362` — `_validate_molecule`, `load_manifest`, `interaction_for`
- `serpentrum/xyzio.py:34-78` — `ELEMENT_SYMBOLS`, `XyzError`, `_line_error` (error contract precedent)
- `serpentrum/game_engine.py:49,168-169` — pure-stdlib discipline, segment record shape
- `serpentrum/stacking.py:36` — pure-stdlib discipline (import math only)
- `tools/check_purity.py:55,60,66-72` — GUI_MODULES, BANNED_ROOTS, classify (PURE auto-classification)
- `tests/test_xtbenv.py:156-251` — `TestValidateBinaryPath`, `TestDetectBinary` (probe order proven)
- `tests/test_molecule_data.py:36-58,91-117` — VALID_MANIFEST schema, tmpdir fixture pattern
- `serpentrum/data/stacking_pi_stack.json` — actual shipped stacking dataset (APPROVED, set_a)
- `serpentrum/data/DATA_SOURCES.md:12-38` — 5 demo CIDs, formulas, atom counts, license
- `test_wsl_winxtb.sh:4` — xtb invoked as relative path (not PATH)

### Research docs (HIGH confidence — [SRC]-verified pointers)
- `.planning/research/PITFALLS.md` Pitfall 11 (lines 267-285) — SDF M CHG formal charges
  `[SRC: chempy/mol.py:74-81]`, mol2 partial charges only `[SRC: chempy/mol2.py:74]`,
  cmd.h_add unreliable `[SRC: pymol/editing.py:1216]`, prefer SDF, do NOT auto-add H
- `.planning/research/PITFALLS.md` Pitfalls 1/12 (lines 300,357) — fixtures-first testing rule
- `.planning/research/FEATURES.md:187` — Demo Set A ring counts "1/2/3/3(±2) — within ≤3-ring constraint ✓"
- `.planning/research/ARCHITECTURE.md:237-241` — data flow: cmd.load → get_model → engine
- `.planning/research/STACK.md:84` — xtb.exe/xtb detection probe order (AGENTS.md rule)
- `.planning/phases/03-molecules-in-the-viewer-setup-tab/03-RESEARCH-setup-ui.md:79,82` —
  upload unit (multi-record SDF), xtb widget design
- `.planning/phases/02-pure-core-game-chemistry-logic/02-RESEARCH-pure-core.md:364-415` —
  manifest schema, data file paths, validation rules
- `.planning/phases/02-pure-core-game-chemistry-logic/02-RESEARCH-demo-data.md:84-94` —
  PubChem CID verification record
- `.planning/phases/02-pure-core-game-chemistry-logic/02-02-SUMMARY.md:109` — unify xtb validators note

### Requirements / roadmap
- `.planning/REQUIREMENTS.md:18 (SETUP-05),42 (STACK-03),59 (DATA-03)`
- `.planning/ROADMAP.md:85-96 (Phase 3 goal + SC1-SC5)`
- `.planning/STATE.md:47` — refuse-and-skip fallback (STACK-03)

### [TRAIN] (marked inline)
- SDF V2000 format column layout (stable MDL standard since 1995; consistent with PITFALLS 11 [SRC])
- Cyclomatic number formula μ = E−V+C (standard graph theory, stable since ~1860)

---

## RESEARCH COMPLETE

**Phase:** 3 — Molecules in the Viewer & Setup Tab (Upload-Validation-Gate + DATA half)
**Confidence:** HIGH (ring-count math, xtb detection, manifest schema, skip-policy keying —
all verified from in-repo code/tests); MEDIUM (SDF V2000 format details — [TRAIN] base
consistent with [SRC]-verified charge claims); LOW (demo-file availability — human-gated)

### Key Findings

- **Ring-count definition: cyclomatic number μ = E − V + C** (the circuit rank). This
  equals the SSSR count for all normal organic molecules, is trivially computable from the
  bond graph (count E, V, C — no ring-perception algorithm), handles multi-component graphs
  via the C term, and is pure-stdlib. All 5 demo molecules pass: **benzene=1, naphthalene=2,
  anthracene=3, phenanthrene=3, biphenyl=2** (all ≤3). Biphenyl's two rings are connected
  by a single bond (C=1, μ=2); even if disconnected, the formula gives the same answer.
- **SDF charge fidelity is [SRC]-verified** (PITFALLS 11): formal charges survive via
  `M  CHG` records; mol2 carries partial charges only → assume charge=0 + warning. The gate
  sums `M  CHG` for SDF; mol2 gets 0. `cmd.h_add` is banned (do NOT auto-add H); the gate
  REJECTS organic molecules with zero explicit H.
- **Skip-policy keying is set-id based:** `interaction_for(molecule, data)` matches
  `molecule['set']` against `interaction['applies_to']['sets']`. Uploaded molecules get
  `set='__upload__'` → no interaction matches → `has_stack_entry=False` → skip-at-pickup
  per STACK-03. Demo molecules get `set='set_a'` → matches `pi_stack_pd` →
  `has_stack_entry=True`.
- **xtb detection is ALREADY BUILT and test-proven:** `xtbenv.detect_binary` probes
  `xtb.exe` then `xtb` (test_xtbenv.py TestDetectBinary). Returns None when not found.
  `setup_logic._xtb_path_problems` is a stale mirror of `xtbenv.validate_binary_path` —
  Phase 3 should UNIFY (per 02-02-SUMMARY.md:109). The two validators own different
  concerns (static validation vs runtime resolution) but share the same rules.
- **Demo Set A has NO shipped SDF files or manifest.json** — only DATA_SOURCES.md +
  stacking_pi_stack.json exist in `serpentrum/data/`. Network access is rejected, so the
  human must provide the 5 PubChem SDFs via a `checkpoint:human-action`. The upload path is
  fully buildable/testable without the checkpoint.

### Ring-Count Recommendation + Demo Counts

**Use the cyclomatic number μ = E − V + C** (circuit rank). Demo molecule counts:

| Molecule | V | E | C | μ | ≤3? |
|----------|---|---|---|---|-----|
| Benzene | 6 | 6 | 1 | 1 | ✓ |
| Naphthalene | 10 | 11 | 1 | 2 | ✓ |
| Anthracene | 14 | 16 | 1 | 3 | ✓ |
| Phenanthrene | 14 | 16 | 1 | 3 | ✓ |
| Biphenyl | 12 | 13 | 1 | 2 | ✓ |

### Demo-File Shipping Recommendation

**Option (b): human provides SDF files via `checkpoint:human-action`.** The agent cannot
fetch (network rejected) and cannot fabricate (AGENTS.md no-fabrication rule). The plan
includes a checkpoint where the human places 5 PubChem 3D SDF files (CIDs 241/931/8418/
995/7095, verified public-domain per DATA_SOURCES.md §1) + a draft manifest.json into
`serpentrum/data/`. The upload path is built and tested independently (no checkpoint
needed). The molfile.py parser is tested with hand-written V2000 fixtures (test data, not
chemistry claims). SC1's "Demo Set A loads" can only be human-verified after the checkpoint.

### Human-Decision Items

1. **Provide the 5 PubChem SDF files** (CIDs 241/931/8418/995/7095) for the
   `checkpoint:human-action`. Download from the PUG REST URL in DATA_SOURCES.md §1. These
   are public-domain US-government data.
2. **Approve manifest.json creation** — the agent creates manifest.json from DATA_SOURCES.md
   metadata + computed ring_atoms indices (from the SDF bond graph); the human verifies.
   Alternatively the human provides the complete manifest.json.
3. **Confirm the data file path/naming** — keep `stacking_pi_stack.json` at `data/` (and
   update the molecule_data.py docstring) OR rename to `demos/stacking.json` (matching the
   research). Loaders are path-agnostic; this is a naming convention decision.
4. **Confirm the `__upload__` sentinel** for uploaded molecules' set-id (vs. a different
   keying approach). The sentinel reuses `interaction_for` cleanly; alternatives (formula
   matching) are more complex and could give uploads incorrect stacking entries.
5. **Confirm the explicit-H rejection rule** — organic (C/N/O) + zero H → reject. This is
  strict (rejects e.g. C60 fullerene, which has zero H legitimately) but catches the common
  missing-H failure. Acceptable for the educational scope (demo set is all pre-protonated
  aromatics).

### File Created

`.planning/phases/03-molecules-in-the-viewer-setup-tab/03-RESEARCH-upload-gate.md`

### Confidence Assessment

| Area | Level | Reason |
|------|-------|--------|
| Ring-count definition + demo math | HIGH | Cyclomatic number is standard graph theory; arithmetic verified by hand; matches FEATURES.md:187 |
| SDF/mol2 charge fidelity | HIGH | PITFALLS 11 [SRC: chempy/mol.py:74-81, mol2.py:74] — verified base |
| SDF V2000 format details | MEDIUM | [TRAIN] format knowledge; consistent with [SRC]-verified M CHG claim; test against fixtures |
| Skip-policy keying | HIGH | interaction_for mechanism verified from molecule_data.py:346-362 + stacking_pi_stack.json |
| Manifest schema | HIGH | Verified from molecule_data.py:137-217 + test_molecule_data.py:36-58 |
| xtb detection wiring | HIGH | xtbenv.py:141-167 + test_xtbenv.py:207-251 (test-proven probe order) |
| Demo-file availability | LOW | No SDF files shipped; human-gated; network rejected |
| Module decomposition | MEDIUM | Design inference from existing boundaries (xyzio precedent, molecule_data scope, purity auto-classification) |

**Valid until:** 2026-10-10 (stable domain; SDF V2000 format is stable since 1995; re-verify
only if the human provides SDFs that reveal format variations).

---

*Upload-validation-gate + DATA research for: serpentrum Phase 3 — Molecules in the Viewer & Setup Tab*
*Researched: 2026-09-10*
