"""Headless Windows PyMOL transform/sweep/completion smoke — 05-07.

Run (from repo root; cwd is /mnt/c-backed so cmd.exe inherits C:\\ cwd):
    timeout 90 cmd.exe /c "C:\\src\\run-conda-pymol.bat -cq smoke\\07_transform_sweep_smoke.py"

Exit codes through the .bat are ALWAYS 0 (even after a Qt C-abort) —
verdicts are flushed sentinels grepped by tests/run_gates.py --smoke:
    SMOKE-OK TRANSFORM    probe-A1 regression: apply_matrix TTT layout
    SMOKE-OK SWEEP        probe-B regression: rigid 6-tick 90 deg sweep
    SMOKE-OK COMPLETION   rename / list / zoom / pickup pattern-delete
    SMOKE-FAIL <step>     a step failed (traceback follows, sentinel
                          withheld — a failed step simply omits it)
    SMOKE-07 DONE         the script reached the end (any state)

REQUIRED smoke (registered in tests/run_gates.py REQUIRED_SMOKES).
Replicates probes A1/B/C/G of 05-RESEARCH-pymol-mechanics.md as
regression for the Phase-5 bridge primitives (G7 part 1) — the
mechanisms are researcher-VERIFIED; this smoke wires-as-is, no
re-spiking.

Template rules (copied verbatim from smoke/05_loop_camera_smoke.py):
  - every print carries flush=True (stdout is block-buffered when piped)
  - NO widget construction (headless C-abort is uncatchable)
  - never add smoke/__init__.py (findPlugins plugin-path safety)
  - NEVER trust __file__ under -cq (resolve ROOT by validating
    serpentrum/__init__.py candidates)
  - verdict = flushed SMOKE-OK/SMOKE-FAIL sentinels ONLY (never exit codes)
  - get_names type is 'public_objects' (proven for 2.5.0 in smoke 03)

The m16 below is built INLINE as a 16-float literal (the probe-A1
fixture) — this smoke pins the RAW PyMOL TTT layout WITHOUT importing
the pure orientation layer (plan 05-02, separate branch).
"""
import os
import sys
import traceback


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

BENZENE = os.path.join(ROOT, 'serpentrum', 'data', 'benzene.sdf')

# Probe-A1 fixture, INLINE (no orientation import): RotZ(90 deg) row-
# major on a COLUMN vector, post-translation t=(1,2,3), pre=(0,0,0).
# Layout: rows 0-2 cols 0-2 = R; m[3],m[7],m[11] = post-t; m[12..14] =
# pre. y = R.x + t, so (x,y,z) -> (-y+1, x+2, z+3) (5-RESEARCH probe A1,
# max err 1.2e-07 A end-to-end).
M16_A1 = [0.0, -1.0, 0.0, 1.0,
          1.0, 0.0, 0.0, 2.0,
          0.0, 0.0, 1.0, 3.0,
          0.0, 0.0, 0.0, 1.0]


def check(name, fn):
    """Run one named step; flush its sentinel ONLY on success."""
    try:
        fn()
        print('SMOKE-OK %s' % name, flush=True)
    except Exception:
        print('SMOKE-FAIL %s (sentinel withheld):' % name, flush=True)
        sys.stdout.write(traceback.format_exc())
        sys.stdout.flush()
        FAILURES.append(name)


def _atoms(name):
    """[(x, y, z), ...] for every atom of object ``name``."""
    model = cmd.get_model(name)
    return [(a.coord[0], a.coord[1], a.coord[2]) for a in model.atom]


def _centroid(atoms):
    n = float(len(atoms))
    return (sum(a[0] for a in atoms) / n,
            sum(a[1] for a in atoms) / n,
            sum(a[2] for a in atoms) / n)


def _diameter(atoms):
    """Atom-set diameter (max pairwise distance) — rigidity probe."""
    best = 0.0
    for ax, ay, az in atoms:
        for bx, by, bz in atoms:
            d = ((ax - bx) ** 2 + (ay - by) ** 2 + (az - bz) ** 2) ** 0.5
            if d > best:
                best = d
    return best


def s_transform():
    """TRANSFORM (probe A1 regression): apply_matrix with the INLINE
    RotZ(90)+t(1,2,3) fixture maps every atom (x,y,z) -> (-y+1, x+2,
    z+3) to <=1e-4 A."""
    pymol_bridge.cleanup_srp()
    pymol_bridge.load_molecule(BENZENE, 'srp_tmpA')
    before = _atoms('srp_tmpA')
    pymol_bridge.apply_matrix('srp_tmpA', M16_A1)
    after = _atoms('srp_tmpA')
    assert len(before) == len(after), \
        'atom count changed: %d -> %d' % (len(before), len(after))
    for (x0, y0, z0), (x1, y1, z1) in zip(before, after):
        expected = (-y0 + 1.0, x0 + 2.0, z0 + 3.0)
        for got, want, axis in zip((x1, y1, z1), expected, 'xyz'):
            assert abs(got - want) <= 1e-4, \
                'TTT layout: (%r,%r,%r) -> %s=%r, expected %r' % \
                (x0, y0, z0, axis, got, want)
    cmd.delete('srp_tmpA')


def s_sweep():
    """SWEEP (probe B regression): SIX sweep_chain(15.0, (0,0)) calls —
    the real per-tick ('turning',) pattern — rigidly rotate srp_head +
    srp_seg_1 + srp_seg_2 by +90 deg CCW about the explicit (0,0) pivot.
    Every centroid: (cx,cy) -> (-cy,cx) to <=1e-3; internal geometry
    (atom-set diameter) unchanged to <=1e-3."""
    pymol_bridge.cleanup_srp()
    names = ('srp_head', 'srp_seg_1', 'srp_seg_2')
    spots = ((3.0, 0.0), (6.0, 2.0), (-2.0, 4.0))  # all away from origin
    for name, (dx, dy) in zip(names, spots):
        pymol_bridge.load_molecule(BENZENE, name)
        cmd.translate([dx, dy, 0.0], name, camera=0)
    c0 = dict((n, _centroid(_atoms(n))) for n in names)
    d0 = dict((n, _diameter(_atoms(n))) for n in names)
    for _ in range(6):
        pymol_bridge.sweep_chain(15.0, (0.0, 0.0))
    for n in names:
        cx, cy, cz = c0[n]
        ax, ay, az = _centroid(_atoms(n))
        # +90 CCW about (0,0): x -> -y, y -> x; z preserved
        assert abs(ax - (-cy)) <= 1e-3, \
            '%s centroid x %r, expected %r (CCW +90)' % (n, ax, -cy)
        assert abs(ay - cx) <= 1e-3, \
            '%s centroid y %r, expected %r (CCW +90)' % (n, ay, cx)
        assert abs(az - cz) <= 1e-3, \
            '%s centroid z %r, expected %r' % (n, az, cz)
        d1 = _diameter(_atoms(n))
        assert abs(d1 - d0[n]) <= 1e-3, \
            '%s not rigid: diameter %r -> %r' % (n, d0[n], d1)


def s_completion():
    """COMPLETION (probes C/G): rename_pickup (unprobed set_name — this
    smoke is its verification), chain_object_names listing, zoom_chain
    framing, delete_pickups pattern-delete with srp_head surviving."""
    # Scene from s_sweep still loaded: srp_head, srp_seg_1, srp_seg_2.
    pymol_bridge.rename_pickup('srp_seg_1', 'srp_seg_renamed')
    names = cmd.get_names('public_objects')
    assert 'srp_seg_renamed' in names, \
        'rename_pickup failed: %r' % (names,)
    assert 'srp_seg_1' not in names, 'old name survived set_name'
    chain = pymol_bridge.chain_object_names()
    assert chain == sorted(chain), 'chain_object_names not sorted'
    for wanted in ('srp_head', 'srp_seg_2', 'srp_seg_renamed'):
        assert wanted in chain, \
            '%s missing from chain list %r' % (wanted, chain)
    pymol_bridge.zoom_chain()  # completion framing; must not raise
    pymol_bridge.load_molecule(BENZENE, 'srp_pickup_x')
    assert 'srp_pickup_x' in cmd.get_names('public_objects'), \
        'srp_pickup_x not loaded'
    pymol_bridge.delete_pickups()
    names = cmd.get_names('public_objects')
    assert 'srp_pickup_x' not in names, 'srp_pickup_x survived delete'
    assert 'srp_head' in names, 'srp_head lost by delete_pickups'
    assert 'srp_seg_2' in names, 'srp_seg_2 lost by delete_pickups'


for _name, _fn in [
    ('TRANSFORM', s_transform),
    ('SWEEP', s_sweep),
    ('COMPLETION', s_completion),
]:
    check(_name, _fn)

# Final line regardless of outcome (per-plan contract). The gate verdict
# reads SMOKE-OK/SMOKE-FAIL sentinels, never this line.
print('SMOKE-07 DONE%s' % (
    '' if not FAILURES else ' (%d step(s) failed: %s)' % (
        len(FAILURES), ', '.join(FAILURES))), flush=True)
