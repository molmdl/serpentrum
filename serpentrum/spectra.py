"""g98 frequency-output parser core for serpentrum (plan 02-01).

Parses the Gaussian-98-style frequency output that ``xtb --ohess`` writes
to ``g98.out``: the Standard-orientation atom block plus frequency blocks
(Frequencies / Red. masses / Frc consts / IR Inten / Raman Activ / Depolar
rows, then per-atom displacement vectors). Block column counts come from
the tokens after '--' on the Frequencies line (1-3; a remainder block
carries fewer than 3), and each block's displacement layout is declared by
its ' Atom AN' header: one coordinate-column label per float, chunked into
one tuple per frequency column (real xtb/Gaussian blocks declare X Y Z per
mode; the plan's synthetic remainder block declares a single coordinate). Written against the committed
fixture grammar (tests/fixtures/xtb/g98.out: 26-atom phenol pi-dimer,
72 modes = 3*26-6 in 24 blocks of 3 columns at stride 35, first
'Frequencies --' line 46, last line 851, EOF-terminated) — never against
fixed columns or fixed line numbers.

Pure stdlib module: the purity gate classifies everything under
serpentrum/ except the entry/GUI modules as PURE, so no pymol/pmg_tk/
PyQt5/numpy import may appear here even inside function bodies.

Scope (ROADMAP wave-1 split): the g98 core ONLY. The Turbomole-format
fallback parser and the trivial-mode filter arrive with plan 02-09; the
line-shape convolution and the parse dispatcher with plan 02-12. Do not
add them here.
"""
from collections import namedtuple

Mode = namedtuple('Mode', 'index freq intensity vectors')
#   index:     int   - 1-based, running count across blocks (fixture: 1..72)
#   freq:      float - cm^-1; negatives kept as negatives
#   intensity: float - km/mol (IR)
#   vectors:   list of (x, y, z) float tuples per atom - len == n_atoms
Atom = namedtuple('Atom', 'atomic_number x y z')

Spectrum = namedtuple('Spectrum', 'n_atoms atoms modes')
#   atoms: list of Atom (from the g98 Standard-orientation block)
#   modes: list of Mode, in file order


class SpectraParseError(ValueError):
    """Loud parse failure: the message carries the parser stage, the
    1-based line number where applicable, and the offending line's first
    ~80 chars. A botched numeric token must surface as THIS error, never
    as a bare ValueError."""


# The five property rows of one frequency block, in exact fixture order;
# every prefix carries exactly one leading space (verified 2026-09-06).
_PROPERTY_PREFIXES = (
    ' Red. masses --',
    ' Frc consts  --',
    ' IR Inten    --',
    ' Raman Activ --',
    ' Depolar     --',
)
_ATOM_HEADER_PREFIX = ' Atom AN'


def _excerpt(line):
    """First ~80 chars of an offending line, for error messages."""
    text = line.strip()
    if len(text) > 80:
        text = text[:77] + '...'
    return text


def _fail(stage, lineno, line, detail):
    """Raise the loud error: stage + 1-based line + excerpt."""
    raise SpectraParseError(
        '%s: line %d: %s [%s]' % (stage, lineno, detail, _excerpt(line)))


def _to_float(token, stage, lineno, line):
    """float() with the loud-failure wrap: a non-numeric token (including
    the g98 '******' overflow token) raises SpectraParseError, never a
    bare ValueError."""
    try:
        return float(token)
    except ValueError:
        _fail(stage, lineno, line,
              'token %r is not a number' % token)


def _to_int(token, stage, lineno, line):
    """int() with the loud-failure wrap (same contract as _to_float)."""
    try:
        return int(token)
    except ValueError:
        _fail(stage, lineno, line,
              'token %r is not an integer' % token)


def _is_dash_line(line):
    """True for the all-dash separator lines framing the atom table."""
    stripped = line.strip()
    return len(stripped) >= 2 and set(stripped) == set('-')


def _parse_atom_block(lines):
    """Parse the Standard-orientation atom block; return the Atom list.

    An absent 'Standard orientation:' line yields [] so the frequency
    scan can deliver its own (more specific) loud failure for files like
    a failed-run log. A PRESENT but malformed block fails loudly here.
    """
    total = len(lines)
    start = None
    for lineno, line in enumerate(lines):
        if line.strip() == 'Standard orientation:':
            start = lineno + 1
            break
    if start is None:
        return []
    # Header frame: dashed line, header text lines, dashed line. Header
    # text is skipped by structure (dash-to-dash), never by line count.
    dash_start = start
    while dash_start < total and not _is_dash_line(lines[dash_start]):
        dash_start += 1
    if dash_start >= total:
        raise SpectraParseError(
            'atom block: line %d: no dashed table header after '
            '"Standard orientation:"' % total)
    dash_rows = dash_start + 1
    while dash_rows < total and not _is_dash_line(lines[dash_rows]):
        dash_rows += 1
    if dash_rows >= total:
        raise SpectraParseError(
            'atom block: line %d: unterminated dashed table header '
            '(no second dash line)' % total)
    atoms = []
    row = dash_rows + 1
    while row < total and not _is_dash_line(lines[row]):
        tokens = lines[row].split()
        if len(tokens) != 6:
            _fail('atom block', row + 1, lines[row],
                  'expected 6 tokens (center, atomic number, type, x, y, '
                  'z), got %d' % len(tokens))
        # Row grammar: int, int, int, float, float, float. Only the
        # atomic number and coordinates are carried into Atom.
        _to_int(tokens[0], 'atom block', row + 1, lines[row])
        atomic_number = _to_int(tokens[1], 'atom block', row + 1, lines[row])
        _to_int(tokens[2], 'atom block', row + 1, lines[row])
        atoms.append(Atom(
            atomic_number,
            _to_float(tokens[3], 'atom block', row + 1, lines[row]),
            _to_float(tokens[4], 'atom block', row + 1, lines[row]),
            _to_float(tokens[5], 'atom block', row + 1, lines[row])))
        row += 1
    if row >= total:
        _fail('atom block', total, '<end of file>',
              'unterminated atom block (no closing dash line)')
    if len(atoms) < 3:
        _fail('atom block', row + 1, lines[row],
              'only %d atom rows; a molecule needs at least 3 atoms'
              % len(atoms))
    return atoms


def _parse_frequency_block(lines, freq_index, n_atoms):
    """Parse one frequency block starting at its ' Frequencies --' line
    (0-based index). Returns (freqs, intensities, vectors, end_index)
    where vectors[column] is the per-atom tuple list for that column.

    The column count comes from the Frequencies line's own token list,
    never from a fixed width: a normal block carries 3 columns, a
    remainder block (n_modes mod 3 != 0) carries 1-2.
    """
    total = len(lines)
    line = lines[freq_index]
    freq_tokens = line.split('--', 1)[1].split()
    ncols = len(freq_tokens)
    if not 1 <= ncols <= 3:
        _fail('frequency block', freq_index + 1, line,
              'expected 1-3 frequency columns, got %d' % ncols)
    freqs = [_to_float(token, 'frequency block', freq_index + 1, line)
             for token in freq_tokens]
    # The five property rows follow, in order; each starts with its
    # exactly-prefixed marker and yields exactly ncols float values.
    intensities = None
    for offset, prefix in enumerate(_PROPERTY_PREFIXES):
        row_index = freq_index + 1 + offset
        if row_index >= total or not lines[row_index].startswith(prefix):
            _fail('frequency block', row_index + 1,
                  lines[row_index] if row_index < total else '<end of file>',
                  'expected property row %r' % prefix.strip())
        row = lines[row_index]
        row_tokens = row.split('--', 1)[1].split()
        if len(row_tokens) != ncols:
            _fail('frequency block', row_index + 1, row,
                  'expected %d values after %r, got %d'
                  % (ncols, prefix.strip(), len(row_tokens)))
        values = [_to_float(token, 'frequency block', row_index + 1, row)
                  for token in row_tokens]
        if prefix == ' IR Inten    --':
            intensities = values
    # Displacement-vector header, then exactly n_atoms rows. The header
    # DECLARES the coordinate layout: 'Atom AN' labels followed by one
    # X/Y/Z-style column label per coordinate. Real g98 blocks list 3
    # labels per mode (X Y Z per column); the synthetic remainder block
    # of the plan declares a single coordinate per mode. Either way the
    # row grammar is token-count-driven: 2 + len(header coordinate
    # labels) tokens per row, chunked into ncols per-mode groups.
    header_index = freq_index + 6
    if (header_index >= total
            or not lines[header_index].startswith(_ATOM_HEADER_PREFIX)):
        _fail('frequency block', header_index + 1,
              (lines[header_index] if header_index < total
               else '<end of file>'),
              'expected %r header' % _ATOM_HEADER_PREFIX.strip())
    header_tokens = lines[header_index].split()
    coord_columns = len(header_tokens) - 2  # minus the 'Atom' 'AN' labels
    if coord_columns < 1 or coord_columns % ncols != 0:
        _fail('frequency block', header_index + 1, lines[header_index],
              'header declares %d coordinate columns for %d frequency '
              'column(s); expected a positive multiple of %d'
              % (coord_columns, ncols, ncols))
    components = coord_columns // ncols
    row_tokens_expected = 2 + coord_columns
    vectors = [[] for _ in range(ncols)]
    row_index = header_index
    for atom_number in range(1, n_atoms + 1):
        row_index += 1
        if row_index >= total:
            _fail('frequency block', total, '<end of file>',
                  'unexpected end of file: displacement row %d of %d '
                  'missing' % (atom_number, n_atoms))
        row = lines[row_index]
        tokens = row.split()
        if len(tokens) != row_tokens_expected:
            _fail('frequency block', row_index + 1, row,
                  'expected %d displacement tokens (index, AN, %d x '
                  '[x y z]), got %d'
                  % (row_tokens_expected, ncols, len(tokens)))
        if _to_int(tokens[0], 'frequency block', row_index + 1, row) \
                != atom_number:
            _fail('frequency block', row_index + 1, row,
                  'expected atom index %d, got %r'
                  % (atom_number, tokens[0]))
        _to_int(tokens[1], 'frequency block', row_index + 1, row)
        for column in range(ncols):
            base = 2 + column * components
            vectors[column].append(tuple(
                _to_float(tokens[base + k], 'frequency block',
                          row_index + 1, row)
                for k in range(components)))
    return freqs, intensities, vectors, row_index + 1


def _parse_frequency_blocks(lines, atoms):
    """Scan the whole file for frequency blocks; return the Mode list."""
    total = len(lines)
    modes = []
    mode_index = 0
    lineno = 0
    found = False
    while lineno < total:
        line = lines[lineno]
        if not line.startswith(' Frequencies --'):
            lineno += 1
            continue
        found = True
        if not atoms:
            raise SpectraParseError(
                'frequency block: line %d: frequency section found but no '
                '"Standard orientation:" atom block precedes it; cannot '
                'size displacement rows [%s]'
                % (lineno + 1, _excerpt(line)))
        freqs, intensities, vectors, end_index = _parse_frequency_block(
            lines, lineno, len(atoms))
        for column in range(len(freqs)):
            mode_index += 1
            modes.append(Mode(mode_index, freqs[column], intensities[column],
                              vectors[column]))
        lineno = end_index
    if not found:
        detail = ("no line starts with ' Frequencies --' (file carries no "
                  'g98 frequency output)')
        if not atoms:
            detail += ' and no Standard-orientation atom block either'
        raise SpectraParseError('no frequency section found: %s' % detail)
    return modes


def parse_g98_text(text):
    """Parse g98 frequency-output text into a Spectrum.

    Lines are split with str.splitlines() (neutralizes CRLF and a missing
    trailing newline); callers open files with encoding='utf-8' (the
    header carries a literal U+207B U+00B9).
    """
    lines = text.splitlines()
    atoms = _parse_atom_block(lines)
    modes = _parse_frequency_blocks(lines, atoms)
    return Spectrum(len(atoms), atoms, modes)


def parse_g98(path):
    """Parse the g98.out file at ``path`` (utf-8) into a Spectrum."""
    with open(path, encoding='utf-8') as fh:
        return parse_g98_text(fh.read())
