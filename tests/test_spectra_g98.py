"""Fixture-driven tests for the g98 spectra parser core (serpentrum/spectra.py).

Every assertion below is pinned to VERIFIED values probed against the
committed xtb spike fixtures on 2026-09-06/07 (02-RESEARCH-pure-core.md
S1.1 + the 02-01 plan's load-bearing facts): 26-atom phenol pi-dimer,
72 modes = 3x26-6 in 24 blocks of 3 columns at stride 35, first
'Frequencies --' line 46, last line 851, EOF-terminated final block.

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

from serpentrum.spectra import (  # noqa: E402
    Atom,
    Mode,
    Spectrum,
    SpectraParseError,
    parse_g98,
    parse_g98_text,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURES = os.path.join(ROOT, 'tests', 'fixtures', 'xtb')
SPIKE_FIXTURES = os.path.join(ROOT, '.planning', 'research',
                              'xtb-spike-fixtures')
G98_PATH = os.path.join(FIXTURES, 'g98.out')

# The EXACT 17-file copy set (single-copy rule): everything the later
# spectra plans (02-09 vibspectrum / 02-12 dispatcher) consume from here.
# Explicitly NOT copied: dimer.xyz (MISLABELED CO2-dimer trap — never mine
# it for phenol data), hessian (Anti-Pattern 5), xtbrestart (binary),
# charges/wbo/xtbtopo.mol/xtbopt.log/xtbhess.xyz (context only).
COPIED_FIXTURES = (
    'bad.err', 'bad.log', 'bad.xyz',
    'co2.err', 'co2.log', 'co2.xyz',
    'dimer2.err', 'dimer2.log', 'dimer2.xyz',
    'g98.out',
    'ohess.err', 'ohess.log',
    'phenol.xyz',
    'repro_oh.err', 'repro_oh.log',
    'vibspectrum',
    'xtbopt.xyz',
)


def read_fixture_text(name):
    """Fixture text with utf-8 (header carries a literal U+207B U+00B9)."""
    with open(os.path.join(FIXTURES, name), encoding='utf-8') as fh:
        return fh.read()


class TestG98HappyPath(unittest.TestCase):
    """Behavior case 1: parse_g98 on the committed dimer fixture."""

    @classmethod
    def setUpClass(cls):
        cls.spectrum = parse_g98(G98_PATH)

    def test_returns_spectrum_namedtuple(self):
        spectrum = self.spectrum
        self.assertIsInstance(spectrum, Spectrum)
        self.assertEqual(spectrum.n_atoms, 26)
        self.assertEqual(len(spectrum.atoms), 26)
        self.assertEqual(len(spectrum.modes), 72)

    def test_first_atom_row(self):
        atom = self.spectrum.atoms[0]
        self.assertIsInstance(atom, Atom)
        self.assertEqual(atom.atomic_number, 6)
        self.assertAlmostEqual(atom.x, 0.020733, places=6)
        self.assertAlmostEqual(atom.y, -1.840903, places=6)
        self.assertAlmostEqual(atom.z, -0.006438, places=6)

    def test_first_mode_anchors(self):
        mode = self.spectrum.modes[0]
        self.assertIsInstance(mode, Mode)
        self.assertEqual(mode.index, 1)
        self.assertAlmostEqual(mode.freq, -31.9175, places=4)
        self.assertAlmostEqual(mode.intensity, 2.4191, places=4)

    def test_last_mode_anchor(self):
        mode = self.spectrum.modes[-1]
        self.assertAlmostEqual(mode.freq, 3521.1843, places=4)

    def test_mode_vectors_are_26_three_float_tuples(self):
        vectors = self.spectrum.modes[0].vectors
        self.assertEqual(len(vectors), 26)
        for vector in vectors:
            self.assertIsInstance(vector, tuple)
            self.assertEqual(len(vector), 3)
            for component in vector:
                self.assertIsInstance(component, float)

    def test_first_vector_column_values(self):
        # Fixture line 53 (mode block 1, atom 1): x1 y1 z1 = -0.02 -0.01 -0.01
        vector = self.spectrum.modes[0].vectors[0]
        self.assertAlmostEqual(vector[0], -0.02, places=2)
        self.assertAlmostEqual(vector[1], -0.01, places=2)
        self.assertAlmostEqual(vector[2], -0.01, places=2)

    def test_negative_frequencies_kept(self):
        # Modes 1-3 are the three imaginary modes: negatives are data.
        first_three = self.spectrum.modes[:3]
        self.assertEqual(len(first_three), 3)
        for mode in first_three:
            self.assertLess(mode.freq, 0.0)


class TestG98BlockStructure(unittest.TestCase):
    """Behavior case 2: 24 blocks x 3 columns, stride-35 grammar end to end."""

    @classmethod
    def setUpClass(cls):
        cls.modes = parse_g98(G98_PATH).modes

    def test_block_1_values(self):
        freqs = [m.freq for m in self.modes[:3]]
        intens = [m.intensity for m in self.modes[:3]]
        expected_freqs = (-31.9175, -23.0766, -18.1086)
        expected_intens = (2.4191, 0.0072, 0.2541)
        for got, want in zip(freqs, expected_freqs):
            self.assertAlmostEqual(got, want, places=4)
        for got, want in zip(intens, expected_intens):
            self.assertAlmostEqual(got, want, places=4)

    def test_block_24_values(self):
        # Modes 70-72: the last block, terminated by EOF (no trailing text).
        freqs = [m.freq for m in self.modes[69:72]]
        expected = (3113.7215, 3519.9549, 3521.1843)
        for got, want in zip(freqs, expected):
            self.assertAlmostEqual(got, want, places=4)

    def test_indices_run_1_to_72_across_blocks(self):
        # Exact-equality case: running 1-based count across all 24 blocks.
        self.assertEqual([m.index for m in self.modes], list(range(1, 73)))

    def test_every_mode_has_26_three_float_vectors(self):
        # Column count comes from the Frequencies line, never fixed; for the
        # committed fixture every block carries 3 columns -> 3-float tuples.
        for mode in self.modes:
            self.assertEqual(len(mode.vectors), 26,
                             'mode %d vector count' % mode.index)
            for vector in mode.vectors:
                self.assertEqual(len(vector), 3)


class TestFixtureByteIdentity(unittest.TestCase):
    """Behavior case 6: the single-copy rule — byte-identical to source."""

    def test_fixture_dir_holds_exactly_the_17_file_set(self):
        # Exact set equality also guards the traps: dimer.xyz (mislabeled
        # CO2 dimer), hessian, xtbrestart must never leak in, and no
        # __init__.py may ever appear under tests/ (plugin-path safety).
        self.assertEqual(sorted(os.listdir(FIXTURES)), sorted(COPIED_FIXTURES))

    def test_every_copy_is_byte_identical_to_source(self):
        for name in COPIED_FIXTURES:
            copy_path = os.path.join(FIXTURES, name)
            source_path = os.path.join(SPIKE_FIXTURES, name)
            with open(copy_path, 'rb') as copy_fh:
                copy_bytes = copy_fh.read()
            with open(source_path, 'rb') as source_fh:
                source_bytes = source_fh.read()
            self.assertEqual(copy_bytes, source_bytes,
                             'fixture copy not byte-identical: %s' % name)


if __name__ == '__main__':
    unittest.main()
