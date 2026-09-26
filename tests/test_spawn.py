"""spawn tests: deterministic seeded pickup-spawn policy pins (G3, 05-03).

Eleven pin groups mirror the plan's behavior cases:

  1. Determinism  -- two same-seed spawners produce identical
     first()/next_after() sequences (positions + ids); a different seed
     yields different full (record id, pid, centroid) shape sequences
     (seeded per-axis uniform draws); seed_from_setup is stable across
     two calls AND across processes (zlib.crc32, never hash()).
  2. Bounds       -- every returned centroid lies inside the wall-margined
     box (|x|,|y| <= 55 - 3.5 + 1e-9 on the medium preset).
  3. Head clear   -- every spawn lands >= min_head_dist from the head:
     a box-proportional minimum (min(max(0.35*h, HEAD_CLEARANCE_A),
     0.8*h) with h the shrunk half-span -> 18.025 A on the +/-55
     fixtures, 11.025 on small +/-35, 28.525 on large +/-85; tiny boxes
     fold the value <= 0.8*h so degenerate legs go vacuous), tunable
     via the min_head_dist_a ctor kwarg and exposed as the read-only
     min_head_dist property (2026-09-26 Phase 5.3 uniform policy --
     the LOOKAHEAD 'ahead of heading' anchoring is RETIRED).
  4. Chain atoms  -- a box-covering chain-atom lattice with exactly ONE
     pocket (downscaled to the +/-35 preset per the plan's cost note):
     the spawn must land in the pocket and every atom of the returned
     (translated) molecule is >= 3.0 A from every lattice atom.
  5. Live pickups -- next_after keeps >= 6.0 A from a live centroid placed
     on the previous spawn.
  6. Cycle + ids  -- records come out in records-list order wrapping
     forever; pids 'pick_0001', 'pick_0002', ... advance only on spawns.
  7. MAX_LIVE     -- can_spawn(live_count) is True for live_count < 4 and
     False for >= 4 (MAX_LIVE_PICKUPS = 4).
  8. build_pickup_seed -- the engine pickup contract: id / molecule_id /
     centroid / translated atoms / atoms_n (atoms REQUIRED by the 02-13
     sweep pickup leg).
  9. Exhaustion   -- no legal position -> None, never an exception, and NO
     state advance (same record + same pid offered on the next call).
 10. Demote       -- demote-after-refuse (2026-09-20, 05-16 cascade fix):
     a refused molecule is not re-served next (never permanently
     excluded either); every-candidate-refused PAUSES spawning for a
     resumable exhaust cooldown (auto-resumes after K ticks; never a
     permanent latch).
 11. Fallback     -- the seeded grid-fallback scan offset (2026-09-26
     Phase 5.3 plan 5.3-02): on a saturated pocket lattice a forced
     fallback starts at a SEEDED cell index (randrange over the cell
     count) and wraps, so different seeds land at DIFFERENT legal cells
     (the corner-bias clustering is gone) while the same seed stays
     byte-identical (GAME-07 holds on the fallback path too).

Spawners are built from the REAL demo records (setloader.load_demo_set
with the shipped stacking dataset) and origin-centered synthetic atoms (6
dummy atoms on a 1.4 A ring -- the clearance math does not need real SDF
geometry).

Discovery (verified on python3.6.9 -- do NOT add -t .):

    python3.6 -m unittest discover -s tests -p "test_*.py" -v
"""
import math
import os
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from serpentrum import setloader  # noqa: E402
from serpentrum import spawn  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Medium preset xy extents (setup_logic.BOX_PRESETS['medium']).
# OWNER-APPROVED CONFIG CHANGES (2026-09-19 then 2026-09-20): medium is
# now +/-55 (was +/-18, then +/-30); all fixtures below scale off these
# two constants.
BOX_MIN = (-55.0, -55.0)
BOX_MAX = (55.0, 55.0)
WALL_MARGIN_A = 3.5

# Canonical setup dict for the seed pins.
SETUP = {
    'schema_version': 1,
    'demo_set': 'set_a',
    'head_molecule': 'random',
    'box_preset': 'medium',
    'win_cap_molecules': 10,
}

# Tolerance for clearance assertions (float arithmetic around exactly-3.0 /
# exactly-6.0 cases).
TOL = 1e-9


def _dummy_atoms(symbol):
    """6 dummy atoms on a 1.4 A ring about the ORIGIN (origin-centered)."""
    return [(symbol,
             1.4 * math.cos(k * math.pi / 3.0),
             1.4 * math.sin(k * math.pi / 3.0),
             0.0) for k in range(6)]


def _dist(ax, ay, bx, by):
    return math.hypot(ax - bx, ay - by)


def _pocket_lattice(pocket=(24.0, 24.0)):
    """Box-covering +/-35-preset chain-atom lattice with exactly ONE
    pocket: points on a 2.0 A grid over [-32, 32]^2 (covers the shrunk
    box [-31.5, 31.5]^2) EXCLUDING every point within 5.0 A of the
    pocket center. Copy of the TestGeometry.test_chain_atom_clearance
    lattice; downscaled to the +/-35 preset per the plan's cost note
    (a full +/-55 cover lattice is ~2,680 atoms and the grid-scan
    fallback would crawl)."""
    lattice = []
    for i in range(33):
        for j in range(33):
            qx = -32.0 + 2.0 * i
            qy = -32.0 + 2.0 * j
            if _dist(qx, qy, pocket[0], pocket[1]) >= 5.0:
                lattice.append(('C', qx, qy, 0.0))
    return lattice


class SpawnTestBase(unittest.TestCase):
    """Shared demo records + spawner factory (real set_a records)."""

    @classmethod
    def setUpClass(cls):
        cls.records, cls.errors = setloader.load_demo_set(
            stacking_path=setloader.default_stacking_path())
        assert cls.errors == [], cls.errors
        assert len(cls.records) == 5  # set_a has 5 species
        cls.atoms_by_id = dict(
            (record['id'], _dummy_atoms('C')) for record in cls.records)

    def make_spawner(self, seed, box_min=BOX_MIN, box_max=BOX_MAX):
        return spawn.PickupSpawner(self.records, box_min, box_max, seed,
                                   self.atoms_by_id)

    @staticmethod
    def shape(result):
        """(record, pid, centroid) -> comparable tuple."""
        record, pid, centroid = result
        return (record['id'], pid, centroid)


class TestSeed(SpawnTestBase):
    """Case 1: seed function stability (crc32, never hash())."""

    def test_seed_from_setup_stable_in_process(self):
        first = spawn.seed_from_setup(SETUP)
        second = spawn.seed_from_setup(SETUP)
        self.assertIsInstance(first, int)
        self.assertEqual(first, second)

    def test_seed_from_setup_changes_with_setup(self):
        other = dict(SETUP)
        other['box_preset'] = 'large'
        self.assertNotEqual(spawn.seed_from_setup(SETUP),
                            spawn.seed_from_setup(other))

    def test_seed_from_setup_stable_across_processes(self):
        # crc32 is process-stable; hash() is not (PYTHONHASHSEED). Prove
        # the pinned contract by re-deriving the seed in a child process.
        code = (
            'import sys; sys.path.insert(0, %r);'
            'from serpentrum import spawn;'
            'print(spawn.seed_from_setup(%r))' % (ROOT, SETUP))
        proc = subprocess.Popen(
            [sys.executable, '-c', code],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=ROOT)
        out, err = proc.communicate()
        self.assertEqual(proc.returncode, 0,
                         'child seed probe failed: %s' % err.decode())
        self.assertEqual(int(out.strip()), spawn.seed_from_setup(SETUP))


class TestDeterminism(SpawnTestBase):
    """Case 1: same seed -> byte-identical sequences; diff seed -> diff."""

    def _drive(self, spawner, rounds):
        """Drive a deterministic call sequence; return list of shapes."""
        out = [self.shape(spawner.first((0.0, 0.0), 'right'))]
        live = [out[0][2]]
        for _ in range(rounds):
            result = spawner.next_after((0.0, 0.0), 'right', [], live)
            self.assertIsNotNone(result)
            out.append(self.shape(result))
            live.append(out[-1][2])
        return out

    def test_same_seed_identical_sequences(self):
        first = self._drive(self.make_spawner(1234), 6)
        second = self._drive(self.make_spawner(1234), 6)
        self.assertEqual(first, second)

    def test_different_seed_diverges(self):
        # Uniform box-sampling policy (2026-09-26 Phase 5.3): there is no
        # lateral channel to read back -- candidates are seeded per-axis
        # uniform draws over the shrunk box. Two different seeds (almost
        # surely) produce different FULL (record id, pid, centroid) shape
        # sequences over the same call sequence. Determinism-semantics
        # pin: the contract is 'same seed => identical', this asserts the
        # complementary 'different seed => different'.
        def shapes(seed):
            spawner = self.make_spawner(seed)
            out = [self.shape(spawner.first((0.0, 0.0), 'right'))]
            for _ in range(5):
                result = spawner.next_after((0.0, 0.0), 'right', [], [])
                self.assertIsNotNone(result)
                out.append(self.shape(result))
            return out
        self.assertNotEqual(shapes(1234), shapes(9999))


class TestGeometry(SpawnTestBase):
    """Cases 2-5: bounds, head clearance, chain-atom and live clearance."""

    def test_bounds_within_wall_margin(self):
        spawner = self.make_spawner(777)
        heads = [(0.0, 0.0), (12.0, 12.0), (-14.0, -6.0), (16.0, 16.0),
                 (-17.0, 17.0), (8.0, -17.0)]
        headings = ['right', 'up', 'left', 'down']
        live = []
        for turn in range(12):
            result = spawner.next_after(
                heads[turn % len(heads)], headings[turn % len(headings)],
                [], live)
            self.assertIsNotNone(result)
            cx, cy = result[2]
            limit = 55.0 - WALL_MARGIN_A + TOL  # BOX_MAX[0] - margin
            self.assertLessEqual(abs(cx), limit)
            self.assertLessEqual(abs(cy), limit)
            live.append((cx, cy))

    def test_first_clears_head_by_min_dist(self):
        # Renamed from test_first_is_ahead_and_clears_head (2026-09-26
        # Phase 5.3): the LOOKAHEAD 'ahead of heading' semantics are
        # RETIRED -- candidates are seeded-uniform over the shrunk box,
        # so 'cx > 0' no longer holds. The surviving head constraint is
        # the box-proportional min_head_dist floor (18.025 A on the
        # module's +/-55 fixtures).
        spawner = self.make_spawner(42)
        result = spawner.first((0.0, 0.0), 'right')
        cx, cy = result[2]
        self.assertGreaterEqual(_dist(cx, cy, 0.0, 0.0),
                                spawner.min_head_dist - TOL)

    def test_chain_atom_clearance(self):
        # Uniform policy rewrite (2026-09-26 Phase 5.3): candidates can
        # land ANYWHERE in the shrunk box, so the clearance probe is a
        # box-covering lattice with exactly ONE pocket (TestExhaustion
        # lattice style, downscaled to the +/-35 preset per the plan's
        # cost note -- a full +/-55 cover lattice is ~2,680 atoms and
        # the grid-scan fallback would crawl). Write-time verification
        # (probe over the exact chain leg, seed-independent): the ONLY
        # legal centroids lie within ~1.6 A of the pocket center and the
        # fallback's first legal hit is (24.5, 22.5), 1.581 A away.
        pocket = (24.0, 24.0)
        lattice = []
        for i in range(33):
            for j in range(33):
                qx = -32.0 + 2.0 * i
                qy = -32.0 + 2.0 * j
                if _dist(qx, qy, pocket[0], pocket[1]) >= 5.0:
                    lattice.append(('C', qx, qy, 0.0))
        spawner = self.make_spawner(42, box_min=(-35.0, -35.0),
                                    box_max=(35.0, 35.0))
        result = spawner.next_after((0.0, 0.0), 'right', lattice, [])
        self.assertIsNotNone(result)
        record, _pid, centroid = result
        cx, cy = centroid
        # Generous pocket bound -- a later fallback-start change cannot
        # break this; the MODE of arrival (32-draw loop vs grid fallback)
        # is deliberately NOT asserted: either path proves the chain leg.
        self.assertLessEqual(_dist(cx, cy, pocket[0], pocket[1]), 6.0)
        for sym, ax, ay, az in self.atoms_by_id[record['id']]:
            tx, ty = ax + cx, ay + cy
            for _csym, qx, qy, _qz in lattice:
                self.assertGreaterEqual(_dist(tx, ty, qx, qy), 3.0 - TOL)

    def _drive_spawns(self, spawner, count):
        """Drive ``count`` next_after calls from a fixed head at the
        origin with an accumulating live list; return the live list."""
        live = []
        for _ in range(count):
            result = spawner.next_after((0.0, 0.0), 'right', [], live)
            self.assertIsNotNone(result)
            live.append(result[2])
        return live

    def test_min_head_dist_default_proportional(self):
        # Default floor = min(max(0.35*h, 5.0), 0.8*h) with h the shrunk
        # half-span (owner-scaled presets 2026-09-19b):
        # small h=31.5 -> 11.025; medium h=51.5 -> 18.025;
        # large h=81.5 -> 28.525.
        cases = [(('small'), (-35.0, -35.0), (35.0, 35.0), 11.025),
                 (('medium'), (-55.0, -55.0), (55.0, 55.0), 18.025),
                 (('large'), (-85.0, -85.0), (85.0, 85.0), 28.525)]
        for name, box_min, box_max, expected in cases:
            with self.subTest(preset=name):
                spawner = self.make_spawner(42, box_min=box_min,
                                            box_max=box_max)
                self.assertLessEqual(
                    abs(spawner.min_head_dist - expected), TOL)

    def test_min_head_dist_kwarg_override(self):
        spawner = spawn.PickupSpawner(
            self.records, BOX_MIN, BOX_MAX, 42, self.atoms_by_id,
            min_head_dist_a=25.0)
        self.assertEqual(spawner.min_head_dist, 25.0)
        live = [spawner.first((0.0, 0.0), 'right')[2]]
        live.extend(self._drive_spawns(spawner, 2))
        for cx, cy in live:
            self.assertGreaterEqual(_dist(cx, cy, 0.0, 0.0), 25.0 - TOL)

    def test_min_head_dist_enforced_by_default(self):
        # 10 consecutive spawns: every centroid >= min_head_dist (18.025)
        # from the head. (RETIRED policy cap: the old LOOKAhead bubble
        # kept every spawn within sqrt(8^2 + 6^2) = 10.0 A of the head.)
        spawner = self.make_spawner(42)
        for cx, cy in self._drive_spawns(spawner, 10):
            self.assertGreaterEqual(_dist(cx, cy, 0.0, 0.0),
                                    spawner.min_head_dist - TOL)

    def test_spawns_spread_across_box(self):
        # The 2026-09-26 owner complaint refuted by construction. Fixed
        # seed 42 verified at write time: 10 spawns visit all 4
        # quadrants, reach 60.0 A from the origin (old bubble cap:
        # 10.0 A), and never violate the floor.
        spawner = self.make_spawner(42)
        live = self._drive_spawns(spawner, 10)
        quadrants = set((cx > 0.0, cy > 0.0) for cx, cy in live)
        # (a) spawns visit >= 3 of the 4 quadrants (exact zero coords
        # impossible given the min-dist floor).
        self.assertGreaterEqual(len(quadrants), 3)
        # (b) at least one spawn lands far beyond the retired 10.0 A
        # LOOKAHEAD bubble.
        self.assertGreater(
            max(_dist(cx, cy, 0.0, 0.0) for cx, cy in live), 30.0)
        # (c) the floor still holds everywhere.
        for cx, cy in live:
            self.assertGreaterEqual(_dist(cx, cy, 0.0, 0.0),
                                    spawner.min_head_dist - TOL)

    def test_tiny_box_min_dist_folds_vacuous(self):
        # Degenerate boxes: the 0.8*h cap folds min_head_dist down (and
        # negative) so the head leg goes vacuous and TestExhaustion's
        # +/-6 and (0,0)-(2,2) None semantics stay meaningful.
        smallish = self.make_spawner(42, box_min=(-6.0, -6.0),
                                     box_max=(6.0, 6.0))
        # h = 2.5 -> min(max(0.875, 5.0), 0.8*2.5) = min(5.0, 2.0) = 2.0.
        self.assertLessEqual(abs(smallish.min_head_dist - 2.0), TOL)
        tiny = self.make_spawner(42, box_min=(0.0, 0.0), box_max=(2.0, 2.0))
        # h = -2.5 -> min(max(-0.875, 5.0), 0.8*-2.5) = -2.0 -> vacuous.
        self.assertLessEqual(tiny.min_head_dist, 0.0)

    def test_live_pickup_clearance(self):
        spawner = self.make_spawner(42)
        first = spawner.first((0.0, 0.0), 'right')
        live = [first[2]]
        result = spawner.next_after((0.0, 0.0), 'right', [], live)
        self.assertIsNotNone(result)
        cx, cy = result[2]
        self.assertGreaterEqual(_dist(cx, cy, live[0][0], live[0][1]),
                                6.0 - TOL)


class TestCycleAndIds(SpawnTestBase):
    """Cases 6-7: record cycle order, pid monotonicity, MAX_LIVE gate."""

    def test_cycle_records_in_list_order_wrapping(self):
        spawner = self.make_spawner(2026)
        expected_ids = [r['id'] for r in self.records]
        live = []
        seen = []
        # 8 spawns = one full cycle of 5 + 3 wrapped.
        result = spawner.first((0.0, 0.0), 'right')
        self.assertIsNotNone(result)
        seen.append(result)
        live.append(result[2])
        for _ in range(7):
            result = spawner.next_after((0.0, 0.0), 'right', [], live)
            self.assertIsNotNone(result)
            seen.append(result)
            live.append(result[2])
        got_ids = [entry[0]['id'] for entry in seen]
        self.assertEqual(got_ids,
                         [expected_ids[i % len(expected_ids)]
                          for i in range(8)])
        got_pids = [entry[1] for entry in seen]
        self.assertEqual(got_pids,
                         ['pick_%04d' % n for n in range(1, 9)])
        # pids strictly increasing.
        serials = [int(pid.split('_')[1]) for pid in got_pids]
        self.assertEqual(serials, sorted(serials))
        self.assertEqual(len(set(serials)), len(serials))

    def test_can_spawn_gate(self):
        self.assertEqual(spawn.MAX_LIVE_PICKUPS, 4)
        spawner = self.make_spawner(1)
        for live_count in (0, 1, 2, 3):
            self.assertTrue(spawner.can_spawn(live_count))
        for live_count in (4, 5, 42):
            self.assertFalse(spawner.can_spawn(live_count))


class TestPickupSeedShape(SpawnTestBase):
    """Case 8: build_pickup_seed emits the engine pickup contract."""

    def test_build_pickup_seed_contract(self):
        record = self.records[0]
        atoms = _dummy_atoms('C')
        seed = spawn.build_pickup_seed(record, 'pick_0007', (3.5, -2.0),
                                       atoms)
        self.assertEqual(seed['id'], 'pick_0007')
        self.assertEqual(seed['molecule_id'], record['id'])
        self.assertEqual(seed['centroid'], (3.5, -2.0))
        self.assertEqual(seed['atoms_n'], len(atoms))
        self.assertEqual(len(seed['atoms']), len(atoms))
        for original, moved in zip(atoms, seed['atoms']):
            self.assertEqual(moved[0], original[0])
            self.assertEqual(moved[1], original[1] + 3.5)
            self.assertEqual(moved[2], original[2] - 2.0)
            self.assertEqual(moved[3], original[3])
        # atoms copied: a fresh list, caller data untouched.
        self.assertIsNot(seed['atoms'], atoms)
        self.assertEqual(atoms, _dummy_atoms('C'))


class TestDemoteAfterRefuse(SpawnTestBase):
    """Case 10: demote-after-refuse (05-16 re-test refuse-cascade fix,
    2026-09-20) — a refused molecule is NOT re-served immediately;
    every-candidate-refused pauses spawning for a resumable exhaust
    cooldown (NEVER a permanent latch — 2026-09-20 follow-up: the
    permanent latch deadlocked runs near walls where refuses are
    position-dependent)."""

    def test_refused_molecule_not_reserved_next(self):
        # Serve the first pickup, refuse its molecule, then the NEXT
        # spawn must be a DIFFERENT molecule (the refused record moved
        # to the back of the serve order).
        spawner = self.make_spawner(1234)
        record, _pid, centroid = spawner.first((0.0, 0.0), 'right')
        spawner.note_resolution(record['id'], refused=True)
        result = spawner.next_after((0.0, 0.0), 'right', [], [centroid])
        self.assertIsNotNone(result)
        self.assertNotEqual(result[0]['id'], record['id'])

    def test_single_refuse_is_not_permanent_exclusion(self):
        # One transient refuse must NOT permanently exclude a molecule
        # (pool of 5, cap 10 REQUIRES repeats): after the rest of the
        # pool cycles once, the refused molecule is served again.
        spawner = self.make_spawner(1234)
        record, _pid, centroid = spawner.first((0.0, 0.0), 'right')
        refused_id = record['id']
        spawner.note_resolution(refused_id, refused=True)
        live = [centroid]
        served = []
        for _ in range(len(self.records)):
            result = spawner.next_after((0.0, 0.0), 'right', [], live)
            self.assertIsNotNone(result)
            served.append(result[0]['id'])
            live.append(result[2])
        # The refused id re-entered exactly once, LAST in the rotation.
        self.assertEqual(served.count(refused_id), 1)
        self.assertEqual(served[-1], refused_id)

    def test_full_streak_pauses_then_auto_resumes(self):
        # Every pool candidate refuses consecutively: the pause fires
        # exactly at the pool size; during the cooldown _spawn returns
        # None even with a clear board -- but the pause is RESUMABLE
        # (tick() counts the window down and spawning resumes), NEVER
        # a permanent latch. (Granular timing/streak-freeze pins live
        # in TestExhaustCooldown.)
        spawner = spawn.PickupSpawner(
            self.records, BOX_MIN, BOX_MAX, 1234, self.atoms_by_id,
            exhaust_cooldown_ticks=3)
        self.assertFalse(spawner.spawn_paused)
        ids = [r['id'] for r in self.records]
        # Drive one issue per refusal: each refused spawn rotates the
        # order; after len(pool) consecutive refuses the pause fires.
        result = spawner.first((0.0, 0.0), 'right')
        self.assertIsNotNone(result)
        live = [result[2]]
        spawner.note_resolution(result[0]['id'], refused=True)
        self.assertFalse(spawner.spawn_paused)
        for _ in range(len(ids) - 1):
            result = spawner.next_after((0.0, 0.0), 'right', [], live)
            self.assertIsNotNone(result)
            live.append(result[2])
            spawner.note_resolution(result[0]['id'], refused=True)
        # len(ids) consecutive refuses have now been recorded.
        self.assertTrue(spawner.spawn_paused)
        # Paused: no spawn while the cooldown runs, cleared board or not.
        self.assertIsNone(spawner.next_after((0.0, 0.0), 'right', [], []))
        self.assertIsNone(spawner.next_after((0.0, 0.0), 'right', [], []))
        # Cooldown elapses: spawning auto-resumes with the same policy.
        while not spawner.tick():
            pass
        self.assertFalse(spawner.spawn_paused)
        self.assertIsNotNone(spawner.next_after((0.0, 0.0), 'right',
                                                [], []))

    def test_placed_resolution_resets_consecutive_counter(self):
        # A placed capture between refuses keeps the pool alive: the
        # consecutive counter resets immediately, so 2N-1 total refuses
        # (alternating with one placement per cycle) never pause.
        spawner = self.make_spawner(1234)
        result = spawner.first((0.0, 0.0), 'right')
        self.assertIsNotNone(result)
        live = [result[2]]
        spawner.note_resolution(result[0]['id'], refused=True)
        for cycle in range(3):
            # Place one (reset), then refuse every OTHER pool record.
            result = spawner.next_after((0.0, 0.0), 'right', [], live)
            self.assertIsNotNone(result)
            live.append(result[2])
            spawner.note_resolution(result[0]['id'], refused=False)
            self.assertFalse(spawner.spawn_paused)
            for _ in range(len(self.records) - 1):
                result = spawner.next_after((0.0, 0.0), 'right', [], live)
                self.assertIsNotNone(result)
                live.append(result[2])
                spawner.note_resolution(result[0]['id'], refused=True)
            # Only len-1 consecutive refuses: below the pause.
            self.assertFalse(spawner.spawn_paused)

    def test_unknown_molecule_id_is_ignored(self):
        spawner = self.make_spawner(1234)
        spawner.note_resolution('no_such_molecule', refused=True)
        self.assertEqual(spawner.pool_size, len(self.records))
        result = spawner.first((0.0, 0.0), 'right')
        self.assertIsNotNone(result)
        self.assertEqual(result[0]['id'], self.records[0]['id'])


class TestExhaustCooldown(SpawnTestBase):
    """Exhaust = a resumable cooldown, never permadeath (2026-09-20
    follow-up to the f211d97 latch).

    Pins: default K == EXHAUST_COOLDOWN_TICKS == 100; pause fires at
    streak == pool size exactly; no spawn during the cooldown; tick()
    returns True exactly on the Kth tick (the resume edge); the refuse
    streak does NOT advance while paused (no extend, no refresh);
    re-pausing after a resume requires a FRESH pool-size streak; a
    placed capture during the pause resets the streak without cutting
    the cooldown short.
    """

    def _paused_spawner(self, cooldown=4):
        """Helper: drive a small-cooldown spawner into the pause with
        pool_size consecutive refuses; assert the pause fired. Returns
        the paused spawner."""
        spawner = spawn.PickupSpawner(
            self.records, BOX_MIN, BOX_MAX, 1234, self.atoms_by_id,
            exhaust_cooldown_ticks=cooldown)
        result = spawner.first((0.0, 0.0), 'right')
        assert result is not None
        live = [result[2]]
        spawner.note_resolution(result[0]['id'], refused=True)
        for _ in range(len(self.records) - 1):
            result = spawner.next_after((0.0, 0.0), 'right', [], live)
            assert result is not None
            live.append(result[2])
            spawner.note_resolution(result[0]['id'], refused=True)
        assert spawner.spawn_paused
        return spawner

    def test_default_cooldown_is_100_ticks(self):
        self.assertEqual(spawn.EXHAUST_COOLDOWN_TICKS, 100)
        spawner = self.make_spawner(1234)
        self.assertEqual(spawner.exhaust_cooldown_ticks, 100)
        self.assertFalse(spawner.spawn_paused)

    def test_constructor_override_smaller_cooldown(self):
        spawner = spawn.PickupSpawner(
            self.records, BOX_MIN, BOX_MAX, 1234, self.atoms_by_id,
            exhaust_cooldown_ticks=2)
        self.assertEqual(spawner.exhaust_cooldown_ticks, 2)

    def test_no_spawn_for_exactly_k_ticks(self):
        # Pause with K=4: each of the first K-1 tick() calls returns
        # False and spawning stays off; the Kth returns True (resume
        # edge) and spawning is back on.
        spawner = self._paused_spawner(cooldown=4)
        for _ in range(3):
            self.assertFalse(spawner.tick())
            self.assertTrue(spawner.spawn_paused)
            self.assertIsNone(
                spawner.next_after((0.0, 0.0), 'right', [], []))
        self.assertTrue(spawner.tick())
        self.assertFalse(spawner.spawn_paused)
        self.assertIsNotNone(spawner.next_after((0.0, 0.0), 'right',
                                                [], []))
        # tick() while NOT paused is a no-op.
        self.assertFalse(spawner.tick())

    def test_streak_does_not_advance_while_paused(self):
        # A refuse recorded DURING the cooldown (a still-live pickup
        # failing on capture) may NOT extend or refresh the window:
        # resume still fires after exactly K total ticks.
        spawner = self._paused_spawner(cooldown=4)
        self.assertFalse(spawner.tick())  # 1 of 4 elapsed
        refused_again = self.records[0]['id']  # current serve front
        spawner.note_resolution(refused_again, refused=True)
        self.assertFalse(spawner.tick())  # 2 of 4
        self.assertFalse(spawner.tick())  # 3 of 4
        self.assertTrue(spawner.tick())   # 4 of 4: resume, not refresh
        self.assertFalse(spawner.spawn_paused)
        # Demotion itself is untouched: rotation still applied for the
        # mid-pause refuse (the served order cycles on the next spawn).
        result = spawner.next_after((0.0, 0.0), 'right', [], [])
        self.assertIsNotNone(result)
        self.assertNotEqual(result[0]['id'], refused_again)

    def test_repause_requires_fresh_pool_size_streak(self):
        # After the resume edge resets the streak, a single refuse does
        # NOT re-pause; a full new pool-size streak is required.
        spawner = self._paused_spawner(cooldown=2)
        self.assertFalse(spawner.tick())
        self.assertTrue(spawner.tick())
        self.assertFalse(spawner.spawn_paused)
        result = spawner.next_after((0.0, 0.0), 'right', [], [])
        self.assertIsNotNone(result)
        live = [result[2]]
        spawner.note_resolution(result[0]['id'], refused=True)
        self.assertFalse(spawner.spawn_paused)  # 1 refuse: no pause
        for _ in range(len(self.records) - 1):
            result = spawner.next_after((0.0, 0.0), 'right', [], live)
            self.assertIsNotNone(result)
            live.append(result[2])
            spawner.note_resolution(result[0]['id'], refused=True)
        self.assertTrue(spawner.spawn_paused)   # full streak: pause

    def test_placed_during_pause_resets_streak_not_cooldown(self):
        # Any successful placement resets the refuse streak IMMEDIATELY
        # (even mid-cooldown) -- but it does NOT cut the cooldown
        # short: spawning stays paused until the window elapses.
        spawner = self._paused_spawner(cooldown=3)
        spawner.note_resolution('anything', refused=False)
        self.assertTrue(spawner.spawn_paused)  # cooldown still runs
        self.assertIsNone(spawner.next_after((0.0, 0.0), 'right', [], []))
        self.assertFalse(spawner.tick())
        self.assertFalse(spawner.tick())
        self.assertTrue(spawner.tick())   # resume after exactly 3 ticks
        self.assertFalse(spawner.spawn_paused)


class TestExhaustion(SpawnTestBase):
    """Case 9: no legal position -> None (no exception, no state advance)."""

    def test_saturated_box_returns_none_without_advance(self):
        # Saturate a SMALL custom box (not the medium preset — the
        # 2026-09-20 owner-approved +/-55 box would need a 70x70 cover
        # lattice against the full grid-scan fallback: slow for a pin).
        # Box +/-6 -> shrunk +/-2.5; the 1.5 A lattice at +/-4.5 puts
        # every in-box point < 3.0 A from a chain atom (and inside the
        # 5.0 A head clearance too).
        spawner = self.make_spawner(42, box_min=(-6.0, -6.0),
                                    box_max=(6.0, 6.0))
        cover = [('C', -4.5 + 1.5 * i, -4.5 + 1.5 * j, 0.0)
                 for i in range(7) for j in range(7)]
        self.assertIsNone(spawner.next_after((0.0, 0.0), 'right', cover, []))
        # No state advance on None: the same record is offered next, and
        # the pid counter did not consume a serial. (Re-head far from
        # the origin so the 5.0 A head clearance legalizes a spot in
        # the small box.)
        result = spawner.next_after((4.0, 4.0), 'left', [], [])
        self.assertIsNotNone(result)
        self.assertEqual(result[0]['id'], self.records[0]['id'])
        self.assertEqual(result[1], 'pick_0001')

    def test_too_small_box_returns_none(self):
        spawner = self.make_spawner(42, box_min=(0.0, 0.0),
                                    box_max=(2.0, 2.0))
        self.assertIsNone(spawner.first((0.0, 0.0), 'right'))
        # Repeat: still None, never an exception.
        self.assertIsNone(spawner.next_after((0.0, 0.0), 'right', [], []))


class TestFallbackOffset(SpawnTestBase):
    """Case 11: seeded grid-fallback scan offset (2026-09-26 Phase 5.3
    plan 5.3-02) — a forced fallback must not always land at the same
    most-negative-corner-first legal cell.

    Fixture: the +/-35 pocket lattice (_pocket_lattice, downscaled per
    the plan's cost note). Write-time probe (seed-independent, over the
    exact chain leg, fixed seeds): EXACTLY two legal fallback cells
    exist — grid index 892 = (24.5, 22.5) and grid index 924 =
    (24.5, 24.5) with nx = ny = 32 over the shrunk box [-31.5, 31.5]^2
    (GRID_STEP_A = 2.0); a continuous uniform draw landing legally in
    the pocket has near-zero measure, so a single next_after almost
    surely exhausts the MAX_DRAWS loop and forces the fallback. The
    head at the origin keeps the min_head_dist (11.025 A) and head
    clearance legs satisfied inside the pocket (pocket is 33.9 A away).
    """

    POCKET = (24.0, 24.0)

    def _drive(self, seed):
        """One forced-fallback spawn on the pocket lattice; returns the
        full (record, pid, centroid) result."""
        spawner = self.make_spawner(seed, box_min=(-35.0, -35.0),
                                    box_max=(35.0, 35.0))
        return spawner.next_after((0.0, 0.0), 'right',
                                  _pocket_lattice(), [])

    def _assert_in_pocket_with_clearance(self, result):
        record, _pid, centroid = result
        cx, cy = centroid
        self.assertLessEqual(_dist(cx, cy, self.POCKET[0], self.POCKET[1]),
                             6.0)
        for sym, ax, ay, az in self.atoms_by_id[record['id']]:
            tx, ty = ax + cx, ay + cy
            for _csym, qx, qy, _qz in _pocket_lattice():
                self.assertGreaterEqual(_dist(tx, ty, qx, qy), 3.0 - TOL)

    def test_fallback_lands_in_only_legal_pocket(self):
        # PIN (may pass under the pre-5.3-02 fallback either way — the
        # MODE of arrival, lucky draw vs fallback, is deliberately NOT
        # asserted): a saturated box with one legal pocket still spawns,
        # in the pocket, with the full chain-atom clearance intact.
        result = self._drive(4242)
        self.assertIsNotNone(result)
        self._assert_in_pocket_with_clearance(result)

    def test_fallback_start_varies_by_seed(self):
        # RED driver: under the pre-5.3-02 fallback (RNG-free x-major
        # scan, first legal wins) EVERY seed lands at grid index 892 =
        # (24.5, 22.5), so the two centroids are EQUAL and this
        # assertNotEqual fails. Seed pair verified at write time: BOTH
        # exhaust the 32-draw loop (no lucky uniform draw) — seed
        # 4242's seeded randrange start reaches legal cell 892 while
        # seed 163's start reaches legal cell 924 = (24.5, 24.5). (The
        # plan's draft pair 4242/777 happened to agree — both reach
        # 892 — so 163 was picked from the divergent pool and recorded
        # here; deterministic thereafter.)
        result_a = self._drive(4242)
        result_b = self._drive(163)
        self.assertIsNotNone(result_a)
        self.assertIsNotNone(result_b)
        self._assert_in_pocket_with_clearance(result_a)
        self._assert_in_pocket_with_clearance(result_b)
        self.assertNotEqual(result_a[2], result_b[2])

    def test_fallback_deterministic_per_seed(self):
        # PIN (GAME-07 on the fallback path): the same seed driven twice
        # through a forced fallback reproduces the same spawn
        # byte-identically — the seeded randrange start is consumed
        # deterministically from the same stream position.
        for seed in (4242, 163):
            first = self.shape(self._drive(seed))
            second = self.shape(self._drive(seed))
            self.assertEqual(first, second)


if __name__ == '__main__':
    unittest.main()
