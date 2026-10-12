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
- ``SETUP_TOOLTIPS`` — (owner insertion Q1, plan 08-13) hover help for
  every Setup control, keyed by widget-ATTRIBUTE name (13 keys, the
  exact attributes gui_setup.py constructs). Student register, ASCII,
  facts ONLY from the setup_logic constants and shipped behavior.
- ``BUTTON_TOOLTIPS`` — (owner insertion Q1, plan 08-13) hover help
  for the six dialog-owned bottom-row buttons, keyed by button role
  (reset/randomize/save/load/cleanup/start — the QPushButton objects
  gui.py:151-168 builds).
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
re-exports named above. The tooltip dicts (plan 08-13) follow the same
single-source contract: the GUI calls QWidget.setToolTip with the dict
values verbatim (gui_setup sets all 13, gui sets all 6) and never
re-derives wording. Every string is pure ASCII — the shipped house
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

# Q1 (owner insertion, plan 08-13): student hover help for the 13 Setup
# controls, keyed by the widget-ATTRIBUTE name the gui_setup wiring
# uses. Facts come ONLY from the setup_logic constants and shipped
# behavior (demo combo items, box half-widths 35/55/85, speed tiers
# 6.0/9.0/11.0/13.0, win cap 1-20 default 10, atom budget default 100,
# threads default 4, the <=-3-ring upload acceptance rule, the
# consent-gated generic overlay). The owner blesses the final wording
# at the resumed GATE V Section A (same review round as the dataset D3
# text); until then this is the owner-drafted default.
SETUP_TOOLTIPS = {
    'demo_combo': (
        'Pick which molecules to play. Demo Set A is the 5 built-in '
        'aromatic molecules; Upload... lets you choose your own '
        '.sdf/.mol2 file.'),
    'upload_path_field': (
        'Read-only: shows the upload file you chose. Pick one with '
        'Browse.'),
    'browse_upload_btn': (
        'Opens a file dialog. Pick a .sdf or .mol2 molecule set; unsafe '
        'files (e.g. a molecule with more than 3 rings) are rejected '
        'with a reason.'),
    'box_combo': (
        'Play-field size: small, medium or large means 35, 55 or 85 A '
        'half-widths. medium (default) comfortably fits the default '
        'win cap.'),
    'head_combo': (
        'The molecule you start as (the snake head). Random picks one '
        'from the chosen set.'),
    'xtb_auto_check': (
        'Find the xtb program on PATH automatically. Leave this ON '
        'unless your xtb lives somewhere else.'),
    'xtb_path_field': (
        'Full path to the xtb executable, used when auto-detect is '
        'OFF.'),
    'browse_xtb_btn': (
        'Pick the xtb executable file; the path is stored for this '
        'setup.'),
    'win_cap_spin': (
        'How many molecules to stack to win: range 1-20, default 10. '
        'Higher caps mean longer games and bigger snakes (and slower '
        'spectra runs).'),
    'speed_combo': (
        'Head speed in A/s: relaxed 6.0, normal 9.0 (default), fast '
        '11.0, expert 13.0. The speed stays constant within a run.'),
    'generic_stack_check': (
        'OFF by default. Turn ON to let uploads carrying a planar '
        'aromatic 6-ring stack at the illustrative geometry, clearly '
        'labeled user-approved; demo-set play is unchanged.'),
    'atom_budget_spin': (
        'Atom-count warning threshold (hessian cost scales ~N^3). '
        'Default 100 atoms; raising it silences the warning earlier, '
        'and larger snakes take much longer to compute.'),
    'threads_spin': (
        'How many CPU threads the xtb spectra run may use: default 4. '
        'Set 1-2 on a modest laptop so PyMOL stays responsive (runs '
        'take longer).'),
}

# Q1 (owner insertion, plan 08-13): hover help for the six dialog-owned
# bottom-row buttons, keyed by button ROLE. Behavior facts: Reset
# paints defaults without touching the 3D scene (materialize is
# Start-only); Randomize redraws head/box/cap/speed/broadening while
# consent + environment keys are never touched (randomize_setup);
# Save/Load are the SETUP-08 .json persistence pair with the
# foreign-xtb-path -> auto-detect fallback (normalize_loaded); Cleanup
# removes only srp_* objects (cleanup_srp); Start applies first, then
# begins the countdown (04-06 route).
BUTTON_TOOLTIPS = {
    'reset': (
        'Restore all default settings. The 3D scene only changes at '
        'the next Start.'),
    'randomize': (
        'Redraw head, box, cap, speed and broadening with concrete '
        'random values. Consent and environment settings are never '
        'touched.'),
    'save': (
        'Write the current settings to a .json file you can keep or '
        'share.'),
    'load': (
        'Read settings from a .json file. A path saved on another '
        'machine falls back to auto-detect here.'),
    'cleanup': (
        'Remove only the srp_* objects the game created; your own '
        'molecules are never touched.'),
    'start': (
        'Apply the settings, materialize the box and head, and start '
        'the countdown.'),
}

# Game-tab next-action hints, keyed by the existing status vocabulary.
_GAME_HINTS = {
    'idle': GAME_FOCUS_HINT + ' ' + CONTROLS_RECAP,
    'countdown': 'Get ready - steer with the arrow keys once GO! '
                 'appears.',
    'playing': 'Steer with the arrow keys. Red wall lines are obstacles '
                '- touching one ends the run. If keys seem dead, click '
                'the 3D viewer first.',
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
