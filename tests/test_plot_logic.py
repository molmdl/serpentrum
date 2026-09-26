"""Tests for the IR plot's PURE data half (serpentrum/plot_logic.py,
plan 07-02 — the SPECTRA-03 pure half).

Every numeric anchor below is pinned to VERIFIED values probed against the
committed fixtures on 2026-09-06/07 (02-RESEARCH-pure-core.md S2 + the
02-12 plan's load-bearing facts; restated in spectra.py:12-15 docstring):

  - g98.out (26-atom phenol pi-dimer, 72 modes): global max-intensity mode
    1150.6639 cm-1 @ 257.1018 km/mol (isolated — nearest sizable neighbor
    37.65 @ 1109.44, 41 cm-1 away); default grid exactly [0.0, 3600.0];
    negatives at modes 1-3 (-31.9175 / -23.0766 / -18.1086 -> n_imaginary
    == 3); EMPTY modes -> the pinned zero curve (spectra.py:465-466).

Tick-selection anchors (plan-pinned): nice_ticks(0, 3600, 8) -> step 500;
nice_ticks(0, 10, 4) -> step 2.5 (1-decimal labels); zero-range and
negative-low inputs never crash.

NOTE on ASCII checks: str.isascii() is python3.7+; the WSL gate compiles
and runs python3.6, so ASCII-ness is asserted via the _is_ascii helper
below (all(ord(c) < 128 ...)).

Discovery command (verified on 3.6.9 — NOTE: `-t .` FAILS on python3.6
with a non-package start dir; do not add it):

    python3.6 -m unittest discover -s tests -p "test_*.py" -v

Convention: every test file in tests/ repeats the sys.path self-insert
below; tests/ deliberately has NO __init__.py (plugin-path safety), and
tests/fixtures/xtb/ is a plain data directory (never a package).
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from serpentrum import plot_logic, spectra  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G98_PATH = os.path.join(ROOT, 'tests', 'fixtures', 'xtb', 'g98.out')

# Verified fixture anchors (02-12 plan load-bearing facts).
PEAK_FREQ = 1150.6639
PEAK_INTEN = 257.1018
FWHM = 16.0


def _is_ascii(text):
    """python3.6-compatible str.isascii() (added upstream only in 3.7)."""
    return all(ord(ch) < 128 for ch in text)


class TestNiceTicks(unittest.TestCase):
    """Classic 1/2/2.5/5 x 10^n step selection; total over degenerate
    inputs (zero-range, negative-low)."""

    def test_anchor_3600(self):
        ticks = plot_logic.nice_ticks(0.0, 3600.0, 8)
        step = ticks[1][0] - ticks[0][0]
        self.assertEqual(step, 500.0)
        self.assertEqual(ticks[0][0], 0.0)
        self.assertLessEqual(ticks[-1][0], 3600.0)
        self.assertIn(len(ticks), range(6, 10))
        for _value, label in ticks:
            self.assertTrue(_is_ascii(label), 'non-ASCII label %r' % label)

    def test_two_point_five_step(self):
        ticks = plot_logic.nice_ticks(0.0, 10.0, 4)
        self.assertEqual([t for t, _label in ticks],
                         [0.0, 2.5, 5.0, 7.5, 10.0])
        self.assertEqual([label for _t, label in ticks],
                         ['0.0', '2.5', '5.0', '7.5', '10.0'])

    def test_subunit_step(self):
        ticks = plot_logic.nice_ticks(0.0, 1.0, 5)
        step = ticks[1][0] - ticks[0][0]
        self.assertEqual(step, 0.2)
        for value, label in ticks:
            self.assertGreaterEqual(value, 0.0)
            self.assertLessEqual(value, 1.0)
            self.assertIn('.', label)
            self.assertEqual(len(label.split('.')[1]), 1,
                             'label %r not at 1-decimal precision' % label)

    def test_zero_range(self):
        ticks = plot_logic.nice_ticks(5.0, 5.0, 8)
        self.assertEqual(len(ticks), 1)
        self.assertEqual(ticks[0][0], 5.0)

    def test_negative_low(self):
        ticks = plot_logic.nice_ticks(-100.0, 900.0, 5)
        values = [t for t, _label in ticks]
        for value in values:
            self.assertGreaterEqual(value, -100.0)
            self.assertLessEqual(value, 900.0)
        for prev, cur in zip(values, values[1:]):
            self.assertLess(prev, cur, 'ticks not strictly ascending')
        diffs = [cur - prev for prev, cur in zip(values, values[1:])]
        self.assertTrue(diffs, 'need >= 2 ticks for a step check')
        for diff in diffs:
            self.assertEqual(diff, 200.0)

    def test_labels_match_step_precision(self):
        # For a step < 1 the labels carry the STEP's decimal count — never
        # a bare '0' where '0.2'-class precision is in force.
        ticks = plot_logic.nice_ticks(0.0, 1.0, 5)
        self.assertEqual(ticks[0][1], '0.0')
        for _value, label in ticks:
            self.assertEqual(len(label.split('.')[1]), 1,
                             'label %r loses the step precision' % label)


class TestBuildScene(unittest.TestCase):
    """Scene = paint-ready data over spectra.broaden: fixture scene, peak
    localization, y_max headroom/floor, ticks in range, ASCII labels,
    fwhm passthrough + ValueError surfacing."""

    @classmethod
    def setUpClass(cls):
        cls.spectrum = spectra.parse_g98(G98_PATH)
        cls.scene = plot_logic.build_scene(cls.spectrum.modes)

    def test_fixture_scene(self):
        scene = self.scene
        self.assertEqual(scene.n_modes, 72)
        self.assertEqual(scene.n_imaginary, 3)
        self.assertEqual(scene.x_min, 0.0)
        self.assertEqual(scene.x_max, 3600.0)
        self.assertEqual(len(scene.xs), 800)
        self.assertEqual(len(scene.ys), 800)

    def test_peak_localization(self):
        scene = self.scene
        k = max(range(len(scene.ys)), key=lambda i: scene.ys[i])
        self.assertGreaterEqual(scene.xs[k], PEAK_FREQ - FWHM)
        self.assertLessEqual(scene.xs[k], PEAK_FREQ + FWHM)
        # Amplitude anchor: grid step = 3600/799 ~ 4.506, so the argmax
        # sits at most half a step (~2.25 cm-1) from 1150.6639; a
        # Gaussian at sigma 6.794574 retains >= 0.946 of its center
        # amplitude there (the 02-12-verified arithmetic; the committed
        # broaden suite pins the same quantity at 0.9 * PEAK_INTEN with
        # ~0.05 of neighbor lift). Measured 249.12 for this grid.
        self.assertGreaterEqual(scene.ys[k], 0.9 * PEAK_INTEN)

    def test_y_max_headroom(self):
        scene = self.scene
        self.assertAlmostEqual(scene.y_max, max(scene.ys) * 1.1,
                               delta=1e-9)
        k = max(range(len(scene.ys)), key=lambda i: scene.ys[i])
        self.assertGreaterEqual(scene.y_max, scene.ys[k])

    def test_empty_modes_floor(self):
        scene = plot_logic.build_scene([])
        self.assertTrue(all(y == 0.0 for y in scene.ys))
        self.assertEqual(scene.y_max, plot_logic.Y_MAX_FLOOR)
        self.assertNotEqual(scene.y_max, 0.0)
        self.assertEqual(scene.n_modes, 0)
        self.assertEqual(scene.n_imaginary, 0)
        self.assertTrue(scene.x_ticks, 'empty scene must still get x ticks')
        self.assertTrue(scene.y_ticks, 'empty scene must still get y ticks')

    def test_ticks_within_range(self):
        scene = self.scene
        x_values = [t for t, _label in scene.x_ticks]
        y_values = [t for t, _label in scene.y_ticks]
        for value in x_values:
            self.assertGreaterEqual(value, scene.x_min)
            self.assertLessEqual(value, scene.x_max)
        for value in y_values:
            self.assertGreaterEqual(value, 0.0)
            self.assertLessEqual(value, scene.y_max)
        for prev, cur in zip(x_values, x_values[1:]):
            self.assertLess(prev, cur, 'x ticks not strictly ascending')
        for prev, cur in zip(y_values, y_values[1:]):
            self.assertLess(prev, cur, 'y ticks not strictly ascending')

    def test_ascii_labels(self):
        scene = self.scene
        self.assertEqual(scene.x_label, 'wavenumber (cm-1)')
        self.assertEqual(scene.y_label, 'IR intensity (km/mol)')
        self.assertTrue(_is_ascii(scene.x_label))
        self.assertTrue(_is_ascii(scene.y_label))

    def test_fwhm_passthrough(self):
        scene32 = plot_logic.build_scene(self.spectrum.modes, fwhm=32.0)
        self.assertEqual(scene32.fwhm, 32.0)
        self.assertNotEqual(scene32.ys, self.scene.ys,
                            'fwhm=32 must differ from fwhm=16 at the '
                            'peak shoulders — fwhm is a live parameter')

    def test_invalid_fwhm_raises(self):
        with self.assertRaises(ValueError):
            plot_logic.build_scene([], fwhm=0.0)


class TestSizePresets(unittest.TestCase):
    """Pure (label, (w, h)) data for the house addItem(label, data) combo
    pattern; 'medium (640x400)' is the pinned default (first entry)."""

    def test_shape(self):
        presets = plot_logic.size_presets()
        self.assertGreaterEqual(len(presets), 2)
        self.assertEqual(presets[0], ('medium (640x400)', (640, 400)))
        for label, dims in presets:
            self.assertIsInstance(label, str)
            self.assertIsInstance(dims, tuple)
            self.assertEqual(len(dims), 2)
            width, height = dims
            self.assertIsInstance(width, int)
            self.assertIsInstance(height, int)
            self.assertGreaterEqual(width, 640)
            self.assertGreaterEqual(height, 400)
            self.assertTrue(_is_ascii(label),
                            'non-ASCII preset label %r' % label)


class TestModeCaption(unittest.TestCase):
    """The imaginary-mode caption: counts only, no raw frequencies (the
    single shared frequency formatter lives in spectra_ui.freq_label)."""

    @classmethod
    def setUpClass(cls):
        cls.scene = plot_logic.build_scene(
            spectra.parse_g98(G98_PATH).modes)

    def test_imaginary_caption(self):
        caption = plot_logic.mode_caption(self.scene)
        self.assertEqual(caption,
                         '72 modes; 3 below 0 (imaginary) - see the table')
        self.assertTrue(_is_ascii(caption))

    def test_no_caption_when_none_imaginary(self):
        zero_imaginary = self.scene._replace(n_imaginary=0)
        self.assertEqual(plot_logic.mode_caption(zero_imaginary), '')


if __name__ == '__main__':
    unittest.main()
