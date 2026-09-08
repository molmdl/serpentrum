"""GameEngine movement core tests (plan 02-06, TDD RED first).

Covers the movement-core contract: continuous-2D constant-speed forward
stepping (SPEED_A_PER_S = 3.0 A/s -> exactly 0.3 A per 0.1 s tick), the
max-1 direction queue with 180-degree and same-direction rejection,
pending-inert behavior (the queue only buffers in this plan), pause and
resume, deterministic reset (GAME-07), the segments test seam, and
two-engine determinism over identical step sequences.

Discovery command (python3.6.9 — NOTE: `-t .` FAILS on python3.6 with a
non-package start dir; do not add it):

    python3.6 -m unittest discover -s tests -p "test_*.py" -v

FORWARD-COMPATIBILITY RULE (02-06 -> 02-13): this suite NEVER calls
step() while a direction request is pending. In 02-06 a pending request
is deliberately inert — step() only moves forward and the queue only
buffers. Plan 02-13 later applies pending turns at the START of step();
because these tests never observe step() with a non-empty pending, that
contract change cannot break them. Queue tests therefore either never
step at all, or step only while pending is empty (e.g. after a request
was rejected and the queue stayed empty).
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from serpentrum import game_engine  # noqa: E402
from serpentrum.game_engine import GameEngine  # noqa: E402

# Canonical constructor args for the behavior cases: start at the origin
# heading right (+x); dt 0.1 s at 3.0 A/s -> exactly 0.3 A per tick.
ENGINE_ARGS = dict(head=(0.0, 0.0), heading='right')

# Coordinate tolerance pinned by the plan (assertAlmostEqual delta).
DELTA = 1e-9


def make_segment(molecule_id='mol_a', x=1.0, y=2.0):
    """Build a FRESH segment record per call.

    Segment record shape (engine state seam): index 0 of a segments list
    is the OLDEST entry (tail-most), the LAST is the most recently
    stacked. Tests must never share mutable dicts between assertions, so
    every call returns brand-new containers.
    """
    atoms = [('C', x, y, 0.0), ('H', x + 1.0, y, 0.0)]
    return {
        'molecule_id': molecule_id,
        'centroid': (x, y),
        'atoms': atoms,
        'atoms_n': len(atoms),
    }


class TestConstruction(unittest.TestCase):
    """Case 1 + 3 + the segments seam: defaults, speed pin, copying."""

    def test_construction_defaults(self):
        engine = GameEngine(**ENGINE_ARGS)
        self.assertEqual(engine.head, (0.0, 0.0))
        self.assertEqual(engine.heading, (1.0, 0.0))
        self.assertEqual(engine.segments, [])
        self.assertEqual(engine.pending, [])
        self.assertIs(engine.paused, False)

    def test_construction_other_heading(self):
        # Heading is stored as a UNIT VECTOR resolved through DIRS, and
        # movement must follow it (not hardcode +x): heading 'up' moves
        # along +y.
        engine = GameEngine(head=(0.0, 0.0), heading='up')
        self.assertEqual(engine.heading, (0.0, 1.0))
        events = engine.step(0.1)
        self.assertAlmostEqual(events[0][1][0], 0.0, delta=DELTA)
        self.assertAlmostEqual(events[0][1][1], 0.3, delta=DELTA)

    def test_invalid_heading_name_raises(self):
        # Unknown heading names are loud (ValueError), consistent with
        # request_direction's invalid-name contract.
        with self.assertRaises(ValueError):
            GameEngine(heading='diagonal')

    def test_speed_constant_pinned(self):
        # GAME-08 pin, asserted as a module constant: 3.0 A/s.
        self.assertEqual(game_engine.SPEED_A_PER_S, 3.0)

    def test_segments_seam_copies(self):
        seg = make_segment()
        segs = [seg]
        engine = GameEngine(segments=segs)
        # Engine owns copies, not caller identity: mutating the caller's
        # dict or list afterwards must not touch engine state.
        self.assertIsNot(engine.segments[0], seg)
        self.assertIsNot(engine.segments[0]['atoms'], seg['atoms'])
        seg['centroid'] = (99.0, 99.0)
        segs.append(make_segment(molecule_id='late'))
        self.assertEqual(engine.segments[0]['centroid'], (1.0, 2.0))
        self.assertEqual(len(engine.segments), 1)
        # Order preserved: index 0 oldest (tail-most), last most recent.
        two = GameEngine(segments=[make_segment('tail'),
                                   make_segment('nearest_head')])
        self.assertEqual(two.segments[0]['molecule_id'], 'tail')
        self.assertEqual(two.segments[1]['molecule_id'], 'nearest_head')


class TestForwardMotion(unittest.TestCase):
    """Cases 2 + 11: exact 0.3 A/tick advance; two-engine determinism."""

    def test_single_step_event_and_position(self):
        engine = GameEngine(**ENGINE_ARGS)
        events = engine.step(0.1)
        self.assertEqual(len(events), 1)
        name, pos = events[0]
        self.assertEqual(name, 'moved')
        self.assertAlmostEqual(pos[0], 0.3, delta=DELTA)
        self.assertAlmostEqual(pos[1], 0.0, delta=DELTA)
        self.assertAlmostEqual(engine.head[0], 0.3, delta=DELTA)
        self.assertAlmostEqual(engine.head[1], 0.0, delta=DELTA)

    def test_k_steps_exact_grid(self):
        # head.x == 0.3 * k after k steps of dt 0.1 (float arithmetic on
        # the 0.3 grid stays within the 1e-9 delta).
        engine = GameEngine(**ENGINE_ARGS)
        for k in range(1, 21):
            engine.step(0.1)
            self.assertAlmostEqual(engine.head[0], 0.3 * k, delta=DELTA)
            self.assertAlmostEqual(engine.head[1], 0.0, delta=DELTA)

    def test_two_engine_determinism(self):
        # Identical args + identical steps -> identical events and
        # positions, exactly (no RNG, no wall-clock anywhere).
        first = GameEngine(**ENGINE_ARGS)
        second = GameEngine(**ENGINE_ARGS)
        for _ in range(20):
            events_a = first.step(0.1)
            events_b = second.step(0.1)
            self.assertEqual(events_a, events_b)
            self.assertEqual(first.head, second.head)


class TestDirectionQueue(unittest.TestCase):
    """Cases 4-8: rejection rules vs the CURRENT heading; max-1 buffer.

    No test in this class ever calls step() (pending-inert forward
    compatibility — see module docstring).
    """

    def test_180_degree_rejected(self):
        engine = GameEngine(**ENGINE_ARGS)
        self.assertIs(engine.request_direction('left'), False)
        self.assertEqual(engine.pending, [])
        # The queue stayed empty, so stepping is allowed and just moves
        # forward (no turn event, no heading change in this plan).
        events = engine.step(0.1)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0][0], 'moved')
        self.assertAlmostEqual(events[0][1][0], 0.3, delta=DELTA)
        self.assertEqual(engine.heading, (1.0, 0.0))

    def test_same_direction_ignored(self):
        engine = GameEngine(**ENGINE_ARGS)
        self.assertIs(engine.request_direction('right'), False)
        self.assertEqual(engine.pending, [])

    def test_buffer_full_rejects_perpendicular(self):
        engine = GameEngine(**ENGINE_ARGS)
        self.assertIs(engine.request_direction('up'), True)
        self.assertEqual(engine.pending, ['up'])
        # 'down' is perpendicular to the CURRENT heading ('right'), so it
        # passes the 180 and same-direction checks and is rejected ONLY
        # by the buffer-full rule (isolates that rule from the 180 rule).
        self.assertIs(engine.request_direction('down'), False)
        self.assertEqual(engine.pending, ['up'])  # first request kept

    def test_180_rejected_even_while_buffer_full(self):
        # The literal case-6 wording ('left' while 'up' is pending):
        # 'left' is a 180-degree reversal of the CURRENT heading, so the
        # 180 rule rejects it; either way it is NOT queued and the
        # buffered request is the one kept.
        engine = GameEngine(**ENGINE_ARGS)
        self.assertIs(engine.request_direction('up'), True)
        self.assertIs(engine.request_direction('left'), False)
        self.assertEqual(engine.pending, ['up'])

    def test_invalid_direction_raises(self):
        engine = GameEngine(**ENGINE_ARGS)
        with self.assertRaises(ValueError):
            engine.request_direction('diagonal')
        self.assertEqual(engine.pending, [])

    def test_queue_is_pure_data(self):
        """Case 8: pending holds exactly the buffered direction-name
        strings in request order — rejected names never enter the queue,
        and no step() is called while pending is non-empty anywhere in
        this suite."""
        engine = GameEngine(**ENGINE_ARGS)
        self.assertIs(engine.request_direction('down'), True)
        self.assertEqual(engine.pending, ['down'])
        self.assertEqual([type(name).__name__ for name in engine.pending],
                         ['str'])
        # A second (buffer-full) request changes nothing.
        self.assertIs(engine.request_direction('up'), False)
        self.assertEqual(engine.pending, ['down'])
        # Requests rejected by the 180 / same-direction rules never enter
        # the queue either (fresh engine; no stepping anywhere here).
        fresh = GameEngine(**ENGINE_ARGS)
        fresh.request_direction('right')  # same direction -> ignored
        fresh.request_direction('left')   # 180 degrees -> ignored
        self.assertEqual(fresh.pending, [])


class TestPauseReset(unittest.TestCase):
    """Cases 9 + 10: pause freezes step() to a no-op; reset rebuilds."""

    def test_pause_freezes_and_resume_restores(self):
        engine = GameEngine(**ENGINE_ARGS)
        engine.pause()
        self.assertIs(engine.paused, True)
        self.assertEqual(engine.step(0.1), [])
        self.assertEqual(engine.head, (0.0, 0.0))
        engine.resume()
        self.assertIs(engine.paused, False)
        events = engine.step(0.1)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0][0], 'moved')
        self.assertAlmostEqual(events[0][1][0], 0.3, delta=DELTA)

    def test_reset_rebuilds_all_state(self):
        engine = GameEngine(**ENGINE_ARGS)
        engine.step(0.1)
        engine.step(0.1)  # moved twice; pending still empty here
        engine.pause()
        # Queue a request AFTER the last step and do NOT step again (the
        # suite never steps with a non-empty pending).
        engine.request_direction('up')
        self.assertEqual(engine.pending, ['up'])
        engine.reset(head=(0.0, 0.0), heading='right')
        self.assertEqual(engine.head, (0.0, 0.0))
        self.assertEqual(engine.heading, (1.0, 0.0))
        self.assertEqual(engine.pending, [])
        self.assertIs(engine.paused, False)
        self.assertEqual(engine.segments, [])
        # After reset it moves again exactly like a fresh engine.
        events = engine.step(0.1)
        self.assertAlmostEqual(events[0][1][0], 0.3, delta=DELTA)

    def test_reset_with_segments(self):
        segs = [make_segment(), make_segment('mol_b')]
        engine = GameEngine(**ENGINE_ARGS)
        engine.step(0.1)
        engine.reset(head=(0.0, 0.0), heading='right', segments=segs)
        self.assertEqual(len(engine.segments), 2)
        self.assertEqual(engine.segments[0]['molecule_id'], 'mol_a')
        self.assertEqual(engine.segments[1]['molecule_id'], 'mol_b')


if __name__ == '__main__':
    unittest.main()
