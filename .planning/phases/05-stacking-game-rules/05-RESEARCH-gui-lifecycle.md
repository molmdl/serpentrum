# Phase 5: Stacking & Game Rules Complete — Research: GUI/Lifecycle Layer

**Aspect:** GameTab / hud_logic / input / PluginDialog wiring for pickup stacking, info-box content (STACK-04), turn sweeps (GAME-10), run completion (GAME-09) and the "Get Spectra" handoff — given everything Phases 1–4 locked.
**Researched:** 2026-09-15 (UTC)
**Domain:** PyQt5 (via `pymol.Qt`) lifecycle wiring over pure engine/stacking + bridge cmd-seam
**Confidence:** HIGH for code-surface claims (every function name/line behavior read directly from the shipped repo sources); MEDIUM for sequences that span modules Phase 5 has not yet written (marked [PLAN-GAP]); human-verify-only for live GUI behavior (01-05 dead end).

**Bottom line (one line):** Phase 4 already shipped the entire lifecycle harness Phase 5 needs — the 100 ms tick loop, the engine event surface (`'stacked'`, `'turning'`, `'turn_refused'`, `'budget_warning'`, `'crashed'`, `'won'`), `engine.attach_segment`/`engine.reject_pickup`, the single `_teardown_round`, and the model-A signal handoff — so Phase 5's GUI work is (a) three new `_handle_event` branches + one placement helper in `gui_game.py`, (b) pure content builders in `hud_logic.py`, (c) a completion presenter + enabled Get Spectra button, (d) pickup teardown folded INTO `_teardown_round`, and (e) two anchor additions (`records`, `last_run`) — with the records-anchoring gap and the pickup-spawn rule being the two real plan-level unknowns.

---

## current_gui_surface

Exact current APIs + locked/pinned behaviors, from source (all HIGH confidence).

### GameTab (`serpentrum/gui_game.py`, 460 lines, GUI purity class)

Public/locked surface:
- `begin_game(setup)` (:157) — teardown-first (`_teardown_round()` line 169), re-centers head via `pymol_bridge.object_exists` + `place_head` (:170-171), builds engine via `_build_engine(setup)` (:187, currently `pickups=None`, cap/atom_budget from setup dict), anchors session on `self._anchor.game_session` (:181), resets info box, runs epoch-guarded countdown.
- `_begin_play(scheduled)` (:230) — **arm-before-timers ordering (locked 04-08):** `session['saved_cam'] = pymol_bridge.lock_camera()` (:243) then `self._input_handle = game_input.install(engine.request_direction)` (:244), THEN `_tick_timer.start()` + `_elapsed_timer.start()`.
- `_on_tick()` (:254) — 100 ms tick (TICK_DT=0.1, TICK_INTERVAL_MS=100, :66-67). Guards session/epoch/paused/finished, calls `engine.step(TICK_DT)`, routes every non-`'moved'` event to `_handle_event(ev, engine)`, drives `pymol_bridge.move_head_delta(nx-old[0], ny-old[1], 0.0)` on move, calls `_update_remaining()` every tick, and funnels finish into `_end_run(engine)`.
- `_handle_event(ev, engine)` (:279) — today handles `'turn_refused'` (logs 'turn refused: %s'), `'crashed'` (logs), `'won'` (logs 'YOU WIN'). **Silently ignores** `'turning'` (deliberate: "too chatty at 10 Hz") and — silently today — `'stacked'` and `'budget_warning'` (they fall through). This is THE Phase 5 hook; only three branches + one helper needed.
- `_update_remaining()` (:313) — reads `hud_logic.remaining_text(engine.molecules_remaining)`; **becomes dynamic for free** once captures increment `molecules_stacked` (already verified in test_hud_logic.py:81-87).
- `_apply_pause_state(paused)` (:334) — pause: `engine.pause()` + timers stop + `_pause_time` rebase marker + `game_input.set_active(False)` (**wizard stays installed, camera stays locked — locked D5**). Resume mirrors with `paused_accum` rebase BEFORE `set_active(True)`.
- `request_auto_pause()` (:369) — guards `status == 'playing'`; PluginDialog.focusInEvent calls it.
- `_end_run(engine)` (:405) — sets `status='over'`, logs verdict **BEFORE** teardown (locked decision), calls `_teardown_round()`.
- `_teardown_round()` (:421) — THE single teardown (locked 04-08, idempotent): tick+elapsed timers stop → `self._epoch += 1` → `game_input.teardown(handle)` (accept-and-ignore) → reads CURRENT session, `pymol_bridge.unlock_camera(session.pop('saved_cam', None))` (pop = double-unlock impossible) → blockSignals pause-button reset (Pitfall G). Call sites: `begin_game`, `_on_restart` (:402), `_end_run` (:414), `shutdown()` (:419). **04-08 explicitly designated this as the extension point for pickup teardown** ("never a second helper").
- Session dict (anchored): `{'engine', 'epoch', 'start_time', 'paused_accum', 'status'}` + ad-hoc `'saved_cam'`, `'_pause_time'`. Anchor = `pmg_tk.startup._serpentrum.game_session` (declared in `__init__.py:26-31`). Survives reload by construction; NEVER the widget, NEVER module globals.
- Epoch: single authority (`self._epoch`); every countdown callback is stale-guardable; teardown bump kills in-flight singleShot chains (Pitfall 9.1).

No `get_spectra_btn` exists yet. No completion presenter exists yet. No pickup/segment state exists in the session yet.

### hud_logic (`serpentrum/hud_logic.py`, 37 lines, PURE)

- `format_elapsed(seconds)` and `remaining_text(value)` — that is ALL. No content-type system, no queue, no priority. The info box is a raw read-only `QTextEdit` appended via `GameTab._log(msg)` (:453).
- **What test_hud_logic.py pins:** 6 `format_elapsed` cases (floor, clamp), 3 `remaining_text` cases (incl. None → 'Remaining: -'), 4 `molecules_remaining` engine-property cases (incl. reset reflection). New content builders must NOT alter these; add alongside.

### input (`serpentrum/input.py`, BRIDGE purity)

- `install(steer_fn)` / `set_active(active)` / `teardown(handle=None)` — route-agnostic seam (locked 04-07, wizard do_special route shipping).
- `do_special` maps GLUT 100/101/102/103 → direction names → `steer_fn(name)` = `engine.request_direction`; return value deliberately IGNORED (engine authority); always grabs (returns True).
- Pause: wizard stays installed, `set_active(False)` = grab-and-no-op (locked).

### gui.py (PluginDialog)

- Fixed page order: Setup = 0 (live SetupTab), Game = 1 (live GameTab), Spectra = 2 (**placeholder** `QWidget` from `_TAB_DEFS`, gui.py:19-23 — no content, no widgets beyond a hint label).
- Model-A handoff (locked 04-06): `SetupTab.start_requested(setup)` → `PluginDialog._on_start_requested` → `self.tabs.setCurrentIndex(1)` + `game_tab.begin_game(setup)`. **GameTab never reaches up to its parent QTabWidget.** This exact pattern is the template for any Get-Spectra tab switch.
- `focusInEvent` → `game_tab.request_auto_pause()`; `closeEvent` → `game_tab.shutdown()`.

### Anchor (`serpentrum/__init__.py`)

`_SerpentrumState` fields today: `dialog`, `controller` (**reserved, unused** — docstring says "the single live game controller (later phases)"), `setup`, `game_session`. Two Phase 5 additions needed (see spectra_handoff + lifecycle_spec).

### Engine event surface GameTab consumes (`game_engine.py`)

- From `step()`: `('moved',(x,y))`, `('turning', tick/total)`, `('turn_refused','boundary'|'body'|'pickup')`, `('stacked', pickup_record)` — engine has ALREADY claimed the pickup and incremented `molecules_stacked`/`atoms_total`/`pickups_remaining` (game_engine.py:702-730), `('budget_warning', atoms_total)` once/run, `('crashed','boundary'|'body')`, `('won',)`. Order pinned by test_engine_rules.py (moved before stacked :341-344; crashed wins precedence :270).
- Controller-called (return, not events): `engine.attach_segment(molecule_id, centroid, atoms)` (:746, counter-NEUTRAL, appends frozen segment) and `engine.reject_pickup(id, reason)` → returns canonical `('refused', id, reason)` (:765; rolls counters back, re-arms pickup — pinned by test_engine_rules.py:421-448 reject-then-recapture).
- Sweep introspection: while `engine.sweeping is not None`, `engine.sweeping['angle_signed']` (±90.0) and `engine.sweeping['total_ticks']` (6) are public state.
- Segment record shape: `{'molecule_id', 'centroid', 'atoms': [(sym,x,y,z)...], 'atoms_n'}`; unknown extra keys are carried through copies (:296-302) — a `ring_indices` key is legal for on-demand frame recompute.

## lifecycle_spec

### 1. Pickup lifecycle (whole capture is ONE tick — no cross-tick pending state)

**Pre-game (begin_game additions — [PLAN-GAP] spawn rule):**
1. `GameTab._build_engine(setup)` must stop seeding `pickups=None` and instead seed a **computed deterministic pickups list** (`{'id','centroid','atoms','atoms_n'}` per record; atoms REQUIRED — the sweep pickup leg consumes them, game_engine.py:305-322). Spawn rule (how many, where, which molecules, re-spawn after capture?) is NOT in scope of this research — it is a plan-level design choice needing a decision (open question 3); the GUI only needs the pure spawner's output list passed into `GameEngine(..., pickups=...)`.
2. The viewer must show pickup objects **as sticks** (GAME-03 "pickups as sticks"; ROADMAP Phase-4 note: "Pickup stick rendering arrives with pickups in Phase 5"). New bridge responsibility: materialize the N pickups at their spawn centroids, one object each named `srp_pickup_<id>` (or numbered), `cmd.show('sticks', ...)` — mirrors existing `materialize` patterns (`load_molecule`, `cmd.show`, `place_head`-style centering, then translate to centroid). Placement happens at begin_game/start (not SetupTab Apply) so Restart-without-Apply still reconstructs the scene deterministically.
3. **Records gap (open question 4):** `begin_game` needs the setloader `records` list (file paths, `ring_atoms`, `has_stack_entry`, names) — today records live ONLY as a local in `SetupTab._on_apply` and are discarded. They must be anchored on `_serpentrum` (recommend a new `records` + `stacking_data` field written by `_on_apply` on success) — the setup dict cannot carry them (schema is scalars-only, setup_logic.py:46-48).

**Capture tick (all inside `_on_tick` → `_handle_event('stacked', ...)`):**
4. Engine emits `('stacked', pickup)` — capture is already claimed/counted. GUI's new `'stacked'` branch ("the Phase-5 connector" the engine docstrings name) does, synchronously:
   a. **Dataset lookup** — record `has_stack_entry` False (the `__upload__` skip-policy keying, setloader.py:51-53) or `molecule_data.interaction_for(...)` None → `engine.reject_pickup(pickup_id, 'no_dataset')`, log the returned `('refused', ...)` tuple + a skip reason line (STACK-03), leave the pickup object VISIBLE (it is re-armed and live). Done.
   b. **Placement math (all PURE, don't-hand-roll):** parse pickup coords from `record['file']` via molfile; extract ONE planar 6-ring in ring order from `record['ring_atoms']` (the manifest stores the FULL 2-core, e.g. naphthalene 10 indices — biphenyl planarity trap, STATE pending-todo; the extraction helper itself belongs to a placement/staging plan, not gui_game); tail frame = head ring frame for the first capture, else recompute the newest segment's frame from its current (sweep-rotated) atoms + stored `ring_indices` via `stacking.ring_frame`; `stacking.place_pickup(...)` with the SHIPPED dataset's `distance_a`/`lateral_offset_a` → `(placed_atoms, R, t)`.
   c. **Clash gate (STACK-05):** `stacking.check_clash(placed_atoms, existing_chain_atoms, box3d)` (existing chain atoms from engine segments' `atoms` + head atoms; box3d includes z faces — see box_display_z_decision). A diagnostic dict → `engine.reject_pickup(pickup_id, diag['kind'])`, log refused line, leave object. Done.
   d. **Success:** apply `R,t` to the pickup object in the viewer (bridge: `cmd.transform_selection` — **matrix layout flagged OPEN by ROADMAP; verify against `editing.py:1946` docstring; verified fallback = `cmd.rotate` + `cmd.translate`**); mark the object as a CHAIN member (rename `srp_pickup_x` → `srp_seg_N` or maintain a session `live_pickup_names` set — needed for the completion "viewer clears" split, see teardown_integration); `engine.attach_segment(molecule_id, centroid, placed_atoms)`; log the structured pickup block (STACK-04 builder); append to session `stacked_history`.
5. HUD: `_update_remaining()` runs on the same tick for free. GAME-04 counts (`molecules_stacked`, `atoms_total`) stay engine-owned and hidden during play (used at completion + SPECTRA-06 re-check).
6. Win check: engine already emitted `('won',)` and set finished on the same tick if cap reached; `_on_tick` funnels to `_end_run`.

**State GameTab holds:** NO widget-owned pickup state — everything lives in the anchored session dict: add `'stacked_history'` (list of `{'id','name','interaction_id','distance_a','lateral_offset_a','citation','outcome': 'stacked'|'refused:<reason>'}`), `'live_pickup_names'` (viewer object names of un-stacked pickups). No cross-tick "pending pickup" state is needed: capture→place-or-refuse is fully synchronous within one tick.

### 2. Turn request flow (GAME-10)

1. Arrow → `KeySteerWizard.do_special` → `engine.request_direction(name)` (buffers max-1; newest-wins only while sweeping — locked 04-07). GUI does nothing at press time.
2. **Next 100 ms tick** (locked 04-09: turn applies at the next tick; designed, not a defect): engine, at `step()` start, pops pending → `start_sweep` 3-leg pre-check (boundary/body/pickup, 7 sampled poses).
   - **Refusal:** `('turn_refused', reason)` → existing `_handle_event` Branch logs one line (`'turn refused: %s'` — already shipped; keep, it is the STACK-04-class "nothing else" surface; do NOT make refusals modal or chattier).
   - **Acceptance:** ticks 1..6 each return ONLY `[('turning', frac)]` — no `'moved'`, no forward motion, exactly one 100 ms tick per sweep step (6 × 100 ms = 600 ms per 90° turn).
3. **Sweep animation ownership:** the ENGINE owns the math (absolute rotation from start-pose, drift-free); the GUI owns the per-tick viewer update ONLY. New `'turning'` branch in `_handle_event`: one bridge call per tick rotating ALL chain objects (excluding `srp_head` — it is the pivot) about the head by `angle_signed / TURN_TICKS` (= ±15°) in model axes. Direction/tick comes from `session['engine'].sweeping['angle_signed']` (public) — the `frac` payload is informational. The sweep tick IS the movement tick — **no second timer** (Pitfall 9.1 double-timer class is banned).
4. The bridge needs a `rotate` about the z-axis through an arbitrary pivot in MODEL axes (camera=0, per the `move_head_delta` precedent at pymol_bridge.py:164-176). `cmd.rotate` axis/origin/camera semantics vs PyMOL source = verify-in-Phase-5 item (open question 2); per-tick incremental rotation is drift-acceptable (6 identical 15° steps; scene re-anchors on every re-materialize/restart anyway).
5. Pause mid-sweep: nothing special — `_apply_pause_state(True)` stops the tick timer; engine retains `sweeping`; resume continues; wizard stays installed; camera stays locked (locked D5). Restart mid-sweep: `begin_game` teardown kills in-flight chain state via epoch + re-materialize.

### 3. Completion flow (GAME-09) — exact sequence, same path for win and crash (locked decision 8)

1. Tick emits `('won',)` or `('crashed', ...)`; `_on_tick` → `_end_run(engine)`.
2. `_end_run` (existing): `session['status'] = 'over'`; log verdict line FIRST; then `_teardown_round()` (timers, epoch, wizard, camera unlock — the saved view pops).
3. **NEW presenter step** (call it `_present_completion(engine)` — runs AFTER `_teardown_round` from `_end_run`; it is NOT a second teardown helper, it is a presenter):
   a. **Viewer clears:** delete the UN-STACKED pickup objects only (session `live_pickup_names`, e.g. `srp_pickup_*` still live) via bridge delete; chain objects (`srp_head` + `srp_seg_*`) STAY — "the snake is still complete" (GAME-05) and must remain visible.
   b. **Camera focuses the snake:** one-shot reframe on the chain selection (F16 `cmd.zoom(selection)` over `srp_head srp_seg_*`; matching ARCHITECTURE's "zoom/origin on snake (F16) → show length + score → enable Get Spectra"). Runs after camera unlock so the restored mouse works. NEVER per-tick (pitfall 14).
   c. **HUD shows length + score:** info box logs final line via a hud_logic builder: molecule count (score), chain length (segments), result; optionally atoms_total now revealed (it feeds the SPECTRA-06 explanation) — `remaining_label` may freeze at its last value or be re-purposed to 'Snake: N molecules'.
   d. **End-of-run interaction breakdown (STACK-04):** hud_logic builder over session `stacked_history` — per interaction name: stacked count, distance, citation; refused count by reason.
   e. **Get Spectra activates:** `get_spectra_btn.setEnabled(True)`; anchor the handoff record (see spectra_handoff) on `_serpentrum`.
4. `'budget_warning'` events during play also log (currently unhandled — one more `_handle_event` branch, reuse a hud_logic builder; molecules/atoms counts stay hidden per GAME-04 but a budget-advisory line is chemistry-teacher content, not a counter display).

## info_box_spec

**Current model verdict:** the info box is a dumb rolling log (`QTextEdit.append` via `_log`) with NO queue and NO priority system, and `test_hud_logic.py` pins only `format_elapsed` + `remaining_text` (+ the engine `molecules_remaining` property). **Do not build a queue/priority system.** The four STACK-04 content classes map onto pure string BUILDERS in `hud_logic.py` (PURE → WSL-testable), called at the event sites; "priority" is already enforced by which events log at all (`'moved'`/`'turning'` silent at 10 Hz — the existing chattiness policy).

| STACK-04 content class | Source data | Builder (new, pure) | Call site |
|---|---|---|---|
| Per-pickup structured content (interaction name, distance, one-line explanation, citation short-code) | picked `interaction` dict (name/distance_a/lateral_offset_a/explanation/citation key) + `stacking_pi_stack.json` citations table (`short`) + pickup record name | `hud_logic.pickup_block(name, interaction, citation_short)` | `'stacked'` success branch |
| Skip with reason (STACK-03 no entry; STACK-05 clash/wall rejection) | `('refused', id, reason)` from `reject_pickup`; clash diag `kind` | `hud_logic.skip_text(pickup_name, reason)` | `'stacked'` refuse branches |
| Idle chemistry tips | dataset citations + explanation lines (human-approved strings only — repo no-fabrication rule) | `hud_logic.idle_tip()` (index/round-robin) or a small shipped list | `begin_game` (today logs 'Get ready...') + optionally one tip per countdown second |
| Early controls hints | static | existing lines ('Get ready...', 'Move with the arrow keys.') + hint_label | unchanged |
| End-of-run breakdown | session `stacked_history` | `hud_logic.breakdown_text(history, counts)` | `_present_completion` |

**Queueing:** none. Deterministic append order = engine event order (pinned by tests). Line format recommendation (educator-readable, FEATURES.md micro-lesson intent): `'+ naphthalene: pi-pi stacking (parallel-displaced), 3.6 A — <one-liner> [Janiak 2000]'`, `'skipped biphenyl: no approved stacking entry'`. All chemistry sentences come from the shipped dataset's own `explanation` field — hud_logic composes, it never writes chemistry.

## spectra_handoff

**What Phase 5 must prepare (Phase 6/7 consume; Phase 5 does NOT build the run):**

- **The record:** at `_present_completion`, anchor `{'result': engine.result, 'molecules_stacked': engine.molecules_stacked, 'atoms_total': engine.atoms_total, 'chain_objects': ['srp_head', 'srp_seg_1', ...], 'snake_id': '<epoch-or-run-id>'}` on `_serpentrum` — recommend a new documented anchor field `last_run` (mirroring the `game_session` precedent; the reserved `controller` field stays reserved). Anchor-survival gives reload safety and a fresh-dialog-readable value.
- **Coordinate extraction (Phase 6's .xyz):** ARCHITECTURE's flow is viewer-extraction (`cmd.get_coordset`/`get_model` over the chain objects [F14]). The engine route (segments' `atoms` lists) is pure and drift-free-exact but excludes head atoms unless separately tracked. **Recommendation: viewer extraction** (per ARCHITECTURE + INFRA-04's viewer-survives-reload truth), with `atoms_total` from the counters cross-checked against the parsed model atom count (Pitfall: "spectra silently showing another molecule's spectrum").
- **Counts (SPECTRA-06 pre-xtb re-check):** engine's `molecules_stacked`/`atoms_total` are the authorities; the handoff carries snapshots so a Phase 6 runner can re-check against `atom_budget` without reading engine internals, plus the setup dict's `atom_budget`/hessian warning chain (setup_logic already owns the static half).
- **"Get Spectra" button placement + routing:** temporary button INSIDE the Game tab (mirrors the temp-Start-in-Setup-tab precedent; Phase 8 owns the canonical row). Disabled at construction/`begin_game`/`_teardown_round`; enabled in `_present_completion`. On click: model-A emit — GameTab declares `spectra_requested` (QtCore.Signal), `PluginDialog` connects it to `setCurrentIndex(2) + hand the anchored last_run to the Spectra page`. Wiring the switch in Phase 5 is optional (SPECTRA-01 is formally Phase 7); the ACTIVATION (GAME-09) is not. Recommendation: emit the signal and connect it now — it is 3 lines, follows the locked 04-06 template, and Phase 7 only replaces the placeholder page content.
- The chained snake in the viewer is also the visual payoff — don't delete it on Get-Spectra; Phase 7 draws mode vectors onto it.

## teardown_integration

What changes INSIDE `_teardown_round` (locked: pickup teardown folds in here, never a second helper):

1. **Keep steps (a)-(e) byte-semantics identical** (timers → epoch → input teardown → unlock via popped `saved_cam` → blockSignals button reset).
2. **Add step (f):** delete the session's LIVE pickup objects (session `live_pickup_names`; `object_exists`-guarded per name or one pattern delete of `srp_pickup_*`). Idempotent via the None/absent guard, same as `unlock_camera`. Note the completion nuance: on the `_end_run` path this runs BEFORE `_present_completion` — which is exactly correct: live (un-stacked) pickups are cleared by teardown, the stacked chain (`srp_seg_*`) is untouched, and the presenter then reframes the remaining chain. Chain objects are removed only by the next materialize/begin_game (cleanup-first contract) or explicit Cleanup.
3. **Also reset** the get-spectra button (disabled) and clear `last_run`-pending state on begin_game paths, under the same session read.
4. **Reload-mid-run gap (flagged):** after a Plugin-Manager reload the new GameTab has `_session None` while the anchor's `game_session` may hold a stale `'saved_cam'` — today's teardown reads ONLY `self._session`, so a reload mid-run leaves the camera mouse-locked until the next full game cycle (`cmd.mouse()` in the next `unlock_camera` recovers buttons; view matrix stays zoomed). Recommend `_teardown_round` read the anchor session as a fallback for the `saved_cam` pop when the widget session is None — one-line hardening, same idempotent contract. (Also the orphaned old wizard survives a reload as a "foreign" instance — `input.teardown`'s isinstance check fails against the reloaded class; old steer_fn still points at a dead engine so it is harmless, but note it.)
5. **Restart × pickups:** `_on_restart` → `begin_game` → teardown (clears live pickups) → spawn + materialize pickups deterministically (same seeds → same scene). Works IF records + spawn are anchored (gap above) — without anchored records, Restart cannot rebuild the pickup scene.
6. **Cleanup button during play (new desync class):** SetupTab's Cleanup (`pymol_bridge.cleanup_srp`) can currently delete the whole scene while a run is live — engine keeps stepping, bridge calls then hit missing objects. Recommend: Cleanup refuses/routes to `shutdown()`-style teardown when `anchor.game_session` status is `'playing'`/`'paused'`.
7. **Pause during sweep:** no pickup interaction; nothing to add (engine holds sweep state; viewer matches on resume).
8. **Dialog close (`shutdown()`):** already funnels to `_teardown_round` — pickup teardown rides along free.

## box_display_z_decision

**Where it lives:** `pymol_bridge.BOX_DISPLAY_Z = 5.0` (pymol_bridge.py:66) — consumed ONLY by `load_box` (z faces ±5.0); `setup_logic.BOX_PRESETS` owns xy only.

**Measured data (03-08-SUMMARY.md, real shipped SDFs, pure-python measurement):**
| molecule | diameter Å | stored z-span Å |
|---|---|---|
| benzene | 4.962 | 0.000 |
| naphthalene | 7.187 | 0.000 |
| phenanthrene | 9.296 | 0.002 |
| biphenyl | 9.198 | 3.426 |
| anthracene | 9.526 | 0.001 |

Worst single-molecule need = diameter/2 = 4.763 Å ≤ 5.0 — any SINGLE molecule fits today's box in ANY orientation with 0.474 Å total slack (0.237/face), no margin. `2·BOX_DISPLAY_Z` never accumulates during play: the π-stack normal lies IN the xy plane (edge-on presentation, locked 03-08 + reinforced by the 04-07 user remark) so stacks grow along x/y only; sweeps rotate about z, leaving z extents invariant.

**What actually needs the margin:** only the worst-case projection of one molecule's diameter onto z — i.e. only if a molecule's LONG axis points along z. The mandatory Phase-5 edge-on orientation hook (ring-plane ⊥ screen, normal in xy) can constrain the long ring axis to lie in-plane (Option A), in which case only the short axis (~5.0 Å max) projects onto z and **5.0 is ample** (10.0 ≫ 5.0). Option B (bump to 6.0, 12.0 Å total = 9.526 + 2.0 margin) buys orientation-independence for molecules the hook cannot orient.

**Recommendation: Option A — keep BOX_DISPLAY_Z = 5.0**, contingent on the orientation hook being applied at materialize/placement to BOTH head and pickups with the long axis in-plane (it is a hard Phase-5 prerequisite anyway). Molecules that cannot be oriented (uploaded molecules without `ring_atoms` — records omit ring_atoms for uploads, setloader.py:76) must either stay flat (z-span ≈ short axis, safe) or be skip-at-pickup by policy — uploads ALREADY are (`__upload__`). If the planner wants a safety cushion for a future "generic fallback" (STACK-06, v2), 6.0 is a one-constant change with zero code impact. Decide at Phase-5 planning; data above is the decision record. Note the clash gate's `box3d` bounds (stacking.check_clash takes 3-tuples incl. z) should use the SAME z faces the box displays (±BOX_DISPLAY_Z) so visual and gate truth cannot diverge.

## dont_hand_roll

| Problem | Don't build | Use instead |
|---|---|---|
| Rigid-body π-stack placement / ring frames | any GUI-side transform math | `stacking.place_pickup` + `stacking.ring_frame` (PURE, exact vs committed dimer2; R,t feed the bridge) |
| Clash rejection | a new distance check | `stacking.check_clash` (2.5 Å threshold pinned by the verified dimer run; wall-first diagnostics) |
| Dataset lookup & skip keying | per-molecule hardcoded distances | `molecule_data.shipped_interactions` / `interaction_for` + record `has_stack_entry` (the `__upload__` sentinel) |
| Molecule coordinates for placement | `cmd.get_model` readback into pure math | `molfile.read_sdf` on `record['file']` (viewer truth == model truth by construction; keeps math WSL-testable) |
| Capture rollback / re-arm | GUI fiddling with engine counters | `engine.reject_pickup` / `engine.attach_segment` (counter-neutral / rollback semantics pinned by test_engine_rules.py) |
| Info-box content | a queue/priority/message system | pure string builders in `hud_logic` + rolling append (matches every pinned test + the existing chattiness policy) |
| Teardown paths | a second cleanup helper | extend `_teardown_round` (locked 04-08) |
| Snake reframe at completion | per-tick camera tracking | one-shot `cmd.zoom` on the chain selection (pitfall 14 bans per-tick reframe) |
| Viewer pickup transform | recomposing matrices by hand | `cmd.transform_selection(R,t)` after verifying layout vs `editing.py:1946`; verified fallback `cmd.rotate`+`cmd.translate` (ROADMAP) |
| HUD counters | new GUI-side counting | read `engine.molecules_stacked` / `atoms_total` / `molecules_remaining` (already pinned) |
| Turn animation timing | a second sweep timer | per-tick rotation in the existing `'turning'` branch of the single 100 ms timer |

## open_questions

1. **`cmd.transform_selection` matrix layout** — ROADMAP-flagged: verify the exact 12/16-float layout vs `editing.py:1946` before wiring; fallback verified (`rotate`+`translate`). Blocks only the success branch of stacking placement. [Phase-5 spike]
2. **`cmd.rotate` model-axes pivot rotation** — axis='z', angle=±15°, origin=head, camera=0 semantics unverified for PyMOL 2.5.0 source; needed by the `'turning'` viewer branch. (Incremental alternative: `cmd.translate` to origin-ish frames is uglier; verify rotate first.) [Phase-5 spike]
3. **Pickup spawn rule — [PLAN-GAP, needs decision].** How many pickups live at once, where they spawn (ARCHITECTURE's stale "engine-placed grid cells" wording suggests N placed at start), whether a captured pickup respawns a replacement, and which molecules (ordered set? seeded RNG like `setup_logic.randomize_head`?). This gates `_build_engine`, the bridge materialize extension, and restart determinism. Recommend a plan-level decision user-facing: e.g. "all remaining set molecules placed at start at deterministic positions, no respawn; win = cap among live pickups".
4. **Records anchoring — [PLAN-GAP].** `setloader` records + stacking dataset are currently SetupTab-locals. Recommend new anchor fields (`records`, `stacking_data`) written by `_on_apply` success and read by `begin_game` — required by pickups AND restart AND the info-box builders. NOT the setup dict (scalars-only schema).
5. **Ticket for orientation hook details** — the edge-on reorientation (per-record rigid transform at materialize) needs a bridge + pure helper (axis choice = long ring axis in-plane; the 03-05 `find_ring_atoms`-style extraction adapted for ONE planar 6-ring in ring order — the biphenyl 2-core planarity trap). Which plan owns it is a planning split decision (it touches materialize/begin_game, i.e. this lifecycle layer's entry points).
6. **Reload-mid-run hardening** — anchor-session fallback for `saved_cam` and the foreign-wizard orphaning (harmless but untidy). Small, but decide whether Phase 5 takes it now.
7. **Cleanup-during-play guard** — who disables/refuses (SetupTab consults `anchor.game_session` status, or dialog routes Cleanup through `shutdown()`). Spec-level decision, low cost either way.
8. **Idle-tip chemistry sentences** — any new sentence shown to users needs human approval per the no-fabrication rule; prefer quoting the shipped dataset's `explanation` field verbatim rather than authoring new chemistry prose.

---

## Sources

**Primary (HIGH confidence — read directly from repo sources):**
- `serpentrum/gui_game.py` (whole file) — tick loop, event routing, teardown, pause, countdown
- `serpentrum/hud_logic.py` + `tests/test_hud_logic.py` — pinned HUD pure surface
- `serpentrum/input.py` — wizard lifecycle contract
- `serpentrum/gui.py` — tab ownership + model-A handoff
- `serpentrum/game_engine.py` + `tests/test_engine_rules.py` — event surface, attach/reject contracts (pinned)
- `serpentrum/pymol_bridge.py` — materialize/cleanup/lock-camera/move_head_delta/BOX_DISPLAY_Z
- `serpentrum/setloader.py`, `molecule_data.py`, `stacking.py`, `setup_logic.py`, `serpentrum/__init__.py` — records, dataset, placement math, anchor
- `serpentrum/data/stacking_pi_stack.json`, `manifest.json` — shipped interaction + ring_atoms (full 2-core)
- `.planning/phases/04-game-loop-input/04-08-SUMMARY.md`, `04-06-SUMMARY.md`, `04-07-SUMMARY.md`, `04-RESEARCH-hud.md`
- `.planning/phases/03-molecules-in-the-viewer-setup-tab/03-08-SUMMARY.md` — edge-on decision + BOX_DISPLAY_Z measurements
- `.planning/STATE.md` (decisions + pending todos), `REQUIREMENTS.md`, `ROADMAP.md`
- `.planning/research/ARCHITECTURE.md` (main lifecycle flow, state ownership), `PITFALLS.md` (pitfalls 5, 7, 9, 10, 14, F16/F17), `STACK.md`, `FEATURES.md`

**Metadata — confidence breakdown:**
- current_gui_surface: HIGH (source-read)
- lifecycle_spec: HIGH for engine/viewer seams; MEDIUM where the unwritten spawn/orientation plans interpose (marked [PLAN-GAP])
- info_box_spec: HIGH (verdict: rolling log + pure builders)
- spectra_handoff: MEDIUM (Phase 6/7 interfaces not yet designed; ARCHITECTURE flow is the authority relied on)
- teardown_integration: HIGH (designated extension point, enumerated)
- box_display_z_decision: HIGH (measured numbers, 03-08)

**Research date:** 2026-09-15 (UTC) — planning-doc date convention; valid ~30 days (stable code surface).
