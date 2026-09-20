---
phase: 05-stacking-game-rules
verified: 2026-09-20T17:11:41Z
status: passed
score: 16/16 plans verified (48/48 plan truths incl. 3 owner-amended); 5/5 ROADMAP criteria (1 amended-verified); 9/9 requirements delivered as amended
re_verification:
  previous_status: human_needed
  previous_score: 15/15 executed plans verified (05-16 pending final plan; 5/5 ROADMAP success criteria structurally verified)
  gaps_closed:
    - "05-16 phase-closing plan executed: gates green (640 unittests + 7/7 required smokes) AND the 8-step consolidated human checkpoint APPROVED BY EVIDENCE across 7 live rounds (2026-09-18..20)"
    - "All five live-GUI truths deferred on 2026-09-17 are now human-verified in the checkpoint register (edge-on materialization, dataset-exact stacking with info content, rigid whole-chain sweep, refusal/skip info lines, completion flow win AND crash with Get Spectra)"
    - "Seven owner-directive behavior overrides landed during the checkpoint were verified as the REPLACEMENT contract against actual code (register below) — none reported as gaps"
  gaps_remaining: []
  regressions: []
gaps: []
---

# Phase 5: Stacking & Game Rules Complete — FINAL Verification Report

**Phase Goal:** The complete v1 game: pickups stack onto the chain at cited geometry, turns pivot the whole chain rigidly, collisions end runs, and both wins and crashes hand a complete snake to the spectra stage.
**Verified:** 2026-09-20T17:11:41Z (HEAD b0ed958, tree clean)
**Status:** **passed** — phase ready for wrap-up
**Re-verification:** Yes — after 05-16 execution + 7-round human checkpoint + 7 owner-directive amendments

**Verdict basis:** must_haves were written pre-checkpoint; seven were DELIBERATELY replaced by owner directives during the 05-16 live checkpoint (lineage: STATE.md Decisions 2026-09-18/19/19b/19c/19d/20). This report verifies the REPLACEMENT behavior against actual code and marks each replaced item **verified as owner-amended** with commit evidence. Replaced items are NOT gaps.

## Goal Achievement

### ROADMAP Success Criteria (goal-backward)

| # | Criterion (as written) | Status | Evidence |
|---|------------------------|--------|----------|
| 1 | Pickup appends at dataset-stored stacking geometry (placed distance == cited value), counts tracked, info box shows interaction name, distance, explanation, citation | ✓ VERIFIED | `attempt_place` drives `stacking.place_pickup` with `interaction['distance_a']`/`lateral_offset_a` — no invented chemistry (placement.py:160-179); `sqrt(3.383²+1.231²)=3.6000 Å @ 20.0°` pinned in tests + smoke 08 PLACE360 flushed live this session; `pickup_block` composes the full dataset line (hud_logic.py:89-108); counters via `attach_segment` + `molecules_stacked`/`atoms_total`; **human: round 2-3 DBG logs `dot=1.000000 d=3.6000` on every capture** |
| 2 | Turn sweeps the whole chain as a rigid body; sweep hitting boundary/body **refused**; 180° reversal impossible **[AMENDED]** | ✓ VERIFIED AS OWNER-AMENDED | Rigid sweep INTACT: ONE `sweep_chain(delta, engine.head)` call site (gui_game.py:814) → `cmd.rotate('z', delta, 'srp_head or srp_seg_*', camera=0, origin=[hx,hy,0])` (pymol_bridge.py). Owner directives cd04525 (2026-09-19: head-only wall veto) + 7659555 (2026-09-19b: 180°-ONLY veto — body/pickup/boundary sweep pre-check legs DELETED, `_sweep_check_safe`/`SWEEP_PICKUP_CLEARANCE_A` retired with zero functional references) mean every perpendicular turn executes and the chain may visually swing through anything during a turn. 180° reversal still impossible (game_engine.py:358-400: dot < -0.5 refused at rest AND while sweeping). Straight-motion GAME-05 crash rules UNTOUCHED (step(): boundary :661, body :679). Pins: test_engine_turn_veto_ghost.py (`test_180_key_is_the_one_remaining_refusal`, `test_body_fixture_now_opens`, `test_pickup_fixture_now_opens`, `test_left_sweep_completes_and_tail_may_clip_outside_box`); **human: rounds 2-4 (rigid train sweep), rounds 3-4 (zero wrong refusals in 1000+ DBG ticks)** |
| 3 | Hitting boundary or own body ends the run leaving the snake complete; win when length exceeds cap | ✓ VERIFIED | Engine step() pinned order moved→boundary→body→stacked→budget→won; `_teardown_round` deletes ONLY `srp_pickup_*` (gui_game.py:1355) — `srp_head`/`srp_seg_*` survive; 'won' fires on cap, GUI guarded by `engine.finished` (gui_game.py:702-704) with the 05-04 un-finish preventing false wins; **human: round 2 (crash), round 3 (cap-10 win on medium), rounds 6-7 (cap-10 win on small)** |
| 4 | On completion (win or crash): viewer clears, camera focuses completed snake, length + score display, Get Spectra activates | ✓ VERIFIED | `_end_run` → `_teardown_round` → `_present_completion` (gui_game.py:1256→1262); `zoom_chain()` AFTER teardown/unlock (gui_game.py:1291, P5-3 ordering); `hud_logic.completion_lines` + `breakdown_lines`; `last_run` anchor (gui_game.py:1299); `get_spectra_btn.setEnabled(True)` presenter-only (gui_game.py:1306); `spectra_requested` Signal (gui_game.py:263, emit :343) → gui.py:77 → `setCurrentIndex(2)` (:105); **human: rounds 2/4 (win + crash completion parity, spectator-confirmed Spectra-tab switch)** |
| 5 | Unverified-dataset pickups skipped with reason in info box; clash gate rejects colliding placements | ✓ VERIFIED | `resolve_skip` ordered taxonomy SKIP_NO_ENTRY→NOT_APPROVED→MODE→NO_RING (placement.py:95-130), pre-resolved BEFORE any geometry in the capture seam (gui_game.py:917 — the 2026-09-20c fix G1 that makes the upload `NoneType has no len()` crash structurally impossible); approval gate via `shipped_interactions` APPROVED set (DATA-02); REFUSE_ATOM clash gate INTACT (placement.py:85, :255) and is the STACK-05 demonstrator (biphenyl 1.87 Å); `reject_pickup` on EVERY non-placed outcome incl. the 'error' last resort; **human: round 4 (upload clean skip + edge-on), rounds 6/7 (demo-mode note, (xN) coalescing, skipped-Nx recap), rounds 3-7 (biphenyl REFUSE_ATOM by design)** |

**Score:** 5/5 success criteria verified (criterion 2 verified as owner-amended)

### Per-Plan Must-Have Verification (16/16)

| Plan | Must-have focus | Status | Evidence |
|------|----------------|--------|----------|
| 05-01 | `molfile.ring_cycle` canonical 6-ring in walk order | ✓ verified (as written) | `def ring_cycle` in molfile.py; bounded-DFS + canonical (length, lex); tests/test_ring_cycle.py pins 5 canonical tuples + sorted-order-fails + determinism; consumed by setloader + tail frames |
| 05-02 | TTT matrix layout + edge-on canonicalization | ✓ verified (as written) | orientation.py: `matrix_rt`/`mat_vec3`/`edge_on_frame`/`edge_on_m16`/`edge_on_atoms`; probe-A1 fixture + z-span anchors; smoke 08 EDGEON/PLANEPAR flushed live this session |
| 05-03 | Deterministic seeded spawner | ✓ verified (as written) | spawn.py `PickupSpawner` + `build_pickup_seed` via `zlib.crc32`; MAX_LIVE_PICKUPS=4, clearance legs intact (WALL_MARGIN_A 3.5, HEAD 5.0, CHAIN_ATOM 3.0, LIVE_PICKUP 6.0); deterministic-seed pins green; spawn-side policy extensions (despawn/demote/cooldown) are additive owner amendments, not contradictions |
| 05-04 | reject_pickup un-finish (win-vs-clash desync) | ✓ verified (as written) | game_engine.py rolls counters back and un-finishes ONLY `finished and result=='won' and molecules_stacked < cap`; crashed runs stay terminal; live in the capture seam (gui_game.py unfinishes_won check before reject) |
| 05-05 | Placement controller seam | ✓ verified (truths 1-2 as written; truth 3 owner-amended) | `resolve`/`resolve_skip`/`tail_frame`/`attempt_place` + outcome contract intact; skip taxonomy pre-geometry (fix G1); **amended:** original truth 3 said the gate "refuses wall/atom violations" — owner directive d33f74c (2026-09-19d) retired the wall leg: `gate()` feeds an effectively UNBOUNDED box (placement.py:192-207, documented "remove the refuse (let it stack out of box since we only bound the head in box)"), only REFUSE_ATOM refuses — the STACK-05 demonstrator |
| 05-06 | Anchors records/stacking_data/last_run + stacking_path wiring | ✓ verified (as written) | `_SerpentrumState` records/stacking_data/last_run on `pmg_tk.startup._serpentrum`; gui_setup passes `stacking_path=setloader.default_stacking_path()` into both load paths and anchors results |
| 05-07 | Bridge primitives + REQUIRED smoke 07 | ✓ verified (as written) | `apply_matrix`/`sweep_chain`/`zoom_chain`/`delete_pickups`/`rename_pickup`/`chain_object_names` + `move_chain_delta` (added by amendment 3); smoke 07 flushed `SMOKE-OK TRANSFORM` live this session |
| 05-08 | stack_ring carry on demo records | ✓ verified (truth 2 owner-amended) | Demo records carry `stack_ring = molfile.ring_cycle(...)` at load (unchanged); **amended:** original truth 2 said "Upload records NEVER carry stack_ring" — owner directive 93f4b2b/22b7245 (2026-09-19d) now gives uploads WITH a canonical planar 6-ring a display-only `stack_ring` driving edge-on render parity (setloader.py:35-39, 89-98); the skip-policy keying is intact because it keys on `has_stack_entry` (the missing dataset entry), never on the ring |
| 05-09 | STACK-04 HUD builders | ✓ verified (as written + extended) | `pickup_block`/`skip_text`/`reason_text`/`budget_text`/`completion_lines`/`breakdown_lines`/`idle_tip`/`resume_note` + owner-added `stack_mode_note` (:134), `ReasonCoalescer` (:226, '(x%d)' :259), recap taxonomy in `breakdown_lines` (:171-186); imports placement code constants (one taxonomy, two consumers) |
| 05-10 | Edge-on materialization + pickup sticks | ✓ verified (as written + extended) | `materialize(..., head_m16)` transforms BEFORE `place_head`; gui_setup computes pure `head_m16`; extended to uploads (UPLEDGEON sentinel flushed live this session) |
| 05-11 | begin_game seeding + head mirror + teardown pickup deletion | ✓ verified (as written + hygiene-extended) | `spawner.first()` → `build_pickup_seed` → `GameEngine(pickups=[seed])` (gui_game.py:469-475); `_teardown_round` still deletes ONLY pickups (chain survives for the completion view); **extended:** begin_game/rebuild_scene now runs `pymol_bridge.cleanup_srp()` (ALL srp_*) BEFORE materializing (56dd68b, gui_game.py:148-186) — restart leftovers can no longer ride the `move_chain_delta` wildcard; completed-snake view persists only completion→Get-Spectra |
| 05-12 | Pure integration chain | ✓ verified (as written, pins updated to amended contract) | tests/test_phase5_integration.py covers win/crash/refuse/skip/un-finish; crash pins rewritten per train-follow (crash = already-overlapping pose tick-1), boundary crash pins preserved (test_engine_rules.py: 4 wall crashes, precedence, strict comparison) |
| 05-13 | Capture seam | ✓ verified (as written + extended) | `_handle_stack_event`: ONE synchronous resolution per 'stacked'; attach+apply_matrix+rename on placed; reject_pickup ALWAYS otherwise; **extended:** skip pre-resolved BEFORE geometry (gui_game.py:917), refused pickups DESPAWN (engine set + engine.pickups filter + `pymol_bridge.delete_object`), skips feed `refused=False` (never latch the cooldown, fix G1) |
| 05-14 | Rigid sweep rendering + budget advisory | ✓ verified (as written) | ONE `sweep_chain` call per tick (gui_game.py:814), delta = `angle_signed/total_ticks`, final tick reuses stored `last_turn_delta` (:813), pure `_rotate_xy` mirror; `'budget_warning'` logs count-free `budget_text()` (:700-701); turn_refused handler now only ever sees the 180-reversal reason (:66-75) |
| 05-15 | Completion presenter + Get Spectra signal | ✓ verified (as written) | `_present_completion` (:1262): verdict → teardown → zoom → completion_lines → breakdown → last_run anchor → presenter-only enable; model-A signal → gui.py `setCurrentIndex(2)`; button disabled at construction (:307)/teardown |
| 05-16 | Phase-closing gates + consolidated human checkpoint | ✓ verified (this report) | Gates re-run green from scratch THIS SESSION (640 unittests; 7/7 required smokes incl. smoke 08 8/8 internal sentinels); the 8-step live checkpoint APPROVED BY EVIDENCE across 7 rounds (register below); 24 checkpoint-window commits enumerated in 05-16-SUMMARY |

**Score:** 16/16 plans verified (48/48 plan must-have truths; 3 truths verified-as-owner-amended: 05-05 t3, 05-08 t2, 05-16's "refused-or-not sweeps" clause)

### Owner-Amendment Register (the replacement contract, verified against code)

| # | Directive | Supersedes | Commits | Code evidence | Human checkpoint |
|---|-----------|-----------|---------|---------------|------------------|
| 1 | Turn veto = 180° reversal ONLY; body/pickup/boundary sweep pre-check legs deleted; every perpendicular turn executes; chain may visually swing through anything during a turn | Original GAME-10 sweep-refusal legs (ROADMAP criterion 2, plans 05-05/05-14/05-16 text) | cd04525, 7659555 | `_sweep_check_safe`/`SWEEP_PICKUP_CLEARANCE_A` gone (only a documented "since-REMOVED" hygiene comment remains, spawn.py:94-96); `request_direction` refuses ONLY dot < -0.5 (game_engine.py:358-400); straight-motion boundary/body crash untouched (step() :661/:679); test_engine_turn_veto_ghost.py pins the rewritten semantics | Rounds 3-4: zero wrong refusals in 1000+ DBG ticks; rigid sweep rounds 2-4 |
| 2 | REFUSE_WALL placement gate REMOVED — stacked chain may extend outside the box on any axis; only the HEAD is box-bound; REFUSE_ATOM clash gate INTACT (STACK-05 demonstrator, biphenyl 1.87 Å) | placement.py wall leg (ROADMAP criterion 5 wall flavor, plan 05-05 truth 3) | d33f74c | placement.py: no REFUSE_WALL constant; `gate()` box effectively unbounded, params retained for call-site stability (:192-207); REFUSE_ATOM returned at :255; head-only box-bound documented game_engine.py:21-33; setup_logic.py:86-89 cross-reference | Rounds 3-7: biphenyl REFUSE_ATOM appears by design every window, pickup despawns, run continues; round 6: near-wall stacking + small-box win |
| 3 | TRAIN-FOLLOW tail — whole chain translates rigidly with the head every 'moved' tick; stacking spacing immutable 3.60 Å (DATA-02-approved 3.60 Å @ 20°; dataset file UNCHANGED) | Stationary-tail engine model | 76d74b3 | `_translate_chain` (game_engine.py:511, called every moved tick :649); `move_chain_delta(dx,dy,dz=0,selection='srp_head or srp_seg_*')` (pymol_bridge.py:179, called gui_game.py:640); test_engine_tail_follow.py pins exact head delta, constant head↔newest distance, capture-then-travel 3.6 Å spacing, sweep ticks don't translate | Rounds 2-3: `dot=1.000000 d=3.6000` on every capture line |
| 4 | Box presets small ±35 / medium ±55 / large ±85 (cap-10 winnability); BOX_DISPLAY_Z 5.0 unchanged | Research-R7 presets (±12/±18/±25, then ±20/±30/±45) | 69b8fb0, 98bf9f2 | setup_logic.py:90-94 `BOX_PRESETS` exact values; straight-fit table documented :80-84; BOX_DISPLAY_Z = 5.0 (pymol_bridge.py:66) | Round 6-7: cap-10 wins on small |
| 5 | Spawn policy: refused pickups DESPAWN; demote-after-refuse round-robin (never permanent exclusion); exhaustion = 100-tick resumable cooldown (EXHAUST_COOLDOWN_TICKS), never a permanent latch; skips NEVER feed the refuse streak; HUD ReasonCoalescer (xN) | "pickup stays visible, run continues" + permadeath latch from f211d97's first cut | f211d97, ee2a1d8, 6b3017a | gui_game.py capture seam despawn (engine.live_pickup_ids.discard + pickups filter + `delete_object`); `note_refuse` demote round-robin (spawn.py:230-263); EXHAUST_COOLDOWN_TICKS=100 resumable cooldown (spawn.py:99, cooldown state machine :187-216); skips feed refused=False (gui_game.py:1017-1022); `ReasonCoalescer` '(x%d)' (hud_logic.py:226/259) | Rounds 3-7: refuse storms ended; round 4 games 1-2 approved post-cooldown |
| 6 | Restart hygiene: begin_game/rebuild_scene runs cleanup_srp (ALL srp_*) BEFORE materializing; completed-snake view persists only completion→Get-Spectra | 05-11's pickup-only teardown as the sole restart defense | 56dd68b | gui_game.py:148-186 `rebuild_scene` — `pymol_bridge.cleanup_srp()` FIRST, then box + head materialize ("ORDER IS LOAD-BEARING"); begin_game calls it; smoke 08 SCENECLR flushed live this session | Rounds 3-4: "new game after win is ok"; no leftovers/wildcard-riding |
| 7 | Upload path: captures with no dataset entry resolve to SKIP BEFORE any geometry (reason in info box, never an exception); uploads with a canonical planar 6-ring (incl. upload head) render edge-on; zero-stackable sets get a one-time begin_game "demonstration mode" info line (`hud_logic.stack_mode_note`) | 05-13's skip-as-only-upload-handling; 05-08's uploads-never-carry-stack_ring | 93f4b2b, 22b7245, 64882c3 | gui_game.py:917 `resolve_skip` BEFORE tail/place (fix G1 — the NoneType crash structurally impossible); setloader.py:35-39/89-98 display-only upload `stack_ring`; `stack_mode_note` (hud_logic.py:134) logged once per run (gui_game.py:418-420); UPLEDGEON sentinel flushed live this session | Round 4: clean skip + edge-on rings; round 7: demo-mode note + "skipped 5x" recap |
| 8 | End-of-run recap taxonomy: SKIP_* → "skipped Nx", REFUSE_* → "refused Nx" | Undifferentiated breakdown labels | e0b2814 | hud_logic.py `breakdown_lines` groups by outcome-code prefix (:171-186, "the names are the contract") | Round 7: recap reads "skipped 5x 931:" |

### Key Link Verification (spot-checked this session)

| From | To | Via | Status | Evidence |
|------|----|----|--------|---------|
| gui_game turning branch | pymol_bridge.sweep_chain | ONE call per tick, pivot = engine.head | ✓ WIRED | gui_game.py:814 — exactly ONE call site in the GUI layer |
| gui_game moved tick | pymol_bridge.move_chain_delta | train-follow translation, same delta as engine | ✓ WIRED | gui_game.py:640; bridge selection 'srp_head or srp_seg_*' (pymol_bridge.py:179) |
| gui_game capture seam | placement.resolve / resolve_skip | skip pre-resolved BEFORE geometry; pure seam decides | ✓ WIRED | gui_game.py:917 (resolve_skip) → :939 (resolve); GUI only attaches/rejects/renders/logs |
| gui_game capture seam | engine.attach_segment / reject_pickup | attach ONLY on placed; reject + despawn on EVERY non-placed outcome | ✓ WIRED | gui_game.py placed branch + reject branch incl. 'error' last-resort; despawn triple (engine set, engine.pickups, viewer object) |
| placement.attempt_place | stacking.place_pickup | dataset distance_a/lateral_offset_a — no invented chemistry | ✓ WIRED | placement.py:176-179 |
| placement.resolve_skip | molecule_data.shipped_interactions | DATA-02 APPROVED-set approval gate | ✓ WIRED | placement.py:119-122 |
| gui_game _end_run | _teardown_round → _present_completion | teardown deletes pickups ONLY; zoom AFTER unlock (P5-3) | ✓ WIRED | gui_game.py:1256→1262; zoom_chain :1291 |
| gui_game _present_completion | `_serpentrum.last_run` + Get Spectra enable | anchor record; presenter-only enable | ✓ WIRED | gui_game.py:1299, :1306 |
| GameTab spectra_requested | gui.py tab switch | model-A Signal → setCurrentIndex(2) | ✓ WIRED | gui_game.py:263/:343 → gui.py:77/:105 |
| hud_logic | placement code constants | one taxonomy, two consumers | ✓ WIRED | hud_logic.py:52 `from . import placement` |
| gui_setup _on_apply | `_serpentrum` anchor | records/stacking_data writes; stacking_path into both load paths | ✓ WIRED | (unchanged since 2026-09-17 verification; diff-scoped) |
| begin_game | spawn.PickupSpawner | spawner.first → build_pickup_seed → GameEngine(pickups=[seed]) | ✓ WIRED | gui_game.py:469-475 |
| won branch | engine.finished guard | false YOU WIN impossible after 05-04 un-finish | ✓ WIRED | gui_game.py:702-704 |

### Requirements Coverage (delivered as amended)

| Requirement | Status | Notes |
|-------------|--------|-------|
| GAME-04 (pickup stacks, counts tracked) | ✓ SATISFIED | dataset-exact placement + counters; human rounds 2-3 |
| GAME-05 (collisions end run, chain complete) | ✓ SATISFIED (as amended) | straight-motion head vs boundary/body crash INTACT; train-follow rewrote the body-crash fixture (crash = already-overlapping pose tick-1) with pins preserved/extended |
| GAME-06 (win at cap) | ✓ SATISFIED | cap-10 wins human-verified on medium (round 3) and small (rounds 6-7); 05-04 un-finish keeps sub-cap refusal from trapping |
| GAME-09 (completion flow + Get Spectra) | ✓ SATISFIED | win AND crash share one path; Spectra-tab switch human-confirmed (round 4) |
| GAME-10 (rigid turns, refusal, no 180°) | ✓ SATISFIED (as amended — the shipped contract) | 180-only veto + rigid whole-chain sweep rendering + immutable 3.60 Å spacing ARE the amended GAME-10; REQUIREMENTS.md already carries the 2026-09-20 behavior note awaiting status flip at wrap-up |
| STACK-01 (cited geometry) | ✓ SATISFIED | 3.6000 Å end-to-end (smoke 08 PLACE360 + human DBG d=3.6000) |
| STACK-03 (skip with reason, no invented chemistry) | ✓ SATISFIED | pre-geometry skip taxonomy; upload parity; demo-mode note |
| STACK-04 (info box content) | ✓ SATISFIED | dataset-composed pickup block, skip/refuse reasons, breakdown, idle tips, (xN) coalescing |
| STACK-05 (clash gate) | ✓ SATISFIED | REFUSE_ATOM intact; biphenyl 1.87 Å the designed demonstrator (human rounds 3-7) |

### Gates Evidence (re-run from scratch by this verification)

| Gate | Result |
|------|--------|
| `python3.6 tests/run_gates.py` — gate 1: syntax + plugin-path safety | PASS |
| gate 2: purity (AST) | PASS |
| gate 3: unittest (scoped discover) | PASS — **Ran 640 tests ... OK** (matches the expected ~640) |
| `python3.6 tests/run_gates.py --smoke` — gate 4: headless smokes (required) | PASS — **all gates green** |
| Required sentinels flushed | `SMOKE-OK SKELETON` (01), `VIEWER-BRIDGE` (03), `VIEWER-DEMO` (04), `LOOP-CAMERA` (05), `INPUT-WIZARD` (06), `TRANSFORM` (07) — 6/6 single-sentinel smokes |
| Smoke 08 internal sentinels (run directly this session) | **8/8:** `SMOKE-OK EDGEON`, `SMOKE-OK PLACE360`, `SMOKE-OK PLANEPAR`, `SMOKE-OK SPAWNOFFS`, `SMOKE-OK HEADRESET`, `SMOKE-OK PICKUPS`, `SMOKE-OK SCENECLR`, `SMOKE-OK UPLEDGEON` — zero SMOKE-FAIL |
| Known non-blocking | `informational smoke smoke/02_dialog_smoke.py: FAIL (non-blocking)` — the documented 01-05 offscreen-Qt dead end; expected, never retried (plan lock) |

### Dataset Integrity Spot-Check

- `serpentrum/data/stacking_pi_stack.json`: `distance_a = 3.383`, `lateral_offset_a = 1.231` → centroid-centroid 3.60 Å @ 20.0° off-normal; `status: APPROVED`; citation janiak2000 (DOI 10.1039/b003010o).
- Unchanged since Phase 2 approval (last commit e0e7b00, 02-11); git-clean at verification time. The 3.60 Å spacing is immutable under the train-follow amendment (pinned by test_engine_tail_follow.py).

### Human Checkpoint Register (7 live rounds, 2026-09-18..20 — from 05-16-SUMMARY verdicts table)

All steps APPROVED BY EVIDENCE from the owner's final-pass logs:

| # | Checklist item | Verdict | Round(s) & evidence |
|---|----------------|---------|---------------------|
| 1a | STACK + GEOMETRY: train-follow; rigid sweep; spacing pinned 3.60 Å | APPROVED | 2-3 — `dot=1.000000 d=3.6000` on every capture line in the DBG logs |
| 1b | RIGID TURN — wall-refusals gone (head-only veto era) | APPROVED | 3 |
| 1c | Near-wall stacking after REFUSE_WALL removal | APPROVED | 6 — small-box win with wall-adjacent placements |
| 2 | Turn veto = 180° only; body/pickup silent-pass everywhere | APPROVED | 3-4 — zero wrong refusals in 1000+ ticks of DBG logs |
| 3 | CRASH: head-wall crash ends run; snake complete; completion + Get Spectra | APPROVED | 2 (crash); parity re-confirmed 4 |
| 4 | SKIP: upload captured → clean skip, run continues | APPROVED | 4 (clean skip + edge-on); 6/7 (demo-mode note + (xN) + skipped-Nx recap) |
| 5 | REFUSE demonstrator: biphenyl REFUSE_ATOM clash (1.87 Å) | APPROVED | 3-7 — by design every window; despawn + run continues |
| 6 | WIN + COMPLETION: cap-10, smooth gameplay | APPROVED | 3 (medium); 6+7 (small); Spectra-tab switch spectator-confirmed (4) |
| 7 | CRASH COMPLETION: identical presentation, Get Spectra activates | APPROVED | 2 — identical completion path as win (locked decision 8, 05-15) |
| 8 | HYGIENE: no leftovers, no wildcard-riding, deterministic restart | APPROVED | 3-4 — "new game after win is ok"; begin_game hard-clean held |
| + | Upload-only demo mode (final-pass test 2) | APPROVED | 7 — begin_game note for zero-stackable set; recap "skipped 5x 931:" |

Debug archives backing the window: `.planning/debug/resolved/05-ghost-point-turn-lock.md` (8a17a74), `05-lagging-tail-wall-box.md` (af33de9), `05-16-retest-fixes.md` (3f89779), `05-upload-only-endless-run.md` (2bff573 — C1+C4 landed; C2 soft Start-warning documented as owner opt-in, not a gap).

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| serpentrum/spawn.py | 94-96 | comment references the retired `SWEEP_PICKUP_CLEARANCE_A` | ℹ️ Info | Intentional documentation of the retired constant ("kept as spawn hygiene 2026-09-20") — no functional reference |
| serpentrum/gui.py | 9,17,33 | "Spectra page is a placeholder until Phase 7" | ℹ️ Info | Planned Phase-7 scope, not Phase 5 |
| serpentrum/xtbenv.py | 98 | bare `pass` | ℹ️ Info | Legitimate success branch in stderr classification, not a stub; not Phase-5 scope |

No TODO/FIXME/XXX/HACK, no placeholder returns, no console-only handlers in any Phase-5 file (scanned all 13 phase-touched serpentrum modules).

### Gaps Summary

**None.** All 16 plans verify against the actual code at all three levels under the amended contract; every key link sampled is wired; both gates re-run green from scratch this session (640 unittests + 7/7 required smokes with smoke 08 at 8/8 internal sentinels); the dataset is intact; the seven owner-directive amendments are all present in code with their pinned regression tests; the human checkpoint closed APPROVED with the final upload-only item resolved in round 7. The only known non-blocking items (smoke 02 informational FAIL; C2 soft Start-warning owner opt-in) are documented deliberate states, not gaps.

## Wrap-up Readiness

Phase 5 is ready for wrap-up: the ROADMAP Phase 5 row can be marked Complete (success criteria 1-5 verified, criterion 2 as owner-amended) and REQUIREMENTS GAME-04, GAME-05, GAME-06, GAME-09, GAME-10, STACK-01, STACK-03, STACK-04, STACK-05 can be flipped to Complete (GAME-10 per the 2026-09-20 amendment note already recorded in REQUIREMENTS.md). Phase 5.1 (GAME-11 speed tiers) was inserted to start AFTER this wrap-up, and its approved base (train-follow / 3.60 Å spacing / 180-only veto) is stable.

---

## Appendix: Machine-History Notes (prior verification, preserved)

### 2026-09-17 verification (superseded by this report)

- **Status then:** human_needed — structural verification fully passed (15/15 executed plans at 3 levels; 5/5 ROADMAP criteria; 561 unittests + 7/7 required smokes green at HEAD d6fc4b5); live-GUI verdicts deferred to plan 05-16's consolidated human checkpoint by design.
- **The five live-GUI items deferred then, and their resolution in the 7-round checkpoint:**
  1. "Pickup materializes as an edge-on stick" → checkpoint 1a/1c + smoke 08 EDGEON/PLANEPAR/UPLEDGEON (rounds 2-3, 6-7) — APPROVED.
  2. "Capture stacks at cited geometry with full info content" → checkpoint 1a (`dot=1.000000 d=3.6000` every capture, rounds 2-3) — APPROVED.
  3. "Rigid whole-chain turn sweep" → checkpoint 1b/2 (rounds 2-4; stationary-tail model replaced by train-follow owner directive 76d74b3 mid-window, then re-approved) — APPROVED.
  4. "Refusal/skip info lines" → checkpoint 4/5 (rounds 3-7; REFUSE_WALL removed per directive d33f74c, REFUSE_ATOM remains the demonstrator; upload skip moved pre-geometry per 93f4b2b) — APPROVED.
  5. "Completion flow — win AND crash" → checkpoint 3/6/7 (rounds 2-4, 6-7; Spectra-tab switch spectator-confirmed round 4) — APPROVED.
- **Gate-count lineage across the window:** 561 (2026-09-17) → 575 → 593 → 603 → 615 → 630 → **640** (final, re-run green this session) — growth entirely from checkpoint regression pins (train-follow, 180-veto, cooldown, upload parity, parallelism).
- The full 2026-09-17 report text is preserved in git history (`.planning/phases/05-stacking-game-rules/05-VERIFICATION.md` at ≤ b0ed958~1).

---

_Verified: 2026-09-20T17:11:41Z_
_Verifier: OpenCode (gsd-verifier)_
