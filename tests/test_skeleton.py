"""Entry-module purity proof: serpentrum/__init__.py imports under WSL
python3.6 with zero sys.modules stubs and zero pymol/Qt side effects
(INFRA-02). Discovery command (verified on 3.6.9 — NOTE: `-t .` FAILS on
python3.6 with a non-package start dir; do not add it):

    python3.6 -m unittest discover -s tests -p "test_*.py" -v

Convention: every future test file in tests/ MUST repeat the sys.path
self-insert below (bioCHEMeleon pattern). tests/ deliberately has NO
__init__.py — the dev plugin path IS the repo root, and findPlugins would
treat a package dir here as a second plugin.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import serpentrum  # noqa: E402


class TestEntryModule(unittest.TestCase):
    def test_import_zero_stubs(self):
        # The import above IS the test: module level pulled in no pymol/Qt.
        self.assertNotIn('pymol', sys.modules)
        self.assertNotIn('pymol.Qt', sys.modules)
        self.assertNotIn('PyQt5.QtWidgets', sys.modules)
        self.assertNotIn('pmg_tk', sys.modules)

    def test_entry_api_exists(self):
        for name in ('_anchor', '__init_plugin__', 'run_plugin_gui'):
            self.assertTrue(callable(getattr(serpentrum, name, None)),
                            'missing entry callable: %s' % name)

    def test_anchor_deferred(self):
        # _anchor() needs pmg_tk (PyMOL runtime only); importing the module
        # must not have executed it, and nothing may have created the anchor.
        self.assertNotIn('pmg_tk.startup', sys.modules)
        self.assertIsNone(serpentrum.__dict__.get('_serpentrum'))


if __name__ == '__main__':
    unittest.main()
