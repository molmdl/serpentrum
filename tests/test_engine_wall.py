"""GameEngine Phase-9 wall tests (plan 09-02): static line obstacle.

The wall is the run's lethal third hazard: an optional STATIC line
obstacle on the movement plane, owned by the engine as plain state and
written by the controller (state-only, the attach_segment pattern).
Steering the HEAD into it is a GAME-05 crash — ('crashed', 'wall'),
finished=True / result='crashed', pending=[], the snake stays
complete -> spectra — the identical end-state code shape to the
boundary/body legs, so the GUI's generic crash->completion path needs
zero edits.

Pinned contracts (09-RESEARCH-engine-policy.md C1/C2):

  * STATE: engine.wall is None or ((ax, ay), (bx, by)) float
    2-tuples; set_wall stores the float-coerced endpoints and emits NO
    events (the controller writes, the engine never echoes);
    clear_wall() and reset() rebuild wall = None (fresh-state rebuild
    includes the wall); the additive wall=None keyword works on
    __init__ AND reset (test seam — production writes go through
    set_wall).
  * REFEREE SLOT: the wall check slots AFTER the boundary block and
    BEFORE the body block — moved -> boundary -> WALL -> body ->
    stacked -> won. Environment-first precedence (boundary over wall)
    and wall-over-body are pinned on same-tick double collisions; a
    crash tick suppresses capture (the boundary-tie precedent,
    test_engine_rules.py:589-608).
  * HEAD-ONLY BINDING: the wall binds the HEAD at straight-motion
    ticks only. Sweeps early-return and never move the head (the head
    is the rotation pivot — game_engine.py:636-637 early return,
    _advance_sweep never touches self.head), so a moved-tick check
    cannot miss a crossing; the chain may swing/clip through the wall
    freely (owner 2026-09-19b philosophy: a silly outcome is
    recoverable; head-only box binding precedent 2026-09-19d).
    wall=None produces byte-identical pre-Phase-9 event streams.
  * STRICT EDGE: the crash compare is STRICT < on the squared distance
    against WALL_COLLISION_RADIUS_A ** 2 via the degenerate-safe
    _point_segment_distance_sq — exactly-at-radius never crashes, and
    a degenerate (zero-length) wall behaves as a point obstacle
    (the helper's len_sq == 0 branch).

The boundary-over-body precedence pin (test_engine_rules.py:302-323)
stays green UNMODIFIED: the wall slots BETWEEN the two legs, never
before/after. All wall pins live in THIS file (house style — the
engine wall plan does not touch test_engine_rules.py).

Determinism: same conventions as tests/test_engine_rules.py — plain
engine state set directly, fixed constants (SPEED_A_PER_S = 3.0 A/s
with dt = 0.1 s -> exactly 0.3 A per tick; box fixture (-18, -18) to
(18, 18) -> margin walls at +-17.0), assertAlmostEqual with DELTA =
1e-9 for float positions. WALL_COLLISION_RADIUS_A is DERIVED FROM THE
MODULE in the exact-radius constructions (never hardcoded) so a future
wall-feel retune moves the test geometry with the constant — the value
itself ships at 2.0 A (equal to BODY_COLLISION_RADIUS_A but
deliberately an INDEPENDENT name, the BOUNDARY_MARGIN_A
one-name-per-margin discipline).

Discovery command (python3.6.9 — NOTE: `-t .` FAILS on python3.6 with a
non-package start dir; do not add it):

    python3.6 -m unittest discover -s tests -p "test_engine_wall.py" -v
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from serpentrum import game_engine  # noqa: E402
from serpentrum.game_engine import GameEngine  # noqa: E402

# Test-tuning constants (mirror tests/test_engine_rules.py).
DT = 0.1
STEP_A = game_engine.SPEED_A_PER_S * DT  # 0.3 A per tick at 3.0 A/s
DELTA = 1e-9

# Boundary-math fixture box (same values as test_engine_rules.py —
# arbitrary box for the engine's margin math, NOT a live preset read):
# (-18, -18) to (18, 18); margin walls (BOUNDARY_MARGIN_A = 1.0) sit
# at +-17.0.
BOX_MIN = (-18.0, -18.0)
BOX_MAX = (18.0, 18.0)
MARGIN_WALL = 17.0  # = 18.0 - BOUNDARY_MARGIN_A


def make_seg_at(x, y, molecule_id='mol'):
    """Build a FRESH segment record with the given 2D centroid.

    Identical seam to tests/test_engine_rules.py (the engine copies
    these on construction). One placeholder atom at the centroid — the
    wall/head checks use centroids and post-move positions only; the
    atom record pins that train-follow still translates atoms when a
    wall is present.
    """
    atoms = [('C', x, y, 0.0)]
    return {
        'molecule_id': molecule_id,
        'centroid': (x, y),
        'atoms': atoms,
        'atoms_n': len(atoms),
    }


def make_pickup(pid, x, y, atoms_n=1):
    """Build a FRESH pickup record (same seam as test_engine_rules.py)."""
    atoms = [('C', x, y, 0.0) for _ in range(atoms_n)]
    return {
        'id': pid,
        'centroid': (x, y),
        'atoms': atoms,
        'atoms_n': atoms_n,
    }


class TestWallState(unittest.TestCase):
    """Wall state contract: None default, float coercion, state-only
    writes, clear/reset rebuild, and the wall= test seam on BOTH
    __init__ and reset."""

    def test_fresh_engine_wall_none(self):
        # A fresh engine has NO wall; a bare reset() rebuilds wall=None
        # (the fresh-state rebuild includes the wall — C1/C4).
        engine = GameEngine()
        self.assertIsNone(engine.wall)
        engine.reset()
        self.assertIsNone(engine.wall)

    def test_set_wall_contract(self):
        # set_wall stores the float-coerced endpoint pair, returns
        # None, and emits NO events: a normal step with the head away
        # from the wall produces ONLY the usual ('moved', ...) — no
        # spawn/despawn/wall event of any kind (state-only write, the
        # attach_segment pattern: the controller writes, the engine
        # never echoes its own state changes as step() events).
        engine = GameEngine(head=(0.0, -10.0), heading='right')
        result = engine.set_wall(((0, 0), (3, 3)))
        self.assertIsNone(result)
        # Ints in, floats out — the stored pair is float-coerced.
        self.assertEqual(engine.wall, ((0.0, 0.0), (3.0, 3.0)))
        events = engine.step(DT)
        # USUAL events only: exactly one 'moved', nothing else.
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0][0], 'moved')
        self.assertAlmostEqual(events[0][1][0], 0.3, delta=DELTA)
        self.assertAlmostEqual(events[0][1][1], -10.0, delta=DELTA)
        for e in events:
            self.assertNotIn(e[0], ('crashed', 'stacked', 'won',
                                    'turning'))
        # A second set_wall REPLACES the first wall (one-live-wall
        # overwrite semantics — the spawn seam relies on it).
        engine.set_wall(((1, 1), (2, 2)))
        self.assertEqual(engine.wall, ((1.0, 1.0), (2.0, 2.0)))

    def test_clear_and_reset(self):
        # clear_wall() and a bare reset() both rebuild wall=None; the
        # additive wall= keyword carries an explicit wall through BOTH
        # signatures (__init__ AND reset — the test seam).
        engine = GameEngine()
        engine.set_wall(((1, 2), (3, 4)))
        self.assertIsNotNone(engine.wall)
        self.assertIsNone(engine.clear_wall())
        self.assertIsNone(engine.wall)
        # Set again, then reset: the fresh-state rebuild includes the
        # wall (it does not survive an epoch as stale environment).
        engine.set_wall(((5, 6), (7, 8)))
        self.assertIsNotNone(engine.wall)
        engine.reset()
        self.assertIsNone(engine.wall)
        # __init__ seam: the constructor keyword plants the wall.
        engine2 = GameEngine(wall=((0, 0), (1, 1)))
        self.assertEqual(engine2.wall, ((0.0, 0.0), (1.0, 1.0)))
        # reset seam: the same keyword re-seeds a new epoch's wall.
        engine2.reset(wall=((2, 2), (4, 4)))
        self.assertEqual(engine2.wall, ((2.0, 2.0), (4.0, 4.0)))
        # ...and the default (wall omitted) rebuilds an absent wall.
        engine2.reset()
        self.assertIsNone(engine2.wall)


class TestWallCrash(unittest.TestCase):
    """The crash leg: steering the HEAD into the wall ends the run via
    the GAME-05 generic completion path, with the boundary/body
    end-state shape."""

    def test_head_into_wall_crashes(self):
        # Box None (wall-only hazard), wall the vertical segment
        # ((3.0, -3.0), (3.0, 3.0)); head (0, 0) heading 'right' at
        # 0.3 A/tick. Wall halo = 2.0 A: post-move head positions
        #   tick 1: (0.3, 0.0) -> wall distance 2.7  (no crash)
        #   tick 2: (0.6, 0.0) -> wall distance 2.4  (no crash)
        #   tick 3: (0.9, 0.0) -> wall distance 2.099... (no crash)
        #   tick 4: (1.2, 0.0) -> wall distance 1.8 < 2.0 -> CRASH.
        # Two trailing segments pin "snake stays complete": the crash
        # neither truncates nor mutates the chain beyond the usual
        # train-follow translation (n=2 -> the body leg cannot fire;
        # limit = n - 1 - SEGMENT_SKIP_RECENT = -1).
        segs = [make_seg_at(-3.0, 1.0, 'seg0'), make_seg_at(-6.0, 1.0, 'seg1')]
        engine = GameEngine(head=(0.0, 0.0), heading='right',
                            segments=segs,
                            wall=((3.0, -3.0), (3.0, 3.0)))
        final_events = []
        for _ in range(40):
            final_events = engine.step(DT)
            if engine.finished:
                break
        self.assertTrue(engine.finished)
        # ('crashed', 'wall') with the identical end-state shape to
        # boundary/body: finished=True, result='crashed', pending=[].
        self.assertEqual(final_events[-1], ('crashed', 'wall'))
        self.assertEqual(engine.result, 'crashed')
        self.assertEqual(engine.pending, [])
        # The crashing tick is [('moved', (1.2, 0.0)), ('crashed',
        # 'wall')] — the move happened (train translated 4 ticks),
        # then the wall ended the run.
        self.assertEqual(len(final_events), 2)
        self.assertEqual(final_events[0][0], 'moved')
        self.assertAlmostEqual(final_events[0][1][0], 1.2, delta=DELTA)
        self.assertAlmostEqual(final_events[0][1][1], 0.0, delta=DELTA)
        # Snake stays complete: both segments still present, centroids
        # and atoms translated by exactly 4 ticks of +0.3 A
        # (train-follow carries on through the crashing tick).
        self.assertEqual(len(engine.segments), 2)
        self.assertAlmostEqual(engine.segments[0]['centroid'][0],
                                -1.8, delta=DELTA)
        self.assertAlmostEqual(engine.segments[1]['centroid'][0],
                                -4.8, delta=DELTA)
        atom = engine.segments[0]['atoms'][0]
        self.assertAlmostEqual(atom[1], -1.8, delta=DELTA)
        # A crashed engine is inert: a later step() returns [] and the
        # snake stays complete at its final pose.
        self.assertEqual(engine.step(DT), [])
        self.assertEqual(len(engine.segments), 2)
        self.assertAlmostEqual(engine.segments[0]['centroid'][0],
                                -1.8, delta=DELTA)

    def test_crash_stops_processing(self):
        # A pickup reachable on the SAME moved tick beyond the wall
        # never captures: the crash precedes capture (the boundary-tie
        # precedent, test_engine_rules.py:589-608 mirror). Pickup at
        # (4.0, 0.0) is beyond the wall at x=3.0:
        #   tick 3 head (0.9, 0.0): pickup distance 3.1 > 3.0 (no
        #   capture), wall distance 2.099... (no crash)
        #   tick 4 head (1.2, 0.0): pickup distance 2.8 <= 3.0 would
        #   capture — but the wall crash fires FIRST, so ('stacked',)
        #   never emits, the counters never move, and the pickup stays
        #   live.
        pickup = make_pickup('p1', 4.0, 0.0, atoms_n=1)
        engine = GameEngine(head=(0.0, 0.0), heading='right',
                            pickups=[pickup],
                            wall=((3.0, -3.0), (3.0, 3.0)))
        # Warm-up: ticks 1-3 stay alive with moved-only events.
        for _ in range(3):
            events = engine.step(DT)
            self.assertFalse(engine.finished)
            self.assertEqual([e[0] for e in events], ['moved'])
        # Tick 4: the crash tick. No capture rides along.
        events = engine.step(DT)
        self.assertEqual(len(events), 2)
        self.assertEqual(events[-1], ('crashed', 'wall'))
        for e in events:
            self.assertNotEqual(e[0], 'stacked')
        self.assertTrue(engine.finished)
        self.assertEqual(engine.molecules_stacked, 0)
        self.assertEqual(engine.pickups_remaining, 1)
        self.assertIn('p1', engine.live_pickup_ids)


class TestRefereeOrder(unittest.TestCase):
    """Referee slot pins: the wall leg slots BETWEEN boundary and body
    — new order moved -> boundary -> wall -> body -> stacked -> won.
    The boundary-over-body pin (test_engine_rules.py:302-323) stays
    green UNMODIFIED because the wall slots BETWEEN the pinned legs,
    never before/after."""

    def test_boundary_over_wall(self):
        # A moved position that hits the margin-adjusted box limit AND
        # sits inside the wall halo at once: the environment-first
        # order means 'boundary' wins (boundary, then wall).
        #   Box ((-18, -18), (18, 18)) -> margin walls at +-17.0.
        #   Wall: vertical ((17.1, 2.0), (17.1, -2.0)).
        #   Head (16.8, 0.0) heading right -> post-move (17.1, 0.0).
        #   Boundary: 17.1 >= 17.0 -> fires. Wall: head ON the wall
        #   segment (distance ~0 < 2.0) would ALSO fire — it must
        #   never run.
        engine = GameEngine(head=(16.8, 0.0), heading='right',
                            box_min=BOX_MIN, box_max=BOX_MAX,
                            wall=((17.1, 2.0), (17.1, -2.0)))
        events = engine.step(DT)
        crash_events = [e for e in events if e[0] == 'crashed']
        self.assertEqual(len(crash_events), 1)
        self.assertEqual(crash_events[0], ('crashed', 'boundary'))
        self.assertTrue(engine.finished)
        self.assertEqual(engine.result, 'crashed')

    def test_wall_over_body(self):
        # A wall lying ON a checked body-edge chord such that one moved
        # position triggers BOTH: 'wall' wins (wall, then body).
        #   Wall: vertical ((0.3, 2.0), (0.3, -2.0)).
        #   Edge 0 (checked; n=4 -> limit=1): c0=(0.3, 2.0),
        #   c1=(0.3, -2.0) — the SAME line. Head (0, 0) heading right
        #   -> post-move (0.3, 0.0) sits ~ON both. The body crash
        #   (distance ~0 < 2.0) would fire if reached — it never runs.
        segs = [make_seg_at(0.3, 2.0, 'c0'), make_seg_at(0.3, -2.0, 'c1'),
                make_seg_at(100.0, 100.0, 'c2'),
                make_seg_at(200.0, 200.0, 'c3')]
        engine = GameEngine(head=(0.0, 0.0), heading='right',
                            segments=segs,
                            wall=((0.3, 2.0), (0.3, -2.0)))
        events = engine.step(DT)
        crash_events = [e for e in events if e[0] == 'crashed']
        self.assertEqual(len(crash_events), 1)
        self.assertEqual(crash_events[0], ('crashed', 'wall'))
        self.assertTrue(engine.finished)
        self.assertEqual(engine.result, 'crashed')

    def test_order_is_moved_boundary_wall_body_stacked_won(self):
        """Authoritative six-leg order pin: moved -> boundary -> wall
        -> body -> stacked -> won. Assembled from the observable order
        legs: (1) the move precedes any crash; (2) boundary-over-wall
        on a same-tick double collision; (3) wall-over-body on a
        same-tick double collision; (4) a wall crash suppresses
        capture (crash stops processing — the boundary-tie precedent);
        (5) stacked precedes won with a wall present and never fires on
        a crash tick (walls do not touch the capture/win machinery).
        Boundary-over-body stays pinned separately in
        test_engine_rules.py (unmodified)."""
        # (1) + (2): moved first, then boundary over wall.
        engine = GameEngine(head=(16.8, 0.0), heading='right',
                            box_min=BOX_MIN, box_max=BOX_MAX,
                            wall=((17.1, 2.0), (17.1, -2.0)))
        events = engine.step(DT)
        self.assertEqual(events[0][0], 'moved')
        self.assertEqual(events[-1], ('crashed', 'boundary'))
        # (3): wall over body (fresh fixtures — same-tick double).
        segs = [make_seg_at(0.3, 2.0, 'c0'), make_seg_at(0.3, -2.0, 'c1'),
                make_seg_at(100.0, 100.0, 'c2'),
                make_seg_at(200.0, 200.0, 'c3')]
        engine = GameEngine(head=(0.0, 0.0), heading='right',
                            segments=segs,
                            wall=((0.3, 2.0), (0.3, -2.0)))
        events = engine.step(DT)
        self.assertEqual(events[0][0], 'moved')
        self.assertEqual(events[-1], ('crashed', 'wall'))
        # (4): the wall crash tick suppresses capture (no 'stacked'
        # even though the pickup at (4.0, 0.0) is within radius).
        pickup = make_pickup('p1', 4.0, 0.0, atoms_n=1)
        engine = GameEngine(head=(0.0, 0.0), heading='right',
                            pickups=[pickup],
                            wall=((3.0, -3.0), (3.0, 3.0)))
        all_events = []
        for _ in range(4):
            all_events.extend(engine.step(DT))
            if engine.finished:
                break
        names = [e[0] for e in all_events]
        crashed_events = [e for e in all_events if e[0] == 'crashed']
        self.assertEqual(crashed_events, [('crashed', 'wall')])
        self.assertNotIn('stacked', names)
        self.assertEqual(engine.molecules_stacked, 0)
        # (5): with the wall clear of the path, a capture tick emits
        # moved -> stacked -> won — the wall never interferes with the
        # capture/win machinery (result='won', not 'crashed').
        pickup2 = make_pickup('p2', 2.5, 0.0, atoms_n=1)
        engine = GameEngine(head=(0.0, 0.0), heading='right',
                            pickups=[pickup2], cap=1,
                            wall=((0.3, 3.0), (5.0, 3.0)))
        events = engine.step(DT)
        self.assertEqual([e[0] for e in events],
                         ['moved', 'stacked', 'won'])
        self.assertTrue(engine.finished)
        self.assertEqual(engine.result, 'won')


class TestStrictEdge(unittest.TestCase):
    """Strict-compare edges: exactly-at-radius NEVER crashes (STRICT <
    on the squared compare — mirrors test_engine_rules.py:272-285 for
    the body), and a degenerate zero-length wall behaves as a point
    obstacle via the helper's len_sq == 0 branch."""

    def test_exactly_at_radius_no_crash(self):
        # Head (1.7, 0.0) heading right -> post-move (2.0, 0.0)
        # EXACTLY (1.7 + 0.3 = 2.0 in this float environment — the same
        # arithmetic the pinned body edge test uses). The wall sits
        # EXACTLY WALL_COLLISION_RADIUS_A past the post-move head:
        # vertical at x = 2.0 + 2.0 = 4.0 (geometry DERIVED from the
        # module constant so a wall-feel retune moves the test with
        # the value). Nearest wall point (4.0, 0.0): distance 2.0,
        # squared 4.0. STRICT <: 4.0 < 4.0 is False -> NO crash; the
        # engine continues.
        post_move_x = 1.7 + STEP_A  # exactly 2.0
        wall_x = post_move_x + game_engine.WALL_COLLISION_RADIUS_A
        engine = GameEngine(head=(1.7, 0.0), heading='right',
                            wall=((wall_x, -3.0), (wall_x, 3.0)))
        events = engine.step(DT)
        self.assertAlmostEqual(engine.head[0], 2.0, delta=DELTA)
        self.assertFalse(engine.finished)
        self.assertEqual([e[0] for e in events], ['moved'])
        # The pass was the STRICTNESS, not a missing check: the very
        # next tick lands at 2.3 -> wall distance 1.7 < 2.0 -> crash.
        events = engine.step(DT)
        self.assertEqual(events[-1], ('crashed', 'wall'))
        self.assertTrue(engine.finished)

    def test_degenerate_wall_is_point_obstacle(self):
        # A degenerate wall ((px, py), (px, py)) is a POINT obstacle
        # (the helper's len_sq == 0 branch returns the point distance).
        # Head (1.0, 1.7) heading up: tick 1 -> (1.0, 2.0) EXACTLY
        # (1.7 + 0.3 = 2.0), which sits EXACTLY
        # WALL_COLLISION_RADIUS_A below the point (1.0, 4.0) (derived
        # from the constant) -> at radius, STRICT < -> NO crash; tick
        # 2 -> (1.0, 2.3): distance 1.7 < 2.0 -> crash.
        point_y = 1.7 + STEP_A + game_engine.WALL_COLLISION_RADIUS_A
        engine = GameEngine(head=(1.0, 1.7), heading='up',
                            wall=((1.0, point_y), (1.0, point_y)))
        events = engine.step(DT)
        self.assertAlmostEqual(engine.head[1], 2.0, delta=DELTA)
        self.assertFalse(engine.finished)
        self.assertEqual([e[0] for e in events], ['moved'])
        events = engine.step(DT)
        self.assertEqual(events[-1], ('crashed', 'wall'))
        self.assertTrue(engine.finished)
        self.assertEqual(engine.result, 'crashed')


class TestHeadOnlyScope(unittest.TestCase):
    """Head-only scope: the wall binds the HEAD ONLY — the chain may
    overlap/clip through it on every tick (never wall-checked), sweeps
    never check it (the head is the pivot and never moves during a
    sweep — early-return proof), and wall=None is byte-identical to the
    pre-Phase-9 behavior."""

    def test_chain_through_wall_never_crashes(self):
        # A chain whose segments sit exactly ON the wall line; the head
        # moves parallel far away. With train-follow the chain rides
        # along the wall line forever (x stays 0 while the wall spans
        # y in [-2, 2] and then past its ends) — if the chain were ever
        # wall-checked, the run would crash on tick 1. It never does:
        # 'moved' events only, for the whole drive.
        segs = [make_seg_at(0.0, -1.0, 'c0'), make_seg_at(0.0, 0.5, 'c1'),
                make_seg_at(0.0, 1.5, 'c2'), make_seg_at(0.0, 2.5, 'c3')]
        engine = GameEngine(head=(10.0, 5.0), heading='up',
                            segments=segs,
                            wall=((0.0, -2.0), (0.0, 2.0)))
        for k in range(1, 21):
            events = engine.step(DT)
            self.assertFalse(engine.finished,
                             'crashed at step %d' % k)
            self.assertEqual([e[0] for e in events], ['moved'])
        # n=4 -> only edge 0 is body-checked ((c0, c1) near the wall
        # line) and the head never approaches it; the chain overlapping
        # the wall provably never fires.
        self.assertIsNone(engine.result)

    def test_sweep_through_wall_no_crash(self):
        # The head SITS 1.0 A INSIDE the 2.0 A wall halo; straight
        # motion would crash on the very next tick. Requesting an
        # 'up' turn instead: the whole 6-tick sweep rotates the chain
        # while the head stays the FIXED pivot — every sweep tick
        # emits ONLY ('turning', ...) with NO crash and NO ('moved',)
        # (the early-return proof: the wall check never runs on sweep
        # ticks). Only AFTER the sweep completes does one straight
        # step meet the wall — the moved-tick gate.
        engine = GameEngine(head=(0.0, 0.0), heading='right',
                            wall=((1.0, -3.0), (1.0, 3.0)))
        self.assertTrue(engine.request_direction('up'))
        for k in range(1, game_engine.TURN_TICKS + 1):
            events = engine.step(DT)
            # Sweep tick: exactly one 'turning' event — no 'moved', no
            # crash, despite the head sitting inside the wall halo.
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0][0], 'turning')
            self.assertAlmostEqual(events[0][1],
                                   k / float(game_engine.TURN_TICKS),
                                   delta=DELTA)
            self.assertFalse(engine.finished)
            # The head is the pivot: it does not move during the sweep.
            self.assertEqual(engine.head, (0.0, 0.0))
        self.assertIsNone(engine.sweeping)
        self.assertEqual(engine.heading, game_engine.DIRS['up'])
        # Post-sweep straight tick: heading 'up' now moves the head to
        # (0.0, 0.3) — 1.0 A from the wall line at x=1.0 -> the crash
        # fires NOW (the moved-tick gate, nothing earlier).
        events = engine.step(DT)
        self.assertEqual(events[0][0], 'moved')
        self.assertEqual(events[-1], ('crashed', 'wall'))
        self.assertTrue(engine.finished)
        self.assertEqual(engine.result, 'crashed')

    def test_wall_none_event_parity(self):
        # wall=None must produce BYTE-IDENTICAL pre-Phase-9 event
        # streams. A short scripted capture drive (capture, buffered
        # turn, full sweep, straight ticks) runs twice on identically
        # seeded engines — one without any wall argument, one with the
        # explicit wall=None kwarg — and the concatenated event lists
        # compare equal EXACTLY (float-for-float: any wall-leg float
        # arithmetic leaking into the stream would break this).
        def drive(engine):
            collected = []
            collected.extend(engine.step(DT))  # capture tick
            engine.request_direction('up')
            for _ in range(game_engine.TURN_TICKS):
                collected.extend(engine.step(DT))  # sweep ticks
            collected.extend(engine.step(DT))
            collected.extend(engine.step(DT))  # straight ticks
            return collected

        engine_a = GameEngine(head=(0.0, 0.0), heading='right',
                              pickups=[make_pickup('p1', 2.5, 0.0,
                                                   atoms_n=2)])
        engine_b = GameEngine(head=(0.0, 0.0), heading='right',
                              pickups=[make_pickup('p1', 2.5, 0.0,
                                                   atoms_n=2)],
                              wall=None)
        self.assertIsNone(engine_b.wall)
        events_a = drive(engine_a)
        events_b = drive(engine_b)
        # Sanity: the drive really exercised capture + sweep + moves.
        names_a = [e[0] for e in events_a]
        self.assertIn('stacked', names_a)
        self.assertEqual(names_a.count('turning'), game_engine.TURN_TICKS)
        self.assertEqual(names_a.count('moved'), 3)
        # The parity pin: byte-identical event streams.
        self.assertEqual(events_a, events_b)


class TestLifecycleInvariants(unittest.TestCase):
    """Lifecycle invariants: paused engines are inert regardless of
    wall placement; the win/reject machinery never interacts with the
    wall; and the wall never moves with the train (environment, like
    the box)."""

    def test_paused_engine_inert(self):
        # pause() freezes the engine: step(dt) returns [] regardless
        # of wall placement — even a wall the head would crash into on
        # the very next tick (the head never moves, so the wall leg
        # never runs). resume() restores live events.
        engine = GameEngine(head=(0.0, 0.0), heading='right',
                            wall=((0.3, -3.0), (0.3, 3.0)))
        engine.pause()
        for _ in range(3):
            self.assertEqual(engine.step(DT), [])
        self.assertFalse(engine.finished)
        self.assertEqual(engine.head, (0.0, 0.0))
        engine.resume()
        events = engine.step(DT)
        self.assertNotEqual(events, [])
        # First live tick lands the head (0.3, 0.0) ON the wall line.
        self.assertEqual(events[-1], ('crashed', 'wall'))
        self.assertTrue(engine.finished)

    def test_wall_never_flutter_with_win_or_reject(self):
        # A run that WINS with a wall standing near the capture: the
        # 'won' emission path is unchanged (['moved', 'stacked',
        # 'won'], result='won'), the wall state does not flutter with
        # the win, and the controller's reject_pickup on that pickup
        # still returns the canonical ('refused', id, reason) tuple
        # with NO wall interaction — the G2 won-rollback un-finish
        # behaves exactly as without a wall (companion to
        # test_engine_win_desync.py).
        pickup = make_pickup('p1', 2.5, 0.0, atoms_n=1)
        wall = ((2.5, 6.0), (2.5, 3.0))  # vertical stub 3.0 A ABOVE
        # the pickup centroid: near the mol but clear of the head's
        # y=0 lane (lane-to-wall >= 3.0 A > halo 2.0 A).
        engine = GameEngine(head=(0.0, 0.0), heading='right',
                            pickups=[pickup], cap=1, wall=wall)
        events = engine.step(DT)
        self.assertEqual([e[0] for e in events],
                         ['moved', 'stacked', 'won'])
        self.assertTrue(engine.finished)
        self.assertEqual(engine.result, 'won')
        self.assertEqual(engine.molecules_stacked, 1)
        self.assertEqual(engine.wall, ((2.5, 6.0), (2.5, 3.0)))
        # Controller-side reject near the wall: canonical tuple, the
        # G2 un-finish fires (sub-cap rollback un-finishes the run),
        # and the wall is untouched by any of it.
        result = engine.reject_pickup('p1', 'clash')
        self.assertEqual(result, ('refused', 'p1', 'clash'))
        self.assertEqual(engine.molecules_stacked, 0)
        self.assertIn('p1', engine.live_pickup_ids)
        self.assertFalse(engine.finished)
        self.assertIsNone(engine.result)
        self.assertEqual(engine.wall, ((2.5, 6.0), (2.5, 3.0)))

    def test_wall_immovable(self):
        # The wall is ENVIRONMENT, like the box: it never translates
        # with the train and never rotates with sweeps. Drive moved
        # ticks AND a full sweep; the stored tuple stays byte-identical
        # after every tick while the head provably advances.
        wall = ((5.0, -2.0), (8.0, 2.0))
        engine = GameEngine(head=(0.0, 0.0), heading='right', wall=wall)
        self.assertTrue(engine.request_direction('up'))
        for _ in range(game_engine.TURN_TICKS + 4):
            engine.step(DT)
            self.assertEqual(engine.wall, ((5.0, -2.0), (8.0, 2.0)))
        # The drive really advanced: 6 sweep ticks (head fixed) then 4
        # straight ticks moving the head up to y = 1.2.
        self.assertEqual(engine.heading, game_engine.DIRS['up'])
        self.assertAlmostEqual(engine.head[0], 0.0, delta=DELTA)
        self.assertAlmostEqual(engine.head[1], 1.2, delta=DELTA)


class TestMultipleWalls(unittest.TestCase):
    """Phase 9.1 (plan 9.1-03): the engine wall slot becomes an
    ACCUMULATING set under the COMPAT route.

    The engine gains engine.walls (a list of endpoint pairs) with
    add_wall (append, state-only, float-coerced, no events) and
    clear_walls semantics; engine.wall becomes a READ-ONLY newest-wall
    accessor (walls[-1] if walls else None). set_wall KEEPS its
    Phase-9 clear-and-plant-one replace semantics (the legacy
    single-wall seam), so every pin in the six classes above stays
    TRUE and byte-unmodified.

    The referee SLOT (moved -> boundary -> wall -> body -> stacked ->
    won) and the ('crashed', 'wall') payload are IDENTICAL: the collision
    leg becomes a first-hit loop over the accumulated set. Every
    accumulated wall is lethal; an EARLY wall stays lethal while later
    walls are present; boundary still precedes wall; wall still
    precedes body; an empty set (walls == []) is byte-identical to the
    shipped wall=None engine.
    """

    def test_add_wall_accumulates_and_accessor_returns_newest(self):
        # add_wall appends a fresh float-coerced pair; returns None;
        # emits NO events (state-only, the attach_segment pattern —
        # mirroring TestWallState.test_set_wall_contract). The wall
        # accessor returns the NEWEST wall (walls[-1]).
        engine = GameEngine(head=(0.0, -10.0), heading='right')
        self.assertIsNone(engine.add_wall(((0, 0), (3, 3))))
        self.assertIsNone(engine.add_wall(((1, 1), (4, 4))))
        self.assertIsNone(engine.add_wall(((2, 2), (5, 5))))
        # Ints in, floats out — every stored pair is float-coerced.
        self.assertEqual(engine.walls,
                         [((0.0, 0.0), (3.0, 3.0)),
                          ((1.0, 1.0), (4.0, 4.0)),
                          ((2.0, 2.0), (5.0, 5.0))])
        # The accessor is the NEWEST accumulated wall.
        self.assertEqual(engine.wall, ((2.0, 2.0), (5.0, 5.0)))
        # State-only: a normal step with the head away from every wall
        # produces ONLY the usual ('moved', ...) — no echo events.
        events = engine.step(DT)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0][0], 'moved')
        self.assertAlmostEqual(events[0][1][0], 0.3, delta=DELTA)
        self.assertAlmostEqual(events[0][1][1], -10.0, delta=DELTA)

    def test_set_wall_still_clears_and_plants_one(self):
        # set_wall KEEPS the Phase-9 clear-and-plant-one replace
        # semantics: after accumulating two walls, set_wall(new) leaves
        # EXACTLY ONE wall (the new one). This is the replacement pin
        # restated for the list state.
        engine = GameEngine()
        engine.add_wall(((0, 0), (3, 3)))
        engine.add_wall(((1, 1), (4, 4)))
        self.assertEqual(len(engine.walls), 2)
        engine.set_wall(((5, 5), (8, 8)))
        self.assertEqual(len(engine.walls), 1)
        self.assertEqual(engine.walls, [((5.0, 5.0), (8.0, 8.0))])
        self.assertEqual(engine.wall, ((5.0, 5.0), (8.0, 8.0)))

    def test_every_accumulated_wall_lethal(self):
        # Every accumulated wall is lethal at the same referee slot:
        # three engines each accumulate 3 walls (one crossing the y=0
        # lane, two far bystanders) and drive the head into the crossing
        # one. Each run ends with exactly ('crashed', 'wall') and the
        # boundary/body end-state shape.
        for target_x in (3.0, 5.0, 7.0):
            engine = GameEngine(head=(0.0, 0.0), heading='right')
            engine.add_wall(((0.0, 10.0), (3.0, 10.0)))       # far (up)
            engine.add_wall(((target_x, -3.0), (target_x, 3.0)))  # lane
            engine.add_wall(((0.0, -10.0), (3.0, -10.0)))     # far (down)
            final_events = []
            for _ in range(80):
                final_events = engine.step(DT)
                if engine.finished:
                    break
            self.assertTrue(engine.finished)
            self.assertEqual(final_events[-1], ('crashed', 'wall'))
            self.assertEqual(engine.result, 'crashed')
            self.assertEqual(engine.pending, [])

    def test_early_wall_crash_with_later_walls_present(self):
        # Persistence lethality (the s11 engine-side mini): wall #1
        # crosses the +x path; wall #2 is far away. Driving right from
        # (0, 0) crashes on wall #1 even though a later wall is present,
        # and BOTH walls remain in the accumulated set afterward.
        engine = GameEngine(head=(0.0, 0.0), heading='right')
        engine.add_wall(((3.0, -3.0), (3.0, 3.0)))       # wall #1 (path)
        engine.add_wall(((40.0, 40.0), (45.0, 45.0)))    # wall #2 (far)
        final_events = []
        for _ in range(40):
            final_events = engine.step(DT)
            if engine.finished:
                break
        self.assertTrue(engine.finished)
        self.assertEqual(final_events[-1], ('crashed', 'wall'))
        self.assertEqual(engine.result, 'crashed')
        # The accumulated set is intact — neither wall was consumed.
        self.assertEqual(len(engine.walls), 2)
        self.assertEqual(engine.walls[0], ((3.0, -3.0), (3.0, 3.0)))
        self.assertEqual(engine.walls[1], ((40.0, 40.0), (45.0, 45.0)))

    def test_boundary_precedes_multi_wall_crash(self):
        # Environment-first precedence holds with a multi-wall set: a
        # moved position that hits the margin box limit AND sits inside
        # a wall halo emits 'boundary' (boundary, then wall).
        #   Box ((-18, -18), (18, 18)) -> margin walls at +-17.0.
        #   Two vertical walls at x = 17.1 and 17.2.
        #   Head (16.8, 0.0) right -> post-move (17.1, 0.0): boundary
        #   fires first; the walls would also fire but never run.
        engine = GameEngine(head=(16.8, 0.0), heading='right',
                            box_min=BOX_MIN, box_max=BOX_MAX)
        engine.add_wall(((17.1, 2.0), (17.1, -2.0)))
        engine.add_wall(((17.2, 2.0), (17.2, -2.0)))
        events = engine.step(DT)
        crash_events = [e for e in events if e[0] == 'crashed']
        self.assertEqual(crash_events, [('crashed', 'boundary')])
        self.assertTrue(engine.finished)
        self.assertEqual(engine.result, 'crashed')

    def test_multi_wall_precedes_body(self):
        # Wall-over-body precedence holds with a multi-wall set: two
        # walls lie ON a checked body-edge chord so one moved position
        # triggers both hazards; 'wall' wins (wall, then body).
        segs = [make_seg_at(0.3, 2.0, 'c0'), make_seg_at(0.3, -2.0, 'c1'),
                make_seg_at(100.0, 100.0, 'c2'),
                make_seg_at(200.0, 200.0, 'c3')]
        engine = GameEngine(head=(0.0, 0.0), heading='right',
                            segments=segs)
        engine.add_wall(((0.3, 2.0), (0.3, -2.0)))
        engine.add_wall(((0.35, 2.0), (0.35, -2.0)))
        events = engine.step(DT)
        crash_events = [e for e in events if e[0] == 'crashed']
        self.assertEqual(crash_events, [('crashed', 'wall')])
        self.assertTrue(engine.finished)
        self.assertEqual(engine.result, 'crashed')

    def test_no_walls_parity_with_legacy(self):
        # An empty accumulated set (walls == []) is byte-identical to
        # the shipped wall=None engine: a scripted capture + sweep +
        # straight drive produces the SAME event stream on identically
        # seeded engines (one bare, one with the explicit wall=None
        # kwarg). Any wall-leg float arithmetic leaking into the stream
        # would break this.
        def drive(engine):
            collected = []
            collected.extend(engine.step(DT))  # capture tick
            engine.request_direction('up')
            for _ in range(game_engine.TURN_TICKS):
                collected.extend(engine.step(DT))  # sweep ticks
            collected.extend(engine.step(DT))
            collected.extend(engine.step(DT))  # straight ticks
            return collected

        engine_a = GameEngine(head=(0.0, 0.0), heading='right',
                              pickups=[make_pickup('p1', 2.5, 0.0,
                                                   atoms_n=2)])
        engine_b = GameEngine(head=(0.0, 0.0), heading='right',
                              pickups=[make_pickup('p1', 2.5, 0.0,
                                                   atoms_n=2)],
                              wall=None)
        self.assertEqual(engine_a.walls, [])
        self.assertEqual(engine_b.walls, [])
        self.assertIsNone(engine_b.wall)
        events_a = drive(engine_a)
        events_b = drive(engine_b)
        # Sanity: the drive really exercised capture + sweep + moves.
        names_a = [e[0] for e in events_a]
        self.assertIn('stacked', names_a)
        self.assertEqual(names_a.count('turning'), game_engine.TURN_TICKS)
        self.assertEqual(names_a.count('moved'), 3)
        # The parity pin: byte-identical event streams.
        self.assertEqual(events_a, events_b)

    def test_reset_and_clear_remove_all(self):
        # reset() and clear_wall() both empty the WHOLE accumulated set
        # (no walls survive an epoch); the wall= __init__/reset seam
        # still plants a SINGLE-wall list; and the wall accessor is
        # read-only (no setter — assignment raises AttributeError).
        engine = GameEngine()
        for i in range(4):
            engine.add_wall(((i, 0), (i, 1)))
        self.assertEqual(len(engine.walls), 4)
        engine.reset()
        self.assertEqual(engine.walls, [])
        self.assertIsNone(engine.wall)
        for i in range(4):
            engine.add_wall(((i, 0), (i, 1)))
        self.assertEqual(len(engine.walls), 4)
        engine.clear_wall()
        self.assertEqual(engine.walls, [])
        self.assertIsNone(engine.wall)
        # The wall= seam plants a single-element list.
        engine.reset(wall=((2, 2), (4, 4)))
        self.assertEqual(engine.walls, [((2.0, 2.0), (4.0, 4.0))])
        self.assertEqual(engine.wall, ((2.0, 2.0), (4.0, 4.0)))
        # Read-only accessor: NO setter exists.
        with self.assertRaises(AttributeError):
            engine.wall = ((0, 0), (1, 1))

    def test_paused_inert_with_walls(self):
        # A paused engine is inert regardless of accumulated walls:
        # step() returns [] and the head never moves, so the wall leg
        # never runs even with a wall ON the head's next-step path.
        engine = GameEngine(head=(0.0, 0.0), heading='right')
        engine.add_wall(((0.3, -3.0), (0.3, 3.0)))
        engine.add_wall(((0.4, -3.0), (0.4, 3.0)))
        engine.add_wall(((0.5, -3.0), (0.5, 3.0)))
        engine.pause()
        for _ in range(3):
            self.assertEqual(engine.step(DT), [])
        self.assertFalse(engine.finished)
        self.assertEqual(engine.head, (0.0, 0.0))

    def test_capture_radius_exceeds_wall_halo(self):
        # Derived one-liner (the 5.1-06 derivation habit): a mol's
        # capturable zone (PICKUP_RADIUS_A, 3.0, inclusive) is STRICTLY
        # larger than a wall's lethal halo (WALL_COLLISION_RADIUS_A,
        # 2.0, strict). An old accumulated wall's halo can therefore
        # never swallow a nearby mol's capture zone — a mol spawning
        # near an existing wall remains capturable by construction (the
        # 9.1 fairness surface).
        self.assertGreater(game_engine.PICKUP_RADIUS_A,
                           game_engine.WALL_COLLISION_RADIUS_A)


if __name__ == '__main__':
    unittest.main()
