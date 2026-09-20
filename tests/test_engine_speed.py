"""GameEngine per-instance speed tests (plan 5.1-01, TDD RED first).

Covers the Phase-5.1 GAME-11 engine knob: the trailing kwarg
``speed_a_per_s`` on ``GameEngine.__init__``/``reset`` — a per-instance
speed injected at construction/reset (GAME-08 stays true by
construction: one attribute, set once, never mutated mid-run). Cases:

1. Default preservation: an engine built WITHOUT the kwarg behaves
   exactly as before (SPEED_A_PER_S = 3.0 A/s -> 0.3 A per 0.1 s tick);
   every pre-5.1 call site stays green untouched.
2. Per-tier displacement: speed 2.0 -> 0.2 A/tick, 6.0 -> 0.6 A/tick,
   and movement always follows the HEADING unit vector (heading 'up'
   with 6.0 -> (0.0, 0.6), never hardcoded +x).
3. Train-follow parity: the WHOLE CHAIN is translated by the SAME
   per-tier delta the head took (_translate_chain consumes the same
   delta — no second speed source).
4. reset re-seed: reset(..., speed_a_per_s=4.5) re-seeds the instance
   speed; a later reset() WITHOUT the kwarg restores the 3.0 default.
5. Loud contract: speed_a_per_s <= 0 raises ValueError (mirrors the
   unknown-heading ValueError).
6. Two-engine determinism over identical step sequences including a
   queued turn (mirrors test_engine_core.py's determinism pattern).
7. GAME-08 module pin UNTOUCHED: game_engine.SPEED_A_PER_S == 3.0 (the
   constant is the kwarg DEFAULT now, never mutated at runtime — it is
   also pinned in test_engine_core.py; kept here as the speed-suite
   anchor).
8. Spawn seed coupling (DOCUMENTED ACCEPTED SIDE EFFECT — do NOT
   "fix"): seed_from_setup crc32s the whole setup dict, so a speed
   change deterministically RE-SEEDS the pickup sequence (a tier switch
   gets its own deterministic spawns — same semantics as changing the
   box size), while copying the dict never changes the seed.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from serpentrum import game_engine  # noqa: E402
from serpentrum import spawn  # noqa: E402
from serpentrum.game_engine import GameEngine  # noqa: E402

# Canonical constructor args: origin, heading right (+x); dt 0.1 s.
ENGINE_ARGS = dict(head=(0.0, 0.0), heading='right')

# Coordinate tolerance (assertAlmostEqual delta), mirroring
# test_engine_core.py's DELTA convention.
DELTA = 1e-9


def make_segment(molecule_id='mol_a', x=1.0, y=2.0):
    """Build a FRESH segment record per call (mirrors test_engine_core).

    Never share mutable dicts between assertions; every call returns
    brand-new containers.
    """
    atoms = [('C', x, y, 0.0), ('H', x + 1.0, y, 0.0)]
    return {
        'molecule_id': molecule_id,
        'centroid': (x, y),
        'atoms': atoms,
        'atoms_n': len(atoms),
    }


class TestDefaultPreserved(unittest.TestCase):
    """Case 1: no kwarg -> the 3.0 A/s baseline is unchanged."""

    def test_default_step_is_03_a(self):
        engine = GameEngine(**ENGINE_ARGS)
        events = engine.step(0.1)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0][0], 'moved')
        self.assertAlmostEqual(events[0][1][0], 0.3, delta=DELTA)
        self.assertAlmostEqual(events[0][1][1], 0.0, delta=DELTA)
        self.assertAlmostEqual(engine.head[0], 0.3, delta=DELTA)
        self.assertAlmostEqual(engine.head[1], 0.0, delta=DELTA)

    def test_default_attribute_is_30(self):
        engine = GameEngine(**ENGINE_ARGS)
        self.assertEqual(engine.speed_a_per_s, 3.0)


class TestPerTierDisplacement(unittest.TestCase):
    """Case 2: per-tier step size; movement follows the heading."""

    def test_relaxed_tier_20(self):
        engine = GameEngine(speed_a_per_s=2.0, **ENGINE_ARGS)
        events = engine.step(0.1)
        self.assertAlmostEqual(events[0][1][0], 0.2, delta=DELTA)
        self.assertAlmostEqual(events[0][1][1], 0.0, delta=DELTA)

    def test_expert_tier_60(self):
        engine = GameEngine(speed_a_per_s=6.0, **ENGINE_ARGS)
        events = engine.step(0.1)
        self.assertAlmostEqual(events[0][1][0], 0.6, delta=DELTA)
        self.assertAlmostEqual(events[0][1][1], 0.0, delta=DELTA)

    def test_movement_follows_heading_not_hardcoded_x(self):
        engine = GameEngine(head=(0.0, 0.0), heading='up',
                            speed_a_per_s=6.0)
        events = engine.step(0.1)
        self.assertAlmostEqual(events[0][1][0], 0.0, delta=DELTA)
        self.assertAlmostEqual(events[0][1][1], 0.6, delta=DELTA)


class TestTrainFollowParity(unittest.TestCase):
    """Case 3: the chain translates by the SAME per-tier delta."""

    def test_segment_translated_by_same_delta(self):
        engine = GameEngine(segments=[make_segment()],
                            speed_a_per_s=6.0, **ENGINE_ARGS)
        engine.step(0.1)
        self.assertAlmostEqual(engine.head[0], 0.6, delta=DELTA)
        self.assertAlmostEqual(engine.head[1], 0.0, delta=DELTA)
        seg = engine.segments[0]
        self.assertAlmostEqual(seg['centroid'][0], 1.6, delta=DELTA)
        self.assertAlmostEqual(seg['centroid'][1], 2.0, delta=DELTA)
        # Atoms ride the identical translation; z and symbols preserved.
        c_atom = seg['atoms'][0]
        self.assertAlmostEqual(c_atom[1], 1.6, delta=DELTA)
        self.assertAlmostEqual(c_atom[2], 2.0, delta=DELTA)
        self.assertEqual(c_atom[0], 'C')
        self.assertEqual(c_atom[3], 0.0)


class TestResetReseed(unittest.TestCase):
    """Case 4: reset re-seeds the speed; reset() restores the default."""

    def test_reset_reseeds_speed(self):
        engine = GameEngine(**ENGINE_ARGS)
        engine.reset(head=(0.0, 0.0), heading='right', speed_a_per_s=4.5)
        self.assertEqual(engine.speed_a_per_s, 4.5)
        events = engine.step(0.1)
        self.assertAlmostEqual(events[0][1][0], 0.45, delta=DELTA)

    def test_reset_without_kwarg_restores_default(self):
        engine = GameEngine(speed_a_per_s=6.0, **ENGINE_ARGS)
        self.assertEqual(engine.speed_a_per_s, 6.0)
        engine.reset(head=(0.0, 0.0), heading='right')
        self.assertEqual(engine.speed_a_per_s, 3.0)
        events = engine.step(0.1)
        self.assertAlmostEqual(events[0][1][0], 0.3, delta=DELTA)


class TestLoudRejection(unittest.TestCase):
    """Case 5: speed_a_per_s <= 0 is a ValueError, not silent clamping."""

    def test_zero_rejected_at_construction(self):
        with self.assertRaises(ValueError):
            GameEngine(speed_a_per_s=0)

    def test_negative_rejected_at_construction(self):
        with self.assertRaises(ValueError):
            GameEngine(speed_a_per_s=-1.0)

    def test_nonpositive_rejected_at_reset(self):
        engine = GameEngine(**ENGINE_ARGS)
        with self.assertRaises(ValueError):
            engine.reset(head=(0.0, 0.0), heading='right',
                         speed_a_per_s=-1.0)


class TestDeterminism(unittest.TestCase):
    """Case 6: two identical engines (speed included) stay identical."""

    def test_two_engine_determinism_with_turn(self):
        first = GameEngine(speed_a_per_s=4.5, **ENGINE_ARGS)
        second = GameEngine(speed_a_per_s=4.5, **ENGINE_ARGS)
        for i in range(20):
            if i == 5:
                # Queue the SAME turn on both; it opens a sweep at the
                # next step (turn ticks never move the head).
                first.request_direction('up')
                second.request_direction('up')
            events_a = first.step(0.1)
            events_b = second.step(0.1)
            self.assertEqual(events_a, events_b)
            self.assertEqual(first.head, second.head)
        # Sanity: the queued turn actually happened (heading now up).
        self.assertEqual(first.heading, (0.0, 1.0))
        self.assertEqual(second.heading, (0.0, 1.0))


class TestConstantPin(unittest.TestCase):
    """Case 7: the GAME-08 module pin is UNTOUCHED by the kwarg."""

    def test_speed_constant_still_30(self):
        self.assertEqual(game_engine.SPEED_A_PER_S, 3.0)


class TestSeedCoupling(unittest.TestCase):
    """Case 8: DOCUMENTED ACCEPTED SIDE EFFECT (do NOT "fix").

    seed_from_setup crc32s the ENTIRE setup dict, so a speed-tier switch
    deterministically re-seeds the pickup sequence — the same semantics
    as changing the box size. Same-tier Restart reproduces the identical
    spawn sequence (GAME-07 intact); copying the dict never changes the
    seed. Research: 5.1-RESEARCH-engine-speed.md "Spawn seed coupling".
    """

    def test_speed_change_reseeds_deterministically(self):
        seed_relaxed = spawn.seed_from_setup({'speed': 2.0})
        seed_expert = spawn.seed_from_setup({'speed': 4.5})
        self.assertNotEqual(seed_relaxed, seed_expert)

    def test_dict_copy_keeps_seed(self):
        setup = {'speed': 4.5, 'box': 'medium', 'win_cap_molecules': 5}
        self.assertEqual(spawn.seed_from_setup(setup),
                         spawn.seed_from_setup(dict(setup)))


if __name__ == '__main__':
    unittest.main()
