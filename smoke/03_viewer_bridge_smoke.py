"""Headless Windows PyMOL viewer-bridge smoke — 03-06.

Run (from repo root; cwd is /mnt/c-backed so cmd.exe inherits C:\\ cwd):
    timeout 90 cmd.exe /c "C:\\src\\run-conda-pymol.bat -cq smoke\\03_viewer_bridge_smoke.py"

Exit codes through the .bat are ALWAYS 0 (even after a Qt C-abort) —
verdicts are flushed sentinels grepped by tests/run_gates.py --smoke:
    SMOKE-OK VIEWER-BRIDGE    all steps passed
    SMOKE-FAIL <step>: ...    a step failed (one line per failure)

Proves the viewer contract end-to-end (03-RESEARCH-viewer-bridge.md
sec 4.4 — the three verify-at-execution claims):
  1. CGO + molecule objects survive .pse save/reload (Pitfall 8.3).
  2. cmd.delete('srp_*') removes exactly the srp-prefixed objects
     (wildcard semantics — discharged [ASSUMPTION] from sec 1.4).
  3. A non-srp sentinel object survives cleanup untouched.
  4. materialize(setup, records) produces exactly srp_box + srp_head.

Template rules (copied from smoke/01_skeleton_smoke.py):
  - every print carries flush=True (stdout is block-buffered when piped)
  - NO widget construction (headless C-abort is uncatchable)
  - never add smoke/__init__.py (findPlugins plugin-path safety)
  - NEVER trust __file__ under -cq (resolve ROOT by validating
    serpentrum/__init__.py candidates)
  - verdict = flushed SMOKE-OK/SMOKE-FAIL sentinels ONLY (never exit codes)

Test data: tests/fixtures/molfile/methane.sdf is a hand-written V2000 SDF
(test data, not a chemistry claim). It serves as both the head molecule
and the non-srp sentinel object.
"""
import os
import sys
import tempfile


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
from serpentrum import pymol_bridge, setup_logic  # noqa: E402

FAILURES = []

FIXTURE = os.path.join(ROOT, 'tests', 'fixtures', 'molfile', 'methane.sdf')


def check(name, fn):
    try:
        fn()
        print('SMOKE-STEP OK  %s' % name, flush=True)
    except Exception as exc:
        print('SMOKE-FAIL %s: %r' % (name, exc), flush=True)
        FAILURES.append(name)


def s_box_load():
    """load_box('medium') creates srp_box CGO in the viewer."""
    pymol_bridge.load_box('medium')
    names = cmd.get_names('public_objects')
    assert 'srp_box' in names, 'srp_box not found after load_box'


def s_head_load():
    """load_molecule + show spheres + place_head for the head."""
    pymol_bridge.load_molecule(FIXTURE, 'srp_head')
    names = cmd.get_names('public_objects')
    assert 'srp_head' in names, 'srp_head not found after load_molecule'
    cmd.show('spheres', 'srp_head')
    pymol_bridge.place_head()  # centering is polish; no position assert


def s_sentinel():
    """Load a non-srp sentinel object to prove wildcard cleanup."""
    cmd.load(FIXTURE, object='user_mol')
    names = cmd.get_names('public_objects')
    assert 'user_mol' in names, 'user_mol sentinel not loaded'


def s_pse_survival():
    """CGO + molecule survive .pse save/reload (Pitfall 8.3)."""
    session = os.path.join(tempfile.gettempdir(), 'srp_smoke_session.pse')
    cmd.save(session)
    cmd.delete('srp_*')
    names = cmd.get_names('public_objects')
    assert 'srp_box' not in names, 'srp_box survived delete before reload'
    assert 'srp_head' not in names, 'srp_head survived delete before reload'
    cmd.load(session)
    names = cmd.get_names('public_objects')
    assert 'srp_box' in names, 'srp_box did not survive .pse reload'
    assert 'srp_head' in names, 'srp_head did not survive .pse reload'


def s_cleanup_wildcard():
    """cleanup_srp deletes exactly srp_* objects; sentinel survives."""
    n = pymol_bridge.cleanup_srp()
    assert n == 2, 'cleanup_srp returned %d, expected 2' % n
    names = cmd.get_names('public_objects')
    assert 'srp_box' not in names, 'srp_box survived cleanup_srp'
    assert 'srp_head' not in names, 'srp_head survived cleanup_srp'
    assert 'user_mol' in names, 'user_mol did not survive cleanup_srp'


def s_materialize():
    """materialize(setup, records) produces srp_box + srp_head."""
    records = [{'id': 'methane', 'name': 'Methane', 'file': FIXTURE}]
    setup = setup_logic.new_setup()
    errs = pymol_bridge.materialize(setup, records)
    assert errs == [], 'materialize returned errors: %r' % errs
    names = cmd.get_names('public_objects')
    assert 'srp_box' in names, 'srp_box not found after materialize'
    assert 'srp_head' in names, 'srp_head not found after materialize'
    n2 = pymol_bridge.cleanup_srp()
    assert n2 == 2, 'cleanup after materialize returned %d, expected 2' % n2
    names = cmd.get_names('public_objects')
    assert 'user_mol' in names, 'user_mol lost after materialize+cleanup'


for _name, _fn in [
    ('box_load', s_box_load),
    ('head_load', s_head_load),
    ('sentinel', s_sentinel),
    ('pse_survival', s_pse_survival),
    ('cleanup_wildcard', s_cleanup_wildcard),
    ('materialize', s_materialize),
]:
    check(_name, _fn)

if FAILURES:
    print('SMOKE-END %d failure(s)' % len(FAILURES), flush=True)
else:
    print('SMOKE-OK VIEWER-BRIDGE', flush=True)
