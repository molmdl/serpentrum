"""serpentrum plugin dialog shell (Phase 1: 3 placeholder tabs).

Module level imports ONLY pymol.Qt — the purity checker's GUI allowlist
is exactly this module. Direct PyQt5 imports are banned project-wide;
Qt reaches this code exclusively through pymol.Qt.

The three placeholder tabs (Setup / Game / Spectra) are registered via
QTabWidget.addTab; real tab content lands in Phases 3/4/7 (ROADMAP) and
the real bottom button row lands in Phase 8.
"""
from pymol.Qt import QtWidgets

# (key, label, placeholder text) — real content lands Phases 3/4/7 (ROADMAP)
_TAB_DEFS = [
    ('setup', 'Setup',
     'Setup tab — game configuration (demo set or upload, box size, '
     'head molecule, xtb path, win cap) arrives in Phase 3.'),
    ('game', 'Game',
     'Game tab — steered movement, timer, pickups and stacking '
     'arrive in Phases 4-5.'),
    ('spectra', 'Spectra',
     'Spectra tab — xtb run, broadened IR spectrum and frequency '
     'table arrive in Phases 6-7.'),
]


class PluginDialog(QtWidgets.QDialog):
    """Modeless 3-tab dialog shell.

    Shown via .show() only — the modal exec call is banned on the main
    dialog (INFRA-05; the Phase 1 checker fails any hit, since no child
    dialogs exist yet).

    Registration contract: each tab page is added with exactly one
    addTab(page, label) call inside __init__, in _TAB_DEFS order.
    """

    def __init__(self, parent=None):
        super(PluginDialog, self).__init__(parent)
        self.setWindowTitle('serpentrum')
        self.setMinimumWidth(450)
        self.tabs = QtWidgets.QTabWidget(self)
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
        buttons.addStretch(1)               # reserved row — no buttons in Phase 1
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
