"""stack_ring carry-through pins (locked decisions 5 + 7; plan 05-08).

setloader computes ``stack_ring = molfile.ring_cycle(record)`` at load
time via ``_build_record`` for DEMO records (plan 05-08) and -- since
2026-09-20c (fix G2, upload edge-on) -- for UPLOAD records too, WHEN the
molecule has a canonical PLANAR 6-ring (``_upload_stack_ring``; ring-less
or non-planar-ring uploads stay ring-less and render as stored). The
upload stack_ring is a DISPLAY field: the STACK-03 capture skip keys on
the missing dataset entry (locked decision 7, the '__upload__' set
sentinel -> has_stack_entry=False), NEVER on the absent ring. Placement
(05-05) and tail frames (05-11/05-13) index placed atoms 1:1 by
``stack_ring`` -- the indices alignment contract: the record's
``elements``/parsed ``coords`` order is the same order the ring indices
were computed against.

Zero stubs; real shipped data (load_demo_set on the shipped Set A,
upload fixtures from tests/fixtures/molfile/ -- the test_setloader.py
precedent).

Discovery (verified on python3.6.9 -- do NOT add -t .):

    python3.6 -m unittest tests.test_setloader_stack_ring -v
"""
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from serpentrum import molfile  # noqa: E402
from serpentrum import orientation  # noqa: E402
from serpentrum import setloader  # noqa: E402
from serpentrum import stacking  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURES = os.path.join(ROOT, 'tests', 'fixtures', 'molfile')

# Canonical ordered 6-cycles, probe-verified (05-RESEARCH-core-integration.md
# ring_extraction_spec) and pinned by plan 05-01's test_ring_cycle.py.
EXPECTED_STACK_RINGS = {
    'benzene': (0, 1, 3, 5, 4, 2),
    'naphthalene': (0, 1, 3, 7, 6, 2),
    'anthracene': (0, 1, 5, 3, 2, 4),
    'phenanthrene': (0, 1, 3, 5, 4, 2),
    'biphenyl': (0, 2, 6, 10, 8, 4),
}


class TestDemoStackRing(unittest.TestCase):
    """Demo records carry the canonical 6-ring cycle at load time."""

    @classmethod
    def setUpClass(cls):
        cls.records, cls.errors = setloader.load_demo_set(
            stacking_path=setloader.default_stacking_path())
        cls.by_id = dict((r['id'], r) for r in cls.records)

    def test_shipped_set_loads_with_zero_errors(self):
        self.assertEqual(self.errors, [])
        self.assertEqual(sorted(self.by_id),
                         sorted(EXPECTED_STACK_RINGS))

    def test_every_record_has_six_int_stack_ring(self):
        for record in self.records:
            self.assertIn('stack_ring', record)
            ring = record['stack_ring']
            self.assertIsInstance(ring, list)
            self.assertEqual(len(ring), 6)
            self.assertEqual(len(set(ring)), 6)
            for index in ring:
                self.assertIsInstance(index, int)

    def test_stack_ring_matches_canonical_tuple_per_molecule(self):
        for mol_id, expected in EXPECTED_STACK_RINGS.items():
            self.assertIn(mol_id, self.by_id)
            self.assertEqual(tuple(self.by_id[mol_id]['stack_ring']),
                             expected)

    def test_stack_ring_indices_align_with_parsed_coords(self):
        # Alignment contract: stack_ring indices index 1:1 into the parsed
        # coords/elements of record['file'] (same record, one parse).
        for record in self.records:
            parsed = molfile.read_sdf(record['file'])
            self.assertEqual(len(parsed), 1)
            coords = parsed[0]['coords']
            elements = parsed[0]['elements']
            self.assertEqual(len(coords), len(elements))
            self.assertEqual(len(coords), record['atom_count'])
            for index in record['stack_ring']:
                self.assertLess(index, len(coords))
            self.assertGreaterEqual(len(coords),
                                    max(record['stack_ring']) + 1)

    def test_ring_atoms_and_stack_ring_coexist(self):
        # ring_atoms (the sorted 2-core from the manifest) still ships
        # ALONGSIDE stack_ring -- both keys coexist on demo records.
        for record in self.records:
            self.assertIn('ring_atoms', record)
            self.assertIn('stack_ring', record)
            self.assertTrue(len(record['ring_atoms']) >= 6)
            # Every stack_ring atom is a ring atom (subset of the 2-core).
            core = set(record['ring_atoms'])
            for index in record['stack_ring']:
                self.assertIn(index, core)


class TestUploadStackRing(unittest.TestCase):
    """2026-09-20c fix G2 (upload edge-on): upload records carry
    stack_ring WHEN a canonical PLANAR 6-ring is resolvable at load
    (``setloader._upload_stack_ring``); ring-less uploads stay ring-less.
    The STACK-03 skip keying (locked decision 7) is untouched: the skip
    keys on the missing dataset entry, never on the ring."""

    def _tmpdir(self):
        path = tempfile.mkdtemp(prefix='srp_stack_ring_test_')
        self.addCleanup(shutil.rmtree, path, True)
        return path

    def _write_sdf(self, dirname, name, record):
        path = os.path.join(dirname, name)
        with open(path, 'w') as handle:
            handle.write(molfile.write_sdf_text(record))
        return path

    def test_single_record_upload_carries_stack_ring(self):
        # Build a minimal single-record SDF (benzene -- a molecule WITH
        # a planar 6-ring) in a tempdir: since fix G2 the ring is
        # computed at load (the edge-on enabler), while the skip policy
        # is untouched.
        source = molfile.read_sdf(
            os.path.join(FIXTURES, 'benzene_naphthalene.sdf'))
        path = self._write_sdf(self._tmpdir(), 'benzene_upload.sdf',
                               source[0])
        records, errors = setloader.load_upload(
            path, setloader.default_stacking_path())
        self.assertEqual(errors, [])
        self.assertEqual(len(records), 1)
        self.assertIn('stack_ring', records[0])
        ring = records[0]['stack_ring']
        self.assertEqual(len(ring), 6)
        self.assertEqual(len(set(ring)), 6)
        for index in ring:
            self.assertIsInstance(index, int)
        # The ring is PROVABLY planar over the record's own file coords
        # (the _upload_stack_ring planarity contract).
        parsed = molfile.read_sdf(records[0]['file'])
        self.assertEqual(len(parsed), 1)
        stacking.ring_frame(parsed[0]['coords'],
                            records[0]['stack_ring'])
        # Skip-policy keying intact: __upload__ matches no interaction.
        self.assertEqual(records[0]['set'], '__upload__')
        self.assertFalse(records[0]['has_stack_entry'])

    def test_multi_record_split_upload_carries_stack_ring(self):
        path = os.path.join(FIXTURES, 'benzene_naphthalene.sdf')
        records, errors = setloader.load_upload(
            path, setloader.default_stacking_path())
        self.assertEqual(errors, [])
        self.assertEqual(len(records), 2)
        self.addCleanup(shutil.rmtree,
                        os.path.dirname(records[0]['file']), True)
        for record in records:
            self.assertIn('stack_ring', record)
            self.assertEqual(record['set'], '__upload__')
            self.assertFalse(record['has_stack_entry'])
            # Indices alignment contract holds per SPLIT file: the
            # ring_frame proof indexes the split file's coords 1:1.
            parsed = molfile.read_sdf(record['file'])
            self.assertEqual(len(parsed), 1)
            stacking.ring_frame(parsed[0]['coords'],
                                record['stack_ring'])

    def test_mol2_upload_carries_stack_ring(self):
        path = os.path.join(FIXTURES, 'benzene.mol2')
        records, errors = setloader.load_upload(
            path, setloader.default_stacking_path())
        self.assertEqual(errors, [])
        self.assertEqual(len(records), 1)
        self.assertIn('stack_ring', records[0])
        ring = records[0]['stack_ring']
        self.assertEqual(len(ring), 6)
        self.assertEqual(len(set(ring)), 6)
        for index in ring:
            self.assertIsInstance(index, int)
        # Alignment + planarity over the mol2 record's own coords.
        parsed = molfile.read_mol2(records[0]['file'])
        stacking.ring_frame(parsed[0]['coords'], ring)

    def test_ringless_upload_stays_ringless(self):
        # Methane (no rings) passes the gate but has no 6-ring to
        # canonicalize: stack_ring stays OMITTED and the molecule
        # renders in its as-stored orientation (fix G2 fallback).
        path = os.path.join(FIXTURES, 'methane.sdf')
        records, errors = setloader.load_upload(
            path, setloader.default_stacking_path())
        self.assertEqual(errors, [])
        self.assertEqual(len(records), 1)
        self.assertNotIn('stack_ring', records[0])
        self.assertEqual(records[0]['set'], '__upload__')


class TestUploadEdgeOn(unittest.TestCase):
    """fix G2/G3 (2026-09-20c, upload edge-on): an edge-on m16 is
    produced from a planar-6-ring upload record via the SAME pure
    machinery the demo seams use; ring-less or non-planar-ring uploads
    fall back to None (as-stored orientation, documented)."""

    def test_planar_ring_upload_produces_edge_on_m16(self):
        path = os.path.join(FIXTURES, 'benzene.mol2')
        records, errors = setloader.load_upload(
            path, setloader.default_stacking_path())
        self.assertEqual(errors, [])
        record = records[0]
        self.assertIn('stack_ring', record)
        parsed = molfile.read_mol2(record['file'])[0]
        m16 = orientation.edge_on_m16(
            parsed['elements'], parsed['coords'], record['stack_ring'])
        self.assertEqual(len(m16), 16)
        for value in m16:
            self.assertIsInstance(value, float)
        # The canonicalization is real: the raw fixture lies FLAT in xy
        # (z-span 0.0) while the edge-on pose stands the ring up to its
        # in-plane diameter — the exact transform _pickup_m16 /
        # reload_head build from it (matrix_rt(R_edge, t, pre)).
        raw_zs = [c[2] for c in parsed['coords']]
        self.assertEqual(max(raw_zs), min(raw_zs))  # fixture: flat
        edges = orientation.edge_on_atoms(
            parsed['elements'], parsed['coords'], record['stack_ring'])
        edge_zs = [a[3] for a in edges]
        self.assertAlmostEqual(
            max(edge_zs) - min(edge_zs), 4.314, places=3)

    def test_ringless_upload_edge_on_fallback_is_none(self):
        parsed = molfile.read_sdf(os.path.join(FIXTURES, 'methane.sdf'))
        self.assertIsNone(setloader._upload_stack_ring(parsed[0]))

    def test_nonplanar_ring_upload_edge_on_fallback_is_none(self):
        # A non-planar 6-ring (benzene with one ring atom pulled 0.5 A
        # off the plane — past the 0.15 A tolerance) must NOT produce a
        # stack_ring: the GUI seams would raise in edge_on_* otherwise.
        source = molfile.read_sdf(
            os.path.join(FIXTURES, 'benzene_naphthalene.sdf'))[0]
        record = dict(source)
        coords = list(source['coords'])
        coords[0] = (coords[0][0], coords[0][1], coords[0][2] + 0.5)
        record['coords'] = coords
        self.assertIsNone(setloader._upload_stack_ring(record))


if __name__ == '__main__':
    unittest.main()
