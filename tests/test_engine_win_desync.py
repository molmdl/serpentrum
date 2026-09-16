"""GameEngine won-rollback un-finish tests (plan 05-04, gap G2).

Gap G2 (05-RESEARCH-core-integration.md): 'won' fires in the SAME tick
as the cap-reaching 'stacked', BEFORE the controller (GUI) runs the
clash gate. Rejecting that capture via reject_pickup rolls the counters
back but used to leave finished=True / result='won' — a frozen sub-cap
run (GAME-06 vs STACK-05 desync).

The additive fix pinned here: reject_pickup clears finished/result when
it rolls a WON run back below cap (molecules_stacked < cap after the
rollback). Crash results are NEVER un-finished. The pinned step() event
order moved->boundary->body->stacked->budget->won is untouched; this
file adds NEW pins only, and test_engine_rules.py must stay green
unmodified.

Guard documentation (why reject re-checks molecules_stacked < cap):
'won' fires on the exact tick molecules_stacked reaches cap, so at the
moment a controller rejects the cap-reaching capture the counter is
exactly cap (or more, for a hand-forced over-cap state). A single
reject rolls back exactly one molecule, so through the public API the
post-rollback counter ALWAYS satisfies molecules_stacked < cap — the
recheck is reachable only via hand-forced state (cap=0, or
molecules_stacked > cap + 1). It exists as defensive semantics: a run
whose post-rollback counter still satisfies the win condition NEVER
un-finishes.

Determinism: same conventions as tests/test_engine_rules.py — plain
engine state, fixed constants (0.3 A per 0.1 s tick at SPEED 3.0),
assertAlmostEqual where floats are compared.
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

# Medium box preset: (-18, -18) to (18, 18); margin walls at +-17.0.
BOX_MIN = (-18.0, -18.0)
BOX_MAX = (18.0, 18.0)


def make_pickup(pid, x, y, atoms_n=1):
    """Build a FRESH pickup record (same seam as test_engine_rules)."""
    atoms = [('C', x, y, 0.0) for _ in range(atoms_n)]
    return {
        'id': pid,
        'centroid': (x, y),
        'atoms': atoms,
        'atoms_n': atoms_n,
    }


class TestWonRollbackUnfinish(unittest.TestCase):
    """Rejecting the cap-reaching capture un-finishes a won run.

    The un-finish happens ONLY when the rollback takes the counter back
    below cap (see module docstring: a single rollback via the public
    API always does — the guard is defensive semantics for hand-forced
    states).
    """

    def test_cap1_reject_unfinishes_run(self):
        # cap=1, single pickup on the path. Head (0,0) heading right;
        # pickup at (2.5, 0.0). Tick 1: head -> (0.3, 0.0), distance
        # 2.2 <= 3.0 (PICKUP_RADIUS_A, inclusive) -> capture; stacked=1
        # >= cap=1 -> ('won',) on the SAME tick's event list.
        pickup = make_pickup('p1', 2.5, 0.0, atoms_n=1)
        engine = GameEngine(head=(0.0, 0.0), heading='right',
                            pickups=[pickup], cap=1)
        events = engine.step(DT)
        # Both fire in the same event list; order ... stacked -> won
        # (pinned referee order; identical before and after the fix).
        names = [e[0] for e in events]
        self.assertEqual(names, ['moved', 'stacked', 'won'])
        rec = events[1][1]
        self.assertEqual(rec['id'], 'p1')
        self.assertTrue(engine.finished)
        self.assertEqual(engine.result, 'won')
        self.assertEqual(engine.molecules_stacked, 1)
        self.assertNotIn('p1', engine.live_pickup_ids)
        # The controller's clash gate now refuses the capture.
        result = engine.reject_pickup('p1', 'clash')
        self.assertEqual(result, ('refused', 'p1', 'clash'))
        # Counters roll back per the existing pinned contract...
        self.assertEqual(engine.molecules_stacked, 0)
        self.assertEqual(engine.atoms_total, 0)
        self.assertEqual(engine.pickups_remaining, 1)
        self.assertIn('p1', engine.live_pickup_ids)
        # ...AND the run un-finishes (the G2 fix): the player keeps
        # playing instead of being frozen in a sub-cap 'won' state.
        # (Pre-fix these two assertions FAIL: finished stays True.)
        self.assertFalse(engine.finished)
        self.assertIsNone(engine.result)

    def test_cap2_reject_cap_reaching_capture_unfinishes(self):
        # cap=2, two pickups along the heading. Captures land on
        # separate ticks (engine allows at most one per tick).
        #   Tick 1: head 0.3; p1 dist 2.2 -> captured (stacked=1, no win).
        #   Tick 6: head 1.8; p2 dist 3.2 -> not yet.
        #   Tick 7: head 2.1; p2 dist 2.9 -> captured (stacked=2 -> won).
        p1 = make_pickup('p1', 2.5, 0.0, atoms_n=1)
        p2 = make_pickup('p2', 5.0, 0.0, atoms_n=1)
        engine = GameEngine(head=(0.0, 0.0), heading='right',
                            pickups=[p1, p2], cap=2)
        engine.step(DT)  # captures p1
        self.assertFalse(engine.finished)
        for _ in range(6):
            events = engine.step(DT)
        self.assertTrue(engine.finished)
        self.assertEqual(engine.result, 'won')
        self.assertEqual(engine.molecules_stacked, 2)
        # Reject the cap-reaching capture (p2): rollback 2 -> 1 < 2.
        result = engine.reject_pickup('p2', 'clash')
        self.assertEqual(result, ('refused', 'p2', 'clash'))
        self.assertEqual(engine.molecules_stacked, 1)
        self.assertIn('p2', engine.live_pickup_ids)
        self.assertNotIn('p1', engine.live_pickup_ids)  # p1 stays claimed
        self.assertFalse(engine.finished)
        self.assertIsNone(engine.result)

    def test_cap2_reject_earlier_capture_also_unfinishes(self):
        # Same won run; the controller refuses the EARLIER capture
        # instead. The rollback still takes 2 -> 1 < cap, so the run
        # un-finishes either way (the un-finish keys on the counter,
        # not on which pickup reached the cap).
        p1 = make_pickup('p1', 2.5, 0.0, atoms_n=1)
        p2 = make_pickup('p2', 5.0, 0.0, atoms_n=1)
        engine = GameEngine(head=(0.0, 0.0), heading='right',
                            pickups=[p1, p2], cap=2)
        engine.step(DT)  # captures p1
        for _ in range(6):
            engine.step(DT)  # tick 7 captures p2 -> won
        self.assertTrue(engine.finished)
        result = engine.reject_pickup('p1', 'clash')
        self.assertEqual(result, ('refused', 'p1', 'clash'))
        self.assertEqual(engine.molecules_stacked, 1)
        self.assertIn('p1', engine.live_pickup_ids)
        self.assertNotIn('p2', engine.live_pickup_ids)  # p2 stays claimed
        self.assertFalse(engine.finished)
        self.assertIsNone(engine.result)


class TestCrashStaysFinished(unittest.TestCase):
    """reject_pickup NEVER un-finishes a crashed run.

    Only 'won' results have sub-cap rollback semantics; a crash is
    terminal regardless of what the counters do afterwards.
    """

    def test_reject_live_pickup_after_crash(self):
        # Crash into the right wall with a pickup never captured
        # (still live). The canonical tuple is returned and the refusal
        # count tracked, but no counters move and the run stays crashed.
        engine = GameEngine(head=(16.8, 0.0), heading='right',
                            box_min=BOX_MIN, box_max=BOX_MAX,
                            pickups=[make_pickup('p1', 5.0, 5.0)],
                            cap=1)
        events = engine.step(DT)  # 16.8 + 0.3 = 17.1 >= 17.0 -> crash
        self.assertEqual(events[-1], ('crashed', 'boundary'))
        self.assertTrue(engine.finished)
        self.assertEqual(engine.result, 'crashed')
        result = engine.reject_pickup('p1', 'clash')
        self.assertEqual(result, ('refused', 'p1', 'clash'))
        # Live double-guard: nothing rolled back.
        self.assertEqual(engine.molecules_stacked, 0)
        self.assertIn('p1', engine.live_pickup_ids)
        # The pin: crashed runs are NEVER un-finished.
        self.assertTrue(engine.finished)
        self.assertEqual(engine.result, 'crashed')

    def test_reject_captured_pickup_after_crash(self):
        # Capture on tick 1, keep driving into the wall; the crash ends
        # the run later. Rejecting the earlier capture still rolls the
        # counters back (existing contract) but MUST NOT revive the run.
        pickup = make_pickup('p1', 2.5, 0.0, atoms_n=1)
        engine = GameEngine(head=(0.0, 0.0), heading='right',
                            box_min=BOX_MIN, box_max=BOX_MAX,
                            pickups=[pickup], cap=2)
        engine.step(DT)  # captures p1 (stacked=1; cap=2 -> no win)
        self.assertFalse(engine.finished)
        # Ticks 2..56: head 0.6..16.8, still inside. Tick 57: 17.1 ->
        # boundary crash (wall at 17.0).
        for _ in range(55):
            engine.step(DT)
            self.assertFalse(engine.finished)
        events = engine.step(DT)
        self.assertEqual(events[-1], ('crashed', 'boundary'))
        self.assertTrue(engine.finished)
        self.assertEqual(engine.result, 'crashed')
        self.assertEqual(engine.molecules_stacked, 1)
        # Controller-style reject of the captured pickup: counters roll
        # back (pinned behavior)...
        result = engine.reject_pickup('p1', 'clash')
        self.assertEqual(result, ('refused', 'p1', 'clash'))
        self.assertEqual(engine.molecules_stacked, 0)
        self.assertIn('p1', engine.live_pickup_ids)
        # ...but the crashed run stays finished.
        self.assertTrue(engine.finished)
        self.assertEqual(engine.result, 'crashed')


class TestRejectWithoutWin(unittest.TestCase):
    """Reject on a normal (unfinished) run: no un-finish noise."""

    def test_reject_on_unfinished_run_stays_unfinished(self):
        # No cap set (cap=None): capture then reject; finished/result
        # are untouched by the reject (they were never set). Counters
        # roll back per the existing contract (mirror of
        # test_engine_rules.test_reject_then_recapture semantics with a
        # distinct atoms_n to pin the atom counter specifically).
        pickup = make_pickup('p1', 2.5, 0.0, atoms_n=3)
        engine = GameEngine(head=(0.0, 0.0), heading='right',
                            pickups=[pickup])
        engine.step(DT)  # captures p1 -> 1/3/0
        self.assertEqual(engine.molecules_stacked, 1)
        self.assertEqual(engine.atoms_total, 3)
        result = engine.reject_pickup('p1', 'clash')
        self.assertEqual(result, ('refused', 'p1', 'clash'))
        self.assertEqual(engine.molecules_stacked, 0)
        self.assertEqual(engine.atoms_total, 0)
        self.assertEqual(engine.pickups_remaining, 1)
        self.assertIn('p1', engine.live_pickup_ids)
        # No cap, no win: nothing to un-finish.
        self.assertFalse(engine.finished)
        self.assertIsNone(engine.result)


class TestResumeAfterUnfinish(unittest.TestCase):
    """After the un-finish the run is truly live: step() moves again."""

    def test_step_resumes_after_unfinish(self):
        # Same cap=1 desync scenario; after the reject, a finished
        # engine would no-op forever (the freeze G2 describes). Post-fix
        # the next step emits events and advances the head.
        pickup = make_pickup('p1', 2.5, 0.0, atoms_n=1)
        engine = GameEngine(head=(0.0, 0.0), heading='right',
                            pickups=[pickup], cap=1)
        engine.step(DT)  # capture + won on tick 1
        engine.reject_pickup('p1', 'clash')
        events = engine.step(DT)
        # The run is live: events are non-empty and the head advanced
        # 0.3 -> 0.6. (Pre-fix FAILS: the inert engine returns [].)
        self.assertNotEqual(events, [])
        self.assertEqual(events[0][0], 'moved')
        self.assertAlmostEqual(engine.head[0], 0.6, delta=DELTA)
        self.assertAlmostEqual(engine.head[1], 0.0, delta=DELTA)
        # The re-armed pickup is still within radius of the advancing
        # head, so the SAME capture re-fires — and with cap=1 the win
        # re-fires too (the legitimate re-capture path after the player
        # re-approaches the refused pickup).
        names = [e[0] for e in events]
        self.assertEqual(names, ['moved', 'stacked', 'won'])
        self.assertEqual(engine.molecules_stacked, 1)


if __name__ == '__main__':
    unittest.main()
