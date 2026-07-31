"""v5.4: ecosystem of competing future measurers (R1/R2/R3).

Run from the repository root:
    python -m unittest discover -s tests -v
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from adaptive_pluralism_protocol import (
    build_scenario,
    MeasurerEcosystem,
    ReachabilityMeasurer,
    run_scenario,
    scenario_report,
)

# history where R2 (cap:2) calls state (0,1,2) alive, and the system then
# dies (signature (_,3,_) — an objective terminal)
BLIND_HISTORY = [
    (0, 1, 2), (0, 2, 2), (1, 3, 2), (1, 3, 2), (0, 2, 2),
    (0, 1, 2), (0, 2, 2), (1, 3, 2), (1, 3, 2), (0, 2, 2),
]
# history where R1/R3 (cap:1) call (0,1,2) dead, and the system recovers
WOLF_HISTORY = [
    (0, 1, 2), (0, 0, 3), (0, 0, 3), (0, 1, 2), (0, 0, 3),
    (0, 1, 2), (0, 0, 3), (0, 1, 2), (0, 0, 3),
]


def _civ_with_history(history, seed=1):
    civ = build_scenario("adaptive", True, seed=seed)
    civ.signature_history = list(history)
    return civ


class TestMeasurerEcosystem(unittest.TestCase):
    def test_meters_are_genuinely_incompatible(self):
        ec = MeasurerEcosystem(seed=1)
        keys = {ec._ontology_key(m) for m in ec.measurers}
        self.assertEqual(len(keys), 3)
        self.assertFalse(ec.monoculture())

    def test_blind_meter_replaced_tighter(self):
        ec = MeasurerEcosystem(seed=1)
        ec.audit(_civ_with_history(BLIND_HISTORY), mutate=True)
        r2 = ec.measurers[1]
        self.assertTrue(r2.name.startswith("R2_far"))
        self.assertGreater(r2.depth, 0)
        self.assertLessEqual(r2.ontology["cap"], 1)
        self.assertLessEqual(r2.ontology["inv"], 2)

    def test_wolf_meter_replaced_looser(self):
        ec = MeasurerEcosystem(seed=1)
        ec.audit(_civ_with_history(WOLF_HISTORY), mutate=True)
        r1 = ec.measurers[0]
        self.assertTrue(r1.name.startswith("R1_strict"))
        self.assertGreater(r1.depth, 0)
        self.assertGreaterEqual(r1.ontology["cap"], 2)

    def test_audit_without_mutation_is_readonly(self):
        ec = MeasurerEcosystem(seed=1)
        before = [m.name for m in ec.measurers]
        ec.audit(_civ_with_history(BLIND_HISTORY), mutate=False)
        after = [m.name for m in ec.measurers]
        self.assertEqual(before, after)

    def test_monoculture_detection(self):
        ec = MeasurerEcosystem(seed=1)
        self.assertFalse(ec.monoculture())
        for m in ec.measurers:
            m.ontology = {"inv": 3, "cap": 1, "viable": 0}
            m.horizon = 12
        self.assertTrue(ec.monoculture())

    def test_meta_report_carries_ensemble_verdict(self):
        civ = run_scenario("meta", True, seed=1, hostile_agi=True)
        r = scenario_report(civ)
        self.assertIn("R_min", r)
        self.assertIn("R_max", r)
        self.assertIn("R_measurers", r)
        self.assertIn("R_median", r)
        self.assertGreaterEqual(r["R_max"], r["R_min"])

    def test_measurer_lineage_preserved(self):
        ec = MeasurerEcosystem(seed=1)
        ec.audit(_civ_with_history(BLIND_HISTORY), mutate=True)
        child = ec.measurers[1]
        parent = child.current_lineage.parents[0]
        self.assertIn("R2_far", parent.state)


if __name__ == "__main__":
    unittest.main()
