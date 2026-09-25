"""Phase 5.2 end-to-end PURE integration chain test (plan 5.2-08, STACK-06).

Proves the COMPOSED Phase 5.2 chain at the pure layer — mirroring how
5.1-06 proved its chain without GUI (headless dialog assertions are
impossible, 01-05; the GUI wiring verdicts belong to the 5.2-09
feel-check):

    schema (5.2-01: generic_stack_consent absent = OFF; bool-typed when
      explicit)
  -> overlay (5.2-02: consent-gated in-memory dataset + generic entry)
  -> taxonomy (5.2-03: SKIP_NO_ENTRY OFF / stackable SKIP_GENERIC_NO_RING ON)
  -> placement (resolve -> placed at the REUSED approved geometry +
     DBG capture-line decode)
  -> notes + recap (5.2-04: C1/variant/consent lines + SC4 labeled group)

All fixtures are REAL: the shipped stacking dataset, the shipped demo
set, and REAL upload-parsed records (a shipped demo SDF reused AS an
upload — the test_hud_content.py real-upload pin precedent: set
'__upload__', has_stack_entry=False, stack_ring present for benign
ring-bearing species). Consent-ON resolve_rec shapes mirror the plan
5.2-06 GUI restamp (has_stack_entry_for(record, overlay)) because the
GUI restamp itself is human-verify territory; the SPIN that stamps it
is pure and pinned here.

The OFF chain assertions coexist with the ON chain (explicit False and
absent-key paths): the pre-existing pins in test_placement /
test_hud_content / test_phase5_integration remain the primary OFF
contract — this file re-proves the COMPOSED path.

python3.6 + unittest; pure modules only (setup_logic / molecule_data /
setloader / generic_stack / placement / hud_logic). No __init__.py here
(plugin-path safety, run_gates gate 1). Discovery:

    python3.6 -m unittest discover -s tests -p "test_phase52_integration.py" -v
"""

import copy
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from serpentrum import generic_stack  # noqa: E402
from serpentrum import hud_logic  # noqa: E402
from serpentrum import molecule_data  # noqa: E402
from serpentrum import placement  # noqa: E402
from serpentrum import setloader  # noqa: E402
from serpentrum import setup_logic  # noqa: E402
from serpentrum import spawn  # noqa: E402

# Fixed step dt (mirrors gui_game.TICK_DT = 0.1; used by the engine
# sections of this chain).
DT = 0.1

# Exact contract literals (5.2-04 landed wording; pinned here as the
# COMPOSED contract — the per-builder pins live in test_hud_content.py).
C1_NOTE = ('this set has no stacking entries - demonstration mode: '
           'practice steering; only a crash ends the run')
VARIANT_NOTE = ('no molecule has a planar aromatic 6-ring for generic '
                'pi-stack - demonstration mode: practice steering; '
                'only a crash ends the run')
CONSENT_NOTE = ('generic pi-stack enabled: illustrative geometry - '
                'user-approved [Janiak 2000]')

_BENZENE_SDF = os.path.join(setloader.package_data_dir(), 'benzene.sdf')


def _load_upload_record(path=_BENZENE_SDF):
    """One real upload-parsed record (shipped SDF reused AS an upload).

    The test_hud_content.py real-upload pin precedent: setloader's
    honest '__upload__' keying — has_stack_entry=False, set
    '__upload__', stack_ring present for ring-bearing species.
    """
    records, errors = setloader.load_upload(
        path, stacking_path=setloader.default_stacking_path())
    assert errors == [], errors
    assert len(records) == 1, records
    record = records[0]
    assert record['set'] == '__upload__', record['set']
    assert record['has_stack_entry'] is False
    assert 'stack_ring' in record, 'shipped benzene is ring-bearing'
    return record


class TestConsentSchemaChain(unittest.TestCase):
    """SC1 pure half: absent key -> OFF; round-trip True; non-bool
    rejects; the documented seed re-pin (crc32 whole-dict semantics)."""

    def test_absent_key_merges_to_off_and_validates(self):
        # A setup file written before 5.2 (NO consent key) loads, merges
        # to OFF, and validates clean (the Phase-8 Save/Load BUTTONS
        # inherit this wiring for free — the 5.1-06 resolution).
        legacy = dict(setup_logic.DEFAULTS)
        legacy.pop('generic_stack_consent')
        self.assertEqual(len(legacy), len(setup_logic.DEFAULTS) - 1)
        loaded = setup_logic.load_setup(
            json.dumps(legacy, sort_keys=True, indent=2))
        self.assertNotIn('generic_stack_consent', loaded)
        merged = setup_logic.merge_defaults(loaded)
        self.assertIs(merged['generic_stack_consent'], False)
        errors, _warnings = setup_logic.validate(merged)
        self.assertEqual(errors, [])

    def test_consent_true_round_trips_and_validates(self):
        setup = setup_logic.new_setup()
        setup['generic_stack_consent'] = True
        text = setup_logic.save_setup(setup)
        loaded = setup_logic.load_setup(text)
        merged = setup_logic.merge_defaults(loaded)
        errors, _warnings = setup_logic.validate(merged)
        self.assertEqual(errors, [])
        self.assertIs(merged['generic_stack_consent'], True)

    def test_non_bool_consent_flags_in_merged_chain(self):
        merged = setup_logic.merge_defaults({'generic_stack_consent': 'yes'})
        errors, _warnings = setup_logic.validate(merged)
        self.assertEqual(errors,
                         ["generic_stack_consent 'yes' must be a boolean"])

    def test_consent_toggle_reseeds_spawn(self):
        # Documentation pin (5.1 precedent): crc32-hashes the WHOLE
        # setup dict, so two setups differing ONLY in the consent flag
        # deterministically produce two different seeds. Documented
        # ACCEPTED side effect, NOT a bug.
        off = setup_logic.merge_defaults({'generic_stack_consent': False})
        on = setup_logic.merge_defaults({'generic_stack_consent': True})
        self.assertNotEqual(spawn.seed_from_setup(off),
                            spawn.seed_from_setup(on))
        self.assertEqual(spawn.seed_from_setup(off),
                         spawn.seed_from_setup(dict(off)))


class TestOverlayTaxonomyChain(unittest.TestCase):
    """SC3 pure half over the REAL dataset + real upload-parsed records:
    OFF skips identically to today; ON stackable for ring-bearing
    uploads, SKIP_GENERIC_NO_RING for ring-less; demo side-effect free.
    """

    def setUp(self):
        self.data = molecule_data.load_stacking(
            setloader.default_stacking_path())
        self.overlay = generic_stack.overlay_stacking_data(self.data, True)
        self.demo_records, errors = setloader.load_demo_set(
            set_id='set_a',
            stacking_path=setloader.default_stacking_path())
        self.assertEqual(errors, [])
        self.upload = _load_upload_record()

    def test_off_upload_skips_no_entry(self):
        # The composed OFF path: load-time record + ORIGINAL dataset.
        self.assertEqual(
            placement.resolve_skip(self.upload, self.data),
            placement.SKIP_NO_ENTRY)

    def test_on_ring_bearing_upload_stackable(self):
        # The plan 5.2-06 restamp shape: consent-aware has_stack_entry
        # recomputed against the OVERLAY, which admits ring-bearing
        # uploads to the ring/response step.
        restamped = dict(self.upload)
        restamped['has_stack_entry'] = generic_stack.has_stack_entry_for(
            self.upload, self.overlay)
        self.assertIs(restamped['has_stack_entry'], True)
        self.assertIsNone(placement.resolve_skip(restamped, self.overlay))

    def test_on_ringless_upload_skips_generic(self):
        # Ring-less upload under consent ON: the generic-entry match
        # selects the SKIP_GENERIC_NO_RING sibling (same ring-check
        # step, unchanged taxonomy ORDER).
        ringless = copy.deepcopy(self.upload)
        del ringless['stack_ring']
        ringless['has_stack_entry'] = True
        self.assertEqual(
            placement.resolve_skip(ringless, self.overlay),
            placement.SKIP_GENERIC_NO_RING)

    def test_demo_records_identical_both_datasets(self):
        # A shipped set_a record resolves the SHIPPED entry in both the
        # original and overlay datasets (first-match order shadows
        # nothing — the generic entry only names '__upload__').
        record = self.demo_records[0]
        original = molecule_data.interaction_for(record, self.data)
        overlayed = molecule_data.interaction_for(record, self.overlay)
        self.assertEqual(original['id'], 'pi_stack_pd')
        self.assertEqual(overlayed['id'], 'pi_stack_pd')

    def test_overlay_demo_side_effect_free(self):
        # EVERY demo record: the overlay cannot leak a generic placement
        # into the demo sets (the generic entry names only '__upload__').
        for record in self.demo_records:
            self.assertEqual(
                molecule_data.interaction_for(record, self.overlay),
                molecule_data.interaction_for(record, self.data))

    def test_stack_mode_note_real_upload_variant_pair(self):
        # The composed C1/variant note pair over the REAL upload record
        # (5.2-04 consent-aware predicate, over the shipped pigment of
        # truth): OFF = the byte-identical C1 line; ON = suppressed for
        # ring-bearing uploads, variant for ring-less.
        self.assertEqual(hud_logic.stack_mode_note([self.upload], False),
                         C1_NOTE)
        self.assertIs(hud_logic.stack_mode_note([self.upload], True), None)
        ringless = copy.deepcopy(self.upload)
        del ringless['stack_ring']
        self.assertEqual(hud_logic.stack_mode_note([ringless], True),
                         VARIANT_NOTE)


class TestNotesChain(unittest.TestCase):
    """The 5.2-04 notes pair over the REAL upload record (OFF C1 pin /
    ON suppress / ON-ringless variant / consent-note pair) — the
    pure-layer half of the once-per-run HUD surface."""

    def setUp(self):
        self.upload = _load_upload_record()

    def test_off_upload_only_note_is_c1_line(self):
        self.assertEqual(hud_logic.stack_mode_note([self.upload], False),
                         C1_NOTE)

    def test_on_ring_bearing_upload_only_note_suppressed(self):
        self.assertIs(hud_logic.stack_mode_note([self.upload], True), None)

    def test_on_ringless_upload_only_note_is_variant(self):
        ringless = copy.deepcopy(self.upload)
        del ringless['stack_ring']
        self.assertEqual(hud_logic.stack_mode_note([ringless], True),
                         VARIANT_NOTE)

    def test_consent_note_pair(self):
        self.assertIs(hud_logic.generic_consent_note(False), None)
        self.assertEqual(hud_logic.generic_consent_note(True),
                         CONSENT_NOTE)


if __name__ == '__main__':
    unittest.main()
