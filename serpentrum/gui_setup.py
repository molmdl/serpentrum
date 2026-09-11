"""serpentrum.gui_setup - the Setup tab configuration form (GUI class).

Phase 3 plan 03-07. SetupTab(QWidget) is the live configuration form that
makes SETUP-02..06 user-visible: demo-set dropdown + upload picker, box
preset, head molecule, xtb auto-detect + manual path, win cap with the
inline hessian warning, and a persistent validate() status label. Two
TEMPORARY buttons (Apply / Show in Viewer + Cleanup) live INSIDE this
page -- the canonical 6-button bottom row (SETUP-07) and save/load
(SETUP-08) stay in Phase 8; the reserved bottom QHBoxLayout in gui.py is
untouched.

Purity class: GUI (pymol.Qt only at module level; bare pymol/pmg_tk
banned at any level; PyQt5/numpy banned). All PyMOL cmd access goes
through pymol_bridge (the BRIDGE-class cmd-seam) -- this module NEVER
imports pymol.cmd directly. setloader (PURE) builds molecule records
before the bridge materializes them. Error surfacing follows the
researched split: one-shot blocking errors use the static
QMessageBox.warning convenience (a static method carrying no blocking
call token in source, so the AST purity gate stays clean); the
hessian-cost advisory is an inline QLabel toggled by the spinbox;
validate() verdicts show in the persistent status label.

Anchor persistence (research sec 8): the live setup dict anchors on
pmg_tk.startup._serpentrum.setup (added to _SerpentrumState in
__init__.py). SetupTab reads/writes it via the anchor object passed in
from run_plugin_gui -> PluginDialog -> SetupTab -- NEVER module globals
(Pitfall 7: reload/double-import would duplicate them). On first anchor
creation, _anchor() initializes state.setup = setup_logic.new_setup();
reload reuses the existing anchor, so the user's dict survives.

Thread boundary: handlers run on the Qt main thread = the PyMOL gui
thread; pymol_bridge/setloader are called directly (sub-second ops, no
worker/queue needed in Phase 3). No threads are spawned.

python3.6 syntax (%-formatting).
"""

from pymol.Qt import QtWidgets, QtCore

from . import setup_logic
from . import setloader
from . import xtbenv
from . import pymol_bridge

# Sentinel userData for the demo-combo Upload entry (UI routing ONLY).
# The setup dict's demo_set field only ever holds KNOWN_SETS values
# (setup_logic.validate rejects anything else); this sentinel tells
# _on_apply to route through setloader.load_upload instead of
# load_demo_set. collect_state() maps it back to the last real set so
# the dict stays valid even while the combo shows 'Upload...'.
_UPLOAD_SENTINEL = '__upload__'


class SetupTab(QtWidgets.QWidget):
    """The Setup configuration form.

    Five QGroupBox sections (Molecule set, Box, Head molecule, xtb, Win
    cap) + a persistent status QLabel + two temporary buttons (Apply /
    Show in Viewer, Cleanup). collect_state()/apply_state() round-trip
    is the established pattern: collect_state reads widgets into the
    setup dict; apply_state populates widgets from the dict. A _loading
    flag guards apply_state against cascading signal recompute.
    """

    def __init__(self, anchor_state=None, parent=None):
        super(SetupTab, self).__init__(parent)
        self._anchor = anchor_state
        self._loading = False
        if (anchor_state is not None
                and getattr(anchor_state, 'setup', None) is not None):
            self._setup = anchor_state.setup
        else:
            self._setup = setup_logic.new_setup()
        self._last_real_set = self._setup.get('demo_set', 'set_a')
        self._build_widgets()
        self._build_layout()
        self._wire_signals()
        self.apply_state(self._setup)

    # --- widget construction ----------------------------------------------

    def _build_widgets(self):
        """Create all widgets and populate combo box items."""
        # --- Molecule set section ---
        self.demo_combo = QtWidgets.QComboBox(self)
        for set_id in setup_logic.KNOWN_SETS:
            label = 'Demo ' + set_id.replace('_', ' ').title()
            self.demo_combo.addItem(label, set_id)
        self.demo_combo.addItem('Upload...', _UPLOAD_SENTINEL)

        self.upload_path_field = QtWidgets.QLineEdit(self)
        self.upload_path_field.setReadOnly(True)
        self.upload_path_field.setPlaceholderText(
            'Click Browse to choose a .sdf or .mol2 file')
        self.browse_upload_btn = QtWidgets.QPushButton('Browse', self)

        # --- Box section ---
        self.box_combo = QtWidgets.QComboBox(self)
        for preset in setup_logic.BOX_PRESETS:
            self.box_combo.addItem(preset.title(), preset)

        # --- Head molecule section ---
        self.head_combo = QtWidgets.QComboBox(self)
        self.head_combo.addItem('Random', 'random')

        # --- xtb section ---
        self.xtb_auto_check = QtWidgets.QCheckBox(
            'Auto-detect (use xtb from PATH)', self)
        self.xtb_path_field = QtWidgets.QLineEdit(self)
        self.xtb_path_field.setPlaceholderText('Manual xtb executable path')
        self.browse_xtb_btn = QtWidgets.QPushButton('Browse', self)

        # --- Win cap section ---
        self.win_cap_spin = QtWidgets.QSpinBox(self)
        self.win_cap_spin.setRange(1, 20)
        self.hessian_label = QtWidgets.QLabel(self)
        self.hessian_label.setWordWrap(True)
        self.hessian_label.setStyleSheet('color: #cc6600;')
        self.hessian_label.hide()

        # --- Status label ---
        self.status_label = QtWidgets.QLabel('ready', self)
        self.status_label.setWordWrap(True)

        # --- Temporary buttons (Phase 3; Phase 8 replaces with the
        #     canonical 6-button bottom row) ---
        self.apply_btn = QtWidgets.QPushButton(
            'Apply / Show in Viewer', self)
        self.cleanup_btn = QtWidgets.QPushButton('Cleanup', self)

    def _build_layout(self):
        """Arrange widgets into 5 QGroupBox sections + status + buttons."""
        layout = QtWidgets.QVBoxLayout(self)

        # --- Molecule set group (QVBoxLayout: upload row needs
        #     show/hide as a unit) ---
        mol_group = QtWidgets.QGroupBox('Molecule set', self)
        mol_lay = QtWidgets.QVBoxLayout(mol_group)
        demo_row = QtWidgets.QHBoxLayout()
        demo_row.addWidget(QtWidgets.QLabel('Demo set:', mol_group))
        demo_row.addWidget(self.demo_combo, 1)
        mol_lay.addLayout(demo_row)
        self._upload_container = QtWidgets.QWidget(mol_group)
        upload_lay = QtWidgets.QHBoxLayout(self._upload_container)
        upload_lay.setContentsMargins(0, 0, 0, 0)
        upload_lay.addWidget(QtWidgets.QLabel('File:', self._upload_container))
        upload_lay.addWidget(self.upload_path_field, 1)
        upload_lay.addWidget(self.browse_upload_btn)
        mol_lay.addWidget(self._upload_container)
        self._upload_container.setVisible(False)
        layout.addWidget(mol_group)

        # --- Box group ---
        box_group = QtWidgets.QGroupBox('Box', self)
        box_form = QtWidgets.QFormLayout(box_group)
        box_form.addRow('Preset:', self.box_combo)
        layout.addWidget(box_group)

        # --- Head molecule group ---
        head_group = QtWidgets.QGroupBox('Head molecule', self)
        head_form = QtWidgets.QFormLayout(head_group)
        head_form.addRow('Head:', self.head_combo)
        layout.addWidget(head_group)

        # --- xtb group ---
        xtb_group = QtWidgets.QGroupBox('xtb', self)
        xtb_form = QtWidgets.QFormLayout(xtb_group)
        xtb_form.addRow('Mode:', self.xtb_auto_check)
        xtb_path_widget = QtWidgets.QWidget(xtb_group)
        xtb_path_lay = QtWidgets.QHBoxLayout(xtb_path_widget)
        xtb_path_lay.setContentsMargins(0, 0, 0, 0)
        xtb_path_lay.addWidget(self.xtb_path_field, 1)
        xtb_path_lay.addWidget(self.browse_xtb_btn)
        xtb_form.addRow('Path:', xtb_path_widget)
        layout.addWidget(xtb_group)

        # --- Win cap group ---
        cap_group = QtWidgets.QGroupBox('Win cap', self)
        cap_form = QtWidgets.QFormLayout(cap_group)
        cap_form.addRow('Molecules:', self.win_cap_spin)
        cap_form.addRow('', self.hessian_label)
        layout.addWidget(cap_group)

        # --- Status label ---
        layout.addWidget(self.status_label)

        # --- Stretch ---
        layout.addStretch(1)

        # --- Temporary buttons row ---
        btn_row = QtWidgets.QHBoxLayout()
        btn_row.addWidget(self.apply_btn)
        btn_row.addWidget(self.cleanup_btn)
        btn_row.addStretch(1)
        layout.addLayout(btn_row)

    def _wire_signals(self):
        """Connect widget signals to handlers."""
        self.demo_combo.currentIndexChanged.connect(self._on_source_changed)
        self.box_combo.currentIndexChanged.connect(self._refresh_status)
        self.head_combo.currentIndexChanged.connect(self._refresh_status)
        self.xtb_auto_check.stateChanged.connect(self._on_xtb_auto_changed)
        self.xtb_path_field.textChanged.connect(self._refresh_status)
        self.upload_path_field.textChanged.connect(self._refresh_status)
        self.win_cap_spin.valueChanged.connect(self._on_cap_changed)
        self.win_cap_spin.valueChanged.connect(self._refresh_status)
        self.apply_btn.clicked.connect(self._on_apply)
        self.cleanup_btn.clicked.connect(self._on_cleanup)
        self.browse_upload_btn.clicked.connect(self._on_browse_upload)
        self.browse_xtb_btn.clicked.connect(self._on_browse_xtb)

    # --- state round-trip -------------------------------------------------

    def collect_state(self):
        """Read all widgets into the setup dict and write back to the anchor.

        The demo combo's '__upload__' sentinel maps to the last real set
        (self._last_real_set) so the dict stays valid. Non-widget fields
        (schema_version, atom_budget, broadening_fwhm, speed) are
        preserved from the existing dict via a shallow copy.
        """
        setup = dict(self._setup)
        source = self.demo_combo.currentData()
        if source == _UPLOAD_SENTINEL:
            setup['demo_set'] = self._last_real_set
        else:
            setup['demo_set'] = source
            self._last_real_set = source
        box = self.box_combo.currentData()
        if box is not None:
            setup['box_preset'] = box
        head = self.head_combo.currentData()
        if head is not None:
            setup['head_molecule'] = head
        if self.xtb_auto_check.isChecked():
            setup['xtb_path'] = None
        else:
            setup['xtb_path'] = self.xtb_path_field.text().strip()
        setup['win_cap_molecules'] = self.win_cap_spin.value()
        self._setup = setup
        if self._anchor is not None:
            self._anchor.setup = setup
        return setup

    def apply_state(self, setup):
        """Populate all widgets from the setup dict (guarded by _loading).

        The _loading flag prevents cascading signal recompute during
        programmatic widget population. _on_cap_changed and
        _refresh_status are called after _loading is cleared so the
        hessian label and status label reflect the applied state.
        """
        self._loading = True
        # Demo set combo: match userData, fallback first real set.
        demo_set = setup.get('demo_set', 'set_a')
        idx = self.demo_combo.findData(demo_set)
        if idx < 0:
            idx = 0
        self.demo_combo.setCurrentIndex(idx)
        # Box preset.
        box = setup.get('box_preset', 'medium')
        idx = self.box_combo.findData(box)
        if idx >= 0:
            self.box_combo.setCurrentIndex(idx)
        # Head molecule (fallback Random if not in the combo).
        head = setup.get('head_molecule', 'random')
        idx = self.head_combo.findData(head)
        if idx < 0:
            idx = 0
        self.head_combo.setCurrentIndex(idx)
        # xtb auto-detect + path.
        xtb_path = setup.get('xtb_path')
        if xtb_path is None:
            self.xtb_auto_check.setChecked(True)
            self.xtb_path_field.setEnabled(False)
            self.browse_xtb_btn.setEnabled(False)
            self.xtb_path_field.setText('')
        else:
            self.xtb_auto_check.setChecked(False)
            self.xtb_path_field.setEnabled(True)
            self.browse_xtb_btn.setEnabled(True)
            self.xtb_path_field.setText(xtb_path)
        # Win cap.
        self.win_cap_spin.setValue(setup.get('win_cap_molecules', 10))
        self._loading = False
        self._on_cap_changed()
        self._refresh_status()

    # --- signal handlers --------------------------------------------------

    def _on_source_changed(self):
        """Reveal/hide the upload row per the demo combo selection."""
        is_upload = self.demo_combo.currentData() == _UPLOAD_SENTINEL
        self._upload_container.setVisible(is_upload)
        self._refresh_status()

    def _on_cap_changed(self):
        """Show the hessian warning QLabel when win cap > 10, else hide."""
        if self._loading:
            return
        if self.win_cap_spin.value() > 10:
            self.hessian_label.setText(setup_logic.HESSIAN_WARNING)
            self.hessian_label.show()
        else:
            self.hessian_label.hide()

    def _on_xtb_auto_changed(self):
        """Enable/disable the xtb path field per the auto-detect checkbox.

        When auto-detect is ON, surface the detect result immediately
        (resolved path or not-found note) so the user sees whether xtb
        was found without clicking Apply. When OFF, revert to the
        validate() verdict (which includes the 'empty path -> error'
        rule for a manually-cleared path field).
        """
        auto = self.xtb_auto_check.isChecked()
        self.xtb_path_field.setEnabled(not auto)
        self.browse_xtb_btn.setEnabled(not auto)
        if not auto or self._loading:
            self._refresh_status()
            return
        self._refresh_status_with_xtb()

    def _refresh_status(self):
        """Refresh the status label from validate(collect_state())."""
        if self._loading:
            return
        errors, warnings = setup_logic.validate(self.collect_state())
        if errors:
            self.status_label.setText('errors: ' + '; '.join(errors))
        elif warnings:
            self.status_label.setText('warning: ' + '; '.join(warnings))
        else:
            self.status_label.setText('ready')

    def _refresh_status_with_xtb(self):
        """Show the xtb detect result, unless validate reports errors.

        Errors take precedence (they block Apply anyway). When validate
        is clean, the status shows the resolved xtb path or a not-found
        note -- the same detect call Apply uses, surfaced immediately on
        the auto-detect toggle so the user does not have to Apply first.
        """
        setup = self.collect_state()
        errors, _warnings = setup_logic.validate(setup)
        if errors:
            self.status_label.setText('errors: ' + '; '.join(errors))
            return
        resolved = xtbenv.detect_binary(
            configured_path=setup.get('xtb_path'))
        if resolved:
            self.status_label.setText('xtb: ' + resolved)
        else:
            self.status_label.setText(
                'xtb not found - set a manual path or add xtb to PATH')

    def _on_browse_upload(self):
        """Open a file dialog to choose an upload molecule set file."""
        path, _filter = QtWidgets.QFileDialog.getOpenFileName(
            self, 'Choose molecule set', '',
            'Molecules (*.sdf *.mol2);;All Files (*)')
        if path:
            self.upload_path_field.setText(path)

    def _on_browse_xtb(self):
        """Open a file dialog to choose the xtb executable."""
        path, _filter = QtWidgets.QFileDialog.getOpenFileName(
            self, 'Choose xtb executable', '', 'All Files (*)')
        if path:
            self.xtb_path_field.setText(path)

    def _populate_head_combo(self, records):
        """Repopulate the head combo from loaded records.

        Entries: 'Random' (userData 'random') + one per record (label =
        record['name'], userData = record['id']). The current selection
        is kept when still present; otherwise defaults to Random.
        Signals are blocked during repopulation to avoid cascading
        _refresh_status calls.
        """
        prev = self.head_combo.currentData()
        self.head_combo.blockSignals(True)
        self.head_combo.clear()
        self.head_combo.addItem('Random', 'random')
        for record in records:
            self.head_combo.addItem(record['name'], record['id'])
        restored = False
        if prev is not None:
            idx = self.head_combo.findData(prev)
            if idx >= 0:
                self.head_combo.setCurrentIndex(idx)
                restored = True
        if not restored:
            self.head_combo.setCurrentIndex(0)
        self.head_combo.blockSignals(False)

    # --- Apply / Cleanup handlers ----------------------------------------

    def _on_apply(self):
        """Apply: validate, load records, materialize box + head.

        Flow (per 03-RESEARCH-setup-ui.md Apply path):
          1. collect_state + validate -> errors stop with a warning modal.
          2. Record building via setloader (demo vs upload routing) ->
             load errors stop with a rejection modal.
          3. Head combo repopulation from loaded records.
          4. pymol_bridge.materialize -> bridge errors stop with a
             'Load failed' modal.
          5. Success: status message + xtb detect note + validate
             warnings; write the dict back to the anchor.
        All dialogs are static QMessageBox.warning(self, title, body).
        """
        setup = self.collect_state()
        errors, warnings = setup_logic.validate(setup)
        if errors:
            QtWidgets.QMessageBox.warning(
                self, 'Cannot apply', '\n'.join(errors))
            self.status_label.setText('errors: ' + '; '.join(errors))
            return

        # Record building: route by the demo combo's currentData().
        source = self.demo_combo.currentData()
        if source == _UPLOAD_SENTINEL:
            path = self.upload_path_field.text().strip()
            records, load_errors = setloader.load_upload(path)
            error_title = 'Upload rejected'
        else:
            records, load_errors = setloader.load_demo_set(set_id=source)
            error_title = 'Cannot load set'
        if load_errors:
            QtWidgets.QMessageBox.warning(
                self, error_title, '\n'.join(load_errors))
            self.status_label.setText(
                'load errors: ' + '; '.join(load_errors))
            return

        # Repopulate head combo from loaded records, then re-read state.
        # _loading guard (defense-in-depth alongside _populate_head_combo's
        # blockSignals) prevents any leaked signal from clobbering the
        # post-Apply status text set below.
        self._loading = True
        self._populate_head_combo(records)
        self._loading = False
        setup = self.collect_state()

        # Materialize box + head via the bridge (the only cmd path).
        bridge_errors = pymol_bridge.materialize(setup, records)
        if bridge_errors:
            QtWidgets.QMessageBox.warning(
                self, 'Load failed', '\n'.join(bridge_errors))
            self.status_label.setText(
                'load failed: ' + '; '.join(bridge_errors))
            return

        # Success: build the status message.
        parts = ['Box + head materialized']
        if setup.get('head_molecule') == 'random':
            parts.append('head will be randomized at game start')
        # xtb detection (advisory in Phase 3; blocking is Phase 6).
        resolved = xtbenv.detect_binary(
            configured_path=setup.get('xtb_path'))
        if resolved:
            parts.append('xtb: ' + resolved)
        else:
            parts.append(
                'xtb not found - set a manual path or add xtb to PATH')
        if warnings:
            parts.append('warning: ' + '; '.join(warnings))
        self.status_label.setText('; '.join(parts))
        # Write the dict back to the anchor (collect_state already did,
        # but be explicit after a successful apply).
        if self._anchor is not None:
            self._anchor.setup = self._setup

    def _on_cleanup(self):
        """Cleanup: remove all srp_* objects from the viewer."""
        n = pymol_bridge.cleanup_srp()
        self.status_label.setText(
            'Cleanup removed %d srp_* object(s)' % n)
