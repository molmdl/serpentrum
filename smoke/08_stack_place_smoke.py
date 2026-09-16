"""Headless Windows PyMOL edge-on + stacking-placement smoke — 05-10.

Run (from repo root; cwd is /mnt/c-backed so cmd.exe inherits C:\\ cwd):
    timeout 90 cmd.exe /c "C:\\src\\run-conda-pymol.bat -cq smoke\\08_stack_place_smoke.py"

Exit codes through the .bat are ALWAYS 0 (even after a Qt C-abort) —
verdicts are flushed sentinels grepped by tests/run_gates.py --smoke:
    SMOKE-OK EDGEON      benzene edge-on in the viewer: z-extent == pure
                         edge_on_atoms z-span AND == 4.297 A research anchor
    SMOKE-OK PLACE360    REAL dataset pi_stack_pd placement lands at
                         3.6000 A ring-centroid distance; pure == viewer
                         coords (probe F of 05-RESEARCH-pymol-mechanics.md
                         END-TO-END through the SHIPPING code path)
    SMOKE-OK PICKUPS     materialize_pickup: sticks-show ran without error;
                         object exists; ring centroid lands at the composed
                         spawn centroid
    SMOKE-FAIL <step>    a step failed (traceback follows, sentinel withheld)
    SMOKE-08 DONE        the script reached the end (any state)

REQUIRED smoke (registered in tests/run_gates.py REQUIRED_SMOKES).
Real data only: serpentrum/data/benzene.sdf + stacking_pi_stack.json
(APPROVED 'pi_stack_pd': distance_a 3.383, lateral_offset_a 1.231;
sqrt(3.383^2 + 1.231^2) = 3.6000 A, Janiak 2000 / DATA-02).

3.6000-PIN NOTE (plan deviation, Rule 1): the pure ring-centroid
distance is EXACTLY sqrt(3.383^2 + 1.231^2) = 3.60000694 A — the plan's
"pure == 3.6000 within 1e-6" is tighter than the dataset encoding by
6.9e-6 and would fail literally. The smoke therefore asserts pure
EXACTNESS against the dataset-derived value within 1e-6 AND the
4-decimal claim via '%.4f' == '3.6000'; the viewer checks keep the
plan's 1e-3 tolerances (probe F2/F5 used 1e-3 / 5e-3 the same way).

Template rules (copied verbatim from smoke 05/07):
  - every print carries flush=True (stdout is block-buffered when piped)
  - NO widget construction (headless C-abort is uncatchable)
  - never add smoke/__init__.py (findPlugins plugin-path safety)
  - NEVER trust __file__ under -cq (resolve ROOT by validating
    serpentrum/__init__.py candidates)
  - verdict = flushed SMOKE-OK/SMOKE-FAIL sentinels ONLY (never exit codes)
  - get_names type is 'public_objects' (proven for 2.5.0 in smoke 03)
  - ring indices come from molfile.ring_cycle (NOT setloader records —
    the 05-08 stack_ring wire-in is a sibling branch)
"""
import math
import os
import sys
import traceback


def _resolve_root():
    """Repo root, defensively (verbatim from smoke/01_skeleton_smoke.py).

    Under -cq exec, __file__ is PyMOL's launcher module (NOT this script),
    so naive dirname(dirname(__file__)) lands in site-packages. Validate
    every candidate by the presence of serpentrum/__init__.py.
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
from serpentrum import molfile  # noqa: E402
from serpentrum import orientation  # noqa: E402
from serpentrum import placement  # noqa: E402
from serpentrum import molecule_data  # noqa: E402
from serpentrum import setloader  # noqa: E402
from serpentrum import stacking  # noqa: E402 (import probe: all pure modules import under PyMOL's python)
from serpentrum import pymol_bridge  # noqa: E402

FAILURES = []

BENZENE = os.path.join(ROOT, 'serpentrum', 'data', 'benzene.sdf')


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


def _ring_centroid_viewer(name, ring):
    """Viewer ring centroid: mean of object atoms at ring indices."""
    pts = _atoms(name)
    ring_pts = [pts[i] for i in ring]
    n = float(len(ring_pts))
    return (sum(p[0] for p in ring_pts) / n,
            sum(p[1] for p in ring_pts) / n,
            sum(p[2] for p in ring_pts) / n)


def _dist(a, b):
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 +
                     (a[2] - b[2]) ** 2)


def s_edgeon():
    """EDGEON: benzene edge-on via the shipping bridge path.

    load_molecule + ONE apply_matrix of the PURE edge_on_m16; the viewer
    z-extent must equal the pure edge_on_atoms z-span (<=1e-3) and the
    4.297 A research anchor (<=2e-3). Leaves 'srp_pickup_benzene' loaded
    as the head/tail proxy (ring centroid at the origin) for PLACE360.
    """
    pymol_bridge.cleanup_srp()
    record = molfile.read_sdf(BENZENE)[0]
    ring = molfile.ring_cycle(record)
    assert ring, 'ring_cycle found no ring in benzene'
    m16 = orientation.edge_on_m16(
        record['elements'], record['coords'], ring)
    pymol_bridge.load_molecule(BENZENE, 'srp_pickup_benzene')
    pymol_bridge.apply_matrix('srp_pickup_benzene', m16)
    (zmin, zmax) = (cmd.get_extent('srp_pickup_benzene')[0][2],
                    cmd.get_extent('srp_pickup_benzene')[1][2])
    viewer_z = zmax - zmin
    pure = orientation.edge_on_atoms(
        record['elements'], record['coords'], ring)
    pure_z = (max(a[3] for a in pure) - min(a[3] for a in pure))
    assert abs(viewer_z - pure_z) <= 1e-3, \
        'viewer z-span %.5f != pure z-span %.5f' % (viewer_z, pure_z)
    assert abs(viewer_z - 4.297) <= 2e-3, \
        'viewer z-span %.5f != 4.297 research anchor' % viewer_z


def s_place360():
    """PLACE360: dataset-exact placement end-to-end (the STACK-01 proof).

    PURE half: tail atoms = edge_on_atoms(benzene); tail frame via
    placement.tail_frame with heading (1, 0) (growth normal -heading);
    attempt_place with the REAL APPROVED pi_stack_pd interaction ->
    (placed, R, t, ring_centroid). Pure ring-centroid distance is EXACT
    (<=1e-6 vs sqrt(3.383^2+1.231^2)) and reports '3.6000' at 4 dp.
    VIEWER half: materialize_pickup edge-on at the origin + apply_matrix
    of matrix_rt(R, t); both ring centroids read back via get_model;
    viewer distance == 3.6000 (<=1e-3); sorted/rounded pure == viewer
    placed coords (<=5e-3; the probe-F5 pattern).
    """
    record = molfile.read_sdf(BENZENE)[0]
    ring = molfile.ring_cycle(record)
    edges = orientation.edge_on_atoms(
        record['elements'], record['coords'], ring)
    tail_c, tail_n, tail_ref = placement.tail_frame(
        [], {}, edges, ring, (1.0, 0.0))
    data = molecule_data.load_stacking(setloader.default_stacking_path())
    interactions = [i for i in molecule_data.shipped_interactions(data)
                    if i['mode'] == 'pi_stack']
    assert interactions, 'no APPROVED pi_stack interaction in dataset'
    interaction = interactions[0]
    placed, rot, tra, ring_centroid = placement.attempt_place(
        edges, ring, tail_c, tail_n, tail_ref, interaction)
    pure_dist = _dist(ring_centroid, tail_c)
    expected = (interaction['distance_a'] ** 2 +
                interaction['lateral_offset_a'] ** 2) ** 0.5
    assert abs(pure_dist - expected) <= 1e-6, \
        'pure distance %.7f != dataset sqrt %.7f' % (pure_dist, expected)
    assert '%.4f' % pure_dist == '3.6000', \
        'pure distance %.7f does not pin 3.6000 at 4 dp' % pure_dist

    m16 = orientation.edge_on_m16(
        record['elements'], record['coords'], ring)
    pymol_bridge.materialize_pickup(BENZENE, 'srp_pickup_p', m16)
    pymol_bridge.apply_matrix(
        'srp_pickup_p', orientation.matrix_rt(rot, tra))
    c_tail = _ring_centroid_viewer('srp_pickup_benzene', ring)
    c_pick = _ring_centroid_viewer('srp_pickup_p', ring)
    assert _dist(c_tail, (0.0, 0.0, 0.0)) <= 1e-3, \
        'tail ring centroid %r not at the origin (edge-on broke)' % (c_tail,)
    viewer_dist = _dist(c_pick, c_tail)
    assert abs(viewer_dist - 3.6000) <= 1e-3, \
        'viewer distance %.5f != 3.6000' % viewer_dist
    assert abs(viewer_dist - pure_dist) <= 1e-3, \
        'viewer distance %.5f != pure %.7f' % (viewer_dist, pure_dist)

    # probe-F5 pattern: order-independent sorted/rounded compare.
    vxyz = _atoms('srp_pickup_p')
    pure_sorted = sorted((round(p[1], 3), round(p[2], 3), round(p[3], 3))
                         for p in placed)
    viewer_sorted = sorted((round(p[0], 3), round(p[1], 3), round(p[2], 3))
                           for p in vxyz)
    assert len(pure_sorted) == len(viewer_sorted), \
        'atom count changed: %d -> %d' % (len(pure_sorted),
                                          len(viewer_sorted))
    max_err = max(_dist(pure_sorted[i], viewer_sorted[i])
                  for i in range(len(pure_sorted)))
    assert max_err <= 5e-3, \
        'pure-vs-viewer placed coords max err %.5f' % max_err


def s_sticks():
    """PICKUPS: materialize_pickup over a spawn-composed m16.

    m16 = matrix_rt(R_edge, spawn, pre): y = R.(x+pre)+t lands the ring
    centroid at the spawn centroid (the docstring contract). cmd.show
    ran without error by the time this returns (a get-rep stick check is
    flaky headless, so the gate is: object EXISTS + no exception) — plus
    the ring-centroid-lands-at-spawn assert that pins the must-have
    truth (pickup materializes edge-on AT ITS SPAWN CENTROID).
    """
    record = molfile.read_sdf(BENZENE)[0]
    ring = molfile.ring_cycle(record)
    rotation, pre = orientation.edge_on_frame(
        record['elements'], record['coords'], ring)
    spawn = (3.0, 0.0, 0.0)
    m_spawn = orientation.matrix_rt(rotation, spawn, pre)
    name = pymol_bridge.materialize_pickup(BENZENE, 'srp_pickup_s', m_spawn)
    assert name in cmd.get_names('public_objects'), \
        '%s missing after materialize_pickup' % name
    centroid = _ring_centroid_viewer(name, ring)
    assert _dist(centroid, spawn) <= 1e-3, \
        'spawn centroid miss: %r, expected %r' % (centroid, spawn)


for _name, _fn in [
    ('EDGEON', s_edgeon),
    ('PLACE360', s_place360),
    ('PICKUPS', s_sticks),
]:
    check(_name, _fn)

# Final line regardless of outcome (per-plan contract). The gate verdict
# reads SMOKE-OK/SMOKE-FAIL sentinels, never this line.
print('SMOKE-08 DONE%s' % (
    '' if not FAILURES else ' (%d step(s) failed: %s)' % (
        len(FAILURES), ', '.join(FAILURES))), flush=True)
