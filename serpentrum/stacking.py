"""Stacking math: ring frames, rigid-body pi-stack placement, clash gate.

PURE module (stdlib ``math`` only -- no pymol/pmg_tk/PyQt5/numpy anywhere;
enforced by tools/check_purity.py, which auto-classifies this file PURE).

Data-driven placement math for STACK-01/02/05 and phase success criterion 1:
a deterministic rigid-body transform that places a "pickup" molecule into a
pi-stacking pose above a "tail" molecule, proven by EXACTLY reproducing the
committed pi-stacked phenol dimer fixture
(``research/xtb-spike-fixtures/dimer2.xyz``: fragment2 == fragment1 +
(0, 0, 3.4), max error 0.0 -- an ECLIPSED pure z-translation).

Three public callables:

- ``ring_frame(atoms, ring_indices)`` -- deterministic orthonormal frame for
  a planar ring subset: (centroid, unit normal, in-plane reference axis).
- ``place_pickup(...)`` -- rigid transform mapping the pickup's ring frame
  onto the tail's (parallel planes, azimuth=0, optional lateral offset).
  Returns ``(placed_atoms, R, t)`` with ``placed = R.p + t``; R and t are
  what the Phase-5 connector feeds ``cmd.transform_selection`` (the exact
  matrix layout that PyMOL expects is flagged OPEN in ARCHITECTURE.md
  section 9 and MUST be verified in Phase 5 against editing.py before
  wiring).
- ``check_clash(...)`` -- pure clash gate: None when clear, else a
  diagnostic dict for the first violation (wall check first, then atoms).

Conventions (verified, see .planning/phases/02-RESEARCH-*.md):
- All vectors are plain 3-tuples of floats; WSL python3.6.9 has no numpy.
- The reference axis (centroid -> FIRST ring atom, orthogonalized against
  the normal) defines azimuth=0. Same molecule in the same conformer =>
  same frame in both fragments (verified on dimer2) => azimuth=0 makes the
  eclipsed dimer exactly reproducible.
- Normal sign is preserved: stacking "above" vs "below" is the caller's
  sign choice on tail_normal.
"""
import math

# STACK-05 clash threshold (Angstrom). xtb infers covalent bonds from rcov
# sums; the maximum rcov sum for the demo elements is ~C+H 1.07 / C+C 1.52 /
# C+O 1.42 A and xtb's tolerance multiplies by ~1.3, so the spurious-bond
# risk ceiling is ~1.9-2.0 A. The verified-safe floor is the committed
# dimer's clean 3.4000 A optimization (research/xtb-spike-fixtures/
# dimer2.xyz; [RUN] evidence in 02-RESEARCH-pure-core.md). 2.5 sits between
# with >= 0.5 A margin both ways. Module constant, not a user setting (v1).
CLASH_THRESHOLD_A = 2.5

# Ring planarity tolerance (A). dimer2's rings are planar to ~2.8e-10 A;
# 0.15 A absorbs real ring puckering while still rejecting genuinely
# non-planar subsets (one atom displaced 0.5 A on a r=1.4 hexagon deviates
# ~0.248 A). Biphenyl handles this by listing ONE ring's atoms in the
# manifest.
PLANARITY_TOL_A = 0.15


def _sub(a, b):
    """Component-wise a - b."""
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _add(a, b):
    """Component-wise a + b."""
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _scale(a, s):
    """Component-wise a * s."""
    return (a[0] * s, a[1] * s, a[2] * s)


def _dot(a, b):
    """Dot product a . b."""
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a, b):
    """Cross product a x b."""
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _norm(a):
    """Euclidean length |a|."""
    return math.sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2])


def _unit(a):
    """Unit vector along a (raises on zero-length input)."""
    length = _norm(a)
    if length == 0.0:
        raise ValueError('cannot unit-normalize zero-length vector')
    return (a[0] / length, a[1] / length, a[2] / length)


def ring_frame(atoms, ring_indices):
    """Deterministic orthonormal frame for a planar ring subset.

    atoms: sequence of (x, y, z) floats (the full molecule's coordinates).
    ring_indices: indices into atoms of the ring atoms, IN RING ORDER
    (the Newell normal is order-stable; reversing the order flips the
    normal's sign).

    Returns (centroid, normal_unit, ref_unit):
    - centroid: mean of the selected atoms.
    - normal_unit: Newell's method over the selected atoms in the given
      index order (order-stable, no degenerate cross products), then
      unit-normalized.
    - ref_unit: unit vector centroid -> FIRST ring atom, orthogonalized
      against the normal. Defines azimuth=0 for place_pickup.

    Raises ValueError with a descriptive message on: fewer than 3 ring
    atoms; a degenerate ring (Newell normal length ~0, e.g. collinear
    points); a non-planar ring (max |dot(p - centroid, normal)| exceeds
    PLANARITY_TOL_A); or a degenerate reference axis (first ring atom on
    the normal axis through the centroid).
    """
    count = len(ring_indices)
    if count < 3:
        raise ValueError('ring needs >= 3 atoms (got %d)' % count)

    points = []
    for idx in ring_indices:
        p = atoms[idx]
        points.append((float(p[0]), float(p[1]), float(p[2])))

    sx = sy = sz = 0.0
    for p in points:
        sx += p[0]
        sy += p[1]
        sz += p[2]
    centroid = (sx / count, sy / count, sz / count)

    # Newell's method over consecutive pairs in the GIVEN index order.
    nx = ny = nz = 0.0
    for i in range(count):
        p = points[i]
        q = points[(i + 1) % count]
        nx += (p[1] - q[1]) * (p[2] + q[2])
        ny += (p[2] - q[2]) * (p[0] + q[0])
        nz += (p[0] - q[0]) * (p[1] + q[1])
    normal_len = math.sqrt(nx * nx + ny * ny + nz * nz)
    if normal_len < 1e-8:
        raise ValueError('degenerate ring (normal length %.3e)' % normal_len)
    normal = (nx / normal_len, ny / normal_len, nz / normal_len)

    max_dev = 0.0
    for p in points:
        dev = abs(_dot(_sub(p, centroid), normal))
        if dev > max_dev:
            max_dev = dev
    if max_dev > PLANARITY_TOL_A:
        raise ValueError('non-planar ring (max deviation %.3f A)' % max_dev)

    v = _sub(points[0], centroid)
    r = _sub(v, _scale(normal, _dot(v, normal)))
    r_len = _norm(r)
    if r_len < 1e-8:
        raise ValueError('degenerate ring reference axis (length %.3e)'
                         % r_len)
    ref = (r[0] / r_len, r[1] / r_len, r[2] / r_len)

    return (centroid, normal, ref)


def _orthonormal_basis(normal, ref):
    """Right-handed basis (r1, r2, n) with r1 x r2 = n.

    normal is unit-normalized; ref is orthogonalized against the normal
    and unit-normalized (idempotent for an already-orthogonal ref).
    Raises ValueError when ref is (nearly) parallel to the normal.
    """
    n = _unit(normal)
    v = _sub(ref, _scale(n, _dot(ref, n)))
    r1_len = _norm(v)
    if r1_len < 1e-8:
        raise ValueError('degenerate reference axis (length %.3e)' % r1_len)
    r1 = (v[0] / r1_len, v[1] / r1_len, v[2] / r1_len)
    r2 = _cross(n, r1)
    return (r1, r2, n)


def place_pickup(pickup_atoms, pickup_ring_indices,
                 tail_centroid, tail_normal, tail_ref,
                 distance_a, lateral_offset_a, lateral_along_ref=True):
    """Place the pickup molecule into a pi-stacking pose on the tail frame.

    pickup_atoms: sequence of (x, y, z) floats -- ALL of the pickup's
    atoms (they are transformed rigidly, not just the ring).
    pickup_ring_indices: indices into pickup_atoms of ONE planar ring,
    in ring order (fed to ring_frame internally).
    tail_centroid / tail_normal / tail_ref: the tail's ring frame, as
    returned by ring_frame on the tail molecule.
    distance_a: separation of the two ring centroids along the tail
    normal (plane-to-plane distance for parallel planes).
    lateral_offset_a: shift of the target centroid within the stacked
    plane, along the tail reference axis (lateral_along_ref=True) or
    along cross(tail_normal, tail_ref) (False). The plane distance is
    unchanged by either.

    Determinism contract (what makes dimer2 exactly reproducible):
    - azimuth = 0: the pickup's reference axis is aligned with the
      tail's projected reference axis. Same molecule in the same
      conformer => identical frames => the transform reduces to a pure
      translation along the normal (the committed dimer's case).
    - normal sign preserved: stacking "above" vs "below" is the
      caller's sign choice on tail_normal.

    Returns (placed_atoms, R, t):
    - placed_atoms: list of (x, y, z) tuples, one per pickup atom;
    - R: the 3x3 rotation, row-major tuple of row-tuples, mapping world
      vectors from the pickup frame to the tail frame (identity when
      the frames coincide);
    - t: translation with placed = R.p + t.
    R and t are what the Phase-5 connector feeds cmd.transform_selection
    (matrix layout convention flagged OPEN -- verify in Phase 5).
    """
    c_pick, n_pick, p1 = ring_frame(pickup_atoms, pickup_ring_indices)
    p2 = _cross(n_pick, p1)

    r1, r2, n_t = _orthonormal_basis(tail_normal, tail_ref)

    # R = B_tail . B_pick^T with basis vectors as columns:
    # R[i][j] = r1[i]*p1[j] + r2[i]*p2[j] + n_t[i]*n_pick[j].
    rows = []
    for i in range(3):
        rows.append((r1[i] * p1[0] + r2[i] * p2[0] + n_t[i] * n_pick[0],
                     r1[i] * p1[1] + r2[i] * p2[1] + n_t[i] * n_pick[1],
                     r1[i] * p1[2] + r2[i] * p2[2] + n_t[i] * n_pick[2]))
    rot = tuple(rows)

    if lateral_along_ref:
        lateral = _scale(r1, lateral_offset_a)
    else:
        lateral = _scale(r2, lateral_offset_a)
    target = _add(_add(tail_centroid, _scale(n_t, distance_a)), lateral)

    placed = []
    for p in pickup_atoms:
        d = _sub((float(p[0]), float(p[1]), float(p[2])), c_pick)
        placed.append((rot[0][0] * d[0] + rot[0][1] * d[1] +
                       rot[0][2] * d[2] + target[0],
                       rot[1][0] * d[0] + rot[1][1] * d[1] +
                       rot[1][2] * d[2] + target[1],
                       rot[2][0] * d[0] + rot[2][1] * d[1] +
                       rot[2][2] * d[2] + target[2]))

    # t = target - R.c_pick, so that placed = R.p + t exactly.
    t = (target[0] - (rot[0][0] * c_pick[0] + rot[0][1] * c_pick[1] +
                      rot[0][2] * c_pick[2]),
         target[1] - (rot[1][0] * c_pick[0] + rot[1][1] * c_pick[1] +
                      rot[1][2] * c_pick[2]),
         target[2] - (rot[2][0] * c_pick[0] + rot[2][1] * c_pick[1] +
                      rot[2][2] * c_pick[2]))

    return (placed, rot, t)


def check_clash(placed_atoms, existing_atoms, box_min, box_max,
                threshold_a=CLASH_THRESHOLD_A):
    """Pure clash gate (STACK-05): None when clear, else first violation.

    placed_atoms: the newly placed atoms to admit.
    existing_atoms: the already-placed geometry to stay clear of.
    box_min / box_max: 3-tuples, inclusive axis bounds (the game's
    z-extent is display-only but the gate checks all three axes).
    threshold_a: minimum allowed placed-vs-existing distance; defaults
    to the module constant CLASH_THRESHOLD_A (2.5 A -- see the rationale
    above; xtb infers spurious covalent bonds below ~2.0 A while the
    verified legal pi-stack sits at 3.4 A).

    Returns None, or a diagnostic dict for the FIRST violation:
    - wall test first (cheaper, deterministic): any placed coordinate
      strictly outside [box_min, box_max] -> {'kind': 'wall',
      'pair': (i, None), 'distance': largest violation amount over all
      violating axes of the first violating atom (i ascending)}. A
      coordinate exactly ON a boundary is legal (inclusive).
    - atom test: first (i, j) pair (i ascending, then j ascending) with
      euclidean distance < threshold_a -> {'kind': 'atom',
      'pair': (i, j), 'distance': d}.
    """
    for i, p in enumerate(placed_atoms):
        worst = 0.0
        for k in range(3):
            coord = p[k]
            if coord < box_min[k]:
                violation = box_min[k] - coord
            elif coord > box_max[k]:
                violation = coord - box_max[k]
            else:
                continue
            if violation > worst:
                worst = violation
        if worst > 0.0:
            return {'kind': 'wall', 'pair': (i, None), 'distance': worst}

    for i, p in enumerate(placed_atoms):
        for j, q in enumerate(existing_atoms):
            dx = p[0] - q[0]
            dy = p[1] - q[1]
            dz = p[2] - q[2]
            dist = math.sqrt(dx * dx + dy * dy + dz * dz)
            if dist < threshold_a:
                return {'kind': 'atom', 'pair': (i, j), 'distance': dist}

    return None
