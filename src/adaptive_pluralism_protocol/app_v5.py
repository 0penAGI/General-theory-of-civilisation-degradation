# ==============================================================================
# ADAPTIVE PLURALISM PROTOCOL (APP) — REFERENCE IMPLEMENTATION v5.0
#
# "Живая система не избегает ошибок.
#  Она сохраняет способность превращать столкновения с реальностью
#  в новые ветви поведения."
#
# CIRM -> APP evolution
# ==============================================================================
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
import random
import json
import time
# ==============================================================================
# 0. EVENTS
# ==============================================================================
@dataclass
class RealityEvent:
    name: str
    intensity: float
    timestamp: float = field(default_factory=time.time)
    def is_overwhelming(self) -> bool:
        return self.intensity > 0.75
# ==============================================================================
# 1. REPLACEABILITY CORE
# ==============================================================================
class ReplaceableComponent:
    def __init__(self, name: str):
        self.name = name
        self.generation = 1
        self.replacement_history = []
    def replace(self, reason: str):
        self.generation += 1
        self.replacement_history.append({
            "generation": self.generation,
            "reason": reason,
            "time": time.time()
        })
        print(
            f"[REPLACE] {self.name} -> generation {self.generation} "
            f"({reason})"
        )
# ==============================================================================
# 2. SCAR MEMORY
# ==============================================================================
@dataclass
class Scar:
    event: str
    action: str
    outcome: str
    pressure: float
    def signature(self):
        return (
            f"{self.event}:"
            f"{self.action}:"
            f"{self.outcome}:"
            f"{round(self.pressure,2)}"
        )
# ==============================================================================
# 3. DAG LINEAGE MEMORY
# ==============================================================================
class LineageNode:
    def __init__(
        self,
        state: str,
        parents=None
    ):
        self.state = state
        self.parents = parents or []
        self.children = []
        for p in self.parents:
            p.children.append(self)
    @staticmethod
    def recombine(a, b, new_state):
        node = LineageNode(
            new_state,
            parents=[a,b]
        )
        print(
            f"[DAG] recombination: "
            f"{a.state[:20]} + {b.state[:20]}"
        )
        return node
# ==============================================================================
# 4. EVOLUTION OPERATORS
# ==============================================================================
class EvolutionOperator(ReplaceableComponent):
    def __init__(self,name):
        super().__init__(name)
    @abstractmethod
    def mutate(
        self,
        strategy:str,
        scars:List[Scar]
    ) -> str:
        pass
class BayesianOperator(EvolutionOperator):
    def __init__(self):
        super().__init__("BayesianOperator")
    def mutate(self,strategy,scars):
        return (
            f"bayes({strategy})"
            f"_learned_from_{len(scars)}_scars"
        )
class CausalOperator(EvolutionOperator):
    def __init__(self):
        super().__init__("CausalOperator")
    def mutate(self,strategy,scars):
        return (
            f"causal_rewire({strategy})"
        )
class StochasticOperator(EvolutionOperator):
    def __init__(self):
        super().__init__("StochasticOperator")
    def mutate(self,strategy,scars):
        seed=random.randint(0,9999)
        return (
            f"random_branch_{seed}"
            f"_from_{strategy}"
        )
# ==============================================================================
# 5. FRAGMENTED REALITY
# ==============================================================================
class Reality:
    def __init__(self):
        self.state={
            "entropy":0.5,
            "pressure":0.5,
            "instability":0.5
        }
    def perturb(self,event:RealityEvent):
        self.state["pressure"]=event.intensity
        print(
            f"[REALITY] {event.name} "
            f"pressure={event.intensity}"
        )
    def observe(self,agent_name):
        bias=(sum(ord(x) for x in agent_name)%20)/100
        value=min(
            1.0,
            self.state["pressure"]+bias-0.1
        )
        return value
# ==============================================================================
# 6. AUTONOMOUS AGENT
# ==============================================================================
class AutonomousAgent(ReplaceableComponent):
    def __init__(
        self,
        name: str,
        initial_strategy: str,
        operator: EvolutionOperator
    ):
        super().__init__(name)
        self.strategy = initial_strategy
        self.operator = operator
        self.scars: List[Scar] = []
        self.lineage_root = LineageNode(initial_strategy)
        self.current_lineage = self.lineage_root
        self.last_observation = 0.0
        self.trust = 1.0
    # --------------------------------------------------
    def explore(self):
        print(
            f"[EXPLORE] {self.name}: {self.strategy}"
        )
        return self.strategy
    # --------------------------------------------------
    def observe(self, reality: Reality):
        self.last_observation = reality.observe(self.name)
        print(
            f"[OBSERVE] {self.name}: "
            f"{self.last_observation:.2f}"
        )
        return self.last_observation
    # --------------------------------------------------
    def synchronize(self,event:RealityEvent):
        threshold = 0.65
        if self.last_observation > threshold:
            print(
                f"[SYNC] {self.name} accepts "
                f"{event.name}"
            )
            return True
        print(
            f"[DOUBT] {self.name} keeps uncertainty"
        )
        return False
    # --------------------------------------------------
    def act(self):
        action = (
            f"{self.name}_action_"
            f"{self.strategy}"
        )
        return action
    # --------------------------------------------------
    def learn(
        self,
        event:RealityEvent,
        action:str,
        success:bool
    ):
        outcome = (
            "adapted"
            if success
            else
            "failed"
        )
        scar = Scar(
            event=event.name,
            action=action,
            outcome=outcome,
            pressure=event.intensity
        )
        self.scars.append(scar)
        # давление реальности
        if event.intensity > 0.55:
            new_strategy = self.operator.mutate(
                self.strategy,
                self.scars
            )
            self.strategy = new_strategy
            self.current_lineage = LineageNode(
                new_strategy,
                parents=[self.current_lineage]
            )
            print(
                f"[EVOLVE] {self.name} -> "
                f"{new_strategy}"
            )
    # --------------------------------------------------
    def export_state(self):
        return {
            "name":self.name,
            "strategy":self.strategy,
            "generation":self.generation,
            "scars":[
                s.signature()
                for s in self.scars
            ]
        }
# ==============================================================================
# 7. LOCAL IMMUNITY
# ==============================================================================
class ImmuneLayer(ReplaceableComponent):
    def __init__(self,name):
        super().__init__(name)
    def inspect(
        self,
        agents:List[AutonomousAgent]
    ):
        raise NotImplementedError
class DiversityImmunity(ImmuneLayer):
    def __init__(self):
        super().__init__(
            "DiversityImmunity"
        )
    def inspect(self,agents):
        strategies={
            a.strategy
            for a in agents
        }
        if len(strategies)==1:
            print(
                "[IMMUNITY] "
                "Monoculture detected"
            )
            return False
        print(
            "[IMMUNITY] "
            f"Diversity={len(strategies)}"
        )
        return True
class ScarImmunity(ImmuneLayer):
    def __init__(self):
        super().__init__(
            "ScarImmunity"
        )
    def inspect(self,agents):
        total=sum(
            len(a.scars)
            for a in agents
        )
        if total==0:
            print(
                "[IMMUNITY] "
                "No learning detected"
            )
            return False
        return True
# ==============================================================================
# 8. RHYTHM AUDIT
# ==============================================================================
class RhythmAudit:
    def evaluate(
        self,
        agents
    ):
        strategies={
            a.strategy
            for a in agents
        }
        if len(strategies)>1:
            print(
                "[RHYTHM] "
                "Search space alive"
            )
            return True
        print(
            "[RHYTHM] "
            "Crystallization risk"
        )
        return False
# ==============================================================================
# 9. PULSE ENGINE
# ==============================================================================
class PulseEngine(ReplaceableComponent):
    def __init__(self):
        super().__init__(
            "AdaptivePulseEngine"
        )
        self.audit = RhythmAudit()
    def execute(
        self,
        agents:List[AutonomousAgent],
        reality:Reality,
        event:RealityEvent,
        immunity_layers:List[ImmuneLayer]
    ):
        print("\n" + "="*70)
        print(
            f"PULSE START: {event.name}"
        )
        print("="*70)
        # --------------------------------------------------
        # PHASE 1
        # Exploration
        # --------------------------------------------------
        for agent in agents:
            agent.explore()
        # --------------------------------------------------
        # PHASE 2
        # Reality collision
        # --------------------------------------------------
        reality.perturb(event)
        observations=[]
        for agent in agents:
            observations.append(
                agent.observe(reality)
            )
        # --------------------------------------------------
        # PHASE 3
        # Temporary synchronization
        # --------------------------------------------------
        consensus=0
        for agent in agents:
            if agent.synchronize(event):
                consensus+=1
        sync_ratio=consensus/len(agents)
        print(
            f"[CONSENSUS] "
            f"{sync_ratio:.2f}"
        )
        # --------------------------------------------------
        # PHASE 4
        # Intervention + scars
        # --------------------------------------------------
        for agent in agents:
            action=agent.act()
            # в реальной системе здесь будет внешний feedback
            success=random.random()>0.35
            agent.learn(
                event,
                action,
                success
            )
        # --------------------------------------------------
        # PHASE 5
        # Local immunity
        # --------------------------------------------------
        for layer in immunity_layers:
            layer.inspect(
                agents
            )
        # --------------------------------------------------
        # PHASE 6
        # Rediscover
        # --------------------------------------------------
        alive=self.audit.evaluate(
            agents
        )
        if not alive:
            print(
                "[WARNING] "
                "Forcing mutation pressure"
            )
            for agent in agents:
                agent.operator.replace(
                    "restore evolutionary distance"
                )
        print(
            "[PULSE END]"
        )
# ==============================================================================
# 10. STATE STORAGE
# ==============================================================================
class MemoryStore:
    @staticmethod
    def save(
        agents,
        filename="app_state.json"
    ):
        data=[
            a.export_state()
            for a in agents
        ]
        with open(
            filename,
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                data,
                f,
                indent=2,
                ensure_ascii=False
            )
        print(
            f"[SAVE] {filename}"
        )
# ==============================================================================
# 11. DEMONSTRATION
# ==============================================================================
if __name__=="__main__":
    print(
        """
====================================================
 ADAPTIVE PLURALISM PROTOCOL v5.0
 Rhythm > Diversity
 Reality > Declaration
 Replaceability > Permanence
====================================================
"""
    )
    reality=Reality()
    agents=[
        AutonomousAgent(
            "Bayesian_Mind",
            "statistical_model",
            BayesianOperator()
        ),
        AutonomousAgent(
            "Causal_Mind",
            "causal_graph",
            CausalOperator()
        ),
        AutonomousAgent(
            "Wild_Mind",
            "unknown_search",
            StochasticOperator()
        )
    ]
    immunity=[
        DiversityImmunity(),
        ScarImmunity()
    ]
    pulse=PulseEngine()
    # сильный удар
    pulse.execute(
        agents,
        reality,
        RealityEvent(
            "systemic_failure",
            0.9
        ),
        immunity
    )
    # слабый сигнал
    pulse.execute(
        agents,
        reality,
        RealityEvent(
            "minor_noise",
            0.3
        ),
        immunity
    )
    # DAG recombination
    hybrid=LineageNode.recombine(
        agents[0].current_lineage,
        agents[1].current_lineage,
        "hybrid_causal_bayes"
    )
    agents[0].current_lineage=hybrid
    agents[0].strategy=hybrid.state
    print(
        "\n[HYBRID]"
        ,
        agents[0].strategy
    )
    MemoryStore.save(
        agents
    )
    print(
        """
====================================================
 APP v5.0 COMPLETE
 System survived:
 - reality collision
 - temporary consensus
 - adaptation
 - scar formation
 - divergence restoration
====================================================
"""
    )
