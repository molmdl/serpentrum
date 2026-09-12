#!/usr/bin/env python3.6
"""AST-based purity/hygiene checker for the serpentrum plugin package.

INFRA-02 gate tool. stdlib-only (ast, os, sys), py3.6-compatible, both
importable (``check_tree``) and runnable as a CLI::

    python3.6 tools/check_purity.py [root]      # default root: repo root

Why AST and not grep: grep cannot distinguish module-level imports from
lazy function-body imports, and it false-positives on docstrings/comments
(bioCHEMeleon shipped exactly that bug). The AST sees neither.

Module classification (posix rel paths from the repo root):

===========================  ======  =============================================
path                         class   rule summary
===========================  ======  =============================================
``serpentrum/__init__.py``   ENTRY   pymol/pmg_tk allowed ONLY lazily inside
                                     function/method bodies; module level is a
                                     violation. PyQt5/numpy never anywhere.
``serpentrum/gui.py``,       GUI     ONLY ``pymol.Qt`` / ``pymol.Qt.*`` import
``serpentrum/gui_setup.py``,         forms (any level); any other pymol*/pmg_tk
``serpentrum/gui_game.py``           anywhere is a violation. PyQt5/numpy never.
``serpentrum/pymol_bridge``, BRIDGE  pymol/pmg_tk allowed at any level; PyQt5/
``serpentrum/input.py``              numpy never; ``.exec_()`` never.
anything else under          PURE    pymol/pmg_tk/PyQt5/numpy never anywhere
``serpentrum/``                      (module level OR function bodies).
===========================  ======  =============================================

PURE is the default-strict class: a future pure module is automatically
covered; a new GUI or BRIDGE module must be added to GUI_MODULES or
BRIDGE_MODULES deliberately.

Additional rules:

- ``.exec_()`` calls are violations in every module class (phase 1 has no
  child dialogs; later phases add an explicit per-module allowlist).
- Banned root segments: ``pymol``, ``pmg_tk``, ``PyQt5``, ``numpy`` (the
  root is the first segment of an ``ImportFrom.module`` or of each
  ``Import`` alias name). Relative imports — ``ImportFrom`` with
  ``module=None`` or ``level > 0`` — are intra-package and always exempt.
- PyQt5 and numpy are banned everywhere: no allowance ever grants them
  (the GUI allowance grants ``pymol.Qt`` only).
- Docstrings/comments are AST-invisible, so policy text mentioning
  ``from PyQt5 import`` is NOT a violation.

Violations are ``(rel_path, lineno, message)`` tuples; ``main()`` prints
``rel:line: message`` and exits 1 on any violation, 0 when clean. Only
files under ``<root>/serpentrum/`` are checked — dev-side tests/, tools/
and smoke/ are not plugin modules.
"""
import ast
import os
import sys

# Explicit GUI allowlist — extend consciously in later phases: a new GUI
# module must be added here deliberately. Everything else defaults PURE.
# gui_game.py = Game tab HUD (Phase 4, plan 04-05): pymol.Qt only —
# 04-RESEARCH-hud.md Q5 (edit mirrors gui_setup.py's entry). Entries for
# not-yet-created files are INERT: check_tree walks existing files only,
# so RealRepoCleanTest must stay green before AND after the file lands.
GUI_MODULES = {'serpentrum/gui.py', 'serpentrum/gui_setup.py',
               'serpentrum/gui_game.py'}

# Explicit cmd-bridge allowlist — the ONLY modules (besides ENTRY-lazy)
# that may import pymol.cmd. Allows pymol/pmg_tk at module level AND in
# bodies; bans PyQt5/numpy everywhere (Qt stays in GUI modules; numpy
# never needed in the bridge — pure modules do the math). .exec_() stays
# banned (the bridge builds no dialogs).
# input.py = KeySteerWizard keyboard steering (Phase 4, plan 04-04):
# pymol.wizard + pymol.cmd at module level, NEVER Qt —
# 04-RESEARCH-input.md "Module placement under purity rules" table.
BRIDGE_MODULES = {'serpentrum/pymol_bridge.py', 'serpentrum/input.py'}

ENTRY_MODULE = 'serpentrum/__init__.py'

# Root segments banned outright for every module class.
BANNED_ROOTS = ('pymol', 'pmg_tk', 'PyQt5', 'numpy')

# The only pymol-family import forms a GUI module may use, at any level.
QT_ALLOWED_PREFIX = 'pymol.Qt'


def classify(rel_path):
    """Return 'ENTRY', 'GUI', 'BRIDGE' or 'PURE' for a posix rel path."""
    if rel_path == ENTRY_MODULE:
        return 'ENTRY'
    if rel_path in GUI_MODULES:
        return 'GUI'
    if rel_path in BRIDGE_MODULES:
        return 'BRIDGE'
    return 'PURE'


def _is_relative(node):
    """True for intra-package relative imports (always exempt)."""
    return isinstance(node, ast.ImportFrom) and (node.level > 0 or
                                                 node.module is None)


def _is_qt_form(node):
    """True iff the node imports pymol.Qt or pymol.Qt.* (GUI allowance)."""
    if isinstance(node, ast.ImportFrom):
        return (node.module == QT_ALLOWED_PREFIX or
                (node.module or '').startswith(QT_ALLOWED_PREFIX + '.'))
    if isinstance(node, ast.Import):
        return any(alias.name == QT_ALLOWED_PREFIX or
                   alias.name.startswith(QT_ALLOWED_PREFIX + '.')
                   for alias in node.names)
    return False


def _imported_roots(node):
    """Set of first-segment roots imported by an Import/ImportFrom node."""
    if isinstance(node, ast.ImportFrom):
        return {node.module.split('.')[0]} if node.module else set()
    if isinstance(node, ast.Import):
        return {alias.name.split('.')[0] for alias in node.names}
    return set()


def _flag(out, rel_path, lineno, msg):
    out.append((rel_path, lineno, msg))


def _check_import_node(out, rel_path, cls, node, at_module_level):
    """Apply the class-specific import rules to one import node."""
    if _is_relative(node):
        return  # intra-package import: always exempt
    roots = _imported_roots(node)
    qt_form = _is_qt_form(node)

    if cls == 'ENTRY':
        # Lazy allowance for pymol/pmg_tk applies ONLY below module level.
        if at_module_level and roots & {'pymol', 'pmg_tk'}:
            for root in sorted(roots & {'pymol', 'pmg_tk'}):
                _flag(out, rel_path, node.lineno,
                      'entry module imports %r at module level '
                      '(lazy function-body import required)' % root)
        # PyQt5/numpy: banned anywhere, module level or bodies.
        for root in sorted(roots & {'PyQt5', 'numpy'}):
            _flag(out, rel_path, node.lineno,
                  'entry module imports %r (banned anywhere)' % root)
    elif cls == 'GUI':
        # Allowlist is pymol.Qt only — any other pymol*/pmg_tk anywhere
        # (module level or bodies) is a violation.
        if roots & {'pymol', 'pmg_tk'} and not qt_form:
            for root in sorted(roots & {'pymol', 'pmg_tk'}):
                _flag(out, rel_path, node.lineno,
                      'GUI module imports %r (allowlist is pymol.Qt only)'
                      % root)
        for root in sorted(roots & {'PyQt5', 'numpy'}):
            _flag(out, rel_path, node.lineno,
                  'GUI module imports %r (banned anywhere)' % root)
    elif cls == 'BRIDGE':
        # Allow pymol/pmg_tk at ANY level (module + bodies) — this is the
        # cmd-seam. PyQt5/numpy banned anywhere (Qt stays in GUI modules;
        # numpy never needed in the bridge — pure modules do the math).
        for root in sorted(roots & {'PyQt5', 'numpy'}):
            _flag(out, rel_path, node.lineno,
                  'bridge module imports %r (banned anywhere)' % root)
    else:  # PURE — default-strict: never anywhere, any level.
        for root in sorted(roots & set(BANNED_ROOTS)):
            _flag(out, rel_path, node.lineno,
                  'pure module imports %r (banned anywhere)' % root)


def check_module(rel_path, tree):
    """Check one parsed module; return [(rel_path, lineno, message)]."""
    out = []
    cls = classify(rel_path)

    # Module-level check: DIRECT children of the module body only — never
    # ast.walk here, or lazy imports inside functions get misflagged.
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            _check_import_node(out, rel_path, cls, node,
                               at_module_level=True)

    # Anywhere check: walk every node, but for ENTRY the pymol/pmg_tk
    # lazy allowance means only PyQt5/numpy are re-flagged below module
    # level (module-level pymol/pmg_tk was already flagged above).
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if node in tree.body:  # already judged at module level
                continue
            _check_import_node(out, rel_path, cls, node,
                               at_module_level=False)
        # Modeless gate: .exec_() calls banned in every module class
        # (INFRA-05 — use .show(); child dialogs get an explicit
        # per-module allowlist in later phases).
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute) and func.attr == 'exec_':
                _flag(out, rel_path, node.lineno,
                      '.exec_() call (modeless violation — use .show())')
    return out


def check_tree(root):
    """Check every .py under <root>/serpentrum/; return sorted violations."""
    pkg_dir = os.path.join(root, 'serpentrum')
    violations = []
    if not os.path.isdir(pkg_dir):
        return violations
    for dirpath, _dirnames, filenames in os.walk(pkg_dir):
        for filename in sorted(filenames):
            if not filename.endswith('.py'):
                continue
            abs_path = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(abs_path, root).replace(os.sep, '/')
            try:
                with open(abs_path, 'rb') as fh:
                    source = fh.read()
                tree = ast.parse(source, filename=abs_path)
            except SyntaxError as exc:
                violations.append((rel_path, exc.lineno or 0,
                                   'SyntaxError: %s' % exc.msg))
                continue
            violations.extend(check_module(rel_path, tree))
    return sorted(violations, key=lambda v: (v[0], v[1]))


def main(argv=None):
    """CLI: print `rel:line: message` per violation; exit 1 if any."""
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv:
        root = argv[0]
    else:
        # Default: repo root = parent of the tools/ dir holding this file.
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    violations = check_tree(root)
    for rel_path, lineno, msg in violations:
        sys.stdout.write('%s:%s: %s\n' % (rel_path, lineno, msg))
    if violations:
        sys.stderr.write('check_purity: %d violation(s)\n' % len(violations))
        return 1
    sys.stdout.write('check_purity: clean (%s)\n' % root)
    return 0


if __name__ == '__main__':
    sys.exit(main())
