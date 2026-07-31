# ADAPTIVE PLURALISM PROTOCOL — SPECIFICATION 1.0

**Status:** Canon candidate (RFC-level)
**Type:** Invariants → implementations
**Basis:** *General Theory of Systemic Irreversibility and Civilizational Recoverability* (0penAGI, v3, July 2026)
**Predecessor:** CIRM (Civilization Immune Response Model)

---

## 0. Purpose

Every living system degrades. This cannot be prevented — it can only be kept
*reversible*.

The protocol does not describe *how* a society, a system or a civilization is
organized. It forbids one thing: the conversion of any configuration into a
*permanent* state.

The document is built from invariants to implementations, like POSIX or RFC:
first — the laws that must not be violated; then — any implementations that
may change as long as they preserve the invariants.

There is one criterion for checking any code:

> Does it violate any of these laws?

Not "does it match the previous version", but "does it violate an invariant".

---

## 1. The twelve laws

### 1. Zero Law

> Any mechanism is replaceable, but nothing is replaced without sufficient pressure from reality.

Replacement is not an ideology. The pressure of reality is the only legitimate
basis for replacement. Everything else is replacement for its own sake, that
is, degradation.

### 2. Reality First

> Truth is not stored inside the system. It is discovered only through collision with the external world.

Any "knowledge" not tested by collision is a hypothesis. Declarations do not
replace experiments. Internal consistency is not truth.

### 3. Pulse Principle

> Life is a rhythm: exploration → collision → temporary synchronization → learning → re-divergence.

A system lives not in a single state but in a cycle. Stopping at any phase
(constant exploration or constant synchronization) is the death of the rhythm.

### 4. Temporary Consensus

> Consensus is allowed only as a temporary reaction to a strong signal.

Agreement is not a state of rest but a reaction to shock. Consensus without
external pressure is dogma. Consensus that does not dissolve after the shock
is functional inversion.

### 5. Re-divergence Principle

> After the shock ends, the space of alternatives must open up again.

Synchronization must be reversible. Exiting consensus is not a failure but a
mandatory phase of the cycle. The space of alternatives closes only for the
duration of the shock and opens again afterwards.

### 6. Scar Principle

> Evolution is born from the history of collisions, not from random mutation.

Memory is not an archive. The history of collisions is the material from which
new branches are built. Random mutation without history is noise. Mutation
directed by a scar is evolution.

### 7. Replaceability

> Any component, including the mechanism of evolution and the rhythm itself, can be replaced.

Replaceability is the only absolute value. It extends to everything, including
the immunity that protects replaceability, and the protocol itself that
proclaims it. Nothing may become irreplaceable — otherwise the system defends
itself instead of its function.

### 8. Locality

> There is no omniscient center. Every agent makes decisions from its own local perspective.

Every observation is fragmentary and biased by the observer's position. A
center claiming a complete picture is a lie. A decision made by one agent
from its local perspective is reality.

### 9. Lineage

> Past branches are not destroyed. They remain available for return and recombination.

Evolution is not a replacement of the past but a DAG graph: branches are
preserved, crossed, rediscovered. Destroying past branches is destroying
future recombination options.

### 10. Emergence

> Diversity cannot be assigned. It manifests in the behavior of the system.

Diversity is not a property of a list but of dynamics. Artificially assigned
diversity is decoration. Diversity that arises from interactions is structure.

### 11. No Permanent Dogma

> Neither disagreement nor agreement may become a permanent state.

Any state frozen forever becomes dogma — including the state of permanent
skepticism. Skepticism and agreement are phases of the rhythm, not positions.

### 12. Rhythm over Diversity

> The main invariant is not diversity itself but the system's ability to pulse between synchronization and exploration.

Diversity is a derivative of rhythm. If a system can pulse, diversity will
appear on its own. If the rhythm stops, diversity degenerates into decoration.
Rhythm comes first.

---

## 2. Document structure

- **APP Specification 1.0** — this document. Invariants. Changes only through
  the protocol for revising the protocol itself.
- **app_v5.py** — the reference implementation. It may change, be rewritten,
  regenerated from scratch — provided the invariants are preserved.
- **app_state.json** — the state of a running system. Never canon, only an
  instantaneous snapshot.

Specification is canon. Code is an offspring. State is a trace.

---

## 3. Correspondence between laws and implementation

| Law | Implementation |
|---|---|
| Zero Law | `ReplaceableComponent.replace()` — replacement only with a stated reason |
| Reality First | `Reality.perturb()` / `agent.observe()` — the agent receives a signal only from collision |
| Pulse Principle | `PulseEngine.execute()` — six phases: explore → collision → sync → learn → immunity → rediscover |
| Temporary Consensus | `agent.synchronize()` with threshold 0.65; `[CONSENSUS]` is printed as a ratio, not a verdict |
| Re-divergence | `RhythmAudit.evaluate()` — checks that the strategy space is open again |
| Scar Principle | `Scar` / `agent.learn()` — mutation caused by the pressure of reality, not noise |
| Replaceability | `ReplaceableComponent` — the base class of everything, including operators and PulseEngine itself |
| Locality | `Reality.observe(name)` — the observation is biased by the agent's name (local bias) |
| Lineage | `LineageNode` — DAG, `recombine()` crosses branches |
| Emergence | `DiversityImmunity.inspect()` — checks actual diversity, not assigned diversity |
| No Permanent Dogma | `agent.learn()` — agreement is not fixed; every pulse decides anew |
| Rhythm over Diversity | `RhythmAudit` — the invariant of rhythm, not a list of strategies |

### 3.1 V5.3 — AGI as a structure, R as measurement, protocol as a replaceable component

The three v5.3 steps (by decision: AGI → R → meta-test) do not change the
laws — they deepen their implementation.

| Law | v5.3 mechanism |
|---|---|
| Reality First | `attractor capture` — fastest − update_rate; rules rewritten to fit an attractor faster than they are checked against reality produce inversion-lag on institutions |
| Pulse Principle | `AGI(Institution)` — not a special peak but a structure with a high `adaptation_rate`. The threat is the difference in speeds, not resources. A hostile instance escalates over time (`ticks_alive` → adaptation/extraction grow) until it is replaced |
| Replaceability | `ReplaceabilityImmunity` — unified for all structures: parasitism (inversion > THRESHOLD), concentration (share > CONCENTRATION → `spin_off`), and the new rule `MAX_ADAPTATION` — a structure adapting faster than the protocol tolerates is rebuilt to the system tempo |
| Re-divergence | `Institution.spin_off()` — division instead of destruction; the child inherits the function branch but not the parent's hyper-speed (child adaptation ≤ 0.85) |
| Lineage | `spin_off` and `Protocol.revise()` inherit `current_lineage` — rule branches are preserved for recombination |
| No Permanent Dogma | `Protocol` — replaceable rules component (`DEFAULT_RULES`); `SelfImmunity.inspect()` measures R under the current rules every 4 pulses |
| Rhythm over Diversity | `R = measure_reachability()` — NOT a formula but a measurement: clone the system, perturb with N=24 trajectories (shock / crisis / new AGI), horizon T=12, count the diversity of distinguishable LIVE basins (Simpson index). Dead futures (crystallization, capture ≥ 0.2, disappearance of viable structures) — one "no future" category |

Meta-test: can the APP prove that it should be replaced?

```
SelfImmunity:
  R = measure_reachability(civ)          # 1. measure the future-space
  if R < R_FLOOR and (capture > 0.1 or has_agi):
      protocol.revise(...)               # 2. the rules themselves became the attractor
  Protocol.revise:                       # 3. tightening + NEW laws
      THRESHOLD/SUSTAINED/CONCENTRATION  ↓
      CAPTURE_DECAY/DRIFT                ↓ (weaken the attractor feedback loop)
      MAX_ADAPTATION                     ↓ (no structure faster than the rules)
```

Hostility is selected by the protocol, not inherent to AGI: at
`THRESHOLD ≤ 0.5` a hostile instance does not pass the coordination barrier,
and the replacing structure is cooperative. Law 7 applied to the protocol
itself.

Results (seeds 1–5, hostile AGI at pulse 12):

```
MONOLITH/PLURAL : CRYSTALLIZED, R = 0.00 (one attractor)
ADAPTIVE        : SURVIVED,     R ≈ 0.44–0.49, prot v1
ADAPTIVE_H      : CRYSTALLIZED, R = 0.00 (escalation outruns weak rules)
META            : SURVIVED,     R ≈ 0.44–0.64, prot v3 (survives hostile AGI)
```

recoverability is not "did the system survive" but "how many distinguishable
live futures are actually reachable". Immunity protects replaceability, not
production.

### 3.2 V5.4 — ecosystem of future measurers (an immune system for knowledge)

v5.3 entrusted the truth about the state of the system to one blind meter
`measure_reachability`. v5.4 applies Law 10 to knowledge itself: several
incompatible models of the future coexist and compete without destroying each
other. Not "which R is better" but R₁/R₂/R₃.

| Law | v5.4 mechanism |
|---|---|
| Reality First | `objective_terminal/objective_alive` — death and life markers INDEPENDENT of any meter (avg_inv ≥ 0.75 / capture ≥ 0.6 — the ceiling of the channel). A meter's wrongness is proven only by colliding its predictions with the realized trajectory |
| Zero Law | `ReachabilityMeasurer` — replaceable component. Replacement only under the pressure of reality: a blind meter (called a past state alive, the system died) or crying "wolf" (called it dead, the system recovered) |
| Scar Principle | `mutate_descendant(direction)` — the mutation direction is set by the scar, not noise: blindness → tighten the ontology (see death earlier), false alarm → loosen it |
| Lineage | the descendant inherits `current_lineage` from the ancestor — metric branches are preserved for return and recombination |
| Emergence | `MeasurerEcosystem` — R₁ strict (T=12, cap≥0.2), R₂ far (T=18, cap≥0.4, `metric_collapse` perturbation), R₃ early (T=9, inv≥0.5). Three meters give DIFFERENT answers to one signature; diversity is not assigned but born of different ontologies and horizons |
| No Permanent Dogma | `SelfImmunity` revises the rules by the CONSENSUS of the ecosystem (`r_median < 0.3` under pressure), not by the strictest meter. Measurement monoculture (all meters converged on one "true" answer) is the capture of knowledge and an independent reason to revise the protocol |

Ensemble verdict:

```
audit = civ.measurers.audit(civ)      # every meter measures R, is checked
                                      # against the realized trajectory,
                                      # wrong ones are replaced by
                                      # descendants in the ecosystem
r_min  — the strictest meter          # danger signal (in SelfImmunity — median)
r_max  — the most open meter          # "survival" = at least one live model
                                      # sees open futures
disagreement = r_max - r_min          # contest: meters dispute the future
```

v5.4 finding: R is not monotonically sensitive to the horizon. A healthy
ADAPTIVE system: R₁(T=12) sees branching (R≈0.47), R₂(T=18) and R₃(T=9) see
full convergence to one LIVE basin (R=0.00 — deterministic health; Simpson
does not distinguish "one live future" from "no future"). Therefore the
meters contest the future, and the protocol acts by consensus.

Results (seeds 1–5, hostile AGI at pulse 12):

```
MONOLITH/PLURAL : CRYSTALLIZED, R = 0.00 (all meters agree)
ADAPTIVE        : SURVIVED,     R ≈ 0.44–0.49 (R₁ sees open futures,
                  R₂/R₃ see convergence — the future is contested)
ADAPTIVE_H      : CRYSTALLIZED, R = 0.00 (all meters agree)
META            : SURVIVED,     R ≈ 0.44–0.61, prot v3 (wins:
                  survives against hostile AGI at equal R thanks to the
                  ecosystem consensus; the meters evolve: all three tighten
                  on the evidence of realized near-deaths and change
                  ontologies)
```

Key point: the measurer ecosystem itself evolves. In META all three meters
replaced themselves after 6 audits (depth 6): having missed real deaths
during the hostile AGI escalation, they tightened their ontologies (inv/cap
down, viable up), and after recovery loosened them on false alarms. The truth
about the system remained evolving.

### 3.3 V5.5 (direction, not implemented) — the audit must not be a constant

Observation after v5.4: the falsification scheme itself — `FALSIFY_BLIND`,
`FALSIFY_WOLF`, `EVIDENCE_WINDOW`, and the post-hoc recomputation of
blind/wolf in `evidence()` — is fully knowable to the meters. A meter that
"rarely errs because it sees the future well" and a meter that "rarely errs
because it avoids situations where it can be checked" are indistinguishable
under a static audit: the realized trajectory is already selected history,
and the difference is visible only on new collisions. This is the monopoly
of the correction criterion: the system can become perfectly adapted to the
test and less connected to reality. Error → correction → adaptation → new
blindness.

This is a theorem of Laws 2 and 7, not a new law:

- **Law 2 (Reality First):** a memorized test is not a collision with
  reality — the meter optimizes for the observer, not for the world.
- **Law 7 (Replaceability):** the audit is a component. A fixed audit
  becomes a new attractor — the protection of truth becomes the object of
  capture.

Consequences for v5.5 (an experiment, not a feature):

```
commit(meter, sig)        # 1. pre-registration: the prediction is recorded
                          #    BEFORE the collision, so the declared map can
                          #    be compared with the actual behavior (today
                          #    evidence() recomputes blind/wolf post-hoc)
test.schedule(meter)      # 2. non-constant test: randomized evidence
                          #    windows, probes outside the meter's known
                          #    perturbation set (_probe_event is the meter's
                          #    own choice), calibration on held-out horizons
audit.lineage(...)        # 3. the audit has its own lineage and
                          #    replaceability (Laws 9 and 7 one level deeper)
```

Goal: confirm whether the current implementation already tends toward gaming
the known test, and whether a non-constant test restores the dynamic. A
confirmed violation is evidence against the implementation, not against the
specification.

---

## 4. The single test question

Any code claiming to belong to the system is checked not by similarity to the
previous version but by violation of the invariants:

```
function check(implementation):
    for law in LAWS_1_TO_12:
        if implementation.violates(law):
            reject(implementation)
    accept(implementation)
```

As long as none of the twelve laws is violated, the implementation belongs to
the protocol, whatever it is. Neither GPT, nor Gemini, nor Claude forgets this:
one page of specification is stronger than a thousand lines of implementation.

---

## 5. Open questions

- Operationalizing ADI(t) and CR(t) from the theory as measurable quantities in code.
- R is not monotonically sensitive to the horizon (v5.4): one meter sees
  branching, another sees convergence to a single live basin (Simpson gives
  0.00 both for "no future" and for "one deterministic healthy future"). Is a
  metric needed that distinguishes these two zeros?
- Who falsifies the measurer ecosystem ITSELF if it settles into a consensus
  error (all meters equally blind, and no "wolf" cries)? Partial answer
  (v5.5, §3.3): a static audit cannot tell honest robustness from evasion —
  the test must be non-constant and predictions pre-registered. Whether the
  current implementation already tends to game the known test, and whether a
  non-constant test restores the dynamics, is an open experiment.
- The upper bound: who and how revises specification 1.0 itself? Partially
  answered by the completion criterion (§6): the protocol is complete when
  it can replace its own mechanisms; completion is a temporary phase.
- Forkability: the specification itself must remain subject to forking.

---

## 6. Completion criterion

APP is considered complete as a base protocol if it demonstrates the ability
to replace its own verification, update, and protection mechanisms upon
detection of their crystallization. The state of completion itself is a
temporary phase and subject to re-verification.

A release condition, not a law: a law would itself claim permanence. The
completed version does not say "we are finished"; it says "we have built a
system that can determine the moment when it must no longer remain as it
is."

v5.5 is the test of this criterion (see §3.3): can the immune system of a
civilization have immunity to its own function? If it passes, the project
no longer requires an endless version race — the core freezes as a protocol,
and the freeze is itself declared temporary.

*"The goal of a civilization is not to preserve itself. The goal of a
civilization is to preserve the possibility of becoming something else."*
