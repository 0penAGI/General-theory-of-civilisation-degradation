"""Regression checks of the APP node (participation layer).

Run from the repository root:
    python -m unittest discover -s tests -v
or:
    python -m pytest tests
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from adaptive_pluralism_protocol.protocol_node import (  # noqa: E402
    ProtocolNode,
    PublicState,
    accept_invite,
    create_invite,
    import_bundle,
    init_node,
    load_peers,
    save_peers,
    sync_peer,
    verify_invite,
)


class ProtocolNodeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="app-node-test-"))
        self.addCleanup(self._clean)
        self.a = init_node(self.tmp / "a", "alice")

    def _clean(self):
        import shutil

        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_genesis_and_verification(self):
        d = self.a.decisions()
        self.assertEqual(len(d), 1)
        self.assertEqual(d[0]["kind"], "declare")
        self.assertEqual(self.a.verify_chain(), [])

    def test_tamper_detection(self):
        ledger = self.tmp / "a" / "DECISIONS.jsonl"
        lines = ledger.read_text().splitlines()
        forged = json.loads(lines[0])
        forged["statement"] = "forged"
        ledger.write_text(json.dumps(forged) + "\n")
        problems = self.a.verify_chain()
        self.assertEqual(len(problems), 1)
        self.assertIn("id does not match", problems[0])

    def test_identity_is_the_key(self):
        other = init_node(self.tmp / "b", "bob")
        self.assertNotEqual(self.a.node_id, other.node_id)
        # a node id must be its public key fingerprint — no key, no id
        self.assertEqual(len(self.a.node_id), 2 + 32)

    def test_chain_links_every_decision(self):
        self.a.append_decision("declare", "second")
        self.a.append_decision("amend", "third")
        ids = [d["id"] for d in self.a.decisions()]
        parents = [d["parent"] for d in self.a.decisions()]
        self.assertEqual(parents, ["-", ids[0], ids[1]])
        self.assertEqual(self.a.verify_chain(), [])

    def test_fork_keeps_history_new_identity(self):
        self.a.append_decision("declare", "pre-fork")
        fork = self.a.fork(self.tmp / "fork", "branch away")
        self.assertNotEqual(fork.node_id, self.a.node_id)
        # full history carried, plus the signed fork decision
        self.assertEqual(len(fork.decisions()), len(self.a.decisions()) + 1)
        self.assertEqual(fork.verify_chain(), [])
        last = fork.last_decision()
        self.assertEqual(last["kind"], "fork")
        self.assertEqual(last["adopted_node"], self.a.node_id)

    def test_adopt_replaces_laws_keeps_lineage(self):
        fork = self.a.fork(self.tmp / "fork", "branch away")
        fork.amend_rules({"self_immunity": "no"}, "test no immunity")
        foreign_last = fork.last_decision()
        adopted = self.a.adopt(self.tmp / "fork", foreign_last["id"], "adopt the fork")
        self.assertEqual(self.a.read_rules()["self_immunity"], "no")
        self.assertEqual(adopted["kind"], "adopt")
        self.assertEqual(adopted["adopted_from"], foreign_last["id"])
        self.assertEqual(adopted["adopted_node"], fork.node_id)
        self.assertEqual(self.a.verify_chain(), [])
        # genesis snapshots the pre-adoption laws; the adopt snapshots the new ones
        decisions = self.a.decisions()
        self.assertEqual(decisions[0]["rules"]["self_immunity"], "yes")
        self.assertEqual(adopted["rules"]["self_immunity"], "no")

    def test_import_refuses_tampered_bundle(self):
        bundle = self.a.export()
        tampered = json.loads(json.dumps(bundle))
        tampered["decisions"][0]["statement"] = "forged"
        with self.assertRaises(SystemExit):
            import_bundle(tampered, self.tmp / "evil")

    def test_import_restores_identity_and_history(self):
        bundle = self.a.export()
        self.a.append_decision("amend", "after export")
        copy = import_bundle(bundle, self.tmp / "copy")
        # the import is the same node: same id, same key, same lineage
        self.assertEqual(copy.node_id, self.a.node_id)
        self.assertEqual(copy.verify_chain(), [])
        self.assertEqual(len(copy.decisions()), len(bundle["decisions"]))

    def test_replaceability_blocks(self):
        self.a.add_institution("Commons_Trust", "commons", replaceable="yes")
        self.a.add_institution("The_Leviathan", "governance", replaceable="no")
        blocks = self.a.replaceability_blocks()
        self.assertEqual([b["name"] for b in blocks], ["The_Leviathan"])
        self.a.add_institution("City_Network", "infrastructure", replaceable="no",
                               replace_with="The_Leviathan")
        self.assertEqual([b["name"] for b in self.a.replaceability_blocks()], ["The_Leviathan"])

    # -- onboarding ------------------------------------------------------

    def test_invite_is_self_signed(self):
        invite = create_invite(self.a)
        self.assertEqual(verify_invite(invite), [])
        self.assertEqual(invite["node"], self.a.node_id)

    def test_invite_tamper_detected(self):
        invite = create_invite(self.a)
        invite["name"] = "mallory"
        self.assertEqual(len(verify_invite(invite)), 1)

    def test_first_contact_trust_on_first_use(self):
        b = init_node(self.tmp / "b", "bob")
        peer = accept_invite(b, create_invite(self.a))
        self.assertEqual(load_peers(b)[self.a.node_id]["name"], "alice")
        self.assertEqual(peer["key"], load_peers(b)[self.a.node_id]["key"])

    def test_peer_key_mismatch_refused(self):
        b = init_node(self.tmp / "b", "bob")
        evil = init_node(self.tmp / "evil", "mallory")
        # a peer record already bound to alice's id, but with a different key
        peers = load_peers(b)
        peers[self.a.node_id] = {
            "name": "alice", "node": self.a.node_id,
            "key": create_invite(evil)["key"],
        }
        save_peers(b, peers)
        with self.assertRaises(SystemExit):
            accept_invite(b, create_invite(self.a))

    def test_impersonation_refused(self):
        b = init_node(self.tmp / "b", "bob")
        accept_invite(b, create_invite(self.a))
        evil = init_node(self.tmp / "evil", "mallory")
        forged = create_invite(evil)
        forged["node"] = self.a.node_id  # claim alice's identity with her own key
        forged["name"] = "alice"
        with self.assertRaises(SystemExit):
            accept_invite(b, forged)

    def test_sync_verifies_and_stores_snapshot(self):
        self.a.append_decision("declare", "history")
        b = init_node(self.tmp / "b", "bob")
        accept_invite(b, create_invite(self.a))
        meta = sync_peer(b, self.a.node_id, self.a.dir)
        self.assertTrue(meta["verified"])
        self.assertEqual(meta["decisions"], len(self.a.decisions()))
        store = self.tmp / "b" / ".app" / "peers" / self.a.node_id
        self.assertTrue((store / ".verified.json").exists())
        # the stored snapshot is itself a verified public state
        self.assertEqual(PublicState(store).verify_chain(), [])

    def test_sync_unknown_peer_refused(self):
        b = init_node(self.tmp / "b", "bob")
        with self.assertRaises(SystemExit):
            sync_peer(b, self.a.node_id, self.a.dir)

    def test_sync_tampered_state_refused(self):
        b = init_node(self.tmp / "b", "bob")
        accept_invite(b, create_invite(self.a))
        ledger = self.tmp / "a" / "DECISIONS.jsonl"
        lines = ledger.read_text().splitlines()
        forged = json.loads(lines[-1])
        forged["statement"] = "I rule"
        ledger.write_text("\n".join([json.dumps(forged)] + lines[1:]) + "\n")
        with self.assertRaises(SystemExit):
            sync_peer(b, self.a.node_id, self.a.dir)
        ledger.write_text("\n".join(lines) + "\n")

    def test_adopt_from_synced_public_state_without_private_key(self):
        self.a.amend_rules({"self_immunity": "no"}, "alice's laws")
        b = init_node(self.tmp / "b", "bob")
        accept_invite(b, create_invite(self.a))
        sync_peer(b, self.a.node_id, self.a.dir)
        store = self.tmp / "b" / ".app" / "peers" / self.a.node_id
        b_before = b.read_rules()["self_immunity"]
        last = PublicState(store).last_decision()
        adopted = b.adopt(store, last["id"], "adopt alice's branch")
        self.assertEqual(b.read_rules()["self_immunity"], "no")
        self.assertEqual(adopted["adopted_node"], self.a.node_id)
        # the import never touched alice's private key — only verifiable facts
        self.assertNotEqual(b_before, "no")


if __name__ == "__main__":
    unittest.main()
