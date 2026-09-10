"""serpentrum — PyMOL plugin: molecular snake + xtb IR spectra.

Module level is stdlib-only by design (INFRA-02): the plugin must import
under WSL python3.6 with zero sys.modules stubs, and PyMOL's plugin loader
must never pull Qt at import time. Qt is imported lazily inside
run_plugin_gui(); pymol inside __init_plugin__().
"""


def _anchor():
    """Return the stable single-instance state object.

    The plugin loads as 'pmg_tk.startup.serpentrum' (NOT
    'pymol.plugins.startup.serpentrum' — that is only an attribute alias).
    Plugin-Manager reinstall re-executes THIS module via importlib.reload,
    and a stray direct import may load it under a second name. Attributes
    on the 'pmg_tk.startup' package object survive both, so live state can
    never duplicate (INFRA-03).
    """
    import pmg_tk.startup
    if not hasattr(pmg_tk.startup, '_serpentrum'):
        class _SerpentrumState(object):
            dialog = None       # the single PluginDialog instance
            controller = None   # the single live game controller (later phases)
            setup = None        # the live setup dict (Phase 3, plan 03-07)
        state = _SerpentrumState()
        from . import setup_logic  # lazy relative import (ENTRY-legal)
        state.setup = setup_logic.new_setup()
        pmg_tk.startup._serpentrum = state
    return pmg_tk.startup._serpentrum


def __init_plugin__(app=None):
    # Local import keeps module level stdlib-only. The real Qt GUI sets
    # pymol.plugins.HAVE_QT = True before calling this (headless: raises
    # catchable QtNotAvailableError — smokes set the flag first).
    from pymol.plugins import addmenuitemqt
    addmenuitemqt('serpentrum', run_plugin_gui)


def run_plugin_gui():
    state = _anchor()
    if state.dialog is None:
        from .gui import PluginDialog            # lazy: Qt loads on first open
        existing = PluginDialog.find_existing()  # adopt orphaned widget (01-02 defines it)
        state.dialog = existing if existing is not None else PluginDialog(anchor_state=state)
    state.dialog.show()      # MODELESS — .show() never .exec_() (INFRA-05)
    state.dialog.raise_()
    state.dialog.activateWindow()
