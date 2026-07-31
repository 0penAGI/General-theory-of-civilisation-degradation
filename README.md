# General Theory of Civilisation Degradation — APP

- **Theory:** `index.html` — the General Theory of Civilisation Degradation.
- **Code:** `adaptive_pluralism_protocol` — an implementation of the APP
  (Adaptive Pluralism Protocol): an immune architecture of civilization
  facing the age of AGI.

*"The goal of a civilization is not to preserve itself. The goal of a
civilization is to preserve the possibility of becoming something else."*

## What this is

Every living system degrades. This cannot be prevented — it can only be kept
*reversible*. The protocol forbids one thing: the conversion of any
configuration into a *permanent* state.

The simulation answers one question: **which structure of society survives
the arrival of AGI without crystallization?** It runs five scenarios —
monolith, plural, adaptive (APP immunity active), adaptive vs hostile AGI,
and a meta-test where the protocol has to prove it should be replaced.

The code is verified not by similarity to a previous version but by the
invariants of the 12 laws (see `docs/SPEC.md`).

## Installation

```bash
pip install -e .
```

No dependencies — standard library only (Python >= 3.10).

## Quick start

Run the five sandbox scenarios:

```bash
python examples/run_scenarios.py
# or after installing:
app-sim
```

Run the APP v5.0 core demo:

```bash
python -m adaptive_pluralism_protocol.app_v5
```

## API

```python
from adaptive_pluralism_protocol import (
    run_scenario,
    scenario_report,
    MeasurerEcosystem,
    measure_reachability,
)

civ = run_scenario("meta", True, seed=1, hostile_agi=True)
r = scenario_report(civ)
print(r["scenario"], r["crystallized"], r["R"], r["R_measurers"], r["protocol_gen"])
```

Key components:

| Component | Role |
|---|---|
| `Institution` / `AGI` | a single hierarchy of structures; AGI is not a special peak but a structure with a high `adaptation_rate` (Law 7) |
| `ReplaceabilityImmunity` | replaceability: parasitism, concentration (`spin_off`), speed (`MAX_ADAPTATION`) |
| `Protocol` | replaceable rules component; `revise()` rewrites the rules when they themselves became the attractor |
| `SelfImmunity` | audit every 4 pulses; the consensus of the meter ecosystem (median R < threshold) under pressure → the protocol revises itself |
| `ReachabilityMeasurer` | one future measurer: death ontology + horizon T + perturbations. A replaceable component; its wrongness is proven by the physical trajectory (blindness → tightening, false alarm → loosening) |
| `MeasurerEcosystem` | R₁/R₂/R₃ — incompatible models of the future, competing without destroying each other; measurement monoculture is a reason to revise the protocol |
| `measure_reachability` | v5.3-compatible wrapper (R₁ ontology). The ensemble verdict is `civ.measurers.audit(civ)` |

## Verification

```bash
python -m unittest discover -s tests -v
```

Stable verdicts (seeds 1–5): MONOLITH/PLURAL crystallize (R=0),
ADAPTIVE survives (R≈0.44–0.49, the future is contested by the meters),
ADAPTIVE_H dies against hostile AGI (R=0), META survives hostile AGI and
rewrites its own protocol (prot v3, wins by ecosystem consensus).

## Documentation

- `docs/SPEC.md` — the 12 APP laws and the v5.3/v5.4 implementation mapping.
- Criterion of belonging to the protocol: not similarity to a previous
  version, but the invariants of the 12 laws (section 4 of the spec).
