"""setloader tests: demo-set manifest verification + upload gating (SC1, DATA-03).

Two test groups mirror the plan's behavior cases:
  - TestDemoPath  (cases 1-6): manifest cross-verification, gate exclusion,
    set filtering, and has_stack_entry keying via interaction_for.
  - TestUploadPath (cases 7-12): extension routing, per-record gating,
    '__upload__' sentinel keying, multi-record SDF splitting, error formats.

Synthetic tmpdir documents ONLY (test_molecule_data.py precedent): no test
creates anything under serpentrum/data/. SDF fixture bytes come from
tests/fixtures/molfile/ (committed in 03-02); single-record files are
produced via molfile.write_sdf_text from the multi-record fixture's parsed
records, so the declared atom_count/charge/ring_count match parsed reality.

Discovery (verified on python3.6.9 -- do NOT add -t .):

    python3.6 -m unittest discover -s tests -p "test_*.py" -v
"""
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from serpentrum import molfile  # noqa: E402
from serpentrum import setloader  # noqa: E402  -- RED: module does not exist yet

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURES = os.path.join(ROOT, 'tests', 'fixtures', 'molfile')

# Parse the multi-record fixture once for record extraction (benzene = record 0,
# naphthalene = record 1). write_sdf_text round-trips these into single-record
# files the demo-tree helper writes into each tmpdir.
_MULTI = molfile.read_sdf(os.path.join(FIXTURES, 'benzene_naphthalene.sdf'))
BENZENE_RECORD = _MULTI[0]       # 12 atoms, charge 0, ring_count 1
NAPHTHALENE_RECORD = _MULTI[1]   # 18 atoms, charge 0, ring_count 2

# Parsed benzene_noh record (6 atoms, no H -- fails the gate).
BENZENE_NOH_RECORD = molfile.read_sdf(
    os.path.join(FIXTURES, 'benzene_noh.sdf'))[0]

# Base manifest: benzene + naphthalene in set_a, declarations matching the
# parsed reality (benzene 12/0/1, naphthalene 18/0/2). ring_atoms lists ONE
# ring's carbon indices per the manifest schema (>= 3 unique ints).
BASE_MANIFEST = {
    'schema_version': 1,
    'sets': [
        {
            'id': 'set_a',
            'name': 'Aromatic pi-stack',
            'molecules': [
                {
                    'id': 'benzene',
                    'name': 'Benzene',
                    'file': 'benzene.sdf',
                    'source_db': 'PubChem',
                    'source_id': 'CID 241',
                    'atom_count': 12,
                    'charge': 0,
                    'ring_count': 1,
                    'ring_atoms': [0, 1, 2, 3, 4, 5],
                    'set': 'set_a',
                },
                {
                    'id': 'naphthalene',
                    'name': 'Naphthalene',
                    'file': 'naphthalene.sdf',
                    'source_db': 'PubChem',
                    'source_id': 'CID 931',
                    'atom_count': 18,
                    'charge': 0,
                    'ring_count': 2,
                    'ring_atoms': [0, 1, 2, 3, 4, 5],
                    'set': 'set_a',
                },
            ],
        },
    ],
}

# Minimal stacking dataset: one APPROVED interaction applying to set_a only.
# interaction_for matches on set id regardless of status, but APPROVED mirrors
# the shipped data for realism.
BASE_STACKING = {
    'schema_version': 1,
    'interactions': [
        {
            'id': 'pi_stack_pd',
            'mode': 'pi_stack',
            'name': 'pi-pi stacking (parallel-displaced)',
            'distance_a': 3.4,
            'lateral_offset_a': 0.0,
            'uncertainty_a': None,
            'citation': 'janiak2000',
            'explanation': 'Aromatic rings stack face-to-face, slightly offset.',
            'applies_to': {'sets': ['set_a']},
            'status': 'APPROVED',
        },
    ],
    'citations': {
        'janiak2000': {
            'short': 'Janiak 2000',
            'doi': '10.1039/b003010o',
            'approved': True,
        },
    },
}


def _copy(doc):
    """Deep-copy a document literal (json round-trip -- no shared mutation)."""
    return json.loads(json.dumps(doc))


class SetLoaderTestCase(unittest.TestCase):
    """Shared tmpdir/writer helpers; one tmpdir per test via addCleanup."""

    def _tmpdir(self):
        path = tempfile.mkdtemp(prefix='srp_setloader_')
        self.addCleanup(shutil.rmtree, path, True)
        return path

    def _write_json(self, dirname, name, obj):
        path = os.path.join(dirname, name)
        with open(path, 'w') as handle:
            handle.write(json.dumps(obj, indent=2))
        return path

    def _write_sdf(self, dirname, name, record):
        path = os.path.join(dirname, name)
        with open(path, 'w') as handle:
            handle.write(molfile.write_sdf_text(record))
        return path

    def _write_text(self, dirname, name, text):
        path = os.path.join(dirname, name)
        with open(path, 'w') as handle:
            handle.write(text)
        return path

    def _demo_tree(self, manifest=None, records=None):
        """Build a tmpdir with manifest.json + SDF files; return data_dir.

        manifest: manifest dict (default BASE_MANIFEST). Each molecule's
          'file' is looked up in <records> to write the SDF bytes.
        records: dict mapping file_name -> molfile record dict to write.
          Default: benzene + naphthalene single-record extracts.
        """
        dirname = self._tmpdir()
        manifest = _copy(BASE_MANIFEST) if manifest is None else _copy(manifest)
        if records is None:
            records = {'benzene.sdf': BENZENE_RECORD,
                       'naphthalene.sdf': NAPHTHALENE_RECORD}
        for molecule_set in manifest['sets']:
            for molecule in molecule_set['molecules']:
                fname = molecule['file']
                if fname in records:
                    self._write_sdf(dirname, fname, records[fname])
        self._write_json(dirname, 'manifest.json', manifest)
        return dirname

    def _stacking_path(self, stacking=None):
        """Write a tmpdir stacking.json; return its path."""
        stacking = _copy(BASE_STACKING) if stacking is None else _copy(stacking)
        dirname = self._tmpdir()
        return self._write_json(dirname, 'stacking.json', stacking)


class TestDemoPath(SetLoaderTestCase):
    """Behavior cases 1-6: demo-set loading with manifest verification.

    load_demo_set(data_dir, set_id, stacking_path) parses + gates every
    manifest molecule's SDF and VERIFIES the manifest declarations
    (atom_count, charge, ring_count) against the parsed reality. Any
    mismatch excludes the molecule with an error naming its id.
    """

    # --- Case 1: demo happy path ---

    def test_demo_happy_path(self):
        data_dir = self._demo_tree()
        stacking_path = self._stacking_path()
        records, errors = setloader.load_demo_set(
            data_dir, 'set_a', stacking_path)
        self.assertEqual(errors, [])
        self.assertEqual(len(records), 2)

        benzene = records[0]
        self.assertEqual(benzene['id'], 'benzene')
        self.assertEqual(benzene['name'], 'Benzene')
        self.assertEqual(benzene['set'], 'set_a')
        self.assertEqual(benzene['source'], 'demo')
        self.assertEqual(benzene['record_index'], 0)
        self.assertEqual(benzene['atom_count'], 12)
        self.assertEqual(benzene['charge'], 0)
        self.assertEqual(benzene['ring_count'], 1)
        self.assertTrue(benzene['has_explicit_h'])
        self.assertTrue(benzene['has_stack_entry'])
        self.assertEqual(benzene['elements'],
                         ['C', 'C', 'C', 'C', 'C', 'C',
                          'H', 'H', 'H', 'H', 'H', 'H'])
        self.assertEqual(benzene['warnings'], [])
        self.assertIn('ring_atoms', benzene)
        self.assertGreaterEqual(len(benzene['ring_atoms']), 3)
        self.assertTrue(os.path.isfile(benzene['file']))

        naph = records[1]
        self.assertEqual(naph['id'], 'naphthalene')
        self.assertEqual(naph['name'], 'Naphthalene')
        self.assertEqual(naph['set'], 'set_a')
        self.assertEqual(naph['source'], 'demo')
        self.assertEqual(naph['record_index'], 0)
        self.assertEqual(naph['atom_count'], 18)
        self.assertEqual(naph['charge'], 0)
        self.assertEqual(naph['ring_count'], 2)
        self.assertTrue(naph['has_explicit_h'])
        self.assertTrue(naph['has_stack_entry'])
        self.assertIn('ring_atoms', naph)
        self.assertTrue(os.path.isfile(naph['file']))

    # --- Case 2: ring_count mismatch ---

    def test_ring_count_mismatch_excludes_molecule(self):
        manifest = _copy(BASE_MANIFEST)
        manifest['sets'][0]['molecules'][1]['ring_count'] = 3  # parsed is 2
        data_dir = self._demo_tree(manifest=manifest)
        stacking_path = self._stacking_path()
        records, errors = setloader.load_demo_set(
            data_dir, 'set_a', stacking_path)
        self.assertEqual([r['id'] for r in records], ['benzene'])
        self.assertEqual(len(errors), 1)
        self.assertIn('naphthalene', errors[0])
        self.assertIn('ring_count', errors[0])
        self.assertIn('3', errors[0])
        self.assertIn('2', errors[0])

    # --- Case 3: atom_count + charge mismatches ---

    def test_atom_count_mismatch_excludes_molecule(self):
        manifest = _copy(BASE_MANIFEST)
        manifest['sets'][0]['molecules'][0]['atom_count'] = 13  # parsed is 12
        data_dir = self._demo_tree(manifest=manifest)
        stacking_path = self._stacking_path()
        records, errors = setloader.load_demo_set(
            data_dir, 'set_a', stacking_path)
        self.assertEqual([r['id'] for r in records], ['naphthalene'])
        self.assertEqual(len(errors), 1)
        self.assertIn('benzene', errors[0])
        self.assertIn('atom_count', errors[0])

    def test_charge_mismatch_excludes_molecule(self):
        manifest = _copy(BASE_MANIFEST)
        manifest['sets'][0]['molecules'][0]['charge'] = -1  # parsed is 0
        data_dir = self._demo_tree(manifest=manifest)
        stacking_path = self._stacking_path()
        records, errors = setloader.load_demo_set(
            data_dir, 'set_a', stacking_path)
        self.assertEqual([r['id'] for r in records], ['naphthalene'])
        self.assertEqual(len(errors), 1)
        self.assertIn('benzene', errors[0])
        self.assertIn('charge', errors[0])

    # --- Case 4: demo multi-record file rejected ---

    def test_demo_multi_record_file_rejected(self):
        manifest = {
            'schema_version': 1,
            'sets': [
                {
                    'id': 'set_a',
                    'name': 'Aromatic pi-stack',
                    'molecules': [
                        {
                            'id': 'multi',
                            'name': 'Multi',
                            'file': 'multi.sdf',
                            'source_db': 'test',
                            'source_id': 'test',
                            'atom_count': 12,
                            'charge': 0,
                            'ring_count': 1,
                            'ring_atoms': [0, 1, 2, 3, 4, 5],
                            'set': 'set_a',
                        },
                    ],
                },
            ],
        }
        dirname = self._tmpdir()
        # Copy the raw multi-record fixture (2 records).
        shutil.copy(
            os.path.join(FIXTURES, 'benzene_naphthalene.sdf'),
            os.path.join(dirname, 'multi.sdf'))
        self._write_json(dirname, 'manifest.json', manifest)
        stacking_path = self._stacking_path()
        records, errors = setloader.load_demo_set(
            dirname, 'set_a', stacking_path)
        self.assertEqual(records, [])
        self.assertEqual(len(errors), 1)
        self.assertIn('must be single-record', errors[0])
        self.assertIn('multi', errors[0])

    # --- Case 5: demo file failing the gate ---

    def test_demo_gate_failing_molecule_excluded(self):
        manifest = {
            'schema_version': 1,
            'sets': [
                {
                    'id': 'set_a',
                    'name': 'Aromatic pi-stack',
                    'molecules': [
                        {
                            'id': 'benzene_noh',
                            'name': 'Benzene No H',
                            'file': 'benzene_noh.sdf',
                            'source_db': 'test',
                            'source_id': 'test',
                            'atom_count': 6,
                            'charge': 0,
                            'ring_count': 1,
                            'ring_atoms': [0, 1, 2, 3, 4, 5],
                            'set': 'set_a',
                        },
                    ],
                },
            ],
        }
        data_dir = self._demo_tree(
            manifest=manifest,
            records={'benzene_noh.sdf': BENZENE_NOH_RECORD})
        stacking_path = self._stacking_path()
        records, errors = setloader.load_demo_set(
            data_dir, 'set_a', stacking_path)
        self.assertEqual(records, [])
        self.assertEqual(len(errors), 1)
        self.assertIn('hydrogens', errors[0])

    # --- Case 6: set filter + has_stack_entry keying ---

    def test_set_filter_returns_only_requested_set(self):
        manifest = {
            'schema_version': 1,
            'sets': [
                {
                    'id': 'set_a',
                    'name': 'Set A',
                    'molecules': [_copy(
                        BASE_MANIFEST['sets'][0]['molecules'][0])],
                },
                {
                    'id': 'set_b',
                    'name': 'Set B',
                    'molecules': [
                        {
                            'id': 'naphthalene',
                            'name': 'Naphthalene',
                            'file': 'naphthalene.sdf',
                            'source_db': 'PubChem',
                            'source_id': 'CID 931',
                            'atom_count': 18,
                            'charge': 0,
                            'ring_count': 2,
                            'ring_atoms': [0, 1, 2, 3, 4, 5],
                            'set': 'set_b',
                        },
                    ],
                },
            ],
        }
        data_dir = self._demo_tree(manifest=manifest)
        stacking_path = self._stacking_path()  # covers only set_a
        records, errors = setloader.load_demo_set(
            data_dir, 'set_b', stacking_path)
        self.assertEqual(errors, [])
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['id'], 'naphthalene')
        self.assertEqual(records[0]['set'], 'set_b')
        self.assertEqual(records[0]['source'], 'demo')
        self.assertFalse(records[0]['has_stack_entry'])


if __name__ == '__main__':
    unittest.main()
