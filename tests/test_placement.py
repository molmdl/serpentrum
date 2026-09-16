"""Placement controller seam tests (plan 05-05, STACK-01/03/05).

TDD for ``serpentrum/placement.py`` — the PURE single function the GUI's
'stacked' branch will call (resolve()), plus its testable parts
(resolve_skip / tail_frame / attempt_place / gate). This file exists before
the module it tests: RED commits fail with ImportError/missing functions,
the GREEN commit is ``serpentrum/placement.py`` itself.

Discovery command (same convention as every tests/test_*.py here; tests/
deliberately has NO __init__.py — the dev plugin path IS the repo root):

    python3.6 -m unittest tests.test_placement -v

Fixture provenance (wave-1 isolation — siblings 05-01/05-02 are NOT merged
into this worktree):

- Real dataset: ``molecule_data.load_stacking(setloader.default_stacking_path())``
  (the shipped APPROVED pi_stack_pd entry: distance_a 3.383 /
  lateral_offset_a 1.231, citation janiak2000).
- Real records: ``setloader.load_demo_set(stacking_path=...)``. Wave-1
  records do NOT carry 'stack_ring' (plan 05-08 adds it in wave 2), so the
  fixture COPIES the real records and sets 'stack_ring' to the canonical
  ring-walk indices probe-verified in 05-RESEARCH-core-integration.md
  (benzene (0,1,3,5,4,2), biphenyl ring A (0,2,6,10,8,4), ...) — exactly
  what plan 05-01/05-08 will produce. Raw SDF order is NOT usable:
  manifest ring_atoms are the sorted 2-core, and passing sorted indices to
  stacking.ring_frame makes a star polygon ("non-planar 1.133 A" trap).
  ``molfile.find_ring_atoms`` is NOT needed for any assertion here (its
  output is the sorted 2-core, which ring_frame rejects) — hardcoded
  canonical cycles per the plan's explicit base-tree allowance.
- Atoms from raw molfile.read_sdf coords (no sibling artifacts). For the
  head, plan 05-02/05-10's edge-on presentation (ring plane edge-on, ring
  normal IN the xy movement plane) is reproduced LOCALLY by a 90-degree
  rotation about y applied to the raw coords: raw demo aromatics lie flat
  in xy (ring normal +/-z) while placement growth normal = -heading is
  always IN xy; without the edge-on pose the head-vs-pickup clash is
  unavoidable and NO game-geometry assertion (3.6000 A staircase,
  clash-free stack) can hold. The rotation is a rigid proper rotation, so
  all exactness values are unaffected.

Policy pins (mirroring placement.py's docstring, decided in plan 05-05):
1. Skip taxonomy, ordered first-match-wins:
   SKIP_NO_ENTRY -> SKIP_NOT_APPROVED -> SKIP_MODE -> SKIP_NO_RING ->
   SKIP_NONPLANAR (the last detected at placement time, not resolve_skip).
2. Tail/growth: empty chain -> head ring frame with growth normal =
   -(heading) promoted to 3D; non-empty -> NEWEST segment's ring frame
   recomputed from its current atoms + records_by_id stack_ring, whose
   computed normal IS the growth continuation (linear staircase).
3. Clash gate over head + all segments + OTHER live pickups' atoms inside
   the 3D box ((x0, y0, -display_z) .. (x1, y1, +display_z)).
4. Outcome contract: placed | skipped(code) | refused(code, detail) —
   resolve() never mutates engine state, so the GUI ALWAYS calls
   engine.reject_pickup on skip/refuse (capture already counted; the
   win-desync fix itself is plan 05-04).
"""
import copy
import math
import os
import sys
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from serpentrum import molfile  # noqa: E402
from serpentrum import molecule_data  # noqa: E402
from serpentrum import placement  # noqa: E402  -- RED: module does not exist yet
from serpentrum import setloader  # noqa: E402
from serpentrum import stacking  # noqa: E402

_STACKING_PATH = setloader.default_stacking_path()
_BENZENE_SDF = os.path.join(setloader.package_data_dir(), 'benzene.sdf')
_BIPHENYL_SDF = os.path.join(setloader.package_data_dir(), 'biphenyl.sdf')

# Canonical ring-walk cycles (05-RESEARCH-core-integration.md, probe-verified
# for these exact SDF files; plan 05-01 (molfile.ring_cycle) will compute
# these from bonds in a later merge; hardcoded here per the plan's explicit
# base-tree allowance).
_BENZENE_RING = (0, 1, 3, 5, 4, 2)
_NAPHTHALENE_RING = (0, 1, 3, 7, 6, 2)
_ANTHRACENE_RING = (0, 1, 5, 3, 2, 4)
_PHENANTHRENE_RING = (0, 1, 3, 5, 4, 2)
_BIPHENYL_RING_A = (0, 2, 6, 10, 8, 4)
_CANONICAL_RINGS = {
    'benzene': _BENZENE_RING,
    'naphthalene': _NAPHTHALENE_RING,
    'anthracene': _ANTHRACENE_RING,
    'phenanthrene': _PHENANTHRENE_RING,
    'biphenyl': _BIPHENYL_RING_A,
}

_HEADING_EAST = (1.0, 0.0)
_MINUS_HEADING_EAST = (-1.0, 0.0, 0.0)
_BOX_SMALL = ((-12.0, -12.0), (12.0, 12.0))
_DISPLAY_Z = 5.0  # pymol_bridge.BOX_DISPLAY_Z (the displayed box constant)
_WIDE_DISPLAY_Z = 7.0  # exceeds biphenyl's max |z| (6.914 A, probe) so the
# biphenyl refusal lands on the ATOM check, as the plan pins


def _load_atoms4(path):
    """(sym, x, y, z) tuples straight from a shipped SDF (raw coords)."""
    record = molfile.read_sdf(path)[0]
    return [(record['elements'][i],) + tuple(record['coords'][i])
            for i in range(record['atom_count'])]


def _xyz(atoms):
    """(x, y, z) floats from either 4-tuples (sym, x, y, z) or 3-tuples."""
    return [tuple(a[1:]) if len(a) == 4 else tuple(a) for a in atoms]


def _rot90y(p):
    """Rotate (x, y, z) 90 degrees about +y: (x,y,z) -> (z, y, -x).

    Maps the raw demo molecules' flat ring normal (0, 0, -1) to (-1, 0, 0)
    — the edge-on presentation contract (ring plane edge-on to screen, ring
    normal in the xy movement plane) that plans 05-02/05-10 implement at
    materialization. A proper rigid rotation: exactness values unaffected.
    """
    return (p[2], p[1], -p[0])


def _edge_on(atoms4):
    """Locally edge-on version of raw (sym, x, y, z) atoms."""
    return [(s,) + _rot90y((x, y, z)) for (s, x, y, z) in atoms4]


def _translated(atoms4, dx, dy):
    return [(s, x + dx, y + dy, z) for (s, x, y, z) in atoms4]


class _FixtureBase(unittest.TestCase):
    """Shared real-data fixtures: dataset, records (stack_ring patched in),
    raw + edge-on atom lists."""

    @classmethod
    def setUpClass(cls):
        cls.stacking_data = molecule_data.load_stacking(_STACKING_PATH)
        cls.interaction = cls.stacking_data['interactions'][0]
        assert cls.interaction['id'] == 'pi_stack_pd'
        records, errors = setloader.load_demo_set(
            stacking_path=_STACKING_PATH)
        assert not errors, errors
        cls.records_by_id = {}
        for record in records:
            patched = dict(record)
            patched['stack_ring'] = list(_CANONICAL_RINGS[record['id']])
            cls.records_by_id[record['id']] = patched
        cls.benzene_raw = _load_atoms4(_BENZENE_SDF)
        cls.biphenyl_raw = _load_atoms4(_BIPHENYL_SDF)
        # The head as the game will hold it: edge-on pose, centroid at origin.
        cls.head = _edge_on(cls.benzene_raw)
        cls.head_c, _hn, cls.head_r = stacking.ring_frame(
            _xyz(cls.head), _BENZENE_RING)


class TestSkipTaxonomy(_FixtureBase):
    """Task 1 pins: ordered resolve_skip taxonomy incl. the approval gate."""

    def test_upload_record_skips_no_entry(self):
        upload_rec = {'set': '__upload__', 'has_stack_entry': False}
        self.assertEqual(
            placement.resolve_skip(upload_rec, self.stacking_data),
            placement.SKIP_NO_ENTRY)

    def test_upload_hits_no_entry_before_no_ring(self):
        # The upload shape also lacks 'stack_ring' — the taxonomy ORDER locks
        # SKIP_NO_ENTRY as the first-match hit (never SKIP_NO_RING).
        upload_rec = {'set': '__upload__', 'has_stack_entry': False}
        self.assertNotIn('stack_ring', upload_rec)
        self.assertEqual(
            placement.resolve_skip(upload_rec, self.stacking_data),
            placement.SKIP_NO_ENTRY)

    def test_set_a_record_with_dataset_is_stackable(self):
        benzene = self.records_by_id['benzene']
        self.assertTrue(benzene['has_stack_entry'])
        self.assertIn('stack_ring', benzene)
        self.assertIsNone(
            placement.resolve_skip(benzene, self.stacking_data))

    def test_draft_interaction_skips_not_approved(self):
        # interaction_for alone is NOT approval-filtered: a DRAFT dataset
        # entry must skip even though an interaction exists and matches.
        draft_data = copy.deepcopy(self.stacking_data)
        draft_data['interactions'][0]['status'] = 'DRAFT'
        self.assertEqual(molecule_data.shipped_interactions(draft_data), [])
        benzene = self.records_by_id['benzene']
        self.assertTrue(benzene['has_stack_entry'])
        self.assertEqual(
            placement.resolve_skip(benzene, draft_data),
            placement.SKIP_NOT_APPROVED)

    def test_non_pi_stack_mode_skips_mode(self):
        mode_data = copy.deepcopy(self.stacking_data)
        mode_data['interactions'][0]['mode'] = 'h_bond'
        # Still APPROVED (isolates the mode check from the approval gate).
        self.assertNotEqual(
            molecule_data.shipped_interactions(mode_data), [])
        self.assertEqual(
            placement.resolve_skip(self.records_by_id['benzene'], mode_data),
            placement.SKIP_MODE)

    def test_missing_stack_ring_skips_no_ring(self):
        ringless = dict(self.records_by_id['benzene'])
        del ringless['stack_ring']
        self.assertEqual(
            placement.resolve_skip(ringless, self.stacking_data),
            placement.SKIP_NO_RING)

    def test_taxonomy_order_full_chain(self):
        # DRAFT + ringless: approval is checked BEFORE stack_ring presence.
        draft_data = copy.deepcopy(self.stacking_data)
        draft_data['interactions'][0]['status'] = 'DRAFT'
        ringless = dict(self.records_by_id['benzene'])
        del ringless['stack_ring']
        self.assertEqual(
            placement.resolve_skip(ringless, draft_data),
            placement.SKIP_NOT_APPROVED)

    def test_outcome_code_constants_are_strings(self):
        # hud_logic (plan 05-09) imports these constants to map codes to text.
        for name in ('SKIP_NO_ENTRY', 'SKIP_NOT_APPROVED', 'SKIP_MODE',
                     'SKIP_NO_RING', 'SKIP_NONPLANAR',
                     'REFUSE_WALL', 'REFUSE_ATOM'):
            self.assertIsInstance(getattr(placement, name), str, name)


class TestTailFrameGrowthPolicy(_FixtureBase):
    """Task 2 pins 1/2/4: tail selection + growth normal policy (G6)."""

    def _first_segment(self):
        """One placed benzene segment on the empty chain (head as tail)."""
        placed, _R, _t, ring_c = placement.attempt_place(
            self.benzene_raw, _BENZENE_RING,
            self.head_c, _MINUS_HEADING_EAST, self.head_r, self.interaction)
        return {
            'molecule_id': 'benzene',
            'centroid': (ring_c[0], ring_c[1]),
            'atoms': placed,
            'atoms_n': len(placed),
        }

    def test_empty_chain_uses_head_frame_with_minus_heading_normal(self):
        c, n, r = placement.tail_frame([], self.records_by_id,
                                       self.head, _BENZENE_RING,
                                       _HEADING_EAST)
        # Centroid + ref come straight from the head's own ring frame...
        for k in range(3):
            self.assertAlmostEqual(c[k], self.head_c[k], places=12)
            self.assertAlmostEqual(r[k], self.head_r[k], places=12)
        # ...while the growth normal is -(heading) promoted to 3D, EXACTLY
        # (behind the head, snake-canonical) — not the head's ring normal.
        self.assertEqual(n, _MINUS_HEADING_EAST)

    def test_first_capture_growth_is_along_minus_heading(self):
        placed, _R, _t, ring_c = placement.attempt_place(
            self.benzene_raw, _BENZENE_RING,
            self.head_c, _MINUS_HEADING_EAST, self.head_r, self.interaction)
        delta = tuple(ring_c[k] - self.head_c[k] for k in range(3))
        # x decreases (placement lands BEHIND an east-moving head) and the
        # along-normal component dominates the 20-degree lateral component.
        self.assertLess(delta[0], 0.0)
        self.assertGreater(abs(delta[0]), abs(delta[1]))

    def test_nonempty_chain_uses_newest_segments_recomputed_frame(self):
        seg = self._first_segment()
        c, n, r = placement.tail_frame([seg], self.records_by_id,
                                       self.head, _BENZENE_RING,
                                       _HEADING_EAST)
        exp_c, exp_n, exp_r = stacking.ring_frame(
            _xyz(seg['atoms']), _BENZENE_RING)
        for k in range(3):
            self.assertAlmostEqual(c[k], exp_c[k], places=12)
            self.assertAlmostEqual(n[k], exp_n[k], places=12)
            self.assertAlmostEqual(r[k], exp_r[k], places=12)

    def test_recomputed_normal_equals_placement_growth_normal(self):
        # tail_frame RECOMPUTES the newest segment's frame from its current
        # atoms; for a same-species stack that recomputed normal must equal
        # the growth normal used at placement (here exactly (-1, 0, 0)) —
        # the linear staircase the research measured clash-safe.
        seg = self._first_segment()
        growth_used = _MINUS_HEADING_EAST
        _c, n, _r = placement.tail_frame([seg], self.records_by_id,
                                         self.head, _BENZENE_RING,
                                         _HEADING_EAST)
        dot = sum(n[k] * growth_used[k] for k in range(3))
        self.assertGreater(dot, 0.99)
        # Chain-continuity companion: the centroid step head -> segment
        # points along the growth normal at the dataset's pinned 20 deg
        # (dot = 3.383/3.6000069 = 0.93972 exactly — the off-normal angle
        # makes a centroid-based dot > 0.99 arithmetically impossible, so
        # continuity is pinned against its exact geometric value).
        c2, _n, _r = placement.tail_frame([seg], self.records_by_id,
                                          self.head, _BENZENE_RING,
                                          _HEADING_EAST)
        delta3 = tuple(c2[k] - self.head_c[k] for k in range(3))
        mag = math.sqrt(sum(v * v for v in delta3))
        cos_step = sum(growth_used[k] * (delta3[k] / mag) for k in range(3))
        expected_cos = (self.interaction['distance_a'] /
                        math.sqrt(self.interaction['distance_a'] ** 2 +
                                  self.interaction['lateral_offset_a'] ** 2))
        self.assertAlmostEqual(cos_step, expected_cos, places=9)
        self.assertGreater(cos_step, 0.93)

    def test_staircase_second_step_is_clean_and_exact(self):
        seg1 = self._first_segment()
        c2, n2, r2 = placement.tail_frame([seg1], self.records_by_id,
                                          self.head, _BENZENE_RING,
                                          _HEADING_EAST)
        placed2, _R2, _t2, ring_c2 = placement.attempt_place(
            self.benzene_raw, _BENZENE_RING, c2, n2, r2, self.interaction)
        step = tuple(ring_c2[k] - c2[k] for k in range(3))
        step_len = math.sqrt(sum(v * v for v in step))
        composed = math.sqrt(self.interaction['distance_a'] ** 2 +
                             self.interaction['lateral_offset_a'] ** 2)
        self.assertAlmostEqual(step_len, composed, places=9)
        existing = _xyz(self.head) + _xyz(seg1['atoms'])
        violation = placement.gate(placed2, existing,
                                   _BOX_SMALL[0], _BOX_SMALL[1],
                                   _DISPLAY_Z)
        self.assertIsNone(violation)


class TestPlacementExactness(_FixtureBase):
    """Task 2 pin 3 (STACK-01): the placed geometry reproduces the APPROVED
    dataset encoding EXACTLY — distance_a/lateral_offset_a decompose the
    measured centroid step, and the composed value rounds to the approved
    3.60 A @ 20 deg headline (Janiak 2000; encoding tolerance inherited
    from test_stacking_dataset.py: the file stores 3.383/1.231, whose
    exact composition sqrt(3.383^2+1.231^2) = 3.6000069 A rounds to 3.6000
    and atan2(1.231, 3.383) = 19.9953 deg rounds to 20.0 deg — exactness is
    pinned against the FORMULA, the headline against its rounding)."""

    def test_placed_centroid_distance_matches_dataset_formula_exactly(self):
        _placed, _R, _t, ring_c = placement.attempt_place(
            self.benzene_raw, _BENZENE_RING,
            self.head_c, _MINUS_HEADING_EAST, self.head_r, self.interaction)
        delta = tuple(ring_c[k] - self.head_c[k] for k in range(3))
        dist = math.sqrt(sum(v * v for v in delta))
        composed = math.sqrt(self.interaction['distance_a'] ** 2 +
                             self.interaction['lateral_offset_a'] ** 2)
        self.assertAlmostEqual(dist, composed, places=9)
        self.assertAlmostEqual(dist, 3.6000, places=4)  # headline rounding

    def test_placed_components_and_off_normal_angle_reproduce_encoding(self):
        _placed, _R, _t, ring_c = placement.attempt_place(
            self.benzene_raw, _BENZENE_RING,
            self.head_c, _MINUS_HEADING_EAST, self.head_r, self.interaction)
        delta = tuple(ring_c[k] - self.head_c[k] for k in range(3))
        along_normal = sum(delta[k] * _MINUS_HEADING_EAST[k]
                           for k in range(3))
        dist = math.sqrt(sum(v * v for v in delta))
        lateral = math.sqrt(max(0.0, dist * dist - along_normal ** 2))
        self.assertAlmostEqual(along_normal,
                               self.interaction['distance_a'], places=9)
        self.assertAlmostEqual(lateral,
                               self.interaction['lateral_offset_a'],
                               places=9)
        angle = math.degrees(math.atan2(lateral, along_normal))
        # Formula-exact reproduction of test_stacking_dataset's pinned
        # expression, then the same 0.5 deg headline tolerance it uses.
        self.assertAlmostEqual(
            angle,
            math.degrees(math.atan2(self.interaction['lateral_offset_a'],
                                    self.interaction['distance_a'])),
            places=9)
        self.assertLessEqual(abs(angle - 20.0), 0.5)

    def test_R_and_t_rigidly_explain_every_placed_atom(self):
        placed, R, t, _ring_c = placement.attempt_place(
            self.benzene_raw, _BENZENE_RING,
            self.head_c, _MINUS_HEADING_EAST, self.head_r, self.interaction)
        self.assertEqual(len(placed), len(self.benzene_raw))
        self.assertEqual(len(R), 3)
        self.assertEqual(len(t), 3)
        src = _xyz(self.benzene_raw)
        for i, p in enumerate(src):
            expect = tuple(sum(R[k][j] * p[j] for j in range(3)) + t[k]
                           for k in range(3))
            got = placed[i][1:]
            for k in range(3):
                self.assertAlmostEqual(got[k], expect[k], places=9)
        self.assertEqual([a[0] for a in placed],
                         [a[0] for a in self.benzene_raw])


class TestClashGateAssembly(_FixtureBase):
    """Task 2 pin 5 (STACK-05): gate() is a THIN 3D-box wrapper over
    stacking.check_clash; the existing set = head + segments + other live
    pickups; a clean 3.6 A stack passes."""

    def _placed_on_head(self):
        placed, _R, _t, _rc = placement.attempt_place(
            self.benzene_raw, _BENZENE_RING,
            self.head_c, _MINUS_HEADING_EAST, self.head_r, self.interaction)
        return placed

    def test_thin_wrapper_matches_check_clash_on_3d_box(self):
        placed = self._placed_on_head()
        existing = _xyz(self.head) + _xyz(self.biphenyl_raw)
        wrapped = placement.gate(placed, existing,
                                 _BOX_SMALL[0], _BOX_SMALL[1], _DISPLAY_Z)
        direct = stacking.check_clash(
            _xyz(placed), _xyz(existing),
            (_BOX_SMALL[0][0], _BOX_SMALL[0][1], -_DISPLAY_Z),
            (_BOX_SMALL[1][0], _BOX_SMALL[1][1], _DISPLAY_Z))
        self.assertEqual(wrapped, direct)

    def test_clean_3_6_a_stack_passes_over_full_existing_set(self):
        seg1 = {'molecule_id': 'benzene', 'centroid': (0.0, 0.0),
                'atoms': self._placed_on_head(),
                'atoms_n': len(self.benzene_raw)}
        # gate sees head + segments + OTHER live pickups (< 2.5 A away from
        # each other but > 2.5 A from the landing zone): the landing zone
        # next to the head stays clean, so none of the three blocks it.
        live_far = [('C', 8.0, 8.0, 0.0), ('H', 9.0, 8.5, 0.0)]
        live_far2 = [('C', 8.0, 6.0, 0.0)]
        existing = (_xyz(self.head) + _xyz(seg1['atoms']) +
                    _xyz(live_far) + _xyz(live_far2))
        c2, n2, r2 = placement.tail_frame([seg1], self.records_by_id,
                                          self.head, _BENZENE_RING,
                                          _HEADING_EAST)
        placed2, _R, _t, _rc = placement.attempt_place(
            self.benzene_raw, _BENZENE_RING, c2, n2, r2, self.interaction)
        self.assertIsNone(placement.gate(placed2, existing,
                                         _BOX_SMALL[0], _BOX_SMALL[1],
                                         _DISPLAY_Z))

    def test_placement_overlapping_a_live_pickup_is_an_atom_violation(self):
        placed = self._placed_on_head()
        # A still-live pickup occupying the landing zone blocks the stack
        # (research open Q7: other live pickups are part of the gate set).
        existing = _xyz(self.head) + placed  # coincident live pickup
        violation = placement.gate(placed, existing,
                                   _BOX_SMALL[0], _BOX_SMALL[1], _DISPLAY_Z)
        self.assertIsNotNone(violation)
        self.assertEqual(violation['kind'], 'atom')

    def test_placement_past_the_display_z_face_is_a_wall_violation(self):
        placed = [('C', 0.0, 0.0, _DISPLAY_Z + 0.5)]
        violation = placement.gate(placed, [],
                                   _BOX_SMALL[0], _BOX_SMALL[1], _DISPLAY_Z)
        self.assertIsNotNone(violation)
        self.assertEqual(violation['kind'], 'wall')
        self.assertAlmostEqual(violation['distance'], 0.5, places=9)

    def test_placement_past_the_xy_face_is_a_wall_violation(self):
        placed = [('C', _BOX_SMALL[1][0] + 0.25, 0.0, 0.0)]
        violation = placement.gate(placed, [],
                                   _BOX_SMALL[0], _BOX_SMALL[1], _DISPLAY_Z)
        self.assertEqual(violation['kind'], 'wall')
        self.assertAlmostEqual(violation['distance'], 0.25, places=9)

    def test_z_bounds_are_symmetric_about_zero(self):
        high = placement.gate([('C', 0.0, 0.0, 5.5)], [],
                              _BOX_SMALL[0], _BOX_SMALL[1], _DISPLAY_Z)
        low = placement.gate([('C', 0.0, 0.0, -5.5)], [],
                             _BOX_SMALL[0], _BOX_SMALL[1], _DISPLAY_Z)
        self.assertEqual(high, low)


class TestBiphenylRefusal(_FixtureBase):
    """Task 2 pin 6 (locked decision: biphenyl is the permanent refuse-path
    demonstrator — DATA OBSERVATION, never to be fixed): the shipped
    biphenyl conformer has its rings at 90.00 deg, so every biphenyl stack
    at dataset geometry clashes (matrix minima 0.688-2.145 A < 2.5 A).
    resolve() must route it to ('refused', REFUSE_ATOM) with the measured
    distance, never to 'placed' and never by fudging the data.

    display_z=7.0 in this test only lifts the DISPLAY box above biphenyl's
    z-extent (probe: max |z| 6.914 A) so the ATOM check is what refuses —
    the plan pins the atom refusal specifically."""

    def _biphenyl_pickup(self):
        record = self.records_by_id['biphenyl']
        return {
            'molecule_id': 'biphenyl',
            'id': 'biphenyl',
            'set': record['set'],
            'has_stack_entry': record['has_stack_entry'],
            'stack_ring': record['stack_ring'],
            'atoms': self.biphenyl_raw,
            'atoms_n': len(self.biphenyl_raw),
        }

    def test_biphenyl_refuses_with_atom_clash_and_distance_detail(self):
        outcome = placement.resolve(
            self._biphenyl_pickup(), self.records_by_id, self.stacking_data,
            self.head, _BENZENE_RING, _HEADING_EAST,
            [], _xyz(self.head),
            _BOX_SMALL[0], _BOX_SMALL[1], _WIDE_DISPLAY_Z)
        self.assertEqual(outcome['status'], 'refused')
        self.assertEqual(outcome['code'], placement.REFUSE_ATOM)
        self.assertEqual(set(outcome), {'status', 'code', 'detail'})
        # Detail carries the measured clash distance formatted '%.2f A'.
        tail = outcome['detail']
        self.assertTrue(tail.endswith(' A'), tail)
        measured = float(tail[:-2])
        self.assertLess(measured, stacking.CLASH_THRESHOLD_A)
        self.assertGreater(measured, 0.0)


class TestResolveOrchestrator(_FixtureBase):
    """Task 2 pin 7 (STACK-01/03/05 outcome contract): resolve() assembles
    skip -> tail -> place -> gate and returns the exact outcome dicts. As a
    PURE function it never mutates engine state, so the GUI can ALWAYS call
    engine.reject_pickup on skip/refuse (capture/rollback symmetry — the
    win-vs-clash desync fix itself is plan 05-04's engine change)."""

    def _benzene_pickup(self):
        record = self.records_by_id['benzene']
        return {
            'molecule_id': 'benzene',
            'id': 'benzene',
            'set': record['set'],
            'has_stack_entry': record['has_stack_entry'],
            'stack_ring': record['stack_ring'],
            'atoms': self.benzene_raw,
            'atoms_n': len(self.benzene_raw),
        }

    def test_happy_path_returns_full_placed_contract(self):
        outcome = placement.resolve(
            self._benzene_pickup(), self.records_by_id, self.stacking_data,
            self.head, _BENZENE_RING, _HEADING_EAST,
            [], _xyz(self.head),
            _BOX_SMALL[0], _BOX_SMALL[1], _DISPLAY_Z)
        self.assertEqual(outcome['status'], 'placed')
        self.assertEqual(
            set(outcome),
            {'status', 'placed_atoms', 'R', 't', 'ring_centroid_xy',
             'interaction', 'citation_short'})
        placed = outcome['placed_atoms']
        self.assertEqual(len(placed), len(self.benzene_raw))
        for atom in placed:
            self.assertEqual(len(atom), 4)
        self.assertEqual([a[0] for a in placed],
                         [a[0] for a in self.benzene_raw])
        self.assertIs(outcome['interaction'], self.interaction)
        self.assertEqual(outcome['citation_short'], 'Janiak 2000')
        # ring_centroid_xy is the engine-attachable 2D centroid of the
        # placed ring, at the dataset geometry behind the head.
        rc = outcome['ring_centroid_xy']
        self.assertEqual(len(rc), 2)
        placed_c = stacking.ring_frame(_xyz(placed), _BENZENE_RING)[0]
        self.assertAlmostEqual(rc[0], placed_c[0], places=12)
        self.assertAlmostEqual(rc[1], placed_c[1], places=12)
        self.assertLess(rc[0], self.head_c[0])

    def test_upload_capture_skips_no_entry_without_placing(self):
        upload_rec = {'set': '__upload__', 'has_stack_entry': False,
                      'atoms': self.benzene_raw}
        outcome = placement.resolve(
            upload_rec, self.records_by_id, self.stacking_data,
            self.head, _BENZENE_RING, _HEADING_EAST,
            [], _xyz(self.head),
            _BOX_SMALL[0], _BOX_SMALL[1], _DISPLAY_Z)
        self.assertEqual(outcome, {'status': 'skipped',
                                   'code': placement.SKIP_NO_ENTRY})

    def test_wall_placement_refuses_with_wall_code(self):
        # Head parked 10 A west: the 3.6 A stack lands past the -x face.
        head_w = _translated(self.head, -10.0, 0.0)
        outcome = placement.resolve(
            self._benzene_pickup(), self.records_by_id, self.stacking_data,
            head_w, _BENZENE_RING, _HEADING_EAST,
            [], _xyz(head_w),
            _BOX_SMALL[0], _BOX_SMALL[1], _DISPLAY_Z)
        self.assertEqual(outcome['status'], 'refused')
        self.assertEqual(outcome['code'], placement.REFUSE_WALL)
        self.assertTrue(outcome['detail'].endswith(' A'))


if __name__ == '__main__':
    unittest.main()
