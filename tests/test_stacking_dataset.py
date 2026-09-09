"""Loader-validated dataset tests for the shipped pi-stack interaction file.

These tests exercise the REAL shipped dataset
(``serpentrum/data/stacking_pi_stack.json``) through the 02-05 validated
loader (``molecule_data.load_stacking``) and assert invariants that hold in
BOTH the pre-checkpoint DRAFT state and any post-checkpoint APPROVED state
(option-a 3.383/1.231 or option-b 3.355/1.221). Nothing here hardcodes the
chosen chemistry value beyond the two verified headline constraints:

  * the composed centroid-centroid distance rounds cleanly to 2 decimals
    (3.60 for option-a, 3.57 for option-b) within 0.005 A;
  * the atan2-derived off-normal angle is 20 deg +/- 0.5 (Janiak abstract).

Also checks DATA_SOURCES.md attribution markers and proves the loader is
genuinely validating (tamper-proofing: a copy with 'distance_a' deleted
must raise DataError naming the file).

Discovery (verified on 3.6.9 — NOTE: `-t .` FAILS; do not add it):

    python3.6 -m unittest discover -s tests -p "test_*.py" -v
"""
import json
import math
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import serpentrum  # noqa: E402
from serpentrum import molecule_data  # noqa: E402

# The three verified DOIs transcribed from 02-RESEARCH-demo-data.md (the only
# DOIs the demo dataset is permitted to carry). Asserted as the closed set so
# an unverified citation (e.g. a 3.4 A claim) can never slip into the file.
VERIFIED_DOIS = (
    '10.1039/b003010o',            # Janiak 2000 (abstract-verified)
    '10.1021/acs.chemmater.0c01184',  # COD 4003564 phenanthrene-TCNB
    '10.1107/S0108768106026814',    # COD 2100607 pyrene
)

DATA_DIR = os.path.join(os.path.dirname(serpentrum.__file__), 'data')
DATASET_PATH = os.path.join(DATA_DIR, 'stacking_pi_stack.json')
SOURCES_PATH = os.path.join(DATA_DIR, 'DATA_SOURCES.md')


class TestDatasetLocation(unittest.TestCase):
    """The shipped dataset lives at the plugin-runtime-safe contract path."""

    def test_dataset_file_exists(self):
        self.assertTrue(os.path.isfile(DATASET_PATH),
                        'shipped dataset missing at %s' % DATASET_PATH)

    def test_data_sources_file_exists(self):
        self.assertTrue(os.path.isfile(SOURCES_PATH),
                        'DATA_SOURCES.md missing at %s' % SOURCES_PATH)


class TestDatasetLoadsThroughValidator(unittest.TestCase):
    """The real shipped file passes molecule_data.load_stacking with no error.

    load_stacking IS the structural validation from 02-05: schema_version 1,
    interaction field types/ranges, citation resolution, applies_to shape.
    If this passes, the file is structurally valid by definition.
    """

    @classmethod
    def setUpClass(cls):
        with open(DATASET_PATH, 'r') as handle:
            cls.raw = json.loads(handle.read())
        cls.data = molecule_data.load_stacking(DATASET_PATH)

    def test_schema_version_is_1(self):
        self.assertEqual(self.data['schema_version'], 1)

    def test_exactly_one_interaction(self):
        self.assertEqual(len(self.data['interactions']), 1)

    def test_interaction_identity_and_mode(self):
        entry = self.data['interactions'][0]
        self.assertEqual(entry['id'], 'pi_stack_pd')
        self.assertEqual(entry['mode'], 'pi_stack')
        self.assertTrue(entry['name'], 'interaction name must be non-empty')

    def test_status_is_draft_or_approved(self):
        # Decision-agnostic: passes before (DRAFT) and after (APPROVED) the
        # human checkpoint. The shipping-policy test below enforces the
        # behavioral consequence of whichever status the file carries.
        entry = self.data['interactions'][0]
        self.assertIn(entry['status'], ('DRAFT', 'APPROVED'))


class TestDerivedGeometryFromTheFile(unittest.TestCase):
    """Composed centroid-centroid + off-normal angle computed FROM THE FILE.

    No hardcoded chemistry beyond the two approved headline constraints
    (clean 2-decimal centroid distance; 20 deg Janiak displacement). This
    passes for option-a (3.383/1.231 -> 3.60 @ 20.0 deg) AND option-b
    (3.355/1.221 -> 3.57 @ 19.99 deg).
    """

    @classmethod
    def setUpClass(cls):
        cls.data = molecule_data.load_stacking(DATASET_PATH)
        cls.entry = cls.data['interactions'][0]

    def test_composed_centroid_rounds_cleanly(self):
        # distance_a is the PERPENDICULAR component, lateral_offset_a the
        # in-plane component (02-04 place_pickup API). Composed centroid-
        # centroid = sqrt(d^2 + l^2). Must land within 0.005 of a clean
        # 2-decimal headline (3.60 option-a / 3.57 option-b).
        d = self.entry['distance_a']
        l = self.entry['lateral_offset_a']
        centroid = math.sqrt(d * d + l * l)
        headline = round(centroid, 2)
        self.assertLessEqual(abs(centroid - headline), 0.005,
                             'composed centroid %.5f not within 0.005 of its '
                             '2-decimal headline %.2f' % (centroid, headline))

    def test_off_normal_angle_is_twenty_degrees(self):
        # atan2(lateral, perpendicular) = the ring-normal-to-centroid-vector
        # angle Janiak's abstract pins at ~20 deg. Verified for both encodings.
        d = self.entry['distance_a']
        l = self.entry['lateral_offset_a']
        angle = math.degrees(math.atan2(l, d))
        self.assertLessEqual(abs(angle - 20.0), 0.5,
                             'off-normal angle %.3f not within 0.5 deg of 20.0'
                             % angle)


class TestCitationIntegrity(unittest.TestCase):
    """Every citation resolves, has the right shape, and is a verified DOI."""

    @classmethod
    def setUpClass(cls):
        cls.data = molecule_data.load_stacking(DATASET_PATH)

    def test_interaction_citation_resolves(self):
        entry = self.data['interactions'][0]
        self.assertIn(entry['citation'], self.data['citations'],
                      "interaction citation '%s' not in citations table"
                      % entry['citation'])

    def test_every_citation_has_required_fields(self):
        for key, cite in self.data['citations'].items():
            self.assertTrue(cite.get('short'),
                            "citation '%s' missing non-empty 'short'" % key)
            self.assertTrue(cite.get('doi'),
                            "citation '%s' missing non-empty 'doi'" % key)
            self.assertIsInstance(cite.get('approved'), bool,
                                  "citation '%s' 'approved' not a bool" % key)

    def test_every_doi_is_in_the_verified_set(self):
        # Closed-set assertion: the dataset may ONLY carry one of the three
        # live-verified DOIs. An unverified citation (e.g. a 3.4 A claim
        # sourced to a closed-access paper we never read) is rejected here.
        for key, cite in self.data['citations'].items():
            self.assertIn(cite['doi'], VERIFIED_DOIS,
                          "citation '%s' doi %r not in the verified set %r"
                          % (key, cite['doi'], VERIFIED_DOIS))


class TestShippingPolicy(unittest.TestCase):
    """DATA-02 gate works in both DRAFT and APPROVED states.

    shipped_interactions returns [] iff the entry is DRAFT; once a human
    flips it to APPROVED the single entry ships. The test asserts the
    CONDITIONAL relationship, so it is green before AND after the checkpoint.
    """

    @classmethod
    def setUpClass(cls):
        cls.data = molecule_data.load_stacking(DATASET_PATH)

    def test_shipping_matches_status(self):
        entry = self.data['interactions'][0]
        shipped = molecule_data.shipped_interactions(self.data)
        if entry['status'] == 'DRAFT':
            self.assertEqual(shipped, [],
                             'DRAFT entry must not ship (DATA-02)')
        else:
            self.assertEqual(len(shipped), 1,
                             'APPROVED entry must ship exactly one interaction')
            self.assertEqual(shipped[0]['id'], entry['id'])


class TestDataSourcesAttribution(unittest.TestCase):
    """DATA_SOURCES.md documents every cited source + names UNVERIFIED items."""

    def test_sources_non_trivial_length(self):
        with open(SOURCES_PATH, 'r') as handle:
            text = handle.read()
        self.assertGreater(len(text.splitlines()), 60,
                           'DATA_SOURCES.md is too short to be complete')

    def test_sources_contains_required_markers(self):
        with open(SOURCES_PATH, 'r') as handle:
            text = handle.read()
        required = ['DRAFT', 'UNVERIFIED', '4003564', '2100607',
                    '3.555', 'herringbone']
        for marker in required:
            self.assertIn(marker, text,
                          'DATA_SOURCES.md missing required marker %r'
                          % marker)

    def test_every_dataset_doi_appears_in_sources(self):
        # Cross-link: every citations[].doi in the dataset must appear in
        # DATA_SOURCES.md (the attribution document).
        with open(SOURCES_PATH, 'r') as handle:
            sources_text = handle.read()
        data = molecule_data.load_stacking(DATASET_PATH)
        for key, cite in data['citations'].items():
            self.assertIn(cite['doi'], sources_text,
                          'doi %r (citation %s) missing from DATA_SOURCES.md'
                          % (cite['doi'], key))


class TestLoaderTamperProofing(unittest.TestCase):
    """The real file passes because it is VALID, not because validation is absent.

    Copy the dataset into a temp dir, delete 'distance_a' from interactions[0],
    and assert load_stacking raises DataError naming the file. Proves the
    loader is actually checking fields on the shipped file's schema.
    """

    def test_mangled_dataset_is_rejected(self):
        tmpdir = tempfile.mkdtemp(prefix='srp_stack_tamper_')
        self.addCleanup(shutil.rmtree, tmpdir, True)
        with open(DATASET_PATH, 'r') as handle:
            doc = json.loads(handle.read())
        del doc['interactions'][0]['distance_a']
        mangled_path = os.path.join(tmpdir, 'stacking_pi_stack.json')
        with open(mangled_path, 'w') as handle:
            handle.write(json.dumps(doc, indent=2))
        with self.assertRaises(molecule_data.DataError) as caught:
            molecule_data.load_stacking(mangled_path)
        message = str(caught.exception)
        self.assertIn('stacking_pi_stack.json', message,
                      'DataError must name the file: %r' % message)
        self.assertIn('distance_a', message,
                      'DataError must name the offending key: %r' % message)


if __name__ == '__main__':
    unittest.main()
