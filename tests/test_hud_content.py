"""tests/test_hud_content.py -- STACK-04 HUD content builders (plan 05-09, TDD RED first).

Pins the PURE info-box content builders added to hud_logic by plan
05-09 (05-RESEARCH-gui-lifecycle.md info_box_spec: the info box stays a
dumb rolling log with NO queue/priority system; these builders are the
only new surface). Every chemistry sentence comes VERBATIM from the
shipped dataset's own fields (no-fabrication rule) — hud_logic composes,
it never writes chemistry:

  hud_logic.pickup_block(name, interaction, citation_short)
      -> '+ <name>: <interaction name>, <d> A plane gap (centroid
         <composed> A @ <angle> deg off-normal) - <explanation> [<short>]'
      where composed = sqrt(d^2 + l^2) and angle = degrees(atan2(l, d))
      from the interaction dict's distance_a / lateral_offset_a (the
      shipped pi_stack_pd entry encodes 3.60 A @ 20.0 deg); the dataset
      explanation is rendered VERBATIM with newlines collapsed to single
      spaces; the citation short code is last.
  hud_logic.skip_text(name, reason) -> 'skipped <name>: <reason>'
  hud_logic.budget_text() -> count-free budget advisory; NO digit may
      appear (GAME-04 keeps molecule/atom counts hidden during play).
  hud_logic.completion_lines(result, molecules, snake_molecules,
      atoms_total) -> four summary lines; counts REVEALED at completion
      (GAME-09 / SPECTRA-06).
  hud_logic.breakdown_lines(history) -> end-of-run grouping of the
      session stacked_history: stacked entries by name, refusals by
      (outcome, name); first-appearance order; empty history -> [].
  hud_logic.idle_tip(explanations, index) -> round-robin 'tip: ...'
      from VERBATIM dataset explanations (newline-collapsed); None on
      an empty list.
  hud_logic.resume_note(name) -> the G2 un-finish info line.
  hud_logic.reason_text(code, detail, name) -> placement.py outcome
      code -> educator-readable reason, rendered through skip_text.

The real shipped dataset is used (molecule_data.load_stacking over
setloader.default_stacking_path()) so the pins track real data changes.

Discovery command (python3.6 — no '-t .' on non-package start dir):

    python3.6 -m unittest discover -s tests -p "test_hud_content.py" -v
"""
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from serpentrum import hud_logic  # noqa: E402
from serpentrum import molecule_data  # noqa: E402
from serpentrum import placement  # noqa: E402
from serpentrum import setloader  # noqa: E402

STACKING_DATA = molecule_data.load_stacking(setloader.default_stacking_path())
PI_STACK_PD = STACKING_DATA['interactions'][0]
JANIAK_SHORT = STACKING_DATA['citations'][PI_STACK_PD['citation']]['short']


def _expected_composed(interaction):
    d = interaction['distance_a']
    l = interaction['lateral_offset_a']
    return math.sqrt(d * d + l * l)


def _expected_angle(interaction):
    return math.degrees(math.atan2(interaction['lateral_offset_a'],
                                   interaction['distance_a']))


class TestPickupBlock(unittest.TestCase):
    """pickup_block: dataset-composed per-pickup info line (STACK-04)."""

    def test_real_dataset_pi_stack_pd(self):
        # The builder renders the SHIPPED pi_stack_pd entry: interaction
        # name, stored 3.38 A plane gap, composed 3.60 A centroid distance
        # @ 20.0 deg off-normal, verbatim explanation, Janiak 2000 short.
        line = hud_logic.pickup_block('naphthalene', PI_STACK_PD,
                                      JANIAK_SHORT)
        self.assertIn('pi-pi stacking (parallel-displaced)', line)
        self.assertIn('3.38', line)
        self.assertIn('3.60', line)
        self.assertIn('20.0', line)
        self.assertIn('Janiak 2000', line)

    def test_exact_format_and_composed_values(self):
        line = hud_logic.pickup_block('naphthalene', PI_STACK_PD,
                                      JANIAK_SHORT)
        explanation = PI_STACK_PD['explanation'].replace('\n', ' ')
        expected = ('+ naphthalene: pi-pi stacking (parallel-displaced), '
                    '%.2f A plane gap (centroid %.2f A @ %.1f deg '
                    'off-normal) - %s [%s]'
                    % (PI_STACK_PD['distance_a'],
                       _expected_composed(PI_STACK_PD),
                       _expected_angle(PI_STACK_PD),
                       explanation, JANIAK_SHORT))
        self.assertEqual(line, expected)
        # The composed pins are the human-verified values (dataset pins).
        self.assertEqual('%.2f' % _expected_composed(PI_STACK_PD), '3.60')
        self.assertEqual('%.1f' % _expected_angle(PI_STACK_PD), '20.0')

    def test_newlines_in_explanation_collapse_to_spaces(self):
        # The info box is a rolling single-line log: multi-line dataset
        # text must never break the line structure.
        interaction = dict(PI_STACK_PD)
        interaction['explanation'] = 'first line\nsecond line'
        line = hud_logic.pickup_block('benzene', interaction,
                                      'Janiak 2000')
        self.assertNotIn('\n', line)
        self.assertIn('first line second line', line)

    def test_citation_short_last(self):
        line = hud_logic.pickup_block('benzene', PI_STACK_PD,
                                      JANIAK_SHORT)
        self.assertTrue(line.endswith('[%s]' % JANIAK_SHORT))

    def test_no_authored_chemistry_uses_dataset_fields_only(self):
        # Swap in a synthetic interaction: only the dict's own fields may
        # appear in the line (hud_logic composes, never writes chemistry).
        interaction = {'name': 'INAME', 'distance_a': 1.5,
                       'lateral_offset_a': 0.5, 'explanation': 'IEXPL'}
        line = hud_logic.pickup_block('ONAME', interaction, 'ISHORT')
        self.assertIn('ONAME', line)
        self.assertIn('INAME', line)
        self.assertIn('IEXPL', line)
        self.assertIn('ISHORT', line)


class TestSkipText(unittest.TestCase):
    """skip_text: refuses/skips name the molecule and the reason."""

    def test_format(self):
        self.assertEqual(hud_logic.skip_text('biphenyl', 'no ring'),
                         'skipped biphenyl: no ring')


class TestBudgetText(unittest.TestCase):
    """budget_text: count-free advisory (GAME-04 hidden during play)."""

    def test_constant_line(self):
        self.assertEqual(
            hud_logic.budget_text(),
            'atom budget exceeded - spectra on this snake may be slow')

    def test_no_digits(self):
        # Counts are revealed ONLY at completion (GAME-09): the during-
        # play advisory must never leak a molecule/atom count.
        text = hud_logic.budget_text()
        self.assertFalse(any(ch.isdigit() for ch in text), text)


class TestCompletionLines(unittest.TestCase):
    """completion_lines: counts REVEALED at completion (GAME-09)."""

    def test_four_lines(self):
        self.assertEqual(
            hud_logic.completion_lines('won', 3, 4, 79),
            ['result: won',
             'score: 3 molecule(s) stacked',
             'snake: 4 molecules (incl. head)',
             'atoms: 79 (spectra input size)'])

    def test_crash_result_renders(self):
        self.assertEqual(
            hud_logic.completion_lines('crashed (boundary)', 1, 2, 41),
            ['result: crashed (boundary)',
             'score: 1 molecule(s) stacked',
             'snake: 2 molecules (incl. head)',
             'atoms: 41 (spectra input size)'])


class TestBreakdownLines(unittest.TestCase):
    """breakdown_lines: end-of-run stacked counts + refusal summary."""

    def test_empty_history(self):
        self.assertEqual(hud_logic.breakdown_lines([]), [])

    def test_stacked_grouped_by_name(self):
        history = [
            {'name': 'naphthalene', 'outcome': 'stacked',
             'distance_a': 3.383, 'citation_short': 'Janiak 2000'},
            {'name': 'naphthalene', 'outcome': 'stacked',
             'distance_a': 3.383, 'citation_short': 'Janiak 2000'},
        ]
        self.assertEqual(hud_logic.breakdown_lines(history),
                         ['stacked 2x naphthalene at 3.38 A plane gap '
                          '[Janiak 2000]'])

    def test_refusals_grouped_by_outcome_and_name(self):
        history = [
            {'name': 'biphenyl', 'outcome': 'SKIP_NO_ENTRY',
             'distance_a': None, 'citation_short': None},
            {'name': 'biphenyl', 'outcome': 'SKIP_NO_ENTRY',
             'distance_a': None, 'citation_short': None},
        ]
        self.assertEqual(hud_logic.breakdown_lines(history),
                         ['refused 2x biphenyl: no verified stacking '
                          'entry for this molecule (no invented '
                          'chemistry)'])

    def test_first_appearance_order(self):
        history = [
            {'name': 'naphthalene', 'outcome': 'stacked',
             'distance_a': 3.383, 'citation_short': 'Janiak 2000'},
            {'name': 'benzene', 'outcome': 'stacked',
             'distance_a': 3.383, 'citation_short': 'Janiak 2000'},
            {'name': 'naphthalene', 'outcome': 'stacked',
             'distance_a': 3.383, 'citation_short': 'Janiak 2000'},
            {'name': 'aniline', 'outcome': 'SKIP_NO_RING',
             'distance_a': None, 'citation_short': None},
        ]
        self.assertEqual(
            hud_logic.breakdown_lines(history),
            ['stacked 2x naphthalene at 3.38 A plane gap [Janiak 2000]',
             'stacked 1x benzene at 3.38 A plane gap [Janiak 2000]',
             'refused 1x aniline: no planar aromatic 6-ring found'])

    def test_distinct_outcome_codes_group_separately(self):
        history = [
            {'name': 'biphenyl', 'outcome': 'SKIP_NO_ENTRY',
             'distance_a': None, 'citation_short': None},
            {'name': 'biphenyl', 'outcome': 'REFUSE_ATOM',
             'distance_a': None, 'citation_short': None},
        ]
        lines = hud_logic.breakdown_lines(history)
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0],
                         'refused 1x biphenyl: no verified stacking '
                         'entry for this molecule (no invented '
                         'chemistry)')
        self.assertEqual(lines[1],
                         'refused 1x biphenyl: placement clashes')


class TestIdleTip(unittest.TestCase):
    """idle_tip: round-robin VERBATIM dataset explanations."""

    def test_round_robin(self):
        tips = ['alpha', 'beta']
        self.assertEqual(hud_logic.idle_tip(tips, 0), 'tip: alpha')
        self.assertEqual(hud_logic.idle_tip(tips, 1), 'tip: beta')
        self.assertEqual(hud_logic.idle_tip(tips, 2), 'tip: alpha')
        self.assertEqual(hud_logic.idle_tip(tips, 3), 'tip: beta')

    def test_empty_returns_none(self):
        self.assertIs(hud_logic.idle_tip([], 0), None)

    def test_newline_collapse(self):
        self.assertEqual(hud_logic.idle_tip(['a\nb'], 0), 'tip: a b')

    def test_real_dataset_explanation_verbatim(self):
        line = hud_logic.idle_tip([PI_STACK_PD['explanation']], 0)
        self.assertEqual(line, 'tip: %s'
                         % PI_STACK_PD['explanation'].replace('\n', ' '))


class TestResumeNote(unittest.TestCase):
    """resume_note: the G2 reject-then-recapture un-finish info line."""

    def test_constant_line(self):
        self.assertEqual(
            hud_logic.resume_note('naphthalene'),
            'placement refused - run continues (cap not reached yet)')


class TestReasonText(unittest.TestCase):
    """reason_text: placement.py outcome code -> educator-readable line.

    The code CONSTANTS come from placement.py itself (one taxonomy, two
    consumers) — never retyped here except as the observable output.
    """

    def test_all_skip_codes(self):
        self.assertEqual(
            hud_logic.reason_text(placement.SKIP_NO_ENTRY, None,
                                  'naphthalene'),
            'skipped naphthalene: no verified stacking entry for this '
            'molecule (no invented chemistry)')
        self.assertEqual(
            hud_logic.reason_text(placement.SKIP_NOT_APPROVED, None,
                                  'naphthalene'),
            'skipped naphthalene: stacking entry not approved yet')
        self.assertEqual(
            hud_logic.reason_text(placement.SKIP_MODE, None, 'naphthalene'),
            'skipped naphthalene: interaction mode not supported in v1')
        self.assertEqual(
            hud_logic.reason_text(placement.SKIP_NO_RING, None,
                                  'naphthalene'),
            'skipped naphthalene: no planar aromatic 6-ring found')
        self.assertEqual(
            hud_logic.reason_text(placement.SKIP_NONPLANAR, None,
                                  'naphthalene'),
            'skipped naphthalene: ring geometry not planar')

    def test_refuse_codes(self):
        self.assertEqual(
            hud_logic.reason_text(placement.REFUSE_WALL, None, 'naphthalene'),
            'skipped naphthalene: placement would leave the play box')

    def test_refuse_atom_includes_detail(self):
        self.assertEqual(
            hud_logic.reason_text(placement.REFUSE_ATOM, '2.10 A',
                                  'naphthalene'),
            'skipped naphthalene: placement clashes (2.10 A)')

    def test_refuse_atom_without_detail_renders_placeholder(self):
        # breakdown_lines has no clash detail: the reason string without
        # a detail renders the bare form (no dangling parenthesis).
        self.assertEqual(
            hud_logic.reason_text(placement.REFUSE_ATOM, None,
                                  'naphthalene'),
            'skipped naphthalene: placement clashes')


if __name__ == '__main__':
    unittest.main()
