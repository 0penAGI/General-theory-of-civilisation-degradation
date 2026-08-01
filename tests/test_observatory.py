"""Integration checks of the Network Observatory HTTP + WS API.

Runs a real ObservatoryServer on an ephemeral port against a temp root and
drives it over HTTP with the standard library only.

    python -m unittest discover -s tests -v
"""

import json
import os
import shutil
import sys
import tempfile
import threading
import unittest
import urllib.request
import urllib.error
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

import observatory  # noqa: E402
from adaptive_pluralism_protocol.protocol_node import init_node, ProtocolNode  # noqa: E402


class ObservatoryApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="obs-test-"))
        # seed a minimal committed network (public states, no keys)
        network = cls.tmp / "network"
        genesis = init_node(network / "genesis", "genesis")
        child = genesis.fork(network / "child", "branch away")
        genesis.seal("superseded", superseded_by=child.node_id)
        for name in ("genesis", "child"):
            app_dir = network / name / ".app"
            if app_dir.exists():
                shutil.rmtree(app_dir)
        server = observatory.ObservatoryServer(("127.0.0.1", 0), observatory.ObservatoryHandler, cls.tmp)
        server.dist = REPO / "frontend" / "dist"  # serve the real built portal
        cls.server = server
        cls.port = server.server_address[1]
        cls.thread = threading.Thread(target=server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def _get(self, path, as_json=True):
        with urllib.request.urlopen(f"http://127.0.0.1:{self.port}{path}", timeout=10) as r:
            body = r.read()
            return r.status, (json.loads(body) if as_json else body.decode("utf-8", "replace"))

    def _post(self, path, data):
        req = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{path}",
            data=json.dumps(data).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def test_hello_and_network(self):
        status, hello = self._get("/api/hello")
        self.assertEqual(status, 200)
        names = {n["name"] for n in hello["network"]["nodes"]}
        self.assertIn("genesis", names)
        self.assertIn("child", names)
        self.assertGreaterEqual(hello["network"]["stats"]["vanished"], 1)
        self.assertGreaterEqual(hello["network"]["stats"]["forks"], 1)

    def test_genesis_lifecycle(self):
        status, node = self._post("/api/nodes", {"name": "my-branch"})
        self.assertEqual(status, 201)
        self.assertEqual(node["source"], "local")
        self.assertEqual(node["name"], "my-branch")
        self.assertFalse(node["sealed"])
        self.assertIsNotNone(node["last_audit"])  # first crash-test ran
        my_id = node["id"]

        status, network = self._get("/api/network")
        self.assertEqual(network["stats"]["branches"], 3)
        self.assertIn(my_id, [n["id"] for n in network["nodes"]])

        # crash-test again
        status, node = self._post(f"/api/nodes/{my_id}/pulse", {})
        self.assertEqual(status, 200)
        self.assertEqual(node["decisions"], 3)  # declare + audit + audit

        # fork your own branch
        status, child = self._post(f"/api/nodes/{my_id}/fork",
                                   {"name": "child", "statement": "branch out"})
        self.assertEqual(status, 200)
        self.assertEqual(child["source"], "local")
        self.assertEqual(child["parent_node"], my_id)
        child_id = child["id"]

        # adopt from a committed seed branch
        status, network = self._get("/api/network")
        seed = next(n for n in network["nodes"] if n["source"] == "seed")
        seed_dec = seed["last_decision"]["id"]
        status, adopted = self._post(f"/api/nodes/{child_id}/adopt",
                                     {"foreign": seed["id"], "decision": seed_dec,
                                      "statement": "accept the seed branch"})
        self.assertEqual(status, 200)
        self.assertEqual(len(adopted["adopted"]), 1)

        # seal your branch — it vanishes, history stays
        status, sealed = self._post(f"/api/nodes/{my_id}/seal",
                                    {"statement": "superseded", "superseded_by": child_id})
        self.assertEqual(status, 200)
        self.assertTrue(sealed["sealed"])
        self.assertEqual(sealed["superseded_by"], child_id)

        # export still works after sealing (export requires a local key)
        status, bundle = self._get(f"/api/nodes/{my_id}/export")
        self.assertEqual(status, 200)
        self.assertEqual(bundle["app"]["node"], my_id)

    def test_seed_is_read_only(self):
        status, network = self._get("/api/network")
        seed = next(n for n in network["nodes"] if n["source"] == "seed")
        status, body = self._post(f"/api/nodes/{seed['id']}/fork",
                                  {"name": "x", "statement": "y"})
        self.assertEqual(status, 409)
        self.assertIn("read-only", body["error"])

    def test_frontend_index_served(self):
        status, html = self._get("/", as_json=False)
        self.assertEqual(status, 200)
        self.assertIn("<html", html.lower())


if __name__ == "__main__":
    unittest.main()
