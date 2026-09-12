"""serpentrum.game_engine — snake engine (movement + rules + sweeps, PURE).

The ROADMAP splits the engine across three plans with disjoint scope:

  02-06: movement core — step() advances the head at SPEED_A_PER_S along
      the current heading and emits ('moved', pos); the direction queue
      only BUFFERS (a pending direction is inert until turns are
      applied); pause/resume/reset (GAME-07).
  02-10: collisions and rules — boundary crash, polyline-edge body
      collision, pickup capture/chain growth, counters, win/budget.
  02-13 (this extension): rigid-pivot turn sweeps — applying buffered
      directions at the START of step() with the 3-leg refusal
      pre-check (GAME-10). A turn rotates the WHOLE chain rigidly about
      the head over TURN_TICKS ticks; atoms rotate WITH their segment
      (x, y rotate; z and symbol preserved) so pairwise stacking
      geometry stays frozen ("stacking geometry immutable at all times").
      Rigid rotation about the head is the only turn model compatible
      with that invariant (grid steps would tear the chain; per-segment
      steering would break the frozen stacking geometry).

Coordinate model (research R4 resolution — CONTINUOUS 2D floats, NOT a
grid): the head and segment centroids live in the box's xy-plane in
Angstroms; z is display-only and carried inside segment atom records,
rotated about the vertical axis through the head only as part of a
sweep (the 2D game plane is xy; z is preserved exactly). The "grid"
wording in ARCHITECTURE.md is stale shorthand — GAME-05's head-centroid-
vs-segments collision, GAME-10's rigid sweeps, and STACK-01's exact
placed distances are all incompatible with quantization.

Body-leg nuance (swept pre-check): rotation about the head preserves
point-to-point distances to the pivot, so head-vs-SEGMENT-POINT checks
are pose-invariant — but head-vs-POLYLINE-EDGE (chord) distances are NOT
(a chord between two rotated centroids can pass nearer the head than
either endpoint distance suggests), and the leg doubles as a defensive
guard if the running state was already overlapping. The swept body leg
therefore uses the SAME model as 02-10's forward check (rotated polyline
edges, same edge set, same _point_segment_distance_sq, same
BODY_COLLISION_RADIUS_A, STRICT <) — one body-collision model across
the whole engine.

Determinism: pure float arithmetic on fixed constants. NO RNG and NO
wall-clock anywhere (pause timing is the GUI's job — Pitfall 9.3), so
two engines built with identical args produce identical state and event
sequences over identical steps. python3.6 syntax only; stdlib-only PURE
module (no pymol / pmg_tk / PyQt5 / numpy — enforced by
tools/check_purity.py); zero sys.modules stubs.
"""

import math

# Constant speed in Angstroms per second (GAME-08: constant speed, no
# acceleration). The VALUE is a tunable placeholder pinned at 3.0 for
# Phase-2 testing (0.3 A per 0.1 s tick); the final feel is decided by
# Phase-4 playtesting (setup_logic mirrors it as its 'speed' default).
SPEED_A_PER_S = 3.0

# --- Rigid-pivot sweep constants (plan 02-13, GAME-10). This plan owns
# them — 02-06's trimmed movement scope defines only SPEED_A_PER_S +
# DIRS; 02-10's constants are collision/capture only. Sweep animation
# polish (easing, partial-tick rendering) is Phase 5; the pure math
# stays coarse at TURN_TICKS samples. ---
TURN_DEGREES = 90.0   # pivot turns are quarter-turns on the 2D plane
TURN_TICKS = 6        # ticks to complete one rigid sweep (15 deg/tick)

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


def _rotate_xy(x, y, cx, cy, cos_t, sin_t):
    """Rotate point (x, y) about center (cx, cy) by the angle whose cos
    and sin are given (CCW positive). Returns (rx, ry).

    dx = x - cx; dy = y - cy;
        rx = cx + dx*cos_t - dy*sin_t
        ry = cy + dx*sin_t + dy*cos_t

    Pure float arithmetic. z and symbol are NEVER touched here — callers
    that rotate atoms carry atom[3] (z) and atom[0] (sym) through
    unchanged, so a sweep about the vertical axis through the head
    preserves the display-only z exactly and keeps the atom identity.
    Verify: (3, 0) about (0, 0) by +90 deg (cos=0, sin=1) -> (0, 3).

    Module-level (not a method) so both the swept pre-check and the
    sweep-tick progression use the identical rotation primitive.
    """
    dx = x - cx
    dy = y - cy
    rx = cx + dx * cos_t - dy * sin_t
    ry = cy + dx * sin_t + dy * cos_t
    return (rx, ry)


class GameEngine(object):
    """Deterministic snake engine state — movement + rules + sweeps.

    State (all plain data, engine-owned):

      head:     (x, y) float tuple — continuous 2D position in
                Angstroms in the box's xy-plane (z is display-only and
                lives in segment atom records; rotated about the head
                only as part of a sweep, with z preserved exactly).
      heading:  unit vector (x, y) — one of the four DIRS axes, never a
                name; the direction of forward travel.
      segments: list of segment records. Order convention: index 0 is
                the OLDEST segment (tail-most), the LAST entry is the
                most recently stacked (nearest the head); new segments
                APPEND at the end. Each record:
                {'molecule_id': str, 'centroid': (x, y),
                 'atoms': [(sym, x, y, z), ...], 'atoms_n': int}
                The constructor/reset parameter is an explicit TEST
                SEAM — production chain growth lands in plan 02-10 —
                and the engine copies it, never sharing or mutating
                caller data. During a sweep the centroids + atom x/y
                are rotated rigidly about the head; z and sym preserved.
      sweeping: None, or the in-progress sweep-state dict (plan 02-13):
                {'start_heading', 'target_heading', 'angle_signed',
                 'total_ticks', 'tick',
                 'start_centroids', 'start_atoms'} — the last two are
                the chain pose captured at sweep open, used to rotate
                ABSOLUTELY each tick (no cross-tick float drift). step()
                advances 'tick' to total_ticks; on the final tick
                heading = target_heading and sweeping is cleared. reset()
                wipes it (epoch safety).
      pending:  list holding AT MOST ONE buffered direction name (the
                max-1 queue "beyond current"). Applied at the START of
                step() while not sweeping (plan 02-13): perpendicular ->
                start_sweep (this tick is sweep tick 1 on success;
                'turn_refused' + fall through on refusal); same-direction
                -> dropped. While sweeping, request_direction buffers
                against the sweep TARGET (newest-wins, max 1).
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
      pickups:  list of pickup records (copied — see _copy_pickups).
                Each: {'id': str, 'centroid': (x, y),
                'atoms': [(sym, x, y, z), ...], 'atoms_n': int}.
                'atoms' is REQUIRED (02-13's swept pickup leg consumes
                atom positions). None/empty = no pickups.
      live_pickup_ids: set of ids not yet captured; capture removes,
                reject_pickup re-adds. Scanned in pickups-list order.
      cap:      int or None — molecules_stacked >= cap emits ('won',).
      atom_budget: int or None — atoms_total > atom_budget emits
                ('budget_warning', atoms_total) exactly once per run.
      molecules_stacked: int counter (incremented on capture, rolled
                back by reject_pickup).
      atoms_total: int counter (sum of captured atoms_n; rolled back
                by reject_pickup).
      pickups_remaining: int counter (live pickup count).
    """

    def __init__(self, head=(0.0, 0.0), heading='right', segments=None,
                 box_min=None, box_max=None,
                 pickups=None, cap=None, atom_budget=None):
        """Seed the engine state (see reset for the parameter contract).

        Kept keyword-friendly: plan 02-10 extends this signature with
        additional keyword arguments, so callers should always pass
        these by name.
        """
        self.reset(head=head, heading=heading, segments=segments,
                   box_min=box_min, box_max=box_max,
                   pickups=pickups, cap=cap, atom_budget=atom_budget)

    def reset(self, head=(0.0, 0.0), heading='right', segments=None,
              box_min=None, box_max=None,
              pickups=None, cap=None, atom_budget=None):
        """Rebuild ALL engine state from the given seeds.

        Same parameters as __init__ (GAME-07 deterministic restart):
        head (x, y) floats, heading a DIRS name resolved to its unit
        vector, segments the test-seam list (copied — see
        _copy_segments), box_min/box_max the axis-aligned play box (None
        disables boundary checking — 02-06's default), pickups the list
        of pickup records (copied — see _copy_pickups; None/empty = no
        pickups), cap the win-cap molecule count (None = no win check),
        atom_budget the warning threshold (None = no budget check).
        Unknown heading names raise ValueError, the same loud contract
        as request_direction.
        """
        if heading not in DIRS:
            raise ValueError('unknown heading: %r (valid: %s)'
                             % (heading, ', '.join(sorted(DIRS))))
        self.head = (float(head[0]), float(head[1]))
        self.heading = DIRS[heading]
        self.segments = self._copy_segments(segments)
        self.pending = []
        self.sweeping = None  # epoch safety: no stale turn survives a reset
        self.paused = False
        self.box_min = tuple(box_min) if box_min is not None else None
        self.box_max = tuple(box_max) if box_max is not None else None
        self.finished = False
        self.result = None
        self.pickups = self._copy_pickups(pickups)
        self.live_pickup_ids = set(p['id'] for p in self.pickups)
        self.cap = cap
        self.atom_budget = atom_budget
        self.molecules_stacked = 0
        self.atoms_total = 0
        self.pickups_remaining = len(self.pickups)
        self._budget_warned = False
        self._refusal_counts = {}

    @property
    def molecules_remaining(self):
        """cap - molecules_stacked (None if cap is None). For the HUD (GAME-07).

        Read-only derived value (plan 04-02, 04-RESEARCH-hud.md Q4:
        keeps ``cap - molecules_stacked`` arithmetic in the pure engine,
        WSL-testable; the HUD reads ``engine.molecules_remaining``).
        Adds NO timing -- the engine has no wall-clock by design
        (04-RESEARCH-gameloop.md Q5/S3). Reflects reset() immediately
        (reset rebuilds cap and zeroes the counter in one epoch).
        """
        return None if self.cap is None else self.cap - self.molecules_stacked

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

    def _copy_pickups(self, pickups):
        """Copy the caller's pickup list into fresh engine-owned dicts.

        Same isolation contract as _copy_segments: each record becomes a
        new dict with a fresh 'atoms' list. 'atoms' is REQUIRED on every
        pickup record (02-13's swept pickup leg consumes atom positions
        at atom-level clearance). Unknown extra keys are carried through.
        """
        if not pickups:
            return []
        copies = []
        for p in pickups:
            copy = dict(p)
            copy['atoms'] = list(p.get('atoms', ()))
            if 'atoms_n' not in copy:
                copy['atoms_n'] = len(copy['atoms'])
            copies.append(copy)
        return copies

    def request_direction(self, direction):
        """Queue a turn request.

        While NOT sweeping (plan 02-06's original rule, reference = the
        CURRENT heading):

          - unknown name             -> ValueError (loud)
          - 180-degree reversal      -> ignored, return False
                                       (dot < -0.5; locked: no reversal)
          - same direction           -> ignored, return False
                                       (dot > 0.5; nothing to turn to)
          - buffer already holds one -> ignored, return False
                                       (at most ONE; FIRST-KEPT)
          - otherwise                -> buffered, return True

        While sweeping (plan 02-13, SWEEP-LEVEL 180 enforcement,
        reference = the sweep's TARGET heading — the heading that will
        be in effect when the request would apply):

          - 180-vs-target / same-as-target -> ignored, return False
                                               (dot < -0.5 or dot > 0.5)
          - otherwise                      -> buffered, return True
                                               (max 1, NEWEST-WINS — an
                                               INTENTIONAL in-sweep
                                               override of the static
                                               first-kept rule; the two
                                               policies are deliberately
                                               NOT unified)

        The 0.5 thresholds are on the unit-vector dot product: axis
        directions give dot values of exactly 1.0 (same), 0.0
        (perpendicular) or -1.0 (reverse), so anything near-perpendicular
        is queuable and anything near-parallel or near-reversed is not.
        """
        if direction not in DIRS:
            raise ValueError('unknown direction: %r (valid: %s)'
                             % (direction, ', '.join(sorted(DIRS))))
        unit = DIRS[direction]
        if self.sweeping is not None:
            target = self.sweeping['target_heading']
            dot = unit[0] * target[0] + unit[1] * target[1]
            if dot < -0.5 or dot > 0.5:
                return False
            # Perpendicular to the sweep target: buffer, newest wins.
            self.pending = [direction]
            return True
        dot = unit[0] * self.heading[0] + unit[1] * self.heading[1]
        if dot < -0.5:
            return False
        if dot > 0.5:
            return False
        if self.pending:
            return False
        self.pending.append(direction)
        return True

    def start_sweep(self, direction):
        """Attempt to open a rigid-pivot turn sweep toward `direction`.

        Public; also the internal path step() uses. Returns a 2-tuple
        ``(opened, events)``:

          - Success: ``(True, [])`` and ``self.sweeping`` is set to the
            sweep-state dict with ``tick=0`` (step() advances it to
            tick 1). The 3-leg pre-check cleared every sampled pose.
          - Refusal: ``(False, [('turn_refused', reason)])`` with ZERO
            state mutation (heading, segments, sweeping, pending all
            unchanged). `reason` is 'boundary', 'body', or 'pickup'.
          - 180-degree / same-as-current-heading: ``(False, [])`` — a
            no-op, NOT a refusal (mirrors request_direction; never
            reached via step() because request_direction filters these).

        The pre-check (_sweep_check_safe) samples K = TURN_TICKS + 1
        poses of the WHOLE chain rotated rigidly about the head and
        refuses on the first boundary / body / pickup hit. Rigid
        rotation about the head is the only turn model compatible with
        the frozen stacking geometry (GAME-10).
        """
        if direction not in DIRS:
            raise ValueError('unknown direction: %r (valid: %s)'
                             % (direction, ', '.join(sorted(DIRS))))
        if self.sweeping is not None:
            # Defensive: a sweep is already open. No second concurrent
            # sweep (step() never calls start_sweep while sweeping).
            return (False, [])
        target = DIRS[direction]
        sx, sy = self.heading
        dot = target[0] * sx + target[1] * sy
        if dot < -0.5 or dot > 0.5:
            # 180-degree reversal or same direction vs the CURRENT
            # heading: a no-op, not a refusal (mirrors request_direction
            # static rule; never reached via step()).
            return (False, [])
        # Signed sweep angle: cross(heading, target) > 0 -> CCW (+90);
        # < 0 -> CW (-90). After the dot filter, target is perpendicular
        # so cross is exactly +/-1 for axis pairs (never 0).
        cross = sx * target[1] - sy * target[0]
        angle_signed = TURN_DEGREES if cross > 0.0 else -TURN_DEGREES
        reason = self._sweep_check_safe(angle_signed)
        if reason is not None:
            return (False, [('turn_refused', reason)])
        # Open the sweep. start_centroids / start_atoms capture the chain
        # pose NOW so each tick rotates ABSOLUTELY from this pose (no
        # cross-tick float drift -> final pose exact to cos/sin quality).
        self.sweeping = {
            'start_heading': self.heading,
            'target_heading': target,
            'angle_signed': angle_signed,
            'total_ticks': TURN_TICKS,
            'tick': 0,
            'start_centroids': [seg['centroid'] for seg in self.segments],
            'start_atoms': [list(seg['atoms']) for seg in self.segments],
        }
        return (True, [])

    def _sweep_check_safe(self, angle_signed):
        """Run the 3-leg swept-region pre-check; return reason or None.

        Samples K = TURN_TICKS + 1 poses (k = 0..TURN_TICKS) of the WHOLE
        chain rotated rigidly about the head by
        th_k = angle_signed * k / TURN_TICKS. At each pose, in order:

          boundary leg (only if box set): any rotated segment CENTROID
            STRICTLY beyond the BOUNDARY_MARGIN_A-adjusted box
            [x0+M, x1-M] x [y0+M, y1-M] -> 'boundary'. (Outside means
            strictly beyond — a centroid exactly at a margin wall is
            inside; this is the swept pre-check model, distinct from
            02-10's inclusive forward-velocity crash at the head.)
          body leg: head vs the rotated chain polyline edges, same edge
            set as 02-10's forward check (i in range(0, n-1-
            SEGMENT_SKIP_RECENT)); STRICT < BODY_COLLISION_RADIUS_A**2
            -> 'body'. (See the module docstring for the chord nuance.)
          pickup leg (atom-level): any rotated CHAIN ATOM (head excluded
            — it is the invariant pivot) within STRICT <
            SWEEP_PICKUP_CLEARANCE_A**2 (2.5 A) of any LIVE pickup ATOM
            -> 'pickup'. Pickups stay put; only the chain moves.

        Returns the first reason found, or None if every sampled pose is
        clear. Pure float math; builds rotated poses in LOCAL variables
        and NEVER writes them into engine state.
        """
        hx, hy = self.head
        n = len(self.segments)
        radius_sq_body = BODY_COLLISION_RADIUS_A * BODY_COLLISION_RADIUS_A
        clearance_sq = SWEEP_PICKUP_CLEARANCE_A * SWEEP_PICKUP_CLEARANCE_A
        box_set = self.box_min is not None and self.box_max is not None
        if box_set:
            bx0, by0 = self.box_min
            bx1, by1 = self.box_max
            wall_x0 = bx0 + BOUNDARY_MARGIN_A
            wall_x1 = bx1 - BOUNDARY_MARGIN_A
            wall_y0 = by0 + BOUNDARY_MARGIN_A
            wall_y1 = by1 - BOUNDARY_MARGIN_A
        # Live pickup atoms (pickups don't move during the sweep).
        live_pickup_atoms = []
        for p in self.pickups:
            if p['id'] in self.live_pickup_ids:
                for atom in p['atoms']:
                    live_pickup_atoms.append((atom[1], atom[2]))
        limit = n - 1 - SEGMENT_SKIP_RECENT
        for k in range(TURN_TICKS + 1):
            th = angle_signed * k / float(TURN_TICKS)
            cos_t = math.cos(math.radians(th))
            sin_t = math.sin(math.radians(th))
            rot_centroids = []
            rot_chain_atoms = []
            for seg in self.segments:
                cx, cy = seg['centroid']
                rcx, rcy = _rotate_xy(cx, cy, hx, hy, cos_t, sin_t)
                rot_centroids.append((rcx, rcy))
                for atom in seg['atoms']:
                    rax, ray = _rotate_xy(atom[1], atom[2],
                                          hx, hy, cos_t, sin_t)
                    rot_chain_atoms.append((rax, ray))
            # Boundary leg (centroid-level, sampled).
            if box_set:
                for rcx, rcy in rot_centroids:
                    if (rcx < wall_x0 or rcx > wall_x1 or
                            rcy < wall_y0 or rcy > wall_y1):
                        return 'boundary'
            # Body leg (head vs rotated polyline edges, 02-10's model).
            if limit > 0:
                for i in range(limit):
                    ax, ay = rot_centroids[i]
                    bx, by = rot_centroids[i + 1]
                    if _point_segment_distance_sq(hx, hy, ax, ay, bx, by) \
                            < radius_sq_body:
                        return 'body'
            # Pickup leg (rotated chain atoms vs live pickup atoms).
            if live_pickup_atoms and rot_chain_atoms:
                for rax, ray in rot_chain_atoms:
                    for px, py in live_pickup_atoms:
                        ddx = rax - px
                        ddy = ray - py
                        if ddx * ddx + ddy * ddy < clearance_sq:
                            return 'pickup'
        return None

    def _advance_sweep(self):
        """Advance the open sweep by one tick; return the tick's events.

        Increments ``sweeping['tick']``, rotates the WHOLE chain
        (centroids + atom x/y) ABSOLUTELY from the sweep's start pose by
        th = angle_signed * tick / total_ticks (so floating-point error
        does NOT accumulate across ticks — the final pose is exact to
        cos/sin quality, well under the 1e-9 assertion delta). z and
        symbol are preserved. Emits ``('turning', tick / total)``. NO
        forward motion and no ``('moved',)`` event during sweeps.

        On the final tick (tick == total_ticks): sets heading =
        target_heading and clears sweeping. Pending is NOT touched here
        — a chained turn is attempted at the NEXT step's start, by the
        same pending-application rule (the revision-pinned timing).
        """
        sweep = self.sweeping
        sweep['tick'] += 1
        tick = sweep['tick']
        total = sweep['total_ticks']
        angle = sweep['angle_signed']
        th = angle * tick / float(total)
        cos_t = math.cos(math.radians(th))
        sin_t = math.sin(math.radians(th))
        hx, hy = self.head
        start_centroids = sweep['start_centroids']
        start_atoms = sweep['start_atoms']
        new_segments = []
        for i in range(len(self.segments)):
            seg = self.segments[i]
            scx, scy = start_centroids[i]
            rcx, rcy = _rotate_xy(scx, scy, hx, hy, cos_t, sin_t)
            new_atoms = []
            for atom in start_atoms[i]:
                sym = atom[0]
                ax = atom[1]
                ay = atom[2]
                az = atom[3]
                rax, ray = _rotate_xy(ax, ay, hx, hy, cos_t, sin_t)
                new_atoms.append((sym, rax, ray, az))
            new_seg = dict(seg)
            new_seg['centroid'] = (rcx, rcy)
            new_seg['atoms'] = new_atoms
            new_segments.append(new_seg)
        self.segments = new_segments
        events = [('turning', tick / float(total))]
        if tick >= total:
            self.heading = sweep['target_heading']
            self.sweeping = None
        return events

    def step(self, dt):
        """Advance the simulation by dt seconds; return the event list.

        Paused -> no-op: return [] and mutate nothing.
        Finished (crashed/won) -> no-op: return [] and mutate nothing.

        Sweep-in-progress (plan 02-13): advance the open sweep one tick
        via _advance_sweep — rotate the whole chain rigidly about the
        head and emit ('turning', tick/total). NO forward motion and no
        ('moved',) event during sweeps. On the final tick heading becomes
        the target and sweeping clears; pending is NOT touched (a chained
        turn is attempted at the NEXT step's start).

        Pending application at step START (plan 02-13, not sweeping): pop
        the front request. Perpendicular to the current heading -> attempt
        start_sweep(d); on success THIS tick is sweep tick 1 (rotate 15
        deg, emit ('turning', 1/6), no 'moved'); on refusal emit
        ('turn_refused', reason), CONSUME the request, and fall through to
        forward motion in the same tick. Same-direction -> dropped
        silently, fall through. (180-degree requests never reach pending —
        request_direction filters them.) The turn attempt runs BEFORE the
        forward branch, so a successful turn tick never also moves the
        head.

        Movement branch (02-06): head += heading * SPEED_A_PER_S * dt,
        and emit ('moved', (x, y)) carrying the NEW position. At
        SPEED_A_PER_S = 3.0 a dt of 0.1 s advances the head exactly 0.3 A
        along the current heading.

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

        Pickup capture (plan 02-10, STACK-05 seam): after the body check,
        scan pickups in list order; the FIRST live pickup whose squared
        centroid distance to the head is <= PICKUP_RADIUS_A ** 2
        (inclusive) is captured — claim it, increment counters, emit
        ('stacked', pickup_record). At most ONE capture per tick. After
        a capture: if atom_budget is set and atoms_total > atom_budget
        and not yet warned, emit ('budget_warning', atoms_total) exactly
        once per run; then if cap is set and molecules_stacked >= cap,
        emit ('won',), set finished=True / result='won', clear pending.
        A crash stops all later event processing (pickup/win never fire
        on a crash tick).
        """
        if self.paused:
            return []
        if self.finished:
            return []
        # Sweep-in-progress: advance one tick; NO forward motion.
        if self.sweeping is not None:
            return self._advance_sweep()
        events = []
        # Pending application at step START (not sweeping): pop the front
        # request. Perpendicular -> start_sweep (this tick becomes sweep
        # tick 1 on success; 'turn_refused' + fall through on refusal).
        # Same-direction / 180 -> dropped, fall through to forward motion.
        if self.pending:
            d = self.pending.pop(0)
            unit = DIRS[d]
            dot = unit[0] * self.heading[0] + unit[1] * self.heading[1]
            if -0.5 <= dot <= 0.5:
                opened, sweep_events = self.start_sweep(d)
                events.extend(sweep_events)
                if opened:
                    # THIS tick is sweep tick 1 (rotate 15 deg, no move).
                    events.extend(self._advance_sweep())
                    return events
                # Refused: request consumed; fall through to forward.
            # Same-direction (or a 180 that should never be here): drop,
            # fall through to forward motion.
        hx, hy = self.head
        ux, uy = self.heading
        nx = hx + ux * SPEED_A_PER_S * dt
        ny = hy + uy * SPEED_A_PER_S * dt
        self.head = (nx, ny)
        events.append(('moved', (nx, ny)))
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
        # Pickup capture (STACK-05 seam): first live pickup within
        # PICKUP_RADIUS_A (inclusive) is claimed and counted. At most
        # ONE per tick (deterministic list order). Capture is followed
        # by the budget warning (once per run) and the win check.
        if self.live_pickup_ids:
            pickup_sq = PICKUP_RADIUS_A * PICKUP_RADIUS_A
            for pickup in self.pickups:
                if pickup['id'] not in self.live_pickup_ids:
                    continue
                px, py = pickup['centroid']
                dx = nx - px
                dy = ny - py
                if dx * dx + dy * dy <= pickup_sq:
                    self.live_pickup_ids.discard(pickup['id'])
                    self.molecules_stacked += 1
                    self.atoms_total += pickup['atoms_n']
                    self.pickups_remaining -= 1
                    events.append(('stacked', pickup))
                    # Budget warning: once per run, never a hard stop.
                    if (self.atom_budget is not None and
                            self.atoms_total > self.atom_budget and
                            not self._budget_warned):
                        self._budget_warned = True
                        events.append(('budget_warning', self.atoms_total))
                    # Win at cap: checked AFTER capture on the same tick.
                    if (self.cap is not None and
                            self.molecules_stacked >= self.cap):
                        events.append(('won',))
                        self.finished = True
                        self.result = 'won'
                        self.pending = []
                        return events
                    break  # at most ONE capture per tick
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

    def attach_segment(self, molecule_id, centroid, atoms):
        """Append the frozen segment record (GAME-10 rigid body).

        Counter-NEUTRAL: the capture already counted this molecule in
        molecules_stacked / atoms_total. The controller calls this
        AFTER stacking.place_pickup succeeds — the segment is the frozen
        placed geometry, appended at the end of the chain (index 0 =
        oldest, last = nearest head).

        The record matches the 02-06 segment seam shape:
        {'molecule_id', 'centroid', 'atoms', 'atoms_n'}.
        """
        self.segments.append({
            'molecule_id': molecule_id,
            'centroid': (float(centroid[0]), float(centroid[1])),
            'atoms': list(atoms),
            'atoms_n': len(atoms),
        })

    def reject_pickup(self, pickup_id, reason='clash'):
        """Roll back a capture and re-arm the pickup (STACK-05 seam).

        The controller calls this when stacking.place_pickup + check_clash
        reject the placement. Rolls the counters back (molecules_stacked
        -= 1, atoms_total -= atoms_n, pickups_remaining += 1), re-adds
        the id to live_pickup_ids, tracks a per-pickup refusal count,
        and RETURNS the canonical 3-tuple ('refused', pickup_id, reason).
        step() events cannot be emitted from controller-called methods,
        so the controller logs the returned tuple.

        Guard: if the pickup is still live (never captured or already
        rejected), the counters are NOT rolled back (prevents double-
        decrement) but the refusal count is still tracked and the
        canonical tuple is still returned.
        """
        pickup = None
        for p in self.pickups:
            if p['id'] == pickup_id:
                pickup = p
                break
        if pickup is None:
            return ('refused', pickup_id, reason)
        self._refusal_counts[pickup_id] = \
            self._refusal_counts.get(pickup_id, 0) + 1
        if pickup_id in self.live_pickup_ids:
            # Already live — never captured or already rejected. Do NOT
            # roll back (counters were never incremented for this id).
            return ('refused', pickup_id, reason)
        self.live_pickup_ids.add(pickup_id)
        self.molecules_stacked -= 1
        self.atoms_total -= pickup['atoms_n']
        self.pickups_remaining += 1
        return ('refused', pickup_id, reason)
