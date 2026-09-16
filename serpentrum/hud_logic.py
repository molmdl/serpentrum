"""serpentrum.hud_logic -- pure display helpers for the Game tab HUD (plan 04-02).

PURE module: stdlib only (no pymol / pmg_tk / PyQt5 / numpy --
check_purity auto-classifies PURE). The wall clock lives in the GUI
(game_engine has NO wall-clock by design, 04-RESEARCH-gameloop.md
Q5/S3); only the formatting lives here, so GAME-07's elapsed timer and
molecules-remaining label math stay WSL-testable while the widgets stay
human-verify-only (01-05).

python3.6 syntax (%-formatting).
"""


def format_elapsed(seconds):
    """Render elapsed seconds as 'M:SS' (minutes not zero-padded,
    seconds zero-padded to 2).

    Fractional seconds are FLOORED (75.9 -> '1:15', never '1:16') via
    int(); negatives are clamped to 0 first (a tick landing before
    start_time must never render negative -- PITFALLS.md 9.3 style).
    """
    if seconds < 0.0:
        seconds = 0.0
    total = int(seconds)
    return '%d:%02d' % (total // 60, total % 60)


def remaining_text(value):
    """Render the molecules-remaining label (GAME-07).

    'Remaining: N' for a concrete count; 'Remaining: -' when the cap is
    None (remaining unknown -- Phase 4 never hits this with the default
    setups, but the engine allows cap=None).
    """
    if value is None:
        return 'Remaining: -'
    return 'Remaining: %d' % value


# ---------------------------------------------------------------------------
# STACK-04 info-box content builders (plan 05-09).
#
# 05-RESEARCH-gui-lifecycle.md info_box_spec: the info box stays a dumb
# rolling log with NO queue/priority system; these PURE builders are the
# only new surface. Every chemistry sentence comes VERBATIM from the
# shipped dataset's own fields (the no-fabrication rule) -- hud_logic
# composes, it never writes chemistry. Outcome codes are IMPORTED from
# placement.py (one taxonomy, two consumers), never redefined here.
# ---------------------------------------------------------------------------
import math  # noqa: E402

from . import placement  # noqa: E402

# Educator-readable reason literals keyed by placement.py outcome code
# (the research's suggested strings; REFUSE_ATOM carries an optional
# clash-distance detail appended as '(...)').
_REASON_TEXT = {
    placement.SKIP_NO_ENTRY:
        'no verified stacking entry for this molecule (no invented chemistry)',
    placement.SKIP_NOT_APPROVED:
        'stacking entry not approved yet',
    placement.SKIP_MODE:
        'interaction mode not supported in v1',
    placement.SKIP_NO_RING:
        'no planar aromatic 6-ring found',
    placement.SKIP_NONPLANAR:
        'ring geometry not planar',
    placement.REFUSE_WALL:
        'placement would leave the play box',
    placement.REFUSE_ATOM:
        'placement clashes',
}


def _one_line(text):
    """Collapse newlines to single spaces (info box = rolling 1-line log)."""
    return ' '.join(text.split())


def _reason(code, detail):
    """Reason literal for a placement code (detail only for REFUSE_ATOM)."""
    text = _REASON_TEXT.get(code, 'unclassified outcome %s' % code)
    if code == placement.REFUSE_ATOM and detail is not None:
        text = '%s (%s)' % (text, detail)
    return text


def pickup_block(name, interaction, citation_short):
    """Structured per-pickup line composed ENTIRELY from the dataset.

    interaction: the dataset interaction dict ('name', 'distance_a',
    'lateral_offset_a', 'explanation'). The displayed plane gap is the
    stored distance_a; the centroid distance and off-normal angle are
    COMPOSED from (distance_a, lateral_offset_a) — sqrt(d^2 + l^2) and
    degrees(atan2(l, d)) — matching the dataset's own encoding note
    (3.60 A @ 20.0 deg for the shipped pi_stack_pd entry). The
    explanation is rendered VERBATIM from the dataset (newlines
    collapsed — never invented here); the citation short-code closes.
    """
    d = interaction['distance_a']
    l = interaction['lateral_offset_a']
    composed = math.sqrt(d * d + l * l)
    angle = math.degrees(math.atan2(l, d))
    return ('+ %s: %s, %.2f A plane gap (centroid %.2f A @ %.1f deg '
            'off-normal) - %s [%s]'
            % (name, interaction['name'], d, composed, angle,
               _one_line(interaction['explanation']), citation_short))


def skip_text(name, reason):
    """Refuse/skip line naming the molecule and the reason (STACK-03/05)."""
    return 'skipped %s: %s' % (name, reason)


def reason_text(code, detail, name):
    """Map a placement.py outcome code to its educator-readable line.

    code: one of placement.SKIP_* / placement.REFUSE_* (imported
    constants — the names are the contract). detail: the refused
    outcome's 'detail' field (clash distance string for REFUSE_ATOM,
    None for everything else). Rendered through skip_text.
    """
    return skip_text(name, _reason(code, detail))


def budget_text():
    """Atom-budget advisory. COUNT-FREE on purpose: GAME-04 keeps the
    molecule/atom counts hidden during play (they are revealed only at
    completion), so this line must never contain a digit."""
    return 'atom budget exceeded - spectra on this snake may be slow'


def completion_lines(result, molecules, snake_molecules, atoms_total):
    """The four completion summary lines (GAME-09 / SPECTRA-06).

    Counts are REVEALED here -- completion is when the hidden counters
    become visible.
    """
    return ['result: %s' % result,
            'score: %d molecule(s) stacked' % molecules,
            'snake: %d molecules (incl. head)' % snake_molecules,
            'atoms: %d (spectra input size)' % atoms_total]


def breakdown_lines(history):
    """End-of-run interaction breakdown over the session history.

    history: list of {'name', 'outcome', 'distance_a', 'citation_short'}
    where outcome is 'stacked' or a placement code. Stacked entries are
    grouped by name; refusals/skips by (outcome, name). Groups render in
    FIRST-APPEARANCE order. Empty history -> [].
    """
    groups = []
    index = {}
    for entry in history:
        key = (entry['outcome'], entry['name'])
        if key not in index:
            index[key] = len(groups)
            groups.append([entry, 0])
        groups[index[key]][1] += 1
    lines = []
    for entry, count in groups:
        if entry['outcome'] == 'stacked':
            lines.append('stacked %dx %s at %.2f A plane gap [%s]'
                         % (count, entry['name'], entry['distance_a'],
                            entry['citation_short']))
        else:
            lines.append('refused %dx %s: %s'
                         % (count, entry['name'],
                            _reason(entry['outcome'], None)))
    return lines


def idle_tip(explanations, index):
    """Round-robin chemistry tip ('tip: ...') from VERBATIM dataset
    explanations (newline-collapsed). None when explanations is empty."""
    if not explanations:
        return None
    return 'tip: %s' % _one_line(explanations[index % len(explanations)])


def resume_note(name):
    """The G2 un-finish info line (plan 05-04): after a reject the run
    is no longer won/finished, so play continues.

    `name` is accepted for call-site symmetry but deliberately unused:
    this is a run-state fact, not molecule-level chemistry."""
    return 'placement refused - run continues (cap not reached yet)'
