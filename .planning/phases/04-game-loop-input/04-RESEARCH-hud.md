# Phase 4 (Game Loop & Input) — Research: Game Tab HUD + State Wiring

**Aspect:** Qt Game tab HUD (countdown, rolling info box, elapsed timer, molecules-remaining, pause/resume, restart) + Start→Game-tab transition + state wiring between GUI, pure engine, and pymol_bridge.
**Researched:** 2026-09-12
**Domain:** PyQt5 (via `pymol.Qt`) tab/widget/timer patterns + anchored session state + engine↔GUI seam
**Confidence:** HIGH for codebase-pattern claims (every claim read directly from serpentrum/ + bioCHEMeleon shipped code + research docs with file:line); GUI verdicts are human-verify-only by repo decision (01-05 dead end).

**Bottom line (one line):** The Game tab is a new `serpentrum/gui_game.py` (`GameTab(QWidget)`, GUI purity class) added to `GUI_MODULES`, replacing the page-1 placeholder in `gui.py`; it owns a 100 ms movement-tick QTimer + a 1 Hz elapsed-label QTimer + an epoch-guarded recursive-singleShot 3-2-1 countdown, a read-only QTextEdit info box, a molecules-remaining label querying `engine.cap - engine.molecules_stacked`, and pause/resume + restart buttons; the game SESSION (engine + epoch + start_time) anchors on a NEW `_serpentrum.game_session` field (mirrors the setup-dict anchor) — never module globals, never the widget; **no engine API additions are needed for the HUD** (it reads existing public attrs), and **no Start button and no controller.py exist yet** (both are Phase 4 deliverables — a temporary Start button follows the Phase 3 temp-button precedent; a separate controller is optional for Phase 4's scope).

---

## ANSWER (recommendations first, with confidence labels)

Labels: `[VERIFIED-source]` = read today from serpentrum/, PyMOL source, or bioCHEMeleon shipped code (file:line cited). `[VERIFIED-empirical]` = run in this environment. `[ASSUMPTION-needs-human-verify]` = inference, not yet verified.

### Q1. Start → Game tab transition

**There is NO Start button yet.** `[VERIFIED-source: serpentrum/gui_setup.py:127-129 (only temp `apply_btn`/`cleanup_btn`); serpentrum/gui.py:61-62 (bottom row = `addStretch(1)` only, comment "reserved row - no buttons in Phase 1"); REQUIREMENTS.md SETUP-07 = Phase 8]`. The canonical 6-button bottom row (Reset, Randomize, Save Setup, Load Setup, Cleanup model, Start) is Phase 8. Phase 4 must add a **temporary** Start button to satisfy GAME-01 ("Clicking Start switches to the Game tab, counts down 3-2-1").

**Recommended placement (mirrors the Phase 3 precedent):** a temporary `start_btn = QPushButton('Start')` **inside the Setup tab** alongside the existing temporary Apply/Cleanup buttons (gui_setup.py:191-195 `btn_row`). Rationale: `[VERIFIED-source: gui_setup.py:125-130 docstring "Two TEMPORARY buttons ... live INSIDE this page -- the canonical 6-button bottom row (SETUP-07) ... stay in Phase 8"]` — Phase 3 established that in-tab temporary buttons are the accepted pattern until Phase 8's canonical row. Putting Start in the Setup tab keeps it co-located with Apply (the user Applies to materialize, then Starts to play). The bottom reserved row in gui.py stays untouched (Phase 8 owns it).

**Tab-switch mechanism (exact Qt call):** `self.tabs.setCurrentIndex(1)` — Setup=0, Game=1, Spectra=2 (fixed page order). `[VERIFIED-source: serpentrum/gui.py:38-41 docstring "self.tabs (QTabWidget) is the documented handle -- setCurrentWidget(page) / setCurrentIndex(i); page order stays fixed Setup -> Game -> Spectra"; gui.py:47 `self.tabs = QtWidgets.QTabWidget(self)`]`.

**Who owns the transition:** the Start button's `clicked` handler. Two viable ownership models:
- **(A) Setup tab emits a signal, PluginDialog switches the tab** (clean separation): `SetupTab` exposes `QtCore.Signal` `start_requested`; `PluginDialog` connects it to `self.tabs.setCurrentIndex(1)` + hands the collected setup dict to the Game tab. `[VERIFIED-source: this is the Qt-idiomatic signal/slot decoupling; gui.py:43-65 PluginDialog already owns self.tabs]`.
- **(B) Setup tab calls a method on the Game tab / anchor directly** (tighter coupling).

**Recommendation: model (A).** `SetupTab` emits `start_requested(setup_dict)`; `PluginDialog.__init__` (or a small `_wire_tabs` method) connects it. The setup dict is already collected by `SetupTab.collect_state()` `[VERIFIED-source: gui_setup.py:214-243]` and anchored on `_serpentrum.setup` `[VERIFIED-source: __init__.py:28]`, so the Game tab can also read it from the anchor. The transition itself (`setCurrentIndex(1)`) lives in `PluginDialog` because that's where `self.tabs` lives — the Game tab should NOT reach up to its parent QTabWidget (fragile). `[ASSUMPTION-needs-human-verify: the signal handoff is standard Qt; the human-verify step confirms the tab actually switches on click]`.

### Q2. Game tab widget spec

Replace the page-1 placeholder with a real `GameTab(QWidget)` in a new `serpentrum/gui_game.py`. The placeholder currently comes from `_TAB_DEFS` `[VERIFIED-source: gui.py:18-25, 51-60]`; Phase 4 builds `GameTab` and inserts it as page 1 (see Code Sketches for the gui.py edit).

**Widget inventory (keep simple per spec.md "simple, user-friendly, clear but sufficient"):**

| Widget | Qt type | Purpose | Update mechanism |
|--------|---------|---------|------------------|
| Countdown label | `QLabel` (large font) | "3" → "2" → "1" → "GO!" | recursive `QTimer.singleShot(1000, ...)` chain, epoch-guarded `[VERIFIED-source: bioCHEMeleon gui_game.py:258-264]` |
| Rolling info box | `QTextEdit` (read-only) | log of events + idle tips | `append(str)` per event `[VERIFIED-source: bioCHEMeleon gui_game.py:119-120 `self._info_log.append(str(msg))`]` |
| Elapsed timer label | `QLabel` | "M:SS" | 1 Hz `QTimer` recompute from `time.time() - start_time - paused_accum` `[VERIFIED-source: bioCHEMeleon gui_game.py:108-111, 228-232]` |
| Molecules-remaining label | `QLabel` | "Remaining: N" | query `engine.cap - engine.molecules_stacked` each tick + on capture `[VERIFIED-source: engine attrs exist — game_engine.py:214-217, 264]` |
| Pause/Resume toggle | `QPushButton` (checkable) | freeze/resume | `engine.pause()`/`resume()` + stop/start tick timer + rebase start_time `[VERIFIED-source: game_engine.py:720-731]` |
| Restart button | `QPushButton` | reset to initial state | `engine.reset(...)` + epoch bump + timer restart (GAME-07) `[VERIFIED-source: game_engine.py:233-270 reset is deterministic]` |

**Elapsed-timer mechanism (purity-safe + drift-free):** a `QTimer(interval=1000)` whose `timeout` slot recomputes `elapsed = time.time() - self._start_time - self._paused_accum` and sets the label. This is **delta-based, not tick-count-accumulated** — drift-free because every update is recomputed from the wall clock. `[VERIFIED-source: bioCHEMeleon gui_game.py:229 `elapsed = time.time() - self._start_time`; PITFALLS.md Pitfall 5 "Elapsed-time math must be delta-based ... never accumulated tick counts"; ARCHITECTURE.md state-ownership map "Elapsed time | GUI (start timestamp + QTimer)"]`. `time` is stdlib; `QTimer`/`QtCore` come via `from pymol.Qt import QtCore` (GUI-class-legal). No pymol import. **On resume from pause:** rebase `self._start_time += (now - pause_time)` (or accumulate `self._paused_accum += (now - pause_time)`) so paused seconds are NOT counted — `[VERIFIED-source: PITFALLS.md Pitfall 9.3 "resume without rebase inflates elapsed time"; bioCHEMeleon gui_game.py:278 `_start_time = time.time() - elapsed` rebase pattern]`.

**Two distinct timers (critical distinction):**
- **Movement tick QTimer** at ~100 ms (dt=0.1 s passed to `engine.step(dt)`): drives the snake forward. At `SPEED_A_PER_S=3.0` this is exactly 0.3 Å/tick — the engine's own test parameter `[VERIFIED-source: game_engine.py:55-56, 585-587; test_engine_core.py:35,38 `ENGINE_ARGS`/`DELTA` use dt 0.1]`. Interval is playtesting-tunable (ARCHITECTURE.md Pattern 3 says "e.g. 250 ms"); recommend 100 ms to match the tested dt and give smooth motion.
- **Elapsed-label QTimer** at 1000 ms (1 Hz): only updates the "M:SS" label. `[VERIFIED-source: bioCHEMeleon gui_game.py:110 `setInterval(1000)`]`.

These are two separate `QTimer` instances. The movement timer is stopped on pause/crash/win; the label timer MAY keep running (it just displays frozen elapsed) but is cleaner to also stop on game-over.

**Molecules-remaining in Phase 4 (no pickups until Phase 5):** GAME-07 says "molecules-remaining-before-win" = `cap - molecules_stacked`. In Phase 4 the engine is seeded with `pickups=None` `[VERIFIED-source: game_engine.py:262-268, pickups=None → pickups_remaining=0]`, so `molecules_stacked` stays 0 and the label shows the full cap (e.g. "Remaining: 10") — frozen but correct. **The widget is built to query `engine.cap - engine.molecules_stacked`**, so Phase 5 makes it dynamic with zero rewiring (capture increments `molecules_stacked` → remaining decrements). `[VERIFIED-source: game_engine.py:699 `self.molecules_stacked += 1` on capture; ROADMAP Phase 4 criterion 4 requires the HUD element exist, NOT that winning is possible — winning needs pickups = Phase 5]`. Note: `engine.pickups_remaining` (= live pickup count) is a DIFFERENT datum and is 0 in Phase 4 — do NOT display it as "remaining before win"; use `cap - molecules_stacked`.

**Rolling info box content in Phase 4:** countdown ("3","2","1","GO!"), movement/turn start (optional — may be too chatty at 10 Hz; recommend logging only state changes: countdown, pause, resume, restart, turn-refusal, crash), idle controls hints ("use arrow keys to steer"), and end-of-run verdict. Per-pickup structured content (STACK-04) is Phase 5.

### Q3. State wiring + anchoring

**Anchor pattern (mirror the setup dict exactly):** add a `game_session = None` field to `_SerpentrumState` in `serpentrum/__init__.py`. `[VERIFIED-source: __init__.py:22-29 `_SerpentrumState` already declares `controller = None` ("the single live game controller (later phases)") — Phase 4 can reuse this field OR add `game_session`; recommend reusing `controller` since the docstring already reserves it, OR adding `game_session` for clarity. The anchor object is `pmg_tk.startup._serpentrum` and survives reload/double-import `[VERIFIED-source: __init__.py:10-30, AGENTS.md:72]`].

**Session object lifecycle (avoids reload duplication — Pitfall 7, and timer leaks — Pitfall 8/9):**

```
state.game_session (anchored on _serpentrum):
  created:  on Start click, IF None OR finished. If a live session exists,
            teardown it first (epoch bump + stop timers) — Restart-mid-game path.
  contents: {'engine': GameEngine, 'epoch': int, 'start_time': float,
             'paused_accum': float, 'status': 'countdown'|'playing'|'paused'|'over'}
  reset:    engine.reset(seeds...) + epoch+=1 + start_time=now + paused_accum=0
            (Restart button; GAME-07 deterministic restart)
  torn down: on dialog close / quit. NOT on reload (the anchor survives; the
             stale QTimer dies with the rebuilt widget; epoch guard no-ops
             any in-flight singleShot from the old widget).
```

**Why the engine anchors on `_serpentrum`, not the GameTab widget:** the widget is rebuilt on Plugin-Manager reload (the dialog is reconstructed `[VERIFIED-source: __init__.py:42-46]`); a widget-owned engine would be duplicated on reload (Pitfall 7's double-singleton). The anchored session is single-instance by construction. The QTimer, by contrast, is owned by the **widget** (Qt parent ownership: `QTimer(self)` — when the widget dies, the timer dies with it `[VERIFIED-source: standard Qt parent-child ownership; bioCHEMeleon gui_game.py:109 `self._timer = QtCore.QTimer()` with implicit self parent]`). The timer's `timeout` callback reads the anchored session's epoch and no-ops if stale — this is the Pitfall 9.1 epoch guard for singleShot chains.

**Epoch guard (mandatory — Pitfall 9.1):** `singleShot` chains CANNOT be cancelled `[VERIFIED-source: PITFALLS.md Pitfall 9.1 "singleShot chains cannot be cancelled ... leaves the old chain alive; it fires _begin_play a second time → two wizards / two timers / duplicated state"; ARCHITECTURE.md F9]`. Every `singleShot` callback (countdown steps) and every `timeout` slot closes over the epoch it was scheduled under and no-ops if `self._epoch != scheduled_epoch`. Bump epoch on every Start / Restart / teardown. `[VERIFIED-source: PITFALLS.md Pitfall 9 "Epoch counter: a monotonically increasing self._epoch; every singleShot callback closes over the epoch ... Bump epoch on every start/restart/cleanup"]`.

**blockSignals precedent (carry into GameTab):** `SetupTab._populate_head_combo` uses `self.head_combo.blockSignals(True)` around programmatic repopulation `[VERIFIED-source: gui_setup.py:382-395]`, plus the `_loading` flag as defense-in-depth `[VERIFIED-source: gui_setup.py:68, 253, 441-443]`. GameTab should mirror this for any programmatic widget state changes (e.g. toggling the Pause button label programmatically on restart).

### Q4. Engine interaction seam

**The engine's public API is COMPLETE for the Phase-4 HUD — no additions needed.** `[VERIFIED-source: serpentrum/game_engine.py — full read today]`. The HUD reads these existing attrs/methods:

| HUD need | Engine API | Verified location |
|----------|------------|-------------------|
| Advance simulation | `step(dt)` → events list | game_engine.py:560-718 |
| Steer | `request_direction(name)` | game_engine.py:311-365 |
| Pause | `pause()` (sets `paused=True`; step() no-ops) | game_engine.py:720-727 |
| Resume | `resume()` | game_engine.py:729-731 |
| Restart (GAME-07) | `reset(head, heading, segments, box_min, box_max, pickups, cap, atom_budget)` — deterministic | game_engine.py:233-270 |
| Molecules-remaining | `cap` + `molecules_stacked` attrs | game_engine.py:214-217, 264 |
| Run-over verdict | `finished` (bool) + `result` ('crashed'/'won'/None) | game_engine.py:198-202 |
| Events to log | `step()` returns `[('moved',(x,y)), ('turning',frac), ('turn_refused',reason), ('crashed','boundary'/'body'), ('stacked',pickup), ('won',), ...]` | game_engine.py:650-717 |

**Elapsed time is DELIBERATELY GUI-owned, NOT an engine gap.** `[VERIFIED-source: game_engine.py:41-46 docstring "NO RNG and NO wall-clock anywhere (pause timing is the GUI's job — Pitfall 9.3)"; ARCHITECTURE.md state-ownership map row "Elapsed time | GUI (start timestamp + QTimer)"]`. The engine is deterministic (pure float arithmetic); wall-clock lives in the GUI. This is a designed split, not a missing feature.

**Engine seeds for Phase 4 (what Start passes to `GameEngine(...)`):** from the anchored setup dict `[VERIFIED-source: setup_logic.py:49-68 DEFAULTS + BOX_PRESETS; gui_setup.py collect_state]`:
- `head=(0.0, 0.0)` — matches `pymol_bridge.place_head` centering at origin `[VERIFIED-source: pymol_bridge.py:108-122]`
- `heading='right'` (default; DIRS['right']=(1,0))
- `box_min, box_max = setup_logic.BOX_PRESETS[setup['box_preset']]` `[VERIFIED-source: setup_logic.py:64-68]`
- `pickups=None` (Phase 5 adds pickups)
- `cap=setup['win_cap_molecules']` `[VERIFIED-source: setup_logic.py:55]`
- `atom_budget=setup['atom_budget']` `[VERIFIED-source: setup_logic.py:56]`

**GUI stays pure (no pymol imports) — all cmd work via pymol_bridge.** `[VERIFIED-source: AGENTS.md:74 "GUI modules are an explicit allowlist in tools/check_purity.py (pymol.Qt only)"; check_purity.py:136-146 GUI class bans any non-Qt pymol]`. GameTab imports `pymol_bridge` (relative, exempt `[VERIFIED-source: check_purity.py:87-90,120-121 _is_relative exempts level>0]`) and calls bridge functions — it NEVER imports `pymol.cmd`. The movement tick's bridge call (translate `srp_head` by the engine delta) is a **bridge API gap** (pymol_bridge has no per-tick translate yet — it has `place_head` one-shot only `[VERIFIED-source: pymol_bridge.py:108-122]`), but that is the **sibling movement/camera aspect**, not this HUD aspect. The HUD itself needs no bridge calls (it only reads engine state + updates Qt labels).

### Q5. Purity + gate integration

**Add `serpentrum/gui_game.py` to `GUI_MODULES`** — mirror exactly how `gui_setup.py` is listed. `[VERIFIED-source: tools/check_purity.py:58 `GUI_MODULES = {'serpentrum/gui.py', 'serpentrum/gui_setup.py'}`; 03-07-SUMMARY.md "gui_setup GUI allowlist entry"]`. The edit: `GUI_MODULES = {'serpentrum/gui.py', 'serpentrum/gui_setup.py', 'serpentrum/gui_game.py'}`.

**Module-level imports in gui_game.py (the GUI-class-legal form):**
```python
from pymol.Qt import QtWidgets, QtCore   # ONLY this pymol form (check_purity.py:73 QT_ALLOWED_PREFIX)
from . import game_engine                  # relative, exempt
from . import pymol_bridge                 # relative, exempt (calls only; no cmd import here)
```
`[VERIFIED-source: gui_setup.py:38-43 mirrors exactly; check_purity.py:136-146 GUI rule]`. `QtCore` is needed for `QTimer`/`Signal`/`Qt` enums — all arrive via `pymol.Qt` `[VERIFIED-source: ARCHITECTURE.md F9 "QtCore.QTimer"; STACK.md "pymol.Qt exports QtCore"]`.

**`.exec_()` is BANNED everywhere** — the AST checker flags any `ast.Call` with `func.attr == 'exec_'` in every module class `[VERIFIED-source: check_purity.py:184-188]`. For any game-over / error modal in the Game tab, use the **static** `QtWidgets.QMessageBox.information(self, title, body)` / `QMessageBox.warning(self, title, body)` — these carry no `.exec_()` token in source (they run their own internal modal loop) `[VERIFIED-source: 03-RESEARCH-setup-ui.md §1.2; gui_setup.py:416-417, 431-432 use static QMessageBox.warning]`. Note bioCHEMeleon's `gui_game.py:345 msg.exec_()` is bioCHEMeleon's own code under a DIFFERENT (looser) gate — serpentrum's stricter AST gate forbids it; do NOT copy that line. (Phase 4 may not need a game-over modal at all — the HUD info box can show the verdict; reserve modals for confirm-restart if wanted.)

**Tick timer purity:** `QTimer` lives in gui_game (GUI class, allowed). The `timeout` slot calls `engine.step(dt)` (pure) and `pymol_bridge.<movement fn>(...)` (bridge, cmd-side). The slot itself runs on the Qt main thread = the PyMOL gui thread, so cmd is safe `[VERIFIED-source: 03-RESEARCH-setup-ui.md §1.4 "cmd.* may be called directly from Qt main-thread handlers"; PITFALLS.md Pitfall 6]`. No thread is spawned — Pitfall 6 (cmd from worker thread) is respected trivially.

### Q6. Smokes + tests

**Headless dialog construction is BANNED (dead end 01-05).** `[VERIFIED-source: STATE.md decision 01-05 "Offscreen Qt route is a DEAD END (dialog construction kills the process silently) — do NOT retry; dialog verdicts stay human-verify"; smoke/02_dialog_smoke.py is INFORMATIONAL non-blocking]`. Therefore:

| Layer | What | How | Where |
|-------|------|-----|-------|
| Pure engine | tick-driving, pause/resume, reset determinism, events | ALREADY covered by `tests/test_engine_core.py`, `test_engine_rules.py`, `test_engine_turns.py` `[VERIFIED-source: tests/ dir listing]` | WSL `python3.6 -m unittest` |
| New pure helpers (if any) | e.g. an `elapsed_format(seconds)→"M:SS"` helper, if extracted to a PURE module | new `tests/test_*.py` mirroring `test_setup_logic.py` convention `[VERIFIED-source: test_setup_logic.py:27 sys.path self-insert, no __init__.py]` | WSL |
| Bridge movement (if a per-tick translate fn is added) | `cmd.translate('srp_head', [dx,dy,dz])` per tick | new `smoke/05_*.py` headless Windows PyMOL smoke, sentinel-flushed, mirroring `smoke/04_demo_e2e_smoke.py` `[VERIFIED-source: smoke/04_demo_e2e_smoke.py template]` | Windows headless via `cmd.exe /c run-conda-pymol.bat -cq` |
| GUI (GameTab, countdown, timers, pause/resume, tab switch, info box) | widget rendering, signal flow, epoch guard, tab switch | **HUMAN-VERIFY ONLY** — 10-step checklist below | real Windows PyMOL |

**Test convention for GUI-adjacent pure logic (separate from widgets):** `test_setup_logic.py` shows the pattern — pure logic lives in a PURE module (`setup_logic.py`), imported directly in WSL tests with `sys.path.insert(0, repo_root)` and NO `sys.modules` stubs `[VERIFIED-source: test_setup_logic.py:27, 03-RESEARCH-setup-ui.md §1.4 F23 "the AA-match pattern (lazy imports, no module-level pymol/Qt/numpy) removes the need for stubs entirely"]`. If Phase 4 extracts any pure helper (e.g. `gui_game_helpers.py` for `format_elapsed` / `format_remaining`), it goes in a PURE module + a `test_gui_game_helpers.py`. Keep GameTab itself thin (widget assembly + signal wiring); push formattable logic to pure helpers so it is WSL-testable.

**Smokes convention (from smoke/02 + smoke/04):** verdict = flushed `SMOKE-OK <NAME>` / `SMOKE-FAIL <step>: ...` sentinels, NEVER exit codes (PyMOL swallows rc through the .bat) `[VERIFIED-source: smoke/02_dialog_smoke.py:9-17, smoke/04_demo_e2e_smoke.py:6-9]`; `flush=True` on every print; resolve ROOT by validating `serpentrum/__init__.py` (never trust `__file__` under `-cq`); NO `__init__.py` in smoke/ `[VERIFIED-source: smoke/04:46-63, 28-31; AGENTS.md:71]`.

---

## Code Sketches

### GameTab class skeleton (follows gui_setup.py conventions)

```python
# serpentrum/gui_game.py — GUI purity class (pymol.Qt only at module level)
"""serpentrum.gui_game — the Game tab HUD (countdown, info box, elapsed
timer, molecules-remaining, pause/resume, restart). Phase 4.

Purity class: GUI (pymol.Qt only; bare pymol/pmg_tk banned; PyQt5/numpy
banned). All cmd access via pymol_bridge (relative import, exempt). The
movement tick QTimer + the 1 Hz elapsed-label QTimer live here (Qt parent
ownership = the GameTab widget). Game SESSION state (engine + epoch +
start_time) anchors on pmg_tk.startup._serpentrum.game_session — NEVER
module globals (Pitfall 7) and NEVER the widget (rebuilt on reload).

python3.6 syntax (%-formatting).
"""
import time
from pymol.Qt import QtWidgets, QtCore

from . import game_engine
from . import pymol_bridge
from . import setup_logic

# Movement tick interval (dt passed to engine.step). 0.1 s matches the
# engine's tested parameter (test_engine_core.py) and gives 0.3 A/tick at
# SPEED_A_PER_S=3.0. Playtesting-tunable (ARCHITECTURE.md Pattern 3).
TICK_DT = 0.1
TICK_INTERVAL_MS = 100
ELAPSED_INTERVAL_MS = 1000


class GameTab(QtWidgets.QWidget):
    """The Game tab HUD.

    Built once by PluginDialog as page 1. Reads the anchored setup dict on
    Start to seed the engine. Owns the tick + elapsed QTimers (Qt parent
    ownership). The session (engine/epoch/start_time) is anchored on
    _serpentrum so reload cannot duplicate it; every singleShot/timeout
    callback closes over the epoch it was scheduled under and no-ops if
    stale (Pitfall 9.1 epoch guard).
    """

    # Emitted when the user clicks Start (collected setup dict carried up
    # to PluginDialog, which switches the tab). Phase 4 temp button — the
    # canonical Start lives in the Phase-8 bottom row (SETUP-07).
    # (Alternative: Start lives in SetupTab and emits there — see Q1.)

    def __init__(self, anchor_state=None, parent=None):
        super(GameTab, self).__init__(parent)
        self._anchor = anchor_state
        self._epoch = 0  # monotonic; bumped on start/restart/teardown
        self._session = None  # the anchored game_session (engine+epoch+...)
        self._build_widgets()
        self._build_layout()
        self._wire_signals()
        # QTimers: Qt-parent-owned by self (die with the widget on reload).
        self._tick_timer = QtCore.QTimer(self)
        self._tick_timer.setInterval(TICK_INTERVAL_MS)
        self._tick_timer.timeout.connect(self._on_tick)
        self._elapsed_timer = QtCore.QTimer(self)
        self._elapsed_timer.setInterval(ELAPSED_INTERVAL_MS)
        self._elapsed_timer.timeout.connect(self._on_elapsed_tick)
        self._set_idle_state()  # widgets disabled until Start

    def _build_widgets(self):
        self.countdown_label = QtWidgets.QLabel('ready', self)
        f = self.countdown_label.font(); f.setPointSize(28)
        self.countdown_label.setFont(f)
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
        lay = QtWidgets.QVBoxLayout(self)
        lay.addWidget(self.countdown_label)
        lay.addWidget(self.info_box, 1)  # stretch: info box grows
        row = QtWidgets.QHBoxLayout()
        row.addWidget(QtWidgets.QLabel('Elapsed:', self))
        row.addWidget(self.elapsed_label)
        row.addStretch(1)
        row.addWidget(QtWidgets.QLabel('Molecules', self))
        row.addWidget(self.remaining_label)
        lay.addLayout(row)
        btn_row = QtWidgets.QHBoxLayout()
        btn_row.addWidget(self.pause_btn)
        btn_row.addWidget(self.restart_btn)
        btn_row.addStretch(1)
        lay.addLayout(btn_row)
        lay.addWidget(self.hint_label)

    def _wire_signals(self):
        self.pause_btn.toggled.connect(self._on_pause_toggled)
        self.restart_btn.clicked.connect(self._on_restart)

    # --- session lifecycle ------------------------------------------------

    def begin_game(self, setup):
        """Called by PluginDialog when Start is clicked (GAME-01).

        Tears down any live session first (Restart-mid-game path), builds
        a fresh engine from the setup dict, anchors the session on
        _serpentrum, bumps epoch, then runs the 3-2-1 countdown. The
        movement tick timer starts at _begin_play (after GO!).
        """
        self._teardown_live_session()  # stop timers, bump epoch
        engine = self._build_engine(setup)
        self._session = {
            'engine': engine,
            'epoch': self._epoch,
            'start_time': None,       # set at _begin_play
            'paused_accum': 0.0,
            'status': 'countdown',
        }
        if self._anchor is not None:
            self._anchor.game_session = self._session
        self._epoch += 1
        self.info_box.clear()
        self._log('Get ready...')
        self._run_countdown(3)

    def _build_engine(self, setup):
        (x0, y0), (x1, y1) = setup_logic.BOX_PRESETS[setup['box_preset']]
        return game_engine.GameEngine(
            head=(0.0, 0.0), heading='right',
            box_min=(x0, y0), box_max=(x1, y1),
            pickups=None,                         # Phase 5
            cap=setup.get('win_cap_molecules'),
            atom_budget=setup.get('atom_budget'))

    def _run_countdown(self, n):
        """3-2-1 countdown via recursive singleShot (epoch-guarded).

        singleShot chains CANNOT be cancelled (Pitfall 9.1) — the epoch
        guard no-ops a stale chain after a Start/Restart bump. Mirrors
        bioCHEMeleon gui_game.py:258-264.
        """
        scheduled = self._epoch
        if n > 0:
            self.countdown_label.setText(str(n))
            self._log(str(n))
            QtCore.QTimer.singleShot(1000,
                lambda: self._countdown_step(n - 1, scheduled))
        else:
            self.countdown_label.setText('GO!')
            self._log('GO!')
            self._begin_play(scheduled)

    def _countdown_step(self, n, scheduled):
        if scheduled != self._epoch:
            return  # stale chain (Start/Restart bumped epoch)
        self._run_countdown(n)

    def _begin_play(self, scheduled):
        if scheduled != self._epoch:
            return  # stale
        self._session['start_time'] = time.time()
        self._session['status'] = 'playing'
        self._tick_timer.start()
        self._elapsed_timer.start()
        self._update_remaining()
        self.pause_btn.setEnabled(True)
        self._log('Move with the arrow keys.')

    # --- tick + elapsed ---------------------------------------------------

    def _on_tick(self):
        sess = self._session
        if sess is None or sess['epoch'] != self._epoch:
            return  # stale / no session
        engine = sess['engine']
        if engine.paused or engine.finished:
            return
        events = engine.step(TICK_DT)
        for ev in events:
            self._handle_event(ev, engine)
        # Movement bridge call (sibling aspect owns the exact fn; here the
        # HUD wires the seam). Phase 4: translate srp_head by the delta.
        # pymol_bridge.move_head(...)  # <-- sibling movement aspect
        if engine.finished:
            self._end_run(engine)

    def _handle_event(self, ev, engine):
        kind = ev[0]
        if kind == 'moved':
            pass  # too chatty to log at 10 Hz; update remaining quietly
        elif kind == 'turning':
            pass  # optional: log sweep progress
        elif kind == 'turn_refused':
            self._log('turn refused: %s' % ev[1])
        elif kind == 'crashed':
            self._log('crashed into %s' % ev[1])
        elif kind == 'won':
            self._log('YOU WIN')
        self._update_remaining()

    def _on_elapsed_tick(self):
        sess = self._session
        if sess is None or sess['start_time'] is None:
            return
        elapsed = time.time() - sess['start_time'] - sess['paused_accum']
        if elapsed < 0:
            elapsed = 0.0
        mins = int(elapsed) // 60
        secs = int(elapsed) % 60
        self.elapsed_label.setText('%d:%02d' % (mins, secs))

    def _update_remaining(self):
        sess = self._session
        if sess is None:
            self.remaining_label.setText('Remaining: -')
            return
        engine = sess['engine']
        cap = engine.cap if engine.cap is not None else 0
        remaining = cap - engine.molecules_stacked
        self.remaining_label.setText('Remaining: %d' % remaining)

    # --- pause / restart / end -------------------------------------------

    def _on_pause_toggled(self, checked):
        sess = self._session
        if sess is None or sess['engine'] is None:
            return
        engine = sess['engine']
        if checked:
            engine.pause()
            self._tick_timer.stop()
            sess['_pause_time'] = time.time()
            sess['status'] = 'paused'
            self.pause_btn.setText('Resume')
            self._log('paused')
        else:
            # rebase: add paused interval to paused_accum (Pitfall 9.3)
            pt = sess.pop('_pause_time', None)
            if pt is not None:
                sess['paused_accum'] += time.time() - pt
            engine.resume()
            self._tick_timer.start()
            sess['status'] = 'playing'
            self.pause_btn.setText('Pause')
            self._log('resumed')

    def _on_restart(self):
        """GAME-07: reset to initial state (deterministic)."""
        sess = self._session
        if sess is None:
            return
        self._teardown_live_session()
        # Re-seed from the anchored setup dict (same config, fresh engine).
        setup = self._anchor.setup if self._anchor is not None else None
        if setup is None:
            self._log('restart needs a setup dict on the anchor')
            return
        self.begin_game(setup)  # rebuilds engine + countdown

    def _end_run(self, engine):
        self._tick_timer.stop()
        # elapsed timer may keep running to show final time; stop it too:
        self._elapsed_timer.stop()
        sess = self._session
        if sess is not None:
            sess['status'] = 'over'
        self.pause_btn.setEnabled(False)
        verdict = engine.result or 'over'
        self._log('run over: %s' % verdict)

    def _teardown_live_session(self):
        """Stop timers + bump epoch (kills stale singleShot chains)."""
        self._tick_timer.stop()
        self._elapsed_timer.stop()
        self._epoch += 1  # any in-flight singleShot now no-ops
        self.pause_btn.setChecked(False)
        self.pause_btn.setText('Pause')
        self.pause_btn.setEnabled(False)

    def _log(self, msg):
        self.info_box.append(str(msg))

    def _set_idle_state(self):
        self.pause_btn.setEnabled(False)
        self.restart_btn.setEnabled(False)
```

### Anchor / session lifecycle (text diagram)

```
pmg_tk.startup._serpentrum (the anchor; survives reload/double-import)
├── dialog        (PluginDialog singleton — Phase 1)
├── controller    (reserved field — Phase 4 may reuse as game_session)
├── setup         (live setup dict — Phase 3)
└── game_session  (NEW Phase 4 — recommended new field)
      │  None until first Start; rebuilt on Restart (epoch bump)
      └── {'engine': GameEngine, 'epoch': int, 'start_time': float|None,
           'paused_accum': float, 'status': str}

QTimer ownership (Qt parent = GameTab widget; dies on widget rebuild):
  GameTab._tick_timer   (100 ms → engine.step + bridge.move_head)
  GameTab._elapsed_timer (1000 ms → recompute label from wall clock)

Epoch guard: every singleShot callback + every timeout slot closes over
  self._epoch at schedule time; no-ops if self._epoch != scheduled.
  Bumped on: begin_game (Start), _on_restart, _teardown_live_session.
  → Pitfall 9.1 (uncancellable singleShot chains) defused.
```

### Signal wiring diagram (text)

```
[Setup tab]                                    [PluginDialog]              [Game tab]
start_btn.clicked ──> SetupTab.collect_state() ──> emit start_requested(setup)
                                                  │
                       PluginDialog connects start_requested ──> game_tab.begin_game(setup)
                                                  │                       │
                                                  ├── tabs.setCurrentIndex(1)   # GAME-01 switch
                                                  │                       │
                                                                          begin_game:
                                                                            teardown live session
                                                                            engine = build_engine(setup)
                                                                            anchor.game_session = {...}
                                                                            epoch++
                                                                            run_countdown(3)
                                                                                │ singleShot chain (epoch-guarded)
                                                                                ▼
                                                                            _begin_play:
                                                                              start_time = now
                                                                              tick_timer.start()
                                                                              elapsed_timer.start()

[Game tab timers]
tick_timer.timeout ──> _on_tick: engine.step(dt) → events → info_box + bridge.move_head
elapsed_timer.timeout ──> _on_elapsed_tick: label = time.time() - start_time - paused_accum
pause_btn.toggled ──> _on_pause_toggled: engine.pause/resume + timer stop/start + rebase
restart_btn.clicked ──> _on_restart: teardown + begin_game(anchor.setup)

[Input] (sibling aspect)
arrow key ──> input.py ──> engine.request_direction(name) ──> buffered → applied at next step()
```

---

## Engine API gap list (Phase 4 must add to game_engine.py — PURE, testable)

**For the HUD aspect: NONE.** The HUD reads only existing public attrs (`cap`, `molecules_stacked`, `finished`, `result`) and calls existing methods (`step`, `pause`, `resume`, `reset`, `request_direction`). Elapsed time is GUI-owned by design. `[VERIFIED-source: game_engine.py full read]`.

**Optional convenience (NOT required, but reduces HUD coupling):** a read-only property on the engine:
```python
@property
def molecules_remaining(self):
    """cap - molecules_stacked (None if cap is None). For the HUD (GAME-07)."""
    return None if self.cap is None else self.cap - self.molecules_stacked
```
This keeps `cap - molecules_stacked` arithmetic in the pure engine (WSL-testable) rather than the GUI. Recommend adding it for cleanliness + a one-line unittest; the HUD then reads `engine.molecules_remaining`. Low-risk, pure, tested.

**Cross-aspect bridge gaps (NOT this aspect — sibling movement/camera aspect owns these; listed so the planner can coordinate):**
- `pymol_bridge.move_head(dx, dy, dz)` (or `set_head_position(x, y)`) — per-tick translate of `srp_head`. Bridge currently has only one-shot `place_head` `[VERIFIED-source: pymol_bridge.py:108-122]`. `cmd.translate` is verified `[VERIFIED-source: ARCHITECTURE.md F14 "translate (editing.py:1610)"; pymol_bridge.py:122 already uses cmd.translate]`.
- `pymol_bridge.lock_camera_2d()` — GAME-02 locked 2D camera. STATE.md decision 03-06: "camera = one-shot cmd.zoom only, NEVER ortho/set_view (Phase 4 owns GAME-02)". The exact mechanism (`cmd.set_view` / `cmd.view` / ortho) is the sibling aspect's research.
- `input.py` (arrow-key binding + event-filter fallback) — sibling input aspect; calls `engine.request_direction`.

---

## Pitfalls (Phase-4-HUD-specific, with verified root causes)

### Pitfall A: Reload duplicates the session / timers (Pitfall 7 + 8)
**What goes wrong:** Plugin-Manager reload re-executes `__init__.py`, reconstructs the dialog → a new GameTab with new QTimers; if the engine/timers were widget-owned, two engines + two timer chains drive one scene.
**Why:** module-level/widget-level singletons duplicate on reload `[VERIFIED-source: PITFALLS.md Pitfall 7; __init__.py:42-46 reconstructs dialog]`.
**How to avoid:** session anchors on `_serpentrum.game_session` (survives reload); QTimers are Qt-parent-owned by the widget (die with it); epoch guard no-ops stale callbacks from the dead widget.
**Warning signs:** two snakes moving after reload; timer ticks applied twice.

### Pitfall B: singleShot countdown double-fires (Pitfall 9.1)
**What goes wrong:** pressing Start (or Restart) during the 3-2-1 countdown leaves the old singleShot chain alive; it fires `_begin_play` a second time → two tick timers.
**Why:** `QTimer.singleShot` chains cannot be cancelled `[VERIFIED-source: PITFALLS.md Pitfall 9.1; bioCHEMeleon gui_game.py:258-264 uses exactly this chain]`.
**How to avoid:** epoch counter — every countdown callback closes over the epoch at schedule time and no-ops if stale; bump epoch on every Start/Restart/teardown.
**Warning signs:** countdown "3 2 1 GO!" then a second "2 1 GO!"; two tick timers running.

### Pitfall C: pause inflates elapsed time (Pitfall 9.3)
**What goes wrong:** pause stops the tick timer but the wall-clock keeps advancing; resume without rebase counts paused seconds as play time.
**Why:** delta-based elapsed = `time.time() - start_time`; if `start_time` isn't rebased, the pause interval is included.
**How to avoid:** on resume, `paused_accum += (now - pause_time)` (or rebase `start_time += (now - pause_time)`). `[VERIFIED-source: PITFALLS.md Pitfall 9.3; bioCHEMeleon gui_game.py:278 rebase pattern]`.
**Warning signs:** elapsed timer "loses" exactly the pause duration.

### Pitfall D: elapsed-timer drift from tick-count accumulation (Pitfall 5)
**What goes wrong:** accumulating "elapsed += tick_interval" per timeout drifts when ticks coalesce (modal block, slow frame).
**Why:** QTimer is not hard-realtime; coalesced ticks undercount.
**How to avoid:** ALWAYS recompute `elapsed = time.time() - start_time - paused_accum` from the wall clock, never accumulate. `[VERIFIED-source: PITFALLS.md Pitfall 5 "delta-based, never accumulated tick counts"]`.
**Warning signs:** elapsed undercounts after any UI hiccup.

### Pitfall E: tab-switch focus steals arrow keys (Pitfall 4.2)
**What goes wrong:** after `setCurrentIndex(1)`, the Game tab widget has focus, not the 3D viewer; arrow keys hit the dialog (or its command-line history) and never reach `cmd.set_key` / the input path.
**Why:** PyMOL key pipeline fires only when the 3D viewer has focus `[VERIFIED-source: PITFALLS.md Pitfall 4.2 "keys only reach the PyMOL key pipeline when the PyMOL main window has focus"]`.
**How to avoid:** (sibling input aspect) — the Qt event-filter fallback captures arrows regardless of focus; PLUS an in-HUD hint "click the 3D viewer to steer" + optional auto-pause on dialog focus-gain. The HUD's job: show the hint label prominently during countdown.
**Warning signs:** "keys don't work" right after the tab switch.

### Pitfall F: timer leak on dialog close (Pitfall 8)
**What goes wrong:** closing the dialog mid-game leaves QTimers firing against a dead widget / stale session.
**Why:** QTimers without parent or not stopped can outlive the widget.
**How to avoid:** QTimers are `QTimer(self)` (parent = GameTab) → Qt deletes them with the widget; ALSO stop them in a `closeEvent`/teardown for belt-and-braces. `[VERIFIED-source: PITFALLS.md Pitfall 8 "Timers: stop in closeEvent/destructor"; standard Qt parent ownership]`.
**Warning signs:** after closing the dialog, the viewer still shows movement or log spam.

### Pitfall G: blockSignals / _loading discipline on programmatic widget updates
**What goes wrong:** programmatically toggling `pause_btn.setChecked(False)` on restart fires `toggled` → `_on_pause_toggled(False)` → spurious `engine.resume()` on a not-paused engine.
**Why:** Qt emits signals on programmatic state changes too.
**How to avoid:** mirror `gui_setup.py`'s `blockSignals(True)` + `_loading` guard pattern `[VERIFIED-source: gui_setup.py:382-395 blockSignals, 441-443 _loading]` around programmatic widget mutation (e.g. wrap `pause_btn.setChecked(False)` in `blockSignals`).

---

## Human-verify checklist (10-step, real Windows PyMOL 2.5.0 — GUI verdicts only)

Mirrors the 03-08 10-step style `[VERIFIED-source: 03-08-SUMMARY.md:103-114]`. All steps run in real Windows PyMOL (headless dialog construction is a dead end, 01-05).

1. **Setup → Start → tab switch:** Apply a demo set + head on the Setup tab; click Start → dialog switches to the Game tab (Setup=0 → Game=1). [GAME-01]
2. **Countdown:** Game tab shows "3" → "2" → "1" → "GO!" at ~1 s intervals in the countdown label AND the rolling info box; the head does NOT move during countdown. [GAME-01]
3. **Continuous movement:** after GO!, the head (spheres) moves forward continuously without stopping; speed looks constant. [GAME-01, GAME-08]
4. **Elapsed timer:** the elapsed label counts up from 0:00 at 1 Hz; matches a wall-clock stopwatch within ±1 s over ~30 s of play (drift check). [GAME-07]
5. **Molecules-remaining:** label shows the configured cap (e.g. "Remaining: 10") and stays there (no pickups in Phase 4 — frozen is correct; dynamic in Phase 5). [GAME-07]
6. **Rolling info box:** countdown lines + "Move with the arrow keys" + any turn-refusal/crash lines appear; box is read-only and scrolls. [GAME-07]
7. **Pause/Resume:** click Pause → tick stops (head freezes), button label flips to "Resume", elapsed timer freezes; click Resume → head moves again, elapsed continues WITHOUT jumping (no inflated time). [GAME-07, Pitfall C]
8. **Restart mid-run:** click Restart → countdown re-runs 3-2-1, head returns to origin, elapsed resets to 0:00, NO second snake / NO double countdown (epoch guard). [GAME-07, Pitfall B]
9. **Restart during countdown:** click Start, then immediately click Restart during "3" → only ONE countdown proceeds; no duplicate timers. [Pitfall B]
10. **Reload safety + modeless:** with a game running, re-add the plugin dir in Plugin Manager (or restart PyMOL) → exactly ONE dialog, ONE session; viewer + command line stay responsive while the Game tab is open (modeless held). [INFRA-03, INFRA-05, Pitfall A]

(Steering with arrow keys, locked 2D camera, and crash-to-spectra are sibling-aspect human-verify steps — input/movement/camera — not in this HUD checklist, though step 3 implicitly needs movement to be visible.)

---

## Open Questions

1. **Start-button placement (temporary):** recommended inside the Setup tab (mirrors Phase 3 temp-button precedent), emitting `start_requested(setup)` to PluginDialog. **Needs planner decision** — alternative: a temporary Start in the reserved bottom row of gui.py (cleaner conceptually but touches the Phase-8-reserved row). The Phase 3 precedent (temp buttons inside the tab page, bottom row untouched) is the safer choice. `[ASSUMPTION-needs-human-verify]`

2. **Separate controller.py or not?** ARCHITECTURE.md lists `controller.py` as the composition root (cmd + Qt) `[VERIFIED-source: ARCHITECTURE.md:99,108]`, but `check_purity.py` has NO class allowing both cmd AND Qt in one module (GUI = Qt-only; BRIDGE = cmd-only) `[VERIFIED-source: check_purity.py:118-157]`. For Phase 4's scope (movement + HUD, no stacking/runner), recommend **NO separate controller** — GameTab (GUI class) owns the QTimers and orchestrates engine (pure) + pymol_bridge (BRIDGE, called via relative import) directly. This is purity-clean. A controller can be extracted in Phase 5/6 when stacking + xtb-runner complexity demands it. If a controller IS wanted, it must be BRIDGE-class (cmd-only) and the QTimers stay in GameTab — the controller exposes plain methods the GUI calls. **Needs planner decision.** `[ASSUMPTION-needs-human-verify]`

3. **Movement tick interval:** recommended 100 ms (dt=0.1, matches engine test params + 0.3 Å/tick). ARCHITECTURE.md Pattern 3 suggests "e.g. 250 ms". Final feel is a Phase-4 playtesting decision (ROADMAP Phase 4 notes "first playable ... motion"). `[ASSUMPTION-needs-human-verify]`

4. **Should elapsed timer keep running on game-over?** Recommend STOP both timers on `engine.finished` (cleaner; the final time is frozen on the label). Alternative: stop tick timer, keep elapsed timer (harmless — it shows the same frozen value). Minor; planner's call.

5. **`molecules_remaining` property on the engine:** optional pure convenience (keeps `cap - molecules_stacked` arithmetic in the testable pure layer). Recommend adding + one unittest, but not strictly required. `[ASSUMPTION-needs-human-verify]`

6. **Cross-aspect coordination:** the HUD's `_on_tick` calls a bridge movement function and the input aspect calls `engine.request_direction`. The planner must ensure the HUD aspect and the movement/camera/input aspects agree on: (a) the bridge `move_head` signature, (b) whether the tick timer lives in GameTab (recommended) or a controller, (c) the epoch/shared-session contract so input-driven direction changes land on the same engine instance the HUD ticks. This research recommends the engine instance is the single shared object inside `anchor.game_session['engine']`, accessed by both the HUD tick and the input handler. `[ASSUMPTION-needs-human-verify]`

---

## Sources

### Primary (HIGH confidence — read today from repo)
- `serpentrum/gui.py` (74 lines) — PluginDialog shell, `_TAB_DEFS` placeholders, `self.tabs` handle + switching contract, reserved bottom row
- `serpentrum/gui_setup.py` (479 lines) — SetupTab pattern: `_build_widgets`/`_build_layout`/`_wire_signals`/`collect_state`/`apply_state`/`_loading` guard/`blockSignals`/temp Apply+Cleanup buttons/anchor write-back
- `serpentrum/game_engine.py` (785 lines) — full public API: `step(dt)`, `request_direction`, `pause`/`resume`/`reset`, attrs (`head`,`heading`,`segments`,`pending`,`sweeping`,`paused`,`finished`,`result`,`cap`,`molecules_stacked`,`atoms_total`,`pickups_remaining`); docstring "NO wall-clock anywhere (pause timing is the GUI's job)"
- `serpentrum/pymol_bridge.py` (204 lines) — `materialize`, `place_head` (one-shot), `cleanup_srp`, `frame_scene`; NO per-tick translate yet
- `serpentrum/__init__.py` (49 lines) — `_anchor()` / `_SerpentrumState` (dialog/controller/setup fields), reload-safe anchoring on `pmg_tk.startup._serpentrum`
- `serpentrum/setup_logic.py` (257 lines) — `DEFAULTS`, `BOX_PRESETS`, `win_cap_molecules`, `atom_budget`, `speed` (3.0)
- `tools/check_purity.py` (235 lines) — GUI_MODULES allowlist, BRIDGE_MODULES, `.exec_()` ban, relative-import exemption
- `.planning/research/ARCHITECTURE.md` — F9 (QTimer/singleShot/refresh), Pattern 3 (engine-owns-truth tick), state-ownership map (elapsed = GUI-owned)
- `.planning/research/PITFALLS.md` — Pitfall 4 (arrow keys/focus), 5 (modal/delta-timer), 7 (double-singleton), 8 (dialog/timer lifetime), 9 (epoch guard / pause rebase / singleShot non-cancellability)
- `.planning/ROADMAP.md` — Phase 4 goal + 5 success criteria (GAME-01,02,03,07,08)
- `.planning/REQUIREMENTS.md` — GAME-01/07/08 text, SETUP-07 (Start button = Phase 8)
- `tests/test_setup_logic.py` / `tests/test_engine_core.py` — pure-test convention (sys.path self-insert, no stubs, no `__init__.py`)
- `smoke/02_dialog_smoke.py` / `smoke/04_demo_e2e_smoke.py` — smoke conventions (flushed sentinels, ROOT validation, no widget construction)
- `.planning/phases/03-*/03-07-SUMMARY.md`, `03-08-SUMMARY.md`, `03-RESEARCH-setup-ui.md` — anchor pattern, temp-button precedent, 10-step human-verify style, QMessageBox.warning static (no exec_ token)

### Secondary (HIGH — bioCHEMeleon shipped v1, read today)
- `tmp/bioCHEMeleon/biochemeleon/gui_game.py:108-111` (1 Hz QTimer), `:228-232` (`_on_tick` delta-based elapsed), `:234-264` (`start_countdown`/`_countdown_step` recursive singleShot), `:266-287` (`_begin_play` stop-then-start timer, `_start_time = time.time() - elapsed` rebase), `:301-304` (pre-modal `cmd.refresh()` + 100 ms singleShot), `:345` (`msg.exec_()` — bioCHEMeleon-only; serpentrum gate BANS this — use static QMessageBox)

### Tertiary (LOW — inference)
- The Start-button placement, controller-or-not, and tick-interval recommendations are design inferences marked `[ASSUMPTION-needs-human-verify]` in Open Questions — not verified by execution.

## Metadata

**Confidence breakdown:**
- Engine API completeness for HUD: HIGH — full read of game_engine.py; every claimed attr/method verified at file:line
- Anchor/session design: HIGH — mirrors the verified setup-dict anchor pattern (`__init__.py:22-30`, `gui_setup.py:241-242`); epoch guard from verified Pitfall 9.1
- GameTab widget spec: HIGH for widget types/timer mechanisms (bioCHEMeleon shipped precedents); MEDIUM for exact layout (aesthetic, human-verify)
- Purity/gate integration: HIGH — read check_purity.py + gui_setup.py; the GUI allowlist edit is mechanical
- Start-button placement / controller-or-not: LOW (design decisions, Open Questions 1-2)

**Research date:** 2026-09-12
**Valid until:** 2026-10-12 (stable codebase; engine/anchor/purity patterns unlikely to shift before Phase 4 execution)
