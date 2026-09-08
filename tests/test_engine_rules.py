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


if __name__ == '__main__':
    unittest.main()
