"""CGO geometry construction -- pure stdlib builders returning float lists.

PURE module (stdlib ``math`` only -- no pymol/pmg_tk/PyQt5/numpy anywhere;
enforced by tools/check_purity.py, which auto-classifies this file PURE).

This is the bridge-facing PURE half of the rendering stack: it constructs
CGO (compiled graphics object) geometry as plain float lists that the
Phase-5 GUI connector will hand to ``cmd.load_cgo``.  Everything here is
buildable and verifiable in WSL python3.6 with ZERO PyMOL imports.

WHY LOCAL CONSTANTS (not ``from pymol import cgo``):
``pymol/cgo.py`` executes ``from pymol import cmd`` at ITS module level
(verified: cgo.py:79-156), so importing it here would (a) violate the
INFRA-02 purity gate and (b) drag the entire GUI runtime into pure-land.
The 15 opcode constants below are LOCAL float literals copied from the
verified cgo.py table (cgo.py:21-65).  There is NO ``VERSION`` constant
in pymol/cgo.py -- none is defined here either (asserted in tests).

Verified float-list layouts (C-source, not guessed):
  SPHERE   = opcode + 4  floats [x, y, z, radius]
             (CGO_SPHERE_SZ = 4,  CGO.h:96;  needs a preceding COLOR)
  CYLINDER = opcode + 13 floats [x1,y1,z1, x2,y2,z2, radius,
                                  r1,g1,b1, r2,g2,b2]
             (CGO_CYLINDER_SZ = 13, CGO.h:100)
  CONE     = opcode + 16 floats [x1,y1,z1, x2,y2,z2,
                                  r_base, r_tip,
                                  cr1,cg1,cb1, cr2,cg2,cb2,
                                  cap1, cap2]
             (CGO_CONE_SZ = 16, CGO.h:143; write order CGO.cpp:916-943;
             caps read CGO.cpp:5754-5756; cCylCap: None=0, Flat=1,
             Round=2, Basis.h:41-46).  Arrow tips use flat caps (1.0).

NOTE on value collisions: several opcodes share the same float value
(LINE_STRIP == END == 3.0; TRIANGLES == VERTEX == 4.0; POINTS == STOP ==
0.0; LINES == NULL == 1.0).  This is intrinsic to PyMOL's CGO encoding --
the parser disambiguates by context.  Our builders only emit one
interpretation per value (e.g. we use END, never LINE_STRIP; VERTEX,
never TRIANGLES), and the test interpreter maps each value to the single
operand-count we use.

Three public builders:
  box_cgo      -- displayed boundary box (STACK.md sec.3) as 12 LINES
                  edges built purely from two corners.
  mode_arrows  -- vibrational mode displacement arrows (SPECTRA-05) as a
                  CYLINDER shaft + CONE head per nonzero displacement
                  vector.
  spheres_cgo  -- one sphere per point (GAME-03 head rendering) as SPHERE
                  records under a single COLOR header.
"""
import math

# --- CGO opcode constants (LOCAL float literals) --------------------------
# Copied from the verified pymol/cgo.py table (cgo.py:21-65).  LOCAL because
# importing pymol.cgo would pull `from pymol import cmd` at its module level
# (cgo.py:79-156), violating INFRA-02 purity.  NO VERSION constant exists in
# pymol/cgo.py -- none is defined here.  DO NOT import pymol.cgo to "sync"
# these; they are verified literals.
POINTS = 0.0           # cgo.py:21
STOP = 0.0             # cgo.py:23
LINES = 1.0            # cgo.py:25
NULL = 1.0             # cgo.py:27
BEGIN = 2.0            # cgo.py:29
LINE_STRIP = 3.0       # cgo.py:31
END = 3.0              # cgo.py:33  (NOTE: same value as LINE_STRIP)
TRIANGLES = 4.0        # cgo.py:35
TRIANGLE_STRIP = 5.0   # cgo.py:37
VERTEX = 4.0           # cgo.py:39  (NOTE: same value as TRIANGLES)
COLOR = 6.0            # cgo.py:41
SPHERE = 7.0           # cgo.py:43
CYLINDER = 9.0         # cgo.py:45
LINEWIDTH = 10.0       # cgo.py:47
CONE = 27.0            # cgo.py:63


def box_cgo(min_corner, max_corner, color=(1.0, 0.4, 0.1), linewidth=2.0):
    """Build a boundary-box CGO stream as 12 LINES edges from two corners.

    PURE: stdlib only, returns a plain list of floats.

    min_corner / max_corner: 3-tuples of the box's min and max vertices.
    color: (r, g, b) float triplet for the edge color.
    linewidth: float line width for the LINES block.

    Returns a float list structured as:
      [LINEWIDTH, w, BEGIN, LINES, COLOR, r, g, b]      -- 8 floats
      + 12 edges, each [VERTEX, x,y,z, VERTEX, x,y,z]    -- 96 floats
      + [END, STOP]                                       -- 2 floats
    Total: 106 floats (parseable by the mini CGO interpreter in tests).

    The 8 corners are enumerated explicitly (c000..c111, binary xyz with
    0=min, 1=max) and the 12 edges listed in standard order: bottom z-min
    rectangle, top z-max rectangle, four verticals.  No loops that could
    silently reorder the edges.
    """
    x0 = float(min_corner[0])
    y0 = float(min_corner[1])
    z0 = float(min_corner[2])
    x1 = float(max_corner[0])
    y1 = float(max_corner[1])
    z1 = float(max_corner[2])
    cr = float(color[0])
    cg = float(color[1])
    cb = float(color[2])
    lw = float(linewidth)

    # 8 corners: cXYZ where X/Y/Z bit = 0 (min) or 1 (max).
    c000 = (x0, y0, z0)
    c100 = (x1, y0, z0)
    c110 = (x1, y1, z0)
    c010 = (x0, y1, z0)
    c001 = (x0, y0, z1)
    c101 = (x1, y0, z1)
    c111 = (x1, y1, z1)
    c011 = (x0, y1, z1)

    # 12 edges in standard order (each corner touches exactly 3 edges).
    edges = [
        # Bottom z-min rectangle: c000-c100-c110-c010-c000
        (c000, c100), (c100, c110), (c110, c010), (c010, c000),
        # Top z-max rectangle: c001-c101-c111-c011-c001
        (c001, c101), (c101, c111), (c111, c011), (c011, c001),
        # Four verticals
        (c000, c001), (c100, c101), (c110, c111), (c010, c011),
    ]

    out = [LINEWIDTH, lw, BEGIN, LINES, COLOR, cr, cg, cb]
    for p_a, p_b in edges:
        out.extend([VERTEX, p_a[0], p_a[1], p_a[2],
                    VERTEX, p_b[0], p_b[1], p_b[2]])
    out.extend([END, STOP])
    return out


def mode_arrows(atoms, vecs, scale=1.0, color=(0.2, 0.6, 1.0),
                base_radius=0.06, length_a=1.2):
    """Build vibrational mode-arrow CGO stream (CYLINDER shaft + CONE head).

    PURE: stdlib math only, returns a plain list of floats.

    atoms: sequence of (x, y, z) atom positions.
    vecs:  same-length sequence of (x, y, z) displacement vectors (as
           extracted from spectra ``Mode.vectors`` by the caller).
    scale: overall scale factor applied to the arrow length.
    color: (r, g, b) float triplet for both shaft and head.
    base_radius: radius of the CYLINDER shaft and the CONE base.
    length_a: base arrow length in Angstrom (before scale).

    For each atom whose displacement magnitude >= 1e-6, emits:
      CYLINDER (14 floats): opcode + [px,py,pz, sx,sy,sz, radius,
                             cr,cg,cb, cr,cg,cb]
        p -> shaft_end, both endpoint colors = arrow color.
      CONE (17 floats): opcode + [sx,sy,sz, tx,ty,tz, r_base, r_tip,
                        cr,cg,cb, cr,cg,cb, cap1, cap2]
        shaft_end -> tip, r_base=base_radius, r_tip=0.0, caps=1.0 (flat).

    Arithmetic (direction normalized BEFORE scaling):
      v_hat   = v / |v|
      shaft_end = p + v_hat * scale * length_a * 0.7
      tip       = p + v_hat * scale * length_a
    The 0.7 shaft fraction leaves 30% of the arrow length for the cone
    head.  A 3 A displacement does NOT make a 3.6 A arrow -- the vector
    is unit-normalized first, then scaled by ``scale * length_a``.

    Vectors shorter than 1e-6 are skipped (no CYLINDER/CONE emitted).

    Returns: [COLOR, r, g, b] + per nonzero vector (CYLINDER + CONE) +
             [STOP].
    """
    cr = float(color[0])
    cg = float(color[1])
    cb = float(color[2])
    sc = float(scale)
    br = float(base_radius)
    la = float(length_a)
    shaft_frac = 0.7  # shaft occupies 70% of the arrow length

    out = [COLOR, cr, cg, cb]
    for atom, vec in zip(atoms, vecs):
        vx = float(vec[0])
        vy = float(vec[1])
        vz = float(vec[2])
        mag = math.sqrt(vx * vx + vy * vy + vz * vz)
        if mag < 1e-6:
            continue
        ux = vx / mag
        uy = vy / mag
        uz = vz / mag
        px = float(atom[0])
        py = float(atom[1])
        pz = float(atom[2])
        # Shaft end and tip along the UNIT direction, then scaled.
        se = sc * la * shaft_frac
        sx = px + ux * se
        sy = py + uy * se
        sz = pz + uz * se
        tp = sc * la
        tx = px + ux * tp
        ty = py + uy * tp
        tz = pz + uz * tp
        # CYLINDER shaft: p -> shaft_end (14 floats total).
        out.extend([CYLINDER, px, py, pz, sx, sy, sz, br,
                    cr, cg, cb, cr, cg, cb])
        # CONE head: shaft_end -> tip (17 floats total, two radii +
        # flat caps 1.0).
        out.extend([CONE, sx, sy, sz, tx, ty, tz, br, 0.0,
                    cr, cg, cb, cr, cg, cb, 1.0, 1.0])
    out.append(STOP)
    return out


def spheres_cgo(points, radius, color):
    """Build a sphere-per-point CGO stream under a single COLOR header.

    PURE: stdlib only, returns a plain list of floats.

    points: sequence of (x, y, z) sphere centers.
    radius: sphere radius (same for all points).
    color:  (r, g, b) float triplet.

    Returns: [COLOR, r, g, b] + per point [SPHERE, x, y, z, radius] +
             [STOP].

    SPHERE = opcode + 4 floats [x, y, z, radius] (CGO_SPHERE_SZ = 4,
    CGO.h:96).  The preceding COLOR triplet sets the draw color.
    """
    cr = float(color[0])
    cg = float(color[1])
    cb = float(color[2])
    rad = float(radius)

    out = [COLOR, cr, cg, cb]
    for p in points:
        out.extend([SPHERE, float(p[0]), float(p[1]), float(p[2]), rad])
    out.append(STOP)
    return out
