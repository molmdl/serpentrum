---
status: resolved
trigger: "this would be impossible to play, seriously distort gameplay. since we can only do rigid turn, id suggest the following; 1. fix the lagging-behind tail that increase the length unreasonably, even with 1-2 eaten mol 2. only detect wall from head, ignore tail 3. increase box size of all size level, this is already medium cant play at all with 1-2 eaten mol!"
created: 2026-09-19T09:34:00Z
updated: 2026-09-19T11:20:00Z

---

## Current Focus

RESOLVED — all three owner directives landed (76d74b3, cd04525, 69b8fb0). Archiving; live retest belongs to the 05-16 checkpoint.

## Symptoms

expected: tail follows head coherently; walls only matter for the head; medium box playable with 1-2 eaten mols
actual: tail lags far behind head even after 1-2 captures; chain-vs-wall sweep veto makes turns refuse near walls; medium box unplayable
errors: none (live gameplay)
reproduction: live PyMOL play, capture 1-2 molecules, keep moving
started: 05-16 human checkpoint live play

## Eliminated

(none yet)

## Evidence

- timestamp: 2026-09-19
  checked: game_engine.py step() movement branch + placement.py tail_frame + gui_game.py _on_tick 'moved' path
  found: step() translates ONLY the head on 'moved' ticks; engine.segments (centroids+atoms) are never translated during forward motion (only rigidly rotated about the head during sweeps). placement.tail_frame chains each new capture off the NEWEST segment's current (stationary) location. gui_game translates only srp_head + the pure head mirror per tick.
  implication: the chain is a stationary trail at capture points; the head runs away at 0.3 A/tick; perceived lag grows without bound between captures.

- timestamp: 2026-09-19
  checked: reproduction /tmp/opencode/repro_tail.py (real set_a records + placement.resolve + engine)
  found: capture 1 at tick 4: head<->seg1 = 3.600 A (correct at capture). tick 20: 8.275 A (grows exactly 0.3 A/tick). capture 2 at tick 24: head<->seg2 = 13.001 A while seg1<->seg2 = 3.600 A EXACTLY (matches user verbatim "distance between the 2 eaten mol looks ok tho"). tick 60: head<->newest = 22.799 A unbounded; head crashed at margin wall 17.1 (old medium box).
  implication: hypothesis (a) confirmed — stationary-by-design chain, NOT the 3.60 A spacing (hypothesis b ruled out as the cause: inter-segment spacing is exactly correct).

- timestamp: 2026-09-19
  checked: post-fix reproduction (same /tmp/opencode/repro_tail.py on the patched engine)
  found: head<->newest constant at 3.600 A (n=1) and 7.200 A (n=2) across 120 ticks; chain span frozen at 3.600 A; head wall crash still ends the run (crashed at margin wall 17.1 as before).
  implication: Item 1 verified — chain is now a rigid train; the 3.60 A spacing holds at all times ('stacking geometry immutable at all times' now true during forward motion too).

- timestamp: 2026-09-19
  checked: pinned consumers for Items 1-3
  found: (Item 1 conflicts) test_engine_rules.py TestBodyCollision seeds a chain AHEAD of the head and expects the head to approach/crash (test_body_crash_exact_tick, test_neck_exemption_skip_proof) — relative geometry becomes invariant under train-follow -> rewrite as guard semantics; test_phase5_integration scenario 3 crash_engine re-seed must become an already-overlapping pose. (Item 2 pins) test_engine_turns.py test_boundary_refusal_centroid_leg + test_refused_chained_sweep_falls_through + module/class docstrings; test_engine_turn_veto_ghost.py (whole wall-veto expectation); hud_logic.turn_refuse_text 'boundary' + test_hud_turn_feedback.py. (Item 3 pins) test_setup_logic.py BOX_PRESETS dict; test_phase5_integration small-preset pin + medium comments; test_spawn.py BOX_MIN/BOX_MAX +-18 fixtures + limit formula. spawn.py WALL_MARGIN_A=3.5 scales off passed extents (no change). Smokes use presets by name (auto-scale). _BOX_SMALL in test_placement.py is an independent gate fixture (no preset equality pin) — leave.
  implication: full pin-change catalog known; each gets an owner-justification comment dated 2026-09-19 UTC.

## Resolution

root_cause: ITEM 1 (lagging tail): stationary-by-design chain — engine.step() translated only the head; engine.segments never translated during forward motion (only sweep-rotated), and placement chains each capture off the newest STATIONARY segment. Reproduced numerically on the real set_a pipeline: capture 1 at 3.600 A behind the head, gap growing exactly 0.3 A/tick (8.275 A after 16 ticks), capture 2 at 13.001 A from the head while seg1<->seg2 stayed 3.600 A; unbounded (22.799 A by crash). Hypothesis (a) confirmed; hypothesis (b) (unfamiliar 3.60 A spacing) ruled out as the cause — inter-segment spacing was always exactly correct. ITEM 2 (wall veto): chain-vs-wall sweep leg was geometrically correct but owner-overridden as unplayable (head-only walls). ITEM 3 (box size): a cap-10 straight chain needs 36 A + 1.0 margin — could never fit the OLD medium (36 A wide).
fix: ITEM 1 (76d74b3): engine _translate_chain on every 'moved' tick (centroids + atom x/y by the SAME head delta, z/sym preserved, fresh record dicts); bridge move_chain_delta ('srp_head or srp_seg_*', camera=0); gui_game 'moved' path uses it. Train = rigid body: translates straight, pivots on turns; 3.60 A spacing frozen at all times. Forward body collision adapted (not deleted): now a same-pose guard (constant relative geometry in straight motion); turn-time screening stays in the sweep body leg. ITEM 2 (cd04525): boundary leg removed from _sweep_check_safe (body/pickup legs remain); head forward 'crashed'/'boundary' UNCHANGED; hud_logic 'boundary' text now head-only; ghost test + engine_turns wall pins rewritten so the SAME states ALLOW the turn; 180-degree still impossible. ITEM 3 (69b8fb0): BOX_PRESETS small +-20 / medium +-30 / large +-45 (was +-12/+-18/+-25); BOX_DISPLAY_Z 5.0 unchanged; setup_logic test pin, spawn fixtures + cover lattice, phase5-integration pins updated.
verification: reproduction re-run post-fix — head<->newest constant 3.600/7.200 A (n=1/2) over 120 ticks, chain span frozen 3.600 A, head wall crash still ends the run (x crash margin now 29.0). Gates green after EVERY commit: python3.6 tests/run_gates.py (final 603 tests = 593 baseline + 6 tail-follow + 3 ghost additions + 1 net body-class addition); run_gates.py --smoke (7/7 REQUIRED sentinels incl. VIEWER-BRIDGE, LOOP-CAMERA, INPUT-WIZARD, TRANSFORM/EDGEON; smoke 02 informational FAIL known). Every engine change justified by failing-then-passing regression tests (RED recorded for all three items).
files_changed: [serpentrum/game_engine.py, serpentrum/pymol_bridge.py, serpentrum/gui_game.py, serpentrum/hud_logic.py, serpentrum/setup_logic.py, tests/test_engine_tail_follow.py (new), tests/test_engine_rules.py, tests/test_phase5_integration.py, tests/test_engine_turn_veto_ghost.py, tests/test_engine_turns.py, tests/test_hud_turn_feedback.py, tests/test_setup_logic.py, tests/test_spawn.py]
