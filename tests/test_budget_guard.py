"""budget_guard behavior-matrix tests (plan 06-01, SPECTRA-06).

The launch re-check is the pure half of SPECTRA-06 ("before launch,
hidden molecule/atom counts re-checked against the configured cap;
exceeding shows a warning", REQUIREMENTS.md:55). It is WARN-AND-PROCEED
by construction: a default-parameter WIN snake (10 stacked + head, set_a
12-24 atoms each) routinely exceeds atom_budget=100, and the win path
freezes molecules_stacked exactly AT the cap (game_engine.py:726-731) —
a blocking guard would make the shipped win path un-runnable
(06-RESEARCH-guard.md Q2).

Key count conventions pinned here:
- molecules_stacked EXCLUDES the head; the viewer chain-object count
  INCLUDES it — the guard renders molecules_stacked + 1.
- atoms_engine is the HEAD-INCLUSIVE run-input count (the true xtb input
  size; last_run['atoms_total'] is head-excluded,
  test_phase5_integration.py:267-273).
- Errors are DATA, not exceptions (setup_logic.validate precedent,
  setup_logic.py:203-224): None / non-numeric / bool inputs never raise.

Discovery command (python3.6; do NOT add `-t .` — fails on non-package
start dirs):

    python3.6 -m unittest discover -s tests -p "test_budget_guard.py" -v

Convention: every test file in tests/ repeats the sys.path self-insert
below. tests/ deliberately has NO __init__.py — the dev plugin path IS
the repo root, and findPlugins would treat a package dir here as a
second plugin.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from serpentrum import budget_guard, setup_logic  # noqa: E402


class TestLaunchBudgetWarnings(unittest.TestCase):
    """launch_budget_warnings(molecules_stacked, molecules_view,
    atoms_engine, atoms_view, atom_budget) -> [one-line warnings]."""

    def test_clean_run_empty(self):
        lines = budget_guard.launch_budget_warnings(9, 10, 96, 96, 100)
        self.assertEqual(lines, [])

    def test_over_budget_single_hessian_line(self):
        lines = budget_guard.launch_budget_warnings(9, 10, 130, 130, 100)
        self.assertEqual(len(lines), 1)
        self.assertIn(setup_logic.HESSIAN_WARNING, lines[0])
        # Revealed counts ride along (game is over; GAME-04's count-free
        # rule applied to play only).
        self.assertIn('130', lines[0])
        self.assertIn('100', lines[0])

    def test_at_budget_not_over(self):
        # Strictly greater triggers; AT the budget is legal.
        lines = budget_guard.launch_budget_warnings(9, 10, 100, 100, 100)
        self.assertEqual(lines, [])

    def test_molecule_desync_line(self):
        # Viewer chain disagrees with the engine counter: warn, proceed.
        lines = budget_guard.launch_budget_warnings(9, 7, 96, 96, 100)
        self.assertEqual(len(lines), 1)
        self.assertIn('7', lines[0])   # viewer sees 7 chain objects
        self.assertIn('10', lines[0])  # engine counted 9 + head = 10

    def test_atom_desync_line(self):
        lines = budget_guard.launch_budget_warnings(9, 10, 96, 104, 100)
        self.assertEqual(len(lines), 1)
        self.assertIn('96', lines[0])
        self.assertIn('104', lines[0])

    def test_both_desyncs_then_budget(self):
        lines = budget_guard.launch_budget_warnings(9, 7, 130, 96, 100)
        self.assertEqual(len(lines), 3)
        # Order pinned: molecule desync, atom desync, hessian LAST.
        self.assertIn('7', lines[0])
        self.assertIn('10', lines[0])
        self.assertIn('96', lines[1])
        self.assertIn('130', lines[1])
        self.assertIn(setup_logic.HESSIAN_WARNING, lines[2])

    def test_unavailable_atoms_line(self):
        # None -> one 'unavailable' line, nothing else, no raise.
        lines = budget_guard.launch_budget_warnings(9, 10, None, 96, 100)
        self.assertEqual(len(lines), 1)
        self.assertIn('unavailable', lines[0])
        # Non-numeric -> identical behavior.
        lines = budget_guard.launch_budget_warnings(9, 10, 'many', 96, 100)
        self.assertEqual(len(lines), 1)
        self.assertIn('unavailable', lines[0])

    def test_bool_not_crash(self):
        # bool-is-int trap (setup_logic._is_number precedent): whatever
        # the guard decides, it must NOT raise. _is_count excludes bool,
        # so it falls into the unavailable branch — pin that outcome.
        lines = budget_guard.launch_budget_warnings(9, 10, True, 96, 100)
        self.assertEqual(len(lines), 1)
        self.assertIn('unavailable', lines[0])

    def test_none_view_counts_skip_desync(self):
        # None viewer counts = cross-check unavailable, NOT a desync:
        # with over-budget atoms only the hessian line survives.
        lines = budget_guard.launch_budget_warnings(
            9, None, 130, None, 100)
        self.assertEqual(len(lines), 1)
        self.assertIn(setup_logic.HESSIAN_WARNING, lines[0])

    def test_no_budget_key(self):
        # atom_budget None = caller could not resolve a budget: no
        # budget line even when atoms_engine is large.
        lines = budget_guard.launch_budget_warnings(9, 10, 130, 130, None)
        self.assertEqual(lines, [])


class TestLaunchCountsLine(unittest.TestCase):
    """launch_counts_line(molecules_stacked, atoms_engine, atom_budget)
    -> one human-readable launch summary line."""

    def test_format(self):
        line = budget_guard.launch_counts_line(9, 96, 100)
        self.assertIn('10 molecules', line)  # 9 stacked + head
        self.assertIn('96 atoms', line)
        self.assertIn('100', line)

    def test_none_atoms(self):
        line = budget_guard.launch_counts_line(9, None, 100)
        self.assertIn('unavailable', line)


class TestDriftPin(unittest.TestCase):
    """HESSIAN_WARNING reuse is drift-pinned (the
    test_module_constants_guard_against_drift precedent,
    tests/test_xtbenv.py:298): a literal amendment in plan 06-11 flows
    through automatically without editing this expectation."""

    def test_warning_reuses_setup_literal(self):
        lines = budget_guard.launch_budget_warnings(9, 10, 250, 250, 100)
        self.assertEqual(len(lines), 1)
        self.assertIn(setup_logic.HESSIAN_WARNING, lines[0])


if __name__ == '__main__':
    unittest.main()
