"""GameEngine collision-and-rules tests (plan 02-10).

Covers the rules half of the engine layered on the 02-06 movement core:
boundary crash (AABB + BOUNDARY_MARGIN_A), polyline-edge self-collision
(head-centroid vs chain edges with a neck exemption), pickup capture
with controller confirm/attach-or-reject semantics, and the score/
win-cap/atom-budget counters with their crash/win/warning events.

Determinism (research §7): pure float math on fixed constants; tests set
engine state directly (plain data) and use assertAlmostEqual for
positions. SPEED_A_PER_S = 3.0 A/s with dt = 0.1 s -> exactly 0.3 A per
tick. box ((-18.0, -18.0), (18.0, 18.0)) -> margin walls at +-17.0 A
(BOUNDARY_MARGIN_A = 1.0).

Discovery command (python3.6.9 — NOTE: `-t .` FAILS on python3.6 with a
non-package start dir; do not add it):

    python3.6 -m unittest discover -s tests -p "test_*.py" -v

FORWARD-COMPATIBILITY RULE (02-06 -> 02-13, inherited): this suite NEVER
calls step() while a direction request is pending. Plan 02-13 will
consume pending turns at the START of step(); because these tests never
observe step() with a non-empty pending, that contract change cannot
break them. The crash-clears-pending contract is therefore exercised
only via post-crash state inspection (pending == []), never by stepping
with a buffered request.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from serpentrum import game_engine  # noqa: E402
from serpentrum.game_engine import GameEngine  # noqa: E402

# Test-tuning constants (mirror the engine's own pins).
DT = 0.1
STEP_A = game_engine.SPEED_A_PER_S * DT  # 0.3 A per tick at 3.0 A/s
DELTA = 1e-9

# Medium box preset (research §8): (-18, -18) to (18, 18); the margin
# walls (BOUNDARY_MARGIN_A = 1.0) sit at +-17.0.
BOX_MIN = (-18.0, -18.0)
BOX_MAX = (18.0, 18.0)
MARGIN_WALL = 17.0  # = 18.0 - BOUNDARY_MARGIN_A


class TestBoundaryCollision(unittest.TestCase):
    """Boundary crash: AABB + BOUNDARY_MARGIN_A on all four walls.

    Crash sets finished=True / result='crashed', clears the pending
    queue, and every later step() is a no-op returning []. box None
    disables boundary checking entirely (02-06's free-moving tests
    never pass a box, so they stay untouched).
    """

    def test_right_wall_crash(self):
        # Head (16.8, 0) heading right (+x): one step -> 17.1 > 17.0 ->
        # crash. Arithmetic: 16.8 + 0.3 = 17.1; 17.1 >= 17.0 -> fires.
        engine = GameEngine(head=(16.8, 0.0), heading='right',
                            box_min=BOX_MIN, box_max=BOX_MAX)
        events = engine.step(DT)
        # Event order: ('moved', ...) then ('crashed', 'boundary').
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0][0], 'moved')
        self.assertAlmostEqual(events[0][1][0], 17.1, delta=DELTA)
        self.assertEqual(events[1], ('crashed', 'boundary'))
        self.assertTrue(engine.finished)
        self.assertEqual(engine.result, 'crashed')

    def test_left_wall_crash(self):
        # Head (-16.8, 0) heading left (-x): one step -> -17.1 <= -17.0
        # -> crash. Arithmetic: -16.8 - 0.3 = -17.1; -17.1 <= -17.0.
        engine = GameEngine(head=(-16.8, 0.0), heading='left',
                            box_min=BOX_MIN, box_max=BOX_MAX)
        events = engine.step(DT)
        self.assertEqual(events[-1], ('crashed', 'boundary'))
        self.assertTrue(engine.finished)
        self.assertEqual(engine.result, 'crashed')

    def test_top_wall_crash(self):
        # Head (0, 16.8) heading up (+y): one step -> 17.1 >= 17.0 ->
        # crash.
        engine = GameEngine(head=(0.0, 16.8), heading='up',
                            box_min=BOX_MIN, box_max=BOX_MAX)
        events = engine.step(DT)
        self.assertEqual(events[-1], ('crashed', 'boundary'))
        self.assertTrue(engine.finished)
        self.assertEqual(engine.result, 'crashed')

    def test_bottom_wall_crash(self):
        # Head (0, -16.8) heading down (-y): one step -> -17.1 -> crash.
        engine = GameEngine(head=(0.0, -16.8), heading='down',
                            box_min=BOX_MIN, box_max=BOX_MAX)
        events = engine.step(DT)
        self.assertEqual(events[-1], ('crashed', 'boundary'))
        self.assertTrue(engine.finished)
        self.assertEqual(engine.result, 'crashed')

    def test_inclusive_edge_at_margin_wall(self):
        # Comparison is INCLUSIVE at the margin-adjusted wall (>= / <=).
        #
        # (a) Head starts exactly AT the wall (17.0, 0); one step lands
        #     at 17.3 -> crash (trivially >= 17.0).
        engine = GameEngine(head=(MARGIN_WALL, 0.0), heading='right',
                            box_min=BOX_MIN, box_max=BOX_MAX)
        events = engine.step(DT)
        self.assertEqual(events[-1], ('crashed', 'boundary'))
        self.assertTrue(engine.finished)
        # (b) The genuine inclusivity proof: head at 16.7, one step of
        #     exactly 0.3 -> lands at 17.0 EXACTLY. A strict > comparison
        #     would NOT fire (17.0 > 17.0 is False); the inclusive >=
        #     does. Arithmetic: 16.7 + 0.3 = 17.0.
        engine2 = GameEngine(head=(MARGIN_WALL - STEP_A, 0.0),
                             heading='right',
                             box_min=BOX_MIN, box_max=BOX_MAX)
        events2 = engine2.step(DT)
        self.assertAlmostEqual(engine2.head[0], MARGIN_WALL, delta=DELTA)
        self.assertEqual(events2[-1], ('crashed', 'boundary'))
        self.assertTrue(engine2.finished)

    def test_just_inside_no_crash(self):
        # Head (16.6, 0), one step -> 16.9 < 17.0 -> alive (no crash).
        # Arithmetic: 16.6 + 0.3 = 16.9; 16.9 >= 17.0 is False.
        engine = GameEngine(head=(16.6, 0.0), heading='right',
                            box_min=BOX_MIN, box_max=BOX_MAX)
        events = engine.step(DT)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0][0], 'moved')
        self.assertAlmostEqual(events[0][1][0], 16.9, delta=DELTA)
        self.assertFalse(engine.finished)
        self.assertIsNone(engine.result)

    def test_box_none_disables_boundary(self):
        # No box set -> head walks past where a wall would be with zero
        # crash events (02-06's free-moving default).
        engine = GameEngine(head=(16.8, 0.0), heading='right')
        for _ in range(20):
            events = engine.step(DT)
            # Only the moved event ever fires; no crash.
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0][0], 'moved')
        self.assertFalse(engine.finished)
        # Head is now well past 17.0 (16.8 + 20*0.3 = 22.8) with no crash.
        self.assertAlmostEqual(engine.head[0], 22.8, delta=DELTA)

    def test_crashed_engine_is_inert(self):
        # After a crash, a second step() returns [] and mutates nothing
        # (head unchanged). Pending-clearing on crash stays contract
        # prose only (forward-compat: this suite never steps with a
        # non-empty pending); we assert the post-crash cleared state.
        engine = GameEngine(head=(16.8, 0.0), heading='right',
                            box_min=BOX_MIN, box_max=BOX_MAX)
        engine.step(DT)  # crashes
        self.assertTrue(engine.finished)
        head_after_crash = engine.head
        events = engine.step(DT)
        self.assertEqual(events, [])
        self.assertEqual(engine.head, head_after_crash)
        self.assertEqual(engine.pending, [])


def make_seg_at(x, y, molecule_id='mol'):
    """Build a FRESH segment record with the given 2D centroid.

    The engine copies these on construction; tests pass a list of them
    as the segments seam. Atoms carry a single placeholder atom at the
    centroid (body collision uses centroids only — atoms are for
    02-13's swept pickup leg).
    """
    atoms = [('C', x, y, 0.0)]
    return {
        'molecule_id': molecule_id,
        'centroid': (x, y),
        'atoms': atoms,
        'atoms_n': len(atoms),
    }


class TestBodyCollision(unittest.TestCase):
    """Self-collision: head-centroid vs chain POLYLINE EDGES (GAME-05).

    The chain polyline connects segment centroids c[0..n-1] (index 0 =
    oldest). Edges (c[i], c[i+1]) are checked for i in range(0, n - 1 -
    SEGMENT_SKIP_RECENT); the SEGMENT_SKIP_RECENT (=2) newest edges
    nearest the head (the neck) are exempt. Crash on STRICT <
    BODY_COLLISION_RADIUS_A ** 2 (= 4.0).
    """

    def test_body_crash_exact_tick(self):
        # n=4 segments -> checked edges = edge 0 only: (c0,c1), the
        # horizontal line y=1.0 for x in [6, 10]. Head travels y=0 at
        # +0.3/step.
        #   Step 14: head (4.2, 0.0). Nearest edge point is the clamped
        #     endpoint (6.0, 1.0). dist^2 = 1.8^2 + 1.0^2 = 3.24 + 1.0
        #     = 4.24. 4.24 < 4.0? NO -> alive.
        #   Step 15: head (4.5, 0.0). dist^2 = 1.5^2 + 1.0^2 = 2.25 +
        #     1.0 = 3.25. 3.25 < 4.0? YES -> ('crashed', 'body').
        segs = [make_seg_at(6.0, 1.0, 'c0'), make_seg_at(10.0, 1.0, 'c1'),
                make_seg_at(14.0, 5.0, 'c2'), make_seg_at(18.0, 9.0, 'c3')]
        engine = GameEngine(head=(0.0, 0.0), heading='right', segments=segs)
        for k in range(1, 15):  # steps 1..14: all alive
            events = engine.step(DT)
            self.assertFalse(engine.finished,
                             'crashed early at step %d' % k)
            self.assertEqual(events[-1][0], 'moved')
        # After step 14: head at (4.2, 0.0).
        self.assertAlmostEqual(engine.head[0], 4.2, delta=DELTA)
        # Step 15: crash.
        events = engine.step(DT)
        self.assertAlmostEqual(engine.head[0], 4.5, delta=DELTA)
        self.assertEqual(events[-1], ('crashed', 'body'))
        self.assertTrue(engine.finished)
        self.assertEqual(engine.result, 'crashed')

    def test_neck_exemption_skip_proof(self):
        # Same c0/c1, but c2=(3.0, 0.0), c3=(9.0, 0.0). Edges (c1,c2)
        # and (c2,c3) are the exempt newest 2. Edge (c2,c3) is the
        # horizontal line y=0.0 from x=3..9 — the head's OWN PATH
        # (distance 0.0 at every tick while head.x is in [3, 9]) — yet
        # NO crash comes from it (skipped). The crash still arrives from
        # edge 0 at step 15 exactly as above. This proves the skip
        # window, not luck.
        segs = [make_seg_at(6.0, 1.0, 'c0'), make_seg_at(10.0, 1.0, 'c1'),
                make_seg_at(3.0, 0.0, 'c2'), make_seg_at(9.0, 0.0, 'c3')]
        engine = GameEngine(head=(0.0, 0.0), heading='right', segments=segs)
        # Steps 10..30 put the head on edge (c2,c3) at distance 0.0 —
        # but that edge is exempt. No crash from it.
        for k in range(1, 15):
            events = engine.step(DT)
            self.assertFalse(engine.finished,
                             'crashed early at step %d (neck not exempt?)' % k)
        # Step 15: crash from edge 0 (c0,c1), NOT from the exempt edge.
        events = engine.step(DT)
        self.assertAlmostEqual(engine.head[0], 4.5, delta=DELTA)
        self.assertEqual(events[-1], ('crashed', 'body'))
        self.assertTrue(engine.finished)

    def test_strict_comparison_exactly_radius_no_crash(self):
        # Edge (0,2)-(4,2): horizontal at y=2.0, x in [0, 4]. Pre-step
        # head (1.7, 0.0) heading right -> post-step (2.0, 0.0). Nearest
        # edge point (2.0, 2.0). dist^2 = 0 + 2.0^2 = 4.0.
        # STRICT <: 4.0 < 4.0 is False -> NO crash.
        # (n=4 so edge 0 is checked; c2/c3 far away and exempt.)
        segs = [make_seg_at(0.0, 2.0, 'c0'), make_seg_at(4.0, 2.0, 'c1'),
                make_seg_at(100.0, 100.0, 'c2'),
                make_seg_at(200.0, 200.0, 'c3')]
        engine = GameEngine(head=(1.7, 0.0), heading='right', segments=segs)
        events = engine.step(DT)
        self.assertAlmostEqual(engine.head[0], 2.0, delta=DELTA)
        self.assertFalse(engine.finished)
        self.assertEqual(events[-1][0], 'moved')

    def test_strict_comparison_just_under_radius_crashes(self):
        # Same edge. Pre-step head (1.7, 0.01) heading right -> post-step
        # (2.0, 0.01). Nearest edge point (2.0, 2.0). dist^2 = 0 +
        # (2.0 - 0.01)^2 = 1.99^2 = 3.9601. 3.9601 < 4.0 -> crash.
        segs = [make_seg_at(0.0, 2.0, 'c0'), make_seg_at(4.0, 2.0, 'c1'),
                make_seg_at(100.0, 100.0, 'c2'),
                make_seg_at(200.0, 200.0, 'c3')]
        engine = GameEngine(head=(1.7, 0.01), heading='right', segments=segs)
        events = engine.step(DT)
        self.assertAlmostEqual(engine.head[0], 2.0, delta=DELTA)
        self.assertAlmostEqual(engine.head[1], 0.01, delta=DELTA)
        self.assertEqual(events[-1], ('crashed', 'body'))
        self.assertTrue(engine.finished)
        self.assertEqual(engine.result, 'crashed')

    def test_crash_precedence_boundary_over_body(self):
        # A tick where the head crosses BOTH a wall and an edge. Boundary
        # check runs first -> exactly one ('crashed', ...) event and it
        # is 'boundary'; the body crash (which would also fire) never
        # runs.
        #   Box ((-18,-18),(18,18)) -> margin walls at +-17.0.
        #   Edge 0: c0=(17.1, 2.0), c1=(17.1, -2.0) — vertical at x=17.1.
        #   Head (16.8, 0.0) heading right -> post-step (17.1, 0.0).
        #   Boundary: 17.1 >= 17.0 -> crash. Body: head ON the edge
        #   (distance 0.0) but body check never runs.
        segs = [make_seg_at(17.1, 2.0, 'c0'), make_seg_at(17.1, -2.0, 'c1'),
                make_seg_at(100.0, 100.0, 'c2'),
                make_seg_at(200.0, 200.0, 'c3')]
        engine = GameEngine(head=(16.8, 0.0), heading='right', segments=segs,
                            box_min=BOX_MIN, box_max=BOX_MAX)
        events = engine.step(DT)
        # Exactly one crash event.
        crash_events = [e for e in events if e[0] == 'crashed']
        self.assertEqual(len(crash_events), 1)
        self.assertEqual(crash_events[0], ('crashed', 'boundary'))
        self.assertTrue(engine.finished)
        self.assertEqual(engine.result, 'crashed')

    def test_too_few_segments_no_body_check(self):
        # n <= 1 + SEGMENT_SKIP_RECENT (= 3) -> range is empty -> no body
        # check possible. Head walks through its own path with no crash.
        # 3 segments: checked edges = range(0, 3-1-2) = range(0, 0) = [].
        segs = [make_seg_at(1.0, 0.0, 'c0'), make_seg_at(2.0, 0.0, 'c1'),
                make_seg_at(3.0, 0.0, 'c2')]
        engine = GameEngine(head=(0.0, 0.0), heading='right', segments=segs)
        for _ in range(20):
            events = engine.step(DT)
            self.assertFalse(engine.finished)
            self.assertEqual(events[-1][0], 'moved')


def make_pickup(pid, x, y, atoms_n=1):
    """Build a FRESH pickup record with the given 2D centroid.

    Pickup record shape (STACK-05 seam): 'atoms' is REQUIRED (02-13's
    swept pickup leg consumes atom positions). atoms_n defaults to 1;
    the atom list is padded to match (tests only need the count for
    counter arithmetic unless exercising the 'atoms' carry-through).
    """
    atoms = [('C', x, y, 0.0) for _ in range(atoms_n)]
    return {
        'id': pid,
        'centroid': (x, y),
        'atoms': atoms,
        'atoms_n': atoms_n,
    }


class TestPickupCapture(unittest.TestCase):
    """Pickup capture/attach/reject + counters (STACK-05 seam).

    Capture: head within PICKUP_RADIUS_A (inclusive) of a live pickup's
    centroid -> ('stacked', pickup) exactly once; counters increment.
    attach_segment: appends the frozen GAME-10 record, counter-NEUTRAL.
    reject_pickup: rolls counters back, re-arms the pickup, RETURNS the
    canonical ('refused', pickup_id, reason) 3-tuple.
    """

    def test_capture_first_step(self):
        # Head (0,0) heading right; pickup at (2.5, 0.0) atoms_n=1.
        # Step 1: head -> (0.3, 0.0). Distance to pickup = 2.5 - 0.3 =
        # 2.2. 2.2^2 = 4.84 <= 9.0 (PICKUP_RADIUS_A^2) -> capture.
        pickup = make_pickup('p1', 2.5, 0.0, atoms_n=1)
        engine = GameEngine(head=(0.0, 0.0), heading='right',
                            pickups=[pickup])
        events = engine.step(DT)
        # Event order: ('moved', ...) then ('stacked', <record>).
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0][0], 'moved')
        self.assertEqual(events[1][0], 'stacked')
        # The stacked record carries 'atoms' (02-13 consumes them).
        stacked_record = events[1][1]
        self.assertEqual(stacked_record['id'], 'p1')
        self.assertIn('atoms', stacked_record)
        self.assertEqual(len(stacked_record['atoms']), 1)
        # Counters: 1 molecule, 1 atom, 0 remaining.
        self.assertEqual(engine.molecules_stacked, 1)
        self.assertEqual(engine.atoms_total, 1)
        self.assertEqual(engine.pickups_remaining, 0)
        # Pickup no longer live.
        self.assertNotIn('p1', engine.live_pickup_ids)

    def test_attach_segment_frozen_record(self):
        # attach_segment appends the frozen GAME-10 record and is
        # counter-NEUTRAL (capture already counted).
        pickup = make_pickup('p1', 2.5, 0.0, atoms_n=1)
        engine = GameEngine(head=(0.0, 0.0), heading='right',
                            pickups=[pickup])
        engine.step(DT)  # captures p1 -> counters 1/1/0
        self.assertEqual(engine.molecules_stacked, 1)
        engine.attach_segment('p1', (2.5, 0.0), [('C', 2.5, 0.0, 0.0)])
        # The frozen record matches the 02-06 segment seam shape.
        seg = engine.segments[-1]
        self.assertEqual(seg['molecule_id'], 'p1')
        self.assertEqual(seg['centroid'], (2.5, 0.0))
        self.assertEqual(seg['atoms'], [('C', 2.5, 0.0, 0.0)])
        self.assertEqual(seg['atoms_n'], 1)
        # Counters unchanged by attach (counter-NEUTRAL).
        self.assertEqual(engine.molecules_stacked, 1)
        self.assertEqual(engine.atoms_total, 1)
        self.assertEqual(engine.pickups_remaining, 0)

    def test_no_capture_out_of_range(self):
        # Pickup at (5.0, 0.0); head heading UP (perpendicular) so the
        # head never approaches the pickup. 20 steps -> no stacked event,
        # counters unchanged (0/0/1).
        pickup = make_pickup('p1', 5.0, 0.0, atoms_n=1)
        engine = GameEngine(head=(0.0, 0.0), heading='up',
                            pickups=[pickup])
        for _ in range(20):
            events = engine.step(DT)
            # No stacked event ever fires.
            for e in events:
                self.assertNotEqual(e[0], 'stacked')
        self.assertEqual(engine.molecules_stacked, 0)
        self.assertEqual(engine.atoms_total, 0)
        self.assertEqual(engine.pickups_remaining, 1)
        self.assertIn('p1', engine.live_pickup_ids)

    def test_capture_exactly_at_radius_inclusive(self):
        # Head (0,0) heading right; pickup at (3.3, 0.0). One step of
        # 0.3 -> head (0.3, 0.0). Distance = 3.3 - 0.3 = 3.0 EXACTLY.
        # 3.0^2 = 9.0 <= 9.0 (PICKUP_RADIUS_A^2) -> captured (inclusive).
        pickup = make_pickup('p1', 3.3, 0.0, atoms_n=1)
        engine = GameEngine(head=(0.0, 0.0), heading='right',
                            pickups=[pickup])
        events = engine.step(DT)
        self.assertEqual(events[-1][0], 'stacked')
        self.assertEqual(engine.molecules_stacked, 1)

    def test_no_refire_while_claimed(self):
        # After capturing a pickup, continue stepping -> no second
        # ('stacked', ...) event (the pickup is no longer live).
        pickup = make_pickup('p1', 2.5, 0.0, atoms_n=1)
        engine = GameEngine(head=(0.0, 0.0), heading='right',
                            pickups=[pickup])
        engine.step(DT)  # captures p1
        self.assertEqual(engine.molecules_stacked, 1)
        # Step many more times past the pickup's position.
        for _ in range(20):
            events = engine.step(DT)
            for e in events:
                self.assertNotEqual(e[0], 'stacked')
        # Still only 1 capture.
        self.assertEqual(engine.molecules_stacked, 1)

    def test_reject_then_recapture(self):
        # reject_pickup RETURNS the canonical 3-tuple, rolls counters
        # back, re-arms the pickup. Stepping then captures again.
        pickup = make_pickup('p1', 2.5, 0.0, atoms_n=1)
        engine = GameEngine(head=(0.0, 0.0), heading='right',
                            pickups=[pickup])
        engine.step(DT)  # captures p1 -> 1/1/0
        self.assertNotIn('p1', engine.live_pickup_ids)
        # Reject: returns ('refused', 'p1', 'clash').
        result = engine.reject_pickup('p1', 'clash')
        self.assertEqual(result, ('refused', 'p1', 'clash'))
        # Counters rolled back: 0/0/1.
        self.assertEqual(engine.molecules_stacked, 0)
        self.assertEqual(engine.atoms_total, 0)
        self.assertEqual(engine.pickups_remaining, 1)
        # Pickup live again.
        self.assertIn('p1', engine.live_pickup_ids)
        # Refusal count tracked.
        self.assertEqual(engine._refusal_counts.get('p1'), 1)
        # Step again -> captures again (head still near the pickup).
        events = engine.step(DT)
        self.assertEqual(events[-1][0], 'stacked')
        self.assertEqual(engine.molecules_stacked, 1)
        self.assertEqual(engine.atoms_total, 1)
        self.assertEqual(engine.pickups_remaining, 0)
        # Refusal count unchanged by the re-capture (only reject tracks).
        self.assertEqual(engine._refusal_counts.get('p1'), 1)

    def test_at_most_one_capture_per_tick(self):
        # Two pickups both within radius on the same tick: only the
        # FIRST (in list order) is captured.
        p1 = make_pickup('p1', 0.3, 0.0, atoms_n=1)  # right at step-1 pos
        p2 = make_pickup('p2', 0.3, 0.0, atoms_n=1)  # same spot
        engine = GameEngine(head=(0.0, 0.0), heading='right',
                            pickups=[p1, p2])
        events = engine.step(DT)  # head -> (0.3, 0.0), both at distance 0
        stacked = [e for e in events if e[0] == 'stacked']
        self.assertEqual(len(stacked), 1)
        self.assertEqual(stacked[0][1]['id'], 'p1')  # list order
        self.assertEqual(engine.molecules_stacked, 1)
        self.assertNotIn('p1', engine.live_pickup_ids)
        self.assertIn('p2', engine.live_pickup_ids)


class TestWinAndBudget(unittest.TestCase):
    """Win at cap ('won') and once-per-run budget warning.

    Win: molecules_stacked >= cap -> ('won',) on the capture tick,
    finished=True / result='won'. Never fires on a crash tick.
    Budget: atoms_total > atom_budget -> ('budget_warning', atoms_total)
    exactly once per run; never a hard stop.
    """

    def test_win_at_cap_second_capture(self):
        # cap=2, two pickups in the path: p1 at (2.5, 0.0), p2 at
        # (5.0, 0.0). Head (0,0) heading right.
        #   Step 1: head (0.3, 0.0). p1 distance 2.2 <= 3.0 -> capture.
        #     molecules_stacked=1 < 2 -> no win.
        #   Steps 2-6: p2 distance > 3.0 (step 6: head 1.8, dist 3.2).
        #   Step 7: head (2.1, 0.0). p2 distance 2.9 <= 3.0 -> capture.
        #     molecules_stacked=2 >= 2 -> ('won',).
        p1 = make_pickup('p1', 2.5, 0.0, atoms_n=1)
        p2 = make_pickup('p2', 5.0, 0.0, atoms_n=1)
        engine = GameEngine(head=(0.0, 0.0), heading='right',
                            pickups=[p1, p2], cap=2)
        # Step 1: capture p1, no win.
        events = engine.step(DT)
        self.assertEqual(events[-1][0], 'stacked')
        self.assertFalse(engine.finished)
        # Steps 2-6: no capture (p2 out of range).
        for _ in range(5):
            engine.step(DT)
            self.assertFalse(engine.finished)
        # Step 7: capture p2 -> win on same tick.
        events = engine.step(DT)
        self.assertEqual(events[-1], ('won',))
        self.assertTrue(engine.finished)
        self.assertEqual(engine.result, 'won')
        self.assertEqual(engine.molecules_stacked, 2)
        # Later step returns [] (finished engine is inert).
        self.assertEqual(engine.step(DT), [])

    def test_budget_warning_once_per_run(self):
        # atom_budget=10, two pickups each atoms_n=20. First capture
        # pushes atoms_total to 20 > 10 -> ('budget_warning', 20).
        # Second capture pushes to 40 > 10, but the warning already
        # fired -> no second warning.
        p1 = make_pickup('p1', 2.5, 0.0, atoms_n=20)
        p2 = make_pickup('p2', 5.0, 0.0, atoms_n=20)
        engine = GameEngine(head=(0.0, 0.0), heading='right',
                            pickups=[p1, p2], atom_budget=10)
        all_events = []
        for _ in range(10):
            all_events.extend(engine.step(DT))
        budget_warnings = [e for e in all_events
                           if e[0] == 'budget_warning']
        # Exactly one budget warning, carrying atoms_total=20.
        self.assertEqual(len(budget_warnings), 1)
        self.assertEqual(budget_warnings[0], ('budget_warning', 20))
        # The game was NOT stopped by the budget warning.
        self.assertFalse(engine.finished)

    def test_budget_warning_cleared_by_reset(self):
        # The _budget_warned flag is cleared by reset(), so a new run
        # can fire the warning again.
        pickup = make_pickup('p1', 2.5, 0.0, atoms_n=20)
        engine = GameEngine(head=(0.0, 0.0), heading='right',
                            pickups=[pickup], atom_budget=10)
        events = engine.step(DT)
        self.assertIn(('budget_warning', 20), events)
        # Reset: flag cleared, counters zeroed.
        engine.reset(head=(0.0, 0.0), heading='right',
                     pickups=[pickup], atom_budget=10)
        self.assertFalse(engine._budget_warned)
        self.assertEqual(engine.atoms_total, 0)
        # Step again -> warning fires again.
        events = engine.step(DT)
        self.assertIn(('budget_warning', 20), events)


class TestEventOrdering(unittest.TestCase):
    """Event order per research §7: ('moved',) -> crash -> ('stacked',)
    -> ('budget_warning',) -> ('won',). A crash stops all later
    processing; pickup/win never fire on a crash tick."""

    def test_move_then_capture_order(self):
        # A tick that both moves and captures: [('moved', ...),
        # ('stacked', ...)] in that order.
        pickup = make_pickup('p1', 2.5, 0.0, atoms_n=1)
        engine = GameEngine(head=(0.0, 0.0), heading='right',
                            pickups=[pickup])
        events = engine.step(DT)
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0][0], 'moved')
        self.assertEqual(events[1][0], 'stacked')

    def test_crashing_tick_emits_nothing_after_crash(self):
        # A crashing tick emits [('moved', ...), ('crashed', ...)] and
        # nothing after — even if a pickup is within range.
        # Head (16.8, 0) heading right, box -> wall crash at 17.1.
        # Pickup at (17.1, 0.0) would be within PICKUP_RADIUS_A, but the
        # boundary crash stops all later processing.
        pickup = make_pickup('p1', 17.1, 0.0, atoms_n=1)
        engine = GameEngine(head=(16.8, 0.0), heading='right',
                            box_min=BOX_MIN, box_max=BOX_MAX,
                            pickups=[pickup])
        events = engine.step(DT)
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0][0], 'moved')
        self.assertEqual(events[1], ('crashed', 'boundary'))
        # No stacked/won/budget events after the crash.
        for e in events:
            self.assertNotIn(e[0], ('stacked', 'won', 'budget_warning'))
        # Pickup was never captured (crash stopped processing first).
        self.assertEqual(engine.molecules_stacked, 0)
        self.assertIn('p1', engine.live_pickup_ids)

    def test_full_capture_order_stacked_budget_won(self):
        # A single tick that captures, fires budget, AND wins: order is
        # ('moved',), ('stacked',), ('budget_warning',), ('won',).
        # cap=1, atom_budget=0 (any capture exceeds), pickup atoms_n=5.
        # Step 1: head (0.3, 0.0), pickup at (2.5, 0.0) dist 2.2 -> cap.
        #   atoms_total=5 > 0 -> budget_warning. molecules_stacked=1 >=
        #   1 -> win. Order: moved, stacked, budget_warning, won.
        pickup = make_pickup('p1', 2.5, 0.0, atoms_n=5)
        engine = GameEngine(head=(0.0, 0.0), heading='right',
                            pickups=[pickup], cap=1, atom_budget=0)
        events = engine.step(DT)
        names = [e[0] for e in events]
        self.assertEqual(names, ['moved', 'stacked', 'budget_warning',
                                 'won'])
        self.assertTrue(engine.finished)
        self.assertEqual(engine.result, 'won')


if __name__ == '__main__':
    unittest.main()
