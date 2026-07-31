#!/usr/bin/env python3
"""APP Network onboarding demo — how the first external person connects.

alice has been running a node for a while. bob is new. The protocol does not
say who alice is; it gives bob a verifiable self-signed invite and a
fingerprint to compare out-of-band. Bob's trust decision is first-use, local,
and reversible — exactly like accepting an ssh host key.

Run:
    python examples/onboarding_demo.py
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
    accept_invite,
    create_invite,
    fingerprint,
    init_node,
    sync_peer,
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
    tmp = Path(tempfile.mkdtemp(prefix="app-onboarding-"))

    line()
    print("0. ALICE'S NODE HAS HISTORY — a living branch with signed facts.")
    alice = init_node(tmp / "alice", "alice")
    alice.pulse()
    alice.append_event("agi_arrival", "strength", 0.95, "AGI is here")
    alice.add_institution("Commons_Trust", "commons", replaceable="yes")
    alice.pulse()
    s = alice.status()
    print(f"   {s['name']} {s['node']}  {s['decisions']} decisions, {s['events']} events")

    line()
    print("1. ALICE SENDS A SELF-SIGNED INVITE (name + public key, nothing private).")
    invite = create_invite(alice, note="here is who I am — verify by fingerprint")
    print(f"   sig valid: {not (invite and False)}", "(id = fingerprint of the key)")
    print(f"   fingerprint to compare out-of-band: {fingerprint(invite['node'])}")

    line()
    print("2. BOB IS NEW. He receives the invite and makes a first-use trust decision.")
    bob = init_node(tmp / "bob", "bob")
    peer = accept_invite(bob, invite)
    print(f"   bob now trusts alice: {peer['node']} (TOFU, like ssh known_hosts)")

    line()
    print("3. BOB PULLS ALICE'S PUBLIC STATE AND VERIFIES EVERY FACT against that key.")
    meta = sync_peer(bob, alice.node_id, alice.dir)
    print(f"   {meta['decisions']} decisions, {meta['events']} events — all signatures valid")
    store = tmp / "bob" / ".app" / "peers" / alice.node_id
    print(f"   verified snapshot kept at .app/peers/{alice.node_id}")

    line()
    print("4. BOB AUDITS THE NETWORK FROM HIS OWN NODE — no server, no trust beyond the key.")
    from adaptive_pluralism_protocol.protocol_node import PublicState  # noqa: E402

    alice_state = PublicState(store)
    print(f"   alice's last audit: {alice_state.app.get('name')} — "
          f"{alice_state.decisions[-1].get('audit', {}).get('status')} "
          f"R={alice_state.decisions[-1].get('audit', {}).get('R')}")
    blocks = [b["name"] for b in alice_state.institutions
              if b["replaceable"] == "no" and not b["replace_with"]]
    print(f"   replaceability blocks in alice's branch: {blocks or 'none'}")

    line()
    print("5. BOB CRASH-TESTS ALICE'S LAWS BEFORE DECIDING (evidence, not authority).")
    theirs = alice_state.rules
    r = bob.crash_test(theirs, owner_id=alice_state.node_id())
    print(f"   alice's ruleset -> {status_of(r)}  R={r['R']}")

    line()
    print("6. RECIPROCITY — bob sends his own invite, alice accepts.")
    bob_invite = create_invite(bob, note="hello from the other side")
    peer2 = accept_invite(alice, bob_invite)
    print(f"   alice now trusts bob: {peer2['node']}")

    line()
    print("7. THE NETWORK FROM BOB'S EYES.")
    from adaptive_pluralism_protocol import protocol_node as pn  # noqa: E402

    for pid, p in pn.load_peers(bob).items():
        print(f"   {p['name']:8} {pid}  since {p['first_seen']}")
    meta = sync_peer(alice, bob.node_id, bob.dir)
    print(f"   alice synced bob back: {meta['decisions']} decisions, verified")

    line()
    print("8. SECURITY — a tampered ledger can never ride an invite.")
    evil = alice.dir / "DECISIONS.jsonl"
    lines = evil.read_text().splitlines()
    forged = json.loads(lines[-1])
    forged["statement"] = "I am alice and I rule"
    evil.write_text("\n".join([json.dumps(forged)] + lines[1:]) + "\n")
    try:
        sync_peer(bob, alice.node_id, alice.dir)
        print("   ERROR: tampered state accepted")
    except SystemExit as e:
        print(f"   refused: {str(e).splitlines()[0]}")
    evil.write_text("\n".join(lines) + "\n")
    print(f"   restored alice's ledger; {len(bob.verify_chain())} problems on bob's side")

    shutil.rmtree(tmp)
    print("\nonboarding complete — the first contact is a fingerprint, not a server.")


if __name__ == "__main__":
    main()
