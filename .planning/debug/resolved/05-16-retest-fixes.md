---
status: resolved
trigger: "05-16 human re-test (SRP_DEBUG=1) after the 2026-09-19 gameplay-override fixes: 4 decayed-play issues found — turn-refusal storm ('none of the arrow key ever works'), biphenyl re-serve cascade (REFUSE_WALL x18 on pick_0005), crashed-run leftovers riding the new run on Restart, and owner directive 'with win cap 10, box dimension must scale too'"
created: 2026-09-20T00:00:00Z
updated: 2026-09-20T00:00:00Z

---

## Current Focus

RESOLVED — all four re-test issues landed as direct-on-main commits:
7659555 (turn veto 180-only), f211d97 (refused-pickup despawn + spawn
demotion + info-box coalescing), 56dd68b (begin_game hard-clean),
98bf9f2 (cap-10 box presets). Full gates green (620 unittests);
`--smoke` PASS incl. new SMOKE-OK SCENECLR in smoke 08.

## Symptoms (from the live SRP_DEBUG=1 log)

1. Refusal storm turns: clusters of `turn refused: pickup (the swinging
   chain would clip a floating molecule)` at ticks 240-249, 380-381,
   425-471, 689-776, 1083-1120; with several floating refused pickups
   on the board, EVERY turn near them was vetoed. User: "none of the
   arrow key ever works". Run ended `crashed into boundary` at tick
   1141 after a long refusal storm. (Items 1-3 of the re-test —
   tail-follow train, rigid turn, no wall-refusals — PASSED.)
2. Biphenyl re-serve cascade: after 4 good captures (Benzene,
   Naphthalene, Anthracene, Phenanthrene, all d=3.6000), pick_0005
   Biphenyl was refused REFUSE_WALL detail=0.95 A exactly 18 times in
   a row (stacked stays 4, pickups climbs to 4) — the same re-armed
   pickup object was re-captured in a loop and stayed floating.
3. Restart leftovers: old eaten molecules from the crashed run remained
   visible AND translated with the new head, located where the old run
   crashed (~x=-29). Root cause known: pymol_bridge.move_chain_delta
   translates the wildcard `srp_head or srp_seg_*` — stale srp_seg_*
   objects rode it (begin_game only pattern-deleted srp_pickup_*).
4. Owner directive: with win cap 10, the box dimension must scale too.

## Root causes + fixes

| # | Root cause | Fix (commit) |
|---|------------|--------------|
| 1 | game_engine._sweep_check_safe body + pickup legs vetoed rigid sweeps whenever the swinging chain approached the body or a floating pickup — with several refused pickups floating, near-total turn lockout | Removed the swept pre-check ENTIRELY; a perpendicular key ALWAYS opens the rigid sweep (visual clipping owner-accepted: "a silly outcome is recoverable; a frozen snake is not"). The only remaining turn refusal is the 180 backward key, dropped at request time in request_direction (DBG 'dropped: 180 reversal' line preserved). GAME-05 forward-motion crash rules (head vs boundary/body) UNTOUCHED. (7659555) |
| 2 | engine.reject_pickup re-ARMED a refused pickup in place; the head looping nearby re-captured it 18x (identical REFUSE_WALL detail=0.95 A); the floating refusees also fed issue 1 | (a) Every non-placed capture resolution now DESPAWNS the eaten-then-rejected pickup — engine live-set/remaining/record list AND the viewer object (pymol_bridge.delete_object) + name tracking. (b) Demote-after-refuse: spawner.note_resolution moves a refused molecule to the back of the round-robin serve order (next spawn is a different molecule; never permanently excluded — pool 5 vs cap 10 REQUIRES repeats); consecutive refuses >= pool size latches pool_exhausted for the rest of the run (one DBG line). (c) hud_logic.ReasonCoalescer: consecutive identical skip/refuse lines collapse into a '(xN)' last-line rewrite; the first of a run always appends (STACK-05 refuse demonstrator preserved; upload SKIP_NO_ENTRY path unchanged). resume_note (G2) now logs only when a reject actually un-froze a 'won'. (f211d97) |
| 3 | begin_game only deleted srp_pickup_*; the stale chain objects rode the move_chain_delta wildcard | New module-level gui_game.rebuild_scene: pymol_bridge.cleanup_srp() deletes EVERY srp_* object BEFORE the new box/head/pickups materialize (order load-bearing). Completion-view persistence is completion->Get-Spectra-ONLY; starting a new run forfeits it (presenter untouched). smoke 08 pins the ordering via SMOKE-OK SCENECLR (stale srp_seg_99 at x=-29 + srp_pickup_stale staged, zero leftovers after rebuild). (56dd68b) |
| 4 | cap default 10 -> 10 x 3.60 = 36.0 A train + a ~36 A swing arc + floating pickups did not fit comfortably in medium +/-30 | Presets: small +/-35 (challenging), medium +/-55 (default, comfortable), large +/-85 (generous). BOX_DISPLAY_Z (5.0) UNCHANGED — the biphenyl z-overshoot REFUSE_WALL at placement is the DESIGNED refuse demonstrator and stays. (98bf9f2) |

## Final preset values + straight-fit table

BOX_PRESETS (xy half-extents, Angstrom):

    small  +/-35   medium  +/-55   large  +/-85   (default: medium)

Straight-fit: max N segments with 3.6*N <= 2H - 2*BOUNDARY_MARGIN_A(1.0):

| preset | span | usable (2H - 2.0) | straight segments N | cap-10 verdict |
|--------|------|-------------------|---------------------|----------------|
| small  | 70   | 68.0              | 18 (68//3.6)        | fits, tight turns (challenging) |
| medium | 110  | 108.0             | 30 (108//3.6)       | 3x straight room (comfortable) |
| large  | 170  | 168.0             | 46 (168//3.6)       | generous |

## Final gates state

- `python3.6 tests/run_gates.py` — gate 1 syntax+plugin-path PASS,
  gate 2 purity PASS, gate 3 unittest 615 PASS.
- `python3.6 tests/run_gates.py --smoke` — all 7 required smokes flush
  SMOKE-OK; smoke 08 flushes all 7 sentinels (EDGEON, PLACE360,
  PLANEPAR, SPAWNOFFS, HEADRESET, PICKUPS, SCENECLR — the new fix-C
  ordering pin); smoke 02 informational FAIL known (Qt widget headless)
  as before.

## Re-test checklist (what the user should now see)

1. Fix A: arrow keys ALWAYS turn (rigid sweep), even next to floating
   molecules or the snake's own body — the chain may visually swing
   through them; only the 180 backward key is refused (silent drop +
   DBG 'dropped: 180 reversal' under SRP_DEBUG=1). Straight into a wall
   still crashes the run.
2. Fix B: a refused/skipped molecule vanishes from the board on
   capture (no floating refusees), the NEXT spawn is a different
   species (biphenyl waits one round-robin pass, never banned), and a
   refuse streak prints once with a '(xN)' suffix instead of one line
   per capture. NOTE: the biphenyl placement refuse message appearing
   at least once is BY DESIGN (STACK-05 must-have demonstrator).
3. Fix C: Restart after a crash starts on a clean board — no eaten
   molecules from the old run anywhere, nothing drifting with the new
   head (the completion screen's chain view survives only until you
   press Get Spectra or start a new run, as designed).
4. Fix D: the boxes are bigger (default medium is now a 110 A square);
   a 10-molecule straight train fits with maneuvering room.

## Follow-up (2026-09-20, same day): game-3 deadlock — permanent pool_exhausted latch

**Symptom (live SRP_DEBUG=1 log, game 3 near the small-box +/-35
walls):** five consecutive placements refused REFUSE_WALL with tiny
positional overshoots (0.76 / 0.81 / 0.83 / 0.83 A past the box edge)
as the head patrolled the wall; the demote-after-refuse round-robin
cycled all 5 demo molecules, then the pool_exhausted latch (f211d97)
fired:

    DBG spawn pool exhausted (5 molecule(s) refused in a row) - no more
    pickups this run

and spawning stopped PERMANENTLY — the run became unwinnable and
un-feedable even though the refuses were position-dependent: once the
head moved away from the wall, the same placements succeeded again.

**Root cause:** the latch conflated "every candidate refused
consecutively" (a local, REVERSIBLE board state) with "the pool can
never succeed" (a global, terminal state). Near a wall streak ==
pool size is EASY to reach and self-resolving — a permanent latch is
the wrong consequence for a temporary condition.

**Fix (ee2a1d8 + 6b3017a): pool exhaustion is a resumable COOLDOWN,
never permadeath.**

- Refuse streak reaching the pool size now PAUSES spawning for
  `spawn.EXHAUST_COOLDOWN_TICKS = 100` movement ticks (~10 s at the
  100 ms game tick; module-level constant so it is tunable, accepted
  via the `exhaust_cooldown_ticks` constructor kwarg for tests).
- The controller advances the clock once per movement tick
  (`gui_game._on_tick` -> `spawner.tick()`); pause-of-game freezes the
  clock in play time. On the resume edge the streak resets and one
  spawn attempt fires immediately with the SAME slot policy as before.
- The refuse streak does NOT advance while paused (no extend, no
  refresh); a placed capture still resets the streak immediately;
  re-pausing after a resume requires a FRESH pool-size streak.
- DBG lines (SRP_DEBUG=1 only): on pause
  `DBG spawn pool cooldown (N refused in a row) - spawning paused K ticks`,
  once per episode; on resume
  `DBG spawn pool cooldown over - spawning resumed`.
- NOT changed: demote-after-refuse round-robin, refused-pickup
  despawn, ReasonCoalescer, REFUSE_WALL/REFUSE_ATOM gate tolerances,
  biphenyl demonstrators, GAME-05 crash rules.

**Chosen K = 100 ticks (~10 s).** Long enough that a permanent wall
hug produces quiet, pause-bounded feeding pauses instead of a refuse
storm; short enough that the transient near-wall case (the deadlock
scenario) recovers within one cruising pass — at 0.3 A/tick the head
travels 30 A during the window, comfortably farther than the 8 A
lookahead that was producing the wall overshoots.

**Re-test expectation:** in the same near-wall situation the refuse
streak now pauses spawning for ~10 s with (under SRP_DEBUG=1) the
cooldown line, then feeding resumes automatically once the head has
moved on — the run stays winnable.
