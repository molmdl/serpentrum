"""setup_logic contract tests: defaults, validation matrix, save/load
round-trip, seeded head randomize (plan 02-07).

Covers the pure half of SETUP-03/04/05/06 and SPECTRA-06's pre-xtb
warning. validate() produces per-key errors and the single exact N-cubed
hessian-cost warning; save/load round-trips the setup dict identically;
randomize_head is seed-deterministic via private random.Random instances
(never the global random module).

Discovery command (verified on python3.6.9 — NOTE: `-t .` FAILS on
python3.6 with a non-package start dir; do not add it):

    python3.6 -m unittest discover -s tests -p "test_setup_logic.py" -v

Convention: every test file in tests/ repeats the sys.path self-insert
below (bioCHEMeleon pattern). tests/ deliberately has NO __init__.py —
the dev plugin path IS the repo root, and findPlugins would treat a
package dir here as a second plugin.
"""
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import serpentrum.setup_logic as setup_logic  # noqa: E402
from serpentrum.setup_logic import (  # noqa: E402
    BOX_PRESETS, DEFAULTS, HESSIAN_WARNING, KNOWN_SETS, SCHEMA_VERSION,
    SetupError, load_setup, new_setup, randomize_head, save_setup, validate,
)
import serpentrum.xtbenv as xtbenv  # noqa: E402

EXPECTED_DEFAULTS = {
    'schema_version': 1,
    'demo_set': 'set_a',
    'head_molecule': 'random',
    'box_preset': 'medium',
    'xtb_path': None,
    'win_cap_molecules': 10,
    'atom_budget': 100,
    'broadening_fwhm': 16.0,
    'speed': 3.0,
}


def _mutated(**overrides):
    """Return a fresh new_setup() with the given fields overridden."""
    setup = new_setup()
    setup.update(overrides)
    return setup


class TestDefaults(unittest.TestCase):
    """DEFAULTS shape + new_setup copy semantics."""

    def test_new_setup_returns_documented_defaults(self):
        # All 9 keys/values exactly as pinned in research R7.
        self.assertEqual(new_setup(), EXPECTED_DEFAULTS)

    def test_new_setup_returns_fresh_copy_mutators_do_not_leak(self):
        s1 = new_setup()
        s1['win_cap_molecules'] = 999
        s1['xtb_path'] = '/overwrite'
        # A second call is unaffected by mutating the first.
        s2 = new_setup()
        self.assertEqual(s2['win_cap_molecules'], 10)
        self.assertIsNone(s2['xtb_path'])

    def test_module_level_defaults_never_mutated(self):
        before = dict(DEFAULTS)
        s = new_setup()
        s['demo_set'] = 'mutated'
        s['schema_version'] = 99
        self.assertEqual(DEFAULTS, before)

    def test_constants_pinned(self):
        self.assertEqual(SCHEMA_VERSION, 1)
        self.assertEqual(KNOWN_SETS, ('set_a',))
        # Box presets: exact xy extents (Angstrom); z-depth is display-only.
        self.assertEqual(BOX_PRESETS, {
            'small': ((-12.0, -12.0), (12.0, 12.0)),
            'medium': ((-18.0, -18.0), (18.0, 18.0)),
            'large': ((-25.0, -25.0), (25.0, 25.0)),
        })
        self.assertEqual(
            HESSIAN_WARNING,
            'hessian cost scales ~N^3; a ~100-atom snake may take 30-90 s')


class TestValidateClean(unittest.TestCase):
    """validate(DEFAULTS) is the empty errors/warnings baseline."""

    def test_defaults_validate_clean(self):
        self.assertEqual(validate(new_setup()), ([], []))

    def test_validate_returns_two_lists(self):
        errors, warnings = validate(new_setup())
        self.assertIsInstance(errors, list)
        self.assertIsInstance(warnings, list)


class TestValidateErrorMatrix(unittest.TestCase):
    """Each single-field mutation produces exactly one error naming the
    offending key (research R7 error list)."""

    def _assert_one_error(self, setup, key_name):
        errors, _warnings = validate(setup)
        self.assertEqual(len(errors), 1,
                         'expected exactly one error, got %r' % (errors,))
        self.assertIn(key_name, errors[0])

    def test_schema_version_foreign(self):
        self._assert_one_error(_mutated(schema_version=2), 'schema_version')

    def test_demo_set_unknown(self):
        self._assert_one_error(_mutated(demo_set='set_b'), 'demo_set')

    def test_box_preset_unknown(self):
        self._assert_one_error(_mutated(box_preset='huge'), 'box_preset')

    def test_win_cap_below_one(self):
        self._assert_one_error(
            _mutated(win_cap_molecules=0), 'win_cap_molecules')

    def test_win_cap_above_hard_max(self):
        self._assert_one_error(
            _mutated(win_cap_molecules=21), 'win_cap_molecules')

    def test_atom_budget_below_one(self):
        self._assert_one_error(_mutated(atom_budget=0), 'atom_budget')

    def test_speed_zero(self):
        self._assert_one_error(_mutated(speed=0), 'speed')

    def test_speed_non_number(self):
        self._assert_one_error(_mutated(speed='fast'), 'speed')

    def test_broadening_fwhm_negative(self):
        self._assert_one_error(
            _mutated(broadening_fwhm=-1.0), 'broadening_fwhm')

    def test_head_molecule_empty(self):
        self._assert_one_error(_mutated(head_molecule=''), 'head_molecule')

    def test_bool_is_not_a_number_for_speed(self):
        # py3.6 bool-is-int trap: True is not a valid speed.
        self._assert_one_error(_mutated(speed=True), 'speed')


class TestValidateXtbPath(unittest.TestCase):
    """xtb_path matrix: None/auto fine; valid file fine; missing/dir/
    quote each produce a precise error. Mirrors xtbenv.validate_binary_path
    rules via the local _xtb_path_problems helper."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix='srp_setup_')
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def _real_file(self):
        path = os.path.join(self.tmp, 'xtb.exe')
        with open(path, 'wb') as handle:
            handle.write(b'MZ')
        return path

    def test_none_is_fine_auto_detect(self):
        errors, _ = validate(_mutated(xtb_path=None))
        self.assertEqual([e for e in errors if 'xtb' in e], [])

    def test_real_file_valid(self):
        errors, _ = validate(_mutated(xtb_path=self._real_file()))
        self.assertEqual([e for e in errors if 'xtb' in e or 'quote' in e],
                         [])

    def test_missing_path_error_mentions_path(self):
        missing = os.path.join(self.tmp, 'no_such_xtb')
        errors, _ = validate(_mutated(xtb_path=missing))
        self.assertTrue(any(missing in e for e in errors),
                        'expected the path in an error; got %r' % (errors,))

    def test_directory_is_not_a_file(self):
        errors, _ = validate(_mutated(xtb_path=self.tmp))
        self.assertTrue(any('not a file' in e for e in errors),
                        'expected a not-a-file error; got %r' % (errors,))

    def test_path_with_quote_character(self):
        quoted = self._real_file() + '"'
        errors, _ = validate(_mutated(xtb_path=quoted))
        self.assertTrue(any('quote' in e for e in errors),
                        'expected a quote error; got %r' % (errors,))


class TestValidateWarnings(unittest.TestCase):
    """The single N-cubed hessian-cost warning (SETUP-06 / SPECTRA-06
    pure half). Fires once if EITHER cap > 10 OR budget > 100."""

    def test_cap_eleven_warns_once_exact_message(self):
        _errors, warnings = validate(_mutated(win_cap_molecules=11))
        self.assertEqual(warnings, [HESSIAN_WARNING])

    def test_cap_ten_no_warning(self):
        _errors, warnings = validate(_mutated(win_cap_molecules=10))
        self.assertEqual(warnings, [])

    def test_budget_over_100_warns(self):
        _errors, warnings = validate(_mutated(atom_budget=101))
        self.assertEqual(warnings, [HESSIAN_WARNING])

    def test_budget_100_no_warning(self):
        _errors, warnings = validate(_mutated(atom_budget=100))
        self.assertEqual(warnings, [])

    def test_cap_and_budget_both_over_still_one_warning(self):
        _errors, warnings = validate(
            _mutated(win_cap_molecules=11, atom_budget=101))
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings, [HESSIAN_WARNING])


class TestValidateNeverRaises(unittest.TestCase):
    """validate returns (errors, warnings) as a 2-tuple of lists for any
    input — errors are data, not exceptions."""

    def test_empty_dict_does_not_raise(self):
        result = validate({})
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], list)
        self.assertIsInstance(result[1], list)
        # An empty dict fails schema_version and every field.
        self.assertTrue(len(result[0]) >= 1)

    def test_non_numeric_cap_does_not_raise(self):
        result = validate(_mutated(win_cap_molecules='lots'))
        self.assertIsInstance(result, tuple)

    def test_none_speed_does_not_raise(self):
        result = validate(_mutated(speed=None))
        self.assertIsInstance(result, tuple)

    def test_non_numeric_budget_does_not_raise(self):
        result = validate(_mutated(atom_budget=None))
        self.assertIsInstance(result, tuple)


class TestSaveLoadRoundTrip(unittest.TestCase):
    """save_setup/load_setup round-trip the setup dict identically as
    sorted-key indented JSON (SETUP-05 pure half)."""

    def test_round_trip_identical(self):
        s = new_setup()
        s['box_preset'] = 'large'
        s['win_cap_molecules'] = 15   # valid; warns (>10) but saves fine
        s['xtb_path'] = None
        loaded = load_setup(save_setup(s))
        self.assertEqual(loaded, s)

    def test_save_output_is_sorted_key_indented_json(self):
        s = new_setup()
        s['box_preset'] = 'large'
        text = save_setup(s)
        self.assertTrue(text.startswith('{'), 'JSON object must start with {')
        self.assertIn('"box_preset"', text)
        # sorted-key: 'atom_budget' (a) precedes 'box_preset' (b) in text.
        self.assertLess(text.index('"atom_budget"'), text.index('"box_preset"'))
        # indent=2 produces a newline + 2-space-indented key.
        self.assertIn('\n  "atom_budget"', text)

    def test_save_invalid_setup_raises_mentioning_key(self):
        bad = new_setup()
        bad['win_cap_molecules'] = 0   # hard error (< 1)
        with self.assertRaises(SetupError) as ctx:
            save_setup(bad)
        self.assertIn('win_cap_molecules', str(ctx.exception))

    def test_save_warns_but_still_serializes(self):
        # A high cap warns but does NOT block save (warnings are advisory).
        s = new_setup()
        s['win_cap_molecules'] = 20   # valid (<=20), warns (>10)
        text = save_setup(s)          # must NOT raise
        self.assertEqual(load_setup(text), s)


class TestLoadSetupErrors(unittest.TestCase):
    """load_setup raises SetupError on corrupt JSON, foreign schema, and
    non-dict payloads (v1 loud-fail; friendly UX = Phase 8 SETUP-08)."""

    def test_invalid_json_mentions_valid_json(self):
        with self.assertRaises(SetupError) as ctx:
            load_setup('not json at all')
        self.assertIn('valid JSON', str(ctx.exception))

    def test_foreign_schema_version_not_supported(self):
        with self.assertRaises(SetupError) as ctx:
            load_setup('{"schema_version": 2}')
        msg = str(ctx.exception)
        self.assertIn('schema_version', msg)
        self.assertIn('not supported', msg)

    def test_non_dict_payload_raises(self):
        with self.assertRaises(SetupError):
            load_setup('[]')        # JSON list, not an object
        with self.assertRaises(SetupError):
            load_setup('42')        # JSON scalar, not an object

    def test_load_does_not_full_validate(self):
        # v1 checks schema_version ONLY: a v1-schema dict with otherwise
        # bogus fields loads without raising (caller validate()s after).
        loaded = load_setup('{"schema_version": 1, "win_cap_molecules": 0}')
        self.assertEqual(loaded['schema_version'], 1)
        self.assertEqual(loaded['win_cap_molecules'], 0)

    def test_v1_schema_loads(self):
        text = save_setup(new_setup())
        loaded = load_setup(text)
        self.assertEqual(loaded, new_setup())


class TestRandomizeHead(unittest.TestCase):
    """randomize_head is seed-deterministic via PRIVATE random.Random
    instances (never the global random module)."""

    CANDIDATES = ['phenol', 'benzene', 'biphenyl']

    def test_same_seed_identical_result(self):
        self.assertEqual(randomize_head(self.CANDIDATES, 42),
                         randomize_head(self.CANDIDATES, 42))

    def test_result_always_a_candidate(self):
        for seed in range(25):
            self.assertIn(randomize_head(self.CANDIDATES, seed),
                          self.CANDIDATES)

    def test_seeds_one_and_two_both_valid_members(self):
        r1 = randomize_head(self.CANDIDATES, 1)
        r2 = randomize_head(self.CANDIDATES, 2)
        self.assertIn(r1, self.CANDIDATES)
        self.assertIn(r2, self.CANDIDATES)
        # Do NOT assert r1 != r2 — seeds may coincidentally agree.

    def test_empty_candidates_raises(self):
        self.assertRaises(SetupError, randomize_head, [], 42)

    def test_private_rng_no_shared_state_across_calls(self):
        # Two calls with the same seed agree even when an intervening
        # different-seed call runs between them (a private Random per call
        # would; the global random module would not).
        first = randomize_head(self.CANDIDATES, 42)
        randomize_head(self.CANDIDATES, 7)      # intervening call
        randomize_head(self.CANDIDATES, 100)    # another intervening call
        again = randomize_head(self.CANDIDATES, 42)
        self.assertEqual(first, again)

    def test_different_candidate_lists_independent(self):
        # Determinism is per (candidates, seed); a different candidate
        # list with the same seed still picks a valid member.
        others = ['water', 'methane', 'ammonia']
        pick = randomize_head(others, 42)
        self.assertIn(pick, others)


class XtbPathUnificationTest(unittest.TestCase):
    """Pin the Phase-3 unification (03-03): setup_logic._xtb_path_problems
    delegates to xtbenv.validate_binary_path, so the two must agree on
    EVERY input class (None/non-str/empty, missing, directory, quoted,
    valid). The pre-existing TestValidateXtbPath matrix stays green
    UNMODIFIED — that is the byte-identity proof for validate(); this
    class pins the direct delegation separately and locks the historical
    message literals against accidental rewording.
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix='srp_unify_')
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def _real_file(self):
        path = os.path.join(self.tmp, 'xtb.exe')
        with open(path, 'wb') as handle:
            handle.write(b'MZ')
        return path

    def test_validators_agree_across_full_input_matrix(self):
        # The full input matrix: None, empty str, non-str, a missing
        # path, a directory, a quoted path (never created on disk), and
        # a real existing file. For each, the delegator and the
        # canonical validator must return EXACTLY the same list
        # (order + content).
        directory = tempfile.mkdtemp(prefix='srp_unify_dir_', dir=self.tmp)
        matrix = [
            None,
            '',
            5,
            os.path.join(tempfile.gettempdir(), 'srp_no_such_xtb.exe'),
            directory,
            "C:\\x'tb.exe",
            self._real_file(),
        ]
        for path in matrix:
            self.assertEqual(
                setup_logic._xtb_path_problems(path),
                xtbenv.validate_binary_path(path),
                'delegator disagrees with canonical validator for %r'
                % (path,))

    def test_missing_path_message_literals_pinned(self):
        # Lock the historical message contract against accidental
        # rewording: a missing path yields exactly the literal below.
        missing = os.path.join(tempfile.gettempdir(), 'srp_no_such_xtb.exe')
        self.assertEqual(
            setup_logic._xtb_path_problems(missing),
            ["'%s' does not exist" % (missing,)])
        # And the delegator matches the canonical validator here too.
        self.assertEqual(
            setup_logic._xtb_path_problems(missing),
            xtbenv.validate_binary_path(missing))


if __name__ == '__main__':
    unittest.main()
