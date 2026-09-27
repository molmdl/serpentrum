"""serpentrum.gui_plot - the SPECTRA-03 IR plot widget (GUI class).

Plan 07-05. DATA-IN: this module consumes the paint-ready ``Scene``
namedtuples built by the PURE half ``plot_logic`` and NEVER recomputes
broadening or ticks (07-RESEARCH-qt-plot.md pitfall 2: paintEvent must
paint, not compute). ONE module-level painter seam,
``paint_scene(painter, rect, scene, show_labels)``, renders the plot
onto ANY paint device: ``IrPlotWidget.paintEvent`` uses it on-screen
and ``render_image`` uses it into a 2x QImage for the save route
(route A — the SAME scene and the SAME look on screen and on disk;
probe stage2/stage4 SMOKE-OK in 07-RESEARCH-qt-plot.md).

The Spectra tab (plan 07-08) embeds ``SpectraPlotPanel``: an
appearance row (y-unit / curve-color / x-direction combos + 'Invert y
axis' + 'Show axis labels' toggles — owner amendment 2026-09-26,
defaults preserving the approved look) and a size/save row
(size-preset combo + Save button) over the plot. The adjustment
surface ends there — NO FWHM control, NO zoom/pan (v2 bait). Save
reporting goes through an optional status_cb
callable(str) the TAB owns: this module NEVER imports pymol.cmd and
spawns no dialogs of its own (the save picker is the static
QFileDialog.getSaveFileName convenience — the static picker carries no
blocking-modal call token, same class as the getOpenFileName precedent
at gui_setup.py:400-411).

QPainter precedents: pmg_qt/volume.py:252-274 paintEvent shape with
antialiasing ON (:266), QFontMetrics-driven margins (:205-207), tick
label dodge (:215-223), curve clip (:269-272), sizeHint QSize(600,200)
(:98-99); dynoplot.py:111-126 aligned drawText forms, :320 update()
on data change. matplotlib is dependency-banned (ARCHITECTURE.md
anti-pattern 6) — QPainter only.

Purity class: GUI (pymol.Qt only; no pymol.cmd, no PyQt5, no numpy;
registered in tools/check_purity.py GUI_MODULES by plan 07-05 Task 1).
python3.6 syntax (%-formatting only — the WSL gate compiles 3.6).
"""
# Fallback (NOT shipped, research [TRAIN] 1): QWidget.grab() renders
# from widget backing state and is unreliable for a never-exposed tab
# page — route A (render_image) needs no widget at all.
from pymol.Qt import QtWidgets, QtCore, QtGui

from . import plot_logic

# The empty-scene hint (ASCII [TRAIN] 2; pinned by smoke 12 stage 4).
EMPTY_HINT = 'run a calculation to plot a spectrum'

# Tick-label collision dodge: skip a tick label when its left edge is
# closer than this to the previously drawn label (volume.py:215-223
# dodge: `x - lastx > w + 2*fw` keeps the label).
_TICK_GAP_CHARS = 2


def _map_x(value, scene, plot_left, plot_w, invert_x=False):
    """Wavenumber value -> plot-local x pixel (reads the scene ONLY).

    invert_x (owner amendment 2026-09-26): descending wavenumber —
    x_max maps to the LEFT edge and x_min to the right (the
    chemistry-conventional 4000 -> 400 journal look).
    """
    span_x = scene.x_max - scene.x_min
    if span_x <= 0.0:  # guard: plot_logic always spans > 0; never divide
        span_x = 1.0
    if invert_x:
        return plot_left + (scene.x_max - float(value)) / span_x * plot_w
    return plot_left + (float(value) - scene.x_min) / span_x * plot_w


def _map_y(value, scene, plot_top, plot_h, invert_y=False):
    """Y value -> plot-local y pixel (reads the scene ONLY).

    PLOT_TOP is the plot rect's top edge (y grows DOWNWARD in device
    coordinates, so a mapped pixel is plot_top + fraction * plot_h).
    Default (invert_y False, the approved look): y = y_max sits at the
    top edge. invert_y True (owner amendment 2026-09-26): the curve
    flips vertically — y = 0 sits at the top edge.
    """
    span_y = scene.y_max
    if span_y <= 0.0:  # guard: plot_logic floors y_max at Y_MAX_FLOOR
        span_y = 1.0
    fraction = float(value) / span_y
    if invert_y:
        return plot_top + fraction * plot_h
    return plot_top + (1.0 - fraction) * plot_h


def paint_scene(painter, rect, scene, show_labels=True,
                invert_x=False, invert_y=False, line_color=None):
    """THE one painter seam: draw the Scene into RECT on any device.

    Used identically by IrPlotWidget.paintEvent and render_image so the
    PNG on disk is pixel-for-pixel the on-screen plot (SPECTRA-03's
    saveable-plot criterion). Antialiasing ON for widget and image
    painters alike (volume.py:266; dynoplot's commented-out :71 is a
    bug-by-omission for curves).

    A None scene paints the axes frame + the centered EMPTY_HINT and
    returns — never a crash. A real zero-curve scene (the pinned
    empty-modes case, spectra.py:465-466) paints as a flat baseline on
    a normal axis, NOT the hint.

    Owner amendments (2026-09-26, checkpoint round 1): invert_x draws
    the wavenumber axis descending (chemistry-conventional 4000 -> 400;
    the tick ITERATION reverses too so drawn pixel positions still
    ascend and the last-pixel label dodge works unchanged); invert_y
    flips the curve vertically (transmittance's journal look);
    line_color, an (r, g, b) float tuple in [0, 1], re-colors the curve
    — None keeps the pinned default blue (#1f4fff) so the approved
    look is exactly preserved.
    """
    painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
    dark = QtGui.QColor('#444444')

    # --- Empty scene: axes frame + centered hint, then return. ---
    if scene is None:
        frame = rect.adjusted(8, 8, -8, -8)
        painter.setPen(QtGui.QPen(dark))
        painter.drawRect(frame)
        painter.drawText(frame, int(QtCore.Qt.AlignCenter), EMPTY_HINT)
        return

    fm = QtGui.QFontMetrics(painter.font())
    fcw = fm.averageCharWidth()

    # --- Margins from QFontMetrics so labels never clip or smear
    #     (volume.py:205-207 — NEVER fixed-35px assumptions; dynoplot's
    #     constants :77-80 are the start point, QFontMetrics widens
    #     the left for the y-tick labels and the rotated y title). ---
    if show_labels:
        left = (fm.height() + 4                # rotated y title
                + max(fm.width(label)
                      for _value, label in scene.y_ticks)
                + fcw * _TICK_GAP_CHARS)
        bottom = fm.height() * 2 + 8           # tick row + x title row
        top = fm.height() // 2 + 4
        right = 12
    else:
        left = 6
        bottom = 6
        top = 4
        right = 12
    plot = rect.adjusted(left, top, -right, -bottom)
    if plot.width() < 10 or plot.height() < 10:
        return  # too small to draw sanely — never crash on a tiny rect

    plot_left = float(plot.left())
    plot_top = float(plot.top())
    plot_w = float(plot.width())
    plot_h = float(plot.height())

    # --- Axes (dark gray; volume.py/dynoplot convention). ---
    painter.setPen(QtGui.QPen(dark))
    painter.drawLine(plot.bottomLeft(), plot.bottomRight())  # x-axis
    painter.drawLine(plot.bottomLeft(), plot.topLeft())      # y-axis

    # --- Ticks: 4px strokes at mapped positions; labels + titles only
    #     when show_labels (the 'Show axis labels' toggle leg). ---
    if show_labels:
        label_h = fm.height()
        last_label_x = None
        # Inverted axes flip the value->pixel direction; iterating the
        # tick list REVERSED restores ascending pixel positions so the
        # last-pixel label dodge below works unchanged (amendment).
        x_ticks = list(scene.x_ticks)
        if invert_x:
            x_ticks.reverse()
        y_ticks = list(scene.y_ticks)
        if invert_y:
            y_ticks.reverse()
        for value, label in x_ticks:
            px = _map_x(value, scene, plot_left, plot_w, invert_x)
            painter.drawLine(int(px), plot.bottom() - 4,
                             int(px), plot.bottom())
            if (last_label_x is not None
                    and px - last_label_x <= fm.width(label)
                    + fcw * _TICK_GAP_CHARS):
                continue  # dodge (volume.py:215-223)
            painter.drawText(
                QtCore.QRect(int(px) - 60, plot.bottom() + 2,
                             120, label_h),
                int(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop),
                label)
            last_label_x = px
        for value, label in y_ticks:
            py = _map_y(value, scene, plot_top, plot_h, invert_y)
            painter.drawLine(plot.left(), int(py),
                             plot.left() + 4, int(py))
            painter.drawText(
                QtCore.QRect(fm.height() + 2,
                             int(py) - label_h // 2,
                             left - fm.height() - 4 - fcw,
                             label_h),
                int(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight),
                label)
        # x title centered below the x-tick labels (ASCII [TRAIN] 2).
        painter.drawText(
            QtCore.QRect(plot.left(),
                         rect.bottom() - label_h,
                         plot.width(), label_h),
            int(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter),
            scene.x_label)
        # y title rotated 90deg at the left-middle (dynoplot.py:111-126
        # aligned forms via the pre-rotated device transform).
        painter.save()
        painter.translate(fm.height() // 2 + 2,
                          plot.top() + plot.height() // 2)
        painter.rotate(-90)
        painter.drawText(
            QtCore.QRect(-plot.height() // 2, -label_h // 2,
                         plot.height(), label_h),
            int(QtCore.Qt.AlignCenter), scene.y_label)
        painter.restore()

    # --- Curve: ONE float QPolygonF (probe stage2: 701-point QPolygonF
    #     paints+saves fine) clipped to the plot rect (volume.py:269-272)
    #     so nothing draws over the margins. ---
    polygon = QtGui.QPolygonF()
    for i in range(len(scene.xs)):
        polygon.append(QtCore.QPointF(
            _map_x(scene.xs[i], scene, plot_left, plot_w, invert_x),
            _map_y(scene.ys[i], scene, plot_top, plot_h, invert_y)))
    # Curve pen: the pinned default blue stays EXACTLY #1f4fff when
    # line_color is None (the approved look); an (r, g, b) tuple re-
    # colors via fromRgbF (owner amendment: blue / red / black).
    if line_color is not None:
        curve_color = QtGui.QColor.fromRgbF(
            float(line_color[0]), float(line_color[1]),
            float(line_color[2]))
    else:
        curve_color = QtGui.QColor('#1f4fff')
    painter.save()
    painter.setClipRect(plot)
    painter.setPen(QtGui.QPen(curve_color, 2))
    painter.drawPolyline(polygon)
    painter.restore()


def render_image(scene, logical_size, scale=2, show_labels=True,
                 invert_x=False, invert_y=False, line_color=None):
    """Route-A save: re-render the Scene into a 2x QImage -> QImage.

    The probe-verified shape (07-RESEARCH-qt-plot.md, stage2/stage4
    SMOKE-OK): QImage at device pixels + white fill +
    setDevicePixelRatio(scale) + the SAME paint_scene seam in LOGICAL
    coordinates. Call ONLY where a Q*Application exists — the real GUI
    always has one; headless callers MUST do the guarded
    QApplication.instance() or QApplication([]) construct first (probe
    RUN A: font access with no app silently hard-kills the process).

    invert_x / invert_y / line_color forward verbatim to paint_scene
    (the route-A invariant: PNG parity with ANY on-screen option state
    — unit, direction, invert, color).
    """
    w, h = logical_size
    img = QtGui.QImage(w * scale, h * scale, QtGui.QImage.Format_RGB32)
    img.fill(QtGui.QColor('white'))
    img.setDevicePixelRatio(float(scale))
    painter = QtGui.QPainter(img)
    paint_scene(painter, QtCore.QRect(0, 0, w, h), scene, show_labels,
                invert_x=invert_x, invert_y=invert_y,
                line_color=line_color)
    painter.end()
    return img


class IrPlotWidget(QtWidgets.QWidget):
    """The broadened-IR plot area: stores a Scene and paints it.

    No caching layer ([TRAIN] 5: set_scene stores, paint reads).
    setMinimumSize floor 320x260 is generous per [TRAIN] 3 — on-screen
    readability is human-verified at 07-06.
    """

    def __init__(self, parent=None):
        super(IrPlotWidget, self).__init__(parent)
        self._scene = None
        self._show_labels = True
        self._invert_x = False
        self._invert_y = False
        self._line_color = None  # None = the pinned default #1f4fff
        self.setMinimumSize(320, 260)

    def sizeHint(self):
        """volume.py:98-99 precedent."""
        return QtCore.QSize(600, 200)

    def set_scene(self, scene):
        """Store the new Scene and request a repaint.

        update() (never repaint()) — dynoplot.py:320; update coalesces
        and v1 has no drag handlers, so no mouse-driven repaints.
        """
        self._scene = scene
        self.update()

    def set_show_labels(self, flag):
        """(Un)draw tick labels + axis titles; the axes/curve persist."""
        self._show_labels = bool(flag)
        self.update()

    def set_invert_x(self, flag):
        """Descending wavenumber axis (chemistry-conventional 4000 ->
        400) when True; ascending (the approved look) when False."""
        self._invert_x = bool(flag)
        self.update()

    def set_invert_y(self, flag):
        """Flip the curve vertically when True (e.g. transmittance's
        journal look); the approved look when False."""
        self._invert_y = bool(flag)
        self.update()

    def set_line_color(self, color_or_None):
        """Re-color the curve: an (r, g, b) float tuple in [0, 1], or
        None to restore the pinned default blue (#1f4fff)."""
        self._line_color = color_or_None
        self.update()

    def paintEvent(self, event):
        """volume.py:252-274 shape: direct paint over the seam, no
        pixmap double-buffer (both precedents skip it)."""
        painter = QtGui.QPainter()
        painter.begin(self)
        paint_scene(painter, self.rect(), self._scene, self._show_labels,
                    invert_x=self._invert_x, invert_y=self._invert_y,
                    line_color=self._line_color)
        painter.end()


class SpectraPlotPanel(QtWidgets.QWidget):
    """The piece the Spectra tab (07-08) embeds.

    TWO control rows over the plot (owner amendment 2026-09-26,
    checkpoint round 1): row A (appearance) holds the y-unit combo
    (plot_logic.UNIT_MODES — intensity default), the curve-color combo
    (blue / red / black), the x-direction combo (ascending / descending
    wavenumber), an 'Invert y axis' checkbox, and the 'Show axis
    labels' toggle; row B holds the size-preset combo
    (plot_logic.size_presets()) and 'Save Plot (PNG)'. The panel keeps
    the BASE intensity Scene and derives the displayed Scene through
    pure plot_logic.scene_with_unit — recompute lives ONLY in the PURE
    half. The panel carries NO status label of its own — save
    reporting goes to the optional status_cb callable(str) the TAB
    sets.
    """

    def __init__(self, parent=None, status_cb=None):
        super(SpectraPlotPanel, self).__init__(parent)
        self._status_cb = status_cb
        self._base_scene = None
        self._unit_mode = plot_logic.UNIT_MODES[0][1]  # 'intensity'
        self.plot = IrPlotWidget(self)

        # --- Row A: appearance (unit / color / direction / toggles).
        self.unit_combo = QtWidgets.QComboBox(self)
        for label, mode in plot_logic.UNIT_MODES:
            self.unit_combo.addItem(label, mode)
        self.color_combo = QtWidgets.QComboBox(self)
        self.color_combo.addItem('blue', None)       # pinned default
        self.color_combo.addItem('red', (1.0, 0.0, 0.0))
        self.color_combo.addItem('black', (0.0, 0.0, 0.0))
        self.xdir_combo = QtWidgets.QComboBox(self)
        self.xdir_combo.addItem('x: ascending', False)
        self.xdir_combo.addItem('x: descending', True)
        self.invert_y_check = QtWidgets.QCheckBox('Invert y axis', self)
        self.invert_y_check.setChecked(False)
        self.labels_check = QtWidgets.QCheckBox('Show axis labels', self)
        self.labels_check.setChecked(True)

        # --- Row B: size preset + save.
        self.size_combo = QtWidgets.QComboBox(self)
        for label, preset in plot_logic.size_presets():
            self.size_combo.addItem(label, preset)
        self.save_btn = QtWidgets.QPushButton('Save Plot (PNG)', self)

        row_appearance = QtWidgets.QHBoxLayout()
        row_appearance.addWidget(QtWidgets.QLabel('y unit:', self))
        row_appearance.addWidget(self.unit_combo)
        row_appearance.addWidget(QtWidgets.QLabel('color:', self))
        row_appearance.addWidget(self.color_combo)
        row_appearance.addWidget(self.xdir_combo)
        row_appearance.addWidget(self.invert_y_check)
        row_appearance.addWidget(self.labels_check)
        row_appearance.addStretch(1)
        row_size = QtWidgets.QHBoxLayout()
        row_size.addWidget(QtWidgets.QLabel('Plot size:', self))
        row_size.addWidget(self.size_combo)
        row_size.addWidget(self.save_btn)
        row_size.addStretch(1)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(row_appearance)
        layout.addLayout(row_size)
        layout.addWidget(self.plot, 1)

        self.unit_combo.currentIndexChanged.connect(self._on_unit_changed)
        self.color_combo.currentIndexChanged.connect(self._on_color_changed)
        self.xdir_combo.currentIndexChanged.connect(self._on_xdir_changed)
        self.invert_y_check.stateChanged.connect(self._on_invert_y)
        self.labels_check.stateChanged.connect(self._on_toggle)
        self.size_combo.currentIndexChanged.connect(self._on_size_changed)
        self.save_btn.clicked.connect(self._on_save)

        # Pin the plot to the DEFAULT preset at construction (same
        # exact-size pin as _on_size_changed) so the first show is
        # already exactly 'medium (640x400)'.
        self._on_size_changed(self.size_combo.currentIndex())

    # --- public seam for the tab -----------------------------------

    def set_scene(self, scene):
        """Store the BASE intensity Scene and forward the unit-derived
        Scene to the plot (data-in; display transforms live purely in
        plot_logic.scene_with_unit)."""
        self._base_scene = scene
        self.plot.set_scene(self._derive_scene())

    # --- internal handlers -----------------------------------------

    def _derive_scene(self):
        """The displayed Scene: the base Scene in the current unit
        mode, or None when no base scene exists yet (the plot then
        shows the empty hint)."""
        if self._base_scene is None:
            return None
        return plot_logic.scene_with_unit(self._base_scene,
                                          self._unit_mode)

    def _report(self, message):
        if self._status_cb is not None:
            self._status_cb(message)

    def _on_unit_changed(self, index):
        mode = self.unit_combo.currentData()
        if mode is None:
            return
        self._unit_mode = mode
        self.plot.set_scene(self._derive_scene())

    def _on_color_changed(self, index):
        self.plot.set_line_color(self.color_combo.currentData())

    def _on_xdir_changed(self, index):
        self.plot.set_invert_x(bool(self.xdir_combo.currentData()))

    def _on_invert_y(self, state):
        self.plot.set_invert_y(self.invert_y_check.isChecked())

    def _on_size_changed(self, index):
        """Pin the plot EXACTLY to the selected (w, h) preset.

        Both minimum AND maximum size are pinned (owner amendment
        2026-09-26, checkpoint round-1 defect c fix): a preset change
        grows AND shrinks the plot deterministically in the layout —
        the plot always matches the chosen preset exactly, and any
        extra window space becomes margin. The window itself stays
        resizable; the plot simply stays preset-sized.

        currentData() gives the (w, h) preset tuple directly; the
        scene is x-range data — resize-responsive by construction,
        NO recompute.
        """
        preset = self.size_combo.currentData()
        if preset is None:
            return
        w, h = preset
        self.plot.setMinimumSize(w, h)
        self.plot.setMaximumSize(w, h)
        self.plot.updateGeometry()
        self.plot.update()

    def _on_toggle(self, state):
        self.plot.set_show_labels(self.labels_check.isChecked())

    def _on_save(self):
        """Static getSaveFileName convenience (gui_setup.py:403 cancel
        guard) -> render_image at 2x -> PNG. Errors report via
        status_cb; this module never imports pymol.cmd for prints.

        Route-A parity (amendment): the CURRENT unit-derived scene and
        the FULL on-screen option state (labels / x-invert / y-invert /
        line color) all forward to render_image, so the PNG matches the
        screen exactly for any option combination.
        """
        scene = self.plot._scene
        if scene is None:
            self._report('nothing to save - run a calculation first')
            return
        path, _filter = QtWidgets.QFileDialog.getSaveFileName(
            self, 'Save spectrum plot', '', 'PNG image (*.png)')
        if not path:
            return  # cancel guard
        if not path.lower().endswith('.png'):
            path += '.png'
        try:
            img = render_image(
                scene, (self.plot.width(), self.plot.height()), scale=2,
                show_labels=self.plot._show_labels,
                invert_x=self.plot._invert_x,
                invert_y=self.plot._invert_y,
                line_color=self.plot._line_color)
            ok = img.save(path, 'PNG')
        except Exception as exc:
            self._report('plot save failed: %s' % exc)
            return
        if ok:
            self._report('plot saved: %s' % path)
        else:
            self._report('plot save failed (Qt returned False)')
