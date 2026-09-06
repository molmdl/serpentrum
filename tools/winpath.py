"""WSL -> Windows path conversion (pure string logic, stdlib-only, py3.6).

BOUNDARY — dev/harness side ONLY: these helpers exist for code running in
the WSL dev shell (gate runners like tests/run_gates.py --xtb, smoke
drivers, one-off probes). The PLUGIN RUNTIME never converts paths at all:
it is Windows PyMOL talking to a Windows xtb.exe with a Windows cwd and
bare relative filenames, so no conversion is ever needed in serpentrum/
package code. [SRC: .planning/research/PITFALLS.md:333, STACK.md:83]

Two output forms:
  to_windows_path('/mnt/c/foo/bar')      -> 'C:/foo/bar'   (forward-slash
      form — safe wherever Windows tools accept forward slashes)
  to_windows_backslash('/mnt/c/foo/bar') -> 'C:\\foo\\bar' (cmd.exe-target
      form — required for cmd.exe /c targets)

Validation is strict: the input must be a WSL mount path — '/mnt/<drive>'
exactly, or '/mnt/<drive>/...' with a single-letter drive. Anything else
('/home/...', relative paths, already-Windows 'C:\\...', bare '/mnt')
raises ValueError — never silently mangle a path.
"""
import re

# '/mnt/c' | '/mnt/C' | '/mnt/c/...'  (rest may be empty for a trailing
# slash; the rest never contributes a leading slash to the output).
_MOUNT_RE = re.compile(r'^/mnt/([a-zA-Z])(?:/(?P<rest>.*))?$')


def _split_mount(path):
    """Validate a WSL mount path; return (drive, rest) or raise ValueError.

    drive is uppercase ('C'); rest is the sub-path below the mount root
    with no leading slash ('' for the mount root itself).
    """
    if not isinstance(path, str):
        raise ValueError(
            'path must be a str, got %s: %r' % (type(path).__name__, path))
    match = _MOUNT_RE.match(path)
    if match is None:
        raise ValueError(
            'not a WSL /mnt/<drive> path: %r (expected /mnt/c, '
            '/mnt/c/foo, ...)' % (path,))
    drive = match.group(1).upper()
    rest = match.group('rest') or ''
    # Collapse accidental doubled slashes; never let one into the output.
    rest = re.sub(r'/{2,}', '/', rest)
    return drive, rest


def to_windows_path(path):
    """Convert a WSL /mnt/<drive> path to its Windows forward-slash form.

    '/mnt/c/foo/bar' -> 'C:/foo/bar';  '/mnt/c' -> 'C:/'

    Raises ValueError for anything that is not a WSL mount path (see
    module docstring). Pure string logic — no filesystem access, and the
    input string is never modified.
    """
    drive, rest = _split_mount(path)
    if rest:
        return '%s:/%s' % (drive, rest)
    return '%s:/' % drive


def to_windows_backslash(path):
    """Convert a WSL /mnt/<drive> path to its Windows backslash form.

    '/mnt/c/foo/bar' -> 'C:\\foo\\bar';  '/mnt/c' -> 'C:\\'

    The form cmd.exe /c targets require. Same validation as
    to_windows_path — raises ValueError on non-WSL-mount input.
    """
    return to_windows_path(path).replace('/', '\\')
