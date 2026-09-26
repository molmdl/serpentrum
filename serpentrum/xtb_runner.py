"""serpentrum.xtb_runner — the xtb run's GUI shell (Phase 6, plan 06-05).

THIN SHELL RULE: every RULE lives in serpentrum/xtb_run.py (state machine,
status mapping, env-knob merge, record shape) and serpentrum/xtbenv.py
(argv, run dir, 3-leg success contract) — this module only wires Qt.
It MUST NOT re-implement a decision already made there.

GUI purity class (tools/check_purity.py GUI_MODULES, inert-first entry
landed in Task 1 of plan 06-05): the ONLY pymol-family import is
``pymol.Qt``; NEVER pymol.cmd (the viewer is not the runner's concern —
06-RESEARCH-runner.md Q2), never PyQt5/numpy, never a blocking exec-call
(modeless rule).

Qt mechanics (all live-pinned by smoke 09, 06-03-SUMMARY.md):

- Connect-before-start is BINDING: errorOccurred(FailedToStart) fires
  SYNCHRONOUSLY inside proc.start() — every signal is wired before
  start() or the error path dies opaquely.
- finished slot signature is (int, QProcess.ExitStatus) — exit status is
  matched against the QtCore.QProcess.* enums, never magic ints (the
  verdict itself consumes only the integer exit code; a killed run
  already fails the contract on exit!=0 and missing files).
- stderr arrives CRLF and is fed VERBATIM to xtbenv.evaluate_run
  (never pre-filtered — the 'abnormal termination' substring trap).
- No polling: signals only — no blocking wait calls on the child and no
  event-pump hacks (PITFALLS.md:64 names the banned APIs).
- One application: QCoreApplication.instance() or create only if None
  (EQ-app-1) — in the real GUI a QApplication already exists.
- Narrow ownership: no module-level state; the controller instance
  lives on pmg_tk.startup._serpentrum, placed there by the CALLER
  (plan 06-09), so reload/double-import can never duplicate it.

python3.6 syntax throughout (%-formatting, no f-strings/walrus).
"""

import os
import shutil
import tempfile

from pymol.Qt import QtCore

from . import xtb_run
from . import xtbenv

# Bound on the in-memory log tail kept for the record's xtb.log file.
_LOG_TAIL = 500


def _ensure_app():
    """Return the running Q(Core)Application, creating one only if None.

    EQ-app-1 / 06-RESEARCH-runner open question 6: a headless -cq process
    starts with NO application, the real PyMOL GUI already has a
    QApplication — create only when None, never a second app.
    """
    app = QtCore.QCoreApplication.instance()
    if app is None:
        app = QtCore.QCoreApplication([])
    return app


class XtbRunController(QtCore.QObject):
    """Single-owner async QProcess xtb runner (the Qt shell of xtb_run).

    Lifecycle: guarded start() -> xtb runs with cwd = a fresh
    xtbenv.new_run_dir spray dir -> readyRead streams log lines ->
    ONE terminal branch (_on_finished, or _on_error when the process
    never started) resolves status via xtb_run.resolve_status over the
    3-leg verdict, copies artifacts into the stable srp_spectra
    directory, DELETES the spray dir, writes _serpentrum.spectra_run,
    clears the cancel flag, and emits run_finished — on EVERY terminal
    branch (bioCHEMeleon discipline). cancel() = proc.kill() only
    (06-RESEARCH-runner Q4); the killed run fails the contract on its
    own and the controller's flag decides the 'cancelled' label.
    """

    # Phase 7 connects: started() on launch, log_line(str) per decoded
    # line (stdout + stderr), run_finished(status, problems) once.
    started = QtCore.Signal()
    log_line = QtCore.Signal(str)
    run_finished = QtCore.Signal(str, list)

    def __init__(self, anchor_state=None):
        super(XtbRunController, self).__init__()
        # The live-state anchor (pmg_tk.startup._serpentrum) — owned by
        # the caller (plan 06-09); this module touches NO module globals.
        self._anchor = anchor_state
        self._status = None            # xtb_run state; None = never ran
        self._cancel_requested = False
        self._log_lines = []           # bounded tail (_LOG_TAIL)
        self._stderr_text = ''         # verbatim stderr for the verdict
        self._input_text = None        # snake.xyz text, for copy-out
        self._run_dir = None           # the spray dir (dies at terminal)
        self._snake_id = None
        self._proc = None              # lazy in start() — an unused
                                       # controller costs nothing

    def status(self):
        """Read-only accessor for the UI: current xtb_run state."""
        return self._status

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self, xyz_text, exe_path, base_dir, snake_id, knobs=None,
              extra_args=None):
        """Launch an xtb --ohess run; return True iff launched.

        Guarded no-op (returns False + log/record exactly like a
        failure, so state never sticks at 'running') unless
        xtb_run.can_start passes and the preflight guards hold. Writes
        snake.xyz INTO a fresh xtbenv.new_run_dir spray dir, launches
        with cwd=that dir and bare-relative argv via xtbenv.build_argv,
        injects only xtb_run-approved env knobs, and never blocks waiting
        on the child (signals only). extra_args None ->
        (xtbenv.XTB_OHESS,) + xtb_run.DEFAULT_THREAD_ARG (the SC5 '-P 4'
        calibration cap, 06-CALIBRATION.md; an explicit caller-supplied
        extra_args still wins); knobs None -> xtb_run.DEFAULT_RUN_KNOBS.
        """
        _ensure_app()
        if not xtb_run.can_start(self._status):
            self.log_line.emit('an xtb run is already active - cancel or '
                               'wait for it to finish')
            return False  # no-double-run guard (PITFALLS.md:66)
        if not xyz_text:
            self._fail_before_start(
                ['run input is empty - complete a game first'], snake_id)
            return False
        if not exe_path:
            self._fail_before_start(
                ['xtb not found - set the xtb path on the Setup tab'],
                snake_id)
            return False
        args = (extra_args if extra_args is not None
                else (xtbenv.XTB_OHESS,) + xtb_run.DEFAULT_THREAD_ARG)
        try:
            argv = xtbenv.build_argv(exe_path, 'snake.xyz',
                                     extra_args=args)
        except ValueError as exc:
            self._fail_before_start([str(exc)], snake_id)
            return False

        self._run_dir = xtbenv.new_run_dir(base_dir)
        with open(os.path.join(self._run_dir, 'snake.xyz'), 'w',
                  encoding='utf-8') as fh:
            fh.write(xyz_text)

        self._drop_prior_stable_dir()

        merged = xtb_run.build_env({}, knobs if knobs is not None
                                   else xtb_run.DEFAULT_RUN_KNOBS)
        env = QtCore.QProcessEnvironment.systemEnvironment()
        for key, value in merged.items():
            env.insert(key, value)

        proc = QtCore.QProcess(self)
        proc.setWorkingDirectory(self._run_dir)
        proc.setProcessEnvironment(env)
        # connect-before-start (BINDING, smoke 09 live pin):
        # errorOccurred(FailedToStart) fires SYNCHRONOUSLY inside
        # proc.start() — a post-start connect would miss it entirely.
        proc.started.connect(self._on_started)
        proc.finished.connect(self._on_finished)
        proc.readyReadStandardOutput.connect(self._on_stdout)
        proc.readyReadStandardError.connect(self._on_stderr)
        error_signal = getattr(proc, 'errorOccurred', proc.error)
        error_signal.connect(self._on_error)

        self._input_text = xyz_text
        self._snake_id = snake_id
        self._stderr_text = ''
        self._log_lines = []
        self._cancel_requested = False
        self._status = xtb_run.RUNNING
        self._proc = proc
        proc.start(argv[0], argv[1:])
        if self._status != xtb_run.RUNNING:
            # _on_error already ran the terminal discipline
            # synchronously (FailedToStart): report no-launch.
            return False
        self.started.emit()
        return True

    def cancel(self):
        """Request cancellation via proc.kill() (Q4; never terminate())."""
        if self._status == xtb_run.RUNNING and self._proc is not None:
            self._cancel_requested = True
            self._proc.kill()
            self.log_line.emit('cancel requested - killing xtb')
        else:
            self.log_line.emit('no running xtb job to cancel')

    # ------------------------------------------------------------------
    # Keep-until-replaced stable dir policy (EQ-artifact-1)
    # ------------------------------------------------------------------

    def _drop_prior_stable_dir(self):
        """Delete the PREVIOUS run's stable srp_spectra dir, if recorded.

        EQ-artifact-1 keep-until-replaced: the NEW start removes the old
        run's stable dir so the previous spectra record's files never
        masquerade as the new run's. Prefix-guarded: NEVER rmtree an
        arbitrary path — only a dir under <temp>/srp_spectra.
        """
        if self._anchor is None:
            return
        prior = getattr(self._anchor, 'spectra_run', None)
        if not prior:
            return
        old_input = prior.get('input_path')
        if not old_input:
            return
        stable_root = os.path.join(tempfile.gettempdir(), 'srp_spectra')
        old_dir = os.path.normpath(os.path.abspath(
            os.path.dirname(old_input)))
        root_norm = os.path.normpath(os.path.abspath(stable_root))
        if old_dir.startswith(root_norm + os.sep) and \
                os.path.isdir(old_dir):
            shutil.rmtree(old_dir, ignore_errors=True)

    # ------------------------------------------------------------------
    # Signal handlers
    # ------------------------------------------------------------------

    def _on_started(self):
        self.log_line.emit('xtb started')

    def _on_stdout(self):
        if self._proc is None:
            return
        chunk = bytes(self._proc.readAllStandardOutput()).decode(
            'utf-8', 'replace')
        self._ingest_chunk(chunk)

    def _on_stderr(self):
        if self._proc is None:
            return
        chunk = bytes(self._proc.readAllStandardError()).decode(
            'utf-8', 'replace')
        # VERBATIM accumulation (CRLF intact) — xtbenv.evaluate_run is
        # CRLF-tolerant; NEVER pre-filter (the 'abnormal termination'
        # substring trap).
        self._stderr_text += chunk
        self._ingest_chunk(chunk)

    def _ingest_chunk(self, chunk):
        for line in chunk.splitlines():
            if line.strip():
                self._log_lines.append(line)
                self.log_line.emit(line)
        del self._log_lines[:-_LOG_TAIL]  # bounded tail

    def _on_finished(self, code, exit_status):
        """THE terminal branch: verdict -> copy-out -> record -> reset.

        Every branch flows through (a)-(g); NO early returns.
        """
        # (a) 3-leg contract verdict over the spray dir listing.
        present = []
        if self._run_dir is not None and os.path.isdir(self._run_dir):
            present = os.listdir(self._run_dir)
        verdict = xtbenv.evaluate_run(code, self._stderr_text,
                                      xtbenv.EXPECTED_FILES, present)
        # (b) cancel flag wins over the verdict (xtb_run.resolve_status).
        status_text = xtb_run.resolve_status(self._cancel_requested,
                                             verdict.ok)
        # (c) copy-out into the stable srp_spectra/<snake_id> dir.
        stable = os.path.join(tempfile.gettempdir(), 'srp_spectra',
                              self._snake_id or 'unknown')
        os.makedirs(stable, exist_ok=True)
        copied = {}
        for fname in ('g98.out', 'vibspectrum', 'xtbopt.xyz'):
            if fname in present:
                target = os.path.join(stable, fname)
                shutil.copy2(os.path.join(self._run_dir, fname), target)
                copied[fname] = target
            else:
                copied[fname] = None
        input_stable = os.path.join(stable, 'snake.xyz')
        with open(input_stable, 'w', encoding='utf-8') as fh:
            fh.write(self._input_text or '')
        log_stable = os.path.join(stable, 'xtb.log')
        with open(log_stable, 'w', encoding='utf-8') as fh:
            fh.write('\n'.join(self._log_lines))
        # (d) frozen-shape record onto the anchor.
        record = xtb_run.new_spectra_run(self._snake_id)
        record['status'] = status_text
        record['problems'] = list(verdict.problems)
        record['input_path'] = input_stable
        record['g98_path'] = copied['g98.out']
        record['vibspectrum_path'] = copied['vibspectrum']
        record['xtbopt_path'] = copied['xtbopt.xyz']
        record['log_path'] = log_stable
        if self._anchor is not None:
            self._anchor.spectra_run = record
        # (e) the spray dir dies ALWAYS (pitfall 10: only after finished
        # — xtb holds files open on cancel and a pre-finished rmtree is a
        # WinError 32 race).
        if self._run_dir is not None:
            shutil.rmtree(self._run_dir, ignore_errors=True)
        # (f) terminal reset — every flag cleared on the terminal branch.
        self._status = {xtb_run.DONE: xtb_run.DONE,
                        xtb_run.FAILED: xtb_run.FAILED,
                        xtb_run.CANCELLED: xtb_run.CANCELLED}[status_text]
        self._cancel_requested = False
        self._proc = None
        self._run_dir = None
        # (g) one terminal signal.
        self.run_finished.emit(status_text, list(verdict.problems))

    def _on_error(self, *args):
        """FailedToStart path: same terminal discipline as a failure.

        errorOccurred fires SYNCHRONOUSLY inside start() and finished()
        will NOT follow. Guards: no-op when the run already finished
        (the finished slot owns that branch) or when the process is
        still in flight (readyRead/finished own those events).
        """
        if self._status != xtb_run.RUNNING or self._proc is None:
            return
        if self._proc.state() != QtCore.QProcess.NotRunning:
            return
        description = self._proc.errorString()
        if self._run_dir is not None:
            shutil.rmtree(self._run_dir, ignore_errors=True)
        self._proc = None
        self._run_dir = None
        self._cancel_requested = False
        self._fail_before_start(
            ['xtb could not be started: %s' % (description,)],
            self._snake_id)

    def _fail_before_start(self, problems, snake_id):
        """Record a failure when no process ever ran (or started).

        Uses the SAME record path as a failure verdict so state never
        sticks at 'running': frozen record onto the anchor, FAILED
        status, per-problem log lines, one run_finished signal.
        """
        record = xtb_run.new_spectra_run(snake_id or 'unknown')
        record['status'] = xtb_run.FAILED
        record['problems'] = list(problems)
        if self._anchor is not None:
            self._anchor.spectra_run = record
        self._status = xtb_run.FAILED
        for problem in problems:
            self.log_line.emit(problem)
        self.run_finished.emit(xtb_run.FAILED, list(problems))
