"""Orientation-math pinning tests (plan 05-02, G5 pure half).

Provenance and pins:

- Probe-A1 fixture (LOCKED layout): ``matrix_rt`` composes the exact
  16-float list PyMOL 2.5.0 ``cmd.transform_selection`` accepts, verified
  end-to-end headless (05-RESEARCH-pymol-mechanics.md, probes A1/A2, max
  error <= 1.2e-07 A; source: pymol-src editing.py:1962-1988). Layout:
  rows 0-2 cols 0-2 = row-major R applied to the column vector, col 3 =
  post-translation, bottom row = pre-translation (y = R.(x+pre) + t).
- Pivot idiom (probe-A2 pattern): rotation about pivot O is
  ``matrix_rt(R, O, pre=-O)`` -- no hand-rolled translate-rotate-translate.
- Edge-on invariants + z-span anchors: LOCKED 03-08 + 04-07 presentation
  decision (ring planes perpendicular to the screen xy plane). The azimuth
  rule is planner-pinned: of the two in-plane ring axes the LONGER span
  lands on +y (the visible screen axis carrying the dataset's lateral
  offset), the SHORTER on +z, so the worst post-edge-on z-extent
  (phenanthrene 7.144 A) keeps BOX_DISPLAY_Z = 5.0 valid. Anchors are the
  research probe-F 'best' column (05-RESEARCH-pymol-mechanics.md open
  question 1 table, atom centers, all atoms incl. H).
- Ring tuples below are the probe-verified canonical single-ring cycles
  from 05-RESEARCH-core-integration.md "ring_extraction_spec" (plan 05-01
  will ship them via ``molfile.ring_cycle``; pinned here directly so this
  module's pins are self-contained).

Real data only: all five demo SDFs are read in place via molfile.read_sdf;
zero stubs. Discovery (per module convention in test_stacking_math.py):

    python3.6 -m unittest tests.test_orientation -v
python3.6.9 compatible: no f-strings, %-formatting only.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from serpentrum import molfile  # noqa: E402
from serpentrum import orientation  # noqa: E402
from serpentrum import stacking  # noqa: E402

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         'serpentrum', 'data')

# Probe-verified canonical cycles (ring_extraction_spec in
# 05-RESEARCH-core-integration.md; min-over-orientations rule).
RINGS = {
    'benzene': (0, 1, 3, 5, 4, 2),
    'naphthalene': (0, 1, 3, 7, 6, 2),
    'anthracene': (0, 1, 5, 3, 2, 4),
    'phenanthrene': (0, 1, 3, 5, 4, 2),
    'biphenyl': (0, 2, 6, 10, 8, 4),
}

# Research probe-F 'best' column: post-edge-on z-spans (short in-plane
# axis on z, longer on y), atom centers over ALL atoms. Tolerance 2e-3.
Z_SPAN_ANCHORS = {
    'benzene': 4.297,
    'naphthalene': 5.547,
    'anthracene': 6.770,
    'phenanthrene': 7.144,
    'biphenyl': 4.317,
}


def _load(name):
    records = molfile.read_sdf(os.path.join(_DATA_DIR, name + '.sdf'))
    assert len(records) == 1, '%s.sdf must hold exactly 1 record' % name
    return records[0]


class TestMatrixLayout(unittest.TestCase):
    """The ONE matrix composer, pinned float-for-float (pitfall P5-8)."""

    # The A1 layout fixture: R with off-axis entries in slots [1] and [4],
    # post-translation (1, 2, 3) in slots [3]/[7]/[11], zero pre.
    R_A1 = ((0.0, 1.0, 0.0),
            (-1.0, 0.0, 0.0),
            (0.0, 0.0, 1.0))
    # True +90 deg CCW about +z (column-vector convention; the exact matrix
    # used by probe A1/A2: maps +x -> +y).
    R_CCW90 = ((0.0, -1.0, 0.0),
               (1.0, 0.0, 0.0),
               (0.0, 0.0, 1.0))

    def test_a1_fixture_exact(self):
        m16 = orientation.matrix_rt(self.R_A1, (1.0, 2.0, 3.0),
                                    pre=(0.0, 0.0, 0.0))
        self.assertEqual(m16, [0.0, 1.0, 0.0, 1.0,
                               -1.0, 0.0, 0.0, 2.0,
                               0.0, 0.0, 1.0, 3.0,
                               0.0, 0.0, 0.0, 1.0])

    def test_pre_translation_lands_in_bottom_row(self):
        m16 = orientation.matrix_rt(self.R_A1, (1.0, 2.0, 3.0),
                                    pre=(0.1, 0.2, 0.3))
        self.assertEqual(len(m16), 16)
        self.assertAlmostEqual(m16[12], 0.1, places=15)
        self.assertAlmostEqual(m16[13], 0.2, places=15)
        self.assertAlmostEqual(m16[14], 0.3, places=15)
        self.assertEqual(m16[15], 1.0)
        # Post-translation stays in column 3.
        self.assertEqual((m16[3], m16[7], m16[11]), (1.0, 2.0, 3.0))

    def test_mat_vec3_row_major(self):
        # +90 deg CCW about z maps +x -> +y, +y -> -x, leaves +z.
        self.assertEqual(orientation.mat_vec3(self.R_CCW90, (1.0, 0.0, 0.0)),
                         (0.0, 1.0, 0.0))
        self.assertEqual(orientation.mat_vec3(self.R_CCW90, (0.0, 1.0, 0.0)),
                         (-1.0, 0.0, 0.0))
        self.assertEqual(orientation.mat_vec3(self.R_CCW90, (0.0, 0.0, 1.0)),
                         (0.0, 0.0, 1.0))

    def test_a2_pivot_idiom(self):
        # Rotating point (3, 0, 0) by +90 deg about pivot (1, 0, 0) must
        # give (1, 2, 0) -- matrix_rt(R, O, pre=-O), y = R.(x+pre) + t.
        pivot = (1.0, 0.0, 0.0)
        m16 = orientation.matrix_rt(self.R_CCW90, pivot,
                                    pre=(-pivot[0], -pivot[1], -pivot[2]))
        # Re-read R / t / pre out of the 16-float list (layout check) and
        # apply via mat_vec3.
        r_back = ((m16[0], m16[1], m16[2]),
                  (m16[4], m16[5], m16[6]),
                  (m16[8], m16[9], m16[10]))
        t_back = (m16[3], m16[7], m16[11])
        pre_back = (m16[12], m16[13], m16[14])
        point = (3.0, 0.0, 0.0)
        shifted = (point[0] + pre_back[0],
                   point[1] + pre_back[1],
                   point[2] + pre_back[2])
        out = orientation.mat_vec3(r_back, shifted)
        result = (out[0] + t_back[0], out[1] + t_back[1], out[2] + t_back[2])
        self.assertAlmostEqual(result[0], 1.0, delta=1e-9)
        self.assertAlmostEqual(result[1], 2.0, delta=1e-9)
        self.assertAlmostEqual(result[2], 0.0, delta=1e-9)


class TestEdgeOn(unittest.TestCase):
    """Edge-on canonicalization invariants over all 5 demo molecules."""

    @classmethod
    def setUpClass(cls):
        cls.records = dict((name, _load(name)) for name in RINGS)

    def _frame(self, name):
        rec = self.records[name]
        return orientation.edge_on_frame(rec['elements'], rec['coords'],
                                         RINGS[name])

    def test_normal_maps_to_plus_x(self):
        for name in RINGS:
            with self.subTest(molecule=name):
                rec = self.records[name]
                r_edge, _pre = self._frame(name)
                _centroid, normal, _ref = stacking.ring_frame(
                    rec['coords'], RINGS[name])
                mapped = orientation.mat_vec3(r_edge, normal)
                self.assertAlmostEqual(mapped[0], 1.0, delta=1e-9)
                self.assertAlmostEqual(mapped[1], 0.0, delta=1e-9)
                self.assertAlmostEqual(mapped[2], 0.0, delta=1e-9)

    def test_pre_is_neg_ring_centroid(self):
        for name in RINGS:
            with self.subTest(molecule=name):
                rec = self.records[name]
                _r_edge, pre = self._frame(name)
                centroid, _normal, _ref = stacking.ring_frame(
                    rec['coords'], RINGS[name])
                self.assertAlmostEqual(pre[0], -centroid[0], delta=1e-12)
                self.assertAlmostEqual(pre[1], -centroid[1], delta=1e-12)
                self.assertAlmostEqual(pre[2], -centroid[2], delta=1e-12)

    def test_ring_centroid_lands_at_origin(self):
        for name in RINGS:
            with self.subTest(molecule=name):
                rec = self.records[name]
                placed = orientation.edge_on_atoms(
                    rec['elements'], rec['coords'], RINGS[name])
                ring = RINGS[name]
                mean = [sum(placed[i][k] for i in ring) / len(ring)
                        for k in (1, 2, 3)]
                self.assertAlmostEqual(mean[0], 0.0, delta=1e-9)
                self.assertAlmostEqual(mean[1], 0.0, delta=1e-9)
                self.assertAlmostEqual(mean[2], 0.0, delta=1e-9)

    def test_ring_atoms_sit_on_the_yz_plane(self):
        # After edge-on the ring normal is +x, so every ring atom's x
        # coordinate (its normal coordinate) is ~0.
        for name in RINGS:
            with self.subTest(molecule=name):
                rec = self.records[name]
                placed = orientation.edge_on_atoms(
                    rec['elements'], rec['coords'], RINGS[name])
                for i in RINGS[name]:
                    self.assertAlmostEqual(placed[i][1], 0.0, delta=1e-9,
                                           msg='atom %d of %s' % (i, name))

    def test_z_span_anchors_and_longer_axis_on_y(self):
        for name in RINGS:
            with self.subTest(molecule=name):
                rec = self.records[name]
                placed = orientation.edge_on_atoms(
                    rec['elements'], rec['coords'], RINGS[name])
                ys = [a[2] for a in placed]
                zs = [a[3] for a in placed]
                y_span = max(ys) - min(ys)
                z_span = max(zs) - min(zs)
                self.assertAlmostEqual(z_span, Z_SPAN_ANCHORS[name],
                                       delta=2e-3,
                                       msg='%s z-span %.4f' % (name, z_span))
                self.assertTrue(z_span <= y_span + 1e-9,
                                '%s: z-span %.4f exceeds y-span %.4f'
                                % (name, z_span, y_span))

    def test_atoms_preserve_symbols_benzene_z_band(self):
        for name in RINGS:
            with self.subTest(molecule=name):
                rec = self.records[name]
                placed = orientation.edge_on_atoms(
                    rec['elements'], rec['coords'], RINGS[name])
                self.assertEqual(len(placed), len(rec['elements']))
                self.assertEqual([a[0] for a in placed],
                                 list(rec['elements']))
        # Benzene: every atom within half the 4.297 span of z = 0.
        rec = self.records['benzene']
        placed = orientation.edge_on_atoms(
            rec['elements'], rec['coords'], RINGS['benzene'])
        for atom in placed:
            self.assertTrue(abs(atom[3]) <= 2.149 + 2e-3,
                            'benzene atom z %.4f out of band' % atom[3])

    def test_m16_matches_matrix_rt_composition(self):
        for name in RINGS:
            with self.subTest(molecule=name):
                rec = self.records[name]
                r_edge, pre = self._frame(name)
                expected = orientation.matrix_rt(r_edge, (0.0, 0.0, 0.0), pre)
                actual = orientation.edge_on_m16(
                    rec['elements'], rec['coords'], RINGS[name])
                self.assertEqual(len(actual), 16)
                self.assertEqual(actual, expected)


if __name__ == '__main__':
    unittest.main()
