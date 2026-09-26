"""Headless Windows PyMOL xtb-runner CONTRACT smoke — Phase 6, plan 06-08.

Run (from repo root; cwd is /mnt/c-backed so cmd.exe inherits C:\\ cwd):
    timeout 300 cmd.exe /c "C:\\src\\run-conda-pymol.bat -cq smoke\\11_xtb_runner_smoke.py"
(longer timeout than the other smokes: several REAL xtb runs happen
inside — co2 ~0.25 s success, dimer2 runs killed at ~300 ms).

Exit codes through the .bat are ALWAYS 0 — verdicts are flushed
    sentinels grepped by tests/run_gates.py --smoke (this smoke is
    INFORMATIONAL there per EQ-smoke-1: found by the [0-9][0-9]_*.py glob,
    run non-blocking, never fails the gate; 06-12 recorded the decision
    to KEEP it informational — no promotion was instructed):
    SMOKE-OK XTB-RUNNER    all steps passed
    SMOKE-FAIL <steps>     one or more steps failed

This smoke proves the plan-06-05 XtbRunController end-to-end against
the REAL xtb.exe (no-fabrication rule: real exe, committed fixtures;
a FAILED run asserted as failed is legitimate testing):
  - s_qprocess_available     QtCore + QCoreApplication ensure (smoke 09)
  - s_runner_constructs      module load under the loader name
                             (pmg_tk.startup.serpentrum.xtb_runner; smoke
                             01 identity mechanics); controller built on
                             the pmg_tk.startup._serpentrum anchor —
                             never module globals
  - s_resolve_xtb            candidate list: SRP_XTB_PATH env ->
                             xtbenv.detect_binary(None) -> the verified
                             C:\\xtb-6.7.1\\bin\\xtb.exe fallback
                             (EQ-binary-1; FAIL names every probe)
  - s_arun_success_contract  REAL co2 --ohess run: start() True, started
                             fired, log lines streamed, run_finished
                             'ok' with problems==[]; anchor.spectra_run
                             'ok' with the frozen SPECTRA_RUN_KEYS shape
                              and non-None paths; the stable dir (under
                              STABLE_ROOT via SRP_SPECTRA_DIR, 06-12)
                              holds snake.xyz/xtb.log/g98.out/vibspectrum/
                              xtbopt.xyz; the srp_ spray dir is GONE at
                             terminal; AND a second run starts after
                             completion (guard releases, SC2)
  - s_responsiveness_tick    QTimer fires DURING a dimer2 run while
                             ctrl.status() == 'running' (headless
                             async-ness proof, SC1 mechanics)
  - s_cancel_path            dimer2 killed at ~300 ms -> 'cancelled'
                             (NOT ok — no fake success; the stable dir
                             for that snake holds snake.xyz + xtb.log
                             but NO g98.out/vibspectrum/xtbopt.xyz);
                             a new run starts after cancel (SC2)
  - s_no_double_run_guard    start() while 'running' returns False +
                             emits the 'already active' log line, no
                             record written
  - s_start_failure_path     bad exe -> start() returns False and
                             run_finished 'failed' SYNCHRONOUSLY (the
                             06-05 synchronous-FailedToStart path:
                             errorOccurred fires inside start(), the
                             terminal discipline runs before start()
                             returns — pitfall 9 'surface, never die')

Controller mechanics honored (live-pinned by smoke 09 / 06-03-SUMMARY):
  - connect-before-start is BINDING: errorOccurred(FailedToStart) fires
    SYNCHRONOUSLY inside proc.start() — run_finished for the bad-exe
    case is emitted inside start() itself, so this smoke connects
    BEFORE calling start() and asserts the record immediately after
    (no event-loop wait on that step).
  - Waiting pattern everywhere else: connect ctrl.run_finished ->
    record + loop.quit; QTimer.singleShot safety timeout; process
    events via the loop only (no processEvents pumping, NEVER
    waitForFinished, no subprocess module).

Template obligations (copied from smoke/01_skeleton_smoke.py):
  - named step functions + check() runner
  - flush=True on EVERY print (stdout is block-buffered when piped)
  - NO widget construction (headless C-abort is uncatchable)
  - never add smoke/__init__.py (findPlugins plugin-path safety)
  - NEVER trust __file__ under -cq — _resolve_root() validates
    candidates for serpentrum/__init__.py
  - new-style .connect() only; bytes(...).decode('utf-8','replace')
    for any QByteArray
  - fixtures: .planning/research/xtb-spike-fixtures/{co2,dimer2}.xyz
"""
import importlib
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

FIXTURES_DIR = os.path.join(ROOT, '.planning', 'research',
                            'xtb-spike-fixtures')

# Owner-directed (06-12): the stable spectra dir is user-settable via
# SRP_SPECTRA_DIR (default <cwd>/srp_spectra). Point it at a fresh
# tempdir BEFORE any run step so the smoke never writes into the repo
# tree regardless of PyMOL's cwd, and so the assertions below know the
# exact stable root.
STABLE_ROOT = tempfile.mkdtemp(prefix='srp_smoke11_stable_')
os.environ['SRP_SPECTRA_DIR'] = STABLE_ROOT

FAILURES = []
APP = None       # ensured QCoreApplication, kept alive for the script
XTB_EXE = None   # resolved by s_resolve_xtb for later steps
PLUGIN = None    # pmg_tk.startup.serpentrum (loader name)
RUNNER = None    # pmg_tk.startup.serpentrum.xtb_runner
XTBRUN = None    # pmg_tk.startup.serpentrum.xtb_run (state constants)
ANCHOR = None    # pmg_tk.startup._serpentrum
CTRL = None      # the XtbRunController under test


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


def _wait_controller(timeout_ms, begin):
    """Drive CTRL to run_finished via QEventLoop (no blocking wait).

    ALL connections happen BEFORE begin() runs (the connect-before-
    start pin — the bad-exe error path emits inside start() itself;
    queued delivery would pass the connect by). quit() before exec_()
    is fine — exec_() then returns immediately. Returns a dict with
    'status'/'problems' when run_finished fired, and 'timeout' True
    when the safety singleShot ended the loop first.
    """
    from pymol.Qt import QtCore
    loop = QtCore.QEventLoop()
    got = {}

    def _on_finished(status, problems):
        got['status'] = status
        got['problems'] = list(problems)
        loop.quit()

    CTRL.run_finished.connect(_on_finished)
    QtCore.QTimer.singleShot(timeout_ms, loop.quit)
    begin()
    loop.exec_()   # legal: smoke scripts are dev-side, not serpentrum/
    got.setdefault('timeout', 'status' not in got)
    return got


def _fixture_text(name):
    with open(os.path.join(FIXTURES_DIR, name), 'r') as fh:
        return fh.read()


def _base_dir():
    """Windows per-user temp — probe-verified (06-RESEARCH-runner Q5)."""
    return tempfile.gettempdir()


def _stable_dir(snake_id):
    """Stable dir for a snake id under the env-overridden STABLE_ROOT."""
    return os.path.join(STABLE_ROOT, snake_id)


def _clean_stable(snake_id):
    """Remove a stale stable dir for OUR snake id before its step.

    Stable dirs are left in place after each step (they ARE the
    artifact policy under test); this only makes repeated smoke runs
    self-contained. Prefix-guarded by the literal smoke11_ id shape —
    never an arbitrary path.
    """
    assert snake_id.startswith('smoke11_'), snake_id
    path = _stable_dir(snake_id)
    if os.path.isdir(path):
        shutil.rmtree(path, ignore_errors=True)


def _srp_entries(base_dir):
    """srp_ SPRAY dirs in <base_dir> (leak scan).

    xtbenv.new_run_dir makes mkdtemp(prefix='srp_') spray dirs. The
    STABLE_ROOT ('srp_smoke11_stable_*', also under %TEMP%) starts with
    'srp_' too but is NOT spray — it is the keep-until-replaced artifact
    policy — and it predates every caller's baseline snapshot, so it is
    never counted as a leak; the historical 'srp_spectra' name is
    excluded for the same reason (pre-06-12 default layout).
    """
    return set(n for n in os.listdir(base_dir)
               if n.startswith('srp_') and n != 'srp_spectra')


# --- Steps -----------------------------------------------------------------

def s_qprocess_available():
    QtCore, app = _qtcore()
    assert hasattr(QtCore, 'QProcess'), 'QtCore.QProcess missing'
    assert hasattr(QtCore, 'QEventLoop'), 'QtCore.QEventLoop missing'
    assert app is QtCore.QCoreApplication.instance(), 'app not installed'
    print('PROBE QT: %s, has QProcess=True, app=%s'
          % (QtCore.QT_VERSION_STR, type(app).__name__), flush=True)


def s_runner_constructs():
    global PLUGIN, RUNNER, XTBRUN, ANCHOR, CTRL
    import pmg_tk.startup
    if ROOT not in pmg_tk.startup.__path__:
        pmg_tk.startup.__path__.append(ROOT)
    PLUGIN = importlib.import_module('pmg_tk.startup.serpentrum')
    assert 'pmg_tk.startup.serpentrum' in sys.modules
    RUNNER = importlib.import_module('pmg_tk.startup.serpentrum.xtb_runner')
    XTBRUN = importlib.import_module('pmg_tk.startup.serpentrum.xtb_run')
    ANCHOR = PLUGIN._anchor()
    assert pmg_tk.startup._serpentrum is ANCHOR, \
        'controller anchor is NOT the pmg_tk.startup._serpentrum anchor'
    CTRL = RUNNER.XtbRunController(ANCHOR)
    assert CTRL is not None
    assert CTRL.status() in (None, 'idle', 'ok', 'failed', 'cancelled'), \
        'unexpected initial status %r' % (CTRL.status(),)
    print('PROBE RUNNER module: %s status0: %r'
          % (RUNNER.__name__, CTRL.status()), flush=True)


def s_resolve_xtb():
    global XTB_EXE
    probes = []
    # 1. explicit env override (smoke/dev seam)
    env_path = os.environ.get('SRP_XTB_PATH')
    probes.append('SRP_XTB_PATH: %s' % (env_path or 'not set'))
    if env_path and os.path.isfile(env_path):
        XTB_EXE = env_path
    # 2. which() probes (xtb.exe then xtb) via the pure helper
    if XTB_EXE is None:
        xtbenv = importlib.import_module('pmg_tk.startup.serpentrum.xtbenv')
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


def s_arun_success_contract():
    """REAL co2 --ohess success contract + restart-after-completion."""
    from pymol.Qt import QtCore
    text = _fixture_text('co2.xyz')
    base_dir = _base_dir()
    _clean_stable('smoke11_ok')
    _clean_stable('smoke11_afterok')
    flags = {}
    log_lines = []
    CTRL.started.connect(lambda: flags.setdefault('started', True))
    CTRL.log_line.connect(log_lines.append)
    srp_before = _srp_entries(base_dir)
    timer = QtCore.QElapsedTimer()
    got = {}

    def _begin():
        timer.start()
        ok = CTRL.start(text, XTB_EXE, base_dir, 'smoke11_ok')
        got['started_ok'] = ok

    result = _wait_controller(120000, _begin)
    elapsed = timer.elapsed()
    print('PROBE ARUN elapsed_ms: %d status: %s problems: %r'
          % (elapsed, result.get('status'), result.get('problems')),
          flush=True)
    assert got.get('started_ok') is True, \
        'start() did not return True: %r' % (got.get('started_ok'),)
    assert not result.get('timeout'), 'safety timeout hit (120 s)'
    assert flags.get('started'), 'started signal never fired'
    assert len(log_lines) >= 1, 'no log_line streamed during the run'
    assert result.get('status') == 'ok', \
        'run_finished status %r != ok' % (result.get('status'),)
    assert result.get('problems') == [], \
        'problems not empty: %r' % (result.get('problems'),)
    # Anchor record: frozen shape + status + real paths.
    record = getattr(ANCHOR, 'spectra_run', None)
    assert record is not None, 'no spectra_run record on the anchor'
    assert sorted(record.keys()) == sorted(XTBRUN.SPECTRA_RUN_KEYS), \
        'record keys not the frozen SPECTRA_RUN_KEYS: %r' \
        % (sorted(record.keys()),)
    assert record['status'] == 'ok', 'record status %r' % (record['status'],)
    assert record['snake_id'] == 'smoke11_ok'
    for key in ('input_path', 'g98_path', 'vibspectrum_path',
                'xtbopt_path', 'log_path'):
        assert record.get(key), 'record[%s] is %r' % (key, record.get(key))
    # Stable dir contents (assert BEFORE any second start: the
    # keep-until-replaced policy deletes the prior dir on the next run).
    stable = _stable_dir('smoke11_ok')
    present = os.listdir(stable) if os.path.isdir(stable) else []
    for fname in ('snake.xyz', 'xtb.log', 'g98.out', 'vibspectrum',
                  'xtbopt.xyz'):
        assert fname in present, \
            'stable dir missing %r (has %r)' % (fname, present)
    # Spray dir hygiene: no NEW srp_-prefixed entry survives the run.
    leaked = _srp_entries(base_dir) - srp_before
    print('PROBE SPRAY leftover: %r' % (sorted(leaked),), flush=True)
    assert not leaked, \
        'spray dir not deleted at terminal: %r' % (sorted(leaked),)

    # SC2: a SECOND run can start after completion. dimer2 (not co2 —
    # co2 completes in ~89 ms and races any pre-scheduled cancel timer,
    # the smoke-09 deviation-1 fact) keeps the cleanup cancel
    # deterministic: kill at 300 ms lands mid-run.
    dimer_text = _fixture_text('dimer2.xyz')
    got2 = {}

    def _begin2():
        ok = CTRL.start(dimer_text, XTB_EXE, base_dir, 'smoke11_afterok')
        got2['started_ok'] = ok
        if ok:
            QtCore.QTimer.singleShot(300, CTRL.cancel)

    result2 = _wait_controller(60000, _begin2)
    print('PROBE RESTART started: %r cleanup_status: %s'
          % (got2.get('started_ok'), result2.get('status')), flush=True)
    assert got2.get('started_ok') is True, \
        'guard did not release after a completed run (start -> %r)' \
        % (got2.get('started_ok'),)
    assert not result2.get('timeout'), 'safety timeout hit (60 s)'
    assert result2.get('status') == 'cancelled', \
        'cleanup run ended %r, expected cancelled' \
        % (result2.get('status'),)


def s_responsiveness_tick():
    """A QTimer fires DURING a dimer2 run while status() == 'running'.

    dimer2 geometry (~0.8-2.8 s) gives the 300 ms tick an order of
    magnitude of margin (co2's 89 ms wall cannot host this assertion —
    smoke-09 deviation-1). Cancel at 600 ms cleans the run up.
    """
    from pymol.Qt import QtCore
    text = _fixture_text('dimer2.xyz')
    base_dir = _base_dir()
    _clean_stable('smoke11_tick')
    tick = {}
    timer = QtCore.QElapsedTimer()

    def _tick():
        tick['fired'] = True
        tick['status'] = CTRL.status()
        tick['elapsed'] = timer.elapsed()

    got = {}

    def _begin():
        timer.start()
        got['started_ok'] = CTRL.start(text, XTB_EXE, base_dir,
                                       'smoke11_tick')
        QtCore.QTimer.singleShot(300, _tick)
        QtCore.QTimer.singleShot(600, CTRL.cancel)

    result = _wait_controller(60000, _begin)
    elapsed = timer.elapsed()
    print('PROBE TICK elapsed_ms: %d tick_at_ms: %s status_at_tick: %s '
          'final: %s'
          % (elapsed, tick.get('elapsed'), tick.get('status'),
             result.get('status')), flush=True)
    assert got.get('started_ok') is True
    assert not result.get('timeout'), 'safety timeout hit (60 s)'
    assert tick.get('fired'), 'responsiveness tick never fired'
    assert tick['status'] == 'running', \
        'tick fired while NOT running (status=%r)' % (tick['status'],)
    assert result.get('status') == 'cancelled', \
        'cleanup cancel ended %r, expected cancelled' \
        % (result.get('status'),)


def s_cancel_path():
    """dimer2 killed at ~300 ms -> 'cancelled', no fake success (SC2)."""
    from pymol.Qt import QtCore
    text = _fixture_text('dimer2.xyz')
    base_dir = _base_dir()
    _clean_stable('smoke11_cancel')
    timer = QtCore.QElapsedTimer()
    got = {}

    def _begin():
        timer.start()
        got['started_ok'] = CTRL.start(text, XTB_EXE, base_dir,
                                       'smoke11_cancel')
        QtCore.QTimer.singleShot(300, CTRL.cancel)

    result = _wait_controller(60000, _begin)
    elapsed = timer.elapsed()
    print('PROBE CANCEL elapsed_ms: %d status: %s'
          % (elapsed, result.get('status')), flush=True)
    assert got.get('started_ok') is True
    assert not result.get('timeout'), 'safety timeout hit (60 s)'
    assert result.get('status') == 'cancelled', \
        'run_finished status %r != cancelled (fake success?)' \
        % (result.get('status'),)
    record = getattr(ANCHOR, 'spectra_run', None)
    assert record is not None and record['status'] == 'cancelled', \
        'anchor record status %r' % (record and record.get('status'),)
    assert record['snake_id'] == 'smoke11_cancel'
    # No fake success: the files leg fails on kill (probe-B fact) — the
    # stable dir holds snake.xyz + xtb.log but NOT the spectra artifacts.
    # (Assert BEFORE any follow-up start: keep-until-replaced deletes it.)
    stable = _stable_dir('smoke11_cancel')
    present = os.listdir(stable) if os.path.isdir(stable) else []
    for fname in ('snake.xyz', 'xtb.log'):
        assert fname in present, \
            'cancel stable dir missing %r (has %r)' % (fname, present)
    for fname in ('g98.out', 'vibspectrum', 'xtbopt.xyz'):
        assert fname not in present, \
            'cancelled run left %r in the stable dir — masquerade' \
            % (fname,)
    assert record['g98_path'] is None, 'record g98_path %r' \
        % (record['g98_path'],)
    assert record['vibspectrum_path'] is None

    # SC2: a new run can start after cancel. The follow-up is TINY co2
    # (~89-250 ms) — whether its terminal label is 'ok' (finished before
    # any cancel lands) or 'cancelled' is not the assertion; start()
    # returning True is the guard-release proof.
    co2_text = _fixture_text('co2.xyz')
    _clean_stable('smoke11_aftercancel')
    got2 = {}

    def _begin2():
        got2['started_ok'] = CTRL.start(co2_text, XTB_EXE, base_dir,
                                        'smoke11_aftercancel')

    result2 = _wait_controller(120000, _begin2)
    print('PROBE AFTER_CANCEL started: %r final: %s'
          % (got2.get('started_ok'), result2.get('status')), flush=True)
    assert got2.get('started_ok') is True, \
        'guard did not release after cancel (start -> %r)' \
        % (got2.get('started_ok'),)
    assert not result2.get('timeout'), 'safety timeout hit (120 s)'
    assert result2.get('status') in ('ok', 'cancelled'), \
        'follow-up run ended %r' % (result2.get('status'),)


def s_no_double_run_guard():
    """start() while 'running' is refused: False + guard log line."""
    from pymol.Qt import QtCore
    dimer_text = _fixture_text('dimer2.xyz')
    co2_text = _fixture_text('co2.xyz')
    base_dir = _base_dir()
    _clean_stable('smoke11_guard')
    log_lines = []
    CTRL.log_line.connect(log_lines.append)
    before = len(log_lines)
    got = {}

    def _begin():
        got['first'] = CTRL.start(dimer_text, XTB_EXE, base_dir,
                                  'smoke11_guard')
        got['second'] = CTRL.start(co2_text, XTB_EXE, base_dir,
                                   'smoke11_double')
        # leave the state clean: kill the active run shortly after.
        QtCore.QTimer.singleShot(300, CTRL.cancel)

    result = _wait_controller(60000, _begin)
    guard_lines = log_lines[before:before + 3]
    print('PROBE GUARD first: %r second: %r guard_log: %r cleanup: %s'
          % (got.get('first'), got.get('second'), guard_lines,
             result.get('status')), flush=True)
    assert got.get('first') is True, 'first start() %r' % (got.get('first'),)
    assert got.get('second') is False, \
        'no-double-run guard failed: second start() -> %r' \
        % (got.get('second'),)
    assert any('already active' in line for line in guard_lines), \
        'guard log line missing in %r' % (guard_lines,)
    assert not result.get('timeout'), 'safety timeout hit (60 s)'
    assert result.get('status') == 'cancelled', \
        'cleanup cancel ended %r, expected cancelled' \
        % (result.get('status'),)


def s_start_failure_path():
    """Bad exe -> 'failed', never a crash (pitfall 9 surface-never-die).

    ACTUAL 06-05 contract (read the code): errorOccurred(FailedToStart)
    fires SYNCHRONOUSLY inside proc.start(); _on_error runs the full
    terminal discipline and emits run_finished BEFORE start() returns,
    and start() then returns False (status already left 'running'). So
    this step connects run_finished first and asserts the record
    IMMEDIATELY after the call — no event-loop wait (nothing would
    arrive anyway).
    """
    from pymol.Qt import QtCore  # noqa: F401  (kept for parity/imports)
    co2_text = _fixture_text('co2.xyz')
    base_dir = _base_dir()
    record_sig = {}

    def _on_finished(status, problems):
        record_sig['status'] = status
        record_sig['problems'] = list(problems)

    CTRL.run_finished.connect(_on_finished)
    raised = None
    returned = object()
    try:
        returned = CTRL.start(co2_text, XTB_EXE + '_missing', base_dir,
                              'smoke11_badexe')
    except Exception as exc:  # the whole point: it must NOT raise
        raised = exc
    print('PROBE BADEXE returned: %r raised: %r signal: %r ctrl.status: %r'
          % (returned, raised, record_sig, CTRL.status()), flush=True)
    assert raised is None, 'start() raised on bad exe: %r' % (raised,)
    assert returned is False, \
        'start() with bad exe returned %r (expected False — the 06-05 ' \
        'synchronous-FailedToStart re-check)' % (returned,)
    assert record_sig.get('status') == 'failed', \
        'run_finished status %r != failed' % (record_sig.get('status'),)
    problems = record_sig.get('problems') or []
    assert any('could not be started' in p for p in problems), \
        'no start-failure problem string: %r' % (problems,)
    record = getattr(ANCHOR, 'spectra_run', None)
    assert record is not None and record['status'] == 'failed', \
        'anchor record %r' % (record,)
    assert record['snake_id'] == 'smoke11_badexe'
    # State is TERMINAL afterwards (and the guard released).
    assert CTRL.status() in XTBRUN.TERMINAL_STATES, \
        'ctrl.status() %r not terminal' % (CTRL.status(),)
    assert XTBRUN.can_start(CTRL.status()), \
        'guard did not release after a failed start'


for _name, _fn in [
    ('qprocess_available', s_qprocess_available),
    ('runner_constructs', s_runner_constructs),
    ('resolve_xtb', s_resolve_xtb),
    ('arun_success_contract', s_arun_success_contract),
    ('responsiveness_tick', s_responsiveness_tick),
    ('cancel_path', s_cancel_path),
    ('no_double_run_guard', s_no_double_run_guard),
    ('start_failure_path', s_start_failure_path),
]:
    check(_name, _fn)

if FAILURES:
    print('SMOKE-FAIL %s' % ','.join(FAILURES), flush=True)
else:
    print('SMOKE-OK XTB-RUNNER', flush=True)
