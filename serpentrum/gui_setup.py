"""serpentrum.gui_setup - the Setup tab configuration form (GUI class).

Phase 3 plan 03-07. SetupTab(QWidget) is the live configuration form that
makes SETUP-02..06 user-visible: demo-set dropdown + upload picker, box
preset, head molecule, xtb auto-detect + manual path, win cap with the
inline hessian warning, and a persistent validate() status label. Three
TEMPORARY buttons (Apply / Show in Viewer, Cleanup, Start) live INSIDE
this page -- the canonical 6-button bottom row (SETUP-07) and save/load
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

from . import generic_stack
from . import hud_logic
from . import molecule_data
from . import molfile
from . import orientation
from . import pymol_bridge
from . import setloader
from . import setup_logic
from . import xtbenv

# Sentinel userData for the demo-combo Upload entry (UI routing ONLY).
# The setup dict's demo_set field only ever holds KNOWN_SETS values
# (setup_logic.validate rejects anything else); this sentinel tells
# _on_apply to route through setloader.load_upload instead of
# load_demo_set. collect_state() maps it back to the last real set so
# the dict stays valid even while the combo shows 'Upload...'.
_UPLOAD_SENTINEL = '__upload__'


class SetupTab(QtWidgets.QWidget):
    """The Setup configuration form.

    Seven QGroupBox sections (Molecule set, Box, Head molecule, xtb,
    Win cap, Speed, Generic stacking) + a persistent status QLabel +
    three temporary buttons
    (Apply / Show in Viewer, Cleanup, Start). collect_state()/apply_state()
    round-trip is the established pattern: collect_state reads widgets
    into the setup dict; apply_state populates widgets from the dict. A
    _loading flag guards apply_state against cascading signal recompute.
    """

    # Emitted with the collected setup dict when Start succeeds (apply
    # first). Temp Phase-4 signal; the canonical Start button lives in
    # the Phase-8 bottom row (SETUP-07).
    start_requested = QtCore.Signal(object)

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

        # --- Speed section (Phase 5.1, plan 5.1-04; 1:1 box_combo
        #     pattern copy over setup_logic.SPEED_TIERS) ---
        self.speed_combo = QtWidgets.QComboBox(self)
        for name, aps in setup_logic.SPEED_TIERS:
            self.speed_combo.addItem('%s (%.1f A/s)' % (name, aps), aps)

        # --- Generic stacking consent section (Phase 5.2, plan 5.2-05;
        #     1:1 xtb_auto_check QCheckBox pattern copy; sub-line is a
        #     plain ALWAYS-VISIBLE word-wrapped QLabel -- the
        #     hessian-label pattern WITHOUT hide()/color; DRAFT wording
        #     owner-amendable at 5.2-09) ---
        self.generic_stack_check = QtWidgets.QCheckBox(
            'Allow generic pi-stack for uploads '
            '(illustrative geometry - user-approved)', self)
        self.generic_stack_note_label = QtWidgets.QLabel(
            'reuses the approved Set A pi-stack geometry '
            '(3.60 A @ 20 deg off-normal) for uploads carrying a '
            'planar aromatic 6-ring', self)
        self.generic_stack_note_label.setWordWrap(True)

        # --- Status label ---
        self.status_label = QtWidgets.QLabel('ready', self)
        self.status_label.setWordWrap(True)

        # --- Temporary buttons (Phase 3; Phase 8 replaces with the
        #     canonical 6-button bottom row) ---
        self.apply_btn = QtWidgets.QPushButton(
            'Apply / Show in Viewer', self)
        self.cleanup_btn = QtWidgets.QPushButton('Cleanup', self)
        self.start_btn = QtWidgets.QPushButton('Start', self)

    def _build_layout(self):
        """Arrange widgets into 7 QGroupBox sections + status + buttons."""
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

        # --- Speed group (Phase 5.1, plan 5.1-04; appended AFTER the
        #     Win cap group as a new sibling section) ---
        speed_group = QtWidgets.QGroupBox('Speed', self)
        speed_form = QtWidgets.QFormLayout(speed_group)
        speed_form.addRow('Tier:', self.speed_combo)
        layout.addWidget(speed_group)

        # --- Generic stacking group (Phase 5.2, plan 5.2-05; appended
        #     AFTER the Speed group as a new sibling section, before
        #     the status label -- 5.1-04 sibling-section precedent) ---
        generic_group = QtWidgets.QGroupBox('Generic stacking', self)
        generic_form = QtWidgets.QFormLayout(generic_group)
        generic_form.addRow('', self.generic_stack_check)
        generic_form.addRow('', self.generic_stack_note_label)
        layout.addWidget(generic_group)

        # --- Status label ---
        layout.addWidget(self.status_label)

        # --- Stretch ---
        layout.addStretch(1)

        # --- Temporary buttons row ---
        btn_row = QtWidgets.QHBoxLayout()
        btn_row.addWidget(self.apply_btn)
        btn_row.addWidget(self.cleanup_btn)
        btn_row.addWidget(self.start_btn)
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
        self.speed_combo.currentIndexChanged.connect(self._refresh_status)
        # House-minimum wire: _refresh_status's own _loading guard
        # covers apply_state restores, so no dedicated handler.
        self.generic_stack_check.stateChanged.connect(self._refresh_status)
        self.apply_btn.clicked.connect(self._on_apply)
        self.cleanup_btn.clicked.connect(self._on_cleanup)
        self.start_btn.clicked.connect(self._on_start)
        self.browse_upload_btn.clicked.connect(self._on_browse_upload)
        self.browse_xtb_btn.clicked.connect(self._on_browse_xtb)

    # --- state round-trip -------------------------------------------------

    def collect_state(self):
        """Read all widgets into the setup dict and write back to the anchor.

        The demo combo's '__upload__' sentinel maps to the last real set
        (self._last_real_set) so the dict stays valid. Speed is
        widget-written via the tier combo (Phase 5.1, plan 5.1-04);
        generic_stack_consent is widget-written via the consent
        checkbox (Phase 5.2, plan 5.2-05). The remaining non-widget
        fields (schema_version, atom_budget, broadening_fwhm) are
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
        speed = self.speed_combo.currentData()
        if speed is not None:
            setup['speed'] = speed
        head = self.head_combo.currentData()
        if head is not None:
            setup['head_molecule'] = head
        if self.xtb_auto_check.isChecked():
            setup['xtb_path'] = None
        else:
            setup['xtb_path'] = self.xtb_path_field.text().strip()
        setup['win_cap_molecules'] = self.win_cap_spin.value()
        setup['generic_stack_consent'] = self.generic_stack_check.isChecked()
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
        # Speed tier (Phase 5.1, plan 5.1-04). Loaded non-tier values
        # (e.g. hand-edited 50.0) fall back to the DEFAULT tier; the
        # dict keeps the custom value until the next collect_state
        # normalizes it (house fallback semantics).
        idx = self.speed_combo.findData(
            setup.get('speed', setup_logic.DEFAULTS['speed']))
        if idx < 0:
            idx = self.speed_combo.findData(setup_logic.DEFAULTS['speed'])
        if idx < 0:
            idx = 0
        self.speed_combo.setCurrentIndex(idx)
        # Generic stacking consent checkbox (Phase 5.2, plan 5.2-05;
        # absent key = OFF via the DEFAULTS fallback -- mirrors the
        # speed restore pattern; under the _loading guard so the
        # setChecked signal does not recompute).
        self.generic_stack_check.setChecked(bool(setup.get(
            'generic_stack_consent',
            setup_logic.DEFAULTS['generic_stack_consent'])))
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
          2. Record building via setloader (demo vs upload routing,
             WITH the stacking dataset so records carry has_stack_entry)
             -> load errors stop with a rejection modal.
          3. Anchor records + the stacking dataset on _serpentrum
             (Phase 5, plan 05-06: begin_game, Restart determinism,
             the skip policy, and the info-box builders consume them).
             Phase 5.2 (plan 5.2-05): the anchored dataset is the
             consent-gated overlay -- OFF anchors the original object,
             ON appends the generic upload entry.
          4. Head combo repopulation from loaded records.
          5. Edge-on head matrix computed PURE-ly (Phase 5, plan 05-10)
             + pymol_bridge.materialize(head_m16=...) -> bridge errors
             stop with a 'Load failed' modal.
          6. Success: status message + absorbed C2 zero-stackable
             clause (consent-aware, reusing hud_logic.stack_mode_note)
             + xtb detect note + validate warnings; write the dict
             back to the anchor.
        All dialogs are static QMessageBox.warning(self, title, body).
        Returns True when the scene materialized; False otherwise
        (Start suppresses its emit on any False path).
        """
        setup = self.collect_state()
        errors, warnings = setup_logic.validate(setup)
        if errors:
            QtWidgets.QMessageBox.warning(
                self, 'Cannot apply', '\n'.join(errors))
            self.status_label.setText('errors: ' + '; '.join(errors))
            return False

        # Generic upload stacking consent (Phase 5.2, plan 5.2-05):
        # read once here so BOTH the overlay anchor below and the
        # absorbed C2 soft warning in the success parts consume the
        # same flag (absent key = OFF via the DEFAULTS fallback).
        consent = setup.get(
            'generic_stack_consent',
            setup_logic.DEFAULTS['generic_stack_consent'])

        # Record building: route by the demo combo's currentData().
        # Phase 5, plan 05-06: both load paths get the stacking dataset
        # so demo records carry has_stack_entry=True (set_a matches the
        # shipped APPROVED pi-stack entry; uploads stay False via the
        # '__upload__' skip-policy keying).
        source = self.demo_combo.currentData()
        if source == _UPLOAD_SENTINEL:
            path = self.upload_path_field.text().strip()
            records, load_errors = setloader.load_upload(
                path, stacking_path=setloader.default_stacking_path())
            error_title = 'Upload rejected'
        else:
            records, load_errors = setloader.load_demo_set(
                set_id=source,
                stacking_path=setloader.default_stacking_path())
            error_title = 'Cannot load set'
        if load_errors:
            QtWidgets.QMessageBox.warning(
                self, error_title, '\n'.join(load_errors))
            self.status_label.setText(
                'load errors: ' + '; '.join(load_errors))
            return False

        # Anchor records + the stacking dataset on _serpentrum (Phase 5,
        # plan 05-06; locked decision 10: NEVER module globals, NEVER
        # the scalar-only setup dict). setloader returns only records +
        # errors, so the dataset dict is loaded fresh here -- the file
        # is tiny and static. On dataset failure, anchor records with
        # stacking_data=None: has_stack_entry was already computed False
        # in that case, so the skip policy degrades to SKIP_NO_ENTRY,
        # which is correct.
        stacking_note = None
        if self._anchor is not None and records:
            stacking_data = None
            try:
                stacking_data = molecule_data.load_stacking(
                    setloader.default_stacking_path())
            except (molecule_data.DataError, IOError):
                stacking_note = (
                    'stacking dataset unavailable - '
                    'pickups will be skipped')
            self._anchor.records = records
            # Consent-gated overlay anchor (Phase 5.2, plan 5.2-05;
            # EQ-engine-3: anchored AT APPLY -- Start always Applies
            # first (model-A handoff), so the Capture resolve read-site
            # (gui_game) consumes the consent decision with ZERO
            # per-capture plumbing). The overlay is the consent
            # carrier: OFF anchors the ORIGINAL dataset object (same
            # object identity = byte-identical capture path); ON
            # appends the generic upload entry LAST so first-match
            # lookup order shadows nothing. overlay_stacking_data is
            # None-safe: stacking_data None -> None anchored (unchanged
            # dataset-unavailable degradation).
            self._anchor.stacking_data = generic_stack.overlay_stacking_data(
                stacking_data, consent)

        # Repopulate head combo from loaded records, then re-read state.
        # _loading guard (defense-in-depth alongside _populate_head_combo's
        # blockSignals) prevents any leaked signal from clobbering the
        # post-Apply status text set below.
        self._loading = True
        self._populate_head_combo(records)
        self._loading = False
        setup = self.collect_state()

        # Compute the edge-on head matrix BEFORE materialize (Phase 5,
        # plan 05-10; locked 03-08 + 04-07: edge-on at materialization,
        # BEFORE any stacking can work). The bridge never parses SDFs,
        # so the pure m16 is computed HERE: _select_head_record is
        # pure-with-respect-to-cmd (no cmd usage), so calling it again
        # picks the SAME record materialize will (its advisory errors
        # are re-generated inside materialize's own error list). A
        # record without 'stack_ring' (ring-less uploads — 2026-09-20c
        # fix G2 gave uploads with a canonical planar 6-ring the demo
        # stack_ring/edge-on path; records without a resolvable ring
        # still) or any parse/frame failure degrades to head_m16=None —
        # flat head — rather than blocking Apply; load problems already
        # surface through the record-building error list.
        head_m16 = None
        if records:
            try:
                head_errors = []
                head_record = pymol_bridge._select_head_record(
                    setup, records, head_errors)
                if (head_record is not None
                        and 'stack_ring' in head_record):
                    parsed = molfile.read_sdf(head_record['file'])[0]
                    head_m16 = orientation.edge_on_m16(
                        parsed['elements'], parsed['coords'],
                        head_record['stack_ring'])
            except Exception:
                head_m16 = None

        # Materialize box + head via the bridge (the only cmd path).
        bridge_errors = pymol_bridge.materialize(
            setup, records, head_m16=head_m16)
        if bridge_errors:
            QtWidgets.QMessageBox.warning(
                self, 'Load failed', '\n'.join(bridge_errors))
            self.status_label.setText(
                'load failed: ' + '; '.join(bridge_errors))
            return False

        # Success: build the status message.
        parts = ['Box + head materialized']
        if stacking_note is not None:
            parts.append(stacking_note)
        if setup.get('head_molecule') == 'random':
            parts.append('head will be randomized at game start')
        # Absorbed C2 soft warning (debug session 05-upload-only,
        # resolved 2026-09-21; absorbed Phase 5.2, plan 5.2-05): SOFT
        # status clause (HARD block REJECTED -- demo mode is
        # legitimate). Reuses hud_logic.stack_mode_note so the Apply
        # warning and the begin_game note share ONE wording source
        # (consent-aware predicate: under consent ON ring-bearing
        # uploads keep a zero-stackable set stackable).
        zero_stackable = hud_logic.stack_mode_note(records, consent)
        if zero_stackable is not None:
            parts.append(zero_stackable)
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
        return True

    def _on_start(self):
        """Start (temp, Phase 4): apply the current config, then emit.

        Applies FIRST so the game always plays on a materialized scene
        (box + head exist for visible movement -- GAME-01); a failed
        apply (validation/load/bridge modal) suppresses the emit. Emits
        the post-apply setup dict; PluginDialog switches tabs and calls
        GameTab.begin_game (HUD research Q1 model A).
        """
        if self._on_apply():
            self.start_requested.emit(self.collect_state())

    def _on_cleanup(self):
        """Cleanup: remove all srp_* objects from the viewer."""
        n = pymol_bridge.cleanup_srp()
        self.status_label.setText(
            'Cleanup removed %d srp_* object(s)' % n)
