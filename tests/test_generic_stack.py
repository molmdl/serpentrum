"""RED tests for serpentrum/generic_stack.py (plan 5.2-02, STACK-06).

Pins the full behavioral contract of the pure generic-stack module:

* ``GENERIC_INTERACTION`` — the code-borne generic entry, structurally a
  mirror of the ``molecule_data`` entry field rules
  (molecule_data.py:251-330), REUSING the human-approved DATA-02
  Set-A geometry (distance_a 3.383 / lateral_offset_a 1.231, which
  decode to 3.60 A @ 20.0 deg off-normal) VERBATIM. The dataset FILE
  is the shipping contract and is never modified by this feature.
* ``overlay_stacking_data`` — the consent-gated in-memory dataset
  overlay builder: OFF = identity (zero-copy), ON = deepcopy with the
  generic entry appended LAST (first-match order intact, shadows
  nothing), None-safe in both consent states.
* ``history_name`` — the recap-grouping decoration
  ('<molecule> (generic pi-stack)'; dataset entries pass through
  unchanged).
* ``has_stack_entry_for`` — the consent-blind stackability helper:
  None dataset falls back to the load-time record flag; otherwise the
  ANCHORED dataset is the consent carrier and ``interaction_for`` is
  recomputed against it.

Label alphabet is ASCII 'pi-stack' everywhere (EQ-engine-5); the pi
glyph appears only in planning docs.

python3.6 + unittest; pure modules only. No __init__.py here
(plugin-path safety, run_gates gate 1).
"""

import copy
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from serpentrum import generic_stack  # noqa: E402
from serpentrum import molecule_data  # noqa: E402
from serpentrum import setloader  # noqa: E402

DATASET_KEYS = {
    'id', 'mode', 'name', 'distance_a', 'lateral_offset_a',
    'uncertainty_a', 'citation', 'explanation', 'applies_to', 'status',
}


def _load_real_dataset():
    """Load the shipped stacking dataset (the shipping contract)."""
    return molecule_data.load_stacking(setloader.default_stacking_path())


class TestGenericInteraction(unittest.TestCase):
    """Structural mirror of the molecule_data entry field rules."""

    def test_required_fields_exact_values(self):
        entry = generic_stack.GENERIC_INTERACTION
        self.assertEqual(set(entry.keys()), DATASET_KEYS)
        self.assertEqual(entry['id'], 'pi_stack_generic')
        self.assertEqual(entry['mode'], 'pi_stack')
        self.assertEqual(entry['distance_a'], 3.383)
        self.assertEqual(entry['lateral_offset_a'], 1.231)
        self.assertIsNone(entry['uncertainty_a'])
        self.assertEqual(entry['citation'], 'janiak2000')
        self.assertEqual(entry['status'], 'APPROVED')
        # ONLY the upload sentinel — demo sets must stay unreachable.
        self.assertEqual(entry['applies_to'], {'sets': ['__upload__']})

    def test_name_label(self):
        self.assertEqual(
            generic_stack.GENERIC_INTERACTION['name'],
            'generic pi-stack (illustrative geometry - user-approved)')

    def test_explanation_honesty(self):
        explanation = generic_stack.GENERIC_INTERACTION['explanation']
        self.assertIsInstance(explanation, str)
        for token in ('illustrative', 'user-approved', '3.60', 'not measured'):
            self.assertIn(token, explanation)
        self.assertNotIn('\n', explanation)

    def test_ascii_only(self):
        entry = generic_stack.GENERIC_INTERACTION
        for key in ('id', 'name', 'explanation'):
            for ch in entry[key]:
                self.assertLess(
                    ord(ch), 128,
                    'non-ASCII char %r in %s' % (ch, key))

    def test_geometry_encodes_approved_ideal(self):
        # The REUSED numbers must still decode to the approved
        # 3.60 A @ 20.0 deg off-normal (DATA-02).
        entry = generic_stack.GENERIC_INTERACTION
        d = entry['distance_a']
        lat = entry['lateral_offset_a']
        self.assertAlmostEqual(math.sqrt(d * d + lat * lat), 3.60, places=3)
        self.assertAlmostEqual(
            math.degrees(math.atan2(lat, d)), 20.0, places=2)

    def test_citation_resolves_in_shipped_dataset(self):
        # The generic entry cites ONLY an already-approved citation.
        data = _load_real_dataset()
        self.assertIn('janiak2000', data['citations'])
        citation = data['citations']['janiak2000']
        self.assertEqual(citation['short'], 'Janiak 2000')
        self.assertTrue(citation['approved'])


class TestOverlayStackingData(unittest.TestCase):
    """Consent-gated in-memory overlay builder semantics."""

    def test_off_returns_same_object(self):
        data = _load_real_dataset()
        snapshot = copy.deepcopy(data)
        result = generic_stack.overlay_stacking_data(data, False)
        self.assertIs(result, data)
        # Deep-equality: the OFF path must not touch the dataset.
        self.assertEqual(data, snapshot)

    def test_on_returns_fresh_copy_with_entry_last(self):
        data = _load_real_dataset()
        original_len = len(data['interactions'])
        result = generic_stack.overlay_stacking_data(data, True)
        self.assertIsNot(result, data)
        self.assertEqual(result['interactions'][-1]['id'], 'pi_stack_generic')
        self.assertEqual(result['interactions'][:-1], data['interactions'])
        self.assertEqual(len(result['interactions']), original_len + 1)
        # Original dataset unchanged (no mutation of the anchored data).
        self.assertEqual(len(data['interactions']), original_len)

    def test_on_entry_is_not_the_module_constant(self):
        data = _load_real_dataset()
        result = generic_stack.overlay_stacking_data(data, True)
        appended = result['interactions'][-1]
        self.assertIsNot(appended, generic_stack.GENERIC_INTERACTION)
        # Mutating the appended copy must leave the constant intact.
        appended['distance_a'] = 9.999
        appended['applies_to']['sets'].append('set_a')
        self.assertEqual(generic_stack.GENERIC_INTERACTION['distance_a'], 3.383)
        self.assertEqual(
            generic_stack.GENERIC_INTERACTION['applies_to'],
            {'sets': ['__upload__']})

    def test_none_safe(self):
        self.assertIsNone(generic_stack.overlay_stacking_data(None, True))
        self.assertIsNone(generic_stack.overlay_stacking_data(None, False))


class TestHistoryName(unittest.TestCase):
    """Recap-grouping name decoration (SC4 mechanism)."""

    def test_generic_decorated(self):
        self.assertEqual(
            generic_stack.history_name(
                'benzene', generic_stack.GENERIC_INTERACTION),
            'benzene (generic pi-stack)')

    def test_dataset_entry_unchanged(self):
        self.assertEqual(
            generic_stack.history_name('benzene', {'id': 'pi_stack_pd'}),
            'benzene')


class TestHasStackEntryFor(unittest.TestCase):
    """Consent-blind stackability helper (pure half of restamping)."""

    def test_none_dataset_falls_back(self):
        record = {'set': '__upload__', 'has_stack_entry': False}
        self.assertFalse(generic_stack.has_stack_entry_for(record, None))
        record = {'set': 'set_a', 'has_stack_entry': True}
        self.assertTrue(generic_stack.has_stack_entry_for(record, None))

    def test_upload_original_dataset_false(self):
        data = _load_real_dataset()
        record = {'set': '__upload__'}
        self.assertFalse(generic_stack.has_stack_entry_for(record, data))

    def test_upload_overlay_true(self):
        data = _load_real_dataset()
        overlay = generic_stack.overlay_stacking_data(data, True)
        record = {'set': '__upload__'}
        self.assertTrue(generic_stack.has_stack_entry_for(record, overlay))

    def test_demo_identical_both_ways(self):
        data = _load_real_dataset()
        overlay = generic_stack.overlay_stacking_data(data, True)
        record = {'set': 'set_a'}
        self.assertTrue(generic_stack.has_stack_entry_for(record, data))
        self.assertTrue(generic_stack.has_stack_entry_for(record, overlay))


if __name__ == '__main__':
    unittest.main()
