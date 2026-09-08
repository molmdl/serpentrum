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

# --- Collision + rules constants (plan 02-10). The ONE margin name
# everywhere is BOUNDARY_MARGIN_A; HEAD_WALL_MARGIN_A is retired. ---

BODY_COLLISION_RADIUS_A = 2.0   # head-centroid vs chain-edge clearance.
# MUST stay < 3.4 A (committed dimer2 stacking distance) minus margin,
# else the head would collide with the segment just stacked behind it.
SEGMENT_SKIP_RECENT = 2         # newest chain edges exempt from self-collision
PICKUP_RADIUS_A = 3.0           # head-vs-pickup-CENTROID capture distance
BOUNDARY_MARGIN_A = 1.0         # = BODY_COLLISION_RADIUS_A / 2 — the ONE
                                # margin constant name everywhere (02-13's
                                # boundary leg reuses it)
SWEEP_PICKUP_CLEARANCE_A = 2.5  # atom-level clearance for 02-13's sweep
                                # pickup leg (same rationale as 02-04
                                # check_clash's 2.5 A inter-fragment
                                # threshold; defined here because this plan
                                # owns the constants block — 02-13 consumes
                                # it)


def _point_segment_distance_sq(px, py, ax, ay, bx, by):
    """Squared distance from point (px, py) to segment (a -> b) in 2D.

    Standard clamped projection: project (p - a) onto (b - a), clamp the
    parameter t to [0, 1] (so the closest point stays on the segment),
    and return the squared distance to that closest point. Compare the
    result against BODY_COLLISION_RADIUS_A ** 2 (strict <).

    Module-level (not a method) so plan 02-13's swept pre-check body leg
    can reuse it on the same polyline edges without re-implementing the
    math. Pure stdlib float arithmetic — no numpy.
    """
    dx = bx - ax
    dy = by - ay
    len_sq = dx * dx + dy * dy
    if len_sq == 0.0:
        # Degenerate segment (a == b): distance to the single point.
        ex = px - ax
        ey = py - ay
        return ex * ex + ey * ey
    # Project (p - a) onto (b - a), clamp t to [0, 1].
    t = ((px - ax) * dx + (py - ay) * dy) / len_sq
    if t < 0.0:
        t = 0.0
    elif t > 1.0:
        t = 1.0
    # Closest point on the segment.
    cx = ax + t * dx
    cy = ay + t * dy
    ex = px - cx
    ey = py - cy
    return ex * ex + ey * ey


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
                max-1 queue "beyond current"). Inert in 02-06; plan 02-13
                consumes it at step start.
      paused:   bool — True makes step() an immediate no-op [].
      box_min:  (x0, y0) float tuple or None — axis-aligned box lower
                corner (from setup_logic's preset). None disables
                boundary checking (02-06's free-moving default).
      box_max:  (x1, y1) float tuple or None — axis-aligned box upper
                corner. None disables boundary checking.
      finished: bool — True once the run has ended (crash or win); every
                later step() is a no-op returning []. Introduced by
                plan 02-10 (02-06's trimmed scope has no end-of-run
                state).
      result:   None, 'crashed', or 'won' — the end-of-run verdict. Set
                together with finished=True.
    """

    def __init__(self, head=(0.0, 0.0), heading='right', segments=None,
                 box_min=None, box_max=None):
        """Seed the engine state (see reset for the parameter contract).

        Kept keyword-friendly: plan 02-10 extends this signature with
        additional keyword arguments, so callers should always pass
        these by name.
        """
        self.reset(head=head, heading=heading, segments=segments,
                   box_min=box_min, box_max=box_max)

    def reset(self, head=(0.0, 0.0), heading='right', segments=None,
              box_min=None, box_max=None):
        """Rebuild ALL engine state from the given seeds.

        Same parameters as __init__ (GAME-07 deterministic restart):
        head (x, y) floats, heading a DIRS name resolved to its unit
        vector, segments the test-seam list (copied — see
        _copy_segments), box_min/box_max the axis-aligned play box (None
        disables boundary checking — 02-06's default). Unknown heading
        names raise ValueError, the same loud contract as
        request_direction.
        """
        if heading not in DIRS:
            raise ValueError('unknown heading: %r (valid: %s)'
                             % (heading, ', '.join(sorted(DIRS))))
        self.head = (float(head[0]), float(head[1]))
        self.heading = DIRS[heading]
        self.segments = self._copy_segments(segments)
        self.pending = []
        self.paused = False
        self.box_min = tuple(box_min) if box_min is not None else None
        self.box_max = tuple(box_max) if box_max is not None else None
        self.finished = False
        self.result = None

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
        Finished (crashed/won) -> no-op: return [] and mutate nothing.

        Movement branch: head += heading * SPEED_A_PER_S * dt, and emit
        [('moved', (x, y))] carrying the NEW position. At SPEED_A_PER_S
        = 3.0 a dt of 0.1 s advances the head exactly 0.3 A along the
        current heading.

        Boundary crash (plan 02-10, GAME-05): after the move, if a box is
        set and the head enters the BOUNDARY_MARGIN_A margin of the AABB
        (inclusive at the margin-adjusted walls), emit
        ('crashed', 'boundary'), set finished=True / result='crashed',
        clear the pending queue, and STOP event processing for this
        tick. A crashed engine no-ops on every later step().

        Self-collision (plan 02-10, GAME-05 — AUTHORITATIVE polyline-edge
        model): after the boundary check, build the chain polyline from
        segment centroids c[0..n-1] (index 0 = oldest, n-1 = newest
        nearest the head). Check edges (c[i], c[i+1]) for i in
        range(0, n - 1 - SEGMENT_SKIP_RECENT) — the SEGMENT_SKIP_RECENT
        newest edges (the neck) are exempt. If the head's squared
        distance to any checked edge is STRICT < BODY_COLLISION_RADIUS_A
        ** 2, emit ('crashed', 'body') and end the run the same way as a
        boundary crash. Boundary check runs first; a crash stops all
        later event processing for the tick.

        A pending direction is deliberately NOT consumed here and
        produces NO event — the queue only buffers; plan 02-13 applies
        pending turns at the START of step(). (Suite consequence: the
        02-06 and 02-10 suites never call step() while a request is
        pending, so that later change cannot break them.)
        """
        if self.paused:
            return []
        if self.finished:
            return []
        hx, hy = self.head
        ux, uy = self.heading
        nx = hx + ux * SPEED_A_PER_S * dt
        ny = hy + uy * SPEED_A_PER_S * dt
        self.head = (nx, ny)
        events = [('moved', (nx, ny))]
        # Boundary crash: AABB + BOUNDARY_MARGIN_A, inclusive at the
        # margin-adjusted walls. A crash stops event processing, ends
        # the run, and clears the pending queue (turn-state hygiene —
        # 02-13 builds on this).
        if self.box_min is not None and self.box_max is not None:
            x0, y0 = self.box_min
            x1, y1 = self.box_max
            if (nx <= x0 + BOUNDARY_MARGIN_A or
                    nx >= x1 - BOUNDARY_MARGIN_A or
                    ny <= y0 + BOUNDARY_MARGIN_A or
                    ny >= y1 - BOUNDARY_MARGIN_A):
                events.append(('crashed', 'boundary'))
                self.finished = True
                self.result = 'crashed'
                self.pending = []
                return events
        # Self-collision: head-centroid vs chain POLYLINE EDGES built
        # from segment centroids. The SEGMENT_SKIP_RECENT edges nearest
        # the head (the neck) are exempt. STRICT < BODY_COLLISION_RADIUS_A**2.
        n = len(self.segments)
        limit = n - 1 - SEGMENT_SKIP_RECENT
        if limit > 0:
            radius_sq = BODY_COLLISION_RADIUS_A * BODY_COLLISION_RADIUS_A
            centroids = [seg['centroid'] for seg in self.segments]
            for i in range(limit):
                ax, ay = centroids[i]
                bx, by = centroids[i + 1]
                if _point_segment_distance_sq(nx, ny, ax, ay, bx, by) \
                        < radius_sq:
                    events.append(('crashed', 'body'))
                    self.finished = True
                    self.result = 'crashed'
                    self.pending = []
                    return events
        return events

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
