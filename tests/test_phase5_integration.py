"""Phase-5 pure integration chain (plan 05-12): win / crash / refuse / skip
/ un-finish / sweep-consistent stacking / spawn determinism, end-to-end on
REAL shipped data with ZERO stubs.

This file is the executable specification of the GUI 'stacked' controller
seam that plan 05-13 codes up (the 02-14 pattern: tests/test_integration_
pure_core.py proved the pure seams before the bridge/xtb plans consumed
them). Every module in the chain is the shipped product code:

    RECORDS   setloader.load_demo_set(stacking_path = default_stacking_path())
              -> real set_a records WITH stack_ring (05-08 merged)
    GEOMETRY  molfile.read_sdf + orientation.edge_on_atoms (05-01/05-02)
    SPAWN     spawn.PickupSpawner fixed seed (05-03)
    ENGINE    game_engine.GameEngine stepped at dt = 0.1 (02-06/02-10/02-13
              + the 05-04 reject-after-won un-finish)
    POLICY    placement.resolve (05-05) -- skip check -> tail frame ->
              attempt_place -> gate, then attach_segment OR reject_pickup

The module-level ``capture()`` helper mirrors 05-RESEARCH-core-integration.md
"engine_contracts" EXACTLY (and matches the plan-05-13 coding spec for
GameTab._handle_stack_event clause-by-clause): placement.resolve performs
skip check -> tail frame -> attempt_place -> gate; on 'placed' the
controller calls engine.attach_segment(molecule_id, ring_centroid_xy,
placed_atoms); on 'skipped'/'refused' it ALWAYS calls engine.reject_pickup(
pickup_id, outcome_code) because the capture already incremented the
counters (the un-finish fix lives on the reject path). The resolve() call
takes the gate box from the engine itself (engine.box_min/box_max) plus the
display_z parameter, exactly like 05-13's implementation.

Existing-atom set for the gate (locked decision in plan 05-05): head atoms
+ ALL segment atoms + OTHER live pickups' atoms (the captured pickup's own
atoms are excluded). The head-atom mirror is pure: origin-centered edge-on
atoms translated to the engine head position (the 05-11/05-13 controller
mirror model; extent-centering is a pymol_bridge display nuance only --
relative stacking geometry is invariant under it).

Scenario 1 hand-places pickup centroids on the head's straight path. The
plan allows "use the spawner or hand-placed centroids on a straight line,
spacing > 6 A"; the spawner's seeded laterals (up to +/-6.0 A) can exceed
the 3.0 A capture radius, which would hang a no-turn scripted run -- exact
capture timing is load-bearing for the counter pins. The spawner itself is
exercised for BYTE-IDENTICAL restart determinism in scenario 8 against a
scenario-1-shaped call sequence (the GAME-07 restart contract).

python3.6 only (%-formatting, no f-strings). tests/ has NO __init__.py (the
dev plugin path IS the repo root). Discovery:

    python3.6 -m unittest tests.test_phase5_integration -v

No serpentrum module is modified by this file; a scenario exposing an
engine/placement defect is a STOP-and-report condition, never a silent
workaround.
"""
import math
import os
import sys
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from serpentrum import game_engine  # noqa: E402
from serpentrum import molfile  # noqa: E402
from serpentrum import molecule_data  # noqa: E402
from serpentrum import orientation  # noqa: E402
from serpentrum import placement  # noqa: E402
from serpentrum import setloader  # noqa: E402
from serpentrum import setup_logic  # noqa: E402
from serpentrum import spawn  # noqa: E402
from serpentrum import stacking  # noqa: E402
from serpentrum.game_engine import GameEngine  # noqa: E402

DT = 0.1
DISPLAY_Z = 5.0  # pymol_bridge.BOX_DISPLAY_Z (passed as a PURE parameter)
DELTA = 1e-6

# ---------------------------------------------------------------------------
# Shared fixture builder + the capture() controller-seam spec
# ---------------------------------------------------------------------------


def build_fixture():
    """records + records_by_id + atoms_by_id (edge-on'd) + stacking_data.

    REAL shipped data: setloader.load_demo_set against the default stacking
    dataset (errors must be empty -- any setloader/manifest/SDF regression
    fails this chain loudly), molfile.read_sdf + orientation.edge_on_atoms
    per record for the origin-centered molecule atoms (the same pipeline
    plan 05-10 landed at materialization).
    """
    stacking_path = setloader.default_stacking_path()
    records, errors = setloader.load_demo_set(stacking_path=stacking_path)
    assert errors == [], errors
    assert len(records) == 5, 'set_a ships exactly 5 species'
    stacking_data = molecule_data.load_stacking(stacking_path)
    atoms_by_id = {}
    for record in records:
        parsed = molfile.read_sdf(record['file'])[0]
        atoms_by_id[record['id']] = orientation.edge_on_atoms(
            parsed['elements'], parsed['coords'], record['stack_ring'])
    return {
        'records': records,
        'records_by_id': dict((record['id'], record) for record in records),
        'atoms_by_id': atoms_by_id,
        'stacking_data': stacking_data,
        'box_min': setup_logic.BOX_PRESETS['medium'][0],  # (-55.0, -55.0)
        'box_max': setup_logic.BOX_PRESETS['medium'][1],  # ( 55.0,  55.0)
        # (values follow BOX_PRESETS live; comments restated for the
        # 2026-09-20 owner-approved cap-10 re-test enlargement)
        'display_z': DISPLAY_Z,
        'head_id': 'benzene',
    }


def head_atom_fn(state, head_xy):
    """The pure head-atom mirror: origin-centered edge-on atoms translated
    to the engine head position (05-11/05-13 controller model)."""
    hx, hy = head_xy
    return [(sym, x + hx, y + hy, z)
            for (sym, x, y, z) in state['atoms_by_id'][state['head_id']]]


def pickup_seed(state, molecule_id, pid, centroid):
    """One engine pickup record the way 05-13 seeds it: spawn.build_pickup_
    seed + the record fields the controller's skip taxonomy needs
    ('stack_ring' / 'has_stack_entry' / 'set' survive engine copies as
    unknown keys)."""
    record = state['records_by_id'][molecule_id]
    seed = spawn.build_pickup_seed(record, pid, centroid,
                                   state['atoms_by_id'][molecule_id])
    seed['stack_ring'] = list(record['stack_ring'])
    seed['has_stack_entry'] = record['has_stack_entry']
    seed['set'] = record['set']
    return seed


def _existing_atoms(engine, captured_id, head_atoms):
    """Locked decision (05-05): head + all segments + OTHER live pickups."""
    out = list(head_atoms)
    for seg in engine.segments:
        out.extend(seg['atoms'])
    for pickup in engine.pickups:
        if (pickup['id'] in engine.live_pickup_ids
                and pickup['id'] != captured_id):
            out.extend(pickup['atoms'])
    return out


def capture(engine, pickup_rec, state):
    """THE controller seam (05-RESEARCH engine_contracts 'stacked' branch).

    Order (plan 05-13 codes exactly this): skip check -> tail frame ->
    attempt_place -> gate (all inside placement.resolve), then
    attach_segment(molecule_id, ring_centroid_xy, placed_atoms) on success
    OR reject_pickup(pickup_id, outcome_code) on skip/refuse. Returns the
    placement outcome dict.
    """
    head_atoms = head_atom_fn(state, engine.head)
    outcome = placement.resolve(
        pickup_rec, state['records_by_id'], state['stacking_data'],
        head_atoms, state['records_by_id'][state['head_id']]['stack_ring'],
        engine.heading, engine.segments,
        _existing_atoms(engine, pickup_rec['id'], head_atoms),
        engine.box_min, engine.box_max, state['display_z'])
    if outcome['status'] == 'placed':
        engine.attach_segment(pickup_rec['molecule_id'],
                              outcome['ring_centroid_xy'],
                              outcome['placed_atoms'])
    else:
        engine.reject_pickup(pickup_rec['id'], outcome['code'])
    return outcome


def _xyz(atoms):
    """(x, y, z) triples from (sym, x, y, z) 4-tuples."""
    return [(a[1], a[2], a[3]) for a in atoms]


def ring_centroid_3d(atoms, stack_ring):
    """3D ring centroid of an atom list via stacking.ring_frame."""
    return stacking.ring_frame(_xyz(atoms), stack_ring)[0]


def _dist3(a, b):
    return math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(3)))


def pre_capture_tail_3d(engine, state):
    """The tail ring-frame centroid (3D) the seam will use for the NEXT
    capture: the head ring frame when the chain is empty (first-capture
    policy), else the newest segment's recomputed frame."""
    if not engine.segments:
        return ring_centroid_3d(
            head_atom_fn(state, engine.head),
            state['records_by_id'][state['head_id']]['stack_ring'])
    seg = engine.segments[-1]
    return ring_centroid_3d(
        seg['atoms'], state['records_by_id'][seg['molecule_id']]['stack_ring'])


def drive(engine, state, max_ticks, stop=None):
    """Step the engine (dt = 0.1), running capture() per ('stacked',) event
    exactly as the GameTab 'stacked' branch will. Returns one frame per
    tick: {'tick', 'events', 'captures': [(pickup_rec, tail_3d, outcome)]}.
    The tail centroid is recorded BEFORE the capture runs so tail->placed
    distances are assertable. Optional stop(events, engine) breaks."""
    frames = []
    for tick in range(max_ticks):
        events = engine.step(DT)
        captures = []
        for event in events:
            if event[0] == 'stacked':
                tail_3d = pre_capture_tail_3d(engine, state)
                outcome = capture(engine, event[1], state)
                captures.append((event[1], tail_3d, outcome))
        frames.append({'tick': tick, 'events': events,
                       'captures': captures})
        if stop is not None and stop(events, engine):
            break
    return frames


class TestPhase5IntegrationChain(unittest.TestCase):
    """The full pure game loop on real shipped data."""

    @classmethod
    def setUpClass(cls):
        cls.state = build_fixture()
        cls.expected_composed = math.sqrt(
            cls.state['stacking_data']['interactions'][0]['distance_a'] ** 2
            + cls.state['stacking_data']['interactions'][0]['lateral_offset_a'] ** 2)

    def _record(self, molecule_id):
        return self.state['records_by_id'][molecule_id]

    # ---- SCENARIO 1 --------------------------------------------------------

    def test_s1_win_at_cap_exact_counters_and_3p6000_geometry(self):
        """GAME-06 + GAME-04 + STACK-01 in one chain: cap = 3, three
        captures along the head's +x path (spacing > 6 A), no turns. The
        run ends 'won' at cap with exact counters, and every placed ring
        centroid sits at sqrt(d^2 + l^2) == 3.6000 A from its tail."""
        state = self.state
        picks = [pickup_seed(state, molecule_id, 'pick_%04d' % (i + 1), pos)
                 for i, (molecule_id, pos) in enumerate([
                     ('benzene', (4.0, 0.0)),
                     ('naphthalene', (11.0, 0.0)),
                     ('anthracene', (17.5, 0.0))])]
        engine = GameEngine(head=(0.0, 0.0), heading='right',
                            box_min=state['box_min'], box_max=state['box_max'],
                            pickups=picks, cap=3)
        frames = drive(engine, state, 400,
                       stop=lambda events, eng: eng.finished)
        # Exactly three captures; every resolve outcome 'placed'.
        captures = [c for frame in frames for c in frame['captures']]
        self.assertEqual(len(captures), 3)
        for (_pickup_rec, _tail, outcome) in captures:
            self.assertEqual(outcome['status'], 'placed')
        # 'won' fired on the final capture tick's event list (engine
        # referee order ... stacked -> won), and the run ended 'won'.
        self.assertIn(('won',), frames[-1]['events'])
        self.assertEqual([e[0] for e in frames[-1]['events']],
                         ['moved', 'stacked', 'won'])
        self.assertTrue(engine.finished)
        self.assertEqual(engine.result, 'won')
        # Exact counters: 3 attachments; molecules_stacked == cap;
        # atoms_total == sum of the captured pickups' atoms_n (head
        # excluded -- engine counters never include the head).
        self.assertEqual(len(engine.segments), 3)
        self.assertEqual(engine.molecules_stacked, 3)
        expected_atoms = sum(pick['atoms_n'] for pick in picks)
        self.assertEqual(engine.atoms_total, expected_atoms)
        self.assertEqual(expected_atoms, sum(
            self._record(pick['molecule_id'])['atom_count']
            for pick in picks))
        # STACK-01: every placed ring-centroid distance to its tail ==
        # sqrt(distance_a^2 + lateral_offset_a^2) from the SHIPPED dataset
        # (3.6000 A at the pinned values), within 1e-6.
        self.assertAlmostEqual(self.expected_composed, 3.6, delta=1e-3)
        for (pickup_rec, tail_3d, outcome) in captures:
            placed_3d = ring_centroid_3d(
                outcome['placed_atoms'],
                self._record(pickup_rec['molecule_id'])['stack_ring'])
            self.assertAlmostEqual(_dist3(tail_3d, placed_3d),
                                   self.expected_composed, delta=DELTA)

    # ---- SCENARIO 2 --------------------------------------------------------

    def test_s2_boundary_crash_keeps_chain_complete(self):
        """GAME-05 boundary path: small preset (+/-35 since the owner-
        approved 2026-09-20 cap-10 enlargement, was +/-12 then +/-20),
        one placed segment, head steered straight into the wall. The
        crash sets finished/result but the chain stays complete;
        step() is a no-op afterwards."""
        state = self.state
        picks = [pickup_seed(state, 'benzene', 'pick_0001', (4.0, 0.0))]
        small_min, small_max = setup_logic.BOX_PRESETS['small']
        self.assertEqual((small_min, small_max),
                         ((-35.0, -35.0), (35.0, 35.0)))
        engine = GameEngine(head=(0.0, 0.0), heading='right',
                            box_min=small_min, box_max=small_max,
                            pickups=picks)
        frames = drive(engine, state, 200,
                       stop=lambda events, eng: eng.finished)
        # The crash fires with the pinned event; note capture() took the
        # gate box from engine.box_min/box_max (the small preset), proving
        # the seam box-tracks the engine, not a module constant.
        self.assertIn(('crashed', 'boundary'), frames[-1]['events'])
        self.assertTrue(engine.finished)
        self.assertEqual(engine.result, 'crashed')
        self.assertEqual(len(engine.segments), 1)
        self.assertEqual(engine.molecules_stacked, 1)
        # Chain preserved: snapshot, then confirm frozen steps change
        # nothing (step() is a no-op [] on a finished engine).
        seg_snapshot = [(tuple(seg['centroid']), list(seg['atoms']),
                         seg['molecule_id']) for seg in engine.segments]
        self.assertEqual(engine.step(DT), [])
        self.assertEqual(engine.step(DT), [])
        after = [(tuple(seg['centroid']), list(seg['atoms']),
                  seg['molecule_id']) for seg in engine.segments]
        self.assertEqual(after, seg_snapshot)

    # ---- SCENARIO 3 --------------------------------------------------------

    def test_s3_body_crash_hits_real_placement_chain_geometry(self):
        """GAME-05 body path, segment-based: four REAL placement-produced
        segments (scripted captures, head +x, chain following the head per
        the 2026-09-19 train-follow rule), then a re-seeded engine whose
        head STARTS already overlapping the checked polyline edge -- the
        guard fires on the first tick.

        TRAIN-FOLLOW RECONCILIATION (owner-directed gameplay change,
        2026-09-19 UTC): this test previously seeded the head 2.5 A
        OUTSIDE the checked edge and drove it in over a few ticks. The
        chain now translates WITH the head, so head<->chain geometry is
        constant during straight motion and that approach is unreachable
        by construction — see test_engine_rules.py for the pinned guard
        semantics. (The "scripted two-90-degree loop-back refused by the
        boundary pre-check" observation from the old docstring is ALSO
        stale: the chain-vs-wall sweep veto was removed by the same
        owner directive — walls apply to the head only.) THIS test still
        proves the placement-produced chain geometry reaches the
        collision model intact -- the collision model itself stays
        pinned by tests/test_engine_rules.py."""
        state = self.state
        picks = [pickup_seed(state, molecule_id, 'pick_%04d' % (i + 1), pos)
                 for i, (molecule_id, pos) in enumerate([
                     ('benzene', (5.0, 0.0)),
                     ('naphthalene', (10.0, 0.0)),
                     ('anthracene', (14.0, 0.0)),
                     ('phenanthrene', (17.0, 0.0))])]
        engine = GameEngine(head=(0.0, 0.0), heading='right',
                            box_min=state['box_min'], box_max=state['box_max'],
                            pickups=picks)
        frames = drive(engine, state, 200,
                       stop=lambda events, eng: len(eng.segments) == 4)
        self.assertEqual(len(engine.segments), 4)
        for frame in frames:
            for (_pickup_rec, _tail, outcome) in frame['captures']:
                self.assertEqual(outcome['status'], 'placed')
        # Copy the real placement chain for the constructor re-seed.
        real_chain = [{'molecule_id': seg['molecule_id'],
                       'centroid': tuple(seg['centroid']),
                       'atoms': list(seg['atoms'])}
                      for seg in engine.segments]
        # Body-collision model: with n = 4 segments the engine checks
        # edges i in range(0, n-1-SEGMENT_SKIP_RECENT[2]) == edge (0, 1)
        # only -- the polyline edge between the two OLDEST segments.
        # Seed the head ON edge 0 so the state STARTS overlapping
        # (distance 0.0 < BODY_COLLISION_RADIUS_A = 2.0): the midpoint
        # of (c0, c1). The guard must fire on the FIRST tick.
        c0 = real_chain[0]['centroid']
        c1 = real_chain[1]['centroid']
        mid = ((c0[0] + c1[0]) / 2.0, (c0[1] + c1[1]) / 2.0)
        crash_engine = GameEngine(head=mid,
                                  heading='right',
                                  box_min=state['box_min'],
                                  box_max=state['box_max'],
                                  segments=real_chain)
        events = crash_engine.step(DT)
        self.assertEqual(events[0][0], 'moved')
        self.assertIn(('crashed', 'body'), events)
        self.assertTrue(crash_engine.finished)
        self.assertEqual(crash_engine.result, 'crashed')
        # The chain stays complete after the body crash and MOVED WITH
        # the head by exactly one tick delta (train-follow rigidity):
        # every centroid/atom shifted by the SAME (+0.3, 0.0) the head
        # took. STEP_A = 3.0 * 0.1.
        step_a = 3.0 * DT
        self.assertEqual(len(crash_engine.segments), 4)
        for i in range(4):
            seg = crash_engine.segments[i]
            self.assertAlmostEqual(seg['centroid'][0],
                                   real_chain[i]['centroid'][0] + step_a,
                                   delta=1e-9)
            self.assertAlmostEqual(seg['centroid'][1],
                                   real_chain[i]['centroid'][1],
                                   delta=1e-9)
            for j, atom in enumerate(seg['atoms']):
                ref = real_chain[i]['atoms'][j]
                self.assertEqual(atom[0], ref[0])
                self.assertAlmostEqual(atom[1], ref[1] + step_a,
                                       delta=1e-9)
                self.assertAlmostEqual(atom[2], ref[2], delta=1e-9)
                self.assertEqual(atom[3], ref[3])
        self.assertEqual(crash_engine.step(DT), [])

    # ---- SCENARIO 4 --------------------------------------------------------

    def test_s4_biphenyl_capture_refuses_refuse_atom(self):
        """STACK-05 refuse path (locked decision 6): biphenyl captured
        over a real set_a segment tail. DATA OBSERVATION (recorded, NOT
        fixed): the shipped biphenyl conformer has its two rings at 90.00
        degrees (measured on the shipped SDF), so EVERY pairwise
        biphenyl-involved stack at the dataset geometry clashes
        (0.688-2.145 A < the 2.5 A gate); biphenyl is the permanent
        refuse-path demonstrator -- no serpentrum module is changed to
        accommodate it."""
        state = self.state
        picks = [pickup_seed(state, 'naphthalene', 'pick_0001', (4.0, 0.0)),
                 pickup_seed(state, 'biphenyl', 'pick_0002', (11.0, 0.0))]
        engine = GameEngine(head=(0.0, 0.0), heading='right',
                            box_min=state['box_min'], box_max=state['box_max'],
                            pickups=picks)
        refused = None
        for frame in drive(
                engine, state, 100,
                stop=lambda events, eng: any(
                    e[0] == 'stacked' and e[1]['id'] == 'pick_0002'
                    for e in events)):
            for (pickup_rec, _tail, outcome) in frame['captures']:
                if pickup_rec['id'] == 'pick_0002':
                    refused = outcome
        self.assertIsNotNone(refused)
        self.assertEqual(refused['status'], 'refused')
        self.assertEqual(refused['code'], placement.REFUSE_ATOM)
        self.assertIn('detail', refused)
        # The capture helper invoked engine.reject_pickup (the rollback
        # seam): counters back to the pre-biphenyl-capture values, the
        # pickup re-armed, exactly one refusal tracked.
        self.assertEqual(engine.molecules_stacked, 1)
        self.assertEqual(len(engine.segments), 1)
        self.assertEqual(engine.atoms_total,
                         self._record('naphthalene')['atom_count'])
        self.assertIn('pick_0002', engine.live_pickup_ids)
        self.assertEqual(engine._refusal_counts['pick_0002'], 1)
        # The run continues (not crashed, not won).
        self.assertFalse(engine.finished)
        self.assertIsNone(engine.result)

    # ---- SCENARIO 5 --------------------------------------------------------

    def test_s5_upload_shaped_capture_skips_no_entry(self):
        """STACK-03 skip path (locked decision 7, '__upload__' keying): an
        upload-shaped record (set == '__upload__', has_stack_entry False,
        NO stack_ring) captured like any pickup is skipped with
        SKIP_NO_ENTRY and the counters net out to zero."""
        state = self.state
        benzene_atoms = state['atoms_by_id']['benzene']
        upload_pickup = {
            'id': 'pick_0001',
            'molecule_id': 'upload_0',
            'centroid': (4.0, 0.0),
            'atoms': [(sym, x + 4.0, y, z)
                      for (sym, x, y, z) in benzene_atoms],
            'atoms_n': len(benzene_atoms),
            'set': '__upload__',
            'has_stack_entry': False,
            # NO 'stack_ring' key -- an upload-shaped record carries none.
        }
        engine = GameEngine(head=(0.0, 0.0), heading='right',
                            box_min=state['box_min'], box_max=state['box_max'],
                            pickups=[upload_pickup])
        skipped = None
        for frame in drive(
                engine, state, 60,
                stop=lambda events, eng: any(e[0] == 'stacked'
                                             for e in events)):
            for (pickup_rec, _tail, outcome) in frame['captures']:
                if pickup_rec['id'] == 'pick_0001':
                    skipped = outcome
        self.assertIsNotNone(skipped)
        self.assertEqual(skipped['status'], 'skipped')
        self.assertEqual(skipped['code'], placement.SKIP_NO_ENTRY)
        # reject_pickup rolled the capture back: counters net zero, the
        # pickup re-armed, exactly one refusal recorded.
        self.assertEqual(engine.molecules_stacked, 0)
        self.assertEqual(engine.atoms_total, 0)
        self.assertEqual(len(engine.segments), 0)
        self.assertIn('pick_0001', engine.live_pickup_ids)
        self.assertEqual(engine._refusal_counts['pick_0001'], 1)

    # ---- SCENARIO 6 --------------------------------------------------------

    def test_s6_cap_reaching_refusal_unfinishes_and_play_resumes(self):
        """G2 / plan 05-04: cap = 1 and the ONLY pickup is the clash-bound
        biphenyl. The capture fires ('stacked', ...) then ('won',) on the
        SAME tick with finished=True / result='won'; the capture helper's
        refuse routes through reject_pickup, which MUST un-finish the run
        (counters back below cap) so play resumes and the head keeps
        moving."""
        state = self.state
        picks = [pickup_seed(state, 'biphenyl', 'pick_0001', (4.0, 0.0))]
        engine = GameEngine(head=(0.0, 0.0), heading='right',
                            box_min=state['box_min'], box_max=state['box_max'],
                            pickups=picks, cap=1)
        # Inline loop (ordering is load-bearing): assert the WON state
        # AFTER step() but BEFORE the seam's reject rolls it back.
        outcome = None
        for _tick in range(60):
            events = engine.step(DT)
            if ('won',) in events:
                # Engine referee order: ... stacked -> won on one tick.
                self.assertEqual([e[0] for e in events],
                                 ['moved', 'stacked', 'won'])
                self.assertTrue(engine.finished)
                self.assertEqual(engine.result, 'won')
                self.assertEqual(engine.molecules_stacked, 1)
                pickup_rec = [e for e in events if e[0] == 'stacked'][0][1]
                outcome = capture(engine, pickup_rec, state)
                break
        self.assertIsNotNone(outcome)
        # The only-pickup biphenyl clashes over the set_a head tail.
        self.assertEqual(outcome['status'], 'refused')
        self.assertEqual(outcome['code'], placement.REFUSE_ATOM)
        # reject_pickup un-finished the run (counters back below cap).
        self.assertFalse(engine.finished)
        self.assertIsNone(engine.result)
        self.assertEqual(engine.molecules_stacked, 0)
        self.assertEqual(engine.atoms_total, 0)
        self.assertIn('pick_0001', engine.live_pickup_ids)
        self.assertEqual(engine._refusal_counts['pick_0001'], 1)
        # Play resumes: the head keeps moving on the next ticks. The
        # re-armed biphenyl sits INSIDE the 3.0 A capture radius, so it
        # re-captures (and re-wins) while in range -- documented behavior
        # (research open Q4: re-armed pickups stay put) -- and every
        # repetition rides the same win/refuse/un-finish seam without
        # refreezing the run.
        head_before = engine.head
        saw_moved = False
        recaptures = 0
        for _tick in range(6):
            events = engine.step(DT)
            if any(e[0] == 'moved' for e in events):
                saw_moved = True
            for event in events:
                if event[0] == 'stacked':
                    recaptures += 1
                    capture(engine, event[1], state)
                    # Each repeated refuse un-finishes again.
                    self.assertFalse(engine.finished)
                    self.assertIsNone(engine.result)
                    self.assertEqual(engine.molecules_stacked, 0)
        self.assertTrue(saw_moved)
        self.assertGreaterEqual(recaptures, 1)
        self.assertGreater(engine._refusal_counts['pick_0001'], 1)
        self.assertNotEqual(engine.head, head_before)
        self.assertFalse(engine.finished)

    # ---- SCENARIO 7 --------------------------------------------------------

    def test_s7_sweep_rotated_tail_frame_continues_growth_direction(self):
        """GAME-10 x STACK-01 interplay: attach one segment, open a 90-
        degree sweep, run all 6 ticks, then capture a second pickup. The
        tail frame MUST come from the sweep-rotated segment atoms, so the
        new growth direction equals the pre-sweep growth direction rotated
        by the sweep angle (dot > 0.99), and ring_frame on the rotated
        atoms stays valid (planarity invariant under rotation)."""
        state = self.state
        picks = [pickup_seed(state, 'naphthalene', 'pick_0001', (4.0, 0.0))]
        engine = GameEngine(head=(0.0, 0.0), heading='right',
                            box_min=state['box_min'], box_max=state['box_max'],
                            pickups=picks)
        first = None
        for frame in drive(engine, state, 100,
                           stop=lambda events, eng: len(eng.segments) == 1):
            for (pickup_rec, tail_3d, outcome) in frame['captures']:
                first = (tail_3d, outcome)
        self.assertIsNotNone(first)
        tail_3d, out1 = first
        self.assertEqual(out1['status'], 'placed')
        # Pre-sweep growth direction (tail -> placed centroid, 3D).
        c1 = ring_centroid_3d(out1['placed_atoms'],
                              self._record('naphthalene')['stack_ring'])
        g1 = (c1[0] - tail_3d[0], c1[1] - tail_3d[1], c1[2] - tail_3d[2])
        self.assertAlmostEqual(_dist3(g1, (0.0, 0.0, 0.0)),
                               self.expected_composed, delta=DELTA)
        # Open a 90-degree sweep and run all TURN_TICKS ticks.
        opened, _events = engine.start_sweep('up')
        self.assertTrue(opened)
        angle_signed = engine.sweeping['angle_signed']
        turning_ticks = 0
        while engine.sweeping is not None:
            events = engine.step(DT)
            turning_ticks += 1
            self.assertEqual(events, [('turning', turning_ticks / 6.0)])
        self.assertEqual(turning_ticks, game_engine.TURN_TICKS)
        self.assertEqual(engine.heading, (0.0, 1.0))
        # Planarity invariant under rotation: ring_frame on the swept
        # segment's rotated atoms returns a valid frame (never raises).
        seg = engine.segments[-1]
        rot_frame = stacking.ring_frame(
            _xyz(seg['atoms']),
            self._record(seg['molecule_id'])['stack_ring'])
        self.assertEqual(len(rot_frame), 3)
        # Train-follow note (2026-09-19): rot_frame is a SNAPSHOT — the
        # segment (and its ring frame) follows the head on every later
        # forward tick, so capture-time tail comparisons must add the
        # head's travel since this snapshot.
        head_at_snapshot = engine.head
        # Mid-run spawn seam (the same pattern plan 05-13 uses on every
        # resolution: the engine has no spawn API -- the controller extends
        # the seeded pickups list / live id set / remaining counter).
        ahead = (engine.head[0], engine.head[1] + 8.0)
        pick2 = pickup_seed(state, 'benzene', 'pick_0002', ahead)
        engine.pickups.append(pick2)
        engine.live_pickup_ids.add(pick2['id'])
        engine.pickups_remaining += 1
        second = None
        for frame in drive(
                engine, state, 200,
                stop=lambda events, eng: len(eng.segments) == 2):
            for (pickup_rec, tail2_3d, outcome) in frame['captures']:
                if pickup_rec['id'] == 'pick_0002':
                    second = (tail2_3d, outcome)
        self.assertIsNotNone(second)
        tail2_3d, out2 = second
        self.assertEqual(out2['status'], 'placed')
        # The tail for the second capture IS the swept segment's
        # rotated frame, translated by the head's travel since the
        # snapshot (train-follow: segment atoms follow the head, and the
        # tail frame is recomputed from the CURRENT atoms at capture
        # time — identical relative geometry, same rigid chain).
        expected_tail = (
            rot_frame[0][0] + (engine.head[0] - head_at_snapshot[0]),
            rot_frame[0][1] + (engine.head[1] - head_at_snapshot[1]),
            rot_frame[0][2])
        self.assertAlmostEqual(_dist3(tail2_3d, expected_tail),
                               0.0, delta=1e-9)
        c2 = ring_centroid_3d(out2['placed_atoms'],
                              self._record('benzene')['stack_ring'])
        g2 = (c2[0] - tail2_3d[0], c2[1] - tail2_3d[1], c2[2] - tail2_3d[2])
        # The new growth direction is the pre-sweep growth direction
        # rotated by the sweep's signed angle (rotation about z; z kept).
        th = math.radians(angle_signed)
        ct, st = math.cos(th), math.sin(th)
        rg1 = (g1[0] * ct - g1[1] * st,
               g1[0] * st + g1[1] * ct, g1[2])
        dot = sum(g2[i] * rg1[i] for i in range(3)) / \
            (_dist3(g2, (0.0, 0.0, 0.0)) * _dist3(rg1, (0.0, 0.0, 0.0)))
        self.assertGreater(dot, 0.99)
        # The composed dataset distance holds post-sweep as well.
        self.assertAlmostEqual(_dist3(g2, (0.0, 0.0, 0.0)),
                               self.expected_composed, delta=DELTA)

    # ---- SCENARIO 8 --------------------------------------------------------

    def test_s8_spawn_positions_reproduce_byte_identically(self):
        """GAME-07 restart determinism at the spawn seam: a full
        scenario-1-shaped spawner call sequence (first() + next_after()
        after each of three captures, with the run's head positions, the
        growing chain atoms and live centroids) reproduces byte-identically
        on a second identical run -- same record ids, pids, and centroid
        floats (private random.Random(seed), never the global random)."""
        state = self.state

        def run_once():
            spawner = spawn.PickupSpawner(
                state['records'], state['box_min'], state['box_max'],
                1701, state['atoms_by_id'])
            log = []
            record, pid, centroid = spawner.first((0.0, 0.0), 'right')
            log.append((record['id'], pid, centroid))
            live = [centroid]
            chain_atoms = []
            # The head x positions scenario 1's captures land at (first
            # head within 3.0 of each pickup centroid), fed to next_after
            # exactly like a live run would after each capture resolution.
            heads = [(1.2, 0.0), (8.1, 0.0), (14.4, 0.0)]
            for i in range(3):
                chain_atoms.extend(state['atoms_by_id']['benzene'])
                result = spawner.next_after(heads[i], 'right',
                                            chain_atoms, list(live))
                if result is None:
                    log.append(None)
                    continue
                record, pid, centroid = result
                log.append((record['id'], pid, centroid))
                live.append(centroid)
            return log

        run_a = run_once()
        run_b = run_once()
        # Exact (float-equality) reproduction of the whole sequence.
        self.assertEqual(run_a, run_b)
        self.assertEqual(len(run_a), 4)
        for entry in run_a:
            self.assertIsNotNone(entry)


if __name__ == '__main__':
    unittest.main()
