"""wall tests: deterministic seeded line-wall spawn policy pins (Phase 9, 09-01).

Seven pin groups mirror the plan's behavior cases:

  1. Seed         -- wall_seed_from_setup is stable in-process AND across
     processes (zlib.crc32, never hash()); it is DISTINCT from the pickup
     seed (the crc32 over '%d|%s' % (pickup_seed, WALL_SALT) isolation
     contract) yet still chains through the pickup seed; WALL_SALT is
     pinned to 'wall-v1' (bumping the salt rotates the wall stream only).
  2. Determinism  -- two same-seed WallSpawners produce byte-identical
     endpoint sequences over the same scripted call schedule; a different
     seed diverges (GAME-07 by construction).
  3. Isolation    -- the 5.3 zero-interaction pin, made cross-feature: a
     PickupSpawner driven ALONGSIDE interleaved wall draws produces the
     SAME (id, pid, centroid) sequence as one driven alone (walls never
     rotate the pickup stream).
  4. Geometry     -- the four clearance legs, all bound expectations
     DERIVED from the module's own constants (the 5.1-06 derivation habit
     -- an owner retune of the tunable table cannot silently break the
     suite): L1 endpoints respect the box margin; length derives from
     WALL_LENGTH_FRACTION * minor-axis span; L3 head clearance, incl. the
     targeted mid-wall rejection replay; L2 per-atom vs the new mol (the
     OWNER no-overlap mandate, sym-first 4-tuple, the STRADDLE case); L4
     per-atom vs live mols (bare 2-tuple).
  5. Exhaustion   -- WALL_MAX_DRAWS exhaustion returns None (caller keeps
     the previous wall); the degenerate box guard returns None WITHOUT
     consuming draws; a non-degenerate near-threshold box DOES consume
     draws.
  6. CtorKwargs   -- the four ctor overrides (wall_box_margin_a,
     wall_head_clearance_a, length_fraction, max_draws) feed read-only
     effective-value properties and change the sampled geometry
     accordingly.
  7. MinAtomClear  -- min_atom_clearance contract: degenerate segment,
     on-segment zero, returns the SQRT distance (not squared), BOTH repo
     atom shapes (sym-first 4-tuple x=[1]/y=[2]; bare 2-/3-tuple
     x=[0]/y=[1]), min over many atoms, empty -> ValueError.

All fixtures are synthetic (dummy ring atoms / far-placed probes) -- the
wall geometry math does not need real SDF data. Discovery (verified on
python3.6.9 -- do NOT add -t .):

    python3.6 -m unittest discover -s tests -p "test_wall.py" -v
"""
import math
import os
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from serpentrum import spawn  # noqa: E402
from serpentrum import wall  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- Preset boxes (setup_logic.BOX_PRESETS) + shared fixtures ---------------

BOX_MIN = (-55.0, -55.0)
BOX_MAX = (55.0, 55.0)

PRESETS = [
    ('small', (-35.0, -35.0), (35.0, 35.0)),
    ('medium', (-55.0, -55.0), (55.0, 55.0)),
    ('large', (-85.0, -85.0), (85.0, 85.0)),
]

# Canonical setup dict for the seed pins (mirrors test_spawn.SETUP).
SETUP = {
    'schema_version': 1,
    'demo_set': 'set_a',
    'head_molecule': 'random',
    'box_preset': 'medium',
    'win_cap_molecules': 10,
}

# A head/atom placed FAR outside every preset box: it makes L2 (new-mol) and
# L3 (head) vacuous so the geometry pins isolate the leg under test.
HEAD_FAR = (1000.0, 1000.0)
FAR_ATOMS = [('C', 1000.0, 1000.0, 0.0)]

# Tolerance for clearance/derived-value assertions.
TOL = 1e-9


def _dummy_atoms(symbol):
    """6 dummy atoms on a 1.4 A ring about the ORIGIN (origin-centered)."""
    return [(symbol,
             1.4 * math.cos(k * math.pi / 3.0),
             1.4 * math.sin(k * math.pi / 3.0),
             0.0) for k in range(6)]


def _midpoint(endpoints):
    """The midpoint of a returned wall segment."""
    (ax, ay), (bx, by) = endpoints
    return (0.5 * (ax + bx), 0.5 * (ay + by))


def _point_seg_dist(px, py, endpoints):
    """Point-to-segment distance (test-side mirror of the module helper)."""
    (ax, ay), (bx, by) = endpoints
    dx = bx - ax
    dy = by - ay
    seg_sq = dx * dx + dy * dy
    if seg_sq <= 0.0:
        return math.hypot(px - ax, py - ay)
    t = ((px - ax) * dx + (py - ay) * dy) / seg_sq
    if t < 0.0:
        t = 0.0
    elif t > 1.0:
        t = 1.0
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


class TestSeed(unittest.TestCase):
    """Case 1: derived wall seed stability + isolation from the pickup seed."""

    def test_wall_seed_stable_in_process(self):
        first = wall.wall_seed_from_setup(SETUP)
        second = wall.wall_seed_from_setup(SETUP)
        self.assertIsInstance(first, int)
        self.assertEqual(first, second)
        other = dict(SETUP)
        other['box_preset'] = 'large'
        self.assertNotEqual(first, wall.wall_seed_from_setup(other))

    def test_wall_seed_cross_process_stable(self):
        # crc32 is process-stable; hash() is not (PYTHONHASHSEED). Prove
        # the pinned contract by re-deriving the wall seed in a child.
        code = (
            'import sys; sys.path.insert(0, %r);'
            'from serpentrum import wall;'
            'print(wall.wall_seed_from_setup(%r))' % (ROOT, SETUP))
        proc = subprocess.Popen(
            [sys.executable, '-c', code],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=ROOT)
        out, err = proc.communicate()
        self.assertEqual(proc.returncode, 0,
                         'child wall seed probe failed: %s' % err.decode())
        self.assertEqual(int(out.strip()), wall.wall_seed_from_setup(SETUP))

    def test_wall_seed_differs_from_pickup_seed(self):
        pickup = spawn.seed_from_setup(SETUP)
        wall_seed = wall.wall_seed_from_setup(SETUP)
        # The salt isolates the two streams.
        self.assertNotEqual(wall_seed, pickup)
        # But the wall derivation still CHAINS through the pickup seed:
        # changing the setup moves BOTH.
        other = dict(SETUP)
        other['box_preset'] = 'large'
        self.assertNotEqual(spawn.seed_from_setup(other), pickup)
        self.assertNotEqual(wall.wall_seed_from_setup(other), wall_seed)

    def test_salt_pinned(self):
        # Retuning the salt rotates the wall stream ONLY.
        self.assertEqual(wall.WALL_SALT, 'wall-v1')


class TestDeterminism(unittest.TestCase):
    """Case 2: same seed -> byte-identical endpoint sequences; diff -> diff."""

    HEADS = [(0.0, 0.0), (3.0, -2.0), (-4.0, 1.0), (2.0, 5.0),
             (-5.0, -3.0), (1.0, 2.0), (4.0, -4.0), (-2.0, 3.0)]

    def _drive(self, seed):
        """Drive 8 next_wall calls over a scripted evolving head schedule."""
        spawner = wall.WallSpawner(BOX_MIN, BOX_MAX, seed)
        out = []
        for hx, hy in self.HEADS:
            out.append(spawner.next_wall((hx, hy), FAR_ATOMS, []))
        return out

    def test_same_seed_identical_sequences(self):
        self.assertEqual(self._drive(1234), self._drive(1234))

    def test_different_seed_diverges(self):
        first = self._drive(1234)
        second = self._drive(9999)
        # At least one endpoint in the schedule differs.
        self.assertNotEqual(first, second)


class TestStreamIsolation(unittest.TestCase):
    """Case 3: the 5.3 zero-interaction pin, made cross-feature."""

    RECORDS = [
        {'id': 'mol_a', 'set': 'set_a'},
        {'id': 'mol_b', 'set': 'set_a'},
    ]
    ATOMS_BY_ID = {
        'mol_a': _dummy_atoms('C'),
        'mol_b': _dummy_atoms('C'),
    }

    def _drive_pickup(self, spawner, rounds, wall_spawner=None):
        """Drive a pickup sequence; optionally interleave a wall draw
        between every spawn. Returns comparable (id, pid, centroid)."""
        first = spawner.first((0.0, 0.0), 'right')
        self.assertIsNotNone(first)
        out = [first]
        live = [first[2]]
        for _ in range(rounds):
            if wall_spawner is not None:
                # A wall draw between every pickup spawn; result ignored.
                wall_spawner.next_wall((0.0, 0.0),
                                       [('C', 50.0, 50.0, 0.0)], [])
            result = spawner.next_after((0.0, 0.0), 'right', [], live)
            self.assertIsNotNone(result)
            out.append(result)
            live.append(result[2])
        return [(record['id'], pid, centroid)
                for record, pid, centroid in out]

    def test_wall_draws_never_touch_pickup_stream(self):
        pickup_seed = spawn.seed_from_setup(SETUP)
        wall_seed = wall.wall_seed_from_setup(SETUP)
        alone = spawn.PickupSpawner(self.RECORDS, BOX_MIN, BOX_MAX,
                                    pickup_seed, self.ATOMS_BY_ID)
        combined = spawn.PickupSpawner(self.RECORDS, BOX_MIN, BOX_MAX,
                                       pickup_seed, self.ATOMS_BY_ID)
        walls = wall.WallSpawner(BOX_MIN, BOX_MAX, wall_seed)
        seq_alone = self._drive_pickup(alone, 6)
        seq_combined = self._drive_pickup(combined, 6, wall_spawner=walls)
        # Walls provably never rotate pickup positions.
        self.assertEqual(seq_alone, seq_combined)


class TestGeometry(unittest.TestCase):
    """Case 4: the four clearance legs, all expectations DERIVED."""

    def _drive(self, spawner, count):
        """Drive ``count`` far-head walls (L2/L3 vacuous) for L1/length."""
        return [spawner.next_wall(HEAD_FAR, FAR_ATOMS, [])
                for _ in range(count)]

    def test_endpoints_respect_box_margin(self):
        for name, box_min, box_max in PRESETS:
            with self.subTest(preset=name):
                spawner = wall.WallSpawner(box_min, box_max, 4242)
                margin = spawner.wall_box_margin
                walls = self._drive(spawner, 6)
                for endpoints in walls:
                    self.assertIsNotNone(endpoints)
                    for px, py in endpoints:
                        self.assertGreaterEqual(
                            px, box_min[0] + margin - TOL)
                        self.assertLessEqual(
                            px, box_max[0] - margin + TOL)
                        self.assertGreaterEqual(
                            py, box_min[1] + margin - TOL)
                        self.assertLessEqual(
                            py, box_max[1] - margin + TOL)

    def test_length_derived_from_span(self):
        for name, box_min, box_max in PRESETS:
            with self.subTest(preset=name):
                spawner = wall.WallSpawner(box_min, box_max, 4242)
                span = min(box_max[0] - box_min[0],
                           box_max[1] - box_min[1])
                expected = wall.WALL_LENGTH_FRACTION * span
                for endpoints in self._drive(spawner, 6):
                    self.assertIsNotNone(endpoints)
                    (ax, ay), (bx, by) = endpoints
                    seg = math.hypot(bx - ax, by - ay)
                    self.assertLessEqual(abs(seg - expected), TOL)

    def test_head_clearance_enforced(self):
        # (a) a plain run: every wall keeps the head at >= clearance.
        spawner = wall.WallSpawner(BOX_MIN, BOX_MAX, 2026)
        for _ in range(6):
            endpoints = spawner.next_wall((0.0, 0.0), FAR_ATOMS, [])
            self.assertIsNotNone(endpoints)
            self.assertGreaterEqual(
                _point_seg_dist(0.0, 0.0, endpoints),
                wall.WALL_HEAD_CLEARANCE_A - TOL)
        # (b) targeted rejection pin: capture a wall W1 from the far-head
        # run, then replay the SAME seed with the head placed AT W1's
        # midpoint -> W1 is rejected and the returned W2 (if any) keeps
        # the head distance.
        first = wall.WallSpawner(BOX_MIN, BOX_MAX, 4242)
        w1 = first.next_wall(HEAD_FAR, FAR_ATOMS, [])
        self.assertIsNotNone(w1)
        mx, my = _midpoint(w1)
        replay = wall.WallSpawner(BOX_MIN, BOX_MAX, 4242)
        w2 = replay.next_wall((mx, my), FAR_ATOMS, [])
        if w2 is not None:
            self.assertGreaterEqual(
                _point_seg_dist(mx, my, w2),
                wall.WALL_HEAD_CLEARANCE_A - TOL)

    def test_new_mol_no_overlap_per_atom(self):
        # The OWNER MANDATE: the wall must not pass through the newly
        # spawned mol. Production feeds RAW sym-first (sym, x, y, z)
        # seeds (L2 indexes x=[1]/y=[2]); place one atom exactly on W1's
        # midpoint (the STRADDLE case) and replay.
        first = wall.WallSpawner(BOX_MIN, BOX_MAX, 4242)
        w1 = first.next_wall(HEAD_FAR, FAR_ATOMS, [])
        self.assertIsNotNone(w1)
        mx, my = _midpoint(w1)
        atoms = [('C', mx, my, 0.0)]
        replay = wall.WallSpawner(BOX_MIN, BOX_MAX, 4242)
        w2 = replay.next_wall(HEAD_FAR, atoms, [])
        if w2 is not None:
            self.assertGreaterEqual(
                wall.min_atom_clearance(w2, atoms),
                wall.WALL_MOL_CLEARANCE_A - TOL)

    def test_live_mol_clearance_enforced(self):
        # Same replay pattern over live_mol_atoms: a bare (x, y) 2-tuple
        # at W1's midpoint (the second accepted shape -- L4 proven on
        # the bare form) drives a different-or-None wall.
        first = wall.WallSpawner(BOX_MIN, BOX_MAX, 4242)
        w1 = first.next_wall(HEAD_FAR, FAR_ATOMS, [])
        self.assertIsNotNone(w1)
        mx, my = _midpoint(w1)
        live = [(mx, my)]
        replay = wall.WallSpawner(BOX_MIN, BOX_MAX, 4242)
        w2 = replay.next_wall(HEAD_FAR, FAR_ATOMS, live)
        if w2 is not None:
            self.assertGreaterEqual(
                wall.min_atom_clearance(w2, live),
                wall.WALL_LIVE_CLEARANCE_A - TOL)


class TestExhaustion(unittest.TestCase):
    """Case 5: exhaustion -> None; degenerate box guard + draw accounting."""

    def test_none_when_nothing_legal(self):
        # head clearance override > box diagonal: every candidate fails L3.
        quick = wall.WallSpawner(BOX_MIN, BOX_MAX, 7,
                                 wall_head_clearance_a=500.0, max_draws=3)
        self.assertIsNone(quick.next_wall((0.0, 0.0), FAR_ATOMS, []))
        full = wall.WallSpawner(BOX_MIN, BOX_MAX, 7,
                                wall_head_clearance_a=500.0)
        self.assertIsNone(full.next_wall((0.0, 0.0), FAR_ATOMS, []))

    def test_degenerate_box_returns_none(self):
        # (0,0)-(5,5): shrunk interval empty on both axes -> None BEFORE
        # any draw (rng state unchanged).
        small = wall.WallSpawner((0.0, 0.0), (5.0, 5.0), 42)
        before = small._rng.getstate()
        self.assertIsNone(small.next_wall((0.0, 0.0), FAR_ATOMS, []))
        self.assertEqual(small._rng.getstate(), before)
        # (0,0)-(13,13): 2*WALL_BOX_MARGIN_A < 13 is FALSE -> the guard
        # does NOT fire; the draw loop runs (rng state advances).
        box13 = wall.WallSpawner((0.0, 0.0), (13.0, 13.0), 42)
        before13 = box13._rng.getstate()
        self.assertIsNone(box13.next_wall(HEAD_FAR, FAR_ATOMS, []))
        self.assertNotEqual(box13._rng.getstate(), before13)


class TestCtorKwargs(unittest.TestCase):
    """Case 6: ctor kwargs override + read-only effective-value properties."""

    def test_kwargs_override_and_properties(self):
        spawner = wall.WallSpawner(BOX_MIN, BOX_MAX, 4242,
                                   wall_box_margin_a=8.0,
                                   length_fraction=0.35,
                                   max_draws=2)
        self.assertEqual(spawner.box_min, (-55.0, -55.0))
        self.assertEqual(spawner.box_max, (55.0, 55.0))
        self.assertEqual(spawner.wall_box_margin, 8.0)
        self.assertEqual(spawner.length_fraction, 0.35)
        self.assertEqual(spawner.max_draws, 2)
        # Unoverridden -> the module table constant.
        self.assertEqual(spawner.wall_head_clearance,
                         wall.WALL_HEAD_CLEARANCE_A)
        # Endpoints respect the 8.0 effective margin.
        walls = [spawner.next_wall(HEAD_FAR, FAR_ATOMS, [])
                 for _ in range(4)]
        for endpoints in walls:
            self.assertIsNotNone(endpoints)
            for px, py in endpoints:
                self.assertGreaterEqual(px, -55.0 + 8.0 - TOL)
                self.assertLessEqual(px, 55.0 - 8.0 + TOL)
                self.assertGreaterEqual(py, -55.0 + 8.0 - TOL)
                self.assertLessEqual(py, 55.0 - 8.0 + TOL)
        # Lengths derive from the 0.35 override (span = 110.0).
        span = 110.0
        for endpoints in walls:
            (ax, ay), (bx, by) = endpoints
            seg = math.hypot(bx - ax, by - ay)
            self.assertLessEqual(abs(seg - 0.35 * span), TOL)
        # Read-only properties: no setter.
        with self.assertRaises(AttributeError):
            spawner.wall_box_margin = 1.0
        with self.assertRaises(AttributeError):
            spawner.length_fraction = 0.9
        # max_draws=2 respected: combined with the L3-blocked state the
        # observable is None (every attempt rejected).
        blocked = wall.WallSpawner(BOX_MIN, BOX_MAX, 4242,
                                   wall_head_clearance_a=500.0, max_draws=2)
        self.assertIsNone(blocked.next_wall((0.0, 0.0), FAR_ATOMS, []))


class TestMinAtomClearance(unittest.TestCase):
    """Case 7: the public per-atom point-segment helper contract."""

    def test_min_atom_clearance_contract(self):
        # Degenerate segment (a == b): distance to the point.
        degenerate = ((2.0, 3.0), (2.0, 3.0))
        self.assertLessEqual(
            abs(wall.min_atom_clearance(degenerate,
                                        [('C', 5.0, 7.0, 0.0)]) - 5.0), TOL)
        # An atom ON the segment => 0.0.
        seg = ((0.0, 0.0), (10.0, 0.0))
        self.assertLessEqual(
            abs(wall.min_atom_clearance(seg, [(5.0, 0.0)])), TOL)
        # Returns the SQRT distance, not the squared distance (4.0, not 16).
        self.assertLessEqual(
            abs(wall.min_atom_clearance(seg, [(0.0, 4.0)]) - 4.0), TOL)
        # BOTH repo shapes agree: sym-first 4-tuple reads x=[1]/y=[2] and
        # returns the SAME distance as its bare (x, y) twin.
        four = wall.min_atom_clearance(seg, [('C', 0.0, 4.0, 0.0)])
        bare = wall.min_atom_clearance(seg, [(0.0, 4.0)])
        self.assertLessEqual(abs(four - bare), TOL)
        # Bare (x, y, z) reads x=[0]/y=[1] (z ignored).
        self.assertLessEqual(
            abs(wall.min_atom_clearance(seg, [(5.0, 0.0, 9.0)])), TOL)
        # Min over many atoms.
        self.assertLessEqual(
            abs(wall.min_atom_clearance(
                seg, [(0.0, 6.0), (0.0, 2.0)]) - 2.0), TOL)
        # Empty atoms => loud programming-error tripwire.
        with self.assertRaises(ValueError):
            wall.min_atom_clearance(seg, [])


# ===========================================================================
# Phase 9.1 (Accumulating Line-Walls) -- ADDITIVE accumulation-policy pins.
# The 7 classes above stay BYTE-UNTOUCHED; these 5 classes exercise the
# accumulation engine room (cap gate / wall-vs-wall L5 / two-tier length /
# accumulated-set determinism / accum ctor kwargs). Every expectation is
# DERIVED from the module's own constants (never hardcoded values), so an
# owner retune at the 9.1-09 feel-check cannot silently break the suite.
# ===========================================================================


def _seg_len(endpoints):
    """Length of a returned wall segment."""
    (ax, ay), (bx, by) = endpoints
    return math.hypot(bx - ax, by - ay)


def _far_walls(count):
    """``count`` short segments parked far outside every preset box."""
    return [((5000.0 + 20.0 * i, 5000.0), (5010.0 + 20.0 * i, 5000.0))
            for i in range(count)]


# A far-away legal-shaped wall: L5 vacuous for any in-box candidate.
FAR_WALL = ((5000.0, 5000.0), (5010.0, 5000.0))


class TestCapGate(unittest.TestCase):
    """Cap-then-stop: at/above the cap -> None, consuming ZERO draws."""

    def test_at_cap_returns_none_zero_draws(self):
        cap = wall.WALL_MAX_LIVE_WALLS
        spawner = wall.WallSpawner(BOX_MIN, BOX_MAX, 4242)
        walls = _far_walls(cap)
        before = spawner._rng.getstate()
        self.assertIsNone(
            spawner.next_wall(HEAD_FAR, FAR_ATOMS, [],
                              existing_walls=walls))
        self.assertEqual(spawner._rng.getstate(), before)

    def test_below_cap_spawns(self):
        cap = wall.WALL_MAX_LIVE_WALLS
        spawner = wall.WallSpawner(BOX_MIN, BOX_MAX, 4242)
        walls = _far_walls(cap - 1)
        self.assertIsNotNone(
            spawner.next_wall(HEAD_FAR, FAR_ATOMS, [],
                              existing_walls=walls))

    def test_above_cap_returns_none(self):
        cap = wall.WALL_MAX_LIVE_WALLS
        spawner = wall.WallSpawner(BOX_MIN, BOX_MAX, 4242)
        walls = _far_walls(cap + 2)
        self.assertIsNone(
            spawner.next_wall(HEAD_FAR, FAR_ATOMS, [],
                              existing_walls=walls))

    def test_ctor_override_lowers_gate(self):
        spawner = wall.WallSpawner(BOX_MIN, BOX_MAX, 4242, max_live_walls=2)
        walls = _far_walls(2)
        before = spawner._rng.getstate()
        self.assertIsNone(
            spawner.next_wall(HEAD_FAR, FAR_ATOMS, [],
                              existing_walls=walls))
        self.assertEqual(spawner._rng.getstate(), before)


class TestWallWallClearance(unittest.TestCase):
    """L5: true segment-segment clearance (crossings => 0.0)."""

    def test_helper_contract(self):
        # Proper X-crossing -> 0.0.
        a = ((0.0, 0.0), (10.0, 10.0))
        b = ((0.0, 10.0), (10.0, 0.0))
        self.assertLessEqual(abs(wall.min_wall_clearance(a, [b])), TOL)
        # Parallel, gap 8.0 -> 8.0.
        c = ((0.0, 0.0), (10.0, 0.0))
        d = ((0.0, 8.0), (10.0, 8.0))
        self.assertLessEqual(abs(wall.min_wall_clearance(c, [d]) - 8.0), TOL)
        # Collinear overlapping -> 0.0.
        e = ((5.0, 0.0), (15.0, 0.0))
        self.assertLessEqual(abs(wall.min_wall_clearance(c, [e])), TOL)
        # Collinear disjoint -> the endpoint point-distance (10.0).
        f = ((20.0, 0.0), (30.0, 0.0))
        self.assertLessEqual(abs(wall.min_wall_clearance(c, [f]) - 10.0), TOL)
        # Degenerate point wall -> distance to the point (5.0).
        g = ((5.0, 5.0), (5.0, 5.0))
        self.assertLessEqual(abs(wall.min_wall_clearance(c, [g]) - 5.0), TOL)
        # Touching endpoint (non-collinear) -> 0.0.
        h = ((10.0, 0.0), (10.0, 10.0))
        self.assertLessEqual(abs(wall.min_wall_clearance(c, [h])), TOL)
        # Empty existing_walls -> loud programming-error tripwire.
        with self.assertRaises(ValueError):
            wall.min_wall_clearance(c, [])

    def test_accepted_wall_clears_existing(self):
        # A huge box so two long walls comfortably coexist; drive call 1
        # with no existing walls -> W1, then call 2 with [W1] -> W2.
        spawner = wall.WallSpawner((-500.0, -500.0), (500.0, 500.0), 4242)
        w1 = spawner.next_wall(HEAD_FAR, FAR_ATOMS, [])
        self.assertIsNotNone(w1)
        w2 = spawner.next_wall(HEAD_FAR, FAR_ATOMS, [], existing_walls=[w1])
        self.assertIsNotNone(w2)
        self.assertGreaterEqual(
            wall.min_wall_clearance(w2, [w1]),
            wall.WALL_WALL_CLEARANCE_A - TOL)

    def test_leg_gates_all_candidates(self):
        # A wall bisecting the box + an impossible 500.0 clearance -> None
        # (the test_none_when_nothing_legal override trick).
        bisect = ((-50.0, 0.0), (50.0, 0.0))
        spawner = wall.WallSpawner(BOX_MIN, BOX_MAX, 4242,
                                   wall_wall_clearance_a=500.0)
        self.assertIsNone(
            spawner.next_wall(HEAD_FAR, FAR_ATOMS, [],
                              existing_walls=[bisect]))


class TestAccumLengthTier(unittest.TestCase):
    """Two-tier length: wall #1 at WALL_LENGTH_FRACTION, walls #2+ at
    WALL_ACCUM_LENGTH_FRACTION; the accum override is respected."""

    def test_tier_lengths_derived(self):
        for name, box_min, box_max in PRESETS:
            with self.subTest(preset=name):
                span = min(box_max[0] - box_min[0],
                           box_max[1] - box_min[1])
                # Tier 0: no existing walls -> full Phase-9 fraction.
                sp0 = wall.WallSpawner(box_min, box_max, 4242)
                w0 = sp0.next_wall(HEAD_FAR, FAR_ATOMS, [])
                self.assertIsNotNone(w0)
                self.assertLessEqual(
                    abs(_seg_len(w0) - wall.WALL_LENGTH_FRACTION * span), TOL)
                # Tier 1: one far-away existing wall -> accum fraction.
                sp1 = wall.WallSpawner(box_min, box_max, 4242)
                w1 = sp1.next_wall(HEAD_FAR, FAR_ATOMS, [],
                                   existing_walls=[FAR_WALL])
                self.assertIsNotNone(w1)
                self.assertLessEqual(
                    abs(_seg_len(w1)
                        - wall.WALL_ACCUM_LENGTH_FRACTION * span), TOL)

    def test_accum_fraction_override(self):
        name, box_min, box_max = PRESETS[1]
        span = min(box_max[0] - box_min[0], box_max[1] - box_min[1])
        spawner = wall.WallSpawner(box_min, box_max, 4242,
                                   accum_length_fraction=0.5)
        w = spawner.next_wall(HEAD_FAR, FAR_ATOMS, [],
                              existing_walls=[FAR_WALL])
        self.assertIsNotNone(w)
        self.assertLessEqual(abs(_seg_len(w) - 0.5 * span), TOL)


class TestAccumulatedDeterminism(unittest.TestCase):
    """GAME-07 same-seed => same accumulated SET (None positions included)."""

    HEADS = [(0.0, 0.0), (3.0, -2.0), (-4.0, 1.0), (2.0, 5.0),
             (-5.0, -3.0), (1.0, 2.0), (4.0, -4.0), (-2.0, 3.0)]

    def _drive(self, seed):
        """Drive 8 calls; the accumulated set grows from prior results."""
        spawner = wall.WallSpawner(BOX_MIN, BOX_MAX, seed)
        walls = []
        out = []
        for hx, hy in self.HEADS:
            result = spawner.next_wall((hx, hy), FAR_ATOMS, [],
                                       existing_walls=walls)
            out.append(result)
            if result is not None:
                walls.append(result)
        return out

    def test_same_seed_same_set(self):
        self.assertEqual(self._drive(1234), self._drive(1234))

    def test_different_seed_diverges(self):
        self.assertNotEqual(self._drive(1234), self._drive(9999))


class TestAccumCtorKwargs(unittest.TestCase):
    """The three accumulation ctor kwargs + read-only properties."""

    def test_overrides_and_defaults(self):
        spawner = wall.WallSpawner(BOX_MIN, BOX_MAX, 4242,
                                   accum_length_fraction=0.5,
                                   wall_wall_clearance_a=12.0,
                                   max_live_walls=3)
        self.assertEqual(spawner.accum_length_fraction, 0.5)
        self.assertEqual(spawner.wall_wall_clearance, 12.0)
        self.assertEqual(spawner.max_live_walls, 3)
        default = wall.WallSpawner(BOX_MIN, BOX_MAX, 4242)
        self.assertEqual(default.accum_length_fraction,
                         wall.WALL_ACCUM_LENGTH_FRACTION)
        self.assertEqual(default.wall_wall_clearance,
                         wall.WALL_WALL_CLEARANCE_A)
        self.assertEqual(default.max_live_walls, wall.WALL_MAX_LIVE_WALLS)

    def test_read_only_properties(self):
        spawner = wall.WallSpawner(BOX_MIN, BOX_MAX, 4242)
        with self.assertRaises(AttributeError):
            spawner.accum_length_fraction = 0.9
        with self.assertRaises(AttributeError):
            spawner.wall_wall_clearance = 1.0
        with self.assertRaises(AttributeError):
            spawner.max_live_walls = 9


if __name__ == '__main__':
    unittest.main()
