"""ring_cycle tests (05-01): canonical planar 6-ring extraction in molfile.

THE TRAP this pins: manifest/setloader ``ring_atoms`` are the sorted 2-core
(e.g. benzene [0..5]), NOT ring-walk order. Feeding them to
``stacking.ring_frame`` spuriously fails planarity even for exactly-flat
benzene (1.133 A star-polygon artifact, probe-verified in
05-RESEARCH-core-integration.md section "ring_extraction_spec").
``molfile.ring_cycle(record)`` is the mandatory shim: ONE planar 6-cycle in
ring-walk order, canonical (smallest index first, min-over-orientations),
deterministic.

Canonical tuples are probe-verified LOCKED values from the research doc:
  benzene      (0, 1, 3, 5, 4, 2)
  naphthalene  (0, 1, 3, 7, 6, 2)
  anthracene   (0, 1, 5, 3, 2, 4)
  phenanthrene (0, 1, 3, 5, 4, 2)
  biphenyl     (0, 2, 6, 10, 8, 4)

Discovery command (verified on python3.6.9 -- `-t .` FAILS on python3.6
with a non-package start dir; do not add it):

    python3.6 -m unittest discover -s tests -p "test_*.py" -v

Real shipped bytes only (serpentrum/data/*.sdf) -- zero stubs.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from serpentrum import molfile  # noqa: E402
from serpentrum import stacking  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'serpentrum', 'data')

MOLECULES = ['benzene', 'naphthalene', 'anthracene', 'phenanthrene',
             'biphenyl']

# Probe-verified canonical 6-cycles (min-over-orientations normalization)
# from 05-RESEARCH-core-integration.md "ring_extraction_spec". LOCKED.
CANONICAL = {
    'benzene': (0, 1, 3, 5, 4, 2),
    'naphthalene': (0, 1, 3, 7, 6, 2),
    'anthracene': (0, 1, 5, 3, 2, 4),
    'phenanthrene': (0, 1, 3, 5, 4, 2),
    'biphenyl': (0, 2, 6, 10, 8, 4),
}

# Synthetic ethanol (C2H6O): 9 atoms, 8 bonds, zero rings. Simple hand
# coordinates -- TEST DATA, the extractor must not care about geometry.
ETHANOL_SDF = """ethanol
  serpentrum-test

  9  8  0  0  0  0  0  0  0  0999 V2000
    0.0000    0.0000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    1.5400    0.0000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    2.3900    0.9400    0.0000 O   0  0  0  0  0  0  0  0  0  0  0  0
   -0.3600    1.0300    0.0000 H   0  0  0  0  0  0  0  0  0  0  0  0
    0.3600   -0.5100    0.8900 H   0  0  0  0  0  0  0  0  0  0  0  0
    0.3600   -0.5100   -0.8900 H   0  0  0  0  0  0  0  0  0  0  0  0
    1.9000   -1.0300    0.0000 H   0  0  0  0  0  0  0  0  0  0  0  0
    1.1800    0.5100    0.8900 H   0  0  0  0  0  0  0  0  0  0  0  0
    3.3000    0.4600    0.0000 H   0  0  0  0  0  0  0  0  0  0  0  0
  1  2  1  0
  2  3  1  0
  1  4  1  0
  1  5  1  0
  1  6  1  0
  2  7  1  0
  2  8  1  0
  3  9  1  0
M  END
$$$$
"""


def _demo_record(name):
    """First (and only) record of the shipped demo SDF for <name>."""
    return molfile.read_sdf(os.path.join(DATA, '%s.sdf' % name))[0]


class TestCanonicalCycles(unittest.TestCase):
    """Case 1: the 5 probe-verified canonical 6-cycles are byte-pinned."""

    def test_benzene(self):
        self.assertEqual(tuple(molfile.ring_cycle(_demo_record('benzene'))),
                         CANONICAL['benzene'])

    def test_naphthalene(self):
        self.assertEqual(
            tuple(molfile.ring_cycle(_demo_record('naphthalene'))),
            CANONICAL['naphthalene'])

    def test_anthracene(self):
        self.assertEqual(
            tuple(molfile.ring_cycle(_demo_record('anthracene'))),
            CANONICAL['anthracene'])

    def test_phenanthrene(self):
        self.assertEqual(
            tuple(molfile.ring_cycle(_demo_record('phenanthrene'))),
            CANONICAL['phenanthrene'])

    def test_biphenyl(self):
        self.assertEqual(
            tuple(molfile.ring_cycle(_demo_record('biphenyl'))),
            CANONICAL['biphenyl'])


class TestTrapRegression(unittest.TestCase):
    """Case 2: the sorted 2-core is NOT ring-walk order (proven, not
    assumed). Benzene's shipped SDF is exactly flat (all z=0.000) yet the
    sorted order draws a star polygon whose Newell normal yields a
    spurious 1.133 A planarity violation."""

    def test_sorted_2core_fails_ring_planarity(self):
        record = _demo_record('benzene')
        core = molfile.find_ring_atoms(record)
        self.assertEqual(core, [0, 1, 2, 3, 4, 5])
        with self.assertRaises(ValueError):
            stacking.ring_frame(record['coords'], core)

    def test_walk_order_passes_ring_planarity(self):
        record = _demo_record('benzene')
        frame = stacking.ring_frame(record['coords'],
                                    molfile.ring_cycle(record))
        self.assertEqual(len(frame), 3)


class TestPlanarityAllDemo(unittest.TestCase):
    """Case 3: ring_cycle output passes ring_frame's 0.15 A planarity
    check for every shipped demo molecule (benzene included)."""

    def test_all_five_pass_ring_frame(self):
        for name in MOLECULES:
            record = _demo_record(name)
            cycle = molfile.ring_cycle(record)
            centroid, normal, ref = stacking.ring_frame(record['coords'],
                                                        cycle)
            for vec in (centroid, normal, ref):
                self.assertEqual(len(vec), 3)


class TestBiphenyl(unittest.TestCase):
    """Case 4: biphenyl's full 2-core (12 atoms, rings at 90.00 deg) is
    genuinely non-planar, but ONE extracted phenyl ring is planar."""

    def test_extracts_one_planar_six_ring(self):
        record = _demo_record('biphenyl')
        cycle = molfile.ring_cycle(record)
        self.assertIsInstance(cycle, list)
        self.assertEqual(len(cycle), 6)
        stacking.ring_frame(record['coords'], cycle)  # must NOT raise

    def test_full_2core_fails_ring_planarity(self):
        record = _demo_record('biphenyl')
        core = molfile.find_ring_atoms(record)
        self.assertEqual(len(core), 12)
        with self.assertRaises(ValueError):
            stacking.ring_frame(record['coords'], core)


class TestDeterminism(unittest.TestCase):
    """Case 5: same record -> identical list on every call (pure fn; the
    normal sign depends on orientation, so the rule must pin it)."""

    def test_repeated_calls_identical(self):
        for name in MOLECULES:
            record = _demo_record(name)
            first = molfile.ring_cycle(record)
            second = molfile.ring_cycle(record)
            self.assertIsInstance(first, list)
            self.assertEqual(first, second)


class TestAcyclic(unittest.TestCase):
    """Case 6: no 3..6-cycle exists (acyclic input) -> empty list."""

    def test_ethanol_returns_empty_list(self):
        record = molfile.read_sdf_text(ETHANOL_SDF)[0]
        self.assertEqual(record['ring_count'], 0)
        self.assertEqual(molfile.ring_cycle(record), [])


if __name__ == '__main__':
    unittest.main()
