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


if __name__ == '__main__':
    unittest.main()
