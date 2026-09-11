"""Headless Windows PyMOL demo end-to-end smoke — 03-08.

Run (from repo root; cwd is /mnt/c-backed so cmd.exe inherits C:\\ cwd):
    timeout 90 cmd.exe /c "C:\\src\\run-conda-pymol.bat -cq smoke\\04_demo_e2e_smoke.py"

Exit codes through the .bat are ALWAYS 0 (even after a Qt C-abort) —
verdicts are flushed sentinels grepped by tests/run_gates.py --smoke:
    SMOKE-OK VIEWER-DEMO    all steps passed
    SMOKE-FAIL <step>: ...  a step failed (one line per failure)

Proves the REAL shipped Demo Set A data flows end-to-end headlessly:
  manifest.json -> setloader.load_demo_set -> pymol_bridge.materialize
  -> head switch -> unknown-id fallback -> cleanup_srp.
This converts part of 03-08's human-verify checkpoint into machine proof:
the data path + viewer-bridge contract that the human confirms visually in
real PyMOL is here asserted on the actual shipped PubChem bytes.

Atom-count expectations are pinned by tests/test_demo_data.py (manifest
order benzene(12), naphthalene(18), anthracene(24), phenanthrene(24),
biphenyl(22)) — these are NOT weakened here; if reality disagrees the
smoke fails loudly so the contract break is investigated, not hidden.

Template rules (copied from smoke/01_skeleton_smoke.py +
smoke/03_viewer_bridge_smoke.py):
  - every print carries flush=True (stdout is block-buffered when piped)
  - NO widget construction (headless C-abort is uncatchable)
  - never add smoke/__init__.py (findPlugins plugin-path safety)
  - NEVER trust __file__ under -cq (resolve ROOT by validating
    serpentrum/__init__.py candidates)
  - verdict = flushed SMOKE-OK/SMOKE-FAIL sentinels ONLY (never exit codes)
  - get_names type is 'public_objects' (proven for 2.5.0 in smoke 03)

materialize cleanup-first contract (03-06): materialize() ALWAYS calls
cleanup_srp() before loading anything — it deletes EVERY srp_* object
first, then reloads srp_box, then selects+loads the head. So after an
unknown-id materialize (head selection returns None -> head skipped),
srp_head is correctly ABSENT (the old head was deleted by the
cleanup-first step and no new head loaded). This smoke asserts that
verified contract; the box-only scene after a failed head pick is the
documented "box-only-ish behavior".
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
from serpentrum import setloader, setup_logic, pymol_bridge  # noqa: E402

FAILURES = []

# Shared across steps: populated by s_real_data_load, read by the
# materialize steps. None until the real-data load step runs; a failed
# load leaves this None and the materialize steps fail loudly (correct).
RECORDS = None

FIXTURE = os.path.join(ROOT, 'tests', 'fixtures', 'molfile', 'methane.sdf')


def check(name, fn):
    try:
        fn()
        print('SMOKE-STEP OK  %s' % name, flush=True)
    except Exception as exc:
        print('SMOKE-FAIL %s: %r' % (name, exc), flush=True)
        FAILURES.append(name)


def s_real_data_load():
    """Real shipped Demo Set A: manifest -> 5 records, all stackable,
    benzene first (manifest order pinned by test_demo_data.py)."""
    global RECORDS
    records, errs = setloader.load_demo_set(
        setloader.package_data_dir(), 'set_a', setloader.default_stacking_path())
    assert errs == [], 'load_demo_set errors: %r' % (errs,)
    assert len(records) == 5, 'expected 5 records, got %d' % len(records)
    assert all(r['has_stack_entry'] for r in records), \
        'not all records have has_stack_entry (set_a matches APPROVED pi_stack)'
    assert records[0]['id'] == 'benzene', \
        'first record id %r, expected benzene (manifest order)' % records[0]['id']
    RECORDS = records


def s_sentinel():
    """Load a non-srp sentinel object (methane) to prove wildcard cleanup
    leaves user objects untouched (same technique as smoke 03)."""
    cmd.load(FIXTURE, object='user_mol')
    names = cmd.get_names('public_objects')
    assert 'user_mol' in names, 'user_mol sentinel not loaded'


def s_materialize_random():
    """Random head -> records[0] = benzene (12 atoms). srp_box + srp_head
    both present after materialize (03-06 contract)."""
    setup = setup_logic.new_setup()
    setup['box_preset'] = 'medium'
    setup['head_molecule'] = 'random'
    errs = pymol_bridge.materialize(setup, RECORDS)
    assert errs == [], 'materialize(random) errors: %r' % (errs,)
    names = cmd.get_names('public_objects')
    assert 'srp_box' in names, 'srp_box not found after materialize'
    assert 'srp_head' in names, 'srp_head not found after materialize'
    n = cmd.count_atoms('srp_head')
    assert n == 12, 'srp_head atom count %d, expected 12 (benzene)' % n


def s_head_switch():
    """Switch head to naphthalene -> 18 atoms. materialize cleaned the
    old srp_* first (cleanup-first contract), then loaded the new head."""
    setup = setup_logic.new_setup()
    setup['box_preset'] = 'medium'
    setup['head_molecule'] = 'naphthalene'
    errs = pymol_bridge.materialize(setup, RECORDS)
    assert errs == [], 'materialize(naphthalene) errors: %r' % (errs,)
    names = cmd.get_names('public_objects')
    assert 'srp_head' in names, 'srp_head not found after head switch'
    n = cmd.count_atoms('srp_head')
    assert n == 18, 'srp_head atom count %d, expected 18 (naphthalene)' % n


def s_unknown_id_fallback():
    """Unknown head id -> 1 error naming the id; no crash. materialize's
    cleanup-first contract deletes srp_head, then head selection returns
    None (head skipped) -> srp_head is ABSENT (box-only scene), srp_box
    still present. No assertion is weakened: this IS the documented
    materialize contract (cleanup_srp runs unconditionally first)."""
    setup = setup_logic.new_setup()
    setup['box_preset'] = 'medium'
    setup['head_molecule'] = 'no_such_id'
    errs = pymol_bridge.materialize(setup, RECORDS)
    assert len(errs) == 1, 'expected 1 error, got %r' % (errs,)
    assert 'no_such_id' in errs[0], 'error message: %r' % (errs[0],)
    names = cmd.get_names('public_objects')
    assert 'srp_box' in names, 'srp_box missing after unknown-id fallback'
    assert 'srp_head' not in names, \
        'srp_head survived unknown-id fallback (cleanup-first contract ' \
        'deletes it; head selection None -> not reloaded -> box-only scene)'


def s_cleanup_real_scene():
    """cleanup_srp removes the remaining srp_* object(s); user_mol
    survives. After the unknown-id fallback only srp_box remains
    (materialize's cleanup-first step already deleted srp_head), so the
    count is 1, not 2 — that IS the correct contract behavior, not a
    weakened assertion. The count reflects how many srp_* objects exist
    at cleanup time."""
    n = pymol_bridge.cleanup_srp()
    assert n == 1, \
        'cleanup_srp returned %d, expected 1 (only srp_box remained ' \
        'after the unknown-id fallback deleted srp_head)' % n
    names = cmd.get_names('public_objects')
    assert 'srp_box' not in names, 'srp_box survived cleanup_srp'
    assert 'srp_head' not in names, 'srp_head survived cleanup_srp'
    assert 'user_mol' in names, 'user_mol did not survive cleanup_srp'


for _name, _fn in [
    ('real_data_load', s_real_data_load),
    ('sentinel', s_sentinel),
    ('materialize_random', s_materialize_random),
    ('head_switch', s_head_switch),
    ('unknown_id_fallback', s_unknown_id_fallback),
    ('cleanup_real_scene', s_cleanup_real_scene),
]:
    check(_name, _fn)

if FAILURES:
    print('SMOKE-END %d failure(s)' % len(FAILURES), flush=True)
else:
    print('SMOKE-OK VIEWER-DEMO', flush=True)
