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

## The network layer — participation, not observation

The sandbox crash-tests rulesets. A **protocol node** is the carrier: real
people, teams and organizations enter the protocol through it. A node is one
branch, one identity, one signed hash-chained ledger — and it is deliberately
small and offline-first (local sovereignty belongs to whoever runs it).

```bash
pip install -e ".[node]"

app-node init my-branch            # genesis: one identity, one signed declaration
app-node status my-branch          # state, last crash-test, replaceability audit
app-node pulse my-branch           # crash-test RULES.md, sign the audit
app-node amend my-branch --rule hostile_agi=yes --note "harden the premise"
app-node fork my-branch fork-a --statement "branch to test a hypothesis"
app-node seal my-branch "superseded by fork-a" --superseded-by N:…
app-node invite my-branch          # self-signed introduction
app-node accept my-branch invite.json   # trust on first use (compare fingerprints)
app-node sync my-branch N:… --source peer-dir
app-node adopt my-branch peer-dir --decision D:… --statement "accept verified laws"
app-node export my-branch bundle.json   # move the node — the bundle is verified on import
```

The one thing a node cannot do is silently rewrite a signed decision.
Forkability is the immunity: any node may fork a branch, rewrite the laws,
and crash-test them. `seal` retires a branch — its history stays, its
leadership ends ("vanished" in the network).

**The committed seed network** (`network/`) is the founding story made
verifiable: six public branches with real forks, an accepted idea (commons
adopting eliza-v2's hostile-AGI premise), a replaceability block (guardian's
The_Leviathan), and a crystallized branch that sealed itself (old-order,
R=0). Regenerate with `python examples/seed_network.py`.

## The Network Observatory — the web entry point

```bash
python observatory.py              # http://localhost:8765
```

A single standard-library server: serves the built web app, a REST API for
protocol nodes, and a WebSocket stream (network events + the simulator).

```bash
cd frontend && npm install && npm run build     # rebuild the web app
```

The web app opens with the **genesis screen**: "the first node knows nothing".
Create a branch, then watch the **Network Observatory** — a lineage graph of
real nodes (forks, accepted ideas, vanished branches), the per-branch
crash-test and rule history, and actions on your own branch (crash-test, fork,
adopt from any verified branch, seal, export). REST API:

| Method | Route | Action |
|---|---|---|
| GET | `/api/network` | full network map (lineage, ideas, vanished) |
| POST | `/api/nodes` | genesis — create a node `{name}` |
| POST | `/api/nodes/{id}/pulse` | crash-test, sign the audit |
| POST | `/api/nodes/{id}/fork` | fork your branch `{name, statement}` |
| POST | `/api/nodes/{id}/adopt` | adopt a verified foreign branch `{foreign, decision, statement}` |
| POST | `/api/nodes/{id}/seal` | retire the branch |
| GET | `/api/nodes/{id}/export` | download the node bundle |

Seeds are read-only (public states, no private keys): you adopt from them,
never through them. Locally created nodes live in `nodes/` (gitignored) —
your sovereignty is that directory and its key.

## Deploying the web app (GitHub Pages)

GitHub Pages is static-only — the observatory's Python backend cannot run
there. The build ships a **static snapshot** of the committed seed network
(`frontend/public/network.json`, regenerate with
`python examples/export_network_snapshot.py`), so the deployed site renders
the real lineage — seeds, forks, accepted ideas, vanished branches — with no
backend. Pushing to `main` runs `.github/workflows/pages.yml`, which builds
`frontend/` and deploys `frontend/dist` (enable **Settings → Pages → Source:
GitHub Actions`).

On the deployed site the observatory is offline by design: the Network view
reads the snapshot and actions are disabled, with a banner pointing to the
live entry point. To create your own node and fork the seeds, run the
observatory locally and open `http://localhost:8765` — the app detects it and
serves everything same-origin. For a hosted observatory later, point the build
at it:

```bash
cd frontend
VITE_OBSERVATORY_URL=wss://your-host VITE_API_BASE=https://your-host npm run build
```

## Current direction (v5.5)

The falsification scheme is knowable to the meters; a static audit cannot
distinguish a meter that errs rarely because it sees well from one that
errs rarely because it avoids being checked. The audit itself must not
become a constant — see §3.3 of the spec. The protocol's release condition
is the completion criterion (§6): complete when it can replace its own
verification, update, and protection mechanisms — and the completion is
itself a temporary phase.

## Documentation

- `docs/SPEC.md` — the 12 APP laws and the v5.3/v5.4 implementation mapping,
  plus the v5.5 direction (§3.3): the audit must not be a constant —
  pre-registered predictions and a non-constant test.
- Criterion of belonging to the protocol: not similarity to a previous
  version, but the invariants of the 12 laws (section 4 of the spec).
