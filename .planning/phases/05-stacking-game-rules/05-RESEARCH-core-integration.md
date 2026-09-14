# Phase 5: Stacking & Game Rules Complete — Core-Integration Research

**Researched:** 2026-09-15
**Domain:** pure core (stacking.py / game_engine.py / molecule_data.py / setloader.py / molfile.py) + dataset integration contracts for the GUI and bridge layers
**Confidence:** HIGH (all claims probe-verified with python3.6 read-only scripts against the real shipped data; baseline gates green: 451 tests, 3/3 gates)

## Summary

The pure core is much further along than the roadmap implies: `stacking.py` (ring frames, rigid-body placement, clash gate), `game_engine.py` (movement, collisions/wins, rigid-pivot sweeps, capture/attach/reject seam), and `molecule_data.py`/`setloader.py` (validated dataset access, record building, `__upload__` skip keying) are all DONE and unit-pinned. Phase 5 is primarily (a) a ring-extraction shim, (b) wiring (records + stacking dataset into the game tab), (c) placement-time policy decisions (normal sign, lateral direction, spawn positions, growth end), and (d) completion handoff. Almost everything the planner needs is callable as-is.

**The single biggest trap is real but measurable:** manifest `ring_atoms` are the FULL 2-core in sorted index order, NOT ring-walk order. Passing them straight to `ring_frame` fails even for flat benzene (spurious "non-planar ring 1.133 A" because Newell's method on a sorted-order star polygon yields a garbage normal). Phase 5 MUST extract ONE canonical 6-cycle in ring order per molecule. Probe-verified canonical cycles exist for all 5 demo molecules (see ring_extraction_spec).

**Second trap (new, probe-discovered):** the shipped biphenyl conformer has its two rings at **90.00°** (measured; the "~44°" note in planning context is wrong for this file). At the dataset geometry (3.383/1.231), EVERY biphenyl-involved pairwise stack clashes (0.69–2.15 Å < the 2.5 Å gate). All 10 fused-aromatic pairs are clean (≥3.386 Å). Biphenyl is effectively unstackable as shipped — every biphenyl pickup will exercise the STACK-03/05 refuse path. Flagged as an open question (data is human-gated by DATA-02).

**Third gap (engine semantics):** 'won' fires in the SAME tick as the cap-reaching 'stacked', BEFORE the controller runs the clash gate. Rejecting that capture rolls counters back but leaves `finished/result='won'` — a desync Phase 5 must resolve (engine extension or accepted-edge decision).

**Primary recommendation:** reuse everything in the pure core; add exactly three small pure pieces — a canonical-ring extractor (lives in `molfile.py`, carried on records as `stack_ring`), a pickup spawn/orientation helper module, and a placement controller seam (pure function assembling frame args) — and wire `setloader.default_stacking_path()` + records into `gui_game.begin_game`. Decide the five open policy questions at plan time (growth end, win-vs-clash desync, spawn policy, edge-on azimuth/z-depth, biphenyl).

## Standard Stack

All stdlib, python3.6 — **no new dependencies**. The pure core is the standard stack:

| Module | Provides | Status |
|--------|----------|--------|
| `serpentrum/stacking.py` | `ring_frame`, `place_pickup`, `check_clash`, `CLASH_THRESHOLD_A=2.5`, `PLANARITY_TOL_A=0.15` | complete, call as-is |
| `serpentrum/game_engine.py` | `GameEngine` full rules + sweeps + capture seams | complete; ONE semantics gap (win-vs-clash) |
| `serpentrum/molecule_data.py` | `load_manifest`, `load_stacking`, `shipped_interactions`, `interaction_for`, `DataError` | complete, call as-is |
| `serpentrum/setloader.py` | `load_demo_set`, `load_upload`, `default_stacking_path`, record schema | needs `stack_ring` carry-through (small) |
| `serpentrum/molfile.py` | `read_sdf/read_mol2`, `find_ring_atoms` (2-core), `gate_set` | needs canonical 6-ring extractor (small, ~30 lines) |
| `serpentrum/setup_logic.py` | `DEFAULTS` (win_cap_molecules=10, atom_budget=100, presets, speed 3.0) | complete, read for cap source |
| `serpentrum/hud_logic.py` | elapsed/remaining formatting | extend for info-box text composition (PURE seam) |

## current_api_surface

### stacking.py (call as-is; do not modify)

| Callable | Signature | Returns | Raises / edge |
|----------|-----------|---------|---------------|
| `ring_frame` | `(atoms: seq[(x,y,z)], ring_indices: seq[int])` | `(centroid, normal_unit, ref_unit)` — 3-tuples | `ValueError` on: <3 atoms; degenerate Newell normal (<1e-8); max plane deviation > 0.15 Å; degenerate ref axis. **`ring_indices` MUST be in ring-walk order**: reversal flips the normal (probe: exact flip, 1e-16); rotating the cycle keeps the normal (1e-16) but changes `ref` by up to 0.687 (probe) — determinism requires canonical rotation |
| `place_pickup` | `(pickup_atoms, pickup_ring_indices, tail_centroid, tail_normal, tail_ref, distance_a, lateral_offset_a, lateral_along_ref=True)` | `(placed_atoms[(x,y,z)...], R (3x3 row-major tuple), t)` with `placed = R.p + t` | exact: probe shows R=identity / target hit to 3.3e-16 for aligned same-molecule frames. Normal sign ("above/below") is the caller's sign choice on `tail_normal`; lateral direction is `lateral_along_ref` (True → along tail ref, False → along cross(normal,ref)); R,t intended for `cmd.transform_selection` (matrix layout OPEN — ARCHITECTURE §9, verify `editing.py:1946` in Phase 5; fallback `cmd.rotate`+`cmd.translate`) |
| `check_clash` | `(placed_atoms, existing_atoms, box_min, box_max, threshold_a=2.5)` | `None` if clear, else first-violation dict `{'kind': 'wall'|'atom', 'pair': (i,j), 'distance': d}` | wall leg first (inclusive bounds legal), then atom pairs (i,j ascending, strict < threshold). box args are **3-tuples** (the engine's 2D box must be extended with z bounds) |

**Pinned invariants (test_stacking_math.py, test_integration_pure_core.py):** dimer2 fixture exactly reproducible (max error <1e-9, pure z-translation); planarity tolerance 0.15 Å (bump 0.5 Å on r=1.4 hexagon rejects at 0.248); dataset file drives Stage-3b placement (composed centroid = sqrt(d²+l²) reproduces inter-fragment stack); clash threshold module constant, +distance-ahead both ways rationale in docstring.

### game_engine.py (call as-is except the one noted gap)

`GameEngine(head=(0.,0.), heading='right', segments=None, box_min=None, box_max=None, pickups=None, cap=None, atom_budget=None)` — 2D floats, Å.

- **State:** `head (x,y)`; `heading` unit vector (never a name); `segments` (index 0 = oldest, last = newest; each `{'molecule_id', 'centroid': (x,y), 'atoms': [(sym,x,y,z)...], 'atoms_n'}` + **unknown extra keys carried through** copies AND through sweep re-rotation — a `stack_ring`/record reference attached at seed time survives); `pickups` seeds the same record shape ('atoms' REQUIRED, swept pickup leg consumes them); `live_pickup_ids`; `cap`, `atom_budget`; counters `molecules_stacked`, `atoms_total` (captured atoms only — **head atoms NOT included**), `pickups_remaining`; `finished`, `result` ('crashed'|'won'); `_refusal_counts`; property `molecules_remaining = cap - molecules_stacked`.
- **`step(dt)` event order (LOCKED, do not change):** paused/finished → `[]`; sweep in progress → `_advance_sweep` only (`('turning', tick/total)`, NO 'moved', NO collision checks, NO captures — safety was pre-checked at open); else: pending application (perpendicular → `start_sweep`; refused → `('turn_refused', reason)` + fall through to forward motion) → `('moved', (x,y))` → boundary (inclusive at margin walls, `BOUNDARY_MARGIN_A=1.0`) → `('crashed','boundary')` → body (head-centroid vs polyline edges `i in range(0, n-1-SEGMENT_SKIP_RECENT[2])`, strict < `2.0²`) → `('crashed','body')` → capture (first live pickup within `PICKUP_RADIUS_A=3.0` INCLUSIVE, at most ONE per tick, list order) → `('stacked', pickup_record)` → `('budget_warning', atoms_total)` (once) → `('won',)`. Crash stops all later processing; crash/win set `finished`, clear pending.
- **Sweep (GAME-10):** `start_sweep(direction) -> (opened, events)`; refusal reasons 'boundary'|'body'|'pickup' with ZERO state mutation; 7-sample pre-check (`k=0..6`, 15°/tick) at open; per-tick rotation is ABSOLUTE from the start pose (no float drift); atoms rotate x/y about head, **z and sym preserved exactly** (stacking geometry frozen); head is the invariant pivot (excluded from the pickup leg); buffer while sweeping is newest-wins vs sweep TARGET; sweep-level 180 enforcement. **Intermediate sweep poses are NOT collision-checked per tick** — the caller must NOT re-check; it must re-render the whole chain from `engine.segments` truth on every `('turning',)` event.
- **`attach_segment(molecule_id, centroid, atoms)`** — counter-NEUTRAL (capture already counted); appends at the "nearest head" end. Call ONLY after `place_pickup`+`check_clash` succeed. `atoms` must be `(sym, x, y, z)` 4-tuples.
- **`reject_pickup(pickup_id, reason='clash') -> ('refused', pickup_id, reason)`** — rolls counters back, re-arms the pickup, tracks per-pickup refusal counts; safe-guarded against double rollback. **Does NOT touch `finished`/`result`** — see the win-desync gap.
- `request_direction`, `pause`, `resume`, `reset` — complete (GAME-07/08).

**Constants (pinned by tests, do not change):** `SPEED_A_PER_S=3.0`, `TURN_DEGREES=90.0`, `TURN_TICKS=6`, `BODY_COLLISION_RADIUS_A=2.0` (MUST stay < stacking distance), `SEGMENT_SKIP_RECENT=2`, `PICKUP_RADIUS_A=3.0`, `BOUNDARY_MARGIN_A=1.0`, `SWEEP_PICKUP_CLEARANCE_A=2.5`.

### molecule_data.py (call as-is)

- `load_manifest(path)` / `load_stacking(path)` → validated dicts; `DataError(ValueError)` names file+entry+rule. Manifest molecule fields: `id, name, file, source_db, source_id, atom_count, charge, ring_count, ring_atoms, set`. Interaction fields: `id, mode, name, distance_a, lateral_offset_a, uncertainty_a, citation (key), explanation, applies_to{sets}, status`. Citations table: `short, doi, approved`.
- `shipped_interactions(data)` → APPROVED-only (DATA-02). `interaction_for(molecule, data)` → first file-order match on `molecule['set']`, or None. **NOT approval-filtered** — callers must gate APPROVED separately (current shipped entry is APPROVED, so no behavioral delta today, but the skip-policy contract must use the approved set).
- Shipped file: exactly ONE interaction `pi_stack_pd`, mode `pi_stack`, d=3.383, l=1.231, citation `janiak2000` ("Janiak 2000", 10.1039/b003010o, approved), status APPROVED, applies_to {set_a}. Composed centroid-centroid = √(3.383²+1.231²)=3.60 Å at atan2(1.231,3.383)=20.0° off-normal (formula pinned in test_stacking_dataset.py — reuse it for STACK-04 display).

### setloader.py (records as-is + one carry-through)

- `load_demo_set(data_dir=None, set_id='set_a', stacking_path=None) -> (records, errors)`; `load_upload(path, stacking_path=None)`. Record keys (probe-verified): `id, name, file, record_index, elements, atom_count, charge, ring_count, has_explicit_h, has_stack_entry, set, source, warnings` (+ `ring_atoms` = sorted 2-core, demo records ONLY — uploads omit it by design).
- **`has_stack_entry` is computed ONLY when `stacking_path` is passed** (`interaction_for({'set': set_id}, data) is not None`). Note: computed WITHOUT the approval filter.
- `UPLOAD_SET_ID = '__upload__'` — matches no interaction → every upload is skip-at-pickup (STACK-03/DATA-03, LOCKED).
- Records do NOT carry coords or bonds — re-read `record['file']` via `molfile.read_sdf` (single-record demo SDFs) to get `elements`, `coords`, `bonds`. Atom order in the file must align with ring indices (true for our own SDFs; smoke-verify that `cmd.load` preserves order for the bridge display).

### setup_logic.py (cap source)

- `DEFAULTS['win_cap_molecules'] = 10` (range 1..20 enforced by `validate`), `atom_budget = 100` (warning-level), `BOX_PRESETS` (small ±12 / medium ±18 / large ±25, xy-only — z is bridge-owned `BOX_DISPLAY_Z=5.0`), `speed` mirrors engine 3.0. **GAME-06 cap = molecule COUNT (`molecules_stacked >= cap`), never Å.** Current wiring: `gui_game._build_engine` already passes `cap=setup.get('win_cap_molecules')`, `atom_budget=setup.get('atom_budget')`.

## gap_analysis (per requirement)

| Req | Exists as-is | Needs extension | Missing entirely |
|-----|--------------|-----------------|------------------|
| **STACK-01** (deterministic placement at dataset geometry) | `place_pickup` + dataset values + ring_frame; exactness probe-verified | nothing in core | controller seam that assembles tail frame from newest segment (or head for the first) + normal-sign / lateral-direction policy; `transform_selection` matrix-layout verification |
| **STACK-03** (skip with reason) | `__upload__` keying; `has_stack_entry`; `interaction_for` → None; `reject_pickup` canonical tuple | reason-string composition (GUI/PURE hud seam); `stack_ring` absence as a skip condition | approval-gated skip (`status != APPROVED`); unsupported-`mode` skip; skip reason rendering in info box |
| **STACK-04** (structured info content) | ALL per-pickup fields in the dataset (name, distance_a, lateral_offset_a, explanation, citation→short/doi); composed-distance formula test-pinned | PURE text-composition helpers (hud_logic-style) so content is unit-testable; end-of-run breakdown from engine counters + per-segment molecule ids | idle chemistry tips + controls hints content (NOT in dataset — hardcode in a PURE seam); wiring into `info_box` |
| **STACK-05** (clash gate) | `check_clash` + 2.5 Å threshold + `reject_pickup` seam; 5-molecule clash matrix measured | 3D box args (extend 2D preset with ±`BOX_DISPLAY_Z`); `existing_atoms` assembly (head atoms + all segment atoms + other live pickup atoms? — see open Q) | — |
| **GAME-04** (stacking + hidden counts) | engine counters (`molecules_stacked`, `atoms_total`) incremented on capture, rolled back on reject; `atoms_n` on every record | completed-snake totals = head `atom_count` + engine `atoms_total` (head not tracked — controller must add) | atom counts ARE in records (atom_count) and in engine via `atoms_n` — aggregation seam only |
| **GAME-05** (boundary/body end run) | FULLY DONE in engine (02-10), pinned by test_engine_rules | — | GUI completion behavior (GAME-09) |
| **GAME-06** (win at cap) | cap wiring + `('won',)` + `molecules_remaining` label | **win-vs-clash desync resolution** (see gap G2) | — |
| **GAME-09** (completion handoff) | `engine.result`, finished segments (sweep-rotated atoms ARE the truth), `_teardown_round` single helper | pickup objects + chain objects teardown INTO `_teardown_round` (04-08 decision); info box breakdown; "Get Spectra" activation | camera focus on completed snake (bridge call, `cmd.zoom` on chain objects); head-atom tracking for the final snake (head atoms currently exist ONLY in PyMOL + controller math); final xyz assembly seam (xyzio exists from Phase 2, used by Phase 6) |
| **GAME-10** (rigid pivot turns) | FULLY DONE in engine (02-13), incl. refusals | `('turning',)` chain re-render in gui_game/bridge (currently silent; only head moves today) | chain PyMOL objects + their per-tick re-sync (apply R about head, or rewrite coords from engine truth) |

**Named gaps (planner must schedule):**
- **G1 — Ring extraction:** no canonical planar 6-ring extractor exists. See ring_extraction_spec.
- **G2 — Win-vs-clash desync:** if the cap-reaching capture is clash-rejected, `('won',)` has already been emitted and `finished=True`; `reject_pickup` rolls counters but does not un-finish. Options: (a) small pure engine extension — defer the win to a new confirm path (e.g., emit 'stacked' without win, and let `attach_segment` check cap — but this CHANGES the test-pinned event order, so prefer an ADDITIVE method, e.g. `confirm_win()` the controller calls after successful attach when `molecules_stacked >= cap` — still changes what step() emits; cleanest additive variant: keep current behavior but add `unfinish()`/make `reject_pickup` clear `finished/result` when it rolls a won run back below cap — the narrowest possible change); (b) documented acceptance (risk: frozen "won" run with sub-cap counter). **Recommend (a)-variant with minimal diff, as an explicit Phase-5 plan decision.**
- **G3 — Pickup spawning:** NO spawn policy exists anywhere (positions, count, respawn-after-capture/reject, exclusion margins from walls/head/existing pickups, RNG policy). ARCHITECTURE's flow says the controller places pickups ("engine-placed grid cells" is stale wording — the engine never spawns). Needs a small PURE module (seeded RNG like `setup_logic.randomize_head`'s private-`Random` pattern, or deterministic layout).
- **G4 — Wiring:** `gui_setup._on_apply` calls `setloader.load_demo_set(set_id=source)` / `load_upload(path)` WITHOUT `stacking_path` → `has_stack_entry` is ALWAYS False today; and `gui_game.begin_game(setup)` receives only the setup dict — records never reach the game tab. Both must be plumbed (records → anchor or begin_game signature).
- **G5 — Edge-on orientation:** LOCKED presentation decision (03-08 + 04-07 remark): ring planes edge-on (normal IN the xy plane). A pure pre-rotation (applied identically to the head at materialization, to pickup records/engine atoms, and to the placement inputs) does not exist. Azimuth choice (which in-plane ring direction maps to z) + `BOX_DISPLAY_Z` 5.0-vs-6.0 are pending decisions. Note probe fact: fused-aromatic SDFs ship with rings flat in xy (z≈0, normal ±z); biphenyl ships 3D.
- **G6 — Growth-end/direction policy:** which molecule is the stacking "tail" on attach (newest/last segment; head molecule when chain is empty) and which side (normal sign) the chain grows on — see open questions.
- **G7 — Chain objects in the bridge:** no `srp_chain_*`/`srp_pickup_*` objects exist; `move_head_delta` only moves the head. Phase 5 bridge additions: materialize pickups, apply placement transform, re-sync chain on 'turning', delete on teardown/capture.

## ring_extraction_spec (the trap — VERDICT + algorithm)

**Verdict:** extraction is mandatory and small. Do NOT call `ring_frame` with manifest `ring_atoms` — they are the full 2-core in **sorted index order, not ring-walk order**. Probe evidence:

| molecule | 2-core (find_ring_atoms) | full 2-core through ring_frame | canonical 6-cycle through ring_frame |
|----------|--------------------------|--------------------------------|--------------------------------------|
| benzene | 6 atoms [0..5] | **FAILS: "non-planar (1.133 A)"** — spurious, caused by star-polygon order, the SDF is exactly flat (all z=0.000) | OK |
| naphthalene | 10 atoms | planar OK (n=giant fused perimeter accepted, but is NOT a ring — wrong frame semantics) | OK |
| anthracene | 14 | planar OK (same caveat) | OK |
| phenanthrene | 14 | planar OK (same caveat) | OK |
| biphenyl | 12 | **FAILS: "non-planar (3.316 A)"** — genuinely non-planar (rings at 90.00°, measured) | OK (each ring individually planar) |

Even where the fused perimeter "passes", its frame is chemically wrong (averaged multi-ring centroid/normal, ref axis points at a shared edge atom) — STACK-01's cited geometry between RING pairs requires one ring.

**Algorithm (pure, ~30 lines, stdlib):**
1. Inputs: `bonds` (list of index pairs — from the SAME molfile record as the coords) and `ring_atoms`/`find_ring_atoms` core (restricted adjacency).
2. Build adjacency restricted to the core.
3. Enumerate simple cycles of length ≤ 6** via bounded DFS from each start node with `nb > start` pruning (probe implementation above; n ≤ 14, trivially fast).
4. Select the canonical cycle: **shortest length; then lexicographic minimum over all 2n rotation/reversal normalizations** (rotate so the smallest index is first AND canonicalize orientation — reversal changes the normal sign, so the rule must fix orientation deterministically, e.g. min tuple over both orientations).
5. Return the ordered index list (ring-walk order).

**Probe-verified canonical outputs (for the exact rule above, min-over-orientations):**
- benzene `(0, 1, 3, 5, 4, 2)` — only cycle
- naphthalene: 2 cycles → `(0, 1, 3, 7, 6, 2)` wins over `(0, 1, 5, 9, 8, 4)`
- anthracene: 3 cycles → `(0, 1, 5, 3, 2, 4)`
- phenanthrene: 3 cycles → `(0, 1, 3, 5, 4, 2)`
- biphenyl: 2 cycles → `(0, 2, 6, 10, 8, 4)` (ring A; ring B `(1, 3, 7, 11, 9, 5)` equivalent by symmetry for frame purposes)

All five pass `ring_frame`'s 0.15 Å planarity check (probe). Determinism: same inputs → same output (pure function); same molecule used as both tail and pickup → same frame → `place_pickup` reduces to pure translation (the dimer2 contract generalizes).

**Where it lives:** the cycle math belongs in `molfile.py` next to `find_ring_atoms` (graph algorithm on the same record; auto-classified PURE). `setloader._build_record` computes it at load time and carries it on the record as **`stack_ring`** (demo records only; uploads stay ring-less). At capture time the pickup record's `stack_ring` indexes into both the SDF coords and the placed atoms 1:1. For tail frames during play, recompute `ring_frame(current_segment_atoms, segment['stack_ring'])` — engine copies carry `stack_ring` through (unknown-key passthrough verified in `_copy_segments` and `_advance_sweep`).

**Test strategy:** pin the five canonical tuples above; benzene sorted-order-fails/walk-order-passes regression (the actual trap); biphenyl ring-A/ring-B planarity + 90° inter-ring angle fact; determinism (repeat calls); a pucker-rejection case; `stack_ring` absent on upload records.

## engine_contracts (what gui_game / pymol_bridge must call, in order)

**At game start (per run — `begin_game`):**
1. Load records WITH the dataset: `setloader.load_demo_set(stacking_path=setloader.default_stacking_path())` (fixes G4).
2. Build the head record selection (existing `materialize` path) AND compute head atoms: read `record['file']` via `molfile.read_sdf`, apply the edge-on pre-rotation (G5), translate so the head ring centroid sits at (0,0,0) = engine head start. Controller keeps `head_atoms` as its own truth (engine never tracks them).
3. Spawn pickups (G3, pure policy) → engine seed records: `{'id', 'centroid': (x,y), 'atoms': [(sym,x,y,z)...], 'atoms_n', PLUS carried extras: 'molecule_id', 'stack_ring', 'record' or fields needed for info box}` — extras survive engine copies.
4. `GameEngine(head=(0.,0.), heading='right', box_min/box_max=BOX_PRESETS[preset], pickups=seed_records, cap=setup['win_cap_molecules'], atom_budget=setup['atom_budget'])`.
5. Bridge: materialize pickup objects (`cmd.load(record['file'])` then apply the SAME pre-rotation + spawn translation — engine truth and display must agree bit-for-bit; prefer applying engine truth via one verified transform call).

**Per tick (existing `_on_tick`, extended):** `events = engine.step(0.1)` then, in event order:
- `('moved', pos)` → `pymol_bridge.move_head_delta(...)` (exists) + update controller `head_atoms` offset.
- `('turning', fraction)` → **NEW:** re-render the whole chain from `engine.segments` (rotate each `srp_chain_*` object about the head by the tick's absolute angle, or rewrite coords from engine truth). Do NOT re-run collision logic — none is needed (pre-checked at open).
- `('stacked', pickup_record)` → **the STACK-05 controller seam, in order:**
  1. Skip pre-checks (STACK-03): approval-gated interaction present? `stack_ring` present? If not → log reason, call NOTHING on the engine (the engine already counted it...). **Correction — always call `reject_pickup(id, reason)` for skips**, because capture already incremented counters; reject re-arms and rolls back. Reason taxonomy below.
  2. Ring extraction was done at load → build tail frame: newest segment's frame (`ring_frame(seg['atoms-as-(x,y,z)'], seg['stack_ring'])`), or the head's frame when `segments` is empty.
  3. `place_pickup(pickup_atoms(pre-rotated), stack_ring, tail_c, ±tail_n, tail_ref, distance_a=3.383, lateral_offset_a=1.231, lateral_along_ref=<policy>)`.
  4. `check_clash(placed, existing=(head_atoms + every segment's atoms [+ other live pickups' atoms? — open Q]), box_min=(x0,y0,-Z), box_max=(x1,y1,+Z))`.
  5. Clear → `engine.attach_segment(molecule_id, placed_ring_centroid_xy, [(sym,x,y,z)...])` + bridge applies `R,t` to the pickup object and renames it `srp_chain_*` (verify `transform_selection` layout first). Clash/wall → `reject_pickup(id, 'clash')` → log the `('refused', id, reason)` tuple + clash detail.
- `('budget_warning', n)` → info-box line (visibility = open Q).
- `('crashed', 'boundary'|'body')` / `('won',)` → GAME-09 flow: teardown INTO `_teardown_round` (04-08 decision), delete remaining live pickup objects, focus camera on the chain, show length + score (`molecules_stacked`), interaction breakdown, activate "Get Spectra". Final snake xyz = head atoms (translated) + every `seg['atoms']` (sweep-rotated — this IS the truth; do not re-read PyMOL).

**Never do:** per-tick collision checks during sweeps; per-tick re-zoom; `cmd.set_key` for arrows (Phase 4 wizard already handles steering); read PyMOL object coords back as truth; place a pickup without `reject_pickup` on any skip (counters would desync).

## skip_policy_matrix

Reason strings are GUI-text (unit-testable in a PURE hud seam). Suggested literals; planner may wordsmith.

| # | Condition | Detection point | Source of truth | Reason (suggested) |
|---|-----------|-----------------|-----------------|--------------------|
| 1 | Upload (`set == '__upload__'`) or set matches no interaction | `has_stack_entry is False` (or `interaction_for` → None) | setloader + molecule_data | "no verified stacking entry for this molecule — skipped (no invented chemistry)" |
| 2 | Interaction exists but `status != 'APPROVED'` | compare against `shipped_interactions(data)` | molecule_data (DATA-02) | "stacking entry not approved yet — skipped" |
| 3 | `mode != 'pi_stack'` (future datasets) | interaction `mode` field | dataset | "interaction mode '<mode>' not supported in v1 — skipped" |
| 4 | No planar 6-ring extractable (e.g. 5-membered rings only) | `stack_ring` absent on record | molfile extractor (G1) | "no planar aromatic 6-ring found — skipped" |
| 5 | `ring_frame` ValueError (non-planar > 0.15 Å / degenerate) | placement attempt | stacking.py exception message | "ring geometry not planar (<msg>) — skipped" |
| 6 | Clash gate `{'kind': 'wall', ...}` | `check_clash` | stacking.py | "placement would leave the play box — skipped" |
| 7 | Clash gate `{'kind': 'atom', ...}` | `check_clash` | stacking.py | "placement clashes (<distance:.2f> Å < 2.5 Å) — skipped" |
| 8 | Turn blocked (boundary/body/pickup) | `('turn_refused', reason)` | engine | NOT a pickup skip — info-box "turn refused: <reason>" (existing line) |

**Biphenyl is today the live demonstrator of row 7** (every pairwise placement at dataset geometry clashes; measured matrix below). Planner should expect biphenyl pickups to ALWAYS refuse as shipped.

| clash matrix (min inter-pair distance, Å; 2.5 Å gate) | pickup: benzene | naphthalene | anthracene | phenanthrene | biphenyl |
|---|---|---|---|---|---|
| tail: benzene | 3.386 | 3.386 | 3.387 | 3.386 | **2.145 CLASH** |
| naphthalene | 3.386 | 3.386 | 3.386 | 3.386 | **1.751 CLASH** |
| anthracene | 3.386 | 3.385 | 3.386 | 3.387 | **1.753 CLASH** |
| phenanthrene | 3.386 | 3.386 | 3.386 | 3.387 | **1.660 CLASH** |
| biphenyl | **1.283 CLASH** | **1.279 CLASH** | **1.278 CLASH** | **1.275 CLASH** | **0.688 CLASH** |

Measured with canonical rings, d=3.383/l=1.231 along ref. Also measured: a 6-segment same-molecule linear chain (successive `place_pickup` output frames) never drops below 3.386 Å anywhere — growth along the same direction is clash-safe for all four fused aromatics. `lateral_along_ref=False` slightly INCREASES clearance for fused aromatics (3.43 vs 3.39) but doesn't rescue biphenyl (1.34 self).

## data_flow_diagram

```
serpentrum/data/manifest.json ─┐
serpentrum/data/stacking_pi_stack.json ─┴─> molecule_data.load_manifest/load_stacking
                                              │ (validated dicts; DataError naming file+rule)
                                              ▼
              setloader.load_demo_set(data_dir, set_id, stacking_path=default_stacking_path())
              setloader.load_upload(path, stacking_path)          [G4: gui_setup must pass stacking_path]
                                              │ records: {id,name,file,elements,atom_count,charge,
                                              │   ring_count,ring_atoms[2-core],has_stack_entry,set,source,warnings}
                                              ▼
              [G1] molfile 6-ring extractor (from record's SDF bonds + 2-core)
                                              │ record['stack_ring'] = canonical ordered 6-cycle (demo only)
                                              ▼
              [G5] edge-on pre-rotation (pure; applied identically to head, pickups, engine atoms, bridge transforms)
                                              ▼
              [G3] spawn policy (pure) → engine pickup records {id,centroid(x,y),atoms(sym,x,y,z),atoms_n,
                                              │   + carried: molecule_id, stack_ring, record fields}
                                              ▼
              game_engine.GameEngine(box_min/max=BOX_PRESETS xy, cap, atom_budget)
                  step(0.1) per 100 ms tick  ──> events ──> gui_game._on_tick
                       │ ('moved')         → bridge.move_head_delta (exists)
                       │ ('turning')       → [G7] re-render chain objects from engine.segments
                       │ ('stacked', rec)  → controller seam (PURE assembly):
                       │      skip checks (matrix rows 1-4) → reject_pickup(id, reason)  [STACK-03]
                       │      tail frame = ring_frame(newest seg atoms, seg stack_ring) [or head when empty]
                       │      place_pickup(..., 3.383, 1.231, <policy flags>)           [STACK-01]
                       │      check_clash(placed, head_atoms+chain_atoms, 3D box)       [STACK-05]
                       │      clear → attach_segment + bridge apply (R,t) → srp_chain_* object
                       │      clash → reject_pickup(id,'clash') + info-box reason
                       │ ('budget_warning') → info box (visibility open)
                       │ ('crashed'|'won')  → GAME-09: _teardown_round (+pickup/chain objects),
                       │      camera focus chain, breakdown, activate Get Spectra
                                              ▼
              Final snake = head_atoms(translated) + Σ seg['atoms']  →  xyzio.write_xyz (Phase 6 seam, exists)
                                              ▼
              STACK-04 info box per pickup: interaction['name'], d=3.383 Å + composed 3.60 Å @ 20°,
              interaction['explanation'], citations[key]['short'] (+ DOI)  — ALL from the dataset;
              idle tips / controls hints = hardcoded PURE text (not in dataset).
```

## dont_hand_roll

| Problem | Don't build | Use instead | Why |
|---------|-------------|-------------|-----|
| Ring frame placement math | any new transform code | `stacking.ring_frame/place_pickup` | dimer2-provable exactness; Newell + azimuth-0 determinism contract |
| Clash detection | spatial hashing / custom distance loop | `stacking.check_clash` | ≤ ~120 atoms; O(n·m) trivial; pinned threshold rationale (xtb rcov ~2.0 vs stack 3.4) |
| Dataset access | GUI-side json.loads | `molecule_data` loaders + `interaction_for` + `shipped_interactions` | DATA-02 approval gating + DataError diagnostics |
| Record building / uploads | bridge-side SDF parsing | `setloader` (records in, never parse in bridge) | unit-testable PURE; `__upload__` keying proven |
| 2-core finding | new graph walk for that | `molfile.find_ring_atoms` | exists; only the 6-cycle extraction on top of it is new (no stdlib alternative — justified) |
| RNG for spawning/head | global `random` | private `random.Random(seed)` per `setup_logic.randomize_head` precedent | determinism + seed isolation |
| Point-segment distance | new helper | `game_engine._point_segment_distance_sq` | the ONE body-collision model engine-wide |
| Rotation math | per-call trig inline | `game_engine._rotate_xy` | identical primitive for sweep pre-check and progression |
| Info text formatting | Qt-side string surgery | `hud_logic`-style PURE seam | WSL-unit-testable; widgets stay human-verify |
| Final snake file | hand-rolled xyz | `xyzio.write_xyz` (Phase 2) | the Phase-6 handoff format, round-trip pinned |
| PyMOL transforms | get_object_ttt / matrix guessing | verified `transform_selection` (verify editing.py:1946 FIRST) or `cmd.rotate`+`cmd.translate` fallback | ttt getter segfaults (gameloop M5); layout flagged OPEN |

**Key insight:** Phase 5 is an integration + policy phase, not a math phase. Every numeric claim above is already test-pinned or probe-verified; new code should be overwhelmingly wiring + small PURE seams, all python3.6/stdlib (purity gate classes PURE/GUI/BRIDGE unchanged).

## open_questions

1. **Biphenyl is unstackable as shipped (measured: 90° twist; every pairwise clash ≤2.145 Å).** Accept it as the permanent refuse-path demonstrator, or raise to the human as a DATA-02 data review (the shipped PubChem 3D conformer is unusual; a twist near literature values would still clash pairwise — likely needs a human decision). No unilateral data change (verification rule).
2. **Win-vs-clash desync (G2).** Additive engine fix (e.g. `reject_pickup` clears `finished/result` when rolling a won run back below cap) vs documented acceptance. Affects test_engine_rules' pinned event order only if we change WHAT step() emits — prefer a method-level additive change and new tests.
3. **Growth end + tail choice (G6).** At attach, is the stacking tail the LAST (newest) segment with growth continuing on the same side (linear staircase — probe-verified clash-safe for the 4 fused aromatics), and the head molecule when segments is empty? And the normal sign/side policy for the very first attachment relative to the head? This interacts with the SEGMENT_SKIP_RECENT=2 "neck" semantics: the engine's exemption covers the two NEWEST indices regardless of world position. Planner must pin one policy and test the geometry.
4. **Spawn policy (G3).** Count, positions (bounds margins ≥ clash threshold from walls + ≥ PICKUP radius spacing?), respawn after capture and after clash-reject (re-armed pickups stay put — a rejected pickup left adjacent to the chain will repeatedly re-capture/refuse; is that intended?), seeded-RNG or deterministic layout, and whether uploaded (always-skipped) molecules may even spawn (spawning a pickup that always refuses is arguably honest STACK-03 pedagogy — decide).
5. **Edge-on orientation definition (G5).** Which in-plane ring direction maps to z (screen depth): long axis along z (max z-extent ~9.5 Å ⇒ BOX_DISPLAY_Z 6.0 "Option B" per 03-08) vs short axis along z; and does the 1.231 lateral offset land in-plane or in z (sets whether the alternating staircase is visible to the locked camera or sinks into the screen). All fused SDFs ship flat in xy (normal ±z) → a ±90° pre-rotation about an in-plane ring axis is required; biphenyl ships 3D with a different canonical pre-rotation. Decision needed BEFORE any stacking lands (04-07 remark).
6. **`transform_selection` matrix layout** — flagged OPEN since ARCHITECTURE §9; first Phase-5 bridge task must read `editing.py:1946` (PyMOL 2.5 source) and smoke-prove one placement; fallback `cmd.rotate`+`cmd.translate`. Also smoke-verify `cmd.load` preserves SDF atom order (indices must match `stack_ring`).
7. **Existing-atom set for the clash gate:** head atoms + chain atoms is minimal; should OTHER STILL-LIVE pickups also block (a placement overlapping a nearby unpicked pickup would later refuse that pickup mid-chain)? Leaning yes for consistency, but it's a policy call (cost trivial).
8. **Score/length semantics at completion:** engine counts captured segments only; does "snake length" shown at GAME-09 include the head (+1)? And `budget_warning` visibility (hidden per GAME-04's "hidden counts" vs an info-box line)?
9. **Idle tips / controls hints content (STACK-04):** not present in the dataset. Confirm hardcoded PURE text is acceptable (recommend: a small tuple in hud_logic or a new `game_text.py` PURE module, unit-tested; NO new dataset keys without a schema bump).

## Sources

### Primary (probe-verified this session, HIGH confidence)
- `serpentrum/stacking.py`, `game_engine.py`, `molecule_data.py`, `setloader.py`, `molfile.py` — full reads + live `python3.6` probes (ring census, planarity, clash matrix, place_pickup exactness, chain-growth clearance, setloader record shapes, `__upload__` behavior)
- `python3.6 tests/run_gates.py` — green baseline (451 tests, 3/3 gates) before conclusions
- `.planning/STATE.md` decisions block; ROADMAP Phase 5 success criteria; REQUIREMENTS text (STACK-03/04 exact wording)

### Secondary (HIGH — design intent)
- `tests/test_stacking_math.py`, `test_stacking_dataset.py`, `test_engine_core/rules/turns.py`, `test_integration_pure_core.py` (test-name census of pinned invariants)
- `.planning/phases/02-*/02-10-SUMMARY.md`, `02-13-SUMMARY.md`, `02-RESEARCH-pure-core.md` §7; `03-05-SUMMARY.md` (ring_atoms contract)
- `.planning/research/ARCHITECTURE.md` §9 + data flow (transform_selection OPEN item); `03-08` decision in STATE.md (edge-on presentation, BOX_DISPLAY_Z Option B, 04-07 remark)

### Tertiary
- None — no web sources used; all chemistry values come from the shipped, human-approved dataset (Janiak 2000, DOI 10.1039/b003010o).

## Metadata

**Confidence breakdown:**
- current API surface: HIGH (code read + probes + pinned tests)
- ring extraction spec: HIGH (probe-verified on all 5 shipped molecules; exact canonical tuples)
- clash matrix / biphenyl finding: HIGH (measured, reproducible one-liner)
- gap analysis: HIGH for core; MEDIUM for GUI-side deltas (gui_game read fully; gui_setup/gui.py read at the wiring points)
- open questions: all are genuine policy decisions, no hidden technical blockers except `transform_selection` layout (fallback exists)

**Research date:** 2026-09-15
**Valid until:** 2026-10-15 (stable pure core; re-probe only if the dataset or SDFs change)
