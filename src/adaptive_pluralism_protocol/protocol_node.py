"""APP protocol node — the participation layer.

The sandbox (civilization_simulator) crash-tests rulesets. A node is the
carrier: real people, teams and organizations enter the protocol through it.
The node is deliberately small and offline-first — local sovereignty belongs
to whoever runs it, not to any server.

The lineage IS the civilization:

    person -> agent -> institution -> protocol -> reality -> scar
        -> change -> new branch

State layout of a node (a directory inside any repo):
    APP.md            node manifest: id, key, parent, principle
    RULES.md          the laws — editable text, meant to be forked
    INSTITUTIONS.md   the organizations this node runs or belongs to
    DECISIONS.jsonl   append-only, signed, hash-chained decision ledger
    EVENTS.jsonl      reality pressure, signed
    .app/key          Ed25519 private key (identity, never leaves the node)

Identity: node id = fingerprint of its Ed25519 public key. A node is what it
can sign. Forkability is the immunity: any node may fork a branch, rewrite
the laws, and crash-test them — the one thing it cannot do is silently rewrite
a signed decision.

First living principle (embedded in every new node):

    We create not a society that knows the right answer,
    but a society that cannot get permanently stuck on the wrong one.
"""

import argparse
import base64
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
except ImportError:
    raise SystemExit(
        "APP node needs 'cryptography'. Install it with:\n"
        "    pip install adaptive-pluralism-protocol[node]"
    )

# -----------------------------------------------------------------------------
# Identity
# -----------------------------------------------------------------------------

PRINCIPLE = (
    "We create not a society that knows the right answer, "
    "but a society that cannot get permanently stuck on the wrong one."
)


def _canon(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _node_id(pub_bytes: bytes) -> str:
    return "N:" + hashlib.blake2b(pub_bytes, digest_size=16).hexdigest()


def _decision_id(content: dict) -> str:
    return "D:" + hashlib.blake2b(_canon(content), digest_size=16).hexdigest()


def _event_id(content: dict) -> str:
    return "E:" + hashlib.blake2b(_canon(content), digest_size=16).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _pub_bytes(key: Ed25519PublicKey) -> bytes:
    return key.public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )


def _pub_b64(key: Ed25519PublicKey) -> str:
    return base64.b64encode(_pub_bytes(key)).decode()


def generate_keypair():
    private = Ed25519PrivateKey.generate()
    public = private.public_key()
    return private, public


# -----------------------------------------------------------------------------
# Node
# -----------------------------------------------------------------------------

class ProtocolNode:
    """A running APP node: one branch, one identity, one signed ledger."""

    def __init__(self, directory: str | os.PathLike):
        self.dir = Path(directory)
        self.app = _read_app(self.dir / "APP.md")
        self._priv = _load_private(self.dir / ".app" / "key")
        self._pub = self._priv.public_key()
        self.node_id = _node_id(_pub_bytes(self._pub))
        assert self.node_id == self.app["node"], "APP.md node id mismatch with key"

    # -- ledger ---------------------------------------------------------

    def decisions(self):
        return _load_ledger(self.dir / "DECISIONS.jsonl")

    def events(self):
        return _load_ledger(self.dir / "EVENTS.jsonl")

    def last_decision(self):
        ds = self.decisions()
        return ds[-1] if ds else None

    def append_decision(
        self,
        kind: str,
        statement: str,
        *,
        falsified_by: str = "",
        rules: dict | None = None,
        audit: dict | None = None,
        adopted_from: str | None = None,
        adopted_node: str | None = None,
    ) -> dict:
        parent = self.last_decision()["id"] if self.decisions() else "-"
        content = {
            "parent": parent,
            "kind": kind,
            "node": self.node_id,
            "key": _pub_b64(self._pub),
            "time": _now(),
            "statement": statement,
            "falsified_by": falsified_by,
        }
        if rules is not None:
            content["rules"] = rules
        if audit is not None:
            content["audit"] = audit
        if adopted_from is not None:
            content["adopted_from"] = adopted_from
        if adopted_node is not None:
            content["adopted_node"] = adopted_node
        entry = dict(content, id=_decision_id(content))
        entry["sig"] = self._sign(content)
        _append_entry(self.dir / "DECISIONS.jsonl", entry)
        return entry

    def append_event(self, name: str, measure: str, value: float, statement: str = "") -> dict:
        content = {
            "node": self.node_id,
            "key": _pub_b64(self._pub),
            "time": _now(),
            "event": name,
            "measure": measure,
            "value": value,
            "statement": statement,
        }
        entry = dict(content, id=_event_id(content))
        entry["sig"] = self._sign(content)
        _append_entry(self.dir / "EVENTS.jsonl", entry)
        return entry

    # -- crypto ---------------------------------------------------------

    def _sign(self, content: dict) -> str:
        return base64.b64encode(self._priv.sign(_canon(content))).decode()

    @staticmethod
    def verify_entry(entry: dict) -> str | None:
        """Return None if the entry is self-consistent, else an error string."""
        raw_pub = base64.b64decode(entry["key"])
        pub = Ed25519PublicKey.from_public_bytes(raw_pub)
        node_id = _node_id(raw_pub)
        if node_id != entry.get("node"):
            return f"node id mismatch: {entry.get('node')} != {node_id}"
        prefix = entry["id"].split(":", 1)[0]
        if prefix not in ("D", "E"):
            return "bad id prefix"
        content = dict(entry)
        content.pop("id", None)
        content.pop("sig", None)
        if entry["id"] != (prefix + ":" + hashlib.blake2b(_canon(content), digest_size=16).hexdigest()):
            return "id does not match content hash"
        try:
            pub.verify(base64.b64decode(entry["sig"]), _canon(content))
        except InvalidSignature:
            return "bad signature"
        return None

    def verify_chain(self) -> list[str]:
        """Verify every signed entry and the decision chain. Returns problems."""
        problems = []
        prev = "-"
        for entry in self.decisions():
            if entry.get("parent", "-") != prev:
                problems.append(
                    f"DECISIONS: chain break — {entry.get('id')} parent {entry.get('parent')}, expected {prev}"
                )
            prev = entry["id"]
            err = self.verify_entry(entry)
            if err:
                problems.append(f"DECISIONS: {entry.get('id')} — {err}")
        for entry in self.events():
            err = self.verify_entry(entry)
            if err:
                problems.append(f"EVENTS: {entry.get('id')} — {err}")
        return problems

    # -- laws -----------------------------------------------------------

    def read_rules(self) -> dict:
        return _parse_kv(self.dir / "RULES.md")

    def read_institutions(self) -> list[dict]:
        return _parse_table(self.dir / "INSTITUTIONS.md")

    def amend_rules(self, changes: dict[str, str], note: str, falsified_by: str = "") -> dict:
        rules = self.read_rules()
        rules.update(changes)
        _write_kv(self.dir / "RULES.md", rules)
        return self.append_decision(
            "amend", note, falsified_by=falsified_by, rules=rules,
        )

    def add_institution(self, name: str, function: str, owner: str = "-",
                        replace_with: str = "", replaceable: str = "yes") -> dict:
        insts = self.read_institutions()
        if any(i["name"] == name for i in insts):
            raise SystemExit(f"institution already exists: {name}")
        _append_table(self.dir / "INSTITUTIONS.md",
                      name, function, owner, replaceable, replace_with)
        return self.append_decision(
            "join",
            f"institution {name} ({function}) connected to the network; "
            f"owner={owner}, replaceable={replaceable}",
            falsified_by=f"the node can no longer replace {name} when its function fails",
        )

    # -- crash-test (feedback loop) -------------------------------------

    def crash_test(self) -> dict:
        """Run the sandbox on this node's RULES.md — an audit, not a model."""
        from .civilization_simulator import (
            CivilizationEngine,
            RealityEvent,
            build_scenario,
            default_events,
            scenario_report,
        )

        rules = self.read_rules()
        scenario = rules.get("scenario", "meta")
        self_immunity = rules.get("self_immunity", "yes") == "yes"
        hostile = rules.get("hostile_agi", "no") == "yes"
        pulses = int(rules.get("pulses", 40))
        agi_at = int(rules.get("agi_at", 12))
        seed = int(rules.get("seed", int(self.node_id[2:], 16) % 99991))

        civ = build_scenario(scenario, self_immunity, seed, hostile_agi=hostile)
        civ.self_immunity = self_immunity  # the node's laws drive the audit, not the kind label
        engine = CivilizationEngine(self_immunity=civ.self_immunity)
        events = default_events(pulses, agi_at)
        for p in range(pulses):
            engine.pulse(civ, events.get(p, RealityEvent("routine", 0.05)))
        report = scenario_report(civ)
        report["rules"] = rules
        report["node"] = self.node_id
        report["seed"] = seed
        return report

    def pulse(self, statement: str = "crash-test of RULES.md") -> dict:
        report = self.crash_test()
        self.append_decision("audit", statement, audit=_audit_slice(report))
        return report

    # -- replaceability audit -------------------------------------------

    def replaceability_blocks(self) -> list[dict]:
        """Institutions that can no longer be replaced — real-world R=0."""
        blocks = []
        for inst in self.read_institutions():
            if inst["replaceable"] == "no" and not inst["replace_with"]:
                blocks.append(inst)
        return blocks

    # -- lineage across forks -------------------------------------------

    def fork(self, target_dir: str | os.PathLike, statement: str) -> "ProtocolNode":
        target = Path(target_dir)
        if target.exists() and any(target.iterdir()):
            raise SystemExit(f"target not empty: {target}")
        target.mkdir(parents=True, exist_ok=True)
        (target / ".app").mkdir(parents=True, exist_ok=True)
        for fname in ("RULES.md", "INSTITUTIONS.md", "DECISIONS.jsonl", "EVENTS.jsonl"):
            _copy(self.dir / fname, target / fname)
        priv, pub = generate_keypair()
        _write_private(target / ".app" / "key", priv)
        parent_last = self.last_decision()
        node_id = _node_id(_pub_bytes(pub))
        _write_app(target / "APP.md", name=self.app["name"], node=node_id,
                   key=_pub_b64(pub), parent_node=self.node_id,
                   forked_from=parent_last["id"] if parent_last else "-",
                   principle=self.app["principle"])
        node = ProtocolNode(target)
        node.append_decision(
            "fork",
            statement,
            adopted_from=parent_last["id"] if parent_last else "-",
            adopted_node=self.node_id,
        )
        return node

    def adopt(self, foreign_dir: str | os.PathLike, decision_id: str, statement: str) -> dict:
        """Exercise the self-replaceable rule: take a foreign branch's laws.

        The foreign ledger is verified (signatures, hashes, chain), then its
        laws replace this node's laws. The old laws stay in the history —
        that is what makes replacement reversible and lineage honest.
        """
        foreign = ProtocolNode(foreign_dir)
        foreign_ledger = foreign.decisions()
        target = next((d for d in foreign_ledger if d["id"] == decision_id), None)
        if target is None:
            raise SystemExit(f"no such decision in {foreign.dir}: {decision_id}")
        problems = foreign.verify_chain()
        if problems:
            raise SystemExit(f"refusing to adopt — foreign ledger fails verification:\n" + "\n".join(problems))
        # replace laws; the current laws remain in this node's history
        _copy(foreign.dir / "RULES.md", self.dir / "RULES.md")
        _copy(foreign.dir / "INSTITUTIONS.md", self.dir / "INSTITUTIONS.md")
        return self.append_decision(
            "adopt",
            statement,
            falsified_by="the adopted laws no longer survive a crash-test",
            rules=self.read_rules(),
            adopted_from=decision_id,
            adopted_node=foreign.node_id,
        )

    # -- state exchange -------------------------------------------------

    def export(self) -> dict:
        """Bundle the node for transport — identity travels with the state.

        Moving a node is the owner's sovereign act (like moving an ssh key);
        the bundle is verified line-by-line on import and a tampered bundle
        is refused.
        """
        pem = self._priv.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
        return {
            "app": self.app,
            "key_pem": base64.b64encode(pem).decode(),
            "rules": self.read_rules(),
            "institutions": self.read_institutions(),
            "decisions": self.decisions(),
            "events": self.events(),
        }

    def status(self) -> dict:
        last = self.last_decision()
        audits = [d for d in self.decisions() if d["kind"] == "audit"]
        return {
            "name": self.app["name"],
            "node": self.node_id,
            "parent_node": self.app.get("parent_node", "-"),
            "decisions": len(self.decisions()),
            "events": len(self.events()),
            "institutions": len(self.read_institutions()),
            "last_decision": last,
            "last_audit": _audit_slice(audits[-1]["audit"]) if audits else None,
            "replaceability_blocks": self.replaceability_blocks(),
        }


# -----------------------------------------------------------------------------
# File format helpers (laws = editable text; facts = signed ledgers)
# -----------------------------------------------------------------------------

APP_TEMPLATE = """# APP node — {name}

node: {node}
key: {key}
name: {name}
parent_node: {parent_node}
forked_from: {forked_from}
principle: "{principle}"
"""

RULES_TEMPLATE = """# APP node rules — crash-tested by the sandbox, never a constitution.
# scenario:  monolith | plural | adaptive | adaptive_h | meta
scenario: meta
self_immunity: yes
hostile_agi: no
audit_period: 4
pulses: 40
agi_at: 12
"""

INSTITUTIONS_TEMPLATE = """# Institutions — the organizations this node runs or belongs to.
# replaceable=no requires a named replace-with, or the network flags it.
| name | function | owner | replaceable | replace-with |
| - | - | - | - | - |
"""


def _read_app(path: Path) -> dict:
    text = path.read_text()
    app: dict[str, str] = {}
    for line in text.splitlines():
        if ":" in line and not line.startswith("#"):
            k, v = line.split(":", 1)
            app[k.strip()] = v.strip().strip('"')
    return app


def _write_app(path: Path, *, name, node, key, parent_node, forked_from, principle):
    path.write_text(APP_TEMPLATE.format(
        name=name, node=node, key=key,
        parent_node=parent_node, forked_from=forked_from, principle=principle,
    ))


def _write_private(path: Path, priv: Ed25519PrivateKey):
    path.write_bytes(priv.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ))
    os.chmod(path, 0o600)


def _load_private(path: Path) -> Ed25519PrivateKey:
    return serialization.load_pem_private_key(path.read_bytes(), password=None)


def _load_ledger(path: Path) -> list[dict]:
    if not path.exists():
        return []
    entries = []
    for line in path.read_text().splitlines():
        if line.strip():
            entries.append(json.loads(line))
    return entries


def _append_entry(path: Path, entry: dict):
    with open(path, "a") as f:
        f.write(json.dumps(entry) + "\n")


def _copy(src: Path, dst: Path):
    if src.exists():
        dst.write_bytes(src.read_bytes())


def _parse_kv(path: Path) -> dict:
    rules: dict[str, str] = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            k, v = line.split(":", 1)
            rules[k.strip()] = v.strip().strip('"')
    return rules


def _write_kv(path: Path, rules: dict):
    if path.exists():
        lines = []
        for line in path.read_text().splitlines():
            if ":" in line and not line.startswith("#"):
                break
            lines.append(line)
    else:
        lines = [l for l in RULES_TEMPLATE.splitlines() if l.startswith("#")]
    for k, v in rules.items():
        lines.append(f"{k}: {v}")
    path.write_text("\n".join(lines) + "\n")


def _parse_table(path: Path) -> list[dict]:
    insts = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line.startswith("|") or line.startswith("|-"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 5 or cells[0] == "name":
            continue
        if all(c in ("-", "") for c in cells[:5]):
            continue
        insts.append({
            "name": cells[0], "function": cells[1], "owner": cells[2],
            "replaceable": cells[3], "replace_with": cells[4] if len(cells) > 4 else "",
        })
    return insts


def _append_table(path: Path, name, function, owner, replaceable, replace_with):
    with open(path, "a") as f:
        f.write(f"| {name} | {function} | {owner} | {replaceable} | {replace_with} |\n")


def _audit_slice(report: dict) -> dict:
    return {
        "scenario": report.get("scenario"),
        "status": ("CRYSTALLIZED" if report.get("crystallized")
                   else "SURVIVED" if report.get("survived") else "DEGRADED"),
        "R": report.get("R"),
        "R_median": report.get("R_median"),
        "R_min": report.get("R_min"),
        "R_max": report.get("R_max"),
        "meters": report.get("R_measurers"),
        "protocol_gen": report.get("protocol_gen"),
        "contested": report.get("contested"),
        "measurement_monoculture": report.get("measurement_monoculture"),
        "F": report.get("F"),
        "capture": report.get("capture"),
    }


# -----------------------------------------------------------------------------
# Bootstrap
# -----------------------------------------------------------------------------

def init_node(directory: str | os.PathLike, name: str) -> ProtocolNode:
    dirp = Path(directory)
    if dirp.exists() and any(dirp.iterdir()):
        raise SystemExit(f"directory not empty: {dirp}")
    dirp.mkdir(parents=True, exist_ok=True)
    (dirp / ".app").mkdir(parents=True, exist_ok=True)
    priv, pub = generate_keypair()
    _write_private(dirp / ".app" / "key", priv)
    node_id = _node_id(_pub_bytes(pub))
    _write_app(dirp / "APP.md", name=name, node=node_id, key=_pub_b64(pub),
               parent_node="-", forked_from="-", principle=PRINCIPLE)
    (dirp / "RULES.md").write_text(RULES_TEMPLATE)
    (dirp / "INSTITUTIONS.md").write_text(INSTITUTIONS_TEMPLATE)
    node = ProtocolNode(dirp)
    node.append_decision(
        "declare",
        f"node {name} enters the network: {PRINCIPLE}",
        falsified_by="a permanent monoculture proves the protocol wrong",
        rules=node.read_rules(),
    )
    return node


def import_bundle(bundle: dict, target_dir: str | os.PathLike) -> ProtocolNode:
    """Materialize an exported state into a fresh directory after verification."""
    target = Path(target_dir)
    if target.exists() and any(target.iterdir()):
        raise SystemExit(f"directory not empty: {target}")
    target.mkdir(parents=True, exist_ok=True)
    (target / ".app").mkdir(parents=True, exist_ok=True)
    _write_private(target / ".app" / "key", serialization.load_pem_private_key(
        base64.b64decode(bundle["key_pem"]), password=None))
    problems = []
    for entry in bundle["decisions"] + bundle["events"]:
        err = ProtocolNode.verify_entry(entry)
        if err:
            problems.append(f"{entry.get('id')} — {err}")
    if problems:
        raise SystemExit("bundle fails verification:\n" + "\n".join(problems))
    (target / "APP.md").write_text(APP_TEMPLATE.format(
        name=bundle["app"]["name"], node=bundle["app"]["node"],
        key=bundle["app"]["key"], parent_node=bundle["app"].get("parent_node", "-"),
        forked_from=bundle["app"].get("forked_from", "-"),
        principle=bundle["app"].get("principle", PRINCIPLE),
    ))
    _write_kv(target / "RULES.md", bundle["rules"])
    (target / "INSTITUTIONS.md").write_text(INSTITUTIONS_TEMPLATE)
    for inst in bundle["institutions"]:
        _append_table(target / "INSTITUTIONS.md",
                      inst["name"], inst["function"], inst.get("owner", "-"),
                      inst.get("replaceable", "yes"), inst.get("replace_with", ""))
    for fname, entries in (("DECISIONS.jsonl", bundle["decisions"]),
                           ("EVENTS.jsonl", bundle["events"])):
        with open(target / fname, "a") as f:
            for e in entries:
                f.write(json.dumps(e) + "\n")
    return ProtocolNode(target)


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------

def _print_status(s: dict):
    print(f"name:        {s['name']}")
    print(f"node:        {s['node']}")
    print(f"parent:      {s['parent_node']}")
    print(f"decisions:   {s['decisions']}   events: {s['events']}   institutions: {s['institutions']}")
    if s["last_audit"]:
        a = s["last_audit"]
        print(f"last audit:  {a['scenario']} -> {a['status']}  R={a['R']}  "
              f"prot=v{a['protocol_gen']}  contested={a['contested']}")
    blocks = s["replaceability_blocks"]
    if blocks:
        print(f"replaceability BLOCKS: {', '.join(b['name'] for b in blocks)}")
    else:
        print("replaceability: every institution has an exit")
    last = s["last_decision"]
    if last:
        print(f"last decision: {last['id']}  {last['kind']}  {last['statement'][:60]}...")


def main_cli(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    p = argparse.ArgumentParser(
        prog="app-node",
        description="APP protocol node — the participation layer of the network.",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    q = sub.add_parser("init", help="create a node (one branch, one identity)")
    q.add_argument("dir")
    q.add_argument("--name", default="unnamed")

    q = sub.add_parser("status", help="show node state")
    q.add_argument("dir")

    q = sub.add_parser("decide", help="append a signed decision")
    q.add_argument("dir")
    q.add_argument("statement")
    q.add_argument("--kind", default="declare")
    q.add_argument("--falsified-by", default="")

    q = sub.add_parser("reality", help="record a real-world event")
    q.add_argument("dir")
    q.add_argument("event")
    q.add_argument("--measure", required=True)
    q.add_argument("--value", type=float, required=True)

    q = sub.add_parser("amend", help="change RULES.md and sign the amendment")
    q.add_argument("dir")
    q.add_argument("--rule", action="append", default=[])
    q.add_argument("--note", default="amend rules")
    q.add_argument("--falsified-by", default="")

    q = sub.add_parser("institution", help="connect an institution to the network")
    q.add_argument("dir")
    q.add_argument("name")
    q.add_argument("--function", required=True)
    q.add_argument("--owner", default="-")
    q.add_argument("--replace-with", default="")
    q.add_argument("--replaceable", choices=("yes", "no"), default="yes")

    q = sub.add_parser("pulse", help="crash-test RULES.md and sign the audit")
    q.add_argument("dir")

    q = sub.add_parser("audit", help="replaceability audit of institutions")
    q.add_argument("dir")

    q = sub.add_parser("fork", help="create a child branch with its own identity")
    q.add_argument("dir")
    q.add_argument("target")
    q.add_argument("--statement", default="fork to test a hypothesis")

    q = sub.add_parser("compare", help="crash-test this node vs a foreign branch")
    q.add_argument("dir")
    q.add_argument("foreign")

    q = sub.add_parser("adopt", help="replace local laws with a verified foreign branch's")
    q.add_argument("dir")
    q.add_argument("foreign")
    q.add_argument("--decision", required=True)
    q.add_argument("--statement", default="adopt verified branch")

    q = sub.add_parser("export", help="bundle the node state for transport")
    q.add_argument("dir")
    q.add_argument("file")

    q = sub.add_parser("import", help="materialize an exported bundle")
    q.add_argument("file")
    q.add_argument("dir")

    q = sub.add_parser("log", help="show the decision ledger")
    q.add_argument("dir")
    q.add_argument("--json", action="store_true")

    q = sub.add_parser("verify", help="verify every signature and the chain")
    q.add_argument("dir")

    args = p.parse_args(argv)

    if args.cmd == "init":
        n = init_node(args.dir, args.name)
        print(f"node created: {n.node_id}")
        print(PRINCIPLE)
        return
    if args.cmd == "import":
        bundle = json.loads(Path(args.file).read_text())
        n = import_bundle(bundle, args.dir)
        print(f"imported: {n.node_id}")
        return

    n = ProtocolNode(args.dir)

    if args.cmd == "status":
        _print_status(n.status())
    elif args.cmd == "decide":
        d = n.append_decision(args.kind, args.statement, falsified_by=args.falsified_by)
        print(d["id"])
    elif args.cmd == "reality":
        e = n.append_event(args.event, args.measure, args.value)
        print(e["id"])
    elif args.cmd == "amend":
        changes = {}
        for r in args.rule:
            k, _, v = r.partition("=")
            changes[k.strip()] = v.strip()
        d = n.amend_rules(changes, args.note, args.falsified_by)
        print(f"{d['id']}  rules: {changes or 'snapshot'}")
    elif args.cmd == "institution":
        d = n.add_institution(args.name, args.function, args.owner, args.replace_with, args.replaceable)
        print(d["id"])
    elif args.cmd == "pulse":
        r = n.pulse()
        a = _audit_slice(r)
        print(f"{a['scenario']} -> {a['status']}  R={a['R']}  prot=v{a['protocol_gen']} "
              f"contested={a['contested']}")
    elif args.cmd == "audit":
        for b in n.replaceability_blocks():
            print(f"BLOCK: {b['name']} ({b['function']}) cannot be replaced")
        if not n.replaceability_blocks():
            print("ok — every institution has an exit")
    elif args.cmd == "fork":
        child = n.fork(args.target, args.statement)
        print(f"forked: {child.node_id}  <-  {n.node_id}")
    elif args.cmd == "compare":
        f = ProtocolNode(args.foreign)
        mine, theirs = n.crash_test(), f.crash_test()
        for label, r in (("self", mine), ("foreign", theirs)):
            a = _audit_slice(r)
            print(f"{label:8} {a['scenario']:10} -> {a['status']:12} R={a['R']} "
                  f"contested={a['contested']}")
    elif args.cmd == "adopt":
        d = n.adopt(args.foreign, args.decision, args.statement)
        print(f"{d['id']}  adopted {d['adopted_from']} from {d['adopted_node']}")
    elif args.cmd == "export":
        Path(args.file).write_text(json.dumps(n.export(), indent=2))
        print(f"exported: {args.file}")
    elif args.cmd == "log":
        for d in reversed(n.decisions()):
            if args.json:
                print(json.dumps(d))
            else:
                print(f"{d['id']}  {d['kind']:8} {d['node']}  {d['statement'][:72]}")
    elif args.cmd == "verify":
        problems = n.verify_chain()
        if problems:
            print("\n".join(problems))
            raise SystemExit(1)
        print("ok — all signatures valid, chain intact")


if __name__ == "__main__":
    main_cli()
