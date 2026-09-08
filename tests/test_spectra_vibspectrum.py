"""Fixture-driven tests for the vibspectrum fallback parser + trivial-mode
filter (serpentrum/spectra.py, plan 02-09).

Every assertion below is pinned to VERIFIED values probed against the
committed xtb spike fixtures on 2026-09-06/07 (02-RESEARCH-pure-core.md
S1.2 + the 02-09 plan's load-bearing facts): the dimer vibspectrum has
78 modes = 6 trivial (|freq| < 10) + 72 real, trivial rows are 4-token
[mode freq intensity '-'], real rows are 5-token [mode symmetry freq
intensity selection], real mode 7 = -31.92 @ 2.41910 (NEGATIVE but NOT
trivial), last mode 78 = 3521.18 @ 34.95709, min real intensity 0.00026.

The synthetic CO2 fixture (tests/fixtures/xtb/synthetic/co2_vibspectrum)
is an 8-row linear-molecule case transcribed from the committed co2.log:
5 trivial modes (3N-5 = 4 vibrational for linear N=3 -> 5 trivial), a
doubly-degenerate 600.18 bend pair, and the intensity-exactly-0.00
symmetric stretch at 1424.95. The 2593.38 asymmetric stretch is honestly
OMITTED (its log intensity token is the overflow '******').

Discovery command (verified on 3.6.9 -- NOTE: `-t .` FAILS on python3.6
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

from serpentrum.spectra import (  # noqa: E402
    Mode,
    Spectrum,
    SpectraParseError,
    parse_g98,
    parse_vibspectrum,
    parse_vibspectrum_text,
    real_modes,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURES = os.path.join(ROOT, 'tests', 'fixtures', 'xtb')
VIBSPECTRUM_PATH = os.path.join(FIXTURES, 'vibspectrum')
G98_PATH = os.path.join(FIXTURES, 'g98.out')
SYNTHETIC_DIR = os.path.join(FIXTURES, 'synthetic')
CO2_VIBSPECTRUM_PATH = os.path.join(SYNTHETIC_DIR, 'co2_vibspectrum')


def read_text(path):
    """Read a fixture file as utf-8 text (header carries U+207B U+00B9)."""
    with open(path, encoding='utf-8') as fh:
        return fh.read()


class TestVibspectrumHappyPath(unittest.TestCase):
    """Grammar case 1: parse_vibspectrum on the committed dimer fixture.

    The committed vibspectrum has 78 modes in file order: 6 trivial
    (modes 1-6, |freq| < 10) + 72 real (modes 7-78). Real mode 7 = -31.92
    @ 2.41910 -- negative but NOT trivial. Every Mode.vectors is the empty
    tuple (vibspectrum carries no displacement vectors); atoms == [].
    """

    @classmethod
    def setUpClass(cls):
        cls.spectrum = parse_vibspectrum(VIBSPECTRUM_PATH)

    def test_returns_spectrum_with_78_modes(self):
        spectrum = self.spectrum
        self.assertIsInstance(spectrum, Spectrum)
        self.assertEqual(spectrum.n_atoms, 0)
        self.assertEqual(spectrum.atoms, [])
        self.assertEqual(len(spectrum.modes), 78)

    def test_every_mode_has_empty_vectors(self):
        for mode in self.spectrum.modes:
            self.assertEqual(mode.vectors, (),
                             'mode %d vectors not empty' % mode.index)

    def test_trivial_modes_1_to_6(self):
        trivial = self.spectrum.modes[:6]
        expected_freqs = [-0.00, -0.00, -0.00, -0.00, 0.00, 0.00]
        for i, mode in enumerate(trivial):
            self.assertEqual(mode.index, i + 1,
                             'trivial mode %d index' % (i + 1))
            self.assertAlmostEqual(mode.freq, expected_freqs[i], places=2)
            self.assertAlmostEqual(mode.intensity, 0.0, places=5)

    def test_real_mode_7_is_negative_real(self):
        # Mode 7 = -31.92 @ 2.41910: NEGATIVE freq but NOT trivial.
        # This is the load-bearing assertion that sign never filters.
        mode = self.spectrum.modes[6]
        self.assertEqual(mode.index, 7)
        self.assertLess(mode.freq, 0.0)
        self.assertAlmostEqual(mode.freq, -31.92, places=2)
        self.assertAlmostEqual(mode.intensity, 2.41910, places=5)

    def test_real_modes_8_and_9_are_negative_real(self):
        # Modes 8-9: -23.08 @ 0.00717, -18.11 @ 0.25411 -- all negative,
        # all real (|freq| >= 10).
        expected = [(-23.08, 0.00717), (-18.11, 0.25411)]
        for i, (freq, intensity) in enumerate(expected):
            mode = self.spectrum.modes[7 + i]
            self.assertEqual(mode.index, 8 + i)
            self.assertLess(mode.freq, 0.0)
            self.assertAlmostEqual(mode.freq, freq, places=2)
            self.assertAlmostEqual(mode.intensity, intensity, places=5)

    def test_last_mode_78(self):
        mode = self.spectrum.modes[-1]
        self.assertEqual(mode.index, 78)
        self.assertAlmostEqual(mode.freq, 3521.18, places=2)
        self.assertAlmostEqual(mode.intensity, 34.95709, places=5)

    def test_min_real_intensity_present(self):
        # Mode 49 (line 52) has intensity 0.00026 -- near-zero rows must
        # survive parsing (SPECTRA-05: zero/near-zero modes included).
        real_intensities = [m.intensity for m in self.spectrum.modes[6:]]
        self.assertAlmostEqual(min(real_intensities), 0.00026, places=5)

    def test_fixture_real_rows_have_symmetry_a(self):
        # The Mode namedtuple (02-01) carries no symmetry field, so verify
        # the fixture directly: all 5-token (real) rows carry 'a' in the
        # symmetry slot (t[1]). This is the fixture property the plan's
        # 'symmetry a on all real modes' requirement refers to.
        with open(VIBSPECTRUM_PATH, encoding='utf-8') as fh:
            for lineno, line in enumerate(fh, 1):
                stripped = line.strip()
                if not stripped or stripped.startswith('#'):
                    continue
                if stripped in ('$vibrational spectrum', '$end'):
                    continue
                tokens = stripped.split()
                if len(tokens) == 5:
                    self.assertEqual(tokens[1], 'a',
                                     'line %d: real row symmetry != a'
                                     % lineno)


class TestRealModesFilter(unittest.TestCase):
    """real_modes() threshold policy: |freq| ONLY — never sign, never
    selection-rule column, never a hardcoded 5/6 trivial count.

    The dimer (nonlinear, 26 atoms) has 6 trivial modes; the synthetic CO2
    (linear, 3 atoms) has 5. A hardcoded 'skip 6' would silently corrupt
    every linear molecule — this class proves the filter is purely
    threshold-based and parameterized.
    """

    @classmethod
    def setUpClass(cls):
        cls.dimer = parse_vibspectrum(VIBSPECTRUM_PATH)
        cls.co2 = parse_vibspectrum(CO2_VIBSPECTRUM_PATH)

    # --- dimer (nonlinear, 6 trivial) ----------------------------------------

    def test_dimer_default_threshold_drops_6_trivial(self):
        real = real_modes(self.dimer)
        self.assertEqual(len(real), 72)
        self.assertEqual([m.index for m in real], list(range(7, 79)))

    def test_dimer_negative_real_modes_kept(self):
        # Modes 7-9 are negative (-31.92 / -23.08 / -18.11) but REAL —
        # sign never filters. This is the load-bearing sign-policy test.
        real = real_modes(self.dimer)
        first_three = real[:3]
        for mode in first_three:
            self.assertLess(mode.freq, 0.0)
        self.assertAlmostEqual(first_three[0].freq, -31.92, places=2)
        self.assertAlmostEqual(first_three[1].freq, -23.08, places=2)
        self.assertAlmostEqual(first_three[2].freq, -18.11, places=2)

    # --- synthetic CO2 (linear, 5 trivial) -----------------------------------

    def test_co2_parses_to_8_modes(self):
        self.assertEqual(len(self.co2.modes), 8)
        self.assertEqual(self.co2.atoms, [])
        self.assertEqual(self.co2.n_atoms, 0)

    def test_co2_5_trivial_3_real(self):
        # 5 trivial (modes 1-5, |0.00| < 10) + 3 real (modes 6-8).
        trivial = self.co2.modes[:5]
        for mode in trivial:
            self.assertLess(abs(mode.freq), 10.0)
        real = self.co2.modes[5:]
        self.assertEqual(len(real), 3)

    def test_co2_default_threshold_returns_3_real(self):
        real = real_modes(self.co2)
        self.assertEqual(len(real), 3)
        self.assertEqual([m.index for m in real], [6, 7, 8])
        freqs = [m.freq for m in real]
        # Degenerate 600.18 pair retained as SEPARATE Mode objects.
        self.assertAlmostEqual(freqs[0], 600.18, places=2)
        self.assertAlmostEqual(freqs[1], 600.18, places=2)
        self.assertAlmostEqual(freqs[2], 1424.95, places=2)

    def test_co2_zero_intensity_mode_kept(self):
        # Mode 8 = 1424.95 symmetric stretch: intensity exactly 0.00
        # (IR-inactive). SPECTRA-05: zero-intensity modes are listed.
        real = real_modes(self.co2)
        mode8 = real[-1]
        self.assertEqual(mode8.index, 8)
        self.assertAlmostEqual(mode8.intensity, 0.0, places=5)

    def test_co2_2593_row_honestly_omitted(self):
        # The 2593.38 asymmetric stretch is NOT in the fixture — its log
        # intensity token is the overflow '******'. Verify no mode has
        # that frequency (the fixture is 8 rows, not 9).
        for mode in self.co2.modes:
            self.assertNotAlmostEqual(mode.freq, 2593.38, places=2,
                                      msg='2593.38 row should be omitted')

    # --- threshold parametrization (proves no hardcoded count) ---------------

    def test_co2_threshold_700_returns_one(self):
        # Raising the threshold to 700 drops the 600.18 pair, keeps only
        # 1424.95. A hardcoded 'skip 5' or 'skip 6' count could not produce
        # this result — only the |freq| threshold can.
        real = real_modes(self.co2, threshold=700.0)
        self.assertEqual(len(real), 1)
        self.assertAlmostEqual(real[0].freq, 1424.95, places=2)

    def test_co2_threshold_0_5_returns_three(self):
        # Lowering the threshold to 0.5 still drops the 0.00 trivial rows
        # (|0.0| < 0.5) and keeps all 3 real modes.
        real = real_modes(self.co2, threshold=0.5)
        self.assertEqual(len(real), 3)
        self.assertEqual([m.index for m in real], [6, 7, 8])

    # --- g98 no-op -----------------------------------------------------------

    def test_g98_no_op_all_72_kept(self):
        # The g98 core projects trivial modes out, so all 72 modes have
        # |freq| >= 18.1 and pass the default threshold. real_modes must
        # return the SAME Mode objects (identity, not copies).
        g98 = parse_g98(G98_PATH)
        real = real_modes(g98)
        self.assertEqual(len(real), 72)
        self.assertEqual([m.index for m in real],
                         [m.index for m in g98.modes])
        for real_mode, orig_mode in zip(real, g98.modes):
            self.assertIs(real_mode, orig_mode)


if __name__ == '__main__':
    unittest.main()
