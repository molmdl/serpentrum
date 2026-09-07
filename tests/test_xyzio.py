"""xyzio writer/reader tests + committed-fixture round-trips (02-03).

Discovery command (verified on python3.6.9 — NOTE: `-t .` FAILS on
python3.6 with a non-package start dir; do not add it):

    python3.6 -m unittest discover -s tests -p "test_*.py" -v

Fixtures are read IN PLACE from .planning/research/xtb-spike-fixtures/
(committed, so parallel worktrees see them; no copies are made).
dimer.xyz is deliberately NEVER used here: it is a mislabeled CO2 dimer
with a stale "phenol" comment (dimer2.xyz is the real pi-stacked dimer).
"""
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from serpentrum import xyzio  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURES = os.path.join(ROOT, '.planning', 'research',
                        'xtb-spike-fixtures')

# The four xtb-accepted geometry fixtures (round-trip targets).
ROUND_TRIP_FIXTURES = ('co2.xyz', 'phenol.xyz', 'dimer2.xyz', 'xtbopt.xyz')


def _assert_xyz_error(testcase, action, *needles):
    """Assert action() raises XyzError whose message contains all needles."""
    try:
        action()
    except xyzio.XyzError as exc:
        message = str(exc)
        for needle in needles:
            testcase.assertIn(needle, message)
    else:
        testcase.fail('XyzError not raised (wanted message containing %r)'
                      % (needles,))


class TestWriteXyz(unittest.TestCase):
    """Writer structure, row format, comment sanitization, validation."""

    def test_writer_structure_and_row_format(self):
        text = xyzio.write_xyz(['C', 'O'],
                               [(0.0, 0.0, 0.0), (1.16, 0.0, 0.0)],
                               'test comment')
        lines = text.splitlines()
        self.assertEqual(len(lines), 4)
        self.assertEqual(lines[0], '2')
        self.assertEqual(lines[1], 'test comment')
        # Direct string assertion on the '%-2s %15.8f %15.8f %15.8f' row
        # format (expected string probed against python3.6 '%'-formatting).
        self.assertEqual(lines[2],
                         'C       0.00000000      0.00000000'
                         '      0.00000000')
        self.assertEqual(lines[3],
                         'O       1.16000000      0.00000000'
                         '      0.00000000')

    def test_writer_output_round_trips_through_reader(self):
        text = xyzio.write_xyz(['C', 'O'],
                               [(0.0, 0.0, 0.0), (1.16, 0.0, 0.0)],
                               'test comment')
        comment, atoms = xyzio.read_xyz_text(text)
        self.assertEqual(comment, 'test comment')
        self.assertEqual(len(atoms), 2)
        self.assertEqual(atoms[0][0], 'C')
        self.assertEqual(atoms[1][0], 'O')
        self.assertAlmostEqual(atoms[0][1], 0.0, places=8)
        self.assertAlmostEqual(atoms[1][1], 1.16, places=8)
        self.assertAlmostEqual(atoms[1][2], 0.0, places=8)
        self.assertAlmostEqual(atoms[1][3], 0.0, places=8)

    def test_comment_newlines_sanitized(self):
        text = xyzio.write_xyz(['C'], [(0.0, 0.0, 0.0)], 'alpha\nbeta')
        lines = text.splitlines()
        # No newline survived into the frame: still exactly 3 lines.
        self.assertEqual(len(lines), 3)
        self.assertEqual(lines[1], 'alpha beta')
        comment, _atoms = xyzio.read_xyz_text(text)
        self.assertEqual(comment, 'alpha beta')

    def test_length_mismatch_rejected(self):
        _assert_xyz_error(
            self,
            lambda: xyzio.write_xyz(['C'],
                                    [(0.0, 0.0, 0.0), (1.0, 1.0, 1.0)]),
            '1 element symbols', '2 coordinate rows')
        _assert_xyz_error(
            self,
            lambda: xyzio.write_xyz(['C', 'O'], [(0.0, 0.0, 0.0)]),
            '2 element symbols', '1 coordinate rows')

    def test_row_not_three_long_rejected(self):
        _assert_xyz_error(
            self,
            lambda: xyzio.write_xyz(['C', 'O'],
                                    [(0.0, 0.0, 0.0), (1.0, 1.0)]),
            'atom 2 has 2 coordinates')


class TestReadFixtures(unittest.TestCase):
    """Exact reads of the committed, xtb-accepted geometry fixtures."""

    def test_read_co2(self):
        comment, atoms = xyzio.read_xyz(os.path.join(FIXTURES, 'co2.xyz'))
        self.assertEqual(comment, 'CO2 linear')
        self.assertEqual([a[0] for a in atoms], ['C', 'O', 'O'])
        self.assertAlmostEqual(atoms[0][1], 0.0, places=8)
        self.assertAlmostEqual(atoms[0][2], 0.0, places=8)
        self.assertAlmostEqual(atoms[0][3], 0.0, places=8)
        self.assertAlmostEqual(atoms[1][1], 1.16, places=8)
        self.assertAlmostEqual(atoms[2][1], -1.16, places=8)

    def test_read_phenol_leading_space_count_line(self):
        comment, atoms = xyzio.read_xyz(os.path.join(FIXTURES,
                                                     'phenol.xyz'))
        self.assertEqual(comment, 'Optimized at B3LYP/6-31G* level')
        self.assertEqual(len(atoms), 13)
        self.assertEqual(atoms[0][0], 'C')
        self.assertAlmostEqual(atoms[0][1], 0.02082100, places=8)
        self.assertAlmostEqual(atoms[0][2], -1.85733400, places=8)
        # Committed element order (research R1): 6 C, 5 ring-H, O, O-H.
        self.assertEqual([a[0] for a in atoms],
                         ['C'] * 6 + ['H'] * 5 + ['O', 'H'])

    def test_read_dimer2(self):
        comment, atoms = xyzio.read_xyz(os.path.join(FIXTURES,
                                                     'dimer2.xyz'))
        self.assertEqual(comment, 'stacked phenol dimer 3.4A z-offset')
        self.assertEqual(len(atoms), 26)


class TestRejections(unittest.TestCase):
    """Structural + symbol validation, each error naming a line number."""

    def test_bad_fixture_rejected_with_symbol_and_line(self):
        # bad.xyz line 3 is 'Xx 0.0 0.0 0.0' — the exact input that makes
        # xtb fail with 'Cannot map symbol to atomic number'.
        _assert_xyz_error(
            self,
            lambda: xyzio.read_xyz(os.path.join(FIXTURES, 'bad.xyz')),
            'line 3', 'Xx')

    def test_count_not_integer(self):
        _assert_xyz_error(self,
                          lambda: xyzio.read_xyz_text('abc\ncomment\n'),
                          'line 1', 'atom count must be an integer')

    def test_count_zero_rejected(self):
        _assert_xyz_error(self,
                          lambda: xyzio.read_xyz_text('0\ncomment\n'),
                          'line 1', 'atom count must be a positive integer')

    def test_count_exceeds_rows(self):
        text = '5\nc\nC 0 0 0\nO 1 0 0\n'
        _assert_xyz_error(self,
                          lambda: xyzio.read_xyz_text(text),
                          'line 1', 'declares 5 atoms', '2 atom rows')

    def test_extra_row_after_declared_count(self):
        text = '2\nc\nC 0 0 0\nO 1 0 0\nH 2 0 0\n'
        _assert_xyz_error(self,
                          lambda: xyzio.read_xyz_text(text),
                          'line 5', 'extra atom row')

    def test_row_too_few_tokens(self):
        text = '1\nc\nC 0.0 0.0\n'
        _assert_xyz_error(self,
                          lambda: xyzio.read_xyz_text(text),
                          'line 3', '4 whitespace-separated fields')

    def test_coordinate_not_float(self):
        text = '1\nc\nC zz 0.0 0.0\n'
        _assert_xyz_error(self,
                          lambda: xyzio.read_xyz_text(text),
                          'line 3', 'coordinate is not a number')

    def test_blank_lines_ignored_around_rows(self):
        text = '2\nc\n\nC 0 0 0\n\nO 1 0 0\n\n'
        comment, atoms = xyzio.read_xyz_text(text)
        self.assertEqual(comment, 'c')
        self.assertEqual(len(atoms), 2)
        self.assertEqual([a[0] for a in atoms], ['C', 'O'])


class TestFixtureRoundTrips(unittest.TestCase):
    """Round-trip proof: committed xtb-accepted geometries survive
    write_xyz_file -> read_xyz with comments intact and coordinates
    within 1e-8 (dimer2's 10-decimal values round by <= 5e-9 through
    the %15.8f writer; the second write is an exact fixed point)."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix='xyzio-rt-')
        self.addCleanup(shutil.rmtree, self.tmpdir, True)

    def _fixture_path(self, name):
        return os.path.join(FIXTURES, name)

    def _rewrite(self, name, suffix):
        """read fixture -> write copy -> read copy; return both parses."""
        comment0, atoms0 = xyzio.read_xyz(self._fixture_path(name))
        out = os.path.join(self.tmpdir, name + suffix)
        xyzio.write_xyz_file(out, [a[0] for a in atoms0],
                             [a[1:] for a in atoms0], comment0)
        comment1, atoms1 = xyzio.read_xyz(out)
        return out, comment0, atoms0, comment1, atoms1

    def _assert_within_1e_8(self, atoms0, atoms1):
        self.assertEqual(len(atoms1), len(atoms0))
        self.assertEqual([a[0] for a in atoms1], [a[0] for a in atoms0])
        for (_s0, x0, y0, z0), (_s1, x1, y1, z1) in zip(atoms0, atoms1):
            self.assertAlmostEqual(x1, x0, delta=1e-8)
            self.assertAlmostEqual(y1, y0, delta=1e-8)
            self.assertAlmostEqual(z1, z0, delta=1e-8)

    def test_roundtrip_co2(self):
        _out, comment0, atoms0, comment1, atoms1 = self._rewrite(
            'co2.xyz', '.rt')
        self.assertEqual(comment1, comment0)
        self.assertEqual(comment1, 'CO2 linear')
        self._assert_within_1e_8(atoms0, atoms1)

    def test_roundtrip_phenol(self):
        _out, comment0, atoms0, comment1, atoms1 = self._rewrite(
            'phenol.xyz', '.rt')
        self.assertEqual(comment1, comment0)
        self.assertEqual(comment1, 'Optimized at B3LYP/6-31G* level')
        self._assert_within_1e_8(atoms0, atoms1)

    def test_roundtrip_dimer2(self):
        _out, comment0, atoms0, comment1, atoms1 = self._rewrite(
            'dimer2.xyz', '.rt')
        self.assertEqual(comment1, comment0)
        self.assertEqual(comment1, 'stacked phenol dimer 3.4A z-offset')
        self._assert_within_1e_8(atoms0, atoms1)

    def test_roundtrip_xtbopt_energy_comment(self):
        _out, comment0, atoms0, comment1, atoms1 = self._rewrite(
            'xtbopt.xyz', '.rt')
        self.assertEqual(comment1, comment0)
        self.assertEqual(comment1, ' energy: -39.914402395930 '
                                   'gnorm: 0.000144376846 '
                                   'xtb: 6.7.1pre (5071a88)')
        self._assert_within_1e_8(atoms0, atoms1)

    def test_cross_consistency_all_fixtures(self):
        # The xtb-accepted-format proof: read_xyz of the ORIGINAL fixture
        # equals read_xyz of the rewritten file within 1e-8 for all four
        # (xtb accepted the originals; our writer's only deviation is the
        # <= 5e-9 coordinate rounding of %15.8f).
        for name in ROUND_TRIP_FIXTURES:
            comment0, atoms0 = xyzio.read_xyz(self._fixture_path(name))
            _out, _c0, _a0, comment1, atoms1 = self._rewrite(name, '.x')
            self.assertEqual(comment1, comment0, name)
            self._assert_within_1e_8(atoms0, atoms1)

    def test_fixed_point_second_write_byte_identical(self):
        # Write the ALREADY-rewritten atoms a second time: the second
        # file parses to coordinates exactly equal (==) to the first
        # rewrite's, and the two written files are byte-identical
        # (8-decimal values re-serialize identically through %15.8f).
        for name in ROUND_TRIP_FIXTURES:
            comment0, atoms0 = xyzio.read_xyz(self._fixture_path(name))
            path1 = os.path.join(self.tmpdir, name + '.w1')
            xyzio.write_xyz_file(path1, [a[0] for a in atoms0],
                                 [a[1:] for a in atoms0], comment0)
            comment1, atoms1 = xyzio.read_xyz(path1)
            path2 = os.path.join(self.tmpdir, name + '.w2')
            xyzio.write_xyz_file(path2, [a[0] for a in atoms1],
                                 [a[1:] for a in atoms1], comment1)
            _comment2, atoms2 = xyzio.read_xyz(path2)
            self.assertEqual(atoms2, atoms1, name)
            with open(path1, 'rb') as handle1:
                with open(path2, 'rb') as handle2:
                    self.assertEqual(handle1.read(), handle2.read(), name)


if __name__ == '__main__':
    unittest.main()
