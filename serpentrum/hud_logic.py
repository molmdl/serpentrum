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
    # REFUSE_WALL retired 2026-09-20c (owner directive: placements may
    # leave the play box; only the head is box-bound). REFUSE_ATOM is the
    # only remaining refuse code.
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

    2026-09-21 (upload-endless debug session, C4): the group label
    carries the placement taxonomy -- SKIP_* codes count as 'skipped Nx'
    (informational skips: no dataset entry / not approved / mode / ring;
    an upload-only run is ALL skips) while REFUSE_* codes count as
    'refused Nx' (placement clashes). Keyed on the outcome-code prefix
    -- placement.py: 'the names are the contract.'
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
            label = ('skipped' if entry['outcome'].startswith('SKIP_')
                     else 'refused')
            lines.append('%s %dx %s: %s'
                         % (label, count, entry['name'],
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


class ReasonCoalescer(object):
    """Coalesce consecutive identical skip/refuse info lines into '(xN)'.

    2026-09-20 (05-16 re-test fix B): a placement refuse used to print
    the SAME 'skipped <name>: <reason>' line on every capture of the
    re-armed pickup (a biphenyl cascade printed it 18 times). The
    coalescer is the PURE state for the GUI's anti-spam policy:

      note(text) -> ('append', text)   the first of a run: display NOW
                                       (the FIRST refuse must always
                                       show — the STACK-05 refuse
                                       demonstrator lives on this)
      note(text) -> ('replace', ...)   an immediate repeat of the last
                                       text: the GUI REWRITES its last
                                       info-box line to carry the
                                       '(xN)' suffix (count includes
                                       the first occurrence)
      break_run()                      any other message breaks the run;
                                       the next repeat appends fresh

    Only CONSECUTIVE identical texts coalesce; interleaved messages
    always append. Pure data — no Qt, no viewer (GUI-testable policy).
    """

    def __init__(self):
        self._last = None
        self._count = 0

    def note(self, text):
        """Register one skip/refuse line -> (mode, line). mode in
        {'append', 'replace'}; count suffix '(xN)' from N=2 up."""
        if text is not None and text == self._last:
            self._count += 1
            return ('replace', '%s (x%d)' % (text, self._count))
        self._last = text
        self._count = 1
        return ('append', text)

    def break_run(self):
        """Reset: the NEXT note() of the same text appends fresh."""
        self._last = None
        self._count = 0


# ---------------------------------------------------------------------------
# SRP_DEBUG=1 live-debug trace builders (05-16 checkpoint follow-up).
# Env-gated in gui_game (read ONCE per begin_game); these PURE builders
# only ever RUN when the user opts in -- default-off silence preserves
# the chattiness policy: nothing here fires per tick in normal play, and
# nothing here contains viewer reads (all numbers arrive as plain args).
# The trace answers "is my stack parallel-displaced?": every placed
# capture prints the placed/tail ring normals (3 decimals), their dot
# (parallel planes = |1.0|), the ring-centroid distance decomposed into
# the along-normal plane gap + lateral shift (4 decimals -- the live
# heights the DATA-02 3.60 A @ 20 deg encoding decodes to), the gate
# box, and the engine counters.
# ---------------------------------------------------------------------------


def _fmt_v3(v):
    """'(x,y,z)' at 3 decimals (the ring-normal formatting block)."""
    return '(%.3f,%.3f,%.3f)' % (v[0], v[1], v[2])


def debug_capture_trace(pickup_id, name, code, detail=None,
                        placed_normal=None, tail_normal=None,
                        distance=None, plane_gap=None, lateral_gap=None,
                        box_min=None, box_max=None,
                        molecules_stacked=None, pickups_remaining=None):
    """One debug line per capture resolution (SRP_DEBUG=1 only).

    pickup_id / name: the captured pickup. code: 'placed' or the
    placement.py outcome code (SKIP_*/REFUSE_* -- the ONE taxonomy).
    detail: refuse detail (clash distance string) when present.
    placed_normal / tail_normal: 3-vectors at 3 decimals, plus their
    dot at 6 decimals; parallel-displaced prints |dot| = 1.0.
    distance / plane_gap / lateral_gap: the LIVE ring-centroid step
    decomposed (4 decimals): distance = |step|, plane_gap = step along
    the growth normal (the 3.383 A encoding), lateral_gap = the
    perpendicular remainder (the 1.231 A encoding). box_min / box_max:
    the 2D gate box the clash check ran against. molecules_stacked /
    pickups_remaining: engine counters AFTER the resolution.
    """
    line = 'DBG capture %s %s %s' % (pickup_id, name, code)
    if detail is not None:
        line += ' detail=%s' % detail
    if placed_normal is not None and tail_normal is not None:
        dot = (placed_normal[0] * tail_normal[0] +
               placed_normal[1] * tail_normal[1] +
               placed_normal[2] * tail_normal[2])
        line += (' n_placed=%s n_tail=%s dot=%.6f'
                 % (_fmt_v3(placed_normal), _fmt_v3(tail_normal), dot))
    if distance is not None:
        line += (' d=%.4f plane=%.4f lat=%.4f'
                 % (distance, plane_gap, lateral_gap))
    if box_min is not None and box_max is not None:
        line += (' box=(%.1f,%.1f)/(%.1f,%.1f)'
                 % (box_min[0], box_min[1], box_max[0], box_max[1]))
    if molecules_stacked is not None:
        line += ' stacked=%d pickups=%d' % (molecules_stacked,
                                            pickups_remaining)
    return line


def debug_spawn_cooldown(pool_size, cooldown_ticks):
    """One DBG line when the spawn pool enters the exhaust cooldown
    (SRP_DEBUG=1).

    The demote-after-refuse pause state (2026-09-20): every pool
    candidate refused consecutively -> spawning PAUSES for
    ``cooldown_ticks`` movement ticks (~10 s at the 100 ms default),
    then auto-resumes (NEVER a permanent latch). Logged ONCE per pause
    episode by the controller.
    """
    return ('DBG spawn pool cooldown (%d refused in a row)'
            ' - spawning paused %d ticks' % (pool_size, cooldown_ticks))


def debug_spawn_cooldown_over():
    """One DBG line when the exhaust cooldown elapses and spawning
    resumes (SRP_DEBUG=1). Logged ONCE per resume edge."""
    return 'DBG spawn pool cooldown over - spawning resumed'


def debug_event_trace(kind, tick=None, heading=None, head_xy=None,
                      sweep_delta=None, result=None,
                      molecules_stacked=None, pickups_remaining=None):
    """One debug line per notable engine event (SRP_DEBUG=1 only).

    kind: 'turning' (first sweep tick only, so a 6-tick sweep prints
    ONCE), 'crashed', 'won', 'end_run'. tick: the controller's logical
    tick counter; heading: axis name; head_xy: engine head; sweep_delta:
    the signed sweep angle in degrees when turning; result: the engine
    result at run end; molecules_stacked / pickups_remaining: engine
    counters when known.
    """
    line = 'DBG event %s' % kind
    if tick is not None:
        line += ' tick=%d' % tick
    if heading is not None:
        line += ' heading=%s' % heading
    if head_xy is not None:
        line += ' head=(%.2f,%.2f)' % head_xy
    if sweep_delta is not None:
        line += ' delta=%+.4f' % sweep_delta
    if result is not None:
        line += ' result=%s' % result
    if molecules_stacked is not None:
        line += ' stacked=%d' % molecules_stacked
    if pickups_remaining is not None:
        line += ' pickups=%d' % pickups_remaining
    return line


# --- Turn feedback (ghost-point follow-up, plan 05-16 live retest) ----------
# The live report: 'only right works after a ghost point' turned out to be
# the (then-pinned) rigid-chain sweep veto plus the pinned silent drops for
# same-direction and 180-degree key presses.
#
# OWNER-APPROVED RULE CHANGES:
#   2026-09-19 UTC ("only detect wall from head, ignore tail"): the sweep
#     pre-check stopped vetting the swinging chain against the walls —
#     walls apply to the HEAD only.
#   2026-09-20 UTC (05-16 re-test directive): the pre-check's remaining
#     BODY and PICKUP legs are removed too — a rigid sweep ALWAYS
#     executes. The ONLY turn refusal left is the 180-degree backward
#     key, dropped at request time in request_direction (classified
#     'dropped: 180 reversal' by classify_turn_request below — that DBG
#     line for the 180 case stays). turn_refuse_text / _TURN_REFUSE_WHY
#     are therefore DEFENSIVE-ONLY (the engine emits no 'turn_refused'
#     events at all); they are kept so a stray future event can never
#     crash the HUD, and so the 05-16 human-verify text contract
#     ('turn refused: <reason> (why)') stays stable.


# One clause per engine refusal reason: what the swung chain would hit.
# ALL reasons are DEFENSIVE (the engine emits no 'turn_refused' events
# since 2026-09-20); the text is kept truthful to the historical rules.
_TURN_REFUSE_WHY = {
    'boundary': 'walls only stop the head '
                '(the chain may swing past the box during a turn)',
    'body': 'the swinging chain would clip the snake\'s own body',
    'pickup': 'the swinging chain would clip a floating molecule',
}


def turn_refuse_text(reason):
    """Player-readable turn-refusal line for the info box.

    Keeps the checkpoint-pinned 'turn refused: <reason>' prefix (the
    05-16 human-verify text reads it literally) and appends the WHY in
    one clause - the missing piece that made a correct chain veto feel
    like a ghost point. Unknown reasons fall back to a generic clause
    (never raises on a future engine reason).

    DEFENSIVE-ONLY (2026-09-20): the engine no longer emits any
    'turn_refused' event — the only refused turn is the 180 backward
    key, which is classified at request time and never becomes an
    event. This builder exists so a stray event can never crash the HUD.
    """
    why = _TURN_REFUSE_WHY.get(
        reason, 'the swinging chain is blocked at this position')
    return 'turn refused: %s (%s)' % (reason, why)


def classify_turn_request(unit, ref_unit, pending_nonempty, in_sweep):
    """Steering-outcome label for ONE arrow press (SRP_DEBUG trace ONLY).

    Mirrors game_engine.request_direction's policies against the given
    reference (the CURRENT heading, or the sweep TARGET while sweeping):
    axis dot products are exactly 1.0 (same), 0.0 (perpendicular) or
    -1.0 (reversal), so the 0.5 thresholds reproduce the engine's
    verdicts without touching it:

      dot > 0.5  -> dropped: same direction (checked first, as in the
                    engine; buffer state never matters)
      dot < -0.5 -> dropped: 180 reversal (impossible by design)
      in-sweep   -> queued (in-sweep, newest-wins) - the intentional
                    in-sweep override of the static first-kept rule
      buffer full-> dropped (a request is already waiting)
      otherwise  -> queued

    unit: the requested direction's unit vector; ref_unit: the
    reference unit vector; pending_nonempty: engine.pending non-empty;
    in_sweep: engine.sweeping is not None.
    """
    dot = unit[0] * ref_unit[0] + unit[1] * ref_unit[1]
    if dot > 0.5:
        return 'dropped: same direction'
    if dot < -0.5:
        return 'dropped: 180 reversal'
    if in_sweep:
        return 'queued (in-sweep, newest-wins)'
    if pending_nonempty:
        return 'dropped: buffer full (another key is already queued)'
    return 'queued'


def debug_turn_request(name, outcome, tick=None, heading=None,
                       head_xy=None, ref=None):
    """One debug line per steering key press (SRP_DEBUG=1 only).

    name: the arrow's direction name. outcome: the
    classify_turn_request label. tick / heading / head_xy: the
    controller state AT the key press (heading is the pre-sweep heading
    during sweeps); ref: the sweep target name when sweeping (the
    direction the request is judged against) or None.
    """
    line = 'DBG turn request %s -> %s' % (name, outcome)
    if tick is not None:
        line += ' tick=%d' % tick
    if heading is not None:
        line += ' heading=%s' % heading
    if head_xy is not None:
        line += ' head=(%.2f,%.2f)' % head_xy
    if ref is not None:
        line += ' ref=%s' % ref
    return line
