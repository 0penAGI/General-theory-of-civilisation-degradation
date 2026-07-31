"""APP — Adaptive Pluralism Protocol.

"A living system does not avoid errors.
 It preserves the ability to turn collisions with reality
 into new branches of behavior."

Core (app_v5) and the v5.4 sandbox simulator (civilization_simulator):
an ecosystem of competing future measurers R1/R2/R3 — the truth about the
state of a system belongs to no single blind meter; a wrong meter is
rejected on the evidence of the realized trajectory and replaced by a
mutated descendant (Law 10 applied to knowledge itself).

Code is verified not by similarity to a previous version but by the
invariants of the 12 laws (see docs/SPEC.md).
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
    ReachabilityMeasurer,
    MeasurerEcosystem,
    run_demo,
    run_experiments,
)

__version__ = "5.4.0"
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
    "ReachabilityMeasurer",
    "MeasurerEcosystem",
    "run_demo",
    "run_experiments",
]
