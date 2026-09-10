"""serpentrum.setup_logic — setup schema, defaults, validation, save/load
and seeded head randomization (PURE).

Plan 02-07 (wave 1 of Phase 2). This module owns the setup DICT that
Phase 3's setup tab edits and Phase 4's GameEngine consumes: the schema
version, the documented defaults, the box xy-extent presets, validation
(per-key errors + the single N-cubed hessian-cost warning), save/load
round-trip as sorted-key JSON, and seed-deterministic head selection.

Scope (research R7 — implement EXACTLY this): schema + defaults +
validate + save/load round-trip + seeded randomize, all unit-tested.
NOT in this plan: Qt wiring (Phase 3 setup tab), the 6-button row
semantics (SETUP-07, Phase 8), friendly corrupt-file UX (SETUP-08,
Phase 8 — v1 ``load_setup`` raises loudly; Phase 8 wraps it). The
win-cap/atom-budget warning here is the PURE half of SETUP-06 /
SPECTRA-06; the actual pre-xtb re-check lives in Phase 6's runner.

Determinism: ``randomize_head`` uses a PRIVATE ``random.Random(seed)``
instance per call — NEVER the global ``random`` module (determinism +
reproducibility on the same 3.6 build; the global module would advance
shared state across calls and break seed-to-seed isolation).

python3.6 syntax only (%-formatting, no dataclasses/walrus); PURE module
(json/random stdlib + one intra-package import) — no pymol / pmg_tk /
PyQt5 / numpy anywhere (enforced by tools/check_purity.py, which
auto-classifies this module PURE; relative intra-package imports are
purity-exempt); zero sys.modules stubs. The xtb-path rules live in
``serpentrum.xtbenv.validate_binary_path``; ``_xtb_path_problems``
delegates to it (unified Phase 3 per 02-02-SUMMARY.md:109) — single
source of the rules, no drift.
"""

import json
import random

from .xtbenv import validate_binary_path

# Schema version (research R7). v1 ships Set A only. load_setup raises
# loudly on any other schema_version; friendly UX is Phase 8 (SETUP-08).
SCHEMA_VERSION = 1

# Demo sets this build knows. v1 ships Set A only (locked decision);
# an unknown id is a validation error (SETUP-03).
KNOWN_SETS = ('set_a',)

# Documented default setup (research R7 / SETUP-04). Callers MUST take a
# COPY via new_setup() — never mutate DEFAULTS directly. Every value is a
# scalar or None, so a shallow dict copy suffices (no nested mutables).
DEFAULTS = {
    'schema_version': SCHEMA_VERSION,
    'demo_set': 'set_a',           # SETUP-04: Set A only (locked)
    'head_molecule': 'random',     # SETUP-04 default 'random'
    'box_preset': 'medium',        # SETUP-03; extents table below
    'xtb_path': None,              # SETUP-05: None = auto-detect
    'win_cap_molecules': 10,       # SETUP-06 (~10 mol / ~100 atoms safe)
    'atom_budget': 100,            # warning threshold (hessian ~N^3)
    'broadening_fwhm': 16.0,       # cm^-1; STACK.md §6: ~10-20 typical
    'speed': 3.0,                  # A/s (mirrors game_engine SPEED_A_PER_S)
}

# Box xy-extents in Angstrom (research R7). Consumed by
# GameEngine(box_min, box_max) in Phase 4. z-depth is display-only and
# is the bridge's concern (Phase 4/5) — NOT encoded here.
BOX_PRESETS = {
    'small': ((-12.0, -12.0), (12.0, 12.0)),
    'medium': ((-18.0, -18.0), (18.0, 18.0)),
    'large': ((-25.0, -25.0), (25.0, 25.0)),
}

# Exact N-cubed hessian-cost warning (SETUP-06 / SPECTRA-06 pure half).
# Rationale: PITFALLS 2 measured 13 atoms 0.28 s / 26 atoms 1.03 s
# hessian wall; N^3 extrapolation puts a ~100-atom snake at 30-90 s. The
# runtime pre-xtb re-check is Phase 6's runner; this is the static half.
HESSIAN_WARNING = ('hessian cost scales ~N^3; '
                   'a ~100-atom snake may take 30-90 s')


class SetupError(ValueError):
    """Raised by save_setup (validation failure) and load_setup (corrupt
    JSON / foreign schema_version / non-dict payload). v1 raises loudly;
    Phase 8 (SETUP-08) wraps these in friendly UX."""


def new_setup():
    """Return a fresh COPY of DEFAULTS that callers may mutate freely.

    All DEFAULTS values are scalars or None, so a shallow ``dict(DEFAULTS)``
    copy is sufficient — no nested mutables need a deep copy. Mutating the
    returned dict never touches the module-level DEFAULTS.
    """
    return dict(DEFAULTS)


def _is_number(value):
    """True for int/float but NOT bool (py3.6 bool-is-int trap:
    ``isinstance(True, int)`` is True, but a bool setup value is a bug,
    not a number)."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _xtb_path_problems(path):
    """Validate a user-configured xtb binary path.

    Delegates to ``serpentrum.xtbenv.validate_binary_path`` — the single
    source of the xtb-path rules (unified Phase 3 per
    02-02-SUMMARY.md:109; previously a local mirror kept in sync by
    hand). The message contract is unchanged: returns a list of problem
    strings (empty list = valid) with the same literals as before:

      (a) empty / None / non-string -> 'xtb path is empty'
      (b) missing on disk           -> "'<path>' does not exist"
      (c) exists but is a directory -> "'<path>' is not a file"
      (d) contains ' or "           -> "path contains quote character(s):
                                       '<path>'"

    Kept as a thin wrapper (not inlined into validate()) so the name
    documents the concern and tests can pin the delegation directly.
    """
    return validate_binary_path(path)


def validate(setup):
    """Validate a setup dict -> (errors: [str], warnings: [str]).

    Never raises for invalid input — errors are DATA, not exceptions.
    Errors accumulate in this order (one precise string per failed
    check, each naming the offending key):

      schema_version  != SCHEMA_VERSION
      demo_set        not in KNOWN_SETS
      box_preset      not in BOX_PRESETS
      win_cap_molecules  not a number, or < 1, or > hard max (20)
      atom_budget        not a number, or < 1   (no hard max — see warning)
      xtb_path        set (not None) but _xtb_path_problems non-empty
      speed           not a number, or <= 0
      broadening_fwhm not a number, or <= 0
      head_molecule   not a non-empty str

    WARNINGS (at most ONE — fires once if EITHER trigger exceeds its
    safe default): win_cap_molecules > 10 OR atom_budget > 100 ->
    exactly HESSIAN_WARNING. The actual pre-xtb re-check is Phase 6's
    runner (SPECTRA-06 runtime half); this is the static pure half.
    """
    errors = []
    warnings = []

    # --- errors (listed order) ---
    sv = setup.get('schema_version')
    if sv != SCHEMA_VERSION:
        errors.append('schema_version %r not supported '
                      '(this build reads version %d)' % (sv, SCHEMA_VERSION))

    demo_set = setup.get('demo_set')
    if demo_set not in KNOWN_SETS:
        errors.append('demo_set %r is not a known set (known: %s)'
                      % (demo_set, ', '.join(KNOWN_SETS)))

    box_preset = setup.get('box_preset')
    if box_preset not in BOX_PRESETS:
        errors.append('box_preset %r is not a known preset (known: %s)'
                      % (box_preset, ', '.join(BOX_PRESETS)))

    cap = setup.get('win_cap_molecules')
    if not _is_number(cap) or cap < 1 or cap > 20:
        errors.append('win_cap_molecules %r is out of range (allowed 1..20)'
                      % (cap,))

    budget = setup.get('atom_budget')
    if not _is_number(budget) or budget < 1:
        errors.append('atom_budget %r is out of range (must be >= 1)'
                      % (budget,))

    xtb_path = setup.get('xtb_path')
    if xtb_path is not None:
        errors.extend(_xtb_path_problems(xtb_path))

    speed = setup.get('speed')
    if not _is_number(speed) or speed <= 0:
        errors.append('speed %r must be a number > 0' % (speed,))

    fwhm = setup.get('broadening_fwhm')
    if not _is_number(fwhm) or fwhm <= 0:
        errors.append('broadening_fwhm %r must be a number > 0' % (fwhm,))

    head_molecule = setup.get('head_molecule')
    if not isinstance(head_molecule, str) or not head_molecule:
        errors.append('head_molecule %r must be a non-empty string'
                      % (head_molecule,))

    # --- warnings (at most one: the N-cubed hessian cost) ---
    # Guarded by _is_number so a non-numeric cap/budget never crashes the
    # comparison (errors are data, not exceptions).
    cap_over = _is_number(cap) and cap > 10
    budget_over = _is_number(budget) and budget > 100
    if cap_over or budget_over:
        warnings.append(HESSIAN_WARNING)

    return errors, warnings


def save_setup(setup):
    """Serialize a setup dict -> sorted-key indented JSON text.

    Validates FIRST: if validate(setup) reports any errors, raises
    SetupError listing them (warnings do NOT block save — a setup with a
    high cap/budget is still serializable; the warning is advisory). On a
    clean setup returns ``json.dumps(setup, sort_keys=True, indent=2)`` —
    stable text for share-a-setup (SETUP-08, Phase 8 educator flow).
    """
    errors, _warnings = validate(setup)
    if errors:
        raise SetupError('setup is invalid: ' + '; '.join(errors))
    return json.dumps(setup, sort_keys=True, indent=2)


def load_setup(text):
    """Parse JSON text -> setup dict. v1 raises loudly (SetupError) on:

      - invalid JSON (any ValueError/JSONDecodeError) ->
        'setup text is not valid JSON: <msg>'
      - non-dict payload (e.g. a JSON list or scalar) ->
        'setup text is not a JSON object (got <type>)'
      - schema_version != SCHEMA_VERSION ->
        'setup schema_version <sv> not supported (this build reads <v>)'

    v1 does NOT validate the loaded dict beyond schema_version — full
    validation is the CALLER's validate() call (a freshly loaded setup is
    untrusted and should be validate()d before use). Friendly corrupt-file
    UX is Phase 8 (SETUP-08); this pure half just raises precisely.
    """
    try:
        data = json.loads(text)
    except ValueError as exc:  # JSONDecodeError is a ValueError subclass.
        raise SetupError('setup text is not valid JSON: %s' % (exc,))
    if not isinstance(data, dict):
        raise SetupError('setup text is not a JSON object (got %s)'
                         % (type(data).__name__,))
    sv = data.get('schema_version')
    if sv != SCHEMA_VERSION:
        raise SetupError('setup schema_version %s not supported '
                         '(this build reads version %d)' % (sv, SCHEMA_VERSION))
    return data


def randomize_head(candidates, seed):
    """Choose a head molecule id from candidates via a PRIVATE seeded RNG.

    Returns ``random.Random(seed).choice(candidates)`` — a fresh
    ``random.Random(seed)`` instance per call, NEVER the global ``random``
    module (determinism + seed-to-seed isolation: two calls with the same
    seed always agree, and an intervening different-seed call never
    perturbs a given seed's result). Empty candidates -> SetupError.
    candidates = validated molecule ids (caller's responsibility).
    """
    if not candidates:
        raise SetupError('no head molecule candidates')
    return random.Random(seed).choice(candidates)
