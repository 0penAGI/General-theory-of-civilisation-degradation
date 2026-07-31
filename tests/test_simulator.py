"""Регрессионные проверки вердиктов песочницы v5.3.

Запуск из корня репозитория:
    python -m unittest discover -s tests -v
или:
    python -m pytest tests
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from adaptive_pluralism_protocol import run_scenario, scenario_report

SCENARIOS = [
    ("monolith", False, False),
    ("plural", False, False),
    ("adaptive", True, False),
    ("adaptive_h", True, True),
    ("meta", True, True),
]


class TestVerdicts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reports = {}
        for kind, immunity, hostile in SCENARIOS:
            civ = run_scenario(
                kind, immunity, seed=1, hostile_agi=hostile
            )
            cls.reports[kind] = scenario_report(civ)

    def test_monolith_crystallizes(self):
        self.assertTrue(self.reports["monolith"]["crystallized"])
        self.assertEqual(self.reports["monolith"]["R"], 0.0)

    def test_plural_crystallizes(self):
        self.assertTrue(self.reports["plural"]["crystallized"])
        self.assertEqual(self.reports["plural"]["R"], 0.0)

    def test_adaptive_survives(self):
        self.assertFalse(self.reports["adaptive"]["crystallized"])
        self.assertGreater(self.reports["adaptive"]["R"], 0.3)

    def test_adaptive_h_dies_against_hostile_agi(self):
        self.assertTrue(self.reports["adaptive_h"]["crystallized"])
        self.assertEqual(self.reports["adaptive_h"]["R"], 0.0)

    def test_meta_survives_hostile_agi_and_revises_protocol(self):
        self.assertFalse(self.reports["meta"]["crystallized"])
        self.assertGreater(self.reports["meta"]["R"], 0.3)
        self.assertGreater(self.reports["meta"]["protocol_gen"], 1)

    def test_meta_outreaches_adaptive(self):
        self.assertGreaterEqual(
            self.reports["meta"]["R"],
            self.reports["adaptive"]["R"],
        )


if __name__ == "__main__":
    unittest.main()
