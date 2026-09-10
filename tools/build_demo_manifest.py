#!/usr/bin/env python3.6
"""Dev-side one-off builder for serpentrum Demo Set A's manifest.json.

Parses the 5 human-provided PubChem 3D SDF files (CIDs verified in
DATA_SOURCES.md sec 1) via serpentrum.molfile, cross-checks every derived
number against the DATA_SOURCES.md-verified metadata (atom counts +
expected cyclomatic ring counts), and writes serpentrum/data/manifest.json.
ABORTS with a clear message on ANY mismatch -- a fabricated manifest is
never written (AGENTS.md no-fabrication rule).

Idempotent: re-running produces the same manifest.json byte-for-byte
(sorted molecule order, json.dumps indent=2).

Dev-side ONLY (tools/ has no __init__.py and must not get one --
AGENTS.md plugin-path safety). Not imported by the plugin runtime; not
covered by the purity gate (which scans serpentrum/ only).

Usage (from the repo root):

    python3.6 tools/build_demo_manifest.py

Conventions: python3.6 syntax, %-formatting (no f-strings/.format),
stdlib + serpentrum.molfile only.
"""
import json
import os
import sys

# Self-insert the repo root so `import serpentrum.molfile` resolves
# regardless of the caller's cwd (mirrors tests/test_*.py pattern).
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from serpentrum import molfile  # noqa: E402  (sys.path set above)

# DATA_SOURCES.md sec 1 -- verified CIDs + atom counts (public domain,
# US Gov/NCBI; acknowledgment requested). The SDF files must already
# exist in serpentrum/data/ (human checkpoint 03-05 Task 1).
# (name, CID string, expected_atom_count)
MOLECULES = [
    ('benzene', '241', 12),
    ('naphthalene', '931', 18),
    ('anthracene', '8418', 24),
    ('phenanthrene', '995', 24),
    ('biphenyl', '7095', 22),
]

# Expected cyclomatic ring counts (03-RESEARCH-upload-gate.md sec 2.2,
# verified arithmetic: mu = E - V + C). All <= 3 -> all pass the gate.
EXPECTED_RING_COUNTS = [1, 2, 3, 3, 2]

# Set identity for the manifest (matches stacking_pi_stack.json
# applies_to.sets == ['set_a'] and molecule_data schema).
SET_ID = 'set_a'
SET_NAME = 'Aromatic pi-stack'
SOURCE_DB = 'PubChem'

# Where the SDF files live + where manifest.json is written.
_DATA_DIR = os.path.join(_REPO_ROOT, 'serpentrum', 'data')
_MANIFEST_PATH = os.path.join(_DATA_DIR, 'manifest.json')


def _abort(message):
    """Print an error to stderr and exit 1 (never write a bad manifest)."""
    sys.stderr.write('build_demo_manifest: ABORT -- %s\n' % message)
    sys.exit(1)


def _build_molecule_entry(name, cid, expected_atoms, expected_rings):
    """Parse one SDF, cross-check reality, return a manifest molecule dict.

    Aborts on: missing file, != 1 record, atom_count mismatch vs the
    DATA_SOURCES.md table, ring_count mismatch vs the verified cyclomatic
    math, or fewer than 3 ring_atoms (find_ring_atoms returns the 2-core;
    < 3 means the molecule has no ring -- a data error for this set).
    """
    sdf_path = os.path.join(_DATA_DIR, name + '.sdf')
    if not os.path.isfile(sdf_path):
        _abort('%s.sdf not found in %s (checkpoint 03-05 Task 1 not met)'
               % (name, _DATA_DIR))

    records = molfile.read_sdf(sdf_path)
    if len(records) != 1:
        _abort('%s.sdf: expected exactly 1 record, got %d'
               % (name, len(records)))

    record = records[0]
    parsed_atoms = record['atom_count']
    parsed_charge = record['charge']
    parsed_rings = record['ring_count']
    ring_atoms = sorted(molfile.find_ring_atoms(record))

    # Cross-check 1: parsed atom count must match DATA_SOURCES.md.
    if parsed_atoms != expected_atoms:
        _abort('%s: parsed atom_count %d != DATA_SOURCES.md expected %d'
               % (name, parsed_atoms, expected_atoms))

    # Cross-check 2: cyclomatic ring count must match verified math.
    if parsed_rings != expected_rings:
        _abort('%s: parsed ring_count %d != expected %d'
               % (name, parsed_rings, expected_rings))

    # Cross-check 3: ring_atoms must have >= 3 atoms (schema minimum;
    # find_ring_atoms returns the 2-core, so a ringless molecule yields []).
    if len(ring_atoms) < 3:
        _abort('%s: find_ring_atoms returned %d atoms (need >= 3)'
               % (name, len(ring_atoms)))

    return {
        'id': name,
        'name': name.capitalize(),
        'file': name + '.sdf',
        'source_db': SOURCE_DB,
        'source_id': 'CID %s' % cid,
        'atom_count': parsed_atoms,
        'charge': parsed_charge,
        'ring_count': parsed_rings,
        'ring_atoms': ring_atoms,
        'set': SET_ID,
    }


def build():
    """Build + write manifest.json. Returns the manifest dict."""
    molecules = []
    for (name, cid, expected_atoms), expected_rings in \
            zip(MOLECULES, EXPECTED_RING_COUNTS):
        entry = _build_molecule_entry(name, cid, expected_atoms,
                                      expected_rings)
        molecules.append(entry)

    manifest = {
        'schema_version': 1,
        'sets': [
            {
                'id': SET_ID,
                'name': SET_NAME,
                'molecules': molecules,
            },
        ],
    }

    with open(_MANIFEST_PATH, 'w') as handle:
        handle.write(json.dumps(manifest, indent=2))
        handle.write('\n')

    return manifest


def _print_summary(manifest):
    """Print a summary table to stdout (id, CID, atoms, charge, rings, #ring_atoms)."""
    print('Demo Set A manifest written: %s' % _MANIFEST_PATH)
    print()
    print('%-14s %-8s %5s %6s %5s %10s' %
          ('id', 'CID', 'atoms', 'charge', 'rings', 'ring_atoms'))
    print('-' * 54)
    for mol in manifest['sets'][0]['molecules']:
        print('%-14s %-8s %5d %6d %5d %10d' %
              (mol['id'], mol['source_id'], mol['atom_count'],
               mol['charge'], mol['ring_count'], len(mol['ring_atoms'])))
    print()
    print('All cross-checks passed (atom counts + ring counts match'
          ' DATA_SOURCES.md / verified cyclomatic math).')


if __name__ == '__main__':
    _print_summary(build())
