"""Ghost-point turn-veto regression — OWNER-OVERRIDDEN veto rules.

History: the live report ("i wasnt at boundary yet ... all other keys not
working lilke after hitting a 'ghost point'") was diagnosed as the pinned
rigid-chain sweep veto (the boundary leg refused a turn whose SWUNG CHAIN
would leave the margin box, even with the head far from any wall) plus
the pinned silent drops for same-direction / 180-degree keys. The 2026-09-20
re-test found the SAME frozen-snake symptom persisting via the body and
pickup legs (with several floating refused pickups on the board, EVERY
turn near them was vetoed; "none of the arrow key ever works").

This file pins the OWNER-APPROVED end state (2026-09-20 UTC, 05-16
re-test directive):

  - Turn sweeps have NO swept pre-check at all — a perpendicular key
    ALWAYS opens the rigid sweep. Visual clipping of the swinging chain
    through walls / the snake's own body / floating pickups is
    owner-accepted (a silly outcome is recoverable; a frozen snake is
    not).
  - Walls apply to the HEAD only: the forward-motion 'crashed'/'boundary'
    and 'crashed'/'body' rules (GAME-05) are UNCHANGED and live in
    tests/test_engine_rules.py.
  - Same-direction keys still drop silently (unchanged); the 180-degree
    backward key is the ONE remaining turn refusal, dropped at request
    time in request_direction (its DBG classification line stays).

The EXACT state from the original report (heading 'up', head (6,2),
3-segment chain trailing down, small-ish +/-12 box) is preserved as the
fixture: the SAME state that used to refuse 'left' on walls now ALLOWS
the turn — that flip IS the proof the override landed.

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
# The user's box situation (small-ish fixture): raw walls +/-12, engine
# margin walls +/-11 (BOUNDARY_MARGIN_A = 1.0) for the HEAD crash rule.
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
    spacing), built nearest-first (index 0 = nearest the head; the
    sweep/rotation assertions are index-order-agnostic). Head is ~10 A
    from the wall ahead and ~5 A from the right-side wall - 'not at the
    boundary' by any visual read."""
    segments = [_seg(HEAD_XY[0], HEAD_XY[1] - 3.6 * (i + 1))
                for i in range(3)]
    return GameEngine(head=HEAD_XY, heading='up', segments=segments,
                      box_min=BOX_MIN, box_max=BOX_MAX)


def _first_margin_exit(direction):
    """First (k, theta_deg, x, y) sweep sample of any chain CENTROID that
    leaves the margin-adjusted box when sweeping 'direction', or None.
    direction: 'left' -> CCW +90; 'right' -> CW -90 (from heading up).
    KEPT as open documentation of the real swing geometry: the LEFT
    swing DOES take the tail past the wall (that is honest viewer
    clipping, owner-accepted) — it simply no longer vetoes the turn.
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


class TestGhostPointStateNowTurnsBothWays(unittest.TestCase):
    """The exact 'only right works' state from the live report — under
    the owner-approved head-only wall rule BOTH perpendiculars open."""

    def test_axis_keys_silently_dropped(self):
        """up (same direction) and down (180 reversal) are dropped at
        request time with NO event and NO feedback (pinned design,
        unchanged)."""
        engine = _build()
        self.assertIs(engine.request_direction('up'), False)
        self.assertIs(engine.request_direction('down'), False)
        self.assertEqual(engine.pending, [])

    def test_left_now_opens_same_state(self):
        """OLD PIN (overridden): left was refused 'boundary' because the
        CCW swing rotated the farthest chain centroid to x = 11.40 > 11.
        NEW (owner directive 2026-09-19): the SAME state ALLOWS the turn
        — the chain sweeps, no refusal event, no mutation veto."""
        engine = _build()
        self.assertIs(engine.request_direction('left'), True)
        events = engine.step(DT)
        self.assertEqual(events, [('turning', 1.0 / 6.0)])
        self.assertIsNotNone(engine.sweeping)
        self.assertEqual(engine.heading, (0.0, 1.0))  # pre-sweep heading

    def test_left_sweep_completes_and_tail_may_clip_outside_box(self):
        """The CCW swing runs to completion; the trailing chain ends the
        turn past the raw +x wall (owner-accepted visual clipping — the
        wall only stops the HEAD, and the head never moved)."""
        engine = _build()
        engine.request_direction('left')
        events = engine.step(DT)
        self.assertEqual(events, [('turning', 1.0 / 6.0)])  # sweep tick 1
        for _ in range(5):  # ticks 2..6
            engine.step(DT)
        self.assertIsNone(engine.sweeping)
        self.assertEqual(engine.heading, (-1.0, 0.0))  # up -> left (CCW)
        self.assertEqual(engine.head, HEAD_XY)  # pivot unmoved
        # Farthest centroid from the head (this fixture is built
        # nearest-first: segments[-1] = (6, -8.8) at 10.8 A out):
        # (0,-10.8) rel -> +90 -> (+10.8, 0) rel -> (16.8, 2.0):
        # beyond the RAW wall 12.0 — clipped, allowed.
        farthest = engine.segments[-1]['centroid']
        self.assertAlmostEqual(farthest[0], 16.8, delta=1e-9)
        self.assertAlmostEqual(farthest[1], 2.0, delta=1e-9)
        self.assertGreater(farthest[0], 12.0)
        # ...but the run is ALIVE (head never touched the wall).
        self.assertFalse(engine.finished)

    def test_right_opens_as_before(self):
        """right was the ONLY safe swing under the old veto; it still
        opens (perpendiculars are never wall-vetoed now)."""
        engine = _build()
        self.assertIs(engine.request_direction('right'), True)
        events = engine.step(DT)
        self.assertIn(('turning', 1.0 / 6.0), events)
        for _ in range(5):  # ticks 2..6
            engine.step(DT)
        self.assertIsNone(engine.sweeping)
        self.assertEqual(engine.heading, (1.0, 0.0))  # up -> right (CW)

    def test_swing_geometry_still_crosses_but_is_allowed(self):
        """Audit trail: the LEFT swing's sampled poses still mathematically
        leave the margin box (x = 11.40 > 11 by the 30-degree sample) —
        the geometry did not change, the RULE did. Walls apply to the
        head only."""
        left_exit = _first_margin_exit('left')
        self.assertIsNotNone(left_exit)
        _k, _theta, rcx, _rcy = left_exit
        self.assertGreater(rcx, MARGIN)  # crosses the RIGHT wall: real
        self.assertIsNone(_first_margin_exit('right'))  # right stays in


class TestAfterTheTurn(unittest.TestCase):
    """After the right turn, same-dir/180 still drop silently and BOTH
    perpendiculars open (no wall can veto the swinging chain)."""

    def _turned(self):
        engine = _build()
        engine.request_direction('right')
        events = engine.step(DT)
        self.assertEqual(events, [('turning', 1.0 / 6.0)])  # tick 1 opens
        for _ in range(5):  # ticks 2..6
            engine.step(DT)
        self.assertIsNone(engine.sweeping)
        self.assertEqual(engine.heading, (1.0, 0.0))
        return engine

    def test_chain_after_right_turn(self):
        engine = self._turned()
        # Chain rotated rigidly CW about the head: now trails -x.
        expected = [(2.4, 2.0), (-1.2, 2.0), (-4.8, 2.0)]
        for seg, want in zip(engine.segments, expected):
            self.assertAlmostEqual(seg['centroid'][0], want[0], delta=1e-9)
            self.assertAlmostEqual(seg['centroid'][1], want[1], delta=1e-9)

    def test_down_and_up_both_open_after_turn(self):
        """OLD PIN (overridden): 'down' was refused 'boundary' (the CW
        swing of the -x trailing chain arced over the RIGHT margin
        wall). NEW: both perpendiculars open."""
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
        # down: USED to refuse 'boundary' — now opens (CW swing, chain
        # may arc over the wall; the head is what walls stop).
        eng = fresh()
        self.assertIs(eng.request_direction('down'), True)
        events = eng.step(DT)
        self.assertEqual(events, [('turning', 1.0 / 6.0)])
        self.assertIsNotNone(eng.sweeping)
        # up: opens as before.
        eng = fresh()
        self.assertIs(eng.request_direction('up'), True)
        events = eng.step(DT)
        self.assertEqual(events, [('turning', 1.0 / 6.0)])
        self.assertIsNotNone(eng.sweeping)


class TestBodyAndPickupLegsAlsoRemoved(unittest.TestCase):
    """2026-09-20 UTC (05-16 re-test directive): the BODY and PICKUP
    legs are REMOVED TOO — the exact states that used to refuse now
    OPEN the sweep and run it to completion. A frozen snake is worse
    than a silly swing. (Fixtures transplanted from
    tests/test_engine_turns.py, plan 02-13 — SAME geometries, flipped
    verdicts.)"""

    def test_body_fixture_now_opens(self):
        def seg_at(x, y):
            return {'molecule_id': 'm', 'centroid': (x, y),
                    'atoms': [('C', x, y, 0.0)], 'atoms_n': 1}
        # head (4,0); the OLD body leg measured dist^2 = 3.25 < 4.0 vs
        # edge (c0,c1) at the unrotated pose and refused 'body'. NEW:
        # no veto — the sweep opens and the chain swings through.
        segs = [seg_at(-2.0, 1.0), seg_at(2.5, 1.0),
                seg_at(3.5, 0.0), seg_at(4.0, -0.5)]
        engine = GameEngine(head=(4.0, 0.0), heading='right',
                            segments=segs)
        opened, events = engine.start_sweep('up')
        self.assertTrue(opened)
        self.assertEqual(events, [])
        self.assertIsNotNone(engine.sweeping)
        for _ in range(6):
            engine.step(0.1)
        self.assertIsNone(engine.sweeping)
        self.assertEqual(engine.heading, (0.0, 1.0))  # right -> up (CCW)
        self.assertFalse(engine.finished)  # a swing clip is not a crash

    def test_pickup_fixture_now_opens(self):
        # chain atom (3,0) passes within 2.5 A of the live pickup atom
        # (0,3) mid-swing — the OLD pickup leg refused 'pickup'; NEW:
        # the sweep opens regardless and the pickup stays LIVE.
        seg = {'molecule_id': 'm', 'centroid': (3.0, 0.0),
               'atoms': [('C', 3.0, 0.0, 0.0)], 'atoms_n': 1}
        pickup = {'id': 'p1', 'centroid': (0.0, 3.0),
                  'atoms': [('O', 0.0, 3.0, 0.0)], 'atoms_n': 1}
        engine = GameEngine(head=(0.0, 0.0), heading='right',
                            segments=[seg], pickups=[pickup])
        opened, events = engine.start_sweep('up')
        self.assertTrue(opened)
        self.assertEqual(events, [])
        self.assertIsNotNone(engine.sweeping)
        for _ in range(6):
            engine.step(0.1)
        self.assertEqual(engine.heading, (0.0, 1.0))
        self.assertIn('p1', engine.live_pickup_ids)
        self.assertFalse(engine.finished)

    def test_180_key_is_the_one_remaining_refusal(self):
        # heading 'right' with a floating pickup AT the head (zero
        # distance — maximal pickup "veto" under the old rule): the
        # perpendicular key STILL opens (no veto), and the 180 key is
        # refused at request time (never buffered, no event).
        pickup = {'id': 'p1', 'centroid': (0.0, 0.0),
                  'atoms': [('O', 0.0, 0.0, 0.0)], 'atoms_n': 1}
        engine = GameEngine(head=(0.0, 0.0), heading='right',
                            pickups=[pickup])
        self.assertIs(engine.request_direction('up'), True)
        self.assertIs(engine.request_direction('left'), False)  # the 180
        self.assertEqual(engine.pending, ['up'])
        events = engine.step(0.1)
        self.assertEqual(events, [('turning', 1.0 / 6.0)])


if __name__ == '__main__':
    unittest.main()
