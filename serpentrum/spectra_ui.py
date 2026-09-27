"""The Spectra tab's PURE decision/display half (plan 07-01;
07-RESEARCH-spectra-seam.md Q7).

Every string/index decision the Spectra UI needs lives here, so the GUI
modules (07-07..07-09) stay thin wiring and never re-derive a label or a
row. Four builders:

- ``freq_label`` — the SINGLE shared frequency formatter for the entire
  Spectra UI. Imaginary convention: negative freqs render as a magnitude
  with an ASCII hyphen-minus and a trailing ``i`` (-31.9175 ->
  '-31.9i'); non-negatives render plain ('%.1f'). ASCII is pinned
  deliberately: REQUIREMENTS.md's typographic '-31.9i' (U+2212) is a
  prose display convention only — code ships ASCII because U+2212 glyph
  coverage is [TRAIN]-risky and the house HUD strings are ASCII
  (07-RESEARCH-qt-plot.md [TRAIN] 2). COORDINATION: plot_logic.py
  (07-02, same wave) deliberately imports NO frequency formatter; the v1
  plot shows no raw frequency labels (ascending axis, count-only
  caption). If a future plot surface ever prints a frequency, it MUST
  import this function — a hand-rolled second formatter is the named
  drift risk (07-RESEARCH-qt-plot.md pitfall 10).
- ``table_rows`` — every spectrum mode in file order (negatives and
  zero-intensity rows included), as (index, freq_label, intensity_label)
  tuples. The intensity label is '%.4g': the vibspectrum fixture's
  smallest real intensity is 0.00026 — '%.2f' would render it '0.00',
  erasing SPECTRA-05's zero-intensity distinction — while an exact 0.0
  renders '0'.
- ``mode_arrow_primitives`` — total selector from a 1-based mode index
  to (atom positions, displacement vectors) for the FROZEN
  cgo_build.mode_arrows builder (cgo_build.py:134-208: directions
  unit-normalized, ALL arrows uniform length; scale is the only knob;
  v1 pins scale=1.0). Returns None, never an exception, when vectors
  are unavailable (vibspectrum parse: atoms == [] and every
  Mode.vectors == () — spectra.py:313-321), the atom list is empty, or
  the index is out of range. Atom order is the g98 Standard-orientation
  order == the xtb run-input order == xtbopt.xyz order
  (07-RESEARCH-spectra-seam.md Q4b: no reordering seam anywhere).
- ``run_status_lines`` — run-verdict lines derived SOLELY from the
  frozen spectra_run record vocabulary (xtb_run.DONE/FAILED/CANCELLED,
  imported — never re-pinned; 06-02 owns the strings): the status plus
  a joined problems line when problems are present. NEVER opens or
  re-scans the log text — the 'abnormal termination' substring trap
  stays dead (06-RESEARCH-guard pitfall 8; xtbenv.evaluate_run owns
  verdicts).
- ``record_spectrum_paths`` (plan 07-08) — the display-path precedence
  over the frozen record: g98 first (the displacement vectors + atom
  block live there), vibspectrum fallback, ``(None, None, 'none')``
  when the record is degenerate or the keys are missing. Pure
  selection ONLY — filesystem existence checks stay in the GUI caller
  (gui_spectra.SpectraTab._populate_spectrum).

Purity: stdlib + ``from . import xtb_run`` (intra-package relative import,
exempt — tools/check_purity.py:95-98); new pure modules auto-classify PURE
(check_purity.py:56-57), so no registration edit. python3.6 syntax,
%-formatting only.

ACCEPTED LIMITATION (07-RESEARCH-spectra-seam.md Q1 risk 1): no co2
g98.out fixture exists anywhere, so the linear 5-trivial-mode g98 leg
cannot be unit-tested end-to-end today. Zero-intensity table coverage is
proven via synthetic Mode tuples + the synthetic co2 vibspectrum fixture;
the linear g98 leg stays smoke-only behind the real-xtb ``--xtb`` gate.
"""

from . import xtb_run


def freq_label(freq):
    """Render one frequency for display.

    freq < 0 -> '-' + ('%.1f' % abs(freq)) + 'i' (ASCII hyphen-minus;
    e.g. freq_label(-31.9175) == '-31.9i'); freq >= 0 -> '%.1f' % freq.

    This is THE one imaginary-convention formatter for the whole Spectra
    UI (table rows today, any future plot caption). REQUIREMENTS.md's
    '-31.9i' is the docs' typographic rendering; code ships ASCII
    (U+2212 glyph coverage is [TRAIN]-risky; HUD strings are ASCII).
    """
    if freq < 0.0:
        return '-' + ('%.1f' % abs(freq)) + 'i'
    return '%.1f' % freq


def table_rows(spectrum):
    """    [(index:int, freq_label:str, intensity_label:str), ...] for EVERY
    mode of ``spectrum``, in file order — negatives and zero-intensity
    rows included. No filtering: the caller decides g98-all-modes vs
    real_modes() fallback before calling. ``spectrum`` may be a Spectrum
    namedtuple (its .modes are iterated) or a bare Mode iterable (the
    real_modes() return value — spectra.py:402-418 returns a list, not a
    Spectrum).

    intensity_label is '%.4g': keeps 0.00026-class intensities visible
    (the co2/vibspectrum fixtures' smallest real value) while an exact
    0.0 renders '0' — the SPECTRA-05 zero-intensity distinction.
    """
    modes = spectrum.modes if hasattr(spectrum, 'modes') else spectrum
    return [(m.index, freq_label(m.freq), '%.4g' % m.intensity)
            for m in modes]


def imaginary_note(freqs):
    """One ASCII guidance line when any freq < 0, else None; wording and
    cutoffs owner-approved at GATE D (08-01) as d2-option-b-two-tier:

    - No imaginary modes -> None (the caller appends nothing).
    - Every imaginary mode strictly below 20i (|freq| < 20.0) -> the
      benign tier, counting ALL imaginary modes:
      '%d small imaginary mode(s) (<20i cm-1): soft inter-stack modes,
      physical for molecular stacks'
    - Any imaginary mode at or above 20i -> the saddle tier WINS,
      counting ONLY the large imaginary modes:
      '%d large imaginary mode(s) (>=20i cm-1): possible saddle point -
      check the structure'

    Boundary: exactly -20.0 lands on the saddle line (the benign cutoff
    is strict <). House style keeps '(s)' even for a singular count —
    no plural special-casing. 'cm-1' and the ASCII hyphen match the
    table header and freq_label conventions. The >=20i tier has never
    been observed in repo runs; its wording is owner-approved, not
    observed-derived.
    """
    imaginary = [f for f in freqs if f < 0.0]
    if not imaginary:
        return None
    large = [f for f in imaginary if abs(f) >= 20.0]
    if large:
        return ('%d large imaginary mode(s) (>=20i cm-1): possible saddle '
                'point - check the structure' % len(large))
    return ('%d small imaginary mode(s) (<20i cm-1): soft inter-stack '
            'modes, physical for molecular stacks' % len(imaginary))


def mode_arrow_primitives(spectrum, mode_index):
    """(atoms_xyz, vectors) for the 1-based ``mode_index`` — raw material
    for the GUI's FROZEN cgo_build.mode_arrows call (cgo_build.py:134-208:
    directions unit-normalized, every nonzero arrow drawn at uniform
    scale*1.2 A length; scale is the only knob; v1 pins scale=1.0).

    Returns None (NEVER an exception) when vectors are unavailable:
    ``spectrum.atoms`` empty, ``mode_index`` out of the 1..len(modes)
    range, or the mode carries no displacement vectors (a vibspectrum
    parse has every Mode.vectors == () — spectra.py:313-321).

    atoms_xyz = [(float x, float y, float z), ...] in g98
    Standard-orientation order (== xtb run-input order == xtbopt.xyz
    order — no reordering seam, 07-RESEARCH-spectra-seam.md Q4b);
    vectors = [(float dx, float dy, float dz), ...] for those atoms.
    """
    if not spectrum.atoms:
        return None
    if mode_index < 1 or mode_index > len(spectrum.modes):
        return None
    mode = spectrum.modes[mode_index - 1]
    if not mode.vectors:
        return None
    atoms = [(float(a.x), float(a.y), float(a.z)) for a in spectrum.atoms]
    vectors = [tuple(float(component) for component in vector)
               for vector in mode.vectors]
    return (atoms, vectors)


def run_status_lines(record):
    """Verdict lines derived SOLELY from the frozen spectra_run record
    vocabulary (xtb_run status constants — imported, never re-pinned;
    06-02 owns the strings).

    Output shape: ``['xtb finished: %s' % status]`` plus a
    ``'problems: ' + '; '.join(problems)`` line when the problems list is
    non-empty. Never opens or re-scans the log file: the 'abnormal
    termination' substring trap stays dead (06-RESEARCH-guard pitfall 8;
    xtbenv.evaluate_run owns the run verdict). A record carrying a
    missing/unreadable 'log_path' key renders identically.
    """
    status = record.get('status')
    lines = ['xtb finished: %s' % status]
    problems = record.get('problems') or []
    if problems:
        lines.append('problems: %s' % '; '.join(str(p) for p in problems))
    return lines


def record_spectrum_paths(record):
    """Display-path precedence over the frozen spectra_run record ->
    ``(g98_path, vibspectrum_path, source)``.

    Precedence (07-RESEARCH-spectra-seam.md Q4d): g98 first — it alone
    carries the displacement vectors + the atom block — so a record
    with g98_path set yields ``(g98, vibs, 'g98')`` even when the
    vibspectrum path is also present. A record with only
    vibspectrum_path yields ``(None, vibs, 'vibspectrum')`` (the caller
    appends the vectors-unavailable note). A degenerate record (both
    paths None/falsey — failed/cancelled runs may carry None paths) or
    missing keys yields ``(None, None, 'none')``.

    Pure selection ONLY: this NEVER touches the filesystem — existence
    checks (os.path.isfile) stay in the GUI caller
    (gui_spectra.SpectraTab._populate_spectrum), keeping the whole
    degenerate matrix unit-testable.
    """
    g98 = record.get('g98_path')
    vibs = record.get('vibspectrum_path')
    if g98:
        return (g98, vibs, 'g98')
    if vibs:
        return (None, vibs, 'vibspectrum')
    return (None, None, 'none')
