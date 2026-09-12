# Phase 4 — Game Loop & Input: INPUT SPIKE Research

**Aspect:** the one open mechanism question — how arrow keys reach the engine.
**Researched:** 2026-09-12
**Domain:** PyMOL 2.5.0 keyboard dispatch (C `PyMOL_Special` + Wizard `do_special` + Qt key path) vs Qt app-level eventFilter
**Confidence:** HIGH for the dispatch mechanism (C++ source + empirical probe); the live-focus/real-keystroke behavior is necessarily `[ASSUMPTION-needs-human-verify]` (headless PyMOL has no window, no QApplication, no key events).

**Bottom line (one line):** Make the **Wizard `do_special` route the PRIMARY** (it is the *only* route that receives up/down — `cmd.set_key('up'/'down', fn)` is stored but **never invoked** on real keypresses, source-verified in `layer5/PyMOL.cpp:2320-2325`); keep the **Qt application-level `eventFilter` as the designed FALLBACK** (solves dialog-focus stealing if the wizard route misbehaves live). **Do NOT use `cmd.set_key` for steering at all** — it cannot do up/down and it mutates global `key_mappings` (leak risk).

---

## ANSWER (recommended input mechanism)

### Primary: Wizard subclass overriding `get_event_mask()` + `do_special`

| # | Claim | Confidence |
|---|-------|------------|
| W1 | A `Wizard` subclass with `get_event_mask()` returning `event_mask_key + event_mask_special` (= **4 + 8 = 12**) receives arrow keys via `do_special(k, x, y, mod)`. The base-class default is pick+select only (1+2), which does NOT fire `do_special`. | `[VERIFIED-source]` `pymol/wizard/__init__.py:6-9,55-56,82-86`; `layer1/Wizard.cpp:217-224,461-467` (event-mask gate `isEventType(cWizEventSpecial)`) |
| W2 | The C entry for arrow/special keys (`PyMOL_Special`, `layer5/PyMOL.cpp:2310-2344`) calls `WizardDoSpecial` **FIRST** (line 2318). `WizardDoSpecial` runs `cmd.get_wizard().do_special(k,x,y,mod)` (`Wizard.cpp:472-475`); a truthy return sets `grabbed=1`. | `[VERIFIED-source]` |
| W3 | `do_special` receives `k` as the **integer GLUT code**: `100=left, 101=up, 102=right, 103=down` (same map as `internal.special_key_codes`). The wizard maps code→direction name. | `[VERIFIED-source]` `pymol/internal.py:414-417`; `layer5/PyMOL.cpp:2318` casts to `unsigned char` and forwards the same `k` |
| W4 | Returning truthy from `do_special` suppresses the `set_key`/`_special` path for **left/right** (prevents the default movie-frame-step). For **up/down** the suppression is unconditional (see Q1 below) regardless of the return value; return `True` anyway for uniformity. | `[VERIFIED-source]` `layer5/PyMOL.cpp:2318,2321-2331,2336-2341` |
| W5 | Wizard lifecycle (`cmd.set_wizard(self)` / `cmd.set_wizard(prior)` restore) is a verified pattern. `cmd.get_wizard()` returns `None` when none is active. | `[VERIFIED-empirical]` (probe: `WIZARD_PRIOR None`, `WIZARD_SET is_ours=True`, `WIZARD_RESTORED current=None`) + `[VERIFIED-source]` `pymol/wizarding.py:110-118,156-164` |
| W6 | A keyboard wizard is constructible headlessly and `do_special` is directly callable. | `[VERIFIED-empirical]` (probe: `WIZARD_BUILT mask=12`, `WIZARD_DOSPECIAL_DIRECT [('special',100,0),('special',101,0),('special',102,0),('special',103,0)]`) |
| W7 | On a **real** keypress, the C layer routes arrows to `do_special`. (Headless cannot generate key events; this is the live-behavior claim.) | `[ASSUMPTION-needs-human-verify]` — mechanism `[VERIFIED-source]`, live dispatch is the human-verify gate |
| W8 | Cosmetic side effect: up/down **always** also reach `OrthoSpecial` (command-line history scroll) regardless of the wizard; left/right leak to `OrthoSpecial` only when the command line holds unsubmitted text. Gameplay unaffected; the command-line text churns. | `[VERIFIED-source]` `layer5/PyMOL.cpp:2321-2332`; `layer1/Ortho.cpp:314-402` (per STACK.md §4.4) |

### Fallback: Qt application-level `eventFilter` (only if the wizard fails human-verify)

| # | Claim | Confidence |
|---|-------|------------|
| F1 | `from pymol.Qt import QtWidgets; app = QtWidgets.QApplication.instance()` returns the global QApplication in real GUI PyMOL (the `PyMOLQtGUI` is a `QMainWindow`, which requires a `QApplication` to exist). | `[VERIFIED-source]` `pmg_qt/pymol_qt_gui.py:31` (`class PyMOLQtGUI(QtWidgets.QMainWindow, …)`); headless `QApplication.instance()` is `None` `[VERIFIED-empirical]` (probe: `QAPP_INSTANCE None`) — so the fallback is **not installable headlessly** |
| F2 | `app.installEventFilter(filter)` installs a `QObject` whose `eventFilter(self, obj, ev)` sees **every** Qt event for **every** widget before the target widget handles it — including arrow `KeyPress` regardless of which widget has focus. PyMOL itself uses this pattern for Tab handling. | `[VERIFIED-source]` `pmg_qt/pymol_qt_gui.py:218-219,438-453` (`lineedit.installEventFilter(self)`, `pymolwidget.installEventFilter(self)`, `eventFilter` method) |
| F3 | The filter catches arrows whether the viewer OR the plugin dialog has focus — i.e. it **solves the focus-stealing problem** that the wizard route has. | `[VERIFIED-source]` (Qt application-event-filter semantics); `[ASSUMPTION-needs-human-verify]` for live behavior in PyMOL's Qt build |
| F4 | A `QObject` eventFilter is constructible headlessly (the class builds); installation requires a live `QApplication`. | `[VERIFIED-empirical]` (probe: `FILTER_OBJECT_BUILT Filter`, `NO_APP_HEADLESS installEventFilter skipped`) |

### Rejected: `cmd.set_key` for steering (DO NOT USE)

| # | Claim | Confidence |
|---|-------|------------|
| S1 | `cmd.set_key('left'/'up'/'right'/'down', fn)` does **not** raise — validation accepts all four (they are in `internal.special_key_names`). The binding is stored in `cmd.key_mappings`. | `[VERIFIED-empirical]` (probe: `SET_KEY_ATTEMPT ok left/up/right/down stored`) + `[VERIFIED-source]` `pymol/controlling.py:778-795` |
| S2 | **`set_key('up'/'down', fn)` callbacks NEVER fire on real keypresses.** The C `PyMOL_Special` switch (`layer5/PyMOL.cpp:2320-2325`) unconditionally sets `grabbed=1` for `P_GLUT_KEY_UP/DOWN` and calls `OrthoSpecial`; the `if(!grabbed)` block at line 2336 (which `PParse("_special …")` → `internal._special` → `_invoke_key` → `key_mappings`) is therefore **skipped for up/down**. Only the wizard's `do_special` receives up/down. | `[VERIFIED-source]` `layer5/PyMOL.cpp:2310-2344`; `pymol/internal.py:447-466` |
| S3 | `set_key('left'/'right', fn)` callbacks DO fire on real keypresses *when the command line is empty* (`OrthoArrowsGrabbed` false → `grabbed` not forced → `_special` runs). Default for left/right is movie frame step (`'_ backward'` / `'_ forward'`). | `[VERIFIED-source]` `layer5/PyMOL.cpp:2326-2331`; `[VERIFIED-empirical]` (probe: `DEFAULTS_BEFORE left -> '_ backward', right -> '_ forward', up/down -> None`) |
| S4 | The `shortcut_manager.reserved_keys = ('CTRL-S','CTRL-E','CTRL-O','CTRL-M','up','down')` reservation is enforced **only** in the GUI shortcut-editor (`ShortcutManager.create_new_shortcut`); `cmd.set_key` itself does NOT check it. So 'up'/'down' are bindable via the API — they just never fire (S2). | `[VERIFIED-source]` `pymol/shortcut_manager.py:21,118-139`; `[VERIFIED-empirical]` (probe: `RESERVED_CHECK_PATH True`) |
| S5 | `cmd.set_key` mutates the **global** `cmd.key_mappings` for the whole PyMOL session; a leaked binding breaks the user's arrow keys outside the game. (PITFALLS.md #4.3.) | `[VERIFIED-source]` `pymol/controlling.py:795` (`_self.key_mappings[key] = fn`) |

> **TRAP DEMONSTRATED:** calling `internal._special(code, 0, 0, 0)` *directly* (the Python handler) fires the set_key callback for **all four** arrows including up/down (probe: `INTERNAL_SPECIAL_PYTHON_PATH … fired: ['up']`). This is misleading — `internal._special` is only reached via `PParse("_special …")` at `PyMOL.cpp:2339`, which sits inside `if(!grabbed)`, which is **never entered for up/down**. A headless test that calls `cmd._special` directly will WRONGLY suggest set_key('up') works. Do not use `internal._special` as evidence of up/down bindability.

### Q1 — `cmd.set_key` arrow bindability (definitive)

- **Accepted by validation?** Yes, all four (`controlling.py:778-789`; `internal.py:425` `special_key_names` includes 'up'/'down'). `[VERIFIED-source]` + `[VERIFIED-empirical]`.
- **Default bindings?** `left` → `'_ backward'` (previous movie frame), `right` → `'_ forward'` (next movie frame); `up`/`down` → **none**. `[VERIFIED-empirical]` (`shortcut_dict.py:11-12`).
- **Do they fire on real keypresses?** `left`/`right`: yes (when command line empty). `up`/`down`: **NO** — hard-blocked by the C `grabbed=1` at `PyMOL.cpp:2323`. `[VERIFIED-source]`.
- **Persist/leak after plugin reload?** `key_mappings` is on the `cmd` object (session-global). A leaked set_key binding persists for the whole PyMOL session until overwritten or PyMOL is restarted. Plugin-Manager reload does NOT clear it. `[VERIFIED-source]` `controlling.py:795`. The wizard route avoids this entirely (set_wizard(prior) restores; no key_mappings mutation).
- **Key-name convention the dispatcher uses?** Integer GLUT codes `100/101/102/103` ↔ names `'left'/'up'/'right'/'down'` via `internal.special_key_codes`. `[VERIFIED-source]` `internal.py:414-417`.

### Q2 — Wizard event-mask behavior

- An active wizard's `do_special` is called by the C layer **before** the `set_key`/`_special` path (`PyMOL_Special` → `WizardDoSpecial` at line 2318, before `if(!grabbed)` at 2336). `[VERIFIED-source]`.
- The event mask is the gate: `Wizard.cpp:217-224` defaults `EventMask = pick+select` (1+2), then calls Python `get_event_mask()`; if it returns an int, that overrides. `WizardDoSpecial` (`Wizard.cpp:465`) checks `isEventType(cWizEventSpecial)` — false unless the mask includes `event_mask_special` (8). **Mandatory override:** `get_event_mask()` returns `event_mask_key + event_mask_special` (= 12). `[VERIFIED-source]` + `[VERIFIED-empirical]` (mask=12 built).
- A custom Wizard is a **viable** input route (W1-W8). It is the only idiomatic route that receives up/down. `[VERIFIED-source]`; live dispatch `[ASSUMPTION-needs-human-verify]`.

### Q3 — Focus stealing (headless CANNOT verify; reasoned from source)

- The 3D viewer is a **Qt** widget (`PyMOLGLWidget`, a `QGLWidget`/`QOpenGLWidget`), not Tk. `pmg_tk` is legacy-only (ARCHITECTURE.md F4). `[VERIFIED-source]` `pmg_qt/pymol_gl_widget.py:25-36`.
- Arrow keys reach the C `PyMOL_Special` path via `PyMOLQtGUI.keyPressEvent` (`pymol_qt_gui.py:50-54`) → `keymapping.keyPressEventToPyMOLButtonArgs` (`keymapping.py:61-97`, arrows → 100/101/102/103, state=-2) → `self.pymolwidget.pymol.button(*args)`. `[VERIFIED-source]`.
- The GL widget has `setFocusPolicy(Qt.ClickFocus)` (`pymol_gl_widget.py:110`) — **clicking the viewer gives it focus**. The GL widget has NO `keyPressEvent` override (grep: only `setFocusPolicy`), so key events propagate up to the `PyMOLQtGUI` QMainWindow, which handles them. `[VERIFIED-source]`.
- The PyMOL command-line `lineedit` installs an eventFilter (`pymol_qt_gui.py:218`) that consumes Up/Down for history navigation (`lineeditKeyPressEventFilter`, lines 419-435) **when the lineedit has focus**. So if the command line has focus, arrows do NOT reach the viewer. `[VERIFIED-source]`.
- Our plugin dialog is a **separate top-level modeless `QDialog`** (`serpentrum/gui.py:28`). When it (or any child widget) has focus, the `PyMOLQtGUI` QMainWindow does not receive key events → arrows do not reach `PyMOL_Special` → the wizard's `do_special` does NOT fire. `[ASSUMPTION-needs-human-verify]` (reasoned from Qt focus semantics; headless cannot test).
- **Implication for the wizard route:** steering works only when the viewer has focus. Mitigations: (a) wizard `get_prompt()` says "click the 3D viewer, then steer with arrow keys"; (b) auto-pause when the plugin dialog gains focus (Qt `focusInEvent` on the dialog → `engine.pause()`), so stolen focus can't kill the snake (PITFALLS.md #4.2). `[ASSUMPTION-needs-human-verify]` — the live focus behavior is the #1 human-verify item.
- **The eventFilter fallback (F1-F4) eliminates this problem** by catching arrows at the application level regardless of focus — its decisive advantage.

### Q4 — Qt application-level eventFilter fallback (verified design)

- Reach the app from the plugin: `from pymol.Qt import QtWidgets; app = QtWidgets.QApplication.instance()`. In real GUI PyMOL this is non-None (the `PyMOLQtGUI` QMainWindow requires it). `[VERIFIED-source]` `pymol_qt_gui.py:31`; headless returns None `[VERIFIED-empirical]`.
- Install: `app.installEventFilter(filter_obj)` where `filter_obj` is a `QtCore.QObject` with an `eventFilter(self, obj, ev)` method. PyMOL itself installs eventFilters on the lineedit and pymolwidget (`pymol_qt_gui.py:218-219`). `[VERIFIED-source]`.
- Map keys to steering: `ev.type() == QtCore.QEvent.KeyPress` and `ev.key()` in `{Qt.Key_Left, Qt.Key_Up, Qt.Key_Right, Qt.Key_Down}` → call `engine.request_direction(name)`. Return `True` to consume (suppress default), `False` to let it propagate.
- **Avoid breaking dialog text-field interaction:** before consuming, check the focused widget — if it is a `QLineEdit`/`QTextEdit`/editable `QComboBox` (or `ev.source()` is such a widget), return `False` so the user can type/navigate text. Standard Qt pattern (`QApplication.focusWidget()`).
- **Lifecycle:** install at countdown-end (`_begin_play`), remove at every teardown (win/lose/pause-to-setup/restart/cleanup). Owned by the controller or the Game tab widget so it is GC-rooted during play.
- Event path: Qt key event → **app eventFilter (ours, if installed)** → target widget's `keyPressEvent` (e.g. `PyMOLQtGUI.keyPressEvent` → C `PyMOL_Special`). By consuming at the app filter, arrows never reach PyMOL's C dispatch during play — no `OrthoSpecial` history churn, no frame-step. `[VERIFIED-source]` (Qt event-filter semantics); `[ASSUMPTION-needs-human-verify]` live.

### Q5 — Recommended route + integration constraints

**Recommendation: Wizard `do_special` PRIMARY, Qt eventFilter FALLBACK. Do NOT use `set_key`.**

Rationale:
1. The wizard is the **only** route that receives up/down (S2 — set_key is hard-blocked for up/down at the C layer). This is a stronger finding than the prior research ("up/down may conflict") — they are not merely conflicting, they are **never invoked**.
2. The wizard is idiomatic PyMOL, matches the bioCHEMeleon wizard-lifecycle precedent, and avoids mutating global `key_mappings` (no leak risk, no save/restore needed — only `set_wizard(prior)` restore).
3. The wizard's weakness is focus stealing (Q3) — mitigated by "click viewer" UX + auto-pause on dialog focus. If human-verify shows this is unsatisfactory, switch to the eventFilter fallback (which solves focus AND all four arrows uniformly).

**Module placement under purity rules** (`tools/check_purity.py`):

| Module | Purity class | Why | What it imports |
|--------|--------------|-----|-----------------|
| `serpentrum/input.py` (NEW) | **BRIDGE** (add to `BRIDGE_MODULES` alongside `pymol_bridge.py`) | Wizard subclass needs `from pymol.wizard import Wizard` + `from pymol import cmd` (`set_wizard`/`get_wizard`). No Qt. | `pymol.wizard.Wizard`, `pymol.cmd` (lazy or module-level — BRIDGE allows both); relative `.game_engine` is exempt |
| eventFilter fallback (if needed) | **GUI** (add a new `serpentrum/gui_input.py` to `GUI_MODULES`, OR host the `QObject` inside `gui_game.py`) | Needs `from pymol.Qt import QtCore, QtWidgets`. No `pymol.cmd`. | `pymol.Qt` only; relative pure imports exempt |
| `serpentrum/controller.py` (future) | PURE+composition (owns the route wiring) | Calls `input.install(engine)` / `input.teardown()` (or the eventFilter equivalent) at countdown-end / teardown. | relative imports only |

> **Note:** `input.py` (BRIDGE) cannot import Qt; the eventFilter fallback (GUI) cannot import `pymol.cmd`. The two routes therefore live in **different purity classes** and different files. The controller picks one. This keeps the purity gate trivially enforceable (extend `BRIDGE_MODULES` or `GUI_MODULES` by one entry, not both in one file).

**Steering seam (tick-boundary semantics):**

```
real keypress
  → (wizard route)  C PyMOL_Special → WizardDoSpecial → wiz.do_special(k,x,y,mod)
                                              ↓
  → (filter route)  Qt app eventFilter → filter.eventFilter(obj, ev)
                                              ↓
                          map k → direction name ('left'/'up'/'right'/'down')
                                              ↓
                          engine.request_direction(name)   # PURE (game_engine.py:311)
                                              ↓
                          engine.pending buffer (max 1; first-kept,
                            or newest-wins while sweeping — game_engine.py:344-365)
                                              ↓
                          NEXT tick: engine.step(dt) applies pending at START
                            (game_engine.py:631-644) → events: moved/turning/…
```

- The input layer is **stateless** about the game: it only forwards a direction name to `engine.request_direction(name)`. It ignores the return value (or logs a refused turn). The engine is the sole authority.
- `request_direction` returns `False` for 180°-reversal, same-direction, or queue-full (max 1) — the engine's responsibility, not the input layer's. Multiple keypresses before a tick do NOT queue beyond one; this is the designed tick-boundary semantics (the snake turns at most once per tick).
- During a **sweep** (rigid-pivot turn in progress, `engine.sweeping is not None`), `request_direction` buffers against the sweep TARGET (newest-wins, max 1) — the input layer does not need to know about sweeps.
- **During pause:** keep the wizard active but have `do_special` return `True` (grab) WITHOUT calling `request_direction` — so arrows neither steer nor step movie frames. (For the eventFilter, simply don't call `request_direction` while `engine.paused`, but still consume the key.) This matches PITFALLS.md #4 ("pausing may keep bindings but queue them").

---

## Evidence

### Probe script
`tmp/spike_probe/probe_input.py` (read-only; restores all state it touches). Syntax-checked with `python3.6 -m py_compile` (SYNTAX_OK). Run via `timeout 120 cmd.exe /c "C:\\src\\run-conda-pymol.bat -cq tmp\\spike_probe\\probe_input.py"`.

### Actual flushed output (excerpts)
```
SPIKE START: 3.9.13
SPIKE   default: left -> '_ backward'
SPIKE   default: up -> None
SPIKE   default: right -> '_ forward'
SPIKE   default: down -> None
SPIKE   ok: left stored -> (<function ...>, (), {})
SPIKE   ok: up stored -> (<function ...>, (), {})
SPIKE   ok: right stored -> (<function ...>, (), {})
SPIKE   ok: down stored -> (<function ...>, (), {})
SPIKE   _special code: 100 left -> fired: ['left']
SPIKE   _special code: 101 up -> fired: ['up']        # TRAP: Python path fires up/down
SPIKE   _special code: 102 right -> fired: ['right']  # but real C path skips them (S2)
SPIKE   _special code: 103 down -> fired: ['down']
SPIKE WIZARD_BUILT: mask= 12 key+special= 12
SPIKE WIZARD_PRIOR: None
SPIKE WIZARD_SET: is_ours= True type= KeyWizard
SPIKE WIZARD_DOSPECIAL_DIRECT: [('special', 100, 0), ('special', 101, 0), ('special', 102, 0), ('special', 103, 0)]
SPIKE WIZARD_RESTORED: current= None
SPIKE   QAPP_INSTANCE: None                            # headless: no QApplication
SPIKE   FILTER_OBJECT_BUILT: Filter
SPIKE   NO_APP_HEADLESS: installEventFilter skipped (app is None)
SPIKE   : left -> ('_ backward', 'previous movie frame', '')
SPIKE   : up -> None
SPIKE   : right -> ('_ forward', 'next movie frame', '')
SPIKE   : down -> None
SPIKE RESERVED_CHECK_PATH: create_new_shortcut references reserved_keys: True
SPIKE DONE:
```

### What the probe proves (and what it cannot)
- **Proves:** set_key accepts all four arrows; defaults (left/right=frame step, up/down=none); wizard construction + mask override + set/get/restore round-trip; `do_special` directly callable; `QApplication.instance()` is None headless; `reserved_keys` is only in the GUI shortcut-editor path.
- **Cannot prove (headless):** the C `PyMOL_Special` dispatch order on a *real* keypress; real focus behavior; eventFilter installation/behavior. These are `[VERIFIED-source]` (C++ read directly) + `[ASSUMPTION-needs-human-verify]` (live).

---

## Concrete code sketches

### Primary route — `serpentrum/input.py` (BRIDGE purity class)

```python
"""serpentrum.input — keyboard steering via a PyMOL Wizard (BRIDGE purity).

The Wizard do_special route is the ONLY idiomatic route that receives up/down
arrows: cmd.set_key('up'/'down', fn) is stored but never invoked, because the
C PyMOL_Special (layer5/PyMOL.cpp:2320-2325) forces grabbed=1 for UP/DOWN and
skips the _special/key_mappings dispatch. Verified 2026-09-12.

BRIDGE class: imports pymol.wizard + pymol.cmd; NEVER Qt/numpy; .exec_() never.
Add 'serpentrum/input.py' to BRIDGE_MODULES in tools/check_purity.py.
"""
from pymol import cmd
from pymol.wizard import Wizard

# GLUT special-key codes -> engine direction names (internal.special_key_codes).
_CODE_TO_DIR = {100: 'left', 101: 'up', 102: 'right', 103: 'down'}


class KeySteerWizard(Wizard):
    """Keyboard steering wizard. Active only during play.

    do_special is called by the C layer (WizardDoSpecial, layer1/Wizard.cpp:472)
    BEFORE the set_key/_special path. Returning True grabs the key (suppresses
    left/right movie-frame-step default). For up/down the grab is unconditional
    in C; True is returned for uniformity.
    """

    def __init__(self, steer_fn, _self=cmd):
        Wizard.__init__(self, _self)
        # steer_fn: callable(name) -> ignored. Controller binds
        # engine.request_direction. Held as a callback so this module stays
        # decoupled from game_engine (relative import would also be fine).
        self._steer = steer_fn
        self._active = True  # cleared on pause so do_special grabs-but-no-ops

    def get_event_mask(self):
        # MANDATORY: base returns pick+select (1+2); do_special never fires
        # without event_mask_special (8). key (4) included for completeness.
        return Wizard.event_mask_key + Wizard.event_mask_special  # 12

    def get_prompt(self):
        return 'serpentrum: click the 3D viewer, then steer with arrow keys'

    def get_panel(self):
        return [[1, 'serpentrum', ''],
                [2, 'Quit game', 'cmd.set_wizard()']]

    def do_special(self, k, x, y, mod):
        # k is the integer GLUT code (100/101/102/103). Map -> direction.
        name = _CODE_TO_DIR.get(int(k))
        if name is not None and self._active:
            self._steer(name)   # -> engine.request_direction(name)
        return True             # grab: suppress frame-step default on left/right


# --- lifecycle (controller calls these) -------------------------------------

def install(steer_fn):
    """Activate the steering wizard at countdown end. Returns the prior wizard
    (or None) for restore. Idempotent: if a KeySteerWizard is already active,
    returns the saved prior without re-installing."""
    prior = cmd.get_wizard()
    if isinstance(prior, KeySteerWizard):
        return getattr(prior, '_saved_wizard', None)
    wiz = KeySteerWizard(steer_fn)
    wiz._saved_wizard = prior
    cmd.set_wizard(wiz)
    cmd.refresh_wizard()
    return prior


def set_active(active):
    """Pause/resume steering without tearing the wizard down. When False,
    do_special grabs the key (no frame-step leak) but does not steer."""
    wiz = cmd.get_wizard()
    if isinstance(wiz, KeySteerWizard):
        wiz._active = bool(active)


def teardown():
    """Restore the prior wizard (or clear if None). Called by EVERY teardown
    path (win/lose/restart/cleanup/plugin-close). Idempotent."""
    wiz = cmd.get_wizard()
    if isinstance(wiz, KeySteerWizard):
        cmd.set_wizard(getattr(wiz, '_saved_wizard', None))
        cmd.refresh_wizard()
```

### Steering call (controller side)

```python
# In controller._begin_play() (after countdown):
import input  # serpentrum.input (BRIDGE)
self._input_prior = input.install(self.engine.request_direction)

# On pause:
input.set_active(False); self.engine.pause()

# On resume:
input.set_active(True);  self.engine.resume(); self._rebase_start_time()

# In _teardown_round() (single helper, every path):
input.teardown()                       # restore prior wizard
self._tick_timer.stop()                # stop the QTimer
self.engine.reset(...)                 # reset engine state
# (Phase 5 adds: delete srp_* pickups, etc.)
```

### Fallback route — Qt app-level eventFilter (GUI purity; only if wizard fails human-verify)

```python
# serpentrum/gui_input.py  (GUI purity: pymol.Qt only; add to GUI_MODULES)
from pymol.Qt import QtCore, QtWidgets
Qt = QtCore.Qt

_ARROWS = {Qt.Key_Left: 'left', Qt.Key_Up: 'up',
           Qt.Key_Right: 'right', Qt.Key_Down: 'down'}
_TEXT_TYPES = (QtWidgets.QLineEdit, QtWidgets.QTextEdit)
# editable combo: check in handler

class SteerEventFilter(QtCore.QObject):
    """App-level eventFilter: catches arrow KeyPress regardless of focus.
    Installed on QApplication.instance() during play; removed at teardown."""

    def __init__(self, steer_fn, parent=None):
        super(SteerEventFilter, self).__init__(parent)
        self._steer = steer_fn
        self._active = True

    def eventFilter(self, obj, ev):
        if ev.type() != QtCore.QEvent.KeyPress:
            return False
        name = _ARROWS.get(ev.key())
        if name is None:
            return False
        # Don't steal arrows from text-input widgets (let user type/navigate).
        focus = QtWidgets.QApplication.focusWidget()
        if isinstance(focus, _TEXT_TYPES):
            return False
        if self._active:
            self._steer(name)   # -> engine.request_direction(name)
        return True             # consume: suppress PyMOL's C PyMOL_Special path


def install(steer_fn):
    app = QtWidgets.QApplication.instance()
    if app is None:
        return None  # no GUI (should not happen during real play)
    f = SteerEventFilter(steer_fn)
    app.installEventFilter(f)
    return f   # caller MUST hold the ref (GC would drop the filter)

def teardown(f):
    if f is None:
        return
    app = QtWidgets.QApplication.instance()
    if app is not None:
        app.removeEventFilter(f)
```

---

## Human-verify checklist (the first real-GUI key test)

This is the **failure-cheap** gate the roadmap schedules in Phase 4. Run in real Windows PyMOL (not headless). Each item: state the expected vs actual.

1. **Wizard receives all four arrows (the core claim, W7).** Load plugin → Start → countdown ends → click the 3D viewer once → press each arrow. *Expect:* the head steers (or at least `request_direction` is called — log it). *Fail mode:* up/down do nothing (would refute W7 — switch to eventFilter fallback).
2. **Left/right do NOT step movie frames (W4).** With no movie loaded, press left/right during play. *Expect:* steering only; no "frame" change in the PyMOL console. *Fail mode:* console shows frame stepping (do_special not grabbing → check `return True`).
3. **Focus stealing (Q3).** During play, click the plugin dialog (or a button), then press arrows WITHOUT clicking back to the viewer. *Expect:* arrows do NOT steer (wizard route) — and the auto-pause fired so the snake didn't crash. *Mitigation verified:* click the viewer again → steering resumes. If this UX is unacceptable → adopt the eventFilter fallback (which should steer even with dialog focus).
4. **Command-line history churn (W8).** During play, press up/down. *Expect:* the PyMOL command line scrolls history (cosmetic); gameplay unaffected. *Acceptable per W8.*
5. **Teardown restore (W5, no leak).** End a run (crash or win). Press left/right/up/down outside the game. *Expect:* left/right revert to movie-frame-step (or prior binding); up/down revert to no-op (or prior). *Fail mode:* arrows still steer a non-existent snake, or left/right are dead (leaked binding) → `teardown()` not called on that path.
6. **Plugin-Manager reload mid-game (Pitfall 7/9).** Start a game, then reload the plugin via Plugin Manager. *Expect:* one dialog, one controller; the old wizard is torn down (no orphaned do_special). *Fail mode:* two steering wizards / double ticks.
7. **Restart during countdown (Pitfall 9.1).** Click Start, then Start again during 3-2-1. *Expect:* one wizard, one tick timer (epoch guard). *Fail mode:* two wizards.
8. **Prior wizard preserved.** If the user had a wizard active (e.g., `wizard measurement`) before starting the game, ending the game restores it. *Expect:* the measurement wizard reappears. *Fail mode:* prior wizard lost (teardown restore broken).
9. **(If fallback adopted) eventFilter + text field.** With the eventFilter installed, click a `QLineEdit` in the dialog and press up/down. *Expect:* the lineedit navigates normally (filter returns False for text widgets); arrows do NOT steer. *Fail mode:* filter steals arrows from text fields → check `_TEXT_TYPES` guard.
10. **(If fallback adopted) eventFilter catches arrows with dialog focus.** Click the dialog (not a text field), press arrows. *Expect:* steering works (the fallback's whole point). *Fail mode:* filter not installed / not seeing events → check `QApplication.instance()` is non-None.

---

## Pitfalls (what will break)

1. **`set_key('up'/'down')` silently does nothing** (S2). The callback is stored; headless `internal._special` even fires it (the TRAP, S5-note). Only the C `PyMOL_Special` gate reveals it never fires on real keypresses. **Use the wizard.**
2. **Missing `get_event_mask()` override.** Base returns 1+2 (pick+select); `do_special` never fires (Wizard.cpp:465 `isEventType(cWizEventSpecial)` false). **Must return 12.** `[VERIFIED-source]`.
3. **Focus stealing kills the snake (Q3).** Wizard route only steers when the viewer has focus. Mitigate: "click viewer" prompt + auto-pause on dialog `focusInEvent`. If unacceptable → eventFilter fallback.
4. **Leaked global rebinds (S5, PITFALLS.md #4.3).** `cmd.set_key` mutates session-global `key_mappings`. The wizard route avoids this (only `set_wizard(prior)` restore). **Do not use set_key.**
5. **Wizard displacement.** `cmd.set_wizard(self)` replaces any active wizard. Save `cmd.get_wizard()` at install, restore at teardown (bioCHEMeleon pattern, `tmp/bioCHEMeleon/biochemeleon/wizard.py:86-92`). Verified round-trip `[VERIFIED-empirical]`.
6. **singleShot countdown double-fire (Pitfall 9.1).** Restart during 3-2-1 arms a second `_begin_play` → two wizards. Mitigate: epoch counter; `install()` is idempotent (skips if a KeySteerWizard is already active).
7. **`do_special` receives an INT, not a name (W3).** Mapping `100/101/102/103` → `'left'/'up'/'right'/'down'`. An unmapped code (e.g. F1=1) returns `None` → no-op (don't crash). `[VERIFIED-source]`.
8. **eventFilter steals arrows from text fields (fallback).** Must guard with `QApplication.focusWidget()` type check. `[ASSUMPTION-needs-human-verify]`.
9. **eventFilter ownership/GC (fallback).** If the `QObject` filter is a local var, Python GCs it → silently stops filtering. Controller or Game tab must hold the ref for the play duration.
10. **`QApplication.instance()` is None headless (F1).** Any smoke test of the fallback must skip if `app is None`. The fallback is human-verify-only.
11. **Purity-class placement (Q5).** `input.py` is BRIDGE (pymol, no Qt); the eventFilter is GUI (Qt, no pymol.cmd). Putting both in one file violates the purity gate (a module can't be both BRIDGE and GUI). Two files, two allowlist entries.
12. **Up/down `OrthoSpecial` churn (W8).** Cosmetic; the command line scrolls. Document in Help. No mitigation needed (gameplay unaffected).

---

## Open questions

1. **Live wizard dispatch on real keypress (W7).** Mechanism is `[VERIFIED-source]`; the live behavior (does `do_special` actually fire when a human presses up/down in the real GUI?) is `[ASSUMPTION-needs-human-verify]` — human-verify item #1. If it fails, switch to the eventFilter fallback (which is designed to work).
2. **Live focus behavior (Q3).** Does clicking the viewer reliably restore steering? Does the dialog steal focus on button clicks? Human-verify items #3. Auto-pause-on-dialog-focus is the safety net either way.
3. **`QApplication.instance()` non-None in real GUI (F1).** Headless is None; real GUI must be non-None (PyMOLQtGUI is a QMainWindow). `[VERIFIED-source]`-inferred; confirm at human-verify item #10 if the fallback is adopted.
4. **EventFilter interaction with PyMOL's own eventFilters (F2).** PyMOL installs filters on `lineedit` and `pymolwidget` (`pymol_qt_gui.py:218-219`). An app-level filter sees events first; should not interfere (we only consume arrows during play), but verify no regression in command-line tab-completion / history during play. `[ASSUMPTION-needs-human-verify]`.
5. **Whether to keep the wizard active during pause or tear it down.** Recommendation: keep it, `set_active(False)` (grab-but-no-op) so arrows don't leak to frame-step. Alternative: tear down on pause, reinstall on resume. The keep-it path is simpler and matches PITFALLS.md #4. Decide at implementation.

---

## Sources

### Primary (HIGH confidence — C++/Python source read directly + empirical probe)
- `pymol-src/layer5/PyMOL.cpp:2305-2344` — `PyMOL_Special` (the arrow-key C entry): `WizardDoSpecial` first (2318); UP/DOWN force `grabbed=1` + `OrthoSpecial` unconditionally (2321-2325); LEFT/RIGHT `OrthoSpecial` only if `OrthoArrowsGrabbed` (2326-2331); `if(!grabbed)` → `PParse("_special …")` (2336-2341) — **the gate that blocks set_key for up/down**.
- `pymol-src/layer1/Wizard.cpp:217-224` (event-mask read from `get_event_mask`), `:327-340` (`WizardDoKey`), `:461-476` (`WizardDoSpecial` → `cmd.get_wizard().do_special(k,x,y,mod)`, truthy return).
- `pymol-src/modules/pymol/internal.py:398-445` (`special_key_codes` 100/101/102/103; `_invoke_key` reads `key_mappings`; `_special` is the Python handler reached only via `PParse`).
- `pymol-src/modules/pymol/controlling.py:719-797` (`set_key`; validation at 778-789 accepts up/down; `_self.key_mappings[key] = fn` at 795).
- `pymol-src/modules/pymol/wizard/__init__.py:6-16,49-56,82-86` (event-mask constants; `get_event_mask` default 1+2; `do_key`/`do_special` default None).
- `pymol-src/modules/pymol/wizarding.py:110-164` (`set_wizard`/`get_wizard` — C-dispatched via `_cmd`).
- `pymol-src/modules/pymol/shortcut_manager.py:21,33-139` (`reserved_keys` incl. 'up','down'; enforced ONLY in `create_new_shortcut`, not `set_key`).
- `pymol-src/modules/pymol/shortcut_dict.py:11-12` (default left/right = frame step).
- `pymol-src/modules/pymol/keyboard.py:87-93` (`get_default_keys` from `shortcut_dict_ref`).
- `pymol-src/modules/pmg_qt/keymapping.py:19-97` (Qt arrows → 100/101/102/103, state=-2 special).
- `pymol-src/modules/pmg_qt/pymol_qt_gui.py:31,50-54,218-219,400-453` (PyMOLQtGUI QMainWindow; keyPressEvent → `pymolwidget.pymol.button`; lineedit/pymolwidget eventFilters; lineedit Up/Down history).
- `pymol-src/modules/pmg_qt/pymol_gl_widget.py:25-36,110` (viewer is Qt GL widget; `Qt.ClickFocus`).
- `tmp/spike_probe/probe_input.py` — empirical probe run 2026-09-12 (output excerpts above). Syntax `python3.6 -m py_compile` OK; run via `cmd.exe /c C:\\src\\run-conda-pymol.bat -cq`.

### Secondary (MEDIUM — prior repo research, cross-referenced)
- `.planning/research/STACK.md` §4 (wizard-key mechanism; C-dispatch-order claim — re-verified directly above from the C++ source).
- `.planning/research/PITFALLS.md` #4 (arrow-key pitfalls; #4.2 focus, #4.3 leaked rebinds), #9 (epoch/teardown), #5 (modal/pause).
- `.planning/research/ARCHITECTURE.md` F11-F13, Pattern 5 (key bindings + event-filter fallback).
- `tmp/bioCHEMeleon/biochemeleon/wizard.py:86-92` (wizard lifecycle save/restore precedent — bioCHEMeleon used `do_pick`/`do_select`, NOT `do_special`; lifecycle pattern only).
- `serpentrum/game_engine.py:311-365,560-718` (`request_direction` API, `step` tick-boundary semantics — the steering seam contract).
- `serpentrum/pymol_bridge.py`, `serpentrum/gui.py:28`, `serpentrum/__init__.py` (current BRIDGE/GUI/ENTRY structure; purity classes).
- `tools/check_purity.py:56-65,76-84` (BRIDGE_MODULES / GUI_MODULES allowlists — `input.py` placement).

### Tertiary (LOW — not relied upon for any claim)
- `layer1/Ortho.cpp:314-402` — referenced via STACK.md §4.4 for the `OrthoSpecial`/`OrthoArrowsGrabbed` cosmetic side effect (not read line-by-line in this spike; the unconditional `OrthoSpecial` call for up/down is read directly at `PyMOL.cpp:2324`).

---

*Input spike for Phase 4: serpentrum — arrow-key steering mechanism.*
*Researched: 2026-09-12. Valid for: PyMOL 2.5.0 open-source (the installed Windows conda build).*
