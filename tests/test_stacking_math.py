"""Data-driven stacking-math tests: ring_frame / place_pickup / check_clash.

Plan 02-04 (STACK-01/02/05, phase success criterion 1). Discovery command
(verified on 3.6.9 -- NOTE: `-t .` FAILS on python3.6 with a non-package
start dir; do not add it):

    python3.6 -m unittest discover -s tests -p "test_*.py" -v

Convention: this file repeats the sys.path self-insert below
(tests/test_skeleton.py pattern); tests/ deliberately has NO __init__.py
(the dev plugin path IS the repo root).

Fixture provenance: the committed pi-stacked phenol dimer
`.planning/research/xtb-spike-fixtures/dimer2.xyz` is read IN PLACE
(no copy; parallel-worktree-safe). VERIFIED ground truth
(02-RESEARCH-pure-core.md section 1.5): 26 atoms, comment
"stacked phenol dimer 3.4A z-offset"; fragment 1 = indices 0-12,
fragment 2 = 13-25, same element sequence; fragment2 == fragment1 +
(0, 0, 3.4) with max error 0.0 over all 13 atoms; ring = indices 0-5
(the six carbons); ring centroid (0.012766437, -0.454242937, ~0.0);
Newell normal (0, 0, 1) to 9+ decimals; planarity deviation ~2.8e-10 A.
Fragment 1 is BOTH the pickup and the tail here -- the committed dimer is
an ECLIPSED pure z-translation, so with coincident pickup/tail frames the
placement must reduce to exactly that translation (R = identity,
t = (0, 0, 3.4)). phenol.xyz is NOT fragment 1 (max diff 0.0226 A -- a
different conformer) and is intentionally unused.

Distance provenance: STACK_D = 3.4 is a fixture-derived TEST CONSTANT
(dimer2's stored inter-fragment offset). The FILE-driven variant -- the
distance read from the stacking dataset via molecule_data -- is a
later-wave integration test (molecule_data is a parallel wave-1 plan).

Wave-1 parallelism: serpentrum.xyzio is deliberately NOT imported here; a
minimal inline parser keeps this plan self-contained.
"""
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import serpentrum.stacking as stacking  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURES = os.path.join(ROOT, '.planning', 'research', 'xtb-spike-fixtures')
DIMER2_XYZ = os.path.join(FIXTURES, 'dimer2.xyz')

# Verified fixture constants (must_haves of plan 02-04).
RING = (0, 1, 2, 3, 4, 5)                             # six ring carbons
EXPECTED_CENTROID = (0.012766437, -0.454242937, 0.0)  # R3 anchor
STACK_D = 3.4  # fixture-derived TEST CONSTANT (dimer2's stored z-offset)
BOX_MIN = (-18.0, -18.0, -5.0)
BOX_MAX = (18.0, 18.0, 5.0)


def _parse_xyz_atoms(path):
    """Minimal inline xyz reader (self-contained by design -- wave-1
    parallelism forbids importing serpentrum.xyzio in this plan)."""
    with open(path) as fh:
        lines = fh.read().splitlines()
    n = int(lines[0].strip())
    symbols = []
    coords = []
    for line in lines[2:2 + n]:
        parts = line.split()
        symbols.append(parts[0])
        coords.append((float(parts[1]), float(parts[2]), float(parts[3])))
    return symbols, coords


def _rot_z90(coords):
    """Pure-python +90-degree rotation about z: (x, y) -> (-y, x)."""
    return [(-p[1], p[0], p[2]) for p in coords]


def _dist(a, b):
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 +
                     (a[2] - b[2]) ** 2)


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _mean(points):
    n = len(points)
    return (sum(p[0] for p in points) / n,
            sum(p[1] for p in points) / n,
            sum(p[2] for p in points) / n)


_SYMBOLS, _COORDS = _parse_xyz_atoms(DIMER2_XYZ)
F1 = _COORDS[:13]
F2 = _COORDS[13:]

# Benzene-like planar hexagon (r = 1.4 A) for the synthetic planarity cases.
_HEX_Y = 1.4 * math.sqrt(3.0) / 2.0
_HEX_FLAT = [(1.4, 0.0, 0.0), (0.7, _HEX_Y, 0.0), (-0.7, _HEX_Y, 0.0),
             (-1.4, 0.0, 0.0), (-0.7, -_HEX_Y, 0.0), (0.7, -_HEX_Y, 0.0)]
_HEX_BUMPED = [(1.4, 0.0, 0.5)] + list(_HEX_FLAT[1:])  # one atom +0.5 A out


class TestDimer2Fixture(unittest.TestCase):
    """Pins the committed fixture contract the placement math relies on."""

    def test_fixture_contract(self):
        # 26 atoms, 13/13 split, same element sequence, and the VERIFIED
        # invariant: fragment2 == fragment1 + (0, 0, 3.4) exactly
        # (documented max abs error 0.0; asserted < 1e-9 for fp parse noise).
        self.assertEqual(len(_SYMBOLS), 26)
        self.assertEqual(len(F1), 13)
        self.assertEqual(len(F2), 13)
        self.assertEqual(_SYMBOLS[:13], _SYMBOLS[13:])
        max_err = max(abs(F2[i][k] - (F1[i][k] + (STACK_D if k == 2 else 0.0)))
                      for i in range(13) for k in range(3))
        self.assertLess(max_err, 1e-9)


class TestRingFrame(unittest.TestCase):
    """Case 1-3: deterministic ring frame + loud error paths."""

    def test_frame_on_dimer2_ring(self):
        # Case 1: verified centroid/normal, plus a sane reference axis.
        centroid, normal, ref = stacking.ring_frame(F1, RING)
        for k in range(3):
            self.assertAlmostEqual(centroid[k], EXPECTED_CENTROID[k], delta=1e-6)
        self.assertAlmostEqual(normal[0], 0.0, delta=1e-9)
        self.assertAlmostEqual(normal[1], 0.0, delta=1e-9)
        self.assertAlmostEqual(normal[2], 1.0, delta=1e-9)
        # ref: unit, perpendicular to the normal, pointing at ring atom 0.
        self.assertAlmostEqual(math.sqrt(ref[0] ** 2 + ref[1] ** 2 + ref[2] ** 2),
                               1.0, delta=1e-9)
        self.assertAlmostEqual(ref[0] * normal[0] + ref[1] * normal[1] +
                               ref[2] * normal[2], 0.0, delta=1e-9)
        atom0 = F1[RING[0]]
        toward0 = (ref[0] * (atom0[0] - centroid[0]) +
                   ref[1] * (atom0[1] - centroid[1]) +
                   ref[2] * (atom0[2] - centroid[2]))
        self.assertGreater(toward0, 0.0)

    def test_planar_control_does_not_raise(self):
        # Control for the tolerance direction: a planar ring must pass.
        centroid, normal, ref = stacking.ring_frame(_HEX_FLAT, (0, 1, 2, 3, 4, 5))
        self.assertGreater(normal[2], 0.99)

    def test_non_planar_ring_raises(self):
        # Case 2: one atom displaced 0.5 A out of plane -> loud ValueError.
        # (Pre-verified: max planarity deviation of this set is ~0.248 A.)
        with self.assertRaises(ValueError) as ctx:
            stacking.ring_frame(_HEX_BUMPED, (0, 1, 2, 3, 4, 5))
        self.assertIn('non-planar', str(ctx.exception))

    def test_too_few_atoms_raises(self):
        # Case 3a: fewer than 3 ring atoms.
        with self.assertRaises(ValueError) as ctx:
            stacking.ring_frame(F1, (0, 1))
        self.assertIn('ring', str(ctx.exception))

    def test_collinear_ring_raises(self):
        # Case 3b: three collinear points -> Newell normal length ~0.
        collinear = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (2.0, 0.0, 0.0)]
        with self.assertRaises(ValueError) as ctx:
            stacking.ring_frame(collinear, (0, 1, 2))
        self.assertIn('degenerate', str(ctx.exception))


class TestPlacePickup(unittest.TestCase):
    """Cases 4-6: rigid-body placement, azimuth alignment, lateral offset."""

    def setUp(self):
        self.centroid, self.normal, self.ref = stacking.ring_frame(F1, RING)

    def test_reproduces_dimer2_exactly(self):
        # Case 4 (THE test): placing fragment 1 at dimer2's stored offset
        # must reproduce the committed fragment 2 geometry. STACK_D is the
        # fixture-derived test constant (see module docstring).
        placed, rot, t = stacking.place_pickup(
            F1, RING, self.centroid, self.normal, self.ref, STACK_D, 0.0)
        max_err = max(_dist(placed[i], F2[i]) for i in range(13))
        self.assertLess(max_err, 1e-6)
        # R must be identity within 1e-9 (coincident frames).
        self.assertEqual(len(rot), 3)
        for i in range(3):
            self.assertEqual(len(rot[i]), 3)
            for j in range(3):
                expected = 1.0 if i == j else 0.0
                self.assertAlmostEqual(rot[i][j], expected, delta=1e-9)
        # t == (0, 0, 3.4) within 1e-6.
        for k, expected in enumerate((0.0, 0.0, STACK_D)):
            self.assertAlmostEqual(t[k], expected, delta=1e-6)

    def test_rotated_pickup_azimuth_aligned(self):
        # Case 5: a pickup rigidly rotated +90 deg about z, placed onto the
        # SAME tail frame with azimuth=0. The transform must genuinely
        # rotate (R != I, placed != rotated input) yet land parallel,
        # rigid, and azimuth-aligned -- which for a rigidly rotated copy
        # of fragment 1 means it lands exactly on the canonical stack
        # position (== fragment 2).
        pickup = _rot_z90(F1)
        placed, rot, _t = stacking.place_pickup(
            pickup, RING, self.centroid, self.normal, self.ref, STACK_D, 0.0)
        # Ring centroid sits one STACK_D step along the tail normal.
        target = tuple(self.centroid[k] + self.normal[k] * STACK_D
                       for k in range(3))
        ring_centroid = _mean([placed[i] for i in RING])
        for k in range(3):
            self.assertAlmostEqual(ring_centroid[k], target[k], delta=1e-6)
        # The rotation actually happened: R is far from identity...
        max_from_identity = max(abs(rot[i][j] - (1.0 if i == j else 0.0))
                                for i in range(3) for j in range(3))
        self.assertGreater(max_from_identity, 0.5)
        # ...and the placed atoms are NOT a pass-through of the rotated
        # input (the transform moved/rotated them).
        min_moved = min(_dist(placed[i], pickup[i]) for i in range(13))
        self.assertGreater(min_moved, 1.0)
        # Rigid transform: each placed atom keeps fragment 1's distance to
        # the stack-axis target point.
        for i in range(13):
            self.assertAlmostEqual(_dist(placed[i], target),
                                   _dist(F1[i], self.centroid), delta=1e-6)
        # Parallel planes: placed ring normal == tail normal (dot 1.0).
        _pc, placed_normal, _pr = stacking.ring_frame(placed, RING)
        self.assertAlmostEqual(placed_normal[0] * self.normal[0] +
                               placed_normal[1] * self.normal[1] +
                               placed_normal[2] * self.normal[2],
                               1.0, delta=1e-9)
        # Azimuth=0 is deterministic: the rotated pickup lands exactly on
        # the unrotated stack position (== committed fragment 2).
        max_err = max(_dist(placed[i], F2[i]) for i in range(13))
        self.assertLess(max_err, 1e-6)

    def test_lateral_offset_along_ref(self):
        # Case 6a: lateral offset along the tail reference axis; the plane
        # distance stays at STACK_D.
        placed, _rot, _t = stacking.place_pickup(
            F1, RING, self.centroid, self.normal, self.ref, STACK_D, 1.0,
            lateral_along_ref=True)
        ring_centroid = _mean([placed[i] for i in RING])
        expected = tuple(self.centroid[k] + self.normal[k] * STACK_D +
                         1.0 * self.ref[k] for k in range(3))
        for k in range(3):
            self.assertAlmostEqual(ring_centroid[k], expected[k], delta=1e-9)

    def test_lateral_offset_along_perp(self):
        # Case 6b: lateral offset along cross(tail_normal, tail_ref).
        placed, _rot, _t = stacking.place_pickup(
            F1, RING, self.centroid, self.normal, self.ref, STACK_D, 1.0,
            lateral_along_ref=False)
        ring_centroid = _mean([placed[i] for i in RING])
        perp = _cross(self.normal, self.ref)
        expected = tuple(self.centroid[k] + self.normal[k] * STACK_D +
                         1.0 * perp[k] for k in range(3))
        for k in range(3):
            self.assertAlmostEqual(ring_centroid[k], expected[k], delta=1e-9)


class TestCheckClash(unittest.TestCase):
    """Case 7-9 + threshold constant: the pure clash gate (STACK-05)."""

    def setUp(self):
        self.centroid, self.normal, self.ref = stacking.ring_frame(F1, RING)
        self.placed_legal, _rot, _t = stacking.place_pickup(
            F1, RING, self.centroid, self.normal, self.ref, STACK_D, 0.0)

    def test_threshold_is_module_constant(self):
        # 2.5 A: between xtb's rcov bond-inference risk ceiling (~2.0 A)
        # and the verified-safe 3.4 A dimer floor. Module constant, not a
        # user setting (v1).
        self.assertEqual(stacking.CLASH_THRESHOLD_A, 2.5)

    def test_legal_stack_passes(self):
        # Case 7: the legal 3.4 A stack passes its own gate (min
        # inter-fragment contact 3.4000 A >= 2.5 A; all atoms in-box).
        self.assertIsNone(stacking.check_clash(
            self.placed_legal, F1, BOX_MIN, BOX_MAX))

    def test_close_placement_fires_atom_clash(self):
        # Case 8: 1.5 A placement -> atom clash on the first scanned pair
        # (i ascending, then j ascending -> (0, 0), the eclipsed contact).
        placed_close, _rot, _t = stacking.place_pickup(
            F1, RING, self.centroid, self.normal, self.ref, 1.5, 0.0)
        result = stacking.check_clash(placed_close, F1, BOX_MIN, BOX_MAX)
        self.assertIsNotNone(result)
        self.assertEqual(result['kind'], 'atom')
        i, j = result['pair']
        self.assertIsInstance(i, int)
        self.assertIsInstance(j, int)
        self.assertEqual((i, j), (0, 0))
        self.assertLess(result['distance'], 2.5)
        self.assertGreater(result['distance'], 1.0)

    def test_wall_violation_fires(self):
        # Case 9a: placed atoms pushed past x = 18 -> wall diagnostic on
        # the first violating atom, carrying the violation amount.
        shifted = [(p[0] + 18.5, p[1], p[2]) for p in self.placed_legal]
        result = stacking.check_clash(shifted, F1, BOX_MIN, BOX_MAX)
        self.assertIsNotNone(result)
        self.assertEqual(result['kind'], 'wall')
        self.assertEqual(result['pair'], (0, None))
        # Atom 0 sits at x = 18.5209034311 -> 0.5209034311 A past the wall.
        self.assertAlmostEqual(result['distance'], 0.5209034311, delta=1e-9)
        self.assertGreater(result['distance'], 0.0)

    def test_wall_reports_worst_axis(self):
        # Case 9c: an atom violating on two axes reports the LARGEST
        # violation amount (x: 0.5, y: 1.0 -> 1.0).
        result = stacking.check_clash([(18.5, 19.0, 0.0)], F1,
                                      BOX_MIN, BOX_MAX)
        self.assertIsNotNone(result)
        self.assertEqual(result['kind'], 'wall')
        self.assertEqual(result['pair'], (0, None))
        self.assertAlmostEqual(result['distance'], 1.0, delta=1e-9)

    def test_boundary_is_inclusive(self):
        # Case 9b: atoms exactly ON the boundary do NOT violate (coords
        # equal to box_min/box_max are legal); just past it does.
        self.assertIsNone(stacking.check_clash(
            [(18.0, 0.0, 0.0)], F1, BOX_MIN, BOX_MAX))
        self.assertIsNone(stacking.check_clash(
            [(-18.0, 0.0, 0.0)], F1, BOX_MIN, BOX_MAX))
        self.assertIsNone(stacking.check_clash(
            [(18.0, 18.0, 5.0)], F1, BOX_MIN, BOX_MAX))
        result = stacking.check_clash([(18.5, 0.0, 0.0)], F1,
                                      BOX_MIN, BOX_MAX)
        self.assertIsNotNone(result)
        self.assertEqual(result['kind'], 'wall')
        self.assertAlmostEqual(result['distance'], 0.5, delta=1e-9)


if __name__ == '__main__':
    unittest.main()
