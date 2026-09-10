"""setloader: validated molecule-record building for demo sets and uploads.

PURE module (stdlib os/tempfile only -- no pymol/pmg_tk/PyQt5/numpy
anywhere; auto-classified PURE by tools/check_purity.py). This is the
loader half of the Phase-3 handoff contract (03-RESEARCH-setup-ui.md
sec 6.3): it lives HERE, not in pymol_bridge.py, because pymol_bridge
imports ``from pymol import cmd`` at module level and therefore CANNOT
be imported under WSL python3.6 (zero-stub test discipline). All logic
that can be unit-tested is unit-tested: manifest cross-verification,
gate enforcement, the ``__upload__`` skip-policy keying, and the
multi-record split live here; the bridge stays a thin cmd-seam.

Two public entry points:

- ``load_demo_set(data_dir, set_id, stacking_path) -> (records, errors)``:
  parses + gates every manifest molecule's SDF and VERIFIES the manifest
  declarations (atom_count, charge, ring_count) against the parsed
  reality. Any mismatch excludes the molecule with an error naming its
  id. Demo records carry ``set=<set_id>`` and ``has_stack_entry``
  computed via ``molecule_data.interaction_for`` against the stacking
  dataset.

- ``load_upload(path, stacking_path) -> (records, errors)``:
  routes by extension (.sdf / .mol2), gates per record, and for
  multi-record SDFs splits accepted records into single-record SDF files
  in one ``srp_upload_`` tempdir. Upload records carry
  ``set='__upload__'`` which matches NO interaction ->
  ``has_stack_entry=False`` (the STACK-03 skip-policy keying, DATA-03).

The ``__upload__`` sentinel is the adopted consolidated decision: no
formula/name matching -- an uploaded benzene must NOT inherit set_a's
stacking entry. The keying reuses ``molecule_data.interaction_for``
without inventing a new lookup.

Tempdir lifecycle: Phase 3 leaves ``srp_upload_*`` tempdirs to OS temp
cleanup (documented, acceptable -- the tempdirs are small single-record
SDF files and the OS /tmp reaper handles them). A future phase may add
explicit cleanup if warranted.

python3.6 syntax (%-formatting), stdlib only. Relative imports
``from . import molfile, molecule_data`` are purity-exempt.
"""

import os
import tempfile

from . import molfile
from . import molecule_data


# Sentinel set id for uploaded molecules. Matches NO interaction in the
# stacking dataset -> has_stack_entry=False -> skip-at-pickup (STACK-03).
UPLOAD_SET_ID = '__upload__'


def package_data_dir():
    """Return the absolute path to serpentrum/data/ (the shipped data dir)."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')


def default_stacking_path():
    """Return the default stacking dataset path (the shipped file name)."""
    return os.path.join(package_data_dir(), 'stacking_pi_stack.json')


def _build_record(molfile_record, *, id, name, file, set_id, source,
                  stacking_data, ring_atoms=None):
    """Build a molecule record dict from a parsed molfile record.

    Computes ``has_stack_entry`` via
    ``molecule_data.interaction_for({'set': set_id}, stacking_data) is not None``
    when ``stacking_data`` is not None, else False.

    ``ring_atoms`` is passed through from the manifest for demo records;
    upload records omit it (they are skip-at-pickup, no stacking
    placement, so ``stacking.ring_frame`` is never called on them).
    """
    has_stack_entry = False
    if stacking_data is not None:
        has_stack_entry = molecule_data.interaction_for(
            {'set': set_id}, stacking_data) is not None
    record = {
        'id': id,
        'name': name,
        'file': file,
        'record_index': molfile_record['record_index'],
        'elements': list(molfile_record['elements']),
        'atom_count': molfile_record['atom_count'],
        'charge': molfile_record['charge'],
        'ring_count': molfile_record['ring_count'],
        'has_explicit_h': molfile_record['has_explicit_h'],
        'has_stack_entry': has_stack_entry,
        'set': set_id,
        'source': source,
        'warnings': list(molfile_record['warnings']),
    }
    if ring_atoms is not None:
        record['ring_atoms'] = list(ring_atoms)
    return record


def load_demo_set(data_dir=None, set_id='set_a', stacking_path=None):
    """Load + verify + gate a demo molecule set -> (records, errors).

    ``data_dir`` is the directory containing manifest.json + SDF files.
    Defaults to ``package_data_dir()`` (the shipped data directory).
    ``set_id`` selects which set to load from the manifest (default
    'set_a'). ``stacking_path`` is the path to the stacking dataset JSON;
    None -> skip the stacking lookup (has_stack_entry=False for all
    records), so tests can run without a stacking file.

    Returns ``(records, errors)``:
    - records: list of molecule record dicts (see module docstring).
    - errors: list of human-readable strings; empty = all good.

    Verification order per molecule:
      1. ``read_sdf`` -- must yield EXACTLY 1 record (multi-record demo
         file -> error + exclude).
      2. ``gate_set`` -- gate reason -> error + exclude.
      3. atom_count / charge / ring_count cross-checks vs the manifest
         (each mismatch -> error + exclude).
      4. record build (has_stack_entry via interaction_for).

    File/parse failures become error entries, never exceptions.
    """
    if data_dir is None:
        data_dir = package_data_dir()

    records = []
    errors = []

    # Load the manifest.
    manifest_path = os.path.join(data_dir, 'manifest.json')
    try:
        manifest = molecule_data.load_manifest(manifest_path)
    except (molecule_data.DataError, IOError) as exc:
        return ([], ['setloader: cannot load manifest: %s' % exc])

    # Load the stacking dataset (if provided).
    stacking_data = None
    if stacking_path is not None:
        try:
            stacking_data = molecule_data.load_stacking(stacking_path)
        except (molecule_data.DataError, IOError) as exc:
            return ([], ['setloader: cannot load stacking dataset: %s' % exc])

    # Find the requested set.
    target_set = None
    for molecule_set in manifest['sets']:
        if molecule_set['id'] == set_id:
            target_set = molecule_set
            break
    if target_set is None:
        return ([], ['setloader: set %r not found in manifest' % set_id])

    # Process each molecule in the set.
    for molecule in target_set['molecules']:
        mol_id = molecule['id']
        mol_file = os.path.join(data_dir, molecule['file'])

        # 1. Read the SDF file (must be single-record).
        try:
            parsed = molfile.read_sdf(mol_file)
        except (molfile.MolFileError, IOError) as exc:
            errors.append('demo molecule %s: cannot read file %s: %s'
                          % (mol_id, molecule['file'], exc))
            continue

        if len(parsed) != 1:
            errors.append('demo molecule %s: file %s must be single-record '
                          '(got %d records)'
                          % (mol_id, molecule['file'], len(parsed)))
            continue

        record = parsed[0]

        # 2. Gate the molecule.
        accepted, rejected = molfile.gate_set([record])
        if rejected:
            _rec, reason = rejected[0]
            errors.append('demo molecule %s: %s' % (mol_id, reason))
            continue

        # 3. Cross-check manifest declarations against parsed reality.
        mismatch = False
        for key in ('atom_count', 'charge', 'ring_count'):
            declared = molecule[key]
            parsed_val = record[key]
            if declared != parsed_val:
                errors.append('demo molecule %s: manifest %s %s does not '
                              'match parsed %s'
                              % (mol_id, key, declared, parsed_val))
                mismatch = True
                break
        if mismatch:
            continue

        # 4. Build the record.
        records.append(_build_record(
            record,
            id=mol_id,
            name=molecule['name'],
            file=mol_file,
            set_id=set_id,
            source='demo',
            stacking_data=stacking_data,
            ring_atoms=molecule['ring_atoms']))

    return (records, errors)


def load_upload(path, stacking_path=None):
    """Load + gate an uploaded SDF/mol2 file -> (records, errors).

    ``path`` is the uploaded file path. ``stacking_path`` is the path to
    the stacking dataset JSON; None -> skip the stacking lookup
    (has_stack_entry=False for all records).

    Routes by extension (case-insensitive):
    - ``.sdf`` -> ``molfile.read_sdf``
    - ``.mol2`` -> ``molfile.read_mol2``
    - else -> error ``'unsupported molecule file type: <ext> (use .sdf
      or .mol2)'``

    Gates per record via ``molfile.gate_set``. Accepted records carry:
    - id ``'upload_<record_index>'``
    - name = title (or id when title is blank)
    - set = ``'__upload__'`` (matches NO interaction -> has_stack_entry
      False, the STACK-03 skip-policy keying)
    - source = ``'upload'``

    Multi-record SDF with >= 1 accepted record: each accepted record is
    written via ``molfile.write_sdf_text`` into
    ``tempfile.mkdtemp(prefix='srp_upload_')`` as
    ``'upload_<record_index>.sdf'``; ``record['file']`` = that path.
    Single-record SDF and mol2 uploads: ``record['file']`` = the
    original path unchanged.

    Rejected records surface as errors (the gate reason already carries
    the ``'<name>: <detail>'`` format). File/parse failures
    (MolFileError / IOError) become error entries, never exceptions.

    Returns ``(records, errors)``.
    """
    # Load the stacking dataset (if provided).
    stacking_data = None
    if stacking_path is not None:
        try:
            stacking_data = molecule_data.load_stacking(stacking_path)
        except (molecule_data.DataError, IOError) as exc:
            return ([], ['setloader: cannot load stacking dataset: %s' % exc])

    # Route by extension (case-insensitive).
    ext = os.path.splitext(path)[1].lower()
    if ext == '.sdf':
        try:
            parsed = molfile.read_sdf(path)
        except (molfile.MolFileError, IOError) as exc:
            return ([], ['setloader: cannot read %s: %s'
                         % (os.path.basename(path), exc)])
    elif ext == '.mol2':
        try:
            parsed = molfile.read_mol2(path)
        except (molfile.MolFileError, IOError) as exc:
            return ([], ['setloader: cannot read %s: %s'
                         % (os.path.basename(path), exc)])
    else:
        return ([], ['unsupported molecule file type: %s '
                     '(use .sdf or .mol2)' % ext])

    # Compute upload names and update titles so gate reasons carry the
    # correct name (title if non-blank, else 'upload_<record_index>').
    for record in parsed:
        title = record.get('title', '').strip()
        if not title:
            record['title'] = 'upload_%d' % record['record_index']
        else:
            record['title'] = title

    # Gate per record.
    accepted, rejected = molfile.gate_set(parsed)

    # Rejections: the gate reason already has '<name>: <detail>' format.
    errors = [reason for _record, reason in rejected]

    # Build records for accepted molecules.
    records = []
    if not accepted:
        return (records, errors)

    is_multi = len(parsed) > 1
    if is_multi and ext == '.sdf':
        # Multi-record SDF: split each accepted record into a
        # single-record SDF file in one srp_upload_ tempdir.
        upload_dir = tempfile.mkdtemp(prefix='srp_upload_')
        for record in accepted:
            idx = record['record_index']
            split_name = 'upload_%d.sdf' % idx
            split_path = os.path.join(upload_dir, split_name)
            with open(split_path, 'w') as handle:
                handle.write(molfile.write_sdf_text(record))
            records.append(_build_record(
                record,
                id='upload_%d' % idx,
                name=record['title'],
                file=split_path,
                set_id=UPLOAD_SET_ID,
                source='upload',
                stacking_data=stacking_data))
    else:
        # Single-record SDF or mol2: file = original path.
        for record in accepted:
            idx = record['record_index']
            records.append(_build_record(
                record,
                id='upload_%d' % idx,
                name=record['title'],
                file=path,
                set_id=UPLOAD_SET_ID,
                source='upload',
                stacking_data=stacking_data))

    return (records, errors)
