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

The Spectra tab (plan 07-08) embeds ``SpectraPlotPanel``: a control
row (size-preset combo + 'Show axis labels' toggle + Save button) over
the plot. v1 adjustment surface ends there — NO FWHM control, NO
zoom/pan (v2 bait). Save reporting goes through an optional status_cb
callable(str) the TAB owns: this module NEVER imports pymol.cmd and
spawns no dialogs of its own (the save picker is the static
QFileDialog.getSaveFileName convenience — no .exec_ token, same class
as the getOpenFileName precedent at gui_setup.py:400-411).

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


def _map_x(value, scene, plot_left, plot_w):
    """Wavenumber value -> plot-local x pixel (reads the scene ONLY)."""
    span_x = scene.x_max - scene.x_min
    if span_x <= 0.0:  # guard: plot_logic always spans > 0; never divide
        span_x = 1.0
    return plot_left + (float(value) - scene.x_min) / span_x * plot_w


def _map_y(value, scene, plot_bottom, plot_h):
    """Intensity value -> plot-local y pixel (reads the scene ONLY)."""
    span_y = scene.y_max
    if span_y <= 0.0:  # guard: plot_logic floors y_max at Y_MAX_FLOOR
        span_y = 1.0
    return plot_bottom - float(value) / span_y * plot_h


def paint_scene(painter, rect, scene, show_labels=True):
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
    plot_bottom = float(plot.bottom())
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
        for value, label in scene.x_ticks:
            px = _map_x(value, scene, plot_left, plot_w)
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
        for value, label in scene.y_ticks:
            py = _map_y(value, scene, plot_bottom, plot_h)
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
            _map_x(scene.xs[i], scene, plot_left, plot_w),
            _map_y(scene.ys[i], scene, plot_bottom, plot_h)))
    painter.save()
    painter.setClipRect(plot)
    painter.setPen(QtGui.QPen(QtGui.QColor('#1f4fff'), 2))
    painter.drawPolyline(polygon)
    painter.restore()


def render_image(scene, logical_size, scale=2, show_labels=True):
    """Route-A save: re-render the Scene into a 2x QImage -> QImage.

    The probe-verified shape (07-RESEARCH-qt-plot.md, stage2/stage4
    SMOKE-OK): QImage at device pixels + white fill +
    setDevicePixelRatio(scale) + the SAME paint_scene seam in LOGICAL
    coordinates. Call ONLY where a Q*Application exists — the real GUI
    always has one; headless callers MUST do the guarded
    QApplication.instance() or QApplication([]) construct first (probe
    RUN A: font access with no app silently hard-kills the process).
    """
    w, h = logical_size
    img = QtGui.QImage(w * scale, h * scale, QtGui.QImage.Format_RGB32)
    img.fill(QtGui.QColor('white'))
    img.setDevicePixelRatio(float(scale))
    painter = QtGui.QPainter(img)
    paint_scene(painter, QtCore.QRect(0, 0, w, h), scene, show_labels)
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

    def paintEvent(self, event):
        """volume.py:252-274 shape: direct paint over the seam, no
        pixmap double-buffer (both precedents skip it)."""
        painter = QtGui.QPainter()
        painter.begin(self)
        paint_scene(painter, self.rect(), self._scene, self._show_labels)
        painter.end()


class SpectraPlotPanel(QtWidgets.QWidget):
    """The piece the Spectra tab (07-08) embeds.

    Control row: size-preset combo (house addItem(label, data) pattern
    over plot_logic.size_presets()) + 'Show axis labels' toggle
    (default ON) + 'Save Plot (PNG)' button. The panel carries NO
    status label of its own — save reporting goes to the optional
    status_cb callable(str) the TAB sets.
    """

    def __init__(self, parent=None, status_cb=None):
        super(SpectraPlotPanel, self).__init__(parent)
        self._status_cb = status_cb
        self.plot = IrPlotWidget(self)

        self.size_combo = QtWidgets.QComboBox(self)
        for label, preset in plot_logic.size_presets():
            self.size_combo.addItem(label, preset)
        self.labels_check = QtWidgets.QCheckBox('Show axis labels', self)
        self.labels_check.setChecked(True)
        self.save_btn = QtWidgets.QPushButton('Save Plot (PNG)', self)

        row = QtWidgets.QHBoxLayout()
        row.addWidget(QtWidgets.QLabel('Plot size:', self))
        row.addWidget(self.size_combo)
        row.addWidget(self.labels_check)
        row.addWidget(self.save_btn)
        row.addStretch(1)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(row)
        layout.addWidget(self.plot, 1)

        self.size_combo.currentIndexChanged.connect(self._on_size_changed)
        self.labels_check.stateChanged.connect(self._on_toggle)
        self.save_btn.clicked.connect(self._on_save)

    # --- public seam for the tab -----------------------------------

    def set_scene(self, scene):
        """Forward the new Scene to the plot (data-in; no recompute)."""
        self.plot.set_scene(scene)

    # --- internal handlers -----------------------------------------

    def _report(self, message):
        if self._status_cb is not None:
            self._status_cb(message)

    def _on_size_changed(self, index):
        # currentData() gives the (w, h) preset tuple directly; the
        # scene is x-range data — resize-responsive by construction,
        # NO recompute.
        preset = self.size_combo.currentData()
        if preset is None:
            return
        w, h = preset
        self.plot.setMinimumSize(max(w, 320), max(h, 260))
        self.plot.updateGeometry()
        self.plot.update()

    def _on_toggle(self, state):
        self.plot.set_show_labels(self.labels_check.isChecked())

    def _on_save(self):
        """Static getSaveFileName convenience (gui_setup.py:403 cancel
        guard) -> render_image at 2x -> PNG. Errors report via
        status_cb; this module never imports pymol.cmd for prints."""
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
                show_labels=self.plot._show_labels)
            ok = img.save(path, 'PNG')
        except Exception as exc:
            self._report('plot save failed: %s' % exc)
            return
        if ok:
            self._report('plot saved: %s' % path)
        else:
            self._report('plot save failed (Qt returned False)')
