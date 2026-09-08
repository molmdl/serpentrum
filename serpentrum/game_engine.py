"""serpentrum.game_engine — snake engine MOVEMENT core (PURE).

Plan 02-06 (wave 1 of the Phase-2 engine split). This module owns ONLY
movement: continuous-2D state, constant-speed forward stepping, the
direction queue, pause/resume/reset, and the segments state seam. The
ROADMAP splits the engine across three plans with disjoint scope:

  02-06 (this plan): movement core — step() advances the head at
      SPEED_A_PER_S along the current heading and emits ('moved', pos);
      the direction queue only BUFFERS (a pending direction is inert
      until turns are applied); pause/resume/reset (GAME-07).
  02-10: collisions and rules — boundary crash, polyline-edge body
      collision, pickup capture/chain growth, counters, win/budget.
  02-13: rigid-pivot turn sweeps — applying buffered directions at the
      START of step() with the 3-leg refusal pre-check.

Coordinate model (research R4 resolution — CONTINUOUS 2D floats, NOT a
grid): the head and segment centroids live in the box's xy-plane in
Angstroms; z is display-only and carried inside segment atom records but
never rotated here. The "grid" wording in ARCHITECTURE.md is stale
shorthand — GAME-05's head-centroid-vs-segments collision, GAME-10's
rigid sweeps, and STACK-01's exact placed distances are all incompatible
with quantization.

Determinism: pure float arithmetic on fixed constants. NO RNG and NO
wall-clock anywhere (pause timing is the GUI's job — Pitfall 9.3), so
two engines built with identical args produce identical state and event
sequences over identical steps. python3.6 syntax only; stdlib-only PURE
module (no pymol / pmg_tk / PyQt5 / numpy — enforced by
tools/check_purity.py); zero sys.modules stubs.
"""

# Constant speed in Angstroms per second (GAME-08: constant speed, no
# acceleration). The VALUE is a tunable placeholder pinned at 3.0 for
# Phase-2 testing (0.3 A per 0.1 s tick); the final feel is decided by
# Phase-4 playtesting (setup_logic mirrors it as its 'speed' default).
SPEED_A_PER_S = 3.0

# Direction names -> unit vectors in the box's xy-plane (math
# convention: +x right, +y up; heading angles right=0, up=+90,
# left=180, down=-90, CCW positive). The heading itself is stored as a
# UNIT VECTOR taken from this map, never as a name.
DIRS = {
    'left': (-1.0, 0.0),
    'right': (1.0, 0.0),
    'up': (0.0, 1.0),
    'down': (0.0, -1.0),
}


class GameEngine(object):
    """Deterministic snake engine state — movement core.

    State (all plain data, engine-owned):

      head:     (x, y) float tuple — continuous 2D position in
                Angstroms in the box's xy-plane (z is display-only and
                lives in segment atom records, never rotated here).
      heading:  unit vector (x, y) — one of the four DIRS axes, never a
                name; the direction of forward travel.
      segments: list of segment records — STATE ONLY in this plan (no
                collision semantics; that is plan 02-10's scope). Order
                convention: index 0 is the OLDEST segment (tail-most),
                the LAST entry is the most recently stacked (nearest
                the head); new segments APPEND at the end. Each record:
                {'molecule_id': str, 'centroid': (x, y),
                 'atoms': [(sym, x, y, z), ...], 'atoms_n': int}
                The constructor/reset parameter is an explicit TEST
                SEAM — production chain growth lands in plan 02-10 —
                and the engine copies it, never sharing or mutating
                caller data.
      pending:  list holding AT MOST ONE buffered direction name (the
                max-1 queue "beyond current"). Inert in this plan: a
                buffered request produces no event and no heading
                change in step(); plan 02-13 consumes it at step start.
      paused:   bool — True makes step() an immediate no-op [].
    """

    def __init__(self, head=(0.0, 0.0), heading='right', segments=None):
        """Seed the engine state (see reset for the parameter contract).

        Kept keyword-friendly: plan 02-10 extends this signature with
        additional keyword arguments, so callers should always pass
        these by name.
        """
        self.reset(head=head, heading=heading, segments=segments)

    def reset(self, head=(0.0, 0.0), heading='right', segments=None):
        """Rebuild ALL engine state from the given seeds.

        Same parameters as __init__ (GAME-07 deterministic restart):
        head (x, y) floats, heading a DIRS name resolved to its unit
        vector, segments the test-seam list (copied — see
        _copy_segments). Unknown heading names raise ValueError, the
        same loud contract as request_direction.
        """
        if heading not in DIRS:
            raise ValueError('unknown heading: %r (valid: %s)'
                             % (heading, ', '.join(sorted(DIRS))))
        self.head = (float(head[0]), float(head[1]))
        self.heading = DIRS[heading]
        self.segments = self._copy_segments(segments)
        self.pending = []
        self.paused = False

    def _copy_segments(self, segments):
        """Copy the caller's segment list into fresh engine-owned dicts.

        Never shares or mutates caller data: each record becomes a new
        dict with a fresh 'atoms' list (atom entries are immutable
        tuples, so a list-level copy suffices). Unknown extra keys are
        carried through so later plans can extend the record without
        changing this copy logic.
        """
        if not segments:
            return []
        copies = []
        for seg in segments:
            copy = dict(seg)
            copy['atoms'] = list(seg.get('atoms', ()))
            if 'atoms_n' not in copy:
                copy['atoms_n'] = len(copy['atoms'])
            copies.append(copy)
        return copies

    def request_direction(self, direction):
        """Queue a turn request against the CURRENT heading.

        Contract (plan 02-06; reference is the current heading — plan
        02-13 switches the reference to the sweep target while
        sweeping, which is out of scope here):

          - unknown name             -> ValueError (loud)
          - 180-degree reversal      -> ignored, return False
                                        (dot < -0.5; locked: no reversal)
          - same direction           -> ignored, return False
                                        (dot > 0.5; nothing to turn to)
          - buffer already holds one -> ignored, return False
                                        (at most ONE request buffered
                                        beyond the current heading)
          - otherwise                -> buffered, return True

        The 0.5 thresholds are on the unit-vector dot product: axis
        directions give dot values of exactly 1.0 (same), 0.0
        (perpendicular) or -1.0 (reverse), so anything near-perpendicular
        is queuable and anything near-parallel or near-reversed is not.
        """
        if direction not in DIRS:
            raise ValueError('unknown direction: %r (valid: %s)'
                             % (direction, ', '.join(sorted(DIRS))))
        unit = DIRS[direction]
        dot = unit[0] * self.heading[0] + unit[1] * self.heading[1]
        if dot < -0.5:
            return False
        if dot > 0.5:
            return False
        if self.pending:
            return False
        self.pending.append(direction)
        return True

    def step(self, dt):
        """Advance the simulation by dt seconds; return the event list.

        Paused -> no-op: return [] and mutate nothing.

        Movement branch (this plan's ONLY step branch): head += heading
        * SPEED_A_PER_S * dt, and emit [('moved', (x, y))] carrying the
        NEW position. At SPEED_A_PER_S = 3.0 a dt of 0.1 s advances the
        head exactly 0.3 A along the current heading.

        A pending direction is deliberately NOT consumed here and
        produces NO event — in plan 02-06 the queue only buffers; plan
        02-13 applies pending turns at the START of step(). (Suite
        consequence: 02-06's tests never call step() while a request is
        pending, so that later change cannot break them.)
        """
        if self.paused:
            return []
        hx, hy = self.head
        ux, uy = self.heading
        nx = hx + ux * SPEED_A_PER_S * dt
        ny = hy + uy * SPEED_A_PER_S * dt
        self.head = (nx, ny)
        return [('moved', (nx, ny))]

    def pause(self):
        """Freeze the simulation: step() becomes a no-op returning [].

        Pure flag flip — no wall-clock is recorded (Pitfall 9.3: pause
        timing belongs to the GUI layer, keeping this module
        deterministic).
        """
        self.paused = True

    def resume(self):
        """Unfreeze the simulation: step() moves the head again."""
        self.paused = False
