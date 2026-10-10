"""The broadened-IR plot's PURE data half (plan 07-02 — SPECTRA-03).

This module builds paint-ready Scenes over the committed
``spectra.broaden`` (the Multiwfn-parity Lorentzian curve — unit-area
per-mode weighting x spectra.CURVE_SCALE; GATE V amendment 2026-10-04):
the broadening, the y_max headroom + floor, nice-tick selection, axis
labels, size-preset data, and the imaginary-mode caption. quick-002
(2026-10-10) adds the discrete-lines representation: the scene echoes
the raw mode sticks and scene_with_unit's 'lines' mode synthesizes
paint segments (Multiwfn discrete-lines style) — the curve transforms
stay untouched. The GUI renderer (plan 07-05, ``gui_plot.paint_scene``)
maps a Scene to pixels and NEVER recomputes (07-RESEARCH-qt-plot.md
pitfall 2: paintEvent must paint, not compute — paint stays O(points)
and every numeric decision is unit-testable here).

Pure stdlib module (``math`` + the intra-package ``from . import
spectra``, which the purity gate exempts): no pymol/pmg_tk/PyQt5/numpy
import may appear here even inside function bodies. python3.6 syntax,
%-formatting only.

Cross-half coordination (pinned at planning): this module deliberately
imports NO frequency formatter — the v1 plot displays no raw frequency
values (ticks are plain wavenumbers; the caption counts imaginary modes).
The single shared imaginary formatter lives in ``spectra_ui.freq_label``
(plan 07-01); do NOT hand-roll one here.
"""
import math
from collections import namedtuple

from . import spectra

Scene = namedtuple(
    'Scene',
    'xs ys x_min x_max y_max x_ticks y_ticks x_label y_label '
    'n_modes n_imaginary fwhm sticks segments')
# xs/ys: the broadened curve on an ascending grid (spectra.broaden).
# x_ticks/y_ticks: precomputed (value, label_str) pairs — the GUI maps
#   values to pixels, never recomputes tick math.
# x_label/y_label: ASCII axis titles.
# n_modes/n_imaginary: mode counts for the caption/status framing.
# fwhm: the broadening actually used (echoed for display/debug).
# sticks: the RAW discrete mode data — a tuple of (freq, intensity)
#   float pairs (the table / spectrum_line.txt values), echoed by
#   build_scene; carried UNCHANGED through every derived scene
#   (data, like n_modes). quick-002 2026-10-10.
# segments: the PAINT representation for the discrete-lines unit
#   mode — None for every curve scene (the painter draws the xs/ys
#   polyline); a tuple of ((x0, y0), (x1, y1)) float pairs when the
#   scene is a lines scene (the painter draws these INSTEAD; the
#   lines scene also empties xs/ys so no stale curve data rides
#   along). quick-002 2026-10-10.

# y-axis floor in Multiwfn-scaled curve units (GATE V amendment
# 2026-10-04: the curve is unit-area Lorentzian x100, not raw km/mol).
# The PINNED empty-modes case (broaden's zero curve)
# returns the zero curve, so max(ys) == 0.0 — an unfloored y_max == 0.0
# gives a zero-range axis and blows up tick math (07-RESEARCH-qt-plot.md
# pitfall 5). The floor gives the silent spectrum a sane 0..1 axis.
Y_MAX_FLOOR = 1.0

# Classic nice-step candidates: 1/2/2.5/5 x 10^n (10 closes the decade).
_NICE_FACTORS = (1.0, 2.0, 2.5, 5.0, 10.0)


def _fmt(value, step):
    """Format a tick value at the STEP's precision.

    decimals = 0 when step is None (zero-range single tick) or an
    integer step; otherwise the step's own decimal count (2.5 -> 1,
    0.2 -> 1, 0.25 -> 2), found by loop-multiplying by 10 (6 loops max).
    Labels carry the step's precision, never the values' — a 0-valued
    tick at 1-decimal precision renders '0.0', not '0'.
    """
    decimals = 0
    if step is not None and not float(step).is_integer():
        scaled = float(step)
        while not scaled.is_integer() and decimals < 6:
            scaled *= 10.0
            decimals += 1
    return ('%.' + str(decimals) + 'f') % value


def nice_ticks(lo, hi, target=8):
    """Classic 1/2/2.5/5 x 10^n nice-tick selection -> [(value, label)].

    All tick values lie within [lo, hi], strictly ascending. Degenerate
    inputs are total: hi <= lo returns a single tick at lo (never a
    division-by-zero); negative lo is fine (ceil/floor bracketing picks
    the interior multiples of the step). Anchors: (0, 3600, 8) -> step
    500; (0, 10, 4) -> step 2.5 with 1-decimal labels.
    """
    if hi <= lo:
        return [(float(lo), _fmt(float(lo), None))]
    raw = (hi - lo) / float(target)
    mag = 10.0 ** math.floor(math.log10(raw))
    step = None
    for factor in _NICE_FACTORS:
        candidate = factor * mag
        if candidate >= raw:
            step = candidate
            break
    k_first = int(math.ceil(float(lo) / step))
    k_last = int(math.floor(float(hi) / step))
    values = [k * step for k in range(k_first, k_last + 1)]
    return [(value, _fmt(value, step)) for value in values]


def build_scene(modes, fwhm=8.0, x_min=0.0, x_max=None, n_points=800):
    """Build the paint-ready Scene over spectra.broaden ->
    Scene(xs, ys, x_min, x_max, y_max, x_ticks, y_ticks, x_label,
    y_label, n_modes, n_imaginary, fwhm, sticks, segments).

    quick-002 (2026-10-10): the scene now also echoes the raw mode
    sticks (``sticks``) for the discrete-lines derivation; the curve
    representation itself is unchanged.

    Thin orchestration ONLY: broaden does the convolutions (its
    ValueError on fwhm <= 0 / n_points < 2 propagates — the caller's
    fwhm is validated upstream by setup_logic). y_max carries 10%
    headroom over the curve peak, floored at Y_MAX_FLOOR so the pinned
    zero-curve case (empty modes) still gets a sane axis. Tick targets:
    x target 8, y target 5.

    v1 axis convention (owner-signable at the 07-06/07-10 checkpoints):
    the wavenumber axis ships ASCENDING (mathematically native —
    broaden's grid is ascending). Chemistry-conventional descending
    (4000 -> 400) is a v2 data-only flip; NO reverse_x flag is built
    now (an untested flag is v2 bait). fwhm arrives from
    setup_logic.DEFAULTS['broadening_fwhm'] read LIVE by the caller
    (plan 07-08's tab) — never re-pinned here.
    """
    xs, ys = spectra.broaden(modes, fwhm=fwhm, x_min=x_min, x_max=x_max,
                             n_points=n_points)
    peak = max(ys) if ys else 0.0
    y_max = max(peak * 1.1, Y_MAX_FLOOR)
    x_lo = float(xs[0])
    x_hi = float(xs[-1])
    x_ticks = nice_ticks(x_lo, x_hi, 8)
    y_ticks = nice_ticks(0.0, y_max, 5)
    n_modes = len(modes)
    n_imaginary = sum(1 for m in modes if m.freq < 0.0)
    return Scene(
        xs=xs,
        ys=ys,
        x_min=x_lo,
        x_max=x_hi,
        y_max=y_max,
        x_ticks=x_ticks,
        y_ticks=y_ticks,
        x_label='wavenumber (cm-1)',
        y_label='epsilon (L mol-1 cm-1)',
        n_modes=n_modes,
        n_imaginary=n_imaginary,
        fwhm=fwhm,
        sticks=tuple((float(m.freq), float(m.intensity))
                     for m in modes),
        segments=None)


# Owner amendments: the y-axis DISPLAY is selectable in the panel.
# (07-06 checkpoint round 1, 2026-09-26) created the 3-entry combo;
# (GATE V amendment 2026-10-04) made the curve the Multiwfn-parity
# epsilon curve, so the original 'IR intensity (km/mol)' combo label
# no longer named what it plots; (quick-002, owner directive
# 2026-10-10) RENAMES the default entry to what it is and ADDS a
# discrete-lines mode. (label, mode) combo data for the house
# addItem(label, data) pattern; the FIRST entry is the default. The
# combo labels name the UNIT MODE; the epsilon-mode AXIS label itself
# is set by build_scene to the Multiwfn-scaled convention
# ('epsilon (L mol-1 cm-1)', GATE V amendment 2026-10-04); the
# lines-mode AXIS label states the real unit ('IR intensity (km/mol)'
# -- the table header's literal). Combo label wording is PROVISIONAL
# pending the owner's live blessing at the gate (quick-002). The
# absorbance/transmittance transforms below normalize by the curve
# peak, so the x100 curve scale cancels -- they are
# convention-invariant and remain UNTOUCHED.
UNIT_MODES = (('epsilon (Multiwfn curve)', 'intensity'),
              ('intensity (km/mol)', 'lines'),
              ('absorbance (arb.)', 'absorbance'),
              ('transmittance (arb.)', 'transmittance'))

_UNIT_MODE_KEYS = tuple(mode for _label, mode in UNIT_MODES)


def scene_with_unit(scene, mode):
    """Re-express a Scene's y-axis in another DISPLAY unit -> Scene.

    Modes (UNIT_MODES):
      - 'intensity': passthrough — the Scene is returned unchanged
        (the y_label it passes through is build_scene's Multiwfn-
        scaled convention, GATE V amendment 2026-10-04; the pinned
        default).
      - 'lines': quick-002 (owner directive 2026-10-10): the DISCRETE
        STICKS representation — one baseline-rooted vertical segment
        per mode at the actual table / spectrum_line.txt (freq,
        intensity) values (Multiwfn 'discrete lines' style). NO
        broadening applies (discrete by definition; fwhm is echoed
        unchanged). The x window keeps the curve's right bound and
        widens LEFT when negative-frequency modes exist so they
        render at negative x; the returned scene empties xs/ys (no
        stale curve data rides along), carries the segments payload,
        and states the real-unit AXIS label 'IR intensity (km/mol)'
        (distinct from the combo label 'intensity (km/mol)'). Empty
        modes -> NO segments (never fabricated).
      - 'absorbance': intensity normalized to peak = 1. Rationale:
        xtb IR intensities (km/mol) are proportional to absorbance via
        Beer-Lambert linearity, so the relative absorbance curve is
        the intensity curve up to an unknown constant; normalizing the
        peak to 1 keeps it honest — arbitrary units, labeled '(arb.)'.
        (The GATE V x100 curve scale cancels in the normalization.)
      - 'transmittance': T = 10**(-A) of the NORMALIZED absorbance
        (T in (0, 1]; peaks point DOWN at T = 0.1; far from peaks
        T ~ 1). Also '(arb.)' — this recomputes nothing physical, it
        re-expresses the normalized curve in the transmittance
        convention. The GUI's y-invert option restores the journal
        look if wanted.

    Unknown modes raise ValueError — loud, never a silent passthrough.
    A lines scene never re-derives either (quick-002): calling this on
    a segments-carrying scene raises ValueError for every non-default
    mode — lines do NOT feed absorbance/transmittance (those are
    curve-based) and derivation always starts from the BASE curve
    scene.
    A zero curve (the pinned empty-modes scene) stays zeros in every
    unit (no division-by-zero; the GUI shows the hint path for an
    empty spectrum anyway). In the curve modes everything except
    ys/y_max/y_ticks/y_label passes through UNCHANGED ('lines'
    additionally synthesizes segments, empties xs/ys, and widens
    x_min/x_ticks left when negative modes exist); sticks pass
    through UNCHANGED everywhere (data, like n_modes). y_max/y_ticks
    recompute under the build_scene policy (10% headroom over the
    new peak, floored at Y_MAX_FLOOR; nice_ticks(0, y_max, 5)).
    """
    if mode not in _UNIT_MODE_KEYS:
        raise ValueError(
            'unknown plot unit mode %r (expected one of %s)'
            % (mode, ', '.join(_UNIT_MODE_KEYS)))
    if mode == 'intensity':
        return scene
    if scene.segments is not None:
        # quick-002 (2026-10-10): derivation always starts from the
        # BASE curve scene. A lines scene re-derives into nothing:
        # lines do NOT feed absorbance/transmittance (those are
        # curve-based), and a lines scene is never re-derived.
        raise ValueError(
            'cannot re-express a discrete-lines scene (mode %r)'
            % (mode,))
    if mode == 'lines':
        # quick-002 (2026-10-10, owner directive): the DISCRETE STICKS
        # mode — one vertical line per mode at the actual table /
        # spectrum_line.txt values (Multiwfn 'discrete lines' style).
        # fwhm/broadening does NOT apply (discrete by definition). The
        # x window keeps the curve's right bound (mode switching never
        # jumps the axis) and widens LEFT when negative-frequency
        # sticks exist so they render at negative x. Empty modes ->
        # zero sticks (never fabricated). The AXIS label states the
        # real unit — distinct from the combo label 'intensity (km/mol)'.
        segments = tuple(((float(freq), 0.0),
                          (float(freq), float(inten)))
                         for freq, inten in scene.sticks)
        x_lo = scene.x_min
        if scene.sticks:
            x_lo = min(x_lo, min(float(freq)
                                 for freq, _inten in scene.sticks))
        y_peak = max((float(inten) for _freq, inten in scene.sticks),
                     default=0.0)
        y_max = max(y_peak * 1.1, Y_MAX_FLOOR)
        return Scene(
            xs=(),
            ys=(),
            x_min=x_lo,
            x_max=scene.x_max,
            y_max=y_max,
            x_ticks=nice_ticks(x_lo, scene.x_max, 8),
            y_ticks=nice_ticks(0.0, y_max, 5),
            x_label=scene.x_label,
            y_label='IR intensity (km/mol)',
            n_modes=scene.n_modes,
            n_imaginary=scene.n_imaginary,
            fwhm=scene.fwhm,
            sticks=scene.sticks,
            segments=segments)
    y_label = dict((m, label) for label, m in UNIT_MODES)[mode]
    peak = max(scene.ys) if scene.ys else 0.0
    if peak <= 0.0:
        a_rel = list(scene.ys)  # zero curve: stays zeros in any unit
    else:
        a_rel = [y / peak for y in scene.ys]
    if mode == 'absorbance':
        new_ys = a_rel
    else:  # 'transmittance'
        new_ys = [10.0 ** (-a) for a in a_rel] if peak > 0.0 else a_rel
    peak_new = max(new_ys) if new_ys else 0.0
    y_max = max(peak_new * 1.1, Y_MAX_FLOOR)
    y_ticks = nice_ticks(0.0, y_max, 5)
    return Scene(
        xs=scene.xs,
        ys=new_ys,
        x_min=scene.x_min,
        x_max=scene.x_max,
        y_max=y_max,
        x_ticks=scene.x_ticks,
        y_ticks=y_ticks,
        x_label=scene.x_label,
        y_label=y_label,
        n_modes=scene.n_modes,
        n_imaginary=scene.n_imaginary,
        fwhm=scene.fwhm,
        sticks=scene.sticks,
        segments=None)


def size_presets():
    """The v1 plot-size adjustment data -> [(label, (w, h))].

    Pure data for the house addItem(label, data) combo pattern
    (gui_setup.py combo precedent) — no widget code here. 'compact
    (640x320)' is the pinned default (first entry) since the round-5
    owner decision (2026-10-10, height-reduction option D, debug
    session .planning/debug/06-window-move-resize-quirk.md): the
    construction-time pin freezes the dialog ~80 logical px shorter.
    'medium (640x400)' — the pre-round-5 default — STAYS as a
    one-click choice (large/wide untouched): the 07-06 exact-preset
    + grow/shrink semantics are unchanged, only the default moved.
    NO FWHM control, NO zoom/pan in v1 (SPECTRA-03 'minimal
    adjustments' = size presets + axis-label toggle only).
    """
    return [('compact (640x320)', (640, 320)),
            ('medium (640x400)', (640, 400)),
            ('large (800x500)', (800, 500)),
            ('wide (960x500)', (960, 500))]


def mode_caption(scene):
    """The imaginary-mode caption string ('' when nothing is imaginary).

    '%d modes; %d below 0 (imaginary) - see the table' — educational
    framing only: the TABLE owns the rows (SPECTRA-05); the plot never
    prints raw frequencies in v1 (the single shared frequency formatter
    is spectra_ui.freq_label — none is hand-rolled here).
    """
    if scene.n_imaginary == 0:
        return ''
    return ('%d modes; %d below 0 (imaginary) - see the table'
            % (scene.n_modes, scene.n_imaginary))
