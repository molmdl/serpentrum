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


class TestWriteSdfRoundTrip(unittest.TestCase):
    """Behavior case 6: write_sdf_text round-trips parsed records.

    For each SDF fixture record: read -> write_sdf_text -> read again
    yields identical elements (order), bond count, charge sum, and coords
    within 1e-6; the written text ends with '$$$'.
    """

    SDF_FIXTURES = ('methane.sdf', 'benzene_naphthalene.sdf',
                    'acetate.sdf', 'benzene_noh.sdf')

    def test_round_trip_preserves_elements_bonds_charge_coords(self):
        for name in self.SDF_FIXTURES:
            records = molfile.read_sdf(_fixture(name))
            for rec in records:
                text = molfile.write_sdf_text(rec)
                self.assertTrue(
                    text.rstrip().endswith('$$$$'),
                    'written text for %s record %d does not end with $$$$'
                    % (name, rec['record_index']))
                round_trip = molfile.read_sdf_text(text)
                self.assertEqual(len(round_trip), 1)
                rt = round_trip[0]
                self.assertEqual(rt['elements'], rec['elements'],
                    'elements mismatch for %s record %d'
                    % (name, rec['record_index']))
                self.assertEqual(len(rt['bonds']), len(rec['bonds']),
                    'bond count mismatch for %s record %d'
                    % (name, rec['record_index']))
                self.assertEqual(rt['charge'], rec['charge'],
                    'charge mismatch for %s record %d'
                    % (name, rec['record_index']))
                self.assertEqual(len(rt['coords']), len(rec['coords']))
                for orig, rt_coord in zip(rec['coords'], rt['coords']):
                    for o_val, r_val in zip(orig, rt_coord):
                        self.assertAlmostEqual(o_val, r_val, places=6)


class TestReadMol2(unittest.TestCase):
    """Behavior case 7: mol2 reader with charge=0 + warning."""

    def test_benzene_mol2(self):
        records = molfile.read_mol2(_fixture('benzene.mol2'))
        self.assertEqual(len(records), 1)
        rec = records[0]
        self.assertEqual(len(rec['elements']), 12)
        self.assertEqual(len(rec['bonds']), 12)
        self.assertEqual(rec['charge'], 0)
        # The mol2-charge warning text must be present.
        self.assertTrue(
            any('mol2' in w.lower() and 'charge' in w.lower()
                for w in rec['warnings']),
            'mol2 charge warning not found in %r' % rec['warnings'])


class TestFindRingAtoms(unittest.TestCase):
    """Behavior case 8: ring-atom finder returns the benzene 6-cycle.

    find_ring_atoms(benzene) -> sorted list of exactly 6 indices that all
    have degree >= 2 within the returned set and form a cycle.
    find_ring_atoms(methane) -> [].
    """

    def test_benzene_returns_six_ring_carbons(self):
        records = molfile.read_sdf(_fixture('benzene_naphthalene.sdf'))
        benzene = records[0]
        ring_atoms = molfile.find_ring_atoms(benzene)
        self.assertEqual(len(ring_atoms), 6)
        self.assertEqual(ring_atoms, sorted(ring_atoms))
        # Each ring atom must have degree >= 2 within the returned set.
        ring_set = set(ring_atoms)
        bond_set = set()
        for a, b in benzene['bonds']:
            bond_set.add((a, b))
            bond_set.add((b, a))
        for atom in ring_atoms:
            neighbors = [other for other in ring_set
                         if other != atom and (atom, other) in bond_set]
            self.assertGreaterEqual(
                len(neighbors), 2,
                'ring atom %d has only %d ring neighbors'
                % (atom, len(neighbors)))

    def test_methane_returns_empty(self):
        records = molfile.read_sdf(_fixture('methane.sdf'))
        methane = records[0]
        self.assertEqual(molfile.find_ring_atoms(methane), [])


class TestGateMatrix(unittest.TestCase):
    """Behavior case 9: gate rejects >3-ring and organic-no-H, accepts
    inorganic-no-H with advisory, charge never rejects.

    gate_molecule(record) -> (ok, reason).
    gate_set(records) -> (accepted, rejected) with per-molecule reasons.
    """

    def _benzene_record(self):
        return molfile.read_sdf(_fixture('benzene_naphthalene.sdf'))[0]

    def _noh_record(self):
        return molfile.read_sdf(_fixture('benzene_noh.sdf'))[0]

    def _synthetic(self, title, elements, ring_count, has_explicit_h,
                   bonds=None):
        """Build a minimal record dict for gate testing."""
        return {
            'title': title,
            'elements': list(elements),
            'coords': [(0.0, 0.0, 0.0)] * len(elements),
            'bonds': list(bonds) if bonds else [],
            'charges': {},
            'record_index': 0,
            'atom_count': len(elements),
            'charge': 0,
            'ring_count': ring_count,
            'has_explicit_h': has_explicit_h,
            'warnings': [],
        }

    def test_benzene_accepted(self):
        ok, reason = molfile.gate_molecule(self._benzene_record())
        self.assertTrue(ok)
        self.assertIsNone(reason)

    def test_ring_count_4_rejected(self):
        rec = self._synthetic('ring4', ['C', 'H'], 4, True)
        ok, reason = molfile.gate_molecule(rec)
        self.assertFalse(ok)
        self.assertIn('rings', reason)
        self.assertIn('3', reason)

    def test_organic_no_h_rejected(self):
        rec = self._noh_record()
        ok, reason = molfile.gate_molecule(rec)
        self.assertFalse(ok)
        self.assertIn('hydrogen', reason.lower())

    def test_inorganic_no_h_accepted_with_warning(self):
        rec = self._synthetic('NaCl', ['Na', 'Cl'], 0, False,
                              bonds=[(0, 1)])
        warnings_before = len(rec['warnings'])
        ok, reason = molfile.gate_molecule(rec)
        self.assertTrue(ok)
        self.assertIsNone(reason)
        self.assertEqual(len(rec['warnings']), warnings_before + 1)
        self.assertIn('hydrogen', rec['warnings'][-1].lower())

    def test_gate_set_ordering(self):
        benzene = self._benzene_record()
        noh = self._noh_record()
        ring4 = self._synthetic('ring4', ['C', 'H'], 4, True)
        accepted, rejected = molfile.gate_set([benzene, noh, ring4])
        self.assertEqual(len(accepted), 1)
        self.assertEqual(accepted[0]['title'], benzene['title'])
        self.assertEqual(len(rejected), 2)
        # Rejected in input order: noh (hydrogen), ring4 (rings).
        self.assertEqual(rejected[0][0]['title'], noh['title'])
        self.assertIn('hydrogen', rejected[0][1].lower())
        self.assertEqual(rejected[1][0]['title'], ring4['title'])
        self.assertIn('rings', rejected[1][1])


if __name__ == '__main__':
    unittest.main()
