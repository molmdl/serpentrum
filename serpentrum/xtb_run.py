"""The xtb runner's PURE decision half (06-RESEARCH-runner Q2): every
rule the Qt controller (serpentrum/xtb_runner.py, plan 06-05) consumes
so the GUI shell stays thin and NEVER re-implements a decision already
here or in serpentrum/xtbenv.py.

Contents (all python3.6, stdlib + ``from . import xyzio`` only — PURE
purity class, auto-covered by tools/check_purity.py, WSL-unittestable
with zero stubs per the 02-02 xtbenv DI precedent):

- Run state machine (Q4): ``can_start`` is THE no-double-run guard (the
  controller calls it before every ``start()``); ``TERMINAL_STATES`` is
  the bioCHEMeleon terminal set — pending flags clear on EVERY terminal
  branch (done/failed/cancelled).
- Cancel -> status mapping (Q4): cancel = ``proc.kill()`` ->
  ``finished(exitStatus=CrashExit)`` -> the killed run ALREADY fails the
  3-leg contract via xtbenv.evaluate_run (exit != 0, files missing);
  ``resolve_status`` reports 'cancelled' from the runner's own tracked
  flag — cancel WINS over the verdict, because a killed run's partially
  captured stderr may still contain a lingering 'normal termination'
  and must never read as success.
- OMP env-knob merge (Q6): ONLY the three help-verified env knobs
  (xtb --help capture tmp/xtb_test/xtb_help.txt:229-231:
  OMP_NUM_THREADS / MKL_NUM_THREADS / OMP_STACKSIZE). No invented knobs.
  WSL-set env does NOT reliably cross into Windows — env injection is
  the QProcess path's job (06-05); this module only merges dicts.
  CALIBRATED default (SC5, 06-CALIBRATION.md 2026-09-26, applied by plan
  06-11): DEFAULT_RUN_KNOBS stays {} (no default env overrides;
  OMP_STACKSIZE dispositioned not needed at the ~104-atom scale) and the
  measured thread cap ships argv-side as DEFAULT_THREAD_ARG ('-P 4').
- Handoff seam (EQ-xyz-1): ``build_run_input`` assembles the final
  snake xyz at COMPLETION from engine/session atoms — head_atoms FIRST,
  then each segment's atoms in engine order (05-RESEARCH:151: do NOT
  re-read PyMOL; the viewer is not a coordinate source).
- Phase-7 handoff record (EQ-artifact-1): ``SPECTRA_RUN_KEYS`` +
  ``new_spectra_run`` freeze the ``_serpentrum.spectra_run`` record
  shape as DATA before any GUI code exists. ``xtbopt_path`` is carried
  for Phase 7's optimized-frame overlay decision (06-RESEARCH-guard
  Q5c). Phase 7 consumers parse from these paths (g98.out first,
  vibspectrum fallback — spectra.py:478-506 contract) and must never
  reshape the record.

Status strings double as state-machine states: 'idle' (or None),
'running', 'ok', 'failed', 'cancelled'.
"""

from . import xyzio

# ---------------------------------------------------------------------------
# Run state machine (Q4)
# ---------------------------------------------------------------------------

IDLE = 'idle'
RUNNING = 'running'
DONE = 'ok'
FAILED = 'failed'
CANCELLED = 'cancelled'

# The terminal set: bioCHEMeleon discipline clears pending flags on
# EVERY terminal branch (done / failed / cancelled — and the GUI error
# path routes into one of these).
TERMINAL_STATES = frozenset((DONE, FAILED, CANCELLED))

# EQ-omp-1 + SC5 outcome (06-CALIBRATION.md, plan 06-07; applied by plan
# 06-11 — supersedes the 06-02 'uncapped until calibration' placeholder):
# NO default env knobs. The measured thread cap lands ARGV-side as
# DEFAULT_THREAD_ARG below (a -P argv flag is not an env knob; build_env's
# verified set is the three OMP_* keys only), and OMP_STACKSIZE is
# dispositioned NOT NEEDED at the ~104-atom scale (no uncapped run
# crashed anywhere in the calibration sweep). {} = 'no env overrides by
# default' is now the FINAL calibration-derived value.
DEFAULT_RUN_KNOBS = {}

# SC5 outcome (06-CALIBRATION.md decision input (b); applied by plan
# 06-11): default argv-level thread cap '-P 4'. Measured on the
# calibration machine (4 cores / 8 hardware threads, 2026-09-26): the cap
# costs ~18% user-perceived wall (107.6 s vs 91.4 s at 104 atoms) while
# leaving 4 hardware threads for PyMOL rendering — directly addressing
# the uncapped-xtb UI-jank pitfall (PITFALLS.md:333,348). Consumed by the
# CONTROLLER's extra_args default (XtbRunController.start, plan 06-05);
# an explicit caller-supplied extra_args still overrides it.
DEFAULT_THREAD_ARG = ('-P', '4')

# xtb --help env knobs, VERIFIED verbatim from the help capture
# (tmp/xtb_test/xtb_help.txt:229-231: MKL_NUM_THREADS, OMP_NUM_THREADS,
# OMP_STACKSIZE). These three are the ONLY verified env knobs — the
# no-invented-knobs rule (06-RESEARCH pitfall 12). OMP_STACKSIZE
# necessity for the ~100-atom hessian is [TRAIN] LOW (PITFALLS:431).
KNOWN_ENV_KNOBS = ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OMP_STACKSIZE')

# EQ-artifact-1: the frozen _serpentrum.spectra_run record key set —
# written by the controller's terminal branch (plan 06-05), consumed by
# Phase 7's spectra presenter without reshaping.
SPECTRA_RUN_KEYS = ('snake_id', 'status', 'problems', 'input_path',
                    'g98_path', 'vibspectrum_path', 'xtbopt_path',
                    'log_path')


def can_start(status):
    """True iff a new run may start from the given run status.

    This IS the no-double-run guard; the controller calls it before
    EVERY start(). Admitted: None / 'idle' (nothing ever ran) and every
    terminal state (a finished run may be replaced). Refused: 'running'
    (a run is in flight) and any unknown state (fail closed).
    """
    return status is None or status == IDLE or status in TERMINAL_STATES


def resolve_status(cancel_requested, verdict_ok):
    """Map a finished run onto its record status string.

    cancel_requested wins UNCONDITIONALLY: a killed run (Q4:
    proc.kill() -> CrashExit -> evaluate_run already fails the exit and
    files legs) may carry a lingering 'normal termination' in partially
    captured stderr — it must NEVER be reported 'ok'. Otherwise map the
    3-leg contract verdict (xtbenv.evaluate_run().ok) 1:1 onto
    'ok' / 'failed'.
    """
    if cancel_requested:
        return CANCELLED
    return DONE if verdict_ok else FAILED


def build_env(base_env, knobs):
    """Merge <knobs> into a COPY of <base_env> and return the copy.

    <base_env> None -> {}; <knobs> None or empty -> plain copy of the
    base. The input dict is NEVER mutated. Each knob key must be in
    KNOWN_ENV_KNOBS (the help-verified set — anything else raises
    ValueError), each value must be non-None and non-empty after
    stringification, and is stored as ``str(value)`` (env vars are
    strings).
    """
    copy = dict(base_env or {})
    if not knobs:
        return copy
    for key, value in knobs.items():
        if key not in KNOWN_ENV_KNOBS:
            raise ValueError(
                "unknown xtb env knob '%s' (verified set: %s)"
                % (key, ', '.join(KNOWN_ENV_KNOBS)))
        if value is None or str(value) == '':
            raise ValueError(
                "empty value for xtb env knob '%s'" % (key,))
        copy[key] = str(value)
    return copy


def build_run_input(head_atoms, segment_atom_lists, snake_id):
    """Assemble the snake run-input xyz text (EQ-xyz-1).

    <head_atoms> is the GUI session's head atom list (None -> ValueError
    — the caller owns the refuse path at completion time); every atom is
    a (sym, x, y, z) 4-tuple (game_engine._translate_chain keeps them
    live truth). The final snake xyz is head atoms FIRST, then each
    segment's atoms in engine order (index 0 = oldest eaten first) —
    assembled from engine/session atoms, NEVER re-read from PyMOL
    (05-RESEARCH:151). Returns xyzio.write_xyz text with comment
    'serpentrum snake <snake_id>' (single line — the writer sanitizes a
    newline-bearing snake_id).
    """
    if head_atoms is None:
        raise ValueError('head atoms unavailable - cannot build the run '
                         'input')
    elements = []
    coords = []
    for sym, x, y, z in head_atoms:
        elements.append(sym)
        coords.append((x, y, z))
    for atoms in segment_atom_lists:
        for sym, x, y, z in atoms:
            elements.append(sym)
            coords.append((x, y, z))
    return xyzio.write_xyz(elements, coords,
                           comment='serpentrum snake %s' % (snake_id,))


def new_spectra_run(snake_id):
    """Return the initial frozen-shape spectra_run record for a new run.

    status starts 'running'; problems starts empty; all paths start None
    and are filled by the controller's terminal branch (plan 06-05),
    which writes the record onto ``_serpentrum.spectra_run``. Phase 7
    consumers read from these paths (parse g98.out first, vibspectrum
    fallback — spectra.py:478-506 contract) and must never reshape the
    record; ``xtbopt_path`` exists for Phase 7's optimized-frame overlay
    decision (06-RESEARCH-guard Q5c).
    """
    return {'snake_id': snake_id,
            'status': RUNNING,
            'problems': [],
            'input_path': None,
            'g98_path': None,
            'vibspectrum_path': None,
            'xtbopt_path': None,
            'log_path': None}
