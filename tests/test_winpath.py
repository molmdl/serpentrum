"""WSL->Windows path conversion rules (tools/winpath.py).

Same conventions as test_skeleton.py: sys.path self-insert of the repo
root (plus tools/ to import winpath); tests/ deliberately has NO
__init__.py — the dev plugin path IS the repo root, and findPlugins would
treat a package dir here as a second plugin. Zero stubs: winpath is pure
stdlib string logic.
"""
import os
import sys
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
_TOOLS = os.path.join(_ROOT, 'tools')
if _TOOLS not in sys.path:
    sys.path.insert(0, _TOOLS)

import winpath  # noqa: E402


class TestToWindowsPath(unittest.TestCase):
    def test_mount_root(self):
        self.assertEqual(winpath.to_windows_path('/mnt/c'), 'C:/')

    def test_single_component(self):
        self.assertEqual(winpath.to_windows_path('/mnt/c/foo'), 'C:/foo')

    def test_nested_with_extension(self):
        self.assertEqual(
            winpath.to_windows_path('/mnt/c/foo/bar.txt'), 'C:/foo/bar.txt')

    def test_trailing_slash(self):
        self.assertEqual(winpath.to_windows_path('/mnt/c/'), 'C:/')

    def test_other_drive(self):
        self.assertEqual(winpath.to_windows_path('/mnt/d/data'), 'D:/data')

    def test_drive_case_insensitive(self):
        self.assertEqual(winpath.to_windows_path('/mnt/C/foo'), 'C:/foo')


class TestToWindowsBackslash(unittest.TestCase):
    def test_mount_root(self):
        self.assertEqual(winpath.to_windows_backslash('/mnt/c'), 'C:\\')

    def test_single_component(self):
        self.assertEqual(winpath.to_windows_backslash('/mnt/c/foo'), 'C:\\foo')

    def test_nested_with_extension(self):
        self.assertEqual(
            winpath.to_windows_backslash('/mnt/c/foo/bar.txt'),
            'C:\\foo\\bar.txt')

    def test_other_drive(self):
        self.assertEqual(
            winpath.to_windows_backslash('/mnt/d/data'), 'D:\\data')


class TestValidationErrors(unittest.TestCase):
    def _assert_value_error(self, path):
        for fn in (winpath.to_windows_path, winpath.to_windows_backslash):
            with self.assertRaises(ValueError):
                fn(path)

    def test_home_path_rejected(self):
        self._assert_value_error('/home/user/x')

    def test_relative_path_rejected(self):
        self._assert_value_error('relative/path')

    def test_already_windows_rejected(self):
        self._assert_value_error('C:\\already')

    def test_bare_mnt_rejected(self):
        self._assert_value_error('/mnt')

    def test_mount_slash_rejected(self):
        # '/mnt/' has no drive letter — not a mount path.
        self._assert_value_error('/mnt/')

    def test_two_letter_drive_rejected(self):
        self._assert_value_error('/mnt/cc/foo')

    def test_empty_string_rejected(self):
        self._assert_value_error('')

    def test_none_rejected(self):
        self._assert_value_error(None)


class TestNoMutation(unittest.TestCase):
    def test_input_string_unchanged(self):
        for path in ('/mnt/c', '/mnt/c/foo', '/mnt/c/foo/bar.txt'):
            before = path
            winpath.to_windows_path(path)
            winpath.to_windows_backslash(path)
            self.assertEqual(path, before)


if __name__ == '__main__':
    unittest.main()
