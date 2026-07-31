"""APP — Adaptive Pluralism Protocol.

«Живая система не избегает ошибок.
 Она сохраняет способность превращать столкновения с реальностью
 в новые ветви поведения.»

Ядро (app_v5) и песочница-симулятор v5.3 (civilization_simulator).

Проверка кода — не сходство с прошлой версией, а инварианты 12 законов
(см. docs/SPEC.md).
"""

from .app_v5 import (
    ReplaceableComponent,
    Reality,
    RealityEvent,
    Scar,
    LineageNode,
    EvolutionOperator,
    BayesianOperator,
    CausalOperator,
    StochasticOperator,
    AutonomousAgent,
    ImmuneLayer,
    DiversityImmunity,
    ScarImmunity,
    RhythmAudit,
    PulseEngine,
    MemoryStore,
)
from .civilization_simulator import (
    Institution,
    AGI,
    Protocol,
    ReplaceabilityImmunity,
    SelfImmunity,
    Civilization,
    CivilizationEngine,
    build_scenario,
    default_events,
    run_scenario,
    scenario_report,
    measure_reachability,
    run_demo,
    run_experiments,
)

__version__ = "5.3.0"
__all__ = [
    "ReplaceableComponent",
    "Reality",
    "RealityEvent",
    "Scar",
    "LineageNode",
    "EvolutionOperator",
    "BayesianOperator",
    "CausalOperator",
    "StochasticOperator",
    "AutonomousAgent",
    "ImmuneLayer",
    "DiversityImmunity",
    "ScarImmunity",
    "RhythmAudit",
    "PulseEngine",
    "MemoryStore",
    "Institution",
    "AGI",
    "Protocol",
    "ReplaceabilityImmunity",
    "SelfImmunity",
    "Civilization",
    "CivilizationEngine",
    "build_scenario",
    "default_events",
    "run_scenario",
    "scenario_report",
    "measure_reachability",
    "run_demo",
    "run_experiments",
]
