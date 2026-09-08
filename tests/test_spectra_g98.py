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


def synthetic_remainder_text():
    """SYNTHETIC 3-atom g98-shaped text carrying a remainder block.

    Clearly labeled synthetic: NO real fixture has a remainder block (the
    committed dimer is 72 = 24x3) — token-count-driven parsing is the
    asserted assumption. Block 1 = modes 1-3 in 3 columns; block 2 =
    mode 4 in 1 column (the 3+1 remainder), per the plan's example row
    grammar (' Atom AN      X' header, 3-token displacement rows).
    """
    return '\n'.join([
        ' Entering Gaussian System, Link 0.exe',
        ' Standard orientation:',
        ' --------------------------------------------------------------------',
        '  Center     Atomic     Atomic              Coordinates (Angstroms)',
        '  Number     Number      Type              X           Y           Z',
        ' --------------------------------------------------------------------',
        '    1          6             0        0.000000    0.000000    0.000000',
        '    2          6             0        1.000000    0.000000    0.000000',
        '    3          1             0        0.000000    1.000000    0.000000',
        ' --------------------------------------------------------------------',
        '                      1                      2                      3',
        ' Frequencies --    10.0000                20.0000                30.0000',
        ' Red. masses --     1.0                    1.0                    1.0',
        ' Frc consts  --     0.0                    0.0                    0.0',
        ' IR Inten    --     1.0                    2.0                    3.0',
        ' Raman Activ --     0.0                    0.0                    0.0',
        ' Depolar     --     0.0                    0.0                    0.0',
        ' Atom AN      X      Y      Z        X      Y      Z        X      Y      Z',
        '   1   6     0.10   0.11   0.12     0.20   0.21   0.22     0.30   0.31   0.32',
        '   2   6     0.13   0.14   0.15     0.23   0.24   0.25     0.33   0.34   0.35',
        '   3   1     0.16   0.17   0.18     0.26   0.27   0.28     0.36   0.37   0.38',
        '                      4',
        ' Frequencies --  100.0000',
        ' Red. masses --  1.0',
        ' Frc consts  --  0.0',
        ' IR Inten    --  5.0',
        ' Raman Activ --  0.0',
        ' Depolar     --  0.0',
        ' Atom AN      X',
        '   1   6    0.10',
        '   2   6    0.20',
        '   3   1    0.30',
    ])


class TestG98RemainderBlock(unittest.TestCase):
    """Behavior case 3 (synthetic input): 3-column block + 1-column
    remainder block parse as 4 modes with 1-float vector tuples."""

    def test_remainder_block_parses_to_four_modes(self):
        spectrum = parse_g98_text(synthetic_remainder_text())
        self.assertEqual(spectrum.n_atoms, 3)
        self.assertEqual(len(spectrum.modes), 4)
        # Mode indices stay a running 1-based count across the 3+1 split.
        self.assertEqual([m.index for m in spectrum.modes],
                         [1, 2, 3, 4])

    def test_full_block_modes_keep_three_float_vectors(self):
        spectrum = parse_g98_text(synthetic_remainder_text())
        for mode in spectrum.modes[:3]:
            self.assertEqual(len(mode.vectors), 3)
            for vector in mode.vectors:
                self.assertEqual(len(vector), 3)
        self.assertAlmostEqual(spectrum.modes[0].freq, 10.0, places=4)
        self.assertAlmostEqual(spectrum.modes[2].intensity, 3.0, places=4)

    def test_remainder_mode_carries_one_float_tuples(self):
        mode = parse_g98_text(synthetic_remainder_text()).modes[3]
        self.assertAlmostEqual(mode.freq, 100.0, places=4)
        self.assertAlmostEqual(mode.intensity, 5.0, places=4)
        vectors = mode.vectors
        self.assertEqual(len(vectors), 3)
        # Exact-equality shape: one float per atom, from 3-token rows.
        for vector, expected in zip(vectors, (0.10, 0.20, 0.30)):
            self.assertIsInstance(vector, tuple)
            self.assertEqual(len(vector), 1)
            self.assertAlmostEqual(vector[0], expected, places=6)


class TestG98LoudFailures(unittest.TestCase):
    """Behavior cases 4-5: corrupt or malformed input fails loudly with
    SpectraParseError (never a bare ValueError), carrying parser stage,
    1-based line number, and the offending line's excerpt."""

    def test_bad_log_raises_naming_missing_frequency_section(self):
        # bad.log: failed xtb run, 105 lines, fatal error at line 97 and
        # NO frequency section anywhere -> the loud-failure contract.
        text = read_fixture_text('bad.log')
        with self.assertRaises(SpectraParseError) as ctx:
            parse_g98_text(text)
        self.assertIn('frequency section', str(ctx.exception))

    def test_malformed_property_row_raises_with_line_and_excerpt(self):
        # Synthetic in-memory corruption of the REAL fixture: block 1's
        # ' IR Inten    --' row (1-based line 49) becomes garbage.
        lines = read_fixture_text('g98.out').splitlines()
        target = None
        for index, line in enumerate(lines):
            if line.startswith(' IR Inten    --'):
                target = index
                break
        self.assertIsNotNone(target, 'no IR Inten row found in fixture')
        self.assertEqual(target, 48, 'fixture grammar shifted: IR Inten '
                         'expected at 1-based line 49')
        lines[target] = ' IR Inten    --  garbage not-floats'
        with self.assertRaises(SpectraParseError) as ctx:
            parse_g98_text('\n'.join(lines))
        message = str(ctx.exception)
        self.assertIn('frequency block', message)   # parser stage
        self.assertIn(str(target + 1), message)     # 1-based line number
        self.assertIn('garbage', message)           # offending-line excerpt


class TestFixtureByteIdentity(unittest.TestCase):
    """Behavior case 6: the single-copy rule — byte-identical to source."""

    def test_fixture_dir_holds_exactly_the_17_file_set(self):
        # Exact FILE set equality also guards the traps: dimer.xyz
        # (mislabeled CO2 dimer), hessian, xtbrestart must never leak in,
        # and no __init__.py may ever appear under tests/ (plugin-path
        # safety). Subdirectories (e.g. synthetic/ added by 02-09) are
        # allowed — only FILES are checked against the 17-copy set.
        files = [name for name in os.listdir(FIXTURES)
                 if os.path.isfile(os.path.join(FIXTURES, name))]
        self.assertEqual(sorted(files), sorted(COPIED_FIXTURES))

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
