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
            game_session = None  # the live game session dict (Phase 4, plan 04-05):
                                 # {'engine', 'epoch', 'start_time', 'paused_accum',
                                 #  'status'} — created by GameTab.begin_game; None
                                 #  until first Start; anchor survives Plugin-Manager
                                 #  reload (Pitfall 7) so the session dict is
                                 #  single-instance by construction.
            records = None       # the live setloader records list (Phase 5, plan
                                 # 05-06): written by SetupTab apply on success;
                                 # consumed by GameTab begin_game for pickups +
                                 # info content; survives reload like game_session.
            stacking_data = None  # the live stacking dataset dict (Phase 5): the
                                  # APPROVED-interaction source for the skip
                                  # policy and STACK-04 content.
            last_run = None      # the completed-run handoff record (Phase 5, plan
                                 # 05-15): {'result', 'molecules_stacked',
                                 # 'atoms_total', 'chain_objects', 'snake_id'};
                                 # written at completion, consumed by the Spectra
                                 # stage (Phases 6/7). The record gains
                                 # 'snake_xyz' (Phase 6, plan 06-06): the
                                 # head-inclusive engine-atom xyz text built at
                                 # completion via xtb_run.build_run_input; None
                                 # when the head mirror was unavailable.
            spectra_run = None   # the live xtb run record (Phase 6, plan 06-05):
                                 # key set frozen by xtb_run.SPECTRA_RUN_KEYS
                                 # ('snake_id', 'status', 'problems',
                                 # 'input_path', 'g98_path', 'vibspectrum_path',
                                 # 'xtbopt_path', 'log_path'); written ONLY by
                                 # the xtb runner's terminal branch; consumed by
                                 # the Spectra stage (Phase 7).
            spectra_runner = None  # the live xtb run controller (Phase 6, plan 06-05;
                                   # declared Phase 7, plan 07-04): an XtbRunController
                                   # create-or-reused by the dialog at first launch
                                   # (gui.py); Qt connections are DIALOG-scoped (they die
                                   # with the dialog and are re-connected fresh), the
                                   # controller object itself survives Plugin-Manager
                                   # reload like dialog/controller. Consumed by the
                                   # Spectra tab (Phase 7) via getattr guards.
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
    state.dialog.show()      # MODELESS - .show() only, never a blocking modal (INFRA-05)
    state.dialog.raise_()
    state.dialog.activateWindow()
