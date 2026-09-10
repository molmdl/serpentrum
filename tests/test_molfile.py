"""molfile SDF reader + cyclomatic ring-count tests (03-02, RED-1).

Discovery command (verified on python3.6.9 -- NOTE: `-t .` FAILS on
python3.6 with a non-package start dir; do not add it):

    python3.6 -m unittest discover -s tests -p "test_*.py" -v

Fixtures are committed V2000/mol2 bytes under tests/fixtures/molfile/
(fixtures-first: the parser is written against committed bytes, not
documentation). These are TEST DATA, not chemistry claims -- simple hand
coordinates are fine, the parser must not care about geometry quality.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from serpentrum import molfile  # noqa: E402  -- RED: ModuleNotFoundError expected

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURES = os.path.join(ROOT, 'tests', 'fixtures', 'molfile')


def _fixture(name):
    """Absolute path to a committed molfile fixture."""
    return os.path.join(FIXTURES, name)


def _read_fixture(name):
    """Read a fixture file's text (utf-8)."""
    with open(_fixture(name), 'r', encoding='utf-8') as handle:
        return handle.read()


class TestCountRings(unittest.TestCase):
    """Behavior case 1: cyclomatic number mu = E - V + C, exact ints.

    No SSSR algorithm -- just edge count, vertex count, and connected
    components via BFS on the adjacency built from (i, j) 0-based pairs.
    H atoms are pendant (net-zero effect on mu).
    """

    def test_benzene_hexagon_one_ring(self):
        # V=6, E=6, C=1, mu = 6-6+1 = 1.
        bonds = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 0)]
        self.assertEqual(molfile.count_rings(bonds, 6), 1)

    def test_naphthalene_two_fused_hexagons(self):
        # Two fused hexagons sharing one edge: V=10, E=11, C=1, mu=2.
        # Ring 1: 0-1-2-3-4-5-0; Ring 2: 4-5-6-7-8-9-4 (shares edge 4-5).
        bonds = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 0),
                 (5, 6), (6, 7), (7, 8), (8, 9), (9, 4)]
        self.assertEqual(molfile.count_rings(bonds, 10), 2)

    def test_biphenyl_shape_two_rings_plus_inter_bond(self):
        # Two hexagons + inter-ring bond: V=12, E=13, C=1, mu=2.
        bonds = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 0),
                 (6, 7), (7, 8), (8, 9), (9, 10), (10, 11), (11, 6),
                 (5, 6)]
        self.assertEqual(molfile.count_rings(bonds, 12), 2)

    def test_two_disconnected_hexagons(self):
        # Two DISCONNECTED hexagons: V=12, E=12, C=2, mu=2.
        bonds = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 0),
                 (6, 7), (7, 8), (8, 9), (9, 10), (10, 11), (11, 6)]
        self.assertEqual(molfile.count_rings(bonds, 12), 2)

    def test_linear_chain_zero_rings(self):
        # V=4, E=3, C=1, mu=0.
        bonds = [(0, 1), (1, 2), (2, 3)]
        self.assertEqual(molfile.count_rings(bonds, 4), 0)

    def test_no_bonds_zero_rings(self):
        # V=3, E=0, C=3, mu=0.
        self.assertEqual(molfile.count_rings([], 3), 0)


class TestReadSdf(unittest.TestCase):
    """Behavior cases 2-4: fixture-driven SDF V2000 parsing."""

    def test_methane_single_record(self):
        # Case 2: methane -- 5 atoms (C + 4 H), 4 bonds, charge 0,
        # ring_count 0, has_explicit_h True.
        records = molfile.read_sdf(_fixture('methane.sdf'))
        self.assertEqual(len(records), 1)
        rec = records[0]
        self.assertEqual(rec['title'], 'methane')
        self.assertEqual(rec['elements'], ['C', 'H', 'H', 'H', 'H'])
        self.assertEqual(len(rec['coords']), 5)
        for coord in rec['coords']:
            self.assertEqual(len(coord), 3)
        self.assertEqual(len(rec['bonds']), 4)
        self.assertEqual(rec['charges'], {})
        self.assertEqual(rec['charge'], 0)
        self.assertEqual(rec['ring_count'], 0)
        self.assertTrue(rec['has_explicit_h'])
        self.assertEqual(rec['record_index'], 0)
        self.assertEqual(rec['warnings'], [])

    def test_benzene_naphthalene_multi_record(self):
        # Case 3: 2 records -- benzene (12/12/1) + naphthalene (18/19/2).
        records = molfile.read_sdf(_fixture('benzene_naphthalene.sdf'))
        self.assertEqual(len(records), 2)
        benz, naph = records[0], records[1]
        # Record 0: benzene.
        self.assertEqual(benz['record_index'], 0)
        self.assertEqual(len(benz['elements']), 12)
        self.assertEqual(len(benz['bonds']), 12)
        self.assertEqual(benz['ring_count'], 1)
        self.assertTrue(benz['has_explicit_h'])
        # Record 1: naphthalene.
        self.assertEqual(naph['record_index'], 1)
        self.assertEqual(len(naph['elements']), 18)
        self.assertEqual(len(naph['bonds']), 19)
        self.assertEqual(naph['ring_count'], 2)
        self.assertTrue(naph['has_explicit_h'])

    def test_acetate_m_chg(self):
        # Case 4: 6 atoms, 5 bonds, M CHG -> charge -1, contains O.
        records = molfile.read_sdf(_fixture('acetate.sdf'))
        self.assertEqual(len(records), 1)
        rec = records[0]
        self.assertEqual(rec['title'], 'acetate')
        self.assertEqual(len(rec['elements']), 6)
        self.assertEqual(len(rec['bonds']), 5)
        self.assertIn('O', rec['elements'])
        self.assertEqual(rec['charge'], -1)
        # The charges dict carries the charged atom index -> -1.
        charged = [idx for idx, chg in rec['charges'].items() if chg == -1]
        self.assertEqual(len(charged), 1)
        self.assertEqual(rec['charges'][charged[0]], -1)


class TestLoudFailures(unittest.TestCase):
    """Behavior case 5: malformed records raise MolFileError with line+snippet.

    Mirrors xyzio.py's XyzError contract: message names the 1-based line
    number and quotes the first ~60 chars of the offending line.
    """

    def test_truncated_record_raises_with_line_and_snippet(self):
        # Counts line says 5 atoms but only 2 atom rows follow before M END.
        text = (
            "truncated\n"
            "  prog\n"
            "\n"
            "  5  0  0  0  0  0  0  0  0  0999 V2000\n"
            "    0.0000    0.0000    0.0000 C   0  0\n"
            "    1.0000    0.0000    0.0000 C   0  0\n"
            "M  END\n"
            "$$$$\n"
        )
        with self.assertRaises(molfile.MolFileError) as caught:
            molfile.read_sdf_text(text)
        message = str(caught.exception)
        self.assertIn('line', message)

    def test_bad_element_symbol_raises_mentioning_symbol(self):
        text = (
            "badsym\n"
            "  prog\n"
            "\n"
            "  1  0  0  0  0  0  0  0  0  0999 V2000\n"
            "    0.0000    0.0000    0.0000 Xx  0  0\n"
            "M  END\n"
            "$$$$\n"
        )
        with self.assertRaises(molfile.MolFileError) as caught:
            molfile.read_sdf_text(text)
        self.assertIn('Xx', str(caught.exception))


if __name__ == '__main__':
    unittest.main()
