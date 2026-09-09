"""Fixture-driven tests for Gaussian broadening (serpentrum/spectra.py broaden,
plan 02-12 — the SPECTRA-03 pure half).

Every assertion below is pinned to VERIFIED values probed against the
committed xtb spike fixtures on 2026-09-06/07 (02-RESEARCH-pure-core.md
S2 + the 02-12 plan's load-bearing facts):

  - g98.out (26-atom phenol pi-dimer, 72 modes): global max-intensity mode
    1150.6639 cm-1 @ 257.1018 km/mol (isolated — nearest sizable neighbor
    37.65 @ 1109.44, 41 cm-1 away). Strongest low mode: 364.42 @ 98.605
    (neighbors: 375.88 @ 0.538, 380.28 @ 0.694, 383.0 @ 19.749).
  - Broadening arithmetic (fwhm 16): sigma = 16/(2*sqrt(2*ln2)) = 6.794574
    (2*sqrt(2*ln2) = 2.354820). Sum of all mode tails at x=0: 7.35e-3 ->
    ratio to the ~257 peak = 2.9e-5 (< 1e-4). Default x_max =
    max(3600.0, 3521.1843 + 5*6.794574 = 3555.16) = 3600.0.
  - Synthetic CO2 (02-09's 8-row fixture): 5 trivial + 3 real; real_modes
    carries the degenerate 600.18 pair (2 x 68.70 = 137.4) and the
    intensity-exactly-0.00 symmetric stretch at 1424.95.

sigma and grids are ALWAYS computed at runtime from the fwhm constants
(never hardcoded decimals); fwhm 16 -> 6.794574, fwhm 32 -> 13.58915.

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

from serpentrum.spectra import (  # noqa: E402
    Mode,
    broaden,
    parse_g98,
    parse_vibspectrum,
    real_modes,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURES = os.path.join(ROOT, 'tests', 'fixtures', 'xtb')
G98_PATH = os.path.join(FIXTURES, 'g98.out')
CO2_VIBSPECTRUM_PATH = os.path.join(FIXTURES, 'synthetic', 'co2_vibspectrum')

# Runtime sigma from fwhm (never hardcoded — the 2*sqrt(2*ln2) identity is
# the asserted arithmetic). fwhm 16 -> 6.794574, fwhm 32 -> 13.58915.
SIGMA_16 = 16.0 / (2.0 * math.sqrt(2.0 * math.log(2.0)))
SIGMA_32 = 32.0 / (2.0 * math.sqrt(2.0 * math.log(2.0)))

# Verified fixture anchors (02-12 plan load-bearing facts).
PEAK_FREQ = 1150.6639
PEAK_INTEN = 257.1018
LOW_MODE_FREQ = 364.4160
LOW_MODE_INTEN = 98.6050


class TestBroadenGridShape(unittest.TestCase):
    """Test 1: grid shape — 800 points spanning [0.0, 3600.0] for the dimer."""

    @classmethod
    def setUpClass(cls):
        cls.modes = parse_g98(G98_PATH).modes
        cls.xs, cls.ys = broaden(cls.modes)

    def test_grid_length_800(self):
        self.assertEqual(len(self.xs), 800)
        self.assertEqual(len(self.ys), 800)
        self.assertEqual(len(self.xs), len(self.ys))

    def test_grid_starts_at_zero(self):
        self.assertEqual(self.xs[0], 0.0)

    def test_grid_ends_at_3600_default_floor_wins(self):
        # Default x_max = max(3600.0, max_freq + 5*sigma) = max(3600.0,
        # 3521.1843 + 5*6.794574 = 3555.16) = 3600.0 — the 3600 floor wins.
        max_freq = max(m.freq for m in self.modes)
        expected_upper = max(3600.0, max_freq + 5.0 * SIGMA_16)
        self.assertEqual(expected_upper, 3600.0)
        self.assertEqual(self.xs[-1], 3600.0)

    def test_grid_monotonically_increasing(self):
        for i in range(len(self.xs) - 1):
            self.assertLess(self.xs[i], self.xs[i + 1],
                            'grid not monotonic at index %d' % i)


class TestBroadenNonNegativity(unittest.TestCase):
    """Test 2: the broadened curve never dips below zero (all intensities
    are >= 0 in the fixtures; the Gaussian sum stays non-negative)."""

    @classmethod
    def setUpClass(cls):
        cls.ys = broaden(parse_g98(G98_PATH).modes)[1]

    def test_min_ys_non_negative(self):
        self.assertGreaterEqual(min(self.ys), 0.0)


class TestBroadenPeakLocation(unittest.TestCase):
    """Test 3: the dimer's broadened curve peaks within +-fwhm of the
    verified max-intensity mode 1150.6639 @ 257.1018."""

    @classmethod
    def setUpClass(cls):
        cls.xs, cls.ys = broaden(parse_g98(G98_PATH).modes)

    def test_argmax_within_fwhm_of_1150(self):
        k = max(range(len(self.ys)), key=lambda i: self.ys[i])
        self.assertLessEqual(abs(self.xs[k] - PEAK_FREQ), 16.0)


class TestBroadenPeakAmplitude(unittest.TestCase):
    """Test 4: at the grid point nearest 1150.6639, the amplitude retains
    >= 0.9 of the peak intensity (Gaussian at <= half a grid step from
    center retains >= 0.945; neighbors add ~0.2)."""

    @classmethod
    def setUpClass(cls):
        cls.xs, cls.ys = broaden(parse_g98(G98_PATH).modes)

    def test_peak_amplitude_sanity(self):
        # Grid step = 3600/799 ~ 4.506; nearest grid point to 1150.6639
        # is within half a step (~2.25 cm-1) of the center.
        nearest = min(range(len(self.xs)),
                      key=lambda i: abs(self.xs[i] - PEAK_FREQ))
        self.assertGreaterEqual(self.ys[nearest], 0.9 * PEAK_INTEN)


class TestBroadenStrongestLowMode(unittest.TestCase):
    """Test 5: within [340, 390], the max of ys lies within +-fwhm of
    364.42 (the 98.605 mode dominates: 383.0 @ 19.749 is 18.6 away and
    contributes < 0.5)."""

    @classmethod
    def setUpClass(cls):
        cls.xs, cls.ys = broaden(parse_g98(G98_PATH).modes)

    def test_low_mode_peak_within_fwhm(self):
        window = [(i, self.xs[i], self.ys[i]) for i in range(len(self.xs))
                  if 340.0 <= self.xs[i] <= 390.0]
        self.assertGreater(len(window), 0, 'no grid points in [340, 390]')
        best_i, best_x, _best_y = max(window, key=lambda t: t[2])
        self.assertLessEqual(abs(best_x - LOW_MODE_FREQ), 16.0)


class TestBroadenNegativeTail(unittest.TestCase):
    """Test 6: the negative-frequency tail at x=0 stays below 1e-4 of the
    peak (verified 2.9e-5) — negatives are summed but the grid starting at
    0.0 keeps their influence negligible."""

    @classmethod
    def setUpClass(cls):
        cls.xs, cls.ys = broaden(parse_g98(G98_PATH).modes)

    def test_tail_ratio_below_1e_4(self):
        peak = max(self.ys)
        self.assertGreater(peak, 0.0)
        self.assertLess(self.ys[0], 1e-4 * peak)


class TestBroadenZeroIntensityExactZero(unittest.TestCase):
    """Test 7: a zero-intensity mode contributes EXACTLY 0 by arithmetic —
    broaden([m1]) == broaden([m1, m0]) (exact list equality), and ys at
    x=700 from [m1, m0] equals 10*exp(-0.5*(200/sigma)^2)."""

    def test_zero_intensity_mode_exact_list_equality(self):
        m1 = Mode(1, 500.0, 10.0, ())
        m0 = Mode(2, 700.0, 0.0, ())
        xs1, ys1 = broaden([m1])
        xs01, ys01 = broaden([m1, m0])
        self.assertEqual(xs1, xs01)
        self.assertEqual(ys1, ys01)

    def test_zero_intensity_mode_arithmetic_at_x_700(self):
        m1 = Mode(1, 500.0, 10.0, ())
        m0 = Mode(2, 700.0, 0.0, ())
        # Grid that includes x=700 exactly: x_min=0, x_max=700, 701 points.
        xs, ys = broaden([m1, m0], x_min=0.0, x_max=700.0, n_points=701)
        self.assertEqual(xs[700], 700.0)
        # Compute expected using the EXACT same arithmetic path as broaden:
        # dx*dx*inv_sigma_sq (not (dx/sigma)**2 — the two differ by a
        # 1-ULP rounding that exp amplifies for large exponents).
        sigma = SIGMA_16
        inv_sigma_sq = 1.0 / (sigma * sigma)
        dx = 700.0 - 500.0
        expected = 10.0 * math.exp(-0.5 * dx * dx * inv_sigma_sq)
        self.assertEqual(ys[700], expected)


class TestBroadenCO2Synthetic(unittest.TestCase):
    """Test 8: the synthetic CO2 fixture — the degenerate 600.18 pair
    dominates (2 x 68.70 = 137.4), the 1424.95 symmetric stretch is silent
    (intensity exactly 0.00), and the 2593.38 mode is honestly absent."""

    @classmethod
    def setUpClass(cls):
        cls.spec = parse_vibspectrum(CO2_VIBSPECTRUM_PATH)
        cls.real = real_modes(cls.spec)
        cls.xs, cls.ys = broaden(cls.real)

    def test_argmax_within_fwhm_of_600_18(self):
        k = max(range(len(self.ys)), key=lambda i: self.ys[i])
        self.assertLessEqual(abs(self.xs[k] - 600.18), 16.0)

    def test_silent_1424_below_threshold_of_peak(self):
        nearest = min(range(len(self.xs)),
                      key=lambda i: abs(self.xs[i] - 1424.95))
        peak = max(self.ys)
        self.assertGreater(peak, 0.0)
        self.assertLess(self.ys[nearest], 1e-3 * peak)

    def test_zero_intensity_mode_exact_list_equality(self):
        # The 1424.95 mode (intensity exactly 0.00) contributes exactly 0:
        # broadening the full real_modes list == broadening just the pair.
        pair_only = [Mode(6, 600.18, 68.70, ()), Mode(7, 600.18, 68.70, ())]
        xs_full, ys_full = broaden(self.real)
        xs_pair, ys_pair = broaden(pair_only)
        self.assertEqual(xs_full, xs_pair)
        self.assertEqual(ys_full, ys_pair)


class TestBroadenParameterization(unittest.TestCase):
    """Test 9: broaden(modes, fwhm=32, x_min=0, x_max=200, n_points=201) ->
    201 points, [0, 200], sigma32 = 13.58915; a single Mode(1, 50, 1, ())
    gives ys[0] ~ exp(-0.5*(50/sigma32)^2) ~ 1.1e-3 > 0 (wider fwhm lifts
    the tail)."""

    def test_grid_shape_201_points(self):
        m = Mode(1, 50.0, 1.0, ())
        xs, ys = broaden([m], fwhm=32.0, x_min=0.0, x_max=200.0,
                         n_points=201)
        self.assertEqual(len(xs), 201)
        self.assertEqual(len(ys), 201)
        self.assertEqual(xs[0], 0.0)
        self.assertEqual(xs[-1], 200.0)

    def test_sigma32_wider_tail_lifts_ys0(self):
        # sigma32 = 32/(2*sqrt(2*ln2)) ~ 13.58915 — wider than sigma16.
        self.assertAlmostEqual(SIGMA_32, 13.58915, places=4)
        m = Mode(1, 50.0, 1.0, ())
        xs, ys = broaden([m], fwhm=32.0, x_min=0.0, x_max=200.0,
                         n_points=201)
        expected_ys0 = math.exp(-0.5 * (50.0 / SIGMA_32) ** 2)
        self.assertAlmostEqual(ys[0], expected_ys0, places=6)
        self.assertGreater(ys[0], 0.0)


class TestBroadenEmptyModesZeroCurve(unittest.TestCase):
    """Test 10: broaden([]) -> the PINNED zero curve — the default grid
    (800 points, [0.0, 3600.0]) with every ys[i] == 0.0 EXACTLY."""

    def test_empty_modes_zero_curve(self):
        xs, ys = broaden([])
        self.assertEqual(len(xs), 800)
        self.assertEqual(len(ys), 800)
        self.assertEqual(xs[0], 0.0)
        self.assertEqual(xs[-1], 3600.0)
        self.assertTrue(all(v == 0.0 for v in ys))
        self.assertEqual(len(set(ys)), 1)


class TestBroadenValueErrorGuards(unittest.TestCase):
    """broaden() raises ValueError on fwhm <= 0 or n_points < 2."""

    def test_fwhm_zero_raises_value_error(self):
        with self.assertRaises(ValueError):
            broaden([], fwhm=0.0)

    def test_fwhm_negative_raises_value_error(self):
        with self.assertRaises(ValueError):
            broaden([], fwhm=-1.0)

    def test_n_points_one_raises_value_error(self):
        with self.assertRaises(ValueError):
            broaden([], n_points=1)


if __name__ == '__main__':
    unittest.main()
