"""Fixture-anchored tests for serpentrum/spectra_ui.py (plan 07-01 — the
SPECTRA-05 pure half).

Anchors (probed 2026-09-27 against the committed fixtures, WSL python3.6;
07-RESEARCH-spectra-seam.md Q1 fixture table):

  - g98.out (26-atom phenol pi-dimer, 72 modes): negative modes 1-3 carry
    freqs -31.9175 / -23.0766 / -18.1086 -> freq_label '-31.9i' / '-23.1i'
    / '-18.1i'; ZERO zero-intensity modes in this g98. The max-intensity
    mode (index 42) is 1150.6639 cm-1 @ 257.1018 km/mol -> labels
    '1150.7' / '257.1'.
  - synthetic/co2_vibspectrum (5 trivial + 3 real): real_modes carries
    600.18 @ 68.70, 600.18 @ 68.70, and the intensity-EXACTLY-0.00
    symmetric stretch 1424.95 -> exactly one row with intensity label '0'
    ('%.4g' keeps a 0.00026-class value distinct from exact zero).

Discovery command (verified on 3.6.9 — '-t .' FAILS on python3.6 with a
non-package start dir; do not add it):

    python3.6 -m unittest discover -s tests -p "test_spectra_ui.py" -v

Convention: every test file in tests/ repeats the sys.path self-insert
below; tests/ deliberately has NO __init__.py (plugin-path safety), and
tests/fixtures/xtb/ is a plain data directory (read in place).
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from serpentrum import spectra, spectra_ui, xtb_run  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURES = os.path.join(ROOT, 'tests', 'fixtures', 'xtb')
G98_PATH = os.path.join(FIXTURES, 'g98.out')
VIB_PATH = os.path.join(FIXTURES, 'vibspectrum')
CO2_VIB_PATH = os.path.join(FIXTURES, 'synthetic', 'co2_vibspectrum')


def _is_ascii(text):
    """True when every char of text is ASCII. str.isascii() is 3.7+; the
    binding gate is python3.6, so this module spells the check out."""
    return all(ord(ch) < 128 for ch in text)


class TestFreqLabel(unittest.TestCase):

    def test_negative_imaginary(self):
        # Fixture g98 modes 1-3 (the pi-dimer's inter-stack soft modes).
        self.assertEqual(spectra_ui.freq_label(-31.9175), '-31.9i')
        self.assertEqual(spectra_ui.freq_label(-23.0766), '-23.1i')
        self.assertEqual(spectra_ui.freq_label(-18.1086), '-18.1i')

    def test_nonnegative_plain(self):
        self.assertEqual(spectra_ui.freq_label(0.0), '0.0')
        self.assertEqual(spectra_ui.freq_label(1150.6639), '1150.7')
        self.assertEqual(spectra_ui.freq_label(257.1018), '257.1')

    def test_ascii_only(self):
        # The doc-pinned convention: ASCII hyphen-minus, NEVER U+2212.
        for freq in (-31.9175, -23.0766, -18.1086, -0.001, 0.0, 1150.6639):
            label = spectra_ui.freq_label(freq)
            self.assertTrue(_is_ascii(label),
                            'non-ASCII label for %r: %r' % (freq, label))
            self.assertNotIn(u'−', label)


class TestTableRows(unittest.TestCase):

    def test_g98_all_modes(self):
        spectrum = spectra.parse_g98(G98_PATH)
        rows = spectra_ui.table_rows(spectrum)
        self.assertEqual(len(rows), 72)
        self.assertEqual(rows[0][0], 1)
        self.assertEqual(rows[0][1], '-31.9i')
        self.assertEqual(rows[2][1], '-18.1i')
        peak = [r for r in rows if r[1] == '1150.7']
        self.assertEqual(len(peak), 1)
        self.assertEqual(peak[0][2], '257.1')

    def test_row_shape(self):
        spectrum = spectra.parse_g98(G98_PATH)
        rows = spectra_ui.table_rows(spectrum)
        for expected_index, row in enumerate(rows, start=1):
            self.assertIsInstance(row, tuple)
            self.assertEqual(len(row), 3)
            index, freq_label, intensity_label = row
            self.assertIsInstance(index, int)
            self.assertIsInstance(freq_label, str)
            self.assertIsInstance(intensity_label, str)
            self.assertEqual(index, expected_index)  # 1..72 in order

    def test_zero_intensity_listed(self):
        # Synthetic Mode tuple — the zero-intensity leg the g98 fixture
        # cannot provide (PITFALLS.md 12.3; this g98 has NONE).
        spectrum = spectra.Spectrum(
            1, [], [spectra.Mode(9, 1500.0, 0.0, ())])
        rows = spectra_ui.table_rows(spectrum)
        self.assertEqual(rows, [(9, '1500.0', '0')])

    def test_co2_vibspectrum_end_to_end(self):
        spec = spectra.parse_vibspectrum(CO2_VIB_PATH)
        rows = spectra_ui.table_rows(spectra.real_modes(spec))
        self.assertEqual(len(rows), 3)
        zero_rows = [r for r in rows if r[2] == '0']
        # Exactly the symmetric stretch (1424.95, intensity exactly 0.00).
        self.assertEqual(len(zero_rows), 1)
        self.assertEqual(zero_rows[0][1], '1425.0')


class TestModeArrowPrimitives(unittest.TestCase):

    def test_g98_mode1(self):
        spectrum = spectra.parse_g98(G98_PATH)
        prims = spectra_ui.mode_arrow_primitives(spectrum, 1)
        self.assertIsNotNone(prims)
        atoms, vecs = prims
        self.assertEqual(len(atoms), 26)
        self.assertEqual(len(vecs), 26)
        for atom in atoms:
            self.assertEqual(len(atom), 3)
            for component in atom:
                self.assertIsInstance(component, float)
        for vec in vecs:
            self.assertEqual(len(vec), 3)
            for component in vec:
                self.assertIsInstance(component, float)

    def test_mode_order(self):
        spectrum = spectra.parse_g98(G98_PATH)
        atoms, vecs = spectra_ui.mode_arrow_primitives(spectrum, 5)
        self.assertEqual(vecs, [tuple(float(c) for c in v)
                                for v in spectrum.modes[4].vectors])

    def test_out_of_range_none(self):
        spectrum = spectra.parse_g98(G98_PATH)
        self.assertIsNone(spectra_ui.mode_arrow_primitives(spectrum, 0))
        self.assertIsNone(spectra_ui.mode_arrow_primitives(spectrum, 73))

    def test_vibspectrum_none(self):
        # vibspectrum carries atoms == [] and every vectors == ()
        # (spectra.py:313-321) — None, never an exception.
        vib = spectra.parse_vibspectrum(VIB_PATH)
        self.assertIsNone(spectra_ui.mode_arrow_primitives(vib, 7))

    def test_empty_atoms_none(self):
        spectrum = spectra.Spectrum(
            0, [], [spectra.Mode(1, 100.0, 5.0, ())])
        self.assertIsNone(spectra_ui.mode_arrow_primitives(spectrum, 1))


class TestRunStatusLines(unittest.TestCase):

    def test_ok_clean(self):
        record = {'status': xtb_run.DONE, 'problems': []}
        self.assertEqual(spectra_ui.run_status_lines(record),
                         ['xtb finished: ok'])

    def test_failed_with_problems(self):
        record = {'status': xtb_run.FAILED, 'problems': ['p1', 'p2']}
        self.assertEqual(spectra_ui.run_status_lines(record),
                         ['xtb finished: failed', 'problems: p1; p2'])

    def test_cancelled(self):
        record = {'status': xtb_run.CANCELLED, 'problems': []}
        self.assertEqual(spectra_ui.run_status_lines(record),
                         ['xtb finished: cancelled'])

    def test_no_log_scanning(self):
        # A 'log_path' pointing at a nonexistent file must NOT change the
        # output: the builder never opens files (never re-scans log text —
        # the 'abnormal termination' substring trap stays dead).
        record = {'status': xtb_run.DONE,
                  'problems': [],
                  'log_path': os.path.join(FIXTURES, 'no_such_file.log')}
        self.assertEqual(spectra_ui.run_status_lines(record),
                         ['xtb finished: ok'])
        record2 = {'status': xtb_run.FAILED,
                   'problems': ['p1'],
                   'log_path': os.path.join(FIXTURES, 'no_such_file.log')}
        self.assertEqual(spectra_ui.run_status_lines(record2),
                         ['xtb finished: failed', 'problems: p1'])


class TestRecordSpectrumPaths(unittest.TestCase):

    def test_ok_record_prefers_g98(self):
        # Both paths present -> g98 wins (vectors + atom block live there).
        record = {'g98_path': '/x/srp_spectra/s1/g98.out',
                  'vibspectrum_path': '/x/srp_spectra/s1/vibspectrum'}
        self.assertEqual(
            spectra_ui.record_spectrum_paths(record),
            ('/x/srp_spectra/s1/g98.out', '/x/srp_spectra/s1/vibspectrum',
             'g98'))

    def test_vibspectrum_fallback(self):
        # g98 missing -> vibspectrum fallback, source named for the note.
        record = {'g98_path': None,
                  'vibspectrum_path': '/x/srp_spectra/s1/vibspectrum'}
        self.assertEqual(
            spectra_ui.record_spectrum_paths(record),
            (None, '/x/srp_spectra/s1/vibspectrum', 'vibspectrum'))

    def test_degenerate_record_both_none(self):
        # failed/cancelled runs may carry None paths -> never fabricate.
        record = {'g98_path': None, 'vibspectrum_path': None}
        self.assertEqual(spectra_ui.record_spectrum_paths(record),
                         (None, None, 'none'))

    def test_empty_dict(self):
        self.assertEqual(spectra_ui.record_spectrum_paths({}),
                         (None, None, 'none'))


if __name__ == '__main__':
    unittest.main()
