"""Self-test for tools/check_purity.py — the fixtures ARE the contract.

Each case builds a minimal serpentrum/-shaped tree under tempfile.mkdtemp()
and asserts exactly which violations the checker must report (or that it
must stay silent). Cleanup is shutil.rmtree via addCleanup — never shell
`rm` (opencode.json denies it). Scoped discovery command (verified on
3.6.9 — `-t .` would FAIL here because tests/ is deliberately not a
package):

    python3.6 -m unittest discover -s tests -p "test_purity_gates.py" -v

AST (not grep) is load-bearing: case 2 proves docstrings mentioning banned
import text are NOT false positives; cases 3 vs 4 prove module-level and
lazy function-body imports are distinguished.
"""
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, 'tools'))

import check_purity  # noqa: E402


class PurityFixtureTest(unittest.TestCase):
    """Cases 1-9: checker behaviour against known-bad / known-clean trees."""

    def make_tree(self, files):
        """Write {posix_relpath: content} under a fresh tempdir and return
        the tempdir root (mirrors the repo layout: serpentrum/ package)."""
        root = tempfile.mkdtemp(prefix='purity_fixture_')
        self.addCleanup(shutil.rmtree, root, True)
        for rel in sorted(files):
            dest = os.path.join(root, *rel.split('/'))
            parent = os.path.dirname(dest)
            if not os.path.isdir(parent):
                os.makedirs(parent)
            with open(dest, 'w') as fh:
                fh.write(files[rel])
        return root

    # -- case 1: pure module, numpy inside a function body --------------
    def test_pure_function_body_numpy_flagged(self):
        root = self.make_tree({
            'serpentrum/other.py': (
                '"""Pure module."""\n'
                '\n'
                '\n'
                'def helper():\n'
                '    import numpy\n'
                '    return numpy.zeros(3)\n'
            ),
        })
        violations = check_purity.check_tree(root)
        self.assertEqual(len(violations), 1, violations)
        rel, lineno, msg = violations[0]
        self.assertEqual(rel, 'serpentrum/other.py')
        self.assertEqual(lineno, 5)  # the `import numpy` line
        self.assertIn('numpy', msg)

    # -- case 2: docstring mentioning banned text must NOT false-positive
    def test_docstring_mention_is_clean(self):
        root = self.make_tree({
            'serpentrum/other.py': (
                '"""We never do `from PyQt5 import QtWidgets` here,\n'
                'nor `import numpy` — documented by policy only.\n'
                '"""\n'
                '\n'
                '\n'
                'def helper():\n'
                '    return None\n'
            ),
        })
        self.assertEqual(check_purity.check_tree(root), [])

    # -- case 3: ENTRY, pymol at module level ---------------------------
    def test_entry_module_level_pymol_flagged(self):
        root = self.make_tree({
            'serpentrum/__init__.py': (
                '"""Entry."""\n'
                'from pymol import cmd\n'
            ),
        })
        violations = check_purity.check_tree(root)
        self.assertEqual(len(violations), 1, violations)
        rel, lineno, msg = violations[0]
        self.assertEqual(rel, 'serpentrum/__init__.py')
        self.assertEqual(lineno, 2)
        self.assertIn('module level', msg)
        self.assertIn('pymol', msg)

    # -- case 4: ENTRY, lazy pymol/pmg_tk inside function bodies --------
    def test_entry_lazy_imports_clean(self):
        root = self.make_tree({
            'serpentrum/__init__.py': (
                '"""Entry."""\n'
                '\n'
                '\n'
                'def __init_plugin__(app=None):\n'
                '    from pymol.plugins import addmenuitemqt\n'
                '    addmenuitemqt("serpentrum", run)\n'
                '\n'
                '\n'
                'def _anchor():\n'
                '    import pmg_tk.startup\n'
                '    return pmg_tk.startup\n'
            ),
        })
        self.assertEqual(check_purity.check_tree(root), [])

    # -- case 5: GUI allowlist, pymol.Qt at module level ----------------
    def test_gui_pymol_dot_qt_module_level_clean(self):
        root = self.make_tree({
            'serpentrum/__init__.py': '"""Entry."""\n',
            'serpentrum/gui.py': (
                '"""GUI module."""\n'
                'from pymol.Qt import QtWidgets\n'
            ),
        })
        self.assertEqual(check_purity.check_tree(root), [])

    # -- case 6: GUI with bare pymol import (any level) -----------------
    def test_gui_bare_pymol_flagged_at_any_level(self):
        module_level = (
            '"""GUI module."""\n'
            'from pymol import cmd\n'
        )
        violations = check_purity.check_tree(self.make_tree({
            'serpentrum/gui.py': module_level,
        }))
        self.assertEqual(len(violations), 1, violations)
        self.assertEqual(violations[0][0], 'serpentrum/gui.py')
        self.assertIn('pymol', violations[0][2])

        in_body = (
            '"""GUI module."""\n'
            '\n'
            '\n'
            'def refresh():\n'
            '    import pmg_tk.startup\n'
            '    return pmg_tk.startup\n'
        )
        violations = check_purity.check_tree(self.make_tree({
            'serpentrum/gui.py': in_body,
        }))
        self.assertEqual(len(violations), 1, violations)
        self.assertEqual(violations[0][1], 5)  # the `import pmg_tk` line
        self.assertIn('pmg_tk', violations[0][2])

    # -- case 7: PyQt5 banned in ANY module class ------------------------
    def test_pyqt5_banned_everywhere(self):
        root = self.make_tree({
            'serpentrum/__init__.py': (
                '"""Entry."""\n'
                'from PyQt5 import QtWidgets\n'
            ),
            'serpentrum/other.py': (
                '"""Pure."""\n'
                'from PyQt5 import QtWidgets\n'
            ),
        })
        violations = check_purity.check_tree(root)
        flagged = {v[0] for v in violations}
        self.assertEqual(flagged, {'serpentrum/__init__.py',
                                   'serpentrum/other.py'})
        for _, _, msg in violations:
            self.assertIn('PyQt5', msg)

    # -- case 8: .exec_() call flagged with file:line --------------------
    def test_exec_call_flagged(self):
        root = self.make_tree({
            'serpentrum/other.py': (
                '"""Pure."""\n'
                '\n'
                '\n'
                'def show(dialog):\n'
                '    dialog.exec_()\n'
            ),
        })
        violations = check_purity.check_tree(root)
        self.assertEqual(len(violations), 1, violations)
        rel, lineno, msg = violations[0]
        self.assertEqual(rel, 'serpentrum/other.py')
        self.assertEqual(lineno, 5)  # the exec_() call line
        self.assertIn('exec_', msg)

    # -- case 9: relative import inside a function is intra-package -----
    def test_relative_import_clean(self):
        root = self.make_tree({
            'serpentrum/__init__.py': (
                '"""Entry."""\n'
                '\n'
                '\n'
                'def open_dialog():\n'
                '    from .gui import PluginDialog\n'
                '    return PluginDialog\n'
            ),
        })
        self.assertEqual(check_purity.check_tree(root), [])


class RealRepoCleanTest(unittest.TestCase):
    """Case 10: the actual repo must pass the checker (validates 01-01
    code; 01-02's gui.py simply does not exist on branches without it)."""

    def test_real_repo_clean(self):
        self.assertEqual(check_purity.check_tree(REPO_ROOT), [])


if __name__ == '__main__':
    unittest.main()
