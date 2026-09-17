---
phase: 05-stacking-game-rules
verified: 2026-09-17T19:17:13Z
status: human_needed
score: 15/15 executed plans verified (05-16 pending final plan; 5/5 ROADMAP success criteria structurally verified)
gaps: []
human_verification:
  - test: "Pickup materializes as an edge-on stick"
    expected: "At GO! the first pickup renders as a STICKS object standing perpendicular to the screen plane (ring edge-on) at its spawn position; the head renders edge-on spheres after Apply"
    why_human: "Visual presentation of real PyMOL geometry cannot be verified headless (01-05: offscreen Qt is a dead end)"
  - test: "Capture stacks at cited geometry with full info content"
    expected: "Steering into a pickup appends it behind the head; the info box shows '+ <name>: <interaction>, <d>.00 A plane gap (centroid <c> A @ <a> deg off-normal) - <verbatim explanation> [<citation short>]' and the placed ring-centroid plane gap equals the dataset distance_a (3.60 A for the shipped pi_stack_pd entry)"
    why_human: "Live viewer geometry + info-box readability need eyes on real PyMOL"
  - test: "Rigid whole-chain turn sweep"
    expected: "A perpendicular turn sweeps srp_head AND every srp_seg_* together as one rigid body about the head pivot (~6 ticks of 15 deg); the chain never shears or leaves a segment behind"
    why_human: "Real-time multi-object rotation behavior is only observable in the live viewer"
  - test: "Refusal/skip info lines"
    expected: "Uploading a molecule and capturing it logs 'skipped <name>: no verified stacking entry for this molecule (no invented chemistry)'; steering biphenyl into a clash logs 'skipped <name>: placement clashes (<distance> A)' then 'placement refused - run continues (cap not reached yet)' and play continues"
    why_human: "End-to-end GUI flow with an upload file requires the live dialog"
  - test: "Completion flow — win AND crash"
    expected: "On reaching the cap (or crashing): live pickups vanish, the camera frames the completed snake, the info box reveals result/score/snake length/atom count + the interaction breakdown, and the Get Spectra button becomes clickable and switches to the Spectra tab"
    why_human: "Tab switching, camera framing and button lifecycle are live-GUI behaviors"
---

# Phase 5: Stacking & Game Rules Complete — Verification Report

**Phase Goal:** The complete v1 game: pickups stack onto the chain at cited geometry, turns pivot the whole chain rigidly, collisions end runs, and both wins and crashes hand a complete snake to the spectra stage.
**Verified:** 2026-09-17T19:17:13Z (HEAD d6fc4b5, tree clean)
**Status:** human_needed (structural verification fully passed; live-GUI verdicts deferred to plan 05-16's consolidated human checkpoint — by design, not a gap)
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (ROADMAP success criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Pickup appends at dataset-stored stacking geometry (placed distance == cited value), counts tracked, info box shows interaction name, distance, explanation, citation | ✓ VERIFIED (structurally) | `placement.attempt_place` drives `stacking.place_pickup` with `interaction['distance_a']`/`lateral_offset_a` (placement.py:169-178, no invented chemistry); `hud_logic.pickup_block` composes the full dataset line incl. 3.60 A @ 20.0 deg formula (hud_logic.py:88-108); counters tracked via `attach_segment` (engine counter-neutral) and `molecules_stacked`/`atoms_total`; smoke 08 verifies the real-data 3.6000 A placement end-to-end headless |
| 2 | Turn sweeps the whole chain rigidly; boundary/body sweep refused; 180° reversal impossible | ✓ VERIFIED (structurally) | ONE `pymol_bridge.sweep_chain(delta, engine.head)` call site (gui_game.py:641) — `cmd.rotate('z', delta, 'srp_head or srp_seg_*', camera=0, origin=[hx,hy,0])` (pymol_bridge.py:311-329); engine refuses boundary/body sweeps with zero mutation and returns `('turn_refused', reason)` (game_engine.py:386-424, gui_game.py:581-582 logs it); 180° reversal ignored via dot < -0.5 both at rest AND while sweeping (game_engine.py:327-363) |
| 3 | Boundary/body (segment-based) hit ends the run leaving the snake complete; win when length exceeds cap | ✓ VERIFIED (structurally) | Engine step() pinned order moved→boundary→body→stacked→budget→won (02-pinned tests green in the 561); `_teardown_round` deletes ONLY `srp_pickup_*` (pymol_bridge.py:361-368) — `srp_head`/`srp_seg_*` untouched, chain stays complete; 'won' fires on cap (engine, guarded in GUI by `engine.finished`, gui_game.py:592) |
| 4 | On win OR crash: viewer clears, camera focuses snake, length + score display, Get Spectra activates | ✓ VERIFIED (structurally) | `_end_run`: verdict log → `_teardown_round` (ONE definition, gui_game.py:1004) → `_present_completion` (gui_game.py:932-997); `zoom_chain()` AFTER teardown (P5-3 ordering honored, gui_game.py:982); `hud_logic.completion_lines` reveals counts; `breakdown_lines` prints history; `_anchor.last_run` anchored with result/counts/chain_objects/snake_id; `get_spectra_btn.setEnabled(True)` presenter-only (teardown/begin_game re-disable); `spectra_requested` → `PluginDialog._on_spectra_requested` → `setCurrentIndex(2)` (gui.py:77,96-105) |
| 5 | Unverified-dataset pickups skipped with reason in info box; clash gate rejects colliding placements | ✓ VERIFIED (structurally) | `resolve_skip` ordered taxonomy SKIP_NO_ENTRY→NOT_APPROVED→MODE→NO_RING (+ NONPLANAR at placement) (placement.py:95-122); approval gate via `shipped_interactions` APPROVED set (DATA-02); uploads keyed `__upload__`/no stack_ring (setloader.py:111-112 demo-only carry); `hud_logic.reason_text` maps every code to an educator line (incl. REFUSE_ATOM clash distance); 3D clash gate over head+segments+other live pickups at ±BOX_DISPLAY_Z (placement.py:181-193, gui_game.py:716-724); `reject_pickup` called on EVERY non-placed outcome incl. the 'error' last resort (gui_game.py:759,775) |

**Score:** 5/5 success criteria structurally verified (live-GUI confirmation pending in 05-16)

### Per-Plan Must-Have Verification

| Plan | Must-have focus | Status | Evidence |
|------|----------------|--------|----------|
| 05-01 | `molfile.ring_cycle` canonical 6-ring in walk order | ✓ verified | `def ring_cycle` (molfile.py:577): 2-core restrict via `find_ring_atoms`, bounded-DFS ≤6 cycles, canonical (length, lex) selection; `tests/test_ring_cycle.py` (188 lines, 110 phase-5 tests collected incl. this file) pins 5 canonical tuples + sorted-order-fails + determinism |
| 05-02 | TTT matrix layout + edge-on canonicalization | ✓ verified | orientation.py:156 lines, `matrix_rt`/`mat_vec3`/`edge_on_frame`/`edge_on_m16`/`edge_on_atoms` all present; `tests/test_orientation.py` (252 lines) pins probe-A1 fixture + z-span anchors; smoke 08 verifies real-data z-span == pure prediction live |
| 05-03 | Deterministic seeded spawner | ✓ verified | spawn.py:279 lines; `PickupSpawner` + `build_pickup_seed` + `seed_from_setup` via `zlib.crc32` (NEVER hash()); MAX_LIVE_PICKUPS=4, LOOKAHEAD_A=8.0, clearance legs per pinned policy; `tests/test_spawn.py` (309 lines) |
| 05-04 | reject_pickup un-finish (win-vs-clash desync) | ✓ verified | game_engine.py:765-819: rolls counters back, re-arms pickup, and un-finishes ONLY `finished and result=='won' and molecules_stacked < cap`; crashed runs never un-finished; event order untouched (all 02 pins green in the 561); `tests/test_engine_win_desync.py` (265 lines) |
| 05-05 | Placement controller seam | ✓ verified | placement.py:244 lines; `resolve`/`resolve_skip`/`tail_frame`/`attempt_place`/`gate` + all 7 outcome-code constants; head-tail `-(heading)` / newest-segment tail policy; outcome contract exactly as pinned; `tests/test_placement.py` (578 lines) incl. 3.6000 A exactness |
| 05-06 | Anchors records/stacking_data/last_run + stacking_path wiring | ✓ verified | `__init__.py` `_SerpentrumState` has `records`/`stacking_data`/`last_run` anchored on `pmg_tk.startup._serpentrum` (lines 32-43); gui_setup.py:448-453 passes `stacking_path=setloader.default_stacking_path()` into BOTH load paths; `self._anchor.records`/`.stacking_data` written on success (lines 480-481); dataset-failure degrades to stacking_data=None → SKIP_NO_ENTRY |
| 05-07 | Bridge primitives + REQUIRED smoke 07 | ✓ verified | pymol_bridge.py: `apply_matrix`(294)/`sweep_chain`(311)/`zoom_chain`(331)/`materialize_pickup`(344)/`delete_pickups`(361)/`rename_pickup`(371)/`chain_object_names`(383); smoke 07 in REQUIRED_SMOKES (run_gates.py:60) and flushed `SMOKE-OK TRANSFORM` live |
| 05-08 | stack_ring carry (demo only) | ✓ verified | setloader.py:218 computes `stack_ring = molfile.ring_cycle(record)` in `_build_record`; carried at 111-112 only when computed; uploads ring-less; `tests/test_setloader_stack_ring.py` (155 lines) |
| 05-09 | STACK-04 HUD builders | ✓ verified | hud_logic.py: `pickup_block`/`skip_text`/`reason_text`/`budget_text` (count-free)/`completion_lines`/`breakdown_lines`/`idle_tip`/`resume_note`; imports placement code constants (one taxonomy, two consumers); `tests/test_hud_content.py` (314 lines); existing format pins untouched |
| 05-10 | Edge-on at materialization + pickup sticks | ✓ verified | `materialize(setup, records, head_m16=None)` applies transform BEFORE `place_head` (pymol_bridge.py:247-292); gui_setup.py:512 computes `head_m16 = orientation.edge_on_m16(...)` from the pure record and passes it (line 529); smoke 08 in REQUIRED_SMOKES, flushed `SMOKE-OK EDGEON` with real-data 3.6000 A end-to-end |
| 05-11 | begin_game seeding + head mirror + teardown pickup deletion | ✓ verified | gui_game.py:274-334: teardown-first, anchored records consumption, `_build_engine` seeds `GameEngine(pickups=[seed])` via `spawner.first((0,0),'right')` → `build_pickup_seed`, materializes each seed edge-on as sticks, `frame_scene()` one-shot; head mirror moved-translation stays equal to viewer truth (no readback, gui_game.py:554-558); `_teardown_round` folds `delete_pickups()` (line 1046) — chain objects untouched |
| 05-12 | Pure integration chain | ✓ verified | `tests/test_phase5_integration.py` (669 lines): records → spawner → engine → placement → attach/reject across win/crash/refuse/skip/un-finish; runs green in the suite |
| 05-13 | Capture seam | ✓ verified | `_handle_stack_event` (gui_game.py:654-775): ONE synchronous resolution per 'stacked' — resolve → placed: attach + `apply_matrix` + rename `srp_pickup_<id>`→`srp_seg_<n>` + pickup_block + history; skip/refuse: `reject_pickup` ALWAYS (single else branch + 'error' except-guard), reason line, resume_note; respawn gate `MAX_LIVE_PICKUPS` after EVERY resolution |
| 05-14 | Rigid sweep + budget advisory | ✓ verified | `_handle_turn_event` (gui_game.py:597-650): ONE `sweep_chain(delta, engine.head)` per tick, delta = `angle_signed/total_ticks`, final tick reuses stored `last_turn_delta`; pure head mirror rotated by the SAME `game_engine._rotate_xy` delta; `'budget_warning'` logs count-free `budget_text()` (gui_game.py:589-590) |
| 05-15 | Completion presenter + Get Spectra signal | ✓ verified | `_present_completion` (gui_game.py:953-997) + `get_spectra_btn` (disabled at construction:233-234, teardown:1052, presenter-only enable:997) + `spectra_requested` Signal (190, wired at 270); gui.py:77 connects it, `_on_spectra_requested` → `setCurrentIndex(2)` (96-105); `last_run` anchored (990-996) |
| 05-16 | Phase-closing gate pass + consolidated human checkpoint | ⊘ pending final plan | Intentionally not yet executed (wave 7, autonomous: false). Its gate-half is independently reproduced HERE (see Gate Results); its human checkpoint is the blocking gate — items listed under Human Verification Required |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `serpentrum/molfile.py` | ring_cycle | ✓ VERIFIED | 694 lines; pure bounded-DFS + canonicalization; feeds setloader + tail frames |
| `serpentrum/orientation.py` | matrix_rt + edge-on | ✓ VERIFIED | 156 lines; 5 public functions; PURE |
| `serpentrum/spawn.py` | PickupSpawner | ✓ VERIFIED | 279 lines; crc32-seeded, cyclic, clearance-validated |
| `serpentrum/game_engine.py` | reject_pickup un-finish | ✓ VERIFIED | 819 lines; additive G2 fix; Phase-2 pins green |
| `serpentrum/placement.py` | resolve seam | ✓ VERIFIED | 244 lines; skip taxonomy + tail policy + 3D gate + outcome contract |
| `serpentrum/setloader.py` | stack_ring carry | ✓ VERIFIED | 344 lines; demo-only, from the SAME parsed record |
| `serpentrum/hud_logic.py` | STACK-04 builders | ✓ VERIFIED | 188 lines; dataset-composed content, count-free budget line |
| `serpentrum/pymol_bridge.py` | Phase-5 cmd seams | ✓ VERIFIED | 394 lines; thin forwarders; BOX_DISPLAY_Z=5.0 shared with gate |
| `serpentrum/gui_game.py` | begin/stack/turn/end seams | ✓ VERIFIED | 1063 lines; all Phase-5 GUI halves |
| `serpentrum/gui_setup.py` | stacking_path + head_m16 | ✓ VERIFIED | 567 lines; both load paths + pure edge-on m16 |
| `serpentrum/gui.py` | tab-switch signal | ✓ VERIFIED | 141 lines; model-A ownership (GameTab never reaches parent) |
| `serpentrum/__init__.py` | anchor fields | ✓ VERIFIED | 67 lines; records/stacking_data/last_run on _serpentrum |
| 8 test files | Phase-5 pins | ✓ VERIFIED | 2730 lines total; all in `unittest discover -s tests -p test_*.py` scope; 110 phase-5 tests re-ran standalone: OK |
| `smoke/07` + `smoke/08` | REQUIRED smokes | ✓ VERIFIED | Both in REQUIRED_SMOKES; both flushed sentinels live |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| gui_setup `_on_apply` | `__init__.py` anchor | `self._anchor.records`/`.stacking_data` writes | ✓ WIRED | Lines 480-481; never module globals (locked decision 10) |
| gui_game `begin_game` | anchor records | `getattr(self._anchor, 'records', ...)` | ✓ WIRED | Line 296; works after Apply AND Restart-without-Apply |
| gui_game `_build_engine` | spawn.PickupSpawner | `spawner.first()` → `build_pickup_seed` → `GameEngine(pickups=[seed])` | ✓ WIRED | Lines 369-383; deterministic crc32 seed |
| gui_game `_handle_stack_event` | placement.resolve | pure seam decides | ✓ WIRED | Line 725; GUI only attaches/rejects/renders/logs |
| gui_game `_handle_stack_event` | engine attach/reject | attach ONLY on placed; reject_pickup ALWAYS otherwise | ✓ WIRED | Lines 731-734 / 759 + 775 ('error' guard) — every non-placed path covered |
| gui_game 'won' branch | engine.finished guard | `if engine.finished:` | ✓ WIRED | Line 592 — false YOU WIN impossible after 05-04 un-finish |
| gui_game 'turning' branch | bridge sweep_chain | ONE call per tick, delta from engine, pivot = engine.head | ✓ WIRED | Line 641 — exactly ONE call site in the GUI layer |
| gui_game 'turning' branch | engine `_rotate_xy` | same primitive, same delta, same pivot | ✓ WIRED | Lines 645-650 — pure mirror == viewer truth |
| gui_game `_end_run` | zoom AFTER teardown | `_teardown_round()` then `_present_completion()` | ✓ WIRED | Lines 947-949; zoom_chain at 982 (P5-3 ordering) |
| gui_game `_present_completion` | `_serpentrum.last_run` | anchor dict with 5 keys | ✓ WIRED | Lines 990-996 |
| gui_game `spectra_requested` | gui.py tab switch | model-A connect → setCurrentIndex(2) | ✓ WIRED | gui_game.py:270 + gui.py:77,105 |
| setloader `_build_record` | molfile.ring_cycle | same parsed record | ✓ WIRED | setloader.py:218 |
| placement `attempt_place` | stacking.place_pickup | dataset distance/lateral, no invented chemistry | ✓ WIRED | placement.py:169-173 |
| placement `resolve` | molecule_data approval gate | shipped_interactions APPROVED set | ✓ WIRED | placement.py:113-117 |
| hud_logic | placement codes | imports SKIP_*/REFUSE_* constants | ✓ WIRED | hud_logic.py:52 — one taxonomy, two consumers |
| per-tick paths | cmd reads | NONE — engine truth + pure mirrors only | ✓ WIRED | `_on_tick`/`_handle_turn_event` do zero cmd reads; `chain_object_names()` is completion-only |

### Structural Invariants

| Invariant | Status |
|-----------|--------|
| ONE `sweep_chain` call site in GUI | ✓ (gui_game.py:641 only) |
| ONE `_teardown_round` definition | ✓ (gui_game.py:1004; 4 call sites: begin_game/291, restart/929, end_run/947, shutdown/1002) |
| No `.exec_()` anywhere in serpentrum/ | ✓ (only docstring mentions of the ban) |
| Anchors on `pmg_tk.startup._serpentrum` | ✓ (never module globals) |
| zoom AFTER camera unlock | ✓ (teardown unlocks → presenter zooms) |

### Gate Results (independently re-run by verifier)

| Gate | Result |
|------|--------|
| `python3.6 tests/run_gates.py` — gate 1: syntax + plugin-path safety | PASS |
| gate 2: purity (AST) | PASS |
| gate 3: unittest (scoped discover) | PASS — **Ran 561 tests ... OK** |
| `python3.6 tests/run_gates.py --smoke` — gate 4: headless smokes (required) | PASS — **all gates green** |
| Smoke sentinels flushed | `SMOKE-OK SKELETON` (01), `VIEWER-BRIDGE` (03), `VIEWER-DEMO` (04), `LOOP-CAMERA` (05), `INPUT-WIZARD` (06), `TRANSFORM` (07), `EDGEON` (08) — 7/7 required |
| Known non-blocking | `informational smoke smoke/02_dialog_smoke.py: FAIL (non-blocking)` — the documented offscreen-Qt dead end; expected |

### Requirements Coverage

| Requirement | Status | Blocking Issue |
|-------------|--------|----------------|
| GAME-04 (pickup stacks, counts) | ✓ SATISFIED (structurally) | live confirm in 05-16 |
| GAME-05 (collisions end run, chain complete) | ✓ SATISFIED (structurally) | live confirm in 05-16 |
| GAME-06 (win at cap) | ✓ SATISFIED (structurally) | live confirm in 05-16 |
| GAME-09 (completion flow + Get Spectra) | ✓ SATISFIED (structurally) | live confirm in 05-16 |
| GAME-10 (rigid turns, refusal, no 180°) | ✓ SATISFIED (structurally) | live confirm in 05-16 |
| STACK-01 (cited geometry) | ✓ SATISFIED (structurally) | live confirm in 05-16 |
| STACK-03 (skip with reason) | ✓ SATISFIED (structurally) | live confirm in 05-16 |
| STACK-04 (info box content) | ✓ SATISFIED (structurally) | live confirm in 05-16 |
| STACK-05 (clash gate) | ✓ SATISFIED (structurally) | live confirm in 05-16 |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| serpentrum/gui.py | 9,17,33 | "Spectra page is a placeholder until Phase 7" | ℹ️ Info | Planned later-phase scope, not Phase 5 |
| serpentrum/gui_setup.py | 101,118 | `setPlaceholderText(...)` | ℹ️ Info | Legitimate Qt UI affordance, not a stub |
| serpentrum/game_engine.py | 52 | "tunable placeholder pinned at 3.0" (TURN_DURATION) | ℹ️ Info | Deliberate pinned constant, tested |
| serpentrum/pymol_bridge.py | 229 | "'random' → records[0] (Phase-3 placeholder)" | ℹ️ Info | Phase-3 documented behavior, unchanged |
| (all gui files) | — | `.exec_` matches are docstrings documenting the ban | ℹ️ Info | No actual calls — modeless rule intact |

**No blocker or warning anti-patterns.** No TODO/FIXME/XXX/HACK in any Phase-5 file.

### Human Verification Required

Plan 05-16 (pending final plan, wave 7) owns ONE consolidated live-PyMOL checkpoint. It must cover:

1. **Pickup materializes as an edge-on stick** — at GO! the pickup renders as sticks standing perpendicular to the screen plane at its spawn position (head = edge-on spheres after Apply).
2. **Capture stacks at cited geometry with info-box content** — steering into a pickup appends it; the info box shows the full dataset line (`+ <name>: <interaction>, 3.60 A plane gap (centroid ... @ 20.0 deg off-normal) - <verbatim explanation> [<citation>]`) and the placed plane gap equals the cited value.
3. **Rigid whole-chain turn sweep** — a perpendicular turn sweeps srp_head + all srp_seg_* together about the head pivot; no shear; chain moves as one body.
4. **Refusal/skip info lines** — an uploaded molecule capture logs the SKIP_NO_ENTRY reason; biphenyl into a clash logs the REFUSE_ATOM reason + "run continues" note and play resumes.
5. **Completion flow, win AND crash** — viewer clears live pickups, camera frames the snake, length + score + atoms revealed, breakdown printed, Get Spectra activates and switches to the Spectra tab; repeat for a crash ending.

### Gaps Summary

**None in the executed scope.** All 15 executed plans' must_haves verify against the actual code at all three levels (existence, substance, wiring); every key link is wired; both gates re-run green from scratch (561 tests + 7/7 required smokes with flushed sentinels). Plan 05-16 is the intentionally-remaining wave-7 plan (phase-closing gate pass + consolidated human checkpoint) — assessed as "pending final plan", not missing work. Its gate-half was independently reproduced here; its human-verify half cannot be automated and is the phase's single blocking human gate.

---

_Verified: 2026-09-17T19:17:13Z_
_Verifier: OpenCode (gsd-verifier)_
