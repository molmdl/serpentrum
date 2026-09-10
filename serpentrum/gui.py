"""serpentrum plugin dialog shell (3-tab dialog; Setup live from Phase 3).

Module level imports ONLY pymol.Qt -- the purity checker's GUI allowlist
is exactly this module plus gui_setup (added in Phase 3). Direct PyQt5
imports are banned project-wide; Qt reaches this code exclusively through
pymol.Qt.

Page 0 (Setup) is the live SetupTab from gui_setup (Phase 3, plan
03-07). Pages 1-2 (Game, Spectra) remain placeholders until Phases 4/7.
The real bottom button row lands in Phase 8 (SETUP-07).
"""
from pymol.Qt import QtWidgets

from .gui_setup import SetupTab

# Placeholder tabs for Game/Spectra (real content lands Phases 4/7).
# Setup is now the live SetupTab (page 0) -- not in this list.
_TAB_DEFS = [
    ('game', 'Game',
     'Game tab - steered movement, timer, pickups and stacking '
     'arrive in Phases 4-5.'),
    ('spectra', 'Spectra',
     'Spectra tab - xtb run, broadened IR spectrum and frequency '
     'table arrive in Phases 6-7.'),
]


class PluginDialog(QtWidgets.QDialog):
    """Modeless 3-tab dialog shell.

    Shown via .show() only -- the main dialog stays modeless (INFRA-05).

    Registration contract: page 0 (Setup) is the live SetupTab from
    gui_setup; pages 1-2 (Game, Spectra) are placeholder QWidgets from
    _TAB_DEFS. Each page is added with exactly one addTab(page, label)
    call inside __init__.

    Switching contract (later phases): self.tabs (QTabWidget) is the
    documented handle -- setCurrentWidget(page) / setCurrentIndex(i);
    page order stays fixed Setup -> Game -> Spectra.
    """

    def __init__(self, parent=None, anchor_state=None):
        super(PluginDialog, self).__init__(parent)
        self.setWindowTitle('serpentrum')
        self.setMinimumWidth(450)
        self.tabs = QtWidgets.QTabWidget(self)
        # Page 0: Setup (live SetupTab from gui_setup).
        setup_page = SetupTab(anchor_state, self.tabs)
        self.tabs.addTab(setup_page, 'Setup')
        # Pages 1-2: Game/Spectra placeholders.
        for _key, label, text in _TAB_DEFS:
            page = QtWidgets.QWidget(self.tabs)
            page_lay = QtWidgets.QVBoxLayout(page)
            hint = QtWidgets.QLabel(text, page)
            hint.setWordWrap(True)
            page_lay.addStretch(1)
            page_lay.addWidget(hint)
            page_lay.addStretch(1)
            self.tabs.addTab(page, label)
        buttons = QtWidgets.QHBoxLayout()   # Phase 8: 6 right-aligned buttons
        buttons.addStretch(1)               # reserved row - no buttons in Phase 1
        outer = QtWidgets.QVBoxLayout(self)
        outer.addWidget(self.tabs)
        outer.addLayout(buttons)

    @classmethod
    def find_existing(cls):
        """Adopt-defense (INFRA-03): return an orphaned PluginDialog if one
        is alive on screen (e.g. anchor attr was lost), else None."""
        for w in QtWidgets.QApplication.topLevelWidgets():
            if isinstance(w, cls):
                return w
        return None
