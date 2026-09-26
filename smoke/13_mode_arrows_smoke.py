"""Headless Windows PyMOL mode-arrows + overlay-identity smoke — 07-03.

Run (from repo root; cwd is /mnt/c-backed so cmd.exe inherits C:\\ cwd):
    timeout 90 cmd.exe /c "C:\\src\\run-conda-pymol.bat -cq smoke\\13_mode_arrows_smoke.py"

Exit codes through the .bat are ALWAYS 0 (even after a Qt C-abort) —
verdicts are flushed sentinels grepped by tests/run_gates.py --smoke:
    STAGE1 PARSE <counts>        fixture g98 parsed (26 atoms / 72 modes)
    STAGE2 ARROWS-LOADED <span>  CGO arrows loaded as srp_mode_vec, sane extent
    STAGE3 XTBOPT-IDENTITY <max> srp_xtbopt 26 atoms; max per-atom delta vs
                                 the g98 atom block printed (asserted < 1e-3 A)
    STAGE4 ZOOM                  zoom_mode_frame issued the one-shot zoom
    SMOKE-OK MODE-ARROWS         all stages passed
    SMOKE-FAIL <stage>: ...      a stage failed (one line per failure)

What this pins (SPECTRA-05, 07-RESEARCH-spectra-seam.md Q4b/Q8-2):
  1. The bridge CGO channel: pb.load_mode_arrows lands the
     cgo_build.mode_arrows stream as the srp_-prefixed object
     srp_mode_vec with a finite, non-degenerate extent.
  2. THE overlay regression: g98 Standard-orientation atom block and
     xtbopt.xyz agree per-atom to < 1e-3 A. The 2026-09-25 probe
     measured max |delta| = 0.0000 A on this fixture (xtb 6.7.1pre);
     1e-3 leaves drift headroom while still killing a real desync.
     Re-asserted on EVERY gate run so an xtb-version drift can never
     ship as a silent vectors-vs-molecule misalignment.
  3. pb.load_xtbopt lands srp_xtbopt with 26 atoms (sticks rep).
  4. pb.zoom_mode_frame returns True when the overlay objects exist
     (guarded one-shot framing; never a Selector error).

Template rules (copied from smoke/01_skeleton_smoke.py):
  - every print carries flush=True (stdout is block-buffered when piped)
  - NO widget construction (headless C-abort is uncatchable)
  - never add smoke/__init__.py (findPlugins plugin-path safety)
  - NEVER trust __file__ under -cq (resolve ROOT by validating
    serpentrum/__init__.py candidates)
  - verdict = flushed sentinels ONLY (never exit codes)
"""
import importlib
import math
import os
import sys


def _resolve_root():
    """Repo root, defensively.

    Under -cq exec, __file__ is PyMOL's launcher module (NOT this script),
    so naive dirname(dirname(__file__)) lands in site-packages. Validate
    every candidate by the presence of serpentrum/__init__.py. Copied
    verbatim from smoke/01_skeleton_smoke.py (probe-verified 01-04).
    """
    candidates = []
    if '__file__' in globals():
        _f = os.path.abspath(__file__)
        candidates.append(os.path.dirname(os.path.dirname(_f)))
        candidates.append(os.path.dirname(_f))
    candidates.append(os.getcwd())
    for _c in candidates:
        if os.path.isfile(os.path.join(_c, 'serpentrum', '__init__.py')):
            return _c
    return os.getcwd()


ROOT = _resolve_root()
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from pymol import cmd  # noqa: E402 (available inside PyMOL runtime)
from serpentrum import cgo_build  # noqa: E402
from serpentrum import pymol_bridge as pb  # noqa: E402
from serpentrum import spectra  # noqa: E402

FAILURES = []

G98_PATH = os.path.join(ROOT, 'tests', 'fixtures', 'xtb', 'g98.out')
XTBOPT_PATH = os.path.join(ROOT, 'tests', 'fixtures', 'xtb', 'xtbopt.xyz')

# Overlay-identity tolerance: probe 2026-09-25 measured max 0.0000 A;
# 1e-3 A leaves xtb-version drift headroom, kills a real desync.
IDENTITY_TOL_A = 1e-3


def check(name, fn):
    try:
        fn()
    except Exception as exc:
        print('SMOKE-FAIL %s: %r' % (name, exc), flush=True)
        FAILURES.append(name)


def s_stage1_parse():
    # Stage 1: parse the committed fixture g98 (the SPECTRA-05 table /
    # vector source). 26 atoms / 72 modes pinned by the Phase-2 parser
    # tests; re-pinned here so the smoke's own inputs are proven live.
    spectrum = spectra.parse_g98(G98_PATH)
    assert spectrum.n_atoms == 26, 'n_atoms %r != 26' % (spectrum.n_atoms,)
    assert len(spectrum.modes) == 72, \
        'modes %r != 72' % (len(spectrum.modes),)
    assert len(spectrum.modes[0].vectors) == 26, \
        'mode 1 vectors %r != 26' % (len(spectrum.modes[0].vectors),)
    print('STAGE1 PARSE atoms=%d modes=%d mode1_freq=%.4f'
          % (spectrum.n_atoms, len(spectrum.modes),
             spectrum.modes[0].freq), flush=True)
    return spectrum


def s_stage2_arrows_loaded(spectrum):
    # Stage 2: build mode-1 (-31.9i) arrows via the FROZEN Phase-2
    # builder and load them through the bridge CGO channel under the
    # srp_-prefixed name. Extent shape [[min3],[max3]] proven in 03-06.
    pb.delete_object(pb.MODE_VEC_NAME)
    atoms_xyz = [(a.x, a.y, a.z) for a in spectrum.atoms]
    cgo = cgo_build.mode_arrows(atoms_xyz, spectrum.modes[0].vectors,
                                scale=1.0)
    name = pb.load_mode_arrows(cgo)
    assert name == pb.MODE_VEC_NAME, 'returned name %r' % (name,)
    assert pb.object_exists(pb.MODE_VEC_NAME), 'srp_mode_vec missing'
    ext = cmd.get_extent(pb.MODE_VEC_NAME)
    spans = []
    for axis in range(3):
        lo = float(ext[0][axis])
        hi = float(ext[1][axis])
        assert math.isfinite(lo) and math.isfinite(hi), \
            'non-finite extent axis %d: %r' % (axis, ext)
        spans.append(hi - lo)
    assert max(spans) > 0.0, 'degenerate extent spans %r' % (spans,)
    print('STAGE2 ARROWS-LOADED spans=%.3f,%.3f,%.3f'
          % (spans[0], spans[1], spans[2]), flush=True)


def s_stage3_xtbopt_identity(spectrum):
    # Stage 3 (THE overlay regression): srp_xtbopt loads with 26 atoms
    # and its coordinates agree with the g98 atom block to < 1e-3 A,
    # in order. A mismatch here means the OPTIMIZED-frame overlay
    # decision (research Q4b) no longer holds -> loud failure, never a
    # silent misalignment.
    pb.delete_object(pb.XTBOPT_NAME)
    name = pb.load_xtbopt(XTBOPT_PATH)
    assert name == pb.XTBOPT_NAME, 'returned name %r' % (name,)
    assert pb.object_exists(pb.XTBOPT_NAME), 'srp_xtbopt missing'
    model = cmd.get_model(pb.XTBOPT_NAME)
    assert len(model.atom) == 26, \
        'xtbopt atoms %r != 26' % (len(model.atom),)
    max_delta = 0.0
    for i, atom in enumerate(model.atom):
        # PyMOL 2.5 chempy Atom exposes .coord ([x, y, z]), not .x/.y/.z.
        cx, cy, cz = atom.coord
        ref = spectrum.atoms[i]
        d = math.sqrt((cx - ref.x) ** 2
                      + (cy - ref.y) ** 2
                      + (cz - ref.z) ** 2)
        if d > max_delta:
            max_delta = d
    assert max_delta < IDENTITY_TOL_A, \
        'g98/xTBOPT per-atom max delta %.6f A >= %.1e A' \
        % (max_delta, IDENTITY_TOL_A)
    print('STAGE3 XTBOPT-IDENTITY max_delta=%.6f A' % max_delta,
          flush=True)


def s_stage4_zoom():
    # Stage 4: one-shot guarded framing issues the zoom (both overlay
    # objects exist from stages 2-3). Selector-error guard: the call
    # must return True and never raise.
    assert pb.zoom_mode_frame() is True, \
        'zoom_mode_frame did not issue the zoom'
    print('STAGE4 ZOOM', flush=True)


def s_cleanup():
    pb.delete_object(pb.MODE_VEC_NAME)
    pb.delete_object(pb.XTBOPT_NAME)
    assert not pb.object_exists(pb.MODE_VEC_NAME), 'srp_mode_vec remains'
    assert not pb.object_exists(pb.XTBOPT_NAME), 'srp_xtbopt remains'


_spectrum = [None]
check('stage1_parse', lambda: _spectrum.__setitem__(0, s_stage1_parse()))
if _spectrum[0] is not None:
    check('stage2_arrows_loaded', lambda: s_stage2_arrows_loaded(_spectrum[0]))
    check('stage3_xtbopt_identity',
          lambda: s_stage3_xtbopt_identity(_spectrum[0]))
    check('stage4_zoom', s_stage4_zoom)
    check('cleanup', s_cleanup)

if FAILURES:
    print('SMOKE-END %d failure(s)' % len(FAILURES), flush=True)
else:
    print('SMOKE-OK MODE-ARROWS', flush=True)
