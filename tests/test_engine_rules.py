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


if __name__ == '__main__':
    unittest.main()
