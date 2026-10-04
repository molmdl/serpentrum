"""tests/test_dialog_fit.py -- PURE unit tests for the fixed-size
dialog placement math (serpentrum/dialog_fit.py; debug session 06,
round 3: opening position + preset-refreeze re-clamp).

The arithmetic is testable HEADLESS because it is pure (py3.6):
dialog_fit imports nothing. The Qt call sites in gui.py are pinned
separately in tests/test_gui_pins.py (TestFixedDialogPositionChrome
-- headless dialog construction is a dead end, decision 01-05).

The "owner machine" cases below encode the measured environment from
the decoded round-2 SRP_DEBUG=1 capture (see the debug file:
identities 926=450*2+26 / 1613=771*2+71 / 1693=811*2+71 pin the 200%
scale and the frame margins native 13/58/13 = LOGICAL 6.5/29/6.5;
available height ~881.5 -> 882 logical px; the dialog freezes at 811
logical tall under the 07-10 cap basis max(560, int(avail*0.92))).
Every expected value is derived by hand in the comments.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from serpentrum import dialog_fit


class TestCenteredTopLeft(unittest.TestCase):
    """The construction-time base: widget rect centered on avail."""

    def test_centers_on_avail(self):
        # (1842-700)//2 = 571, (882-811)//2 = 35 -- the owner-machine
        # numbers: 811 of 882 leaves 35 logical px per side.
        self.assertEqual(
            dialog_fit.centered_top_left((0, 0, 1842, 882), (700, 811)),
            (571, 35))

    def test_integer_floor_division(self):
        # odd slack floors: (100-10)//2 == 45, (101-20)//2 == 40 --
        # positions stay integral, never half-pixel.
        self.assertEqual(
            dialog_fit.centered_top_left((0, 0, 100, 101), (10, 20)),
            (45, 40))

    def test_negative_origin_monitor(self):
        # secondary monitor left of the primary: centering is
        # relative to the avail rect wherever it lives.
        self.assertEqual(
            dialog_fit.centered_top_left((-1920, 0, 1920, 1040),
                                         (700, 811)),
            (-1920 + 610, 114))


class TestClampedPositionOwnerMachine(unittest.TestCase):
    """The owner's screen: available 1842x882 logical, dialog 700x811
    frozen (cap regime), frame margins top 29 LOGICAL (native 58 at
    200%). Centering alone must survive the clamp -- and must leave
    the real frame edges INSIDE the screen."""

    FALLBACK = dialog_fit.FALLBACK_FRAME_MARGINS  # (8, 32, 8, 8)
    AVAIL = (0, 0, 1842, 882)
    SIZE = (700, 811)

    def test_centered_base_survives_clamp_with_fallback(self):
        base = dialog_fit.centered_top_left(self.AVAIL, self.SIZE)
        self.assertEqual(
            dialog_fit.clamped_position(
                self.AVAIL, self.SIZE, self.FALLBACK, base),
            base)
        # headroom-vs-frame-margin verification (the reason pure
        # centering is safe in the cap regime): with the REAL
        # measured top margin 29, the frame top sits >= 0 ...
        y = base[1]
        self.assertGreaterEqual(
            y - 29, 0,
            'frame top must stay on-screen: %d - 29 = %d' % (y, y - 29))
        # ... and with the real bottom margin 6.5 (use 7 rounded
        # outward) the frame bottom stays above the avail bottom.
        self.assertLessEqual(y + 811 + 7, 882)

    def test_centered_base_survives_clamp_with_measured_margins(self):
        # real logical frame margins measured at 200%:
        # left/right 6.5, top 29, bottom 6.5 (outward-rounded ints
        # here). Clamp interval [29, 64] still contains 35.
        base = dialog_fit.centered_top_left(self.AVAIL, self.SIZE)
        self.assertEqual(
            dialog_fit.clamped_position(
                self.AVAIL, self.SIZE, (7, 29, 7, 7), base),
            base)

    def test_float_margins_do_not_move_or_crash(self):
        # frameMargins() can hand back floats in principle; the math
        # must neither crash nor shift the centered placement.
        base = dialog_fit.centered_top_left(self.AVAIL, self.SIZE)
        self.assertEqual(
            dialog_fit.clamped_position(
                self.AVAIL, self.SIZE, (6.5, 29.0, 6.5, 6.5), base),
            base)


class TestClampedPositionFloorRegime(unittest.TestCase):
    """The 560-floor regime (avail < 609 logical): the 0.92 headroom
    is gone, so CENTERING ALONE WOULD CLIP THE TITLE BAR -- the
    margin-aware clamp must shift the widget down instead."""

    def test_floor_case_shifts_down_to_keep_frame_top_inside(self):
        # avail 608, dialog 560: centered top = (608-560)//2 = 24;
        # clamp lower bound = 0 + 32 -> 24 < 32, so the clamp moves
        # the widget DOWN to 32. With the real 29-logical top margin
        # the frame top then sits at 32 - 29 = 3 >= 0: inside.
        base = dialog_fit.centered_top_left((0, 0, 1024, 608),
                                             (500, 560))
        self.assertEqual(base[1], 24)
        self.assertEqual(
            dialog_fit.clamped_position(
                (0, 0, 1024, 608), (500, 560),
                dialog_fit.FALLBACK_FRAME_MARGINS, base),
            (262, 32))

    def test_degenerate_avail_pins_frame_top(self):
        # avail 500 < 560 + margins: NO fitting position exists.
        # Policy: pin the frame TOP edge to the avail top (widget
        # top = 32) -- title bar stays visible/grabbable, overflow
        # rides on the bottom. x is untouched (it fits).
        self.assertEqual(
            dialog_fit.clamped_position(
                (0, 0, 1024, 500), (500, 560),
                dialog_fit.FALLBACK_FRAME_MARGINS, (100, 200)),
            (100, 32))


class TestClampedPositionRefreeze(unittest.TestCase):
    """Post-show refreeze semantics: clamp the CURRENT position
    under the NEW size with MINIMAL shift -- never re-center."""

    def test_grown_dialog_botted_out_is_pulled_back_up(self):
        # dialog grew to 811 tall while sitting low (y=850): clamp
        # interval [32, 882-811-8=63] -> y moves UP to exactly 63,
        # x untouched. This is the "grown dialog centered under the
        # old position could bottom out" fix.
        self.assertEqual(
            dialog_fit.clamped_position(
                (0, 0, 1842, 882), (700, 811),
                dialog_fit.FALLBACK_FRAME_MARGINS, (146, 850)),
            (146, 63))

    def test_current_position_preserved_when_it_fits(self):
        # a fitting user placement is byte-identically preserved --
        # no gratuitous re-centering on preset changes.
        self.assertEqual(
            dialog_fit.clamped_position(
                (0, 0, 1842, 882), (700, 771),
                dialog_fit.FALLBACK_FRAME_MARGINS, (100, 50)),
            (100, 50))

    def test_dragged_high_dialog_is_shifted_down(self):
        # user parked the dialog near the top (y=10): frame top
        # would sit at 10-32 above the screen -> clamp to 32.
        self.assertEqual(
            dialog_fit.clamped_position(
                (0, 0, 1842, 882), (700, 811),
                dialog_fit.FALLBACK_FRAME_MARGINS, (100, 10)),
            (100, 32))


class TestClampedPositionWideAxis(unittest.TestCase):
    """The x axis gets the identical clamp (width-cap / oversize
    behavior is axis-symmetric)."""

    def test_centered_wide_dialog_survives(self):
        base = dialog_fit.centered_top_left((0, 0, 800, 882), (700, 811))
        # interval [8, 800-700-8=92] contains 50: unchanged.
        self.assertEqual(
            dialog_fit.clamped_position(
                (0, 0, 800, 882), (700, 811),
                dialog_fit.FALLBACK_FRAME_MARGINS, base),
            base)

    def test_oversize_width_pins_left(self):
        # dialog 900 wider than avail 800: interval empty -> pin the
        # frame LEFT edge to the avail left (widget x = 8).
        self.assertEqual(
            dialog_fit.clamped_position(
                (0, 0, 800, 882), (900, 811),
                dialog_fit.FALLBACK_FRAME_MARGINS, (-50, 40)),
            (8, 40))


class TestFallbackMargins(unittest.TestCase):
    """The pre-show estimate must stay OUTWARD-rounded vs the
    measured logical frame (native 13/58/13 at 200% = 6.5/29/6.5),
    pinned by literal: (left, top, right, bottom)."""

    def test_fallback_margins_literal(self):
        self.assertEqual(dialog_fit.FALLBACK_FRAME_MARGINS,
                         (8, 32, 8, 8))
        left, top, right, bottom = dialog_fit.FALLBACK_FRAME_MARGINS
        self.assertGreaterEqual(top, 29,
                                'top estimate covers the measured '
                                '29-logical title bar')
        self.assertGreaterEqual(left, 6.5)
        self.assertGreaterEqual(right, 6.5)
        self.assertGreaterEqual(bottom, 6.5)


if __name__ == '__main__':
    unittest.main()
