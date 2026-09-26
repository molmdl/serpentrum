"""Phase-6 pure integration chain (plan 06-10): the exact module
composition the GUI launch pipeline (06-09) and the runner controller
(06-05) implement, pinned end-to-end on REAL fixture bytes with ZERO
stubs — so any seam drift between xtb_run / budget_guard / xyzio /
xtbenv fails here BEFORE GUI work relies on it.

The chain (02-14 pure-core / 05-12 integration-suite precedent — every
module in the chain is shipped product code, NO glue logic in between):

    INPUT     xtb_run.build_run_input(head_atoms, segments, snake_id)
              -> xyzio.write_xyz text (head FIRST, segments in order)
    ROUNDTRIP xyzio.read_xyz_text(text) -> (comment, atoms)
    GUARD     budget_guard.launch_budget_warnings / launch_counts_line
              (SPECTRA-06 warn-and-proceed, head-inclusive counts)
    LAUNCH    xtbenv.build_argv -> [exe, 'snake.xyz', '--ohess']
              (list argv + quote-rejection injection guard)
    STATE     xtb_run.can_start (no-double-run guard) /
              resolve_status (cancel WINS over the contract verdict)
    CONTRACT  xtbenv.evaluate_run 3-leg contract (exit / stderr / files)
              vs the committed .err fixture bytes IN PLACE
    RECORD    xtb_run.new_spectra_run -> the frozen SPECTRA_RUN_KEYS
              record shape Phase 7 consumes without reshaping

The killed-run scenario reconstructs the live probe-B state
synthetically (06-RESEARCH-runner.md Q4: kill() 309 ms into a real
dimer --ohess -> finished(exitcode=62097, exitstatus=CrashExit); run
dir retains ONLY '.xtboptok', 'snake.xyz', 'xtbopt.log') and asserts
BOTH halves of no-fake-success: resolve_status(True, anything) ==
'cancelled', AND evaluate_run(62097, success-looking stderr, ...,
partial files).ok is False — a lingering 'normal termination' in
partially captured stderr must never read as success.

The over-budget win-snake scenario proves the guard WARNS and never
BLOCKS with revealed head-inclusive counts: a default win freezes
molecules_stacked exactly AT the cap (game_engine.py:726-731), so the
molecule leg is counts/desync only and ONLY the atom leg can fire
setup_logic.HESSIAN_WARNING (budget_guard.py module docstring).

python3.6 only (%-formatting, no f-strings). tests/ has NO __init__.py
(the dev plugin path IS the repo root). Fixtures are read IN PLACE from
.planning/research/xtb-spike-fixtures/ (committed; present in every
worktree). Discovery (do NOT add `-t .`: fails on 3.6 non-package):

    python3.6 -m unittest discover -s tests -p "test_phase6_integration.py" -v

No serpentrum module is modified by this file; the merged wave-1/2
module behavior is TRUTH — a scenario exposing a module defect is a
STOP-and-report condition, never a silent workaround.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from serpentrum import budget_guard  # noqa: E402
from serpentrum import setup_logic  # noqa: E402
from serpentrum import xtb_run  # noqa: E402
from serpentrum import xtbenv  # noqa: E402
from serpentrum import xyzio  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURES = os.path.join(ROOT, '.planning', 'research', 'xtb-spike-fixtures')


def _err_text(name):
    """Fixture .err bytes -> utf-8 text, passed AS-IS (CRLF retained).

    ohess.err: 'normal termination of xtb\\r\\n' (27 B) — the success
    stderr of a completed --ohess run. bad.err: 'abnormal termination
    of xtb\\r\\n' (29 B) — the substring trap: 'abnormal' CONTAINS
    'normal termination'.
    """
    with open(os.path.join(FIXTURES, name), 'rb') as handle:
        return handle.read().decode('utf-8')


def _co2_head_atoms():
    """Head atoms from the committed co2.xyz fixture (3 atoms), in the
    engine-shaped (sym, x, y, z) tuple form build_run_input consumes."""
    _comment, atoms = xyzio.read_xyz(os.path.join(FIXTURES, 'co2.xyz'))
    return atoms


class TestHappyPathChain(unittest.TestCase):
    """Completion -> run input -> xyz round-trip -> guard -> launch
    argv -> state machine -> 3-leg contract -> Phase-7 record, in the
    exact call order the GUI/controller implement."""

    def test_completion_to_record(self):
        head_atoms = _co2_head_atoms()
        self.assertEqual(len(head_atoms), 3)
        # One synthetic two-atom segment (the eaten pickup's atoms as
        # the engine carries them): 3 + 2 = 5 head-INCLUSIVE atoms.
        segments = [[('C', 0.0, 0.0, 3.0), ('H', 0.0, 0.0, 4.1)]]

        # INPUT: engine-shaped atoms -> run-input xyz text.
        text = xtb_run.build_run_input(head_atoms, segments, 'run_7')
        comment, atoms = xyzio.read_xyz_text(text)
        self.assertEqual(len(atoms), 5)
        self.assertTrue(comment.startswith('serpentrum snake run_7'))

        # GUARD: molecules_view = stacked 1 + head = 2; 5 atoms is far
        # under the 100 budget -> a clean launch is an EMPTY list.
        warnings = budget_guard.launch_budget_warnings(
            1, 2, len(atoms), len(atoms), 100)
        self.assertEqual(warnings, [])
        counts = budget_guard.launch_counts_line(1, len(atoms), 100)
        self.assertIn('2 molecules', counts)  # incl. head
        self.assertIn('5 atoms', counts)

        # STATE + LAUNCH: a fresh start is admitted from idle; the argv
        # contract is [exe, bare-relative input, '--ohess'].
        self.assertTrue(xtb_run.can_start('idle'))
        argv = xtbenv.build_argv('C:/xtb/xtb.exe', 'snake.xyz')
        self.assertEqual(argv, ['C:/xtb/xtb.exe', 'snake.xyz', '--ohess'])

        # CONTRACT: the committed ohess.err success bytes + all expected
        # files present -> ok, no problems.
        verdict = xtbenv.evaluate_run(
            0, _err_text('ohess.err'), xtbenv.EXPECTED_FILES,
            ('g98.out', 'vibspectrum'))
        self.assertTrue(verdict.ok)
        self.assertEqual(verdict.problems, [])

        # RECORD: no cancel -> the verdict maps 1:1; the record carries
        # exactly the frozen Phase-7 key set.
        status = xtb_run.resolve_status(False, verdict.ok)
        self.assertEqual(status, 'ok')
        record = xtb_run.new_spectra_run('run_7')
        record['status'] = status
        record['problems'] = verdict.problems
        self.assertEqual(set(record), set(xtb_run.SPECTRA_RUN_KEYS))
        self.assertEqual(record['status'], 'ok')

    def test_over_budget_win_snake_warns_not_blocks(self):
        # The structurally mandatory warn-and-proceed pin
        # (06-RESEARCH-guard.md Q2): a default WIN snake exceeds
        # atom_budget=100, yet the launch chain must CONTINUE.
        head = [('C', 0.0, 0.0, 0.0)] * 12          # head: 12 atoms
        segments = [[('C', 0.0, 0.0, 0.0)] * 22
                    for _i in range(9)]             # 9 stacked x 22
        text = xtb_run.build_run_input(head, segments, 'win_snake')
        _comment, atoms = xyzio.read_xyz_text(text)
        self.assertEqual(len(atoms), 210)           # head-inclusive

        # molecules_stacked 10 (win AT the cap), viewer incl-head 11;
        # BOTH viewer counts agree (no desync) -> exactly ONE line: the
        # hessian warning with the revealed head-inclusive count.
        warnings = budget_guard.launch_budget_warnings(10, 11, 210, 210, 100)
        self.assertEqual(len(warnings), 1)
        self.assertIn(setup_logic.HESSIAN_WARNING, warnings[0])
        self.assertIn('210', warnings[0])
        self.assertIn('100', warnings[0])

        # Warn-and-proceed: the guard returned data (no raise) and the
        # rest of the launch chain keeps working on the SAME counts.
        self.assertTrue(xtb_run.can_start('idle'))
        argv = xtbenv.build_argv('C:/xtb/xtb.exe', 'snake.xyz')
        self.assertEqual(argv[-1], '--ohess')


class TestCancelChain(unittest.TestCase):
    """The killed-run no-fake-success pin, in both its halves."""

    def test_killed_run_never_fake_success(self):
        # Probe-B state (06-RESEARCH-runner Q4): kill() 309 ms into a
        # real dimer --ohess -> finished(exitcode=62097); run dir holds
        # ONLY the optimizer-stage files. A lingering success-looking
        # stderr must NEVER survive either half of the cancel path.
        self.assertEqual(xtb_run.resolve_status(True, True), 'cancelled')
        self.assertEqual(xtb_run.resolve_status(True, False), 'cancelled')

        verdict = xtbenv.evaluate_run(
            62097, _err_text('ohess.err'), xtbenv.EXPECTED_FILES,
            ('.xtboptok', 'snake.xyz', 'xtbopt.log'))
        self.assertFalse(verdict.ok)
        self.assertTrue(any('exit code' in p for p in verdict.problems))
        self.assertTrue(
            any('missing expected output' in p for p in verdict.problems))
        # The stderr leg PASSED (the fixture bytes are a success line):
        # the files leg alone still kills the run — no fake success.
        self.assertEqual(len(verdict.problems), 2)

    def test_state_machine_cancel_cycle(self):
        # SC2: cancel -> relaunch. idle admits -> running refuses ->
        # cancelled admits again (terminal state replaces).
        self.assertTrue(xtb_run.can_start('idle'))
        status = 'running'
        self.assertFalse(xtb_run.can_start(status))
        status = xtb_run.resolve_status(True, False)
        self.assertEqual(status, 'cancelled')
        self.assertTrue(xtb_run.can_start(status))

    def test_state_machine_complete_then_relaunch(self):
        # SC2: completion -> relaunch. running -> 'ok' -> start again.
        self.assertFalse(xtb_run.can_start('running'))
        status = xtb_run.resolve_status(False, True)
        self.assertEqual(status, 'ok')
        self.assertTrue(xtb_run.can_start(status))


class TestDesyncChain(unittest.TestCase):
    """Viewer-vs-engine count mismatches are desync WARNINGS (stale
    scene, cosmetic) — never exceptions, never a launch block."""

    def test_viewer_mismatch_warns(self):
        # Viewer chain has 7 objects (engine counted 9 + head = 10) and
        # 80 atoms vs the 96-atom run input -> two desync lines, NO
        # hessian line (96 <= 100 budget), no raise.
        warnings = budget_guard.launch_budget_warnings(9, 7, 96, 80, 100)
        self.assertEqual(len(warnings), 2)
        self.assertIn('molecule count mismatch', warnings[0])
        self.assertIn('7', warnings[0])    # viewer chain objects
        self.assertIn('10', warnings[0])   # engine counted 9 + head
        self.assertIn('80', warnings[1])
        self.assertIn('96', warnings[1])
        self.assertFalse(
            any(setup_logic.HESSIAN_WARNING in line for line in warnings))

    def test_garbage_inputs_unavailable_line(self):
        # atoms_engine not numeric -> exactly ONE 'unavailable' line,
        # nothing else, never an exception (errors are DATA).
        warnings = budget_guard.launch_budget_warnings(9, 10, None, None, 100)
        self.assertEqual(len(warnings), 1)
        self.assertIn('unavailable', warnings[0])
        self.assertIn('budget re-check skipped', warnings[0])
        # The counts line degrades the same way.
        counts = budget_guard.launch_counts_line(9, None, 100)
        self.assertIn('unavailable', counts)


class TestContractGuardRails(unittest.TestCase):
    """The contract legs and the launch injection guard stay pinned
    through Phase 6."""

    def test_build_argv_rejects_quotes(self):
        # A quote in ANY argument would corrupt the list-argv safety
        # contract — the launch path refuses outright.
        with self.assertRaises(ValueError):
            xtbenv.build_argv('C:/x/y.exe', "sn'ake.xyz")
        with self.assertRaises(ValueError):
            xtbenv.build_argv('C:/x/"y".exe', 'snake.xyz')

    def test_abnormal_stderr_never_ok(self):
        # bad.err's 'abnormal termination' CONTAINS 'normal termination'
        # as a substring; exit 0 + files present must STILL fail the
        # stderr leg (failure-before-success ordering stays pinned).
        verdict = xtbenv.evaluate_run(
            0, _err_text('bad.err'), xtbenv.EXPECTED_FILES,
            ('g98.out', 'vibspectrum'))
        self.assertFalse(verdict.ok)
        self.assertTrue(any('abnormal' in p for p in verdict.problems))

    def test_record_shape_frozen(self):
        # The Phase-7 contract pin: the key set is fixed and the
        # initial record is fully specified (status 'running', empty
        # problems, all paths None) — consumers never reshape it.
        self.assertEqual(
            tuple(sorted(xtb_run.SPECTRA_RUN_KEYS)),
            ('g98_path', 'input_path', 'log_path', 'problems',
             'snake_id', 'status', 'vibspectrum_path', 'xtbopt_path'))
        record = xtb_run.new_spectra_run('run_9')
        self.assertEqual(set(record), set(xtb_run.SPECTRA_RUN_KEYS))
        self.assertEqual(record['snake_id'], 'run_9')
        self.assertEqual(record['status'], 'running')
        self.assertEqual(record['problems'], [])
        for key in ('input_path', 'g98_path', 'vibspectrum_path',
                    'xtbopt_path', 'log_path'):
            self.assertIsNone(record[key])


if __name__ == '__main__':
    unittest.main()
