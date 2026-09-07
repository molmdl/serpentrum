"""xtbenv contract tests vs committed .err fixture bytes (plan 02-02).

The fixture .err files are read IN PLACE from
.planning/research/xtb-spike-fixtures/ (committed; present in every
parallel worktree — no copies are made by this plan). Their exact bytes:
ohess/co2/dimer2/repro_oh = 'normal termination of xtb\\r\\n' (27 B);
bad = 'abnormal termination of xtb\\r\\n' (29 B). Exit codes are NOT
recorded in the fixtures (PITFALLS 3 documents rc=128 for the bad run),
so unit tests use synthetic rc values with the fixture stderr text.

Discovery command (verified on python3.6.9 — NOTE: `-t .` FAILS on
python3.6 with a non-package start dir; do not add it):

    python3.6 -m unittest discover -s tests -p "test_xtbenv.py" -v

Convention: every test file in tests/ repeats the sys.path self-insert
below (bioCHEMeleon pattern). tests/ deliberately has NO __init__.py —
the dev plugin path IS the repo root, and findPlugins would treat a
package dir here as a second plugin.
"""
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import serpentrum.xtbenv as xtbenv  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURES = os.path.join(ROOT, '.planning', 'research', 'xtb-spike-fixtures')

SUCCESS_ERRS = ('ohess.err', 'co2.err', 'dimer2.err', 'repro_oh.err')
EXPECTED = ('g98.out', 'vibspectrum')


def _err_text(name):
    """Fixture .err bytes -> utf-8 text, passed AS-IS (CRLF retained)."""
    with open(os.path.join(FIXTURES, name), 'rb') as handle:
        return handle.read().decode('utf-8')


class TestEvaluateRunFixtures(unittest.TestCase):
    """The 3-leg success contract proven against committed fixture bytes."""

    def test_success_fixtures_ok_with_all_files(self):
        for name in SUCCESS_ERRS:
            text = _err_text(name)
            # CRLF must be retained end-to-end: the substring contract
            # check has to tolerate the trailing \r\n.
            self.assertIn('\r\n', text, name)
            verdict = xtbenv.evaluate_run(
                0, text, EXPECTED, EXPECTED)
            self.assertTrue(verdict.ok, name)
            self.assertEqual(verdict.problems, [], name)

    def test_bad_fixture_three_leg_failure(self):
        text = _err_text('bad.err')
        verdict = xtbenv.evaluate_run(128, text, EXPECTED, ())
        self.assertFalse(verdict.ok)
        self.assertEqual(len(verdict.problems), 3)
        self.assertTrue(any('exit code' in p for p in verdict.problems))
        self.assertTrue(any('abnormal termination' in p
                            for p in verdict.problems))
        files_problems = [p for p in verdict.problems
                          if 'g98.out' in p or 'vibspectrum' in p]
        self.assertEqual(len(files_problems), 1)
        self.assertIn('g98.out', files_problems[0])
        self.assertIn('vibspectrum', files_problems[0])

    def test_repro_oh_story_stderr_success_without_files_rejected(self):
        # THE phase criterion 3 case: stderr said 'normal termination'
        # (identical bytes in repro_oh.err) yet NO output files were
        # produced. Success must be rejected with exactly ONE problem,
        # and that problem must be about files only.
        text = _err_text('ohess.err')
        verdict = xtbenv.evaluate_run(0, text, EXPECTED, ())
        self.assertFalse(verdict.ok)
        self.assertEqual(len(verdict.problems), 1)
        problem = verdict.problems[0]
        self.assertIn('g98.out', problem)
        self.assertIn('vibspectrum', problem)
        self.assertNotIn('exit', problem)
        self.assertNotIn('termination', problem)

    def test_partial_files_problem_names_only_missing(self):
        text = _err_text('ohess.err')
        verdict = xtbenv.evaluate_run(0, text, EXPECTED, ('g98.out',))
        self.assertFalse(verdict.ok)
        self.assertEqual(len(verdict.problems), 1)
        problem = verdict.problems[0]
        self.assertIn('vibspectrum', problem)
        self.assertNotIn('g98.out', problem)

    def test_subset_expectation_extra_present_files_fine(self):
        text = _err_text('co2.err')
        verdict = xtbenv.evaluate_run(
            0, text, ('vibspectrum',), ('g98.out', 'vibspectrum'))
        self.assertTrue(verdict.ok)
        self.assertEqual(verdict.problems, [])

    def test_leg_independence(self):
        good_text = _err_text('ohess.err')
        bad_text = _err_text('bad.err')
        present = ('g98.out', 'vibspectrum')

        # Exit 0 + bad stderr + files present -> ONLY the stderr problem.
        verdict = xtbenv.evaluate_run(0, bad_text, EXPECTED, present)
        self.assertFalse(verdict.ok)
        self.assertEqual(len(verdict.problems), 1)
        self.assertIn('abnormal termination', verdict.problems[0])

        # rc=1 + good stderr + files present -> ONLY the exit problem.
        verdict = xtbenv.evaluate_run(1, good_text, EXPECTED, present)
        self.assertFalse(verdict.ok)
        self.assertEqual(len(verdict.problems), 1)
        self.assertEqual(verdict.problems[0], 'exit code 1 != 0')

    def test_stderr_lacks_message_format(self):
        # Empty stderr -> the 'lacks' branch with an empty got-excerpt.
        verdict = xtbenv.evaluate_run(0, '', ('g98.out',), ('g98.out',))
        self.assertFalse(verdict.ok)
        self.assertEqual(len(verdict.problems), 1)
        self.assertIn("stderr lacks 'normal termination'",
                      verdict.problems[0])
        self.assertIn("(got: '')", verdict.problems[0])

        # Whitespace-collapsed excerpt, capped at 60 chars.
        verdict = xtbenv.evaluate_run(
            0, 'a\r\n   b\tc' + 'x' * 100, ('g98.out',), ('g98.out',))
        problem = verdict.problems[0]
        self.assertIn("(got: 'a b c", problem)
        start = problem.index("(got: '") + len("(got: '")
        end = problem.rindex("')")
        self.assertLessEqual(len(problem[start:end]), 60)


class _RecordingWhich(object):
    """Fake which_fn: records every query, returns canned answers.

    Dependency injection per plan 02-02 — NO xtb install needed and NO
    sys.modules stubs (the zero-stub rule bans pymol/Qt module stubbing;
    a plain injected callable is just a parameter).
    """

    def __init__(self, answers):
        self._answers = answers
        self.queries = []

    def __call__(self, name):
        self.queries.append(name)
        return self._answers.get(name)


class TestValidateBinaryPath(unittest.TestCase):
    """Validation rules proven against real tmpdir files (no xtb)."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix='srp_test_')
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def _real_file(self):
        path = os.path.join(self.tmp, 'xtb.exe')
        with open(path, 'wb') as handle:
            handle.write(b'MZ')
        return path

    def test_existing_file_valid(self):
        self.assertEqual(xtbenv.validate_binary_path(self._real_file()), [])

    def test_missing_path_does_not_exist(self):
        missing = os.path.join(self.tmp, 'nope.exe')
        problems = xtbenv.validate_binary_path(missing)
        self.assertEqual(len(problems), 1)
        self.assertIn('does not exist', problems[0])

    def test_directory_is_not_a_file(self):
        problems = xtbenv.validate_binary_path(self.tmp)
        self.assertEqual(len(problems), 1)
        self.assertIn('not a file', problems[0])

    def test_quote_characters_rejected(self):
        quoted = self._real_file() + '"'
        problems = xtbenv.validate_binary_path(quoted)
        self.assertTrue(any('quote' in p for p in problems))

    def test_problems_accumulate(self):
        # Existing DIRECTORY whose name contains a quote: 'not a file'
        # AND 'quote' both reported.
        quoted_dir = os.path.join(self.tmp, "di'r")
        os.makedirs(quoted_dir)
        problems = xtbenv.validate_binary_path(quoted_dir)
        self.assertEqual(len(problems), 2)
        self.assertTrue(any('not a file' in p for p in problems))
        self.assertTrue(any('quote' in p for p in problems))

    def test_empty_none_and_non_string(self):
        self.assertEqual(xtbenv.validate_binary_path(''),
                         ['xtb path is empty'])
        self.assertEqual(xtbenv.validate_binary_path(None),
                         ['xtb path is empty'])
        self.assertEqual(xtbenv.validate_binary_path(42),
                         ['xtb path is empty'])


class TestDetectBinary(unittest.TestCase):
    """Probe order (configured -> xtb.exe -> xtb) proven with DI fakes."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix='srp_test_')
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def _real_file(self):
        path = os.path.join(self.tmp, 'xtb.exe')
        with open(path, 'wb') as handle:
            handle.write(b'MZ')
        return path

    def test_valid_configured_path_wins_without_probing(self):
        configured = self._real_file()
        fake = _RecordingWhich({'xtb.exe': None, 'xtb': None})
        self.assertEqual(xtbenv.detect_binary(configured, fake), configured)
        self.assertEqual(fake.queries, [])

    def test_invalid_configured_path_falls_through_to_which(self):
        # Missing on disk -> validation problem -> which probe runs.
        missing = os.path.join(self.tmp, 'missing.exe')
        fake = _RecordingWhich({'xtb.exe': 'C:\\xtb\\xtb.exe'})
        self.assertEqual(xtbenv.detect_binary(missing, fake),
                         'C:\\xtb\\xtb.exe')
        self.assertEqual(fake.queries, ['xtb.exe'])

        # A DIRECTORY configured path also fails validation -> falls
        # through, and the probe order holds (xtb.exe before xtb).
        fake2 = _RecordingWhich({'xtb.exe': None, 'xtb': '/usr/bin/xtb'})
        self.assertEqual(xtbenv.detect_binary(self.tmp, fake2),
                         '/usr/bin/xtb')
        self.assertEqual(fake2.queries, ['xtb.exe', 'xtb'])

    def test_windows_conda_env_probed_before_linux(self):
        fake = _RecordingWhich({'xtb.exe': None, 'xtb': '/usr/bin/xtb'})
        self.assertEqual(xtbenv.detect_binary(None, fake), '/usr/bin/xtb')
        self.assertEqual(fake.queries, ['xtb.exe', 'xtb'])
        self.assertLess(fake.queries.index('xtb.exe'),
                        fake.queries.index('xtb'))

    def test_nothing_found_returns_none(self):
        fake = _RecordingWhich({})
        self.assertIsNone(xtbenv.detect_binary(None, fake))
        self.assertEqual(fake.queries, ['xtb.exe', 'xtb'])


if __name__ == '__main__':
    unittest.main()
