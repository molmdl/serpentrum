"""Structural tests for serpentrum/cgo_build.py -- pure CGO stream builders.

Discovery command (verified on python3.6.9 -- NOTE: `-t .` FAILS on 3.6
with a non-package start dir; do not add it):

    python3.6 -m unittest discover -s tests -p "test_*.py" -v

Convention: tests/ deliberately has NO __init__.py (the dev plugin path
IS the repo root; findPlugins would treat a package dir here as a second
plugin).  Every test file repeats the sys.path self-insert below.
"""
import os
import sys
import unittest
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from serpentrum import cgo_build  # noqa: E402


# --- Mini CGO-stream interpreter ------------------------------------------
# Maps each opcode VALUE to its operand count.  This resolves the value
# collisions intrinsic to CGO (e.g. 4.0 = VERTEX not TRIANGLES, 3.0 = END
# not LINE_STRIP) by mapping each value to the single interpretation our
# builders use.  The interpreter walks (opcode, operand_count) pairs and
# asserts the stream divides exactly into valid records with no trailing
# garbage and no unknown opcodes.
_OPERANDS = {
    10.0: 1,   # LINEWIDTH
    6.0: 3,    # COLOR
    4.0: 3,    # VERTEX  (not TRIANGLES -- our builders emit VERTEX only)
    2.0: 0,    # BEGIN
    3.0: 0,    # END     (not LINE_STRIP -- our builders emit END only)
    0.0: 0,    # STOP    (not POINTS -- our builders emit STOP only)
    1.0: 0,    # LINES   (not NULL -- our builders emit LINES only)
    7.0: 4,    # SPHERE
    9.0: 13,   # CYLINDER
    27.0: 16,  # CONE
}


def _interpret_cgo(stream):
    """Walk a CGO float list as (opcode, [operands]) records.

    Returns a list of (opcode_value, [operand_floats]) tuples.  Raises
    AssertionError on unknown opcodes, operand overruns, or trailing
    floats after STOP.
    """
    records = []
    i = 0
    n = len(stream)
    while i < n:
        op = stream[i]
        if op not in _OPERANDS:
            raise AssertionError(
                'unknown opcode %r at index %d' % (op, i))
        count = _OPERANDS[op]
        if i + 1 + count > n:
            raise AssertionError(
                'opcode %r at index %d needs %d operands but only %d '
                'remain' % (op, i, count, n - i - 1))
        records.append((op, list(stream[i + 1:i + 1 + count])))
        i += 1 + count
        if op == 0.0:  # STOP terminates the stream
            if i != n:
                raise AssertionError(
                    'trailing %d float(s) after STOP at index %d'
                    % (n - i, i))
            break
    if i < n:
        raise AssertionError('stream ended mid-record at index %d' % i)
    return records


def _vertex_triples(records):
    """Extract (x, y, z) tuples from VERTEX records in parsed output."""
    return [tuple(operands) for op, operands in records
            if op == cgo_build.VERTEX]


class TestConstants(unittest.TestCase):
    """The 15 local opcode constants must match the verified cgo.py table."""

    def test_all_fifteen_constants_match_verified_table(self):
        expected = {
            'POINTS': 0.0,
            'STOP': 0.0,
            'LINES': 1.0,
            'NULL': 1.0,
            'BEGIN': 2.0,
            'LINE_STRIP': 3.0,
            'END': 3.0,
            'TRIANGLES': 4.0,
            'TRIANGLE_STRIP': 5.0,
            'VERTEX': 4.0,
            'COLOR': 6.0,
            'SPHERE': 7.0,
            'CYLINDER': 9.0,
            'LINEWIDTH': 10.0,
            'CONE': 27.0,
        }
        for name, val in sorted(expected.items()):
            actual = getattr(cgo_build, name, None)
            self.assertEqual(
                actual, val,
                '%s should be %.1f, got %r' % (name, val, actual))

    def test_no_version_constant(self):
        # pymol/cgo.py has NO VERSION constant -- cgo_build must not
        # define one either (the research question's list included it in
        # error; assert its absence).
        self.assertFalse(
            hasattr(cgo_build, 'VERSION'),
            'pymol/cgo.py has NO VERSION constant -- cgo_build must not '
            'define one either')

    def test_all_constants_are_floats(self):
        names = ('POINTS', 'STOP', 'LINES', 'NULL', 'BEGIN', 'LINE_STRIP',
                 'END', 'TRIANGLES', 'TRIANGLE_STRIP', 'VERTEX', 'COLOR',
                 'SPHERE', 'CYLINDER', 'LINEWIDTH', 'CONE')
        for name in names:
            self.assertIsInstance(
                getattr(cgo_build, name), float,
                '%s must be a float literal, not %s'
                % (name, type(getattr(cgo_build, name)).__name__))


class TestBoxCgo(unittest.TestCase):
    """Boundary-box builder: parseable 12-edge LINES stream from 2 corners."""

    def test_structure_and_length(self):
        stream = cgo_build.box_cgo((-1.0, -2.0, -3.0), (1.0, 2.0, 3.0))
        # Interpreter must parse the whole stream cleanly (no exceptions).
        records = _interpret_cgo(stream)
        # Total: 8 (header) + 96 (24 VERTEX x 4) + 2 (END + STOP) = 106.
        self.assertEqual(len(stream), 106)
        # First two floats: LINEWIDTH, linewidth.
        self.assertEqual(stream[0], cgo_build.LINEWIDTH)
        self.assertEqual(stream[1], 2.0)
        # Positional structure.
        self.assertEqual(stream[2], cgo_build.BEGIN)
        self.assertEqual(stream[3], cgo_build.LINES)
        self.assertEqual(stream[4], cgo_build.COLOR)
        self.assertEqual(stream[5:8], [1.0, 0.4, 0.1])
        self.assertEqual(stream[-2:], [cgo_build.END, cgo_build.STOP])
        # Record counts.
        opcodes = [r[0] for r in records]
        self.assertEqual(opcodes.count(cgo_build.BEGIN), 1)
        self.assertEqual(opcodes.count(cgo_build.LINES), 1)
        self.assertEqual(opcodes.count(cgo_build.COLOR), 1)
        self.assertEqual(opcodes.count(cgo_build.END), 1)
        self.assertEqual(opcodes.count(cgo_build.STOP), 1)
        self.assertEqual(opcodes.count(cgo_build.VERTEX), 24)

    def test_all_values_are_floats(self):
        stream = cgo_build.box_cgo((0.0, 0.0, 0.0), (1.0, 1.0, 1.0))
        for i, v in enumerate(stream):
            self.assertIsInstance(
                v, float,
                'stream[%d] = %r is %s, not float'
                % (i, v, type(v).__name__))

    def test_corner_multiplicity(self):
        mn = (-1.0, -2.0, -3.0)
        mx = (1.0, 2.0, 3.0)
        stream = cgo_build.box_cgo(mn, mx)
        records = _interpret_cgo(stream)
        verts = _vertex_triples(records)
        # The 8 corners.
        corners = {
            (mn[0], mn[1], mn[2]),
            (mx[0], mn[1], mn[2]),
            (mx[0], mx[1], mn[2]),
            (mn[0], mx[1], mn[2]),
            (mn[0], mn[1], mx[2]),
            (mx[0], mn[1], mx[2]),
            (mx[0], mx[1], mx[2]),
            (mn[0], mx[1], mx[2]),
        }
        counts = Counter(verts)
        self.assertEqual(len(counts), 8,
                         'expected exactly 8 distinct vertices, got %d'
                         % len(counts))
        for c in corners:
            self.assertEqual(
                counts.get(c, 0), 3,
                'corner %r should appear exactly 3 times, got %d'
                % (c, counts.get(c, 0)))
        self.assertEqual(len(verts), 24)

    def test_coords_within_bounds(self):
        mn = (-1.0, -2.0, -3.0)
        mx = (1.0, 2.0, 3.0)
        stream = cgo_build.box_cgo(mn, mx)
        records = _interpret_cgo(stream)
        for op, operands in records:
            if op == cgo_build.VERTEX:
                for k in range(3):
                    self.assertGreaterEqual(operands[k], mn[k],
                                            'coord below min on axis %d' % k)
                    self.assertLessEqual(operands[k], mx[k],
                                         'coord above max on axis %d' % k)

    def test_extreme_corners_present(self):
        mn = (-1.0, -2.0, -3.0)
        mx = (1.0, 2.0, 3.0)
        stream = cgo_build.box_cgo(mn, mx)
        records = _interpret_cgo(stream)
        verts = set(_vertex_triples(records))
        self.assertIn(mn, verts, 'min corner not found among vertices')
        self.assertIn(mx, verts, 'max corner not found among vertices')

    def test_custom_color_and_linewidth(self):
        stream = cgo_build.box_cgo(
            (0.0, 0.0, 0.0), (1.0, 1.0, 1.0),
            color=(0.5, 0.5, 0.5), linewidth=5.0)
        self.assertEqual(stream[0], cgo_build.LINEWIDTH)
        self.assertEqual(stream[1], 5.0)
        self.assertEqual(stream[4], cgo_build.COLOR)
        self.assertEqual(stream[5:8], [0.5, 0.5, 0.5])


if __name__ == '__main__':
    unittest.main()
