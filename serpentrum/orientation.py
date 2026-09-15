"""Edge-on orientation math + the verified PyMOL TTT matrix builder (G5).

PURE module (stdlib only -- no pymol/pmg_tk/PyQt5/numpy anywhere;
auto-classified PURE by tools/check_purity.py, no registration needed).
python3.6 syntax only (no f-strings).

VERIFIED MATRIX VERDICT: ``cmd.transform_selection`` in PyMOL 2.5.0 accepts
16 floats where rows 0-2 cols 0-2 hold a row-major 3x3 R applied to the
COLUMN vector, col 3 (slots 3/7/11) is the post-translation, and the bottom
row (slots 12-14) is a pre-translation applied BEFORE R::

    y = R.(x + pre) + t

Confirmed by headless probes A1/A2 at <= 1.2e-07 A and by the shipped
source pymol-src/modules/pymol/editing.py:1962-1988 (see
.planning/phases/05-stacking-game-rules/05-RESEARCH-pymol-mechanics.md).
``matrix_rt`` below is the ONE and ONLY matrix composer (pitfall P5-8: a
swapped pre/post slot lands placements ~2x target-translation away; the
unit test pins all 16 floats against the probe-A1 fixture). For a pure
rotation use pre=(0,0,0); for a pivot rotation about O use pre=-O, t=+O.

EDGE-ON CANONICALIZATION (LOCKED 03-08 + 04-07 presentation decision):
every molecule object (head AND pickups) is canonicalized exactly ONCE at
load so its ring plane stands perpendicular to the screen xy plane -- the
pi-stack normal then lies IN the visible movement plane and stacks grow in
x/y. Mapping (``edge_on_frame``):

- ring normal      -> +x  (chain axis, in the xy plane)
- LONGER in-plane ring axis  -> +y  (planner-pinned azimuth rule: the
  visible screen axis carries the dataset's lateral offset)
- SHORTER in-plane ring axis -> +z  (keeps the worst post-edge-on
  z-extent -- phenanthrene 7.144 A, atom centers -- inside
  2 * BOX_DISPLAY_Z = 10.0 A, so BOX_DISPLAY_Z = 5.0 stays; if a future
  vdW-sphere overhang policy ever revisits that constant, only the
  constant changes, not this rule)
- ring centroid    -> origin

The input basis is ``stacking.ring_frame``'s (centroid, normal, ref) over
ONE planar ring in ring order (see 05-RESEARCH-core-integration.md
"ring_extraction_spec" -- manifest ring_atoms must NOT be fed directly).
All math is plain 3-tuples of floats; WSL python3.6 has no numpy.
"""

from . import stacking


def _dot(a, b):
    """Dot product a . b."""
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a, b):
    """Cross product a x b."""
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _span(atoms, axis):
    """max - min of the projection of ALL atoms onto <axis>."""
    lo = hi = _dot(atoms[0], axis)
    for p in atoms[1:]:
        d = _dot(p, axis)
        if d < lo:
            lo = d
        if d > hi:
            hi = d
    return hi - lo


def matrix_rt(R, t, pre=(0.0, 0.0, 0.0)):
    """Build the 16-float TTT list PyMOL 2.5.0 transform_selection accepts.

    Verified A1/A2 (<= 1.2e-07 A; editing.py:1962-1988): rows 0-2 cols 0-2
    = row-major R applied to the column vector; col 3 = post-translation
    (applied AFTER R); bottom row = pre-translation (added BEFORE R).
    So y = R.(x + pre) + t.

    R: 3x3 row-major tuple-of-tuples. t / pre: 3-tuples of floats.
    For stacking place_pickup (R, t): pre = (0,0,0).
    For pivot rotation about O: pre = -O, t = +O.
    """
    return [R[0][0], R[0][1], R[0][2], t[0],
            R[1][0], R[1][1], R[1][2], t[1],
            R[2][0], R[2][1], R[2][2], t[2],
            pre[0], pre[1], pre[2], 1.0]


def mat_vec3(R, v):
    """Row-major 3x3 R times 3-vector v -> 3-tuple."""
    return (R[0][0] * v[0] + R[0][1] * v[1] + R[0][2] * v[2],
            R[1][0] * v[0] + R[1][1] * v[1] + R[1][2] * v[2],
            R[2][0] * v[0] + R[2][1] * v[1] + R[2][2] * v[2])


def edge_on_frame(elements, coords, ring_indices):
    """Compute (R_edge, pre) canonicalizing the molecule edge-on.

    elements: element symbols per atom (kept for signature symmetry with
    edge_on_atoms/edge_on_m16; the frame depends on geometry only).
    coords: sequence of (x, y, z) floats for ALL atoms.
    ring_indices: ONE planar ring in ring order (fed to
    ``stacking.ring_frame``).

    Returns (R_edge, pre):
    - R_edge: 3x3 rotation as rows (normal, u, v) with
      mat_vec3(R_edge, normal) == (1,0,0), mat_vec3(R_edge, u) == (0,1,0),
      mat_vec3(R_edge, v) == (0,0,1). u is the LONGER-span in-plane ring
      axis (out of ref and cross(normal, ref), spans measured over ALL
      atoms -- H atoms extend beyond the ring carbons), v = cross(normal,
      u); rows (n, u, v) with v = n x u guarantee determinant +1 (a pure
      rotation, never a reflection).
    - pre: -ring centroid, so y = R_edge.(p + pre) maps the centroid to
      the origin.
    """
    atoms = [(float(p[0]), float(p[1]), float(p[2])) for p in coords]
    centroid, normal, ref = stacking.ring_frame(atoms, ring_indices)
    r2 = _cross(normal, ref)
    if _span(atoms, r2) > _span(atoms, ref):
        u = r2
    else:
        u = ref
    v = _cross(normal, u)
    rotation = (normal, u, v)
    pre = (-centroid[0], -centroid[1], -centroid[2])
    return (rotation, pre)


def edge_on_atoms(elements, coords, ring_indices):
    """Apply the edge-on canonicalization; return [(sym, x, y, z), ...].

    Symbols preserved in order; every atom gets y = R_edge.(p + pre)
    (the same transform cmd.transform_selection would apply to the object
    via edge_on_m16, computed here purely).
    """
    rotation, pre = edge_on_frame(elements, coords, ring_indices)
    placed = []
    for sym, p in zip(elements, coords):
        shifted = (float(p[0]) + pre[0],
                   float(p[1]) + pre[1],
                   float(p[2]) + pre[2])
        out = mat_vec3(rotation, shifted)
        placed.append((sym, out[0], out[1], out[2]))
    return placed


def edge_on_m16(elements, coords, ring_indices):
    """The 16-float TTT that canonicalizes the object edge-on in one shot.

    Equivalent to matrix_rt(R_edge, (0,0,0), pre): pre-translation moves
    the ring centroid to the origin, then R_edge maps normal -> +x,
    longer in-plane axis -> +y, shorter -> +z. Feed directly to
    cmd.transform_selection (verified layout; see module docstring).
    """
    rotation, pre = edge_on_frame(elements, coords, ring_indices)
    return matrix_rt(rotation, (0.0, 0.0, 0.0), pre)
