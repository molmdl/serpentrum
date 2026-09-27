"""Headless Windows PyMOL plot-renderer smoke — 07-05 (SPECTRA-03).

Run (from repo root; cwd is /mnt/c-backed so cmd.exe inherits C:\\ cwd):
    timeout 90 cmd.exe /c "C:\\src\\run-conda-pymol.bat -cq smoke\\12_plot_smoke.py"

Exit codes through the .bat are ALWAYS 0 (even after a Qt C-abort) —
verdicts are flushed sentinels grepped by tests/run_gates.py --smoke:
    STAGE0 APP                    guarded QApplication([]) exists
    STAGE1 SCENE <counts>         fixture g98 parsed + Scene built
    STAGE2 PNG-FULL <bytes>       render_image -> temp PNG: magic bytes +
                                  reload 1600x1000 (800x500 @ scale 2)
    STAGE3 PNG-NOLABELS           show_labels=False leg writes a valid PNG
    STAGE4 PNG-EMPTY              None scene paints the hint, never crashes
    STAGE5 OPTIONS <bytes>        unit/color/invert render parity leg
                                  (owner amendment 2026-09-26)
    SMOKE-OK PLOT-RENDER          all stages passed
    SMOKE-FAIL <stage>: ...       a stage failed (one line per failure)

What this pins (07-RESEARCH-qt-plot.md — the probe's evidence, promoted
to a REQUIRED smoke; supersedes smoke/tmp_research_07_plot_probe.py):
  0. THE LOAD-BEARING APP GUARD (probe RUN A): font access
     (QFontMetrics/drawText) with NO Q*Application silently hard-kills
     the process — no traceback. Stage 0 adopts-or-creates the app
     BEFORE any render. In the real GUI an app always exists; this
     guard is what makes the renderer smoke-able headless at all.
  1. Route A save (probe stage2/stage4): render_image re-renders the
     SAME paint_scene seam into a 2x QImage and img.save(path, 'PNG')
     yields a valid PNG (magic bytes + reload width round-trip).
  2. The 'Show axis labels' toggle leg renders headless (show_labels
     False skips every drawText/QFontMetrics path).
  3. The empty-scene (None) hint path renders without a crash.

Template rules (copied from smoke/01_skeleton_smoke.py / 13):
  - every print carries flush=True (stdout is block-buffered when piped)
  - NO widget construction (headless C-abort is uncatchable) — IMAGES
    ONLY; the bare QApplication has no widgets (probe stage3-safe)
  - never add smoke/__init__.py (findPlugins plugin-path safety)
  - NEVER trust __file__ under -cq (resolve ROOT by validating
    serpentrum/__init__.py candidates)
  - verdict = flushed sentinels ONLY (never exit codes)
"""
import os
import sys
import tempfile


def _resolve_root():
    """Repo root, defensively (copied from smoke/01_skeleton_smoke.py).

    Under -cq exec, __file__ is PyMOL's launcher module (NOT this
    script), so naive dirname(dirname(__file__)) lands in
    site-packages. Validate every candidate by the presence of
    serpentrum/__init__.py.
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

from pymol.Qt import QtWidgets, QtCore, QtGui  # noqa: E402

FAILURES = []
G98_PATH = os.path.join(ROOT, 'tests', 'fixtures', 'xtb', 'g98.out')
TMP_PNGS = []

# PNG magic bytes (probe stage2 assertion).
PNG_MAGIC = b'\x89PNG'


def check(name, fn):
    try:
        fn()
    except Exception as exc:
        print('SMOKE-FAIL %s: %r' % (name, exc), flush=True)
        FAILURES.append(name)


def _save_and_assert_png(img, tag):
    """img.save -> temp PNG; assert file bytes + PNG magic; return size."""
    tmp = os.path.join(tempfile.gettempdir(),
                       'srp_smoke12_plot_%s.png' % tag)
    TMP_PNGS.append(tmp)
    ok = img.save(tmp, 'PNG')
    assert ok, 'QImage.save(%r, PNG) returned False' % tmp
    with open(tmp, 'rb') as fh:
        data = fh.read()
    assert data[:4] == PNG_MAGIC, \
        'first bytes %r != PNG magic' % (data[:4],)
    return len(data), tmp


def s_stage0_app():
    # Stage 0 — THE APP GUARD (probe RUN A): font access without a
    # Q*Application SILENTLY HARD-KILLS the process. Adopt an existing
    # app or construct a BARE one (no widgets — probe stage3 proves
    # this is safe headless). Never construct a second app (warns).
    global _APP
    _APP = QtWidgets.QApplication.instance()
    if _APP is None:
        _APP = QtWidgets.QApplication([])
    print('STAGE0 APP', flush=True)


def s_stage1_scene():
    # Stage 1: parse the committed g98 fixture (real data — 26 atoms /
    # 72 modes / 3 imaginary) and build the Scene via the PURE half.
    # The renderer consumes Scenes ONLY (pitfall 2: never recompute).
    from serpentrum import spectra, plot_logic
    spectrum = spectra.parse_g98(G98_PATH)
    assert spectrum.n_atoms == 26, 'n_atoms %r != 26' % (spectrum.n_atoms,)
    assert len(spectrum.modes) == 72, \
        'modes %r != 72' % (len(spectrum.modes),)
    scene = plot_logic.build_scene(spectrum.modes)
    assert scene.n_modes == 72, 'scene n_modes %r' % (scene.n_modes,)
    assert scene.n_imaginary == 3, \
        'scene n_imaginary %r != 3' % (scene.n_imaginary,)
    print('STAGE1 SCENE modes=%d imaginary=%d n_points=%d y_max=%.2f'
          % (scene.n_modes, scene.n_imaginary, len(scene.xs),
             scene.y_max), flush=True)
    return scene


def s_stage2_render_full(scene):
    # Stage 2: THE SAVE ROUTE. render_image at 800x500 @ scale 2 ->
    # temp PNG; assert PNG magic bytes + reload dimensions 1600x1000
    # (probe stage2/stage4 round-trip), plus a sane nonzero size.
    from serpentrum import gui_plot
    img = gui_plot.render_image(scene, (800, 500), scale=2)
    assert img.width() == 1600 and img.height() == 1000, \
        'image %dx%d != 1600x1000' % (img.width(), img.height())
    size, tmp = _save_and_assert_png(img, 'full')
    reload_img = QtGui.QImage(tmp)
    assert reload_img.width() == 1600 and reload_img.height() == 1000, \
        'reload %dx%d != 1600x1000' % (reload_img.width(),
                                       reload_img.height())
    assert size > 1000, 'suspiciously small PNG: %d bytes' % size
    print('STAGE2 PNG-FULL %s %d bytes' % (tmp, size), flush=True)


def s_stage3_render_nolabels(scene):
    # Stage 3 (axis-toggle leg): 'Show axis labels' OFF renders a valid
    # PNG too (the no-drawText path — no margins/fonts in margins).
    from serpentrum import gui_plot
    img = gui_plot.render_image(scene, (640, 400), scale=2,
                                show_labels=False)
    size, tmp = _save_and_assert_png(img, 'nolabels')
    reload_img = QtGui.QImage(tmp)
    assert reload_img.width() == 1280 and reload_img.height() == 800, \
        'reload %dx%d != 1280x800' % (reload_img.width(),
                                      reload_img.height())
    print('STAGE3 PNG-NOLABELS %d bytes' % size, flush=True)


def s_stage4_render_empty():
    # Stage 4 (empty-scene leg): None scene paints the axes frame +
    # the pinned 'run a calculation to plot a spectrum' hint — never a
    # crash (the real zero-curve scene paths through the normal axis).
    from serpentrum import gui_plot
    img = gui_plot.render_image(None, (640, 400), scale=2)
    size, _tmp = _save_and_assert_png(img, 'empty')
    print('STAGE4 PNG-EMPTY %d bytes' % size, flush=True)


def s_stage5_render_options(scene):
    # Stage 5 (owner-amendment options leg, 2026-09-26): the FULL
    # non-default option combination — transmittance unit (pure derive)
    # + invert_x + invert_y + red line color — renders through the
    # SAME paint_scene seam to a valid PNG (route-A parity regression:
    # the PNG save path must accept every on-screen option state).
    from serpentrum import gui_plot, plot_logic
    t_scene = plot_logic.scene_with_unit(scene, 'transmittance')
    assert abs(min(t_scene.ys) - 0.1) < 1e-6, \
        'transmittance peak %r != 0.1' % (min(t_scene.ys),)
    img = gui_plot.render_image(t_scene, (640, 400), scale=2,
                                show_labels=True, invert_x=True,
                                invert_y=True, line_color=(1.0, 0.0, 0.0))
    size, _tmp = _save_and_assert_png(img, 'options')
    print('STAGE5 OPTIONS %d bytes' % size, flush=True)


def s_cleanup():
    for path in TMP_PNGS:
        try:
            os.remove(path)
        except Exception:
            pass  # temp-dir leftovers are harmless; never fail cleanup


_APP = None
_scene = [None]
check('stage0_app', s_stage0_app)
if _APP is not None:
    check('stage1_scene', lambda: _scene.__setitem__(0, s_stage1_scene()))
    if _scene[0] is not None:
        check('stage2_render_full', lambda: s_stage2_render_full(_scene[0]))
        check('stage3_render_nolabels',
              lambda: s_stage3_render_nolabels(_scene[0]))
        check('stage4_render_empty', s_stage4_render_empty)
        check('stage5_render_options', lambda: s_stage5_render_options(_scene[0]))
        check('cleanup', s_cleanup)

if FAILURES:
    print('SMOKE-END %d failure(s)' % len(FAILURES), flush=True)
else:
    print('SMOKE-OK PLOT-RENDER', flush=True)
