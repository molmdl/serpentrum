"""Pure SDF V2000 / mol2 reader, cyclomatic ring counter, and load-time gate.

This is the DATA half's foundation: every uploaded/demo molecule is parsed
and gated HERE (pure, WSL-testable, zero-stub) before anything touches
PyMOL. The gate rejects unsafe molecules with a clear reason (SC1) and
computes the graph facts (ring count, ring atoms, charge, explicit H)
that molecule records carry into Phase 5/6.

Kept in ONE cohesive module per 03-RESEARCH-upload-gate.md sec 8.2 (parse
+ gate are tightly coupled; extending molecule_data or xyzio was rejected
there).

Format facts encoded here:

- SDF V2000 is a multi-record format: records are separated by lines whose
  stripped content is ``$$$$``. Each record has a title (line 1), a
  program/timestamp line (line 2), a comment (line 3), a counts line
  (line 4: 3-char atom count + 3-char bond count + metadata + ``V2000``),
  an atom block, a bond block, and a property block (``M  END`` closes it).
  Formal charges survive via ``M  CHG`` records (PITFALLS 11,
  [SRC: chempy/mol.py:74-81]); sum ALL values across ALL M CHG lines.

- mol2 carries PARTIAL charges only ([SRC: chempy/mol2.py:74]) -> formal
  charge is assumed 0 and a warning is emitted.

- Ring count = cyclomatic number mu = E - V + C (circuit rank = SSSR count
  for normal organics). Computed from the bond graph: V = atom count,
  E = len(bonds), C = connected components via BFS on adjacency. Verified
  demo math: benzene 1, naphthalene 2, anthracene 3, phenanthrene 3,
  biphenyl 2.

Every parse failure raises MolFileError carrying the 1-based line number
and the offending line's first ~60 characters, mirroring xyzio.XyzError.

Pure module (purity gate class PURE): stdlib only, zero pymol/pmg_tk/
PyQt5/numpy anywhere, python3.6 syntax only. ELEMENT_SYMBOLS is reused
from xyzio via an intra-package relative import (purity-exempt).
"""

from .xyzio import ELEMENT_SYMBOLS

# How many characters of an offending line a MolFileError quotes.
_SNIPPET_MAX = 60

# Warning text emitted for mol2 records (formal charges do not survive).
MOL2_CHARGE_WARNING = ('mol2 does not preserve formal charges; charge '
                       'assumed 0. Use SDF for ionic species.')


class MolFileError(ValueError):
    """Invalid SDF/mol2 content (structure, symbol, or number).

    The message names the 1-based line number and quotes the first ~60
    characters of the offending line, e.g.::

        line 7: expected atom row 3 but found property/end line (M  END)
    """


def _line_error(lineno, text, message):
    """Build a MolFileError for 1-based <lineno> quoting a snippet of <text>.

    Mirrors xyzio._line_error (xyzio.py:73-78).
    """
    snippet = text.strip()
    if len(snippet) > _SNIPPET_MAX:
        snippet = snippet[:_SNIPPET_MAX] + '...'
    return MolFileError('line %d: %s (%s)' % (lineno, message, snippet))


def count_rings(bonds, atom_count):
    """Cyclomatic number mu = E - V + C (circuit rank = SSSR count).

    <bonds> is a list of (i, j) 0-based atom-index pairs. <atom_count> is
    V (the number of vertices). E = len(bonds). C = connected components
    counted via BFS on the adjacency built from <bonds>.

    For normal organic molecules mu equals the SSSR count, so "<= 3 rings"
    means mu <= 3. H atoms are pendant (net-zero effect on mu: each adds
    1 vertex + 1 edge). Multi-component graphs are handled correctly by
    the C term.
    """
    if atom_count <= 0:
        return 0
    adjacency = [set() for _ in range(atom_count)]
    for a, b in bonds:
        if 0 <= a < atom_count and 0 <= b < atom_count:
            adjacency[a].add(b)
            adjacency[b].add(a)
    visited = set()
    components = 0
    for start in range(atom_count):
        if start in visited:
            continue
        components += 1
        queue = [start]
        visited.add(start)
        while queue:
            node = queue.pop(0)
            for neighbor in adjacency[node]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
    return len(bonds) - atom_count + components


def read_sdf_text(text):
    """Parse multi-record SDF V2000 <text> -> list of record dicts.

    Records are split on lines whose stripped content is ``$$$$``. Each
    record dict carries: title, elements, coords, bonds, charges,
    record_index, atom_count, charge, ring_count, has_explicit_h, warnings.

    Raises MolFileError (with 1-based line number + snippet) on any
    structural violation or failed int/float conversion.
    """
    lines = text.splitlines()
    records = []
    record_index = 0
    pos = 0
    while pos < len(lines):
        start = pos
        while pos < len(lines) and lines[pos].strip() != '$$$$':
            pos += 1
        record_lines = lines[start:pos]
        if pos < len(lines):
            pos += 1  # skip the $$$$ separator line
        # Skip empty records (e.g. trailing blank lines after last $$$$).
        if not any(line.strip() for line in record_lines):
            continue
        record = _parse_sdf_record(record_lines, start, record_index)
        records.append(record)
        record_index += 1
    return records


def read_sdf(path):
    """Read an SDF file (utf-8) -> list of record dicts (see read_sdf_text)."""
    with open(path, 'r', encoding='utf-8') as handle:
        return read_sdf_text(handle.read())


def _parse_sdf_record(record_lines, line_offset, record_index):
    """Parse one SDF V2000 record; line numbers are absolute 1-based.

    <line_offset> is the 0-based index of the record's first line in the
    full file, so the 1-based absolute line number for 0-based index i
    within <record_lines> is line_offset + i + 1.
    """

    def abs_lineno(i):
        return line_offset + i + 1

    if len(record_lines) < 4:
        lineno = abs_lineno(0)
        text = record_lines[0] if record_lines else ''
        raise _line_error(lineno, text,
                          'record %d: expected at least 4 lines (title, '
                          'program, comment, counts), got %d'
                          % (record_index, len(record_lines)))

    title = record_lines[0].strip()

    # Counts line is line 4 (0-based index 3).
    natoms, nbonds = _parse_counts_line(record_lines[3], abs_lineno(3))

    # Atom block: lines 4..(4+natoms-1).
    elements = []
    coords = []
    for i in range(natoms):
        idx = 4 + i
        if idx >= len(record_lines):
            last = len(record_lines) - 1
            raise _line_error(abs_lineno(last),
                              record_lines[last] if record_lines else '',
                              'expected %d atom rows but only %d found'
                              % (natoms, i))
        line = record_lines[idx]
        stripped = line.strip()
        if not stripped or stripped.startswith('M'):
            raise _line_error(abs_lineno(idx), line,
                              'expected atom row %d but found property/end '
                              'line' % (i + 1))
        element, coord = _parse_atom_line(line, abs_lineno(idx))
        elements.append(element)
        coords.append(coord)

    # Bond block: lines (4+natoms)..(4+natoms+nbonds-1).
    bonds = []
    for i in range(nbonds):
        idx = 4 + natoms + i
        if idx >= len(record_lines):
            last = len(record_lines) - 1
            raise _line_error(abs_lineno(last),
                              record_lines[last] if record_lines else '',
                              'expected %d bond rows but only %d found'
                              % (nbonds, i))
        line = record_lines[idx]
        stripped = line.strip()
        if not stripped or stripped.startswith('M'):
            raise _line_error(abs_lineno(idx), line,
                              'expected bond row %d but found property/end '
                              'line' % (i + 1))
        bonds.append(_parse_bond_line(line, abs_lineno(idx), natoms))

    # Property block: M lines (M CHG for charges, M END closes).
    charges = {}
    idx = 4 + natoms + nbonds
    while idx < len(record_lines):
        line = record_lines[idx]
        stripped = line.strip()
        if stripped == 'M  END':
            break
        tokens = stripped.split()
        if len(tokens) >= 2 and tokens[0] == 'M' and tokens[1] == 'CHG':
            _parse_m_chg_tokens(tokens, abs_lineno(idx), charges, natoms,
                                line)
        idx += 1

    charge = sum(charges.values())
    ring_count = count_rings(bonds, len(elements))
    has_explicit_h = 'H' in elements

    return {
        'title': title,
        'elements': elements,
        'coords': coords,
        'bonds': bonds,
        'charges': charges,
        'record_index': record_index,
        'atom_count': len(elements),
        'charge': charge,
        'ring_count': ring_count,
        'has_explicit_h': has_explicit_h,
        'warnings': [],
    }


def _parse_counts_line(line, lineno):
    """Parse (natoms, nbonds) from a V2000 counts line.

    Whitespace-split is the primary path; fixed 3-char slices are the
    fallback (handles rows with unusual spacing).
    """
    tokens = line.split()
    natoms = None
    nbonds = None
    if len(tokens) >= 2:
        try:
            natoms = int(tokens[0])
            nbonds = int(tokens[1])
        except ValueError:
            natoms = None
    if natoms is None:
        try:
            natoms = int(line[0:3])
            nbonds = int(line[3:6])
        except (ValueError, IndexError):
            raise _line_error(lineno, line,
                              'counts line: cannot parse atom count and '
                              'bond count')
    return natoms, nbonds


def _parse_atom_line(line, lineno):
    """Parse (element, (x, y, z)) from a V2000 atom row.

    Whitespace-split primary (tokens[0:3] = coords, tokens[3] = element);
    fixed-width fallback (cols 0-9, 10-19, 20-29 = coords, cols 31-33 =
    element). Element validated case-sensitively against ELEMENT_SYMBOLS.
    """
    tokens = line.split()
    element = None
    coords = None
    if len(tokens) >= 4:
        try:
            x = float(tokens[0])
            y = float(tokens[1])
            z = float(tokens[2])
            element = tokens[3]
            coords = (x, y, z)
        except ValueError:
            element = None
    if element is None or coords is None:
        try:
            x = float(line[0:10])
            y = float(line[10:20])
            z = float(line[20:30])
            element = line[31:34].strip()
            coords = (x, y, z)
        except (ValueError, IndexError):
            raise _line_error(lineno, line,
                              'atom line: cannot parse coordinates and '
                              'element')
    if element not in ELEMENT_SYMBOLS:
        raise _line_error(lineno, line,
                          'unknown element symbol %r' % element)
    return element, coords


def _parse_bond_line(line, lineno, natoms):
    """Parse (a1, a2) 0-based atom indices from a V2000 bond row.

    Whitespace-split primary (tokens[0], tokens[1] = 1-based indices);
    fixed 3-char slices fallback. Indices validated in [1, natoms].
    """
    tokens = line.split()
    a1 = None
    a2 = None
    if len(tokens) >= 2:
        try:
            a1 = int(tokens[0])
            a2 = int(tokens[1])
        except ValueError:
            a1 = None
    if a1 is None:
        try:
            a1 = int(line[0:3])
            a2 = int(line[3:6])
        except (ValueError, IndexError):
            raise _line_error(lineno, line,
                              'bond line: cannot parse atom indices')
    if a1 < 1 or a2 < 1 or a1 > natoms or a2 > natoms:
        raise _line_error(lineno, line,
                          'bond line: atom index out of range [1, %d]'
                          % natoms)
    return (a1 - 1, a2 - 1)


def _parse_m_chg_tokens(tokens, lineno, charges, natoms, line):
    """Parse M CHG property line tokens into the <charges> dict.

    tokens = ['M', 'CHG', pair_count, idx1, chg1, idx2, chg2, ...].
    Atom indices are 1-based in the file; stored 0-based in <charges>.
    """
    rest = tokens[2:]
    if not rest:
        return
    try:
        pair_count = int(rest[0])
    except ValueError:
        raise _line_error(lineno, line,
                          'M CHG: pair count is not an integer')
    if len(rest) < 1 + pair_count * 2:
        raise _line_error(lineno, line,
                          'M CHG: expected %d index/charge pairs but found '
                          'fewer' % pair_count)
    for i in range(pair_count):
        try:
            atom_idx = int(rest[1 + i * 2])
            charge_val = int(rest[2 + i * 2])
        except ValueError:
            raise _line_error(lineno, line,
                              'M CHG: pair %d is not an integer' % i)
        if atom_idx < 1 or atom_idx > natoms:
            raise _line_error(lineno, line,
                              'M CHG: atom index %d out of range [1, %d]'
                              % (atom_idx, natoms))
        charges[atom_idx - 1] = charge_val


def write_sdf_text(record):
    """Serialize one record dict to V2000 text ending with ``$$$$``.

    Fixed-width V2000: counts line ``%3d%3d ... 999 V2000``, atom rows
    ``%10.4f%10.4f%10.4f %-3s 0 ...``, bond rows ``%3d%3d%3d  0`` (type 1
    = single), M CHG lines from ``record['charges']`` (<= 8 pairs/line).
    Round-trips through read_sdf_text: read -> write -> read reproduces
    the same elements/bonds/charge/coords (enables the Phase-3 upload
    split in 03-04).
    """
    elements = record['elements']
    coords = record['coords']
    bonds = record['bonds']
    charges = record['charges']
    natoms = len(elements)
    nbonds = len(bonds)

    lines = []
    # Line 1: title.
    lines.append(record.get('title', ''))
    # Line 2: program/timestamp line.
    lines.append('  serpentrum')
    # Line 3: comment (blank).
    lines.append('')
    # Line 4: counts line.
    lines.append('%3d%3d  0  0  0  0  0  0  0  0999 V2000'
                 % (natoms, nbonds))
    # Atom block.
    for i in range(natoms):
        x, y, z = coords[i]
        lines.append(
            '%10.4f%10.4f%10.4f %-3s 0  0  0  0  0  0  0  0  0  0  0  0'
            % (x, y, z, elements[i]))
    # Bond block (bond type 1 = single for all; type not stored on record).
    for a, b in bonds:
        lines.append('%3d%3d%3d  0' % (a + 1, b + 1, 1))
    # M CHG property lines (<= 8 pairs per line).
    if charges:
        items = sorted(charges.items())
        for chunk_start in range(0, len(items), 8):
            chunk = items[chunk_start:chunk_start + 8]
            parts = ['M  CHG%3d' % len(chunk)]
            for idx, chg in chunk:
                parts.append('%4d%4d' % (idx + 1, chg))
            lines.append(''.join(parts))
    # M END + record separator.
    lines.append('M  END')
    lines.append('$$$$')
    return '\n'.join(lines) + '\n'


def read_mol2_text(text):
    """Parse mol2 <text> -> list of record dicts.

    mol2 carries PARTIAL charges only (PITFALLS 11,
    [SRC: chempy/mol2.py:74]) -> formal charge is assumed 0 and a
    warning is appended to ``record['warnings']``. Element symbols are
    extracted from the sybyl atom type (e.g. ``C.ar`` -> ``C``).

    Same MolFileError contract (1-based line + snippet) as read_sdf_text.
    """
    lines = text.splitlines()

    # Locate the @<TRIPOS>MOLECULE section header.
    mol_start = None
    for i, line in enumerate(lines):
        if line.strip() == '@<TRIPOS>MOLECULE':
            mol_start = i
            break
    if mol_start is None:
        return []  # no molecule section -> empty list

    # Molecule name is the line after the header.
    title = ''
    if mol_start + 1 < len(lines):
        title = lines[mol_start + 1].strip()

    # Locate @<TRIPOS>ATOM and @<TRIPOS>BOND sections.
    atom_start = None
    bond_start = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped == '@<TRIPOS>ATOM':
            atom_start = i
        elif stripped == '@<TRIPOS>BOND':
            bond_start = i

    # Parse atom rows.
    elements = []
    coords = []
    if atom_start is not None:
        pos = atom_start + 1
        while pos < len(lines):
            stripped = lines[pos].strip()
            if stripped.startswith('@<TRIPOS>'):
                break
            if stripped:
                tokens = stripped.split()
                if len(tokens) >= 6:
                    try:
                        x = float(tokens[2])
                        y = float(tokens[3])
                        z = float(tokens[4])
                    except ValueError:
                        raise _line_error(pos + 1, lines[pos],
                                          'mol2 atom line: cannot parse '
                                          'coordinates')
                    sybyl_type = tokens[5]
                    element = sybyl_type.split('.')[0]
                    if element not in ELEMENT_SYMBOLS:
                        raise _line_error(pos + 1, lines[pos],
                                          'unknown element symbol %r'
                                          % element)
                    elements.append(element)
                    coords.append((x, y, z))
            pos += 1

    # Parse bond rows.
    bonds = []
    if bond_start is not None:
        pos = bond_start + 1
        while pos < len(lines):
            stripped = lines[pos].strip()
            if stripped.startswith('@<TRIPOS>'):
                break
            if stripped:
                tokens = stripped.split()
                if len(tokens) >= 3:
                    try:
                        a1 = int(tokens[1])
                        a2 = int(tokens[2])
                    except ValueError:
                        raise _line_error(pos + 1, lines[pos],
                                          'mol2 bond line: cannot parse '
                                          'atom indices')
                    bonds.append((a1 - 1, a2 - 1))
            pos += 1

    ring_count = count_rings(bonds, len(elements))
    has_explicit_h = 'H' in elements

    return [{
        'title': title,
        'elements': elements,
        'coords': coords,
        'bonds': bonds,
        'charges': {},
        'record_index': 0,
        'atom_count': len(elements),
        'charge': 0,
        'ring_count': ring_count,
        'has_explicit_h': has_explicit_h,
        'warnings': [MOL2_CHARGE_WARNING],
    }]


def read_mol2(path):
    """Read a mol2 file (utf-8) -> list of record dicts (see read_mol2_text)."""
    with open(path, 'r', encoding='utf-8') as handle:
        return read_mol2_text(handle.read())


def find_ring_atoms(record):
    """Return sorted indices of atoms in any ring (the 2-core of the graph).

    Iteratively removes pendant atoms (degree < 2) until the remaining
    subgraph has all degrees >= 2. The surviving atoms are ring atoms.
    Returns ``[]`` when the graph is acyclic (no rings survive).

    For benzene this yields the 6 ring carbons; for methane ``[]``.
    """
    bonds = record['bonds']
    atom_count = record['atom_count']
    if atom_count == 0:
        return []

    adjacency = [set() for _ in range(atom_count)]
    for a, b in bonds:
        if 0 <= a < atom_count and 0 <= b < atom_count:
            adjacency[a].add(b)
            adjacency[b].add(a)

    removed = set()
    changed = True
    while changed:
        changed = False
        for i in range(atom_count):
            if i in removed:
                continue
            degree = len(adjacency[i] - removed)
            if degree < 2:
                removed.add(i)
                changed = True

    return [i for i in range(atom_count) if i not in removed]


# Elements considered "organic" for the explicit-H gate.
_ORGANIC_ELEMENTS = frozenset(('C', 'N', 'O'))


def gate_molecule(record):
    """Check a molecule record against the load-time gate (SC1 / DATA-03).

    Checks IN ORDER:
      (a) ring_count > 3  ->  reject (reason names the count and the limit)
      (b) organic (C/N/O) with zero explicit H  ->  reject (pre-protonated
          file required; auto-H is banned per PITFALLS 11)
      (c) inorganic with zero explicit H  ->  accept + append hydrogen
          advisory to ``record['warnings']``

    Charge is INFORMATION, never a rejection.

    Returns ``(ok, reason)``: ok is True/False; reason is None when
    accepted, a clear human-readable string when rejected.
    """
    name = record.get('title', 'molecule')

    # (a) Ring-count gate.
    if record['ring_count'] > 3:
        return (False,
                '%s: has %d rings (limit is 3)'
                % (name, record['ring_count']))

    # (b) Organic + zero explicit H.
    elements = record['elements']
    is_organic = any(e in _ORGANIC_ELEMENTS for e in elements)
    if is_organic and not record['has_explicit_h']:
        return (False,
                '%s: no explicit hydrogens found - provide a '
                'pre-protonated file (auto-H is not used per policy)'
                % name)

    # (c) Inorganic + zero explicit H: warn but accept.
    if not is_organic and not record['has_explicit_h']:
        record['warnings'].append(
            '%s: no hydrogens - verify this is correct for an inorganic '
            'molecule' % name)

    return (True, None)


def gate_set(records):
    """Apply gate_molecule to a list; return ``(accepted, rejected)``.

    ``accepted`` is a list of records that passed the gate.
    ``rejected`` is a list of ``(record, reason)`` tuples in input order.
    """
    accepted = []
    rejected = []
    for record in records:
        ok, reason = gate_molecule(record)
        if ok:
            accepted.append(record)
        else:
            rejected.append((record, reason))
    return accepted, rejected
