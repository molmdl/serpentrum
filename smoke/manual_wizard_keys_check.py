"""REAL-GUI arrow-keys harness — plan 04-07 human-verify (04-04 staging).

This is NOT a headless smoke: the non-NN_ name keeps
tests/run_gates.py --smoke (glob smoke/[0-9][0-9]_*.py) from ever
auto-running it. Run it MANUALLY inside a real Windows PyMOL GUI from the
PyMOL command line:

    run smoke\\manual_wizard_keys_check.py

What it stages (04-RESEARCH-input.md human-verify checklist items 1-4):
  - materializes the medium box + benzene head (demo set A) and frames it
  - installs the KeySteerWizard (serpentrum/input.py) bound to
    engine.request_direction through a logger/nudger — each arrow press
    prints a KEY line and nudges the head 0.3 A so the wizard route is
    VISIBLE without a tick loop (this is exactly the W7 probe; the real
    snake movement arrives with the wired loop in plan 04-08)
  - registers 'srp_keys_off' so the human can restore the prior wizard
    state when done

The human then (checklist order):
  1. clicks the 3D viewer once, presses each arrow -> KEY lines + nudges
     (fail mode: up/down do nothing -> refutes W7 -> eventFilter fallback)
  2. clicks the serpentrum dialog / PyMOL command line, presses arrows ->
     focus-stealing observation (Q3); up/down may scroll command-line
     history (cosmetic, W8)
  3. types srp_keys_off -> restores the prior wizard (W5)

Template rules (per smoke/01_skeleton_smoke.py): flush=True on every
print, NEVER trust __file__ under -cq/exec (resolve ROOT defensively),
NO widget construction.
"""
import os
import sys


def _resolve_root():
    """Repo root, defensively (identical to the smoke template)."""
    candidates = []
    if '__file__' in globals():
        _f = os.path.abspath(__file__)
        candidates.append(os.path.dirname(os.path.dirname(_f)))
        candidates.append(os.path.dirname(_f))
    candidates.append(os.getcwd())
    for _c in candidates:
        if os.path.isfile(os.path.join(_c, 'serpentrum', '__init__.py')):
            return _c
    return os.getcwd()


ROOT = _resolve_root()
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from pymol import cmd  # noqa: E402 (available inside PyMOL runtime)
from serpentrum import pymol_bridge  # noqa: E402
from serpentrum import setup_logic  # noqa: E402
from serpentrum import setloader  # noqa: E402
from serpentrum import game_engine  # noqa: E402
from serpentrum import input as srp_input  # noqa: E402

# --- scene: medium box + demo head, framed ---------------------------------
records, errs = setloader.load_demo_set(
    setloader.package_data_dir(), 'set_a',
    setloader.default_stacking_path())
assert not errs, 'demo set failed to load: %r' % (errs,)
setup = setup_logic.new_setup()
pymol_bridge.materialize(setup, records)
print('HARNESS scene: srp_box + %s materialized (medium box)'
      % pymol_bridge.HEAD_NAME, flush=True)

# --- engine seam: medium box bounds, heading 'right' (same as the game) ----
(x0, y0), (x1, y1) = setup_logic.BOX_PRESETS['medium']
engine = game_engine.GameEngine(head=(0.0, 0.0), heading='right',
                                box_min=(x0, y0), box_max=(x1, y1))


def _steer(name):
    """The wizard's steer callback: forward to the engine + nudge visibly.

    ``engine.request_direction`` is the real seam contract (unknown name
    raises ValueError; 180-degree / same-direction / buffer-full return
    False — expected here sequentially since no tick loop drains the
    buffer). The 0.3 A nudge makes the WIZARD ROUTE visible per keypress;
    it is NOT the game movement (that arrives with the tick loop).
    """
    ok = engine.request_direction(name)
    d = game_engine.DIRS[name]
    pymol_bridge.move_head_delta(d[0] * 0.3, d[1] * 0.3, 0.0)
    print('KEY %-5s -> request_direction=%s (head nudged 0.3 A; False = '
          'engine refused: reversal/same/buffer-full)' % (name, ok),
          flush=True)


prior = srp_input.install(_steer)
print('HARNESS prompt: %s' % cmd.get_wizard().get_prompt(), flush=True)
print('HARNESS prior wizard saved: %r (restored by srp_keys_off)'
      % (prior,), flush=True)
print('HARNESS how to probe:', flush=True)
print('  1. click the 3D viewer once, then press LEFT/UP/RIGHT/DOWN '
      '-> watch KEY lines + head nudges', flush=True)
print('  2. click the serpentrum dialog or the PyMOL command line, press '
      'arrows -> the focus test (up/down may scroll history, cosmetic)',
      flush=True)


def _keys_off():
    """Restore the prior wizard; the human runs 'srp_keys_off' in PyMOL."""
    srp_input.teardown()
    print('keys OFF — wizard now: %r' % (cmd.get_wizard(),), flush=True)


cmd.extend('srp_keys_off', _keys_off)

print('HARNESS READY — steer with arrows after clicking the viewer; '
      'type srp_keys_off to restore.', flush=True)
