"""Headless QProcess wall-time calibration probe (plan 06-07, SC5).

Run (from the repo root; cwd is /mnt/c-backed so cmd.exe inherits C:\\ cwd):
    timeout 900 cmd.exe /c "C:\\src\\run-conda-pymol.bat -cq tools\\measure_calib_qprocess.py"

Measures the TRUE USER-PERCEIVED wall (QElapsedTimer around the whole
QProcess run, incl. process-spawn overhead) for the committed 104-atom
calibration fixture (tests/fixtures/calib_snake_104.xyz) on REAL runs —
twice, serially:

  run A: argv ['snake.xyz', '--ohess', '-P', '4']  (best measured capped
         setting from the WSL sweep; the candidate DEFAULT_RUN_KNOBS cap
         per the UI-jank rationale, PITFALLS.md:333,348)
  run B: argv ['snake.xyz', '--ohess']             (uncapped; the sweep
         winner on wall time)

Prints flushed 'PROBE WALL-MS' lines + the stderr head and a final
'CALIB-OK QPROCESS' / 'CALIB-FAIL' sentinel. Exit codes through the .bat
are always 0 — verdicts travel via the sentinel only.

Mechanics are copied from smoke/09_qprocess_smoke.py (live-probed
2026-09-24, 06-RESEARCH-runner.md Q1/Q3/Q4/Q7): one QCoreApplication
ensured, QEventLoop + signal->loop.quit() + single-shot safety timeout
(NEVER waitForFinished), defensive error-signal attribute, exe candidate
list SRP_XTB_PATH -> xtbenv.detect_binary(None) -> C:\\xtb-6.7.1\\bin\\xtb.exe.
Pure-runs only: no widget construction, no serpentrum changes.

python3.6 syntax (gate 1 syntax-walks tools/); the conda runtime is 3.9.
"""
import os
import shutil
import sys
import tempfile


def _resolve_root():
    """Repo root, defensively (never trust __file__ under -cq)."""
    candidates = []
    if '__file__' in globals():
        _f = os.path.abspath(__file__)
        candidates.append(os.path.dirname(os.path.dirname(_f)))
        candidates.append(os.path.dirname(_f))
    candidates.append(os.getcwd())
    for _c in candidates:
        if os.path.isfile(os.path.join(_c, 'serpentrum', '__init__.py')):
            return _c
    return os.getcwd()


ROOT = _resolve_root()
FIXTURE = os.path.join(ROOT, 'tests', 'fixtures', 'calib_snake_104.xyz')
RUNS = (
    ('P4', ['snake.xyz', '--ohess', '-P', '4']),
    ('uncapped', ['snake.xyz', '--ohess']),
)
SAFETY_TIMEOUT_MS = 600000  # 10 min per run; sweep saw <= ~5 min at -P 1


def _resolve_exe():
    """The smoke-09 candidate list, 06-RESEARCH-runner.md EQ-binary-1."""
    env_path = os.environ.get('SRP_XTB_PATH')
    if env_path and os.path.isfile(env_path):
        return env_path
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    from serpentrum import xtbenv  # PURE, safe headless
    found = xtbenv.detect_binary(None)
    if found:
        return found
    fallback = 'C:\\xtb-6.7.1\\bin\\xtb.exe'
    if os.path.isfile(fallback):
        return fallback
    return None


def _qt():
    from pymol.Qt import QtCore
    app = QtCore.QCoreApplication.instance()
    if app is None:
        app = QtCore.QCoreApplication([])
    return QtCore, app


def _run_once(QtCore, exe, label, argv):
    """One real --ohess run driven to finished via QEventLoop.

    Returns (elapsed_ms, finish_code, exit_status, stderr_head) or
    raises AssertionError on timeout/error conditions.
    """
    with open(FIXTURE, 'r') as fh:
        xyz_text = fh.read()
    tmpdir = tempfile.mkdtemp(prefix='srp_calib_%s_' % label)
    try:
        with open(os.path.join(tmpdir, 'snake.xyz'), 'w') as fh:
            fh.write(xyz_text)
        proc = QtCore.QProcess()
        proc.setWorkingDirectory(tmpdir)
        loop = QtCore.QEventLoop()
        got = {}
        errsig = getattr(proc, 'errorOccurred', proc.error)
        stderr_chunks = []
        proc.readyReadStandardError.connect(
            lambda: stderr_chunks.append(bytes(proc.readAllStandardError())))
        proc.finished.connect(
            lambda code, status: (got.update(code=code, status=status),
                                  loop.quit()))
        errsig.connect(lambda err: (got.update(err=err), loop.quit()))
        QtCore.QTimer.singleShot(SAFETY_TIMEOUT_MS, loop.quit)
        timer = QtCore.QElapsedTimer()
        timer.start()
        proc.start(exe, argv)
        loop.exec_()
        elapsed = timer.elapsed()
        stderr_text = b''.join(stderr_chunks).decode('utf-8', 'replace')
        head = ' | '.join(stderr_text.splitlines()[:3])[:200]
        print('PROBE WALL-MS %s: %d' % (label, elapsed), flush=True)
        print('PROBE STDERR-HEAD %s: %s' % (label, head), flush=True)
        if 'code' not in got:
            raise AssertionError(
                '%s: run did not finish (timeout or FailedToStart %r)'
                % (label, got))
        assert got['code'] == 0, '%s: exit code %r != 0' % (label, got['code'])
        assert got['status'] == QtCore.QProcess.NormalExit, \
            '%s: exitStatus %r != NormalExit' % (label, got['status'])
        assert 'normal termination of xtb' in stderr_text, \
            '%s: stderr contract literal missing: %r' % (label, head)
        present = os.listdir(tmpdir)
        for name in ('g98.out', 'vibspectrum'):
            assert name in present, \
                '%s: contract file %r missing in %r' % (label, name, tmpdir)
        return elapsed, got['code'], got['status'], head
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def main():
    QtCore, _app = _qt()
    exe = _resolve_exe()
    assert exe is not None, 'no xtb binary resolved (SRP_XTB_PATH unset)'
    print('PROBE XTB_EXE: %s' % exe, flush=True)
    print('PROBE FIXTURE: %s' % FIXTURE, flush=True)
    results = []
    for label, argv in RUNS:
        elapsed, code, status, head = _run_once(QtCore, exe, label, argv)
        results.append((label, elapsed))
    for label, elapsed in results:
        print('CALIB WALL-MS %s: %d' % (label, elapsed), flush=True)
    print('CALIB-OK QPROCESS', flush=True)


try:
    main()
except Exception as exc:
    print('CALIB-FAIL: %r' % (exc,), flush=True)
