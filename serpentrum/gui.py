"""serpentrum plugin dialog shell (3-tab dialog; Setup + Game live).

Module level imports ONLY pymol.Qt -- the purity checker's GUI allowlist
is exactly this module plus gui_setup and gui_game. Direct PyQt5
imports are banned project-wide; Qt reaches this code exclusively through
pymol.Qt.

Pages 0-1 (Setup, Game) are live (SetupTab from 03-07; GameTab from
Phase 4); page 2 (Spectra) is the Phase-6 placeholder: a status label,
a bounded streaming log area and a contextual Cancel/Run-again button
wired to the anchored XtbRunController's signals (plan 06-09) -- Phase
7 replaces the page CONTENT, the launch + signal contracts survive.
The real bottom button row lands in Phase 8 (SETUP-07).
"""
from pymol.Qt import QtCore
from pymol.Qt import QtWidgets

from .gui_setup import SetupTab
from .gui_game import GameTab

# Generic placeholder tabs (none today: the Spectra page moved into
# _build_spectra_placeholder, plan 06-09). Future placeholder pages may
# be added back to this loop.
_TAB_DEFS = [
]

# ~200-line bound on the streaming log area (the document's block cap
# trims the oldest blocks on append).
_LOG_MAX_BLOCKS = 200
# Soft bound on the small status label so repeated launches can never
# grow it unboundedly (oldest lines dropped first).
_STATUS_MAX_LINES = 12

# The one refuse line shared by the launch pipeline and the Run-again
# button when no completed snake exists yet.
_NO_SNAKE_LINE = ('no completed snake to run - play a game to completion '
                  'first (Get Spectra activates on win or crash)')


class PluginDialog(QtWidgets.QDialog):
    """Modeless 3-tab dialog shell.

    Shown via .show() only -- the main dialog stays modeless (INFRA-05).

    Registration contract: page 0 (Setup) is the live SetupTab from
    gui_setup; page 1 (Game) is the live GameTab from gui_game; page 2
    (Spectra) is built by _build_spectra_placeholder (plan 06-09).
    Each page is added with exactly one addTab(page, label) call inside
    __init__.

    Switching contract: self.tabs (QTabWidget) is the documented
    handle -- setCurrentWidget(page) / setCurrentIndex(i); page order
    stays fixed Setup -> Game -> Spectra. The Start transition
    (GAME-01) is owned HERE: SetupTab.start_requested connects to
    _on_start_requested, which setCurrentIndex(1) + begin_game(setup);
    the Game tab never reaches up to its parent QTabWidget.

    Lifecycle hooks (plan 04-08): focusInEvent delegates to
    game_tab.request_auto_pause() (the Q3 focus-stealing safety net --
    a mid-run dialog focus gain pauses the game before the snake can
    crash unattended); closeEvent delegates to game_tab.shutdown()
    (mid-game dialog close tears down timers + wizard + camera lock --
    Pitfalls 8/9). Both guard with getattr(self, 'game_tab', None).
    """

    def __init__(self, parent=None, anchor_state=None):
        super(PluginDialog, self).__init__(parent)
        self.setWindowTitle('serpentrum')
        self.setMinimumWidth(450)
        # Live-state anchor (pmg_tk.startup._serpentrum): carries setup,
        # last_run and the Phase-6 spectra_runner; survives Plugin-
        # Manager reload; stripped-down constructions may pass None --
        # every launch path guards getattr, never raises.
        self._anchor = anchor_state
        # Dialog-scoped runner-wiring guard (plan 06-09): the anchored
        # controller outlives THIS dialog, so each dialog instance
        # connects the controller's signals to ITS OWN slots exactly
        # once (the old dialog's Qt connections die with it; connecting
        # twice on one dialog would duplicate slot calls).
        self._runner_connected = False
        self.tabs = QtWidgets.QTabWidget(self)
        # Page 0: Setup (live SetupTab from gui_setup).
        setup_page = SetupTab(anchor_state, self.tabs)
        self.tabs.addTab(setup_page, 'Setup')
        # Page 1: Game (live GameTab from Phase 4, plan 04-05).
        self.game_tab = GameTab(anchor_state, self.tabs)
        self.tabs.addTab(self.game_tab, 'Game')
        # Page 2: Spectra placeholder (Phase-6 control surface, plan
        # 06-09; Phase 7 replaces the page CONTENT, not the contract).
        self.tabs.addTab(self._build_spectra_placeholder(self.tabs),
                         'Spectra')
        # Any further generic placeholder pages (none today).
        for _key, label, text in _TAB_DEFS:
            page = QtWidgets.QWidget(self.tabs)
            page_lay = QtWidgets.QVBoxLayout(page)
            hint = QtWidgets.QLabel(text, page)
            hint.setWordWrap(True)
            page_lay.addStretch(1)
            page_lay.addWidget(hint)
            page_lay.addStretch(1)
            self.tabs.addTab(page, label)
        # Start flow (GAME-01, HUD research Q1 model A): SetupTab emits
        # start_requested(setup); this dialog owns the tab switch.
        setup_page.start_requested.connect(self._on_start_requested)
        # Get Spectra flow (GAME-09, plan 05-15): same model-A pattern -
        # GameTab emits spectra_requested; this dialog owns the switch.
        self.game_tab.spectra_requested.connect(self._on_spectra_requested)
        buttons = QtWidgets.QHBoxLayout()   # Phase 8: 6 right-aligned buttons
        buttons.addStretch(1)               # reserved row - no buttons in Phase 1
        outer = QtWidgets.QVBoxLayout(self)
        outer.addWidget(self.tabs)
        outer.addLayout(buttons)

    def _on_start_requested(self, setup):
        """GAME-01: switch to the Game tab and begin the session.

        The switch lives HERE (self.tabs is this dialog's handle); the
        Game tab never reaches up to its parent QTabWidget (HUD research
        Q1). begin_game tears down any live session first, rebuilds the
        engine from the setup dict, and runs the epoch-guarded
        countdown.
        """
        self.tabs.setCurrentIndex(1)
        self.game_tab.begin_game(setup)

    def _on_spectra_requested(self):
        """GAME-09: switch to the Spectra tab (model-A handoff per 04-06).

        The dialog owns the QTabWidget - GameTab never reaches its
        parent (locked decision 9). Page 2 is the Phase-7 placeholder
        (Phase 7 replaces its content); the last_run anchor record is
        already on _serpentrum for Phases 6/7, so nothing is passed
        through the signal itself.
        """
        self.tabs.setCurrentIndex(2)

    def _build_spectra_placeholder(self, parent):
        """Phase-6 Spectra placeholder page (plan 06-09, EQ-ux-1).

        Temporary control surface (Phase 7 replaces the page CONTENT;
        the launch + runner-signal contracts survive):

        - self.spectra_status: word-wrapped status label. Initial text
          is the old placeholder hint plus the how-to line ('complete a
          game, then press Get Spectra on the Game tab'); launch/
          verdict one-liners append here via _log_spectra_line, capped
          at _STATUS_MAX_LINES.
        - self.spectra_log: read-only streaming area for the runner's
          log_line events, bounded to _LOG_MAX_BLOCKS blocks (oldest
          trimmed by the document cap).
        - self.spectra_run_btn: contextual button -- 'Cancel xtb run'
          while a run is in flight, 'Run again' after any terminal
          branch; disabled until the first launch ('no xtb run yet').

        Layout: status on top, log stretching, button right-aligned
        under the log. NOTHING is added to the reserved bottom button
        row (Phase 8, SETUP-07).
        """
        page = QtWidgets.QWidget(parent)
        lay = QtWidgets.QVBoxLayout(page)
        self.spectra_status = QtWidgets.QLabel(
            'Spectra tab - xtb run, broadened IR spectrum and frequency '
            'table arrive in Phases 6-7. Complete a game, then press '
            'Get Spectra on the Game tab.', page)
        self.spectra_status.setWordWrap(True)
        self.spectra_log = QtWidgets.QTextBrowser(page)
        self.spectra_log.setReadOnly(True)
        self.spectra_log.document().setMaximumBlockCount(_LOG_MAX_BLOCKS)
        self.spectra_run_btn = QtWidgets.QPushButton('Cancel xtb run',
                                                     page)
        self.spectra_run_btn.setEnabled(False)
        self.spectra_run_btn.setToolTip('no xtb run yet')
        self.spectra_run_btn.clicked.connect(self._on_spectra_run_button)
        lay.addWidget(self.spectra_status)
        lay.addWidget(self.spectra_log, 1)
        lay.addWidget(self.spectra_run_btn, 0, QtCore.Qt.AlignRight)
        return page

    def _log_spectra_line(self, line):
        """Append one launch/verdict line to the Spectra status label.

        Also mirrors the line into the Game tab's info box via
        game_tab.log_external (EQ-ux-2: the established one-line-log
        channel stays fed); every reach is getattr-guarded -- a missing
        game_tab or info box can never crash a launch path. The label
        keeps at most _STATUS_MAX_LINES lines (oldest dropped first),
        so repeated launches cannot grow it unboundedly.
        """
        lines = self.spectra_status.text().split('\n')
        lines.append(line)
        if len(lines) > _STATUS_MAX_LINES:
            lines = lines[-_STATUS_MAX_LINES:]
        self.spectra_status.setText('\n'.join(lines))
        game_tab = getattr(self, 'game_tab', None)
        if game_tab is not None:
            log_external = getattr(game_tab, 'log_external', None)
            if log_external is not None:
                log_external(line)

    def _connect_runner(self, controller):
        """Wire the anchored XtbRunController's signals to THIS dialog.

        Guard flag is dialog-scoped, NOT anchor-scoped (plan 06-09):
        the controller lives on the anchor and can outlive this dialog;
        a Plugin-Manager reload builds a NEW dialog whose slots then
        receive the connections (the old dialog's Qt connections die
        with it). Idempotent within one dialog lifetime.
        """
        if self._runner_connected:
            return
        controller.started.connect(self._on_runner_started)
        controller.log_line.connect(self._on_runner_log_line)
        controller.run_finished.connect(self._on_run_finished)
        self._runner_connected = True

    def _on_runner_started(self):
        """Runner launch acknowledged: status line + arm the cancel leg."""
        self._log_spectra_line(
            'xtb running... (async - the dialog stays responsive)')
        self.spectra_run_btn.setText('Cancel xtb run')
        self.spectra_run_btn.setToolTip('cancel the running xtb job')
        self.spectra_run_btn.setEnabled(True)

    def _on_runner_log_line(self, line):
        """Stream one decoded xtb output line into the log area."""
        self.spectra_log.append(line)

    def _on_run_finished(self, status, problems):
        """Terminal branch (ok/failed/cancelled): verdict line + re-arm.

        Re-enables Get Spectra (the launch API owns its disarm; Q5
        re-entrancy) and flips the placeholder button to 'Run again' so
        SC2's relaunch-after-cancel/completion is one click away.
        """
        line = 'xtb finished: %s' % (status,)
        if problems:
            line += ' - ' + '; '.join(str(p) for p in problems)
        self._log_spectra_line(line)
        game_tab = getattr(self, 'game_tab', None)
        if game_tab is not None:
            btn = getattr(game_tab, 'get_spectra_btn', None)
            if btn is not None:
                btn.setEnabled(True)
        self.spectra_run_btn.setText('Run again')
        self.spectra_run_btn.setToolTip(
            'launch another xtb run on the completed snake')
        self.spectra_run_btn.setEnabled(True)

    def _on_spectra_run_button(self):
        """Contextual placeholder button (plan 06-09, EQ-ux-1).

        Cancel leg: the anchored controller reports a live run
        (status() 'running' mirrors xtb_run.RUNNING) -> cancel()
        (proc.kill() only -- the runner's terminal branch owns the
        verdict). Run-again leg (any terminal state): re-enter the FULL
        launch pipeline via _on_spectra_requested so every re-check
        (counts line, budget warnings, binary resolution, Get-Spectra
        disarm) holds on EVERY relaunch (SC4) -- NEVER
        _launch_spectra_run with stale values. No completed snake: the
        shared refuse line in the status area.
        """
        anchor = getattr(self, '_anchor', None)
        controller = (getattr(anchor, 'spectra_runner', None)
                      if anchor is not None else None)
        if (controller is not None
                and controller.status() == 'running'):
            controller.cancel()
            return
        record = (getattr(anchor, 'last_run', None)
                  if anchor is not None else None)
        if record is not None and record.get('snake_xyz'):
            # Re-enter the full pipeline; setCurrentIndex(2) is a no-op
            # on this page, so the visit is idempotent.
            self._on_spectra_requested()
            return
        self._log_spectra_line(_NO_SNAKE_LINE)

    def focusInEvent(self, event):
        """Q3 focus-stealing safety net (04-RESEARCH-input.md Q3 (b)).

        Fires on ANY dialog focus gain (including the Start click), but
        request_auto_pause guards on status == 'playing', so
        countdown/idle/over states are unaffected; only a mid-run focus
        steal auto-pauses. The snake can no longer crash unattended
        while the user reads the HUD.
        """
        QtWidgets.QDialog.focusInEvent(self, event)
        game_tab = getattr(self, 'game_tab', None)
        if game_tab is not None:
            game_tab.request_auto_pause()

    def closeEvent(self, event):
        """Mid-game dialog close must tear down the live round (Pitfall
        8/9: a closed dialog must never leave a locked mouse or an
        orphaned do_special). shutdown() funnels into the single
        _teardown_round (timers + epoch + input + camera); the session
        anchor survives for a later reopen via begin_game's
        teardown-first discipline.
        """
        game_tab = getattr(self, 'game_tab', None)
        if game_tab is not None:
            game_tab.shutdown()
        QtWidgets.QDialog.closeEvent(self, event)

    @classmethod
    def find_existing(cls):
        """Adopt-defense (INFRA-03): return an orphaned PluginDialog if one
        is alive on screen (e.g. anchor attr was lost), else None."""
        for w in QtWidgets.QApplication.topLevelWidgets():
            if isinstance(w, cls):
                return w
        return None
