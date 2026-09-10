"""Real-file regression suite for Demo Set A (checkpoint 03-05 post-gate).

skipUnless-guarded: skips cleanly while the 5 PubChem 3D SDFs + manifest
are absent (pre-checkpoint), hard-passes once they exist. Closes the
fixtures-first gap: the molfile parser + <=3-ring gate are now proven
against actual PubChem bytes (not just hand-written fixtures).

Tests (all read-only -- NO writes to serpentrum/data/):
  - manifest.json loads via molecule_data.load_manifest (5 molecules, 1 set)
  - each of the 5 SDFs: file exists, read_sdf yields exactly 1 record,
    gate_molecule ACCEPTS (ok=True, reason=None)
  - parsed atom_count/charge/ring_count equal the manifest's declared values
  - computed cyclomatic ring counts equal [1, 2, 3, 3, 2] by molecule id
  - manifest ring_atoms are >= 3 unique int indices in [0, atom_count)

Discovery: python3.6 -m unittest discover -s tests -p "test_*.py" -v
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from serpentrum import molfile  # noqa: E402
from serpentrum import molecule_data  # noqa: E402

# serpentrum/data/ sits next to the serpentrum/ package directory.
_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         'serpentrum', 'data')

_SDF_NAMES = ['benzene.sdf', 'naphthalene.sdf', 'anthracene.sdf',
              'phenanthrene.sdf', 'biphenyl.sdf']

# Skip cleanly pre-checkpoint: all 5 SDFs + manifest.json must exist.
HAS_DATA = all(os.path.isfile(os.path.join(_DATA_DIR, f))
               for f in _SDF_NAMES + ['manifest.json'])

# Expected cyclomatic ring counts by molecule id (verified arithmetic,
# 03-RESEARCH-upload-gate.md sec 2.2: mu = E - V + C).
EXPECTED_RING_COUNTS = {
    'benzene': 1,
    'naphthalene': 2,
    'anthracene': 3,
    'phenanthrene': 3,
    'biphenyl': 2,
}


@unittest.skipUnless(HAS_DATA,
                     'demo Set A SDFs + manifest not yet provided '
                     '(checkpoint 03-05)')
class TestDemoSetA(unittest.TestCase):
    """Real-file regression: the 5 shipped PubChem SDFs + manifest.json."""

    @classmethod
    def setUpClass(cls):
        """Load the manifest once; build an id -> molecule map."""
        cls.manifest_path = os.path.join(_DATA_DIR, 'manifest.json')
        cls.manifest = molecule_data.load_manifest(cls.manifest_path)
        cls.molecules = {}
        for mol_set in cls.manifest['sets']:
            for mol in mol_set['molecules']:
                cls.molecules[mol['id']] = mol

    def test_manifest_structure(self):
        """schema_version 1, one set, exactly 5 molecules."""
        self.assertEqual(self.manifest['schema_version'], 1)
        self.assertEqual(len(self.manifest['sets']), 1)
        mol_set = self.manifest['sets'][0]
        self.assertEqual(mol_set['id'], 'set_a')
        self.assertEqual(mol_set['name'], 'Aromatic pi-stack')
        self.assertEqual(len(mol_set['molecules']), 5)

    def test_manifest_has_expected_molecule_ids(self):
        """The 5 DATA_SOURCES.md molecules, in order."""
        ids = [m['id'] for m in self.manifest['sets'][0]['molecules']]
        self.assertEqual(ids, ['benzene', 'naphthalene', 'anthracene',
                               'phenanthrene', 'biphenyl'])

    def test_manifest_source_metadata(self):
        """Every molecule: source_db='PubChem', source_id='CID <n>'."""
        expected_cids = {
            'benzene': 'CID 241', 'naphthalene': 'CID 931',
            'anthracene': 'CID 8418', 'phenanthrene': 'CID 995',
            'biphenyl': 'CID 7095',
        }
        for mol_id, expected_cid in expected_cids.items():
            mol = self.molecules[mol_id]
            self.assertEqual(mol['source_db'], 'PubChem',
                             '%s: source_db' % mol_id)
            self.assertEqual(mol['source_id'], expected_cid,
                             '%s: source_id' % mol_id)

    def test_each_sdf_parses_and_gates_and_matches_manifest(self):
        """For each of the 5 molecules: 1 record, gate accepts, manifest
        atom_count/charge/ring_count match the parsed SDF reality."""
        for mol_id, mol in self.molecules.items():
            with self.subTest(molecule=mol_id):
                sdf_path = os.path.join(_DATA_DIR, mol['file'])
                self.assertTrue(os.path.isfile(sdf_path),
                                '%s: file missing' % mol_id)

                records = molfile.read_sdf(sdf_path)
                self.assertEqual(len(records), 1,
                                 '%s: expected 1 record, got %d'
                                 % (mol_id, len(records)))

                record = records[0]
                ok, reason = molfile.gate_molecule(record)
                self.assertTrue(ok, '%s: gate rejected -- %s'
                                % (mol_id, reason))

                # Manifest values must equal parsed reality.
                self.assertEqual(record['atom_count'], mol['atom_count'],
                                 '%s: atom_count mismatch' % mol_id)
                self.assertEqual(record['charge'], mol['charge'],
                                 '%s: charge mismatch' % mol_id)
                self.assertEqual(record['ring_count'], mol['ring_count'],
                                 '%s: ring_count mismatch' % mol_id)

    def test_ring_counts_match_expected_map(self):
        """Cyclomatic ring counts: benzene 1, naphthalene 2, anthracene 3,
        phenanthrene 3, biphenyl 2 (all <= 3 -> all pass the gate)."""
        for mol_id, expected in EXPECTED_RING_COUNTS.items():
            with self.subTest(molecule=mol_id):
                mol = self.molecules[mol_id]
                self.assertEqual(mol['ring_count'], expected,
                                 '%s: ring_count %d != expected %d'
                                 % (mol_id, mol['ring_count'], expected))
                self.assertLessEqual(mol['ring_count'], 3,
                                     '%s: exceeds 3-ring gate' % mol_id)

    def test_ring_atoms_valid(self):
        """Manifest ring_atoms: >= 3 unique int indices in [0, atom_count)."""
        for mol_id, mol in self.molecules.items():
            with self.subTest(molecule=mol_id):
                ring_atoms = mol['ring_atoms']
                atom_count = mol['atom_count']
                self.assertGreaterEqual(len(ring_atoms), 3,
                                        '%s: < 3 ring_atoms' % mol_id)
                for idx in ring_atoms:
                    self.assertIsInstance(idx, int,
                                          '%s: ring_atoms not int' % mol_id)
                    self.assertFalse(isinstance(idx, bool),
                                     '%s: ring_atoms is bool' % mol_id)
                    self.assertGreaterEqual(idx, 0,
                                            '%s: ring_atoms < 0' % mol_id)
                    self.assertLess(idx, atom_count,
                                    '%s: ring_atoms >= atom_count' % mol_id)
                self.assertEqual(len(ring_atoms), len(set(ring_atoms)),
                                 '%s: ring_atoms not unique' % mol_id)

    def test_manifest_molecules_belong_to_set_a(self):
        """Every molecule's 'set' key equals the parent set id."""
        for mol_id, mol in self.molecules.items():
            self.assertEqual(mol['set'], 'set_a',
                             '%s: set != set_a' % mol_id)


if __name__ == '__main__':
    unittest.main()
