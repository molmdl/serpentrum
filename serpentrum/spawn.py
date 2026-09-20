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
  - POSITION: LOOKAHEAD_A = 8.0 along the current heading plus a seeded
    lateral offset in [-6.0, +6.0] quantized to 0.1 A, validated
    against: wall margin 3.5 A (shrunk box), head-centroid clearance
    5.0 A, chain-ATOM clearance 3.0 A (originally sized to keep the
    since-REMOVED 2.5 A sweep pickup-leg pre-check satisfiable near
    fresh spawns; kept 2026-09-20 as good placement hygiene), and
    live-pickup-centroid clearance 6.0 A. Up to 32
    seeded retries (MAX_DRAWS), then a DETERMINISTIC grid-scan fallback
    (GRID_STEP_A = 2.0 over the shrunk box, x-major / y-minor order,
    first legal wins), else None. On None there is NO state advance --
    the same record is offered again on the next call, and the pid
    counter is not consumed.
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
LOOKAHEAD_A = 8.0             # candidate lead along the current heading
LATERAL_MAX_A = 6.0           # seeded lateral offset in +/- this range
LATERAL_QUANTUM_A = 0.1       # lateral quantization step
WALL_MARGIN_A = 3.5           # shrunk-box containment margin
HEAD_CLEARANCE_A = 5.0        # centroid distance from the head
CHAIN_ATOM_CLEARANCE_A = 3.0  # per-atom distance vs chain atoms (> 2.5 A
                              # — sized against the since-REMOVED
                              # game_engine.SWEEP_PICKUP_CLEARANCE_A sweep
                              # pickup leg; kept as spawn hygiene 2026-09-20)
LIVE_PICKUP_CLEARANCE_A = 6.0  # centroid distance vs live pickups
MAX_DRAWS = 32                # seeded retries before the grid-scan fallback
GRID_STEP_A = 2.0             # deterministic fallback scan step

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

    State: cycle index over records + a spawn counter (pids
    'pick_0001', 'pick_0002', ...). Both advance ONLY on a returned
    spawn -- an exhausted (None) call replays the same record and the
    same pid on the next call.
    """

    def __init__(self, records, box_min, box_max, seed, atoms_by_id):
        self._records = list(records)
        self._box_min = (float(box_min[0]), float(box_min[1]))
        self._box_max = (float(box_max[0]), float(box_max[1]))
        self._rng = random.Random(seed)
        self._atoms_by_id = atoms_by_id
        self._cycle = 0
        self._issued = 0

    # --- public API -------------------------------------------------

    def can_spawn(self, live_count):
        """MAX_LIVE gate: True while live_count < MAX_LIVE_PICKUPS (4)."""
        return live_count < MAX_LIVE_PICKUPS

    def first(self, head_xy, heading):
        """Spawn the initial pickup (begin_game): no chain, no live."""
        return self._spawn(head_xy, heading, (), ())

    def next_after(self, head_xy, heading, chain_atoms, live_centroids):
        """Spawn the next pickup after one capture resolution.

        ``chain_atoms``: every chain atom so far (head molecule atoms +
        every attached segment's atoms, (sym, x, y, z) shape) -- the
        per-atom clearance leg keeps fresh spawns out of the snake.
        ``live_centroids``: (x, y) pairs of pickups currently live --
        the 6.0 A centroid spacing leg. Returns the same
        ``(record, pid, centroid)`` 3-tuple as ``first``, or None when
        no legal position exists (NO state advance on None).
        """
        return self._spawn(head_xy, heading, chain_atoms, live_centroids)

    # --- internals --------------------------------------------------

    def _spawn(self, head_xy, heading, chain_atoms, live_centroids):
        if not self._records:
            return None
        if heading not in _DIRS:
            raise ValueError('unknown heading: %r (valid: %s)'
                             % (heading, ', '.join(sorted(_DIRS))))
        ux, uy = _DIRS[heading]
        # Perpendicular (CCW): for (ux, uy) -> (-uy, ux). 'right' gives
        # (0, 1): laterals run along +y. One fixed convention, captured
        # in the seed stream, is all determinism needs.
        px, py = -uy, ux
        record = self._records[self._cycle % len(self._records)]
        atoms = self._atoms_by_id[record['id']]
        base_x = head_xy[0] + ux * LOOKAHEAD_A
        base_y = head_xy[1] + uy * LOOKAHEAD_A
        for _ in range(MAX_DRAWS):
            lateral = self._draw_lateral()
            cx = base_x + px * lateral
            cy = base_y + py * lateral
            if self._legal(cx, cy, head_xy, atoms, chain_atoms,
                           live_centroids):
                return self._issue(record, cx, cy)
        # Deterministic grid-scan fallback over the shrunk box, x-major /
        # y-minor order, FIRST legal wins. Fully deterministic for fixed
        # (head, chain, live) inputs -- no RNG involved.
        x0 = self._box_min[0] + WALL_MARGIN_A
        x1 = self._box_max[0] - WALL_MARGIN_A
        y0 = self._box_min[1] + WALL_MARGIN_A
        y1 = self._box_max[1] - WALL_MARGIN_A
        gx = x0
        while gx <= x1 + 1e-9:
            gy = y0
            while gy <= y1 + 1e-9:
                if self._legal(gx, gy, head_xy, atoms, chain_atoms,
                               live_centroids):
                    return self._issue(record, gx, gy)
                gy += GRID_STEP_A
            gx += GRID_STEP_A
        return None

    def _draw_lateral(self):
        """One seeded lateral draw in [-6.0, +6.0], 0.1-quantized."""
        raw = self._rng.uniform(-LATERAL_MAX_A, LATERAL_MAX_A)
        return round(raw / LATERAL_QUANTUM_A) * LATERAL_QUANTUM_A

    def _legal(self, cx, cy, head_xy, atoms, chain_atoms, live_centroids):
        """All four clearance legs for one candidate centroid.

        Legs (a candidate failing ANY leg is rejected):
          1. shrunk-box containment (wall margin, inclusive bounds);
          2. head-centroid distance >= HEAD_CLEARANCE_A (5.0 A);
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
        # 2. Head clearance.
        head_dx = cx - head_xy[0]
        head_dy = cy - head_xy[1]
        if (head_dx * head_dx + head_dy * head_dy
                < HEAD_CLEARANCE_A * HEAD_CLEARANCE_A):
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
        """Accept a validated candidate: advance state, return the tuple."""
        self._cycle += 1
        self._issued += 1
        pid = 'pick_%04d' % self._issued
        return (record, pid, (cx, cy))
