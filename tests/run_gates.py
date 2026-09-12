#!/usr/bin/env python3.6
"""Single gate entry point for the serpentrum plugin (INFRA-06 harness).

Usage (from anywhere; ROOT is resolved from this file's location):

    python3.6 tests/run_gates.py [--smoke] [--xtb]

Default gates (WSL-native, sub-second):

  1. Syntax + plugin-path safety — py_compile walk over serpentrum/, tools/,
     tests/, smoke/ plus safety checks for stray root-level .py files and
     forbidden __init__.py markers in dev dirs (the dev plugin path IS the
     repo root; findPlugins would autoload a top-level .py file or a
     package dir as a second plugin at GUI startup).
  2. Purity — tools/check_purity.check_tree(ROOT) (INFRA-02, AST-based).
  3. Scoped unittest — subprocess `python -m unittest discover -s tests
     -p "test_*.py" -v`. Scope-limited on purpose: unscoped discovery
     wanders into serpentrum/ and imports pymol. NOTE: `-t .` is NOT used —
     it fails on python3.6 with a non-package start dir.

Flag-gated Windows legs (--smoke, INFRA-01): headless Windows PyMOL smokes
via `cmd.exe /c C:\src\run-conda-pymol.bat -cq <script>`. Verdicts come
from printed SMOKE-OK / SMOKE-FAIL sentinels ONLY — exit codes through the
.bat are always 0 (even after a Qt C-abort) and are never trusted.

Flag-gated Windows leg (--xtb, INFRA-01): direct WSL exec of the Windows
xtb.exe — invoked by WSL-style path (the repo-root symlink xtb-6.7.1 ->
/mnt/c/xtb-6.7.1), with a /mnt/c-backed cwd and bare relative args (the
research-verified pattern [RUN 2026-09-06], as in test_wsl_winxtb.sh; NO
cmd.exe here). The verdict asserts BOTH 'xtb version' AND 'normal
termination' in the captured output. For a direct exec the child exit
code is meaningful (unlike the .bat legs) and is captured, but the gate
asserts on content anyway.

Exit code: 0 when every default gate (and every required smoke) passes,
1 otherwise. A missing required smoke is a failure; informational smokes
(any other smoke/NN_*.py) are run when present and NEVER fail the gate.
"""
import argparse
import glob
import os
import py_compile
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Directories walked by the syntax gate (missing dirs -> empty, fine).
WALK_DIRS = ('serpentrum', 'tools', 'tests', 'smoke')

# Dev dirs that must NEVER contain an __init__.py (package marker).
SAFETY_DIRS = ('tests', 'smoke', 'tools')

# Required headless smokes (a missing one fails the gate).
REQUIRED_SMOKES = ('smoke/01_skeleton_smoke.py',
                    'smoke/03_viewer_bridge_smoke.py',
                    'smoke/04_demo_e2e_smoke.py',
                    'smoke/05_loop_camera_smoke.py')

SMOKE_BAT = 'C:\\src\\run-conda-pymol.bat'
SMOKE_TIMEOUT = 90  # seconds, per research Q3

# Gate 5 (--xtb): the Windows xtb.exe, reached through the repo-root
# symlink; direct WSL exec, /mnt/c-backed cwd, bare relative args.
XTB_EXE_REL = os.path.join('xtb-6.7.1', 'bin', 'xtb.exe')
XTB_TIMEOUT = 60  # seconds, per research Q4


def _py_files(dir_name):
    """All *.py under <ROOT>/<dir_name> (recursive); [] when dir missing."""
    pattern = os.path.join(ROOT, dir_name, '**', '*.py')
    return sorted(glob.glob(pattern, recursive=True))


def gate_syntax_safety(failures):
    """Gate 1: py_compile walk + plugin-path safety (INFRA-06)."""
    failed = False
    for dir_name in WALK_DIRS:
        for path in _py_files(dir_name):
            try:
                py_compile.compile(path, doraise=True)
            except py_compile.PyCompileError as exc:
                failed = True
                failures.append('%s: %s' % (os.path.relpath(path, ROOT),
                                            str(exc).strip()))
    # Safety (a): no .py directly in the repo root.
    for path in sorted(glob.glob(os.path.join(ROOT, '*.py'))):
        failed = True
        failures.append(
            'root-level .py: %s — the dev plugin path IS the repo root; '
            'findPlugins would autoload it as a plugin at GUI startup'
            % os.path.basename(path))
    # Safety (b): no __init__.py directly inside dev dirs.
    for dir_name in SAFETY_DIRS:
        init_path = os.path.join(ROOT, dir_name, '__init__.py')
        if os.path.isfile(init_path):
            failed = True
            failures.append(
                '%s/__init__.py must not exist — a package dir in the repo '
                'root would be loaded as a second plugin by findPlugins'
                % dir_name)
    return not failed


def gate_purity(failures):
    """Gate 2: AST purity checker over serpentrum/ (INFRA-02)."""
    tools_dir = os.path.join(ROOT, 'tools')
    if tools_dir not in sys.path:
        sys.path.insert(0, tools_dir)
    import check_purity
    violations = check_purity.check_tree(ROOT)
    for rel_path, lineno, msg in violations:
        failures.append('%s:%s: %s' % (rel_path, lineno, msg))
    return not violations


def gate_unittest(failures):
    """Gate 3: unittest discovery scoped to tests/ (no -t .: fails on 3.6)."""
    proc = subprocess.run(
        [sys.executable, '-m', 'unittest', 'discover',
         '-s', 'tests', '-p', 'test_*.py', '-v'],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=ROOT)
    out = proc.stdout.decode('utf-8', errors='replace')
    sys.stdout.write(out)
    if proc.returncode != 0:
        failures.append('unittest discover exited %d' % proc.returncode)
        return False
    return True


def run_smoke(rel_path):
    """Run one headless smoke; return (passed, captured_output)."""
    cmd = SMOKE_BAT + ' -cq ' + rel_path.replace('/', '\\')
    try:
        proc = subprocess.run(
            ['cmd.exe', '/c', cmd], cwd=ROOT,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            timeout=SMOKE_TIMEOUT)
    except subprocess.TimeoutExpired:
        return False, ('TIMEOUT after %ss' % SMOKE_TIMEOUT)
    # Exit codes are always 0 through the .bat — never trusted.
    out = proc.stdout.decode('utf-8', errors='replace')
    passed = 'SMOKE-OK' in out and 'SMOKE-FAIL' not in out
    return passed, out


def gate_smoke(failures, notes):
    """Flag-gated Windows leg: required smokes must pass; informational
    smokes are reported and never fail the gate."""
    smoke_dir = os.path.join(ROOT, 'smoke')
    found = []
    if os.path.isdir(smoke_dir):
        for path in sorted(glob.glob(os.path.join(smoke_dir, '[0-9][0-9]_*.py'))):
            found.append('smoke/' + os.path.basename(path))
    ok = True
    for rel_path in REQUIRED_SMOKES:
        if rel_path not in found:
            failures.append('required smoke %s missing '
                            '(created by plan 01-04)' % rel_path)
            ok = False
            continue
        passed, out = run_smoke(rel_path)
        if passed:
            notes.append('smoke %s: PASS (sentinel SMOKE-OK)' % rel_path)
            # Echo the flushed sentinel line itself so captured gate
            # output carries the literal proof (e.g. 'SMOKE-OK SKELETON').
            for line in out.splitlines():
                if 'SMOKE-OK' in line:
                    notes.append('smoke %s: %s' % (rel_path, line.strip()))
                    break
        else:
            failures.append('smoke %s: FAIL (no flushed SMOKE-OK sentinel, '
                            'or SMOKE-FAIL present)' % rel_path)
            sys.stdout.write('--- last 40 lines of %s output ---\n'
                             % rel_path)
            sys.stdout.write('\n'.join(out.splitlines()[-40:]) + '\n')
            ok = False
    for rel_path in found:
        if rel_path in REQUIRED_SMOKES:
            continue
        passed, _out = run_smoke(rel_path)
        notes.append('informational smoke %s: %s'
                     % (rel_path, 'PASS' if passed else 'FAIL (non-blocking)'))
    return ok


def gate_xtb(failures, notes):
    """Flag-gated Windows leg: prove Windows xtb is invocable from WSL.

    The research-verified pattern (INFRA-01, [RUN 2026-09-06]): exec the
    exe DIRECTLY by WSL-style path (no cmd.exe), with a /mnt/c-backed cwd
    and bare relative args. Verdict = 'xtb version' AND 'normal
    termination' in the output; the direct-exec exit code is meaningful
    and captured, but the gate asserts on content regardless.
    """
    # (a) Conversion sanity — exercises tools/winpath from the gate. The
    # repo must live on /mnt/c for the Windows legs to work at all.
    tools_dir = os.path.join(ROOT, 'tools')
    if tools_dir not in sys.path:
        sys.path.insert(0, tools_dir)
    try:
        import winpath
    except ImportError as exc:
        failures.append('xtb gate: cannot import tools/winpath.py: %r' % exc)
        return False
    try:
        win_root = winpath.to_windows_path(ROOT)
    except ValueError as exc:
        failures.append('xtb gate: repo root is not a WSL /mnt/<drive> '
                        'path (%r) — Windows legs cannot work' % exc)
        return False
    if not win_root.startswith('C:/'):
        failures.append('xtb gate: repo root maps to %r, expected C:/... '
                        '— repo must live on /mnt/c' % win_root)
        return False
    notes.append('xtb gate: winpath sanity %s -> %s' % (ROOT, win_root))

    # (b) Resolve the exe.
    exe = os.path.join(ROOT, XTB_EXE_REL)
    if not os.path.isfile(exe):
        failures.append('xtb gate: exe missing at %s (expected repo-root '
                        'symlink xtb-6.7.1 -> /mnt/c/xtb-6.7.1)' % exe)
        return False

    # (c) Probe: direct WSL exec, /mnt/c-backed cwd, bare relative args.
    try:
        proc = subprocess.run(
            [exe, '--version'], cwd=ROOT,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            timeout=XTB_TIMEOUT)
    except subprocess.TimeoutExpired:
        failures.append('xtb gate: no output within %ss — exe or cwd '
                        'contract broken' % XTB_TIMEOUT)
        return False
    except OSError as exc:
        failures.append('xtb gate: could not exec %s: %r' % (exe, exc))
        return False

    out = proc.stdout.decode('utf-8', errors='replace')
    rc = proc.returncode
    has_version = 'xtb version' in out
    has_termination = 'normal termination' in out
    for line in out.splitlines():
        if 'xtb version' in line:
            notes.append('xtb gate: %s (rc=%d)' % (line.strip(), rc))
            break
    for line in out.splitlines():
        if 'normal termination' in line:
            # Echo the literal proof line into the captured gate output.
            notes.append('xtb gate: %s' % line.strip())
            break
    if has_version and has_termination:
        return True
    failures.append(
        'xtb gate: output contract broken (xtb version found: %s, '
        'normal termination found: %s, child rc: %s) — expected '
        "'xtb version 6.7.1pre ...' + 'normal termination of xtb'"
        % (has_version, has_termination, rc))
    sys.stdout.write('--- last 20 lines of xtb --version output ---\n')
    sys.stdout.write('\n'.join(out.splitlines()[-20:]) + '\n')
    return False


def main(argv=None):
    args = argparse.ArgumentParser(
        description='serpentrum gate runner (syntax, safety, purity, '
                    'unittest; --smoke adds headless Windows PyMOL smokes, '
                    '--xtb adds the Windows-xtb-from-WSL probe)')
    args.add_argument('--smoke', action='store_true',
                      help='also run headless Windows PyMOL smokes')
    args.add_argument('--xtb', action='store_true',
                      help='also probe Windows xtb from WSL '
                           '(direct exec, asserts xtb version + '
                           'normal termination)')
    known = args.parse_args(argv if argv is not None else sys.argv[1:])

    os.chdir(ROOT)  # subprocesses and cmd.exe inherit the repo cwd
    failures = []
    notes = []
    results = []

    results.append(('gate 1: syntax + plugin-path safety',
                    gate_syntax_safety(failures)))
    results.append(('gate 2: purity (AST)', gate_purity(failures)))
    results.append(('gate 3: unittest (scoped discover)',
                    gate_unittest(failures)))
    if known.smoke:
        results.append(('gate 4: headless smokes (required)',
                        gate_smoke(failures, notes)))
    if known.xtb:
        results.append(('gate 5: xtb probe (Windows from WSL)',
                        gate_xtb(failures, notes)))

    for note in notes:
        sys.stdout.write('note: %s\n' % note)
    sys.stdout.write('\n=== GATE SUMMARY ===\n')
    for name, passed in results:
        sys.stdout.write('%-40s %s\n' % (name, 'PASS' if passed else 'FAIL'))
    if failures:
        sys.stdout.write('\nFAILURES (%d):\n' % len(failures))
        for failure in failures:
            sys.stdout.write('  - %s\n' % failure)
        sys.stderr.write('run_gates: %d failure(s)\n' % len(failures))
        return 1
    sys.stdout.write('\nrun_gates: all gates green\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
