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
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from serpentrum import game_engine  # noqa: E402
from serpentrum import generic_stack  # noqa: E402
from serpentrum import hud_logic  # noqa: E402
from serpentrum import molfile  # noqa: E402
from serpentrum import molecule_data  # noqa: E402
from serpentrum import orientation  # noqa: E402
from serpentrum import placement  # noqa: E402
from serpentrum import setloader  # noqa: E402
from serpentrum import setup_logic  # noqa: E402
from serpentrum import spawn  # noqa: E402
from serpentrum import stacking  # noqa: E402

# Fixed step dt (mirrors gui_game.TICK_DT = 0.1; used by the engine
# sections of this chain).
DT = 0.1
# pymol_bridge.BOX_DISPLAY_Z mirrored as a PURE constant (never imported
# — pymol_bridge is viewer-side; the same constant test_phase5_integration
# carries).
DISPLAY_Z = 5.0
# 'right' heading (engine DIRS unit).
HEADING = (1.0, 0.0)

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


class TestGenericPlacementOutcome(unittest.TestCase):
    """SC2 pure half: a ring-bearing upload PLACES at the reused
    approved geometry through resolve() against the overlay, and the
    placed step DECODES to the approved 3.60 A / 3.383 A / 1.231 A (the
    DBG capture-line math, proven purely — the 5.2-09 feel-check
    live-verifies the same decode inside the GUI)."""

    def setUp(self):
        self.record = _load_upload_record()
        parsed = molfile.read_sdf(self.record['file'])[0]
        self.atoms = orientation.edge_on_atoms(
            parsed['elements'], parsed['coords'], self.record['stack_ring'])
        self.records_by_id = {self.record['id']: self.record}
        self.data = molecule_data.load_stacking(
            setloader.default_stacking_path())
        self.overlay = generic_stack.overlay_stacking_data(self.data, True)

    def _resolve_rec(self, stacking_data):
        # The plan 5.2-06 restamp shape, pure layer: consent-aware
        # has_stack_entry over the ANCHORED dataset (the overlay for
        # consent ON; the original dataset for the OFF control).
        return {'id': self.record['id'],
                'molecule_id': self.record['id'],
                'set': self.record['set'],
                'has_stack_entry': generic_stack.has_stack_entry_for(
                    self.record, stacking_data),
                'stack_ring': list(self.record['stack_ring']),
                'atoms': list(self.atoms)}

    def _resolve(self, stacking_data):
        box_min, box_max = setup_logic.BOX_PRESETS['medium']
        return placement.resolve(
            self._resolve_rec(stacking_data), self.records_by_id,
            stacking_data,
            list(self.atoms), self.record['stack_ring'], HEADING,
            [], list(self.atoms),
            box_min, box_max, DISPLAY_Z)

    def test_resolve_places_generic(self):
        outcome = self._resolve(self.overlay)
        self.assertEqual(outcome['status'], 'placed')
        self.assertEqual(outcome['interaction']['id'], 'pi_stack_generic')
        self.assertEqual(outcome['interaction']['distance_a'], 3.383)
        self.assertEqual(outcome['citation_short'], 'Janiak 2000')

    def test_placed_step_decodes_approved_geometry(self):
        # First-capture tail frame (placement.tail_frame over the SAME
        # inputs resolve consumed) vs placed ring frame (stacking.ring_frame
        # over outcome['placed_atoms'] + the record's stack_ring): the DBG
        # capture-line inputs, recomputed PURELY.
        tail_c, tail_n, _tail_ref = placement.tail_frame(
            [], self.records_by_id, list(self.atoms),
            self.record['stack_ring'], HEADING)
        outcome = self._resolve(self.overlay)
        placed_c, placed_n, _pref = stacking.ring_frame(
            _xyz(outcome['placed_atoms']), self.record['stack_ring'])
        step = tuple(placed_c[k] - tail_c[k] for k in range(3))
        distance = math.sqrt(sum(v * v for v in step))
        plane = (step[0] * tail_n[0] + step[1] * tail_n[1] +
                 step[2] * tail_n[2])
        lateral = math.sqrt(distance * distance - plane * plane)
        # The DBG decode: d = 3.60, plane gap = 3.383, lateral = 1.231.
        self.assertAlmostEqual(distance, 3.60, places=3)
        self.assertAlmostEqual(plane, 3.383, places=3)
        self.assertAlmostEqual(lateral, 1.231, places=3)
        # Parallel-displaced: the two ring normals stay parallel.
        dot = sum(placed_n[k] * tail_n[k] for k in range(3))
        self.assertAlmostEqual(abs(dot), 1.0, places=6)

    def test_off_same_record_still_skips(self):
        # Identical geometry chain against the ORIGINAL dataset: the
        # restamp there resolves nothing (interaction_for '__upload__'
        # -> None), so the same record takes the byte-identical OFF skip.
        self.assertEqual(
            self._resolve(self.data),
            {'status': 'skipped', 'code': placement.SKIP_NO_ENTRY})


# ---------------------------------------------------------------------------
# Shared fixture builder + the capture()/drive() controller-seam spec
# (module-local mirrors of test_phase5_integration's s4 helpers — tests
# never import each other; house pattern).
# ---------------------------------------------------------------------------


def _xyz(atoms):
    """(x, y, z) floats from (sym, x, y, z) 4-tuples."""
    return [(float(a[1]), float(a[2]), float(a[3])) for a in atoms]


def _head_atoms(state, head_xy):
    """Origin-centered edge-on head atoms translated to the engine head
    (the 05-11/05-13 controller mirror model)."""
    hx, hy = head_xy
    return [(sym, x + hx, y + hy, z)
            for (sym, x, y, z) in state['atoms']]


def _pickup_seed(state, pid, centroid):
    """One engine pickup record: build_pickup_seed + the record fields
    the consent-ON skip taxonomy consumes (unknown keys survive engine
    copies)."""
    record = state['record']
    seed = spawn.build_pickup_seed(record, pid, centroid, state['atoms'])
    seed['stack_ring'] = list(record['stack_ring'])
    seed['set'] = record['set']
    return seed


def _existing_atoms(engine, captured_id, head_atoms):
    """Locked gate set: head + all segments + OTHER live pickups."""
    out = list(head_atoms)
    for seg in engine.segments:
        out.extend(seg['atoms'])
    for pickup in engine.pickups:
        if (pickup['id'] in engine.live_pickup_ids
                and pickup['id'] != captured_id):
            out.extend(pickup['atoms'])
    return out


def capture(engine, pickup_rec, state):
    """THE controller seam, consent-ON (the 5.2-06 transcription at the
    pure layer): restamp has_stack_entry consent-aware via
    has_stack_entry_for(record, overlay), then placement.resolve in
    skip -> tail -> place -> gate order; attach_segment on 'placed',
    reject_pickup on anything else. Returns the outcome dict.
    """
    resolve_rec = dict(pickup_rec)
    resolve_rec['has_stack_entry'] = generic_stack.has_stack_entry_for(
        state['record'], state['stacking_data'])
    head_atoms = _head_atoms(state, engine.head)
    outcome = placement.resolve(
        resolve_rec, state['records_by_id'], state['stacking_data'],
        head_atoms, state['record']['stack_ring'], engine.heading,
        engine.segments,
        _existing_atoms(engine, pickup_rec['id'], head_atoms),
        engine.box_min, engine.box_max, state['display_z'])
    if outcome['status'] == 'placed':
        engine.attach_segment(pickup_rec['molecule_id'],
                              outcome['ring_centroid_xy'],
                              outcome['placed_atoms'])
    else:
        engine.reject_pickup(pickup_rec['id'], outcome['code'])
    return outcome


def drive(engine, state, max_ticks, stop=None):
    """Step the engine (dt = 0.1), running capture() per ('stacked',)
    event exactly as the GameTab 'stacked' branch does. Optional
    stop(events, engine) breaks. Returns the per-tick capture tuples."""
    frames = []
    for tick in range(max_ticks):
        events = engine.step(DT)
        captures = []
        for event in events:
            if event[0] == 'stacked':
                outcome = capture(engine, event[1], state)
                captures.append((event[1], outcome))
        frames.append({'tick': tick, 'events': events,
                       'captures': captures})
        if stop is not None and stop(events, engine):
            break
    return frames


class TestUploadOnlyWinPath(unittest.TestCase):
    """SC2/SC4 pure half: ONE ring-bearing upload species, cap=2, wins
    an upload-only game under consent ON with the composed placed
    outcome + decorated labeled recap (mirroring the plan 5.2-06/07
    history enrollment: interaction_id 'pi_stack_generic' +
    generic_stack.history_name decoration)."""

    def setUp(self):
        record = _load_upload_record()
        parsed = molfile.read_sdf(record['file'])[0]
        box_min, box_max = setup_logic.BOX_PRESETS['medium']
        self.state = {
            'record': record,
            'records_by_id': {record['id']: record},
            'atoms': orientation.edge_on_atoms(
                parsed['elements'], parsed['coords'],
                record['stack_ring']),
            'stacking_data': generic_stack.overlay_stacking_data(
                molecule_data.load_stacking(
                    setloader.default_stacking_path()), True),
            'box_min': box_min,
            'box_max': box_max,
            'display_z': DISPLAY_Z,
        }

    def test_upload_only_game_wins_under_consent(self):
        state = self.state
        picks = [_pickup_seed(state, 'pick_0001', (4.0, 0.0)),
                 _pickup_seed(state, 'pick_0002', (10.0, 0.0))]
        engine = game_engine.GameEngine(
            head=(0.0, 0.0), heading='right',
            box_min=state['box_min'], box_max=state['box_max'],
            pickups=picks, cap=2)
        frames = drive(engine, state, 400,
                       stop=lambda events, eng: eng.finished)
        captures = [c for frame in frames for c in frame['captures']]
        self.assertEqual(len(captures), 2)
        for (_pickup_rec, outcome) in captures:
            self.assertEqual(outcome['status'], 'placed')
            self.assertEqual(outcome['interaction']['id'],
                             'pi_stack_generic')
        # The win: 'won' at cap on the final capture tick, result won,
        # exact counters, chain complete.
        self.assertIn(('won',), frames[-1]['events'])
        self.assertEqual(engine.result, 'won')
        self.assertEqual(engine.molecules_stacked, 2)
        self.assertEqual(len(engine.segments), 2)
        # Composed stacked_history the way gui_game enrolls stacked
        # entries (plan 5.2-06/07: name decorated by
        # generic_stack.history_name, interaction_id recorded).
        name = state['record']['name']
        history = [{'name': generic_stack.history_name(
                        name, outcome['interaction']),
                    'outcome': 'stacked',
                    'distance_a': outcome['interaction']['distance_a'],
                    'citation_short': outcome['citation_short'],
                    'interaction_id': outcome['interaction']['id']}
                   for (_pickup_rec, outcome) in captures]
        for entry in history:
            self.assertEqual(entry['interaction_id'], 'pi_stack_generic')
            self.assertTrue(entry['name'].endswith(' (generic pi-stack)'),
                            entry['name'])
        # The composed labeled recap group (SC4): one line, '2x', the
        # decorated name, the plane gap, the citation.
        expected = ('stacked 2x %s (generic pi-stack) at 3.38 A plane '
                    'gap [Janiak 2000]' % name)
        self.assertEqual(hud_logic.breakdown_lines(history), [expected])

    def test_recap_distinct_from_dataset_group(self):
        # SC4's distinctness: the same molecule NAME stacked via the
        # shipped dataset entry AND the generic consent entry renders
        # TWO distinct labeled recap groups — generic carries
        # '(generic pi-stack)', both carry '[Janiak 2000]'.
        pd_entry = molecule_data.interaction_for(
            {'set': 'set_a'}, molecule_data.load_stacking(
                setloader.default_stacking_path()))
        name = self.state['record']['name']
        generic = generic_stack.GENERIC_INTERACTION
        history = [
            {'name': name, 'outcome': 'stacked',
             'distance_a': pd_entry['distance_a'],
             'citation_short': 'Janiak 2000',
             'interaction_id': pd_entry['id']},
            {'name': generic_stack.history_name(name, generic),
             'outcome': 'stacked',
             'distance_a': generic['distance_a'],
             'citation_short': 'Janiak 2000',
             'interaction_id': generic['id']},
        ]
        lines = hud_logic.breakdown_lines(history)
        self.assertEqual(lines, [
            'stacked 1x %s at 3.38 A plane gap [Janiak 2000]' % name,
            'stacked 1x %s (generic pi-stack) at 3.38 A plane gap '
            '[Janiak 2000]' % name])


if __name__ == '__main__':
    unittest.main()
