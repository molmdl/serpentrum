"""serpentrum.xtbenv — xtb success contract + binary detection (PURE).

Phase-2 pure half of SPECTRA-02 / SETUP-05 (plan 02-02). Everything in
this module is stdlib-only (no pymol / pmg_tk / PyQt5 / numpy — enforced
by tools/check_purity.py) and python3.6-compatible.

The success contract (research PITFALLS 3, fixture-proven 2026-09-06):
a run counts as successful ONLY when ALL THREE legs hold:

  1. exit code == 0
  2. stderr contains 'normal termination'
  3. every expected output file is present in the run dir

The committed repro_oh fixtures prove leg 3 is load-bearing, not
belt-and-braces: that run's stderr said 'normal termination of xtb' yet
it produced NO g98.out / vibspectrum (wrong invocation flags) — stderr
success alone is NOT success. Contract failures produce one
human-readable problem string per failed leg.

Consistency anchor: tests/run_gates.py gate 5 asserts 'xtb version' AND
'normal termination' in the Windows-xtb probe output; the STDERR_SUCCESS
literal here must never drift from that assertion. The invocation flag
is --ohess (locked 2026-09-06; NEVER '-o --hess' — Pitfall 1, which
silently skips the Hessian with exit 0 and no error).
"""

import collections
import os
import shutil

# Invocation constant (locked 2026-09-06): one word, never '-o --hess'.
XTB_OHESS = '--ohess'

# What an --ohess run must leave in the run dir for the spectra pipeline
# (g98.out: primary parser target incl. mode vectors; vibspectrum:
# Turbomole-format freq/intensity fallback).
EXPECTED_FILES = ('g98.out', 'vibspectrum')

# stderr contract literals (must stay consistent with gate 5's
# 'normal termination' assertion in tests/run_gates.py).
STDERR_SUCCESS = 'normal termination'
STDERR_FAILURE = 'abnormal termination'

# ok: bool — whether ALL contract legs held.
# problems: list of human-readable strings, one per failed leg.
RunVerdict = collections.namedtuple('RunVerdict', 'ok problems')


def evaluate_run(exit_code, stderr_text, expected_files, present_files):
    """Evaluate the 3-leg xtb success contract for one finished run.

    ok iff exit_code == 0 AND STDERR_SUCCESS in stderr_text AND
    set(expected_files) <= set(present_files) — with one refinement the
    fixture bytes force: STDERR_FAILURE is tested BEFORE STDERR_SUCCESS,
    because 'abnormal termination' contains 'normal termination' as a
    substring ("ab*normal termination*") and would otherwise masquerade
    as success. expected_files is a
    sequence (usually EXPECTED_FILES, or a subset e.g. ('vibspectrum',)
    when vectors are not needed); present_files is what actually exists
    in the run dir.

    Returns a RunVerdict whose problems list carries exactly one
    human-readable entry per failed leg:

      exit leg  -> 'exit code 128 != 0'          (actual rc rendered)
      stderr leg-> "stderr reports 'abnormal termination'" when
                   STDERR_FAILURE is present, else
                   "stderr lacks 'normal termination' (got: '<first 60
                   chars, whitespace-collapsed>')"
      files leg -> 'missing expected output file(s): g98.out, vibspectrum'
                   (sorted, comma-space joined)

    Fixture-backed cases (committed .err bytes, .planning/research/
    xtb-spike-fixtures/):
      'normal termination of xtb\\r\\n', rc=0, both files  -> ok
      'abnormal termination of xtb\\r\\n', rc=128 (synthetic; fixtures
        do not record rc — PITFALLS 3), no files -> three problems
      'normal termination of xtb\\r\\n', rc=0, NO files -> exactly one
        files problem (the repro_oh story: stderr success alone is
        NOT success)
    """
    problems = []

    # Leg 1: exit code.
    if exit_code != 0:
        problems.append('exit code %s != 0' % (exit_code,))

    # Leg 2: stderr termination line (CRLF-tolerant substring check).
    # NOTE: STDERR_FAILURE is checked FIRST — 'abnormal termination'
    # contains the substring 'normal termination' ("ab*normal
    # termination*"), so a success-first check would misclassify a bad
    # run as success (proven by the committed bad.err fixture bytes).
    if STDERR_FAILURE in stderr_text:
        problems.append("stderr reports '%s'" % (STDERR_FAILURE,))
    elif STDERR_SUCCESS in stderr_text:
        pass
    else:
        collapsed = ' '.join(stderr_text.split())
        problems.append("stderr lacks '%s' (got: '%s')"
                        % (STDERR_SUCCESS, collapsed[:60]))

    # Leg 3: expected output files present (extra present files are fine).
    missing = sorted(set(expected_files) - set(present_files))
    if missing:
        problems.append('missing expected output file(s): %s'
                        % ', '.join(missing))

    return RunVerdict(ok=not problems, problems=problems)


def validate_binary_path(path):
    """Validate a user-configured xtb binary path.

    Returns a list of problem strings (empty list = valid). Problems
    accumulate where meaningfully checkable:

      (a) empty / None / non-string -> 'xtb path is empty'
      (b) missing on disk           -> "'<path>' does not exist"
      (c) exists but is a directory -> "'<path>' is not a file"
      (d) contains ' or "           -> "path contains quote character(s):
                                       '<path>'"

    Quote characters are rejected outright: they would break the
    list-argv safety contract downstream (see build_argv).
    """
    problems = []
    if not isinstance(path, str) or not path:
        problems.append('xtb path is empty')
        return problems
    if not os.path.exists(path):
        problems.append("'%s' does not exist" % (path,))
    elif not os.path.isfile(path):
        problems.append("'%s' is not a file" % (path,))
    if '"' in path or "'" in path:
        problems.append("path contains quote character(s): '%s'" % (path,))
    return problems


def detect_binary(configured_path=None, which_fn=shutil.which):
    """Resolve the xtb executable path (probe order: research PITFALLS 3
    / AGENTS.md rule):

      1. configured_path (if given): validate_binary_path; a VALID
         configured path wins immediately; an invalid one falls through
         to auto-detection.
      2. which_fn('xtb.exe') — Windows conda env first (the plugin runs
         inside Windows PyMOL).
      3. which_fn('xtb')     — Linux fallback.
      4. None when nothing resolves.

    which_fn is dependency-injected (default shutil.which) so tests run
    with NO xtb installed and NO sys.modules stubs — just pass a fake
    function.
    """
    if configured_path:
        problems = validate_binary_path(configured_path)
        if not problems:
            return configured_path
    exe = which_fn('xtb.exe')
    if exe:
        return exe
    exe = which_fn('xtb')
    if exe:
        return exe
    return None
