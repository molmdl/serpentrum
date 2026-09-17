"""Ring-plane parallelism regression (05-16 checkpoint follow-up).

Live-verified bug: in real Windows PyMOL the placed segment appeared
PERPENDICULAR (T-shaped edge-to-face) to the tail ring instead of
PARALLEL-DISPLACED (face-to-face pi-stack). Every pre-existing check
(test_phase5_integration scenario 1, smoke/08 PLACE360) asserted the
ring-centroid DISTANCE only -- 3.6000 A -- and none asserted the placed
ring PLANE stays parallel to the tail ring plane. This file closes that
blind spot on the PURE side, on the real shipped data and the real
engine sweep machinery:

    for EVERY canonical heading (right / up / left / down):
      - FIRST capture (empty chain, head-tailed tail_frame policy):
        the placed ring plane MUST be parallel to the head's ring plane,
        i.e. |dot(placed_ring_normal, head_ring_normal)| > 0.999, AND
        the growth normal the placement was built on MUST equal the
        first-capture policy (-heading), AND the ring-centroid distance
        MUST stay sqrt(distance_a^2 + lateral_offset_a^2) == 3.6000 A.
      - post-sweep capture (after a rigid 90-degree sweep, tail = the
        sweep-rotated NEWEST segment): |dot(placed_n, tail_n)| > 0.999
        with the recomputed tail frame and the same 3.6000 A distance.

The normal SIGN is walk-order dependent (stacking.ring_frame's Newell
normal flips under ring-order reversal; the first-capture growth normal
is caller-signed to -heading by placement.tail_frame), so parallelism
is asserted as |dot| -- planes are parallel iff their normals are
parallel OR antiparallel. The growth-normal alignment is additionally
asserted EXACTLY: dot(placed_normal, growth_normal) == 1 within 1e-9,
which is the place_pickup contract (R maps the pickup normal onto the
given tail growth normal).

python3.6 only (%-formatting, no f-strings). tests/ has NO __init__.py;
discovery runs as `python -m unittest discover -s tests`, so this file
is fully self-contained (no cross-test imports).
"""
import math
import os
import sys
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from serpentrum import game_engine  # noqa: E402
from serpentrum import molfile  # noqa: E402
from serpentrum import molecule_data  # noqa: E402
from serpentrum import orientation  # noqa: E402
from serpentrum import placement  # noqa: E402
from serpentrum import setloader  # noqa: E402
from serpentrum import setup_logic  # noqa: E402
from serpentrum import spawn  # noqa: E402
from serpentrum import stacking  # noqa: E402
from serpentrum.game_engine import GameEngine  # noqa: E402

DT = 0.1
DISPLAY_Z = 5.0
DELTA = 1e-6
PARALLEL_DOT = 0.999

# 90-degree CCW sweep target per start heading (cross product positive).
PERPENDICULAR = {'right': 'up', 'up': 'left', 'left': 'down',
                 'down': 'right'}


def build_fixture():
    """REAL shipped data: set_a records + stacking dataset + edge-on atoms."""
    stacking_path = setloader.default_stacking_path()
    records, errors = setloader.load_demo_set(stacking_path=stacking_path)
    assert errors == [], errors
    stacking_data = molecule_data.load_stacking(stacking_path)
    atoms_by_id = {}
    for record in records:
        parsed = molfile.read_sdf(record['file'])[0]
        atoms_by_id[record['id']] = orientation.edge_on_atoms(
            parsed['elements'], parsed['coords'], record['stack_ring'])
    return {
        'records_by_id': dict((r['id'], r) for r in records),
        'atoms_by_id': atoms_by_id,
        'stacking_data': stacking_data,
        'box_min': setup_logic.BOX_PRESETS['medium'][0],
        'box_max': setup_logic.BOX_PRESETS['medium'][1],
        'head_id': 'benzene',
    }


def _xyz(atoms):
    return [(a[1], a[2], a[3]) for a in atoms]


def _dist3(a, b):
    return math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(3)))


def _dot(a, b):
    return sum(a[i] * b[i] for i in range(3))


def _frame(atoms, stack_ring):
    """The stacking.ring_frame 3-tuple for (sym, x, y, z) atoms."""
    return stacking.ring_frame(_xyz(atoms), stack_ring)


class TestStackPlaneParallelism(unittest.TestCase):
    """Blind-spot regression: parallel planes, every heading, first sweep."""

    @classmethod
    def setUpClass(cls):
        cls.state = build_fixture()
        cls.expected_composed = math.sqrt(
            cls.state['stacking_data']['interactions'][0]['distance_a'] ** 2
            + cls.state['stacking_data']['interactions'][0]['lateral_offset_a'] ** 2)
        # Dataset-pinned numbers (DATA-02): 3.6000 A at 4 decimals.
        assert '%.4f' % cls.expected_composed == '3.6000'

    def _new_mirror(self):
        """The 05-13 world-coordinate head mirror: origin-centered edge-on
        atoms at engine head (0, 0). Kept WORLD-anchored (translated per
        moved tick, rotated per sweep tick) exactly like _on_tick /
        _handle_turn_event keep session['head_atoms']."""
        return list(self.state['atoms_by_id'][self.state['head_id']])

    def _spin(self, engine, mirror, target):
        """Open and run one full 90-degree sweep, rotating the mirror by
        the SAME per-tick delta the bridge applies to the head object
        (game_engine._rotate_xy about engine.head, z preserved) -- the
        05-14 mirror discipline. After engine.step(DT) the sweep ends
        with heading == target."""
        opened, _events = engine.start_sweep(target)
        self.assertTrue(opened, 'sweep to %s refused (fixture defect)'
                        % target)
        angle = engine.sweeping['angle_signed']
        delta = math.radians(
            angle / float(game_engine.TURN_TICKS))
        ct, st = math.cos(delta), math.sin(delta)
        while engine.sweeping is not None:
            hx, hy = engine.head
            mirror = [(sym,) +
                      game_engine._rotate_xy(x, y, hx, hy, ct, st) + (z,)
                      for (sym, x, y, z) in mirror]
            engine.step(DT)
        return mirror

    def _seed_and_capture(self, engine, mirror, molecule_id, pid,
                          centroid):
        """Hand-place one pickup record ahead, drive the engine (moving
        the mirror with every ('moved',) tick), capture it and return
        (outcome, tail_frame, mirror_after). Mirrors the 05-13 seam
        clause-by-clause."""
        state = self.state
        record = state['records_by_id'][molecule_id]
        seed = spawn.build_pickup_seed(
            record, pid, centroid, state['atoms_by_id'][molecule_id])
        seed['stack_ring'] = list(record['stack_ring'])
        seed['has_stack_entry'] = record['has_stack_entry']
        seed['set'] = record['set']
        engine.pickups.append(seed)
        engine.live_pickup_ids.add(pid)
        engine.pickups_remaining += 1
        for _tick in range(400):
            old = engine.head
            events = engine.step(DT)
            if any(e[0] == 'moved' for e in events):
                dx = engine.head[0] - old[0]
                dy = engine.head[1] - old[1]
                mirror = [(sym, x + dx, y + dy, z)
                          for (sym, x, y, z) in mirror]
            for event in events:
                if event[0] != 'stacked' or event[1]['id'] != pid:
                    continue
                head_atoms = mirror
                tail = placement.tail_frame(
                    engine.segments, state['records_by_id'], head_atoms,
                    state['records_by_id'][self.state['head_id']]
                    ['stack_ring'],
                    engine.heading)
                existing = list(head_atoms)
                for seg in engine.segments:
                    existing.extend(seg['atoms'])
                outcome = placement.resolve(
                    event[1], state['records_by_id'],
                    state['stacking_data'], head_atoms,
                    state['records_by_id'][self.state['head_id']]
                    ['stack_ring'],
                    engine.heading, engine.segments, existing,
                    engine.box_min, engine.box_max, DISPLAY_Z)
                if outcome['status'] == 'placed':
                    engine.attach_segment(molecule_id,
                                          outcome['ring_centroid_xy'],
                                          outcome['placed_atoms'])
                else:
                    engine.reject_pickup(pid, outcome['code'])
                return (outcome, tail, mirror)
        raise AssertionError('pickup %s never captured within 400 ticks'
                             % pid)

    def _assert_parallel(self, outcome, tail, molecule_id):
        """The blind-spot pin: parallel ring planes + composed distance."""
        state = self.state
        record = state['records_by_id'][molecule_id]
        p_c, p_n, _p_r = _frame(outcome['placed_atoms'], record['stack_ring'])
        t_c, t_n_growth, _t_r = tail
        # The growth-normal alignment is EXACT (place_pickup's contract:
        # R maps the pickup ring normal onto the given growth normal).
        self.assertAlmostEqual(_dot(p_n, t_n_growth), 1.0, delta=1e-9,
                               msg='placed normal off the growth normal')
        # Plane parallelism is sign-insensitive (walk-order artifact).
        self.assertGreater(abs(_dot(p_n, t_n_growth)), PARALLEL_DOT)
        self.assertAlmostEqual(_dist3(p_c, t_c),
                               self.expected_composed, delta=DELTA,
                               msg='ring-centroid distance off 3.6000')
        return (p_c, p_n)

    def _capture_and_sweep_per_heading(self, target_heading):
        """First capture + post-sweep capture at a NON-default heading,
        with the head mirror swept into that heading first (the live
        reachability model: the engine always opens at heading 'right';
        every other heading is reached by rigid sweeps, and the mirror /
        viewer head atoms rotate with the sweeps so the ring normal
        stays parallel to the heading -- which is precisely what the
        buggy _reset_head_viewer violated in the VIEWER layer)."""
        state = self.state
        engine = GameEngine(head=(0.0, 0.0), heading='right',
                            box_min=state['box_min'],
                            box_max=state['box_max'],
                            pickups=None)
        mirror = self._new_mirror()
        # Spin the engine + mirror into the target heading (engine truth
        # through the sweep machinery; mirror rotated per-tick the same
        # way the bridge rotates the head object).
        paths = {'right': [],
                 'up': ['up'],
                 'down': ['down'],
                 # 180-degree reversals are refused (GAME-10): two
                 # sweeps reach 'left'.
                 'left': ['up', 'left']}
        for target in paths[target_heading]:
            mirror = self._spin(engine, mirror, target)
        hx, hy = engine.heading

        # FIRST capture: empty chain -> head-tailed frame.
        first = self._seed_and_capture(
            engine, mirror, 'naphthalene', 'pick_a',
            (engine.head[0] + hx * 4.0, engine.head[1] + hy * 4.0))
        f_outcome, f_tail, mirror = first
        self.assertEqual(f_outcome['status'], 'placed',
                         'first capture not placed for %s' % target_heading)
        head_frame = _frame(
            mirror,
            state['records_by_id'][self.state['head_id']]['stack_ring'])
        # The tail RING normal (parallelism target) vs the caller-signed
        # growth normal (-heading): opposite signs by policy; |dot| is
        # the plane-parallelism assertion.
        self.assertGreater(
            abs(_dot(_frame(f_outcome['placed_atoms'],
                            state['records_by_id']['naphthalene']
                            ['stack_ring'])[1],
                     head_frame[1])),
            PARALLEL_DOT,
            'first capture (%s) ring plane not parallel to the head '
            'ring plane' % target_heading)
        self._assert_parallel(f_outcome, f_tail, 'naphthalene')

        # Rigid 90-degree sweep (engine truth; segments rotate ABSOLUTE;
        # mirror rotates per-tick the 05-14 way).
        mirror = self._spin(engine, mirror, PERPENDICULAR[target_heading])

        # SECOND capture: tail = the sweep-rotated NEWEST segment.
        nx, ny = engine.heading
        second = self._seed_and_capture(
            engine, mirror, 'benzene', 'pick_b',
            (engine.head[0] + nx * 4.0, engine.head[1] + ny * 4.0))
        s_outcome, s_tail, _mirror2 = second
        self.assertEqual(s_outcome['status'], 'placed',
                         'post-sweep capture not placed for %s'
                         % target_heading)
        seg = engine.segments[-2]  # the tail BEFORE the second attach
        seg_frame = _frame(seg['atoms'],
                           state['records_by_id'][seg['molecule_id']]
                           ['stack_ring'])
        self.assertGreater(
            abs(_dot(_frame(s_outcome['placed_atoms'],
                            state['records_by_id']['benzene']
                            ['stack_ring'])[1],
                     seg_frame[1])),
            PARALLEL_DOT,
            'post-sweep capture (%s) ring plane not parallel to the '
            'tail segment ring plane' % target_heading)
        self._assert_parallel(s_outcome, s_tail, 'benzene')

    def test_heading_right_first_and_post_sweep_parallel(self):
        self._capture_and_sweep_per_heading('right')

    def test_heading_up_first_and_post_sweep_parallel(self):
        self._capture_and_sweep_per_heading('up')

    def test_heading_left_first_and_post_sweep_parallel(self):
        self._capture_and_sweep_per_heading('left')

    def test_heading_down_first_and_post_sweep_parallel(self):
        self._capture_and_sweep_per_heading('down')


if __name__ == '__main__':
    unittest.main()
