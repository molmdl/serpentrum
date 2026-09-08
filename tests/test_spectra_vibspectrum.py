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
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURES = os.path.join(ROOT, 'tests', 'fixtures', 'xtb')
VIBSPECTRUM_PATH = os.path.join(FIXTURES, 'vibspectrum')
G98_PATH = os.path.join(FIXTURES, 'g98.out')


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


if __name__ == '__main__':
    unittest.main()
