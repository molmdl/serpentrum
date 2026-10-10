"""Tests for the IR plot's PURE data half (serpentrum/plot_logic.py,
plan 07-02 — the SPECTRA-03 pure half).

Every numeric anchor below is pinned to VERIFIED values probed against
the committed fixtures (02-RESEARCH-pure-core.md S2, the 02-12
load-bearing facts, re-probed 2026-10-04 for the GATE V amendment):

  - g98.out (26-atom phenol pi-dimer, 72 modes): max-intensity mode
    1150.6639 cm-1 @ 257.1018 km/mol (isolated — nearest sizable
    neighbor 37.65 @ 1109.44, 41 cm-1 away); second-strongest mode
    405.1591 @ 235.5447; negatives at modes 1-3 (-31.9175 / -23.0766 /
    -18.1086 -> n_imaginary == 3); EMPTY modes -> the pinned zero curve
    (broaden's empty-modes contract).
  - GATE V amendment (owner directive 2026-10-04): the curve is the
    Multiwfn-parity Lorentzian (FWHM 8, unit-area x100), so the scene
    peaks at the strong mode the grid samples best — the 235.5447 mode
    (measured argmax 405.506884 @ 1873.257563 = 0.9994 of its (100/pi)*
    (I/g) center 1874.3476) — and the y axis reads 'epsilon (L mol-1
    cm-1)' (owner unit correction 2026-10-04: Multiwfn's discrete lines
    are km/mol; the curve is the molar absorption coefficient).

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
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from serpentrum import plot_logic, spectra  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G98_PATH = os.path.join(ROOT, 'tests', 'fixtures', 'xtb', 'g98.out')

# Verified fixture anchors (probe-verified 2026-10-04).
PEAK_FREQ = 1150.6639
PEAK_INTEN = 257.1018
SECOND_FREQ = 405.1591
SECOND_INTEN = 235.5447
FWHM = 8.0


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
        # GATE V amendment (2026-10-04): under the Multiwfn-parity
        # Lorentzian (unit-area x100, FWHM 8) the fixture scene peaks at
        # the second-strongest mode 405.1591 @ 235.5447 (grid-sampled at
        # dx = +0.348), NOT at the max-intensity 1150.6639 mode (whose
        # nearest grid point sits dx = -1.7277 away, value 1732.0 =
        # 0.847 of its center). Measured argmax value 1873.257563 =
        # 0.9994 * CENTRAL, where CENTRAL = (100/pi)*(235.5447/4).
        self.assertGreaterEqual(scene.xs[k], SECOND_FREQ - FWHM)
        self.assertLessEqual(scene.xs[k], SECOND_FREQ + FWHM)
        central = (100.0 / math.pi) * (SECOND_INTEN / (FWHM / 2.0))
        self.assertGreaterEqual(scene.ys[k], 0.9 * central)
        self.assertLessEqual(scene.ys[k], 1.1 * central)

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
        # GATE V amendment (2026-10-04): the curve values are the
        # Multiwfn-scaled convention (unit-area Lorentzian x100), so the
        # y axis must NOT claim raw km/mol. Owner unit correction (GATE
        # V, same date): Multiwfn's discrete lines are km/mol; the
        # curve is the molar absorption coefficient epsilon (L mol-1
        # cm-1).
        self.assertEqual(scene.y_label,
                         'epsilon (L mol-1 cm-1)')
        self.assertTrue(_is_ascii(scene.x_label))
        self.assertTrue(_is_ascii(scene.y_label))

    def test_fwhm_passthrough(self):
        scene32 = plot_logic.build_scene(self.spectrum.modes, fwhm=32.0)
        self.assertEqual(scene32.fwhm, 32.0)
        self.assertNotEqual(scene32.ys, self.scene.ys,
                            'fwhm=32 must differ from the default fwhm=8 '
                            'at the peak shoulders — fwhm is a live '
                            'parameter')

    def test_invalid_fwhm_raises(self):
        with self.assertRaises(ValueError):
            plot_logic.build_scene([], fwhm=0.0)


class TestSizePresets(unittest.TestCase):
    """Pure (label, (w, h)) data for the house addItem(label, data)
    combo pattern; 'compact (640x320)' is the pinned default (first
    entry) since round 5 (owner decision 2026-10-10, debug session 06
    height reduction, option D); 'medium (640x400)' -- the pre-round-5
    default -- must STAY a one-click choice together with large/wide
    (the 07-06 exact-preset + grow/shrink surface is unchanged)."""

    def test_shape(self):
        presets = plot_logic.size_presets()
        self.assertGreaterEqual(len(presets), 2)
        self.assertEqual(presets[0], ('compact (640x320)', (640, 320)))
        for label, dims in presets:
            self.assertIsInstance(label, str)
            self.assertIsInstance(dims, tuple)
            self.assertEqual(len(dims), 2)
            width, height = dims
            self.assertIsInstance(width, int)
            self.assertIsInstance(height, int)
            self.assertGreaterEqual(width, 640)
            self.assertGreaterEqual(height, 320)
            self.assertTrue(_is_ascii(label),
                            'non-ASCII preset label %r' % label)

    def test_pre_round_5_presets_retained(self):
        # Round-5 pin (option D): ONLY the default moved to compact;
        # every pre-round-5 preset stays a one-click choice.
        presets = plot_logic.size_presets()
        self.assertIn(('medium (640x400)', (640, 400)), presets,
                      'medium must remain one click back to the '
                      'pre-round-5 default look')
        self.assertIn(('large (800x500)', (800, 500)), presets)
        self.assertIn(('wide (960x500)', (960, 500)), presets)


class TestUnitModes(unittest.TestCase):
    """Owner amendment (07-06 checkpoint round 1, 2026-09-26): y-axis
    DISPLAY unit selectable in the panel - intensity (default,
    unchanged) / absorbance (arb.) / transmittance (arb.). The
    transforms live PURE here: absorbance = intensity normalized to
    peak = 1 (xtb IR intensities are proportional to absorbance via
    Beer-Lambert linearity - arbitrary units, honestly labeled
    '(arb.)'); transmittance = 10**(-A) of that normalized absorbance
    (peaks point down, T in (0, 1]). Unknown modes raise ValueError
    (loud, never a silent passthrough). All non-y Scene fields pass
    through UNCHANGED in every derived scene. quick-002 (owner
    directive 2026-10-10) renamed the default combo entry to 'epsilon
    (Multiwfn curve)' (label ONLY - the mode key stays 'intensity',
    the approved curve look and axis label unchanged) and added the
    'lines' discrete-sticks mode (own coverage: TestLinesMode below).
    """

    @classmethod
    def setUpClass(cls):
        cls.spectrum = spectra.parse_g98(G98_PATH)
        cls.scene = plot_logic.build_scene(cls.spectrum.modes)

    def test_unit_modes_table(self):
        self.assertTrue(hasattr(plot_logic, 'UNIT_MODES'))
        table = plot_logic.UNIT_MODES
        self.assertIsInstance(table, tuple)
        for label, mode in table:
            self.assertTrue(_is_ascii(label),
                            'non-ASCII unit label %r' % label)
            self.assertTrue(_is_ascii(mode))
        self.assertEqual([label for label, _mode in table],
                         ['epsilon (Multiwfn curve)',
                          'intensity (km/mol)',
                          'absorbance (arb.)',
                          'transmittance (arb.)'])
        self.assertEqual([mode for _label, mode in table],
                         ['intensity', 'lines', 'absorbance',
                          'transmittance'])
        # The approved look; quick-002 renamed the LABEL only (the
        # internal mode key stays 'intensity' - passthrough
        # semantics, the existing pins hold).
        self.assertEqual(table[0],
                         ('epsilon (Multiwfn curve)', 'intensity'))

    def test_intensity_passthrough(self):
        derived = plot_logic.scene_with_unit(self.scene, 'intensity')
        self.assertEqual(list(derived.ys), list(self.scene.ys))
        self.assertEqual(derived.y_label, self.scene.y_label)

    def test_absorbance_peak_one(self):
        derived = plot_logic.scene_with_unit(self.scene, 'absorbance')
        self.assertAlmostEqual(max(derived.ys), 1.0, delta=1e-9)
        # The normalization is a monotone scale - argmax is the same
        # grid point as in the intensity scene (shape preserved).
        argmax_base = max(range(len(self.scene.ys)),
                          key=lambda i: self.scene.ys[i])
        argmax_abs = max(range(len(derived.ys)),
                         key=lambda i: derived.ys[i])
        self.assertEqual(argmax_base, argmax_abs)
        self.assertEqual(derived.y_label, 'absorbance (arb.)')
        self.assertAlmostEqual(
            derived.y_max, max(1.0 * 1.1, plot_logic.Y_MAX_FLOOR),
            delta=1e-9)
        y_values = [value for value, _label in derived.y_ticks]
        self.assertTrue(y_values, 'y_ticks must be non-empty')
        for value in y_values:
            self.assertGreaterEqual(value, 0.0)
            self.assertLessEqual(value, derived.y_max)
        for prev, cur in zip(y_values, y_values[1:]):
            self.assertLess(prev, cur, 'y_ticks not strictly ascending')

    def test_transmittance_bounds_and_peak(self):
        derived = plot_logic.scene_with_unit(self.scene, 'transmittance')
        for y in derived.ys:
            self.assertGreater(y, 0.0)
            self.assertLessEqual(y, 1.0)
        # At the absorbance peak (A = 1) T = 10**(-1) = 0.1.
        self.assertAlmostEqual(min(derived.ys), 0.1, delta=1e-9)
        # Far from any peak (intensity ~ 0 -> A_rel ~ 0) T ~ 1.
        argmin_base = min(range(len(self.scene.ys)),
                          key=lambda i: self.scene.ys[i])
        self.assertGreater(derived.ys[argmin_base], 0.999)
        self.assertEqual(derived.y_label, 'transmittance (arb.)')

    def test_empty_scene_safe(self):
        # The pinned zero curve (empty modes): no division-by-zero;
        # a zero curve stays zeros in every unit (an empty spectrum
        # shows the hint path in the GUI anyway).
        empty = plot_logic.build_scene([])
        for mode in ('absorbance', 'transmittance'):
            derived = plot_logic.scene_with_unit(empty, mode)
            self.assertTrue(all(y == 0.0 for y in derived.ys),
                            'mode %r must zero-passthrough' % mode)

    def test_unknown_mode_raises(self):
        with self.assertRaises(ValueError):
            plot_logic.scene_with_unit(self.scene, 'wavenumber')

    def test_non_y_fields_unchanged(self):
        for mode in ('absorbance', 'transmittance'):
            derived = plot_logic.scene_with_unit(self.scene, mode)
            self.assertEqual(derived.xs, self.scene.xs)
            self.assertEqual(derived.x_min, self.scene.x_min)
            self.assertEqual(derived.x_max, self.scene.x_max)
            self.assertEqual(derived.x_ticks, self.scene.x_ticks)
            self.assertEqual(derived.x_label, self.scene.x_label)
            self.assertEqual(derived.n_modes, self.scene.n_modes)
            self.assertEqual(derived.n_imaginary,
                             self.scene.n_imaginary)
            self.assertEqual(derived.fwhm, self.scene.fwhm)
            # quick-002: the raw sticks ride along unchanged (data,
            # like n_modes); a curve unit never carries segments.
            self.assertEqual(derived.sticks, self.scene.sticks)
            self.assertIsNone(derived.segments)


class TestLinesMode(unittest.TestCase):
    """quick-002 (owner directive 2026-10-10): the DISCRETE STICKS unit
    mode ('intensity (km/mol)'), added next to the renamed default. One
    baseline-rooted vertical stick per mode at the actual table /
    spectrum_line.txt (frequency, IR intensity) values; NO broadening
    (fwhm is irrelevant - discrete by definition); empty modes -> NO
    sticks (never fabricated); negative-frequency sticks render at
    NEGATIVE x - the x window widens LEFT (07-01 freq_label governs
    TABLE text, not plot x); a lines scene never re-derives (lines do
    not feed the curve-based absorbance/transmittance).
    """

    @classmethod
    def setUpClass(cls):
        cls.spectrum = spectra.parse_g98(G98_PATH)
        cls.scene = plot_logic.build_scene(cls.spectrum.modes)
        cls.lines = plot_logic.scene_with_unit(cls.scene, 'lines')

    def test_sticks_echo_raw_mode_data(self):
        # build_scene echoes the RAW (freq, intensity) mode data -
        # the table values, not the broadened curve.
        self.assertEqual(
            self.scene.sticks,
            tuple((m.freq, m.intensity) for m in self.spectrum.modes))
        self.assertEqual(len(self.scene.sticks), 72)
        self.assertIsNone(self.scene.segments)
        self.assertEqual(plot_logic.build_scene([]).sticks, ())

    def test_segments_one_baseline_rooted_stick_per_mode(self):
        # One vertical stick per mode: ((freq, 0.0), (freq, inten))
        # IN sticks order; the lines scene carries NO curve data (xs/ys
        # emptied - nothing stale to draw, the painter reads segments
        # instead).
        self.assertEqual(len(self.lines.segments), 72)
        for segment, (freq, inten) in zip(self.lines.segments,
                                          self.scene.sticks):
            self.assertEqual(segment, ((freq, 0.0), (freq, inten)))
        self.assertEqual(self.lines.xs, ())
        self.assertEqual(self.lines.ys, ())

    def test_axis_labels(self):
        # The lines AXIS label states the REAL unit - the frequency
        # table header's literal; distinct from the combo label
        # 'intensity (km/mol)'.
        self.assertEqual(self.lines.y_label, 'IR intensity (km/mol)')
        self.assertEqual(self.lines.x_label, 'wavenumber (cm-1)')
        self.assertTrue(_is_ascii(self.lines.y_label))

    def test_y_max_headroom_over_peak_intensity(self):
        # The stick peak IS the raw max table intensity (257.1018,
        # PEAK_INTEN); the build_scene headroom policy applies
        # (10%, floored) so the tallest stick never clips.
        self.assertAlmostEqual(self.lines.y_max, PEAK_INTEN * 1.1,
                               delta=1e-9)
        for value, _label in self.lines.y_ticks:
            self.assertGreaterEqual(value, 0.0)
            self.assertLessEqual(value, self.lines.y_max)

    def test_negative_frequencies_widens_x_min_left(self):
        # Fixture modes 1-3 are imaginary (-31.9175 / -23.0766 /
        # -18.1086): the lines x window widens LEFT of the curve's
        # 0.0 so the imaginary sticks render at negative x; the RIGHT
        # bound stays the curve window (mode switching never jumps
        # the axis).
        self.assertAlmostEqual(self.lines.x_min, -31.9175, delta=1e-9)
        self.assertEqual(self.lines.x_max, self.scene.x_max)
        self.assertEqual(self.lines.x_max, 3600.0)
        x_values = [value for value, _label in self.lines.x_ticks]
        for prev, cur in zip(x_values, x_values[1:]):
            self.assertLess(prev, cur, 'x ticks not strictly ascending')

    def test_empty_modes_no_sticks(self):
        # Empty modes -> a sane axis with ZERO sticks - never
        # fabricated data points.
        derived = plot_logic.scene_with_unit(
            plot_logic.build_scene([]), 'lines')
        self.assertEqual(derived.segments, ())
        self.assertEqual(derived.y_max, plot_logic.Y_MAX_FLOOR)
        self.assertEqual(derived.x_min, 0.0)

    def test_fwhm_irrelevant(self):
        # Discrete by definition - the fwhm=32 curve differs from the
        # default fwhm=8 curve, but the sticks (and so the segments)
        # are broadening-independent.
        lines32 = plot_logic.scene_with_unit(
            plot_logic.build_scene(self.spectrum.modes, fwhm=32.0),
            'lines')
        self.assertEqual(lines32.segments, self.lines.segments)

    def test_counts_and_fwhm_passthrough(self):
        self.assertEqual(self.lines.n_modes, 72)
        self.assertEqual(self.lines.n_imaginary, 3)
        self.assertEqual(self.lines.fwhm, self.scene.fwhm)
        self.assertEqual(self.lines.sticks, self.scene.sticks)

    def test_lines_scene_never_rederives(self):
        # A lines scene feeds NO further derivation - not even back
        # into 'lines': derivation always starts from the BASE curve
        # scene (lines must never feed the curve-based units).
        for mode in ('lines', 'absorbance', 'transmittance'):
            with self.assertRaises(ValueError):
                plot_logic.scene_with_unit(self.lines, mode)


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
