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
    'speed': 6.0,                  # A/s = the 'normal' tier (owner-final
                                   # 2026-09-25 feel-check; game_engine's
                                   # SPEED_A_PER_S stays 3.0 as the v1
                                   # baseline + kwarg fallback only)
    'generic_stack_consent': False,  # STACK-06 (Phase 5.2): generic upload
                                     # pi-stack consent; OFF by default —
                                     # absent key = OFF via merge_defaults
                                     # (docstring below).
}

# Box xy-extents in Angstrom (research R7). Consumed by
# GameEngine(box_min, box_max) in Phase 4. z-depth is display-only and
# is the bridge's concern (Phase 4/5) — NOT encoded here.
#
# OWNER-APPROVED CONFIG CHANGES:
# 2026-09-19 (05-16 checkpoint): enlarged from the research-R7 values
#   (small +/-12, medium +/-18, large +/-25) to small +/-20, medium
#   +/-30, large +/-45 — a cap-10 straight chain (10 x 3.60 = 36.0 A)
#   plus the 1.0 A crash margin could never fit in the old medium.
# 2026-09-20 (05-16 re-test, owner directive "with win cap 10, box
#   dimension must scale too"): enlarged again. Rationale: the win cap
#   default is 10 -> the full train (head + 9 eaten = 10 x 3.60 =
#   36.0 A straight) plus maneuvering room (a full rigid sweep of that
#   chain traces a ~36 A radius arc; a few floating pickups occupy
#   spawn lanes) must fit COMFORTABLY in the default. MEDIUM
#   (+/-55, 110 A span) is sized for exactly that: a centered 36 A
#   chain sweeps inside the box with ~19 A headroom per side; SMALL
#   (+/-35, 70 A span) is deliberately challenging (cap-10 chain fits
#   straight, cross-box sweeps clip); LARGE (+/-85, 170 A span) is
#   generous. Straight-fit table (max N straight segments with
#   3.6*N <= 2H - 2*BOUNDARY_MARGIN_A(1.0)):
#     small  +/-35 -> 68 A usable -> 18 segments
#     medium +/-55 -> 108 A usable -> 30 segments
#     large  +/-85 -> 168 A usable -> 46 segments
# Default stays 'medium'. BOX_DISPLAY_Z (5.0) is UNCHANGED (display-only;
# 2026-09-20c owner directive: the placement wall gate is gone — the
# chain may stack past the box in any axis; only the head is box-bound
# via GAME-05, and biphenyl's genuine atom clash stays the designed
# refuse demonstrator).
BOX_PRESETS = {
    'small': ((-35.0, -35.0), (35.0, 35.0)),
    'medium': ((-55.0, -55.0), (55.0, 55.0)),
    'large': ((-85.0, -85.0), (85.0, 85.0)),
}

# Speed tiers: named difficulty levels as (name, A/s) pairs (plan 5.1-02,
# SC1). OWNER-FINALIZED at the 5.1-06 feel-check (2026-09-25): the drafts
# (2.0/3.0/4.5/6.0) all played too slow — "only expert feel like playing"
# — so the scale shifted up: relaxed 3.0 (= the old v1 baseline) and
# normal 6.0 (= the old expert, the owner's playable anchor) are FINAL;
# fast 7.5 / expert 9.0 are the owner's "try" values pending a feel round
# at the new speeds. Value tweaks remain edits to THIS table only, and
# the exact tuple pin in tests/test_setup_logic.py is the visible
# reviewable diff for those tweaks. A tuple-of-tuples (insertion-ordered,
# py3.6-safe — NEVER a dict for ordering) because insertion order drives
# the GUI combo order. SINGLE source for the setup-tab combo (5.1-04),
# the HUD speed note (5.1-03/05), and speed_tier_for() tier-name
# resolution. The schema key 'speed' STAYS numeric (DEFAULTS['speed'] =
# 6.0 = 'normal'): backcompat is free (every setup file ever written
# already carries it) and no SCHEMA_VERSION bump is needed.
SPEED_TIERS = (
    ('relaxed', 3.0),
    ('normal', 6.0),
    ('fast', 7.5),
    ('expert', 9.0),
)

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


def merge_defaults(loaded):
    """Overlay a loaded setup dict onto DEFAULTS (plan 5.1-02, SC3).

    Absent keys fall back to the documented defaults — the backcompat
    seam for setup files written before a key existed (Phase 5.1's
    'speed'; Phase 5.2 reuses this seam for its consent key, "absent
    key = OFF"). Keys present in ``loaded`` WIN over the defaults;
    unknown EXTRA keys in ``loaded`` pass through untouched (unknown
    keys are tolerated everywhere today).

    NEVER mutates ``loaded`` or module-level DEFAULTS — the returned
    dict is a fresh copy. Applied by CALLERS after ``load_setup``;
    ``load_setup`` itself keeps its no-merge contract (it returns the
    raw dict and lets the caller decide), pinned by
    test_load_does_not_full_validate.
    """
    merged = dict(DEFAULTS)
    merged.update(loaded)
    return merged


def speed_tier_for(speed):
    """Resolve a speed (A/s) to its tier name, else 'custom' (plan 5.1-02).

    EXACT float match against SPEED_TIERS values only — deliberately NO
    nearest-match guessing: a hand-tuned 3.1 is honestly 'custom', not
    a near-'normal'. Feeds the HUD speed note (5.1-03/05). Deliberately
    NOT used to tighten validate(): any number > 0 stays legal in the
    schema (accept-as-is); the tier combo is the UI constraint, not the
    schema.
    """
    for name, aps in SPEED_TIERS:
        if speed == aps:
            return name
    return 'custom'


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
      generic_stack_consent  present but not a bool (missing key
                        PASSES — absent = OFF backcompat; an EXPLICIT
                        non-bool like 'yes' or None errors: consent is
                        a safety-relevant opt-in and must never be
                        silently enabled by a truthy non-bool)

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

    # STACK-06 (Phase 5.2, plan 5.2-01): consent is a safety-relevant
    # opt-in — a truthy non-bool from a hand-edited file must NOT
    # silently enable it. Missing key passes (absent = OFF backcompat);
    # an explicit None (or any non-bool) errors. INVERSE of the
    # _is_number bool trap: here the value must BE a bool.
    consent = setup.get('generic_stack_consent', False)
    if not isinstance(consent, bool):
        errors.append('generic_stack_consent %r must be a boolean'
                      % (consent,))

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
