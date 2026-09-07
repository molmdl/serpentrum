"""Pure .xyz handoff I/O for the serpentrum snake -> xtb -> spectra flow.

This is the file format the Phase-6 runner writes (snake geometry -> xtb
input) and reads back (xtbopt.xyz). The format facts encoded here are
PROVEN, not guessed: every committed fixture under
.planning/research/xtb-spike-fixtures/ was accepted by xtb 6.7.1pre with
normal termination, so the tolerated variants below are real:

- line 1 is the atom count; LEADING WHITESPACE IS TOLERATED (the phenol
  fixture's count line is '    13').
- line 2 is a free-text comment whose content is arbitrary ('CO2 linear',
  'Optimized at B3LYP/6-31G* level', xtb's 'energy: ... gnorm: ...' line).
- then one row per atom: `Symbol X Y Z`, whitespace-separated with
  arbitrary alignment; blank lines between rows are ignored.

Element symbols are validated CASE-SENSITIVELY against the 118 IUPAC
symbols: 'Cl' is accepted, 'CL' and 'cl' are rejected. This catches the
exact failure xtb itself reports as "Cannot map symbol to atomic number"
(bad.xyz line 3, symbol 'Xx') BEFORE an expensive xtb run is wasted.

Every parse failure raises XyzError carrying the 1-based line number and
the offending line's first ~60 characters, so bad game data points at the
exact row that broke it. Writing is a fixed point: coordinates are
serialized with '%-2s %15.8f %15.8f %15.8f', and re-serializing values
parsed from that format reproduces the file byte-for-byte.

Pure module (purity gate class PURE): stdlib only, zero pymol/pmg_tk/
PyQt5/numpy anywhere, python3.6 syntax only.
"""

# All 118 IUPAC element symbols, in atomic-number order (periods 1-7,
# lanthanides and actinides included). Matching is CASE-SENSITIVE:
# 'Cl' matches, 'CL' and 'cl' do not.
ELEMENT_SYMBOLS = frozenset((
    # Period 1-2
    'H', 'He', 'Li', 'Be', 'B', 'C', 'N', 'O', 'F', 'Ne',
    # Period 3
    'Na', 'Mg', 'Al', 'Si', 'P', 'S', 'Cl', 'Ar',
    # Period 4
    'K', 'Ca', 'Sc', 'Ti', 'V', 'Cr', 'Mn', 'Fe', 'Co', 'Ni', 'Cu', 'Zn',
    'Ga', 'Ge', 'As', 'Se', 'Br', 'Kr',
    # Period 5
    'Rb', 'Sr', 'Y', 'Zr', 'Nb', 'Mo', 'Tc', 'Ru', 'Rh', 'Pd', 'Ag', 'Cd',
    'In', 'Sn', 'Sb', 'Te', 'I', 'Xe',
    # Period 6 (incl. lanthanides La-Lu)
    'Cs', 'Ba', 'La', 'Ce', 'Pr', 'Nd', 'Pm', 'Sm', 'Eu', 'Gd', 'Tb', 'Dy',
    'Ho', 'Er', 'Tm', 'Yb', 'Lu', 'Hf', 'Ta', 'W', 'Re', 'Os', 'Ir', 'Pt',
    'Au', 'Hg', 'Tl', 'Pb', 'Bi', 'Po', 'At', 'Rn',
    # Period 7 (incl. actinides Ac-Lr)
    'Fr', 'Ra', 'Ac', 'Th', 'Pa', 'U', 'Np', 'Pu', 'Am', 'Cm', 'Bk', 'Cf',
    'Es', 'Fm', 'Md', 'No', 'Lr', 'Rf', 'Db', 'Sg', 'Bh', 'Hs', 'Mt', 'Ds',
    'Rg', 'Cn', 'Nh', 'Fl', 'Mc', 'Lv', 'Ts', 'Og',
))

# Fixed writer row format (fixture-proven: xtb accepts any sane spacing;
# we emit exactly this and round-trip it).
ROW_FORMAT = '%-2s %15.8f %15.8f %15.8f'

# How many characters of an offending line an XyzError quotes.
_SNIPPET_MAX = 60


class XyzError(ValueError):
    """Invalid .xyz content (structure, symbol, or number).

    The message names the 1-based line number and quotes the first ~60
    characters of the offending line, e.g.::

        line 3: unknown element symbol 'Xx' (Xx 0.0 0.0 0.0)
    """


def _line_error(lineno, text, message):
    """Build an XyzError for 1-based <lineno> quoting a snippet of <text>."""
    snippet = text.strip()
    if len(snippet) > _SNIPPET_MAX:
        snippet = snippet[:_SNIPPET_MAX] + '...'
    return XyzError('line %d: %s (%s)' % (lineno, message, snippet))


def write_xyz(elements, coords, comment=''):
    """Serialize one .xyz frame to text and return it.

    Line 1 is the atom count; line 2 is <comment> with any '\\r' or '\\n'
    replaced by a single space (a raw newline would corrupt the frame);
    then one ROW_FORMAT row per atom. Raises XyzError when the element
    and coordinate counts differ or a coordinate row is not exactly 3
    long. Symbol validity is enforced on READ (see read_xyz_text), so a
    written frame always parses back or raises loudly.
    """
    if len(elements) != len(coords):
        raise XyzError(
            'write_xyz: %d element symbols but %d coordinate rows'
            % (len(elements), len(coords)))
    lines = [str(len(elements)),
             comment.replace('\r', ' ').replace('\n', ' ')]
    for index in range(len(elements)):
        row = coords[index]
        try:
            width = len(row)
        except TypeError:
            raise XyzError('write_xyz: atom %d coordinates are not a '
                           '3-item sequence (%r)' % (index + 1, row))
        if width != 3:
            raise XyzError('write_xyz: atom %d has %d coordinates, '
                           'need exactly 3' % (index + 1, width))
        lines.append(ROW_FORMAT % (elements[index], row[0], row[1], row[2]))
    return '\n'.join(lines) + '\n'


def write_xyz_file(path, elements, coords, comment=''):
    """Write one .xyz frame (see write_xyz) to <path> as utf-8 text."""
    text = write_xyz(elements, coords, comment=comment)
    with open(path, 'w', encoding='utf-8') as handle:
        handle.write(text)


def read_xyz_text(text):
    """Parse one .xyz frame from <text> -> (comment, atoms).

    <comment> is line 2 verbatim; <atoms> is a list of
    (symbol, x, y, z) tuples in file order. Blank lines between atom
    rows are ignored. Raises XyzError on: fewer than 2 lines, a line-1
    count that is not a positive integer, fewer or extra non-empty atom
    rows vs the declared count, a row with fewer than 4 whitespace-
    separated fields, an unknown element symbol, or a non-float
    coordinate — each message naming the 1-based line number.
    """
    lines = text.splitlines()
    if len(lines) < 2:
        raise XyzError('xyz frame needs a count line and a comment line, '
                       'got %d line(s)' % len(lines))
    count_line = lines[0]
    try:
        count = int(count_line.strip())
    except ValueError:
        raise _line_error(1, count_line, 'atom count must be an integer')
    if count <= 0:
        raise _line_error(1, count_line,
                          'atom count must be a positive integer')
    comment = lines[1]
    atoms = []
    lineno = 2
    for raw in lines[2:]:
        lineno += 1
        stripped = raw.strip()
        if not stripped:
            continue  # blank lines are ignored between/around atom rows
        if len(atoms) >= count:
            raise _line_error(lineno, raw,
                              'extra atom row after the %d declared' % count)
        tokens = stripped.split()
        if len(tokens) < 4:
            raise _line_error(lineno, raw,
                              'atom row needs 4 whitespace-separated '
                              'fields (symbol x y z), got %d' % len(tokens))
        symbol = tokens[0]
        if symbol not in ELEMENT_SYMBOLS:
            raise _line_error(lineno, raw,
                              'unknown element symbol %r' % symbol)
        try:
            x = float(tokens[1])
            y = float(tokens[2])
            z = float(tokens[3])
        except ValueError:
            raise _line_error(lineno, raw, 'coordinate is not a number')
        atoms.append((symbol, x, y, z))
    if len(atoms) < count:
        raise _line_error(1, count_line,
                          'atom count declares %d atoms but only %d atom '
                          'rows found' % (count, len(atoms)))
    return comment, atoms


def read_xyz(path):
    """Read one .xyz frame from <path> (utf-8) -> (comment, atoms)."""
    with open(path, 'r', encoding='utf-8') as handle:
        return read_xyz_text(handle.read())
