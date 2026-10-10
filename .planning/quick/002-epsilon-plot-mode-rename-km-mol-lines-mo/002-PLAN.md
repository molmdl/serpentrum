---
phase: quick-002
plan: 002
type: execute
wave: 1
depends_on: []
files_modified:
  - serpentrum/plot_logic.py
  - serpentrum/gui_plot.py
  - tests/test_plot_logic.py
  - smoke/12_plot_smoke.py
  - smoke/manual_plot_check.py
autonomous: true

must_haves:
  truths:
    - "The y-unit combo's first (default) entry reads 'epsilon (Multiwfn curve)' and shows the UNCHANGED approved curve (axis label still 'epsilon (L mol-1 cm-1)')"
    - "Selecting 'lines (km/mol)' shows one sharp vertical stick per mode at the actual table (frequency, IR intensity) values — NO broadening, y axis label 'IR intensity (km/mol)'"
    - "Negative-frequency sticks render at negative x (the lines scene's x_min widens left of 0); the x right bound stays the curve window"
    - "Empty modes in lines mode show axes with ZERO sticks (never fabricated)"
    - "Absorbance/transmittance behave EXACTLY as approved (curve-based math byte-untouched; a lines scene never feeds them)"
    - "A saved PNG of any unit mode matches the screen (route-A parity incl. the lines representation)"
  artifacts:
    - path: "serpentrum/plot_logic.py"
      provides: "UNIT_MODES 4 entries (epsilon default / lines / absorbance / transmittance) + Scene.sticks/segments fields + scene_with_unit 'lines' derivation with loud ValueError guards"
      contains: "'lines (km/mol)'"
    - path: "serpentrum/gui_plot.py"
      provides: "paint_scene representation branch: scene.segments drawn as vertical lines INSTEAD of the xs/ys polyline, same pen/clip path (route-A parity)"
      contains: "scene.segments is not None"
    - path: "tests/test_plot_logic.py"
      provides: "renamed UNIT_MODES literal pins + TestLinesMode (sticks echo, segments shape, negative-x widening, empty contract, fwhm irrelevance, re-derive guards)"
      contains: "TestLinesMode"
    - path: "smoke/12_plot_smoke.py"
      provides: "STAGE6 LINES leg — the lines scene renders through render_image to a valid PNG (the painter branch's only automated coverage)"
      contains: "STAGE6 LINES"
    - path: "smoke/manual_plot_check.py"
      provides: "updated human checklist: renamed default combo step h + new h2 discrete-lines step"
      contains: "h2."
  key_links:
    - from: "serpentrum/gui_plot.py paint_scene"
      to: "scene.segments"
      via: "representation branch — segments drawn per-segment via _map_x/_map_y (honors invert_x/invert_y/line_color), else the unchanged QPolygonF polyline"
      pattern: "scene\\.segments is not None"
    - from: "serpentrum/plot_logic.py scene_with_unit"
      to: "scene.sticks (raw mode data echoed by build_scene)"
      via: "'lines' derivation synthesizes ((freq, 0.0), (freq, intensity)) paint segments — the ONLY consumer of sticks"
      pattern: "scene\\.sticks"
    - from: "serpentrum/gui_plot.py SpectraPlotPanel"
      to: "plot_logic.UNIT_MODES + scene_with_unit"
      via: "combo populates from UNIT_MODES (4 entries); _derive_scene routes ALL modes incl. 'lines' — panel needs ZERO code changes"
      pattern: "for label, mode in plot_logic\\.UNIT_MODES"
---

<objective>
Make the Spectra plot's y-unit combo stop lying about what it shows, and give it a real km/mol discrete-lines option.

Purpose: OWNER DIRECTIVE 2026-10-10 (mid-GATE-V, design confirmed by owner option pick). The 07-06-approved combo offers "IR intensity (km/mol)" (default) / absorbance / transmittance. After the Multiwfn-parity change (5ece303, GATE V 2026-10-04) the "intensity" curve is the Lorentzian FWHM-8 unit-area x CURVE_SCALE(100) curve, axis-labeled `epsilon (L mol-1 cm-1)` (75cd278) — the combo label no longer names what it plots (owner: "confusing; fix"). Owner-confirmed design: (a) RENAME the default option to what it is (the epsilon curve; stays default); (b) ADD a new mode = DISCRETE STICKS in km/mol, one vertical line per mode at the actual table/spectrum_line.txt values (Multiwfn "discrete lines" style). Final combo: epsilon / lines km/mol / absorbance / transmittance.

Output: plot_logic.py gains the 4-entry UNIT_MODES + Scene stick/segment fields + the pure lines derivation; gui_plot.py paint_scene gains the segment branch through the ONE paint seam (route-A PNG parity); test/smoke/manual pins updated in the same commits. Panel + tab need ZERO code changes.
</objective>

<execution_context>
@~/.config/opencode/get-shit-done/workflows/execute-plan.md
@~/.config/opencode/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@serpentrum/plot_logic.py
@serpentrum/gui_plot.py
@tests/test_plot_logic.py
@smoke/12_plot_smoke.py
@smoke/manual_plot_check.py

Read-on-demand (verified seams, do NOT re-derive):
- serpentrum/spectra.py:29 — `Mode = namedtuple('Mode', 'index freq intensity vectors')`: the fields are `.freq` and `.intensity` (NOT `.inten`).
- serpentrum/spectra.py:441-495 — CURVE_SCALE = 100.0; broaden() builds the ascending 0..3600 grid (default x_max=None -> 3600) — UNTOUCHED by this plan.
- serpentrum/gui_spectra.py:155 — table header literal `'IR intensity (km/mol)'` is the TABLE's CORRECT literal (it shows real km/mol values) — leave it; the lines-mode AXIS label deliberately reuses the same literal.
- serpentrum/gui_spectra.py:356-357 — the tab's only plot seam: `plot_logic.build_scene(spectrum.modes, fwhm=float(fwhm))` -> `plot_panel.set_scene(scene)`. UNTOUCHED (panel API unchanged).
- tests/run_gates.py:55 REQUIRED_SMOKES — smoke 12 is a required smoke; verdict = flushed SMOKE-OK sentinels, NEVER exit codes (PyMOL swallows rc through the .bat).

Verified facts you can rely on (probed 2026-10-10 by the planner):
- smoke/12_plot_smoke.py STAGE5 is STRUCTURAL (re-verified today): it calls `plot_logic.scene_with_unit(scene, 'transmittance')` with the mode KEY and asserts min-ys ~= 0.1 — NO combo-label literals. It needs no rename fix; it GAINS a stage 6.
- tests/test_gui_pins.py has NO unit-mode / UNIT_MODES source-scans (verified) — untouched.
- smoke/14_release_e2e_smoke.py asserts only structural Scene fields (n_modes/n_imaginary/y_max) + a curve render — trailing namedtuple fields break nothing — untouched.
- Nothing outside plot_logic.py constructs `plot_logic.Scene(...)` (grep-verified): build_scene (keyword args) + scene_with_unit (keyword args) are the only two construction sites; tests use `build_scene` + `_replace`.
- python3.6: `collections.namedtuple` has NO `defaults` kwarg (added 3.7) — BOTH Scene construction sites must pass the new fields explicitly.
- README.md:43 says "y unit / color / x direction / invert / size presets" — generic wording, still true after this change — README intentionally untouched (docs follow the owner-blessed wording at the gate).

HARD CONSTRAINTS (violating any of these fails the task):
- python3.6 syntax ONLY (%-formatting, no f-strings) in all shipped code/tests/smokes.
- plot_logic.py stays PURE: zero pymol/pmg_tk/PyQt5/numpy even inside function bodies (intra-package `from . import spectra` is the purity gate's exempted exception).
- gui_plot.py stays GUI-class (pymol.Qt only; no pymol.cmd, no PyQt5, no numpy; GUI_MODULES single-writer — do NOT add modules to the allowlist).
- No new dependencies; QPainter only (matplotlib is dependency-banned, ARCHITECTURE.md anti-pattern 6).
- Offscreen Qt widget construction is a DEAD END (decision 01-05) — the painter branch is covered by smoke 12's render_image leg + the manual gate, NEVER headless widget tests.
- Gates before every commit (repo root, WSL): `python3.6 tests/run_gates.py` green. Task 2 additionally runs `python3.6 tests/run_gates.py --smoke` (the GUI painter branch changes ship only after its smoke leg is green).
- Do NOT modify: serpentrum/spectra.py, serpentrum/gui_spectra.py, serpentrum/gui.py, serpentrum/data/DATA_SOURCES.md, tests/test_stacking_dataset.py, README.md, ROADMAP.md, .planning/STATE.md, any .planning/phases/08-* file, smoke/14_release_e2e_smoke.py, tests/test_gui_pins.py. NOTHING named `srp_` changes (no viewer work at all).
- Absorbance/transmittance math is FROZEN in place: the normalization/10^-A code in scene_with_unit keeps its exact arithmetic (scale-invariant, owner-approved twice).
- Commit style: Conventional Commits with scope (quick-002). One atomic commit per task; coupled literal pins land in the SAME commit as their source.
</context>

<tasks>

<task type="auto">
  <name>Task 1: Pure half — UNIT_MODES rename + 'lines' mode + Scene stick/segment fields + literal pins</name>
  <files>serpentrum/plot_logic.py, tests/test_plot_logic.py</files>
  <action>
CHOSEN SHAPE — the base curve scene carries the raw stick DATA (`sticks`), and scene_with_unit synthesizes the paint representation (`segments`) for the 'lines' mode. The panel's derive path (`_base_scene` -> `scene_with_unit`) then covers all 4 modes with ZERO GUI changes. Rejected alternatives (do not revisit): (a) a degenerate polyline in xs/ys — drawPolyline would draw diagonal/horizontal connectors between sticks, not the Multiwfn look; (b) passing modes to the panel (set_scene API change) — touches gui_spectra.py + both smoke harnesses for no purity gain.

1. serpentrum/plot_logic.py — `Scene` namedtuple (lines 29-38): append two trailing fields and document them:

```python
Scene = namedtuple(
    'Scene',
    'xs ys x_min x_max y_max x_ticks y_ticks x_label y_label '
    'n_modes n_imaginary fwhm sticks segments')
```

Extend the field comment block below it with:

```python
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
```

2. build_scene (Scene construction at lines 125-137): add the two keyword args to the existing constructor call (keep every existing kwarg byte-identical):

```python
        sticks=tuple((float(m.freq), float(m.intensity))
                     for m in modes),
        segments=None)
```

Add one docstring sentence: the scene now echoes the raw mode sticks (`sticks`) for the discrete-lines derivation; the curve representation itself is unchanged.

3. UNIT_MODES + its comment block (lines 140-150) — replace BOTH with:

```python
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
              ('lines (km/mol)', 'lines'),
              ('absorbance (arb.)', 'absorbance'),
              ('transmittance (arb.)', 'transmittance'))
```

Note the INTERNAL mode key for the default stays 'intensity' (passthrough semantics + existing pins preserved); only the combo LABEL changes. `_UNIT_MODE_KEYS` (line 152) picks up 'lines' automatically.

4. scene_with_unit (lines 155-215) — insert, in this exact order after the existing unknown-mode ValueError check:

```python
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
        # real unit — distinct from the combo label 'lines (km/mol)'.
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
```

Then in the EXISTING absorbance/transmittance tail: keep the `y_label = dict(...)` lookup and the normalization arithmetic byte-identical; only the final `return Scene(...)` gains `sticks=scene.sticks,` and `segments=None,` (a curve unit never carries segments). Update the function docstring: document the 'lines' mode (discrete sticks, no broadening, left-widened x window, empty -> no sticks) and the new ValueError guard (a lines scene never re-derives).

5. Module docstring (lines 1-23): after the sentence listing what the module builds, add: "quick-002 (2026-10-10) adds the discrete-lines representation: the scene echoes the raw mode sticks and scene_with_unit's 'lines' mode synthesizes paint segments (Multiwfn discrete-lines style) — the curve transforms stay untouched."

6. tests/test_plot_logic.py — coupled literal pins (SAME COMMIT as the source):
   - `test_unit_modes_table` (~lines 279-287): label list becomes `['epsilon (Multiwfn curve)', 'lines (km/mol)', 'absorbance (arb.)', 'transmittance (arb.)']`; mode list becomes `['intensity', 'lines', 'absorbance', 'transmittance']`; the default-first pin becomes `self.assertEqual(table[0], ('epsilon (Multiwfn curve)', 'intensity'))` with a comment "the approved look; quick-002 renamed the LABEL only". Extend the TestUnitModes class docstring with one quick-002 provenance sentence.
   - `test_non_y_fields_unchanged` (~lines 343-354): inside the existing loop add `self.assertEqual(derived.sticks, self.scene.sticks)` and `self.assertIsNone(derived.segments)`.
   - NEW class `TestLinesMode` (after TestUnitModes; fixture constants PEAK_INTEN = 257.1018 already exist at module top). setUpClass: `cls.spectrum = spectra.parse_g98(G98_PATH)`; `cls.scene = plot_logic.build_scene(cls.spectrum.modes)`; `cls.lines = plot_logic.scene_with_unit(cls.scene, 'lines')`. Class docstring carries the quick-002 provenance (owner directive 2026-10-10; discrete sticks at table values; no broadening; empty -> NO sticks; negatives at negative x — 07-01 freq_label governs TABLE text, not plot x; lines never re-derive). Nine tests:
     - test_sticks_echo_raw_mode_data: `scene.sticks == tuple((m.freq, m.intensity) for m in spectrum.modes)`; `len(scene.sticks) == 72`; `scene.segments is None`; `plot_logic.build_scene([]).sticks == ()`.
     - test_segments_one_baseline_rooted_stick_per_mode: `len(lines.segments) == 72`; each `segment == ((freq, 0.0), (freq, inten))` zipped against scene.sticks IN ORDER; `lines.xs == ()` and `lines.ys == ()` (no curve data rides a lines scene).
     - test_axis_labels: `lines.y_label == 'IR intensity (km/mol)'`; `lines.x_label == 'wavenumber (cm-1)'`; `_is_ascii(lines.y_label)`.
     - test_y_max_headroom_over_peak_intensity: `assertAlmostEqual(lines.y_max, PEAK_INTEN * 1.1, delta=1e-9)`; every y_ticks value within [0, y_max].
     - test_negative_frequencies_widens_x_min_left: `assertAlmostEqual(lines.x_min, -31.9175, delta=1e-9)` (fixture modes 1-3 are -31.9175/-23.0766/-18.1086; x_min widens LEFT of the curve's 0.0); `lines.x_max == scene.x_max` (3600.0 — the right bound stays the curve window); x_ticks strictly ascending.
     - test_empty_modes_no_sticks: `build_scene([])` -> 'lines': `segments == ()`; `y_max == plot_logic.Y_MAX_FLOOR`; `x_min == 0.0` (never fabricate; sane axis).
     - test_fwhm_irrelevant: `build_scene(modes, fwhm=32.0)` -> 'lines' has `segments ==` the fwhm=8 lines segments (discrete by definition — broadening does not apply).
     - test_counts_and_fwhm_passthrough: `lines.n_modes == 72`; `lines.n_imaginary == 3`; `lines.fwhm == scene.fwhm`; `lines.sticks == scene.sticks`.
     - test_lines_scene_never_rederives: for mode in ('lines', 'absorbance', 'transmittance'): `assertRaises(ValueError)` around `plot_logic.scene_with_unit(self.lines, mode)`.
   - Do NOT touch: test_ascii_labels (the 'epsilon (L mol-1 cm-1)' pin at ~line 200 stays — the axis label is unchanged), test_intensity_passthrough, test_absorbance_peak_one, test_transmittance_bounds_and_peak, test_empty_scene_safe, TestNiceTicks/TestBuildScene/TestSizePresets/TestModeCaption.
  </action>
  <verify>python3.6 -m unittest discover -s tests -p "test_plot_logic.py" -v — all green (updated literal pins + 9 new TestLinesMode tests). Then python3.6 tests/run_gates.py from repo root — full default battery green (986 baseline + 9 new ≈ 995; exact total printed by the gate).</verify>
  <done>UNIT_MODES carries the 4 owner-confirmed entries with 'epsilon (Multiwfn curve)' first (default); build_scene echoes sticks (72 pairs for the fixture, () for empty); scene_with_unit('lines') returns a segments-carrying scene with axis 'IR intensity (km/mol)', x_min widened to -31.9175 for the fixture, Y_MAX_FLOOR y axis for empty modes, and fwhm-independent segments; absorbance/transmittance arithmetic byte-untouched and a lines scene raises on re-derivation; plot_logic still PURE; full default gate green.</done>
  Commit: `feat(quick-002): rename epsilon unit mode + add km/mol discrete-lines mode (pure half)`
</task>

<task type="auto">
  <name>Task 2: GUI half — paint_scene segment branch + smoke 12 STAGE6 + manual gate checklist</name>
  <files>serpentrum/gui_plot.py, smoke/12_plot_smoke.py, smoke/manual_plot_check.py</files>
  <action>
1. serpentrum/gui_plot.py — `paint_scene` curve block (lines 213-234): restructure into ONE representation branch. Replace the whole block (from the `# --- Curve:` comment through `painter.restore()`) with:

```python
    # --- Representation (quick-002, 2026-10-10): a curve scene draws
    #     ONE float QPolygonF polyline (probe stage2: 701-point
    #     QPolygonF paints+saves fine); a discrete-lines scene carries
    #     segments instead — one vertical line per mode, drawn with
    #     the SAME pen (color + width 2) and clip rect so route-A
    #     parity and the color/invert options apply unchanged. An
    #     EMPTY segments tuple draws nothing (empty modes -> no
    #     sticks, never fabricated). Clipped to the plot rect
    #     (volume.py:269-272) either way so nothing draws over the
    #     margins. ---
    if line_color is not None:
        curve_color = QtGui.QColor.fromRgbF(
            float(line_color[0]), float(line_color[1]),
            float(line_color[2]))
    else:
        curve_color = QtGui.QColor('#1f4fff')
    painter.save()
    painter.setClipRect(plot)
    painter.setPen(QtGui.QPen(curve_color, 2))
    if scene.segments is not None:
        for (x0, y0), (x1, y1) in scene.segments:
            painter.drawLine(
                QtCore.QPointF(
                    _map_x(x0, scene, plot_left, plot_w, invert_x),
                    _map_y(y0, scene, plot_top, plot_h, invert_y)),
                QtCore.QPointF(
                    _map_x(x1, scene, plot_left, plot_w, invert_x),
                    _map_y(y1, scene, plot_top, plot_h, invert_y)))
    else:
        polygon = QtGui.QPolygonF()
        for i in range(len(scene.xs)):
            polygon.append(QtCore.QPointF(
                _map_x(scene.xs[i], scene, plot_left, plot_w, invert_x),
                _map_y(scene.ys[i], scene, plot_top, plot_h, invert_y)))
        painter.drawPolyline(polygon)
    painter.restore()
```

(The pen construction moves ABOVE the branch; the curve path is behavior-identical to today — the pinned #1f4fff default, width 2, clip rect, single drawPolyline. The lines path routes through the SAME _map_x/_map_y so invert_x/invert_y flip sticks correctly for free, and render_image inherits the branch via the unchanged seam — route-A PNG parity for the lines representation.)

Extend paint_scene's docstring with one paragraph: "A lines scene (scene.segments not None — quick-002 2026-10-10) draws one vertical segment per mode through the same pen/clip path; ticks, margins, and labels are representation-independent (they read the scene's tick/label fields only). An empty segments tuple paints axes only." Add one sentence to the module docstring's seam description: the seam serves curve AND discrete-lines scenes.

2. SpectraPlotPanel: ZERO code changes — the combo populates from plot_logic.UNIT_MODES (now 4 entries), `_unit_mode` defaults to `UNIT_MODES[0][1]` = 'intensity' (unchanged key), and `_derive_scene` routes 'lines' through scene_with_unit. Verify this by reading, not editing.

3. smoke/12_plot_smoke.py — add the lines leg (the painter branch's ONLY automated coverage — headless widget construction is banned, 01-05):
   - Docstring sentinel list (~line 14): add `STAGE6 LINES <bytes>          discrete-lines scene renders to a valid PNG (quick-002)`.
   - New stage function after s_stage5_render_options:

```python
def s_stage6_render_lines(scene):
    # Stage 6 (quick-002 lines leg, 2026-10-10): the discrete-lines
    # scene derives PURELY and renders through the SAME paint_scene
    # seam to a valid PNG (route-A parity for the segment
    # representation — the painter branch's only automated coverage).
    from serpentrum import gui_plot, plot_logic
    l_scene = plot_logic.scene_with_unit(scene, 'lines')
    assert l_scene.segments is not None, 'lines scene carries no segments'
    assert len(l_scene.segments) == 72, \
        'segments %r != 72 modes' % (len(l_scene.segments),)
    assert l_scene.y_label == 'IR intensity (km/mol)', \
        'y_label %r' % (l_scene.y_label,)
    assert all(y0 == 0.0
               for (_x0, y0), (_x1, _y1) in l_scene.segments), \
        'segments must be baseline-rooted'
    img = gui_plot.render_image(l_scene, (640, 400), scale=2)
    size, _tmp = _save_and_assert_png(img, 'lines')
    print('STAGE6 LINES %d bytes' % size, flush=True)
```

   - Runner chain (~line 210): insert `check('stage6_render_lines', lambda: s_stage6_render_lines(_scene[0]))` after the stage5 check (before `check('cleanup', s_cleanup)`).
   - STAGE5 stays byte-untouched (verified structural 2026-10-10 — it asserts no unit-mode NAMES).

4. smoke/manual_plot_check.py — the human checklist must name the new surface (the owner blesses final combo wording live at this gate):
   - Replace the step-h print block (~lines 114-119) so it names the renamed default first, keeping absorbance/transmittance wording:

```python
print('     h. y-unit combo (quick-002): the DEFAULT is now '
      "'epsilon (Multiwfn curve)' - the approved curve", flush=True)
print("        look, y label 'epsilon (L mol-1 cm-1)'; "
      'absorbance - the curve normalizes (peak touches the top '
      'of', flush=True)
print("        the axis), y label becomes 'absorbance (arb.)'; "
      'transmittance - the curve flips (peaks point', flush=True)
print("        DOWN), y label 'transmittance (arb.)', T <= 1 on "
      'the scale', flush=True)
```

   - Immediately after it, add the new lines step:

```python
print("     h2. y-unit combo 'lines (km/mol)' (quick-002): "
      'DISCRETE vertical sticks - one per table row, at the',
      flush=True)
print("        table's (frequency, IR intensity) values; y label "
      "'IR intensity (km/mol)'; sharp lines (NO", flush=True)
print('        broadening, unlike the epsilon curve); stick count '
      'matches the table rows; switching back to', flush=True)
print("        'epsilon (Multiwfn curve)' restores the smooth "
      'curve', flush=True)
```

   - Step a's `'epsilon (L mol-1 cm-1)'` axis-label print (~line 96) stays byte-identical (the axis label is unchanged).
   - Modeless discipline unchanged: .show() only, never exec_.
  </action>
  <verify>python3.6 tests/run_gates.py — default battery green. Then python3.6 tests/run_gates.py --smoke — the required Windows-PyMOL smoke battery green; smoke 12 must flush STAGE0 APP .. STAGE5 OPTIONS .. STAGE6 LINES <bytes> and the final `SMOKE-OK PLOT-RENDER` sentinel (verdict = flushed sentinels, NEVER exit codes — PyMOL swallows rc through the .bat). git status shows NO modifications outside this plan's files_modified list.</verify>
  <done>paint_scene draws discrete-lines scenes through the one seam (same pen/clip/invert/color path — route-A PNG parity) while the curve path is behavior-identical; panel and tab need zero changes; smoke 12 proves the lines scene headless (segments count/label/baseline-root + valid PNG round-trip); the manual gate checklist walks the human through the renamed default and the new lines mode; both gates green.</done>
  Commit: `feat(quick-002): paint discrete-lines scenes + smoke/manual gate updates`
</task>

</tasks>

<verification>
1. `python3.6 tests/run_gates.py` from repo root — green (986 baseline + 9 new pins ≈ 995; exact total printed by the gate).
2. `python3.6 tests/run_gates.py --smoke` — required smoke battery green; smoke 12 flushes STAGE6 LINES + SMOKE-OK PLOT-RENDER.
3. Headless spot-proof (pure, no Qt):

       python3.6 -c "
       import sys; sys.path.insert(0, '.')
       from serpentrum import spectra, plot_logic
       s = spectra.parse_g98('tests/fixtures/xtb/g98.out')
       sc = plot_logic.build_scene(s.modes)
       ls = plot_logic.scene_with_unit(sc, 'lines')
       assert [m for _l, m in plot_logic.UNIT_MODES] == ['intensity', 'lines', 'absorbance', 'transmittance']
       assert plot_logic.UNIT_MODES[0] == ('epsilon (Multiwfn curve)', 'intensity')
       assert len(ls.segments) == 72 and ls.y_label == 'IR intensity (km/mol)'
       assert ls.x_min == min(0.0, min(f for f, _i in sc.sticks)) < 0.0
       assert ls.x_max == sc.x_max and ls.sticks == sc.sticks
       e = plot_logic.scene_with_unit(plot_logic.build_scene([]), 'lines')
       assert e.segments == () and e.y_max == plot_logic.Y_MAX_FLOOR
       print('QUICK002-SPOT-OK')
       "

   (expected final line: QUICK002-SPOT-OK)
4. Approved surfaces untouched: `git diff` shows NO changes to serpentrum/spectra.py, serpentrum/gui_spectra.py, serpentrum/gui.py, README.md, smoke/14_release_e2e_smoke.py, tests/test_gui_pins.py; test_plot_logic.py's absorbance/transmittance tests (test_absorbance_peak_one, test_transmittance_bounds_and_peak) pass UNMODIFIED; the 'epsilon (L mol-1 cm-1)' axis pin (~test line 200) is byte-identical.
5. Scope guard: `git status` lists ONLY the plan's files_modified (plus this plan's own .planning files).
</verification>

<success_criteria>
- Both task commits landed with scope (quick-002); every commit preceded by a green default gate; Task 2's commit preceded by a green --smoke battery.
- Combo reads: 'epsilon (Multiwfn curve)' (default — the approved look, axis 'epsilon (L mol-1 cm-1)', byte-unchanged) / 'lines (km/mol)' (NEW) / 'absorbance (arb.)' / 'transmittance (arb.)'. Wording provisional pending the owner's live blessing at the gate.
- lines mode: one baseline-rooted vertical stick per mode at the actual (freq, intensity) table values, y axis 'IR intensity (km/mol)', NO broadening (fwhm-independent), negative-frequency sticks at negative x (x_min widens left; right bound stays the curve window), empty modes -> zero sticks.
- Absorbance/transmittance math byte-untouched; a lines scene raises ValueError on any re-derivation (lines never feed curve units).
- Route-A parity holds for every unit mode incl. lines (smoke 12 STAGE6 + the unchanged render_image seam).
- Zero frozen-file changes; nothing named srp_ touched; plot_logic still PURE; gui_plot still GUI-class with no new allowlist entries.
</success_criteria>

<output>
After completion, create `.planning/quick/002-epsilon-plot-mode-rename-km-mol-lines-mo/002-SUMMARY.md` (note the provisional combo wording + that the owner blesses final labels live at the GATE V amendment round, per the 2026-10-10 directive).
</output>
