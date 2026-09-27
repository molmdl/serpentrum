"""In-game help and hint strings (the DOCS-03 PURE half; plan 08-06).

Every user-visible help/hint string that must be testable in WSL
python3.6 and pinnable by the plan-08-03 doc-vs-code audit lives here,
so the GUI modules (gui_setup/gui_game/gui_spectra) only render them
verbatim and never re-derive wording. Plan 08-06 ships this module;
plan 08-09 owns ALL wiring and currently renders none of it.

Contents:

- ``GAME_FOCUS_HINT`` — the canonical focus hint, single-sourced from
  gui_game.py:320-323 (where the literal still renders today; 08-09
  rewires that site to this constant in one commit together with the
  test drift alarm).
- ``CONTROLS_RECAP`` — one-line controls summary honoring the GAME-10
  amended contract (the turn veto refuses 180-degree turns ONLY because
  the chain is rigid — pivot-only steering) and naming the buttons that
  exist (Pause/Resume checkable, Restart, Get Spectra — gui_game.py:
  311-318).
- ``SETUP_HINTS`` — the two Setup-tab hint clauses. BOTH are
  Start-only: plan 08-08 removes the temp preview control and the
  04-06 contract makes Start the only apply-first route, so the hint
  must never reference the removed control.
  'before_apply' renders at the SetupTab initial/_on_reset status seam;
  'after_apply' is the short clause 08-09 appends after a successful
  Start-apply. Note it says 'apply' as a VERB clause (the separate
  d1-c-staleness fix to the success text lives in 08-09, not here).
- ``game_hint(state)`` — state-driven next-action for the Game tab over
  {'idle','countdown','playing','paused','over'} (the existing status
  vocabulary — gui_game.py:405,642,1280,1352).
- ``spectra_hint(state)`` — state-driven next-action for the Spectra tab
  over {'pre_run','running','done','failed'} (the existing statuses;
  'pre_run' and 'running' are the gui_spectra.py literals at :130-132
  and :222-223, re-exported here verbatim so 08-09 can single-source
  them without changing the pinned text).

Wording here is the researched default set confirmed at GATE D with
d4-confirm-all (owner, 2026-09-28; .planning/phases/
08-demo-data-docs-release-audit/08-01-SUMMARY.md) plus the two literal
re-exports named above. Every string is pure ASCII — the shipped house
convention (spectra_ui.freq_label U+2212 precedent; 'cm-1' table
header).

Purity: new modules under serpentrum/ auto-classify PURE
(tools/check_purity.py:56-57) — zero registration edits. Stdlib imports
only (none needed at module scope). python3.6 syntax, %-formatting
ready (no f-strings anywhere in this codebase's 3.6 support window).
"""

GAME_FOCUS_HINT = ('Click Start on the Setup tab. Steer with arrow '
                   'keys; click the 3D viewer first if keys seem dead.')

CONTROLS_RECAP = ('Arrow keys steer (no 180-degree turns - rigid chain '
                  'pivot); Pause/Resume, Restart and Get Spectra are '
                  'buttons.')

SETUP_HINTS = {
    # START-ONLY vocab (08-08 removes the temp preview control;
    # 04-06 makes Start the only apply-first route).
    'before_apply': 'choose settings, then press Start to play',
    'after_apply': 'press Start to play',
}

# Game-tab next-action hints, keyed by the existing status vocabulary.
_GAME_HINTS = {
    'idle': GAME_FOCUS_HINT + ' ' + CONTROLS_RECAP,
    'countdown': 'Get ready - steer with the arrow keys once GO! '
                 'appears.',
    'playing': 'Steer with the arrow keys. If keys seem dead, click the '
               '3D viewer first.',
    'paused': 'Paused - press Resume to continue.',
    'over': 'Run over - press Get Spectra to compute the IR spectrum of '
            'your snake.',
}

# Spectra-tab next-action hints. 'pre_run' and 'running' are the
# EXISTING gui_spectra.py literals (initial status :130-132; the 06-09
# pinned started line :222-223), single-sourced HERE verbatim — 08-09
# rewires those two construction/started sites to these constants
# without changing their pinned text.
_SPECTRA_HINTS = {
    'pre_run': ('Spectra tab - complete a game, then press Get Spectra '
                'on the Game tab. Progress streams here.'),
    'running': 'xtb running... (async - the dialog stays responsive)',
    'done': 'Click a table row to draw that vibration on the optimized '
            'structure; Save Plot (PNG) writes a file.',
    'failed': 'Run failed or cancelled - press Run again to retry, or '
              'check the log.',
}


def game_hint(state):
    """Next-action hint for one Game-tab state in
    {'idle','countdown','playing','paused','over'} -> str.

    Unknown states raise ValueError (loud, never silent): callers pass
    existing status vocabulary, so an unknown key signals a drifted or
    typo'd source state and must fail in tests, not render garbage.
    """
    try:
        return _GAME_HINTS[state]
    except KeyError:
        raise ValueError(
            'unknown game state %r (expected one of %s)'
            % (state, sorted(_GAME_HINTS)))


def spectra_hint(state):
    """Next-action hint for one Spectra-tab state in
    {'pre_run','running','done','failed'} -> str.

    Unknown states raise ValueError (loud, never silent), same contract
    as game_hint.
    """
    try:
        return _SPECTRA_HINTS[state]
    except KeyError:
        raise ValueError(
            'unknown spectra state %r (expected one of %s)'
            % (state, sorted(_SPECTRA_HINTS)))
