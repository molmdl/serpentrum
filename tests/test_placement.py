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


if __name__ == '__main__':
    unittest.main()
