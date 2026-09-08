"""Validated demo-data loader for serpentrum's two JSON data files (STACK-02).

The stacking geometry the game places molecules with is a DATA FILE, never
a code constant. This module loads and STRUCTURALLY validates:

- the molecule manifest (sets + molecules, incl. ring_atoms indices for
  stacking)      -> serpentrum/data/demos/manifest.json  (shipped by a later plan)
- the stacking-interaction dataset (mode + distance + lateral offset +
  citation + DRAFT/APPROVED status)
                 -> serpentrum/data/demos/stacking.json (shipped by a later plan)

Both loaders take the PATH of the JSON file; the base directory against
which molecule ``file`` references are checked is derived from that path
(os.path.dirname). Every structural violation raises DataError naming the
file, the entry index, and the offending key/rule, e.g.::

    stacking.json interaction 0: missing key 'distance_a'

so educator-facing data files stay debuggable. Validation is STRUCTURAL
only: a citation key must resolve in the citations table, but 'approved'
is data, not a loader opinion — no chemistry truth is judged here.

DRAFT vs APPROVED is DATA-02's human approval track: DRAFT entries stay
loadable and testable, but nothing ships as chemistry until a human pins
the values and flips the status in the data file. The only DOI used by
the demo data is the one verified live during research (Janiak 2000,
10.1039/b003010o) — no chemistry value is invented by this module or by
its tests (the 3.4 A test value exists solely to reproduce the COMMITTED
dimer2 fixture; the demo-data research recommends 3.6 A for shipping,
which is the human's call, later).

Pure module (purity gate class PURE): stdlib json/os only, zero pymol/
pmg_tk/PyQt5/numpy anywhere, python3.6 syntax only.
"""

import json
import os

# Sanity ceiling for interaction distances: a centroid-centroid stacking
# distance beyond 10 A is a data-entry error, not chemistry (the verified
# pi-stack range is ~3.3-3.8 A; Janiak 2000 abstract: "up to 3.8 A").
MAX_DISTANCE_A = 10.0

# The only interaction statuses a v1 dataset may carry. Case-sensitive on
# purpose: 'draft' is a typo, not a status.
VALID_STATUSES = ('DRAFT', 'APPROVED')


class DataError(ValueError):
    """Invalid demo-data file (unreadable, unparsable, or structurally wrong).

    Message pattern: ``'<file basename> <entry kind> <index>: <problem>'``
    for entry-level problems (e.g. ``stacking.json interaction 0: missing
    key 'distance_a'``) and ``'<file basename>: <problem>'`` for file-level
    ones (e.g. ``manifest.json: unsupported schema_version 2 (expected 1)``).
    """


def _read_json(path):
    """Read + parse a JSON file into a dict, failing loudly as DataError."""
    base = os.path.basename(path)
    try:
        with open(path, 'r') as handle:
            text = handle.read()
    except IOError as exc:
        raise DataError('%s: cannot read file (%s)' % (base, exc))
    try:
        data = json.loads(text)
    except ValueError as exc:
        raise DataError('%s: invalid JSON (%s)' % (base, exc))
    if not isinstance(data, dict):
        raise DataError('%s: top level must be a JSON object (got %s)'
                        % (base, type(data).__name__))
    return data


def _is_int(value):
    """True for real ints only — the py3.6 bool-is-int trap rejects bools.

    isinstance(True, int) is True on every Python 3, so an int validator
    that does not exclude bool explicitly would accept ``atom_count: true``.
    """
    return isinstance(value, int) and not isinstance(value, bool)


def _is_number(value):
    """True for float or int (bools rejected — same trap as _is_int)."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _require_key(container, key, where):
    """Fetch a required mapping key or raise the canonical missing-key error."""
    if key not in container:
        raise DataError("%s: missing key '%s'" % (where, key))
    return container[key]


def _require_str(value, where, key):
    """Validate a required non-empty string field and return it."""
    if not isinstance(value, str) or not value:
        raise DataError("%s: key '%s' must be a non-empty string (got %r)"
                        % (where, key, value))
    return value


def _require_schema_version(data, base):
    """schema_version must be exactly the int 1 (bools rejected)."""
    version = _require_key(data, 'schema_version', base)
    if not _is_int(version) or version != 1:
        raise DataError('%s: unsupported schema_version %r (expected 1)'
                        % (base, version))


def _validate_ring_atoms(ring_atoms, where, atom_count):
    """ring_atoms: list of >= 3 UNIQUE int indices in [0, atom_count)."""
    if not isinstance(ring_atoms, list):
        raise DataError("%s: key 'ring_atoms' must be a list (got %s)"
                        % (where, type(ring_atoms).__name__))
    if len(ring_atoms) < 3:
        raise DataError("%s: key 'ring_atoms' needs at least 3 indices (got %d)"
                        % (where, len(ring_atoms)))
    for index in ring_atoms:
        if not _is_int(index):
            raise DataError("%s: ring_atoms entries must be integers (got %r)"
                            % (where, index))
        if index < 0 or index >= atom_count:
            raise DataError('%s: ring_atoms index %d out of range [0, %d)'
                            % (where, index, atom_count))
    seen = set()
    for index in ring_atoms:
        if index in seen:
            raise DataError('%s: ring_atoms indices must be unique (duplicate %d)'
                            % (where, index))
        seen.add(index)


def _validate_molecule(molecule, where, set_id, base_dir, seen_ids):
    """Validate one manifest molecule entry (rules per key, in schema order)."""
    if not isinstance(molecule, dict):
        raise DataError('%s: molecule must be a JSON object (got %s)'
                        % (where, type(molecule).__name__))

    molecule_id = _require_str(_require_key(molecule, 'id', where), where, 'id')
    if molecule_id in seen_ids:
        raise DataError("%s: duplicate molecule id '%s' (molecule ids must be"
                        ' unique across the whole manifest)' % (where, molecule_id))
    seen_ids.add(molecule_id)

    _require_str(_require_key(molecule, 'name', where), where, 'name')
    file_name = _require_str(_require_key(molecule, 'file', where), where, 'file')
    _require_str(_require_key(molecule, 'source_db', where), where, 'source_db')
    _require_str(_require_key(molecule, 'source_id', where), where, 'source_id')

    atom_count = _require_key(molecule, 'atom_count', where)
    if not _is_int(atom_count) or atom_count <= 0:
        raise DataError("%s: key 'atom_count' must be an int > 0 (got %r)"
                        % (where, atom_count))

    charge = _require_key(molecule, 'charge', where)
    if not _is_int(charge):
        raise DataError("%s: key 'charge' must be an int (got %r)" % (where, charge))

    ring_count = _require_key(molecule, 'ring_count', where)
    if not _is_int(ring_count) or ring_count < 1:
        raise DataError("%s: key 'ring_count' must be an int >= 1 (got %r)"
                        % (where, ring_count))

    _validate_ring_atoms(_require_key(molecule, 'ring_atoms', where),
                         where, atom_count)

    declared_set = _require_key(molecule, 'set', where)
    if declared_set != set_id:
        raise DataError("%s: key 'set' must equal the parent set id '%s' (got %r)"
                        % (where, set_id, declared_set))

    # The geometry file must exist next to the manifest (base_dir is the
    # manifest's own directory, derived from the path the caller passed).
    molecule_path = os.path.join(base_dir, file_name)
    if not os.path.isfile(molecule_path):
        raise DataError("%s: molecule file '%s' not found in the manifest's"
                        " directory" % (where, file_name))


def load_manifest(path):
    """Load + structurally validate a molecule manifest (v1 schema).

    ``path`` is the manifest FILE path; molecule ``file`` references are
    resolved against its directory. Returns the parsed dict on success;
    raises DataError naming file, entry index and rule on any violation.
    """
    base = os.path.basename(path)
    data = _read_json(path)
    _require_schema_version(data, base)

    sets = _require_key(data, 'sets', base)
    if not isinstance(sets, list) or not sets:
        raise DataError("%s: key 'sets' must be a non-empty list" % base)

    base_dir = os.path.dirname(path)
    seen_ids = set()
    for set_index, molecule_set in enumerate(sets):
        where = '%s set %d' % (base, set_index)
        if not isinstance(molecule_set, dict):
            raise DataError('%s: set must be a JSON object (got %s)'
                            % (where, type(molecule_set).__name__))
        set_id = _require_str(_require_key(molecule_set, 'id', where), where, 'id')
        _require_str(_require_key(molecule_set, 'name', where), where, 'name')

        molecules = _require_key(molecule_set, 'molecules', where)
        if not isinstance(molecules, list) or not molecules:
            raise DataError("%s: key 'molecules' must be a non-empty list" % where)

        for mol_index, molecule in enumerate(molecules):
            where_m = '%s molecule %d' % (where, mol_index)
            _validate_molecule(molecule, where_m, set_id, base_dir, seen_ids)

    return data


def _validate_citations(citations, base):
    """Each citation entry: short/doi non-empty str + approved bool."""
    for key in citations:
        where = "%s citation '%s'" % (base, key)
        entry = citations[key]
        if not isinstance(entry, dict):
            raise DataError('%s: citation entry must be an object (got %s)'
                            % (where, type(entry).__name__))
        _require_str(_require_key(entry, 'short', where), where, 'short')
        _require_str(_require_key(entry, 'doi', where), where, 'doi')
        approved = _require_key(entry, 'approved', where)
        if not isinstance(approved, bool):
            raise DataError("%s: key 'approved' must be a bool (got %r)"
                            % (where, approved))


def _validate_applies_to(applies_to, where):
    """applies_to: object with a non-empty 'sets' list of non-empty strings."""
    if not isinstance(applies_to, dict):
        raise DataError("%s: key 'applies_to' must be an object (got %s)"
                        % (where, type(applies_to).__name__))
    sets = _require_key(applies_to, 'sets', where)
    if not isinstance(sets, list) or not sets:
        raise DataError("%s: key 'applies_to' must contain a non-empty 'sets'"
                        ' list' % where)
    for set_id in sets:
        if not isinstance(set_id, str) or not set_id:
            raise DataError("%s: 'applies_to' sets entries must be non-empty"
                            ' strings (got %r)' % (where, set_id))


def _validate_interaction(interaction, where, citations, seen_ids):
    """Validate one interaction entry (rules per key, in schema order)."""
    if not isinstance(interaction, dict):
        raise DataError('%s: interaction must be a JSON object (got %s)'
                        % (where, type(interaction).__name__))

    interaction_id = _require_str(_require_key(interaction, 'id', where),
                                  where, 'id')
    if interaction_id in seen_ids:
        raise DataError("%s: duplicate interaction id '%s'"
                        % (where, interaction_id))
    seen_ids.add(interaction_id)

    _require_str(_require_key(interaction, 'mode', where), where, 'mode')
    _require_str(_require_key(interaction, 'name', where), where, 'name')

    distance = _require_key(interaction, 'distance_a', where)
    if not _is_number(distance) or not 0.0 < distance <= MAX_DISTANCE_A:
        raise DataError("%s: key 'distance_a' must satisfy 0 < d <= %s (got %r)"
                        % (where, MAX_DISTANCE_A, distance))

    offset = _require_key(interaction, 'lateral_offset_a', where)
    if not _is_number(offset) or offset < 0:
        raise DataError("%s: key 'lateral_offset_a' must be a number >= 0 (got %r)"
                        % (where, offset))

    uncertainty = _require_key(interaction, 'uncertainty_a', where)
    if uncertainty is not None and (not _is_number(uncertainty) or uncertainty < 0):
        raise DataError("%s: key 'uncertainty_a' must be null or a number >= 0"
                        ' (got %r)' % (where, uncertainty))

    # Citation is a KEY into the citations table — structural resolution
    # only; whether the cited source is approved is data, not loader opinion.
    citation = _require_key(interaction, 'citation', where)
    if not isinstance(citation, str) or not citation:
        raise DataError("%s: key 'citation' must be a non-empty string (got %r)"
                        % (where, citation))
    if citation not in citations:
        raise DataError("%s: unknown citation '%s'" % (where, citation))

    explanation = _require_key(interaction, 'explanation', where)
    if not isinstance(explanation, str):
        raise DataError("%s: key 'explanation' must be a string (got %r)"
                        % (where, explanation))

    _validate_applies_to(_require_key(interaction, 'applies_to', where), where)

    status = _require_key(interaction, 'status', where)
    if status not in VALID_STATUSES:
        raise DataError("%s: key 'status' must be 'DRAFT' or 'APPROVED' (got %r)"
                        % (where, status))


def load_stacking(path):
    """Load + structurally validate a stacking-interaction dataset (v1).

    ``path`` is the stacking.json FILE path. Returns the parsed dict on
    success; raises DataError naming file, entry index and rule on any
    violation. Both DRAFT and APPROVED entries load — approval gating is
    shipped_interactions()'s job (DATA-02), not the loader's.
    """
    base = os.path.basename(path)
    data = _read_json(path)
    _require_schema_version(data, base)

    interactions = _require_key(data, 'interactions', base)
    if not isinstance(interactions, list) or not interactions:
        raise DataError("%s: key 'interactions' must be a non-empty list" % base)

    citations = _require_key(data, 'citations', base)
    if not isinstance(citations, dict):
        raise DataError("%s: key 'citations' must be an object" % base)
    _validate_citations(citations, base)

    seen_ids = set()
    for index, interaction in enumerate(interactions):
        where = '%s interaction %d' % (base, index)
        _validate_interaction(interaction, where, citations, seen_ids)

    return data


def shipped_interactions(data):
    """Return ONLY the status=='APPROVED' interactions, preserving file order.

    DRAFT entries stay loadable and testable (this whole module happily
    works on DRAFT data) but never ship: DATA-02's human approval track is
    what flips a DRAFT status to APPROVED in the data file — no invented
    or auto-approved chemistry. Callers that consume game-facing chemistry
    must read interactions through this accessor.
    """
    return [interaction for interaction in data['interactions']
            if interaction['status'] == 'APPROVED']


def interaction_for(molecule, data):
    """First interaction (file order — deterministic) applying to a molecule.

    Matches molecule['set'] (a validated manifest molecule's parent set id)
    against each interaction's applies_to['sets']; returns the FIRST match
    or None when none applies — the STACK-03 refuse-and-skip input (no
    applicable interaction => the molecule is skipped, never force-placed).

    NOTE: this does NOT filter by approval status. Callers gate on
    status=='APPROVED' (via shipped_interactions or a direct check) for
    shipping decisions; a DRAFT entry returned here is test/preview data.
    """
    set_id = molecule['set']
    for interaction in data['interactions']:
        if set_id in interaction['applies_to']['sets']:
            return interaction
    return None
