"""Train-follow tail regression (owner-directed gameplay change, 2026-09-19 UTC).

Live report (05-16 mid-flight human checkpoint, verbatim): "fix the
lagging-behind tail that increase the length unreasonably, even with 1-2
eaten mol" (earlier session: "after eating the 2nd mol the 2 eaten mol
lagging FAR behind the head (distance between the 2 eaten mol looks ok
tho").

DIAGNOSIS (reproduced on the old engine with the real set_a pipeline):
the engine translated ONLY the head on 'moved' ticks; segments were
never translated during forward motion (only rigidly rotated about the
head during sweeps), and placement chains each capture off the newest
STATIONARY segment. Capture 1 landed 3.600 A behind the head, but 16
ticks later the gap was 8.275 A and growing unbounded at exactly the
travel speed (0.3 A/tick); capture 2 landed 13.001 A from the head while
the seg1<->seg2 spacing stayed 3.600 A EXACTLY - the spacing was never
the problem, the stationary chain was.

FIX (owner directive): the chain is a rigid molecular assembly - it
FOLLOWS the head. Every 'moved' tick translates ALL segments (centroids
+ atom x/y) by the SAME delta the head took; z and symbols are
preserved exactly. Combined with GAME-10's rigid sweeps (rotation about
the head), the whole chain is now a single rigid body that translates
on straight travel and pivots on turns - "stacking geometry immutable
at all times" now holds during forward motion too, and the approved
3.60 A per-molecule spacing is unchanged by construction (common
translation preserves every pairwise distance).

CONSEQUENCE (honest reconciliation, pinned in test_engine_rules.py):
head<->chain relative geometry is CONSTANT during straight motion (the
head and chain share one translation), so GAME-05's forward body check
can only ever fire from an ALREADY-overlapping pose (a hand-seeded
state; unreachable in real play, which is guarded at placement time and
by the sweep pre-check's body leg). The forward check is kept as that
cheap guard - not deleted.

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

from serpentrum.game_engine import GameEngine  # noqa: E402

DT = 0.1
STEP_A = 3.0 * DT  # 0.3 A per tick at SPEED_A_PER_S = 3.0
DELTA = 1e-9


def make_seg(x, y, molecule_id='mol', atoms=None):
    """FRESH segment record; atoms default to one placeholder atom with a
    nonzero z so the z-preservation leg is real."""
    if atoms is None:
        atoms = [('C', x + 1.4, y - 0.5, 2.0)]
    return {'molecule_id': molecule_id, 'centroid': (x, y),
            'atoms': list(atoms), 'atoms_n': len(atoms)}


def _dist2(ax, ay, bx, by):
    dx, dy = ax - bx, ay - by
    return dx * dx + dy * dy


class TestChainTranslatesWithHead(unittest.TestCase):
    """Every 'moved' tick translates the WHOLE chain by the head delta."""

    def test_segments_translate_by_exact_head_delta(self):
        # Head (0,0) heading right; three segments trailing -x at the
        # approved 3.6 A stacking spacing. After 10 forward ticks the
        # head is at (3.0, 0) and EVERY segment/atom must have shifted
        # by exactly (+3.0, 0.0).
        start = [(-10.8, 0.0), (-7.2, 0.0), (-3.6, 0.0)]  # oldest-first
        segs = [make_seg(x, y, 's%d' % i) for i, (x, y) in
                enumerate(start)]
        engine = GameEngine(head=(0.0, 0.0), heading='right',
                            segments=segs)
        atom_start = [seg['atoms'][0] for seg in engine.segments]
        for _ in range(10):
            events = engine.step(DT)
            self.assertEqual(events[0][0], 'moved')
        self.assertAlmostEqual(engine.head[0], 3.0, delta=DELTA)
        for i, (x0, y0) in enumerate(start):
            cx, cy = engine.segments[i]['centroid']
            self.assertAlmostEqual(cx, x0 + 3.0, delta=DELTA)
            self.assertAlmostEqual(cy, y0, delta=DELTA)
            # Atom x/y shifted by the identical delta; z and symbol
            # preserved exactly.
            sym0, ax0, ay0, az0 = atom_start[i]
            sym, ax, ay, az = engine.segments[i]['atoms'][0]
            self.assertEqual(sym, sym0)
            self.assertAlmostEqual(ax, ax0 + 3.0, delta=DELTA)
            self.assertAlmostEqual(ay, ay0, delta=DELTA)
            self.assertEqual(az, az0)

    def test_head_to_newest_distance_is_constant(self):
        # The live symptom, pinned: the head<->newest-segment distance
        # must NOT drift as the head keeps moving. Seeded at the
        # approved 3.6 A it stays 3.6 A at every tick.
        # Oldest-first (index 0 = tail-most, last = nearest the head).
        segs = [make_seg(-7.2, 0.0, 's0'), make_seg(-3.6, 0.0, 's1')]
        engine = GameEngine(head=(0.0, 0.0), heading='right',
                            segments=segs)
        newest0 = engine.segments[-1]['centroid']
        # The LAST entry is nearest the head (index 0 is the oldest,
        # tail-most) - the engine's order convention.
        self.assertEqual(newest0, (-3.6, 0.0))
        for _ in range(30):
            engine.step(DT)
            nx, ny = engine.head
            cx, cy = engine.segments[-1]['centroid']
            self.assertAlmostEqual(_dist2(nx, ny, cx, cy), 3.6 * 3.6,
                                   delta=DELTA)
            # Inter-segment spacing equally frozen (3.6 A).
            c0 = engine.segments[0]['centroid']
            self.assertAlmostEqual(_dist2(c0[0], c0[1], cx, cy),
                                   3.6 * 3.6, delta=DELTA)

    def test_capture_then_travel_keeps_3p6_spacing(self):
        # End-to-end shape of the live scenario: capture a pickup,
        # attach the placed segment (the controller seam: 3.6 A behind
        # the head along -heading), keep driving; the gap never grows.
        pickup = {'id': 'p1', 'centroid': (2.5, 0.0),
                  'atoms': [('C', 2.5, 0.0, 0.0)], 'atoms_n': 1}
        engine = GameEngine(head=(0.0, 0.0), heading='right',
                            pickups=[pickup])
        events = engine.step(DT)  # head -> (0.3, 0); captures p1
        self.assertEqual(events[-1][0], 'stacked')
        # The controller-seam shape: place 3.6 A behind the head and
        # attach (counter-neutral).
        hx, hy = engine.head
        engine.attach_segment(
            'p1', (hx - 3.6, hy),
            [('C', hx - 3.6 + 1.4, hy, 0.0)])
        for _ in range(40):
            engine.step(DT)
            nx, ny = engine.head
            cx, cy = engine.segments[-1]['centroid']
            self.assertAlmostEqual(_dist2(nx, ny, cx, cy), 3.6 * 3.6,
                                   delta=DELTA)


class TestFollowAfterSweep(unittest.TestCase):
    """After a rigid 90-degree sweep, the chain still follows along the
    NEW heading (GAME-10 rigid sweeps untouched: rotation tests live in
    test_engine_turns.py)."""

    def test_follow_along_new_heading_after_sweep(self):
        segs = [make_seg(-3.6, 0.0, 's0')]
        engine = GameEngine(head=(0.0, 0.0), heading='right',
                            segments=segs)
        engine.request_direction('up')
        for _ in range(6):  # complete the sweep
            engine.step(DT)
        self.assertEqual(engine.heading, (0.0, 1.0))
        # Sweep rotated the segment about the head: (-3.6, 0) -> (0, -3.6).
        cx, cy = engine.segments[0]['centroid']
        self.assertAlmostEqual(cx, 0.0, delta=DELTA)
        self.assertAlmostEqual(cy, -3.6, delta=DELTA)
        # Five forward ticks along +y: chain follows by the same delta.
        for _ in range(5):
            engine.step(DT)
        self.assertAlmostEqual(engine.head[0], 0.0, delta=DELTA)
        self.assertAlmostEqual(engine.head[1], 1.5, delta=DELTA)
        cx, cy = engine.segments[0]['centroid']
        self.assertAlmostEqual(cx, 0.0, delta=DELTA)
        self.assertAlmostEqual(cy, -3.6 + 1.5, delta=DELTA)
        # Distance head<->segment unchanged through sweep + follow.
        self.assertAlmostEqual(
            _dist2(0.0, 1.5, cx, cy), 3.6 * 3.6, delta=DELTA)

    def test_sweep_ticks_themselves_do_not_translate(self):
        # During a sweep there is NO forward motion and no translational
        # drift: the chain only rotates about the head (GAME-10).
        segs = [make_seg(-3.6, 0.0, 's0')]
        engine = GameEngine(head=(0.0, 0.0), heading='right',
                            segments=segs)
        engine.request_direction('up')
        for _ in range(6):
            events = engine.step(DT)
            self.assertEqual(events[0][0], 'turning')
        self.assertEqual(engine.head, (0.0, 0.0))  # pivot unmoved
        cx, cy = engine.segments[0]['centroid']
        self.assertAlmostEqual(_dist2(0.0, 0.0, cx, cy), 3.6 * 3.6,
                               delta=DELTA)


class TestFollowAndCrashSemantics(unittest.TestCase):
    """GAME-05 head-wall crash is UNCHANGED by the follow rule: the head
    entering the margin still ends the run (the chain follows - walls
    only stop the head)."""

    def test_head_wall_crash_still_ends_run_with_chain(self):
        segs = [make_seg(9.6, 0.0, 's0'), make_seg(13.2, 0.0, 's1')]
        engine = GameEngine(head=(16.8, 0.0), heading='right',
                            segments=segs,
                            box_min=(-18.0, -18.0), box_max=(18.0, 18.0))
        events = engine.step(DT)
        self.assertEqual(events[-1], ('crashed', 'boundary'))
        self.assertTrue(engine.finished)
        self.assertEqual(engine.result, 'crashed')
        # The chain followed the final move by the same delta.
        self.assertAlmostEqual(engine.segments[0]['centroid'][0], 9.9,
                               delta=DELTA)
        self.assertAlmostEqual(engine.segments[1]['centroid'][0], 13.5,
                               delta=DELTA)
        # Finished engine is inert: nothing moves afterwards.
        self.assertEqual(engine.step(DT), [])


if __name__ == '__main__':
    unittest.main()
