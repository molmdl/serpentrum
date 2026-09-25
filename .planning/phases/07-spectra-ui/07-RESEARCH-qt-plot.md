# Phase 7: Spectra UI — SPECTRA-03 plot widget + save-PNG research

**Researched:** 2026-09-25 (UTC)
**Scope:** the plot half of Phase 7 ONLY — Gaussian-broadened IR plot widget (`QPainter`, no matplotlib) and the save-plot-PNG route. The frequency table / mode vectors / log / Get-Spectra flow belong to the other research half.
**Confidence:** HIGH for the save route and painter precedents (live headless probes + in-repo source); MEDIUM for [TRAIN] items (execution-time verification).

## Summary

The save-PNG open question is **settled by live probe evidence**: painting a `QImage` with `QPainter` and calling `image.save(path, 'PNG')` works in this PyMOL build **without any widget and even without a QApplication** — including in `pymol -cq` headless mode (probe stage2 SMOKE-OK; PNG magic bytes + reload verified). The one hard trap found: **font access (`QFontMetrics` / `drawText`) silently hard-kills the process if no `Q*Application` exists** (probe RUN A output stops dead between sentinels); constructing a **bare `QApplication([])` — no widgets — revives it completely** (probe stage3/stage4 SMOKE-OK). In the real plugin there is always a QApplication, and (new finding) a bare QApplication is also constructible headless, so the renderer is **headless-verifiable** as a REQUIRED smoke.

The recommended shipping route is **route A: one painter seam, two devices** — a single `paint_scene(painter, rect, scene)` draws the plot onto ANY `QPaintDevice`; `paintEvent` paints the widget with it, and Save re-renders the same scene into a `QImage` at 2x pixels and saves. `QWidget.grab()` (route B, the "unverified in PyMOL's Qt build" route from ROADMAP.md:255) is **demoted to fallback** — it's widget-state-dependent and not headless-provable. The widget design follows the two in-repo precedents at file:line granularity: `pmg_qt/volume.py` (paintEvent + antialiasing + QFontMetrics-driven margins + clip region) and `dynoplot.py` (margins + aligned drawText ticks + `update()` on data change). The pure/GUI split follows the `hud_logic` house pattern: a new PURE module `plot_logic.py` builds the scene (broaden wrapper, nice ticks, labels, the shared `-31.9i` formatter) and a new GUI module `gui_plot.py` hosts the widget + size combo + save button; `gui_plot.py` needs one-line registration in `tools/check_purity.py`'s GUI_MODULES (check_purity.py:62-64).

**Primary recommendation:** ship route A (re-render into QImage via the shared painter seam, 2x pixels, `.save(path, 'PNG')`), save-path picker via the verified `QFileDialog.getSaveFileName` static-convenience precedent (gui_setup.py:400-411), no `QWidget.grab()` in v1.

---

## Verified facts

Every claim below cites in-repo source (`file:line`) or the live probe (`smoke/tmp_research_07_plot_probe.py`, executed 2026-09-25 headless via `run-conda-pymol.bat -cq`; verdict = flushed sentinels).

### Build / runtime

- **Qt 5.12.9, PyQt5 5.12.3** in the Windows conda PyMOL (probe stage0: `qVersion=5.12.9 QT_VERSION_STR=5.12.9 PYQT_VERSION_STR=5.12.3`).
- **Windows runtime python is 3.9** (probe stage0: `python=3.9`) — but the repo gate is py3.6 syntax + %-formatting (AGENTS.md; opencode gates compile under python3.6). Do NOT write 3.7+ syntax even though the runtime would accept it.
- In `-cq` headless mode `QApplication.instance()` is `None` (probe stage0).

### Save-PNG route (question 2 — SETTLED by probe)

- **[PROBE stage2] Widget-free, app-free paint+save works.** `QImage(800,600, Format_RGB32)` + `QPainter` (antialiasing, `QPen` width 2, `drawLine` axes, 701-point `QPolygon` `drawPolyline`, float `QPolygonF` variant, darkGray stick dash) → `img.save(pt, 'PNG')` returned `True`; file exists, 13365 bytes, PNG magic bytes match, reloads with width 800. Path was `C:\Users\nglok\AppData\Local\Temp\...png` — a plain Windows path from inside the Windows python, no WSL conversion (runtime needs none; conversion is a dev-side concern, PITFALLS.md:335).
- **[PROBE RUN A] Text WITHOUT any `Q*Application` kills the process.** The run printed every sentinel up to stage2, then died between sentinels at the first font access (no traceback, no Qt message via `qInstallMessageHandler`, no script-end line — a hard abort, matching Qt's "must construct a QGuiApplication before accessing QFontDatabase" class of assertion). **Design consequence: a headless smoke of the plot renderer must construct (or adopt) a QApplication before any `paint_scene` call that touches fonts.** (Root-cause wording is [TRAIN]; the failure/success FACTS are probed.)
- **[PROBE stage3] A bare `QApplication([])` constructs fine headless** (no widgets created; the 01-05 dialog-construction dead end was NOT retried and is NOT needed). The smoke must guard with `if QApplication.instance() is None:` (constructing a second app when one exists warns) — the gadget both paths use is the same.
- **[PROBE stage4] Under that app, all text ops pass:** `QFontMetrics(p.font())` (family `'MS Shell Dlg 2'`, height 25), `drawText(x, y, str)` (volume.py form) and `drawText(x, y, w, h, flags, str)` (dynoplot.py form), PNG valid (magic bytes). In the real GUI runtime a QApplication always exists, so this constraint is smoke-side only.
- **[PROBE stage1] DPI capability:** `QImage.setDevicePixelRatio` EXISTS; a 400x300 image at dpr=2.0 round-trips to logical 200x150. `QImage.deviceIndependentSize` does NOT exist in PyQt5 5.12.3 (binding gap) — do logical-size math manually, if ever needed.
- **[PROBE] `QtGui.QPolygonF` and `QtGui.QPainterPath` exist** and a 701-point `QPolygonF` polyline paints+saves fine — float-coordinate curves are available (preferred over int `QPolygon` rounding for a fine grid).
- **PNG "viewable outside PyMOL" (SPECTRA-03):** the headless-provable half (bytes, magic, reload, size) is done by the smoke; the open-the-file-in-a-viewer half is a human-verify item (planned, not probed).

### `QWidget.grab()` (route B)

- No in-repo source or probe evidence; STACK.md:97 proposed `widget.grab().save(path)` as the save route, and ROADMAP.md:255 flags it "unverified in PyMOL's Qt build". Qt 5.12 documented behavior: `grab()` renders the widget into a `QPixmap` using the widget's own backing state — **[TRAIN]**; behavior for a never-exposed/hidden tab page is unspecified enough to be a risk. **Decision: NOT the shipping route.** Keep as a documented fallback (human-verify only) behind route A, which needs no widget at all.

### QPainter precedents in THIS tree (question 1)

`pymol-src` is a symlinked mirror of the PyMOL 2.5.0 module source; `Pymol-script-repo/plugins/dynoplot.py` is the plugin precedent. Both are importable-source-grounded (ARCHITECTURE.md:40 "F24").

From `pymol-src/modules/pmg_qt/volume.py` (the in-tree, actively-shipped precedent):
- **paintEvent shape:** override paints directly (no pixmap double-buffer): `painter = QtGui.QPainter(); painter.begin(self); painter.setRenderHint(QtGui.QPainter.Antialiasing); ...; painter.end()` — volume.py:252-274.
- **Margins via rect.adjust:** `self.paint_rect = event.rect(); self.paint_rect.adjust(self.left_margin, 0, 0, -self.bottom_margin)` with `left_margin=35, bottom_margin=20` — volume.py:257-258, 87-88.
- **QFontMetrics-driven layout:** `fm = QtGui.QFontMetrics(painter.font())`, `averageCharWidth()/width()/height()` drive tick label placement and value boxes — volume.py:205-207, 184-195.
- **Clip region for the curve:** `painter.setClipRect(...); paintHistogram(...); painter.setClipping(False)` — volume.py:269-272.
- **Per-pixel curve via QPainterPath** (moveTo/lineTo across `rect.width()` columns, lerp) — volume.py:155-174.
- **Tick-with-label-dodge** (skip a tick if it would collide: `if x - lastx > w + 2*fw:`) — volume.py:215-223; vertical equivalent :228-234.
- **sizeHint:** `return QtCore.QSize(600, 200)` — volume.py:98-99.

From `Pymol-script-repo/plugins/dynoplot.py` (plugin-side precedent, PyQt port):
- **Import style:** `from pymol.Qt import QtCore, QtGui, QtWidgets` + `Qt = QtCore.Qt` — dynoplot.py:21-23 (same as volume.py:9-12).
- **paintEvent (minimal):** begin/paint sub-functions/end; NOTE antialiasing is COMMENTED OUT here — dynoplot.py:68-74 (:71). volume.py turns it ON; for a smooth Gaussian curve prefer volume.py's choice.
- **Margins:** fixed inset constants `xmin = rect.left() + 40; xmax = rect.right() - 19; ymin = rect.top() + 10; ymax = rect.bottom() - 29` — dynoplot.py:77-80.
- **Aligned multiline tick labels:** `drawText(x, y, w, h, Qt.AlignHCenter|Qt.AlignBottom, str(label))` / `Qt.AlignVCenter|Qt.AlignRight` — dynoplot.py:111-113, 123-126.
- **`self.update()` (not `repaint()`) on data change** — dynoplot.py:320 (`# repaint`). update() coalesces; volume.py mixes both (e.g. :303 `repaint()`, :732 `update()`). House rule for the plot: `update()` on new data/set_scene; `repaint()` unnecessary in v1 (no drag interactions).
- **No double-buffer pixmap in either precedent** — Qt's raster paint engine handles it.

### `spectra.py` actual API (design target — question 4)

- `Mode = namedtuple('Mode', 'index freq intensity vectors')` — spectra.py:29; negative freqs kept as negatives.
- `Spectrum = namedtuple('Spectrum', 'n_atoms atoms modes')` — spectra.py:36.
- `broaden(modes, fwhm=16.0, x_min=0.0, x_max=None, n_points=800) -> (xs, ys)` — spectra.py:433. Grid: `[x_min, max(3600.0, max_freq + 5*sigma)]` both ends inclusive (:458-464); sigma = fwhm/2.35482 computed at runtime (:430, :456); **empty modes → `(grid, [0.0]*n_points)` zero curve, never an exception** (:465-466); negatives summed (invisible tail: 2.9e-5 of peak at x=0, per docstring :446 and 02-12-PLAN.md:75); zero-intensity modes contribute exactly 0 (:473); raises `ValueError` on `fwhm<=0` or `n_points<2` (:450-455).
- Dispatchers `parse_text`/`parse(path)` (g98 vs vibspectrum sniffing) — spectra.py:478-505. `real_modes(spectrum, threshold=10.0)` — spectra.py:402-418 (threshold on |freq| only; negatives survive).
- Index correspondence g98↔vibspectrum proven with offset = 3N−len(g98 modes) — 02-12-PLAN.md:77; the plot consumes modes by `Mode.index` only for ORDER, the table/vector half owns the table↔vector mapping (Pitfall 12 lives there, not in the plot).
- Fixtures for a renderer smoke: `tests/fixtures/xtb/g98.out` (26 atoms, 72 modes, first block freqs −31.9175/−23.0766/−18.1086; max-intensity 1150.6639 @ 257.1018 km/mol; default grid exactly [0.0, 3600.0]) — spectra.py:12-15 docstring + 02-12-PLAN.md:74-75.

### House GUI/patterns

- **Import style:** `from pymol.Qt import QtWidgets, QtCore` (gui_setup.py:38; gui.py:12) — new module adds `QtGui` to the list.
- **Signals:** `xxx = QtCore.Signal(object)` class attrs (gui_game.py:269, gui_setup.py:71).
- **blockSignals on programmatic combo updates:** gui_setup.py:423-427; gui_game.py:1235-1237.
- **Combo with userData pattern:** `combo.addItem(label, data)`; select by `findData` — gui_setup.py:106-108 (box_combo), 94-97 (demo_combo).
- **File picker:** static-convenience `QtWidgets.QFileDialog.getOpenFileName(self, title, '', filter)`; empty result string = cancel — gui_setup.py:400-411. **`getSaveFileName` is the same static-convenience class** (a static method — no `.exec_()` token in source, so the AST purity gate's exec_ ban (check_purity.py:192-196) is untouched; same allowance the repo already relies on for getOpenFileName + static QMessageBox.warning per gui_setup.py:17-21).
- **Dialog/tab ownership:** page 2 is currently a static placeholder from `_TAB_DEFS` (gui.py:19-23, 62-71); `PluginDialog` owns tab switching (`_on_spectra_requested` → `setCurrentIndex(2)`, gui.py:96-105). Phase 7 replaces the placeholder page with a real Spectra tab (other half) into which this plot panel embeds.
- **Modeless:** `.show()` only; no `.exec_()` anywhere (AGENTS.md; enforced by the AST gate).

### Purity mechanics (question 5)

- GUI allowlist: `GUI_MODULES = {'serpentrum/gui.py', 'serpentrum/gui_setup.py', 'serpentrum/gui_game.py'}` — tools/check_purity.py:62-64. **A new plot GUI module (e.g. `serpentrum/gui_plot.py`) MUST be added to this set deliberately** (per the inert-entry convention note :59-61: entries for not-yet-created files are inert, so the registration edit can land in the SAME plan that creates the file or in a preceding Wave-1 purity plan, mirroring 04-01).
- GUI class rule: ONLY `pymol.Qt`/`pymol.Qt.*` import forms (any level); bare `pymol`/`pmg_tk` and `PyQt5`/`numpy` are violations — check_purity.py:21-23 (table), :144-154. So `gui_plot.py` may NOT import `pymol.cmd` (no viewer access — it doesn't need any).
- **New PURE modules need NO registration** — "Everything else defaults PURE" (:27-31, :56-57, :161-165). `serpentrum/plot_logic.py` is automatically PURE (stdlib-only; imports of `spectra` are intra-package relative and exempt, :95-98).

### Context anchors (Phase 6 seam)

- The plot is drawn AFTER a run completes (06-11-PLAN.md:1-8, HESSIAN_WARNING context); the run record + `last_run['snake_xyz']` anchor live on `_serpentrum` (gui.py:101-103 documents the anchor handoff). The plot widget itself stays data-in: `set_scene(scene)` — the Spectra tab (other half) holds the record and calls it. This keeps SPECTRA-03 plans decoupled from the runner.

---

## [TRAIN] items (unverifiable now — verify at execution/human-verify)

1. **`QWidget.grab()` semantics in Qt 5.12.9/PyQt5 5.12.3:** docs say it renders the widget into a QPixmap from its backing state; for a widget inside a QTab page that was never the current page, contents may be stale/blank. [TRAIN] — only relevant if route A is abandoned; human-verify in that case. Shipping route A does not depend on it.
2. **Unicode glyph coverage in 'MS Shell Dlg 2'** (the headless default; GUI default may differ): U+2212 minus (`−`) and U+207B superscript minus (`cm⁻¹`) are NOT probe-verified for visual rendering (QString accepts them; rendering as boxes is the risk). **Recommendation: ASCII in v1** — `'-31.9i'` (hyphen-minus), `'wavenumber (cm-1)'`, `'IR intensity (km/mol)'`. Upgrade to typographic forms only behind a human eyeball check.
3. **Actual GUI default font metrics size:** headless default was height 25 px; the GUI app font typically renders smaller. Margins/labels are computed from `QFontMetrics(painter.font())` at paint time (volume.py:205 precedent), which makes the layout self-adjusting — but the min-height that keeps labels readable should be human-verified (set a generous `minimumHeight`).
4. **Descending x-axis convention:** chemistry plots IR spectra high→low wavenumber (4000→400); broaden()'s grid is ascending [0, 3600]. SPECTRA-03/REQUIREMENTS don't mandate either; PITFALLS.md:308 only warns against an axis extending below 0. Ascending is mathematically native; descending is chemically conventional (pure-builder flag `reverse_x` makes it a 1-line inversion). **Decision for the planner/owner — recommend ascending for v1 simplicity, flag in the plan.**
5. **Tab-switch repaint cost:** Qt repaints hidden→shown QTab pages via normal paintEvent delivery; an 800-point QPolygonF polyline paint is trivial ([TRAIN]: sub-millisecond; the probe drew 2x701-point polylines with no measurable delay, but no timing was instrumented). No caching layer in v1; recomputed-scene caching lives in `set_scene` (paint reads, never computes).

---

## Recommended design

### Module layout (house pure-builders + thin-GUI pattern)

```
serpentrum/
├── plot_logic.py   # NEW — PURE (no registration needed). WSL python3.6 unit-testable.
└── gui_plot.py     # NEW — GUI class. Requires ONE edit: add 'serpentrum/gui_plot.py'
                    #       to GUI_MODULES in tools/check_purity.py:62-64.
```

### `plot_logic.py` (PURE — stdlib + intra-package `spectra` import exempt)

Proposed API (planner may rename; contracts matter, names don't):

- `Scene` (namedtuple): `xs, ys, x_min, x_max, y_max, x_ticks, y_ticks, x_label, y_label, n_modes, n_imaginary, fwhm`.
  - `x_ticks`/`y_ticks`: list of `(value, label_str)` pairs (pure data — the GUI maps to pixels).
- `build_scene(modes, fwhm=16.0, x_min=0.0, x_max=None, n_points=800) -> Scene`
  - Thin orchestration over `spectra.broaden` (:433): computes y_max as `max(ys) * 1.1` headroom with a **floor** (`y_max = max(y_max, 1.0 km/mol)`-class constant) so the pinned zero-curve case (empty modes, spectra.py:465-466) still gets sensible ticks rather than a zero-range axis.
  - `n_imaginary = count(freq < 0)` — feeds an optional caption like `'3 modes below 0 (imaginary) shown in the table'` (education framing; table owns the rows). Zero-intensity modes need NO handling — exact-0 contribution is spectra.py:473 arithmetic.
- `nice_ticks(lo, hi, target=8) -> [(value, label)]` — classic 1/2/2.5/5×10^n step selection, pure and unit-testable; expected anchor: `nice_ticks(0, 3600, 8)` → step 500. Labels via `'%.0f'`-style formatting at the tick's own precision.
- `format_freq(freq) -> str` — **the shared imaginary formatter:** `'%.1fi' % freq` for negatives (`-31.9175` → `'-31.9i'`, matching REQUIREMENTS.md SPECTRA-05's `−31.9i` example with ASCII hyphen), `'%.1f'` for non-negatives. **The table half (SPECTRA-05) imports THIS function** so plot captions and table rows render identically — coordinate with the other researcher/half to keep it the single convention (lives here because it's plot-side first; equally fine in `spectra.py` if the planner prefers).
- `size_presets() -> [(label, (w, h))]` — the "plot size" adjustment data: e.g. `('medium (640x400)', (640,400))`, `('large (800x500)', (800,500))`, `('wide (960x500)', (960,500))`. Pure data; GUI renders combo items via the house `addItem(label, data)` pattern.

Tests (WSL 3.6, zero stubs, house style): tick anchors incl. zero-range and negative-lo behavior; scene from the committed `g98.out` fixture (max point within ±fwhm of 1150.6639; y_max floor on empty; n_imaginary == 3 for the dimer); `format_freq` table (`-31.9175→'-31.9i'`, `0.0→'0.0'`, `1150.6639→'1150.7'`); size preset sanity. Sources: spectra.py:433-475 contracts, 02-12-PLAN.md:74-77 verified anchors.

### `gui_plot.py` (GUI — pymol.Qt only)

- `class IrPlotWidget(QtWidgets.QWidget)`:
  - Holds a `Scene` (or `None` → paints axes + a centered "run a calculation to plot a spectrum"-class hint; empty-spectrum pin renders as a flat baseline per spectra.py:465-466).
  - `sizeHint()` (volume.py:98-99 precedent) + `setMinimumSize(...)` from the active preset.
  - `set_scene(scene)`: store + `self.update()` (dynoplot.py:320 pattern).
  - `set_size_preset(w, h)`: resize/minimum-size + `update()`; grid recomputation is NOT needed (scene is x-range data, paint maps to current rect — resize-responsive by construction).
  - `paintEvent(event)`: dynoplot minimal shape (:68-74) calling the seam below with `painter.begin(self)`.
- **`paint_scene(painter, rect, scene)` — the one painter seam (module-level function)**, used identically by `paintEvent` and by save:
  - volume.py pattern: antialiasing ON (:266), margins — start from dynoplot constants (:77-80) but let `QFontMetrics` (volume.py:205-207) widen the left margin to fit y-tick labels (`fm.width(...)` over the tick label strings from the scene).
  - x/y axes: `drawLine`; ticks: short strokes + aligned `drawText` labels (dynoplot.py:98-130 pattern) with the volume.py dodge (`if x - lastx > w + 2*fw:`, :220) so small widgets never smear labels.
  - Axis titles: x = `'wavenumber (cm-1)'`, y = `'IR intensity (km/mol)'` (ASCII per [TRAIN] #2).
  - Curve: map scene `xs/ys` → `QPolygonF` float polyline (probe-verified) inside `rect`; clip to the plot rect (volume.py:269-272) so nothing draws over margins.
- `class SpectraPlotPanel(QtWidgets.QWidget)` (the piece the Spectra tab embeds):
  - `IrPlotWidget` + a control row: **size combo** (house `addItem(title, preset)` pattern from `box_combo`, gui_setup.py:106-108) + **"Save Plot (PNG)"** button. Optionally a **"Show axis labels"** checkbox (the other half of "minimal adjustments" — toggles titles/tick labels, default ON).
  - "Minimal adjustments (plot size, axis labels)" (SPECTRA-03) interpreted concretely as: **size preset combo + axis-label toggle** — and nothing else in v1 (explicitly NO FWHM control, NO zoom/pan; those are v2 bait).
  - `save_requested`-style signal emission is unnecessary — the button handler is local: picker → `render_png(path)`; errors surface in the caller-owned status label via a small status callback or return-and-report (match how the other half wires status).
- **Save implementation (route A — SHIPPING):**
  ```python
  def render_image(scene, logical_size, scale=2):
      w, h = logical_size
      img = QtGui.QImage(w * scale, h * scale, QtGui.QImage.Format_RGB32)
      img.fill(QtGui.QColor('white'))
      img.setDevicePixelRatio(float(scale))   # probe-verified c2
      painter = QtGui.QPainter(img)
      paint_scene(painter, QtCore.QRect(0, 0, w, h), scene)  # logical coords
      painter.end()
      return img
  ```
  `img.save(path, 'PNG')` (probe rc + reload + magic verified). Same scene → identical on-screen and on-disk plot. `path` comes from `QtWidgets.QFileDialog.getSaveFileName(self, 'Save spectrum plot', '', 'PNG image (*.png)')` (static convenience, getOpenFileName precedent gui_setup.py:400-411). Append `.png` if the user omitted it (getSaveFileName doesn't auto-append on all platforms — [TRAIN], cheap to handle). Default dir: empty string (Qt remembers last dir), matching repo convention.
- **Route B (`QWidget.grab()`): documented, unshipped fallback** — one comment + an open question; ship only if route A hits a real wall at human-verify.

### Headless smoke (REQUIRED-class, house protocol)

`smoke/12_plot_smoke.py` (dev-side, not a plugin module — purity gate walks `serpentrum/` only, check_purity.py:49-50):
1. `app = QApplication.instance() or QApplication([])` (probe-verified guarded construct — **this is the load-bearing finding that makes the renderer smoke-able at all**).
2. `spectra.parse_g98('tests/fixtures/xtb/g98.out')` via a Windows-side path; `plot_logic.build_scene(spectrum.modes)`.
3. `img = gui_plot.render_image(scene, (800, 500), scale=2)` → save to a temp PNG; assert magic bytes + nonzero size + reload width == 1600.
4. Flushed sentinel lines per house convention (AGENTS.md smoke verdict rule — never exit codes).

This exercises the pure builders against the REAL fixture and the full painter seam (fonts included) headlessly. **Human-verify remainder:** the on-screen look in the real tab, the size combo reflow, opening the PNG in a viewer, and the empty/imaginary-heavy spectrum cosmetics.

---

## Pitfalls (what could sink the plot plans)

1. **Font access without a Q*Application = silent process kill.** [PROBE RUN A: sentinels stop with no traceback.] Any render path invoked before an app exists aborts PyMOL entirely (a crash-class worse than an exception). Avoid: guarded app construction in the smoke (verified pattern above); never call render code at import time or from a non-Qt context.
2. **`paintEvent` computing, not painting.** Re-running `broaden` or tick selection inside paint means recompute on every repaint (resize, tab switch, expose). The scene is built once in `set_scene`; `paint_scene` only maps. (800×72 Gaussian evaluations aren't expensive, but tabs/exposes are unpredictable — keep paint O(points).)
3. **Tick-label collisions / clipping into margins.** Avoid with the volume.py dodge (:220) + QFontMetrics-driven margins (:205-207, 184-195), NOT fixed-35px assumptions.
4. **Antialiasing OFF** (dynoplot's commented-out line :71 looks like a bug-by-omission for curves): follow volume.py (:266) and enable it on widget AND QImage painters alike.
5. **Y-axis zero-range on the empty/zero curve.** The pinned zero-curve (spectra.py:465-466) gives `max(ys) == 0.0`; a `y_max = 0` axis breaks tick math (division-by-span). Floor y_max (design above) and unit-test the empty scene.
6. **`.png` filename suffix + cancel handling.** `getSaveFileName` returns `''` on cancel — guard (gui_setup.py:403 precedent `if path:`); don't `.save('')` (Qt returns False silently). Append `.png` if missing.
7. **Repaint loops via `repaint()` in event handlers.** Use `update()` on data change (dynoplot.py:320); v1 has no drag handlers, so no mouse-driven repaints at all.
8. **Purity drift:** `gui_plot.py` importing `pymol.cmd` "just for a status print" fails the GUI allowlist (check_purity.py:144-154) — status/log output goes through the Spectra tab (other half). PyQt5/numpymatplotlib imports are always banned (:152-154); matplotlib is dependency-banned outright (ARCHITECTURE.md Anti-Pattern 6; PITFALLS.md:339 grep-verified "no matplotlib in the tree").
9. **Python-version drift:** runtime is 3.9 (probe) but the WSL gate compiles 3.6 — %-formatting, no f-strings, no walrus (repo gate discipline).
10. **Cross-half drift on the imaginary formatter:** if the table half hand-rolls `'%.1fi'` elsewhere, plot captions and table rows can diverge (e.g. rounding edges like GHz-mode 53's 5e-5 class). Single shared function in `plot_logic` (or `spectra.py`), imported by both halves — coordinate at planning.
11. **Hidden-tab-page paint state:** the plot must NOT depend on being visible (route A doesn't; this is exactly what makes route B `grab()` risky — [TRAIN] #1). Also: a `set_scene` arriving while the tab is on page 0/1 is fine — Qt repaints on first expose.
12. **Windows-path handling at save:** plugin runtime is all-Windows — a `C:\...` string from the picker saves directly (probe path proved it); NO WSL conversion at runtime (PITFALLS.md:335 reserves conversion for dev-side smokes, where the smoke's temp path IS already Windows-native inside the Windows python).

---

## Open questions for the planner

1. **Module split for the Spectra tab:** is `gui_plot.py`'s `SpectraPlotPanel` embedded by the other half's `SpectraTab` (replaces the gui.py:62-71 placeholder), or does the plot plan OWN a standalone `serpentrum/gui_spectra.py`-style page with the other pieces composited later? Recommended: separate GUI modules (plot vs tab/container) — both registered in GUI_MODULES — to keep parallel plans non-conflicting on gui.py edits (gui.py page-2 registration is a ONE-SLOT edit; sequence it).
2. **Ascending vs descending wavenumber axis** ([TRAIN] #4) — owner-visible convention choice; recommend ascending + a `reverse_x` builder flag so swapping is data-only.
3. **"Minimal adjustments" final cut:** proposed = size combo + axis-label toggle. Confirm no FWHM control in v1 (roadmap's "minimal" reading) — a hidden FWHM choice would silently fork the plotted curve from any future "reference" annotation.
4. **Register `format_freq` in plot_logic vs spectra.py** — needs joint decision with the table/vectors half so exactly one formatter exists.
5. **Human-verify scope for the PNG:** probe proves bytes/reload, not "looks right in a real viewer" — the plan should carry a checkpoint that opens `smoke`-saved and GUI-saved PNGs on the Windows desktop.
6. **`QWidget.grab()`:** permanently dropped from v1, or kept as a human-verify science project? (Recommendation: drop — route A is strictly more verifiable.)

## Sources

- **[PROBE]** `smoke/tmp_research_07_plot_probe.py` — executed 2026-09-25 headless (`run-conda-pymol.bat -cq`) as three staged runs then consolidated into this one file (re-run green: stages 0-4 all SMOKE-OK). All Qt-build, save-route, font, and DPI claims above cite its sentinels. (Throwaway research artifact; a real `smoke/12_plot_smoke.py` supersedes it at execution.)
- **[SRC]** `pymol-src/modules/pmg_qt/volume.py:9-12,87-88,98-99,155-174,184-207,215-234,252-274,269-272` (QPainter editor widget precedent, in PyMOL 2.5.0 source tree)
- **[SRC]** `Pymol-script-repo/plugins/dynoplot.py:21-23,68-130,320,37` (plugin-angle precedent)
- **[SRC]** `serpentrum/spectra.py:29,36,402-418,430,433-505` (Mode/Spectrum/broaden/parse contracts)
- **[SRC]** `tools/check_purity.py:21-31,49-50,56-73,95-98,144-165,192-196` (purity classes + registration mechanics)
- **[SRC]** `serpentrum/gui_setup.py:17-21,38,71,106-108,400-411,423-427`; `serpentrum/gui.py:12,19-23,62-71,96-105`; `serpentrum/gui_game.py:269,1235-1237` (house Qt/pattern precedents)
- **[PLAN]** `.planning/phases/02-pure-core-game-chemistry-logic/02-12-PLAN.md:74-77` (verified fixture anchors: 72 modes, 1150.6639@257.1018, 2.9e-5 tail ratio, FWHM arithmetic)
- **[PLAN]** `.planning/phases/06-xtb-pipeline/06-11-PLAN.md:1-8` (post-run drawing context, HESSIAN_WARNING)
- **[PLAN]** `.planning/ROADMAP.md:244-255` (Phase 7 scope, grab() caution); `.planning/REQUIREMENTS.md:52,54` (SPECTRA-03/05 wording incl. `−31.9i`); `.planning/research/ARCHITECTURE.md:40,388-391` (F24 QPainter decision, matplotlib anti-pattern); `.planning/research/PITFALLS.md:308,335,339,366` (axis-below-0 warning, path-conversion boundary, no-matplotlib, imaginary display)
- **[TRAIN]** items: QWidget.grab semantics; font glyph coverage; chemistry axis convention — all flagged inline above.

## Metadata

**Confidence breakdown:**
- Save-PNG route: HIGH (live probe, this exact build/OS)
- QPainter precedent patterns: HIGH (in-tree source at file:line)
- spectra.broaden contract / pure split: HIGH (committed code + pinned plan facts)
- Purity registration: HIGH (gate source read)
- [TRAIN] list: all marked; none load-bearing for the shipping design

**Research date:** 2026-09-25 (UTC)
**Valid until:** ~2026-10-25 (stable Qt 5.12 probe facts; the only fast-moving input is the Phase-6 spectra_run record shape in the other half's plans)
