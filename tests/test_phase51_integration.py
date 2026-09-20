"""Phase 5.1 end-to-end PURE integration chain test (plan 5.1-06, Task 1).

Proves SC3 + SC2 at the pure layer for EVERY tier in
``setup_logic.SPEED_TIERS``:

  SPEED_TIERS -> save_setup -> load_setup -> merge_defaults -> validate
  -> GameEngine(speed_a_per_s=...) -> step()

plus the three backcompat/acceptance pins:

* absent-key backcompat — a setup file written WITHOUT a 'speed' key
  loads, merges to the documented default tier, and validates clean
  (SC3's "files written before this feature load with the default
  tier"; the Phase-8 Save/Load BUTTONS inherit this wiring for free).
* custom-speed acceptance — a hand-tuned speed (e.g. 50.0 A/s) merges
  and validates clean (accept-as-is rule; the tier combo is the UI
  constraint, not the schema) and resolves to the 'custom' tier name.
* seed-coupling documentation pin — seed_from_setup crc32-hashes the
  WHOLE setup dict, so two different tiers deterministically produce
  two different seeds. This is a DOCUMENTED ACCEPTED side effect (plan
  5.1-06 orchestrator context; same semantics as changing the box
  size), NOT a bug.

Expectations are DERIVED from setup_logic.SPEED_TIERS /
setup_logic.DEFAULTS — never hardcoded — so owner value tweaks at the
feel-check never break this file.

python3.6 + unittest; pure modules only (setup_logic / game_engine /
spawn). No __init__.py here (plugin-path safety, run_gates gate 1).
"""

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from serpentrum import game_engine  # noqa: E402
from serpentrum import setup_logic  # noqa: E402
from serpentrum import spawn  # noqa: E402

# Fixed step dt (mirrors gui_game.TICK_DT = 0.1) and the coordinate
# tolerance convention from test_engine_core.py (DELTA = 1e-9).
DT = 0.1
DELTA = 1e-9


class TestPerTierPureChain(unittest.TestCase):
    """SC3 + SC2 pure proof, parametrized over every SPEED_TIERS entry."""

    def test_tier_chain(self):
        box_min, box_max = setup_logic.BOX_PRESETS['medium']
        for name, aps in setup_logic.SPEED_TIERS:
            with self.subTest(tier=name, aps=aps):
                # save -> load round-trip (SC3 persistence half).
                setup = setup_logic.new_setup()
                setup['speed'] = aps
                text = setup_logic.save_setup(setup)
                loaded = setup_logic.load_setup(text)
                # merge + validate (SC3 chain into live state).
                merged = setup_logic.merge_defaults(loaded)
                self.assertEqual(merged['speed'], aps)
                errors, _warnings = setup_logic.validate(merged)
                self.assertEqual(errors, [],
                                 'tier %s validate errors: %r'
                                 % (name, errors))
                # construct + step (SC2: tier speed drives the engine).
                engine = game_engine.GameEngine(
                    head=(0.0, 0.0), heading='right',
                    box_min=box_min, box_max=box_max,
                    speed_a_per_s=merged['speed'])
                engine.step(DT)
                hx, hy = engine.head
                self.assertAlmostEqual(hx, aps * DT, delta=DELTA,
                                       msg='tier %s head x after one step'
                                       % (name,))
                self.assertAlmostEqual(hy, 0.0, delta=DELTA,
                                       msg='tier %s head y drift'
                                       % (name,))


class TestAbsentKeyBackcompat(unittest.TestCase):
    """Pre-feature setup files (no 'speed' key) default-tier cleanly."""

    def test_load_merge_validate_without_speed(self):
        legacy = dict(setup_logic.DEFAULTS)
        legacy.pop('speed')
        text = json.dumps(legacy, sort_keys=True, indent=2)
        loaded = setup_logic.load_setup(text)
        self.assertNotIn('speed', loaded)
        merged = setup_logic.merge_defaults(loaded)
        self.assertEqual(merged['speed'], setup_logic.DEFAULTS['speed'])
        errors, _warnings = setup_logic.validate(merged)
        self.assertEqual(errors, [])
        # The default must be a NAMED tier, never 'custom'.
        self.assertEqual(
            setup_logic.speed_tier_for(merged['speed']), 'normal')


class TestCustomSpeedAcceptance(unittest.TestCase):
    """Hand-tuned speeds stay loadable (accept-as-is rule)."""

    def test_custom_speed_validates_and_resolves_custom(self):
        custom = setup_logic.merge_defaults({'speed': 50.0})
        self.assertEqual(custom['speed'], 50.0)
        errors, _warnings = setup_logic.validate(custom)
        self.assertEqual(errors, [])
        self.assertEqual(setup_logic.speed_tier_for(50.0), 'custom')


class TestSeedCouplingPin(unittest.TestCase):
    """DOCUMENTED ACCEPTED side effect: crc32(setup) re-seeds per tier."""

    def test_distinct_tiers_distinct_seeds(self):
        names_pairs = list(setup_logic.SPEED_TIERS)
        self.assertGreaterEqual(len(names_pairs), 2,
                                'pin needs >= 2 tiers')
        (name_a, aps_a), (name_b, aps_b) = names_pairs[0], names_pairs[-1]
        merged_a = setup_logic.merge_defaults({'speed': aps_a})
        merged_b = setup_logic.merge_defaults({'speed': aps_b})
        seed_a = spawn.seed_from_setup(merged_a)
        seed_b = spawn.seed_from_setup(merged_b)
        self.assertNotEqual(seed_a, seed_b,
                            'tiers %s / %s must seed differently'
                            % (name_a, name_b))
        # Determinism per tier: same dict re-hash is stable.
        self.assertEqual(seed_a, spawn.seed_from_setup(dict(merged_a)))


if __name__ == '__main__':
    unittest.main()
