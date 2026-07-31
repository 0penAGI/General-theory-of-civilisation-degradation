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
    import_bundle,
    init_node,
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


if __name__ == "__main__":
    unittest.main()
