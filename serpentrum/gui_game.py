"""serpentrum.gui_game - the Game tab HUD (Phase 4, plan 04-05).

GameTab(QWidget) is the GAME-01/GAME-07/GAME-08 engine-and-display core:
the epoch-guarded 3-2-1-GO! countdown, the 100 ms movement tick that
drives engine.step + pymol_bridge.move_head_delta, the 1 Hz
wall-clock-delta elapsed label, the molecules-remaining label, the
read-only rolling info box, pause/resume with the Pitfall 9.3 time
rebase, and the deterministic restart. Plan 04-08 wired the play
lifecycle: _begin_play locks the camera (GAME-02) + installs the
steering wizard (GAME-03) BEFORE the timers start; _teardown_round is
THE single teardown helper on every end path (Pitfall 9.2); pause gates
steering via game_input.set_active (wizard stays installed, camera
stays locked - research D5); request_auto_pause is the focus-stealing
safety net (input research Q3 (b)). The Start button + tab switch are
plan 04-06. Plan 05-11 wires the game-start half of Phase 5: begin_game
seeds the FIRST deterministic pickup via spawn.PickupSpawner over the
anchored records, materializes it edge-on as sticks, mirrors the head
purely (edge-on + extent-center + per-tick translate == viewer truth),
and resets the head pose on Restart. The 'stacked' capture seam
(05-13), swept-turn rendering (05-14), and completion handoff (05-15)
all build on this session state.

Purity class: GUI (pymol.Qt ONLY at module level - the check_purity
GUI_MODULES entry landed in plan 04-01; relative imports of the pure
and bridge modules are exempt; PyQt5/numpy banned). The bridge owns
all viewer-command access - this module NEVER imports pymol directly.
Blocking modal-run calls are BANNED everywhere (modeless rule): no
modals in this tab, the info box shows verdicts. python3.6 syntax
(%-formatting).

Reload model (Pitfall 7/8): the two QTimers are Qt-parent-owned by this
widget and die with it on a Plugin-Manager reload; the game SESSION dict
(engine + epoch + start_time + paused_accum + status + the plan 05-11
head-mirror/spawn state) anchors on
pmg_tk.startup._serpentrum.game_session (the field added to
_SerpentrumState in __init__.py, this plan's Task 1) and therefore
survives reload - single-instance by construction, NEVER module globals
and NEVER widget-owned. Every singleShot countdown callback closes over
the epoch it was scheduled under and no-ops if stale (Pitfall 9.1 -
singleShot chains cannot be cancelled); _teardown_round bumps
self._epoch to kill any in-flight chain, and begin_game records the
session epoch AFTER that bump (single epoch authority - no second
increment).

Thread boundary (04-RESEARCH-gameloop.md Q1): the QTimer timeout slots
run on the Qt main thread = the PyMOL GUI thread, so engine.step (pure)
and the bridge movement call are safe directly - no threads are
spawned. Elapsed-time math is delta-based from the wall clock
(time.time() - start_time - paused_accum), NEVER accumulated tick
counts (Pitfall 5).
"""

import math
import os
import time

from pymol.Qt import QtWidgets, QtCore

from . import game_engine
from . import hud_logic
from . import pymol_bridge
from . import setup_logic
# Pure modules consumed by the Phase-5 begin_game wiring (plan 05-11):
# molfile (record parsing), orientation (edge-on matrices/atoms),
# placement (the 05-13 'stacked' seam), spawn (deterministic pickup
# spawner). Relative imports of pure modules are purity-exempt in the
# GUI class.
from . import molfile
from . import orientation
from . import placement
from . import spawn as spawn_mod
# ROUTE-AGNOSTIC input seam (04-07 verdict APPROVED the wizard route).
# Both routes expose identical install/set_active/teardown signatures,
# so a fallback verdict would swap this ONE line to
# ``from . import gui_input as game_input`` (nothing else changes).
from . import input as game_input

# Movement tick: 100 ms with dt=0.1 s passed to engine.step -> exactly
# 0.3 A/tick at SPEED_A_PER_S=3.0, matching the engine's tested
# parameter (test_engine_core.py DELTA=0.1; 04-RESEARCH-gameloop.md
# S2). Fixed dt keeps engine determinism; cadence jitter is eaten by
# QTimer, not by the simulation. Playtesting-tunable.
TICK_DT = 0.1
TICK_INTERVAL_MS = 100

# Elapsed label refresh rate (1 Hz; only the "M:SS" text updates).
ELAPSED_INTERVAL_MS = 1000


# --- Phase-5 pure mirror helpers (plan 05-11) -------------------------------
# These replicate in PURE math the exact transforms the bridge applies to
# the viewer objects so the controller's atom mirrors stay exactly equal
# to the objects' atomic coordinates (mirror == viewer by construction).

def _extent_offset(atoms):
    """Per-axis min/max midpoint of (sym, x, y, z) atoms.

    pymol_bridge.place_head's centering math in PURE form: the offset is
    the same one place_head subtracts from the viewer object, so pure
    mirrors built with it line up with the object's coordinates 1:1.
    """
    xs = [a[1] for a in atoms]
    ys = [a[2] for a in atoms]
    zs = [a[3] for a in atoms]
    return ((min(xs) + max(xs)) / 2.0,
            (min(ys) + max(ys)) / 2.0,
            (min(zs) + max(zs)) / 2.0)


def _extent_center(atoms):
    """Return a NEW atom list translated by -_extent_offset(atoms)."""
    ox, oy, oz = _extent_offset(atoms)
    return [(a[0], a[1] - ox, a[2] - oy, a[3] - oz) for a in atoms]


def _read_record(path):
    """Parse one molecule file -> the first molfile record dict.

    Routes by extension exactly like setloader.load_upload so upload
    records (.mol2 allowed) parse with the mol2 reader; demo records
    always take the SDF path.
    """
    if os.path.splitext(path)[1].lower() == '.mol2':
        return molfile.read_mol2(path)[0]
    return molfile.read_sdf(path)[0]


def _heading_name(heading):
    """Reverse-lookup the DIRS name for an engine heading unit vector.

    spawn.PickupSpawner's contract takes the heading NAME ('left' /
    'right' / 'up' / 'down' - spawn.py _DIRS keying) while the engine
    stores the unit vector. Rigid 90-degree sweeps keep the engine
    heading EXACTLY on one of the four axis vectors, so an exact
    match always exists during play.
    """
    for name, unit in game_engine.DIRS.items():
        if unit == heading:
            return name
    raise ValueError('heading %r is not an axis direction' % (heading,))


class GameTab(QtWidgets.QWidget):
    """The Game tab HUD.

    Built by PluginDialog as page 1 (plan 04-06 wires it in and calls
    begin_game on Start). Owns the tick + elapsed QTimers (Qt parent
    ownership - they die with the widget). The session dict anchors on
    _serpentrum.game_session so a Plugin-Manager reload cannot
    duplicate it; every singleShot/timeout callback is epoch-guarded
    (Pitfall 9.1).

    Phase 5 note (plan 05-11): pickups + completion-flow cleanup are now
    live - begin_game seeds/materializes the first pickup and
    _teardown_round pattern-deletes srp_pickup_* on EVERY end path, so
    an un-stacked pickup dies while the chain (srp_head/srp_seg_*)
    stays complete (the GAME-09 'viewer clears' ordering: on the
    _end_run path teardown runs BEFORE the completion presenter).

    Phase 5 note (plan 05-13): the 'stacked' capture seam is live -
    _handle_stack_event resolves every ('stacked', pickup) event
    synchronously in ONE tick via placement.resolve (skip -> tail ->
    place -> gate), attaches placed pickups to the chain (viewer
    transform + 'srp_seg_<n>' rename inside the srp_ prefix), and
    rejects EVERY non-placed outcome through engine.reject_pickup
    (locked decision 13 - counters can never desync, and a clash-
    refused cap capture un-finishes the run via 05-04). Every
    resolution appends to the session's stacked_history (the STACK-04
    per-pickup record whose 'name'/'outcome'/'distance_a'/
    'citation_short'/'interaction_id' fields hud_logic.breakdown_lines
    consumes at completion) and runs the one-spawn-per-resolution
    respawn gate (05-03). The 'won' branch logs only when
    engine.finished still holds, so a false YOU WIN is impossible.
    """

    def __init__(self, anchor_state=None, parent=None):
        super(GameTab, self).__init__(parent)
        self._anchor = anchor_state
        self._epoch = 0        # single epoch authority (see class docstring)
        self._session = None   # the live session dict (also anchored)
        self._build_widgets()
        self._build_layout()
        self._wire_signals()
        # Two DISTINCT QTimers, both Qt-parent-owned by self: the 100 ms
        # movement tick and the 1 Hz elapsed-label refresh (research Q2's
        # two-distinct-timers table).
        self._tick_timer = QtCore.QTimer(self)
        self._tick_timer.setInterval(TICK_INTERVAL_MS)
        self._tick_timer.timeout.connect(self._on_tick)
        self._elapsed_timer = QtCore.QTimer(self)
        self._elapsed_timer.setInterval(ELAPSED_INTERVAL_MS)
        self._elapsed_timer.timeout.connect(self._on_elapsed_tick)
        self._set_idle_state()  # buttons disabled until a game begins

    # --- widget construction ----------------------------------------------

    def _build_widgets(self):
        """Create the researched Q2 widget inventory."""
        self.countdown_label = QtWidgets.QLabel('ready', self)
        font = self.countdown_label.font()
        font.setPointSize(28)
        self.countdown_label.setFont(font)
        self.countdown_label.setAlignment(QtCore.Qt.AlignCenter)

        self.info_box = QtWidgets.QTextEdit(self)
        self.info_box.setReadOnly(True)

        self.elapsed_label = QtWidgets.QLabel('0:00', self)
        self.remaining_label = QtWidgets.QLabel('Remaining: -', self)

        self.pause_btn = QtWidgets.QPushButton('Pause', self)
        self.pause_btn.setCheckable(True)
        self.restart_btn = QtWidgets.QPushButton('Restart', self)

        self.hint_label = QtWidgets.QLabel(
            'Click Start on the Setup tab. Steer with arrow keys; '
            'click the 3D viewer first if keys seem dead.', self)
        self.hint_label.setWordWrap(True)

    def _build_layout(self):
        """VBox[countdown, info(stretch), status row, button row, hint]."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.countdown_label)
        layout.addWidget(self.info_box, 1)  # stretch: info box grows

        row = QtWidgets.QHBoxLayout()
        row.addWidget(QtWidgets.QLabel('Elapsed:', self))
        row.addWidget(self.elapsed_label)
        row.addStretch(1)
        row.addWidget(QtWidgets.QLabel('Molecules', self))
        row.addWidget(self.remaining_label)
        layout.addLayout(row)

        btn_row = QtWidgets.QHBoxLayout()
        btn_row.addWidget(self.pause_btn)
        btn_row.addWidget(self.restart_btn)
        btn_row.addStretch(1)
        layout.addLayout(btn_row)

        layout.addWidget(self.hint_label)

    def _wire_signals(self):
        """Connect widget signals to handlers."""
        self.pause_btn.toggled.connect(self._on_pause_toggled)
        self.restart_btn.clicked.connect(self._on_restart)

    # --- session lifecycle -------------------------------------------------

    def begin_game(self, setup):
        """Start a new game from the setup dict (GAME-01).

        Called by PluginDialog (plan 04-06) and by Restart. Tears down
        any live session FIRST (restart-mid-game and reload-mid-game
        paths, research Pitfall A/12), restores the head's canonical
        edge-on pose + origin centering when the scene has one (turn
        sweeps rotate the head's atomic coords; Restart must return
        pose AND center so the object matches the engine's fresh
        (0,0)/'right' state), builds a deterministic engine seeded with
        the first spawn-mod pickup (plan 05-11), anchors the session
        with the pure head mirror + spawn state, materializes the
        pickup object edge-on as sticks, frames ONCE (the 03-06
        one-shot contract - NEVER per-tick), then runs the
        epoch-guarded countdown. The movement tick starts at
        _begin_play (after GO!).
        """
        self._teardown_round()  # timers, epoch, input, camera (ONE helper)
        self.info_box.clear()
        records = []
        if self._anchor is not None:
            records = getattr(self._anchor, 'records', None) or []
        records_by_id = dict((r['id'], r) for r in records)
        self._reset_head_viewer(records_by_id, setup)
        engine, extras = self._build_engine(setup)
        self._session = {
            'engine': engine,
            'epoch': self._epoch,   # recorded AFTER the teardown bump
            'start_time': None,     # set at _begin_play
            'paused_accum': 0.0,
            'status': 'countdown',
            # Phase 5 (plan 05-11): pure mirror + spawn/session state.
            'head_atoms': extras['head_atoms'],
            'head_stack_ring': extras['head_stack_ring'],
            'records_by_id': extras['records_by_id'],
            'spawner': extras['spawner'],
            'stacked_history': [],
            'live_pickup_names': [],
            'last_turn_delta': 0.0,
        }
        if self._anchor is not None:
            self._anchor.game_session = self._session
        # Materialize the seeded pickup(s) edge-on as sticks (GAME-03) -
        # AFTER the session exists (live_pickup_names tracks them),
        # BEFORE the countdown (the scene must be complete at GO!).
        for seed in engine.pickups:
            record = records_by_id[seed['molecule_id']]
            name = 'srp_pickup_%s' % seed['id']
            pymol_bridge.materialize_pickup(
                record['file'], name,
                self._pickup_m16(record, seed['centroid']))
            self._session['live_pickup_names'].append(name)
        pymol_bridge.frame_scene()  # ONE-SHOT framing (03-06 contract)
        self._log('Get ready...')
        self.restart_btn.setEnabled(True)
        self._run_countdown(3)

    def _build_engine(self, setup):
        """Seed a deterministic GameEngine + the session mirrors.

        head (0,0) matches the bridge's origin centering; heading
        'right'; box from setup_logic.BOX_PRESETS; cap/atom_budget from
        the setup dict. Phase 5 (plan 05-11): the FIRST pickup is
        spawned deterministically - spawn_mod.PickupSpawner seeded by
        crc32(setup) over the anchored records - and passed to
        GameEngine(pickups=[seed]) so the capture leg has a live target;
        begin_game then materializes the matching viewer object. With
        no records anchored the game degrades to pickups=None (playable
        but nothing to capture) instead of crashing. (The dataset half,
        _anchor.stacking_data, is consumed by the 05-13 'stacked' seam
        straight from the anchor.)

        Returns (engine, extras); extras carries the session-folded
        state: 'head_atoms' (the pure viewer mirror, or None),
        'head_stack_ring' (or None), 'records_by_id' (dict), 'spawner'
        (or None). begin_game turns it into the session dict keys.
        """
        (x0, y0), (x1, y1) = setup_logic.BOX_PRESETS[setup['box_preset']]
        extras = {'head_atoms': None,
                  'head_stack_ring': None,
                  'records_by_id': {},
                  'spawner': None}
        pickups = None
        records = []
        if self._anchor is not None:
            records = getattr(self._anchor, 'records', None) or []
        if not records:
            self._log('no records anchored - play without pickups')
        else:
            records_by_id = dict((r['id'], r) for r in records)
            extras['records_by_id'] = records_by_id
            extras['head_atoms'], extras['head_stack_ring'] = (
                self._build_head_state(records_by_id, setup))
            atoms_by_id = dict((r['id'], self._mirror_atoms(r))
                               for r in records)
            spawner = spawn_mod.PickupSpawner(
                records, (x0, y0), (x1, y1),
                spawn_mod.seed_from_setup(setup), atoms_by_id)
            extras['spawner'] = spawner
            # heading NAME: the spawner's contract is 'right' etc., not a
            # unit vector (spawn.py _DIRS keying).
            result = spawner.first((0.0, 0.0), 'right')
            if result is not None:
                record, pid, centroid = result
                seed = spawn_mod.build_pickup_seed(
                    record, pid, centroid, atoms_by_id[record['id']])
                pickups = [seed]
        engine = game_engine.GameEngine(
            head=(0.0, 0.0), heading='right',
            box_min=(x0, y0), box_max=(x1, y1),
            pickups=pickups,
            cap=setup.get('win_cap_molecules'),
            atom_budget=setup.get('atom_budget'))
        return (engine, extras)

    def _build_head_state(self, records_by_id, setup):
        """The PURE head mirror: (head_atoms, head_stack_ring) / (None, None).

        Selects the head record the SAME way materialize does
        (pymol_bridge._select_head_record; errors discarded - Apply
        already surfaced them). Returns (None, None) when the scene has
        no head (box-only Apply) or the record has no stack_ring
        (uploads degrade flat, matching the Apply path). head_atoms are
        edge_on_atoms EXTENT-CENTERED in pure math - the exact pose
        edge_on_m16 + place_head gives srp_head - so mirror == viewer.
        """
        record = pymol_bridge._select_head_record(
            setup, list(records_by_id.values()), [])
        if record is None or 'stack_ring' not in record:
            return (None, None)
        parsed = _read_record(record['file'])
        atoms = orientation.edge_on_atoms(
            parsed['elements'], parsed['coords'], record['stack_ring'])
        return (_extent_center(atoms), record['stack_ring'])

    def _reset_head_viewer(self, records_by_id, setup):
        """Restore srp_head's canonical edge-on pose, then re-center it.

        The Restart pose reset: turn sweeps rotate the head's ATOMIC
        coords in the viewer, so every begin_game must re-apply
        edge_on_m16 BEFORE place_head - otherwise a restarted round
        would keep the swept pose while the engine heads 'right'. No-op
        when the scene has no head object; a record without stack_ring
        (uploads) gets the bare place_head centering (the Apply path's
        head_m16=None parity).
        """
        if not pymol_bridge.object_exists(pymol_bridge.HEAD_NAME):
            return
        record = pymol_bridge._select_head_record(
            setup, list(records_by_id.values()), [])
        if record is not None and 'stack_ring' in record:
            parsed = _read_record(record['file'])
            pymol_bridge.apply_matrix(
                pymol_bridge.HEAD_NAME,
                orientation.edge_on_m16(
                    parsed['elements'], parsed['coords'],
                    record['stack_ring']))
        pymol_bridge.place_head(pymol_bridge.HEAD_NAME)

    def _mirror_atoms(self, record):
        """Origin-centered (sym, x, y, z) mirror atoms for ONE record.

        The spawner/engine truth for this molecule BEFORE the spawn
        centroid translate. Records WITH stack_ring (demo):
        edge_on_atoms (ring centroid at origin - the exact pose
        materialize_pickup's m16 puts in the viewer). Records WITHOUT
        (uploads): stored coords extent-centered, matching
        _pickup_m16's identity-rotation fallback, so the spawner's
        per-atom clearance leg stays truthful for upload pickups too.
        """
        parsed = _read_record(record['file'])
        if 'stack_ring' in record:
            return orientation.edge_on_atoms(
                parsed['elements'], parsed['coords'], record['stack_ring'])
        atoms = [(sym, float(p[0]), float(p[1]), float(p[2]))
                 for sym, p in zip(parsed['elements'], parsed['coords'])]
        return _extent_center(atoms)

    def _pickup_m16(self, record, centroid):
        """The ONE 16-float TTT landing a pickup edge-on at a spawn centroid.

        orientation.matrix_rt(R_edge, (cx, cy, 0.0), pre) per
        materialize_pickup's caller contract - the exact transform
        whose result _mirror_atoms + build_pickup_seed mirror purely.
        Records without stack_ring (uploads) use an identity rotation
        with the extent-center pre-shift (stored pose centered at the
        spawn point, the same fallback _mirror_atoms uses).
        """
        cx, cy = centroid
        parsed = _read_record(record['file'])
        if 'stack_ring' in record:
            rotation, pre = orientation.edge_on_frame(
                parsed['elements'], parsed['coords'], record['stack_ring'])
            return orientation.matrix_rt(rotation, (cx, cy, 0.0), pre)
        atoms = [(sym, float(p[0]), float(p[1]), float(p[2]))
                 for sym, p in zip(parsed['elements'], parsed['coords'])]
        ox, oy, oz = _extent_offset(atoms)
        identity = ((1.0, 0.0, 0.0),
                    (0.0, 1.0, 0.0),
                    (0.0, 0.0, 1.0))
        return orientation.matrix_rt(identity, (cx, cy, 0.0),
                                     (-ox, -oy, -oz))

    # --- countdown (epoch-guarded singleShot chain) ------------------------

    def _run_countdown(self, n):
        """3-2-1-GO! via a recursive singleShot(1000, ...) chain.

        Every scheduled callback closes over ``scheduled =
        self._epoch`` AT SCHEDULE TIME and no-ops if the epoch has
        moved on (Pitfall 9.1: singleShot chains cannot be cancelled;
        a Start/Restart during the countdown must not fire a second
        _begin_play).
        """
        scheduled = self._epoch
        if n > 0:
            self.countdown_label.setText(str(n))
            self._log(str(n))
            QtCore.QTimer.singleShot(
                1000, lambda: self._countdown_step(n - 1, scheduled))
        else:
            self.countdown_label.setText('GO!')
            self._log('GO!')
            self._begin_play(scheduled)

    def _countdown_step(self, n, scheduled):
        if scheduled != self._epoch:
            return  # stale chain - teardown bumped the epoch
        self._run_countdown(n)

    def _begin_play(self, scheduled):
        """GO!: arm lock + steering, then start the timers (gameloop Q6).

        Order matters: lock_camera + input install BEFORE the timers so
        the first tick is already locked/steerable (GAME-02 + GAME-03
        arm together at the same instant). Everything runs on the GUI
        thread (gameloop Q1/T4) - no marshaling.
        """
        if scheduled != self._epoch:
            return  # stale countdown chain
        session = self._session
        session['start_time'] = time.time()
        session['status'] = 'playing'
        session['saved_cam'] = pymol_bridge.lock_camera()  # GAME-02 lock
        self._input_handle = game_input.install(
            session['engine'].request_direction)           # GAME-03 steering
        self._tick_timer.start()
        self._elapsed_timer.start()
        self._update_remaining()
        self.pause_btn.setEnabled(True)
        self._log('Move with the arrow keys.')

    # --- tick + elapsed ----------------------------------------------------

    def _on_tick(self):
        """100 ms movement tick: engine.step + bridge head movement."""
        session = self._session
        if session is None or session['epoch'] != self._epoch:
            return  # no session / stale (post-teardown)
        engine = session['engine']
        if engine.paused or engine.finished:
            return
        old = engine.head
        events = engine.step(TICK_DT)
        moved = False
        for ev in events:
            if ev[0] == 'moved':
                moved = True
            else:
                self._handle_event(ev, engine)
        if moved:
            # Engine truth, drift-free (gameloop M3): the delta is the
            # engine's own increment; engine.head is the last moved pos.
            nx, ny = engine.head
            dx = nx - old[0]
            dy = ny - old[1]
            pymol_bridge.move_head_delta(dx, dy, 0.0)
            # Keep the PURE head mirror exactly equal to the viewer's
            # srp_head coordinates (plan 05-11): the SAME delta, applied
            # in pure math - no readback, no drift.
            if session['head_atoms'] is not None:
                session['head_atoms'] = [
                    (sym, x + dx, y + dy, z)
                    for (sym, x, y, z) in session['head_atoms']]
        self._update_remaining()
        if engine.finished:
            self._end_run(engine)

    def _handle_event(self, ev, engine):
        """Route one engine event to the info box (or the Phase-5 seams).

        'moved' is silent in the log (too chatty at 10 Hz, research
        Q2); 'turning' ALSO stays log-silent but is not silent in the
        viewer - the GAME-10 viewer half (plan 05-14) renders the
        engine's rigid sweep there (see _handle_turn_event).
        'stacked' funnels into _handle_stack_event (the Phase-5 capture
        seam, plan 05-13) - it arrives BEFORE 'budget_warning' and
        'won' in the engine's pinned per-tick event order, so a
        clash-refused cap capture has already un-finished the engine
        (plan 05-04) when 'won' is dispatched next; the 'won' branch
        therefore logs only if engine.finished still holds (a false
        YOU WIN is impossible by construction). 'budget_warning' (plan
        05-14) logs the count-FREE advisory (GAME-04 hidden counts:
        the payload's atoms_total is deliberately NOT displayed; the
        number reappears only at completion via completion_lines).
        """
        kind = ev[0]
        if kind == 'turn_refused':
            self._log('turn refused: %s' % ev[1])
        elif kind == 'turning':
            self._handle_turn_event(engine)
        elif kind == 'stacked':
            self._handle_stack_event(ev[1], engine)
        elif kind == 'crashed':
            self._log('crashed into %s' % ev[1])
        elif kind == 'budget_warning':
            self._log(hud_logic.budget_text())
        elif kind == 'won':
            if engine.finished:
                self._log('YOU WIN')

    # --- Phase-5 sweep rendering (plan 05-14, GAME-10 viewer half) ---------

    def _handle_turn_event(self, engine):
        """Render ONE ('turning',) tick of the engine's rigid sweep.

        The engine owns ALL sweep math/time (locked decision: engine
        emits ('turning', frac); the GUI adds ONE rotation call per
        tick - 05-RESEARCH-pymol-mechanics Pattern 5). Per tick:

        1. delta = sweeping['angle_signed'] / sweeping['total_ticks']
           (= +/-15 deg) while engine.sweeping is not None. The FINAL
           sweep tick is the exception: _advance_sweep clears
           sweeping BEFORE the event list is handled, so tick 6 comes
           back from session['last_turn_delta'] (stored on EVERY
           non-None path - the tick-5 value is the same +/-15 deg,
           so the final 15-degree step still rotates).
        2. ONE pymol_bridge.sweep_chain(delta, engine.head) call -
           cmd.rotate('z', delta, 'srp_head or srp_seg_*', camera=0,
           origin=[hx, hy, 0]): the WHOLE chain sweeps as a rigid body
           about the head pivot; srp_head is INCLUDED so it spins in
           place and its ring normal follows the chain (Pattern 2,
           probe-verified; origin= is mandatory, pitfall P5-4).
           Sign comes from the engine (delta > 0 = CCW, matching
           _rotate_xy).
        3. The PURE head mirror rotates by the SAME delta with the
           SAME game_engine._rotate_xy primitive about
           (head[0], head[1]); z and sym preserved exactly (the way
           _advance_sweep treats segments) - pure truth == viewer
           truth for the next tail frame and the clash gate.

        No collision logic here (pre-checked at sweep open - engine
        contract); no second timer (the sweep tick IS the movement
        tick); pause mid-sweep needs nothing (timers stop, engine
        retains sweeping, resume continues). NO info-box line per
        tick (existing chattiness policy - the sweep is visible in
        the viewer).
        """
        session = self._session
        sweep = engine.sweeping
        if sweep is not None:
            delta = sweep['angle_signed'] / float(sweep['total_ticks'])
            session['last_turn_delta'] = delta
        else:
            # Final sweep tick: engine cleared sweeping; reuse the
            # stored per-tick delta (same signed 15-degree step).
            delta = session['last_turn_delta']
        pymol_bridge.sweep_chain(delta, engine.head)  # ONE cmd call
        head_atoms = session['head_atoms']
        if head_atoms is not None:
            hx, hy = engine.head
            cos_t = math.cos(math.radians(delta))
            sin_t = math.sin(math.radians(delta))
            session['head_atoms'] = [
                (sym,) + game_engine._rotate_xy(x, y, hx, hy, cos_t, sin_t)
                + (z,)
                for (sym, x, y, z) in head_atoms]

    # --- Phase-5 capture seam (plan 05-13) -----------------------------------

    def _handle_stack_event(self, pickup_rec, engine):
        """The 'stacked' capture seam - the Phase-5 connector.

        ONE synchronous resolution per ('stacked', pickup) event, a
        line-by-line GUI transcription of tests/test_phase5_integration.
        py's capture() helper - SAME ORDER: skip -> tail -> place ->
        gate (all inside placement.resolve) -> attach/reject:

          placed  -> engine.attach_segment (counter-neutral; the
                     capture already counted), viewer transform
                     (orientation.matrix_rt(R, t) via bridge), rename
                     'srp_pickup_<id>' -> 'srp_seg_<n>' (the srp_
                     prefix contract: cleanup_srp + delete_pickups
                     only ever see game objects), STACK-04 structured
                     pickup block, stacked_history entry.
          skipped/refused -> engine.reject_pickup ALWAYS (locked
                     decision 13 - the capture already incremented
                     the counters, and the un-finish fix from plan
                     05-04 lives on this path, so counters can never
                     desync), then the educator-readable reason line.
                     A refused pickup's viewer object stays VISIBLE
                     (reject re-arms it), and hud_logic.resume_note
                     records the G2 un-finish for the player.

        After EVERY resolution (success or refusal, plan 05-03 spawn
        policy) the respawn gate runs: at most ONE new spawn per
        resolution, gated by MAX_LIVE_PICKUPS. The engine has no
        spawn API; the controller extends the seeded pickups list /
        live id set / remaining counter exactly as reset() would
        have - same record shape, engine-owned thereafter.

        The whole body is wrapped in try/except -> 'placement error'
        + reject_pickup(id, 'error') as the last-resort counter
        guard (a capture may never dangle). A segment already
        attached is never rolled back (attach == counted == tracked:
        rejecting there would DESYNC the counters it guards).
        Viewer-read discipline: placement decides in PURE math from
        the session/engine mirrors; the ONLY cmd calls here are
        transform/rename/materialize WRITES (research Never-do list).
        """
        session = self._session
        attached = False
        try:
            records_by_id = session['records_by_id']
            stacking_data = None
            if self._anchor is not None:
                stacking_data = getattr(self._anchor, 'stacking_data', None)
            head_atoms = session['head_atoms'] or []
            head_stack_ring = session['head_stack_ring']
            display_z = pymol_bridge.BOX_DISPLAY_Z
            # Resolution-time enrichment: the engine pickup record
            # carries only the seed keys; placement's skip taxonomy
            # needs the record's stack_ring / has_stack_entry / set
            # (the test seam's pickup_seed carries them on the seed;
            # enriching here from records_by_id keeps ONE truth and
            # covers begin_game-seeded pickups identically).
            record = records_by_id[pickup_rec['molecule_id']]
            resolve_rec = dict(pickup_rec)
            if 'stack_ring' in record:
                resolve_rec['stack_ring'] = list(record['stack_ring'])
            resolve_rec['has_stack_entry'] = record.get('has_stack_entry')
            resolve_rec['set'] = record.get('set')
            # Locked clash-gate set (plan 05-05): head + ALL segment
            # atoms + OTHER live pickups' atoms (own atoms excluded).
            existing_atoms = list(head_atoms)
            for seg in engine.segments:
                existing_atoms.extend(seg['atoms'])
            for p in engine.pickups:
                if (p['id'] in engine.live_pickup_ids
                        and p['id'] != pickup_rec['id']):
                    existing_atoms.extend(p['atoms'])
            outcome = placement.resolve(
                resolve_rec, records_by_id, stacking_data,
                head_atoms, head_stack_ring, engine.heading,
                engine.segments, existing_atoms,
                engine.box_min, engine.box_max, display_z)
            name = record['name']
            if outcome['status'] == 'placed':
                engine.attach_segment(pickup_rec['molecule_id'],
                                      outcome['ring_centroid_xy'],
                                      outcome['placed_atoms'])
                attached = True
                old_name = 'srp_pickup_%s' % pickup_rec['id']
                m16 = orientation.matrix_rt(outcome['R'], outcome['t'])
                pymol_bridge.apply_matrix(old_name, m16)
                # len(engine.segments) AFTER attach -> 1-based index
                # (smoke 07 verified cmd.set_name live).
                new_name = 'srp_seg_%d' % len(engine.segments)
                pymol_bridge.rename_pickup(old_name, new_name)
                if old_name in session['live_pickup_names']:
                    session['live_pickup_names'].remove(old_name)
                session['stacked_history'].append({
                    'name': name,
                    'outcome': 'stacked',
                    'distance_a': outcome['interaction']['distance_a'],
                    'citation_short': outcome['citation_short'],
                    'interaction_id': outcome['interaction']['id'],
                })
                self._log(hud_logic.pickup_block(
                    name, outcome['interaction'], outcome['citation_short']))
            else:
                code = outcome['code']
                # reject_pickup on EVERY non-placed outcome (locked
                # decision 13): capture counters roll back, pickup
                # re-arms, a cap-reaching 'won' un-finishes (05-04).
                engine.reject_pickup(pickup_rec['id'], code)
                self._log(hud_logic.reason_text(
                    code, outcome.get('detail'), name))
                session['stacked_history'].append({
                    'name': name, 'outcome': code})
                if outcome['status'] == 'refused':
                    # The viewer object stays VISIBLE (re-armed) and
                    # the run continues - the G2 un-finish line.
                    self._log(hud_logic.resume_note(name))
            self._respawn_pickup(session, engine)
        except Exception as exc:
            self._log('placement error: %s' % exc)
            if not attached:
                # Last-resort counter guard: never leave a capture
                # dangling. Skipped when the segment already attached
                # (rolling back there would desync the counters).
                engine.reject_pickup(pickup_rec['id'], 'error')

    def _respawn_pickup(self, session, engine):
        """The ONE-spawn-per-resolution respawn gate (plan 05-03).

        At most one new pickup per resolution, gated by the spawner's
        MAX_LIVE_PICKUPS ceiling. The engine has no spawn API, so the
        controller APPENDS the seed dict to engine.pickups, adds the
        pid to engine.live_pickup_ids and bumps
        engine.pickups_remaining - the exact engine-owned state
        GameEngine(pickups=[seed]) builds at reset() (same record
        shape, unknown keys carried through engine copies). The
        viewer object materializes edge-on as sticks at the spawn
        centroid ('m16 from edge_on + centroid', the same _pickup_m16
        begin_game uses) and registers in live_pickup_names.
        """
        spawner = session['spawner']
        if spawner is None:
            return
        if not spawner.can_spawn(len(engine.live_pickup_ids)):
            return
        chain_atoms = list(session['head_atoms'] or [])
        for seg in engine.segments:
            chain_atoms.extend(seg['atoms'])
        live_centroids = [p['centroid'] for p in engine.pickups
                          if p['id'] in engine.live_pickup_ids]
        result = spawner.next_after(
            engine.head, _heading_name(engine.heading),
            chain_atoms, live_centroids)
        if result is None:
            return  # no legal position: NO state advance (05-03)
        record, pid, centroid = result
        seed = spawn_mod.build_pickup_seed(
            record, pid, centroid, self._mirror_atoms(record))
        if 'stack_ring' in record:
            seed['stack_ring'] = list(record['stack_ring'])
        seed['has_stack_entry'] = record.get('has_stack_entry')
        seed['set'] = record.get('set')
        engine.pickups.append(seed)
        engine.live_pickup_ids.add(pid)
        engine.pickups_remaining += 1
        name = 'srp_pickup_%s' % pid
        pymol_bridge.materialize_pickup(
            record['file'], name, self._pickup_m16(record, centroid))
        session['live_pickup_names'].append(name)

    def _on_elapsed_tick(self):
        """1 Hz elapsed refresh - delta-based, NEVER accumulated (Pitfall 5).

        Recomputes from the WALL CLOCK every second:
        time.time() - start_time - paused_accum, clamped >= 0. Pause
        seconds are excluded via the Pitfall 9.3 rebase in
        _on_pause_toggled.
        """
        session = self._session
        if session is None or session['epoch'] != self._epoch:
            return
        if session['start_time'] is None:
            return  # still in countdown
        elapsed = (time.time() - session['start_time']
                   - session['paused_accum'])
        if elapsed < 0.0:
            elapsed = 0.0
        self.elapsed_label.setText(hud_logic.format_elapsed(elapsed))

    def _update_remaining(self):
        """Refresh the molecules-remaining label (GAME-07)."""
        session = self._session
        if session is None:
            self.remaining_label.setText('Remaining: -')
            return
        self.remaining_label.setText(
            hud_logic.remaining_text(session['engine'].molecules_remaining))

    # --- pause / restart / end ---------------------------------------------

    def _on_pause_toggled(self, checked):
        """Thin guard: needs a live session; delegates to _apply_pause_state.

        The SAME tick-timer instance is stop()/start()ed (never a new
        timer - Pitfall 9.1 double-timer variant).
        """
        if self._session is None:
            return
        self._apply_pause_state(bool(checked))

    def _apply_pause_state(self, paused):
        """Pause/resume mechanics shared with request_auto_pause.

        Pause: freeze the tick + elapsed refresh, engine.pause(), gate
        steering (game_input.set_active(False) - the wizard STAYS
        installed but grabs-and-no-ops, so paused arrows neither steer
        nor step movie frames, input research open-q 5 resolution).
        Resume: rebase elapsed (Pitfall 9.3), engine.resume(), re-arm
        steering AFTER the paused_accum rebase. The camera is NOT
        touched on pause - it stays LOCKED (research D5: unlocking
        would let the user rotate a frozen scene).
        """
        session = self._session
        engine = session['engine']
        if paused:
            engine.pause()
            self._tick_timer.stop()
            self._elapsed_timer.stop()
            session['_pause_time'] = time.time()
            session['status'] = 'paused'
            game_input.set_active(False)  # grab-and-no-op, wizard stays
            self.pause_btn.setText('Resume')
            self._log('paused')
        else:
            pause_time = session.pop('_pause_time', None)
            if pause_time is not None:
                session['paused_accum'] += time.time() - pause_time
            game_input.set_active(True)   # re-arm steering after rebase
            engine.resume()
            self._tick_timer.start()
            self._elapsed_timer.start()
            session['status'] = 'playing'
            self.pause_btn.setText('Pause')
            self._log('resumed')

    def request_auto_pause(self):
        """Q3 focus-stealing mitigation (input research Q3 (b)).

        Called by PluginDialog.focusInEvent: fires on ANY dialog focus
        gain (including the Start click), but guards on
        status == 'playing' so countdown/idle/over states are
        unaffected. blockSignals prevents the programmatic setChecked
        from re-entering _on_pause_toggled (Pitfall G). The snake can
        no longer crash unattended while the user reads the HUD.
        """
        session = self._session
        if session is None or session.get('status') != 'playing':
            return
        self.pause_btn.blockSignals(True)
        self.pause_btn.setChecked(True)
        self.pause_btn.blockSignals(False)
        self._apply_pause_state(True)
        self._log('auto-paused (dialog took focus - click Resume, '
                  'then the 3D viewer)')

    def _on_restart(self):
        """Restart mid-game (GAME-07): deterministic re-run of the countdown.

        Needs a live session AND the anchored setup dict. begin_game
        re-runs teardown, so a mid-countdown Restart dies by the epoch
        guard (no double timer, Pitfall 9.1).
        """
        if self._session is None:
            return
        setup = self._anchor.setup if self._anchor is not None else None
        if setup is None:
            self._log('restart needs a setup dict')
            return
        self._teardown_round()
        self.begin_game(setup)

    def _end_run(self, engine):
        """End the run: log the verdict, then tear down via the ONE helper.

        The verdict is logged FIRST so it stays visible in the info box;
        timers/input/camera then die with the run via _teardown_round.
        """
        if self._session is not None:
            self._session['status'] = 'over'
        self._log('run over: %s' % (engine.result or 'over'))
        self._teardown_round()

    def shutdown(self):
        """dialog-close hook (PluginDialog.closeEvent) - every end path
        funnels here (Pitfall 9.2)."""
        self._teardown_round()

    def _teardown_round(self):
        """THE single teardown helper (Pitfall 9.2), idempotent.

        Called by EVERY end path (begin_game restart/first-start,
        _end_run crash/won, dialog close via shutdown()): (a) stop both
        timers; (b) bump the epoch (kills stale singleShot chains);
        (c) input teardown (teardown(handle) accepts-and-IGNORES on the
        wizard route - uniform with the fallback route, input research
        Q5); (d) camera restore - read the CURRENT session BEFORE it
        could be replaced/nulled, and pop saved_cam so a double-touch
        unlock is impossible by construction; (e) the pause button is
        reset PROGRAMMATICALLY under blockSignals (Pitfall G: a naked
        setChecked(False) would fire toggled and trigger a spurious
        resume on a dead/rebuilt engine); (f) pickup cleanup (plan
        05-11): pattern-delete srp_pickup_* - un-stacked pickups die on
        EVERY end path while srp_head/srp_seg_* are untouched, folded
        INTO this ONE helper per locked decision 8 (never a second
        helper); idempotent like the unlock, needed by restart AND by
        the completion flow's 'viewer clears' semantics.
        """
        self._tick_timer.stop()
        self._elapsed_timer.stop()
        self._epoch += 1  # any in-flight singleShot now no-ops
        handle = getattr(self, '_input_handle', None)
        game_input.teardown(handle)
        self._input_handle = None
        session = self._session
        if session is not None:
            pymol_bridge.unlock_camera(session.pop('saved_cam', None))
        pymol_bridge.delete_pickups()  # (f) live pickups die here, chain stays
        self.pause_btn.blockSignals(True)
        self.pause_btn.setChecked(False)
        self.pause_btn.setText('Pause')
        self.pause_btn.setEnabled(False)
        self.pause_btn.blockSignals(False)

    # --- misc ---------------------------------------------------------------

    def _log(self, msg):
        """Append one line to the read-only rolling info box."""
        self.info_box.append(str(msg))

    def _set_idle_state(self):
        """Idle HUD: nothing to pause or restart until a game begins."""
        self.pause_btn.setEnabled(False)
        self.restart_btn.setEnabled(False)
