"""GameEngine rigid-pivot turn-sweep tests (plan 02-13, GAME-10).

Covers the rigid chain pivot: a turn rotates the WHOLE chain rigidly
about the head over TURN_TICKS=6 ticks (15 deg/tick), REFUSED with
('turn_refused', reason) and zero state mutation when any of the 7
sampled swept poses hits the boundary, the body, or swings a chain atom
within SWEEP_PICKUP_CLEARANCE_A (2.5 A, atom-level) of a live pickup
atom. 180-degree enforcement is judged at sweep level (against the sweep
target while sweeping). Pending applies exactly once at the start of the
step after sweep completion; reset wipes all turn state.

Determinism (research sec 7): pure float math on fixed constants; tests
set engine state directly (plain data) and use assertAlmostEqual for
positions. TURN_DEGREES = 90.0, TURN_TICKS = 6 -> 15 deg/tick; the
pre-check samples K = TURN_TICKS + 1 = 7 poses (k = 0..6).

Discovery command (python3.6.9 — NOTE: `-t .` FAILS on python3.6 with a
non-package start dir; do not add it):

    python3.6 -m unittest discover -s tests -p "test_*.py" -v

This suite is owned by plan 02-13. test_engine_core.py (02-06 movement)
and test_engine_rules.py (02-10 collisions/rules) are owned by prior
plans and are NEVER edited here; if a prior assertion genuinely
contradicts this contract, plan 02-13 stops and reports a dependency
violation instead.
"""
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from serpentrum import game_engine  # noqa: E402
from serpentrum.game_engine import GameEngine  # noqa: E402

# Test-tuning constants (mirror the engine's own pins).
DELTA = 1e-9
TURN_DEG = game_engine.TURN_DEGREES   # 90.0
TURN_N = game_engine.TURN_TICKS       # 6


def make_seg_at(x, y, molecule_id='mol', atoms=None):
    """Build a FRESH segment record with the given 2D centroid.

    `atoms` defaults to a single placeholder atom at the centroid. The
    swept pickup leg consumes atom positions, so tests that exercise it
    pass an explicit atoms list.
    """
    if atoms is None:
        atoms = [('C', x, y, 0.0)]
    return {
        'molecule_id': molecule_id,
        'centroid': (x, y),
        'atoms': list(atoms),
        'atoms_n': len(atoms),
    }


def make_pickup(pid, x, y, atoms=None):
    """Build a FRESH pickup record with the given 2D centroid + atoms."""
    if atoms is None:
        atoms = [('O', x, y, 0.0)]
    return {
        'id': pid,
        'centroid': (x, y),
        'atoms': list(atoms),
        'atoms_n': len(atoms),
    }


class TestRotationHelper(unittest.TestCase):
    """_rotate_xy contract: CCW-positive rotation about a center.

    z and symbol are NEVER touched by _rotate_xy (it takes only x, y);
    callers carry atom[3] (z) and atom[0] (sym) through unchanged. The
    full atom-z-through-sweep assertion lives in TestSweepProgress
    (rotation exactness over a full sweep).
    """

    def test_rotate_plus_90_about_origin(self):
        # (3, 0) about (0, 0) by +90 deg (cos=0, sin=1) -> (0, 3).
        cos_t = math.cos(math.radians(90.0))
        sin_t = math.sin(math.radians(90.0))
        rx, ry = game_engine._rotate_xy(3.0, 0.0, 0.0, 0.0, cos_t, sin_t)
        self.assertAlmostEqual(rx, 0.0, delta=DELTA)
        self.assertAlmostEqual(ry, 3.0, delta=DELTA)

    def test_rotate_minus_90_about_origin(self):
        # (3, 0) about (0, 0) by -90 deg (cos=0, sin=-1) -> (0, -3).
        cos_t = math.cos(math.radians(-90.0))
        sin_t = math.sin(math.radians(-90.0))
        rx, ry = game_engine._rotate_xy(3.0, 0.0, 0.0, 0.0, cos_t, sin_t)
        self.assertAlmostEqual(rx, 0.0, delta=DELTA)
        self.assertAlmostEqual(ry, -3.0, delta=DELTA)

    def test_rotate_atom_xy_preserves_z_by_caller(self):
        # An atom (sym, x=4, y=1, z=2.0): rotate (4, 1) about origin by
        # +90 deg -> x' = 4*cos90 - 1*sin90 = -1; y' = 4*sin90 + 1*cos90
        # = 4. The helper returns (-1, 4); z is preserved by the caller
        # (_apply_rotation copies atom[3] unchanged), asserted end-to-end
        # in TestSweepProgress.test_rotation_exactness_full_sweep.
        cos_t = math.cos(math.radians(90.0))
        sin_t = math.sin(math.radians(90.0))
        rx, ry = game_engine._rotate_xy(4.0, 1.0, 0.0, 0.0, cos_t, sin_t)
        self.assertAlmostEqual(rx, -1.0, delta=DELTA)
        self.assertAlmostEqual(ry, 4.0, delta=DELTA)

    def test_rotate_about_non_origin_center(self):
        # (10, 0) about center (4, 0) by +90 deg: offset (6, 0) ->
        # rotated (0, 6) -> position (4, 6). (Boundary-refusal geometry:
        # the rotated centroid's y = 6.0 exceeds the margin wall 1.0.)
        cos_t = math.cos(math.radians(90.0))
        sin_t = math.sin(math.radians(90.0))
        rx, ry = game_engine._rotate_xy(10.0, 0.0, 4.0, 0.0, cos_t, sin_t)
        self.assertAlmostEqual(rx, 4.0, delta=DELTA)
        self.assertAlmostEqual(ry, 6.0, delta=DELTA)


class TestSweepConstants(unittest.TestCase):
    """TURN_DEGREES / TURN_TICKS are defined by this plan (02-06's
    trimmed movement scope carries no sweep constants)."""

    def test_constants_pinned(self):
        self.assertEqual(game_engine.TURN_DEGREES, 90.0)
        self.assertEqual(game_engine.TURN_TICKS, 6)

    def test_tick_share_is_15_deg(self):
        self.assertAlmostEqual(game_engine.TURN_DEGREES / game_engine.TURN_TICKS,
                               15.0, delta=DELTA)

    def test_pre_check_sample_count(self):
        # K = TURN_TICKS + 1 = 7 sampled poses (k = 0..6, inclusive ends).
        self.assertEqual(game_engine.TURN_TICKS + 1, 7)


class TestSweepRefusalThreeLegs(unittest.TestCase):
    """start_sweep's 7-sample 3-leg pre-check: boundary / body / pickup
    refusals with reason-tagged ('turn_refused', reason) events and ZERO
    state mutation. Head excluded from the pickup leg (it is the pivot)."""

    def test_boundary_refusal_centroid_leg(self):
        # box ((-2,-2),(20,2)); margin walls x in [-1, 19], y in [-1, 1].
        # head (4,0) heading (1,0); segs (7,0),(10,0). start_sweep('up')
        # is CCW +90. centroid (10,0) has offset (6,0) from head (4,0);
        # rotated +90 -> offset (0,6) -> position (4,6). 6.0 > y1-M =
        # 2.0 - 1.0 = 1.0 -> refuse 'boundary'. (n=2 -> no body leg; no
        # pickups -> only the boundary leg can fire.)
        segs = [make_seg_at(7.0, 0.0, 's0'), make_seg_at(10.0, 0.0, 's1')]
        engine = GameEngine(head=(4.0, 0.0), heading='right',
                            box_min=(-2.0, -2.0), box_max=(20.0, 2.0),
                            segments=segs)
        opened, events = engine.start_sweep('up')
        self.assertFalse(opened)
        self.assertEqual(events, [('turn_refused', 'boundary')])
        # ZERO state mutation: heading, centroids, sweeping, pending.
        self.assertEqual(engine.heading, (1.0, 0.0))
        self.assertEqual(engine.segments[0]['centroid'], (7.0, 0.0))
        self.assertEqual(engine.segments[1]['centroid'], (10.0, 0.0))
        self.assertIsNone(engine.sweeping)
        self.assertEqual(engine.pending, [])

    def test_body_refusal_defensive_leg(self):
        # head (4,0) heading (1,0); segs c0=(-2,1), c1=(2.5,1),
        # c2=(3.5,0), c3=(4,-0.5). n=4 -> only edge 0 (c0->c1) is
        # checked (limit = 4-1-2 = 1). head (4,0) to edge 0 (horizontal
        # y=1, x in [-2, 2.5]): nearest point is the clamped endpoint
        # (2.5, 1.0); dist^2 = (4-2.5)^2 + (0-1)^2 = 1.5^2 + 1.0^2 =
        # 2.25 + 1.0 = 3.25 < 4.0 (BODY_COLLISION_RADIUS_A^2) -> the
        # CURRENT pose (sample k=0, th=0, unrotated) already violates ->
        # refuse 'body'. No box, no pickups -> only the body leg fires.
        segs = [make_seg_at(-2.0, 1.0, 'c0'), make_seg_at(2.5, 1.0, 'c1'),
                make_seg_at(3.5, 0.0, 'c2'), make_seg_at(4.0, -0.5, 'c3')]
        engine = GameEngine(head=(4.0, 0.0), heading='right', segments=segs)
        opened, events = engine.start_sweep('up')
        self.assertFalse(opened)
        self.assertEqual(events, [('turn_refused', 'body')])
        self.assertEqual(engine.heading, (1.0, 0.0))
        self.assertEqual(engine.segments[0]['centroid'], (-2.0, 1.0))
        self.assertEqual(engine.segments[3]['centroid'], (4.0, -0.5))
        self.assertIsNone(engine.sweeping)
        self.assertEqual(engine.pending, [])

    def test_pickup_refusal_atom_level(self):
        # head (0,0) heading (1,0); seg m1 centroid (3,0) atom
        # ('C',3,0,0); live pickup p1 centroid (0,3) atom ('O',0,3,0).
        # start_sweep('up') CCW +90: the chain atom (3,0) rotates on the
        # radius-3 circle about the origin. At sample k=3 (th=45 deg) it
        # sits at (3*cos45, 3*sin45) = (2.1213, 2.1213); distance to the
        # pickup atom (0,3) = sqrt(2.1213^2 + (2.1213-3)^2) =
        # sqrt(4.5 + 0.7721) = sqrt(5.2721) = 2.296 < 2.5
        # (SWEEP_PICKUP_CLEARANCE_A) -> refuse 'pickup'. (n=1 -> no body
        # leg; no box -> only the pickup leg fires.)
        seg = make_seg_at(3.0, 0.0, 'm1', atoms=[('C', 3.0, 0.0, 0.0)])
        pickup = make_pickup('p1', 0.0, 3.0, atoms=[('O', 0.0, 3.0, 0.0)])
        engine = GameEngine(head=(0.0, 0.0), heading='right',
                            segments=[seg], pickups=[pickup])
        opened, events = engine.start_sweep('up')
        self.assertFalse(opened)
        self.assertEqual(events, [('turn_refused', 'pickup')])
        self.assertEqual(engine.heading, (1.0, 0.0))
        self.assertEqual(engine.segments[0]['centroid'], (3.0, 0.0))
        self.assertEqual(engine.segments[0]['atoms'],
                         [('C', 3.0, 0.0, 0.0)])
        self.assertIsNone(engine.sweeping)
        self.assertEqual(engine.pending, [])
        # Pickup still live (not captured by a sweep pre-check).
        self.assertIn('p1', engine.live_pickup_ids)

    def test_pickup_positive_control_sweep_opens(self):
        # Same chain geometry, pickup atom at (12,0,0). The rotating
        # chain atom traces the radius-3 circle; its min distance to
        # (12,0) is 12 - 3 = 9 > 2.5 -> no pickup hit. No box, no body
        # (n=1) -> start_sweep returns (True, []) and the sweep opens.
        seg = make_seg_at(3.0, 0.0, 'm1', atoms=[('C', 3.0, 0.0, 0.0)])
        pickup = make_pickup('p1', 12.0, 0.0, atoms=[('O', 12.0, 0.0, 0.0)])
        engine = GameEngine(head=(0.0, 0.0), heading='right',
                            segments=[seg], pickups=[pickup])
        opened, events = engine.start_sweep('up')
        self.assertTrue(opened)
        self.assertEqual(events, [])
        self.assertIsNotNone(engine.sweeping)
        # Sweep state seeded correctly: tick 0, CCW target up.
        self.assertEqual(engine.sweeping['target_heading'], (0.0, 1.0))
        self.assertEqual(engine.sweeping['angle_signed'], TURN_DEG)
        self.assertEqual(engine.sweeping['tick'], 0)
        self.assertEqual(engine.sweeping['total_ticks'], TURN_N)

    def test_head_excluded_from_pickup_leg(self):
        # Live pickup with its atom EXACTLY at the head/pivot (0,0,0)
        # (centroid (0,0)). The chain atom (3,0,0) rotates on the
        # radius-3 circle about the origin; its distance to the origin
        # is 3.0 at EVERY sampled pose > 2.5 -> the sweep OPENS. This
        # proves the head/pivot point itself is NOT treated as a checked
        # chain atom (a head-level check would refuse at distance 0 at
        # every pose). The head is the invariant pivot, not a chain atom.
        seg = make_seg_at(3.0, 0.0, 'm1', atoms=[('C', 3.0, 0.0, 0.0)])
        pickup = make_pickup('p1', 0.0, 0.0, atoms=[('O', 0.0, 0.0, 0.0)])
        engine = GameEngine(head=(0.0, 0.0), heading='right',
                            segments=[seg], pickups=[pickup])
        opened, events = engine.start_sweep('up')
        self.assertTrue(opened)
        self.assertEqual(events, [])
        self.assertIsNotNone(engine.sweeping)


class TestStartSweepEdgeCases(unittest.TestCase):
    """start_sweep defensive contracts: 180/same are no-ops (not
    refusals); unknown names raise; CW sign is negative."""

    def test_180_vs_current_heading_is_noop(self):
        # heading (1,0); start_sweep('left') is a 180-degree reversal
        # vs the CURRENT heading (dot = -1 < -0.5) -> (False, []) with
        # NO refusal event and NO state mutation (mirrors
        # request_direction; never reached via step()).
        engine = GameEngine(head=(0.0, 0.0), heading='right')
        opened, events = engine.start_sweep('left')
        self.assertFalse(opened)
        self.assertEqual(events, [])
        self.assertIsNone(engine.sweeping)

    def test_same_as_current_heading_is_noop(self):
        engine = GameEngine(head=(0.0, 0.0), heading='right')
        opened, events = engine.start_sweep('right')
        self.assertFalse(opened)
        self.assertEqual(events, [])
        self.assertIsNone(engine.sweeping)

    def test_unknown_direction_raises(self):
        engine = GameEngine(head=(0.0, 0.0), heading='right')
        with self.assertRaises(ValueError):
            engine.start_sweep('diagonal')
        self.assertIsNone(engine.sweeping)

    def test_cw_turn_signs_negative(self):
        # heading (1,0); 'down' target (0,-1). cross = sx*ty - sy*tx =
        # 1*(-1) - 0*0 = -1 < 0 -> CW -> angle_signed = -90. The sweep
        # opens (no box/segments/pickups to hit).
        engine = GameEngine(head=(0.0, 0.0), heading='right')
        opened, events = engine.start_sweep('down')
        self.assertTrue(opened)
        self.assertEqual(events, [])
        self.assertEqual(engine.sweeping['angle_signed'], -TURN_DEG)
        self.assertEqual(engine.sweeping['target_heading'], (0.0, -1.0))


class TestRequestDirectionSweepLevel(unittest.TestCase):
    """While sweeping, request_direction judges against the sweep TARGET
    (newest-wins, max 1). While not sweeping, 02-06's original rule
    (first-kept) stands unchanged."""

    def test_not_sweeping_original_rule_unchanged(self):
        # 02-06 behavior: 180 rejected, same rejected, first-kept buffer.
        engine = GameEngine(head=(0.0, 0.0), heading='right')
        self.assertFalse(engine.request_direction('left'))   # 180
        self.assertFalse(engine.request_direction('right'))  # same
        self.assertTrue(engine.request_direction('up'))      # perpendicular
        self.assertEqual(engine.pending, ['up'])
        self.assertFalse(engine.request_direction('down'))   # buffer full
        self.assertEqual(engine.pending, ['up'])             # first kept

    def test_sweep_180_vs_target_ignored(self):
        # Open an up-sweep (heading (1,0) -> target (0,1)). 'down' is a
        # 180-vs-target (dot = 0*0 + 1*(-1) = -1 < -0.5) -> ignored;
        # pending stays empty.
        engine = GameEngine(head=(0.0, 0.0), heading='right')
        engine.start_sweep('up')
        self.assertIsNotNone(engine.sweeping)
        self.assertFalse(engine.request_direction('down'))
        self.assertEqual(engine.pending, [])

    def test_sweep_same_as_target_ignored(self):
        # 'up' while sweeping toward (0,1): dot = 1 > 0.5 -> ignored.
        engine = GameEngine(head=(0.0, 0.0), heading='right')
        engine.start_sweep('up')
        self.assertFalse(engine.request_direction('up'))
        self.assertEqual(engine.pending, [])

    def test_sweep_perpendicular_buffered_newest_wins(self):
        # Open up-sweep. 'left' is perpendicular to target (0,1)
        # (dot = 0) -> buffered. Then 'right' is also perpendicular ->
        # NEWEST WINS (max 1): pending becomes ['right'], overwriting.
        engine = GameEngine(head=(0.0, 0.0), heading='right')
        engine.start_sweep('up')
        self.assertTrue(engine.request_direction('left'))
        self.assertEqual(engine.pending, ['left'])
        self.assertTrue(engine.request_direction('right'))
        self.assertEqual(engine.pending, ['right'])  # newest wins


if __name__ == '__main__':
    unittest.main()
