"""Headless Windows PyMOL skeleton smoke — INFRA-01.

Run (from repo root; cwd is /mnt/c-backed so cmd.exe inherits C:\\ cwd):
    timeout 90 cmd.exe /c "C:\\src\\run-conda-pymol.bat -cq smoke\\01_skeleton_smoke.py"

Exit codes through the .bat are ALWAYS 0 (even after a Qt C-abort) —
verdicts are flushed sentinels grepped by tests/run_gates.py --smoke:
    SMOKE-OK SKELETON        all steps passed
    SMOKE-FAIL <step>: ...   a step failed (one line per failure)

This is the template every later phase's smoke copies: named step
functions + check() runner + flushed sentinel epilogue. Hard rules for
any smoke derived from this file:
  - every print carries flush=True (stdout is block-buffered when piped;
    unflushed prints are lost on abort)
  - NO widget construction (headless C-abort is uncatchable)
  - never add smoke/__init__.py (findPlugins plugin-path safety)
  - NEVER trust __file__ under -cq: probe [RUN 2026-09-06] showed it is
    PyMOL's own launcher (...site-packages\\pymol\\__init__.py), not this
    script — resolve ROOT by validating candidates for serpentrum/
"""
import importlib
import os
import sys


def _resolve_root():
    """Repo root, defensively.

    The invocation contract guarantees cwd is the repo root, but __file__
    under -cq exec is PyMOL's launcher module (NOT this script), so the
    naive dirname(dirname(__file__)) lands in site-packages. Validate
    every candidate by the presence of serpentrum/__init__.py.
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
    try:
        fn()
        print('SMOKE-STEP OK  %s' % name, flush=True)
    except Exception as exc:
        print('SMOKE-FAIL %s: %r' % (name, exc), flush=True)
        FAILURES.append(name)


def s_loader_namespace():
    import pymol.plugins  # noqa: F401
    import pmg_tk.startup
    assert hasattr(pmg_tk.startup, '__path__'), 'pmg_tk.startup not a package'


def s_import_under_loader_name():
    import pmg_tk.startup
    if ROOT not in pmg_tk.startup.__path__:
        pmg_tk.startup.__path__.append(ROOT)
    mod = importlib.import_module('pmg_tk.startup.serpentrum')
    assert 'pmg_tk.startup.serpentrum' in sys.modules
    assert callable(mod.__init_plugin__)
    assert callable(mod.run_plugin_gui)


def s_no_qt_at_import():
    # Runtime proof of the module-level-import ban (headless PyMOL does
    # not preload Qt, so any eager import would show up here).
    assert 'PyQt5.QtWidgets' not in sys.modules, 'eager Qt import!'
    assert 'pymol.Qt' not in sys.modules, 'eager pymol.Qt import!'


def s_menu_registration():
    import pymol.plugins
    pymol.plugins.HAVE_QT = True   # exactly what the real GUI does first
    mod = importlib.import_module('pmg_tk.startup.serpentrum')
    mod.__init_plugin__()          # registers on the fake headless menuBar


def s_anchor_identity():
    mod = importlib.import_module('pmg_tk.startup.serpentrum')
    assert mod._anchor() is mod._anchor(), 'anchor not stable'


def s_reload_survival():
    import pmg_tk.startup
    mod = importlib.import_module('pmg_tk.startup.serpentrum')
    anchor = pmg_tk.startup._serpentrum
    importlib.reload(mod)
    assert pmg_tk.startup._serpentrum is anchor, 'anchor lost on reload'


def s_double_import_adoption():
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    alias = importlib.import_module('serpentrum')   # second module name
    import pmg_tk.startup
    assert alias._anchor() is pmg_tk.startup._serpentrum, 'alias made a second state'


# Order is load-bearing: no_qt_at_import must run after the plugin import
# (so the assertion measures the plugin's own import, headless PyMOL
# preloads nothing) and before menu_registration (which imports
# pymol.plugins — still Qt-free — and sets HAVE_QT).
for _name, _fn in [
    ('loader_namespace', s_loader_namespace),
    ('import_under_loader_name', s_import_under_loader_name),
    ('no_qt_at_import', s_no_qt_at_import),
    ('menu_registration', s_menu_registration),
    ('anchor_identity', s_anchor_identity),
    ('reload_survival', s_reload_survival),
    ('double_import_adoption', s_double_import_adoption),
]:
    check(_name, _fn)

if FAILURES:
    print('SMOKE-END %d failure(s)' % len(FAILURES), flush=True)
else:
    print('SMOKE-OK SKELETON', flush=True)
