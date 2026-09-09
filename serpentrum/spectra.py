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
import math
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


# ---------------------------------------------------------------------------
# Plan 02-09: Turbomole vibspectrum fallback parser + trivial-mode filter.
# Appended below the g98 core (02-01); parse_g98 behavior is unchanged.
# ---------------------------------------------------------------------------

_VIBSPECTRUM_HEADER = '$vibrational spectrum'
_VIBSPECTRUM_END = '$end'


def parse_vibspectrum_text(text):
    """Parse Turbomole-format vibspectrum text -> Spectrum.

    The vibspectrum file carries frequency + IR intensity per mode but NO
    atom geometry and NO displacement vectors: ``atoms == []`` and each
    Mode's ``vectors == ()``. ``n_atoms = 0`` is intentional — consumers
    take N from the g98 parse or the .xyz. Trivial modes (translations /
    rotations) appear explicitly with |freq| < ~10; real_modes() filters
    them out by threshold.

    Grammar (research S1.2, byte-verified against the committed fixture):
      line 1  = '$vibrational spectrum'           (header)
      '#'...  = comment                            (skipped)
      data    = 4-token trivial row  [mode freq intensity '-']
              | 5-token real row    [mode symmetry freq intensity selection]
      last    = '$end'

    Uniform field indexing: ``mode = int(t[0])`` (the file's own 1-based
    numbering, trivial rows included), ``freq = float(t[-3])``,
    ``intensity = float(t[-2])``; ``symmetry = t[1]`` when 5 tokens else
    ``''`` (parsed for grammar validation, not stored — the Mode namedtuple
    from 02-01 carries no symmetry/selection field, per the plan's
    ``Mode(index=mode, freq=freq, intensity=intensity, vectors=())``
    construction). Lines are split with str.splitlines() (neutralizes CRLF
    and a missing trailing newline); callers open files utf-8 (the comment
    header carries a literal U+207B U+00B9 in '(km*mol⁻¹)').

    Non-numeric mode/freq/intensity tokens raise
    ``SpectraParseError('vibspectrum numeric field', ...)`` — never a bare
    ValueError. A wrong token count raises ``SpectraParseError('vibspectrum
    row', ...)``. A missing header or missing $end raises a
    SpectraParseError whose message names the stage and the 1-based line.
    """
    lines = text.splitlines()

    # $end check: the final non-blank line must be '$end'. An empty input
    # or a header-only input both surface here (missing-$end path), which
    # is the plan's loud-failure contract for those cases.
    last_nonblank = None
    for index in range(len(lines) - 1, -1, -1):
        if lines[index].strip():
            last_nonblank = index
            break
    if last_nonblank is None:
        _fail('vibspectrum end', 1, '<empty>',
              "expected '$end' but input is empty")
    if lines[last_nonblank].strip() != _VIBSPECTRUM_END:
        _fail('vibspectrum end', last_nonblank + 1, lines[last_nonblank],
              "expected '$end'")

    # Header check: line 1 must be '$vibrational spectrum'.
    if not lines or lines[0].strip() != _VIBSPECTRUM_HEADER:
        _fail('vibspectrum header', 1,
              lines[0] if lines else '<empty>',
              "expected '%s'" % _VIBSPECTRUM_HEADER)

    modes = []
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith('#'):
            continue
        if stripped == _VIBSPECTRUM_HEADER or stripped == _VIBSPECTRUM_END:
            continue
        tokens = line.split()
        ntok = len(tokens)
        if ntok not in (4, 5):
            _fail('vibspectrum row', index + 1, line,
                  'expected 4 or 5 tokens, got %d' % ntok)
        # ntok is 4 (trivial) or 5 (real) here — else _fail raised.
        # Uniform indexing: t[0]=mode, t[-3]=freq, t[-2]=intensity.
        mode = _to_int(tokens[0], 'vibspectrum numeric field',
                       index + 1, line)
        freq = _to_float(tokens[-3], 'vibspectrum numeric field',
                         index + 1, line)
        intensity = _to_float(tokens[-2], 'vibspectrum numeric field',
                              index + 1, line)
        modes.append(Mode(mode, freq, intensity, ()))

    return Spectrum(0, [], modes)


def parse_vibspectrum(path):
    """Parse the vibspectrum file at ``path`` (utf-8) into a Spectrum."""
    with open(path, encoding='utf-8') as fh:
        return parse_vibspectrum_text(fh.read())


def real_modes(spectrum, threshold=10.0):
    """Return the non-trivial modes of ``spectrum``, order preserved.

    Returns ``[m for m in spectrum.modes if abs(m.freq) >= threshold]``.

    Policy (fixture-verified): threshold on |freq| ONLY.
      - Never on sign: dimer modes 7-9 are negative REAL modes (-31.92 /
        -23.08 / -18.11) and must survive.
      - Never on the selection-rule column: 14 real 'NO' rows carry
        nonzero intensity (min 0.00026) and must survive.
      - Never a hardcoded trivial count: nonlinear molecules have 6
        trivial modes, linear ones 5 — a hardcoded 'skip 6' would silently
        corrupt every linear molecule (the CO2 case: 5 trivial).
      - No-op on g98 spectra: the g98 core projects trivial modes out, so
        all 72 modes have |freq| >= 18.1 and pass the default threshold.
    """
    return [m for m in spectrum.modes if abs(m.freq) >= threshold]


# ---------------------------------------------------------------------------
# Plan 02-12: Gaussian broadening, unified parse dispatcher, loud-failure
# hardening. Appended below the g98 core (02-01) and the vibspectrum
# fallback (02-09); existing parser behavior is unchanged.
# ---------------------------------------------------------------------------

# sigma = fwhm / (2*sqrt(2*ln(2)))  (~ fwhm/2.35482; 16 -> 6.794574,
# 32 -> 13.58915). Precomputed once at import; broaden() multiplies fwhm
# by this factor, never hardcodes the decimal.
_SIGMA_PER_FWHM = 1.0 / (2.0 * math.sqrt(2.0 * math.log(2.0)))


def broaden(modes, fwhm=16.0, x_min=0.0, x_max=None, n_points=800):
    """Sum of Gaussians, one per mode: y(x) = sum(I_i * exp(-0.5*((x-f_i)/sigma)^2)).

    sigma = fwhm / (2*sqrt(2*ln(2)))  (~ fwhm/2.35482; 16 -> 6.794574,
    32 -> 13.58915).
    Grid: xs[i] = x_min + (x_max - x_min) * i / (n_points - 1), i in
    0..n_points-1 (both ends inclusive). x_max default:
    max(3600.0, max(freq) + 5*sigma) — the 3600 floor keeps the plotted
    axis at the xtb display range; with NO modes the default grid is
    [x_min, 3600.0].
    EMPTY MODES -> (grid, [0.0]*n_points): the PINNED zero-curve semantics
    (a silent spectrum plots as a flat zero line, never an exception).
    Negatives are NOT special-cased (their in-grid tail is negligible:
    exp(-11) at -31.9 with fwhm 16); zero-intensity modes contribute
    exactly 0 by arithmetic.
    Raises ValueError on fwhm <= 0 or n_points < 2.
    """
    if fwhm <= 0.0:
        raise ValueError(
            'broaden: fwhm must be positive, got %r' % (fwhm,))
    if n_points < 2:
        raise ValueError(
            'broaden: n_points must be >= 2, got %r' % (n_points,))
    sigma = fwhm * _SIGMA_PER_FWHM
    if x_max is None:
        if modes:
            x_max = max(3600.0,
                        max(m.freq for m in modes) + 5.0 * sigma)
        else:
            x_max = 3600.0
    span = x_max - x_min
    xs = [x_min + span * i / (n_points - 1) for i in range(n_points)]
    if not modes:
        return xs, [0.0] * n_points
    inv_sigma_sq = 1.0 / (sigma * sigma)
    ys = []
    for x in xs:
        total = 0.0
        for m in modes:
            dx = x - m.freq
            total += m.intensity * math.exp(-0.5 * dx * dx * inv_sigma_sq)
        ys.append(total)
    return xs, ys
