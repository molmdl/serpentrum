"""Headless Windows PyMOL QProcess-in-conda gate smoke — Phase 6 gate.

Run (from repo root; cwd is /mnt/c-backed so cmd.exe inherits C:\\ cwd):
    timeout 120 cmd.exe /c "C:\\src\\run-conda-pymol.bat -cq smoke\\09_qprocess_smoke.py"

Exit codes through the .bat are ALWAYS 0 — verdicts are flushed
sentinels grepped by tests/run_gates.py --smoke (this smoke is
INFORMATIONAL there: found by the [0-9][0-9]_*.py glob, run
non-blocking, never fails the gate — research Q7 promotion policy):
    SMOKE-OK QPROCESS        all steps passed
    SMOKE-FAIL <steps>       one or more steps failed

This smoke discharges the roadmap's Phase-6 gate: "QProcess in the
Windows conda PyMOL build". Every mechanism was live-probed
2026-09-24 (.planning/phases/06-xtb-pipeline/06-RESEARCH-runner.md,
Q1/Q3/Q4/Q7, probes A/B/C in tmp/spike_probe/):
  - probe A: QProcess/QEventLoop present under Qt 5.12.9 (PyQt5 via
    pymol.Qt); -cq headless has NO Q(Core)Application
    (COREAPP_BEFORE: None) -> this smoke creates one when absent
    (EQ-app-1); xtb.exe --version finished (0, NormalExit) with
    stderr b'normal termination of xtb\\r\\n' (the xtbenv.STDERR_SUCCESS
    contract literal).
  - probe B: proc.kill() ~300 ms into a real --ohess run ->
    finished(exitcode=62097, exitstatus=1=QProcess.CrashExit);
    state returns to NotRunning immediately; partial run dir retains
    no g98.out/vibspectrum (a killed run can never masquerade).
  - probe C: QTimer.singleShot fired DURING a live run (headless
    async-ness proof); QProcessEnvironment injection verified.
  - EQ-binary-1: xtb.exe is NOT on the Windows PATH and the repo-root
    xtb-6.7.1 symlink is Windows-inaccessible -> candidate list:
    SRP_XTB_PATH env -> xtbenv.detect_binary(None) which() probes ->
    C:\\xtb-6.7.1\\bin\\xtb.exe (verified working). No resolution ->
    SMOKE-FAIL naming every probe (never an opaque FailedToStart).
  - EQ-runner-1: the error signal is connected defensively via
    getattr(proc, 'errorOccurred', proc.error); a PROBE line records
    which attribute exists (settles research open question 5).

Template obligations (copied from smoke/01_skeleton_smoke.py):
  - named step functions + check() runner
  - flush=True on EVERY print (stdout is block-buffered when piped)
  - NO widget construction (headless C-abort is uncatchable)
  - never add smoke/__init__.py (findPlugins plugin-path safety)
  - NEVER trust __file__ under -cq — _resolve_root() validates
    candidates for serpentrum/__init__.py
  - NEVER waitForFinished (PITFALLS: blocking freezes the loop);
    QEventLoop + signal->loop.quit() + QTimer.singleShot safety
    timeout per step instead
  - the xtb runs below are REAL (no-fabrication rule): committed
    fixtures .planning/research/xtb-spike-fixtures/{co2,dimer2}.xyz
"""
import os
import shutil
import sys
import tempfile


def _resolve_root():
    """Repo root, defensively (see smoke/01_skeleton_smoke.py)."""
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

# Per-run temp dirs live under the Windows per-user temp (%TEMP%) —
# probe-verified writable end-to-end from the conda Python; NEVER the
# PyMOL session dir (PITFALLS 3.1: xtb sprays ~10 files into its cwd).
FIXTURES_DIR = os.path.join(ROOT, '.planning', 'research',
                            'xtb-spike-fixtures')

FAILURES = []
APP = None      # ensured QCoreApplication, kept alive for the script
XTB_EXE = None  # resolved by s_resolve_xtb for later steps


def check(name, fn):
    try:
        fn()
        print('SMOKE-STEP OK  %s' % name, flush=True)
    except Exception as exc:
        print('SMOKE-FAIL %s: %r' % (name, exc), flush=True)
        FAILURES.append(name)


def _qtcore():
    global APP
    from pymol.Qt import QtCore
    app = QtCore.QCoreApplication.instance()
    if app is None:
        app = QtCore.QCoreApplication([])   # EQ-app-1: exactly one app
        APP = app
    return QtCore, app


def _wait_run(QtCore, proc, timeout_ms, begin, on_terminal=None):
    """Drive proc to a terminal signal via QEventLoop (no blocking wait).

    begin() performs the proc.start(). ALL connections happen BEFORE
    begin() runs — live-pinned fact (this smoke, error-path step):
    errorOccurred(FailedToStart) is emitted SYNCHRONOUSLY during
    start() itself, so a post-start connect never sees it (the loop
    only quit via the safety timeout; queued delivery never replayed).
    quit() before exec_() is fine — exec_() then returns immediately.

    Returns a dict with keys 'code'/'status' when finished fired (plus
    'err' when the error signal fired) and 'timeout' True when the
    safety singleShot ended the loop first. finished(int,ExitStatus)
    IS emitted after a kill(); after a FailedToStart error Qt emits
    only the error signal, so both are wired to loop.quit.
    """
    loop = QtCore.QEventLoop()
    got = {}
    errsig = getattr(proc, 'errorOccurred', proc.error)

    def _on_finished(code, status):
        got['code'] = code
        got['status'] = status
        if on_terminal is not None:
            on_terminal('finished', got)
        loop.quit()

    def _on_error(err):
        got['err'] = err
        if on_terminal is not None:
            on_terminal('error', got)
        loop.quit()

    proc.finished.connect(_on_finished)
    errsig.connect(_on_error)
    QtCore.QTimer.singleShot(timeout_ms, loop.quit)
    begin()
    loop.exec_()   # legal: smoke scripts are dev-side, not serpentrum/
    got.setdefault('timeout', 'code' not in got and 'err' not in got)
    return got


# --- Steps -----------------------------------------------------------------

def s_qprocess_available():
    QtCore, app = _qtcore()
    assert hasattr(QtCore, 'QProcess'), 'QtCore.QProcess missing'
    assert hasattr(QtCore, 'QEventLoop'), 'QtCore.QEventLoop missing'
    assert app is QtCore.QCoreApplication.instance(), 'app not installed'
    print('PROBE QT: %s, has QProcess=True, app=%s'
          % (QtCore.QT_VERSION_STR, type(app).__name__), flush=True)


def s_resolve_xtb():
    global XTB_EXE
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    from serpentrum import xtbenv   # PURE, safe headless (no Qt import)
    probes = []
    # 1. explicit env override (smoke/dev seam)
    env_path = os.environ.get('SRP_XTB_PATH')
    probes.append('SRP_XTB_PATH: %s' % (env_path or 'not set'))
    if env_path and os.path.isfile(env_path):
        XTB_EXE = env_path
    # 2. which() probes (xtb.exe then xtb) via the pure helper
    if XTB_EXE is None:
        found = xtbenv.detect_binary(None)
        probes.append("xtbenv.detect_binary(None): %s" % (found or 'None'))
        if found:
            XTB_EXE = found
    # 3. verified fallback path (EQ-binary-1)
    if XTB_EXE is None:
        fallback = 'C:\\xtb-6.7.1\\bin\\xtb.exe'
        ok = os.path.isfile(fallback)
        probes.append('fallback %s: %s' % (fallback,
                                           'exists' if ok else 'missing'))
        if ok:
            XTB_EXE = fallback
    if XTB_EXE is None:
        raise AssertionError(
            'xtb binary resolution failed; probes tried: %s. '
            'xtb.exe not on PATH; repo symlink not Windows-traversable; '
            'set SRP_XTB_PATH or install at C:\\xtb-6.7.1'
            % ' | '.join(probes))
    print('PROBE XTB_EXE: %s' % XTB_EXE, flush=True)


def s_version_run():
    QtCore, _app = _qtcore()
    proc = QtCore.QProcess()
    # EQ-runner-1: defensive error-signal choice + PROBE which exists.
    err_name = ('errorOccurred' if hasattr(proc, 'errorOccurred')
                else 'error')
    assert getattr(proc, err_name) is not None
    print('PROBE ERR_SIGNAL_ATTR: %s' % err_name, flush=True)
    chunks_stderr = []
    fired = {}
    proc.started.connect(lambda: fired.setdefault('started', True))
    proc.readyReadStandardError.connect(
        lambda: chunks_stderr.append(bytes(proc.readAllStandardError())))
    timer = QtCore.QElapsedTimer()
    timer.start()
    got = _wait_run(QtCore, proc, 30000,
                    begin=lambda: proc.start(XTB_EXE, ['--version']))
    elapsed = timer.elapsed()
    print('PROBE VERSION elapsed_ms: %d' % elapsed, flush=True)
    assert fired.get('started'), 'started signal never fired'
    assert not got.get('timeout'), 'safety timeout hit (30 s)'
    assert 'code' in got, 'finished never delivered: %r' % (got,)
    assert got['code'] == 0, 'exit code %r != 0' % (got['code'],)
    assert got['status'] == QtCore.QProcess.NormalExit, \
        'exitStatus %r != NormalExit' % (got['status'],)
    stderr_text = b''.join(chunks_stderr).decode('utf-8', 'replace')
    assert 'normal termination of xtb' in stderr_text, \
        'stderr contract literal missing: %r' % (stderr_text[:120],)


def s_responsiveness_during_run():
    """QTimer fires DURING a live QProcess run (headless async-ness).

    Fixture choice pinned by live measurement: co2 --ohess completed in
    89 ms end-to-end here (probe-verified the day the smoke was written)
    — far too fast for a pre-scheduled tick to fire mid-run reliably.
    dimer2 (26 atoms, probe geometry ~2.8 s) gives the 300 ms tick
    an order of magnitude of margin. The tick records the process state
    at fire time; it MUST be QProcess.Running.
    """
    QtCore, _app = _qtcore()
    with open(os.path.join(FIXTURES_DIR, 'dimer2.xyz'), 'r') as fh:
        xyz_text = fh.read()
    tmpdir = tempfile.mkdtemp(prefix='srp_smoke_run_')
    try:
        with open(os.path.join(tmpdir, 'snake.xyz'), 'w') as fh:
            fh.write(xyz_text)
        proc = QtCore.QProcess()
        tick = {}
        timer = QtCore.QElapsedTimer()

        def _tick():
            tick['fired'] = True
            tick['state'] = proc.state()
            tick['elapsed'] = timer.elapsed()

        def _terminal(kind, _got):
            tick.setdefault('finish_elapsed', timer.elapsed())

        QtCore.QTimer.singleShot(300, _tick)
        proc.setWorkingDirectory(tmpdir)
        timer.start()
        got = _wait_run(
            QtCore, proc, 60000,
            begin=lambda: proc.start(XTB_EXE, ['snake.xyz', '--ohess']),
            on_terminal=_terminal)
        elapsed = timer.elapsed()
        print('PROBE RUN elapsed_ms: %d tick_at_ms: %s tick_state: %s'
              % (elapsed, tick.get('elapsed'), tick.get('state')),
              flush=True)
        assert tick.get('fired'), 'responsiveness tick never fired'
        assert tick['state'] == QtCore.QProcess.Running, \
            'tick fired while NOT running (state=%r)' % (tick['state'],)
        assert tick['elapsed'] < tick.get('finish_elapsed', 10 ** 12), \
            'tick fired after the run finished'
        assert not got.get('timeout'), 'safety timeout hit (60 s)'
        assert 'code' in got, 'finished never delivered: %r' % (got,)
        assert got['code'] == 0, 'exit code %r != 0' % (got['code'],)
        assert got['status'] == QtCore.QProcess.NormalExit, \
            'exitStatus %r != NormalExit' % (got['status'],)
    finally:
        # pitfall 10: delete only AFTER finished (state NotRunning).
        shutil.rmtree(tmpdir, ignore_errors=True)


def s_kill_cancel():
    """kill() ~300 ms into a real --ohess run -> CrashExit (probe B)."""
    QtCore, _app = _qtcore()
    with open(os.path.join(FIXTURES_DIR, 'dimer2.xyz'), 'r') as fh:
        xyz_text = fh.read()
    tmpdir = tempfile.mkdtemp(prefix='srp_smoke_dimer_')
    try:
        with open(os.path.join(tmpdir, 'snake.xyz'), 'w') as fh:
            fh.write(xyz_text)
        proc = QtCore.QProcess()
        state_at_finished = {}

        def _terminal(kind, _got):
            state_at_finished['state'] = proc.state()

        timer = QtCore.QElapsedTimer()
        proc.setWorkingDirectory(tmpdir)
        QtCore.QTimer.singleShot(300, proc.kill)
        timer.start()
        got = _wait_run(
            QtCore, proc, 30000,
            begin=lambda: proc.start(XTB_EXE, ['snake.xyz', '--ohess']),
            on_terminal=_terminal)
        elapsed = timer.elapsed()
        print('PROBE KILL elapsed_ms: %d exitcode: %s exitstatus: %s '
              'state_at_finished: %s'
              % (elapsed, got.get('code'), got.get('status'),
                 state_at_finished.get('state')), flush=True)
        assert not got.get('timeout'), 'safety timeout hit (30 s)'
        assert 'code' in got, 'finished never delivered: %r' % (got,)
        assert got['status'] == QtCore.QProcess.CrashExit, \
            'exitStatus %r != QProcess.CrashExit' % (got['status'],)
        assert state_at_finished.get('state') == QtCore.QProcess.NotRunning, \
            'state at finished %r != NotRunning' \
            % (state_at_finished.get('state'),)
        # probe-B fact: partial files cannot masquerade as success.
        present = os.listdir(tmpdir)
        for name in ('g98.out', 'vibspectrum'):
            assert name not in present, \
                'killed run left %r in %r — masquerade hazard' \
                % (name, tmpdir)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def s_error_path_probe():
    """Nonexistent exe -> error signal surfaces, nothing crashes
    (pitfall 9: 'xtb not found' must surface, never an opaque death)."""
    QtCore, _app = _qtcore()
    proc = QtCore.QProcess()
    err_name = ('errorOccurred' if hasattr(proc, 'errorOccurred')
                else 'error')
    # _wait_run wires the error/finished signals BEFORE start, so the
    # FailedToStart emission cannot race past the connect.
    got = _wait_run(QtCore, proc, 10000,
                    begin=lambda: proc.start(XTB_EXE + '_missing',
                                             ['--version']))
    err_code = proc.error()
    print('PROBE ERR_PATH attr: %s err_signal: %r proc.error(): %s '
          'state: %s'
          % (err_name, got.get('err'), err_code, proc.state()),
          flush=True)
    fired = ('err' in got) or (err_code == QtCore.QProcess.FailedToStart)
    assert fired, \
        'neither the error signal nor FailedToStart was observed: %r' \
        % (got,)
    assert err_code != QtCore.QProcess.UnknownError, \
        'unexpected UnknownError on failed start: %r' % (err_code,)
    assert proc.state() == QtCore.QProcess.NotRunning, \
        'proc left %r after failed start' % (proc.state(),)


for _name, _fn in [
    ('qprocess_available', s_qprocess_available),
    ('resolve_xtb', s_resolve_xtb),
    ('version_run', s_version_run),
    ('responsiveness_during_run', s_responsiveness_during_run),
    ('kill_cancel', s_kill_cancel),
    ('error_path_probe', s_error_path_probe),
]:
    check(_name, _fn)

if FAILURES:
    print('SMOKE-FAIL %s' % ','.join(FAILURES), flush=True)
else:
    print('SMOKE-OK QPROCESS', flush=True)
