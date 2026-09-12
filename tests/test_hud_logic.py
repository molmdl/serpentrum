"""tests/test_hud_logic.py -- HUD pure display helpers (plan 04-02, TDD RED first).

Covers the three WSL-testable display calculations extracted from the
Game tab's widget code (04-RESEARCH-hud.md Q2/Q6: extract formatable
logic to a PURE module + test file, keep GameTab thin — the widgets
themselves stay human-verify-only per 01-05):

  hud_logic.format_elapsed(seconds)  -> 'M:SS' (minutes not zero-padded,
      seconds zero-padded to 2, fractional seconds FLOORED, negatives
      clamped to '0:00') — the Game tab's delta-based elapsed display.
  hud_logic.remaining_text(value)    -> 'Remaining: N' or 'Remaining: -'
      (None-safe molecules-remaining label, GAME-07).
  GameEngine.molecules_remaining     -> read-only property:
      cap - molecules_stacked, None when cap is None (04-RESEARCH-hud.md
      Q4: keeps the arithmetic in the testable pure engine; the HUD reads
      engine.molecules_remaining). The engine has NO wall-clock by
      design (04-RESEARCH-gameloop.md Q5/S3) — this property adds no
      timing.

Discovery command (python3.6 — no '-t .' on non-package start dir):

    python3.6 -m unittest discover -s tests -p "test_hud_logic.py" -v
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from serpentrum import hud_logic  # noqa: E402
from serpentrum.game_engine import GameEngine  # noqa: E402

ENGINE_ARGS = dict(head=(0.0, 0.0), heading='right')


class TestFormatElapsed(unittest.TestCase):
    """format_elapsed(seconds) -> 'M:SS'; 6 pinned cases."""

    def test_zero(self):
        self.assertEqual(hud_logic.format_elapsed(0), '0:00')

    def test_over_one_minute(self):
        self.assertEqual(hud_logic.format_elapsed(65), '1:05')

    def test_ten_minutes_no_padding(self):
        self.assertEqual(hud_logic.format_elapsed(600), '10:00')

    def test_fractional_seconds_floored(self):
        # 75.9 must render '1:15', never '1:16' (floor, not round).
        self.assertEqual(hud_logic.format_elapsed(75.9), '1:15')

    def test_negative_clamped(self):
        # A tick landing before start_time must never render negative.
        self.assertEqual(hud_logic.format_elapsed(-3.2), '0:00')

    def test_just_under_an_hour(self):
        self.assertEqual(hud_logic.format_elapsed(3599), '59:59')


class TestRemainingText(unittest.TestCase):
    """remaining_text(value) -> 'Remaining: N' | 'Remaining: -'."""

    def test_positive(self):
        self.assertEqual(hud_logic.remaining_text(10), 'Remaining: 10')

    def test_zero(self):
        self.assertEqual(hud_logic.remaining_text(0), 'Remaining: 0')

    def test_none(self):
        # cap is None -> remaining is unknown; the engine allows cap=None.
        self.assertEqual(hud_logic.remaining_text(None), 'Remaining: -')


class TestEngineMoleculesRemaining(unittest.TestCase):
    """GameEngine.molecules_remaining: cap - molecules_stacked, None-safe."""

    def test_full_cap_at_start(self):
        engine = GameEngine(cap=10, **ENGINE_ARGS)
        self.assertEqual(engine.molecules_remaining, 10)

    def test_after_stacking(self):
        # molecules_stacked is a plain public counter (game_engine.py
        # increments it on capture); stub the stacked count directly.
        engine = GameEngine(cap=10, **ENGINE_ARGS)
        engine.molecules_stacked = 3
        self.assertEqual(engine.molecules_remaining, 7)

    def test_none_cap(self):
        engine = GameEngine(cap=None, **ENGINE_ARGS)
        self.assertIs(engine.molecules_remaining, None)

    def test_reflects_reset(self):
        # Reset semantics: reset(cap=5) rebuilds cap + zeroes the counter,
        # so the property shows the fresh cap immediately afterwards.
        engine = GameEngine(cap=10, **ENGINE_ARGS)
        engine.molecules_stacked = 3
        engine.reset(head=(0.0, 0.0), heading='right', cap=5)
        self.assertEqual(engine.molecules_remaining, 5)
        # The property is read-only derived state: reset must not have
        # churned anything else observable here (GAME-07 determinism).
        self.assertEqual(engine.head, (0.0, 0.0))
        self.assertIs(engine.paused, False)


if __name__ == '__main__':
    unittest.main()
