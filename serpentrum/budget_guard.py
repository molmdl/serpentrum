"""serpentrum.budget_guard — SPECTRA-06 pre-launch atom-budget re-check
(PURE).

Plan 06-01 (Phase 6, xtb Pipeline). Pure, WSL-testable decision functions
— ``(ints in) -> [one-line warning strings out]`` — that the GUI merely
logs, in the house builder pattern (hud_logic.speed_note precedent: the
pure layer composes sentences; the GUI logs once, injecting cap values and
counts it owns).

SPECTRA-06 ("before launch, hidden molecule/atom counts re-checked against
the configured cap; exceeding it shows a warning", REQUIREMENTS.md:55) is
implemented here as WARN-AND-PROCEED, never a block. This is structurally
mandatory, not a UX choice: a default-parameter WIN snake (10 stacked +
head = 11 set_a molecules x 12-24 atoms => 130-260 atoms) routinely
exceeds ``atom_budget=100``, and the win condition freezes
``molecules_stacked`` exactly AT the cap (game_engine.py:726-731) — a
blocking guard would make the shipped win path un-runnable
(06-RESEARCH-guard.md Q2). SETUP-06's warn-and-proceed precedent
(setup_logic.py: warnings decorate, never abort) applies verbatim.

Count conventions (load-bearing):
- ``molecules_stacked`` is the engine counter and EXCLUDES the head
  (callers pass ``last_run['molecules_stacked']``); the viewer
  chain-object count INCLUDES it. The guard does the +1 internally.
- ``atoms_engine`` is the HEAD-INCLUSIVE run-input count — the true xtb
  input size. ``last_run['atoms_total']`` EXCLUDES the head
  (test_phase5_integration.py:267-273) and must NOT be passed here.
- The molecule leg is the counts line + desync check ONLY: a legal run can
  never have ``molecules_stacked > win_cap`` (win freezes AT the cap), so
  an incl-head-vs-cap comparison would always warn on wins. ONLY the atom
  budget can trigger the hessian warning. (Pinned here so nobody "fixes"
  it later — 06-RESEARCH-guard.md Q2, plan 06-01 resolved decision.)

Semantics:
- Errors are DATA, not exceptions (setup_logic.validate precedent,
  setup_logic.py:203-224): every function NEVER raises; None/non-numeric
  inputs produce an 'unavailable' line (or are skipped) instead of
  crashing. The py3.6 bool-is-int trap is respected via ``_is_count``
  (setup_logic._is_number precedent, setup_logic.py:175-179).
- Viewer-vs-run-input count mismatches are desync WARNINGS (stale scene,
  cosmetic) — the run input is engine truth, launch proceeds.
- The over-budget line reuses ``setup_logic.HESSIAN_WARNING`` VERBATIM so
  SETUP-06 and SPECTRA-06 wording never drift (drift-pinned by
  tests/test_budget_guard.py; drill-pin precedent
  tests/test_xtbenv.py:298). Do NOT call ``setup_logic.validate()`` here:
  it warns about CONFIG at edit time; this guard warns about THE RUN at
  launch time (setup_logic.py:15-16 assigns the runtime half to Phase 6).

python3.6 syntax only (%%-formatting, no f-strings/walrus); PURE module —
stdlib + ``from . import setup_logic`` (HESSIAN_WARNING only); no pymol /
pmg_tk / PyQt5 / numpy anywhere (auto-classified PURE by
tools/check_purity.py; intra-package imports are purity-exempt).
"""

from . import setup_logic


def _is_count(value):
    """True for int/float but NOT bool (py3.6 bool-is-int trap:
    ``isinstance(True, int)`` is True, but a bool count is a bug, not a
    number — setup_logic._is_number precedent)."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def launch_budget_warnings(molecules_stacked, molecules_view, atoms_engine,
                           atoms_view, atom_budget):
    """SPECTRA-06 pre-launch re-check -> list of ONE-LINE warning strings
    ([] = clean). NEVER raises; NEVER blocks — warn-and-proceed.

    Parameters (all supplied by the caller, typically plan 06-09's launch
    API — this module never reads setup or viewers itself):
      molecules_stacked  engine counter EXCLUDING the head
                         (last_run['molecules_stacked'])
      molecules_view     viewer chain-object count INCLUDING the head
                         (len(last_run['chain_objects']));
                         None = cross-check unavailable
      atoms_engine       head-inclusive run-input atom count (the true xtb
                         input size)
      atoms_view         viewer atom count; None = cross-check unavailable
      atom_budget        from setup (caller may pass the DEFAULTS
                         fallback); None = no budget resolved

    Behavior:
    - atoms_engine not numeric -> exactly one 'unavailable' line, nothing
      else.
    - Molecule desync (viewer count != molecules_stacked + 1) and atom
      desync (viewer != run input) each produce one warning line; launch
      proceeds (the run input is engine truth; a stale scene is cosmetic).
    - atom_budget numeric and atoms_engine > atom_budget -> exactly one
      line carrying setup_logic.HESSIAN_WARNING verbatim WITH the revealed
      counts (the game is over; GAME-04's count-free rule applied to play
      only).
    - Desync lines first, budget line LAST. Here-doc pinned order is
      consumed by tests/test_budget_guard.py.
    """
    if not _is_count(atoms_engine):
        return ['spectra input atom count unavailable - '
                'budget re-check skipped']

    lines = []

    # Molecule leg: counts + desync ONLY (never a cap comparison — win
    # freezes molecules_stacked AT the cap, so incl-head vs cap would
    # always warn on wins; see module docstring).
    if (_is_count(molecules_stacked) and _is_count(molecules_view)
            and molecules_view != molecules_stacked + 1):
        lines.append('molecule count mismatch: viewer chain has %s '
                     'object(s), completed run counted %d (incl. head) - '
                     'scene may be stale'
                     % (molecules_view, int(molecules_stacked) + 1))

    if _is_count(atoms_view) and atoms_view != atoms_engine:
        lines.append('viewer chain atom count %s != run input atom count '
                     '%s - scene may be stale; using the run input count'
                     % (atoms_view, atoms_engine))

    if _is_count(atom_budget) and atoms_engine > atom_budget:
        lines.append('%s (this snake: %d atoms > budget %s)'
                     % (setup_logic.HESSIAN_WARNING, int(atoms_engine),
                        atom_budget))

    return lines


def launch_counts_line(molecules_stacked, atoms_engine, atom_budget):
    """Render the launch counts line: 'spectra input: %d molecules (incl.
    head), %s atoms (budget %s)'.

    molecules_stacked excludes the head (rendered +1). Atoms render via
    the _is_count guard as 'unavailable' when not a count — NEVER raises.
    """
    if _is_count(atoms_engine):
        atoms_text = '%d' % (int(atoms_engine),)
    else:
        atoms_text = 'unavailable'
    return ('spectra input: %s molecules (incl. head), %s atoms '
            '(budget %s)'
            % ((molecules_stacked + 1) if _is_count(molecules_stacked)
               else 'unavailable', atoms_text, atom_budget))
