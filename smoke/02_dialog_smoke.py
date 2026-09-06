"""EXPERIMENTAL offscreen-QApplication dialog construction smoke — INFRA-01.

The one UNVERIFIED mechanism from research Q3: headless PyMOL cannot
construct widgets (QDialog() with no QApplication -> uncatchable Qt
C-abort, exit code still 0). This smoke tests exactly the proposed
spike: QT_QPA_PLATFORM=offscreen + constructing QApplication BEFORE any
widget might make headless dialog asserts possible.

Verdict discipline (identical to 01_skeleton_smoke.py): flushed printed
sentinels ONLY, never exit codes —
    SMOKE-OK DIALOG          all steps passed (offscreen works: later
                             phases may promote this to a required gate)
    SMOKE-FAIL <step>: ...   a step failed (one line per failure)
    (no sentinel)            process died mid-run (e.g. Qt C-abort)
run_gates.py --smoke auto-discovers this script as INFORMATIONAL: any of
the three outcomes is reported as a note and NEVER fails the gate. The
authoritative dialog verdict is the 01-06 human-verify checkpoint.

Run (from repo root; cwd is /mnt/c-backed so cmd.exe inherits C:\\ cwd):
    timeout 90 cmd.exe /c "C:\\src\\run-conda-pymol.bat -cq smoke\\02_dialog_smoke.py"
"""
import os

# FIRST LINE OF LOGIC — must land before ANY Qt import. Headless PyMOL
# does not preload Qt, so setting it here still precedes Qt init.
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import importlib  # noqa: E402
import sys  # noqa: E402


def _resolve_root():
    """Repo root, defensively.

    Under -cq, __file__ IS defined but is PyMOL's own launcher
    (...site-packages\\pymol\\__init__.py), NOT this script [RUN
    2026-09-06]. Validate every candidate by the presence of
    serpentrum/__init__.py, exactly like 01_skeleton_smoke.py.
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

FAILURES = []


def check(name, fn):
    # Attempt trace printed BEFORE the risky call: if a Qt C-abort kills
    # the process mid-step, the log still shows where it died.
    print('SMOKE-ATTEMPT %s' % name, flush=True)
    try:
        fn()
        print('SMOKE-STEP OK  %s' % name, flush=True)
    except Exception as exc:
        print('SMOKE-FAIL %s: %r' % (name, exc), flush=True)
        FAILURES.append(name)


def s_offscreen_env():
    assert os.environ.get('QT_QPA_PLATFORM') == 'offscreen', (
        'QT_QPA_PLATFORM=%r, expected offscreen'
        % os.environ.get('QT_QPA_PLATFORM'))


def s_root_resolved():
    assert os.path.isfile(os.path.join(ROOT, 'serpentrum', '__init__.py')), (
        'ROOT %r has no serpentrum/__init__.py' % ROOT)


def s_loader_namespace():
    import pymol.plugins  # noqa: F401
    import pmg_tk.startup
    assert hasattr(pmg_tk.startup, '__path__'), 'pmg_tk.startup not a package'


def s_import_under_loader_name():
    import pmg_tk.startup
    if ROOT not in pmg_tk.startup.__path__:
        pmg_tk.startup.__path__.append(ROOT)
    importlib.import_module('pmg_tk.startup.serpentrum')
    global GUI
    GUI = importlib.import_module('pmg_tk.startup.serpentrum.gui')
    assert 'pmg_tk.startup.serpentrum.gui' in sys.modules


def s_qapplication_first():
    # The application MUST exist before any widget is constructed — the
    # exact ordering headless PyMOL misses (research Q3 probe).
    from pymol.Qt import QtWidgets
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    assert app is not None, 'QApplication construction returned None'


def s_dialog_construct():
    global DLG
    DLG = GUI.PluginDialog()


def s_dialog_facts():
    assert DLG.tabs.count() == 3, 'tab count %d != 3' % DLG.tabs.count()
    labels = [DLG.tabs.tabText(i) for i in range(DLG.tabs.count())]
    assert labels == ['Setup', 'Game', 'Spectra'], 'tab labels %r' % labels
    assert DLG.windowTitle() == 'serpentrum', (
        'windowTitle %r' % DLG.windowTitle())
    assert not DLG.modal(), 'dialog must default modeless'


# Order is load-bearing: env + root first, then the plugin import, then
# QApplication BEFORE the dialog (the mechanism under test).
for _name, _fn in [
    ('offscreen_env', s_offscreen_env),
    ('root_resolved', s_root_resolved),
    ('loader_namespace', s_loader_namespace),
    ('import_under_loader_name', s_import_under_loader_name),
    ('qapplication_first', s_qapplication_first),
    ('dialog_construct', s_dialog_construct),
    ('dialog_facts', s_dialog_facts),
]:
    check(_name, _fn)

if FAILURES:
    print('SMOKE-END %d failure(s)' % len(FAILURES), flush=True)
else:
    print('SMOKE-OK DIALOG', flush=True)
