"""serpentrum.input — keyboard steering via a PyMOL Wizard (BRIDGE purity).

THE VERIFIED DISPATCH CHAIN (04-RESEARCH-input.md W1-W8, 2026-09-12):
a real keypress reaches the C layer as
PyMOLQtGUI.keyPressEvent -> keymapping.keyPressEventToPyMOLButtonArgs
(arrows -> GLUT codes 100/101/102/103, state=-2) ->
pymolwidget.pymol.button -> C PyMOL_Special (layer5/PyMOL.cpp:2310-2344)
-> WizardDoSpecial FIRST (line 2318) -> cmd.get_wizard().do_special(k,x,y,mod).

WHY THE WIZARD AND NOT set_key: the C PyMOL_Special switch
(PyMOL.cpp:2320-2336) force-sets grabbed=1 for UP/DOWN unconditionally and
routes them to OrthoSpecial, so the ``if(!grabbed)`` block that would
PParse("_special ...") -> internal._special -> key_mappings is SKIPPED for
up/down. A key binding registered for 'up' or 'down' via the set_key API
is therefore stored in cmd.key_mappings but NEVER invoked on real
keypresses (S2). For left/right the same API mutates the SESSION-GLOBAL
cmd.key_mappings dict, leaking a binding that breaks the user's arrow keys
outside the game until PyMOL restarts (S5). The wizard route receives all
four arrows via do_special (the ONLY idiomatic route that gets up/down)
and restores cleanly via cmd.set_wizard(prior) with zero key_mappings
mutation.

THE TRAP WARNING: calling internal._special(code, 0, 0, 0) directly (the
PYTHON handler) fires any stored set_key-style callbacks for ALL FOUR
arrows including up/down. That is misleading — internal._special is only
reached via the PParse inside ``if(!grabbed)``, which the C layer never
enters for up/down. A headless result from internal._special is NEVER
evidence of up/down bindability.

Steering seam contract (stateless input layer): do_special maps the GLUT
code to a direction NAME and forwards it to the injected steer callback —
the controller binds engine.request_direction, which buffers max-1 at the
tick boundary (game_engine.py:311-365). The steer return value is IGNORED
(False for 180-degree / same-direction / buffer-full is the ENGINE's
authority, not ours). do_special ALWAYS returns True: the grab suppresses
the left/right movie-frame-step default (W4); for up/down the C-layer
grab is unconditional anyway.

Pause semantics (PITFALLS.md #4; research open-q 5 resolution): the wizard
STAYS installed during pause — set_active(False) makes do_special
grab-but-no-op, so paused arrows neither steer nor step movie frames. The
wizard tears down only at game-over / restart / quit.

Lifecycle uniformity (Q5 note): install returns the displaced prior wizard
(an opaque handle); teardown(handle=None) accepts-but-ignores the handle
argument so GameTab code is route-agnostic — if plan 04-07's human-verify
mandates the Qt eventFilter fallback (gui_input.py), the swap is a
one-line import change because BOTH routes offer
install(steer_fn)/set_active(active)/teardown(handle) and return opaque
handles.

BRIDGE purity statement: this module imports pymol.wizard + pymol.cmd at
module level — legal ONLY because tools/check_purity.py lists
serpentrum/input.py in BRIDGE_MODULES (pre-registered by plan 04-01).
PyQt5 / numpy are NEVER imported here (Qt stays in GUI modules);
.exec_() is never called (the bridge builds no dialogs). python3.6
syntax only (%-formatting).
"""

from pymol import cmd
from pymol.wizard import Wizard

# GLUT special-key codes -> engine direction names. do_special receives k
# as the INTEGER (internal.special_key_codes, internal.py:414-417; W3).
_CODE_TO_DIR = {100: 'left', 101: 'up', 102: 'right', 103: 'down'}


class KeySteerWizard(Wizard):
    """Arrow-key steering wizard. Installed only during play rounds.

    do_special is called by the C layer (WizardDoSpecial,
    layer1/Wizard.cpp:472-475) BEFORE the set_key/_special path. The
    event-mask override is MANDATORY: the Wizard base returns pick+select
    (1+2) and do_special never fires without event_mask_special (8)
    (Wizard.cpp:465 isEventType(cWizEventSpecial); W1/pitfall 2).
    """

    def __init__(self, steer_fn, _self=cmd):
        Wizard.__init__(self, _self)
        # steer_fn: callable(name) -> return IGNORED. The controller binds
        # engine.request_direction; holding it as a callback keeps this
        # module decoupled from game_engine internals (stateless input).
        self._steer = steer_fn
        # Pause gate: set_active(False) makes do_special grab-but-no-op.
        self._active = True

    def get_event_mask(self):
        # key (4) + special (8) = 12. Verified CLASS attributes
        # (pymol/wizard/__init__.py:6-9); mask 12 probed WIZARD_BUILT.
        return Wizard.event_mask_key + Wizard.event_mask_special

    def get_prompt(self):
        # Focus mitigation (Q3 (a)): the wizard only receives keys while
        # the 3D viewer holds focus.
        return 'serpentrum: click the 3D viewer, then steer with arrow keys'

    def get_panel(self):
        return [[1, 'serpentrum', ''],
                [2, 'Quit game', 'cmd.set_wizard()']]

    def do_special(self, k, x, y, mod):
        """Map the GLUT code + forward to steer; ALWAYS grab (return True).

        Unmapped codes (e.g. F1=1) no-op without crashing (pitfall 7).
        While paused (_active False) the key is still grabbed but never
        forwarded — no steering and no movie-frame-step leak.
        """
        name = _CODE_TO_DIR.get(int(k))
        if name is not None and self._active:
            self._steer(name)   # -> engine.request_direction(name)
        return True


# --- lifecycle (GameTab calls these; plan 04-08 wires them) -----------------

def install(steer_fn):
    """Install the steering wizard; return the displaced prior wizard.

    Idempotent (pitfalls 5/6: wizard displacement + singleShot double-fire
    safety): if a KeySteerWizard is already active, return ITS saved prior
    WITHOUT re-installing. The returned handle is opaque to callers.
    """
    prior = cmd.get_wizard()
    if isinstance(prior, KeySteerWizard):
        return getattr(prior, '_saved_wizard', None)
    wiz = KeySteerWizard(steer_fn)
    wiz._saved_wizard = prior
    cmd.set_wizard(wiz)
    cmd.refresh_wizard()
    return prior


def set_active(active):
    """Pause/resume steering WITHOUT tearing the wizard down.

    False: do_special grabs-but-no-ops (paused arrows steer nothing and
    step no movie frames). True: steering resumes. No-op when the active
    wizard is not ours (foreign wizard stay-respect policy).
    """
    wiz = cmd.get_wizard()
    if isinstance(wiz, KeySteerWizard):
        wiz._active = bool(active)


def teardown(handle=None):
    """Restore the wizard displaced by install (or clear to None).

    ``handle`` is accepted-and-IGNORED (route-swap uniformity with the
    eventFilter fallback, whose teardown needs its filter object: both
    routes then expose teardown(handle) so GameTab stays route-agnostic).
    Idempotent: no wizard or a foreign wizard active -> no-op. Restores by
    reading the SAVED prior off the live wizard — never the caller's
    handle — so repeated teardown is safe. NEVER touches cmd.key_mappings.
    """
    wiz = cmd.get_wizard()
    if isinstance(wiz, KeySteerWizard):
        cmd.set_wizard(getattr(wiz, '_saved_wizard', None))
        cmd.refresh_wizard()
