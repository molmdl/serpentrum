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
and the frequency table at SpectraTab's PINNED layout indices. Plan
08-08 landed the canonical 6-button bottom action row (SETUP-07) in
the QHBoxLayout reserved here since Phase 1; plan 08-13 gives every
button a student hover tooltip from help_text.BUTTON_TOOLTIPS
(QWidget.setToolTip, wired verbatim beside each construction).
"""
import tempfile

from pymol.Qt import QtCore, QtWidgets

from . import budget_guard
from . import dialog_fit
from . import help_text
from . import pymol_bridge
from . import setup_logic
from . import xtb_run
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
    _on_start_requested, which switches to the Game page (exactly ONE
    Start switch, the 04-06 byte-identical route) and calls
    begin_game(setup); the Game tab never reaches up to its parent
    QTabWidget.

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
        # Fixed-dialog chrome (round 3, debug session
        # .planning/debug/06-window-move-resize-quirk.md; owner
        # follow-up after the round-2 fixed-size patch: dragging the
        # TOP sizing border "sometimes flicks" and translates the
        # window). With min == max (freeze_dialog_size), a native
        # WS_THICKFRAME sizing-border grab can no longer resize
        # something: Windows clamps the height to the fixed size, so
        # the drag TRANSLATES the whole window instead. The
        # MSWindows fixed-size-dialog hint (flag expression below)
        # gives the dialog the fixed-dialog FRAME: no sizing borders
        # at all, so every edge and corner is hit-tested as
        # caption/dead glass and drags are fully inert. MUST be
        # applied here at construction, BEFORE the entry's .show()
        # (a setWindowFlags call on a visible widget hides it); OR'd
        # into the existing flags, never replacing them wholesale.
        # The thin chrome changes the FRAME margins slightly (the
        # sizing borders go away; the title bar stays), which is
        # fine in contract terms: freeze + position work from the
        # cap bases and the (scale-invariant) title-bar margin, not
        # from exact frame metrics.
        self.setWindowFlags(
            self.windowFlags() | QtCore.Qt.MSWindowsFixedSizeDialogHint)
        # Dialog sizing: FIXED SIZE, applied once at the END of
        # __init__ (see freeze_dialog_size below). The old
        # construction-time envelope (min width 450 + the 07-10
        # height cap, max(560, 0.92*avail)) is fully SUBSUMED by the
        # freeze: the 450 min-width promise survives inside it; the
        # height basis is 0.73 since round 5 (width stays 0.92 --
        # see freeze_dialog_size).
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
        # Page 0: Setup (live SetupTab from gui_setup). Retained as
        # self.setup_page (plan 08-08): the bottom action row wires to
        # the page's handlers, so the dialog must keep the reference.
        self.setup_page = SetupTab(anchor_state, self.tabs)
        self.tabs.addTab(self.setup_page, 'Setup')
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
        self.setup_page.start_requested.connect(self._on_start_requested)
        # Gameplay pause hook (plan 08-08): bottom-row handlers call
        # this BEFORE opening any modal (PITFALLS.md Pitfall 5 -- the
        # row is visible on the Game tab mid-run). request_auto_pause
        # already guards on status == 'playing', so unconditional calls
        # are safe; attribute assignment, never a signal.
        self.setup_page.game_pause_request = self.game_tab.request_auto_pause
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
        # Canonical bottom action row (plan 08-08, SETUP-07; button
        # order + labels verbatim from spec.md:21-26: Reset, Randomize,
        # Save Setup, Load Setup, Cleanup model, Start). addStretch(1)
        # FIRST keeps the six buttons right-aligned. All six wire to
        # SetupTab handlers; Start reuses the UNCHANGED _on_start (the
        # 04-06 byte-identical route: apply-first bool contract ->
        # start_requested.emit -> _on_start_requested owns the tab
        # switch + begin_game). Static QPushButton + .clicked.connect
        # only -- no dialogs, no blocking-call tokens.
        buttons = QtWidgets.QHBoxLayout()
        buttons.addStretch(1)
        reset_btn = QtWidgets.QPushButton('Reset', self)
        reset_btn.clicked.connect(self.setup_page._on_reset)
        reset_btn.setToolTip(help_text.BUTTON_TOOLTIPS['reset'])
        buttons.addWidget(reset_btn)
        randomize_btn = QtWidgets.QPushButton('Randomize', self)
        randomize_btn.clicked.connect(self.setup_page._on_randomize)
        randomize_btn.setToolTip(help_text.BUTTON_TOOLTIPS['randomize'])
        buttons.addWidget(randomize_btn)
        save_btn = QtWidgets.QPushButton('Save Setup', self)
        save_btn.clicked.connect(self.setup_page._on_save_setup)
        save_btn.setToolTip(help_text.BUTTON_TOOLTIPS['save'])
        buttons.addWidget(save_btn)
        load_btn = QtWidgets.QPushButton('Load Setup', self)
        load_btn.clicked.connect(self.setup_page._on_load_setup)
        load_btn.setToolTip(help_text.BUTTON_TOOLTIPS['load'])
        buttons.addWidget(load_btn)
        cleanup_btn = QtWidgets.QPushButton('Cleanup model', self)
        cleanup_btn.clicked.connect(self.setup_page._on_cleanup)
        cleanup_btn.setToolTip(help_text.BUTTON_TOOLTIPS['cleanup'])
        buttons.addWidget(cleanup_btn)
        start_btn = QtWidgets.QPushButton('Start', self)
        start_btn.clicked.connect(self.setup_page._on_start)
        start_btn.setToolTip(help_text.BUTTON_TOOLTIPS['start'])
        buttons.addWidget(start_btn)
        outer = QtWidgets.QVBoxLayout(self)
        outer.addWidget(self.tabs)
        outer.addLayout(buttons)
        # Fixed dialog size (owner directive 2026-10-04, debug session
        # .planning/debug/06-window-move-resize-quirk.md). 07-10
        # checkpoint round 1 owner directive, KEPT VERBATIM: "the
        # plugin window must never exceed the screen". The 07-10
        # implementation (min-width 450 + max-height cap) left a
        # 771->811 logical-px min-versus-max envelope; under the
        # owner's 200% Windows display scaling that slack put Qt and
        # Windows into a continuous WM geometry negotiation (decoded
        # SRP_DEBUG=1 console log: mintrack 926x1613 versus maxtrack
        # 0x1693, native heights oscillating 1622<->1778, frame tops
        # above the screen top) -- the owner-reported move flicker +
        # resize bounds escape. Owner decision: disable resize -- a
        # fixed-size game dialog, the reference-plugin precedent
        # (biochemeleon; see the debug file for what its dialog
        # actually ships). The game needs no user resize: the
        # SpectraTab log (cap 110) and table (cap 150) scroll
        # internally and the plot keeps its exact preset. setFixedSize
        # makes minimum == maximum, so WM_GETMINMAXINFO reports
        # mintrack == maxtrack: zero slack -- no resize handles, no
        # Qt<->Windows renegotiation at any move/size event. Stock
        # Windows move behavior stays (the window may be dragged
        # partially off-screen and back, like every other window):
        # the 07-10 directive bounds SIZE, not position.
        # ROUND 5 AMENDMENT (owner decision 2026-10-10, option D
        # "Two-column form", same debug session): the height cap
        # basis drops 0.92 -> 0.73 (width term untouched) and the
        # freeze gains the clip-proof rail max(minimumSizeHint.h,
        # min(hint, cap)) -- see freeze_dialog_size for the numbers.
        self.spectra_tab.plot_panel.dialog_size_refreeze = \
            self.freeze_dialog_size
        self.freeze_dialog_size()

    def freeze_dialog_size(self):
        """Freeze the dialog at its natural laid-out size, capped to
        the available screen -- the GATE V-approved opening look --
        and place it so its FRAME fits the screen.

        desired = sizeHint(): called after the top-level layout is
        complete, this is the same quantity Qt uses to open the
        dialog, so the frozen size reproduces the laid-out look
        exactly (including the 640x320 compact default plot
        preset pin -- the Spectra tab is part of the layout).

        Caps: the WIDTH keeps the 07-10 basis byte-identical
        (avail * 0.92 headroom, 450 min-width promise); the HEIGHT
        basis is 0.73 since the round-5 owner decision (2026-10-10,
        height-reduction option D "Two-column form", debug session
        .planning/debug/06-window-move-resize-quirk.md): with the
        two-column Setup page + the compact default plot, the
        content floor drops to ~640-668 logical px, so the cap
        max(560, int(avail.height() * 0.73)) (= 643 on the owner
        machine, avail 882) freezes a dialog ~170 logical px shorter
        than the old 811 -- casual title-bar drags no longer ride the
        bottom edge past the taskbar (~35 logical px of slack at
        811-of-882 vs ~240 at 643-of-882).

        Clip-proof rail (round 5, part of every menu option):
        height = max(minimumSizeHint().height(),
        min(desired.height(), cap_h)). minimumSizeHint is the LIVE
        layout minimum (totalMinimumSize), so the freeze can never
        fall below the content -- worst case it lands a few px TALLER
        than the cap, never clipping. The rail also rescues the
        PRESET-GROWN refreeze: a larger preset (e.g. large 800x500)
        raises the layout minimum above the cap, and the dialog
        re-freezes at the minimum (grows to fit, then the position
        clamp keeps the frame on-screen) instead of clipping at the
        cap. The width term needs no rail: max(450, ...) is its
        floor, and a layout hint can never undercut its own minimum.

        Position (round 3): a fixed SIZE was never paired with a
        POSITION -- Qt's default centers a fresh dialog on its parent
        (the PyMOL main window), which at ~92% screen height left
        the frame's bottom edge below the screen. One-shot placement
        from PURE dialog_fit math on the same available rect:
        PRE-SHOW (construction) the base is the avail center + frame
        -- with the round-5 height the centered widget top lands ~107
        logical px down (avail 882, dialog ~643-668), so the ~29-
        logical title-bar margin is absorbed with room to spare, and
        the clamp still covers the 560-floor + degenerate regimes
        where centering alone would not (see dialog_fit's docstring
        arithmetic). POST-SHOW (the plot-preset refreeze) the base is
        the CURRENT position, clamped under the NEW size with
        minimal shift so a grown dialog never bottoms out. move()
        pre-show only records the placement (Qt then opens exactly
        there -- no parent re-centering, no WM traffic on a hidden
        window); the refreeze move is one deliberate programmatic
        move per preset click. NO move/resize event handlers exist
        anywhere in serpentrum/ (that regression class is closed,
        test-pinned in tests/test_gui_pins.py) -- pre-show placement
        plus this hook are the only position code there is.

        Re-frozen on plot-preset changes via the injected hook
        plot_panel.dialog_size_refreeze (the 07-06 owner-approved
        exact-preset surface: choosing a larger/smaller preset makes
        the dialog re-freeze to fit, replacing the old auto-resize
        -- preset changes are the only post-construction change to
        the layout's minimums)."""
        avail = QtWidgets.QApplication.desktop().availableGeometry(self)
        desired = self.sizeHint()
        # Width: the 07-10 0.92 basis, byte-identical (no width growth
        # in the round-5 decision). Height: 0.73 since round 5 (see
        # docstring), 560 floor kept.
        cap_w = int(avail.width() * 0.92)
        cap_h = max(560, int(avail.height() * 0.73))
        # Clip-proof rail: never freeze below the live layout minimum.
        hinted_h = min(desired.height(), cap_h)
        height = max(self.minimumSizeHint().height(), hinted_h)
        self.setFixedSize(
            max(450, min(desired.width(), cap_w)),
            height)
        # One-shot frame-fit position on the SAME available rect
        # (round 3): margins from the live native window when it
        # exists (refreeze, post-show), else the measured fallback
        # estimates (construction, pre-show: windowHandle() is
        # None). Pure math in dialog_fit; this is the thin Qt seam.
        avail_tuple = (avail.x(), avail.y(),
                       avail.width(), avail.height())
        frozen_size = (self.width(), self.height())
        if self.isVisible():
            base = (self.x(), self.y())
        else:
            base = dialog_fit.centered_top_left(avail_tuple,
                                                frozen_size)
        x, y = dialog_fit.clamped_position(
            avail_tuple, frozen_size,
            self._frame_margins_for_clamp(), base)
        self.move(x, y)

    def _frame_margins_for_clamp(self):
        """Native frame margins for the position clamp, or the
        measured estimates when the native window does not exist.

        windowHandle() exists only once Qt has created the native
        window (first show); frameMargins() can also stay all-zero
        on some platforms until the frame is decorated, and a zero
        TOP margin is impossible for a titled Windows dialog -- both
        cases degrade to dialog_fit.FALLBACK_FRAME_MARGINS (outward-
        rounded logical estimates, see its comment). Safe to call at
        any time: pure attribute reads off the live window, no WM
        interaction.
        """
        handle = self.windowHandle()
        if handle is not None:
            margins = handle.frameMargins()
            top = margins.top()
            if top > 0:
                return (margins.left(), top,
                        margins.right(), margins.bottom())
        return dialog_fit.FALLBACK_FRAME_MARGINS

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

        Thread cap (owner insertion Q2, plan 08-12): extra_args carries
        the setup's thread cap via xtb_run's PURE thread_arg seam -
        the documented caller-override mechanism (the runner's own
        default fires only when extra_args is None). An absent/invalid
        key degrades to DEFAULT_THREAD_ARG (the shipped '-P 4' cap),
        so argv is byte-identical to the old default whenever the key
        is missing (all 06 runner pins stay green; the runner itself
        is UNTOUCHED).

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
        setup = getattr(anchor, 'setup', None)
        threads = setup.get('xtb_threads') if setup else None
        extra_args = (xtbenv.XTB_OHESS,) + xtb_run.thread_arg(threads)
        started = controller.start(record['snake_xyz'], exe,
                                   tempfile.gettempdir(),
                                   record['snake_id'],
                                   extra_args=extra_args)
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
