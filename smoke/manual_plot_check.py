"""REAL-GUI plot-check harness - plan 07-06 human-verify (SPECTRA-03).

This is NOT a headless smoke: the non-NN_ name keeps
tests/run_gates.py --smoke (glob smoke/[0-9][0-9]_*.py) from ever
auto-running it. Run it MANUALLY inside a real Windows PyMOL GUI from the
PyMOL command line:

    run smoke\\manual_plot_check.py

What it stages (07-RESEARCH-qt-plot.md [TRAIN] items 2-5):
  - parses the committed 72-mode dimer fixture
    (tests/fixtures/xtb/g98.out) via spectra.parse_g98 and builds the
    paint-ready Scene via plot_logic.build_scene - the SAME scene the
    headless smoke 12 proves
  - hosts ONE gui_plot.SpectraPlotPanel (size-preset combo +
    'Show axis labels' toggle + 'Save Plot (PNG)') in a modeless
    top-level QWidget window so the human can verify the on-screen
    look, the combo reflow, the label toggle, and the save-PNG route
  - routes the panel's save reports (status_cb=print) to the PyMOL
    console so 'plot saved: <path>' is visible inline

Template rules (per smoke/manual_wizard_keys_check.py): the non-NN_
filename, defensive _resolve_root() via serpentrum/__init__.py (NEVER
trust __file__ under run/exec), sys.path insert, flush=True prints,
no exec_ calls anywhere. One DELIBERATE difference from that template:
THIS harness constructs widgets - legal here because the real GUI has
a live QApplication and event loop (the 01-05 dead end was HEADLESS
dialog construction only). Modeless discipline still applies: .show()
only, NEVER the exec_ call.

Fail-cheap contract: if the human rejects the render, fixes land in
gui_plot.py/plot_logic.py and THIS checkpoint re-runs - the tab plans
(07-07+) have not started embedding yet (the 04-07 house precedent).
"""
import os
import sys


def _resolve_root():
    """Repo root, defensively (identical to the smoke template)."""
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

from pymol.Qt import QtWidgets  # noqa: E402 (inside the PyMOL runtime)
from serpentrum import spectra  # noqa: E402
from serpentrum import plot_logic  # noqa: E402
from serpentrum import gui_plot  # noqa: E402

# --- scene: the SAME dimer fixture the headless smoke 12 proves --------
FIXTURE = os.path.join(ROOT, 'tests', 'fixtures', 'xtb', 'g98.out')
spectrum = spectra.parse_g98(FIXTURE)
scene = plot_logic.build_scene(spectrum.modes)
print('HARNESS scene: %d modes (%d imaginary), peak framed by '
      'build_scene, fixture g98.out'
      % (scene.n_modes, scene.n_imaginary), flush=True)

# --- modeless top-level host window ------------------------------------
# Module-level reference: the window must NOT be garbage-collected while
# the human probes it (no parent holds it - it is the top level).
CHECK_WINDOW = QtWidgets.QWidget()
CHECK_WINDOW.setWindowTitle(
    'serpentrum plot check - close PyMOL when done')
layout = QtWidgets.QVBoxLayout(CHECK_WINDOW)
# status_cb=print: the panel's save reports land in the PyMOL console.
panel = gui_plot.SpectraPlotPanel(CHECK_WINDOW, status_cb=print)
layout.addWidget(panel)
panel.set_scene(scene)
CHECK_WINDOW.resize(700, 560)
CHECK_WINDOW.show()  # MODELESS - never the exec_ call
print('HARNESS panel staged and shown (modeless).', flush=True)

# --- the numbered human checklist (mirrors the 07-06 checkpoint) -------
print('HARNESS how to verify:', flush=True)
print('  1. gates in WSL: python3.6 tests/run_gates.py --smoke must show '
      "'smoke/12_plot_smoke.py: PASS' with a SMOKE-OK sentinel",
      flush=True)
print('  2. (you just ran: run smoke\\manual_plot_check.py)', flush=True)
print('  3. on the staged panel, verify in order:', flush=True)
print('     a. broadened curve renders smoothly (antialiased); axes + '
      'tick labels legible;', flush=True)
print("        y label 'IR intensity (km/mol)' readable (rotated); "
      "x label 'wavenumber (cm-1)' below", flush=True)
print('     b. x axis runs ASCENDING 0 -> 3600 (v1 convention - say so '
      'in your verdict)', flush=True)
print('     c. switch the size combo (medium/large/wide) - the widget '
      'reflows, labels never', flush=True)
print('        smear or clip into margins', flush=True)
print("     d. uncheck/recheck 'Show axis labels' - titles + tick "
      'labels hide/show; the curve stays', flush=True)
print("     e. click 'Save Plot (PNG)', choose a Windows path (e.g. "
      "Desktop) - console prints", flush=True)
print("        'plot saved: ...'", flush=True)
print('     f. open the saved PNG OUTSIDE PyMOL (Explorer/Paint) - it '
      'matches the on-screen plot', flush=True)
print('        (labels, curve, white background) and is a real PNG',
      flush=True)
print('     g. resize the PyMOL window/panel - no crashes, no label '
      'garbage at small sizes', flush=True)
print('  4. report any visual defect precisely (which step, what looks '
      'wrong)', flush=True)

print('PLOT-CHECK-STAGED', flush=True)
