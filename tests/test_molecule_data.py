"""Validated demo-data loader tests: manifest + stacking v1 schemas (STACK-02).

Every rejection case from the plan matrix is proven, including the
py3.6 bool-is-int trap (isinstance(True, int) is True — integer validators
must reject bools explicitly) and the research's literal error message
("stacking.json interaction 0: missing key 'distance_a'") reproduced
VERBATIM.

Synthetic tmpdir documents ONLY: the shipped data files under
serpentrum/data/demos/ are a later plan's deliverable and must stay
pristine — no test here creates anything under serpentrum/data/. The
dummy phenol.xyz in each tmpdir is an existence-check target only;
its content is irrelevant to the loader.

Discovery command (verified on 3.6.9 — NOTE: `-t .` FAILS on python3.6
with a non-package start dir; do not add it):

    python3.6 -m unittest discover -s tests -p "test_*.py" -v
"""
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from serpentrum import molecule_data  # noqa: E402

# The two EXACT research-schema documents (02-RESEARCH-pure-core.md R6;
# 02-RESEARCH-demo-data.md content mapped into this schema). distance_a
# 3.4 exists to reproduce the COMMITTED dimer2 fixture for testing; it is
# NOT a shipped chemistry claim (DATA-02: the human approval track pins
# the shipping value later; the demo-data research recommends 3.6).
VALID_MANIFEST = {
    'schema_version': 1,
    'sets': [
        {
            'id': 'set_a',
            'name': 'Aromatic pi-stack',
            'molecules': [
                {
                    'id': 'phenol',
                    'name': 'Phenol',
                    'file': 'phenol.xyz',
                    'source_db': 'PubChem',
                    'source_id': 'CID 996',
                    'atom_count': 13,
                    'charge': 0,
                    'ring_count': 1,
                    'ring_atoms': [0, 1, 2, 3, 4, 5],
                    'set': 'set_a',
                },
            ],
        },
    ],
}

VALID_STACKING = {
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
            'status': 'DRAFT',
        },
    ],
    'citations': {
        'janiak2000': {
            'short': 'Janiak 2000',
            'doi': '10.1039/b003010o',
            'approved': False,
        },
    },
}


def _copy(doc):
    """Deep-copy a document literal (json round-trip — no shared mutation)."""
    return json.loads(json.dumps(doc))


class MoleculeDataTestCase(unittest.TestCase):
    """Shared tmpdir/writer helpers; one tmpdir per test via addCleanup."""

    def _tmpdir(self):
        path = tempfile.mkdtemp(prefix='srp_moldata_')
        self.addCleanup(shutil.rmtree, path, True)
        return path

    def _write(self, dirname, name, obj):
        """Dump obj as JSON (indent=2) into dirname/name; return the path."""
        path = os.path.join(dirname, name)
        with open(path, 'w') as handle:
            handle.write(json.dumps(obj, indent=2))
        return path

    def _write_text(self, dirname, name, text):
        """Write raw text (for malformed-JSON and dummy .xyz files)."""
        path = os.path.join(dirname, name)
        with open(path, 'w') as handle:
            handle.write(text)
        return path

    def _manifest_dir(self):
        """Tmpdir holding the dummy phenol.xyz the manifest references."""
        dirname = self._tmpdir()
        self._write_text(dirname, 'phenol.xyz', 'dummy\n')
        return dirname

    def _manifest_path(self, dirname, doc=None):
        doc = _copy(VALID_MANIFEST) if doc is None else doc
        return self._write(dirname, 'manifest.json', doc)

    def _stacking_path(self, dirname, doc=None):
        doc = _copy(VALID_STACKING) if doc is None else doc
        return self._write(dirname, 'stacking.json', doc)

    def _assert_data_error(self, loader, path, fragments):
        """Assert loader(path) raises DataError containing every fragment."""
        with self.assertRaises(molecule_data.DataError) as caught:
            loader(path)
        message = str(caught.exception)
        for fragment in fragments:
            self.assertIn(fragment, message,
                          'expected %r in DataError message %r'
                          % (fragment, message))
        return message


class TestValidDocuments(MoleculeDataTestCase):
    """The v1 research schemas load and return the parsed dicts."""

    def test_valid_manifest_loads(self):
        data = molecule_data.load_manifest(self._manifest_path(self._manifest_dir()))
        self.assertEqual(data['schema_version'], 1)
        self.assertEqual(data['sets'][0]['id'], 'set_a')
        molecule = data['sets'][0]['molecules'][0]
        self.assertEqual(molecule['id'], 'phenol')
        self.assertEqual(molecule['atom_count'], 13)
        self.assertEqual(molecule['ring_atoms'], [0, 1, 2, 3, 4, 5])

    def test_valid_stacking_loads(self):
        data = molecule_data.load_stacking(self._stacking_path(self._tmpdir()))
        self.assertEqual(data['schema_version'], 1)
        interaction = data['interactions'][0]
        self.assertEqual(interaction['id'], 'pi_stack_pd')
        self.assertEqual(interaction['mode'], 'pi_stack')
        self.assertEqual(interaction['distance_a'], 3.4)
        self.assertIsNone(interaction['uncertainty_a'])
        self.assertEqual(interaction['status'], 'DRAFT')
        self.assertEqual(data['citations']['janiak2000']['doi'],
                         '10.1039/b003010o')


class TestManifestRejections(MoleculeDataTestCase):
    """Each structural violation raises DataError: file + entry + problem."""

    def test_rejects_schema_version_2(self):
        doc = _copy(VALID_MANIFEST)
        doc['schema_version'] = 2
        path = self._manifest_path(self._manifest_dir(), doc)
        self._assert_data_error(molecule_data.load_manifest, path,
                                ['manifest.json', 'schema_version'])

    def test_rejects_schema_version_bool(self):
        doc = _copy(VALID_MANIFEST)
        doc['schema_version'] = True
        path = self._manifest_path(self._manifest_dir(), doc)
        self._assert_data_error(molecule_data.load_manifest, path,
                                ['manifest.json', 'schema_version'])

    def test_missing_atom_count_exact_message(self):
        doc = _copy(VALID_MANIFEST)
        del doc['sets'][0]['molecules'][0]['atom_count']
        path = self._manifest_path(self._manifest_dir(), doc)
        message = self._assert_data_error(
            molecule_data.load_manifest, path,
            ["manifest.json set 0 molecule 0: missing key 'atom_count'"])
        self.assertEqual(message,
                         "manifest.json set 0 molecule 0: missing key 'atom_count'")

    def test_rejects_atom_count_bad_type(self):
        doc = _copy(VALID_MANIFEST)
        doc['sets'][0]['molecules'][0]['atom_count'] = 'x'
        path = self._manifest_path(self._manifest_dir(), doc)
        self._assert_data_error(
            molecule_data.load_manifest, path,
            ['manifest.json set 0 molecule 0', "key 'atom_count'"])

    def test_rejects_atom_count_bool_trap(self):
        # isinstance(True, int) is True on py3.6 — the loader must not accept
        # atom_count: true (this is why _is_int excludes bool explicitly).
        doc = _copy(VALID_MANIFEST)
        doc['sets'][0]['molecules'][0]['atom_count'] = True
        path = self._manifest_path(self._manifest_dir(), doc)
        self._assert_data_error(
            molecule_data.load_manifest, path,
            ['manifest.json set 0 molecule 0', "key 'atom_count'"])

    def test_rejects_ring_atoms_too_few(self):
        doc = _copy(VALID_MANIFEST)
        doc['sets'][0]['molecules'][0]['ring_atoms'] = [0, 1]
        path = self._manifest_path(self._manifest_dir(), doc)
        self._assert_data_error(
            molecule_data.load_manifest, path,
            ['manifest.json set 0 molecule 0', 'at least 3'])

    def test_rejects_ring_atoms_out_of_range(self):
        # atom_count is 13, so index 13 is the first out-of-range value.
        doc = _copy(VALID_MANIFEST)
        doc['sets'][0]['molecules'][0]['ring_atoms'] = [0, 1, 13]
        path = self._manifest_path(self._manifest_dir(), doc)
        self._assert_data_error(
            molecule_data.load_manifest, path,
            ['manifest.json set 0 molecule 0',
             'ring_atoms index 13 out of range [0, 13)'])

    def test_rejects_ring_atoms_duplicates(self):
        doc = _copy(VALID_MANIFEST)
        doc['sets'][0]['molecules'][0]['ring_atoms'] = [0, 0, 1, 2, 3, 4]
        path = self._manifest_path(self._manifest_dir(), doc)
        self._assert_data_error(
            molecule_data.load_manifest, path,
            ['manifest.json set 0 molecule 0',
             'ring_atoms indices must be unique'])

    def test_rejects_ring_atoms_bool_entry(self):
        doc = _copy(VALID_MANIFEST)
        doc['sets'][0]['molecules'][0]['ring_atoms'] = [0, 1, 2, True, 4, 5]
        path = self._manifest_path(self._manifest_dir(), doc)
        self._assert_data_error(
            molecule_data.load_manifest, path,
            ['manifest.json set 0 molecule 0', 'must be integers'])

    def test_rejects_ring_count_zero(self):
        doc = _copy(VALID_MANIFEST)
        doc['sets'][0]['molecules'][0]['ring_count'] = 0
        path = self._manifest_path(self._manifest_dir(), doc)
        self._assert_data_error(
            molecule_data.load_manifest, path,
            ['manifest.json set 0 molecule 0', "key 'ring_count'"])

    def test_rejects_mismatched_set(self):
        doc = _copy(VALID_MANIFEST)
        doc['sets'][0]['molecules'][0]['set'] = 'set_b'
        path = self._manifest_path(self._manifest_dir(), doc)
        self._assert_data_error(
            molecule_data.load_manifest, path,
            ['manifest.json set 0 molecule 0', "key 'set'", "'set_a'"])

    def test_rejects_duplicate_molecule_id_across_sets(self):
        doc = _copy(VALID_MANIFEST)
        clone = _copy(VALID_MANIFEST['sets'][0]['molecules'][0])
        clone['set'] = 'set_b'
        doc['sets'].append(
            {'id': 'set_b', 'name': 'Second set', 'molecules': [clone]})
        path = self._manifest_path(self._manifest_dir(), doc)
        self._assert_data_error(
            molecule_data.load_manifest, path,
            ['manifest.json set 1 molecule 0', "duplicate molecule id 'phenol'"])

    def test_rejects_missing_molecule_file(self):
        doc = _copy(VALID_MANIFEST)
        doc['sets'][0]['molecules'][0]['file'] = 'nope.xyz'
        path = self._manifest_path(self._manifest_dir(), doc)
        self._assert_data_error(
            molecule_data.load_manifest, path,
            ['manifest.json set 0 molecule 0', "'nope.xyz'", 'not found'])

    def test_rejects_invalid_json_text(self):
        path = self._write_text(self._manifest_dir(), 'manifest.json',
                                '{"schema_version": 1, oops}')
        self._assert_data_error(molecule_data.load_manifest, path,
                                ['manifest.json', 'invalid JSON'])

    def test_rejects_non_object_top_level(self):
        path = self._write_text(self._manifest_dir(), 'manifest.json', '[]')
        self._assert_data_error(molecule_data.load_manifest, path,
                                ['manifest.json', 'top level must be a JSON object'])


class TestStackingRejections(MoleculeDataTestCase):
    """Each structural violation raises DataError: file + entry + problem."""

    def test_missing_distance_exact_research_message(self):
        # The research's literal example, reproduced VERBATIM.
        doc = _copy(VALID_STACKING)
        del doc['interactions'][0]['distance_a']
        path = self._stacking_path(self._tmpdir(), doc)
        with self.assertRaises(molecule_data.DataError) as caught:
            molecule_data.load_stacking(path)
        self.assertEqual(str(caught.exception),
                         "stacking.json interaction 0: missing key 'distance_a'")

    def test_rejects_distance_zero(self):
        doc = _copy(VALID_STACKING)
        doc['interactions'][0]['distance_a'] = 0.0
        path = self._stacking_path(self._tmpdir(), doc)
        self._assert_data_error(
            molecule_data.load_stacking, path,
            ['stacking.json interaction 0', "key 'distance_a'"])

    def test_rejects_distance_above_ceiling(self):
        doc = _copy(VALID_STACKING)
        doc['interactions'][0]['distance_a'] = 11.0
        path = self._stacking_path(self._tmpdir(), doc)
        self._assert_data_error(
            molecule_data.load_stacking, path,
            ['stacking.json interaction 0', "key 'distance_a'"])

    def test_rejects_distance_bool_trap(self):
        doc = _copy(VALID_STACKING)
        doc['interactions'][0]['distance_a'] = True
        path = self._stacking_path(self._tmpdir(), doc)
        self._assert_data_error(
            molecule_data.load_stacking, path,
            ['stacking.json interaction 0', "key 'distance_a'"])

    def test_rejects_negative_lateral_offset(self):
        doc = _copy(VALID_STACKING)
        doc['interactions'][0]['lateral_offset_a'] = -0.5
        path = self._stacking_path(self._tmpdir(), doc)
        self._assert_data_error(
            molecule_data.load_stacking, path,
            ['stacking.json interaction 0', "key 'lateral_offset_a'"])

    def test_rejects_negative_uncertainty(self):
        doc = _copy(VALID_STACKING)
        doc['interactions'][0]['uncertainty_a'] = -1.0
        path = self._stacking_path(self._tmpdir(), doc)
        self._assert_data_error(
            molecule_data.load_stacking, path,
            ['stacking.json interaction 0', "key 'uncertainty_a'"])

    def test_rejects_lowercase_status(self):
        # Case-sensitive on purpose: 'draft' is a typo, not a status.
        doc = _copy(VALID_STACKING)
        doc['interactions'][0]['status'] = 'draft'
        path = self._stacking_path(self._tmpdir(), doc)
        self._assert_data_error(
            molecule_data.load_stacking, path,
            ['stacking.json interaction 0', "'DRAFT'", "'APPROVED'"])

    def test_rejects_unknown_citation(self):
        doc = _copy(VALID_STACKING)
        doc['interactions'][0]['citation'] = 'nope'
        path = self._stacking_path(self._tmpdir(), doc)
        self._assert_data_error(
            molecule_data.load_stacking, path,
            ['stacking.json interaction 0', "unknown citation 'nope'"])

    def test_rejects_citation_entry_missing_doi(self):
        doc = _copy(VALID_STACKING)
        del doc['citations']['janiak2000']['doi']
        path = self._stacking_path(self._tmpdir(), doc)
        self._assert_data_error(
            molecule_data.load_stacking, path,
            ["stacking.json citation 'janiak2000'", "missing key 'doi'"])

    def test_rejects_citation_approved_not_bool(self):
        doc = _copy(VALID_STACKING)
        doc['citations']['janiak2000']['approved'] = 'yes'
        path = self._stacking_path(self._tmpdir(), doc)
        self._assert_data_error(
            molecule_data.load_stacking, path,
            ["stacking.json citation 'janiak2000'", "key 'approved'"])

    def test_rejects_empty_applies_to_sets(self):
        doc = _copy(VALID_STACKING)
        doc['interactions'][0]['applies_to']['sets'] = []
        path = self._stacking_path(self._tmpdir(), doc)
        self._assert_data_error(
            molecule_data.load_stacking, path,
            ['stacking.json interaction 0', "'applies_to'"])

    def test_rejects_duplicate_interaction_id(self):
        doc = _copy(VALID_STACKING)
        doc['interactions'].append(_copy(doc['interactions'][0]))
        path = self._stacking_path(self._tmpdir(), doc)
        self._assert_data_error(
            molecule_data.load_stacking, path,
            ['stacking.json interaction 1',
             "duplicate interaction id 'pi_stack_pd'"])

    def test_rejects_invalid_json_text(self):
        path = self._write_text(self._tmpdir(), 'stacking.json', 'not json at all')
        self._assert_data_error(molecule_data.load_stacking, path,
                                ['stacking.json', 'invalid JSON'])


class TestPathContract(MoleculeDataTestCase):
    """Loaders take the PATH of the JSON file; base_dir is derived from it."""

    def test_molecule_files_resolve_against_manifest_dir(self):
        nested = os.path.join(self._tmpdir(), 'nested')
        os.makedirs(nested)
        self._write_text(nested, 'phenol.xyz', 'dummy\n')
        path = self._write(nested, 'manifest.json', _copy(VALID_MANIFEST))
        # The reference resolves against the manifest's OWN directory
        # (dirname of the passed path), not the caller's cwd.
        data = molecule_data.load_manifest(path)
        self.assertEqual(data['sets'][0]['molecules'][0]['file'], 'phenol.xyz')

    def test_directory_argument_is_a_loud_error(self):
        dirname = self._tmpdir()
        with self.assertRaises(molecule_data.DataError):
            molecule_data.load_manifest(dirname)
        with self.assertRaises(molecule_data.DataError):
            molecule_data.load_stacking(dirname)


class TestShippedInteractions(MoleculeDataTestCase):
    """DATA-02 code side: shipped_interactions returns APPROVED only."""

    def test_draft_dataset_ships_nothing(self):
        # The research dataset as written is DRAFT — nothing ships yet.
        data = molecule_data.load_stacking(self._stacking_path(self._tmpdir()))
        self.assertEqual(molecule_data.shipped_interactions(data), [])

    def test_approved_flip_ships_entry(self):
        # The human track's DRAFT -> APPROVED flip happens IN THE DATA FILE;
        # the loader accepts the flipped document and the accessor ships it.
        doc = _copy(VALID_STACKING)
        doc['interactions'][0]['status'] = 'APPROVED'
        data = molecule_data.load_stacking(self._stacking_path(self._tmpdir(), doc))
        shipped = molecule_data.shipped_interactions(data)
        self.assertEqual(len(shipped), 1)
        self.assertEqual(shipped[0]['id'], 'pi_stack_pd')
        self.assertEqual(shipped[0]['distance_a'], 3.4)

    def test_mixed_statuses_keep_file_order(self):
        doc = _copy(VALID_STACKING)
        approved_first = _copy(doc['interactions'][0])
        approved_first['id'] = 'stack_alpha'
        approved_first['status'] = 'APPROVED'
        draft_middle = _copy(doc['interactions'][0])
        draft_middle['id'] = 'stack_bravo'  # stays DRAFT
        approved_last = _copy(doc['interactions'][0])
        approved_last['id'] = 'stack_charlie'
        approved_last['status'] = 'APPROVED'
        doc['interactions'] = [approved_first, draft_middle, approved_last]
        data = molecule_data.load_stacking(self._stacking_path(self._tmpdir(), doc))
        shipped = molecule_data.shipped_interactions(data)
        self.assertEqual([entry['id'] for entry in shipped],
                         ['stack_alpha', 'stack_charlie'])


class TestInteractionFor(MoleculeDataTestCase):
    """STACK-03 input: set-based lookup, first match wins, else None."""

    def test_set_a_matches_pi_stack_entry(self):
        data = molecule_data.load_stacking(self._stacking_path(self._tmpdir()))
        entry = molecule_data.interaction_for({'set': 'set_a'}, data)
        self.assertIsNotNone(entry)
        self.assertEqual(entry['id'], 'pi_stack_pd')

    def test_unmatched_set_returns_none(self):
        data = molecule_data.load_stacking(self._stacking_path(self._tmpdir()))
        self.assertIsNone(molecule_data.interaction_for({'set': 'set_b'}, data))

    def test_first_match_wins(self):
        # Two interactions both applicable to set_a: the EARLIER file-order
        # entry is returned (deterministic, no "best match" guessing).
        doc = _copy(VALID_STACKING)
        second = _copy(doc['interactions'][0])
        second['id'] = 'pi_stack_second'
        doc['interactions'].append(second)
        data = molecule_data.load_stacking(self._stacking_path(self._tmpdir(), doc))
        entry = molecule_data.interaction_for({'set': 'set_a'}, data)
        self.assertEqual(entry['id'], 'pi_stack_pd')


class TestShippedShapeProof(MoleculeDataTestCase):
    """Round trip: BOTH research documents load together from one tmpdir."""

    def test_distance_flows_from_the_file(self):
        """The placement distance the later integration test builds on is
        READ from stacking.json — never a code constant (STACK-02). The
        committed dimer2 fixture (fragment 2 = fragment 1 + (0, 0, 3.4))
        reproduces at exactly the value the file carries; its DRAFT status
        means the human approval track still owns the shipping decision
        (DATA-02). No serpentrum/data/ file is created or touched here."""
        dirname = self._tmpdir()
        self._write_text(dirname, 'phenol.xyz', 'dummy\n')
        manifest = molecule_data.load_manifest(
            self._write(dirname, 'manifest.json', _copy(VALID_MANIFEST)))
        stacking = molecule_data.load_stacking(
            self._write(dirname, 'stacking.json', _copy(VALID_STACKING)))
        molecule = manifest['sets'][0]['molecules'][0]
        entry = molecule_data.interaction_for(molecule, stacking)
        self.assertIsNotNone(entry)
        distance_a = entry['distance_a']  # read FROM the loaded data file
        self.assertEqual(distance_a, 3.4)
        self.assertEqual(entry['lateral_offset_a'], 0.0)
        self.assertEqual(entry['citation'], 'janiak2000')
        # DRAFT entries are fully usable for tests but ship nothing.
        self.assertEqual(molecule_data.shipped_interactions(stacking), [])


if __name__ == '__main__':
    unittest.main()
