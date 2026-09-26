"""Headless Windows PyMOL chain atom-count smoke — 06-04 (SPECTRA-06).

Run (from repo root; cwd is /mnt/c-backed so cmd.exe inherits C:\\ cwd):
    timeout 90 cmd.exe /c "C:\\src\\run-conda-pymol.bat -cq smoke\\10_chain_count_smoke.py"

Exit codes through the .bat are ALWAYS 0 (even after a Qt C-abort) —
verdicts are flushed sentinels grepped by tests/run_gates.py --smoke:
    SMOKE-OK CHAIN-COUNT    all steps passed
    SMOKE-FAIL <step>: ...  a step failed (one line per failure)

Proves the bridge count channel (SPECTRA-06 cross-check, plan 06-09):
  1. chain_atom_counts(names) returns len(cmd.get_model(name).atom) per
     object, in INPUT order, via get_model (the verified-safe reader).
  2. Counts cross-pin to the manifest atom_count values loaded in place:
     benzene 12, naphthalene 18 (serpentrum/data/manifest.json — the
     same validated field setloader carries, setloader.py:108-109).
  3. A MISSING object yields 0 (documented desync signal for the budget
     guard), never raises — a stale scene warns, never crashes launch.
  4. cleanup_srp removes the srp_* chain objects it loaded.

EQ-xyz-1: counts ONLY. No coordinate export is pinned here — run-input
coords come from the engine atoms (plans 06-02/06-06), never re-read
from the viewer.

Template rules (copied from smoke/01_skeleton_smoke.py):
  - every print carries flush=True (stdout is block-buffered when piped)
  - NO widget construction (headless C-abort is uncatchable)
  - never add smoke/__init__.py (findPlugins plugin-path safety)
  - NEVER trust __file__ under -cq (resolve ROOT by validating
    serpentrum/__init__.py candidates)
  - verdict = flushed SMOKE-OK/SMOKE-FAIL sentinels ONLY (never exit codes)
"""
import importlib
import json
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

DATA_DIR = os.path.join(ROOT, 'serpentrum', 'data')
MANIFEST = os.path.join(DATA_DIR, 'manifest.json')


def check(name, fn):
    try:
        fn()
        print('SMOKE-STEP OK  %s' % name, flush=True)
    except Exception as exc:
        print('SMOKE-FAIL %s: %r' % (name, exc), flush=True)
        FAILURES.append(name)


def _manifest_atom_count(mol_id):
    """atom_count for molecule ``mol_id`` from the in-place manifest
    (the same validated field setloader carries, setloader.py:108-109)."""
    with open(MANIFEST, 'r') as fh:
        data = json.load(fh)
    for mol_set in data['sets']:
        for mol in mol_set['molecules']:
            if mol['id'] == mol_id:
                return mol['atom_count']
    raise AssertionError('manifest has no molecule %r' % mol_id)


def s_bridge_import():
    # Bridge import under the loader name path (smoke 01 pattern): the
    # plugin loads as pmg_tk.startup.serpentrum; the bridge is a
    # submodule of that same tree.
    import pmg_tk.startup
    if ROOT not in pmg_tk.startup.__path__:
        pmg_tk.startup.__path__.append(ROOT)
    mod = importlib.import_module('pmg_tk.startup.serpentrum.pymol_bridge')
    assert callable(mod.chain_atom_counts), 'chain_atom_counts missing'
    assert callable(mod.chain_object_names), 'chain_object_names missing'
    assert callable(mod.cleanup_srp), 'cleanup_srp missing'


def s_load_head():
    # Clean slate first: a stale srp_* scene must not leak into the
    # count assertions.
    pymol_bridge.cleanup_srp()
    cmd.load(os.path.join(DATA_DIR, 'benzene.sdf'), object='srp_head',
             zoom=0)
    names = pymol_bridge.chain_object_names()
    assert names == ['srp_head'], 'unexpected chain names %r' % (names,)


def s_count_head():
    counts = pymol_bridge.chain_atom_counts(['srp_head'])
    assert counts == [12], 'benzene count %r != [12]' % (counts,)
    pinned = _manifest_atom_count('benzene')
    assert pinned == 12, 'manifest benzene atom_count %r != 12' % (pinned,)
    assert counts[0] == pinned, 'bridge %r != manifest %r' % (counts[0],
                                                             pinned)


def s_load_segment_count():
    cmd.load(os.path.join(DATA_DIR, 'naphthalene.sdf'),
             object='srp_seg_0', zoom=0)
    names = pymol_bridge.chain_object_names()
    assert names == ['srp_head', 'srp_seg_0'], \
        'unexpected chain names %r' % (names,)
    counts = pymol_bridge.chain_atom_counts(names)
    assert counts == [12, 18], 'chain counts %r != [12, 18]' % (counts,)
    pinned = _manifest_atom_count('naphthalene')
    assert pinned == 18, \
        'manifest naphthalene atom_count %r != 18' % (pinned,)
    assert counts[1] == pinned, 'bridge %r != manifest %r' % (counts[1],
                                                              pinned)


def s_missing_object_zero():
    # DOCUMENTED policy: a vanished object is a desync signal (0), never
    # a crash — the launch cross-check must survive a stale scene.
    counts = pymol_bridge.chain_atom_counts(['srp_seg_99'])
    assert counts == [0], 'missing-object counts %r != [0]' % (counts,)


def s_cleanup():
    n = pymol_bridge.cleanup_srp()
    assert n == 2, 'cleanup_srp deleted %d, expected 2' % n
    names = pymol_bridge.chain_object_names()
    assert names == [], 'chain objects remain after cleanup: %r' % (names,)


for _name, _fn in [
    ('bridge_import', s_bridge_import),
    ('load_head', s_load_head),
    ('count_head', s_count_head),
    ('load_segment_count', s_load_segment_count),
    ('missing_object_zero', s_missing_object_zero),
    ('cleanup', s_cleanup),
]:
    check(_name, _fn)

if FAILURES:
    print('SMOKE-END %d failure(s)' % len(FAILURES), flush=True)
else:
    print('SMOKE-OK CHAIN-COUNT', flush=True)
