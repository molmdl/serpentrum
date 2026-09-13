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
plan 04-06; pickups/stacking/win-handoff are Phase 5 (the engine is
seeded with pickups=None here).

Purity class: GUI (pymol.Qt ONLY at module level - the check_purity
GUI_MODULES entry landed in plan 04-01; relative imports of the pure
and bridge modules are exempt; PyQt5/numpy banned). The bridge owns
all viewer-command access - this module NEVER imports pymol directly.
Blocking modal-run calls are BANNED everywhere (modeless rule): no
modals in this tab, the info box shows verdicts. python3.6 syntax
(%-formatting).

Reload model (Pitfall 7/8): the two QTimers are Qt-parent-owned by this
widget and die with it on a Plugin-Manager reload; the game SESSION dict
(engine + epoch + start_time + paused_accum + status) anchors on
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

import time

from pymol.Qt import QtWidgets, QtCore

from . import game_engine
from . import hud_logic
from . import pymol_bridge
from . import setup_logic
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


class GameTab(QtWidgets.QWidget):
    """The Game tab HUD.

    Built by PluginDialog as page 1 (plan 04-06 wires it in and calls
    begin_game on Start). Owns the tick + elapsed QTimers (Qt parent
    ownership - they die with the widget). The session dict anchors on
    _serpentrum.game_session so a Plugin-Manager reload cannot
    duplicate it; every singleShot/timeout callback is epoch-guarded
    (Pitfall 9.1).
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
        paths, research Pitfall A/12), re-centers the head object when
        the scene has one (Restart must return the head to origin - the
        engine resets to (0,0) and the object must match), builds a
        deterministic engine from the setup dict, anchors the session,
        then runs the epoch-guarded countdown. The movement tick starts
        at _begin_play (after GO!).
        """
        self._teardown_round()  # timers, epoch, input, camera (ONE helper)
        if pymol_bridge.object_exists(pymol_bridge.HEAD_NAME):
            pymol_bridge.place_head(pymol_bridge.HEAD_NAME)
        engine = self._build_engine(setup)
        self._session = {
            'engine': engine,
            'epoch': self._epoch,   # recorded AFTER the teardown bump
            'start_time': None,     # set at _begin_play
            'paused_accum': 0.0,
            'status': 'countdown',
        }
        if self._anchor is not None:
            self._anchor.game_session = self._session
        self.info_box.clear()
        self._log('Get ready...')
        self.restart_btn.setEnabled(True)
        self._run_countdown(3)

    def _build_engine(self, setup):
        """Seed a deterministic GameEngine from the setup dict.

        head (0,0) matches the bridge's origin centering; heading
        'right'; box from setup_logic.BOX_PRESETS; Phase-4 seeds
        pickups=None (Phase 5 adds pickups; 'won' stays unreachable);
        cap/atom_budget from the setup dict.
        """
        (x0, y0), (x1, y1) = setup_logic.BOX_PRESETS[setup['box_preset']]
        return game_engine.GameEngine(
            head=(0.0, 0.0), heading='right',
            box_min=(x0, y0), box_max=(x1, y1),
            pickups=None,
            cap=setup.get('win_cap_molecules'),
            atom_budget=setup.get('atom_budget'))

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
            pymol_bridge.move_head_delta(nx - old[0], ny - old[1], 0.0)
        self._update_remaining()
        if engine.finished:
            self._end_run(engine)

    def _handle_event(self, ev, engine):
        """Route one engine event to the info box (or silence).

        'moved'/'turning' are silent (too chatty at 10 Hz, research
        Q2). 'won' is unreachable in Phase 4 (pickups=None) and kept
        for Phase 5.
        """
        kind = ev[0]
        if kind == 'turn_refused':
            self._log('turn refused: %s' % ev[1])
        elif kind == 'crashed':
            self._log('crashed into %s' % ev[1])
        elif kind == 'won':
            self._log('YOU WIN')

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
        resume on a dead/rebuilt engine).
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
