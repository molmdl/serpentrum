"""serpentrum.gui_spectra — the Spectra tab's live control surface (Phase 7,
plans 07-07/07-08; SPECTRA-01 tab surface, SPECTRA-03 on-screen plot,
SPECTRA-04 streaming log).

SpectraTab(anchor_state, parent) replaces the 06-09 placeholder page: a
word-wrapped status label, a bounded streaming log panel, the embedded
SpectraPlotPanel (07-05/07-06, human-approved look — embedded AS-IS),
and a contextual run/cancel button. The DIALOG wires the surfaces to the
anchored XtbRunController's signals (started / log_line / run_finished)
and owns all cross-tab orchestration (the launch pipeline, the
Get-Spectra re-enable, the game info-box feed) — this tab NEVER reaches
up to its parent widget (no parent-widget lookups anywhere) and NEVER
launches a run itself: Run-again is the emit-only
``run_again_requested`` signal, which the dialog connects to the full
launch pipeline (06-09's pinned Run-again semantics; model-A, locked
decision 9). Cancel calls the anchor-owned controller directly.

07-08 plot feed (SPECTRA-03 on-screen half): on run_finished (and on
construction when a terminal record already exists, via
reflect_run_state) the tab parses the frozen record's g98 output
(vibspectrum fallback with an explicit vectors-unavailable note), reads
broadening_fwhm LIVE from the anchored setup (setup_logic.DEFAULTS
fallback — never re-pinned), builds the Scene via plot_logic.build_scene
and hands it to the panel. The panel stays data-in (Scenes only, no
runner coupling); its own adjustments (size, unit, color, direction,
y-invert, labels, Save Plot) keep working untouched, and Save outcomes
arrive via status_cb -> set_status_line. Degenerate records
(failed/cancelled, missing/corrupt files) never fabricate: the plot
stays empty and the status carries the verdict/problems or a clear
'spectrum could not be read' line (SpectraParseError/OSError caught —
Phase-6 SC3). One Spectrum per record is kept on ``self._spectrum`` —
the SINGLE parse 07-09's table/vectors reuse (index desync structurally
impossible, 07-RESEARCH-spectra-seam.md Q4d).

07-RESEARCH-spectra-seam.md Q3: the log panel is a QPlainTextEdit,
read-only, with setMaximumBlockCount(500) — the bound matches the
controller's 500-line tail (xtb_runner._LOG_TAIL) so memory stays flat
while streaming, and appendPlainText self-trims the oldest blocks. A
late/reloading tab calls replay_log(controller.log_tail()) BEFORE the
dialog connects log_line, so lines emitted before the connect are never
lost (the reload early-line hole, closed by 07-04's accessor).

Layout indices are PINNED for the later plans (07-RESEARCH Q5/Q6; the
contract lives in the 07-07 plan): today (post-07-08)
    [0] = status label, [1] = log panel (stretch 2),
    [2] = plot panel (stretch 3), [3] = button row.
07-09 inserts the table at index 2 (stretch 2), yielding the final
order status[0] / log[1] / table[2] / plot[3] / buttons[4]. Insert at
the pinned index ONLY — never append.

GUI purity class (tools/check_purity.py GUI_MODULES — the inert-first
entry landed in plan 07-05): ``pymol.Qt`` ONLY (Qt reaches this code
exclusively through pymol.Qt — direct PyQt5 is banned project-wide);
relative imports of the pure sibling modules (``spectra_ui``) are exempt
(check_purity.py:95-98). NO pymol.cmd (the viewer is not this tab's
concern), no blocking modal-run call (modeless rule), NO module-level
state. python3.6 syntax throughout (%-formatting, no f-strings).
"""

import os

from pymol.Qt import QtWidgets, QtCore

# Pure siblings: the frozen verdict-line vocabulary (never re-grepped
# from the log — the 'abnormal termination' substring trap stays dead),
# the parse/Scene/live-fwhm seams (07-08), and the frozen status
# constants (06-02 — imported, never re-pinned).
from . import plot_logic, setup_logic, spectra, spectra_ui, xtb_run
from .gui_plot import SpectraPlotPanel


class SpectraTab(QtWidgets.QWidget):
    """The Spectra tab's status / streaming-log / run-control surfaces.

    Built by PluginDialog as page 2 (plan 07-07; the 06-09 placeholder
    page is gone). Owns: the status label, the bounded log panel, the
    embedded SpectraPlotPanel and its record->Scene feed (07-08 —
    SPECTRA-03 on-screen plot feed complete), the contextual run button
    and its label logic, and the runner-slot display updates (started /
    log_line / run_finished). The dialog owns: the launch pipeline, the
    connect-once guard, the Get-Spectra re-enable and the game info-box
    feed (cross-tab orchestration the tab must not reach up for —
    model-A). Next: 07-09's table + mode vectors, reusing the
    ``self._spectrum`` single-source parse.

    Layout (PINNED — see the module docstring's insert contract):
    [0] status label, [1] log panel (stretch 2), [2] plot panel
    (stretch 3), [3] button row (right-aligned). 07-09 inserts the
    table at index 2.
    """

    # Model-A return path (the gui_game.spectra_requested template):
    # emit-only; PluginDialog connects it to its own launch slot so a
    # Run-again click re-enters the FULL pipeline (06-09 semantics —
    # NEVER _launch_spectra_run with stale values).
    run_again_requested = QtCore.Signal()

    def __init__(self, anchor_state=None, parent=None):
        super(SpectraTab, self).__init__(parent)
        self._anchor = anchor_state
        # The single-source parse of the current record (07-08; 07-09's
        # table/vectors consume it) plus the vibspectrum-fallback note.
        self._spectrum = None
        self._spectrum_note = None
        self._build_widgets()
        self._build_layout()

    def _build_widgets(self):
        """Create the four surfaces (PINNED order per the contract)."""
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
        # 07-05/07-06 human-approved panel, embedded AS-IS (approved
        # look = its defaults). Data-in only: the tab feeds Scenes via
        # set_scene; the panel's own adjustments (unit/color/direction/
        # y-invert/size/Save) stay local; Save outcomes arrive through
        # status_cb -> the tab's status line.
        self.plot_panel = SpectraPlotPanel(
            self, status_cb=self.set_status_line)
        self.run_btn = QtWidgets.QPushButton('no xtb run yet', self)
        self.run_btn.setToolTip('no xtb run yet')
        self.run_btn.setEnabled(False)
        self.run_btn.clicked.connect(self._on_run_button)

    def _build_layout(self):
        """[0] status, [1] log (stretch 2), [2] plot panel (stretch 3),
        [3] right-aligned button row.

        INSERT CONTRACT: 07-09 inserts the table at index 2 (stretch 2)
        -> plot shifts to 3, buttons to 4 -> final order status / log /
        table / plot / buttons. Insert at the pinned index ONLY — never
        append.
        """
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.status_label)          # [0]
        layout.addWidget(self.log_panel, 2)          # [1] stretch 2
        layout.addWidget(self.plot_panel, 3)         # [2] stretch 3
        btn_row = QtWidgets.QHBoxLayout()            # [3]
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
        visible in BOTH surfaces. 07-08 extends this slot with plot
        population from the same record (07-09 adds the table).
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
        # 07-08: the plot feed runs off the SAME record as the verdict.
        self._refresh_from_record(record)

    def reflect_run_state(self):
        """Render the anchored runner/record state at construction/reload.

        Called by the dialog AFTER _connect_runner: a live run draws the
        running surface; a terminal record that predates this dialog
        renders its verdict immediately; otherwise the idle hint and the
        disabled button stand. All anchor reads are getattr-guarded — a
        stripped-down (None) anchor can never crash the tab. The plot
        repopulates here too (07-08): the terminal branch flows through
        on_run_finished, whose _refresh_from_record call parses the
        anchored record — a plugin reload / dialog reopen after a
        completed run never leaves a stale empty panel.
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

    # --- the 07-08 record->Scene plot feed ----------------------------

    def _refresh_from_record(self, record):
        """Point the plot feed at a terminal record (07-08).

        'ok' records populate the plot; every degenerate state
        (failed/cancelled/idle, None paths, missing anchor payload)
        resets to the empty-scene hint — never a fabricated curve
        (Phase-6 SC3; 07-RESEARCH-spectra-seam.md Q8-10).
        """
        if record and record.get('status') == xtb_run.DONE:
            self._populate_spectrum(record)
        else:
            self._spectrum = None
            self._spectrum_note = None
            self.plot_panel.set_scene(None)

    def _populate_spectrum(self, record):
        """Parse the record's spectrum artifact and put it on the plot.

        Precedence (07-RESEARCH-spectra-seam.md Q4d): g98 first — it
        alone carries the displacement vectors + atom block; vibspectrum
        fallback when g98_path is None/missing (with an explicit
        vectors-unavailable note). NEVER re-merges g98 vectors with
        vibspectrum rows. The parse runs on the UI thread — legal (the
        787-line fixture parses in ms; the xtb run itself is Phase 6's
        QProcess).

        Degenerate guards — nothing fabricated, nothing crashes:
        missing/unreadable/corrupt files catch SpectraParseError +
        OSError (SpectraParseError is a ValueError subclass, so the
        ValueError leg also covers any parser arithmetic slip), leave
        the plot empty and surface one clear status line. fwhm is read
        LIVE from the anchored setup at populate time (06-11's lesson:
        runtime-read constants; 06-09's atom_budget precedent), falling
        back to setup_logic.DEFAULTS when the anchor setup is
        absent/invalid — never re-pinned, never a crash on a stripped
        anchor.
        """
        # Pure path precedence (g98 first, vibspectrum fallback, 'none'
        # when degenerate) — tested in tests/test_spectra_ui.py; the
        # os.path.isfile existence checks stay here in the tab.
        g98_path, vibs_path, source = spectra_ui.record_spectrum_paths(
            record or {})
        source_note = None
        try:
            if source == 'g98' and os.path.isfile(g98_path):
                spectrum = spectra.parse(g98_path)
            else:
                if not (vibs_path and os.path.isfile(vibs_path)):
                    # Degenerate/failed record: verdict + problems are
                    # already in the status; the plot stays empty.
                    self._spectrum = None
                    self._spectrum_note = None
                    self.plot_panel.set_scene(None)
                    return
                spectrum = spectra.parse(vibs_path)
                spectrum = spectra.Spectrum(
                    spectrum.n_atoms, spectrum.atoms,
                    spectra.real_modes(spectrum))
                source_note = ('showing vibspectrum - no displacement '
                               'vectors available (table only)')
        except (spectra.SpectraParseError, OSError, ValueError) as exc:
            self._spectrum = None
            self._spectrum_note = None
            self.plot_panel.set_scene(None)
            self.set_status_line('spectrum could not be read: %s' % exc)
            return
        setup = getattr(self._anchor, 'setup', None)
        fwhm = setup.get('broadening_fwhm') if setup else None
        if not isinstance(fwhm, (int, float)) or fwhm <= 0:
            fwhm = setup_logic.DEFAULTS['broadening_fwhm']
        scene = plot_logic.build_scene(spectrum.modes, fwhm=float(fwhm))
        self.plot_panel.set_scene(scene)
        # Single-source parse: 07-09's table/vectors reuse THIS object.
        self._spectrum = spectrum
        self._spectrum_note = source_note
        if source_note:
            self.set_status_line(source_note)
        caption = plot_logic.mode_caption(scene)
        if caption:
            self.append_log_line(caption)

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
