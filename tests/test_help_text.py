"""Pinned-in-WSL tests for serpentrum/help_text.py (plan 08-06 — the
DOCS-03 text layer: state-driven next-action hints, the canonical focus
hint, and the controls recap). All wording here is the researched
default set confirmed at GATE D with d4-confirm-all (owner, 2026-09-28;
.planning/phases/08-demo-data-docs-release-audit/08-01-SUMMARY.md), and
every shipped string is pure ASCII (the house convention that shipped
fmt strings are ASCII — freq_label U+2212 precedent).

GUI WIRING IS NOT THIS PLAN: plan 08-09 renders these strings at the
existing seams (SetupTab initial/_on_reset status, the Game tab
hint_label, the Spectra status/log flow). 08-06 ships only the PURE
module plus these pins.

Discovery command (verified on 3.6.9 — '-t .' FAILS on python3.6):

    python3.6 -m unittest discover -s tests -p "test_help_text.py" -v

Convention: every test file in tests/ repeats the sys.path self-insert
below; tests/ deliberately has NO __init__.py (plugin-path safety).
"""
import ast
import io
import os
import sys
import tokenize
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from serpentrum import help_text  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

GAME_FOCUS_LITERAL = ('Click Start on the Setup tab. Steer with arrow '
                      'keys; click the 3D viewer first if keys seem dead.')
CONTROLS_LITERAL = ('Arrow keys steer (no 180-degree turns - rigid chain '
                    'pivot); Pause/Resume, Restart and Get Spectra are '
                    'buttons.')
PRE_RUN_LITERAL = ('Spectra tab - complete a game, then press Get '
                   'Spectra on the Game tab. Progress streams here.')
RUNNING_LITERAL = 'xtb running... (async - the dialog stays responsive)'

GAME_STATES = ('idle', 'countdown', 'playing', 'paused', 'over')
SPECTRA_STATES = ('pre_run', 'running', 'done', 'failed')


def _is_ascii(text):
    """True when every char of text is ASCII. str.isascii() is 3.7+; the
    binding gate is python3.6, so this module spells the check out."""
    return all(ord(ch) < 128 for ch in text)


def _adjacent_literals(path):
    """Every string literal in the python source at ``path``, with
    implicitly concatenated (adjacent) literals joined into one value.

    Adjacency rule: STRING tokens separated ONLY by whitespace/comment
    tokens (NL, NEWLINE, INDENT, DEDENT, COMMENT) form one run — which is
    exactly how python resolves implicit concatenation tree-wide. This
    reconstructs multi-line source literals (e.g. the gui_game.py
    hint_label call, split across two lines) so a substring check can
    compare against the fully-joined constant without re-deriving how it
    was formatted.
    """
    with open(path, 'r') as fh:
        source = fh.read()
    runs = []
    parts = []
    trivia = (tokenize.NL, tokenize.NEWLINE, tokenize.INDENT,
              tokenize.DEDENT, tokenize.COMMENT)
    for tok in tokenize.generate_tokens(io.StringIO(source).readline):
        if tok.type == tokenize.STRING:
            parts.append(ast.literal_eval(tok.string))
        elif tok.type in trivia:
            continue
        else:
            if parts:
                runs.append(''.join(parts))
                parts = []
    if parts:
        runs.append(''.join(parts))
    return runs


class TestConstants(unittest.TestCase):

    def test_game_focus_hint_literal(self):
        # Canonical single source (08-06); 08-09 rewires gui_game to
        # import this constant.
        self.assertEqual(help_text.GAME_FOCUS_HINT, GAME_FOCUS_LITERAL)

    def test_controls_recap_literal(self):
        # Matches the GAME-10 amended contract (turn veto refuses 180
        # degree turns only) and the named Game tab buttons
        # (Pause/Resume checkable, Restart, Get Spectra - gui_game.py:
        # 311-318).
        self.assertEqual(help_text.CONTROLS_RECAP, CONTROLS_LITERAL)

    def test_setup_hints_start_only(self):
        # START-ONLY vocab: 08-08 removes the temp Apply / Show in
        # Viewer control and 04-06 makes Start the only apply-first
        # route; the hint must never reference a removed control.
        self.assertEqual(
            help_text.SETUP_HINTS['before_apply'],
            'choose settings, then press Start to play')
        self.assertEqual(
            help_text.SETUP_HINTS['after_apply'],
            'press Start to play')


class TestGameHint(unittest.TestCase):

    def test_idle(self):
        self.assertEqual(help_text.game_hint('idle'),
                         GAME_FOCUS_LITERAL + ' ' + CONTROLS_LITERAL)

    def test_countdown(self):
        self.assertEqual(
            help_text.game_hint('countdown'),
            'Get ready - steer with the arrow keys once GO! appears.')

    def test_playing(self):
        self.assertEqual(
            help_text.game_hint('playing'),
            'Steer with the arrow keys. If keys seem dead, click the 3D '
            'viewer first.')

    def test_paused(self):
        self.assertEqual(help_text.game_hint('paused'),
                         'Paused - press Resume to continue.')

    def test_over(self):
        self.assertEqual(
            help_text.game_hint('over'),
            'Run over - press Get Spectra to compute the IR spectrum of '
            'your snake.')

    def test_unknown_state_raises(self):
        # Loud callers: only the existing status vocabulary is legal.
        for bad in ('', 'bogus', 'Idle', 'IDLE', 'pre_run', 'running',
                    'done', 'failed', 'over '):
            self.assertRaises(ValueError, help_text.game_hint, bad)


class TestSpectraHint(unittest.TestCase):

    def test_pre_run(self):
        # The EXISTING initial literal from gui_spectra.py:130-132,
        # single-sourced here verbatim.
        self.assertEqual(help_text.spectra_hint('pre_run'),
                         PRE_RUN_LITERAL)

    def test_running(self):
        # The 06-09-pinned started literal (gui_spectra.py:222-223),
        # re-exported as a hint constant; 08-09 wires the source to this
        # constant without changing the pinned text.
        self.assertEqual(help_text.spectra_hint('running'),
                         RUNNING_LITERAL)

    def test_done(self):
        self.assertEqual(
            help_text.spectra_hint('done'),
            'Click a table row to draw that vibration on the optimized '
            'structure; Save Plot (PNG) writes a file.')

    def test_failed(self):
        self.assertEqual(
            help_text.spectra_hint('failed'),
            'Run failed or cancelled - press Run again to retry, or '
            'check the log.')

    def test_unknown_state_raises(self):
        for bad in ('', 'bogus', 'ok', 'cancelled', 'PRE_RUN',
                    'idle', 'countdown', 'playing', 'paused', 'over',
                    'pre_run '):
            self.assertRaises(ValueError, help_text.spectra_hint, bad)


class TestAsciiSweep(unittest.TestCase):

    def test_every_public_string_is_ascii(self):
        strings = [help_text.GAME_FOCUS_HINT, help_text.CONTROLS_RECAP]
        strings.extend(sorted(help_text.SETUP_HINTS.values()))
        strings.extend(help_text.game_hint(state)
                       for state in GAME_STATES)
        strings.extend(help_text.spectra_hint(state)
                       for state in SPECTRA_STATES)
        for text in strings:
            self.assertTrue(_is_ascii(text),
                            'non-ASCII help text: %r' % text)


class TestDriftAlarms(unittest.TestCase):

    def test_focus_hint_matches_gui_game_literal(self):
        # Drift alarm for 08-09's rewiring: gui_game.py:320-323 still
        # owns the joined focus-hint literal today. NOTE ON THE MOVE:
        # plan 08-09 Task 1 replaces the gui_game.py literal with a
        # help_text.GAME_FOCUS_HINT reference and, IN THE SAME COMMIT,
        # updates this assertion to accept (and pin) the constant
        # reference there instead.
        gui_game_literals = _adjacent_literals(
            os.path.join(ROOT, 'serpentrum', 'gui_game.py'))
        self.assertIn(help_text.GAME_FOCUS_HINT, gui_game_literals,
                      'gui_game.py no longer contains the GAME_FOCUS_'
                      'HINT literal - single-source drift')

    def test_no_removed_control_reference(self):
        # 08-08 removes the temp Apply / Show in Viewer control; none of
        # the help strings (nor the module source itself, comments
        # included) may reference it.
        with open(os.path.join(ROOT, 'serpentrum', 'help_text.py'),
                  'r') as fh:
            source = fh.read()
        self.assertNotIn('Apply / Show in Viewer', source)


if __name__ == '__main__':
    unittest.main()
