"""tests/test_gui_pins.py -- source-text pins for the Phase 8 bottom
action row and the removed Phase-3 temporary row (plan 08-08,
SETUP-07/08).

Headless widget construction is a dead end (decision 01-05; smoke 02
re-probed dead 2026-09-28), so the canonical bottom-row contract is
pinned as SOURCE TEXT, mirroring the tests/test_hud_content.py:592-603
source-pin pattern and the 07-07 raw-source grep audits:

  gui.py
    - the 6 button labels appear IN spec order: Reset, Randomize,
      Save Setup, Load Setup, Cleanup model, Start (spec.md:21-26)
    - exactly ONE 'setCurrentIndex(1)' occurrence (the 04-06
      byte-identical Start route; a second Start switch is banned)
  serpentrum/*.py
    - ZERO blocking-modal-call tokens (modeless gate; grep audit
      precedent 07-07). The token literal is written with a gap below
      ("ex" + "ec_") so THIS test file stays free of it.
  gui_setup.py
    - ZERO 'Apply / Show in Viewer' tokens (the Phase-3 temporary row
      is removed AND no docstring may name the removed control)
    - the internal apply+validate-first path (_on_apply) and the
      cleanup path (_on_cleanup) survive (the bottom row calls them)
    - no dangling references to the removed widget attributes
    - OWNER DIRECTIVE (GATE D round 2, plan 08-08): _populate_head_combo
      is invoked from at least one site OUTSIDE _on_apply (the eager
      demo-set-selection / upload-browse population) so head options
      appearing without Apply cannot silently regress.

  gui.py + gui_plot.py (owner directive 2026-10-04, debug session
  .planning/debug/06-window-move-resize-quirk.md)
    - the dialog is FIXED-SIZE: freeze_dialog_size applies
      setFixedSize at construction (the 07-10 envelope -- min-width
      450 + max-height cap -- is subsumed with the same floors).
      Since round 5 (owner decision 2026-10-10, option D "Two-column
      form"): the HEIGHT cap basis is 0.73 (width keeps the 07-10
      0.92) and the freeze carries the clip-proof rail
      max(minimumSizeHint, min(hint, cap)) on the height term
    - NO resizeEvent/moveEvent handlers in gui.py (a containment
      handler re-enters the broken WM negotiation; any future
      deliberate exception must update these pins)
    - the 07-06 plot-preset surface survives the fixed size via the
      injected dialog_size_refreeze hook (grow AND shrink stay
      automatic)

  gui.py + serpentrum/dialog_fit.py (round 3 follow-ups on the
  owner's live test of the fixed-size patch, same debug session)
    - opening position: ONE frame-fit clamp through PURE
      serpentrum/dialog_fit math -- center-on-available at
      construction (pre-show move()), current-position re-clamp on
      the preset refreeze; no event handlers, ever
    - MSWindowsFixedSizeDialogHint at CONSTRUCTION pre-show (thin
      fixed-dialog chrome, sizing borders gone: every edge inert);
      exactly one setWindowFlags call site (a post-show flag change
      would HIDE the window, and the refreeze must never touch
      flags)
    - ZERO resizeEvent/moveEvent handlers anywhere under serpentrum/
      (repo-wide pin; the round-1 regression class stays closed)
    - behavioral pins for the placement math live in
      tests/test_dialog_fit.py (pure module, headless-testable --
      py3.6)

Convention: every test file in tests/ repeats the sys.path self-insert
below (bioCHEMeleon pattern). tests/ deliberately has NO __init__.py --
the dev plugin path IS the repo root, and findPlugins would treat a
package dir here as a second plugin.
"""
import glob
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SERPENTRUM_GLOB = os.path.join(_REPO_ROOT, 'serpentrum', '*.py')

_BUTTON_LABELS = ['Reset', 'Randomize', 'Save Setup', 'Load Setup',
                  'Cleanup model', 'Start']


def _read(relpath):
    with open(os.path.join(_REPO_ROOT, relpath)) as handle:
        return handle.read()


class TestBottomRowContract(unittest.TestCase):
    """gui.py carries the canonical 6-button bottom action row."""

    def test_six_button_labels_appear_in_spec_order(self):
        source = _read(os.path.join('serpentrum', 'gui.py'))
        pos = -1
        for label in _BUTTON_LABELS:
            needle = "QPushButton('%s'" % label
            found = source.find(needle)
            self.assertGreaterEqual(
                found, 0, 'button %r missing from gui.py' % (label,))
            self.assertGreater(
                found, pos,
                'button %r out of spec order in gui.py' % (label,))
            pos = found

    def test_exactly_one_start_switch(self):
        source = _read(os.path.join('serpentrum', 'gui.py'))
        self.assertEqual(
            source.count('setCurrentIndex(1)'), 1,
            'the 04-06 byte-identical Start route must stay the ONLY '
            'Game-tab switch')


class TestModelessBan(unittest.TestCase):
    """No blocking-modal-call token survives anywhere in serpentrum/*.py
    (07-07 grep-audit precedent; the AST purity gate bans the call, this
    pin bans the literal so raw-source audits never false-positive)."""

    def test_no_blocking_modal_token_anywhere(self):
        token = 'ex' + 'ec_'  # written split so this file stays clean
        offenders = []
        for path in glob.glob(_SERPENTRUM_GLOB):
            with open(path) as handle:
                if token in handle.read():
                    offenders.append(path)
        self.assertEqual(offenders, [],
                         'blocking-modal token found in: %r' % offenders)


class TestTempRowRemoved(unittest.TestCase):
    """gui_setup.py: the Phase-3 temporary row is gone; the internal
    paths the bottom row depends on survive."""

    def test_removed_control_named_nowhere(self):
        source = _read(os.path.join('serpentrum', 'gui_setup.py'))
        self.assertNotIn(
            'Apply / ' + 'Show in Viewer', source,  # split: docstring pin
            'the removed temp control must not be named anywhere')

    def test_no_dangling_removed_widget_references(self):
        source = _read(os.path.join('serpentrum', 'gui_setup.py'))
        for attr in ('self.apply_btn', 'self.cleanup_btn',
                     'self.start_btn', 'btn_row'):
            self.assertNotIn(
                attr, source,
                'dangling reference to removed widget %r' % (attr,))

    def test_internal_paths_survive(self):
        source = _read(os.path.join('serpentrum', 'gui_setup.py'))
        self.assertIn('def _on_apply(', source)
        self.assertIn('def _on_cleanup(', source)
        self.assertIn('def _on_start(', source)
        self.assertIn('def _on_reset(', source)
        self.assertIn('def _on_randomize(', source)
        self.assertIn('def _on_save_setup(', source)
        self.assertIn('def _on_load_setup(', source)


class TestEagerHeadPopulation(unittest.TestCase):
    """Owner directive (GATE D round 2, plan 08-08): head options appear
    without the old Apply click -- _populate_head_combo must be invoked
    from at least one site OUTSIDE _on_apply."""

    def test_populate_head_combo_called_outside_on_apply(self):
        source = _read(os.path.join('serpentrum', 'gui_setup.py'))
        apply_start = source.find('    def _on_apply(')
        self.assertGreaterEqual(apply_start, 0, '_on_apply must survive')
        apply_end = source.find('\n    def ', apply_start + 1)
        self.assertGreater(apply_end, apply_start,
                           '_on_apply must not be the last method')
        outside = source[:apply_start] + source[apply_end:]
        call_sites = outside.count('self._populate_head_combo(')
        self.assertGreaterEqual(
            call_sites, 1,
            'no eager _populate_head_combo call site outside _on_apply')


class TestGameplayExclusionWiring(unittest.TestCase):
    """quick-001 (2026-10-01, owner-approved): the set_a biphenyl
    gameplay-exclusion wiring pins, source-scan style (headless widget
    construction is a dead end -- decision 01-05).

    gui_setup.py: imports the pure spawn module AND the head-combo
    populator skips gameplay-excluded records (single seam -- display,
    _head_candidates/Randomize, and collect_state all inherit the
    filter).

    gui_game.py: the gameplay head path resolves through
    spawn_mod.effective_head_id (the stale-saved-setup fallback,
    upstream of the untouched bridge resolver).
    """

    @staticmethod
    def _method_body(source, needle):
        start = source.find(needle)
        assert start >= 0, '%r not found' % (needle,)
        end = source.find('\n    def ', start + 1)
        if end < 0:
            end = len(source)
        return source[start:end]

    def test_gui_setup_combo_filters_excluded_records(self):
        source = _read(os.path.join('serpentrum', 'gui_setup.py'))
        self.assertIn('from . import spawn', source)
        body = self._method_body(source, 'def _populate_head_combo(')
        self.assertIn('is_gameplay_excluded', body)

    def test_gui_game_head_path_uses_effective_head_id(self):
        source = _read(os.path.join('serpentrum', 'gui_game.py'))
        body = self._method_body(source, 'def _build_head_state(')
        self.assertIn('spawn_mod.effective_head_id', body)


class TestPerformanceControls(unittest.TestCase):
    """Plan 08-12 (owner insertion Q2, recorded 2026-10-01 at the
    paused GATE V checkpoint): the Setup tab's Performance group (atom
    budget + xtb threads) and the launch argv seam, pinned source-scan
    style (house 08-08 pattern; headless widget construction is a dead
    end -- decision 01-05).

    gui_setup.py: BOTH Performance spins are widget-written INSIDE
    collect_state's body (Save/Load/Reset/Randomize/Start all flow
    through it) and the Performance group exists.

    gui.py: the launch seam builds extra_args through xtb_run's
    thread_arg with EXACTLY ONE call site, and NO inline '-P' literal
    may appear in gui.py -- the ONLY '-P' argv source stays
    xtb_run.py (DEFAULT_THREAD_ARG / thread_arg).
    """

    @staticmethod
    def _method_body(source, needle):
        start = source.find(needle)
        assert start >= 0, '%r not found' % (needle,)
        end = source.find('\n    def ', start + 1)
        if end < 0:
            end = len(source)
        return source[start:end]

    def test_performance_pins_and_launch_thread_seam(self):
        # gui_setup.py: collect_state writes both keys from the
        # Performance widgets; the group itself exists.
        gui_setup_src = _read(os.path.join('serpentrum', 'gui_setup.py'))
        collect_body = self._method_body(gui_setup_src,
                                         '    def collect_state(')
        self.assertIn("setup['atom_budget'] = "
                      'self.atom_budget_spin.value()', collect_body)
        self.assertIn("setup['xtb_threads'] = "
                      'self.threads_spin.value()', collect_body)
        self.assertIn("'Performance'", gui_setup_src)
        # gui.py: exactly ONE thread_arg call site (the desk-seam
        # producer), and no inline '-P' argv literal may leak in.
        gui_src = _read(os.path.join('serpentrum', 'gui.py'))
        self.assertEqual(gui_src.count('xtb_run.thread_arg'), 1,
                         'exactly one xtb thread_arg call site '
                         '(_launch_spectra_run)')
        self.assertNotIn("'-P'", gui_src,
                         "gui.py must not carry an inline '-P' argv "
                         "literal (the only '-P' source is xtb_run.py)")
        # Purity discipline unchanged: no blocking-modal token in
        # gui_setup.py (belt-and-braces alongside TestModelessBan's
        # repo-wide scan; token written split so THIS file stays
        # clean).
        token = 'ex' + 'ec_'
        self.assertNotIn(token, gui_setup_src)


class TestFixedDialogSize(unittest.TestCase):
    """Owner directive 2026-10-04 (debug session
    .planning/debug/06-window-move-resize-quirk.md, round 2): the
    plugin dialog is FIXED-SIZE -- user resizing disabled, zero
    min-vs-max envelope slack under 200% display scaling (the
    decoded WM negotiation ping-pong behind the move flicker).

    gui.py: freeze_dialog_size applies setFixedSize ONCE at
    construction (and again on plot-preset changes) at the natural
    sizeHint capped to the available screen -- width on the 07-10
    basis (avail * 0.92 headroom, 450 min-width promise) and, since
    round 5 (owner decision 2026-10-10, height-reduction option D
    "Two-column form"), height on max(560, int(avail * 0.73)) with
    the clip-proof rail max(minimumSizeHint, min(hint, cap_h)) --
    no resizeEvent/moveEvent handlers, no construction-time
    setMinimumWidth/setMaximumHeight envelope creep-back.

    gui_plot.py: the 07-06 exact-preset surface survives via the
    injected dialog_size_refreeze hook (a preset change re-freezes
    the dialog to fit -- grow AND shrink stay automatic).
    Source-scan style (headless construction is a dead end --
    decision 01-05).
    """

    @staticmethod
    def _method_body(source, needle):
        start = source.find(needle)
        assert start >= 0, '%r not found' % (needle,)
        end = source.find('\n    def ', start + 1)
        if end < 0:
            end = len(source)
        return source[start:end]

    def test_freeze_dialog_size_pin(self):
        source = _read(os.path.join('serpentrum', 'gui.py'))
        body = self._method_body(source, '    def freeze_dialog_size(')
        self.assertIn('self.setFixedSize(', body)
        # Width: the 07-10 cap basis survives inside the freeze
        # (0.92 headroom + 450 min-width promise; unchanged by the
        # round-5 decision -- no width growth).
        self.assertIn('int(avail.width() * 0.92)', body)
        self.assertIn('max(450, min(desired.width(), cap_w))', body)
        # Height: round-5 basis 0.73 (owner decision 2026-10-10,
        # option D) with the 560 floor kept.
        self.assertIn('max(560, int(avail.height() * 0.73))', body)
        self.assertIn('min(desired.height(), cap_h)', body)
        # Clip-proof rail (round 5): the freeze can never fall below
        # the LIVE layout minimum -- a cap below content would clip
        # children inside the fixed window, and a preset-grown
        # refreeze must land at the (larger) minimum, never the cap.
        self.assertIn('max(self.minimumSizeHint().height(), hinted_h)',
                      body)
        # freeze runs once at construction end.
        self.assertIn('self.freeze_dialog_size()', source)

    def test_no_move_resize_event_handlers(self):
        source = _read(os.path.join('serpentrum', 'gui.py'))
        self.assertNotIn(
            'def resizeEvent(', source,
            'a resizeEvent handler re-enters the WM negotiation the '
            'fixed size is designed to remove (see debug session 06; '
            'a deliberate future exception must update this pin)')
        self.assertNotIn(
            'def moveEvent(', source,
            'a moveEvent handler re-enters the WM negotiation the '
            'fixed size is designed to remove (see debug session 06; '
            'a deliberate future exception must update this pin)')
        # the subsumed construction-time envelope must not creep back
        self.assertNotIn('setMinimumWidth(450)', source,
                         'the 450 promise is subsumed by the freeze '
                         '(max(450, ...) floor inside '
                         'freeze_dialog_size)')
        self.assertNotIn('setMaximumHeight(', source,
                         'the 07-10 height cap is subsumed by the '
                         'freeze (cap_h inside freeze_dialog_size)')

    def test_plot_preset_refreeze_wiring(self):
        gui_src = _read(os.path.join('serpentrum', 'gui.py'))
        self.assertIn('plot_panel.dialog_size_refreeze', gui_src,
                      'PluginDialog must inject the re-freeze hook '
                      'into the spectra plot panel')
        plot_src = _read(os.path.join('serpentrum', 'gui_plot.py'))
        self.assertIn("getattr(self, 'dialog_size_refreeze', None)",
                      plot_src,
                      'the preset handler must call the OPTIONAL '
                      'hook (absent when the panel is hosted '
                      'standalone, e.g. the smokes)')

    def test_07_10_content_caps_survive(self):
        # The 07-10 approved content contract is byte-identical: the
        # internal scroll caps stay widget-level in gui_spectra.py.
        spectra_src = _read(os.path.join('serpentrum',
                                         'gui_spectra.py'))
        self.assertIn('setMaximumHeight(110)', spectra_src,
                      'SpectraTab log panel cap (07-10 r1 fix)')
        self.assertIn('setMaximumHeight(150)', spectra_src,
                      'SpectraTab table cap (07-10 r1 fix)')


class TestFixedDialogPositionChrome(unittest.TestCase):
    """Round 3 (owner live-test follow-ups on the round-2 fixed-size
    patch, debug session .planning/debug/06-window-move-resize-quirk.md):

    (1) OPENING POSITION was never set anywhere -- Qt parent-centered
        the dialog and its frame opened bottom-out on the owner's
        screen. Now freeze_dialog_size owns size AND placement via
        PURE serpentrum/dialog_fit math: pre-show the base is the
        available-geometry center (the round-5 height leaves the
        centered widget top ~107+ logical px down, absorbing the
        ~29-logical title-bar margin with room to spare; the clamp
        covers the 560-floor regime where centering alone would
        not), post-show (preset refreeze) the base is the CURRENT
        position clamped under the new size.
    (2) TOP-BORDER TRANSLATE: with min==max the native WS_THICKFRAME
        sizing hit-test + clamp turns an edge grab into a window
        MOVE. MSWindowsFixedSizeDialogHint (fixed-dialog chrome, no
        sizing borders) makes every edge fully inert.
    (3) Refreeze re-clamp: the plot hook stays bound to
        freeze_dialog_size, so preset grow/shrink re-applies the
        position clamp (a grown dialog never bottoms out).
    No move/resize event handlers anywhere under serpentrum/ (the
    round-1 regression class stays closed). Source-scan style
    (headless construction is a dead end -- decision 01-05); the
    clamp arithmetic itself is behavior-tested in
    tests/test_dialog_fit.py.
    """

    @staticmethod
    def _method_body(source, needle):
        start = source.find(needle)
        assert start >= 0, '%r not found' % (needle,)
        end = source.find('\n    def ', start + 1)
        if end < 0:
            end = len(source)
        return source[start:end]

    def test_mswindows_fixed_dialog_hint_once_and_preshow(self):
        source = _read(os.path.join('serpentrum', 'gui.py'))
        # the hint exists, expressed through pymol.Qt QtCore, and
        # appears EXACTLY ONCE in gui.py.
        self.assertEqual(source.count('MSWindowsFixedSizeDialogHint'), 1)
        self.assertIn('QtCore.Qt.MSWindowsFixedSizeDialogHint', source)
        # applied via ONE setWindowFlags call site -- never a
        # second site (a post-show flag change HIDE the window;
        # the refreeze path must never touch flags).
        self.assertEqual(source.count('self.setWindowFlags('), 1)
        # OR'd into the existing flags, not replaced wholesale.
        self.assertRegex(
            source,
            r'setWindowFlags\(\s*self\.windowFlags\(\)\s*\|\s*'
            r'QtCore\.Qt\.MSWindowsFixedSizeDialogHint')
        # the call site is INSIDE __init__ (physically before the
        # freeze method): construction -- i.e. BEFORE the entry's
        # .show() can ever run.
        flags_at = source.find('self.setWindowFlags(')
        self.assertLess(
            flags_at, source.find('    def freeze_dialog_size('),
            'the hint must live inside __init__ (pre-show; flag '
            'changes after show hide the window)')

    def test_position_clamp_lives_inside_freeze(self):
        source = _read(os.path.join('serpentrum', 'gui.py'))
        body = self._method_body(source, '    def freeze_dialog_size(')
        # the pure placement math is imported natively and used in
        # the freeze -- the ONE position code path (construction +
        # refreeze both route through it).
        self.assertIn('from . import dialog_fit', source)
        self.assertIn('dialog_fit.centered_top_left(', body,
                      'pre-show base = available-geometry center')
        self.assertIn('dialog_fit.clamped_position(', body,
                      'frame-fit clamp')
        self.assertIn('self.isVisible()', body,
                      'the pre-show/post-show seam (construction '
                      'centers; refreeze clamps the current position)')
        self.assertIn('self.move(', body,
                      'one-shot placement mechanism (move() pre-show '
                      'only records the position; no WM traffic on a '
                      'hidden window)')

    def test_refreeze_hook_reapplies_position(self):
        # the plot-preset hook stays bound to freeze_dialog_size,
        # which now owns size AND position -> preset grow/shrink
        # re-clamps the placement (grown dialog never bottoms out).
        # (the \\? allows the source's line-continuation backslash.)
        gui_src = _read(os.path.join('serpentrum', 'gui.py'))
        self.assertRegex(
            gui_src,
            r'dialog_size_refreeze\s*=\s*\\?\s*self\.freeze_dialog_size',
            'the refreeze hook must remain bound to '
            'freeze_dialog_size')
        plot_src = _read(os.path.join('serpentrum', 'gui_plot.py'))
        self.assertIn("getattr(self, 'dialog_size_refreeze', None)",
                      plot_src,
                      'the preset handler must call the OPTIONAL '
                      'hook (absent when the panel is hosted '
                      'standalone, e.g. the smokes)')

    def test_frame_margins_helper_guards(self):
        # the native-margins read is guarded on both ends: the
        # window handle may not exist (pre-show) and some platforms
        # hand back all-zero margins -- both degrade to the measured
        # FALLBACK_FRAME_MARGINS estimates, never a bare crash.
        source = _read(os.path.join('serpentrum', 'gui.py'))
        body = self._method_body(source,
                                 '    def _frame_margins_for_clamp(')
        self.assertIn('self.windowHandle()', body)
        self.assertIn('.frameMargins()', body)
        self.assertIn('is not None', body)
        self.assertIn('top > 0', body)
        self.assertIn('dialog_fit.FALLBACK_FRAME_MARGINS', body)

    def test_no_move_resize_handlers_repo_wide(self):
        # repo-wide (stronger than the gui.py-only round-2 pin): NO
        # persistent move/resize event handler may exist anywhere in
        # the plugin package -- the negotiation-.handler regression
        # class from debug round 1 stays closed.
        offenders = []
        for path in sorted(glob.glob(_SERPENTRUM_GLOB)):
            with open(path) as handle:
                content = handle.read()
            for token in ('def resizeEvent(', 'def moveEvent('):
                if token in content:
                    offenders.append('%s: %s' % (path, token))
        self.assertEqual(
            offenders, [],
            'move/resize event handlers are banned repo-wide '
            '(debug session 06); a deliberate future exception '
            'must update this pin: %r' % offenders)


if __name__ == '__main__':
    unittest.main()
