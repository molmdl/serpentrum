"""serpentrum plugin dialog shell (3-tab dialog; Setup + Game live).

Module level imports ONLY pymol.Qt -- the purity checker's GUI allowlist
is exactly this module plus gui_setup and gui_game. Direct PyQt5
imports are banned project-wide; Qt reaches this code exclusively through
pymol.Qt.

Pages 0-1 (Setup, Game) are live (SetupTab from 03-07; GameTab from
Phase 4); page 2 (Spectra) remains a placeholder until Phase 7.
The real bottom button row lands in Phase 8 (SETUP-07).
"""
from pymol.Qt import QtWidgets

from .gui_setup import SetupTab
from .gui_game import GameTab

# Placeholder tabs (real content lands in later phases). Setup and
# Game are live pages 0-1 -- not in this list.
_TAB_DEFS = [
    ('spectra', 'Spectra',
     'Spectra tab - xtb run, broadened IR spectrum and frequency '
     'table arrive in Phases 6-7.'),
]


class PluginDialog(QtWidgets.QDialog):
    """Modeless 3-tab dialog shell.

    Shown via .show() only -- the main dialog stays modeless (INFRA-05).

    Registration contract: page 0 (Setup) is the live SetupTab from
    gui_setup; page 1 (Game) is the live GameTab from gui_game; page 2
    (Spectra) is a placeholder QWidget from _TAB_DEFS. Each page is
    added with exactly one addTab(page, label) call inside __init__.

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
        self.tabs = QtWidgets.QTabWidget(self)
        # Page 0: Setup (live SetupTab from gui_setup).
        setup_page = SetupTab(anchor_state, self.tabs)
        self.tabs.addTab(setup_page, 'Setup')
        # Page 1: Game (live GameTab from Phase 4, plan 04-05).
        self.game_tab = GameTab(anchor_state, self.tabs)
        self.tabs.addTab(self.game_tab, 'Game')
        # Page 2+: Spectra placeholder.
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
