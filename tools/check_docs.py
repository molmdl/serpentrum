#!/usr/bin/env python3.6
"""Doc-vs-code audit for the serpentrum docs corpus (DOCS-04 leg A).

Proves on every gate run that every README/help claim matches code and
data reality (the reproduce-steps leg lives in the release UAT). Seven
check families, each an individual function returning ``(ok, message)``
with injectable text/sources so tests feed tamper fixtures without ever
touching the repo; ``run_all(repo_root)`` aggregates them against the
live repo; ``main()`` is the CLI (per-check PASS/FAIL lines, exit 0/1)
— the tools/check_purity.py dual CLI/import precedent.

Families:

1.  vibe-block        README lines 1-4 match the approved vibe block
                      byte-exact (VIBE_LINES below, read off the post-
                      08-07 README at authoring time — approved by
                      construction).
2.  placeholders      zero 'TBD' in README.md; zero 'sECDpent' in
                      README.md and spec.md.
3.  control-literals  quoted UI control names exist in their named code
                      files (post-08-08 bottom row, post-08-09 literals;
                      the focus hint is pinned as the single-sourced
                      ``help_text.GAME_FOCUS_HINT`` reference, never the
                      bare string). 'Apply / Show in Viewer' is
                      deliberately NOT pinned: 08-08 removed that control
                      (Start is the only materialize route, 04-06
                      apply-first) and its name is banned from docs by
                      check 7.
4.  numeric-claims    README tokens are COMPOSED from the sources of
                      truth — setup_logic SPEED_TIERS / DEFAULTS /
                      BOX_PRESETS / win-cap bounds / HESSIAN_WARNING, the
                      stacking dataset and manifest.json (both loaded
                      through molecule_data) — never hardcoded here.
                      Bare numbers are digit-guarded ('6.0' cannot hide
                      inside '16.0'). The banned pre-calibration
                      '30-90 s' phrasing must stay gone.
5.  install-recipe    'Add plugin directory' AND 'restart PyMOL'
                      present; 'Install New Plugin' absent.
6.  path-refs         every back-ticked path token in README exists on
                      disk relative to the repo root (URLs and anything
                      with '@' skipped).
7.  claim-bans        removed/retracted claims can never reappear in
                      README (see _CLAIM_BANS), plus the affirmative
                      'animation' claim: allowed ONLY when the same
                      sentence precedes it with 'no ' or 'static' (tiny
                      explicit window for the README static-vectors
                      disclaimer); anything else fails.

GUI-free and purity-walk-invisible (tools/ is dev-side). python3.6,
stdlib only, %-formatting.
"""
import math
import os
import re
import sys


def _find_repo_root(start):
    """First ancestor of ``start`` containing the serpentrum/ package.

    The script may run from anywhere; anchoring on the package directory
    (not on argv's cwd) keeps resolution correct in every invocation.
    """
    here = os.path.abspath(start)
    while True:
        if os.path.isdir(os.path.join(here, 'serpentrum')):
            return here
        parent = os.path.dirname(here)
        if parent == here:
            raise RuntimeError('no serpentrum/ package above %r' % start)
        here = parent


REPO_ROOT = _find_repo_root(os.path.dirname(os.path.abspath(__file__)))

# Approved vibe block (post-08-07 README.md lines 1-4) pinned BYTE-EXACT,
# including the trailing spaces on lines 1 and 3. Approved by
# construction: this is the shipped block, read off the live README when
# the tool was authored (plan 08-03 behavior item 1).
VIBE_LINES = (
    '> This is a vibe-coding project. While the human attempt to verify the source of all ',
    '> contents, if you find any issues please contact me.',
    '> ',
    '> !! v1.0 - vibe-coded, review before production/teaching use !!',
)

# Placeholder / legacy-name rules: (banned literal, docs it may never
# appear in). 'TBD' would be an unfinished doc; 'sECDpent' is the
# pre-rename project name, scrubbed from the shipped corpus (08-07).
_PLACEHOLDER_RULES = (
    ('TBD', ('README.md',)),
    ('sECDpent', ('README.md', 'spec.md')),
)

# Control-name literals pinned for DOCS-04: (code file, exact literal).
# Tab names pin the addTab call sites; button labels pin their quoted
# forms. 'Apply / Show in Viewer' is deliberately absent (removed by
# 08-08; banned from docs in check 7). The focus hint pins the
# help_text.GAME_FOCUS_HINT REFERENCE that 08-09 single-sourced into
# gui_game.py — not the bare literal, which lives only in help_text.py.
CONTROLS = (
    ('serpentrum/gui.py', "addTab(self.setup_page, 'Setup')"),
    ('serpentrum/gui.py', "addTab(self.game_tab, 'Game')"),
    ('serpentrum/gui.py', "addTab(self.spectra_tab, 'Spectra')"),
    ('serpentrum/gui.py', "'Reset'"),
    ('serpentrum/gui.py', "'Randomize'"),
    ('serpentrum/gui.py', "'Save Setup'"),
    ('serpentrum/gui.py', "'Load Setup'"),
    ('serpentrum/gui.py', "'Cleanup model'"),
    ('serpentrum/gui.py', "'Start'"),
    ('serpentrum/gui_setup.py', 'Box + head materialized'),
    ('serpentrum/gui_game.py', "'Pause'"),
    ('serpentrum/gui_game.py', "'Resume'"),
    ('serpentrum/gui_game.py', "'Restart'"),
    ('serpentrum/gui_game.py', "'Get Spectra'"),
    ('serpentrum/gui_game.py', 'help_text.GAME_FOCUS_HINT'),
    ('serpentrum/gui_spectra.py', "'no xtb run yet'"),
    ('serpentrum/gui_spectra.py', "'Cancel xtb run'"),
    ('serpentrum/gui_spectra.py', "'Run again'"),
    ('serpentrum/gui_plot.py', "'Save Plot (PNG)'"),
    ('serpentrum/input.py',
     'serpentrum: click the 3D viewer, then steer with arrow keys'),
)

CONTROL_FILES = tuple(sorted(set(rel for rel, _lit in CONTROLS)))

# The pre-calibration hessian estimate — replaced by measured numbers at
# the 06-07 calibration (HESSIAN_WARNING docstring); must stay gone.
_NUMERIC_BANS = ('30-90 s',)

# Banned claims: removed control (08-08), retracted feature/method
# naming, and the 'P = pause' proposal that NEVER shipped (the canonical
# pause is the Pause/Resume button + auto-pause on dialog focus).
_CLAIM_BANS = (
    'P = pause',
    'Apply / Show in Viewer',
    'xtb4stda',
    'std2',
    'Generate and export',
)

# Affirmative-'animation' allowlist window — keep TINY and explicit: a
# sentence may contain 'animation' ONLY when preceded within the SAME
# sentence by one of these markers (exactly the README static-vectors
# disclaimer shape). Anything else is an affirmative claim and fails.
_ANIMATION_ALLOWLIST = ('no ', 'static')

_BARE_NUMBER = re.compile(r'\d+(?:\.\d+)?$')


def check_vibe(readme_text):
    """(ok, message): README lines 1-4 == VIBE_LINES byte-exact."""
    head = readme_text.split('\n')[:len(VIBE_LINES)]
    if head == list(VIBE_LINES):
        return True, 'vibe block matches the approved %d-line block' % len(
            VIBE_LINES)
    return False, ('README lines 1-%d drifted from the approved vibe '
                   'block: %r' % (len(VIBE_LINES), head))


def check_placeholders(readme_text, spec_text):
    """(ok, message): no 'TBD' in README; no 'sECDpent' in README/spec."""
    texts = {'README.md': readme_text, 'spec.md': spec_text}
    hits = []
    for banned, docs in _PLACEHOLDER_RULES:
        for name in docs:
            if banned in texts[name]:
                hits.append('%r found in %s' % (banned, name))
    if hits:
        return False, 'placeholder ban hits: ' + '; '.join(hits)
    return True, 'no TBD/sECDpent placeholders in the docs corpus'


def check_controls(sources):
    """(ok, message): every pinned control literal exists in its file.

    ``sources`` maps repo-relative posix paths to file text — injectable
    so tests tamper individual fixtures without touching the repo.
    """
    missing = []
    for rel_path, literal in CONTROLS:
        text = sources.get(rel_path)
        if text is None:
            missing.append('%s (source not provided)' % rel_path)
        elif literal not in text:
            missing.append('%s: missing literal %r' % (rel_path, literal))
    if missing:
        return False, 'control literals missing: ' + '; '.join(missing)
    return True, 'all %d control literals present' % len(CONTROLS)


def collect_numeric_context(repo_root):
    """Compose the docs numbers FROM the sources of truth (never
    hardcoded): setup_logic constants, the stacking dataset and
    manifest.json — the latter two loaded through molecule_data (both
    are gate-verified PURE modules).
    """
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)
    from serpentrum import molecule_data, setup_logic  # PURE modules

    data_dir = os.path.join(repo_root, 'serpentrum', 'data')
    stacking = molecule_data.load_stacking(
        os.path.join(data_dir, 'stacking_pi_stack.json'))
    manifest = molecule_data.load_manifest(
        os.path.join(data_dir, 'manifest.json'))

    stack = stacking['interactions'][0]
    gap = stack['distance_a']
    offset = stack['lateral_offset_a']
    centroid = math.sqrt(gap * gap + offset * offset)
    angle = math.degrees(math.atan2(offset, gap))

    molecules = []
    for mol_set in manifest['sets']:
        molecules.extend(mol_set['molecules'])

    # The measured tail of HESSIAN_WARNING (the '~N^3' scaling preamble
    # is not restated in the README; the measured sentence is).
    hessian_tail = setup_logic.HESSIAN_WARNING.split('; ', 1)[1]

    return {
        'speed_tiers': [value for _name, value in setup_logic.SPEED_TIERS],
        'default_speed': setup_logic.DEFAULTS['speed'],
        'box_half_widths': [int(extent[1][0]) for extent in
                            setup_logic.BOX_PRESETS.values()],
        'default_box': setup_logic.DEFAULTS['box_preset'],
        'win_cap': setup_logic.DEFAULTS['win_cap_molecules'],
        'win_cap_min': setup_logic.RANDOMIZE_WIN_CAP_MIN,
        'win_cap_max': setup_logic.RANDOMIZE_WIN_CAP_MAX,
        'atom_budget': setup_logic.DEFAULTS['atom_budget'],
        'broadening_fwhm': setup_logic.DEFAULTS['broadening_fwhm'],
        'stack_gap_a': gap,
        'stack_offset_a': offset,
        'stack_centroid_a': centroid,
        'stack_angle_deg': angle,
        'molecules': molecules,
        'hessian_tail': hessian_tail,
    }


def expected_numeric_tokens(context):
    """The exact README substrings implied by the sources of truth.

    A future edit that drifts SPEED_TIERS / BOX_PRESETS / DEFAULTS /
    stacking / manifest values without updating the README turns into a
    missing token here — numeric drift FAILS the default gate.
    """
    tokens = ['%.1f' % value for value in context['speed_tiers']]
    tokens.append('%.1f (default)' % context['default_speed'])
    tokens.extend('%d' % width for width in context['box_half_widths'])
    tokens.append('%s default' % context['default_box'])
    tokens.append('win cap default %d (range %d-%d)'
                  % (context['win_cap'], context['win_cap_min'],
                     context['win_cap_max']))
    tokens.append('atom budget %d atoms' % context['atom_budget'])
    tokens.append('broadening %.1f cm-1' % context['broadening_fwhm'])
    tokens.append('a %.3f A plane gap plus a %.3f A lateral offset'
                  % (context['stack_gap_a'], context['stack_offset_a']))
    tokens.append('a %.2f A centroid-centroid distance at %.1f deg '
                  'off-normal' % (context['stack_centroid_a'],
                                  context['stack_angle_deg']))
    for molecule in context['molecules']:
        tokens.append(molecule['source_id'])
        tokens.append(', %d atoms)' % molecule['atom_count'])
    tokens.append(context['hessian_tail'])
    return tokens


def _contains_token(text, token):
    """Token present in text. Bare numbers are digit-guarded so e.g.
    '6.0' cannot masquerade as the tail of '16.0' (word-boundary style:
    no digit or '.' immediately before, no digit immediately after).
    """
    if _BARE_NUMBER.match(token):
        pattern = r'(?<![\d.])' + re.escape(token) + r'(?![\d])'
        return re.search(pattern, text) is not None
    return token in text


def check_numeric(readme_text, context):
    """(ok, message): composed tokens present, banned numbers absent."""
    problems = []
    for token in expected_numeric_tokens(context):
        if not _contains_token(readme_text, token):
            problems.append('missing token %r' % token)
    for banned in _NUMERIC_BANS:
        if banned in readme_text:
            problems.append('banned pre-calibration number %r present'
                            % banned)
    if problems:
        return False, '; '.join(problems)
    return True, 'all %d composed numeric tokens present' % len(
        expected_numeric_tokens(context))


def check_install(readme_text):
    """(ok, message): plugin-directory install route pinned; the
    single-file 'Install New Plugin' route banned."""
    problems = []
    for required in ('Add plugin directory', 'restart PyMOL'):
        if required not in readme_text:
            problems.append('missing install step %r' % required)
    if 'Install New Plugin' in readme_text:
        problems.append("banned route 'Install New Plugin' present")
    if problems:
        return False, '; '.join(problems)
    return True, 'plugin-directory install route pinned'


def check_paths(readme_text, exists_fn):
    """(ok, message): every back-ticked path token exists per exists_fn.

    URLs ('://') and anything containing '@' (emails) are skipped; every
    other token is judged as a repo-root-relative path.
    """
    missing = []
    for token in sorted(set(re.findall(r'`([^`]+)`', readme_text))):
        if '://' in token or '@' in token:
            continue
        if not exists_fn(token):
            missing.append(token)
    if missing:
        return False, ('back-ticked paths missing on disk: '
                       + ', '.join(missing))
    return True, 'all back-ticked paths exist on disk'


def _animation_problems(text):
    """One problem sentence per affirmative 'animation' mention."""
    problems = []
    for sentence in re.split(r'(?<=[.!?])\s+|\n', text):
        for match in re.finditer('animation', sentence):
            prefix = sentence[:match.start()]
            if not any(marker in prefix
                       for marker in _ANIMATION_ALLOWLIST):
                problems.append(sentence.strip())
    return problems


def check_claim_bans(readme_text):
    """(ok, message): banned claims can never reappear in README."""
    problems = ['banned claim %r present' % claim
                for claim in _CLAIM_BANS if claim in readme_text]
    problems.extend('affirmative animation claim: %r' % sentence
                    for sentence in _animation_problems(readme_text))
    if problems:
        return False, '; '.join(problems)
    return True, 'no banned claims in README'


def _read_text(repo_root, rel_path):
    with open(os.path.join(repo_root, rel_path),
              encoding='utf-8') as fh:
        return fh.read()


def run_all(repo_root):
    """Run every check family against the live repo.

    Returns an ordered list of ``(check, ok, message)`` tuples; the gate
    wrapper (tests/test_docs_audit.py) asserts zero failures.
    """
    readme = _read_text(repo_root, 'README.md')
    spec = _read_text(repo_root, 'spec.md')
    sources = dict((rel, _read_text(repo_root, rel))
                   for rel in CONTROL_FILES)
    context = collect_numeric_context(os.path.abspath(repo_root))
    root = os.path.abspath(repo_root)

    def _exists(rel_path):
        return os.path.exists(os.path.join(root, rel_path))

    return [
        ('vibe-block',) + check_vibe(readme),
        ('placeholders',) + check_placeholders(readme, spec),
        ('control-literals',) + check_controls(sources),
        ('numeric-claims',) + check_numeric(readme, context),
        ('install-recipe',) + check_install(readme),
        ('path-refs',) + check_paths(readme, _exists),
        ('claim-bans',) + check_claim_bans(readme),
    ]


def main(argv=None):
    """CLI: per-check 'PASS/FAIL name: message' lines; exit 1 if any FAIL."""
    argv = list(sys.argv[1:] if argv is None else argv)
    repo_root = argv[0] if argv else REPO_ROOT
    results = run_all(repo_root)
    failed = 0
    for name, ok, message in results:
        sys.stdout.write('%s %s: %s\n'
                         % ('PASS' if ok else 'FAIL', name, message))
        sys.stdout.flush()
        if not ok:
            failed += 1
    sys.stdout.write('check_docs: %d/%d checks PASS (%s)\n'
                     % (len(results) - failed, len(results),
                        os.path.abspath(repo_root)))
    sys.stdout.flush()
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
