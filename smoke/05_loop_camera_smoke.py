"""Headless Windows PyMOL loop-camera smoke — 04-03.

Run (from repo root; cwd is /mnt/c-backed so cmd.exe inherits C:\\ cwd):
    timeout 90 cmd.exe /c "C:\\src\\run-conda-pymol.bat -cq smoke\\05_loop_camera_smoke.py"

Exit codes through the .bat are ALWAYS 0 (even after a Qt C-abort) —
verdicts are flushed sentinels grepped by tests/run_gates.py --smoke:
    SMOKE-OK LOOP-CAMERA    all steps passed
    SMOKE-FAIL <step>: ...  a step failed (one line per failure)

Machine-proves the Phase-4 game-loop cmd seams live in pymol_bridge
(04-RESEARCH-gameloop.md Q2/Q3 recipes, verbatim):
  move_head_delta  — zero-drift atomic translate, camera=0 (model axes),
                     5 x 0.3 A lands at exactly 1.5 A (probe TL_5TICKS_0.3A,
                     M3); dz=0 contract (2D plane, P3)
  lock_camera      — saves {ortho, view}, ortho on, frames srp_box,
                     button('none') x16 (GAME-02)
  unlock_camera    — cmd.mouse() + ortho + set_view round-trip
  object_exists    — get_names('public_objects') presence guard

Template rules (copied verbatim from smoke/04_demo_e2e_smoke.py):
  - every print carries flush=True (stdout is block-buffered when piped)
  - NO widget construction (headless C-abort is uncatchable)
  - never add smoke/__init__.py (findPlugins plugin-path safety)
  - NEVER trust __file__ under -cq (resolve ROOT by validating
    serpentrum/__init__.py candidates)
  - verdict = flushed SMOKE-OK/SMOKE-FAIL sentinels ONLY (never exit codes)
  - get_names type is 'public_objects' (proven for 2.5.0 in smoke 03)
"""
import os
import sys


def _resolve_root():
    """Repo root, defensively.

    Under -cq exec, __file__ is PyMOL's launcher module (NOT this script),
    so naive dirname(dirname(__file__)) lands in site-packages. Validate
    every candidate by the presence of serpentrum/__init__.py. Copied
    verbatim from smoke/01_skeleton_smoke.py (probe-verified 01-04).
    """
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

FAILURES = []

# Shared across steps: the saved camera state from s_lock_camera is read
# back by s_unlock_camera (the round-trip contract).
SAVED = None

FIXTURE = os.path.join(ROOT, 'tests', 'fixtures', 'molfile', 'methane.sdf')


def check(name, fn):
    try:
        fn()
        print('SMOKE-STEP OK  %s' % name, flush=True)
    except Exception as exc:
        print('SMOKE-FAIL %s: %r' % (name, exc), flush=True)
        FAILURES.append(name)


def s_scene():
    """Box + head scene: srp_box AND srp_head both public objects."""
    pymol_bridge.load_box('medium')
    pymol_bridge.load_molecule(FIXTURE, pymol_bridge.HEAD_NAME)
    pymol_bridge.place_head(pymol_bridge.HEAD_NAME)
    names = cmd.get_names('public_objects')
    assert 'srp_box' in names, 'srp_box not found after load_box'
    assert 'srp_head' in names, 'srp_head not found after load_molecule'


def s_move_zero_drift():
    """5 x move_head_delta(0.3, 0, 0) = EXACTLY 1.5 A in x (probe
    TL_5TICKS_0.3A, M3); y and z extents untouched (dz=0, 2D plane P3)."""
    ext0 = cmd.get_extent(pymol_bridge.HEAD_NAME)
    for _ in range(5):
        pymol_bridge.move_head_delta(0.3, 0.0, 0.0)
    ext1 = cmd.get_extent(pymol_bridge.HEAD_NAME)
    # Tolerance 1e-5: PyMOL stores atomic coords as C floats (32-bit), so
    # the probe M3's exact 1.5 (pseudoatom at exactly 0.0) becomes ~6e-8
    # residual here (methane coords are not float32-exact). 1e-5 still
    # catches real drift/desync (camera-axes bugs are Angstrom-scale).
    dx = ext1[0][0] - ext0[0][0]
    assert abs(dx - 1.5) < 1e-5, 'x drift: dx=%r, expected 1.5' % dx
    assert ext1[0][1] == ext0[0][1] and ext1[1][1] == ext0[1][1], \
        'y extents changed: %r -> %r' % (ext0, ext1)
    assert ext1[0][2] == ext0[0][2] and ext1[1][2] == ext0[1][2], \
        'z extents changed (dz=0 contract broken): %r -> %r' % (ext0, ext1)


def s_lock_camera():
    """lock_camera: pre-lock ortho 'off' (probe C1), post-lock ortho 'on',
    saved view is 18 floats (probe C2), the 16 button('none') calls raise
    nothing (implicit — probe C3 showed zero errors)."""
    global SAVED
    SAVED = pymol_bridge.lock_camera()
    assert SAVED['ortho'] == 'off', \
        'pre-lock ortho %r, expected off (default, probe C1)' % SAVED['ortho']
    assert cmd.get('ortho') == 'on', 'post-lock ortho not on'
    assert len(SAVED['view']) == 18, \
        'saved view has %d floats, expected 18 (probe C2)' % len(SAVED['view'])


def s_unlock_camera():
    """unlock_camera: ortho restored to the saved 'off'; get_view round-
    trips stably (probe VIEW_STABLE). cmd.mouse() restoring the button
    mode defaults is proven here by no-exception ONLY — PyMOL 2.5.0 has
    no per-button read-back API; the real mouse-drag restore verdict is
    human-verify (plan 04-09 checklist)."""
    pymol_bridge.unlock_camera(SAVED)
    assert cmd.get('ortho') == 'off', 'ortho after unlock not off'
    v = cmd.get_view()
    assert v == SAVED['view'], 'view not stable after unlock round-trip'


def s_object_exists():
    """object_exists: True for srp_head, False for a never-loaded name."""
    assert pymol_bridge.object_exists('srp_head') is True
    assert pymol_bridge.object_exists('srp_nope') is False


def s_cleanup():
    """Non-srp sentinel survives cleanup_srp; srp_* all gone (namespace
    hygiene unchanged by the new functions)."""
    cmd.load(FIXTURE, object='user_mol')
    pymol_bridge.cleanup_srp()
    names = cmd.get_names('public_objects')
    assert 'srp_box' not in names, 'srp_box survived cleanup_srp'
    assert 'srp_head' not in names, 'srp_head survived cleanup_srp'
    assert 'user_mol' in names, 'user_mol did not survive cleanup_srp'


for _name, _fn in [
    ('scene', s_scene),
    ('move_zero_drift', s_move_zero_drift),
    ('lock_camera', s_lock_camera),
    ('unlock_camera', s_unlock_camera),
    ('object_exists', s_object_exists),
    ('cleanup', s_cleanup),
]:
    check(_name, _fn)

if FAILURES:
    print('SMOKE-END %d failure(s)' % len(FAILURES), flush=True)
else:
    print('SMOKE-OK LOOP-CAMERA', flush=True)
