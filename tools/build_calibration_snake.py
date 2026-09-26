"""Deterministic calibration-snake fixture builder (plan 06-07, SC5).

Tiles the committed, xtb-accepted dimer motif
.planning/research/xtb-spike-fixtures/dimer2.xyz (26 atoms = two 13-atom
phenol layers at the ~3.4 A stack offset) into N-layer stacks:

    N=4 -> 52 atoms -> tests/fixtures/calib_snake_52.xyz
    N=8 -> 104 atoms -> tests/fixtures/calib_snake_104.xyz

Geometry is DERIVED ONLY from the committed fixture (inter-layer centroid
delta of the two 13-atom halves) — never hand-edited. The builder is
deterministic: no RNG, no clock. Round-trip parsing via
serpentrum.xyzio.read_xyz_text asserts the written fixture is parseable
and carries exactly 13*N atoms.

python3.6, stdlib only. Run from anywhere:

    python3.6 tools/build_calibration_snake.py
"""
import os
import sys

# tools/ has no __init__.py (plugin-path safety, run_gates gate 1);
# self-insert the repo root so 'serpentrum' imports resolve.
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from serpentrum import xyzio

DIMER_PATH = os.path.join(_ROOT, '.planning', 'research',
                          'xtb-spike-fixtures', 'dimer2.xyz')
FIXTURES_DIR = os.path.join(_ROOT, 'tests', 'fixtures')
LAYER_ATOMS = 13
SIZES = (4, 8)  # N layers -> 52 / 104 atoms
# Sanity bound on the xtb-validated inter-layer stack offset (Angstrom).
DELTA_MIN = 3.0
DELTA_MAX = 4.0


def _centroid(layer):
    """Per-axis mean of a [(sym, x, y, z), ...] layer -> (cx, cy, cz)."""
    n = len(layer)
    return (sum(a[1] for a in layer) / n,
            sum(a[2] for a in layer) / n,
            sum(a[3] for a in layer) / n)


def main():
    comment, atoms = xyzio.read_xyz(DIMER_PATH)
    if len(atoms) != 2 * LAYER_ATOMS:
        raise SystemExit('dimer2.xyz: expected %d atoms, parsed %d'
                         % (2 * LAYER_ATOMS, len(atoms)))
    layer_a = atoms[0:LAYER_ATOMS]
    layer_b = atoms[LAYER_ATOMS:2 * LAYER_ATOMS]
    ca = _centroid(layer_a)
    cb = _centroid(layer_b)
    dx, dy, dz = (cb[0] - ca[0], cb[1] - ca[1], cb[2] - ca[2])
    magnitude = (dx * dx + dy * dy + dz * dz) ** 0.5
    if not (DELTA_MIN <= magnitude <= DELTA_MAX):
        raise SystemExit(
            'dimer2.xyz: inter-layer centroid delta |%.4f| A outside '
            'the xtb-validated sanity bound [%.1f, %.1f] A — motif '
            'changed? Aborting.' % (magnitude, DELTA_MIN, DELTA_MAX))
    print('dimer2 motif: %r (%d atoms); layer delta = (%.6f, %.6f, %.6f)'
          ' |delta| = %.4f A'
          % (comment, len(atoms), dx, dy, dz, magnitude))
    for n_layers in SIZES:
        elements = []
        coords = []
        for i in range(n_layers):
            for sym, x, y, z in layer_a:
                elements.append(sym)
                coords.append((x + i * dx, y + i * dy, z + i * dz))
        total = n_layers * LAYER_ATOMS
        text = xyzio.write_xyz(
            elements, coords,
            comment='serpentrum calib snake N=%d layers from dimer2 motif'
                    % n_layers)
        # Round-trip assertion: the written fixture must re-parse to
        # exactly 13*N atoms before it is committed.
        _comment2, atoms2 = xyzio.read_xyz_text(text)
        if len(atoms2) != total:
            raise SystemExit('round-trip: expected %d atoms, parsed %d'
                             % (total, len(atoms2)))
        path = os.path.join(FIXTURES_DIR, 'calib_snake_%d.xyz' % total)
        with open(path, 'w', encoding='utf-8') as handle:
            handle.write(text)
        print('wrote %s (%d atoms, round-trip verified)' % (path, total))
    print('52 and 104 fixtures built')


if __name__ == '__main__':
    main()
