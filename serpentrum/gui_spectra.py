"""serpentrum.gui_spectra — the Spectra tab's live control surface (Phase 7,
plan 07-07; SPECTRA-01 tab surface, SPECTRA-04 streaming log).

SpectraTab(anchor_state, parent) replaces the 06-09 placeholder page: a
word-wrapped status label, a bounded streaming log panel, and a contextual
run/cancel button. The DIALOG wires the surfaces to the anchored
XtbRunController's signals (started / log_line / run_finished) and owns
all cross-tab orchestration (the launch pipeline, the Get-Spectra
re-enable, the game info-box feed) — this tab NEVER reaches up to its
parent widget (no parent-widget lookups anywhere) and NEVER launches a
run itself: Run-again is the emit-only ``run_again_requested`` signal,
which the dialog connects to the full launch pipeline (06-09's pinned
Run-again semantics; model-A, locked decision 9). Cancel calls the
anchor-owned controller directly.

07-RESEARCH-spectra-seam.md Q3: the log panel is a QPlainTextEdit,
read-only, with setMaximumBlockCount(500) — the bound matches the
controller's 500-line tail (xtb_runner._LOG_TAIL) so memory stays flat
while streaming, and appendPlainText self-trims the oldest blocks. A
late/reloading tab calls replay_log(controller.log_tail()) BEFORE the
dialog connects log_line, so lines emitted before the connect are never
lost (the reload early-line hole, closed by 07-04's accessor).

Layout indices are PINNED for the later plans (07-RESEARCH Q5/Q6; the
contract lives in the 07-07 plan): today
    [0] = status label, [1] = log panel (stretch 2), [2] = button row.
07-08 builds the plot panel in __init__ between log and buttons (status /
log / PANEL / buttons). 07-09 inserts the table at index 2 (stretch 2),
yielding the final order status[0] / log[1] / table[2] / plot[3] /
buttons[4]. Insert at the pinned index ONLY — never append.

GUI purity class (tools/check_purity.py GUI_MODULES — the inert-first
entry landed in plan 07-05): ``pymol.Qt`` ONLY (Qt reaches this code
exclusively through pymol.Qt — direct PyQt5 is banned project-wide);
relative imports of the pure sibling modules (``spectra_ui``) are exempt
(check_purity.py:95-98). NO pymol.cmd (the viewer is not this tab's
concern), no blocking modal-run call (modeless rule), NO module-level
state. python3.6 syntax throughout (%-formatting, no f-strings).
"""

from pymol.Qt import QtWidgets, QtCore

# Pure sibling: the frozen verdict-line vocabulary (never re-grepped from
# the log — the 'abnormal termination' substring trap stays dead).
from . import spectra_ui


class SpectraTab(QtWidgets.QWidget):
    """The Spectra tab's status / streaming-log / run-control surfaces.

    Built by PluginDialog as page 2 (plan 07-07; the 06-09 placeholder
    page is gone). Owns: the status label, the bounded log panel, the
    contextual run button and its label logic, and the runner-slot
    display updates (started / log_line / run_finished). The dialog
    owns: the launch pipeline, the connect-once guard, the Get-Spectra
    re-enable and the game info-box feed (cross-tab orchestration the
    tab must not reach up for — model-A).

    Layout (PINNED — see the module docstring's insert contract):
    [0] status label, [1] log panel (stretch 2), [2] button row
    (right-aligned). 07-08 inserts the plot panel, 07-09 the table, each
    at its pinned index.
    """

    # Model-A return path (the gui_game.spectra_requested template):
    # emit-only; PluginDialog connects it to its own launch slot so a
    # Run-again click re-enters the FULL pipeline (06-09 semantics —
    # NEVER _launch_spectra_run with stale values).
    run_again_requested = QtCore.Signal()

    def __init__(self, anchor_state=None, parent=None):
        super(SpectraTab, self).__init__(parent)
        self._anchor = anchor_state
        self._build_widgets()
        self._build_layout()

    def _build_widgets(self):
        """Create the three surfaces (PINNED order per the contract)."""
        self.status_label = QtWidgets.QLabel(
            'Spectra tab - complete a game, then press Get Spectra on '
            'the Game tab. Progress streams here.', self)
        self.status_label.setWordWrap(True)
        # Research Q3 [TRAIN] MEDIUM: QPlainTextEdit + 500-block cap ==
        # the controller's tail — flat memory while streaming; human-
        # verified streaming at the 07-10 checkpoint.
        self.log_panel = QtWidgets.QPlainTextEdit(self)
        self.log_panel.setReadOnly(True)
        self.log_panel.setMaximumBlockCount(500)
        self.run_btn = QtWidgets.QPushButton('no xtb run yet', self)
        self.run_btn.setToolTip('no xtb run yet')
        self.run_btn.setEnabled(False)
        self.run_btn.clicked.connect(self._on_run_button)

    def _build_layout(self):
        """[0] status, [1] log (stretch 2), [2] right-aligned button row.

        INSERT CONTRACT: 07-08 inserts the plot panel at index 2 (this
        plan's button row shifts to 3); 07-09 inserts the table at index
        2 (plot shifts to 3, buttons to 4) -> final order status / log /
        table / plot / buttons.
        """
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.status_label)          # [0]
        layout.addWidget(self.log_panel, 2)          # [1] stretch 2
        btn_row = QtWidgets.QHBoxLayout()            # [2]
        btn_row.addStretch(1)
        btn_row.addWidget(self.run_btn)
        layout.addLayout(btn_row)

    # --- surface writers (called by the dialog via signals/methods) ----

    def append_log_line(self, text):
        """Stream one decoded xtb output line into the log panel.

        The SPECTRA-04 streaming sink: the dialog connects this directly
        to controller.log_line (plain .connect — same-thread Qt; the
        500-block cap self-trims on append).
        """
        self.log_panel.appendPlainText(str(text))

    def set_status_line(self, text):
        """Set the one-line status label (launch/verdict one-liners)."""
        self.status_label.setText(str(text))

    def replay_log(self, lines):
        """Replay a historical log tail (the reload early-line recovery).

        The dialog feeds controller.log_tail() (07-04) through this
        BEFORE connecting log_line, so lines emitted before the connect
        are never lost.
        """
        for line in lines:
            self.append_log_line(line)

    def on_runner_started(self):
        """Runner launch acknowledged: status line + arm the cancel leg.

        The 06-09 pinned started text, verbatim.
        """
        self.set_status_line(
            'xtb running... (async - the dialog stays responsive)')
        self.run_btn.setText('Cancel xtb run')
        self.run_btn.setToolTip('cancel the running xtb job')
        self.run_btn.setEnabled(True)

    def on_run_finished(self, status, problems):
        """Terminal branch (ok/failed/cancelled): verdict + re-arm.

        Verdict lines come from spectra_ui.run_status_lines over the
        anchored spectra_run record (falling back to the signal payload
        when the anchor carries none) — the FROZEN vocabulary, never
        re-grepped from the log text. The first line lands on the status
        label and every line lands in the log panel, so the verdict is
        visible in BOTH surfaces. 07-08/07-09 extend this slot with
        plot/table population from the same record.
        """
        record = getattr(self._anchor, 'spectra_run', None) or {
            'status': status, 'problems': problems}
        lines = spectra_ui.run_status_lines(record)
        if lines:
            self.set_status_line(lines[0])
        for line in lines:
            self.append_log_line(line)
        self.run_btn.setText('Run again')
        self.run_btn.setToolTip(
            'launch another xtb run on the completed snake')
        self.run_btn.setEnabled(True)

    def reflect_run_state(self):
        """Render the anchored runner/record state at construction/reload.

        Called by the dialog AFTER _connect_runner: a live run draws the
        running surface; a terminal record that predates this dialog
        renders its verdict immediately; otherwise the idle hint and the
        disabled button stand. All anchor reads are getattr-guarded — a
        stripped-down (None) anchor can never crash the tab.
        """
        runner = getattr(self._anchor, 'spectra_runner', None)
        if runner is not None and runner.status() == 'running':
            self.on_runner_started()
            return
        record = getattr(self._anchor, 'spectra_run', None)
        if (record and record.get('status')
                in ('ok', 'failed', 'cancelled')):
            self.on_run_finished(record.get('status'),
                                 record.get('problems') or [])

    # --- the contextual button -----------------------------------------

    def _on_run_button(self):
        """Cancel while running; otherwise request the full relaunch.

        Cancel leg: the anchored controller reports a live run ->
        controller.cancel() directly (the controller is anchor-owned;
        cancel emits its own log line, which the dialog's log_line
        connection delivers here). Run-again leg: EMIT
        run_again_requested — the dialog re-enters the FULL launch
        pipeline (re-read last_run, re-check counts, re-run the guard,
        re-resolve the binary, disarm Get Spectra — 06-09's pinned
        Run-again semantics). This tab NEVER launches.
        """
        runner = getattr(self._anchor, 'spectra_runner', None)
        if runner is not None and runner.status() == 'running':
            runner.cancel()
            return
        self.run_again_requested.emit()
