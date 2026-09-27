"""serpentrum plugin dialog shell (3-tab dialog; all three pages live).

Module level imports ONLY pymol.Qt -- the purity checker's GUI allowlist
covers this module plus gui_setup, gui_game and gui_spectra (the last
registered inert in 07-05, made live here in 07-07). Direct PyQt5
imports are banned project-wide; Qt reaches this code exclusively
through pymol.Qt.

Pages 0-1 (Setup, Game) are live (SetupTab from 03-07; GameTab from
Phase 4); page 2 (Spectra) is the live SpectraTab from gui_spectra
(plan 07-07 -- the 06-09 placeholder page is gone; the launch + runner
signal contracts survive intact). Plans 07-08/07-09 add the plot panel
and the frequency table at SpectraTab's PINNED layout indices. The
real bottom button row lands in Phase 8 (SETUP-07).
"""
import tempfile

from pymol.Qt import QtWidgets

from . import budget_guard
from . import pymol_bridge
from . import setup_logic
from . import xtb_runner
from . import xtbenv
from . import xyzio
from .gui_setup import SetupTab
from .gui_game import GameTab
from .gui_spectra import SpectraTab

# The one refuse line shared by the launch pipeline and the Run-again
# button when no completed snake exists yet.
_NO_SNAKE_LINE = ('no completed snake to run - play a game to completion '
                  'first (Get Spectra activates on win or crash)')


class PluginDialog(QtWidgets.QDialog):
    """Modeless 3-tab dialog shell.

    Shown via .show() only -- the main dialog stays modeless (INFRA-05).

    Registration contract: page 0 (Setup) is the live SetupTab from
    gui_setup; page 1 (Game) is the live GameTab from gui_game; page 2
    (Spectra) is the live SpectraTab from gui_spectra (plan 07-07).
    Each page is added with exactly one addTab(page, label) call inside
    __init__.

    Spectra orchestration (plan 07-07, model-A / locked decision 9):
    the dialog OWNS all cross-tab work -- the launch pipeline
    (_on_spectra_requested), the dialog-scoped connect-once guard over
    the anchored controller's signals, the Get-Spectra re-enable on the
    terminal branch, and the game info-box feed (game_tab.log_external).
    The tab OWNS its three surfaces (status label, streaming log panel,
    contextual run button) and NEVER reaches up: its Run-again leg is
    the emit-only run_again_requested signal, connected HERE to the
    full launch pipeline (06-09's pinned Run-again semantics). Plans
    07-08/07-09 add the plot panel and table at the tab's pinned layout
    indices; the modeless + model-A contracts are unchanged.

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
        # 07-10 checkpoint round 1 (owner directive: the plugin window
        # must never exceed the screen): cap the dialog to the available
        # screen height — content scrolls within tabs; the plot keeps
        # its approved preset size. The QApplication always exists in
        # the PyMOL GUI.
        avail = QtWidgets.QApplication.desktop().availableGeometry(self)
        self.setMaximumHeight(max(560, int(avail.height() * 0.92)))
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
        # Page 2: Spectra (live SpectraTab from gui_spectra, plan 07-07;
        # the 06-09 placeholder page is gone - the launch + signal
        # contracts survive). Table/plot surfaces arrive in 07-08/07-09
        # at the tab's pinned layout indices.
        self.spectra_tab = SpectraTab(anchor_state, self.tabs)
        self.tabs.addTab(self.spectra_tab, 'Spectra')
        # Start flow (GAME-01, HUD research Q1 model A): SetupTab emits
        # start_requested(setup); this dialog owns the tab switch.
        setup_page.start_requested.connect(self._on_start_requested)
        # Get Spectra flow (GAME-09, plan 05-15): same model-A pattern -
        # GameTab emits spectra_requested; this dialog owns the switch.
        self.game_tab.spectra_requested.connect(self._on_spectra_requested)
        # Run-again flow (plan 07-07): the tab's button emits only; the
        # dialog re-enters the FULL launch pipeline (identical to a Get
        # Spectra press - 06-09's pinned Run-again semantics).
        self.spectra_tab.run_again_requested.connect(
            self._on_spectra_requested)
        # Reload recovery (plan 07-07): a live or terminal controller
        # from before this dialog was built renders immediately - the
        # connect-once path replays the controller's log tail BEFORE
        # wiring log_line, then reflect_run_state draws the surface.
        runner = (getattr(anchor_state, 'spectra_runner', None)
                  if anchor_state is not None else None)
        if runner is not None:
            self._connect_runner(runner)
            self.spectra_tab.reflect_run_state()
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
        """GAME-09: switch to the Spectra tab, then run the Phase-6
        launch pipeline (plan 06-09, SPECTRA-02/06).

        The dialog owns the QTabWidget - GameTab never reaches its
        parent (locked decision 9 / model-A). The Spectra-tab switch
        stays FIRST (the switch is GAME-09/Phase-7 UX) so the user
        watches the status area as the pipeline speaks. The
        spectra_requested signal contract is UNCHANGED - the extension
        lives entirely in this SLOT, never in GameTab.

        Pipeline legs (each precondition failure emits one CLEAR line
        and NO launch - SC3, never a fake success):

        1. Anchor guard: None means stripped-down state -> 'plugin
           state unavailable - reopen the plugin'.
        2. last_run guard: missing record or missing snake_xyz -> the
           shared _NO_SNAKE_LINE (precondition failure per
           EQ-desync-1, not a desync warning). Get Spectra stays as-is.
        3. Head-inclusive counts (research guard Q1/pitfall 1):
           atoms_engine = len(xyzio.read_xyz_text(snake_xyz)[1]) - the
           TRUE xtb input size; NEVER last_run['atoms_total']
           (head-EXCLUDED). xyzio.XyzError -> 'run input is corrupt:
           <exc>' quoted verbatim, no launch (the engine-built input
           should never be corrupt; this is the launch-boundary
           contract). Viewer cross-check: pymol_bridge.chain_atom_counts
           over the frozen last_run['chain_objects'] (sum = atoms incl.
           head, len = molecules incl. head).
        4. SPECTRA-06 re-check (warn-and-proceed, log-lines-only,
           EQ-guard-2): budget_guard.launch_counts_line +
           launch_budget_warnings, every line logged BEFORE any launch
           (SC4) into the status area AND the game info box (EQ-ux-2).
           atom_budget comes from the anchor's setup with the
           setup_logic.DEFAULTS fallback when setup is None (reload
           hole - NEVER crash).
        5. Binary resolution: xtbenv.detect_binary with the
           SETUP-05-configured path (the user seam; the runner adds no
           fallback list). None -> 'xtb not found - set the xtb path on
           the Setup tab (auto-detect found nothing)', no launch, Get
           Spectra stays enabled (nothing started).
        6. Disarm Get Spectra (the launch API owns the disarm - research
           guard Q5 re-entrancy; re-enable happens on the terminal
           run_finished branch or on a refused start) and launch via
           _launch_spectra_run (async - the dialog never blocks).
        """
        self.tabs.setCurrentIndex(2)
        anchor = getattr(self, '_anchor', None)
        if anchor is None:
            self._log_spectra_line(
                'plugin state unavailable - reopen the plugin')
            return
        record = getattr(anchor, 'last_run', None)
        if record is None or not record.get('snake_xyz'):
            self._log_spectra_line(_NO_SNAKE_LINE)
            return
        try:
            _comment, atoms = xyzio.read_xyz_text(record['snake_xyz'])
        except xyzio.XyzError as exc:
            self._log_spectra_line('run input is corrupt: %s' % (exc,))
            return
        atoms_engine = len(atoms)
        molecules_stacked = record['molecules_stacked']
        names = record['chain_objects'] or []
        view_counts = pymol_bridge.chain_atom_counts(names)
        atoms_view = sum(view_counts)
        molecules_view = len(names)
        setup = getattr(anchor, 'setup', None)
        atom_budget = (setup.get('atom_budget') if setup
                       else setup_logic.DEFAULTS['atom_budget'])
        lines = [budget_guard.launch_counts_line(
            molecules_stacked, atoms_engine, atom_budget)]
        lines += budget_guard.launch_budget_warnings(
            molecules_stacked, molecules_view, atoms_engine, atoms_view,
            atom_budget)
        for line in lines:
            self._log_spectra_line(line)
        exe = xtbenv.detect_binary(setup.get('xtb_path') if setup
                                   else None)
        if exe is None:
            self._log_spectra_line(
                'xtb not found - set the xtb path on the Setup tab '
                '(auto-detect found nothing)')
            return
        game_tab = getattr(self, 'game_tab', None)
        if game_tab is not None:
            btn = getattr(game_tab, 'get_spectra_btn', None)
            if btn is not None:
                btn.setEnabled(False)
        self._launch_spectra_run(record, exe)

    def _launch_spectra_run(self, record, exe):
        """Create-or-reuse the anchored controller and start the run.

        Controller ownership (plan 06-09): the FIRST launch builds
        xtb_runner.XtbRunController(anchor) and parks it on
        anchor.spectra_runner (narrow ownership - no module-level
        state, reload-single by construction), then wires its signals
        via _connect_runner (dialog-scoped once, NOT anchor-scoped).
        base_dir is tempfile.gettempdir() evaluated INSIDE Windows
        PyMOL (never a /mnt/c path at runtime - STACK.md:168);
        snake_id comes from the frozen last_run record.

        A False return from start() (no-double-run guard or a preflight
        failure - the controller already emitted its own log line)
        re-enables Get Spectra and notes the no-start: the disarm from
        step 6 is unwound and state never sticks at 'running'."""
        anchor = self._anchor
        controller = getattr(anchor, 'spectra_runner', None)
        if controller is None:
            controller = xtb_runner.XtbRunController(anchor)
            anchor.spectra_runner = controller
        self._connect_runner(controller)
        started = controller.start(record['snake_xyz'], exe,
                                   tempfile.gettempdir(),
                                   record['snake_id'])
        if not started:
            game_tab = getattr(self, 'game_tab', None)
            if game_tab is not None:
                btn = getattr(game_tab, 'get_spectra_btn', None)
                if btn is not None:
                    btn.setEnabled(True)
            self._log_spectra_line('xtb run did not start (see log)')

    def _log_spectra_line(self, line):
        """Route one launch/verdict line to the SpectraTab surfaces.

        Plan 07-07 destination rewire (06-09 decisions unchanged): the
        line lands on the tab's status label AND its streaming log
        panel (both stay readable), and keeps mirroring into the Game
        tab's info box via game_tab.log_external (EQ-ux-2: the
        established one-line-log channel stays fed); every reach is
        getattr-guarded -- a missing game_tab or info box can never
        crash a launch path.
        """
        self.spectra_tab.set_status_line(line)
        self.spectra_tab.append_log_line(line)
        game_tab = getattr(self, 'game_tab', None)
        if game_tab is not None:
            log_external = getattr(game_tab, 'log_external', None)
            if log_external is not None:
                log_external(line)

    def _connect_runner(self, controller):
        """Wire the anchored XtbRunController's signals (plan 07-07).

        Guard flag is dialog-scoped, NOT anchor-scoped (plan 06-09):
        the controller lives on the anchor and can outlive this dialog;
        a Plugin-Manager reload builds a NEW dialog whose slots then
        receive the connections (the old dialog's Qt connections die
        with it). Idempotent within one dialog lifetime.

        The replay BEFORE the connect closes the reload early-line
        hole: controller.log_tail() (07-04's accessor) streams the
        bounded tail into the tab first, then plain same-thread
        connects hand over the live stream. log_line/started land
        STRAIGHT on the tab's methods; run_finished lands on the
        dialog's cross-tab slot (Get-Spectra re-enable first, then the
        tab's terminal display). Re-launches on a reused controller
        are safe: start() resets the controller's tail (06-05
        behavior) and this one-time path has already run.
        """
        if self._runner_connected:
            return
        self.spectra_tab.replay_log(controller.log_tail())
        controller.log_line.connect(self.spectra_tab.append_log_line)
        controller.started.connect(self.spectra_tab.on_runner_started)
        controller.run_finished.connect(self._on_spectra_run_finished)
        self._runner_connected = True

    def _on_spectra_run_finished(self, status, problems):
        """Terminal branch (ok/failed/cancelled): dialog-owned leg.

        The dialog owns the cross-tab orchestration (model-A): FIRST
        re-enable Get Spectra (getattr-guarded -- 06-09's pinned
        terminal re-enable; the launch API owns the disarm, Q5
        re-entrancy), THEN hand the verdict to the tab's terminal
        display (run_status_lines vocabulary + 'Run again' button
        flip). The tab never reaches up.
        """
        game_tab = getattr(self, 'game_tab', None)
        if game_tab is not None:
            btn = getattr(game_tab, 'get_spectra_btn', None)
            if btn is not None:
                btn.setEnabled(True)
        self.spectra_tab.on_run_finished(status, problems)

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
