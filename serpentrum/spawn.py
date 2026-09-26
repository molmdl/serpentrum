"""serpentrum.spawn -- the PURE pickup-spawn policy (gap G3, plan 05-03).

The engine has a capture leg but NO spawn policy anywhere (ARCHITECTURE's
"engine-placed grid cells" is stale wording -- the engine never spawns);
this module is the one engine-adjacent behavior that exists nowhere
today. gui_game seeds ``GameEngine(pickups=...)`` from these results and
materializes the matching viewer objects.

PINNED POLICY (stated explicitly per the planning mandate):

  - ONE NEW spawn per resolution (never batch-spawn). After begin_game
    spawns the first pickup (``first``), every capture resolution
    ('stacked' handled -- success OR refusal) may spawn the next
    molecule (``next_after``), gated by a live-pickup ceiling
    MAX_LIVE_PICKUPS = 4 so refusal-lingering pickups cannot accumulate
    unbounded while the game keeps progressing (see ``can_spawn``).
  - CYCLIC molecule order: records in anchored list order, wrapping
    forever (set_a has 5 species; cap default 10 requires species
    reuse -- chemically valid, probe-verified 6-segment same-molecule
    chains are clash-safe).
  - DEMOTE-AFTER-REFUSE (2026-09-20, 05-16 re-test fix): the controller
    calls ``note_resolution(molecule_id, refused)`` after EVERY capture
    resolution. A refused/skipped molecule is moved to the BACK of the
    round-robin serve order (never permanently excluded -- the 5-mol
    pool + cap 10 REQUIRES repeats), so the NEXT spawn is a DIFFERENT
    molecule; a placed capture resets the consecutive-refuse counter.
    If refuses in a     row reach the pool size (every candidate refused
    consecutively), spawning PAUSES for a resumable COOLDOWN of
    EXHAUST_COOLDOWN_TICKS movement ticks (2026-09-20 follow-up: the
    permanent latch from f211d97 deadlocked runs near walls -- those
    refuses were POSITION-dependent and cleared once the head moved
    away, so a permanent stop was wrong). Since 2026-09-20c (owner
    directive, wall placement gate removed) refusals are CLASH-only, so
    the cooldown now fires only on genuine clash streaks -- the
    near-wall deadlock class it was built to absorb is gone, and it
    remains a pure safety net. The controller advances the
    cooldown clock via ``tick()`` once per 100 ms movement tick; when
    it elapses, the refuse streak resets and spawning RESUMES
    automatically with the same slot policy as before.
  - POSITION: 2026-09-26 Phase 5.3 (owner: 'make it more random in the
    box'): candidates are seeded-uniform over the shrunk box -- each of
    MAX_DRAWS attempts draws cx, cy per axis via the private seeded RNG
    over     [box_min + WALL_MARGIN_A, box_max - WALL_MARGIN_A]. The pre-5.3
    lookahead/lateral policy (every spawn confined to a 10 A bubble:
    8.0 A ahead of the head plus a seeded lateral in +/-6.0) is
    RETIRED; heading is position-neutral -- still validated for API
    compatibility, never referenced by the candidate math. Each
    candidate must ALSO clear a box-proportional MINIMUM head distance
    min(max(MIN_HEAD_DIST_FACTOR * h, HEAD_CLEARANCE_A),
    MIN_HEAD_DIST_CAP_FACTOR * h) with h the shrunk half-span (18.025 A
    on medium +/-55, so no unlucky draw lands 'too simple' close to the
    snake; the min_head_dist_a ctor kwarg overrides; h <= 0 on
    degenerate boxes folds the value <= 0 so the leg goes vacuous and
    exhaustion behavior is unchanged), plus the surviving placement
    hygiene legs: wall margin 3.5 A (shrunk box), chain-ATOM clearance
    3.0 A (originally sized to keep the since-REMOVED 2.5 A sweep
    pickup-leg pre-check satisfiable near fresh spawns; kept 2026-09-20
    as good placement hygiene), and live-pickup-centroid clearance
    6.0 A. Up to 32 seeded retries (    MAX_DRAWS), then a DETERMINISTIC
    grid-scan fallback (GRID_STEP_A = 2.0 over the shrunk box, x-major
    / y-minor cell indexing, first legal wins), else None. 2026-09-26
    Phase 5.3 plan 5.3-02: the scan starts at a seeded cell (one
    randrange over the cell count) and wraps -- same coverage (every
    cell checked exactly once, so None is returned only when genuinely
    no legal cell exists), kills the corner-bias clustering when the
    fallback fires on saturated boxes; still deterministic per seed.
    On None there is NO
    state advance -- the same record is offered again on the next call,
    and the pid counter is not consumed.
  - SEED: zlib.crc32 over a canonical setup string (NEVER hash() --
    PYTHONHASHSEED randomizes str hashes across processes). crc32 is
    process-stable: restart with the same setup reproduces the same
    spawn sequence (GAME-07 restart determinism).
  - UPLOADS spawn and are skipped at capture (honest STACK-03 pedagogy;
    locked decision 7): records whose ``set`` is '__upload__' cycle
    through exactly like demo records; the capture-time skip lives in
    the controller, not here.

Determinism: a private ``random.Random(seed)`` per spawner
(setup_logic.randomize_head precedent -- NEVER the global random
module); two spawners built with the same records/box/seed produce
byte-identical (record, pid, centroid) sequences over the same call
sequence.

Fully decoupled: NO imports from game_engine / orientation / molfile.
The caller passes ``atoms_by_id`` mapping record id -> the molecule's
ORIGIN-CENTERED atoms as ``(sym, x, y, z)`` tuples; the spawner
translates them to each candidate for the chain-atom clearance leg.
chain_atoms use the SAME ``(sym, x, y, z)`` engine-atom shape (z and
symbol are carried but the game plane is xy, so only x/y are compared).

python3.6 syntax only (%-formatting, no f-strings); PURE module
(stdlib math/zlib/random only -- no pymol / pmg_tk / PyQt5 / numpy
anywhere; auto-classified PURE by tools/check_purity.py); zero
sys.modules stubs.
"""

import math
import random
import zlib

# --- Pinned policy constants (plan 05-03; docstring above is the policy) ---

MAX_LIVE_PICKUPS = 4          # live-pickup ceiling (can_spawn gate)
MIN_HEAD_DIST_FACTOR = 0.35   # box-proportional min-head-distance factor
                              # (2026-09-26 Phase 5.3; owner-retunable at
                              # the feel-check, 5.1 SPEED_TIERS retune
                              # precedent; the min_head_dist_a ctor kwarg
                              # overrides)
MIN_HEAD_DIST_CAP_FACTOR = 0.8  # upper clamp: min_dist < span guarantees
                              # a legal point exists (and degenerate
                              # boxes fold the leg vacuous)
WALL_MARGIN_A = 3.5           # shrunk-box containment margin
HEAD_CLEARANCE_A = 5.0        # centroid distance from the head
CHAIN_ATOM_CLEARANCE_A = 3.0  # per-atom distance vs chain atoms (> 2.5 A
                              # — sized against the since-REMOVED
                              # game_engine.SWEEP_PICKUP_CLEARANCE_A sweep
                              # pickup leg; kept as spawn hygiene 2026-09-20)
LIVE_PICKUP_CLEARANCE_A = 6.0  # centroid distance vs live pickups
MAX_DRAWS = 32                # seeded retries before the grid-scan fallback
GRID_STEP_A = 2.0             # deterministic fallback scan step
EXHAUST_COOLDOWN_TICKS = 100  # exhaust pause window in movement ticks
                              # (100 ms tick -> ~10 s of wall-clock play):
                              # refuses in a row == pool size PAUSES
                              # spawning for this many ticks, then it
                              # auto-resumes; ANY placed capture or a
                              # completed cooldown resets the streak

# Heading name -> unit vector in the xy plane. Deliberately a PRIVATE
# mirror of game_engine.DIRS (this module is fully decoupled -- it must
# not import the engine; the contract is one of the four axis names).
_DIRS = {
    'left': (-1.0, 0.0),
    'right': (1.0, 0.0),
    'up': (0.0, 1.0),
    'down': (0.0, -1.0),
}


def seed_from_setup(setup):
    """Canonical, process-stable seed for a setup dict -> int.

    The canonical string is the sorted ``'%s=%r' % (key, value)`` items
    joined by ';' -- sorted so dict insertion order never matters, repr
    so values are unambiguous. Seeded via ``zlib.crc32`` of the utf-8
    bytes: crc32 is deterministic ACROSS PROCESSES (NEVER use hash() --
    PYTHONHASHSEED randomizes str hashes per process, which would break
    restart determinism).
    """
    canonical = ';'.join(sorted('%s=%r' % (key, value)
                                for key, value in setup.items()))
    return zlib.crc32(canonical.encode('utf-8'))


def build_pickup_seed(record, pid, centroid, atoms):
    """Assemble one engine pickup record (the GameEngine(pickups=...) seed).

    Contract (game_engine 'atoms' REQUIRED -- 02-13's swept pickup leg
    consumes atom positions): ``{'id': pid, 'molecule_id': record['id'],
    'centroid': (cx, cy), 'atoms': [(sym, x+cx, y+cy, z), ...],
    'atoms_n': len(atoms)}``. The origin-centered ``atoms`` are COPIED
    into a fresh translated list -- caller data is never mutated or
    shared. Callers may add extra keys (stack_ring, record fields) to the
    returned dict afterwards; the engine copies carry unknown keys
    through.
    """
    cx, cy = centroid
    moved = [(atom[0], atom[1] + cx, atom[2] + cy, atom[3])
             for atom in atoms]
    return {
        'id': pid,
        'molecule_id': record['id'],
        'centroid': (cx, cy),
        'atoms': moved,
        'atoms_n': len(atoms),
    }


class PickupSpawner(object):
    """Seeded, cyclic, clearance-validated pickup spawner.

    Parameters:

      records:     molecule records in ANCHORED list order (the cycle
                   order -- setloader.load_demo_set / load_upload output,
                   uploads included on purpose).
      box_min:     (x0, y0) box lower corner (setup_logic.BOX_PRESETS).
      box_max:     (x1, y1) box upper corner.
      seed:        int (see seed_from_setup) feeding a PRIVATE
                   random.Random -- never the global random module.
      atoms_by_id: record id -> that molecule's ORIGIN-CENTERED atoms as
                   (sym, x, y, z) tuples. Every record id MUST be
                   present (KeyError is the loud caller-bug signal).
      exhaust_cooldown_ticks: the exhaust-pause window in movement
                   ticks (default EXHAUST_COOLDOWN_TICKS = 100, ~10 s at
                   the 100 ms tick). Tunable for tests / difficulty.
      min_head_dist_a: minimum head-to-centroid distance enforced by
                   _legal leg 2 (default None -> the box-proportional
                   min(max(MIN_HEAD_DIST_FACTOR * h, HEAD_CLEARANCE_A),
                   MIN_HEAD_DIST_CAP_FACTOR * h) with h the shrunk
                   half-span; 2026-09-26 Phase 5.3). Tunable for tests /
                   difficulty, same pattern as exhaust_cooldown_ticks.

    State: a round-robin serve ORDER over records + a spawn counter
    (pids 'pick_0001', 'pick_0002', ...). Both advance ONLY on a
    returned spawn -- an exhausted (None) call replays the same record
    and the same pid on the next call. The order rotates on every
    issued spawn (front record moves to the back -- equivalent to the
    original cyclic index) and additionally on demote-after-refuse
    (the refused record moves to the back EARLY); pid assignment is
    untouched by demotions. The refuse-streak / cooldown state machine
    (note_resolution + tick) never touches order or pid either.
    """

    def __init__(self, records, box_min, box_max, seed, atoms_by_id,
                 exhaust_cooldown_ticks=EXHAUST_COOLDOWN_TICKS,
                 min_head_dist_a=None):
        self._records = list(records)
        self._box_min = (float(box_min[0]), float(box_min[1]))
        self._box_max = (float(box_max[0]), float(box_max[1]))
        self._rng = random.Random(seed)
        # Box-proportional minimum head distance (2026-09-26 Phase 5.3):
        # h = shrunk half-span (min axis keeps non-square boxes safe;
        # identical on the square presets). h <= 0 (degenerate boxes)
        # folds the value <= 0 -- the leg goes vacuous and exhaustion
        # behavior is unchanged.
        if min_head_dist_a is not None:
            self._min_head_dist = float(min_head_dist_a)
        else:
            x0, x1, y0, y1 = self._shrunk_bounds()
            h = 0.5 * min(x1 - x0, y1 - y0)
            self._min_head_dist = min(
                max(MIN_HEAD_DIST_FACTOR * h, HEAD_CLEARANCE_A),
                MIN_HEAD_DIST_CAP_FACTOR * h)
        self._atoms_by_id = atoms_by_id
        self._order = list(records)  # round-robin serve order (front first)
        self._issued = 0
        # Demote-after-refuse state (2026-09-20): consecutive refused
        # resolutions; reaching the pool size PAUSES spawning for
        # exhaust_cooldown_ticks movement ticks (a resumable cooldown,
        # NEVER a permanent latch -- position-dependent refuses clear
        # once the head moves). tick() advances the clock.
        self._exhaust_cooldown_ticks = int(exhaust_cooldown_ticks)
        self._consecutive_refuses = 0
        self._cooldown_remaining = 0

    # --- public API -------------------------------------------------

    def can_spawn(self, live_count):
        """MAX_LIVE gate: True while live_count < MAX_LIVE_PICKUPS (4)."""
        return live_count < MAX_LIVE_PICKUPS

    @property
    def spawn_paused(self):
        """True during the exhaust cooldown: every pool record refused
        consecutively, so ``_spawn`` returns None. Resumable -- the
        controller's per-tick ``tick()`` calls count the window down
        and spawning then resumes automatically. Read-only."""
        return self._cooldown_remaining > 0

    @property
    def exhaust_cooldown_ticks(self):
        """The configured exhaust-pause window in movement ticks (for
        the GUI's cooldown DBG line)."""
        return self._exhaust_cooldown_ticks

    @property
    def min_head_dist(self):
        """The minimum head-to-centroid distance enforced by _legal leg
        2 (2026-09-26 Phase 5.3 uniform policy; box-proportional default
        or the min_head_dist_a ctor override). Tests/GUI introspection,
        mirrors exhaust_cooldown_ticks. Read-only."""
        return self._min_head_dist

    @property
    def pool_size(self):
        """The number of pool records (for the GUI's cooldown DBG line)."""
        return len(self._order)

    def note_resolution(self, molecule_id, refused):
        """Record one capture resolution for demote-after-refuse (05-16
        cascade fix, 2026-09-20).

        refused=True (a REFUSE_* outcome; 2026-09-20c fix G1: only
        placement clashes -- the wall leg is retired): move the record
        to the BACK of the serve order so the next spawn serves a
        DIFFERENT molecule (never a permanent exclusion -- cap 10
        requires repeats), and count consecutive refuses; refuses in a
        row >= pool size PAUSE spawning for exhaust_cooldown_ticks
        movement ticks (auto-resuming, NEVER latched). While paused
        the streak does NOT advance (resolves of pickups still live on
        the board may neither extend nor refresh the cooldown).
        SKIP_* outcomes are INFORMATIONAL (2026-09-20c fix G1: upload
        captures skip for the missing dataset entry, they are not
        placement refuses) and must be reported with refused=False so
        they never latch the exhaust cooldown.

        refused=False (a 'placed' capture, or an informational SKIP_*
        outcome per fix G1 above): reset the consecutive
        counter IMMEDIATELY (any successful placement ends the refuse
        streak). A molecule already at the back of the order needs no
        rotation (the just-served front already advanced), so demotion
        is a no-op in the common "served then immediately refused"
        case. Unknown molecule ids are ignored (defensive).
        """
        if not refused:
            self._consecutive_refuses = 0
            return
        for i, record in enumerate(self._order):
            if record['id'] == molecule_id:
                self._order.append(self._order.pop(i))
                break
        if self._cooldown_remaining > 0:
            # Paused already: demote above still applies (round-robin
            # policy is untouched), but the streak is frozen so the
            # cooldown cannot be extended or refreshed.
            return
        self._consecutive_refuses += 1
        if self._consecutive_refuses >= len(self._order):
            self._cooldown_remaining = self._exhaust_cooldown_ticks

    def tick(self):
        """Advance the exhaust cooldown clock by ONE movement tick
        (the controller's 100 ms game tick; wall-clock pauses stop the
        tick timer, so the window elapses in PLAY time).

        Returns True exactly on the tick the cooldown elapses (the
        resume edge -- the streak resets and spawning resumes), False
        otherwise. Calling tick() while not paused is a cheap no-op.
        """
        if self._cooldown_remaining <= 0:
            return False
        self._cooldown_remaining -= 1
        if self._cooldown_remaining == 0:
            # Resume edge: the streak resets, so re-pausing requires a
            # fresh run of pool-size consecutive refuses.
            self._consecutive_refuses = 0
            return True
        return False

    def first(self, head_xy, heading):
        """Spawn the initial pickup (begin_game): no chain, no live.

        ``heading`` is accepted for API compatibility only (validated,
        position-neutral): candidates are seeded-uniform over the
        shrunk box (2026-09-26 Phase 5.3), never heading-anchored.
        """
        return self._spawn(head_xy, heading, (), ())

    def next_after(self, head_xy, heading, chain_atoms, live_centroids):
        """Spawn the next pickup after one capture resolution.

        ``heading``: accepted for API compatibility only (validated,
        position-neutral) -- see ``first``. ``chain_atoms``: every
        chain atom so far (head molecule atoms + every attached
        segment's atoms, (sym, x, y, z) shape) -- the per-atom
        clearance leg keeps fresh spawns out of the snake.
        ``live_centroids``: (x, y) pairs of pickups currently live --
        the 6.0 A centroid spacing leg. Returns the same
        ``(record, pid, centroid)`` 3-tuple as ``first``, or None when
        no legal position exists (NO state advance on None).
        """
        return self._spawn(head_xy, heading, chain_atoms, live_centroids)

    # --- internals --------------------------------------------------

    def _shrunk_bounds(self):
        """(x0, x1, y0, y1) of the shrunk (wall-margined) box --
        box_min + WALL_MARGIN_A / box_max - WALL_MARGIN_A. Shared by
        the uniform sampling loop, the grid-scan fallback, and the
        min_head_dist half-span computation."""
        x0 = self._box_min[0] + WALL_MARGIN_A
        x1 = self._box_max[0] - WALL_MARGIN_A
        y0 = self._box_min[1] + WALL_MARGIN_A
        y1 = self._box_max[1] - WALL_MARGIN_A
        return (x0, x1, y0, y1)

    def _spawn(self, head_xy, heading, chain_atoms, live_centroids):
        if not self._order:
            return None
        if self._cooldown_remaining > 0:
            # Exhaust cooldown pause: every pool record refused in a
            # row -- spawning is paused until tick() counts the window
            # down (resumable, NEVER a permanent latch).
            return None
        if heading not in _DIRS:
            raise ValueError('unknown heading: %r (valid: %s)'
                             % (heading, ', '.join(sorted(_DIRS))))
        # 2026-09-26 Phase 5.3 (owner: 'make it more random in the
        # box'): candidates are seeded-UNIFORM over the shrunk box --
        # per-axis rng.uniform draws, two seeded draws per attempt.
        # Heading is otherwise UNUSED (position-neutral; validated
        # above for API compatibility). Draw ORDER is fixed and
        # captured in the seed stream, so same-seed sequences remain
        # byte-identical (GAME-07).
        x0, x1, y0, y1 = self._shrunk_bounds()
        record = self._order[0]
        atoms = self._atoms_by_id[record['id']]
        for _ in range(MAX_DRAWS):
            cx = self._rng.uniform(x0, x1)
            cy = self._rng.uniform(y0, y1)
            if self._legal(cx, cy, head_xy, atoms, chain_atoms,
                           live_centroids):
                return self._issue(record, cx, cy)
        # Grid-scan fallback over the shrunk box (factored helper,
        # 2026-09-26 Phase 5.3 plan 5.3-02). Fully deterministic for
        # fixed (head, chain, live, seed) inputs.
        return self._grid_scan(record, atoms, head_xy, chain_atoms,
                               live_centroids)

    def _grid_scan(self, record, atoms, head_xy, chain_atoms,
                   live_centroids):
        """Deterministic grid-scan fallback over the shrunk box: every
        cell is checked EXACTLY ONCE (x-major / y-minor cell indexing),
        first legal wins, else None.

        2026-09-26 Phase 5.3 plan 5.3-02: the scan starts at a SEEDED
        cell -- ``self._rng.randrange(cell_count)`` -- and wraps
        (``(start + i) % cell_count``), so identical coverage to the old
        most-negative-corner-first scan but a per-seed start cell. The
        pre-5.3-02 scan always landed at the same most-negative first
        legal cell when it fired, clustering forced spawns late-game on
        saturated small boxes; the seeded start kills that corner-bias
        while staying deterministic per seed (GAME-07): the randrange
        draw is consumed ONLY when the fallback fires (the MAX_DRAWS
        uniform draws precede it), so successful 32-draw sequences keep
        their exact pre-existing stream shape.

        Degenerate-box guard: a non-positive axis count (shrunk span <=
        0, e.g. the (0,0)-(2,2) test box: nx = ny = -1) returns None
        BEFORE any rng draw -- guarded on the AXIS counts, not on
        cell_count (nx*ny can be positive there, so a cell_count-only
        guard would not intercept).
        """
        x0, x1, y0, y1 = self._shrunk_bounds()
        nx = int((x1 - x0) / GRID_STEP_A + 1e-9) + 1
        ny = int((y1 - y0) / GRID_STEP_A + 1e-9) + 1
        if nx <= 0 or ny <= 0:
            return None
        cell_count = nx * ny
        start = self._rng.randrange(cell_count)
        for i in range(cell_count):
            idx = (start + i) % cell_count
            gx = x0 + (idx % nx) * GRID_STEP_A
            gy = y0 + (idx // nx) * GRID_STEP_A
            if self._legal(gx, gy, head_xy, atoms, chain_atoms,
                           live_centroids):
                return self._issue(record, gx, gy)
        return None

    def _legal(self, cx, cy, head_xy, atoms, chain_atoms, live_centroids):
        """All four clearance legs for one candidate centroid.

        Legs (a candidate failing ANY leg is rejected):
          1. shrunk-box containment (wall margin, inclusive bounds);
          2. head-centroid distance >= max(self._min_head_dist,
             HEAD_CLEARANCE_A) -- the box-proportional floor (2026-09-26
             Phase 5.3) subsumes the 5.0 A absolute hard floor on the
             real presets; tiny boxes fold the proportional value down
             so the floor stays HEAD_CLEARANCE_A (and h <= 0 folds it
             <= 0 -> the leg goes vacuous);
          3. every translated candidate atom >= CHAIN_ATOM_CLEARANCE_A
             (3.0 A) from every chain atom (xy plane);
          4. centroid distance >= LIVE_PICKUP_CLEARANCE_A (6.0 A) from
             every live pickup centroid.
        """
        # 1. Wall margin (shrunk box, inclusive).
        if not (self._box_min[0] + WALL_MARGIN_A <= cx
                <= self._box_max[0] - WALL_MARGIN_A):
            return False
        if not (self._box_min[1] + WALL_MARGIN_A <= cy
                <= self._box_max[1] - WALL_MARGIN_A):
            return False
        # 2. Head clearance: the box-proportional minimum with
        # HEAD_CLEARANCE_A as the absolute hard floor (max of the two).
        head_limit = self._min_head_dist
        if head_limit < HEAD_CLEARANCE_A:
            head_limit = HEAD_CLEARANCE_A
        head_dx = cx - head_xy[0]
        head_dy = cy - head_xy[1]
        if (head_dx * head_dx + head_dy * head_dy
                < head_limit * head_limit):
            return False
        # 3. Chain-atom clearance (candidate-translated atoms, xy).
        chain_sq = CHAIN_ATOM_CLEARANCE_A * CHAIN_ATOM_CLEARANCE_A
        if chain_atoms:
            for atom in atoms:
                tx = atom[1] + cx
                ty = atom[2] + cy
                for chain_atom in chain_atoms:
                    dx = tx - chain_atom[1]
                    dy = ty - chain_atom[2]
                    if dx * dx + dy * dy < chain_sq:
                        return False
        # 4. Live-pickup centroid clearance.
        live_sq = LIVE_PICKUP_CLEARANCE_A * LIVE_PICKUP_CLEARANCE_A
        for lx, ly in live_centroids:
            dx = cx - lx
            dy = cy - ly
            if dx * dx + dy * dy < live_sq:
                return False
        return True

    def _issue(self, record, cx, cy):
        """Accept a validated candidate: advance state, return the tuple.

        Rotates the serve order (front record to the back -- the
        round-robin advance) and consumes one pid serial. Runs ONLY on
        a returned spawn: a None result leaves order and pid untouched.
        """
        self._order.append(self._order.pop(0))
        self._issued += 1
        pid = 'pick_%04d' % self._issued
        return (record, pid, (cx, cy))
