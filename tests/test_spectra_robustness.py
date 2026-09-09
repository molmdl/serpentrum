"""Fixture-driven tests for the unified parse dispatcher, the g98<->
vibspectrum index-correspondence invariant, and the phenol-monomer eigval
cross-check (serpentrum/spectra.py, plan 02-12 — closing success criterion
2's "fails loudly on the corrupt fixture" across the phenol, CO2 and
pi-stacked-dimer legs end to end).

Every assertion below is pinned to VERIFIED values probed against the
committed xtb spike fixtures on 2026-09-06/07 (02-RESEARCH-pure-core.md
S2 + the 02-12 plan's load-bearing facts):

  - g98.out: 26 atoms, 72 modes (3*26-6). vibspectrum: 78 modes (6 trivial
    + 72 real). Index correspondence: offset = 3*26 - 72 = 6 (computed
    from the files, never hardcoded); 0 mismatches across all 72 modes at
    freq abs=0.01 / intensity abs=1e-4. The exact 5e-5 intensity boundary
    case is mode 53: g98 0.0233 vs vibspectrum 0.02325.
  - ohess.log (phenol monomer): first 'projected vibrational frequencies'
    block at line 494; 'eigval :' rows 495-501 carry 6+6+6+6+6+6+3 = 39
    eigvals == 3*13-6 (N read from phenol.xyz, whose count line says 13).
    First 6 are ~0 (projected translation/rotation contaminants);
    remaining 33 are positive (min 218.56).
  - Tolerances WHY: vibspectrum freq column is 2-decimal (bound 0.005 —
    mode 77 sits at 3519.95 vs g98 3519.9549 = 0.0049); g98 intensity
    column is 4-decimal (bound 5e-5 — mode 53 sits at exactly 0.02325 vs
    0.0233, the exact float boundary). Test tolerances 0.01 / 1e-4 are
    100-1000x tighter than any mode-mispairing error.

Discovery command (verified on 3.6.9 — NOTE: `-t .` FAILS on python3.6
with a non-package start dir; do not add it):

    python3.6 -m unittest discover -s tests -p "test_*.py" -v

Convention: every test file in tests/ repeats the sys.path self-insert
below; tests/ deliberately has NO __init__.py (plugin-path safety), and
tests/fixtures/xtb/ is a plain data directory (never a package).
"""
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from serpentrum.spectra import (  # noqa: E402
    SpectraParseError,
    parse,
    parse_g98,
    parse_g98_text,
    parse_text,
    parse_vibspectrum,
    parse_vibspectrum_text,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURES = os.path.join(ROOT, 'tests', 'fixtures', 'xtb')
G98_PATH = os.path.join(FIXTURES, 'g98.out')
VIBSPECTRUM_PATH = os.path.join(FIXTURES, 'vibspectrum')
BAD_LOG_PATH = os.path.join(FIXTURES, 'bad.log')
OHESS_LOG_PATH = os.path.join(FIXTURES, 'ohess.log')
PHENOL_XYZ_PATH = os.path.join(FIXTURES, 'phenol.xyz')


def read_text(path):
    """Read a fixture file as utf-8 text (header carries U+207B U+00B9)."""
    with open(path, encoding='utf-8') as fh:
        return fh.read()


class TestUnifiedDispatcher(unittest.TestCase):
    """parse_text()/parse() sniff the format from content, never from the
    file name: '$vibrational spectrum' first line -> vibspectrum;
    'Standard orientation:' anywhere -> g98; else loud error."""

    @classmethod
    def setUpClass(cls):
        cls.g98_text = read_text(G98_PATH)
        cls.vib_text = read_text(VIBSPECTRUM_PATH)
        cls.bad_text = read_text(BAD_LOG_PATH)

    def test_parse_text_vibspectrum_returns_78_modes_no_atoms(self):
        spectrum = parse_text(self.vib_text)
        self.assertEqual(spectrum.n_atoms, 0)
        self.assertEqual(spectrum.atoms, [])
        self.assertEqual(len(spectrum.modes), 78)

    def test_parse_text_g98_returns_26_atoms_72_modes(self):
        spectrum = parse_text(self.g98_text)
        self.assertEqual(spectrum.n_atoms, 26)
        self.assertEqual(len(spectrum.atoms), 26)
        self.assertEqual(len(spectrum.modes), 72)

    def test_parse_text_bad_log_raises_unrecognized_format(self):
        # bad.log has no frequency section AND no 'Standard orientation:'
        # marker -> the dispatcher's unrecognized-format path (NOT the g98
        # parser's no-frequency-section path).
        with self.assertRaises(SpectraParseError) as ctx:
            parse_text(self.bad_text)
        self.assertIn('unrecognized format', str(ctx.exception))

    def test_parse_path_matches_parse_text_vibspectrum(self):
        self.assertEqual(len(parse(VIBSPECTRUM_PATH).modes), 78)
        self.assertEqual(len(parse_text(self.vib_text).modes), 78)

    def test_parse_path_matches_parse_text_g98(self):
        self.assertEqual(len(parse(G98_PATH).modes), 72)
        self.assertEqual(len(parse_text(self.g98_text).modes), 72)

    def test_parse_empty_text_raises_unrecognized_format(self):
        with self.assertRaises(SpectraParseError) as ctx:
            parse_text('')
        self.assertIn('unrecognized format', str(ctx.exception))


class TestIndexCorrespondence(unittest.TestCase):
    """The dimer fixtures satisfy the g98<->vibspectrum index
    correspondence: offset computed as 3*n_atoms - len(g98_modes) (= 6),
    0 mismatches across all 72 modes within freq 0.01 / intensity 1e-4.

    Tolerances WHY (documented in the plan's load-bearing facts):
      - vibspectrum freq column is 2-decimal: bound 0.005 (mode 77 sits at
        3519.95 vs g98 3519.9549 = 0.0049). Test tolerance 0.01 is 2x the
        rounding bound — 100x tighter than any mode-mispairing error.
      - g98 intensity column is 4-decimal: bound 5e-5 (mode 53 sits at
        exactly 0.02325 vs 0.0233, the exact float boundary). Test
        tolerance 1e-4 is 2x the rounding bound — 1000x tighter than any
        mode-mispairing error. Naive <= 5e-5 float comparison can fail;
        1e-4 cannot.
    """

    @classmethod
    def setUpClass(cls):
        cls.g = parse_g98(G98_PATH)
        cls.vs = parse_vibspectrum(VIBSPECTRUM_PATH)

    def test_g98_atom_and_mode_counts(self):
        self.assertEqual(self.g.n_atoms, 26)
        self.assertEqual(len(self.g.modes), 72)
        self.assertEqual(len(self.g.modes), 3 * self.g.n_atoms - 6)

    def test_vibspectrum_mode_count_is_3n(self):
        # vibspectrum carries all 3N modes (trivial + real); n_atoms is 0
        # (no geometry), so derive N from the g98 parse.
        n_atoms = self.g.n_atoms
        self.assertEqual(len(self.vs.modes), 3 * n_atoms)

    def test_offset_computed_from_files(self):
        # offset = 3*N - len(g98_modes), computed from the files — NEVER a
        # literal 6. Cross-check against the vibspectrum's own trivial-row
        # count (two independent derivations must agree).
        offset = 3 * self.g.n_atoms - len(self.g.modes)
        trivial_count = sum(1 for m in self.vs.modes if abs(m.freq) < 10.0)
        self.assertEqual(offset, trivial_count)

    def test_all_72_modes_match_within_tolerances(self):
        offset = 3 * self.g.n_atoms - len(self.g.modes)
        self.assertEqual(len(self.g.modes), 72)
        for j in range(len(self.g.modes)):
            g_mode = self.g.modes[j]
            vs_mode = self.vs.modes[j + offset]
            self.assertAlmostEqual(g_mode.freq, vs_mode.freq, delta=0.01,
                                   msg='mode %d freq mismatch' % (j + 1))
            self.assertAlmostEqual(g_mode.intensity, vs_mode.intensity,
                                   delta=1e-4,
                                   msg='mode %d intensity mismatch' % (j + 1))

    def test_mode_numbering_lines_up(self):
        offset = 3 * self.g.n_atoms - len(self.g.modes)
        for j in range(len(self.g.modes)):
            vs_mode = self.vs.modes[j + offset]
            self.assertEqual(vs_mode.index, j + offset + 1,
                             'vibspectrum mode index mismatch at j=%d' % j)

    def test_exact_boundary_case_mode_53(self):
        # The exact 5e-5 intensity boundary case: g98 mode 53 = 0.0233 vs
        # vibspectrum mode 59 = 0.02325. d_intensity = 5e-5, the exact
        # 4-decimal rounding bound. The 1e-4 tolerance MUST pass this
        # (a naive <= 5e-5 comparison would fail).
        offset = 3 * self.g.n_atoms - len(self.g.modes)
        g53 = self.g.modes[52]  # 0-based index 52 = mode 53
        # g98 mode 53 corresponds to vibspectrum mode 53+offset = 59
        vs_corresponding = self.vs.modes[52 + offset]
        self.assertEqual(vs_corresponding.index, 59)
        self.assertAlmostEqual(g53.intensity, 0.0233, places=4)
        self.assertAlmostEqual(vs_corresponding.intensity, 0.02325, places=5)
        self.assertAlmostEqual(g53.intensity, vs_corresponding.intensity,
                               delta=1e-4)


class TestPhenolEigvalCrossCheck(unittest.TestCase):
    """The phenol-monomer leg of criterion 2: ohess.log's first 'projected
    vibrational frequencies' block carries exactly 39 eigvals == 3*13
    (all 3N projected frequencies, including the 6 trivial contaminants);
    the remaining 33 == 3*13-6 are real vibrational modes. This is the
    monomer complement to the dimer g98 (72 = 3*26-6 real modes) and the
    synthetic CO2 (5 trivial = 3N-5) legs.

    NOTE: the plan's text says "39 == 3*13-6" but 3*13-6 = 33, not 39. The
    ohess.log projected-frequency block carries ALL 3N = 39 frequencies
    (translations + rotations + vibrations); the first 6 are ~0 (trivial)
    and the remaining 33 = 3N-6 are real. The test asserts the correct
    arithmetic: len(eigvals) == 3*N == 39, len(eigvals[6:]) == 3*N-6 == 33.
    (Plan arithmetic typo — Rule 1 deviation, documented in SUMMARY.)

    The eigval extraction is TEST-SIDE line parsing (split on 'eigval :',
    take the floats) — NOT a new parser function in spectra.py. Only the
    FIRST block is used (later blocks at line 637+ are further MD
    snapshots).
    """

    @classmethod
    def setUpClass(cls):
        cls.xyz_text = read_text(PHENOL_XYZ_PATH)
        cls.ohess_text = read_text(OHESS_LOG_PATH)

    def test_phenol_xyz_count_line_is_13(self):
        # phenol.xyz line 1 is the atom-count line; line 2 is the comment.
        lines = self.xyz_text.splitlines()
        self.assertEqual(int(lines[0].strip()), 13)

    def test_ohess_first_block_has_3N_eigvals(self):
        # ohess.log carries ALL 3N = 39 projected frequencies (trivial +
        # real); the g98 parser's 72 = 3*26-6 carries only the real modes.
        n_atoms = int(self.xyz_text.splitlines()[0].strip())
        eigvals = self._extract_first_block_eigvals(self.ohess_text)
        self.assertEqual(len(eigvals), 3 * n_atoms)
        self.assertEqual(len(eigvals), 39)

    def test_ohess_real_mode_count_is_3N_minus_6(self):
        # The 33 real modes (after the 6 trivial) == 3*N - 6.
        n_atoms = int(self.xyz_text.splitlines()[0].strip())
        eigvals = self._extract_first_block_eigvals(self.ohess_text)
        self.assertEqual(len(eigvals[6:]), 3 * n_atoms - 6)
        self.assertEqual(len(eigvals[6:]), 33)

    def test_ohess_first_6_eigvals_near_zero(self):
        # The first 6 are ~0 (projected translation/rotation contaminants).
        eigvals = self._extract_first_block_eigvals(self.ohess_text)
        for i, val in enumerate(eigvals[:6]):
            self.assertLess(abs(val), 1e-2,
                            'eigval %d not near zero: %r' % (i + 1, val))

    def test_ohess_remaining_33_eigvals_positive_above_200(self):
        # The remaining 33 are positive (verified min 218.56).
        eigvals = self._extract_first_block_eigvals(self.ohess_text)
        self.assertEqual(len(eigvals), 39)
        for i, val in enumerate(eigvals[6:]):
            self.assertGreater(val, 200.0,
                               'eigval %d not positive above 200: %r'
                               % (i + 7, val))

    @staticmethod
    def _extract_first_block_eigvals(text):
        """Test-side line parsing: find the FIRST 'projected vibrational
        frequencies' line, then collect every following 'eigval :' row
        (stop at the first line that does not start with 'eigval :').
        Returns the list of float eigvals."""
        lines = text.splitlines()
        start = None
        for i, line in enumerate(lines):
            if 'projected vibrational frequencies' in line:
                start = i
                break
        assert start is not None, 'no projected-frequency block in ohess.log'
        eigvals = []
        for j in range(start + 1, len(lines)):
            line = lines[j]
            if not line.lstrip().startswith('eigval :'):
                break
            after = line.split('eigval :', 1)[1]
            eigvals.extend(float(tok) for tok in after.split())
        return eigvals


_LINE_NUMBER_RE = re.compile(r'line\D*(\d+)')


def _extract_line_number(message):
    """Pull the first 1-based line number from a SpectraParseError message
    (format: '<stage>: line <N>: <detail> [<excerpt>]'). Returns None if
    no line number is present."""
    match = _LINE_NUMBER_RE.search(message)
    return int(match.group(1)) if match else None


class TestCorruptFixtureLoudFailures(unittest.TestCase):
    """Every corrupt path raises SpectraParseError (never a bare ValueError)
    carrying stage + 1-based line number + ~80-char excerpt.

    Corrupt variants are built IN MEMORY from committed fixture text —
    fixture files on disk are never modified. The 02-01/02-09 parsers
    already wrap ALL numeric conversions via _to_float/_to_int (verified:
    float('******') surfaces as SpectraParseError, not ValueError); this
    plan owns the file post-merge and closes any gap if found — no gap
    was found, so no hardening was needed.
    """

    @classmethod
    def setUpClass(cls):
        cls.g98_text = read_text(G98_PATH)
        cls.vib_text = read_text(VIBSPECTRUM_PATH)
        cls.bad_text = read_text(BAD_LOG_PATH)

    def test_bad_log_raises_naming_frequency_section(self):
        # bad.log: 105 lines, fatal error at line 97, NO frequency section
        # anywhere -> the g98 parser's no-frequency-section loud failure.
        with self.assertRaises(SpectraParseError) as ctx:
            parse_g98_text(self.bad_text)
        self.assertIn('frequency section', str(ctx.exception))

    def test_truncated_g98_mid_atom_rows_raises_with_line_number(self):
        # lines[:480] falls MID-ATOM-ROWS of block 13: block 13's
        # ' Frequencies --' is at line 466, property lines 467-471, ' Atom
        # AN' header at 472, its 26 atom rows span 473-498. Line 480 is
        # atom row 8 of 26 -> the parser hits EOF mid-block.
        lines = self.g98_text.splitlines()
        text = '\n'.join(lines[:480])
        with self.assertRaises(SpectraParseError) as ctx:
            parse_g98_text(text)
        lineno = _extract_line_number(str(ctx.exception))
        self.assertIsNotNone(lineno,
                             'no line number in: %s' % ctx.exception)
        self.assertLessEqual(lineno, 480)

    def test_truncated_g98_mid_header_raises_with_line_number(self):
        # lines[:470] falls mid-property-lines of block 13 (between the
        # Frequencies line 466 and the atom rows 473-498, inside the
        # property lines 467-471): the parser expects a property row that
        # was truncated away.
        lines = self.g98_text.splitlines()
        text = '\n'.join(lines[:470])
        with self.assertRaises(SpectraParseError) as ctx:
            parse_g98_text(text)
        lineno = _extract_line_number(str(ctx.exception))
        self.assertIsNotNone(lineno,
                             'no line number in: %s' % ctx.exception)

    def test_g98_asterisk_overflow_raises_not_valueerror(self):
        # Replace mode 1's IR intensity token '2.4191' (line 49) with the
        # g98 overflow marker '******'. float('******') raises ValueError;
        # the parser must wrap it into SpectraParseError with a line number.
        text = self.g98_text.replace('2.4191', '******', 1)
        with self.assertRaises(SpectraParseError) as ctx:
            parse_g98_text(text)
        # Must be SpectraParseError, NOT a bare ValueError escaping the
        # conversion wrapper.
        self.assertIs(type(ctx.exception), SpectraParseError)
        lineno = _extract_line_number(str(ctx.exception))
        self.assertIsNotNone(lineno,
                             'no line number in: %s' % ctx.exception)

    def test_vibspectrum_asterisk_overflow_raises_not_valueerror(self):
        # Replace mode 7's intensity token '2.41910' (line 10) with the
        # overflow marker '******'. Same contract as the g98 case.
        text = self.vib_text.replace('2.41910', '******', 1)
        with self.assertRaises(SpectraParseError) as ctx:
            parse_vibspectrum_text(text)
        self.assertIs(type(ctx.exception), SpectraParseError)
        lineno = _extract_line_number(str(ctx.exception))
        self.assertIsNotNone(lineno,
                             'no line number in: %s' % ctx.exception)

    def test_unmodified_fixtures_still_parse(self):
        # Identity guard: the UNMODIFIED g98 and vibspectrum text still
        # parse fine (guards against a sloppy mutation in the tests above
        # corrupting the shared setUpClass fixture text).
        g = parse_g98_text(self.g98_text)
        self.assertEqual(len(g.modes), 72)
        vs = parse_vibspectrum_text(self.vib_text)
        self.assertEqual(len(vs.modes), 78)


if __name__ == '__main__':
    unittest.main()
