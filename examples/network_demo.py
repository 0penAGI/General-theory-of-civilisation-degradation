#!/usr/bin/env python3
"""APP Network demo — the first living organism, not a model of one.

Two nodes (alice, bob) enter the network. Alice's node forks a branch to test
a hypothesis, the fork's laws survive a crash-test, and bob adopts them with
lineage. Reality pressure is injected as signed events; the sandbox feedback
loop appends audits to each ledger.

Run:
    python examples/network_demo.py
"""

import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from adaptive_pluralism_protocol.protocol_node import (  # noqa: E402
    ProtocolNode,
    import_bundle,
    init_node,
)


def line(rule: str = "-") -> None:
    print(rule * 70)


def status_of(r: dict) -> str:
    if r["crystallized"]:
        return "CRYSTALLIZED"
    if r["survived"]:
        return "SURVIVED"
    return "DEGRADED"


def main() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="app-network-"))
    alice = init_node(tmp / "alice", "alice")
    bob = init_node(tmp / "bob", "bob")

    line()
    print("1. TWO NODES ENTER THE NETWORK — identity is what a node can sign.")
    for n in (alice, bob):
        print(f"   {n.app['name']:5} {n.node_id}")
    for n in (alice, bob):
        print(f"   verify {n.app['name']}:", "ok" if not n.verify_chain() else n.verify_chain())

    line()
    print("2. INSTITUTIONS JOIN THE NETWORK (declared replaceability).")
    for n, insts in (
        (alice, [("Commons_Trust", "commons", "", "yes"),
                 ("The_Leviathan", "governance", "", "no")]),
        (bob, [("Science_Schools", "research", "", "yes")]),
    ):
        for name, fn, rw, rep in insts:
            n.add_institution(name, fn, replace_with=rw, replaceable=rep)
    print("   alice blocks:", [b["name"] for b in alice.replaceability_blocks()])
    print("   bob blocks:  ", [b["name"] for b in bob.replaceability_blocks()])

    line()
    print("3. REALITY PRESSURE — a signed event, the sandbox's metric_collapse.")
    ev = bob.append_event("metric_collapse", "ADI", 0.82,
                          statement="knowledge institutions stop decaying")
    print(f"   {ev['id']}  {ev['event']} {ev['measure']}={ev['value']}")

    line()
    print("4. FEEDBACK LOOP — every node crash-tests its RULES.md (an audit, not a law).")
    for n in (alice, bob):
        r = n.crash_test()
        print(f"   {n.app['name']:5} {r['scenario']:>10} -> {status_of(r):12} "
              f"R={r['R']} prot=v{r['protocol_gen']} contested={r['contested']}")

    line()
    print("5. FORK — alice forks to test the immunity hypothesis.")
    fork = alice.fork(tmp / "alice-fork", "fork: does self-immunity keep the future open?")
    print(f"   {fork.node_id}  forked_from {alice.last_decision()['id']}")

    line()
    print("6. THE FORK CHANGES THE LAWS and crash-tests them.")
    fork.amend_rules({"self_immunity": "no"}, "test without self-immunity")
    r = fork.crash_test()
    print(f"   {r['scenario']} -> {status_of(r)}  R={r['R']} (hypothesis test)")
    fork.amend_rules({"self_immunity": "yes"},
                     "hypothesis rejected — self-immunity restored, wrong answer stays replaceable")
    r = fork.crash_test()
    print(f"   {r['scenario']} -> {status_of(r)}  R={r['R']} (hypothesis restored)")

    line()
    print("7. ADOPT — bob replaces his laws with the verified fork's, keeping lineage.")
    last_fork = fork.last_decision()
    bob.adopt(tmp / "alice-fork", last_fork["id"],
              "adopt the forked branch: the wrong answer must stay replaceable")
    adopted = bob.last_decision()
    print(f"   {adopted['id']}  adopted_from {adopted['adopted_from']}  "
          f"adopted_node {adopted['adopted_node']}")
    print("   bob old laws preserved in history; new laws crash-tested:")
    r = bob.crash_test()
    print(f"   {r['scenario']} -> {status_of(r)}  R={r['R']} prot=v{r['protocol_gen']}")

    line()
    print("8. STATE EXCHANGE — export, verify, transport, import.")
    bundle = bob.export()
    tampered = json.loads(json.dumps(bundle))
    tampered["decisions"][0]["statement"] = "forged entry"
    try:
        import_bundle(tampered, tmp / "evil")
        print("   ERROR: tampered bundle accepted")
    except SystemExit as e:
        print(f"   tampered bundle refused: {str(e).splitlines()[0]}")
    carol = import_bundle(bundle, tmp / "carol")
    print(f"   {carol.node_id}  verify:", "ok" if not carol.verify_chain() else carol.verify_chain())
    print("   carol is bob's node alive on another machine — same identity, same lineage.")

    line()
    print("9. THE FIRST LIVING PRINCIPLE, tested by the whole network.")
    nodes = [("alice", alice), ("bob", bob), ("alice/fork", fork), ("bob/carol", carol)]
    for _label, n in nodes:
        n.pulse()
    for label, n in nodes:
        s = n.status()
        a = s["last_audit"] or {}
        blocks = ", ".join(b["name"] for b in s["replaceability_blocks"]) or "-"
        audit = f"{a.get('status')} R={a.get('R')}" if a else "no audit"
        print(f"   {label:11} {s['node']}  {audit:16} blocks: {blocks}")

    shutil.rmtree(tmp)
    print("\nnetwork survived — every node is a branch that can die and be replaced.")


if __name__ == "__main__":
    main()
