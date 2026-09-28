"""DOCS-05 integrity-audit wrapper tests — tools/audit_requirements.py (plan 08-10).

Fixtures are EMBEDDED markdown strings (built here from an independent
hardcoded canonical-ID list), NEVER the live .planning/REQUIREMENTS.md:
the live ledger is mid-reconciliation while this plan executes. Fixture A
mirrors the historical current-state shape (some Complete-table rows with
unchecked boxes); fixture B mirrors the reconciled shape plus one
Evidence path that does not exist — proving every check bites in BOTH
directions without touching the real file.

python3.6, stdlib unittest, %-formatting, sys.path self-insert for the
tools/ directory (no tools/__init__.py — plugin-path safety gate).
Discovery: python3.6 -m unittest tests.test_audit_requirements -v
"""
import io
import os
import sys
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, 'tools'))

import audit_requirements as ar  # noqa: E402  (RED: module exists only from GREEN on)

# Independent hardcoded canonical list — the fixtures are built from THIS
# list, so if the tool's own list drifts the tests still bite (Pitfall 8:
# the stale-'44' count-drift class). 8+11+6+6+4+6+5 = 46.
IDS = (
    ['SETUP-%02d' % i for i in range(1, 9)] +
    ['GAME-%02d' % i for i in range(1, 12)] +
    ['STACK-%02d' % i for i in range(1, 7)] +
    ['SPECTRA-%02d' % i for i in range(1, 7)] +
    ['DATA-%02d' % i for i in range(1, 5)] +
    ['INFRA-%02d' % i for i in range(1, 7)] +
    ['DOCS-%02d' % i for i in range(1, 6)])
assert len(IDS) == 46

PENDING_10 = ['SETUP-07', 'SETUP-08', 'DATA-01', 'DATA-02', 'DATA-04',
              'DOCS-01', 'DOCS-02', 'DOCS-03', 'DOCS-04', 'DOCS-05']

# The historical mismatch set (table Complete, checkbox [ ]) from the
# pre-reconciliation ledger: SETUP-01, STACK-06, INFRA-01/02/03/05/06.
MISMATCH_7 = ['SETUP-01', 'STACK-06', 'INFRA-01', 'INFRA-02', 'INFRA-03',
              'INFRA-05', 'INFRA-06']

_GOOD_EVIDENCE = 'tests/test_gui_pins.py + smoke/14_release_e2e_smoke.py; serpentrum/gui.py; GATE V (08-11) approval (08-11-SUMMARY.md)'
_BAD_EVIDENCE = 'tests/test_fixture_missing_on_disk.py; GATE V (08-11) approval'


def _build(statuses, boxes, evidence=None):
    """Build an embedded requirements-ledger markdown fixture."""
    lines = ['# fixture ledger', '']
    for rid in IDS:
        lines.append('- [%s] **%s**: requirement text' % (boxes[rid], rid))
    lines.append('')
    header = '| Requirement | Phase | Status |'
    sep = '|-------------|-------|--------|'
    if evidence is not None:
        header += ' Evidence |'
        sep += '----------|'
    lines.append(header)
    lines.append(sep)
    for rid in IDS:
        row = '| %s | Phase 1 | %s |' % (rid, statuses[rid])
        if evidence is not None:
            row += ' %s |' % evidence[rid]
        lines.append(row)
    lines.append('')
    return '\n'.join(lines)


def _fixture_a():
    """Current-state shape: 46 rows, 10 Pending, 7 historical box mismatches."""
    statuses = dict((rid, 'Complete') for rid in IDS)
    statuses['GAME-10'] = 'Complete (owner-amended contract - see note)'
    for rid in PENDING_10:
        statuses[rid] = 'Pending'
    boxes = {}
    for rid in IDS:
        if rid in PENDING_10 or rid in MISMATCH_7:
            boxes[rid] = ' '
        else:
            boxes[rid] = 'x'
    return _build(statuses, boxes)


def _fixture_b():
    """Reconciled shape: boxes agree; Evidence column present incl. prose
    tokens ('GATE V (08-11) approval', '08-11-SUMMARY.md' — no '/', never
    path-checked); one row carries a path that does not exist."""
    statuses = dict((rid, 'Complete') for rid in IDS)
    statuses['GAME-10'] = 'Complete (owner-amended contract - see note)'
    for rid in PENDING_10:
        statuses[rid] = 'Pending'
    boxes = dict((rid, (' ' if rid in PENDING_10 else 'x')) for rid in IDS)
    evidence = dict((rid, _GOOD_EVIDENCE) for rid in IDS)
    evidence['GAME-10'] = _BAD_EVIDENCE
    return _build(statuses, boxes, evidence)


def _by_name(results):
    return dict((name, (ok, message)) for (name, ok, message) in results)


class TestCanonicalList(unittest.TestCase):
    """The tool's hardcoded canonical list must match the independent
    fixture list — count drift (the stale '44' class) fails loudly."""

    def test_canonical_list_matches_fixture(self):
        self.assertEqual(tuple(IDS), tuple(ar.CANONICAL_IDS))
        self.assertEqual(46, len(ar.CANONICAL_IDS))


class TestFixtureA(unittest.TestCase):
    """Current-state shape: ids/count green, checkbox-agreement RED on the
    historical 7 mismatches, evidence check vacuous (no Evidence column)."""

    def setUp(self):
        self.results = _by_name(ar.run_checks(_fixture_a(), REPO_ROOT))

    def test_ids_unique_ok(self):
        ok, msg = self.results['ids-unique']
        self.assertTrue(ok, msg)

    def test_row_count_ok(self):
        ok, msg = self.results['row-count']
        self.assertTrue(ok, msg)
        self.assertIn('46', msg)

    def test_evidence_paths_vacuous_ok(self):
        # Fixture A has no Evidence column: nothing to check, must pass.
        ok, msg = self.results['evidence-paths']
        self.assertTrue(ok, msg)

    def test_checkbox_agreement_fails_naming_the_seven(self):
        ok, msg = self.results['checkbox-agreement']
        self.assertFalse(ok, 'historical mismatch must fail check 4')
        for rid in MISMATCH_7:
            self.assertIn(rid, msg)

    def test_release_mode_lists_exactly_ten_pending(self):
        results = _by_name(ar.run_checks(_fixture_a(), REPO_ROOT,
                                         release=True))
        ok, msg = results['no-pending']
        self.assertFalse(ok)
        for rid in PENDING_10:
            self.assertIn(rid, msg)
        # and nothing else sneaks in
        for rid in IDS:
            if rid not in PENDING_10:
                self.assertNotIn(rid, msg)

    def test_default_mode_has_no_release_check(self):
        self.assertNotIn('no-pending', self.results)


class TestFixtureB(unittest.TestCase):
    """Reconciled shape: checks 1-4 green once the one bad Evidence path is
    fixed; the bad-path variant fails check 3 naming the path."""

    def test_reconciled_with_bad_evidence_path_fails_check3(self):
        results = _by_name(ar.run_checks(_fixture_b(), REPO_ROOT))
        ok, msg = results['evidence-paths']
        self.assertFalse(ok, 'missing evidence path must fail check 3')
        self.assertIn('tests/test_fixture_missing_on_disk.py', msg)
        self.assertIn('GAME-10', msg)
        # other checks stay green
        self.assertTrue(results['ids-unique'][0])
        self.assertTrue(results['row-count'][0])
        self.assertTrue(results['checkbox-agreement'][0])

    def test_fixed_evidence_paths_all_green(self):
        fixed = _fixture_b().replace(_BAD_EVIDENCE, _GOOD_EVIDENCE)
        results = _by_name(ar.run_checks(fixed, REPO_ROOT))
        for name in ('ids-unique', 'row-count', 'evidence-paths',
                     'checkbox-agreement'):
            self.assertTrue(results[name][0], '%s: %s' % results[name])

    def test_release_green_when_zero_pending(self):
        all_complete = _fixture_a().replace('Pending', 'Complete')
        # also flip the 10 boxes to x so agreement holds
        lines = []
        for line in all_complete.split('\n'):
            for rid in PENDING_10:
                if line.startswith('- [ ] **%s**' % rid):
                    line = line.replace('- [ ] **%s**' % rid,
                                        '- [x] **%s**' % rid)
            lines.append(line)
        all_complete = '\n'.join(lines)
        results = _by_name(ar.run_checks(all_complete, REPO_ROOT,
                                         release=True))
        self.assertTrue(results['no-pending'][0],
                        results['no-pending'][1])


class TestEdgeCases(unittest.TestCase):
    def test_unknown_status_fails_naming_row(self):
        bad = _fixture_a().replace(
            '| GAME-01 | Phase 1 | Complete |',
            '| GAME-01 | Phase 1 | Verified |')
        results = _by_name(ar.run_checks(bad, REPO_ROOT))
        ok, msg = results['checkbox-agreement']
        self.assertFalse(ok)
        self.assertIn('GAME-01', msg)
        self.assertIn('Verified', msg)

    def test_duplicate_id_fails_unique_check(self):
        dup = _fixture_a().replace(
            '| GAME-02 | Phase 1 | Complete |',
            '| GAME-02 | Phase 1 | Complete |\n| GAME-02 | Phase 1 | Complete |')
        results = _by_name(ar.run_checks(dup, REPO_ROOT))
        ok, msg = results['ids-unique']
        self.assertFalse(ok)
        self.assertIn('GAME-02', msg)

    def test_wrong_row_count_fails(self):
        # remove one row -> 45 -> count check fails loudly
        short = _fixture_a().replace('| INFRA-06 | Phase 1 | Complete |\n', '')
        results = _by_name(ar.run_checks(short, REPO_ROOT))
        ok, msg = results['row-count']
        self.assertFalse(ok)
        # and the missing ID is reported by the unique check
        ok2, msg2 = results['ids-unique']
        self.assertFalse(ok2)
        self.assertIn('INFRA-06', msg2)

    def test_prose_evidence_tokens_never_path_checked(self):
        # tokens without '/' ('GATE', 'V', '(08-11)', 'approval',
        # '08-11-SUMMARY.md') must never be treated as repo paths
        results = _by_name(ar.run_checks(_fixture_b().replace(
            _BAD_EVIDENCE, 'GATE V (08-11) approval (08-11-SUMMARY.md)'),
            REPO_ROOT))
        self.assertTrue(results['evidence-paths'][0],
                        results['evidence-paths'][1])


class TestCli(unittest.TestCase):
    """CLI: PASS/FAIL lines flushed, exit 0 when green, 1 on any failure."""

    def _write_fixture(self, text):
        import tempfile
        fd, path = tempfile.mkstemp(suffix='.md')
        with os.fdopen(fd, 'w') as fh:
            fh.write(text)
        self.addCleanup(os.unlink, path)
        return path

    def test_cli_green_exit_zero(self):
        path = self._write_fixture(
            _fixture_b().replace(_BAD_EVIDENCE, _GOOD_EVIDENCE))
        buf = io.StringIO()
        real = sys.stdout
        try:
            sys.stdout = buf
            code = ar.main([path])
        finally:
            sys.stdout = real
        out = buf.getvalue()
        self.assertEqual(0, code, out)
        self.assertIn('PASS', out)
        self.assertNotIn('FAIL', out)

    def test_cli_failure_exit_one_and_flag(self):
        path = self._write_fixture(_fixture_a())  # 7 mismatches
        buf = io.StringIO()
        real = sys.stdout
        try:
            sys.stdout = buf
            code = ar.main([path])
        finally:
            sys.stdout = real
        out = buf.getvalue()
        self.assertEqual(1, code)
        self.assertIn('FAIL checkbox-agreement', out)

        buf = io.StringIO()
        try:
            sys.stdout = buf
            code = ar.main(['--release', path])
        finally:
            sys.stdout = real
        out = buf.getvalue()
        self.assertEqual(1, code)
        self.assertIn('FAIL no-pending', out)
        for rid in PENDING_10:
            self.assertIn(rid, out)


if __name__ == '__main__':
    unittest.main()
