"""HUD turn-feedback builders (ghost-point follow-up, plan 05-16 retest).

The live 'ghost point' symptom traced to the rigid-chain sweep veto was
correct-by-design - what was missing was FEEDBACK a player (and the
SRP_DEBUG tracer) can act on:

  - turn_refuse_text(reason): the info-box line for a refused turn.
    Keeps the checkpoint-pinned 'turn refused: <reason>' prefix and adds
    the why-clause a player can act on. (2026-09-19 owner directive: the
    wall veto is gone — walls apply to the head only; remaining refusal
    reasons are 'body' and 'pickup'.)
  - classify_turn_request(unit, ref_unit, pending_nonempty, in_sweep):
    the steering-outcome label the debug request trace prints for every
    arrow press; mirrors game_engine.request_direction's policies (same
    direction / 180 reversal drop silently, buffer max-1 first-kept,
    in-sweep newest-wins against the sweep TARGET).
  - debug_turn_request(name, outcome, ...): one 'DBG turn request' line
    per key press (SRP_DEBUG=1 only).

PURE stdlib; python3.6 (%-formatting). Discovery:

    python3.6 -m unittest discover -s tests -p "test_*.py" -v
"""
import os
import sys
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from serpentrum import hud_logic  # noqa: E402

RIGHT = (1.0, 0.0)
LEFT = (-1.0, 0.0)
UP = (0.0, 1.0)
DOWN = (0.0, -1.0)


class TestTurnRefuseText(unittest.TestCase):
    """The player-visible refusal line (checkpoint prefix preserved)."""

    def test_boundary_explains_head_only_wall_rule(self):
        # OWNER-APPROVED RULE CHANGE (2026-09-19 UTC): the wall leg of
        # the sweep pre-check is gone ('only detect wall from head,
        # ignore tail'); the chain may swing past the box during a
        # turn. The old text claimed "the swinging chain would cross the
        # wall" — pin the new head-only wording instead (kept defensive:
        # the engine no longer emits this reason).
        line = hud_logic.turn_refuse_text('boundary')
        self.assertTrue(line.startswith('turn refused: boundary'))
        self.assertIn('head', line)
        self.assertNotIn('swinging chain would cross the wall', line)

    def test_body_explains_self_collision(self):
        line = hud_logic.turn_refuse_text('body')
        self.assertTrue(line.startswith('turn refused: body'))
        self.assertIn('chain', line)

    def test_pickup_explains_molecule_clash(self):
        line = hud_logic.turn_refuse_text('pickup')
        self.assertTrue(line.startswith('turn refused: pickup'))
        self.assertIn('molecule', line)

    def test_unknown_reason_falls_back(self):
        line = hud_logic.turn_refuse_text('weird')
        self.assertTrue(line.startswith('turn refused: weird'))
        self.assertIn('chain', line)


class TestClassifyTurnRequest(unittest.TestCase):
    """Steering-outcome labels mirroring engine.request_direction."""

    def test_same_direction_drops(self):
        self.assertEqual(
            hud_logic.classify_turn_request(RIGHT, RIGHT, False, False),
            'dropped: same direction')
        # same-direction is checked BEFORE buffer-full (engine order)
        self.assertEqual(
            hud_logic.classify_turn_request(RIGHT, RIGHT, True, False),
            'dropped: same direction')

    def test_reversal_drops(self):
        self.assertEqual(
            hud_logic.classify_turn_request(LEFT, RIGHT, False, False),
            'dropped: 180 reversal')

    def test_buffer_full_drops_first_kept(self):
        self.assertEqual(
            hud_logic.classify_turn_request(UP, RIGHT, True, False),
            'dropped: buffer full (another key is already queued)')

    def test_queued_plain(self):
        self.assertEqual(
            hud_logic.classify_turn_request(UP, RIGHT, False, False),
            'queued')

    def test_in_sweep_reference_is_target_newest_wins(self):
        # Sweeping toward 'right': ref is the TARGET, newest always wins.
        self.assertEqual(
            hud_logic.classify_turn_request(UP, RIGHT, True, True),
            'queued (in-sweep, newest-wins)')
        self.assertEqual(
            hud_logic.classify_turn_request(DOWN, RIGHT, False, True),
            'queued (in-sweep, newest-wins)')
        # same as the sweep TARGET drops
        self.assertEqual(
            hud_logic.classify_turn_request(RIGHT, RIGHT, False, True),
            'dropped: same direction')
        # 180 of the sweep TARGET drops
        self.assertEqual(
            hud_logic.classify_turn_request(LEFT, RIGHT, True, True),
            'dropped: 180 reversal')


class TestDebugTurnRequest(unittest.TestCase):
    """Line shape: 'DBG turn request <dir> -> <outcome> [context]'."""

    def test_minimal(self):
        line = hud_logic.debug_turn_request('up', 'queued')
        self.assertEqual(line, 'DBG turn request up -> queued')

    def test_full_context(self):
        line = hud_logic.debug_turn_request(
            'left', 'dropped: 180 reversal', tick=42, heading='right',
            head_xy=(1.25, -2.5), ref='up')
        self.assertEqual(
            line,
            'DBG turn request left -> dropped: 180 reversal'
            ' tick=42 heading=right head=(1.25,-2.50) ref=up')

    def test_optional_fields_omit_cleanly(self):
        line = hud_logic.debug_turn_request('down', 'queued', tick=7)
        self.assertEqual(line, 'DBG turn request down -> queued tick=7')


if __name__ == '__main__':
    unittest.main()
