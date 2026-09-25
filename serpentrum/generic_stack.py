"""Generic upload pi-stack entry and consent-gated dataset overlay (STACK-06).

This is the DATA half of the generic upload stacking consent feature
(research Approach A): the consent policy is expressed as DATA through the
existing ``molecule_data.interaction_for`` lookup, so the approval gate,
mode gate, placement math, citation resolution, and HUD rendering all
consume the generic entry UNCHANGED.

Invariants this module exists to protect:

* REUSE, never invent — ``GENERIC_INTERACTION``'s ``distance_a`` /
  ``lateral_offset_a`` are the human-approved DATA-02 Set-A numbers
  (3.383 / 1.231, encoding 3.60 A @ 20.0 deg off-normal) copied
  VERBATIM. No new geometry values exist anywhere.
* The dataset FILE (``serpentrum/data/stacking_pi_stack.json``) is the
  shipping contract — it is NEVER modified. The overlay built here is
  in-memory only, per-run.
* Consent is carried by the OVERLAY itself: with the generic entry
  appended, ``interaction_for({'set': '__upload__'}, overlay)`` finds
  it; without it, the lookup returns None exactly as today (the
  consent-OFF byte-identical seam). Every consumer downstream stays
  consent-blind — it just sees "a dataset".
* The generic entry is appended LAST in the copy so first-match file
  order shadows nothing: set_a still first-matches the shipped
  ``pi_stack_pd`` entry; only ``'__upload__'`` (which matches nothing
  in the shipped file by construction, STACK-03) resolves to it.

Purity: stdlib + ``molecule_data`` only — no pymol/Qt/numpy. python3.6,
%-formatting (house style).
"""

import copy

from . import molecule_data

_GENERIC_SUFFIX = ' (generic pi-stack)'

GENERIC_INTERACTION = {
    # Own id — distinct from the shipped 'pi_stack_pd' so recap rows can
    # be told apart via the already-stored interaction_id.
    'id': 'pi_stack_generic',
    # Same mode as the shipped entry — the mode gate consumes it as-is.
    'mode': 'pi_stack',
    # ASCII 'pi-stack' label alphabet (EQ-engine-5); HUD renders this
    # verbatim via pickup_block.
    'name': 'generic pi-stack (illustrative geometry - user-approved)',
    # REUSED from the shipped pi_stack_pd entry — the DATA-02-approved
    # encoding of 3.60 A @ 20 deg off-normal. Never invented.
    'distance_a': 3.383,
    'lateral_offset_a': 1.231,
    # No measurement uncertainty claimed — mirrors the shipped entry;
    # the explanation carries the "not measured" honesty instead.
    'uncertainty_a': None,
    # Cites ONLY an already-approved citation from the shipped table
    # (janiak2000.short == 'Janiak 2000', approved true).
    'citation': 'janiak2000',
    'explanation': (
        'Generic fallback reusing the approved idealized Set A pi-stack '
        'geometry (3.60 A @ 20 deg off-normal); this upload molecule was '
        'not measured - the geometry is illustrative, user-approved via '
        'explicit consent; crystalline-context scope caveat applies '
        '(DATA_SOURCES.md [Janiak 2000]).'),
    # ONLY the upload sentinel — uploads match it, no demo set ever can
    # setloader.UPLOAD_SET_ID '__upload__' is the STACK-03 skip-policy key).
    'applies_to': {'sets': ['__upload__']},
    # Structural approval gate: placement enforces status=='APPROVED'
    # via id-membership. The flag is the mechanism; the GEOMETRY itself
    # is the human-approved DATA-02 decision being reused.
    'status': 'APPROVED',
}


def overlay_stacking_data(stacking_data, consent):
    """Consent-gated in-memory dataset overlay.

    consent falsy -> returns ``stacking_data`` UNCHANGED (same object;
    the zero-copy OFF path — consent OFF is byte-identical to today).

    ``stacking_data is None`` -> returns None in either consent state
    (dataset-unavailable degradation; consumers already handle None).

    Otherwise -> deep-copies the dataset and appends ONE deepcopy of
    ``GENERIC_INTERACTION`` LAST. Appending last keeps first-match
    lookup order intact (set_a still resolves to the shipped entry);
    the extra deepcopy means mutating the appended dict can never
    corrupt the module constant.
    """
    if not consent:
        return stacking_data
    if stacking_data is None:
        return None
    data = copy.deepcopy(stacking_data)
    data['interactions'].append(copy.deepcopy(GENERIC_INTERACTION))
    return data


def history_name(molecule_name, interaction):
    """Recap-grouping display name for a stacked molecule (SC4).

    Returns ``'<molecule> (generic pi-stack)'`` when the placed
    interaction is the generic entry, so the end-of-run recap groups
    consent placements distinctly from dataset placements WITHOUT any
    breakdown_lines edits (EQ-engine-6/EQ-setup-7 — the stored
    interaction_id key is untouched). Dataset entries return the
    molecule name unchanged.
    """
    if interaction.get('id') == GENERIC_INTERACTION['id']:
        return '%s%s' % (molecule_name, _GENERIC_SUFFIX)
    return molecule_name


def has_stack_entry_for(record, stacking_data):
    """Whether ``record`` resolves to any stacking entry in ``stacking_data``.

    The pure half of consent-aware stamping (EQ-engine-2); the GUI call
    site lands in plan 5.2-06. Mirrors setloader._build_record's
    definition (``interaction_for``-based) so demo records read
    identically either way. Semantics: the ANCHORED dataset is the
    consent carrier — recompute the lookup against it; a None dataset
    (gui_setup's degradation contract) falls back to the load-time
    ``has_stack_entry`` flag on the record.
    """
    if stacking_data is None:
        return record.get('has_stack_entry')
    return molecule_data.interaction_for(
        {'set': record.get('set')}, stacking_data) is not None
