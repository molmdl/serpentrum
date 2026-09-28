"""serpentrum.gui_spectra — the Spectra tab's live control surface (Phase 7,
plans 07-07..07-09; SPECTRA-01 tab surface, SPECTRA-03 on-screen plot,
SPECTRA-04 streaming log, SPECTRA-05 frequency table + mode vectors).

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

Layout indices are PINNED (07-RESEARCH Q5/Q6; the contract lives in
the 07-07 plan). FINAL order (07-09 inserted the table at index 2):
    [0] = status label, [1] = log panel (stretch 2),
    [2] = frequency table (stretch 2, SPECTRA-05),
    [3] = plot panel (stretch 3), [4] = button row.
07-10 checkpoint round 1 (owner directive — the dialog must fit the
screen): the log and the table carry FIXED maximum heights (scrolling)
so the page stays compact; the plot panel keeps its approved
exact-preset sizing (stretch still hands the panel the leftover space).
The dialog itself is also screen-capped in gui.py.

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
# the parse/Scene/live-fwhm seams (07-08), the frozen CGO arrow builder
# (07-09 consumes at scale=1.0), and the frozen status constants
# (06-02 — imported, never re-pinned). pymol_bridge is the BRIDGE seam
# for the viewer overlay (GUI -> BRIDGE import is the 06-09 precedent,
# check_purity.py:95-98).
from . import (cgo_build, help_text, plot_logic, pymol_bridge, setup_logic,
               spectra, spectra_ui, xtb_run)
from .gui_plot import SpectraPlotPanel


class SpectraTab(QtWidgets.QWidget):
    """The Spectra tab's status / streaming-log / run-control surfaces.

    Built by PluginDialog as page 2 (plan 07-07; the 06-09 placeholder
    page is gone). Owns: the status label, the bounded log panel, the
    SPECTRA-05 frequency table (07-09 — every parsed mode via the
    SHARED spectra_ui.table_rows/freq_label formatters; a row click
    draws that mode's static displacement vectors on the OPTIMIZED
    frame srp_xtbopt via the BRIDGE overlay, replace-per-click with
    once-per-record load/zoom), the embedded
    SpectraPlotPanel and its record->Scene feed (07-08 — SPECTRA-03
    on-screen plot feed complete), the contextual run button and its
    label logic, and the runner-slot display updates (started /
    log_line / run_finished). The dialog owns: the launch pipeline, the
    connect-once guard, the Get-Spectra re-enable and the game info-box
    feed (cross-tab orchestration the tab must not reach up for —
    model-A). The table and the plot render the SAME
    ``self._spectrum`` single-source parse (07-08) — index desync is
    structurally impossible (07-RESEARCH-spectra-seam.md Q4d).

    Layout (PINNED — see the module docstring; FINAL order):
    [0] status label, [1] log panel (stretch 2; fixed max height,
    scrolling — 07-10 owner directive), [2] frequency table
    (stretch 2; fixed max height, scrolling — same directive),
    [3] plot panel (stretch 3; approved exact-preset sizing kept),
    [4] button row (right-aligned).
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
        # 07-09 once-per-record overlay guards (viewer side, Task 2):
        # srp_xtbopt loads once per snake_id; the camera frames once
        # per snake_id (pitfall 14 — never per table click).
        self._xtbopt_snake_id = None
        self._zoomed_snake_id = None
        self._build_widgets()
        self._build_layout()

    def _build_widgets(self):
        """Create the four surfaces (PINNED order per the contract)."""
        # DOCS-03 (plan 08-09): the pre-run initial status is
        # single-sourced from help_text.spectra_hint('pre_run') - the
        # 08-06 pins prove the string byte-identical to the literal it
        # replaces. The 'xtb running...' started line stays inline
        # (pinned by 06-09; the audit pins it in place).
        self.status_label = QtWidgets.QLabel(
            help_text.spectra_hint('pre_run'), self)
        self.status_label.setWordWrap(True)
        # Research Q3 [TRAIN] MEDIUM: QPlainTextEdit + 500-block cap ==
        # the controller's tail — flat memory while streaming; human-
        # verified streaming at the 07-10 checkpoint.
        self.log_panel = QtWidgets.QPlainTextEdit(self)
        self.log_panel.setReadOnly(True)
        self.log_panel.setMaximumBlockCount(500)
        # 07-10 checkpoint round 1 (owner directive: the dialog too tall —
        # it must fit the screen): cap the log so it scrolls (~7 lines
        # visible) instead of inflating the page; the 500-block tail is
        # unchanged.
        self.log_panel.setMaximumHeight(110)
        # SPECTRA-05 frequency table (07-09): one read-only row per
        # parsed mode, SelectRows, click -> mode vectors (Task 2).
        # Populated ONLY from self._spectrum via spectra_ui.table_rows
        # (single-source parse — never re-derived here).
        self.table = QtWidgets.QTableWidget(0, 3, self)
        self.table.setHorizontalHeaderLabels(
            ('mode', 'frequency (cm-1)', 'IR intensity (km/mol)'))
        self.table.setEditTriggers(
            QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectRows)
        self.table.setSelectionMode(
            QtWidgets.QAbstractItemView.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.cellClicked.connect(self._on_table_cell_clicked)
        # 07-10 checkpoint round 1 (owner directive: the dialog too tall —
        # it must fit the screen): cap the table so it scrolls (~6-7 rows
        # visible via the scrollbar); row clicks are unaffected.
        self.table.setMaximumHeight(150)
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
        """FINAL pinned order: [0] status, [1] log (stretch 2),
        [2] frequency table (stretch 2), [3] plot panel (stretch 3),
        [4] right-aligned button row.
        """
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.status_label)          # [0]
        layout.addWidget(self.log_panel, 2)          # [1] stretch 2
        layout.addWidget(self.table, 2)              # [2] stretch 2
        layout.addWidget(self.plot_panel, 3)         # [3] stretch 3
        btn_row = QtWidgets.QHBoxLayout()            # [4]
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
            self._populate_table()

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
                    # already in the status; the plot and table stay
                    # empty.
                    self._spectrum = None
                    self._spectrum_note = None
                    self.plot_panel.set_scene(None)
                    self._populate_table()
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
            self._populate_table()
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
        # The SAME parse drives the SPECTRA-05 table (07-09).
        self._populate_table()
        # DOCS-03 (plan 08-09): a successful populate lands the
        # done-state next-action hint on the status line; the
        # vibspectrum-fallback advisory takes precedence when there is
        # one (the pre-08-09 behavior for that footnote, kept).
        if source_note:
            self.set_status_line(source_note)
        else:
            self.set_status_line(help_text.spectra_hint('done'))
        caption = plot_logic.mode_caption(scene)
        if caption:
            self.append_log_line(caption)
        # DOCS-03 (plan 08-09): the GATE D two-tier negative-frequency
        # guidance (spectra_ui.imaginary_note, 08-06) appends one log
        # line beside the mode caption via the SAME append seam; None
        # (no imaginary modes) appends nothing.
        note = spectra_ui.imaginary_note(
            [mode.freq for mode in spectrum.modes])
        if note is not None:
            self.append_log_line(note)

    # --- SPECTRA-05 frequency table + mode vectors (07-09) -------------

    def _populate_table(self):
        """Rebuild the frequency table from the SINGLE parse.

        Row r <=> self._spectrum.modes[r] — the table reads the one
        Spectrum 07-08 stored on the tab (single-source parse from the
        record; NEVER re-derived, re-parsed, or re-merged here, so an
        index desync between table rows and mode vectors is
        structurally impossible — 07-RESEARCH-spectra-seam.md Q4d).
        All labels come from the SHARED spectra_ui.table_rows (the
        single imaginary formatter freq_label: negatives as '-31.9i',
        ASCII hyphen-minus; intensities '%.4g' so zero-intensity rows
        stay visible AND distinct from tiny-but-nonzero — SPECTRA-05).
        A None spectrum (failed/cancelled/idle/corrupt record) clears
        the table — rows are never fabricated (Phase-6 SC3).
        """
        self.table.setRowCount(0)
        if self._spectrum is None:
            return
        rows = spectra_ui.table_rows(self._spectrum)
        self.table.setRowCount(len(rows))
        flags = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        for r, (idx, flabel, ilabel) in enumerate(rows):
            for column, text in enumerate((str(idx), flabel, ilabel)):
                item = QtWidgets.QTableWidgetItem(text)
                item.setFlags(flags)  # read-only, never editable
                self.table.setItem(r, column, item)
        self.table.resizeColumnsToContents()

    def _on_table_cell_clicked(self, row, column):
        """Row click -> the clicked mode's static displacement vectors
        drawn on the OPTIMIZED frame (SPECTRA-05; the cellClicked
        column is ignored — the ROW selects the mode).

        Flow: row r <=> self._spectrum.modes[r] (the single-source
        parse; 1-based selector input is r + 1) ->
        spectra_ui.mode_arrow_primitives -> the FROZEN
        cgo_build.mode_arrows at the v1-pinned scale=1.0
        (unit-normalized, uniform-length) -> pymol_bridge
        load_mode_arrows as srp_mode_vec. Every cmd touch goes through
        the BRIDGE seams (07-03) — the tab never imports pymol.cmd.

        Frame decision (07-RESEARCH-spectra-seam.md Q4b probe): the g98
        Standard-orientation atom block the arrows are built from is
        coordinate-identical to xtbopt.xyz (max pairwise-diff 1e-6 A),
        so the vectors are drawn over srp_xtbopt loaded from
        record['xtbopt_path'] — the game frame (srp_head/srp_seg_*)
        would be wrong by up to 0.14 A AND can have been cleaned.
        srp_xtbopt loads ONCE per record (snake_id-guarded,
        delete-then-reload on change); the camera zoom
        (zoom_mode_frame) fires ONCE per record (pitfall 14 — never
        per click). Repeated clicks REPLACE srp_mode_vec
        (delete-then-load; arrows never accumulate).

        Refusals are clear status lines, never crashes: no spectrum /
        missing xtbopt / vibspectrum-only parse (mode_arrow_primitives
        returns None). srp_ objects die at cleanup_srp / begin_game;
        a vanished overlay object mid-life is tolerated (every delete
        and zoom is guarded — pymol_bridge.object_exists / the 07-03
        guarded zoom). Static vectors only — per-tick animation is v2
        (GAME-09-v2). Every draw first sweeps srp_* to sticks
        (pymol_bridge.show_srp_sticks) — owner post-approval follow-up
        (07-10): the sphere head occluded the head-position vectors.
        """
        if self._spectrum is None:
            return
        record = getattr(self._anchor, 'spectra_run', None) or {}
        prims = spectra_ui.mode_arrow_primitives(self._spectrum, row + 1)
        if prims is None:
            self.set_status_line(
                'this spectrum has no displacement vectors '
                '(vibspectrum fallback) - vectors need the g98 output')
            return
        xtbopt_path = record.get('xtbopt_path')
        if not xtbopt_path:
            self.set_status_line(
                'the optimized structure file is unavailable - cannot '
                'draw mode vectors')
            return
        # Load the optimized frame ONCE per record (replace on
        # snake_id change or a vanished srp_xtbopt).
        if (not pymol_bridge.object_exists('srp_xtbopt')
                or self._xtbopt_snake_id != record.get('snake_id')):
            try:
                pymol_bridge.delete_object('srp_xtbopt')
                pymol_bridge.load_xtbopt(xtbopt_path)
                self._xtbopt_snake_id = record.get('snake_id')
            except OSError as exc:
                self.set_status_line(
                    'the optimized structure could not be loaded: %s'
                    % exc)
                return
        # Sticks sweep: the game snake's sphere head occludes the
        # head-position vectors (owner 07-10 post-approval follow-up);
        # hide/show are cheap no-ops when already sticks, so this runs
        # idempotently on every click. CGO/objects like srp_mode_vec
        # are unaffected; the game rebuild restores its own reps.
        pymol_bridge.show_srp_sticks()
        # Arrows: replace-per-click (delete-then-load; never
        # accumulate). Frozen builder; v1 pins scale=1.0.
        pymol_bridge.delete_object('srp_mode_vec')
        cgo = cgo_build.mode_arrows(prims[0], prims[1], scale=1.0)
        pymol_bridge.load_mode_arrows(cgo)
        # Camera: frame the overlay ONCE per record (pitfall 14); the
        # bridge zoom is a guarded no-op when neither object exists.
        if self._zoomed_snake_id != record.get('snake_id'):
            pymol_bridge.zoom_mode_frame()
            self._zoomed_snake_id = record.get('snake_id')
        # The educational framing states the frame EXPLICITLY (owner
        # sign-off at 07-10; an amended interpretation edits this line
        # + the load target only).
        self.set_status_line(
            'mode %d: vectors drawn on the optimized structure '
            '(srp_xtbopt)' % (row + 1))

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
