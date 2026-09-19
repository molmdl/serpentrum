---
status: resolved
trigger: "i wasnt at boundary yet, the head had some distance before the wall, i was able to turn right but all other keys not working lilke after hitting a 'ghost point'"
created: 2026-09-19T00:00:00Z
updated: 2026-09-19T00:00:00Z
---

## Current Focus

hypothesis: (forming — needs reproduction: direction-specific turn refusal in the sweep pre-check)
test: scripted pure-engine + GUI-seam reproduction driving turns with head far from walls
expecting: pin the exact state where up/down/left do nothing but right turns
next_action: read test_phase5_integration.py harness, then build a pure-layer scripted reproduction

## Symptoms

expected: all four arrow keys steer (perpendiculars turn, same-dir no-op, 180 silently dropped)
actual: mid-run, after turning RIGHT once, left/up/down arrows do nothing (like hitting an invisible 'ghost point'); user was NOT at the boundary
errors: none reported by user (SRP_DEBUG=1 was forgotten — no DBG lines captured)
reproduction: live PyMOL play, after some point mid-run; prior run worked for stacking
started: 05-16 mid-flight human checkpoint live retest

## Eliminated

- hypothesis: SRP_DEBUG tracer itself throws when env var OFF
  evidence: tracer reads os.environ ONCE at begin_game into session['debug']; every debug path in gui_game (_dbg_event, _handle_turn_event debug branch, _dbg_capture_line, debug_capture_trace) is guarded by session.get('debug') — default False path is byte-identical silence; no formatting happens when off.
  timestamp: 2026-09-19

- hypothesis: engine heading could make ONLY 'right' pass request_direction filters
  evidence: heading is always an axis unit vector (only set from game_engine.DIRS); for any axis heading, both perpendiculars always pass the dot filter (dot==0). A single stable engine state cannot make exactly 'right' pass while both perpendiculars fail — the state must involve the sweep pre-check refusing one rotation direction, or the GUI seam.
  timestamp: 2026-09-19

## Evidence

- timestamp: 2026-09-19
  checked: game_engine.py request_direction / start_sweep / _sweep_check_safe
  found: (1) while NOT sweeping, request_direction is FIRST-KEPT max-1, rejects same/180 silently (return False, wizard ignores the return); (2) while sweeping, reference is the sweep TARGET with newest-wins replace; (3) start_sweep pre-check samples k=0..TURN_TICKS poses of the WHOLE chain about the head: k=0 is the CURRENT pose — if any segment centroid currently sits OUTSIDE the margin-adjusted box [box+M, box-M], EVERY turn attempt (CW and CCW both) refuses with 'boundary' at k=0 because the k=0 rotated pose equals the current pose; the FORWARD crash check never validates segment centroids being inside the box, only the head — so a run can be alive with an out-of-margin segment centroid and then refuse every turn forever.
  implication: "ghost point, not at boundary" matches: the head is far from the wall, but a placed SEGMENT centroid near/past the margin (or the swept boundary leg) vetoes turns with reason 'boundary' — which also would explain why user reads it as an invisible wall. Need to confirm what geometry placement produces (ring centroid ~3.6 A ring-ring => segment centroids near the head, not near walls... unless the box is small).

- timestamp: 2026-09-19
  checked: _sweep_check_safe k=0 pose: th = angle*0/6 = 0 -> cos=1, sin=0 exactly, so rot pose == current pose bit-exact; boundary leg at k=0 will refuse identical for CW and CCW. If refusal differs by rotation direction, the hit must be at k>0 (chain actually swinging through something), or k=0 with direction-independent state can't explain 'right works, left dead' — BUT 'up/down dead while heading=up' IS explained by same-dir/180 silent drops, and 'left dead, right works' = direction-specific k>0 refusal.
  implication: the full 'only right works' state = heading up (or down) + one-direction sweep refusal (boundary/body/pickup leg on the swept path).

## Resolution

root_cause: NOT an engine/input logic bug — the state the user hit is the PINNED rigid-chain sweep veto (GAME-10, game_engine._sweep_check_safe boundary leg) combined with the PINNED silent drops for same-direction and 180-degree keys (request_direction). Exact live state reproduced: heading 'up', head at (6,2) in the small box (margin walls ±11), 3-segment chain trailing down. Pressing up = same-direction (silent no-op by design), down = 180 reversal (silent reject by design), left = perpendicular sweep attempt refused with ('turn_refused','boundary') because the CCW swing genuinely rotates the farthest chain centroid to x=11.40 > 11 (margin wall) by 30° of the sweep (verified numerically — the chain WOULD cross the wall; the viewer would have shown the chain clipping out). right = the only geometrically safe 90° swing → opens. Head itself is 5-10 A from every wall → 'not at boundary' + 'ghost point'. After the right turn the same pattern repeats with different free/vetoed sides — keys recover whenever the swung chain clears the margin box, so NOTHING is stuck. The actual defect is the FEEDBACK layer: (1) the info box line 'turn refused: boundary' carries no explanation that the veto is about the CHAIN swinging, not the head; (2) same-dir/180 key presses are silent by design; (3) the SRP_DEBUG=1 tracer logs sweep opens/captures but ZERO lines for turn requests (accepted/rejected + why) or turn refusals — so the user's strict debug retest (if flag set) would STILL not explain the symptom.
fix: (owning layer: gui_game + hud_logic; engine untouched — Phase-2 pinned behavior verified correct) hud_logic gains turn_refuse_text(reason) (player-readable, keeps 'turn refused: <reason>' prefix per checkpoint text), classify_turn_request(unit, ref, pending_nonempty, in_sweep) + debug_turn_request(...) builders; gui_game logs the rich refusal line + a DBG turn_refused event (tick/heading/head/reason), and _begin_play binds a debug-aware steering adapter ONLY when session['debug'] so every keypress prints queued/dropped-and-why (default-off byte-identical silence).
verification: python3.6 tests/run_gates.py green (593 tests: 575 baseline + 18 new); python3.6 tests/run_gates.py --smoke green (7/7 REQUIRED sentinels incl. INPUT-WIZARD + TRANSFORM; smoke 02 informational non-blocking FAIL known); mechanism regression tests/test_engine_turn_veto_ghost.py 6/6 + hud feedback tests/test_hud_turn_feedback.py 12/12
files_changed: [serpentrum/hud_logic.py, serpentrum/gui_game.py, tests/test_engine_turn_veto_ghost.py, tests/test_hud_turn_feedback.py]
commits: [cb02333 test(05), 0af3cde fix(05)]
