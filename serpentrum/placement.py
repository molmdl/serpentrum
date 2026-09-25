"""Placement controller seam: the PURE 'stacked'-branch policy (STACK-01/03/05).

PURE module (stdlib ``math`` only plus relative imports of the pure sibling
modules ``stacking`` and ``molecule_data``; no pymol/pmg_tk/PyQt5/numpy
anywhere; auto-classified PURE by tools/check_purity.py). python3.6 syntax
(%-formatting). Never imports game_engine/pymol/Qt.

This module is the SINGLE function the GUI's 'stacked' branch calls
(``resolve()``) plus its testable parts. It exists to keep gui_game thin:
every placement decision of Phase 5 is WSL-unit-testable here
(pins: tests/test_placement.py). The four open policy questions from
05-RESEARCH-core-integration.md are PINNED as follows (plan 05-05):

1. **Skip taxonomy (ordered, first match wins):**
   - SKIP_NO_ENTRY: ``has_stack_entry`` is False / ``interaction_for``
     returns None (the ``__upload__`` keying — uploaded molecules never
     inherit set_a's entry; locked decision)
   - SKIP_NOT_APPROVED: the interaction's id is not in
     ``molecule_data.shipped_interactions`` (DATA-02 approval gate;
     ``interaction_for`` alone is NOT approval-filtered)
   - SKIP_MODE: the found interaction's mode != 'pi_stack' (v1 supports
     pi_stack only)
    - SKIP_NO_RING: the record carries no ``stack_ring`` (no canonical
      planar 6-ring extractable at load time)
    - SKIP_GENERIC_NO_RING: Phase 5.2 (STACK-06) — consent-ON generic
      upload entry matched but the upload carries no canonical planar
      6-ring (sibling of SKIP_NO_RING at the same ring-check step,
      chosen by WHICH entry matched; unreachable when consent is OFF)
    - SKIP_NONPLANAR: ``stacking.ring_frame`` raises ValueError at
      placement time (non-planar or degenerate ring geometry)

2. **Tail/growth policy (research G6 — the linear staircase):**
   - Chain empty -> the tail is the HEAD's ring frame; the growth normal
     is ``-(heading)`` promoted to 3D (behind the head, snake-canonical).
     The returned (centroid, ref) are the head's computed ring frame; only
     the normal is forced to -heading (the head materializes edge-on, so
     this is its in-plane ring normal by construction).
   - Chain non-empty -> the tail is the NEWEST segment's ring frame,
     RECOMPUTED from the segment's current (sweep-rotated) atoms via
     ``records_by_id[seg['molecule_id']]['stack_ring']``. The computed
     normal IS the growth continuation: by construction (azimuth=0
     placement) it equals the growth normal the segment was placed with, so
     the chain continues the same linear staircase the research measured
     clash-safe (>= 3.386 A for every fused-aromatic pair).
   - Lateral offset always along the tail ref axis
     (``lateral_along_ref=True`` — the visible in-plane axis after the
     edge-on presentation pinned in plan 05-02).

3. **Clash-gate existing set (research open Q7 — decided):** head atoms +
   ALL segment atoms + OTHER live pickups' atoms. A placement overlapping a
   still-live pickup would refuse that pickup mid-chain later; blocking it
   up front is consistent and trivially cheap. OWNER DIRECTIVE
   2026-09-20c: the WALL leg of the gate is RETIRED — placements are
   NEVER refused for leaving the play box ("remove the refuse (let it
   stack out of box since we only bound the head in box)"). The stacked
   chain may extend past the box in ANY axis; only the HEAD is box-bound
   (via the GAME-05 crash rule in game_engine). The ATOM clash leg is
   UNTOUCHED (REFUSE_ATOM stays the STACK-05 demonstrator; the box
   parameters of gate()/resolve() are retained for call-site stability
   but no longer bound the placement).

4. **Outcome contract:** resolve() returns exactly one of

   - ``{'status': 'placed', 'placed_atoms', 'R', 't',
     'ring_centroid_xy', 'interaction', 'citation_short'}``
   - ``{'status': 'skipped', 'code'}``
   - ``{'status': 'refused', 'code', 'detail'}`` (code is REFUSE_ATOM
     only; detail = ``'%.2f A' % clash_distance``)

   resolve() is a PURE function — it NEVER touches engine state. The GUI
   maps codes to text via hud_logic (plan 05-09) and ALWAYS calls
   ``engine.reject_pickup`` on skip/refuse, because the capture was already
   counted (win/counter rollback symmetry is engine-owned; the reject path
   is where plan 05-04's un-finish fix lives).
"""
from . import stacking
from . import molecule_data
from . import generic_stack

# Outcome codes — string constants imported by hud_logic (plan 05-09) to
# compose the info-box text. The names are the contract.
SKIP_NO_ENTRY = 'SKIP_NO_ENTRY'
SKIP_NOT_APPROVED = 'SKIP_NOT_APPROVED'
SKIP_MODE = 'SKIP_MODE'
SKIP_NO_RING = 'SKIP_NO_RING'
SKIP_GENERIC_NO_RING = 'SKIP_GENERIC_NO_RING'
# Phase 5.2 (STACK-06): consent-ON generic entry matched (the overlay
# anchored at Apply) but the upload carries no canonical planar
# 6-ring. Sibling of SKIP_NO_RING at the SAME taxonomy step — chosen
# by WHICH entry matched, so the ORDER is unchanged. Unreachable when
# consent is OFF: uploads never pass the has_stack_entry pre-guard
# below (load-time False via the '__upload__' keying).
SKIP_NONPLANAR = 'SKIP_NONPLANAR'
# REFUSE_WALL retired 2026-09-20c (owner directive): the wall leg of the
# clash gate is gone — only atom clashes refuse. The placement taxonomy
# is now placed / clash-refuse / skip.
REFUSE_ATOM = 'REFUSE_ATOM'

# The only stacking mode v1 knows how to place.
_SUPPORTED_MODE = 'pi_stack'


def _xyz(atoms):
    """(x, y, z) float triples from (sym, x, y, z) 4-tuples or 3-tuples."""
    triples = []
    for atom in atoms:
        if len(atom) == 4:
            triples.append((float(atom[1]), float(atom[2]), float(atom[3])))
        else:
            triples.append((float(atom[0]), float(atom[1]), float(atom[2])))
    return triples


def resolve_skip(record, stacking_data):
    """Ordered skip taxonomy: return a SKIP_* code or None (stackable).

    First match wins (the order IS the policy):

    1. SKIP_NO_ENTRY     -- no dataset entry applies to this molecule
    2. SKIP_NOT_APPROVED -- entry exists but is not APPROVED (DATA-02)
    3. SKIP_MODE         -- entry mode is not 'pi_stack'
    4. SKIP_NO_RING / SKIP_GENERIC_NO_RING -- record carries no
       'stack_ring' (the generic code when the FOUND entry is the 5.2
       generic upload entry)

    SKIP_NONPLANAR is NOT detected here: it surfaces at placement time when
    stacking.ring_frame raises (resolve() catches ValueError).
    """
    interaction = None
    if record.get('has_stack_entry'):
        interaction = molecule_data.interaction_for(record, stacking_data)
    if interaction is None:
        return SKIP_NO_ENTRY
    approved_ids = set(
        entry['id']
        for entry in molecule_data.shipped_interactions(stacking_data))
    if interaction['id'] not in approved_ids:
        return SKIP_NOT_APPROVED
    if interaction['mode'] != _SUPPORTED_MODE:
        return SKIP_MODE
    if 'stack_ring' not in record:
        if interaction['id'] == generic_stack.GENERIC_INTERACTION['id']:
            return SKIP_GENERIC_NO_RING
        return SKIP_NO_RING
    return None


def tail_frame(segments, records_by_id, head_atoms, head_stack_ring,
               heading):
    """Return the (centroid, normal, ref) growth frame for the next stack.

    segments: engine segment records (index 0 = oldest, last = newest);
    empty -> FIRST-capture policy. head_atoms: the head molecule's atoms as
    (sym, x, y, z). heading: the engine's 2D unit heading (hx, hy).

    Chain empty -> (head ring centroid, (-hx, -hy, 0.0), head ring ref):
    the growth normal is EXACTLY -(heading) (behind the head,
    snake-canonical); centroid and ref come from the head's computed ring
    frame unchanged.

    Chain non-empty -> the NEWEST segment's ring frame recomputed from its
    current atoms and the canonical ring indices carried by records_by_id.
    The recomputed normal is used AS-IS: it equals the growth normal the
    segment was placed with (azimuth=0 contract), i.e. the linear
    staircase's continuation.
    """
    if not segments:
        centroid, _computed_normal, ref = stacking.ring_frame(
            _xyz(head_atoms), head_stack_ring)
        return (centroid, (-heading[0], -heading[1], 0.0), ref)
    segment = segments[-1]
    stack_ring = records_by_id[segment['molecule_id']]['stack_ring']
    return stacking.ring_frame(_xyz(segment['atoms']), stack_ring)


def attempt_place(pickup_atoms, pickup_stack_ring,
                  tail_c, tail_n, tail_ref, interaction):
    """Place the pickup on the tail frame at the DATASET geometry.

    pickup_atoms: (sym, x, y, z) 4-tuples for the whole pickup molecule.
    interaction: the dataset interaction dict; its distance_a /
    lateral_offset_a drive placement — no invented chemistry.

    Returns (placed_atoms, R, t, ring_centroid):
    - placed_atoms: (sym, x, y, z) 4-tuples, same order/elements as input
    - R, t: stacking.place_pickup's rigid transform (for the bridge)
    - ring_centroid: the placed pickup's recomputed ring centroid (3D)

    Raises ValueError from stacking.ring_frame on non-planar/degenerate
    rings (the caller routes this to SKIP_NONPLANAR).
    """
    placed, R, t = stacking.place_pickup(
        _xyz(pickup_atoms), pickup_stack_ring,
        tail_c, tail_n, tail_ref,
        interaction['distance_a'], interaction['lateral_offset_a'],
        lateral_along_ref=True)
    placed4 = [(pickup_atoms[i][0],
                placed[i][0], placed[i][1], placed[i][2])
               for i in range(len(placed))]
    ring_centroid = stacking.ring_frame(placed, pickup_stack_ring)[0]
    return (placed4, R, t, ring_centroid)


# The wall leg of stacking.check_clash is retired (owner directive
# 2026-09-20c): gate() feeds an effectively UNBOUNDED box so the wall
# check can never fire and the ATOM leg is the only refusal left.
_UNBOUNDED_MIN = (float('-inf'), float('-inf'), float('-inf'))
_UNBOUNDED_MAX = (float('inf'), float('inf'), float('inf'))


def gate(placed_atoms, existing_atoms, box_min2d, box_max2d, display_z):
    """Thin wrapper over stacking.check_clash (no reimplementation).

    ``existing_atoms`` is the caller's full gate set: head + all
    segments + other live pickups. Returns stacking.check_clash's dict
    (or None) unchanged.

    box_min2d / box_max2d / display_z are RETAINED for call-site
    stability only: since 2026-09-20c (owner directive — "remove the
    refuse (let it stack out of box since we only bound the head in
    box)") placements are never refused for leaving the play box, so the
    gate box is effectively unbounded and 'wall' violations can never
    be returned; only 'atom' clashes refuse (REFUSE_ATOM).
    """
    _ = (box_min2d, box_max2d, display_z)  # retained args (see docstring)
    return stacking.check_clash(
        _xyz(placed_atoms), _xyz(existing_atoms),
        _UNBOUNDED_MIN, _UNBOUNDED_MAX)


def resolve(pickup_rec, records_by_id, stacking_data, head_atoms,
            head_stack_ring, heading, segments, existing_atoms,
            box_min2d, box_max2d, display_z):
    """Orchestrate one captured pickup: skip -> place -> gate -> outcome.

    pickup_rec: the captured pickup's record — needs 'set' +
    'has_stack_entry' + 'stack_ring' for the skip taxonomy, and 'atoms'
    ((sym, x, y, z)) for placement. records_by_id: molecule records with
    'stack_ring' (newest-segment tail frames). stacking_data: the validated
    stacking dataset. head_atoms/head_stack_ring/heading: the first-capture
    tail policy inputs. segments: engine segment records (last = newest).
    existing_atoms: the full clash-gate set (head + segments + other live
    pickups). box_min2d/box_max2d/display_z: retained for call-site
    stability; the wall leg is retired (owner directive 2026-09-20c), so
    only atom clashes refuse — placements may land past the box in any
    axis (only the head is box-bound, via GAME-05).

    Returns the outcome contract documented in the module docstring. Never
    raises for data problems (they become outcome codes; a ValueError from
    stacking.ring_frame maps to SKIP_NONPLANAR).
    """
    code = resolve_skip(pickup_rec, stacking_data)
    if code is not None:
        return {'status': 'skipped', 'code': code}

    interaction = molecule_data.interaction_for(pickup_rec, stacking_data)
    try:
        tail_c, tail_n, tail_ref = tail_frame(
            segments, records_by_id, head_atoms, head_stack_ring, heading)
        placed, R, t, ring_centroid = attempt_place(
            pickup_rec['atoms'], pickup_rec['stack_ring'],
            tail_c, tail_n, tail_ref, interaction)
    except ValueError:
        return {'status': 'skipped', 'code': SKIP_NONPLANAR}

    violation = gate(placed, existing_atoms,
                     box_min2d, box_max2d, display_z)
    if violation is not None:
        # gate() can only return 'atom' violations (the wall leg is
        # retired); every refusal is an atom clash.
        return {'status': 'refused', 'code': REFUSE_ATOM,
                'detail': '%.2f A' % violation['distance']}

    return {'status': 'placed',
            'placed_atoms': placed,
            'R': R,
            't': t,
            'ring_centroid_xy': (ring_centroid[0], ring_centroid[1]),
            'interaction': interaction,
            'citation_short':
                stacking_data['citations'][interaction['citation']]['short']}
