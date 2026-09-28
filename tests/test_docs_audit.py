"""DOCS-04 leg A wrapper tests — the doc-vs-code audit (plan 08-03).

Drives tools/check_docs.py in BOTH directions:

  - PASS direction: the live repo (post-08-07 README, post-08-08 bottom
    row, post-08-06 help_text, post-08-09 wiring) must pass every check
    family, and run_all() must report zero failures. The final
    integration test is the leg the default gate suite rides via gate-3
    unittest discovery (tests/run_gates.py needs no edit).
  - FAIL direction: tamper fixtures — small in-test string corpora built
    by mutating the real README / code-source texts — must be REJECTED,
    proving each check bites (tamper-proof by construction). The real
    repo is never modified: fixtures are injected into the check
    functions' text/sources parameters.

python3.6, stdlib unittest, %-formatting, sys.path self-insert for the
tools/ directory (no tools/__init__.py — plugin-path safety gate).
Discovery: python3.6 -m unittest tests.test_docs_audit -v
"""
import os
import sys
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, 'tools'))

import check_docs  # noqa: E402  (RED: module exists only from GREEN on)


def _read(rel_path):
    """UTF-8 text of a repo file (read-only fixture source)."""
    with open(os.path.join(check_docs.REPO_ROOT, rel_path),
              encoding='utf-8') as fh:
        return fh.read()


class TestVibeBlock(unittest.TestCase):
    """Check 1: README lines 1-4 are the approved vibe block byte-exact."""

    def test_live_readme_vibe_block_passes(self):
        ok, msg = check_docs.check_vibe(_read('README.md'))
        self.assertTrue(ok, msg)

    def test_one_character_tamper_fails(self):
        lines = _read('README.md').split('\n')
        lines[1] = lines[1] + 'x'  # one character changed inside the block
        ok, _msg = check_docs.check_vibe('\n'.join(lines))
        self.assertFalse(ok, 'a one-character vibe-block drift must fail')


class TestPlaceholders(unittest.TestCase):
    """Check 2: zero 'TBD' in README; zero 'sECDpent' in README+spec."""

    def test_live_docs_pass(self):
        ok, msg = check_docs.check_placeholders(_read('README.md'),
                                                _read('spec.md'))
        self.assertTrue(ok, msg)

    def test_tbd_injection_fails(self):
        ok, _msg = check_docs.check_placeholders(
            _read('README.md') + '\nTBD\n', _read('spec.md'))
        self.assertFalse(ok)

    def test_secdpent_injection_in_readme_fails(self):
        ok, _msg = check_docs.check_placeholders(
            _read('README.md') + '\nsECDpent\n', _read('spec.md'))
        self.assertFalse(ok)

    def test_secdpent_injection_in_spec_fails(self):
        ok, _msg = check_docs.check_placeholders(
            _read('README.md'), _read('spec.md') + '\nsECDpent\n')
        self.assertFalse(ok)


class TestControlLiterals(unittest.TestCase):
    """Check 3: quoted UI control names exist in their named code files."""

    @classmethod
    def setUpClass(cls):
        cls.sources = dict((rel, _read(rel))
                           for rel in check_docs.CONTROL_FILES)

    def test_live_sources_pass(self):
        ok, msg = check_docs.check_controls(self.sources)
        self.assertTrue(ok, msg)

    def test_renamed_get_spectra_fails(self):
        fixture = dict(self.sources)
        mangled = fixture['serpentrum/gui_game.py'].replace(
            "'Get Spectra'", "'Grab Spectra'")
        self.assertNotEqual(mangled, fixture['serpentrum/gui_game.py'])
        fixture['serpentrum/gui_game.py'] = mangled
        ok, _msg = check_docs.check_controls(fixture)
        self.assertFalse(ok)

    def test_dropped_box_head_literal_fails(self):
        fixture = dict(self.sources)
        mangled = fixture['serpentrum/gui_setup.py'].replace(
            'Box + head materialized', 'Box made')
        self.assertNotEqual(mangled, fixture['serpentrum/gui_setup.py'])
        fixture['serpentrum/gui_setup.py'] = mangled
        ok, _msg = check_docs.check_controls(fixture)
        self.assertFalse(ok)


class TestNumericClaims(unittest.TestCase):
    """Check 4: README numbers equal the imported/loaded code+data truth."""

    @classmethod
    def setUpClass(cls):
        cls.context = check_docs.collect_numeric_context(
            check_docs.REPO_ROOT)
        cls.readme = _read('README.md')

    def test_live_readme_passes(self):
        ok, msg = check_docs.check_numeric(self.readme, self.context)
        self.assertTrue(ok, msg)

    def test_tampered_stacking_distance_fails(self):
        fixture = self.readme.replace('3.60 A centroid-centroid',
                                      '3.4 A centroid-centroid')
        self.assertNotEqual(fixture, self.readme)
        ok, _msg = check_docs.check_numeric(fixture, self.context)
        self.assertFalse(ok)

    def test_tampered_speed_tier_fails(self):
        fixture = self.readme.replace('6.0 (default)', '5.0 (default)')
        self.assertNotEqual(fixture, self.readme)
        ok, _msg = check_docs.check_numeric(fixture, self.context)
        self.assertFalse(ok)


class TestInstallRecipe(unittest.TestCase):
    """Check 5: plugin-directory install route pinned; the single-file
    'Install New Plugin' route banned."""

    @classmethod
    def setUpClass(cls):
        cls.readme = _read('README.md')

    def test_live_readme_passes(self):
        ok, msg = check_docs.check_install(self.readme)
        self.assertTrue(ok, msg)

    def test_install_new_plugin_route_fails(self):
        ok, _msg = check_docs.check_install(
            self.readme + '\nInstall New Plugin\n')
        self.assertFalse(ok)

    def test_missing_restart_step_fails(self):
        fixture = self.readme.replace('restart PyMOL', 'relaunch PyMOL')
        self.assertNotEqual(fixture, self.readme)
        ok, _msg = check_docs.check_install(fixture)
        self.assertFalse(ok)


class TestPathRefs(unittest.TestCase):
    """Check 6: every back-ticked path token in README exists on disk."""

    @classmethod
    def setUpClass(cls):
        cls.readme = _read('README.md')

    def _exists(self, rel_path):
        return os.path.exists(os.path.join(REPO_ROOT, rel_path))

    def test_live_readme_passes(self):
        ok, msg = check_docs.check_paths(self.readme, self._exists)
        self.assertTrue(ok, msg)

    def test_missing_backticked_path_fails(self):
        ok, _msg = check_docs.check_paths(
            self.readme + '\n`docs/nope.md`\n', self._exists)
        self.assertFalse(ok)


class TestClaimBans(unittest.TestCase):
    """Check 7: banned claims (removed control, retracted feature names,
    the affirmative-animation claim) can never reappear in README."""

    @classmethod
    def setUpClass(cls):
        cls.readme = _read('README.md')

    def test_live_readme_passes(self):
        ok, msg = check_docs.check_claim_bans(self.readme)
        self.assertTrue(ok, msg)

    def test_p_pause_claim_fails(self):
        ok, _msg = check_docs.check_claim_bans(
            self.readme + '\nP = pause\n')
        self.assertFalse(ok)

    def test_removed_control_name_fails(self):
        ok, _msg = check_docs.check_claim_bans(
            self.readme + '\nApply / Show in Viewer\n')
        self.assertFalse(ok)

    def test_affirmative_animation_claim_fails(self):
        ok, _msg = check_docs.check_claim_bans(
            self.readme + '\nThe plugin plays an animation of modes.\n')
        self.assertFalse(ok)

    def test_animation_disclaimer_allowlist_passes(self):
        # The tiny, explicit window: 'animation' is allowed only when the
        # SAME sentence precedes it with 'no ' or 'static' (the README
        # static-vectors disclaimer shape).
        ok, _msg = check_docs.check_claim_bans(
            self.readme + '\nVectors are drawn as static markers; '
                          'no animation is performed.\n')
        self.assertTrue(ok)


class TestRunAllIntegration(unittest.TestCase):
    """The leg the default gate suite runs: run_all on the real repo."""

    def test_run_all_reports_zero_failures(self):
        results = check_docs.run_all(check_docs.REPO_ROOT)
        failures = [(name, msg) for name, ok, msg in results if not ok]
        self.assertEqual(failures, [])
        self.assertEqual(sorted(name for name, _ok, _msg in results),
                         ['claim-bans', 'control-literals',
                          'install-recipe', 'numeric-claims',
                          'path-refs', 'placeholders', 'vibe-block'])


if __name__ == '__main__':
    unittest.main()
