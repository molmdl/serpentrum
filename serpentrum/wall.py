"""serpentrum.wall -- the PURE seeded random line-wall spawn policy (Phase 9).

2026-10-12 Phase 9 (owner request): seeded-random line-walls inside the
box, spawned together with each next mol, never overlapping it; private
random.Random + crc32 derived stream per GAME-07; spawn.py is untouched by
construction (the 5.3 isolation contract).

WHY A SEPARATE MODULE (do not merge into spawn.py):
``spawn.py`` is BYTE-IDENTICAL by contract (the verified 5.3 SC4 zero-edit
pin). The wall policy lives here and derives its OWN RNG stream from the
pickup seed -- ``crc32(pickup_seed|WALL_SALT)`` -- so pre/post-Phase-9
pickup replay is unchanged while walls feel random. The wall stream is
fully isolated: wall draws can never rotate pickup positions (pinned by
tests/test_wall.py TestStreamIsolation).

PINNED POLICY (stated explicitly per the planning mandate):

  - One wall per ``next_wall`` call: 3 seeded draws per attempt in a
    PINNED order -- anchor x uniform over the margin-shrunk box, anchor y
    likewise, then theta uniform over [0, pi) (an unoriented line, so an
    arbitrary angle suffices). Draws are consumed on EVERY attempt
    regardless of leg outcome (simpler than the pickup state-advance
    rules -- there is no record cycle to protect).
  - Length derives from the box: ``2 * half_len`` with
    ``half_len = 0.5 * WALL_LENGTH_FRACTION * min(x-span, y-span)``
    (never a hardcoded A literal -- the owner retune is a single edit).
  - Four clearance legs (a candidate failing ANY leg is redrawn):
    L1 both endpoints inside the margin-shrunk box on both axes;
    L2 every NEW-mol atom >= WALL_MOL_CLEARANCE_A from the segment (the
    owner no-overlap mandate, PER-ATOM, so the STRADDLE case -- a wall
    through one atom -- is rejected);
    L3 the head >= WALL_HEAD_CLEARANCE_A from the segment (launch safety);
    L4 every other live mol's atom >= WALL_LIVE_CLEARANCE_A.
  - 2026-10-14 Phase 9.1 (accumulating line-walls) amendments -- the
    spawner stays STATELESS about accumulation; the caller passes the
    accumulated set each call via the additive ``existing_walls=()`` input:
    * CAP GATE: ``len(existing_walls) >= WALL_MAX_LIVE_WALLS`` => None
      consuming ZERO draws (the degenerate-guard pattern) -- cap-then-stop:
      at the ceiling, captures keep spawning mols but add no walls.
    * TWO-TIER LENGTH: wall #1 (empty accumulated set) keeps
      WALL_LENGTH_FRACTION; walls #2+ draw
      WALL_ACCUM_LENGTH_FRACTION (still computed once per call).
    * L5: a candidate must additionally clear EVERY existing wall by
      >= WALL_WALL_CLEARANCE_A (true segment-segment via
      ``min_wall_clearance``; crossings and collinear overlaps rejected).
    * Determinism holds because ``existing_walls`` is a pure function of the
      same stream's prior draws (same seed + same set evolution => same set).
  - Exhaustion (WALL_MAX_DRAWS attempts, no legal candidate) => None: the
    CALLER keeps the previous walls (the accumulated set adds nothing -- a
    benign v1-look degradation; a wall is a bonus obstacle, not a required
    resource; there is deliberately NO grid-scan fallback). A degenerate box
    (shrunk interval empty on either axis) returns None IMMEDIATELY,
    consuming no draws.

Constants live in ONE tunable block below (the 5.1 SPEED_TIERS / 5.3
MIN_HEAD_DIST_FACTOR retune precedent): values are feel-check drafts, names
and seams are firm. Bumping WALL_SALT rotates the wall stream only.

ATOM-SHAPE CONTRACT (ONE shape across Phase 9 -- production feeds RAW):
sym-first 4-tuples ``(sym, x, y, z)`` read x=[1]/y=[2] (the seed/record
``'atoms'`` shape -- build_pickup_seed spawn.py:226-233, _mirror_atoms
gui_game.py:576-594); bare ``(x, y)`` / ``(x, y, z)`` tuples read
x=[0]/y=[1]. ``min_atom_clearance`` accepts both.

python3.6 syntax only (%-formatting, no f-strings); PURE module
(stdlib math/random/zlib + the PURE spawn module for the canonical seed
string ONLY -- no pymol / pmg_tk / PyQt5 / numpy anywhere; auto-classified
PURE by tools/check_purity.py, zero allowlist edits).
"""

import math
import random
import zlib

from . import spawn

# --- Pinned policy constants (Phase 9 plan 09-01; ONE tunable table) ------

WALL_LENGTH_FRACTION = 0.45    # fraction of the minor-axis box span
WALL_BOX_MARGIN_A = 6.0        # endpoint inset from every face (corridors:
                               # free width = margin - BOUNDARY 1.0 - halo
                               # 2.0 = 3.0 A at 6.0)
WALL_HEAD_CLEARANCE_A = 8.0    # launch safety: ~0.89 s reaction at the
                               # 9.0 A/s default, ~0.62 s at expert 13.0
WALL_MOL_CLEARANCE_A = 3.0     # per-atom vs the new mol (the chain-atom
                               # clearance value, spawn.py:118 precedent)
WALL_LIVE_CLEARANCE_A = 3.0    # per-atom vs other live mols
WALL_MAX_DRAWS = 32            # seeded attempts before None (no fallback)
WALL_SALT = 'wall-v1'          # bump to rotate the wall stream only
# --- Phase 9.1 accumulation policy (drafts -- owner retunes at 9.1-09) ----
WALL_MAX_LIVE_WALLS = 5        # accumulated-wall ceiling: at cap, captures
                               # keep spawning mols but add no walls (the
                               # spawn.MAX_LIVE_PICKUPS ceiling shape; owner
                               # feel-check grid 3/5/8)
WALL_ACCUM_LENGTH_FRACTION = 0.35  # length tier for walls #2+ (Phase-9's
                               # researched 'short' option: 24.5/38.5/59.5 A
                               # on S/M/L boxes; wall #1 keeps
                               # WALL_LENGTH_FRACTION 0.45 -- grid
                               # 0.25/0.35/0.45=full)
WALL_WALL_CLEARANCE_A = 8.0    # L5: a new wall keeps this far from every
                               # existing wall (true segment-segment,
                               # crossings rejected; usable between-wall
                               # corridor = 8.0 - 2x2.0 halo = 4.0 A --
                               # grid 6/8/12)


def wall_seed_from_setup(setup):
    """Derived, process-stable wall seed for a setup dict -> int.

    Chains through ``spawn.seed_from_setup`` (the canonical crc32 setup
    string) and salts it -- ``zlib.crc32`` over
    ``'%d|%s' % (pickup_seed, WALL_SALT)`` -- so the wall RNG stream is
    DISTINCT from the pickup stream (GAME-07 restart determinism intact;
    NEVER hash()).
    """
    pickup_seed = spawn.seed_from_setup(setup)
    return zlib.crc32(('%d|%s' % (pickup_seed, WALL_SALT)).encode('utf-8'))


def _point_segment_distance_sq(px, py, ax, ay, bx, by):
    """Squared point-to-segment distance (identical clamped-projection
    contract to game_engine's collision helper; the degenerate a==b case is
    handled). Kept LOCAL so the wall spawner stays self-contained -- the
    ENGINE's collision leg keeps its own copy (09-02)."""
    dx = bx - ax
    dy = by - ay
    seg_sq = dx * dx + dy * dy
    if seg_sq <= 0.0:
        ex = px - ax
        ey = py - ay
        return ex * ex + ey * ey
    t = ((px - ax) * dx + (py - ay) * dy) / seg_sq
    if t < 0.0:
        t = 0.0
    elif t > 1.0:
        t = 1.0
    cx = ax + t * dx
    cy = ay + t * dy
    ex = px - cx
    ey = py - cy
    return ex * ex + ey * ey


def _atom_xy(atom):
    """(x, y) for an atom in either repo shape (see module docstring)."""
    if len(atom) == 4:
        return (atom[1], atom[2])
    return (atom[0], atom[1])


def min_atom_clearance(endpoints, atoms):
    """Min over ``atoms`` of the SQRT distance to the segment ``endpoints``.

    The single per-atom point-segment source shared with the future
    controller DBG gap (09-07). ``endpoints`` is ``((ax, ay), (bx, by))``;
    ``atoms`` may mix the two repo shapes (sym-first 4-tuples read
    x=[1]/y=[2]; bare 2-/3-tuples read x=[0]/y=[1]). Returns the minimum
    distance (a float), NOT squared. Empty ``atoms`` -> ValueError (a loud
    programming-error tripwire; ``next_wall``'s L4 guards emptiness itself
    -- ``live_mol_atoms`` may legitimately be empty). PURE.
    """
    if not atoms:
        raise ValueError('min_atom_clearance requires at least one atom')
    (ax, ay), (bx, by) = endpoints
    best = None
    for atom in atoms:
        px, py = _atom_xy(atom)
        dist = math.sqrt(_point_segment_distance_sq(px, py, ax, ay, bx, by))
        if best is None or dist < best:
            best = dist
    return best


def _segment_segment_distance(ax, ay, bx, by, cx, cy, dx, dy):
    """SQRT min distance between segment (a, b) and segment (c, d).

    The Phase-9.1 wall-vs-wall geometry: a proper crossing returns 0.0, a
    collinear overlap (or a shared/touching endpoint) returns 0.0, and
    otherwise the min over the four endpoint-to-other-segment distances
    (degenerate zero-length segments fall out naturally). PURE.
    """
    # The four orientation cross products of the two segments.
    d1 = (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)
    d2 = (bx - ax) * (dy - ay) - (by - ay) * (dx - ax)
    d3 = (dx - cx) * (ay - cy) - (dy - cy) * (ax - cx)
    d4 = (dx - cx) * (by - cy) - (dy - cy) * (bx - cx)
    # Proper crossing (each segment straddles the other's line).
    if d1 * d2 < 0.0 and d3 * d4 < 0.0:
        return 0.0
    # Collinear (all four orientations exactly zero): a 1-D projection-
    # overlap test decides touch (0.0) vs disjoint.
    if d1 == 0.0 and d2 == 0.0 and d3 == 0.0 and d4 == 0.0:
        ux = bx - ax
        uy = by - ay
        if ux == 0.0 and uy == 0.0:
            ux = dx - cx
            uy = dy - cy
        if not (ux == 0.0 and uy == 0.0):
            ta = ax * ux + ay * uy
            tb = bx * ux + by * uy
            tc = cx * ux + cy * uy
            td = dx * ux + dy * uy
            lo1, hi1 = (ta, tb) if ta <= tb else (tb, ta)
            lo2, hi2 = (tc, td) if tc <= td else (td, tc)
            if max(lo1, lo2) <= min(hi1, hi2):
                return 0.0
    # Min over the four endpoint-to-other-segment distances.
    best_sq = _point_segment_distance_sq(ax, ay, cx, cy, dx, dy)
    for px, py, ex, ey, fx, fy in (
            (bx, by, cx, cy, dx, dy),
            (cx, cy, ax, ay, bx, by),
            (dx, dy, ax, ay, bx, by)):
        sq = _point_segment_distance_sq(px, py, ex, ey, fx, fy)
        if sq < best_sq:
            best_sq = sq
    return math.sqrt(best_sq)


def min_wall_clearance(endpoints, existing_walls):
    """Min SQRT segment-segment distance from ``endpoints`` to the walls.

    The Phase-9.1 L5 fairness leg: a newly drawn wall must keep at least
    ``WALL_WALL_CLEARANCE_A`` from every already-accumulated wall. True
    segment-segment distance -- a proper crossing returns 0.0, as does a
    collinear overlap or a touching endpoint (so near-coincident double
    lines and X-crossings are rejected). ``existing_walls`` is a sequence of
    ``((ax, ay), (bx, by))`` segment pairs. Returns the minimum distance
    (a float), NOT squared. Empty ``existing_walls`` -> ValueError (the
    ``min_atom_clearance`` tripwire contract; ``next_wall`` guards emptiness
    itself -- it only calls this when the accumulated set is non-empty).
    Docstring consumer: the future controller DBG ``wwgap`` audit line
    (9.1-07). PURE.
    """
    if not existing_walls:
        raise ValueError('min_wall_clearance requires at least one wall')
    (ax, ay), (bx, by) = endpoints
    best = None
    for wall in existing_walls:
        (cx, cy), (dx, dy) = wall
        dist = _segment_segment_distance(ax, ay, bx, by, cx, cy, dx, dy)
        if best is None or dist < best:
            best = dist
    return best


class WallSpawner(object):
    """Seeded, four-leg-validated random line-wall spawner.

    Parameters:

      box_min:  (x0, y0) box lower corner (setup_logic.BOX_PRESETS).
      box_max:  (x1, y1) box upper corner.
      seed:     int (see wall_seed_from_setup) feeding a PRIVATE
                random.Random -- never the global random module.
      wall_box_margin_a:    override for WALL_BOX_MARGIN_A (endpoint inset).
      wall_head_clearance_a: override for WALL_HEAD_CLEARANCE_A (L3).
      length_fraction:      override for WALL_LENGTH_FRACTION.
      max_draws:            seeded attempts before None (default
                            WALL_MAX_DRAWS).
      accum_length_fraction: override for WALL_ACCUM_LENGTH_FRACTION (the
                            length tier for walls #2+; 9.1).
      wall_wall_clearance_a: override for WALL_WALL_CLEARANCE_A (L5; 9.1).
      max_live_walls:       override for WALL_MAX_LIVE_WALLS (the cap gate;
                            9.1).

    All overrides feed read-only effective-value properties (tests / GUI
    introspection), mirroring spawn.PickupSpawner's introspection style
    (spawn.py:328-345).
    """

    def __init__(self, box_min, box_max, seed, wall_box_margin_a=None,
                 wall_head_clearance_a=None, length_fraction=None,
                 max_draws=WALL_MAX_DRAWS, accum_length_fraction=None,
                 wall_wall_clearance_a=None, max_live_walls=None):
        self._box_min = (float(box_min[0]), float(box_min[1]))
        self._box_max = (float(box_max[0]), float(box_max[1]))
        if wall_box_margin_a is not None:
            self._wall_box_margin = float(wall_box_margin_a)
        else:
            self._wall_box_margin = WALL_BOX_MARGIN_A
        if wall_head_clearance_a is not None:
            self._wall_head_clearance = float(wall_head_clearance_a)
        else:
            self._wall_head_clearance = WALL_HEAD_CLEARANCE_A
        if length_fraction is not None:
            self._length_fraction = float(length_fraction)
        else:
            self._length_fraction = WALL_LENGTH_FRACTION
        if accum_length_fraction is not None:
            self._accum_length_fraction = float(accum_length_fraction)
        else:
            self._accum_length_fraction = WALL_ACCUM_LENGTH_FRACTION
        if wall_wall_clearance_a is not None:
            self._wall_wall_clearance = float(wall_wall_clearance_a)
        else:
            self._wall_wall_clearance = WALL_WALL_CLEARANCE_A
        if max_live_walls is not None:
            self._max_live_walls = int(max_live_walls)
        else:
            self._max_live_walls = WALL_MAX_LIVE_WALLS
        self._max_draws = int(max_draws)
        self._rng = random.Random(seed)

    # --- read-only effective-value introspection ---------------------

    @property
    def box_min(self):
        """The box lower corner (x0, y0). Read-only."""
        return self._box_min

    @property
    def box_max(self):
        """The box upper corner (x1, y1). Read-only."""
        return self._box_max

    @property
    def wall_box_margin(self):
        """The effective endpoint inset (L1). Read-only."""
        return self._wall_box_margin

    @property
    def wall_head_clearance(self):
        """The effective head-to-segment clearance (L3). Read-only."""
        return self._wall_head_clearance

    @property
    def length_fraction(self):
        """The effective segment-length fraction of the minor span."""
        return self._length_fraction

    @property
    def max_draws(self):
        """The seeded attempts allowed before None. Read-only."""
        return self._max_draws

    @property
    def accum_length_fraction(self):
        """The effective length fraction for walls #2+ (9.1 tier). Read-only."""
        return self._accum_length_fraction

    @property
    def wall_wall_clearance(self):
        """The effective candidate-vs-existing-set clearance (L5). Read-only."""
        return self._wall_wall_clearance

    @property
    def max_live_walls(self):
        """The accumulated-wall ceiling (the cap gate). Read-only."""
        return self._max_live_walls

    # --- public API -------------------------------------------------

    def next_wall(self, head_xy, new_mol_atoms, live_mol_atoms,
                  existing_walls=()):
        """Sample one legal line-wall, or None on exhaustion / at the cap.

        ``head_xy``: (x, y) of the head (L3 origin). ``new_mol_atoms``:
        the freshly spawned mol's raw atoms (REQUIRED -- a spawn always has
        a mol; empty -> ValueError). ``live_mol_atoms``: every OTHER live
        mol's raw atoms (may be empty -- L4 is skipped then).
        ``existing_walls``: the already-accumulated wall set the caller
        holds (9.1); each entry is ``((ax, ay), (bx, by))`` (may be empty /
        defaulted -- Phase-9 parity).

        Returns ``((ax, ay), (bx, by))`` -- the wall segment endpoints -- or
        None when no candidate survived WALL_MAX_DRAWS attempts (the caller
        keeps the previous walls; the accumulated set adds nothing), or when
        ``len(existing_walls) >= WALL_MAX_LIVE_WALLS`` (the cap gate; None
        consuming ZERO draws -- the degenerate-guard pattern).

        Two length tiers: with an empty accumulated set the wall uses
        ``WALL_LENGTH_FRACTION`` (the shipped Phase-9 look); with a non-empty
        set it uses ``WALL_ACCUM_LENGTH_FRACTION`` (walls #2+). A fifth
        clearance leg L5 (9.1) additionally requires the candidate to clear
        every existing wall by >= ``WALL_WALL_CLEARANCE_A`` (true
        segment-segment; crossings rejected). Deterministic per (seed, call
        sequence, accumulated-set evolution).
        """
        if not new_mol_atoms:
            raise ValueError('next_wall requires new_mol_atoms '
                             '(a spawn always has a mol)')
        walls = list(existing_walls) if existing_walls else []
        x0, y0 = self._box_min
        x1, y1 = self._box_max
        margin = self._wall_box_margin
        # Degenerate-box guard: shrunk interval empty on either axis =>
        # None immediately, NO draws consumed (spawn.py precedent).
        if (x1 - x0) < 2.0 * margin or (y1 - y0) < 2.0 * margin:
            return None
        # Cap gate: at/above the accumulated-wall ceiling => None BEFORE any
        # draw (the degenerate-guard zero-draw pattern).
        if len(walls) >= self._max_live_walls:
            return None
        sx0 = x0 + margin
        sx1 = x1 - margin
        sy0 = y0 + margin
        sy1 = y1 - margin
        # Length is fixed per call (computed once, outside the loop); the
        # tier depends on whether the accumulated set is empty.
        if walls:
            fraction = self._accum_length_fraction
        else:
            fraction = self._length_fraction
        half_len = 0.5 * fraction * min(x1 - x0, y1 - y0)
        head_sq = self._wall_head_clearance * self._wall_head_clearance
        for _ in range(self._max_draws):
            # 3 seeded draws per attempt, PINNED order: anchor x, anchor
            # y, theta. Consumed regardless of leg outcome.
            cx = self._rng.uniform(sx0, sx1)
            cy = self._rng.uniform(sy0, sy1)
            theta = self._rng.uniform(0.0, math.pi)
            cos_t = math.cos(theta)
            sin_t = math.sin(theta)
            ax = cx - half_len * cos_t
            ay = cy - half_len * sin_t
            bx = cx + half_len * cos_t
            by = cy + half_len * sin_t
            # L1: both endpoints inside the margin-shrunk box on both axes.
            if ax < sx0 or ax > sx1 or ay < sy0 or ay > sy1:
                continue
            if bx < sx0 or bx > sx1 or by < sy0 or by > sy1:
                continue
            endpoints = ((ax, ay), (bx, by))
            # L2: every new-mol atom >= WALL_MOL_CLEARANCE_A (PER-ATOM).
            if (min_atom_clearance(endpoints, new_mol_atoms)
                    < WALL_MOL_CLEARANCE_A):
                continue
            # L3: the head >= WALL_HEAD_CLEARANCE_A (squared compare).
            if _point_segment_distance_sq(head_xy[0], head_xy[1],
                                          ax, ay, bx, by) < head_sq:
                continue
            # L4: every other live mol's atom >= WALL_LIVE_CLEARANCE_A.
            if live_mol_atoms:
                if (min_atom_clearance(endpoints, live_mol_atoms)
                        < WALL_LIVE_CLEARANCE_A):
                    continue
            # L5 (9.1): clear every existing accumulated wall.
            if walls:
                if (min_wall_clearance(endpoints, walls)
                        < self._wall_wall_clearance):
                    continue
            return ((float(ax), float(ay)), (float(bx), float(by)))
        return None
