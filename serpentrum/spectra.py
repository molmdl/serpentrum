"""g98 frequency-output parser core for serpentrum (plan 02-01).

Parses the Gaussian-98-style frequency output that ``xtb --ohess`` writes
to ``g98.out``: the Standard-orientation atom block plus frequency blocks
(Frequencies / Red. masses / Frc consts / IR Inten / Raman Activ / Depolar
rows, then per-atom displacement vectors). Written against the committed
fixture grammar (tests/fixtures/xtb/g98.out: 26-atom phenol pi-dimer,
72 modes = 3*26-6 in 24 blocks of 3 columns at stride 35, first
'Frequencies --' line 46, last line 851, EOF-terminated) — never against
fixed columns or fixed line numbers.

Pure stdlib module: the purity gate classifies everything under
serpentrum/ except the entry/GUI modules as PURE, so no pymol/pmg_tk/
PyQt5/numpy import may appear here even inside function bodies.

Scope (ROADMAP wave-1 split): the g98 core ONLY. parse_vibspectrum and
real_modes arrive with plan 02-09; broaden and the parse dispatcher with
plan 02-12. Do not add them here.
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
        int(tokens[0])
        atomic_number = int(tokens[1])
        int(tokens[2])
        atoms.append(Atom(atomic_number, float(tokens[3]), float(tokens[4]),
                          float(tokens[5])))
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
    where vectors[column] is the per-atom tuple list for that column."""
    total = len(lines)
    line = lines[freq_index]
    freq_tokens = line.split('--', 1)[1].split()
    if len(freq_tokens) != 3:
        _fail('frequency block', freq_index + 1, line,
              'expected 3 frequency columns, got %d' % len(freq_tokens))
    freqs = [float(token) for token in freq_tokens]
    # The five property rows follow, in order; each starts with its
    # exactly-prefixed marker. Column values come from the tokens after
    # '--' on each row (never fixed columns).
    intensities = None
    for offset, prefix in enumerate(_PROPERTY_PREFIXES):
        row_index = freq_index + 1 + offset
        if row_index >= total or not lines[row_index].startswith(prefix):
            _fail('frequency block', row_index + 1,
                  lines[row_index] if row_index < total else '<end of file>',
                  'expected property row %r' % prefix.strip())
        if prefix == ' IR Inten    --':
            intensities = [float(token) for token in
                           lines[row_index].split('--', 1)[1].split()]
    # Displacement-vector header, then exactly n_atoms rows.
    header_index = freq_index + 6
    if (header_index >= total
            or not lines[header_index].startswith(_ATOM_HEADER_PREFIX)):
        _fail('frequency block', header_index + 1,
              (lines[header_index] if header_index < total
               else '<end of file>'),
              'expected %r header' % _ATOM_HEADER_PREFIX.strip())
    vectors = [[] for _ in range(3)]
    row_index = header_index
    for atom_number in range(1, n_atoms + 1):
        row_index += 1
        if row_index >= total:
            _fail('frequency block', total, '<end of file>',
                  'unexpected end of file: displacement row %d of %d '
                  'missing' % (atom_number, n_atoms))
        tokens = lines[row_index].split()
        if len(tokens) != 11:  # index, AN, then 3 columns x 3 components
            _fail('frequency block', row_index + 1, lines[row_index],
                  'expected 11 displacement tokens (index, AN, 3 x '
                  '[x y z]), got %d' % len(tokens))
        if int(tokens[0]) != atom_number:
            _fail('frequency block', row_index + 1, lines[row_index],
                  'expected atom index %d, got %r'
                  % (atom_number, tokens[0]))
        for column in range(3):
            base = 2 + 3 * column
            vectors[column].append((float(tokens[base]),
                                    float(tokens[base + 1]),
                                    float(tokens[base + 2])))
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
        for column in range(3):
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
