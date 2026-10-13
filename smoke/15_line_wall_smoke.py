"""Headless Windows PyMOL line-wall CHANNEL smoke — 09-08 (Phase 9).

Run (from repo root; cwd is /mnt/c-backed so cmd.exe inherits C:\\ cwd):
    timeout 90 cmd.exe /c "C:\\src\\run-conda-pymol.bat -cq smoke\\15_line_wall_smoke.py"

Exit codes through the .bat are ALWAYS 0 (even after a Qt C-abort) —
verdicts are flushed sentinels grepped by tests/run_gates.py --smoke:
    STAGE0 BANNER ...            header (NO Qt app: CGO-only smoke)
    STAGE1 WALL-LOADED ...       load_line_wall -> srp_wall; extent xy ==
                                 endpoints +-1e-3; z span == (-5, +5)
    STAGE2 WALL-REPLACE ...      delete-then-load MOVES the extent exactly
                                 (the 07-09 replace contract)
    STAGE3 WALL-SPAWN ...        scripted capture drive; on the resolution
                                 mirror the controller seam (next_after ->
                                 build_pickup_seed append -> next_wall ->
                                 set_wall); both names public; per-atom gap
                                 >= WALL_MOL_CLEARANCE_A
    STAGE4 WALL-CRASH ...        engine drive into a wall -> result
                                 'crashed', final event ('crashed', 'wall')
    STAGE5 WALL-DELETE ...       delete_walls removes exactly srp_wall*;
                                 non-srp sentinel + pickups survive
    STAGE6 SCENECLR-WALL ...     rebuild_scene sweeps wall leftovers; fresh
                                 srp_box + srp_head present
    SMOKE-OK LINE-WALL           all stages passed
    SMOKE-FAIL <stage>: ...      a stage failed (one line per failure)

This is Phase 9's viewer-channel evidence leg (09-RESEARCH-viewer-bridge.md
sec 3): the bridge wall functions (09-05) and the wall-crash semantics
(09-02) are NOT WSL-unit-testable (module-level `from pymol import cmd`),
so their truth is these SMOKE-OK sentinels. One mechanism per numbered
smoke (07 transforms / 13 arrows / 14 release chain precedent) — walls
are a new object kind + new bridge channel + new engine rule.

VERIFY-AT-EXECUTION (plan contract): `cmd.get_extent` on a LINES-only CGO
is live-proven indirectly (smoke 13 reads srp_mode_vec, also LINES) but the
wall fence path is new here. IF it ever misbehaves (garbage / None /
exception) the stage prints a FALLBACK note, keeps the name-presence
assertion and continues — the exact CGO floats are already pinned
pure-side by TestWallCgo.

Template rules (copied from smoke/01, 03, 13, 14):
  - every print carries flush=True (stdout is block-buffered when piped)
  - NO Qt app and NO widget construction (CGO-only smoke — no
    QPainter/fonts leg; headless Qt C-aborts are uncatchable)
  - never add smoke/__init__.py (findPlugins plugin-path safety)
  - NEVER trust __file__ under -cq (resolve ROOT by validating
    serpentrum/__init__.py candidates)
  - verdict = flushed SMOKE-OK/SMOKE-FAIL sentinels ONLY (never exit codes)
  - get_names type is 'public_objects' (proven for 2.5.0 in smoke 03)
"""
import math
import os
import sys


def _resolve_root():
    """Repo root, defensively (copied from smoke/01_skeleton_smoke.py).

    Under -cq launch, __file__ is PyMOL's launcher module (NOT this
    script), so naive dirname(dirname(__file__)) lands in site-packages.
    Validate every candidate by the presence of serpentrum/__init__.py.
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
from serpentrum import game_engine  # noqa: E402
from serpentrum import gui_game  # noqa: E402 (module import is headless-safe)
from serpentrum import molfile  # noqa: E402
from serpentrum import orientation  # noqa: E402
from serpentrum import pymol_bridge as pb  # noqa: E402
from serpentrum import setloader  # noqa: E402
from serpentrum import setup_logic  # noqa: E402
from serpentrum import spawn as spawn_mod  # noqa: E402
from serpentrum import wall as wall_mod  # noqa: E402

FAILURES = []

METHANE = os.path.join(ROOT, 'tests', 'fixtures', 'molfile', 'methane.sdf')
BENZENE = os.path.join(ROOT, 'serpentrum', 'data', 'benzene.sdf')
DT = 0.1  # the shipped cadence: QTimer 100 ms -> step(0.1) (gui_game.py:88-90)


def check(name, fn):
    try:
        fn()
    except Exception as exc:
        print('SMOKE-FAIL %s: %r' % (name, exc), flush=True)
        FAILURES.append(name)


# --- pure-mirror helpers (copied from smoke/14 / gui_game) ------------------

def _extent_center(atoms):
    """gui_game._extent_center in miniature: extent-midpoint translate."""
    xs = [a[1] for a in atoms]
    ys = [a[2] for a in atoms]
    zs = [a[3] for a in atoms]
    ox = (min(xs) + max(xs)) / 2.0
    oy = (min(ys) + max(ys)) / 2.0
    oz = (min(zs) + max(zs)) / 2.0
    return [(a[0], a[1] - ox, a[2] - oy, a[3] - oz) for a in atoms]


def _mirror_atoms(record):
    """Origin-centered edge-on (sym, x, y, z) atoms for one record.

    gui_game._mirror_atoms' demo half: stack_ring records take
    orientation.edge_on_atoms — the exact pose the pickup m16 lands in
    the viewer, so engine-side spawn geometry mirrors the viewer 1:1.
    """
    parsed = molfile.read_sdf(record['file'])[0]
    assert 'stack_ring' in record, \
        'record %r has no stack_ring (set_a pin)' % (record['id'],)
    return orientation.edge_on_atoms(
        parsed['elements'], parsed['coords'], record['stack_ring'])


def _pickup_m16(record, centroid):
    """gui_game._pickup_m16: the ONE m16 landing a pickup edge-on."""
    parsed = molfile.read_sdf(record['file'])[0]
    cx, cy = centroid
    if 'stack_ring' in record:
        rotation, pre = orientation.edge_on_frame(
            parsed['elements'], parsed['coords'], record['stack_ring'])
        return orientation.matrix_rt(rotation, (cx, cy, 0.0), pre)
    atoms = [(sym, float(p[0]), float(p[1]), float(p[2]))
             for sym, p in zip(parsed['elements'], parsed['coords'])]
    centered = _extent_center(atoms)
    ox = atoms[0][1] - centered[0][1]
    oy = atoms[0][2] - centered[0][2]
    oz = atoms[0][3] - centered[0][3]
    identity = ((1.0, 0.0, 0.0),
                (0.0, 1.0, 0.0),
                (0.0, 0.0, 1.0))
    return orientation.matrix_rt(identity, (cx, cy, 0.0), (-ox, -oy, -oz))


def _cgo_extent(name):
    """Return ((lo3),(hi3)) or None when get_extent is unusable here.

    VERIFY-AT-EXECUTION guard: any exception / malformed / non-finite /
    inverted extent -> None, and the caller falls back to name presence.
    """
    try:
        ext = cmd.get_extent(name)
    except Exception:
        return None
    try:
        lo = tuple(float(v) for v in ext[0])
        hi = tuple(float(v) for v in ext[1])
    except Exception:
        return None
    if len(lo) != 3 or len(hi) != 3:
        return None
    for v in list(lo) + list(hi):
        if not math.isfinite(v):
            return None
    for axis in range(3):
        if hi[axis] < lo[axis]:
            return None
    return (lo, hi)


def _spans(ext):
    (lo, hi) = ext
    return (hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2])


# --- stages ----------------------------------------------------------------

def s0_header():
    # Header only: NO Qt app (CGO-only smoke — no paint leg), NO
    # widget construction. _resolve_root already ran at import.
    print('STAGE0 BANNER root=%s no-Qt-App CGO-only' % ROOT,
          flush=True)


def s1_wall_loaded():
    # Stage 1: load_line_wall lands the fence CGO as srp_wall; the xy
    # extent equals the engine-owned endpoints and z spans the display
    # band (-BOX_DISPLAY_Z, +BOX_DISPLAY_Z) = (-5.0, +5.0).
    pb.delete_object(pb.WALL_NAME)
    name = pb.load_line_wall((-20.0, -10.0), (10.0, 15.0))
    assert name == pb.WALL_NAME, 'returned name %r' % (name,)
    assert pb.WALL_NAME in cmd.get_names('public_objects'), 'srp_wall missing'
    ext = _cgo_extent(pb.WALL_NAME)
    if ext is None:
        print('STAGE1 WALL-LOADED FALLBACK get_extent-unusable name-only',
              flush=True)
        return
    (lo, hi) = ext
    assert abs(lo[0] - (-20.0)) <= 1e-3 and abs(hi[0] - 10.0) <= 1e-3, \
        'x endpoints %r != (-20.0, 10.0)' % ((lo[0], hi[0]),)
    assert abs(lo[1] - (-10.0)) <= 1e-3 and abs(hi[1] - 15.0) <= 1e-3, \
        'y endpoints %r != (-10.0, 15.0)' % ((lo[1], hi[1]),)
    assert abs(lo[2] - (-5.0)) <= 1e-3 and abs(hi[2] - 5.0) <= 1e-3, \
        'z span %r != (-5.0, 5.0)' % ((lo[2], hi[2]),)
    sp = _spans(ext)
    print('STAGE1 WALL-LOADED spans=%.3f,%.3f,%.3f' % sp, flush=True)


def s2_wall_replace():
    # Stage 2: the 07-09 delete-then-load replace contract — deleting
    # srp_wall then loading new endpoints MOVES the extent exactly.
    pb.delete_object(pb.WALL_NAME)
    assert pb.WALL_NAME not in cmd.get_names('public_objects'), \
        'srp_wall survived delete_object'
    pb.load_line_wall((5.0, 20.0), (-15.0, -25.0))
    assert pb.WALL_NAME in cmd.get_names('public_objects'), \
        'srp_wall missing after replace'
    ext = _cgo_extent(pb.WALL_NAME)
    if ext is None:
        print('STAGE2 WALL-REPLACE FALLBACK get_extent-unusable name-only',
              flush=True)
        return
    (lo, hi) = ext
    assert abs(lo[0] - (-15.0)) <= 1e-3 and abs(hi[0] - 5.0) <= 1e-3, \
        'x extent did not move: %r != (-15.0, 5.0)' % ((lo[0], hi[0]),)
    assert abs(lo[1] - (-25.0)) <= 1e-3 and abs(hi[1] - 20.0) <= 1e-3, \
        'y extent did not move: %r != (-25.0, 20.0)' % ((lo[1], hi[1]),)
    assert abs(lo[2] - (-5.0)) <= 1e-3 and abs(hi[2] - 5.0) <= 1e-3, \
        'z span %r != (-5.0, 5.0)' % ((lo[2], hi[2]),)
    sp = _spans(ext)
    print('STAGE2 WALL-REPLACE spans=%.3f,%.3f,%.3f' % sp, flush=True)


def s3_wall_spawn():
    # Stage 3: the controller-mirroring capture drive. A pickup sits on
    # the straight +x path; when the engine reports 'stacked' we mirror
    # the controller seam (next_after -> build_pickup_seed append ->
    # next_wall -> set_wall) and materialize BOTH viewer objects. The
    # wall policy's L2 leg guarantees the per-atom gap to the NEW mol.
    records, errs = setloader.load_demo_set(
        setloader.package_data_dir(), 'set_a',
        setloader.default_stacking_path())
    assert errs == [], 'load_demo_set errors: %r' % (errs,)
    assert len(records) == 5, 'expected 5 records, got %d' % len(records)
    setup = setup_logic.new_setup()
    setup['box_preset'] = 'medium'
    setup['head_molecule'] = 'benzene'
    box_min, box_max = setup_logic.BOX_PRESETS[setup['box_preset']]
    atoms_by_id = dict((r['id'], _mirror_atoms(r)) for r in records)
    pickup_seed = spawn_mod.seed_from_setup(setup)
    spawner = spawn_mod.PickupSpawner(records, box_min, box_max,
                                      pickup_seed, atoms_by_id)
    wall_seed = wall_mod.wall_seed_from_setup(setup)
    wall_spawner = wall_mod.WallSpawner(box_min, box_max, wall_seed)
    head_atoms = _extent_center(_mirror_atoms(records[0]))
    # Initial deterministic pickup ON the +x path (no steering needed).
    rec0 = records[0]
    init = spawn_mod.build_pickup_seed(
        rec0, 'p0', (6.0, 0.0), _mirror_atoms(rec0))
    pb.materialize_pickup(rec0['file'], 'srp_pickup_p0',
                          _pickup_m16(rec0, (6.0, 0.0)))
    engine = game_engine.GameEngine(
        head=(0.0, 0.0), heading='right',
        box_min=box_min, box_max=box_max,
        pickups=[init],
        cap=setup['win_cap_molecules'],
        atom_budget=setup['atom_budget'],
        speed_a_per_s=setup['speed'])
    ticks = 0
    spawned = False
    new_pid = None
    seed = None
    while not engine.finished and not spawned:
        events = engine.step(DT)
        ticks += 1
        assert ticks < 1000, 'drive did not capture in 1000 ticks'
        for ev in events:
            if ev[0] != 'stacked':
                continue
            engine.attach_segment(ev[1]['molecule_id'], ev[1]['centroid'],
                                  ev[1]['atoms'])
            # --- controller seam (exact order) ---------------------
            chain_atoms = list(head_atoms)
            for seg in engine.segments:
                chain_atoms.extend(seg['atoms'])
            live_centroids = [p['centroid'] for p in engine.pickups
                              if p['id'] in engine.live_pickup_ids]
            result = spawner.next_after(engine.head, 'right',
                                        chain_atoms, live_centroids)
            assert result is not None, 'next_after returned None'
            rec, new_pid, centroid = result
            seed = spawn_mod.build_pickup_seed(
                rec, new_pid, centroid, _mirror_atoms(rec))
            engine.pickups.append(seed)
            engine.live_pickup_ids.add(new_pid)
            engine.pickups_remaining += 1
            live_atoms = []
            for p in engine.pickups:
                if p['id'] != new_pid and p['id'] in engine.live_pickup_ids:
                    live_atoms.extend(p['atoms'])
            wall = wall_spawner.next_wall(engine.head, seed['atoms'],
                                          live_atoms)
            engine.set_wall(wall)
            # --- viewer materializations (both) --------------------
            pb.materialize_pickup(rec['file'], 'srp_pickup_%s' % new_pid,
                                  _pickup_m16(rec, centroid))
            if wall is not None:
                pb.load_line_wall(wall[0], wall[1])
            spawned = True
            break
    assert spawned, 'no capture resolution occurred'
    assert engine.wall is not None, 'wall policy returned None (exhaustion)'
    names = cmd.get_names('public_objects')
    assert ('srp_pickup_%s' % new_pid) in names, \
        'new pickup %r not public' % (new_pid,)
    assert pb.WALL_NAME in names, 'srp_wall not loaded'
    clearance = wall_mod.min_atom_clearance(engine.wall, seed['atoms'])
    assert clearance >= wall_mod.WALL_MOL_CLEARANCE_A - 1e-3, \
        'min per-atom clearance %.4f < %.4f' \
        % (clearance, wall_mod.WALL_MOL_CLEARANCE_A)
    print('STAGE3 WALL-SPAWN ticks=%d pickup=%s clearance=%.4f'
          % (ticks, new_pid, clearance), flush=True)


def s4_wall_crash():
    # Stage 4: a fresh engine driven head-first into a wall across the
    # +x path ends result='crashed' with final event ('crashed', 'wall').
    engine = game_engine.GameEngine(
        head=(0.0, 0.0), heading='right',
        wall=((3.0, -3.0), (3.0, 3.0)))
    final = []
    ticks = 0
    while not engine.finished:
        final = engine.step(DT)
        ticks += 1
        assert ticks < 1000, 'wall crash did not fire in 1000 ticks'
    assert engine.result == 'crashed', \
        'result %r != crashed' % (engine.result,)
    assert engine.finished, 'engine not finished'
    assert final[-1] == ('crashed', 'wall'), \
        'final event %r != (crashed, wall)' % (final[-1],)
    print('STAGE4 WALL-CRASH ticks=%d reason=wall' % ticks, flush=True)


def s5_wall_delete():
    # Stage 5: delete_walls removes EXACTLY srp_wall* — the singular
    # srp_wall and an indexed srp_wall_7 both go; a non-srp sentinel and
    # an srp_pickup_* object both survive (the INFRA-04 class proof).
    pb.load_line_wall((-2.0, 0.0), (2.0, 0.0))
    pb.load_line_wall((3.0, 3.0), (4.0, 4.0), name='srp_wall_7')
    cmd.load(METHANE, object='user_wall_sentinel')
    cmd.load(METHANE, object='srp_pickup_tempsentry')
    before = [n for n in cmd.get_names('public_objects')
              if n.startswith('srp_wall')]
    assert 'srp_wall' in before, 'srp_wall not staged'
    assert 'srp_wall_7' in before, 'srp_wall_7 not staged'
    pb.delete_walls()
    names = cmd.get_names('public_objects')
    assert 'srp_wall' not in names, 'srp_wall survived delete_walls'
    assert 'srp_wall_7' not in names, 'srp_wall_7 survived delete_walls'
    assert 'user_wall_sentinel' in names, 'non-srp sentinel was deleted'
    assert 'srp_pickup_tempsentry' in names, 'pickup was deleted'
    print('STAGE5 WALL-DELETE removed=%d sentinel+pickup survive'
          % len(before), flush=True)


def s6_sceneclr_wall():
    # Stage 6: rebuild_scene (the headless begin_game/Restart seam)
    # sweeps every srp_wall* leftover via cleanup_srp-first and rebuilds
    # a fresh box + canonical head.
    pb.load_line_wall((-2.0, 0.0), (2.0, 0.0))
    pb.load_line_wall((3.0, 3.0), (4.0, 4.0), name='srp_wall_3')
    record = molfile.read_sdf(BENZENE)[0]
    ring = molfile.ring_cycle(record)
    setup = {'box_preset': 'small', 'head_molecule': 'benzene'}
    records_by_id = {'benzene': {'id': 'benzene', 'file': BENZENE,
                                 'stack_ring': list(ring),
                                 'has_stack_entry': True}}
    gui_game.rebuild_scene(setup, records_by_id)
    names = set(cmd.get_names('public_objects'))
    leftovers = [n for n in names if n.startswith('srp_wall')]
    assert not leftovers, 'wall leftovers survived rebuild_scene: %r' \
        % (leftovers,)
    assert pb.BOX_NAME in names, 'fresh srp_box missing'
    assert pb.HEAD_NAME in names, 'fresh srp_head missing'
    print('STAGE6 SCENECLR-WALL left=%d fresh-box+head'
          % len(leftovers), flush=True)


for _name, _fn in [
    ('stage0_header', s0_header),
    ('stage1_wall_loaded', s1_wall_loaded),
    ('stage2_wall_replace', s2_wall_replace),
    ('stage3_wall_spawn', s3_wall_spawn),
    ('stage4_wall_crash', s4_wall_crash),
    ('stage5_wall_delete', s5_wall_delete),
    ('stage6_sceneclr_wall', s6_sceneclr_wall),
]:
    if not FAILURES:
        check(_name, _fn)

if FAILURES:
    print('SMOKE-END %d failure(s)' % len(FAILURES), flush=True)
else:
    print('SMOKE-OK LINE-WALL', flush=True)
