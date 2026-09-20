"""spawn tests: deterministic seeded pickup-spawn policy pins (G3, 05-03).

Nine pin groups mirror the plan's behavior cases:

  1. Determinism  -- two same-seed spawners produce identical
     first()/next_after() sequences (positions + ids); a different seed
     yields different lateral draws; seed_from_setup is stable across two
     calls AND across processes (zlib.crc32, never hash()).
  2. Bounds       -- every returned centroid lies inside the wall-margined
     box (|x|,|y| <= 18 - 3.5 + 1e-9 on the medium preset).
  3. Head clear   -- first(head=(0,0), heading='right') lands >= 5.0 A from
     the head and generally ahead (x > 0 under the LOOKAHEAD_A = 8.0 rule).
  4. Chain atoms  -- with a dense chain-atom patch around the lookahead
     point, every atom of the returned (translated) molecule is >= 3.0 A
     from every chain atom.
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
from serpentrum import spawn  # noqa: E402  -- RED: module does not exist yet

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
        # Raw lateral draws (no clearance constraints beyond the always-
        # satisfied head/box legs): heading 'right' => centroid y IS the
        # quantized lateral draw. Two different seeds (almost surely)
        # produce different sequences.
        def laterals(seed):
            spawner = self.make_spawner(seed)
            values = [spawner.first((0.0, 0.0), 'right')[2][1]]
            for _ in range(5):
                result = spawner.next_after((0.0, 0.0), 'right', [], [])
                values.append(result[2][1])
            return values
        self.assertNotEqual(laterals(1234), laterals(9999))


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

    def test_first_is_ahead_and_clears_head(self):
        result = self.make_spawner(42).first((0.0, 0.0), 'right')
        cx, cy = result[2]
        self.assertGreaterEqual(_dist(cx, cy, 0.0, 0.0), 5.0 - TOL)
        # LOOKAHEAD_A = 8.0 along the heading -> the first spawn is ahead.
        self.assertGreater(cx, 0.0)

    def test_chain_atom_clearance(self):
        # Dense chain-atom patch around the lookahead point (8, 0).
        patch = [('C', 4.0 + i * 1.0, -4.0 + j * 1.0, 0.0)
                 for i in range(9) for j in range(9)]
        result = self.make_spawner(42).next_after((0.0, 0.0), 'right',
                                                  patch, [])
        self.assertIsNotNone(result)
        record, _pid, centroid = result
        cx, cy = centroid
        for sym, ax, ay, az in self.atoms_by_id[record['id']]:
            tx, ty = ax + cx, ay + cy
            for _csym, qx, qy, _qz in patch:
                self.assertGreaterEqual(_dist(tx, ty, qx, qy), 3.0 - TOL)

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


if __name__ == '__main__':
    unittest.main()
