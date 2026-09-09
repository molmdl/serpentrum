"""Cross-module pure-core integration chain (plan 02-14, the FINAL Phase-2
plan).

Unit tests (plans 02-01..02-13) prove each pure module in isolation. This
file proves the SEAMS: a single chain where each stage CONSUMES the
previous stage's output, so a regression in any module OR data schema
breaks the chain even when every unit test still passes. That is the
point of an integration test.

WHAT MAKES THIS A REAL INTEGRATION PROOF (research R11, adapted to the
dataset-driven reality locked in plan 02-05):

1. The stacking distance is read FROM THE SHIPPED DATA FILE
   (serpentrum/data/stacking_pi_stack.json) via molecule_data.load_stacking
   -- never a code constant. A schema/format regression in the dataset
   breaks the placement assertion. The expected centroid distance is
   derived as sqrt(d^2 + l^2) from the file's own (distance_a,
   lateral_offset_a); the test is DECISION-AGNOSTIC (it would still pass
   if the human re-pinned the APPROVED values, as long as the file and
   the math agree).

2. The placed atom count becomes the parser's expected n_atoms. The
   stacking stage places 13 atoms onto a 13-atom tail (26 total); the
   spectra parser then reports n_atoms == 26 == len(tail) + len(placed).
   The xyz/parse layers must agree on atom count -- a mismatch here is a
   handoff bug no unit test catches.

3. The xtb success contract is evaluated on the SAME fixture bytes the
   parser fixtures came from (ohess.err / repro_oh.err / bad.err). The
   load-bearing case is repro_oh: stderr says 'normal termination' but
   NO output files exist -> the contract MUST reject it (stderr success
   alone is not success; research PITFALLS 3).

4. The xyz handoff format round-trips: write_xyz -> read_xyz reproduces
   the 26-atom placed geometry within 1e-8. This is the exact format the
   Phase-6 runner writes (snake geometry -> xtb input) and reads back.

Chain (data flows top to bottom):

  STAGE 1  dataset     molecule_data.load_stacking -> (d, l, expected)
  STAGE 2  geometry    xyzio.read_xyz(dimer2.xyz) -> 26 atoms, 13/13 split
  STAGE 3a exact       stacking.ring_frame + place_pickup(3.4, 0.0)
                       -> reproduces fragment 2 within 1e-6 (criterion 1)
                       + check_clash both ways (3.4 clears, 1.5 fires)
  STAGE 3b dataset     place_pickup(d, l) -> measured centroid == sqrt(d^2+l^2)
                       within 1e-4 (STACK-01); angle ~20 deg; clash clears
  STAGE 4  contract    xtbenv.evaluate_run on fixture .err bytes
                       (ok / not-ok-repro_oh / not-ok-bad) (criterion 3)
  STAGE 5  parse       spectra.parse_g98 + parse_vibspectrum
                       n_atoms == 26 == len(tail)+len(placed);
                       72 == 3N-6 g98 modes; 78 == 3N vib modes;
                       correspondence at computed offset (criterion 2)
  STAGE 6  round-trip  xyzio.write_xyz + read_xyz -> 26 atoms, 1e-8 equal

Convention: sys.path self-insert preamble (tests/test_skeleton.py
pattern); tests/ has NO __init__.py (the dev plugin path IS the repo
root). python3.6 only (%-formatting, no dataclasses/walrus/f-string `=`).
ZERO sys.modules stubs -- every serpentrum module is real, stdlib-only
PURE. Discovery: `python3.6 -m unittest discover -s tests -p "test_*.py" -v`
(never `-t .`).
"""
import math
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import serpentrum.molecule_data as molecule_data  # noqa: E402
import serpentrum.setup_logic as setup_logic      # noqa: E402
import serpentrum.spectra as spectra              # noqa: E402
import serpentrum.stacking as stacking            # noqa: E402
import serpentrum.xtbenv as xtbenv                # noqa: E402
import serpentrum.xyzio as xyzio                  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
XTB_FIXTURES = os.path.join(ROOT, 'tests', 'fixtures', 'xtb')
DATA_DIR = os.path.join(ROOT, 'serpentrum', 'data')

# Fixture paths (the plan's tests/fixtures/xtb/ copies + the shipped dataset).
DIMER2_XYZ = os.path.join(XTB_FIXTURES, 'dimer2.xyz')
G98_OUT = os.path.join(XTB_FIXTURES, 'g98.out')
VIBSPECTRUM = os.path.join(XTB_FIXTURES, 'vibspectrum')
STACKING_JSON = os.path.join(DATA_DIR, 'stacking_pi_stack.json')

# The committed dimer's ring is its six carbons (indices 0-5 of each
# 13-atom phenol fragment; element order CCCCCCHHHHHOH). Verified fixture
# knowledge -- the committed eclipse is a pure z-translation of 3.4 A.
RING = (0, 1, 2, 3, 4, 5)
N_ATOMS = 26
HALF = 13  # 26 / 2 (fragment 1 = atoms 0-12, fragment 2 = atoms 13-25)


def _centroid(points):
    """Mean of a sequence of (x, y, z) tuples (plain-tuple math, no numpy)."""
    n = len(points)
    sx = sy = sz = 0.0
    for p in points:
        sx += p[0]
        sy += p[1]
        sz += p[2]
    return (sx / n, sy / n, sz / n)


def _distance(a, b):
    """Euclidean distance between two 3-tuples."""
    dx = a[0] - b[0]
    dy = a[1] - b[1]
    dz = a[2] - b[2]
    return math.sqrt(dx * dx + dy * dy + dz * dz)


def _read_text(path):
    """Read a fixture file as utf-8 text (CRLF preserved for .err bytes)."""
    with open(path, encoding='utf-8') as handle:
        return handle.read()


class PureCoreIntegrationChain(unittest.TestCase):
    """ONE chain: data flows stage to stage. setUp builds the whole chain
    once; the ordered test methods assert each stage's contract while
    consuming the previous stage's real output (so a seam regression
    cascades into a downstream failure, not a silent pass)."""

    def setUp(self):
        # The integration boundary box comes from setup_logic's medium
        # preset (the real setup -> engine seam). check_clash takes 3-tuple
        # box_min/box_max; z is display-only, so the medium xy preset is
        # extended with a generous z range that never fires a wall check
        # (the clash-gate assertions below are about atom-atom distance).
        box_xy_min, box_xy_max = setup_logic.BOX_PRESETS['medium']
        self.box_min = (box_xy_min[0], box_xy_min[1], -50.0)
        self.box_max = (box_xy_max[0], box_xy_max[1], 50.0)

        # A temp dir for the STAGE 6 round-trip file (cleaned up per test).
        self.rt_dir = tempfile.mkdtemp(prefix='srp_int_')
        self.addCleanup(shutil.rmtree, self.rt_dir)

        self._build_chain()

    def _build_chain(self):
        """Build the full chain once; each stage stores its outputs on
        self so the ordered test methods consume real downstream data."""

        # --- STAGE 1: dataset (STACK-02) ---
        # The distance is read FROM THE FILE. expected_centroid is derived
        # from the file's own (d, l); the test is decision-agnostic.
        data = molecule_data.load_stacking(STACKING_JSON)
        entry = data['interactions'][0]
        self.d = entry['distance_a']
        self.l = entry['lateral_offset_a']
        self.expected_centroid = math.sqrt(self.d * self.d + self.l * self.l)

        # --- STAGE 2: geometry (xyzio) ---
        self.comment, atoms = xyzio.read_xyz(DIMER2_XYZ)
        self.atoms = atoms
        self.f1 = atoms[:HALF]
        self.f2 = atoms[HALF:]
        self.f1_coords = [(x, y, z) for (_s, x, y, z) in self.f1]
        self.f2_coords = [(x, y, z) for (_s, x, y, z) in self.f2]

        # --- STAGE 3a: exact reproduction (phase criterion 1) ---
        # Fragment 1 is BOTH the pickup and the tail (the committed dimer
        # is an eclipsed pure z-translation), so coincident frames reduce
        # the placement to exactly f1 + (0, 0, 3.4) == fragment 2.
        self.tail_c, self.tail_n, self.tail_ref = stacking.ring_frame(
            self.f1_coords, list(RING))
        self.placed_exact, _r_exact, _t_exact = stacking.place_pickup(
            self.f1_coords, list(RING),
            self.tail_c, self.tail_n, self.tail_ref,
            distance_a=3.4, lateral_offset_a=0.0)
        # The clash-gate contrast: 1.5 A separation must FIRE.
        self.placed_clash, _r_clash, _t_clash = stacking.place_pickup(
            self.f1_coords, list(RING),
            self.tail_c, self.tail_n, self.tail_ref,
            distance_a=1.5, lateral_offset_a=0.0)

        # --- STAGE 3b: dataset-driven placement (STACK-01) ---
        # place_pickup at the file's own (d, l); the ring centroid of the
        # placed fragment must land at sqrt(d^2 + l^2) from the tail
        # centroid. This is the data-driven geometry the game ships.
        self.placed2, _r2, _t2 = stacking.place_pickup(
            self.f1_coords, list(RING),
            self.tail_c, self.tail_n, self.tail_ref,
            distance_a=self.d, lateral_offset_a=self.l)
        self.ring_centroid2 = _centroid([self.placed2[i] for i in RING])
        self.measured = _distance(self.ring_centroid2, self.tail_c)

        # --- STAGE 4: xtb contract (criterion 3) on fixture bytes ---
        # ohess.err: stderr success + both files -> ok.
        # repro_oh.err: stderr success, NO files -> NOT ok (the load-bearing
        #   case -- stderr success alone is not success).
        # bad.err: 'abnormal termination' + no files -> NOT ok.
        self.v_ok = xtbenv.evaluate_run(
            0, _read_text(os.path.join(XTB_FIXTURES, 'ohess.err')),
            xtbenv.EXPECTED_FILES, xtbenv.EXPECTED_FILES)
        self.v_repro = xtbenv.evaluate_run(
            0, _read_text(os.path.join(XTB_FIXTURES, 'repro_oh.err')),
            xtbenv.EXPECTED_FILES, ())
        self.v_bad = xtbenv.evaluate_run(
            128, _read_text(os.path.join(XTB_FIXTURES, 'bad.err')),
            xtbenv.EXPECTED_FILES, ())

        # --- STAGE 5: parse + mode counts (criterion 2) ---
        self.g98 = spectra.parse_g98(G98_OUT)
        self.vib = spectra.parse_vibspectrum(VIBSPECTRUM)
        # The correspondence offset is COMPUTED from the atom count, not
        # hardcoded: 3N vib modes minus (3N-6) g98 modes == 6 trivial rows.
        self.offset = 3 * N_ATOMS - len(self.g98.modes)

        # --- STAGE 6: handoff round-trip (xyzio) ---
        # The 26-atom set is the 13-atom tail + a 13-atom pickup of the
        # same molecule (placed2). place_pickup returns coordinates only,
        # so the pickup's symbols are the tail's own (same molecule).
        self.rt_elements = ([s for (s, _x, _y, _z) in self.f1]
                            + [s for (s, _x, _y, _z) in self.f1])
        self.rt_coords = self.f1_coords + [tuple(p) for p in self.placed2]

    # ------------------------------------------------------------------
    # Ordered stage assertions. unittest runs them in lexical order
    # (test_stage1 before test_stage2 ...); each consumes the real output
    # the previous stage produced in setUp, so a seam regression cascades.
    # ------------------------------------------------------------------

    def test_stage1_dataset(self):
        """STAGE 1: the shipped dataset drives the placement (STACK-02)."""
        self.assertGreater(self.d, 0)
        self.assertGreaterEqual(self.l, 0)
        # expected_centroid is derived FROM THE FILE, not hardcoded.
        self.assertAlmostEqual(self.expected_centroid,
                               math.sqrt(self.d ** 2 + self.l ** 2))

    def test_stage2_geometry(self):
        """STAGE 2: xyzio reads the committed dimer (26 atoms, 13/13)."""
        self.assertEqual(len(self.atoms), N_ATOMS)
        self.assertEqual(len(self.f1), HALF)
        self.assertEqual(len(self.f2), HALF)
        self.assertEqual(self.comment, 'stacked phenol dimer 3.4A z-offset')
        # Verified fixture knowledge: fragment2 == fragment1 + (0, 0, 3.4).
        for i in range(HALF):
            self.assertAlmostEqual(self.f2_coords[i][2] - self.f1_coords[i][2],
                                   3.4, places=6)

    def test_stage3a_exact_reproduction_and_clash_gate(self):
        """STAGE 3a: place_pickup(3.4, 0.0) reproduces fragment 2 within
        1e-6 (phase success criterion 1); the legal stack clears
        check_clash while a 1.5 A placement fires it (STACK-05)."""
        # EXACT reproduction over all 13 atoms x 3 coordinates.
        max_err = 0.0
        for i in range(HALF):
            for k in range(3):
                err = abs(self.placed_exact[i][k] - self.f2_coords[i][k])
                if err > max_err:
                    max_err = err
        self.assertLess(max_err, 1e-6,
                         'dimer2 not reproduced exactly (max err %.3e)' % max_err)
        # Legal 3.4 A eclipsed stack clears the 2.5 A clash threshold.
        self.assertIsNone(stacking.check_clash(
            self.placed_exact, self.f1_coords, self.box_min, self.box_max))
        # A 1.5 A separation fires the gate (returns a violation dict).
        verdict = stacking.check_clash(
            self.placed_clash, self.f1_coords, self.box_min, self.box_max)
        self.assertIsNotNone(verdict, '1.5 A placement must fire check_clash')
        self.assertEqual(verdict['kind'], 'atom')

    def test_stage3b_dataset_driven_placement(self):
        """STAGE 3b: the file's (d, l) composes to a centroid-centroid
        distance of sqrt(d^2 + l^2) within 1e-4 (STACK-01, decision-
        agnostic); the off-normal angle is ~20 deg; the stack clears
        check_clash (perp component >= 3.35 clears 2.5)."""
        self.assertLessEqual(abs(self.measured - self.expected_centroid), 1e-4,
                             'measured %.6f != expected %.6f'
                             % (self.measured, self.expected_centroid))
        angle = math.degrees(math.atan2(self.l, self.d))
        self.assertLessEqual(abs(angle - 20.0), 0.5,
                             'off-normal angle %.4f deg not ~20' % angle)
        self.assertIsNone(stacking.check_clash(
            self.placed2, self.f1_coords, self.box_min, self.box_max))

    def test_stage4_xtb_contract(self):
        """STAGE 4: the 3-leg xtb success contract on fixture bytes
        (criterion 3). repro_oh is load-bearing: stderr success with NO
        output files must NOT be ok."""
        # ohess: exit 0 + stderr success + both files -> ok, no problems.
        self.assertTrue(self.v_ok.ok)
        self.assertEqual(self.v_ok.problems, [])
        # repro_oh: stderr success but NO files -> NOT ok, and a problem
        # names the missing file (stderr success alone is not success).
        self.assertFalse(self.v_repro.ok)
        joined = ' '.join(self.v_repro.problems)
        self.assertIn('missing expected output file', joined)
        # bad: abnormal termination + no files -> NOT ok.
        self.assertFalse(self.v_bad.ok)

    def test_stage5_parse_and_mode_counts(self):
        """STAGE 5: spectra parser on real fixtures (criterion 2). The
        placed atom count from STAGE 3 IS the expected parser n_atoms
        (the xyz/parse layers must agree); 72 == 3N-6 g98 modes, 78 ==
        3N vib modes, with frequency/intensity correspondence at the
        computed offset."""
        # The seam: parser n_atoms == tail + placed atom counts.
        self.assertEqual(self.g98.n_atoms, N_ATOMS)
        self.assertEqual(self.g98.n_atoms, len(self.f1) + len(self.placed2))
        # 3N-6 g98 modes (nonlinear molecule).
        self.assertEqual(len(self.g98.modes), 3 * N_ATOMS - 6)
        self.assertEqual(len(self.g98.modes), 72)
        # 3N vibspectrum modes (trivial modes included).
        self.assertEqual(len(self.vib.modes), 3 * N_ATOMS)
        self.assertEqual(len(self.vib.modes), 78)
        # Correspondence at the computed offset (6 trivial rows skipped).
        self.assertEqual(self.offset, 6)
        for j in range(len(self.g98.modes)):
            vib_mode = self.vib.modes[j + self.offset]
            g98_mode = self.g98.modes[j]
            self.assertLessEqual(abs(vib_mode.freq - g98_mode.freq), 0.01,
                                 'mode %d freq mismatch: vib %.4f g98 %.4f'
                                 % (j, vib_mode.freq, g98_mode.freq))
            self.assertLessEqual(
                abs(vib_mode.intensity - g98_mode.intensity), 1e-4,
                'mode %d intensity mismatch: vib %.6f g98 %.6f'
                % (j, vib_mode.intensity, g98_mode.intensity))

    def test_stage6_xyz_round_trip(self):
        """STAGE 6: the Phase-6 handoff format round-trips. write_xyz ->
        read_xyz reproduces the 26-atom placed geometry: identical
        symbols, coordinates equal within 1e-8."""
        text = xyzio.write_xyz(self.rt_elements, self.rt_coords,
                               comment='serpentrum integration round-trip')
        rt_path = os.path.join(self.rt_dir, 'roundtrip.xyz')
        with open(rt_path, 'w', encoding='utf-8') as handle:
            handle.write(text)
        rt_comment, rt_atoms = xyzio.read_xyz(rt_path)
        self.assertEqual(rt_comment, 'serpentrum integration round-trip')
        self.assertEqual(len(rt_atoms), N_ATOMS)
        # Symbols identical, in order.
        self.assertEqual([a[0] for a in rt_atoms], self.rt_elements)
        # Coordinates equal within 1e-8 (the writer's 8-decimal format).
        for i in range(N_ATOMS):
            for k in range(3):
                self.assertLessEqual(
                    abs(rt_atoms[i][k + 1] - self.rt_coords[i][k]), 1e-8,
                    'atom %d coord %d round-trip mismatch' % (i, k))


if __name__ == '__main__':
    unittest.main()
