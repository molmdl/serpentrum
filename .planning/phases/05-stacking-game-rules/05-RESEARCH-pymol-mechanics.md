# Phase 5: Stacking & Game Rules — PyMOL Viewer Mechanics Research

**Researched:** 2026-09-15
**Domain:** PyMOL 2.5.0 command mechanics for edge-on orientation, rigid chain sweeps, stacking placement, completion flow
**Confidence:** HIGH (every load-bearing claim verified either by headless Windows PyMOL probes or by reading `pymol-src/modules/pymol/editing.py` shipped in-repo)

**Probe artifacts (gitignored under `tmp/`):**
- `tmp/p5_pymol_probe.py` — headless probe, run `timeout 150 cmd.exe /c "C:\src\run-conda-pymol.bat -cq tmp\p5_pymol_probe.py"` from repo root. 17 PASS / 1 "fail" (the fail is a 3.7e-06 Å incremental-rotate drift vs my 1e-6 gate — recorded as a finding, not a blocker).
- `/tmp/opencode/p5_extents_pure.py` — WSL pure-python extent measurement (BOX_DISPLAY_Z decision data).

## Summary

Every Phase-5 viewer mechanic is verified working with the exact commands below. The two load-bearing verdicts:

1. **Matrix verdict (ROADMAP "verify transform_selection matrix layout"): VERIFIED.** `cmd.transform_selection(selection, m16)` expects 16 floats where rows 0–2 cols 0–2 hold a **row-major 3×3 R** applied to the **column vector**, col 3 (`m[3], m[7], m[11]`) is the post-translation, and the bottom row (`m[12], m[13], m[14]`) is a **pre-translation applied BEFORE R**. So `y = R·(x + pre) + t`. stacking.py's `(R, t)` from `place_pickup` maps **directly**: `[R00,R01,R02,t0, R10,R11,R12,t1, R20,R21,R22,t2, 0,0,0,1]`. Probe-measured end-to-end: a benzene placed via this exact matrix landed at 3.6000 Å ring-centroid distance vs the dataset's `sqrt(3.383²+1.231²)=3.60`, and its viewer coordinates matched the pure-layer `placed` output to <5e-3 Å (sorted/rounded compare). The fallback is unnecessary but confirmed available (`cmd.rotate` + `cmd.translate` build the identical matrix internally — `editing.py:1688-1692, 1815-1819`).
2. **Rigid-sweep verdict: ONE `cmd.rotate` call per tick.** `cmd.rotate('z', angle, 'sel covering N objects', camera=0, origin=[hx,hy,0])` rigidly rotates **all** selected objects about the pivot with **atomic-coordinate** writes (z exactly preserved, internal geometry preserved to <5e-7 Å, wildcards OK, a CGO in the selection is harmless). 10 objects cost **~0.4 ms/tick headless** — three orders of magnitude inside the 100 ms budget. No group objects, no per-object matrices, no cumulative-transform bookkeeping needed.

**Primary recommendation:** bridge gets three new thin functions — `apply_edge_on(name, m16)` (at load/materialize, reusing the verified matrix builder), `sweep_chain(angle, pivot, names)` (one `cmd.rotate` per `('turning',)` tick), `place_object(name, R, t)` (one `cmd.transform_selection` per `('stacked',)` event). All matrix construction stays in the pure layer; the bridge only forwards.

## Standard Stack

The established commands (all verified this phase):

| Command (PyMOL 2.5.0) | Verified signature / behavior | Why standard |
|---|---|---|
| `cmd.transform_selection(sel, m16)` | 16-float list; layout above; state=-1; regenerates representations automatically (editing.py docstring) | THE placement/orientation primitive; exact, no drift |
| `cmd.rotate('z', deg, sel, camera=0, origin=[x,y,0])` | `deg`>0 = CCW about +z (matches engine `_rotate_xy` sign — probe B); atomic coords; selection may span objects & wildcards; CGO members ignored | THE sweep primitive — one call per tick |
| `cmd.translate([dx,dy,0], name, camera=0)` | atomic, zero drift (04 probe M3) | existing `move_head_delta` — per `('moved',)` tick |
| `cmd.get_extent(sel)` | works on multi-object selections (probe G2) | combined-snake bounds at completion |
| `cmd.get_model(sel)` | merged `.atom` list across objects (probe G1: 2 benzenes → 24 atoms) | placed-distance verification in smokes |
| `cmd.delete('srp_pickup_*')` | pattern delete works (probe G4); `cleanup_srp`'s `'srp_*'` pattern already covers all pickup/segment names | teardown scope |
| `cmd.disable(name)` / `cmd.zoom(sel)` / `cmd.refresh()` | all work at completion (probe G3) | GAME-09 framing |
| `cmd.set_object_ttt` / `transform_object` | write-only safe; **`cmd.get_object_ttt` SEGFAULTS** (04 probe M5 — never call) | not needed for Phase 5; `transform_object` measured 10× in 0.04 ms as an alternate sweep path (E2) |

### NOT used (rejected after verification)
| Instead of | We use | Why |
|---|---|---|
| PyMOL group objects | one `cmd.rotate` on an or-selection | group adds naming/lifecycle complexity for zero benefit (probe B proves selection works) |
| per-object cumulative 4×4 bookkeeping | incremental per-tick rotate | measured drift 3.7e-06 Å **per full 90° sweep** — irrelevant at any snake length; engine already rotates its own records absolutely, so engine↔viewer agreement is dominated by nothing else |
| `homogenous=1`-style matrices | TTT layout (homogenous=0) | PyMOL's `homogenous` path is self-admitted "Possibly Wrong" (editing.py:1904-1920) |

**No new Python dependencies.** All math is tuples/`math` (pure layer); numpy is NOT available to the bridge (purity).

## Architecture Patterns

### Where each piece lives

```
pure layer (WSL-testable, no pymol):
  molfile.find_ring_atoms + NEW ring_cycle(bonds, ring_set)   # ring ORDER (see Pitfall P5-1)
  stacking.ring_frame(atoms, ring_in_bond_order)
  NEW canonical_edge_on(atoms, ring) -> (R_edge, pre, post)   # pure matrix builder
  stacking.place_pickup(...) -> (placed, R, t)                # existing, verified exact
  stacking.check_clash(placed, engine_placed_atoms, ...)      # existing; feed ENGINE records
  game_engine step()/sweeps                                   # owns all truth; viewer mirrors

pymol_bridge (the ONLY cmd importer, new thin fns):
  apply_matrix(name, m16)            # cmd.transform_selection
  sweep_chain(delta_deg, pivot_xy)   # ONE cmd.rotate per ('turning',) tick,
                                     #   selection = 'srp_*' (box CGO harmless) or explicit head+segments
  place_segment(pickup_name, m16)    # transform_selection then set_name -> srp_seg_N
  completion_frame()                 # delete srp_box (+ stray pickups), zoom('srp_*'), refresh

gui_game (controller):
  on 'stacked': build m16 from place_pickup(+check_clash; reject_pickup on clash), attach_segment
  on 'turning': sweep_chain(angle_signed/TURN_TICKS, engine.head)
  _end_run: teardown FIRST (unlocks camera) THEN completion_frame (see Pitfall P5-3)
```

### Pattern 1: Edge-on canonicalization at load time (04-07 invariant)
**What:** every molecule object (head AND each pickup) is transformed exactly once at load into a canonical edge-on pose: ring normal → **+x** (chain axis, in the xy plane), ring ref axis r1 → **+z** (vertical), r2 → **+y** (lateral). Ring centroid → origin.
**Mechanism (verified end-to-end, probe F):** compute `R_edge` purely from the stored ring frame as `R_edge = C·Bᵀ` with basis columns B=(r1,r2,n), C=((0,0,1),(0,1,0),(1,0,0)); then `m16 = [R_edge | post=(0,0,0) | pre=−ring_centroid]`; one `cmd.transform_selection`.
**Where:** head at `materialize` (before `place_head`... note: edge-on THEN translate-to-origin — the existing `place_head` extent-centers; do edge-on first so its extent is the canonical one); each pickup at spawn load. **Never** at placement time — placement then degenerates to a near-translation (probe F's R,t came out identity-like translation for identical molecules, exactly the STACK-01 determinism property).
**Why canonical C as above:** after this pose, `place_pickup` tail frame is simply `((hx,hy,0), chain_normal, (0,0,1))` — the tail frame needs NO viewer queries at all.

### Pattern 2: Sweep tick = one rotate; head spins in place
The selection for `sweep_chain` should **include `srp_head`**: the pivot is the head's center, so the head rotates in place (its ring normal follows the chain — visually AND for the next stack's frame consistency the canonical pose implies normal≈heading; a rigid sweep keeps `normal == chain axis` invariant). Engine does not track head orientation; the same single call handles it for free (probe B included `srp_head` in the rotation selection and verified rigid, correct results).

### Pattern 3: Stack-sign convention (controller, not bridge)
Segments trail **behind** the head along −heading, so new placements use `tail_normal = −(heading)` (or equivalently +heading with stack on that side) — `place_pickup`'s documented sign freedom. Lateral offset stays along canonical ref (+z) per dataset. This is the one sign decision the planner must pin in the plan; both choices are geometrically valid, behind-the-head is snake-canonical.

### Pattern 4: Completion flow (GAME-09) — ordering contract
`_teardown_round` (unlock_camera) must run **before** the completion zoom: `unlock_camera` ends with `cmd.set_view(saved_view)`, which **overwrites any prior zoom** (18-float view includes scale/position — verified semantics in viewing.py + lock/unlock code). Sequence: stop timers → unlock camera → `cmd.delete('srp_box')` + stray `srp_pickup_*` → `cmd.zoom('srp_*')` → `cmd.refresh()` → show Get Spectra. The saved default view looks down −z at the xy plane (04 research C2), so zoom('srp_*') frames the snake in 2D without `cmd.orient`.

### Pattern 5: Per-tick PyMOL calls are exactly ONE
Per tick: `move_head_delta` on ('moved',) OR `sweep_chain` on ('turning',). **No `get_extent`, no `get_model`, no `get_names` per tick.** The engine tracks all positions as floats; PyMOL is a pure renderer (confirmed by design + 04 research perf table). Viewer reads happen only at setup/completion/smoke-verification.

## Don't Hand-Roll

| Problem | Don't build | Use instead | Why |
|---|---|---|---|
| matrix composition (pivot rotation = translate-rotate-translate) | custom TTT composer | pre/post slots of the one matrix: `pre=−pivot, post=+pivot` (verified A2, 2.4e-07 Å) | PyMOL's TTT layout IS the pivot idiom; `cmd.rotate(origin=...)` does it for free |
| ring atom ORDER for `ring_frame` | assume manifest order works | `molfile.find_ring_atoms` + DFS single-cycle traversal (prototype in `tmp/p5_pymol_probe.py` `dfs()/cycle` and `tmp` extent probe) | **manifest `ring_atoms` are SORTED indices, not bond order — benzene fails planarity (1.133 Å) if fed directly; biphenyl's 12-atom set is non-planar (twisted) — see Pitfall P5-1** |
| rigid multi-object rotation | group objects / TTT matrices / per-object loops | ONE `cmd.rotate(..., selection, origin=...)` | verified rigid + 0.4 ms/tick |
| placed-distance verification per tick | runtime `get_model` checks | verify once in a headless smoke (probe F pattern) | per-tick reads are the documented perf trap (PITFALLS perf table) |
| sweep-angle re-derivation in bridge | parse engine internals | `angle_signed/TURN_TICKS` passed from controller from the sweep state | engine already computed the sign; bridge stays dumb |
| delete/reload objects each sweep tick | any rebuild | incremental rotate | drift 3.7e-06 Å/sweep — see Open Questions for the (non-)issue |
| collision checks vs viewer geometry | `get_extent`/ray casting per tick | engine 2D math on tracked records (existing `_point_segment_distance_sq` etc.) | already built; viewer never queried |

## Common Pitfalls

### P5-1: Manifest `ring_atoms` are NOT ring-order — `ring_frame` rejects them directly
**What goes wrong:** `stacking.ring_frame(atoms, manifest['ring_atoms'])` raises `ValueError('non-planar ring (max deviation 1.133 A)')` for **benzene** (deviation 1.133 Å), and biphenyl (12-atom, twisted two-ring set) cannot form a planar frame at all (1.595 Å).
**Why:** `ring_frame` requires ring indices **in bond order** (Newell normal is order-stable but order-SENSITIVE for scrambled orders); the manifest stores sorted index sets (`[0..5]`, `[0..13]`, biphenyl `[0..11]` spanning both rings). Naphthalene/anthracene/phenanthrene's sorted sets happen to pass only by luck of atom numbering.
**How to avoid (REQUIRED new pure helper):** derive a single ring cycle from the bond graph at load: `molfile.find_ring_atoms(record)` → DFS single-cycle traversal (working prototype in both probe scripts this phase; ~20 lines, deterministic via sorted-neighbor walk). Feed cycle to `ring_frame`. For biphenyl this yields ONE phenyl ring — matching the stacking.py docstring intent ("biphenyl lists ONE ring's atoms"), and flags the **manifest biphenyl `ring_atoms` (12 entries) as DATA BUG** to fix or tolerate via the DFS reduction.
**Warning signs:** ValueError 'non-planar ring' at game start for benzene pickups (the FIRST molecule anyone tests!).
**Confidence:** HIGH — reproduced pure-WSL this session.

### P5-2: `cmd.get_object_ttt` segfaults; TTT display matrices are write-only
Carried from 04 probe M5: never read back object transforms; all needed state lives in the engine/pure layer. `transform_object`/rotate/translate write **atomic coordinates** — `get_extent`/`get_model` are safe read-backs (probe G).

### P5-3: Completion zoom BEFORE unlock is silently lost
`unlock_camera` → `set_view(saved)` clobbers an earlier `zoom`. Zoom AFTER teardown (Pattern 4).

### P5-4: `cmd.rotate` without `origin=` rotates about the **current view center**, not the head
`editing.py:1807-1808`: `origin=None` → view origin. Any pivot rotation MUST pass `origin=[hx,hy,0]` explicitly (probe B/A2 both pinned the real pivot). Also pass `camera=0` — `camera=1` would rotate about a camera-space axis (same desync class as translate, gameloop pitfall 4).

### P5-5: Sweep deletions must not happen mid-sweep; pattern deletes cover everything
`cleanup_srp()` pattern-deletes `srp_*` — all pickup/segment objects included by naming (verified pattern semantics in G4 + 03 smoke). No code change needed; just keep the `srp_` naming on every spawned object. Epoch guards already handle stale timers.

### P5-6: Spheres vdW overhang vs box z-depth (the 03-08 question, now with numbers)
Not a code bug — a render-depth decision (see Open Questions). The box CGO is display-only, but with spheres rep the overhang is user-visible.

### P5-7: `transform_selection` regenerates representations automatically — but ONLY for real molecular objects
CGO objects are not transformed (probe C2: harmless inclusion). Selection strings are cheap; no need to exclude `srp_box` from the sweep selection (defensive: still fine to use an explicit ` or `-joined molecule list).

### P5-8: Pre/post translation order is easy to swap
If a future edit moves the translation into the wrong slot, placement lands ~2×target-translation away. Locked by the probe matrix builder pattern: build `m16` in ONE pure helper, unit-test its 16 floats against a hand-computed case (R=RotZ90, t=(1,2,3)) — the probe A1 case is the fixture.

## Code Examples (verified this session)

### Matrix builder (the ONLY layout PyMOL accepts for R,t)
```python
def matrix_rt(R, t, pre=(0.0, 0.0, 0.0)):
    \"\"\"Verified A1/A2: rows 0-2 cols 0-2 = row-major R applied to the
    column vector; col 3 = post-translation (applied AFTER R); bottom row
    = pre-translation (added BEFORE R). y = R.(x + pre) + t.
    For stacking place_pickup (R,t): pre = (0,0,0).
    For pivot rotation about O: pre = -O, post = +O.\"\"\"
    return [R[0][0], R[0][1], R[0][2], t[0],
            R[1][0], R[1][1], R[1][2], t[1],
            R[2][0], R[2][1], R[2][2], t[2],
            pre[0], pre[1], pre[2], 1.0]
# cmd.transform_selection(sel, m16)  -> max err 1.2e-07 A (probe A1)
```

### One rigid sweep tick
```python
# 10 objects including head + CGO box in selection: rigid, 0.38 ms (probe B/E1)
cmd.rotate('z', delta_deg, 'srp_head or srp_seg0 or srp_seg1', camera=0,
           origin=[hx, hy, 0.0])
# delta_deg > 0 == CCW, same sign convention as engine _rotate_xy/start_sweep
```

### Edge-on one-shot at load (probe F)
```python
centroid_s, normal_s, ref_s = stacking.ring_frame(atoms, ring_cycle)
r2 = cross(normal_s, ref_s)
B = (ref_s, r2, normal_s)                      # stored basis columns
C = ((0.0,0.0,1.0), (0.0,1.0,0.0), (1.0,0.0,0.0))  # r1->+z, r2->+y, n->+x
R_edge = C . B^T                                # pure 3x3 helper
cmd.transform_selection(name, matrix_rt(R_edge, (0,0,0), pre=neg(centroid_s)))
# benzene z-span after edge-on == pure-layer prediction 4.962 A (exact match)
```

## Performance Guardrails (measured)

| Operation | Measured (headless, Windows conda PyMOL 2.5.0) | Budget |
|---|---|---|
| one multi-object `cmd.rotate`, 10 objects | 0.38 ms | 100 ms tick |
| 10× per-object `cmd.transform_object` equivalent | 0.04 ms | — |
| 10× per-object `cmd.rotate` | 0.31 ms | — |
| worst v1 object count | cap≤20 → ≤20 segments + head + box + pickups ≈ ≤30 objects | trivial |
| worst v1 atom count | cap≤20 mol × ≤24 atoms (anthracene/phenanthrene) + head ≈ 504 atoms; defaults (cap 10) ≈ 264 | atom_budget=100 warn (SETUP-06; hessian ~N³ — PITFALLS perf table; SPECTRA-06 owns calibration) |

GUI-thread redraw cost is NOT measured (headless) — the only perf residual; rotate GUI-smoothness is a human-verify item at 04-style UAT, but 0.4 ms of cmd time leaves ~99 ms for redraw.

## Verification Plan

| Claim | Status | How to re-verify during execution |
|---|---|---|
| matrix layout (R row-major, col-vec, pre/post slots) | HEADLESS-VERIFIED (A1 1.2e-07, A2 2.4e-07) + source (editing.py:1962-1988) | keep probe A1 fixture as a smoke step |
| one-call multi-object rigid sweep | HEADLESS-VERIFIED (B: centroid+internal+z all < 5e-07) | smoke: 3-object chain, 90° sweep, extent/centroid asserts |
| sweep sign (CCW positive == engine CCW) | HEADLESS-VERIFIED (B expected-value match) | assert seg1 centroid lands at rotated position |
| wildcard + CGO-harmless rotate | HEADLESS-VERIFIED (C1/C2) | keep in smoke |
| incremental-sweep drift | HEADLESS-MEASURED 3.72e-06 Å per 90° sweep | not a bug; document; if ever worried, mirror via absolute-angle rotates computed from the pure layer |
| placement end-to-end (3.6000 Å) | HEADLESS-VERIFIED (F2), pure-placed == viewer (F5, 0.00 sorted/rounded) | replicate in the phase smoke with the real dataset values |
| clash gate on placed coords | VERIFIED clear for benzene pd-stack (F3) — feed ENGINE placed atoms, never stored SDF coords | unit: check_clash(placed, segment_atoms) in controller test |
| completion ops (disable/zoom/pattern-delete/merged get_model + extent) | HEADLESS-VERIFIED (G1-G4) | completion-flow smoke |
| `cmd.set_name` (pickup→segment rename) | NOT PROBED — bog-standard API (naming.py); fallback delete+reload equally fine | one smoke line |
| rotate-side redraw smoothness at 10 Hz in real GUI | NOT MEASURED (headless) | human-verify UAT |

## Open Questions (for the user / planning decisions)

1. **BOX_DISPLAY_Z decision (03-08 Option A 5.0 vs Option B 6.0) — NOW WITH DATA.** Edge-on z-spans (atom centers), canonical `r1→z` choice per the Pattern-1 scheme — but the vn choice of WHICH in-plane axis is vertical matters:

   | molecule | span r1 | span r2 | best (long axis lateral) | +2×1.70 vdW |
   |---|---|---|---|---|
   | benzene | 4.962 | 4.297 | 4.297 | 7.697 |
   | naphthalene | 7.079 | 5.547 | 5.547 | 8.947 |
   | anthracene | 9.207 | 6.770 | 6.770 | 10.170 |
   | phenanthrene | 7.144 | 8.122 | 7.144 | 10.544 |
   | biphenyl | 9.198 | 4.317 | 4.317 | 7.717 |

   - Worst atom-center z-span with **long-axis-lateral** orientation: **7.144 Å (phenanthrene)** → fits 2·5.0=10.0 with 2.86 Å slack; **+vdW spheres = 10.54 → pokes out 0.27 Å/side at BOX_DISPLAY_Z=5.0**, fits 12.0 cleanly.
   - Worst with naive ref-vertical: 9.207 (anthracene) → 12.6 incl. vdW — exceeds BOTH options. (This is the 03-08 "0.474 Å slack" configuration, atom centers only.)
   - **Recommendation to user:** orient long-axis-lateral (rotate about the normal at canonicalization so the longer of span r1/r2 lands lateral) and keep **Option A (5.0)** if the 0.27 Å/side spheres overhang is acceptable, else **Option B (6.0)** guarantees even the anthracene-24-atom spheres stay inside. Dataset cycles allow either; the pure helper computes spans per molecule from the SDFs, so the orientation rule is data-driven, not hardcoded.
2. **Manifest biphenyl `ring_atoms` (12 atoms, non-planar):** fix data (list one ring's 6) or tolerate via the DFS single-cycle reduction (prototype works). Recommend a data fix + loader note; but the pure helper should still derive order from bonds (P5-1) rather than trusting manifest order.
3. **Stack side:** new segments attach behind the nearest-chain end along −heading (snake-canonical) — confirm vs "stack behind head" UX intent.
4. **Segment object naming:** `srp_pickup_<id>` → rename to `srp_seg_<n>` at capture (cheap) or delete+reload (simple)? Rename keeps the atom set identical to what the player saw; either is pattern-safe for cleanup.

## Sources

### Primary (HIGH confidence)
- Headless probe `tmp/p5_pymol_probe.py` run 2026-09-15 via `C:\src\run-conda-pymol.bat -cq` — all PROBE-PASS lines quoted above (A1/A2/B/C1/C2/E1/E3/F1/F2/F3/F5/G1-G4) and the D-drift measurement (3.72e-06 Å).
- `pymol-src/modules/pymol/editing.py:1610-2050` — translate/rotate/transform_selection/transform_object/set_object_ttt source, incl. the exact TTT construction in `rotate` (lines 1815-1819) and the transform_selection docstring semantics (1962-1988).
- WSL pure probe `/tmp/opencode/p5_extents_pure.py` using shipped `serpentrum/molfile.py` + `serpentrum/stacking.py` over committed SDFs — all extent numbers and the P5-1 ring-order failure reproduction.
- 04-RESEARCH-gameloop.md probe carries: M3 (translate zero-drift), M5 (get_object_ttt segfault), C2 (default view down −z).

### Secondary (MEDIUM confidence)
- `cmd.set_name` rename availability (standard API, unprobed — trivially smoke-testable).
- GUI redraw cost of rotate at 10 Hz (headless gives no redraw timing) — human-verify item.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — every command headless-verified or source-read
- Architecture: HIGH — patterns are thin wrappers over verified primitives
- Pitfalls: HIGH (P5-1/P5-4 source+probe; P5-2 prior probe; P5-3 source semantics)
- Performance: HIGH for cmd-call timings (measured); MEDIUM for GUI redraw (unmeasured)

**Research date:** 2026-09-15
**Valid until:** single PyMOL version (2.5.0 pinned) — no drift expected; re-verify only if the PyMOL build changes
