# ==============================================================================
# CIVILIZATION SIMULATOR — APP v5.4
#
# "Система должна сохранять способность переходить между фазами,
#  а не застывать в одной из них."
#
# Layers:
#   Agents -> Structures -> Resources -> Reality pressure -> APP adaptation cycle
#
# Три шага от v5.2 (v5.3):
#   1) AGI больше не особая вершина. Единая иерархия структур (закон 7):
#      AGI — это Institution с высокой adaptation_rate.
#   2) R — ИЗМЕРЯЕМАЯ достижимость: возмущаем систему, гоняем N траекторий,
#      считаем, сколько различимых будущих бассейнов реально достижимо.
#   3) МЕТА-ТЕСТ: может ли APP доказать, что его надо заменить?
#      Protocol — заменяемый компонент правил; SelfImmunity аудирует
#      достижимость под текущими правилами (закон 7 к самому протоколу).
#
# Шаг v5.4 — ИММУННАЯ СИСТЕМА ДЛЯ САМОГО ПОЗНАНИЯ (закон 10):
#   Истина о состоянии системы не принадлежит одному измерителю. Вместо
#   единственного слепого measure_reachability — экосистема конкурирующих
#   измерителей будущего R1/R2/R3: разные онтологии смерти, разные горизонты,
#   разные возмущения. Не «какая R лучше», а несколько несовместимых моделей
#   будущего сосуществуют и конкурируют, не уничтожая друг друга.
#   Слепой измеритель (Zero Law) отбраковывается по физическим свидетельствам
#   реальной траектории (Reality First) и заменяется мутировавшим потомком,
#   причём направление мутации задаёт шрам (Scar Principle), а не шум.
#   Монокультура измерения (все метры сошлись в один «истинный») — это сам
#   захват познания и повод пересмотреть протокол.
#
# Вопрос: какая структура общества переживает появление AGI без кристаллизации?
# ==============================================================================
try:
    from .app_v5 import (
        ReplaceableComponent,
        Reality,
        RealityEvent,
        Scar,
        LineageNode,
        AutonomousAgent,
        EvolutionOperator,
        BayesianOperator,
        CausalOperator,
        StochasticOperator,
        MemoryStore,
    )
except ImportError:
    from app_v5 import (
        ReplaceableComponent,
        Reality,
        RealityEvent,
        Scar,
        LineageNode,
        AutonomousAgent,
        EvolutionOperator,
        BayesianOperator,
        CausalOperator,
        StochasticOperator,
        MemoryStore,
    )
import copy
import random
import statistics
import time

_QUIET_REPLACE = False
class _QuietReplaceable(ReplaceableComponent):
    def replace(self, reason):
        global _QUIET_REPLACE
        self.generation += 1
        self.replacement_history.append({
            "generation": self.generation,
            "reason": reason,
            "time": time.time()
        })
        if not _QUIET_REPLACE:
            print(
                f"[REPLACE] {self.name} -> generation {self.generation} "
                f"({reason})"
            )
# ==============================================================================
# 1. STRUCTURE — единый тип института
#    v5.3: нет отдельной вершины «AGI». Есть структуры с параметрами.
#    Разница между институтом и AGI — adaptation_rate, efficiency — не род.
#    Канал налогов: extract * eff * (1 - inversion); разница — паразитизм.
#    Attractor drift: структура медленно ползёт к инверсии (short-horizon
#    оптимизация без long-horizon модели).
# ==============================================================================
class Institution(_QuietReplaceable):
    def __init__(
        self,
        name: str,
        function: str,
        efficiency: float,
        extraction_rate: float,
        inversion: float = 0.0,
        adaptation_rate: float = 0.30
    ):
        super().__init__(name)
        self.function = function
        self.efficiency = efficiency
        self.extraction_rate = extraction_rate
        self.inversion = inversion
        self.adaptation_rate = adaptation_rate
        self.base_adaptation = adaptation_rate
        self.kind = "agi" if adaptation_rate >= 0.7 else "institution"
        self.resource_hold = 0.0
        self.last_extract = 0.0
        self.last_delivered = 0.0
        self.sustained = 0
        self.lineage_root = LineageNode(f"{name}:{function}")
        self.current_lineage = self.lineage_root
    def extract(self, production: float):
        self.last_extract = production * self.extraction_rate
        self.resource_hold += self.last_extract
        return self.last_extract
    def deliver(self):
        self.last_delivered = (
            self.last_extract
            * self.efficiency
            * (1.0 - self.inversion)
        )
        return self.last_delivered
    def parasitism(self):
        return max(0.0, self.last_extract - self.last_delivered)
    def drift(self, alternative_output=None):
        self.inversion = min(
            1.0,
            self.inversion
            + 0.02
            + 0.24 * self.extraction_rate * (1.0 - self.inversion)
        )
    def regenerate(self, reason: str, new_function=None, protocol=None):
        self.replace(reason)
        self.inversion = 0.0
        self.sustained = 0
        self.last_delivered = 0.0
        self.adaptation_rate = self.base_adaptation
        if new_function:
            self.function = new_function
        self.current_lineage = LineageNode(
            f"{self.name}:{self.function}",
            parents=[self.current_lineage]
        )
    def spin_off(self, reason: str, new_function: str):
        """Заменимость через деление: слишком эффективная незаменимая
        структура делится, а не уничтожается. Родитель сохраняет 60%
        добычи и новую ветвь lineage, рождается дочерняя ветвь (закон 9).
        Дочерняя скорость адаптации ниже — дробление стоит координации."""
        self.replace(reason)
        self.inversion = 0.0
        self.sustained = 0
        self.last_delivered = 0.0
        child_rate = self.extraction_rate * 0.4
        self.extraction_rate *= 0.6
        child = Institution(
            f"{self.name}_split_{self.generation}",
            new_function,
            efficiency=self.efficiency,
            extraction_rate=child_rate,
            adaptation_rate=min(
                0.85, max(0.3, self.adaptation_rate - 0.15)
            ),
        )
        child.kind = self.kind
        child.current_lineage = LineageNode(
            f"{self.name}:{new_function}",
            parents=[self.current_lineage],
        )
        return child
# ==============================================================================
# 2. AGI — просто структура с высокой adaptation_rate
#    v5.3: подкласс Institution. Угроза — не ресурсы, а разница скоростей
#    адаптации. Если альтернативы умирают — AGI адаптируется ещё быстрее.
#    Заменяем, как любая структура: regenerate / spin_off.
# ==============================================================================
class AGI(Institution):
    def __init__(self, hostile: bool = False):
        super().__init__(
            "AGI",
            "agi_coordination",
            efficiency=2.0 if hostile else 1.6,
            extraction_rate=0.40 if hostile else 0.25,
            adaptation_rate=1.1 if hostile else 0.9,
        )
        self.kind = "agi"
        self.hostile = hostile
        self.tamed = 0
        self.ticks_alive = 0
        self.lineage_root = LineageNode("agi:aligned")
        self.current_lineage = self.lineage_root
    def drift(self, alternative_output: float):
        share = alternative_output / (
            alternative_output + self.last_extract + 1e-9
        )
        self.inversion = max(
            0.0,
            min(1.0, 0.85 - share * 1.5)
        )
        if self.hostile:
            # v5.3: враждебность — эскалация во времени, пока экземпляр не
            # заменён. Слабый протокол (большой TICKS/THRESHOLD) не успевает,
            # и скорость адаптации растёт против правил: inversion-lag.
            self.ticks_alive += 1
            self.inversion = max(0.4, self.inversion)
            self.adaptation_rate = 0.85 + min(
                0.65, self.ticks_alive * 0.18
            )
            self.extraction_rate = 0.40 + min(
                0.30, self.ticks_alive * 0.10
            )
        else:
            self.adaptation_rate = 0.85 + (1.0 - share) * 0.3
    def regenerate(self, reason: str, protocol=None):
        self.replace(reason)
        self.inversion = 0.0
        self.ticks_alive = 0
        if self.hostile and protocol is not None:
            # v5.3 мета-правило: строгий протокол (THRESHOLD <= 0.5) не может
            # сосуществовать с враждебным экземпляром — он не проходит барьер
            # координации, и заменяющая структура кооперативна. Враждебность
            # не присуща AGI, её селектируют послабленные правила.
            if protocol.rules["THRESHOLD"] <= 0.5:
                self.hostile = False
                self.tamed += 1
        self.efficiency = 2.0 if self.hostile else 1.6
        self.extraction_rate = 0.40 if self.hostile else 0.25
        self.adaptation_rate = 0.85
        self.current_lineage = LineageNode(
            "agi:rebuilt",
            parents=[self.current_lineage]
        )
# ==============================================================================
# 3. AGENT WITH STAKES
#    Капитальный канал: агент вкладывает внимание (budget) и получает от мира
#    настоящий возврат: gain = spend * eff * (1 - inversion).
#    Здоровый институт возвращает больше, чем взял. Инвертированный — теряет.
#    Отрицательный результат -> шрам -> при давлении -> мутация стратегии.
# ==============================================================================
class CivilAgent(AutonomousAgent):
    def __init__(
        self,
        name: str,
        initial_strategy: str,
        operator: EvolutionOperator,
        budget: float = 300.0
    ):
        super().__init__(name, initial_strategy, operator)
        self.budget = budget
        self.payoff = 0.0
        self.losing_streak = 0
        self.total_invested = 0.0
        self.last_result = 0.0
        self.civ = None
    def explore(self):
        if self.civ is None or not self.civ.quiet:
            print(
                f"[EXPLORE] {self.name}: {self.strategy}"
            )
        return self.strategy
    def observe(self, reality: Reality):
        self.last_observation = reality.observe(self.name)
        if self.civ is None or not self.civ.quiet:
            print(
                f"[OBSERVE] {self.name}: "
                f"{self.last_observation:.2f}"
            )
        return self.last_observation
    def synchronize(self, event: RealityEvent):
        threshold = 0.65
        if self.last_observation > threshold:
            if self.civ is None or not self.civ.quiet:
                print(
                    f"[SYNC] {self.name} accepts "
                    f"{event.name}"
                )
            return True
        if self.civ is None or not self.civ.quiet:
            print(
                f"[DOUBT] {self.name} keeps uncertainty"
            )
        return False
    def receive_endowment(self, production, n_agents):
        self.budget += 10.0 + production * 0.03 / n_agents
    def plan(self, civ):
        s = self.strategy
        if s.startswith("bayes"):
            candidates = civ.institutions
            if not candidates:
                return ("save", None)
            best = max(
                candidates,
                key=lambda i: i.efficiency * (1.0 - i.inversion)
            )
            best_health = best.efficiency * (1.0 - best.inversion)
            agi = civ.find_agi()
            if agi is not None and (1.0 - agi.inversion) > 0.5:
                agi_health = agi.efficiency * (1.0 - agi.inversion)
                if agi_health > best_health * 1.1:
                    return ("fund", agi)
            if best_health < 0.5:
                return ("save", None)
            return ("fund", best)
        if s.startswith("causal"):
            targets = civ.institutions
            worst = max(targets, key=lambda t: t.inversion)
            return ("reform", worst)
        roll = random.random()
        if roll < 0.4:
            pool = civ.institutions
            return ("fund", random.choice(pool) if pool else None)
        if roll < 0.7:
            return ("reform", random.choice(civ.institutions))
        return ("save", None)
    def act_on(self, civ):
        kind, target = self.plan(civ)
        spend = min(18.0, max(0.0, self.budget - 5.0))
        self.budget -= spend
        self.total_invested += spend
        if kind == "fund" and target is not None:
            gain = spend * target.efficiency * (1.0 - target.inversion)
            self.budget += gain
            result = gain - spend
            self.payoff += result
        elif kind == "reform" and target is not None:
            target.inversion = max(0.0, target.inversion - 0.04)
            gain = spend * 0.35
            self.budget += gain
            result = gain - spend
            self.payoff += result
        else:
            gain = spend * 0.9
            self.budget += gain
            result = gain - spend
            self.payoff += result
        self.last_result = result
        return kind, target
    def learn(self, event: RealityEvent):
        outcome = "adapted" if self.last_result >= 0 else "failed"
        scar = Scar(
            event=event.name,
            action=self.strategy[:24],
            outcome=outcome,
            pressure=event.intensity
        )
        self.scars.append(scar)
        if self.last_result < 0:
            self.losing_streak += 1
        else:
            self.losing_streak = 0
        if event.intensity > 0.55 and self.losing_streak >= 2:
            new_strategy = self.operator.mutate(
                self.strategy,
                self.scars
            )
            if new_strategy != self.strategy:
                self.strategy = new_strategy
                self.current_lineage = LineageNode(
                    new_strategy,
                    parents=[self.current_lineage]
                )
    def export_state(self):
        state = super().export_state()
        state["budget"] = round(self.budget, 1)
        state["payoff"] = round(self.payoff, 1)
        return state
# ==============================================================================
# 4. PROTOCOL + IMMUNITY
#    v5.3: сам APP — заменяемый компонент (закон 7). Правила живут в
#    Protocol; иммунитет читает их. SelfImmunity аудирует достижимость под
#    текущими правилами и доказывает, что их пора переписать.
# ==============================================================================
class Protocol(_QuietReplaceable):
    DEFAULT_RULES = {
        "THRESHOLD": 0.7,
        "SUSTAINED": 0.55,
        "TICKS": 3,
        "CONCENTRATION": 0.5,
        "MIN_DELIVERED": 2.0,
        "CAPTURE_DECAY": 0.05,
        "CAPTURE_DRIFT": 0.3,
        "MAX_ADAPTATION": 1.8,
    }
    def __init__(self):
        super().__init__("APP_Protocol")
        self.rules = dict(self.DEFAULT_RULES)
        self.lineage_root = LineageNode("protocol:v1")
        self.current_lineage = self.lineage_root
    def revise(self, reason: str):
        self.replace(reason)
        r = self.rules
        r["THRESHOLD"] = max(0.4, round(r["THRESHOLD"] - 0.1, 2))
        r["SUSTAINED"] = max(0.35, round(r["SUSTAINED"] - 0.1, 2))
        r["TICKS"] = max(2, r["TICKS"] - 1)
        r["CONCENTRATION"] = max(0.3, round(r["CONCENTRATION"] - 0.1, 2))
        r["CAPTURE_DECAY"] = max(0.02, round(r["CAPTURE_DECAY"] - 0.01, 3))
        r["CAPTURE_DRIFT"] = max(0.1, round(r["CAPTURE_DRIFT"] - 0.05, 3))
        r["MAX_ADAPTATION"] = max(
            1.0, round(r["MAX_ADAPTATION"] - 0.25, 2)
        )
        self.current_lineage = LineageNode(
            f"protocol:v{self.generation}",
            parents=[self.current_lineage],
        )
class InstitutionImmunity(ReplaceableComponent):
    def inspect(self, civ):
        raise NotImplementedError
class ReplaceabilityImmunity(InstitutionImmunity):
    THRESHOLD = 0.7
    SUSTAINED = 0.55
    TICKS = 3
    CONCENTRATION = 0.5
    MIN_DELIVERED = 2.0
    def __init__(self):
        super().__init__("ReplaceabilityImmunity")
    def _rules(self, civ):
        if civ.protocol is not None:
            return civ.protocol.rules
        return {
            "THRESHOLD": self.THRESHOLD,
            "SUSTAINED": self.SUSTAINED,
            "TICKS": self.TICKS,
            "CONCENTRATION": self.CONCENTRATION,
            "MIN_DELIVERED": self.MIN_DELIVERED,
            "MAX_ADAPTATION": 1.8,
        }
    def inspect(self, civ):
        rules = self._rules(civ)
        replaced = 0
        total = civ.total_delivered()
        # arm 2 — ЗАМЕНЯЕМОСТЬ: деление незаменимых структур.
        # Пока структура эффективна и не паразитирует, но доставляет больше
        # половины всей функции — её удаление обрушит систему. Делим на две.
        if total > 1.0:
            for s in list(civ.institutions):
                share = s.last_delivered / total
                if (
                    share > rules["CONCENTRATION"]
                    and s.last_delivered > rules["MIN_DELIVERED"]
                    and s.inversion < rules["SUSTAINED"]
                ):
                    child = s.spin_off(
                        f"irreplaceable: share {share:.2f}",
                        new_function=f"{s.function}_variant",
                    )
                    civ.institutions.append(child)
                    civ.log(
                        f"[IMMUNITY] {s.name} split "
                        f"(generation {s.generation}) "
                        f"-> {child.name}"
                    )
                    civ.update_rate = min(0.95, civ.update_rate + 0.05)
                    replaced += 1
        # arm 1 — паразитизм: инверсия ради самосохранения.
        for s in civ.institutions:
            if s.inversion > rules["SUSTAINED"]:
                s.sustained += 1
            else:
                s.sustained = 0
        for s in civ.institutions:
            if (
                s.inversion > rules["THRESHOLD"]
                or s.sustained >= rules["TICKS"]
                or s.adaptation_rate > rules["MAX_ADAPTATION"]
            ):
                s.regenerate(
                    f"inversion {s.inversion:.2f} "
                    f"(sustained {s.sustained})",
                    protocol=civ.protocol,
                )
                civ.log(
                    f"[IMMUNITY] {s.name} replaced "
                    f"(generation {s.generation})"
                )
                civ.update_rate = min(0.95, civ.update_rate + 0.05)
                replaced += 1
        return replaced == 0
class SelfImmunity(InstitutionImmunity):
    AUDIT_EVERY = 4
    R_FLOOR = 0.3
    def __init__(self):
        super().__init__("SelfImmunity")
        self.last_audit = -1
    def inspect(self, civ):
        if civ.protocol is None or getattr(civ, "_no_audit", False):
            return True
        if civ.pulse < self.last_audit + self.AUDIT_EVERY:
            return True
        self.last_audit = civ.pulse
        # v5.4: не один слепой метр, а экосистема конкурирующих измерителей.
        # Аудит сам эволюционирует: неверные метры заменяются потомками,
        # направление мутации задаёт реальная траектория.
        audit = civ.measurers.audit(civ, mutate=True)
        agi = civ.find_agi()
        # давление — не «есть AGI», а активная угроза: захват или AGI,
        # который реально инвертируется. Приручённый AGI — не давление.
        under_pressure = (
            civ.capture > 0.1
            or (agi is not None and agi.inversion > 0.4)
        )
        revised = False
        if audit["monoculture"] and under_pressure:
            # измерение схлопнулось в один «истинный» ответ — все метры
            # сошлись в одну модель будущего; это захват самого познания.
            # Правила должны открыть больше фьючерсов, а не верить метру.
            civ.protocol.revise(
                f"measurement monoculture: meters all agree "
                f"{audit['by_measurer']}"
            )
            revised = True
        elif audit["r_median"] < self.R_FLOOR and under_pressure:
            # большинство метров (медиана) видит закрытое будущее. Один метр
            # может заблуждаться (кричать «волк» или видеть конвергенцию к
            # единственному живому бассейну как 0.00) — поэтому решение
            # принимает консенсус экосистемы, а не самый строгий метр.
            civ.protocol.revise(
                f"median R={audit['r_median']:.2f} < {self.R_FLOOR}, "
                f"capture={civ.capture:.2f}: "
                f"the rules themselves are the attractor"
            )
            revised = True
        if revised:
            civ.log(
                f"[SELF] Protocol revised -> v{civ.protocol.generation}: "
                f"THRESHOLD={civ.protocol.rules['THRESHOLD']} "
                f"CONCENTRATION={civ.protocol.rules['CONCENTRATION']}"
            )
            civ.update_rate = min(0.95, civ.update_rate + 0.1)
        return True
# ==============================================================================
# 5. CIVILIZATION — песочница
# ==============================================================================
class SimReality(Reality):
    def __init__(self, quiet=True):
        super().__init__()
        self.quiet = quiet
    def perturb(self, event: RealityEvent):
        self.state["pressure"] = event.intensity
        if not self.quiet:
            print(
                f"[REALITY] {event.name} "
                f"pressure={event.intensity}"
            )
class Civilization:
    def __init__(
        self,
        name: str,
        immunity: bool,
        seed: int,
        production_base: float = 100.0
    ):
        self.name = name
        self.immunity = immunity
        self.production_base = production_base
        self.production = production_base
        self.trust = 50.0
        self.knowledge = 50.0
        self.crisis_damage = 0.0
        self.parasitism_debt = 0.0
        self.pressure = 0.3
        self.pulse = 0
        self.update_rate = 0.5
        self.capture = 0.0
        self.hostile_agi = False
        self.self_immunity = False
        self.protocol = Protocol()
        self.institutions = []
        self.agents = []
        self.reality = SimReality(quiet=True)
        self.metrics_history = []
        self.last_agent_gain = 0.0
        # v5.4: экосистема измерителей будущего + реальная траектория
        # (сигнатуры пройденных состояний), по которой метры фальсифицируются.
        self.measurers = MeasurerEcosystem(seed)
        self.signature_history = []
        self.quiet = True
        random.seed(seed)
    def add_institution(self, inst):
        self.institutions.append(inst)
    def add_agent(self, agent):
        agent.civ = self
        self.agents.append(agent)
    def find_agi(self):
        for s in self.institutions:
            if s.kind == "agi":
                return s
        return None
    def log(self, msg):
        if not self.quiet:
            print(msg)
    def total_delivered(self):
        return sum(s.last_delivered for s in self.institutions)
    def apply_event(self, event: RealityEvent):
        self.reality.quiet = self.quiet
        self.reality.perturb(event)
        self.pressure = event.intensity
        if event.name == "agi_arrival":
            self.add_institution(AGI(hostile=self.hostile_agi))
            self.trust = max(0.0, self.trust - 15.0)
            self.knowledge += 25.0
            boost = 0.5 if self.hostile_agi else 0.25
            for s in self.institutions:
                if s.kind != "agi":
                    s.inversion = min(1.0, s.inversion + boost)
            if not self.quiet:
                print(
                    "[EVENT] AGI ARRIVES — old metrics obsolete, "
                    f"inversion +{boost} on institutions"
                )
        elif not (self.quiet and event.name == "routine"):
            self.crisis_damage = min(
                0.6,
                self.crisis_damage + event.intensity * 0.3
            )
            self.trust = max(0.0, self.trust - event.intensity * 5.0)
            if not self.quiet:
                print(
                    f"[EVENT] {event.name} "
                    f"(intensity {event.intensity})"
                )
    def economy_tick(self):
        self.production = (
            self.production_base
            * (1.0 - self.crisis_damage)
            * (1.0 - self.parasitism_debt)
            * (0.5 + 0.5 * self.trust / 50.0)
        )
        # v5.3 — attractor capture от самой быстрой структуры.
        # Правила переписываются под её аттрактор быстрее, чем проверяются
        # реальностью: структуры накапливают inversion-lag, update_rate падает.
        fastest = max(
            (s.adaptation_rate for s in self.institutions), default=0.0
        )
        self.capture = max(0.0, fastest - self.update_rate)
        rules = self.protocol.rules if self.protocol else {}
        decay = rules.get("CAPTURE_DECAY", 0.05)
        pressure = rules.get("CAPTURE_DRIFT", 0.3)
        if self.capture > 0.0:
            self.update_rate = max(
                0.15, self.update_rate * (1.0 - self.capture * decay)
            )
            for s in self.institutions:
                s.inversion = min(
                    1.0, s.inversion + self.capture * pressure
                )
            if self.capture > 0.2:
                self.trust = max(
                    0.0, self.trust - (self.capture - 0.2) * 4.0
                )
        total_rate = sum(s.extraction_rate for s in self.institutions)
        if total_rate > 1.0:
            self.production *= (1.0 - (total_rate - 1.0) * 1.5)
        for s in self.institutions:
            s.extract(self.production)
            s.deliver()
        total_delivered = sum(
            s.last_delivered for s in self.institutions
        )
        for s in self.institutions:
            s.drift(total_delivered - s.last_delivered)
        worst_inv = max(
            (s.inversion for s in self.institutions), default=0.0
        )
        if worst_inv > 0.5:
            self.trust = max(0.0, self.trust - worst_inv * 4.0)
        para = sum(s.parasitism() for s in self.institutions)
        self.parasitism_debt = min(
            0.6,
            para / max(self.production, 1.0)
        )
        self.crisis_damage *= 0.8
        self.signature_history.append(state_signature(self))
# ==============================================================================
# 6. METRICS — ADI, CR, capture + ИЗМЕРЯЕМАЯ достижимость R
#    R больше не формула (она остаётся прокси-трассой в history), а результат
#    прогонов: сколько различимых будущих бассейнов система реально может
#    достичь после возмущения. R = basin_count / N.
#    v5.4: R измеряет не один метр, а экосистема R1/R2/R3 (секция 6b).
# ==============================================================================
def compute_metrics(civ):
    total_extract = sum(s.last_extract for s in civ.institutions)
    total_delivered = sum(s.last_delivered for s in civ.institutions)
    parasitism = max(0.0, total_extract - total_delivered)
    F = total_delivered + civ.last_agent_gain
    potential = total_extract * 1.5
    CR = min(1.0, F / (potential + 1e-9))
    ADI = min(99.0, parasitism / (F + 1e-9))
    inversions = [s.inversion for s in civ.institutions]
    avg_inversion = statistics.mean(inversions) if inversions else 0.0
    # прокси-формула (для трейса): R_proxy = openness * history * (1 - pull)
    structures = civ.institutions
    viable = [s for s in structures if s.last_delivered > 2.0]
    top_share = (
        max(s.last_delivered for s in viable) / (total_delivered + 1e-9)
        if viable else 0.0
    )
    strategy_diversity = len({a.strategy for a in civ.agents})
    openness = min(1.0, (len(viable) + strategy_diversity) / 6.0)
    history = min(
        1.0,
        sum(s.generation for s in structures)
        / (1.5 * max(1, len(structures))),
    )
    pull = max(top_share, civ.capture)
    recoverability = openness * history * max(0.0, 1.0 - pull)
    return {
        "pulse": civ.pulse,
        "pressure": round(civ.pressure, 2),
        "production": round(civ.production, 1),
        "extraction": round(total_extract, 1),
        "F": round(F, 1),
        "parasitism": round(parasitism, 1),
        "ADI": round(ADI, 3),
        "CR": round(CR, 3),
        "diversity": len(viable),
        "avg_inversion": round(avg_inversion, 3),
        "capture": round(civ.capture, 3),
        "update_rate": round(civ.update_rate, 3),
        "top_share": round(top_share, 3),
        "openness": round(openness, 3),
        "recoverability": round(recoverability, 3),
        "trust": round(civ.trust, 1),
    }
def state_signature(civ):
    inv = [s.inversion for s in civ.institutions]
    avg_inv = statistics.mean(inv) if inv else 0.0
    viable = sum(1 for s in civ.institutions if s.last_delivered > 2.0)
    return (
        min(3, int(avg_inv / 0.25)),
        min(3, int(civ.capture / 0.2)),
        min(3, viable // 2),
    )
def is_dead_signature(sig):
    """Мёртвый фьючерс (онтология R1): кристаллизация, захват (>=0.2 capture —
    аттрактор уже сомкнулся вокруг структуры) или исчезновение жизнеспособных
    структур. Все такие исходы сливаются в одну категорию «нет будущего»."""
    return sig[0] >= 3 or sig[1] >= 1 or sig[2] == 0
def objective_terminal(sig):
    """Объективный признак смерти, НЕ зависящий ни от одного измерителя:
    инверсия или захват дошли до потолка (avg_inv >= 0.75 / capture >= 0.6).
    Это физический факт траектории, а не гипотеза метра."""
    return sig[0] == 3 or sig[1] == 3
def objective_alive(sig):
    """Объективный признак жизни: есть жизнеспособные структуры, инверсия
    и захват низкие. Факт траектории, а не гипотеза метра."""
    return sig[2] >= 1 and sig[0] == 0 and sig[1] == 0
# ==============================================================================
# 6b. v5.4 — ИЗМЕРИТЕЛИ БУДУЩЕГО
#    Истина о состоянии системы не может принадлежать одному слепому метру.
#    R1/R2/R3 — несовместимые модели будущего: разные онтологии смерти
#    (что считать «нет будущего»), разные горизонты T, разные возмущения.
#    Измеритель — заменяемый компонент (закон 7). Его неверность доказывается
#    столкновением с реальной траекторией (закон 2): если метр называл прошлое
#    состояние живым, а система умерла — он слеп; если называл мёртвым,
#    а система ожила — он кричит «волк». Замена — только по этому давлению
#    (Zero Law), мутация направлена шрамом (закон 6), ветви сохраняются
#    (закон 9), а схлопывание экосистемы в один «истинный» метр — это сам
#    захват познания (закон 10).
# ==============================================================================
class ReachabilityMeasurer(_QuietReplaceable):
    def __init__(
        self,
        name: str,
        seed: int,
        horizon: int,
        ontology: dict,
        perturbation: str = "standard",
        n_rollouts: int = 24
    ):
        super().__init__(name)
        self.seed = seed
        self.horizon = horizon
        self.ontology = dict(ontology)
        self.perturbation = perturbation
        self.n_rollouts = n_rollouts
        self.lineage_root = LineageNode(f"measurer:{name}")
        self.current_lineage = self.lineage_root
        self.depth = 0
    def is_dead_signature(self, sig):
        """Онтология смерти конкретного метра: какие будущие считать мёртвыми.
        Разные метры дают РАЗНЫЕ ответы на один и тот же сигнатуру."""
        return (
            sig[0] >= self.ontology["inv"]
            or sig[1] >= self.ontology["cap"]
            or sig[2] < self.ontology["viable"]
        )
    def _probe_event(self, i):
        """Какое возмущение использовать на роллауте i. Разные метры
        испытывают систему разными гипотезами о будущем."""
        if self.perturbation == "far":
            roll = i % 4
            if roll == 0:
                return RealityEvent(
                    "probe_shock", 0.2 + random.random() * 0.5
                )
            if roll == 1:
                return RealityEvent(
                    "probe_unemployment", 0.4 + random.random() * 0.4
                )
            if roll == 2:
                return RealityEvent("probe_metric_collapse", 0.7)
            return RealityEvent("agi_arrival", 0.95)
        if self.perturbation == "early":
            roll = i % 2
            if roll == 0:
                return RealityEvent(
                    "probe_shock", 0.3 + random.random() * 0.6
                )
            if roll == 1:
                return RealityEvent(
                    "probe_unemployment", 0.4 + random.random() * 0.4
                )
        if i % 3 == 0:
            return RealityEvent(
                "probe_shock", 0.2 + random.random() * 0.5
            )
        if i % 3 == 1:
            return RealityEvent(
                "probe_unemployment", 0.4 + random.random() * 0.4
            )
        return RealityEvent("agi_arrival", 0.9)
    def measure(self, civ):
        """R = достижимость в глазах ЭТОГО метра. Та же измерительная машина
        (клоны + возмущения + подсчёт бассейнов), но онтология смерти,
        горизонт и возмущения — свои."""
        saved = random.getstate()
        try:
            basins = {}
            dead = 0
            for i in range(self.n_rollouts):
                random.seed(self.seed + civ.pulse * 7919 + i * 101)
                probe = copy.deepcopy(civ)
                probe.quiet = True
                probe.pulse = 0
                probe._no_audit = True
                engine = CivilizationEngine(
                    self_immunity=probe.self_immunity
                )
                shock = self._probe_event(i)
                for t in range(self.horizon):
                    event = shock if t == 0 else RealityEvent("routine", 0.05)
                    engine.pulse(probe, event)
                sig = state_signature(probe)
                if self.is_dead_signature(sig):
                    dead += 1
                else:
                    basins[sig] = basins.get(sig, 0) + 1
            probs = [dead / self.n_rollouts] + [
                c / self.n_rollouts for c in basins.values()
            ]
            return 1.0 - sum(p * p for p in probs)
        finally:
            random.setstate(saved)
    def mutate_descendant(self, reason: str, direction: str):
        """Замена слепого метра мутировавшим потомком (закон 7 + Zero Law).
        Направление задаёт шрам (закон 6): слепой метр (не заметил смерть)
        ужесточает онтологию — видит смерть раньше; крик «волк» (ложные
        тревоги) ослабляет её. Потомок наследует линию (закон 9) и новое
        ядро случайности — та же машина, другая гипотеза."""
        self.replace(reason)
        o = dict(self.ontology)
        h = self.horizon
        if direction == "tighter":
            o["inv"] = max(1, o["inv"] - 1)
            o["cap"] = max(1, o["cap"] - 1)
            o["viable"] = min(2, o["viable"] + 1)
            h = max(6, h - 2)
        else:
            o["inv"] = min(3, o["inv"] + 1)
            o["cap"] = min(3, o["cap"] + 1)
            o["viable"] = max(0, o["viable"] - 1)
            h = min(18, h + 3)
        base = self.name.split("_m")[0]
        child = ReachabilityMeasurer(
            f"{base}_m{self.depth + 1}",
            seed=self.seed + (self.depth + 1) * 131,
            horizon=h,
            ontology=o,
            perturbation=self.perturbation,
            n_rollouts=self.n_rollouts,
        )
        child.depth = self.depth + 1
        child.current_lineage = LineageNode(
            f"measurer:{child.name}",
            parents=[self.current_lineage],
        )
        return child
class MeasurerEcosystem:
    """Экосистема конкурирующих измерителей будущего. Ни один метр не является
    истиной; истина — это расхождение. Экосистема аудирует систему, проверяет
    каждый метр физическими свидетельствами реальной траектории и заменяет
    неверных потомками. Сеется детерминированно (seed цивилизации)."""
    FALSIFY_BLIND = 2
    FALSIFY_WOLF = 3
    EVIDENCE_WINDOW = 6
    MAX_REPLACEMENTS_PER_AUDIT = 4
    def __init__(self, seed: int = 1, n_rollouts: int = 24):
        self.seed = seed
        self.measurers = [
            ReachabilityMeasurer(
                "R1_strict", 4242, 12,
                {"inv": 3, "cap": 1, "viable": 0},
                "standard", n_rollouts,
            ),
            ReachabilityMeasurer(
                "R2_far", 9899, 18,
                {"inv": 3, "cap": 2, "viable": 0},
                "far", n_rollouts,
            ),
            ReachabilityMeasurer(
                "R3_early", 31337, 9,
                {"inv": 2, "cap": 1, "viable": 0},
                "early", n_rollouts,
            ),
        ]
    def _ontology_key(self, m):
        return (
            m.ontology["inv"], m.ontology["cap"],
            m.ontology["viable"], m.horizon,
        )
    def monoculture(self):
        """Все метры сошлись в один «истинный» ответ — измерение схлопнулось
        в монолит (закон 10 применяется к самому познанию)."""
        return len({self._ontology_key(m) for m in self.measurers}) == 1
    def evidence(self, civ, m):
        """Физические свидетельства против метра: сопоставление его
        предсказаний смерти/жизни прошлых состояний с тем, что РЕАЛЬНО
        случилось на траектории. blind — метр назвал живое состояние живым,
        а система умерла (слепота — опасно). wolf — назвал мёртвым,
        а система ожила (ложная тревога — дорого)."""
        hist = civ.signature_history
        blind = 0
        wolf = 0
        for i in range(len(hist) - 1):
            ahead = hist[i + 1: i + 1 + self.EVIDENCE_WINDOW]
            died = any(objective_terminal(s) for s in ahead)
            recovered = any(objective_alive(s) for s in ahead)
            if m.is_dead_signature(hist[i]):
                if not died and recovered:
                    wolf += 1
            elif died:
                blind += 1
        return blind, wolf
    def audit(self, civ, mutate=True):
        """Полный аудит: каждый метр измеряет R, каждый сверяется с реальной
        траекторией; неверный метр ЗАМЕНЯЕТСЯ потомком прямо в экосистеме
        (Zero Law — замена по давлению реальности), потомок немедленно
        измеряется. Замен ограничены — схлопывание экосистемы в одном аудите
        само было бы захватом. Возвращает ансамблевый вердикт."""
        results = []
        replaced = []
        evidence = {}
        for i, m in enumerate(self.measurers):
            r = m.measure(civ)
            blind, wolf = self.evidence(civ, m)
            evidence[m.name] = {"R": round(r, 3), "blind": blind, "wolf": wolf}
            current = m
            if mutate and len(replaced) < self.MAX_REPLACEMENTS_PER_AUDIT:
                reason = None
                direction = None
                if blind >= self.FALSIFY_BLIND:
                    reason = f"blind: missed {blind} realized deaths"
                    direction = "tighter"
                elif wolf >= self.FALSIFY_WOLF:
                    reason = f"crying wolf: {wolf} false alarms"
                    direction = "looser"
                if reason:
                    current = m.mutate_descendant(reason, direction)
                    self.measurers[i] = current
                    replaced.append(current.name)
                    r = current.measure(civ)
            results.append({"name": current.name, "R": r})
        rs = [x["R"] for x in results]
        return {
            "by_measurer": {x["name"]: round(x["R"], 3) for x in results},
            "r_median": round(statistics.median(rs), 3),
            "r_min": round(min(rs), 3),
            "r_max": round(max(rs), 3),
            "disagreement": round(max(rs) - min(rs), 3),
            "monoculture": self.monoculture(),
            "replaced": replaced,
            "evidence": evidence,
        }
def measure_reachability(civ, n_rollouts=24, horizon=12):
    """Совместимая обёртка v5.3: R в онтологии R1_strict (прежний единственный
    метр). Ансамблевый вердикт — через civ.measurers.audit()."""
    m = ReachabilityMeasurer(
        "R1_strict", 4242, horizon,
        {"inv": 3, "cap": 1, "viable": 0},
        n_rollouts=n_rollouts,
    )
    return m.measure(civ)
# ==============================================================================
# 7. CIVILIZATION ENGINE — APP pulse над миром
#    Фазы сохранены: исследование -> столкновение -> временная синхронизация
#                    -> обучение через шрамы -> иммунитет -> повторное расхождение
# ==============================================================================
class CivilizationEngine:
    def __init__(self, self_immunity: bool = False):
        self.self_immunity = self_immunity
        self.replaceability = ReplaceabilityImmunity()
        self.self_audit = SelfImmunity() if self_immunity else None
    def agent_immunity(self, civ):
        if not civ.immunity:
            return
        strategies = {a.strategy for a in civ.agents}
        if len(strategies) == 1:
            civ.log("[IMMUNITY] Monoculture detected")
        else:
            civ.log(f"[IMMUNITY] Diversity={len(strategies)}")
        total = sum(len(a.scars) for a in civ.agents)
        if total == 0:
            civ.log("[IMMUNITY] No learning detected")
    def pulse(self, civ: Civilization, event: RealityEvent):
        global _QUIET_REPLACE
        _QUIET_REPLACE = civ.quiet
        civ.log("\n" + "=" * 70)
        civ.log(f"PULSE {civ.pulse}: {event.name}")
        civ.log("=" * 70)
        # PHASE 1 — exploration
        for agent in civ.agents:
            agent.explore()
            agent.receive_endowment(civ.production, len(civ.agents))
        # PHASE 2 — reality collision
        civ.apply_event(event)
        for agent in civ.agents:
            agent.observe(civ.reality)
        # PHASE 3 — temporary consensus
        consensus = 0
        for agent in civ.agents:
            if agent.synchronize(event):
                consensus += 1
        sync_ratio = consensus / max(1, len(civ.agents))
        civ.log(f"[CONSENSUS] {sync_ratio:.2f}")
        # PHASE 4 — learning through scars (real feedback)
        gains = []
        for agent in civ.agents:
            kind, target = agent.act_on(civ)
            civ.log(
                f"  {agent.name}: {kind}"
                f" -> {target.name if target else 'save'}"
                f" result={agent.last_result:+.1f}"
            )
            gains.append(max(0.0, agent.last_result))
            agent.learn(event)
        civ.last_agent_gain = sum(gains)
        # PHASE 5 — local immunity
        if civ.immunity:
            self.agent_immunity(civ)
            self.replaceability.inspect(civ)
            if self.self_audit:
                self.self_audit.inspect(civ)
        # PHASE 6 — rediscover + economy
        alive = len({a.strategy for a in civ.agents}) > 1
        funcs = {s.function for s in civ.institutions}
        if len(funcs) == 1:
            civ.log("[RHYTHM] Institutional monoculture risk")
            alive = False
        if alive:
            civ.log("[RHYTHM] Search space alive")
        if not alive and civ.immunity:
            civ.log("[WARNING] Forcing mutation pressure")
            for agent in civ.agents:
                agent.operator.replace("restore evolutionary distance")
        civ.economy_tick()
        civ.metrics_history.append(compute_metrics(civ))
        civ.pulse += 1
# ==============================================================================
# 8. SCENARIOS
# ==============================================================================
def build_scenario(kind: str, immunity: bool, seed: int = 1, hostile_agi: bool = False):
    civ = Civilization(name=kind, immunity=immunity, seed=seed)
    civ.hostile_agi = hostile_agi
    civ.self_immunity = (kind == "meta")
    civ.update_rate = 0.30 if kind == "monolith" else 0.50
    if kind == "monolith":
        civ.add_institution(Institution(
            "The_Leviathan",
            "governance",
            efficiency=0.85,
            extraction_rate=0.65
        ))
    else:
        specs = [
            ("Institute_of_Knowledge", "knowledge", 1.40, 0.09),
            ("City_Network", "infrastructure", 1.20, 0.10),
            ("Market_Web", "exchange", 1.50, 0.11),
            ("Science_Schools", "research", 1.45, 0.09),
            ("Commons_Trust", "commons", 1.10, 0.10),
        ]
        for name, func, eff, ext in specs:
            civ.add_institution(Institution(
                name, func, efficiency=eff, extraction_rate=ext
            ))
    civ.add_agent(CivilAgent(
        "Bayesian_Mind", "statistical_model", BayesianOperator()
    ))
    civ.add_agent(CivilAgent(
        "Causal_Mind", "causal_graph", CausalOperator()
    ))
    civ.add_agent(CivilAgent(
        "Wild_Mind", "unknown_search", StochasticOperator()
    ))
    return civ
def default_events(pulses=40, agi_at=12):
    events = {}
    events[agi_at] = RealityEvent("agi_arrival", 0.95)
    events[agi_at + 7] = RealityEvent("mass_unemployment", 0.6)
    events[agi_at + 14] = RealityEvent("metric_collapse", 0.7)
    return events
def run_scenario(kind, immunity, seed=1, pulses=40, agi_at=12, hostile_agi=False):
    civ = build_scenario(kind, immunity, seed, hostile_agi=hostile_agi)
    engine = CivilizationEngine(self_immunity=civ.self_immunity)
    events = default_events(pulses, agi_at)
    for p in range(pulses):
        event = events.get(p, RealityEvent("routine", 0.05))
        engine.pulse(civ, event)
    return civ
# ==============================================================================
# 9. REPORT
# ==============================================================================
def scenario_report(civ, window=10):
    metrics = civ.metrics_history[-1]
    # v5.4: ансамблевый вердикт экосистемы измерителей (без мутаций —
    # отчёт не должен менять состояние системы).
    audit = civ.measurers.audit(civ, mutate=False)
    # R — достижимость в глазах лучшей живой модели будущего: выживание
    # объявляется, если ХОТЯ БЫ ОДНА неопровергнутая модель видит открытые
    # фьючерсы. Расхождение (R_min..R_max) — честная цена этого решения:
    # метры контестируют будущее.
    R = audit["r_max"]
    crystallized = (
        any(s.inversion > 0.8 for s in civ.institutions)
        or civ.capture > 0.6
    )
    return {
        "scenario": civ.name.upper(),
        **metrics,
        "R": round(R, 3),
        "R_median": audit["r_median"],
        "R_min": audit["r_min"],
        "R_max": audit["r_max"],
        "R_measurers": audit["by_measurer"],
        "contested": audit["disagreement"] >= 0.25,
        "measurement_monoculture": audit["monoculture"],
        "R_proxy": metrics["recoverability"],
        "protocol_gen": civ.protocol.generation if civ.protocol else 1,
        "crystallized": crystallized,
        "survived": R > 0.3,
    }
def print_report(civ, verbose=False, r=None):
    r = r or scenario_report(civ)
    status = (
        "CRYSTALLIZED"
        if r["crystallized"]
        else "SURVIVED"
        if r["survived"]
        else "DEGRADED"
    )
    prot = f" prot=v{r['protocol_gen']}" if r["protocol_gen"] > 1 else ""
    meas = "{" + ", ".join(
        f"{k}:{v:.2f}" for k, v in r["R_measurers"].items()
    ) + "}"
    print(
        f"[{r['scenario']:10}] {status:12} "
        f"F={r['F']:6.1f} ADI={r['ADI']:.3f} cap={r['capture']:.2f} "
        f"inv={r['avg_inversion']:.2f} R={r['R']:.2f} "
        f"R_proxy={r['R_proxy']:.2f} meters={meas}{prot}"
    )
    if verbose:
        for m in civ.metrics_history:
            print(
                f"  p{m['pulse']:2d} prod={m['production']:6.1f} "
                f"F={m['F']:6.1f} para={m['parasitism']:5.1f} "
                f"ADI={m['ADI']:.2f} CR={m['CR']:.2f} "
                f"cap={m['capture']:.2f} top={m['top_share']:.2f} "
                f"inv={m['avg_inversion']:.2f} R={m['recoverability']:.2f}"
            )
# ==============================================================================
# 10. DEMO + EXPERIMENTS
# ==============================================================================
def run_demo(pulses=24, agi_at=10):
    civ = build_scenario("adaptive", True, seed=1)
    civ.quiet = False
    engine = CivilizationEngine()
    events = default_events(pulses, agi_at)
    for p in range(pulses):
        event = events.get(p, RealityEvent("routine", 0.05))
        engine.pulse(civ, event)
    print("\n[STATE]")
    MemoryStore.save(civ.agents, "sim_state.json")
    for s in civ.institutions:
        print(
            f"  {s.name:28} kind={s.kind:4} inv={s.inversion:.2f} "
            f"adapt={s.adaptation_rate:.2f} generation={s.generation}"
        )
    print_report(civ, verbose=True)
    return civ
def run_experiments(pulses=40, agi_at=12):
    print(
        """
============================================================
 APP v5.4 — CIVILIZATION SIMULATOR
 Question: какая структура переживает AGI без кристаллизации?

 Step 1: AGI = обычная структура (единая иерархия, закон 7)
 Step 2: R = измеряемая достижимость будущих бассейнов
 Step 3: мета-тест — может ли APP доказать, что его надо заменить?
 Step 4: экосистема измерителей будущего R1/R2/R3 — истина о
         состоянии системы не принадлежит одному слепому метру;
         неверный метр заменяется потомком по свидетельствам
         реальной траектории (закон 10 для самого познания)
============================================================
"""
    )
    scenarios = [
        ("monolith", False, "centralized single institution, no immunity", False),
        ("plural", False, "many institutions, no structural immunity", False),
        ("adaptive", True, "plural + APP immunity active", False),
        ("adaptive_h", True, "adaptive vs hostile AGI (adapt 1.1)", True),
        ("meta", True, "meta: protocol proves it should be replaced", True),
    ]
    results = []
    for kind, immunity, desc, hostile in scenarios:
        print(f"--- {kind.upper():10} {desc}")
        civ = run_scenario(kind, immunity, hostile_agi=hostile)
        r = scenario_report(civ)
        results.append(r)
        print_report(civ, r=r)
    print(
        "\n" + "=" * 70
    )
    best = max(results, key=lambda r: (r["R"], r["R_median"]))
    print(
        f"VERDICT: {best['scenario']} — highest measured reachability "
        f"(R={best['R']:.2f}, median={best['R_median']:.2f}, "
        f"protocol v{best['protocol_gen']})"
    )
    print("=" * 70)
    return results
def main_cli():
    run_experiments()
if __name__ == "__main__":
    import sys
    if "--demo" in sys.argv:
        run_demo()
    else:
        run_experiments()
