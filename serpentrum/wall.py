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
  - Exhaustion (WALL_MAX_DRAWS attempts, no legal candidate) => None: the
    CALLER keeps the previous wall (a benign v1-look degradation -- a wall
    is a bonus obstacle, not a required resource; there is deliberately NO
    grid-scan fallback). A degenerate box (shrunk interval empty on either
    axis) returns None IMMEDIATELY, consuming no draws.

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

    All four overrides feed read-only effective-value properties (tests /
    GUI introspection), mirroring spawn.PickupSpawner's introspection style
    (spawn.py:328-345).
    """

    def __init__(self, box_min, box_max, seed, wall_box_margin_a=None,
                 wall_head_clearance_a=None, length_fraction=None,
                 max_draws=WALL_MAX_DRAWS):
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

    # --- public API -------------------------------------------------

    def next_wall(self, head_xy, new_mol_atoms, live_mol_atoms):
        """Sample one legal line-wall, or None on exhaustion.

        ``head_xy``: (x, y) of the head (L3 origin). ``new_mol_atoms``:
        the freshly spawned mol's raw atoms (REQUIRED -- a spawn always has
        a mol; empty -> ValueError). ``live_mol_atoms``: every OTHER live
        mol's raw atoms (may be empty -- L4 is skipped then).

        Returns ``((ax, ay), (bx, by))`` -- the wall segment endpoints -- or
        None when no candidate survived WALL_MAX_DRAWS attempts (the caller
        keeps the previous wall). Deterministic per (seed, call sequence).
        """
        if not new_mol_atoms:
            raise ValueError('next_wall requires new_mol_atoms '
                             '(a spawn always has a mol)')
        x0, y0 = self._box_min
        x1, y1 = self._box_max
        margin = self._wall_box_margin
        # Degenerate-box guard: shrunk interval empty on either axis =>
        # None immediately, NO draws consumed (spawn.py precedent).
        if (x1 - x0) < 2.0 * margin or (y1 - y0) < 2.0 * margin:
            return None
        sx0 = x0 + margin
        sx1 = x1 - margin
        sy0 = y0 + margin
        sy1 = y1 - margin
        # Length is fixed per call (computed once, outside the loop).
        half_len = 0.5 * self._length_fraction * min(x1 - x0, y1 - y0)
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
            return ((float(ax), float(ay)), (float(bx), float(by)))
        return None
