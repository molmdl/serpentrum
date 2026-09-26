"""xtb_run pure-half contract tests (plan 06-02, SPECTRA-02).

Every decision rule the Phase-6 Qt runner controller (plan 06-05) needs
lives in serpentrum/xtb_run.py as a pure function so python3.6 can
unit-test it with ZERO stubs (the 02-02 xtbenv DI precedent). What is
pinned here:

- the run state machine: start() admitted only from idle/terminal states
  (the no-double-run guard), and the terminal set as a frozenset
  (bioCHEMeleon discipline: pending flags clear on EVERY terminal
  branch — done/failed/cancelled).
- resolve_status: a cancel-requested finish maps to 'cancelled'
  REGARDLESS of the 3-leg contract verdict (a killed run's lingering
  'normal termination' stderr must never read as success); otherwise
  'ok'/'failed' from xtbenv.evaluate_run.
- build_env: merges ONLY the three help-verified OMP env knobs
  (xtb --help:229-231: OMP_NUM_THREADS / MKL_NUM_THREADS /
  OMP_STACKSIZE), values stringified, empties rejected, input never
  mutated. No invented knobs.
- build_run_input: head-inclusive snake xyz (head atoms first, then
  segments in engine order) through xyzio.write_xyz, round-tripped via
  xyzio.read_xyz_text — text IS the handoff seam (EQ-xyz-1).
- the spectra_run record shape frozen as data (EQ-artifact-1):
  SPECTRA_RUN_KEYS + new_spectra_run initial dict.

Discovery command (verified on python3.6.9 — NOTE: `-t .` FAILS on
python3.6 with a non-package start dir; do not add it):

    python3.6 -m unittest discover -s tests -p "test_xtb_run.py" -v

Convention: every test file in tests/ repeats the sys.path self-insert
below (bioCHEMeleon pattern). tests/ deliberately has NO __init__.py —
the dev plugin path IS the repo root, and findPlugins would treat a
package dir here as a second plugin.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from serpentrum import xtb_run, xyzio, xtbenv  # noqa: E402,F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURES = os.path.join(ROOT, '.planning', 'research', 'xtb-spike-fixtures')


class TestStateMachine(unittest.TestCase):
    """No-double-run guard + terminal discipline, tested exhaustively."""

    def test_can_start_matrix(self):
        # start() is admitted from idle (None / 'idle') and every
        # terminal state (a finished run may start again)...
        self.assertTrue(xtb_run.can_start(None))
        self.assertTrue(xtb_run.can_start('idle'))
        self.assertTrue(xtb_run.can_start('ok'))
        self.assertTrue(xtb_run.can_start('failed'))
        self.assertTrue(xtb_run.can_start('cancelled'))
        # ...but NEVER while a run is in flight...
        self.assertFalse(xtb_run.can_start('running'))
        # ...and unknown states never start either.
        self.assertFalse(xtb_run.can_start('bogus'))

    def test_terminal_set(self):
        self.assertIsInstance(xtb_run.TERMINAL_STATES, frozenset)
        for state in ('ok', 'failed', 'cancelled'):
            self.assertIn(state, xtb_run.TERMINAL_STATES)
        for state in ('running', 'idle'):
            self.assertNotIn(state, xtb_run.TERMINAL_STATES)

    def test_resolve_status_cancel_wins(self):
        # Cancel WINS over the verdict — even if partially-captured
        # stderr said 'normal termination', a killed run is 'cancelled',
        # never 'ok'.
        self.assertEqual(xtb_run.resolve_status(True, True), 'cancelled')
        self.assertEqual(xtb_run.resolve_status(True, False), 'cancelled')

    def test_resolve_status_contract(self):
        # Without a cancel request the verdict maps 1:1 onto 'ok' /
        # 'failed' (verdict comes from xtbenv.evaluate_run).
        self.assertEqual(xtb_run.resolve_status(False, True), 'ok')
        self.assertEqual(xtb_run.resolve_status(False, False), 'failed')


class TestBuildEnv(unittest.TestCase):
    """OMP env-knob merge: verified keys only, copy semantics."""

    def test_default_empty(self):
        base = {'A': '1'}
        merged = xtb_run.build_env(base, None)
        self.assertEqual(merged, {'A': '1'})
        self.assertIsNot(merged, base)

    def test_merge_stringifies(self):
        merged = xtb_run.build_env({}, {'OMP_NUM_THREADS': 2})
        self.assertEqual(merged, {'OMP_NUM_THREADS': '2'})

    def test_no_mutation(self):
        base = {'X': '1'}
        xtb_run.build_env(base, {'OMP_NUM_THREADS': '2'})
        self.assertEqual(base, {'X': '1'})

    def test_unknown_key_rejected(self):
        # Only the help-verified keys (xtb --help:229-231) are legal —
        # no invented env knobs.
        self.assertRaises(ValueError, xtb_run.build_env, {}, {'FOO': '1'})

    def test_empty_value_rejected(self):
        self.assertRaises(ValueError, xtb_run.build_env,
                          {}, {'OMP_NUM_THREADS': ''})

    def test_default_run_knobs_uncapped(self):
        # EQ-omp-1 pin: the runner ships UNCAPPED until the calibration
        # experiment (plan 06-07) measures; plan 06-11 owns the default
        # edit and may change this ONE literal.
        self.assertEqual(xtb_run.DEFAULT_RUN_KNOBS, {})


class TestBuildRunInput(unittest.TestCase):
    """Snake xyz assembly: head first, then segments in engine order."""

    def test_head_first_then_segments(self):
        head = [('C', 0.0, 0.0, 0.0), ('H', 1.0, 0.0, 0.0)]
        segs = [[('O', 2.0, 0.0, 0.0)]]
        text = xtb_run.build_run_input(head, segs, 'run_1')
        comment, atoms = xyzio.read_xyz_text(text)
        self.assertEqual(len(atoms), 3)
        self.assertEqual([a[0] for a in atoms], ['C', 'H', 'O'])
        self.assertTrue(comment.startswith('serpentrum snake '), comment)

    def test_comment_single_line(self):
        # A snake_id containing a newline must never break the frame —
        # the writer sanitizes it (xyzio.write_xyz replaces \r/\n).
        head = [('C', 0.0, 0.0, 0.0)]
        text = xtb_run.build_run_input(head, [], 'run_2\nhax')
        comment, atoms = xyzio.read_xyz_text(text)
        self.assertEqual(len(atoms), 1)
        self.assertNotIn('\n', comment)

    def test_none_head_raises(self):
        self.assertRaises(ValueError, xtb_run.build_run_input,
                          None, [], 'run_1')

    def test_multi_segment_order(self):
        # Two segments land in segment order — index 0 (oldest eaten)
        # first.
        head = [('C', 0.0, 0.0, 0.0)]
        seg0 = [('N', 1.0, 0.0, 0.0)]
        seg1 = [('O', 2.0, 0.0, 0.0), ('F', 3.0, 0.0, 0.0)]
        text = xtb_run.build_run_input(head, [seg0, seg1], 'run_1')
        _comment, atoms = xyzio.read_xyz_text(text)
        self.assertEqual([a[0] for a in atoms], ['C', 'N', 'O', 'F'])

    def test_real_fixture_round_trip(self):
        # The committed co2.xyz (xtb-accepted bytes) rebuilds as head
        # only and round-trips unchanged in count and symbols.
        _comment, atoms = xyzio.read_xyz(os.path.join(FIXTURES, 'co2.xyz'))
        self.assertEqual(len(atoms), 3)
        text = xtb_run.build_run_input(atoms, [], 'co2_head')
        comment2, atoms2 = xyzio.read_xyz_text(text)
        self.assertEqual(len(atoms2), 3)
        self.assertEqual([a[0] for a in atoms2], [a[0] for a in atoms])
        self.assertTrue(comment2.startswith('serpentrum snake '))


class TestSpectraRunRecord(unittest.TestCase):
    """The Phase-7 handoff record shape, frozen as data (EQ-artifact-1)."""

    def test_keys_frozen(self):
        self.assertEqual(set(xtb_run.SPECTRA_RUN_KEYS),
                         {'snake_id', 'status', 'problems', 'input_path',
                          'g98_path', 'vibspectrum_path', 'xtbopt_path',
                          'log_path'})

    def test_new_record_initial(self):
        self.assertEqual(
            xtb_run.new_spectra_run('run_3'),
            {'snake_id': 'run_3',
             'status': 'running',
             'problems': [],
             'input_path': None,
             'g98_path': None,
             'vibspectrum_path': None,
             'xtbopt_path': None,
             'log_path': None})


if __name__ == '__main__':
    unittest.main()
