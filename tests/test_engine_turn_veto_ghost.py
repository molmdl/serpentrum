"""Ghost-point turn-veto regression (plan 05-16 live retest follow-up).

Live report (verbatim): "i wasnt at boundary yet, the head had some
distance before the wall, i was able to turn right but all other keys
not working lilke after hitting a 'ghost point'".

This file PINS the diagnosis: the state is the GAME-10 rigid-chain swept
veto (game_engine._sweep_check_safe boundary leg) plus the pinned silent
drops for same-direction / 180-degree key presses in request_direction.
Reproduced EXACTLY: heading 'up', head mid-box far from any wall, a
3-segment chain trailing behind; pressing:

    up    -> silent drop (same direction, by design)
    down  -> silent drop (180 reversal, impossible by design)
    left  -> ('turn_refused', 'boundary')  ... GEOMETRICALLY JUSTIFIED:
             the CCW swing rotates the farthest chain centroid to
             x = 11.40 > 11 (the margin wall) by 30 deg of the sweep;
             the chain truly would cross the wall.
    right -> sweep opens (the ONLY geometrically safe 90-degree swing)

=> "only right works" with the head far from every wall. The veto is
correct-by-design (a refused turn leaves the chain untouched, matching
the 05-16 checkpoint text); after the turn the keys recover whenever the
swung chain clears the margin box. These tests guard the pinned behavior
and the geometric justification against regression.

PURE stdlib; python3.6 (%-formatting). Discovery:

    python3.6 -m unittest discover -s tests -p "test_*.py" -v
"""
import math
import os
import sys
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from serpentrum.game_engine import (  # noqa: E402
    BOUNDARY_MARGIN_A, GameEngine, _rotate_xy)

DT = 0.1
# The user's box situation (small preset): raw walls +/-12, engine margin
# walls +/-11 (BOUNDARY_MARGIN_A = 1.0).
BOX_MIN = (-12.0, -12.0)
BOX_MAX = (12.0, 12.0)
MARGIN = 12.0 - BOUNDARY_MARGIN_A  # 11.0

HEAD_XY = (6.0, 2.0)


def _seg(cx, cy):
    """Small molecule-like segment record (6 C atoms, 1.4 A ring)."""
    atoms = []
    for i in range(6):
        a = math.pi * i / 3.0
        atoms.append(('C', cx + 1.4 * math.cos(a),
                      cy + 1.4 * math.sin(a), 0.0))
    return {'molecule_id': 'fake', 'centroid': (cx, cy),
            'atoms': atoms, 'atoms_n': 6}


def _build():
    """The user's live state: heading 'up', head (6,2), 3 segments
    trailing straight down at 3.6 A spacing (the placed-stacking chain
    spacing), oldest-first. Head is ~10 A from the wall ahead and ~5 A
    from the right-side wall - 'not at the boundary' by any visual read.
    """
    segments = [_seg(HEAD_XY[0], HEAD_XY[1] - 3.6 * (i + 1))
                for i in range(3)]
    return GameEngine(head=HEAD_XY, heading='up', segments=segments,
                      box_min=BOX_MIN, box_max=BOX_MAX)


def _first_margin_exit(direction):
    """First (k, theta_deg, x, y) sweep sample of any chain CENTROID that
    leaves the margin-adjusted box when sweeping 'direction', or None.
    direction: 'left' -> CCW +90; 'right' -> CW -90 (from heading up).
    This is exactly the boundary leg's sampled model, recomputed openly
    here so the justification is auditable (not re-trusted from the
    implementation under test).
    """
    angle = 90.0 if direction == 'left' else -90.0
    hx, hy = HEAD_XY
    centroids = [(HEAD_XY[0], HEAD_XY[1] - 3.6 * (i + 1))
                 for i in range(3)]
    for k in range(7):  # k = 0..TURN_TICKS, same sampling as the engine
        th = math.radians(angle * k / 6.0)
        cos_t, sin_t = math.cos(th), math.sin(th)
        for cx, cy in centroids:
            rcx, rcy = _rotate_xy(cx, cy, hx, hy, cos_t, sin_t)
            if (rcx < -MARGIN or rcx > MARGIN or
                    rcy < -MARGIN or rcy > MARGIN):
                return (k, angle * k / 6.0, rcx, rcy)
    return None


class TestGhostPointOnlyRightWorks(unittest.TestCase):
    """The exact 'only right works' state from the live report."""

    def test_axis_keys_silently_dropped(self):
        """up (same direction) and down (180 reversal) are dropped at
        request time with NO event and NO feedback (pinned design)."""
        engine = _build()
        self.assertIs(engine.request_direction('up'), False)
        self.assertIs(engine.request_direction('down'), False)
        self.assertEqual(engine.pending, [])

    def test_left_refused_boundary_with_zero_mutation(self):
        """left (perpendicular) is refused 'boundary' and leaves heading,
        head, segments, sweeping and pending UNTOUCHED (the checkpoint's
        'a refused turn must not move the chain')."""
        engine = _build()
        before = ([tuple(s['centroid']) for s in engine.segments],
                  engine.heading, engine.head)
        self.assertIs(engine.request_direction('left'), True)
        events = engine.step(DT)
        self.assertEqual(events[0], ('turn_refused', 'boundary'))
        self.assertIn(('moved', (6.0, 2.3)), events)  # fell through forward
        self.assertIsNone(engine.sweeping)
        self.assertEqual([tuple(s['centroid']) for s in engine.segments],
                         before[0])
        self.assertEqual(engine.heading, before[1])
        self.assertEqual(engine.pending, [])  # refused request is consumed

    def test_right_opens_the_only_safe_swing(self):
        """right (perpendicular) opens a sweep - the ONE safe 90-degree
        swing in this geometry - and the sweep completes cleanly."""
        engine = _build()
        self.assertIs(engine.request_direction('right'), True)
        events = engine.step(DT)
        self.assertIn(('turning', 1.0 / 6.0), events)
        while engine.sweeping is not None:
            engine.step(DT)
        self.assertEqual(engine.heading, (1.0, 0.0))  # up -> right (CW)

    def test_refusals_are_geometrically_justified(self):
        """The veto is NOT a ghost: the refused LEFT swing genuinely puts
        a chain centroid outside the margin wall (x = 11.40 > 11 by the
        30-degree sample), while the accepted RIGHT swing keeps every
        sampled centroid inside the margin box. If this justification
        ever flips, the engine veto itself - not the feedback - is the
        bug and this test must fail loudly.
        """
        left_exit = _first_margin_exit('left')
        self.assertIsNotNone(left_exit)
        _k, _theta, rcx, _rcy = left_exit
        self.assertGreater(rcx, MARGIN)  # exits through the RIGHT wall
        self.assertIsNone(_first_margin_exit('right'))


class TestKeysRecoverAfterTheTurn(unittest.TestCase):
    """After the right turn, the same rule set re-explains every key:
    same-dir/180 drop silently, the swing into the wall is refused
    (again geometrically justified), the swing into free space opens.
    Proves the state is never 'stuck' - every verdict tracks geometry.
    """

    def _turned(self):
        engine = _build()
        engine.request_direction('right')
        while True:
            engine.step(DT)
            if engine.sweeping is None:
                break
        self.assertEqual(engine.heading, (1.0, 0.0))
        return engine

    def test_heading_and_chain_after_right_turn(self):
        engine = self._turned()
        # Chain rotated rigidly CW about the head: now trails -x.
        expected = [(2.4, 2.0), (-1.2, 2.0), (-4.8, 2.0)]
        for seg, want in zip(engine.segments, expected):
            self.assertAlmostEqual(seg['centroid'][0], want[0], delta=1e-9)
            self.assertAlmostEqual(seg['centroid'][1], want[1], delta=1e-9)

    def test_down_refused_up_opens_after_turn(self):
        engine = self._turned()

        def fresh():
            # GameEngine copies caller segments (_copy_segments contract),
            # so reusing the post-turn state per key press is safe.
            return GameEngine(head=engine.head, heading='right',
                              segments=engine.segments,
                              box_min=BOX_MIN, box_max=BOX_MAX)
        # same-direction and 180 still drop silently
        self.assertIs(fresh().request_direction('right'), False)
        self.assertIs(fresh().request_direction('left'), False)
        # down: CW swing of the -x trailing chain arcs over the RIGHT
        # margin wall -> refused, justified
        eng = fresh()
        self.assertIs(eng.request_direction('down'), True)
        events = eng.step(DT)
        self.assertEqual(events[0], ('turn_refused', 'boundary'))
        self.assertIsNone(eng.sweeping)
        # up: CCW swing clears everything -> opens
        eng = fresh()
        self.assertIs(eng.request_direction('up'), True)
        events = eng.step(DT)
        self.assertIn(('turning', 1.0 / 6.0), events)
        self.assertIsNotNone(eng.sweeping)


if __name__ == '__main__':
    unittest.main()
