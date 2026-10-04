"""Fixture-driven tests for the Multiwfn-parity IR broadening
(serpentrum/spectra.py broaden — GATE V amendment, 2026-10-04).

The pre-parity suite (plan 02-12) pinned a Gaussian of FWHM 16 with
each mode's Gaussian PEAKING at I_i. Owner directive (recorded
2026-10-04, mid GATE V walk-through): the plotted curve must match
Multiwfn's default export EXACTLY — Lorentzian mode, FWHM 8.00000
cm^-1, unit-area per-mode weighting, scale ratio for curve 100.00000:

    y(x) = CURVE_SCALE(100) * sum_i  I_i * (1/pi) * g / ((x - f_i)^2 + g^2)
    g = fwhm / 2.0

The mode intensity is carried as AREA by its Lorentzian: a single
mode's curve centers at CENTRAL = (100/pi)*(I/g), falls to EXACTLY
half that at x = f +- g (the FWHM points), and decays ~x^-2 in the
tails. CURVE_SCALE's 100.0 was fitted to the owner's Multiwfn 3.x
default export (srp_spectra/run_1, gitignored) on 2026-10-04 — max
relative error 4.9e-7 over 1000 sampled points; the closed-form
regression below pins the same formula synthetic-mode-for-mode.

Verified fixture anchors (probe-reverified 2026-10-04 against the
committed xtb spike fixtures — frequencies/intensities are UNCHANGED
from the 02-12 era; only the curve convention moved):

  - g98.out (26-atom phenol pi-dimer, 72 modes): max-intensity mode
    1150.6639 cm-1 @ 257.1018 km/mol (isolated — nearest sizable
    neighbor 37.65 @ 1109.44, 41 cm-1 away); second-strongest mode
    405.1591 @ 235.5447 (91.6% of the max intensity, well placed on
    the default grid); strongest low mode 364.42 @ 98.605 (neighbors:
    375.88 @ 0.538, 380.28 @ 0.694, 383.0 @ 19.749); negative real
    modes -31.9175 @ 2.4191 / -23.0766 @ 0.0072 / -18.1086 @ 0.2541.
  - New-convention measured anchors (default call: fwhm 8 -> g 4.0,
    grid [0.0, 3600.0], 800 points, step ~4.5056; CENTRAL(I) =
    (100/pi)*(I/g)):
      * default x_max = max(3600.0, 3521.1843 + 5*g = 3541.1843) =
        3600.0 — the 3600 floor still wins.
      * global argmax 405.506884 @ 1873.257563 = 0.9994 * CENTRAL of
        the 235.5447 mode (grid-sampled at dx = +0.348). Under
        unit-area weighting the curve peaks at the strong mode the
        grid samples BEST, so the curve NO LONGER peaks at the
        max-intensity mode: 1150.6639 falls at dx = -1.7277 (value
        1732.015288 = 0.8467 * its CENTRAL). Both anchors are pinned.
      * tail at x = 0: 0.809039 = 4.3e-4 of the peak — Lorentzian
        tails are heavy (profile g^2/(dx^2+g^2) at the negative
        modes), so the old Gaussian-era 1e-4 bound moved to 1e-3.
  - Synthetic CO2 (02-09's 8-row fixture): 5 trivial + 3 real;
    real_modes carries the degenerate 600.18 pair (2 x 68.70 = 137.4)
    and the intensity-exactly-0.00 symmetric stretch at 1424.95;
    measured argmax 599.249061 @ 1037.2134 (dx = -0.93 from 600.18);
    the silent mode's curve share is 2.5e-5 of the peak.

g and every expectation are ALWAYS computed at runtime from the fwhm
constants (never hardcoded decimals); fwhm 8 -> g 4.0, fwhm 32 ->
g 16.0.

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
    CURVE_SCALE,
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

# Runtime Lorentzian half-width (HWHM) from fwhm (never hardcoded — the
# g = fwhm/2 identity is the asserted arithmetic). fwhm 8 -> 4.0,
# fwhm 32 -> 16.0.
G_8 = 8.0 / 2.0
G_32 = 32.0 / 2.0


def _central(intensity, g=G_8):
    """Single-mode Lorentzian center value under the parity convention:
    CURVE_SCALE * (1/pi) * I/g — the (100/pi)*(I/g) identity."""
    return CURVE_SCALE * intensity / (math.pi * g)


# Verified fixture anchors (probe-verified 2026-10-04).
PEAK_FREQ = 1150.6639
PEAK_INTEN = 257.1018
SECOND_FREQ = 405.1591
SECOND_INTEN = 235.5447
LOW_MODE_FREQ = 364.4160
LOW_MODE_INTEN = 98.6050

# Synthetic stand-in for the owner's Multiwfn reference scenario
# (srp_spectra/run_1, GITIGNORED — never read here): the run's dominant
# stick (3086.20 @ 134.181 km/mol, the max of its 138 modes) plus two
# moderate neighbors. The 3-mode list is NOT the full run; the
# regression asserts the FORMULA — every term, the x100 scale, g = fwhm/2
# — which the owner verified numerically against the whole export
# (max relative error 4.9e-7, 2026-10-04).
PARITY_MODES = (Mode(1, 3086.20, 134.181, ()),
                Mode(2, 3069.00, 8.0, ()),
                Mode(3, 3105.50, 5.5, ()))


def _expected_parity(x, fwhm=8.0):
    """INDEPENDENT closed form of the Multiwfn curve at x (regrouped —
    deliberately NOT broaden's expression tree, so a convention drift
    in either shape fails loudly)."""
    g = fwhm / 2.0
    total = 0.0
    for m in PARITY_MODES:
        total += (CURVE_SCALE * m.intensity) \
            * (g / (math.pi * ((x - m.freq) ** 2 + g ** 2)))
    return total


class TestBroadenGridShape(unittest.TestCase):
    """Test 1: grid shape — 800 points spanning [0.0, 3600.0] for the
    dimer (the 3600 floor still wins under the 5*g tail allowance)."""

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
        # Default x_max = max(3600.0, max_freq + 5*g) = max(3600.0,
        # 3521.1843 + 5*4.0 = 3541.1843) = 3600.0 — the 3600 floor wins.
        max_freq = max(m.freq for m in self.modes)
        expected_upper = max(3600.0, max_freq + 5.0 * G_8)
        self.assertEqual(expected_upper, 3600.0)
        self.assertEqual(self.xs[-1], 3600.0)

    def test_grid_monotonically_increasing(self):
        for i in range(len(self.xs) - 1):
            self.assertLess(self.xs[i], self.xs[i + 1],
                            'grid not monotonic at index %d' % i)


class TestBroadenNonNegativity(unittest.TestCase):
    """Test 2: the broadened curve never dips below zero (all
    intensities are >= 0 in the fixtures; the Lorentzian sum stays
    non-negative)."""

    @classmethod
    def setUpClass(cls):
        cls.ys = broaden(parse_g98(G98_PATH).modes)[1]

    def test_min_ys_non_negative(self):
        self.assertGreaterEqual(min(self.ys), 0.0)


class TestBroadenPeakLocation(unittest.TestCase):
    """Test 3 (re-derived 2026-10-04): under unit-area weighting the
    curve peaks at the strong mode the grid samples BEST, which for the
    dimer is the SECOND-strongest mode (405.1591 @ 235.5447, sampled at
    dx = +0.348), NOT at the max-intensity mode (1150.6639, whose
    nearest grid point sits dx = -1.7277 away). The FWHM-16 Gaussian
    suite pinned the old argmax-at-max-intensity-mode claim; that
    convention is gone."""

    @classmethod
    def setUpClass(cls):
        cls.xs, cls.ys = broaden(parse_g98(G98_PATH).modes)

    def test_argmax_within_fwhm_of_405_16(self):
        k = max(range(len(self.ys)), key=lambda i: self.ys[i])
        self.assertLessEqual(abs(self.xs[k] - SECOND_FREQ), 8.0)

    def test_argmax_value_tracks_central_of_235_54_mode(self):
        # Measured 1873.257563 = 0.9994 * CENTRAL(235.5447) = 1874.3476:
        # the grid samples the mode at dx = +0.348 (factor ~0.9925), so
        # the value stays inside [0.9, 1.1] * CENTRAL (the small
        # neighbor lift from 383.0 @ 19.749 is ~+13, included).
        k = max(range(len(self.ys)), key=lambda i: self.ys[i])
        central = _central(SECOND_INTEN)
        self.assertGreaterEqual(self.ys[k], 0.9 * central)
        self.assertLessEqual(self.ys[k], 1.1 * central)


class TestBroadenPeakAmplitude(unittest.TestCase):
    """Test 4 (re-derived 2026-10-04): at the grid point nearest the
    max-intensity mode (1150.6639 @ 257.1018), the curve carries the
    unit-area Lorentzian weight: measured 1732.015288 = 0.8467 *
    CENTRAL(257.1018). The grid (step ~4.5056 ~ g) can sample a peak at
    most half a step off-center, where the profile retains
    g^2/(dx^2+g^2) >= 16/(2.2528^2+16) = 0.759; neighbor tails only add
    (the 37.65 @ 1109.44 mode, 41 cm-1 away, contributes ~+2.8)."""

    @classmethod
    def setUpClass(cls):
        cls.xs, cls.ys = broaden(parse_g98(G98_PATH).modes)

    def test_peak_amplitude_sanity(self):
        nearest = min(range(len(self.xs)),
                       key=lambda i: abs(self.xs[i] - PEAK_FREQ))
        central = _central(PEAK_INTEN)
        self.assertGreaterEqual(self.ys[nearest], 0.70 * central)
        self.assertLessEqual(self.ys[nearest], central)
        # Far off its center the curve does NOT claim the mode's full
        # central value (the raw-km/mol peak-height convention would
        # answer ~257 here; parity answers 0.85*2045.95 = 1732.0).
        self.assertGreater(central, self.ys[nearest])


class TestBroadenStrongestLowMode(unittest.TestCase):
    """Test 5: within [340, 390], the max of ys lies within +-fwhm of
    364.42 (the 98.605 mode dominates: 383.0 @ 19.749 is 18.6 away and
    contributes only ~0.9% of the 364-mode's central there)."""

    @classmethod
    def setUpClass(cls):
        cls.xs, cls.ys = broaden(parse_g98(G98_PATH).modes)

    def test_low_mode_peak_within_fwhm(self):
        window = [(i, self.xs[i], self.ys[i]) for i in range(len(self.xs))
                  if 340.0 <= self.xs[i] <= 390.0]
        self.assertGreater(len(window), 0, 'no grid points in [340, 390]')
        best_i, best_x, _best_y = max(window, key=lambda t: t[2])
        self.assertLessEqual(abs(best_x - LOW_MODE_FREQ), 8.0)


class TestBroadenNegativeTail(unittest.TestCase):
    """Test 6 (bound re-derived 2026-10-04): the tail at x=0 stays
    below 1e-3 of the peak (measured 4.3e-4) — negatives are summed but
    the grid starting at 0.0 keeps their influence small. The heavy
    Lorentzian tail (profile g^2/(dx^2+g^2), not exp-decay) makes this
    ~15x the old Gaussian-era 2.9e-5; the bound moved 1e-4 -> 1e-3."""

    @classmethod
    def setUpClass(cls):
        cls.xs, cls.ys = broaden(parse_g98(G98_PATH).modes)

    def test_tail_ratio_below_1e_3(self):
        peak = max(self.ys)
        self.assertGreater(peak, 0.0)
        self.assertLess(self.ys[0], 1e-3 * peak)


class TestBroadenZeroIntensityExactZero(unittest.TestCase):
    """Test 7: a zero-intensity mode contributes EXACTLY 0 by
    arithmetic — broaden([m1]) == broaden([m1, m0]) (exact list
    equality), and ys at x=700 from [m1, m0] equals the mirrored
    Lorentzian term (KMOL intensities carried as area)."""

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
        # Compute expected using the EXACT same arithmetic path as
        # broaden (CURVE_SCALE * (I * (1/pi)) * g / (dx*dx + g*g) —
        # precomputing 1/pi once; NOT the regrouped algebra, whose
        # different rounding order would mask a 1-ULP drift).
        inv_pi = 1.0 / math.pi
        dx = 700.0 - 500.0
        expected = CURVE_SCALE * (10.0 * inv_pi) * G_8 / (dx * dx + G_8 * G_8)
        self.assertEqual(ys[700], expected)


class TestBroadenCO2Synthetic(unittest.TestCase):
    """Test 8: the synthetic CO2 fixture — the degenerate 600.18 pair
    dominates (2 x 68.70 = 137.4; measured argmax 599.249061 @
    1037.2134), the 1424.95 symmetric stretch is silent (intensity
    exactly 0.00), and the 2593.38 mode is honestly absent."""

    @classmethod
    def setUpClass(cls):
        cls.spec = parse_vibspectrum(CO2_VIBSPECTRUM_PATH)
        cls.real = real_modes(cls.spec)
        cls.xs, cls.ys = broaden(cls.real)

    def test_argmax_within_fwhm_of_600_18(self):
        k = max(range(len(self.ys)), key=lambda i: self.ys[i])
        self.assertLessEqual(abs(self.xs[k] - 600.18), 8.0)

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
    """Test 9: broaden(modes, fwhm=32, x_min=0, x_max=200, n_points=201)
    -> 201 points, [0, 200], g32 = 16.0; a single Mode(1, 50, 1, ())
    gives ys[0] ~ (100/1)*(1/pi)*16/(50^2+16^2) = 0.1848 at x=0 — the
    wider fwhm lifts the tail (grows linearly in g when far from the
    center)."""

    def test_grid_shape_201_points(self):
        m = Mode(1, 50.0, 1.0, ())
        xs, ys = broaden([m], fwhm=32.0, x_min=0.0, x_max=200.0,
                         n_points=201)
        self.assertEqual(len(xs), 201)
        self.assertEqual(len(ys), 201)
        self.assertEqual(xs[0], 0.0)
        self.assertEqual(xs[-1], 200.0)

    def test_g32_wider_tail_lifts_ys0(self):
        # g32 = 32/2 = 16.0 — wider than g8 = 4.0.
        self.assertAlmostEqual(G_32, 16.0, places=9)
        m = Mode(1, 50.0, 1.0, ())
        xs, ys = broaden([m], fwhm=32.0, x_min=0.0, x_max=200.0,
                         n_points=201)
        inv_pi = 1.0 / math.pi
        expected_ys0 = CURVE_SCALE * (1.0 * inv_pi) * G_32 \
            / (50.0 * 50.0 + G_32 * G_32)
        self.assertEqual(ys[0], expected_ys0)
        # Wider fwhm -> the same far tail point sits HIGHER.
        _xs8, ys8 = broaden([m], fwhm=8.0, x_min=0.0, x_max=200.0,
                            n_points=201)
        self.assertGreater(ys[0], ys8[0])


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


class TestBroadenSingleModeIdentities(unittest.TestCase):
    """Test 11 (new-convention identities, GATE V 2026-10-04): for a
    single mode the curve is the x100 unit-area Lorentzian EXACTLY —
    center value CENTRAL, EXACT half-height at f +- g (a power-of-two
    halving in the float arithmetic), fwhm kwarg moving the half-height
    points, exact two-mode superposition, the negative-frequency tail
    arithmetic, and the far x^-2 decay."""

    # Exact integer grid: x_i = 600*i/600 = i, so f = 500, f +- g = 496
    # and 504 (default fwhm) or 484/516 (fwhm 32) are on-grid exactly.
    MODE = Mode(1, 500.0, 10.0, ())

    def _curve(self, fwhm=None):
        if fwhm is None:
            return broaden([self.MODE], x_min=0.0, x_max=600.0,
                           n_points=601)
        return broaden([self.MODE], fwhm=fwhm, x_min=0.0, x_max=600.0,
                        n_points=601)

    def test_center_value_is_central(self):
        _xs, ys = self._curve()
        self.assertAlmostEqual(
            ys[500], (CURVE_SCALE / math.pi) * (10.0 / G_8), places=9)
        # The same value via broaden's own arithmetic path, EXACTLY.
        inv_pi = 1.0 / math.pi
        mirror = CURVE_SCALE * (10.0 * inv_pi) * G_8 / (G_8 * G_8)
        self.assertEqual(ys[500], mirror)

    def test_half_height_exactly_at_f_plus_minus_g(self):
        # Default fwhm (8.0): half-height at 500 +- 4 — which ALSO pins
        # the default: the halving is exact float arithmetic (the
        # denominator doubles, a power-of-two scale).
        _xs, ys = self._curve()
        self.assertEqual(2.0 * ys[504], ys[500])
        self.assertEqual(2.0 * ys[496], ys[500])

    def test_default_fwhm_is_8_not_16(self):
        # The pre-parity default (16.0, g 8.0) would put the half-height
        # at 500 +- 8 instead — assert it does NOT, so a default
        # regression fails here.
        _xs, ys = self._curve()
        self.assertNotEqual(2.0 * ys[508], ys[500])
        self.assertNotEqual(2.0 * ys[492], ys[500])

    def test_fwhm_kwarg_overrides_half_height(self):
        # fwhm=32 -> g=16: half-height moves to 500 +- 16 (and no longer
        # sits at 500 +- 4).
        _xs, ys = self._curve(fwhm=32.0)
        self.assertEqual(2.0 * ys[516], ys[500])
        self.assertEqual(2.0 * ys[484], ys[500])
        self.assertNotEqual(2.0 * ys[504], ys[500])

    def test_two_mode_superposition_exact(self):
        # The curve is a plain sum: [m1, m2] equals the elementwise sum
        # of the single-mode curves, EXACTLY (same accumulation order).
        m2 = Mode(2, 900.0, 3.5, ())
        _xs1, ys1 = broaden([self.MODE])
        _xs2, ys2 = broaden([m2])
        _xs12, ys12 = broaden([self.MODE, m2])
        self.assertEqual(ys12, [ys1[i] + ys2[i] for i in range(len(ys12))])

    def test_negative_mode_tail_arithmetic(self):
        # Negatives are NOT special-cased: a mode at -50 contributes its
        # same Lorentzian term at x=0 — mirror-EXACT arithmetic.
        m = Mode(1, -50.0, 5.0, ())
        _xs, ys = broaden([m], x_min=0.0, x_max=200.0, n_points=201)
        inv_pi = 1.0 / math.pi
        expected = CURVE_SCALE * (5.0 * inv_pi) * G_8 \
            / (50.0 * 50.0 + G_8 * G_8)
        self.assertEqual(ys[0], expected)
        # The profile falls off away from the (off-grid) center.
        self.assertGreater(ys[0], ys[100])

    def test_far_tail_x_minus_two_decay(self):
        # Lorentzian far tail ~ x^-2: for a mode at 1000, y(3000)/
        # y(2000) == (1000^2+g^2)/(2000^2+g^2) = 0.2500030 (integer
        # grid [0, 3000], 3001 points).
        m = Mode(1, 1000.0, 1.0, ())
        _xs, ys = broaden([m], x_min=0.0, x_max=3000.0, n_points=3001)
        expected_ratio = (1000.0 ** 2 + G_8 * G_8) \
            / (2000.0 ** 2 + G_8 * G_8)
        self.assertAlmostEqual(ys[3000] / ys[2000], expected_ratio,
                               places=12)
        self.assertAlmostEqual(expected_ratio, 0.25, places=4)


class TestMultiwfnParityRegression(unittest.TestCase):
    """Test 12 (GATE V acceptance math, 2026-10-04): broaden must
    reproduce Multiwfn's default IR curve formula EXACTLY —
    SCALE(100) * sum_i I_i * (1/pi) * g / ((x - f_i)^2 + g^2), g =
    fwhm/2 — on the owner's reference scenario shape (dominant
    3086.20 stick + moderate neighbors; see PARITY_MODES). The expected
    values are computed from an INDEPENDENTLY grouped closed form, so
    any convention drift — peak-height weighting instead of unit-area, a
    misplaced pi, a dropped x100 scale, a Gaussian reversion, or a wrong
    g definition — fails loudly."""

    def test_matches_closed_form_on_exact_grid(self):
        # 1 cm-1 integer grid covering the peak flank and the far tail;
        # the DEFAULT fwhm (8.0 -> g 4.0) is part of what is pinned (a
        # default regression moves every expected value).
        xs, ys = broaden(list(PARITY_MODES), x_min=0.0, x_max=6000.0,
                         n_points=6001)
        for x in (3086, 3087, 3088, 3200, 4000, 6000):
            expected = _expected_parity(float(x))
            self.assertAlmostEqual(
                ys[x], expected,
                delta=1e-9 * max(1.0, abs(expected)),
                msg='parity drift at x=%d' % x)
        # The peak sits on the dominant stick's flank: within fwhm of
        # 3086.20 (measured at 3086 or 3087 among the integers).
        k = max(range(len(ys)), key=lambda i: ys[i])
        self.assertLessEqual(abs(xs[k] - 3086.20), 8.0)


if __name__ == '__main__':
    unittest.main()
