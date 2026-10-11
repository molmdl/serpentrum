# Phase 9: Random Line-Wall Spawning — Engine & Policy Research

**Researched:** 2026-10-12 (UTC)
**Focus:** pure engine layer + game-rules policy — wall state, spawn policy, collision semantics, determinism, lifetime, event wiring, test impact
**Companion researcher:** bridge/CGO/visibility half (drawing, colors, smokes) — this document specs the SEAMS that half consumes, not the drawing itself
**Confidence:** HIGH (every claim verified against live source with file:line; verified-baseline probes run on WSL python3.6)

**Owner request (verbatim, 2026-10-11):** "improve gameplay experience by random spawn line as wall-within-box after picking up a mol, at the same time as the spawn of the next mol. the line-wall should not overlap with the newly spawn mol."

---

## 1. Verified current behavior (file:line evidence)

### 1.1 Engine referee: exact event order and gating points

`serpentrum/game_engine.py` `GameEngine.step(dt)` (line 557) processes in this fixed order:

| # | Leg | Code | Event emitted |
|---|-----|------|--------------|
| 0 | paused / finished early return | :631-634 | `[]` |
| 1 | sweep-in-progress early return | :636-637 | `('turning', tick/total)` via `_advance_sweep` (:478-527) — **no forward motion, head does NOT move during sweeps** (head is the rotation pivot, :502; verified head-fixed) |
| 2 | pending-direction application | :643-656 | sweep tick 1 or fall-through |
| 3 | movement + train-follow | :657-668 | `('moved', (nx, ny))` |
| 4 | **boundary crash (head-only)** | :673-684 | `('crashed', 'boundary')`, `finished=True`, `result='crashed'`, `pending=[]`, return |
| 5 | **body crash (head-only)** | :688-702 | `('crashed', 'body')`, same end-state, return |
| 6 | pickup capture | :707-735 | `('stacked', pickup)` (:720), then optional `('budget_warning', n)` (:722-726), then optional `('won',)` (:728-734) |

Verified semantics that Phase 9 builds on:

- **Boundary binds the HEAD ONLY at straight-motion ticks.** The check reads only the post-move head `(nx, ny)` (:676-679); the chain is never boundary-checked (owner directive 2026-09-19d — STATE.md:87; game_engine.py docstring :21-24, :56-62). Comparison is INCLUSIVE at the margin-adjusted walls, `BOUNDARY_MARGIN_A = 1.0` (:110), pinned by test_engine_rules.py:105-125.
- **Body collision is head-centroid vs polyline edges, STRICT `<`:** `_point_segment_distance_sq` (module-level, :120-151, degenerate segment handled :135-139) against `BODY_COLLISION_RADIUS_A = 2.0` squared (:105, :691), edges `range(0, n - 1 - SEGMENT_SKIP_RECENT)` with `SEGMENT_SKIP_RECENT = 2` neck exemption (:108, :689). Pinned by test_engine_rules.py:185-335 (incl. exactly-at-radius no-crash :272-285, boundary-over-body precedence :302-323, crash-stops-processing :589-608).
- **Crash legs are head-only, and sweeps return early** — the head cannot approach anything during a sweep. The 180° key is the ONLY turn veto (request_direction :369-423; start_sweep always opens :425-476). The swept pre-check is deleted entirely (docstring :25-33, :116-117).
- The engine has **NO RNG, no wall-clock** (docstring :64-69) — GAME-07 determinism by construction: same ctor args + same call sequence ⇒ identical state/events.

### 1.2 Head + wall-adjacent state representation today

- Head: `self.head = (x, y)` float tuple on the movement plane (xy); z is display-only and lives inside atom records (:297, docstring :47-54, :183-187).
- Box: `box_min`/`box_max` 2-tuples or None (:303-304). None disables boundary checking.
- Pickups: copied record dicts with REQUIRED `atoms` (:350-367); engine-owned state `live_pickup_ids` set + counters (:307-315). The engine has **no spawn API**: the GUI controller appends spawn results to `engine.pickups` / `live_pickup_ids` / `pickups_remaining` directly (gui_game.py:1208-1213, 1251-1253) — "same record shape, engine-owned thereafter".
- `reset()` rebuilds ALL state (:269-315) — currently no wall anywhere (`grep -n wall serpentrum/game_engine.py` → only boundary "wall" phrasing for the BOX walls).
- Crash reasons exist ONLY as the `('crashed', reason)` payload; `result` is the unstructured `'crashed'`/`'won'` (:235-236). The GUI's handler is generic: `self._log('crashed into %s' % ev[1])` (gui_game.py:770-772) — ANY reason string renders with ZERO handler edits.

### 1.3 Pickup spawn machinery (the "next mol" call chain)

**Construction + first spawn** (begin_game): `begin_game` (gui_game.py:363) → `_build_engine` (:477) → `PickupSpawner(records, box, spawn_mod.seed_from_setup(setup), atoms_by_id)` (:520-522) → `spawner.first((0.0, 0.0), 'right')` (:526) → `build_pickup_seed` (:529-530) → `GameEngine(pickups=[seed])` (:532-538) → begin_game materializes viewer objects (:436-442).

**Respawn chain** (after every capture resolution): `_on_tick` (:685) → `engine.step(TICK_DT)` (:694) → event dispatch (:697-701) → `'stacked'` → `_handle_stack_event` (:900) → resolution (skip/place/refuse) → `spawner.note_resolution(mol_id, refused=(status=='refused'))` (:1155-1159) → **`_respawn_pickup(session, engine)` (:1160)**. A second call site fires on the exhaust-cooldown resume edge in `_on_tick` (:727-732).

`_respawn_pickup` (:1205-1257): gates on `can_spawn(len(engine.live_pickup_ids))` (`MAX_LIVE_PICKUPS = 4`, spawn.py:107) → builds `chain_atoms` (head mirror + segment atoms, :1224-1226) and `live_centroids` (:1227-1228) → `spawner.next_after(engine.head, _heading_name(engine.heading), chain_atoms, live_centroids)` (:1229-1231) → on None: DBG-note + return, **no state advance** (05-03 contract, :1232-1243) → on success: append seed to engine + `materialize_pickup` (:1244-1257).

**Spawn policy internals** (spawn.py): private `random.Random(seed)` (:281); `seed_from_setup` = `zlib.crc32` over sorted `key=%r` items (:198-210; cross-process pinned by test_spawn.py:174-187). `_spawn` (:445-476): order-empty guard, cooldown guard, heading validated-but-unused, up to `MAX_DRAWS = 32` seeded per-axis uniform draws over the shrunk box (:463-471), then `_grid_scan` fallback (:478-516, seeded `randrange` start :508, degenerate-box guard :503-506). `_legal` legs (:518-569): wall margin 3.5 Å, box-proportional min head distance (factor 0.35, floor 5.0, cap 0.8×h — :108-115, :287-294), chain-atom clearance 3.0 Å per-atom, live-pickup centroid clearance 6.0 Å. Demote-after-refuse + resumable `EXHAUST_COOLDOWN_TICKS = 100` cooldown (:125-130, :347-406) is fully decoupled from geometry.

**Draw-order contract captured in the seed stream:** each spawn consumes exactly 2 uniform draws per attempt and (only on fallback) one randrange (game_engine-neither knows nor cares; test_spawn.py pins relative same-seed equality only — no absolute position pins anywhere: verified all 13 pin groups are relative/derived, e.g. TestDeterminism :190-225, TestGeometry :228-378, TestFallbackOffset :697-770).

### 1.4 Engine→GUI event flow (no queue; synchronous return lists)

- `step(dt)` RETURNS the event list; the GUI dispatches in order within the same 100 ms tick (gui_game.py:694-701). There is no event queue, no deferred delivery.
- Controller-initiated state changes (spawn, attach, reject) emit NO engine events in either direction — the controller acts at call time and logs via returned tuples (`reject_pickup` RETURNS `('refused', id, reason)`, game_engine.py:770-824; attach_segment returns None :751-768). This is the exact pattern the wall seam must copy: **the engine is state-only for controller writes.**
- `'turn_refused'` is a DEFENSIVE-ONLY handler today (gui_game.py:756-765) — the engine emits no such event.
- Completion: `_end_run` (gui_game.py:1382-1402) → `_teardown_round` (:1482-1530; pattern-deletes `srp_pickup_*` only, :1524) → `_present_completion` (:1406-1475; `hud_logic.completion_lines(engine.result, ...)` — result is `'crashed'`/`'won'`, the crash REASON never reaches the presenter). Win and crash share this identical path (locked decision 8).
- SRP_DEBUG crashed trace is generic over the payload: `_dbg_event(engine, 'crashed', result=ev[1])` (gui_game.py:772).

### 1.5 End-of-run / restart / cleanup lifecycle

- `rebuild_scene` (gui_game.py:161-205) runs `pymol_bridge.cleanup_srp()` FIRST (:194) — deletes EVERY `srp_*` object (pymol_bridge.py:129-143, pattern `cmd.delete('srp_*')`). Any wall object named `srp_wall` is therefore purged at restart/completion-restart by the existing sweep, with zero new cleanup code.
- `begin_game` tears down FIRST (:397), rebuilds the scene, then `_build_engine` constructs a FRESH engine + spawner — engine wall state does not survive a begin_game by construction. The only place wall state can linger is inside a live engine object, which dies with the session.
- Every game builds a fresh `PickupSpawner` (seeded from the setup, deterministic) — restart replays the identical spawn sequence for identical play (GAME-07 restart semantics, _on_restart :1359-1380 + 5.1-05 note :1366-1371).

### 1.6 Purity, gates, and pinned source-scan constraints

- Purity classes (tools/check_purity.py:72-84): GUI_MODULES = {gui.py, gui_setup.py, gui_game.py, xtb_runner.py, gui_plot.py, gui_spectra.py}; BRIDGE_MODULES = {pymol_bridge.py, input.py}; **everything else defaults PURE (:95-103)** — a new stdlib-only `serpentrum/wall.py` is auto-classified PURE, zero checker edits (spawn.py precedent).
- Gate 3 discovers `tests/test_*.py` by pattern (tests/run_gates.py:137-144) — new test files auto-join the suite.
- **Active pins Phase 9 must not break:**
  - test_hud_content.py:828-892 (`TestGuiSpawnCallSites`): gui_game.py source must keep EXACTLY ONE `spawn_mod.PickupSpawner(`, ONE `spawner.first(`, ONE `spawner.next_after(`, ONE `spawn_mod.seed_from_setup(`, and contain NO `min_head_dist_a` string, and keep `_heading_name(engine.heading)`.
  - test_hud_content.py:895-939 (`TestDebugTailBinding`): the `_handle_stack_event` body slice (from `def _handle_stack_event` to `def _dbg_capture_line`) must contain EXACTLY TWO `debug_tail = None` — additive lines are safe; removing/reordering the existing ones is not.
  - test_hud_content.py:355 + test_placement.py:234: `REFUSE_WALL` must stay absent from `placement.__dict__` — Phase 9 must NOT reintroduce any wall placement-refusal taxonomy.
  - test_hud_content.py:725-738, 798-810: exactly one `generic_consent_note(` / one `speed_note(` call site in gui_game.py.
  - test_gui_pins.py:185-206: gui_game.py source pin that the gameplay head path routes through `effective_head_id` (additive-safe).
- Placement gate is atom-clash ONLY (placement.py:204-219 — box args retained but unbounded since 2026-09-20c); walls are NOT and must not become a placement-refusal concern.

### 1.7 Baseline verification (2026-10-12, WSL python3.6.9)

Scoped unittest runs, all green, unmodified: `test_engine_rules` 28 OK; `test_engine_core` 17 OK; `test_spawn` 41 OK; `test_phase5_integration` 9 OK (s1–s9). Full-battery reference: 995 unittests + 11/11 required smokes green at HEAD (STATE.md:13-15, 2026-10-11 quick-003).

---

## 2. Design contracts for Phase 9

Everything below is the implementable spec derived from §1. Constants are DRAFT defaults for the owner feel-check (see §3) — the NAMES and SEAMS are the research's firm recommendation; the VALUES are owner-retunable by design (single-data-line retune, 5.1 SPEED_TIERS precedent).

### 2.1 C1 — Wall state (pure engine)

- **Representation:** a single open-ended line segment on the movement plane: **`engine.wall = None or ((ax, ay), (bx, by))`** — plain float 2-tuples of 2-tuples, same coordinate frame as `head`/`box_min`/`box_max` (absolute box xy; NO z — z is display-only, game_engine.py:47-54). No thickness in engine state; thickness comes from the collision radius constant.
- **Collision constant:** add **`WALL_COLLISION_RADIUS_A = 2.0`** to game_engine.py (same VALUE as `BODY_COLLISION_RADIUS_A` :105, deliberately an INDEPENDENT name so the owner can retune wall feel without touching body feel — the BOUNDARY_MARGIN_A "one name per margin" discipline, :102-110). Collision check: `_point_segment_distance_sq(nx, ny, ax, ay, bx, by) < WALL_COLLISION_RADIUS_A ** 2` — STRICT `<` and degenerate-segment-safe via the existing module-level helper (:120-151). One constant, one collision language: "the head's clearance against solid geometry is 2.0 Å".
- **API (state-only, controller-written, mirroring attach_segment :751-768):**
  - `set_wall(endpoints)` — stores `((float(ax), float(ay)), (float(bx), float(by)))`; returns None; emits NO events.
  - `clear_wall()` — sets `wall = None`.
  - `reset()` gains `self.wall = None` (:269-315 state-rebuild) + an optional `wall=None` keyword on `__init__`/`reset` (test seam; both signatures are keyword-friendly by contract :262-263; additive kwarg breaks no caller — verified no exhaustive `__dict__` pins in test_engine_core.py:61-110, 217-259).
  - The wall NEVER translates with the train and NEVER rotates with sweeps — it is environment, like the box.

### 2.2 C2 — Collision semantics (crash leg)

- **Class:** GAME-05 crash — hitting a wall ends the run, snake stays complete → spectra. Event `('crashed', 'wall')`, `finished=True`, `result='crashed'`, `pending=[]`, identical end-state code to boundary/body (game_engine.py:673-702).
- **Referee slot:** **after boundary, before body** — new order: `moved → boundary → wall → body → stacked → won`. Rationale: environment collisions first (boundary, then wall) then self; the slot uses the IDENTICAL gating point as the boundary check (post-move `(nx, ny)`, straight-motion ticks only) leaving the pinned boundary/body legs and their precedence tests untouched (test_engine_rules.py:302-323 boundary-over-body stays green — wall slots BETWEEN them, boundary-over-wall and wall-over-body get NEW pins).
- **Sweep interplay (D-WALL-SCOPE, recommended default head-only):** the wall binds the HEAD ONLY. Proof of completeness: the head does not move during sweeps (step early-return :636-637; `_advance_sweep` never touches `self.head`, :494-527), so a head-only check at moved ticks can never miss a crossing; the chain may visually swing/clip through a wall exactly as it may clip the box and its own body (owner philosophy 2026-09-19b: "a silly outcome is recoverable, a frozen snake is not"; head-only box binding precedent 2026-09-19d, STATE.md:83/:87). NO change to placement.gate (walls are not placement concerns — pin at test_hud_content.py:355).
- **Same-tick capture tie:** the wall check precedes pickup capture, so a tick that both crosses a wall and reaches a pickup crashes (identical tie semantics to boundary, test_engine_rules.py:589-608). The spawn-clearance legs (C3) make this rare and fair.
- **GUI surface cost: ZERO for the crash path.** `_handle_event`'s `crashed` branch is payload-generic (`'crashed into %s'`, gui_game.py:770-772) → logs "crashed into wall" with no edit; `_end_run`/`_present_completion` run on `engine.result` (generic, :1382-1475); `hud_logic.completion_lines` takes `result` only (hud_logic.py:247-261); the SRP_DEBUG trace is generic (:772). No HUD builder changes required for the crash class.

### 2.3 C3 — Spawn policy (new pure module)

- **Module:** new **`serpentrum/wall.py`** (stdlib `math`/`random`/`zlib` only — auto-PURE per check_purity.py:95-103; spawn.py docstring-precedented style). Do NOT extend `spawn.py` or `PickupSpawner`: isolation is the requirement (question 8) — spawn.py stays byte-identical so the 2026-09-19b/c demote/cooldown machinery ships untouched by construction, and the verified "signatures unchanged, gui zero-edit" contract from 5.3 (ROADMAP.md:226, SC4) stays intact.
- **Class `WallSpawner(box_min, box_max, seed, wall_box_margin_a=None, wall_head_clearance_a=None, length_fraction=None, max_draws=WALL_MAX_DRAWS)`** with read-only properties mirroring the spawner introspection pattern (spawn.py:328-345). Draw contract (3 draws per attempt, pinned order):
  1. `cx = rng.uniform(-(B - m), B - m)`, `cy = same` (anchor = wall CENTER; `B` = per-axis half-extent, `m = WALL_BOX_MARGIN_A`)
  2. `theta = rng.uniform(0.0, math.pi)` (orientation; see D-WALL-ORIENT)
  3. endpoints = anchor ± half-length along `(cos θ, sin θ)`, length = `WALL_LENGTH_FRACTION × minor-axis span` (fixed per attempt)
- **Clearance legs** (a candidate failing ANY leg is redrawn, up to `WALL_MAX_DRAWS = 32`; then None):
  - **L1 Endpoint inset (MANDATORY, fairness):** both endpoints ≥ `WALL_BOX_MARGIN_A` (default 6.0) from every box face. Guarantees each wall end leaves a passable corridor: free corridor width = margin − boundary margin (1.0) − wall halo (2.0) = 3.0 Å at 6.0 margin (5.0 Å at 8.0) — probe-checked below. With one-at-a-time walls (C4) a convex box can NEVER be split into disconnected regions: both ends are always roundable.
  - **L2 New-mol no-overlap (OWNER MANDATE, made precise):** every TRANSLATED atom of the newly spawned molecule keeps ≥ `CHAIN_ATOM_CLEARANCE_A` = 3.0 Å (spawn.py:118 precedent value) distance from the wall segment, using point-segment math. "Overlap" is thus DEFINED as: any mol atom within 3.0 Å of the wall line. (Per-atom, not centroid: molecules are multi-Å lattices — the centroid form would allow a mol straddling the line.)
  - **L3 Head clearance (fairness):** head-centroid to wall-segment distance ≥ `WALL_HEAD_CLEARANCE_A` (default 12.0). Arithmetic: at expert tier 13.0 Å/s = 1.3 Å/tick (quick-003 tiers, STATE.md:101), a dead-ahead wall at 12.0 Å gives 9.2 ticks; an immediate perpendicular key costs 1 (turn applies at next tick, 04-09 note STATE.md:80) + 6 (sweep, TURN_TICKS :89) = 7 ticks before the head stops advancing toward it → ≥ 2.2 ticks (~0.22 s) reaction slack at expert, ~6.3 ticks (0.63 s) at the 9.0 default. A wall can never spawn ON the head's imminent path (would be an unfair instant death — mirrors 5.3's min-head-distance floor rationale).
  - **L4 Live-mol clearance (recommended, prevents "silly" walling-in of standing mols):** every atom of every OTHER live pickup keeps ≥ 3.0 Å from the wall segment.
- **None semantics:** on exhaustion return None and **keep the previous wall** (no despawn, no change) — the benign degradation is v1-look play for one round. Failure is rare: probe-measured worst-case adversarial small-box acceptance 15.6%/draw at margin 6.0 → P(success in 32 draws) = 99.56% (87.3% at margin 8.0 with same draws; raise max_draws to 64 → 98.3%). NO grid-scan fallback is needed (walls are a bonus obstacle, not a required resource like pickups).
- **Draws are consumed on every attempt regardless of outcome** (simpler than the pickup spawner's state-advance rules — there is no record cycle or pid to protect); determinism holds because the call sequence is deterministic (GAME-07).
- **Wall visual geometry (bridge half, other researcher):** the PURE builder belongs in `cgo_build.py` (e.g. `wall_cgo((ax, ay), (bx, by), z_extent, color, linewidth)` alongside `box_cgo` :75-131) and the BRIDGE loader in `pymol_bridge.py` (e.g. `load_wall` / `delete_wall`, object name `'srp_wall'` — inside SRP_PREFIX so `cleanup_srp` sweeps it, pymol_bridge.py:61, :129-143). z-extent is the other researcher's call (on-plane line at z=0 vs vertical fence at ±`BOX_DISPLAY_Z` = 5.0, :66); the ENGINE is xy-only and indifferent.

### 2.4 C4 — Lifetime contract

- **One live wall at a time (default; D-WALL-LIFETIME):** each successful wall spawn REPLACES the previous wall — engine `set_wall` overwrites; bridge does delete-then-load (`srp_wall`). Box-filling arithmetic for the alternative: a cap-10 game yields ≤ 9 wall-spawn events (captures 1–9 spawn mols 2–10; capture 10 wins) — 9 accumulated ~30 Å walls on the small ±35 box (70 Å span) would leave no navigable lattice; accumulation is rejected by arithmetic, revisit only as an explicit owner escalation (e.g. tier-dependent count).
- **Win-tick guard:** on the cap-reaching capture the engine is ALREADY `finished=True`/`result='won'` during `'stacked'` event dispatch (step() sets it before returning the event list — probe-verified §5; note `_respawn_pickup` currently does NOT guard this and materializes a doomed pickup on the win tick, gui_game.py:1244-1257, harmless because teardown pattern-deletes `srp_pickup_*` :1524 — a wall would NOT be swept there). The wall seam MUST guard `if engine.finished: return` — this also prevents a wall flashing onto the completion screen.
- **At crash/win (completion):** default — the wall STAYS as environment scenery (like `srp_box`, which teardown does not delete; `_teardown_round` touches only `srp_pickup_*`, :1524) and vanishes at the next `begin_game` via `rebuild_scene`'s `cleanup_srp` (:194). This keeps the crash cause visible on the completion board. (D-WALL-TEARDOWN offers the alternative: pattern-delete in `_teardown_round`.)
- **Restart:** NO explicit engine reset hook needed — `begin_game` constructs a fresh engine (wall=None via reset) + fresh `WallSpawner` (same seed ⇒ same wall sequence). The only engine edit is `reset()` initializing `self.wall = None` (C1).
- **Pause:** wall spawning happens inside the `'stacked'` event handler, which never runs while paused (paused `step()` returns `[]`, :631-632) — no pause interplay to design.

### 2.5 C5 — Determinism (GAME-07)

- **Decision: SEPARATE derived stream (option b, recommended).** `wall.py` gets its own private `random.Random` seeded by a derived seed:
  ```python
  WALL_SALT = 'wall-v1'   # bump to rotate the wall stream only
  def wall_seed_from_setup(setup):
      return zlib.crc32(('%d|%s' % (spawn.seed_from_setup(setup),
                                    WALL_SALT)).encode('utf-8'))
  ```
  (imports spawn for the canonical crc32 string only — spawn.py is fully decoupled, :88-93.) The seed-derivation stability pin mirrors test_spawn.py TestSeed incl. the cross-process subprocess probe (:174-187).
- **Rationale vs the shared-stream alternative (option a):**
  1. **Verified-contract preservation:** 5.3's shipped + verified contract is `PickupSpawner.__init__/first/next_after` signatures unchanged and gui_game zero-edit for spawns (ROADMAP.md:224-226, 5.3-04's zero-edit verdict, test_hud_content.py:828-892 pins). A shared stream forces a shared-RNG injection = a signature change = breaking a verified SC by design.
  2. **Behavioral stability:** pre/post-Phase-9, the SAME setup replays IDENTICAL pickup sequences (the 5.3 owner-approved feel stays comparable at the Phase-9 feel-check; no confound between "walls changed the game" and "spawns silently moved").
  3. **Maintenance isolation:** with a shared stream, any future change in wall draw count (e.g. D-WALL-ORIENT retunes, added legs) rotates every downstream pickup position — a silent cross-feature regression channel. Separate streams make wall-policy edits provably pickup-neutral (and vice versa).
  4. 5.3-05's own impact analysis (5.3-05-SUMMARY.md:115-117) treats stream-shape changes as "acceptable but needing re-proof" — separate streams avoid the re-proof class entirely.
  - Note honestly: existing test_spawn.py pins would survive EITHER option (they are relative/derived, §1.3) — the separate stream is chosen for the production-behavior and isolation reasons above, not to save tests. If a pin legitimately needs to change someday, the 5.3-02 sanctioned seed-swap precedent (STATE.md:44, seed pair 4242/163 documented in-test) is the procedure.
- GAME-07 restated for Phase 9: same setup + same call sequence ⇒ identical (pickup positions, wall endpoints) sequences — two streams, one contract.

### 2.6 C6 — Event surface & GUI wiring (the seam)

- **No new engine event types for spawn/despawn.** The controller initiates like it does for pickups today (gui_game.py:1208-1213): in `_respawn_pickup`'s SUCCESS branch (after the pickup materializes, :1244-1257), guarded by `not engine.finished`:
  1. `wall = wall_spawner.next_wall(engine.head, seed_atoms_translated, live_pickup_atoms)` — inputs ALREADY assembled in `_respawn_pickup` (chain_atoms :1224-1226, live centroids :1227-1228; add the new pickup's translated atoms from the freshly built `seed`).
  2. on None → return (old wall persists).
  3. on result → `engine.set_wall(wall)`; `pymol_bridge` delete+load `'srp_wall'` with the CGO; optionally store `session['wall']` for the DBG trace.
- This placement automatically gives the owner's exact pairing — "at the same time as the spawn of the next mol" — at BOTH `_respawn_pickup` call sites (capture resolution :1160 AND cooldown-resume edge :727-732), and it inherits the right cadence: no mol spawn (MAX_LIVE gate / cooldown pause with the None path) ⇒ no wall swap.
- **Session/`_build_engine` additions:** construct the `WallSpawner` in `_build_engine` beside the `PickupSpawner` (:520-522, seed via `wall_mod.wall_seed_from_setup(setup)` — a DIFFERENT call-site string so the "exactly one `spawn_mod.seed_from_setup(`" source pin stays at 1); carry it on the session (a new `'wall_spawner'` key; session dict is additive at :405-430). No-records-anchored runs (spawner None, :511-512) degrade to no walls — box-only parity.
- **Chattiness policy (default):** wall spawn is HUD-silent, exactly like pickup spawns today (no info-box line exists for pickups; only SRP_DEBUG cooldown lines, :1237-1242) — the visible geometry IS the cue. If the owner wants a line ("a wall appeared"), it is a one-builder hud_logic addition at the seam; D-WALL-HUD. No coalescer interaction (only reason lines coalesce, :1546-1567).
- **Win-tick guard + source-scan survival:** the wall seam lines go at the END of `_respawn_pickup` — the `TestDebugTailBinding` slice covers `_handle_stack_event`→`_dbg_capture_line` and counts `debug_tail = None` == 2 (test_hud_content.py:916-937); adding lines inside `_respawn_pickup` (a method between the two defs) changes the slice content but not the counted literal — safe. New source-scan pins (5.3-04 house pattern) should pin: exactly one `WallSpawner(` construction, one `next_wall(` call, and the `engine.finished` guard, plus NO `min_head_dist_a`-named wall kwargs (test_hud_content.py:880-885).

### 2.7 C7 — Cooldown/demote machinery isolation (question 8 boundary)

- The wall seam calls ONLY `WallSpawner.next_wall` + `engine.set_wall`. It never calls `note_resolution`/`tick`/`can_spawn`, never mutates `PickupSpawner` state, and lives in `_respawn_pickup`'s success branch — AFTER the `can_spawn` gate and AFTER `next_after` succeeded, so it cannot affect any refuse/demote/cooldown path. `spawn.py` gets ZERO edits (the module is the isolation boundary — its byte-identity is checkable in review via `git diff --stat`).
- The 2026-09-19b/c behaviors (refused-despawn + round-robin demote + resumable exhaust cooldown, spawn.py:347-406) remain byte-identical by construction. During an exhaust-cooldown pause the wall stream is naturally quiescent (no mol spawns ⇒ no wall swaps); when the resume edge fires (:727-732) both spawn together — the owner's pairing invariant, by placement rather than by policy code.

---

## 3. Decision table (owner feel-check surface)

Numbered for the planner's checkpoint handoff. Defaults are the research recommendation; each is a data-line or free-parameter retune (no mechanism changes).

| # | Decision | Options | Default + rationale |
|---|----------|---------|---------------------|
| **D-WALL-SCOPE** | Wall binds head-only (chain exempt during sweeps AND straight motion) | (a) head-only · (b) chain-bound too (sweep veto) | **(a)** — mirrors the shipped head-only box rule (2026-09-19d); chain clipping is owner-accepted ("silly outcome is recoverable") vs (b) re-introducing the deleted frozen-snake class (2026-09-19b) |
| **D-WALL-CRASH** | Hitting a wall | (a) run ends, GAME-05 class, snake complete → spectra · (b) non-lethal obstacle | **(a)** — boundary/body precedent; (b) has no engine concept (no bounce/health system) and would need invented mechanics |
| **D-WALL-TRIGGER** | When the wall swaps | (a) every successful next-mol spawn (incl. after refuses/skips) · (b) only after PLACED captures | **(a)** — the owner's literal pairing ("at the same time as the spawn of the next mol"); the refuse cascade already produces those spawns; zero extra branching |
| **D-WALL-LIFETIME** | Concurrent walls | (a) one live wall, replaced each spawn · (b) accumulating | **(a)** — §2.4 arithmetic: cap-10 ⇒ ≤ 9 walls; accumulating ~30 Å walls saturates the small box; accumulation can be a future difficulty escalation |
| **D-WALL-LENGTH** | Wall length | fraction of minor-axis span: 0.35 / **0.45** / 0.55 (S/M/L ⇒ 24.5/38.5/59.5 · **31.5/49.5/76.5** · 38.5/60.5/93.5 Å) | **0.45** — reads as a real wall, never dominates a crossing; owner feel-check knob |
| **D-WALL-ORIENT** | Orientation | (a) arbitrary angle, uniform [0, π) · (b) axis-aligned (0/90°) | **(a)** — "random line" reads arbitrary; collision/draw cost identical (§2.3); (b) available if playtest feels chaotic |
| **D-WALL-CLEAR-MOL** | New-mol no-overlap radius (owner MANDATE) | per-atom distance from wall line: 2.0 / **3.0** / 5.0 Å | **3.0 Å** — matches the shipped chain-atom clearance leg size (spawn.py:118); precise per-atom definition kills all straddle cases |
| **D-WALL-CLEAR-HEAD** | Head launch-safety clearance | 8.0 / **12.0** / 16.0 Å | **12.0** — expert-speed sweep-escape arithmetic in §2.3 L3 (~0.22 s reaction slack at 13 Å/s, ~0.63 s at default 9) |
| **D-WALL-CLEAR-LIVE** | Also keep walls off OTHER standing mols | (a) on, 3.0 Å per-atom · (b) off | **(a)** — trivially cheap leg; prevents the wall slicing a standing mol (silly-but-avoidable) |
| **D-WALL-BOX-MARGIN** | Wall endpoints inset from box faces | **6.0** / 8.0 Å | **6.0** — probe: 99.56% spawn success in 32 draws on adversarial small-box states (vs 87.3% at 8.0); corridor free-width 3.0 Å (2.3 expert ticks) vs 5.0 Å — both passable; pick by feel |
| **D-WALL-RADIUS** | Wall collision radius (`WALL_COLLISION_RADIUS_A`) | 1.0 / **2.0** / 3.0 Å | **2.0** — equals body radius: one collision language, no visible unfairness; independent name for retunes |
| **D-WALL-SEED** | Wall RNG stream | (a) shared with pickups · **(b) separate derived stream** (`crc32(seed|wall-v1)`) | **(b)** — §2.5: preserves the verified 5.3 zero-edit signature contract + pre/post replay stability |
| **D-WALL-TEARDOWN** | Wall at completion screen | (a) stays as scenery, purged at restart by `cleanup_srp` · (b) deleted in `_teardown_round` | **(a)** — crash cause visible on the final board; zero new teardown code (`srp_box` precedent) |
| **D-WALL-HUD** | Info-box line on wall spawn | (a) silent (geometry is the cue) · (b) one short line | **(a)** — matches the silent pickup-spawn chattiness policy; (b) is a one-builder add if wanted |
| D-WALL-VISUAL | Color/z-extent/visibility cue | — | **other researcher's scope** (bridge/CGO half); engine is xy-only |

---

## 4. Test impact

### 4.1 Existing files — TOUCHED (edits required)

| File | Change | Why |
|------|--------|-----|
| `tests/test_phase5_integration.py` | **additive**: new scenario s10 (capture → wall spawn → wall crash → completion, derived expectations only) + docstring scenario-list line (house style — the docstring enumerates s1–s9 today, :42-48) | Phase-9 end-to-end re-proof; 5.3-03 precedent (`s9` was the 5.3 addition; "s9" is a scenario NAME in this file, not a Phase-9 reference — decoded from grep + 5.3-03-PLAN.md) |
| `tests/test_hud_content.py` (or test_gui_pins.py, the 5.3-04 pattern's next home) | **additive**: new source-scan pins — one `WallSpawner(` construction site, one `next_wall(` call, the `engine.finished` win-tick guard, no `min_head_dist_a`-shaped wall kwarg strings | 5.3-04 house pattern making the seam durable |
| `tests/test_docs_audit.py` / help-README surfaces | **only if** D-WALL-HUD flips to a line or docs mention walls (docs half — the audit pins literals together with code, quick-003 precedent) | conditional |

Additive-within-file only: the new wall seam lines in `gui_game.py` must not disturb `TestDebugTailBinding`'s slice-counted `debug_tail = None` == 2 (verified safe — the seam goes inside `_respawn_pickup`, which shares the slice region but not the literal; the existing `_respawn_pickup` already sits there, gui_game.py:1205).

### 4.2 Existing files — UNTOUCHED (verified by pin analysis + baseline runs)

| File | Reason it stays green UNMODIFIED |
|------|-------------------------------|
| `test_spawn.py` (41) | Separate stream means zero interaction; even the relative/derived pins would survive a shared stream (§2.5 note) — with (b) chosen, `spawn.py` is byte-identical, so this file trivially holds |
| `test_engine_core.py` (17) | Movement/pending/reset pins attribute-by-attribute — no exhaustive `__dict__` pin anywhere; additive `wall=None` ctor/reset kwarg is invisible to all 17 |
| `test_engine_rules.py` (28) | Wall defaults to None ⇒ all 28 pins byte-identical; new wall legs go in a NEW file (house style: test_engine_turn_veto_ghost precedent) |
| `test_engine_turns.py`, `test_engine_turn_veto_ghost.py`, `test_engine_tail_follow.py`, `test_engine_speed.py`, `test_engine_win_desync.py` | No wall input anywhere; engine wall check slots after boundary without touching the swept/pending/speed/win-desync code paths (game_engine.py:673-684 boundary block unchanged) |
| `test_phase5_integration.py` s1–s9 | Additive scenario only; s8/s9 drive `PickupSpawner` alone (unaware of walls) |
| `test_placement.py`, `test_hud_logic.py` | placement.py/hud_logic untouched by the engine-side scope (unless D-WALL-HUD flips) |
| `test_purity_gates.py` | `wall.py` auto-PURE (stdlib only — same classification basis as spawn.py); no new GUI/BRIDGE module introduced by the engine half |
| `test_gui_pins.py` | Presence-type source pins on gui_game.py — additive lines safe |

### 4.3 NEW pure-test canon (5.3-01/03 patterns — deterministic candidate generator + derived expectations)

- **`tests/test_wall.py`** (policy, mirrors test_spawn.py structure):
  - Seed derivation: `wall_seed_from_setup` stable in-process + **across processes (subprocess probe, test_spawn.py:174-187 precedent)**; changes with setup; salt distinct from pickup seed.
  - Determinism: same seed ⇒ byte-identical endpoint sequences; different seed diverges.
  - Stream isolation: a pickup spawner built alongside wall draws produces the SAME pickup sequence as one built alone (the 5.3 zero-interaction pin).
  - Legs: endpoint inset (all four faces), head clearance, new-mol per-atom no-overlap (STRADDLE case must be rejected — a wall passing near the centroid but clipping an atom), live-mol clearance, length bounds (derived from fraction × span — never hardcoded).
  - Exhaustion → None + benign keep-old-wall semantics; every constant exposed for retune; pin VALUES derived from module constants (5.1-06 derivation habit so owner retunes can't silently break tests).
- **`tests/test_engine_wall.py`** (collision, mirrors test_engine_rules style):
  - `('crashed', 'wall')` + `result='crashed'` + `finished` + `pending=[]`; run ends, snake complete.
  - Referee order: moved → wall crash → nothing after (capture suppressed on the crash tick — boundary-tie precedent); **boundary-over-wall** and **wall-over-body** precedence (fresh companion to test_engine_rules.py:302-323).
  - Strict-at-radius no-crash (mirror :272-285 with the wall); degenerate zero-length wall behaves as a point obstacle (helper :135-139).
  - Head-only scope: chain sweeps through a wall — no crash, no moved event (sweep-tick early-return proof); wall=None ⇒ event streams identical to pre-Phase-9 behavior.
  - `set_wall`/`clear_wall`/`reset` state contract; paused engine inert; win-desync interplay NONE (walls never interact with reject_pickup — pin the untouched win path).
- **`tests/test_phase5_integration.py` s10**: real-set_a chain — capture → synchronized next-mol + wall spawn (both clearances hold) → steer head into the wall → `('crashed', 'wall')` → completion-path counters (snake complete, molecules_stacked intact) → full-drive byte-identical re-run (GAME-07 end-to-end, mirroring s9's derived-bounds discipline :708-814).

---

## 5. Confirmation-by-probe (WSL python3.6.9, 2026-10-12)

| Probe | Command | Result |
|-------|---------|--------|
| Baseline: engine rules suite | `python3.6 -m unittest discover -s tests -p "test_engine_rules.py"` | **Ran 28 tests — OK** |
| Baseline: engine core suite | `... -p "test_engine_core.py"` | **Ran 17 tests — OK** |
| Baseline: spawn suite | `... -p "test_spawn.py"` | **Ran 41 tests — OK** |
| Baseline: integration chains | `... -p "test_phase5_integration.py"` | **Ran 9 tests — OK** (s1–s9) |
| Winning-tick semantics (supports C4's guard design) | inline `GameEngine(cap=1)` capture probe | `events = [moved, stacked, won]`; **`engine.finished == True` and `result == 'won'` ALREADY set when the GUI would dispatch `'stacked'`** — i.e. an `if engine.finished` guard in the wall seam provably blocks the win-tick wall |
| Wall-policy feasibility arithmetic | `/tmp/opencode/wall_feasibility_probe.py` (Monte-Carlo over adversarial small-box head/mol states, draft constants) | margin 6.0: worst-case per-draw acceptance 15.6% → **P(≥1 legal wall in 32 draws) = 99.56%**; corridor free-width 3.0 Å (2.3 expert ticks). margin 8.0: 6.2%/draw → 87.3% in 32 draws (98.3% at 64). Confirms: no grid fallback needed; misses are rare + benign (keep old wall) |
| Sweep immobility (head-only completeness) | code-trace verification, no probe needed | `_advance_sweep` never mutates `self.head` (game_engine.py:494-527); sweeps return early with no movement (:636-637) — a head-only wall check at moved ticks cannot miss a crossing |

No repo file was modified by any probe (the feasibility script lives in `/tmp/opencode/`).

---

## 6. Plan-slicing hints

Derived from actual work (not padded); durations absent — fine-grained granularity per the owner's Phase-9 directive. Dependency order: the two pure halves are disjoint files and can run in parallel (worktree protocol for the wave); integration and GUI depend on both.

```
Wave 1 (parallel, TDD pure logic, disjoint files):
  09-01  TDD serpentrum/wall.py — wall_seed_from_setup + WallSpawner policy
         (constants, 3-draw contract, 4 legs, MAX_DRAWS/None, properties)
         + tests/test_wall.py
  09-02  TDD engine wall state + collision — WALL_COLLISION_RADIUS_A,
         set_wall/clear_wall, wall in reset(), ('crashed','wall') leg between
         boundary and body, precedence + strict-edge + head-only-sweep pins
         + tests/test_engine_wall.py
         (files: game_engine.py + new test — NOT spawn.py, NOT test_spawn.py)
Wave 2 (needs 09-01 + 09-02):
  09-03  TDD integration chain s10 — capture→spawn+wall→crash→completion,
         derived expectations + byte-identical re-run
         (tests/test_phase5_integration.py additive + docstring line)
Wave 3 (parallel; both consume the C6 seam; drawing half may be the
        companion researcher's plan — surface split:
        gui wiring here, CGO/bridge visuals there):
  09-04  cgo_build.wall_cgo builder + pymol_bridge load_wall/delete_wall
         ('srp_wall', replace-per-spawn)      [PURE builder + BRIDGE seam]
  09-05  gui_game wiring — _build_engine WallSpawner construction,
         session key, _respawn_pickup success-branch wall seam with the
         finished-guard, (D-WALL-HUD line if flipped) + new source-scan pins
Wave 4 (wrap):
  09-06  full gates (python3.6 tests/run_gates.py) + required smokes
         (any wall-scene additions per the other researcher) +
         BLOCKING owner feel-check checkpoint (decision table §3 in hand —
         length/orientation/clearances/cadence verdicts are FEEL numbers;
         5.1-06/5.2-09/5.3-05 precedent: gates recorded BEFORE the feel-check,
         retunes are single-data-line edits afterwards)
```

Hard rules for every plan (from AGENTS.md + this research): python3.6 %formatting; `wall.py` stays auto-PURE (stdlib only); no `REFUSE_WALL`-shaped placement codes (two active absence-pins); `spawn.py`/`PickupSpawner` signatures byte-identical (5.3 SC4 + source-scan pins); `srp_` prefix mandatory on the wall object; no `.exec_()`; tests/ has no `__init__.py`; prior suites stay green UNMODIFIED (per-file plan §4.1 in the `files_modified` frontmatter).

**Nothing in this phase needs pymol/installation access in its pure half** — it is 100% WSL-TDD until the bridge/visual + feel-check legs.

---

## 7. Metadata

**Confidence breakdown:**
- Verified current behavior (§1): HIGH — every claim read from live source with line numbers; baselines re-run green on 2026-10-12.
- Design contracts (§2): HIGH for seams/names/mechanics (they extend verified adjacent patterns — attach_segment, boundary leg, source-scan pins); MEDIUM for constant VALUES (drafts pending the owner feel-check by design).
- Test impact (§4): HIGH — pin-by-pin analysis over the four closest suites + the source-scan/debug-tail slices; LOW residual risk only in non-engine suites not read line-by-line (they were screened via grep for crash-tuple/attribute exhaustiveness and found scenario-specific).

**Research date:** 2026-10-12
**Valid until:** stable repo state (engine/spawn seams change rarely; re-verify only if 09-adjacent files move before planning lands)
