#!/usr/bin/env python3
"""Network Observatory — HTTP + WebSocket server for the APP network.

The observatory watches the network of protocol nodes: real branches with
real identities, forks, accepted ideas, sealed (vanished) branches. It also
keeps the original civilization-simulator stream.

What a reader can do:
    • look at the network    (lineage, forks, adoptions, vanished branches)
    • create a node          (genesis: the first node knows nothing)
    • crash-test their node  (pulse)
    • fork their own branch
    • adopt a verified foreign branch's idea
    • retire their branch    (seal — it vanishes, its history does not)

The observatory never rewrites a signed decision. It can only append.

Serves:
    http://localhost:8765/         the web portal (frontend/dist)
    ws://localhost:8765/           the live stream (sim + network events)

Standard library only (Python >= 3.10).

    python observatory.py              # http://localhost:8765
    python observatory.py --port 9000
"""

import base64
import hashlib
import json
import os
import socket
import socketserver
import struct
import sys
import threading
import time
from pathlib import Path

try:
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))
    from adaptive_pluralism_protocol import (
        build_scenario,
        default_events,
        CivilizationEngine,
        RealityEvent,
        scenario_report,
    )
    from adaptive_pluralism_protocol.civilization_simulator import compute_metrics
    from adaptive_pluralism_protocol.protocol_node import (
        ProtocolNode,
        PublicState,
        init_node,
    )
except ImportError:
    from adaptive_pluralism_protocol import (
        build_scenario,
        default_events,
        CivilizationEngine,
        RealityEvent,
        scenario_report,
    )
    from adaptive_pluralism_protocol.civilization_simulator import compute_metrics
    from adaptive_pluralism_protocol.protocol_node import (
        ProtocolNode,
        PublicState,
        init_node,
    )

WS_MAGIC = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

SCENARIOS = {
    "monolith": {"immunity": False, "hostile": False, "desc": "single institution, no immunity"},
    "plural": {"immunity": False, "hostile": False, "desc": "many institutions, no structural immunity"},
    "adaptive": {"immunity": True, "hostile": False, "desc": "plural + APP immunity active"},
    "adaptive_h": {"immunity": True, "hostile": True, "desc": "adaptive vs hostile AGI"},
    "meta": {"immunity": True, "hostile": True, "desc": "meta: protocol proves it should be replaced"},
}

PULSES = 40
AGI_AT = 12
PULSE_DELAY = 0.08
AUDIT_EVERY = 4
MAX_HISTORY = 400

CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".mjs": "text/javascript; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".ico": "image/x-icon",
    ".json": "application/json",
    ".webmanifest": "application/manifest+json",
    ".woff2": "font/woff2",
    ".ttf": "font/ttf",
}


class WebSocketConnection:
    """A single RFC 6455 WebSocket connection (server side, no dependencies)."""

    def __init__(self, sock, addr):
        self.sock = sock
        self.addr = addr
        self.sock.settimeout(2.0)
        self.closed = False

    def _read_exact(self, n):
        buf = b""
        while len(buf) < n:
            chunk = self.sock.recv(n - len(buf))
            if not chunk:
                raise ConnectionError("socket closed")
            buf += chunk
        return buf

    def send_text(self, text):
        if self.closed:
            return False
        payload = text.encode("utf-8")
        n = len(payload)
        if n < 126:
            frame = struct.pack("!BB", 0x81, n) + payload
        elif n < 65536:
            frame = struct.pack("!BBH", 0x81, 126, n) + payload
        else:
            frame = struct.pack("!BBQ", 0x81, 127, n) + payload
        try:
            self.sock.sendall(frame)
            return True
        except OSError:
            self.closed = True
            return False

    def recv_text(self):
        try:
            b0, b1 = self._read_exact(2)
        except (ConnectionError, socket.timeout, OSError):
            return None
        opcode = b0 & 0x0F
        length = b1 & 0x7F
        masked = b1 & 0x80
        if length == 126:
            length = struct.unpack("!H", self._read_exact(2))[0]
        elif length == 127:
            length = struct.unpack("!Q", self._read_exact(8))[0]
        mask = self._read_exact(4) if masked else None
        payload = self._read_exact(length)
        if mask:
            payload = bytes(
                b ^ mask[i % 4] for i, b in enumerate(payload)
            )
        if opcode in (0x8, 0x9, 0xA):
            return None
        if opcode == 0x1:
            return payload.decode("utf-8")
        return None

    def close(self):
        self.closed = True
        try:
            self.sock.close()
        except OSError:
            pass


class ObservatoryServer(socketserver.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, addr, handler, root: Path):
        super().__init__(addr, handler)
        self.root = root.resolve()
        self.network_dir = self.root / "network"
        self.nodes_dir = self.root / "nodes"
        self.nodes_dir.mkdir(exist_ok=True)
        self.dist = self.root / "frontend" / "dist"
        self.clients = set()
        self.lock = threading.Lock()
        self.running = False
        self.current = None
        self.history = []
        self.verdict = None
        self._stop = threading.Event()
        self._netmap = {}
        self.reindex()

    # ------------------------------------------------------------------
    # network scan
    # ------------------------------------------------------------------

    def reindex(self):
        mapping = {}
        for source, base in (("seed", self.network_dir), ("local", self.nodes_dir)):
            if not base.exists():
                continue
            for entry in sorted(base.iterdir()):
                if not entry.is_dir() or entry.name.startswith("."):
                    continue
                if not (entry / "APP.md").exists():
                    continue
                try:
                    state = PublicState(entry)
                except Exception:
                    continue
                mapping[state.node_id()] = {"dir": entry, "source": source}
        self._netmap = mapping
        return mapping

    def node_view(self, node_id: str) -> dict:
        info = self._netmap.get(node_id)
        if info is None:
            raise KeyError(f"unknown node: {node_id}")
        state = PublicState(info["dir"])
        decisions = state.decisions
        last = decisions[-1] if decisions else None
        sealed = bool(last and last["kind"] == "seal")
        audits = [d["audit"] for d in decisions if d["kind"] == "audit"]
        return {
            "id": state.node_id(),
            "name": state.app.get("name", "?"),
            "key": state.app.get("key", ""),
            "parent_node": state.app.get("parent_node", "-"),
            "forked_from": state.app.get("forked_from", "-"),
            "source": info["source"],
            "decisions": len(decisions),
            "events": len(state.events),
            "institutions": state.institutions,
            "rules": state.rules,
            "sealed": sealed,
            "superseded_by": last.get("superseded_by", "") if sealed else "",
            "last_decision": last,
            "last_audit": audits[-1] if audits else None,
            "rule_changes": [d for d in decisions if "rules" in d],
            "adopted": [d for d in decisions if d["kind"] == "adopt"],
            "blocks": [
                i for i in state.institutions
                if i.get("replaceable") == "no" and not i.get("replace_with")
            ],
        }

    def network_payload(self) -> dict:
        self.reindex()
        nodes = [self.node_view(nid) for nid in sorted(self._netmap)]
        seen: set = set()
        ideas = []
        for nid in sorted(self._netmap):
            for d in self.node_view(nid)["adopted"]:
                key = (d.get("adopted_from", "-"), d.get("adopted_node", "-"))
                if key in seen:
                    continue
                seen.add(key)
                ideas.append({
                    "node": nid,
                    "name": d["statement"],
                    "adopted_from": d.get("adopted_from", "-"),
                    "adopted_node": d.get("adopted_node", "-"),
                    "time": d.get("time", ""),
                })
        vanished = [
            {"id": nid, "name": self.node_view(nid)["name"],
             "superseded_by": self.node_view(nid)["superseded_by"]}
            for nid in sorted(self._netmap)
            if self.node_view(nid)["sealed"]
        ]
        return {
            "nodes": nodes,
            "ideas": ideas,
            "vanished": vanished,
            "stats": {
                "branches": len(nodes),
                "live": sum(1 for n in nodes if not n["sealed"]),
                "vanished": len(vanished),
                "ideas": len(ideas),
                "forks": sum(1 for n in nodes if n["parent_node"] != "-"),
            },
        }

    def broadcast_network(self):
        payload = {"type": "network", "network": self.network_payload()}
        self.broadcast(payload)
        return payload["network"]

    # ------------------------------------------------------------------
    # node mutations (append-only — never rewrite)
    # ------------------------------------------------------------------

    def _local_node(self, node_id: str) -> ProtocolNode:
        info = self._netmap.get(node_id)
        if info is None:
            raise KeyError(f"unknown node: {node_id}")
        if info["source"] != "local":
            raise ValueError("that branch is a committed seed — it is read-only, adopt from it instead")
        return ProtocolNode(info["dir"])

    def _foreign_state(self, node_id: str) -> PublicState:
        info = self._netmap.get(node_id)
        if info is None:
            raise KeyError(f"unknown node: {node_id}")
        return PublicState(info["dir"])

    @staticmethod
    def _set_name(dirp: Path, name: str):
        lines = []
        for line in (dirp / "APP.md").read_text().splitlines():
            if line.startswith("name:"):
                lines.append(f"name: {name}")
            else:
                lines.append(line)
        (dirp / "APP.md").write_text("\n".join(lines) + "\n")

    def create_node(self, name: str) -> dict:
        staging = self.nodes_dir / f".staging-{time.time_ns()}"
        node = init_node(staging, name)
        target = self.nodes_dir / node.node_id
        os.rename(staging, target)
        node = ProtocolNode(target)
        node.pulse("first crash-test of the founding laws")
        self.reindex()
        self.broadcast_network()
        return self.node_view(node.node_id)

    def fork_node(self, node_id: str, name: str, statement: str) -> dict:
        parent = self._local_node(node_id)
        staging = self.nodes_dir / f".staging-{time.time_ns()}"
        child = parent.fork(staging, statement)
        if name:
            self._set_name(staging, name)
        target = self.nodes_dir / child.node_id
        os.rename(staging, target)
        child = ProtocolNode(target)
        self.reindex()
        self.broadcast_network()
        return self.node_view(child.node_id)

    def adopt_node(self, node_id: str, foreign_id: str, decision_id: str, statement: str) -> dict:
        mine = self._local_node(node_id)
        foreign = self._foreign_state(foreign_id)
        mine.adopt(foreign.dir, decision_id, statement)
        mine.pulse("accepted idea crash-tested")
        self.reindex()
        self.broadcast_network()
        return self.node_view(node_id)

    def seal_node(self, node_id: str, statement: str, superseded_by: str = "") -> dict:
        node = self._local_node(node_id)
        node.seal(statement, superseded_by)
        self.reindex()
        self.broadcast_network()
        return self.node_view(node_id)

    def pulse_node(self, node_id: str, statement: str = "crash-test of RULES.md") -> dict:
        node = self._local_node(node_id)
        node.pulse(statement)
        self.reindex()
        self.broadcast_network()
        return self.node_view(node_id)

    def export_node(self, node_id: str) -> dict:
        return self._local_node(node_id).export()

    # ------------------------------------------------------------------
    # simulator stream
    # ------------------------------------------------------------------

    def broadcast(self, message):
        text = json.dumps(message)
        dead = []
        with self.lock:
            for c in list(self.clients):
                if not c.send_text(text):
                    dead.append(c)
            for c in dead:
                self.clients.discard(c)

    def hello(self):
        return {
            "type": "hello",
            "name": "NETWORK OBSERVATORY",
            "protocol": "APP v5.4",
            "pulses": PULSES,
            "agi_at": AGI_AT,
            "scenarios": [
                {"id": k, "desc": v["desc"], "immunity": v["immunity"]}
                for k, v in SCENARIOS.items()
            ],
            "running": self.running,
            "current": self.current,
            "network": self.network_payload(),
        }

    def request_run(self, scenario, seed):
        if scenario not in SCENARIOS:
            return False, f"unknown scenario: {scenario}"
        self._stop.set()
        threading.Thread(
            target=self._run_worker,
            args=(scenario, int(seed)),
            daemon=True,
        ).start()
        return True, "started"

    def _run_worker(self, scenario, seed):
        if self.running:
            self._stop.wait(0.05)
        self._stop.clear()
        self.running = True
        self.current = {"scenario": scenario, "seed": seed}
        self.history = []
        self.verdict = None
        self.broadcast(
            {
                "type": "run_start",
                "scenario": scenario,
                "seed": seed,
                "pulses": PULSES,
                "agi_at": AGI_AT,
            }
        )
        cfg = SCENARIOS[scenario]
        civ = build_scenario(
            scenario,
            cfg["immunity"],
            seed=seed,
            hostile_agi=cfg["hostile"],
        )
        engine = CivilizationEngine(self_immunity=civ.self_immunity)
        events = default_events(PULSES, AGI_AT)
        prev = None
        last_audit = None
        try:
            for p in range(PULSES):
                if self._stop.is_set():
                    break
                event = events.get(p, RealityEvent("routine", 0.05))
                engine.pulse(civ, event)
                if p % AUDIT_EVERY == 0 or p == PULSES - 1:
                    last_audit = civ.measurers.audit(civ, mutate=False)
                snap = self._snapshot(civ, event, last_audit, prev)
                prev = snap
                self.history.append(snap)
                if len(self.history) > MAX_HISTORY:
                    self.history = self.history[-MAX_HISTORY:]
                self.broadcast(snap)
                time.sleep(PULSE_DELAY)
            report = scenario_report(civ)
            self.verdict = report
            status = (
                "CRYSTALLIZED"
                if report["crystallized"]
                else "SURVIVED"
                if report["survived"]
                else "DEGRADED"
            )
            self.broadcast(
                {
                    "type": "verdict",
                    "scenario": scenario,
                    "seed": seed,
                    "status": status,
                    "report": report,
                }
            )
        finally:
            self.running = False
            self.current = None
            self._stop.clear()

    def _snapshot(self, civ, event, audit, prev):
        snap = {
            "type": "pulse",
            "scenario": civ.name.lower(),
            "seed": getattr(civ, "seed", 1),
            "pulse": civ.pulse,
            "event": event.name,
            "event_intensity": round(event.intensity, 2),
            "metrics": compute_metrics(civ),
            "institutions": [
                {
                    "name": s.name,
                    "kind": s.kind,
                    "function": s.function,
                    "inversion": round(s.inversion, 3),
                    "adaptation_rate": round(s.adaptation_rate, 3),
                    "extraction_rate": round(s.extraction_rate, 3),
                    "efficiency": s.efficiency,
                    "generation": s.generation,
                    "last_delivered": round(s.last_delivered, 2),
                    "last_extract": round(s.last_extract, 2),
                }
                for s in civ.institutions
            ],
            "agents": [
                {
                    "name": a.name,
                    "strategy": a.strategy,
                    "generation": a.generation,
                    "scars": len(a.scars),
                }
                for a in civ.agents
            ],
            "audit": audit,
            "protocol_gen": civ.protocol.generation if civ.protocol else 1,
            "protocol_rules": civ.protocol.rules if civ.protocol else {},
            "crisis_damage": round(civ.crisis_damage, 3),
            "parasitism_debt": round(civ.parasitism_debt, 3),
        }
        changes = self._changes(prev, snap)
        if changes:
            snap["changes"] = changes
        return snap

    def _changes(self, prev, snap):
        if prev is None:
            return []
        changes = []
        prev_inst = {i["name"]: i for i in prev["institutions"]}
        for i in snap["institutions"]:
            old = prev_inst.get(i["name"])
            if old is None:
                changes.append(f"structure born: {i['name']}")
            elif old["generation"] < i["generation"]:
                changes.append(f"structure replaced: {i['name']} -> gen {i['generation']}")
        if prev["protocol_gen"] < snap["protocol_gen"]:
            changes.append(
                f"protocol revised -> v{snap['protocol_gen']} "
                f"(rules tightened)"
            )
        if prev.get("audit") and snap.get("audit"):
            replaced = snap["audit"].get("replaced") or []
            for name in replaced:
                if name not in (prev["audit"].get("replaced") or []):
                    changes.append(f"measurer replaced: {name}")
        return changes


class ObservatoryHandler(socketserver.BaseRequestHandler):
    def _read_header_block(self):
        header = b""
        while b"\r\n\r\n" not in header:
            chunk = self.request.recv(4096)
            if not chunk:
                raise ConnectionError("connection closed")
            header += chunk
        head, _, rest = header.partition(b"\r\n\r\n")
        lines = head.decode("latin-1").split("\r\n")
        method, path, version = lines[0].split(" ", 2)
        headers = {}
        for line in lines[1:]:
            if ":" in line:
                k, v = line.split(":", 1)
                headers[k.strip().lower()] = v.strip()
        return method, path, version, headers, rest

    def handle(self):
        server: ObservatoryServer = self.server
        conn = WebSocketConnection(self.request, self.client_address)
        try:
            method, path, version, headers, body_head = self._read_header_block()
        except (ConnectionError, OSError, ValueError):
            conn.close()
            return

        if headers.get("upgrade", "").lower() == "websocket":
            self._ws_handle(conn, headers, server)
            return

        # ── HTTP request ──
        if method in ("POST", "PUT", "PATCH"):
            length = int(headers.get("content-length", "0") or 0)
            body = body_head + (conn._read_exact(length - len(body_head)) if length > len(body_head) else b"")
        else:
            body = b""
        try:
            self._http_handle(conn, method, path, headers, body, server)
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # WebSocket
    # ------------------------------------------------------------------

    def _ws_handle(self, conn, headers, server: ObservatoryServer):
        key = headers.get("sec-websocket-key", "")
        accept = base64.b64encode(
            hashlib.sha1((key + WS_MAGIC).encode()).digest()
        ).decode()
        try:
            conn.sock.sendall(
                (
                    "HTTP/1.1 101 Switching Protocols\r\n"
                    "Upgrade: websocket\r\n"
                    "Connection: Upgrade\r\n"
                    f"Sec-WebSocket-Accept: {accept}\r\n"
                    "\r\n"
                ).encode()
            )
        except OSError:
            conn.close()
            return
        conn.sock.settimeout(None)
        with server.lock:
            server.clients.add(conn)
        conn.send_text(json.dumps(server.hello()))
        if server.history:
            conn.send_text(
                json.dumps(
                    {
                        "type": "replay",
                        "history": server.history,
                        "verdict": server.verdict,
                    }
                )
            )
        try:
            while True:
                text = conn.recv_text()
                if text is None:
                    break
                try:
                    msg = json.loads(text)
                except json.JSONDecodeError:
                    continue
                action = msg.get("action")
                if action == "run":
                    ok, reason = server.request_run(
                        msg.get("scenario", "adaptive"),
                        msg.get("seed", 1),
                    )
                    if not ok:
                        conn.send_text(
                            json.dumps({"type": "error", "message": reason})
                        )
                elif action == "network":
                    conn.send_text(
                        json.dumps({"type": "network", "network": server.network_payload()})
                    )
                elif action == "ping":
                    conn.send_text(json.dumps({"type": "pong"}))
        except (ConnectionError, OSError):
            pass
        finally:
            conn.close()
            with server.lock:
                server.clients.discard(conn)

    # ------------------------------------------------------------------
    # HTTP
    # ------------------------------------------------------------------

    def _send(self, conn, status, content_type, body, headers=None):
        code, reason = status
        resp = f"HTTP/1.1 {code} {reason}\r\n"
        resp += f"Content-Type: {content_type}\r\n"
        resp += f"Content-Length: {len(body)}\r\n"
        resp += "Connection: close\r\n"
        resp += "Access-Control-Allow-Origin: *\r\n"
        if headers:
            for k, v in headers.items():
                resp += f"{k}: {v}\r\n"
        resp += "\r\n"
        try:
            conn.sock.sendall(resp.encode("latin-1") + body)
        except OSError:
            pass

    def _json(self, conn, status, obj, headers=None):
        body = json.dumps(obj, indent=1).encode("utf-8")
        self._send(conn, status, "application/json; charset=utf-8", body, headers)

    def _http_handle(self, conn, method, path, headers, body, server: ObservatoryServer):
        if method == "OPTIONS":
            conn.sock.sendall(
                (
                    "HTTP/1.1 204 No Content\r\n"
                    "Content-Length: 0\r\n"
                    "Access-Control-Allow-Origin: *\r\n"
                    "Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n"
                    "Access-Control-Allow-Headers: Content-Type\r\n"
                    "\r\n"
                ).encode()
            )
            return

        if path.startswith("/api/"):
            self._api(conn, method, path, body, server)
            return
        if method != "GET":
            self._json(conn, (405, "Method Not Allowed"), {"error": "method not allowed"})
            return
        self._static(conn, path, server)

    # ── REST ──

    def _api(self, conn, method, path, body, server: ObservatoryServer):
        parts = [p for p in path.split("?")[0].split("/") if p]
        try:
            if parts == ["api", "hello"] and method == "GET":
                self._json(conn, (200, "OK"), server.hello())
                return
            if parts == ["api", "network"] and method == "GET":
                self._json(conn, (200, "OK"), server.network_payload())
                return
            if parts == ["api", "nodes"] and method == "GET":
                self._json(conn, (200, "OK"), {
                    "nodes": [server.node_view(nid) for nid in sorted(server._netmap)]
                })
                return
            if parts == ["api", "nodes"] and method == "POST":
                data = self._payload(body)
                name = (data.get("name") or "").strip() or "unnamed"
                view = server.create_node(name)
                self._json(conn, (201, "Created"), view)
                return
            if len(parts) == 3 and parts[:2] == ["api", "nodes"] and method == "GET":
                self._json(conn, (200, "OK"), server.node_view(parts[2]))
                return
            if len(parts) == 4 and parts[:2] == ["api", "nodes"]:
                node_id, action = parts[2], parts[3]
                if action == "export" and method == "GET":
                    bundle = server.export_node(node_id)
                    self._json(conn, (200, "OK"), bundle, {
                        "Content-Disposition": f'attachment; filename="{node_id}.bundle.json"',
                    })
                    return
                if action in ("fork", "adopt", "seal", "pulse") and method == "POST":
                    data = self._payload(body)
                    if action == "fork":
                        view = server.fork_node(node_id, (data.get("name") or "").strip(),
                                                data.get("statement", "fork to test a hypothesis"))
                    elif action == "adopt":
                        view = server.adopt_node(node_id, data.get("foreign", ""),
                                                 data.get("decision", ""),
                                                 data.get("statement", "adopt a verified branch"))
                    elif action == "seal":
                        view = server.seal_node(node_id, data.get("statement", "branch retired"),
                                                data.get("superseded_by", ""))
                    else:
                        view = server.pulse_node(node_id, data.get("statement", "crash-test of RULES.md"))
                    self._json(conn, (200, "OK"), view)
                    return
        except KeyError as e:
            self._json(conn, (404, "Not Found"), {"error": str(e)})
            return
        except ValueError as e:
            self._json(conn, (409, "Conflict"), {"error": str(e)})
            return
        except SystemExit as e:
            self._json(conn, (400, "Bad Request"), {"error": str(e)})
            return
        except Exception as e:  # noqa: BLE001
            self._json(conn, (500, "Internal Server Error"), {"error": f"{e}"})
            return
        self._json(conn, (404, "Not Found"), {"error": f"no such route: {path}"})

    @staticmethod
    def _payload(body: bytes) -> dict:
        if not body:
            return {}
        try:
            return json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            return {}

    # ── static ──

    def _static(self, conn, path, server: ObservatoryServer):
        rel = path.lstrip("/") or "index.html"
        is_asset = rel.startswith("assets/")
        if not is_asset and not rel.startswith("index"):
            rel = "index.html"
        target = (server.dist / rel).resolve()
        if not str(target).startswith(str(server.dist.resolve())):
            self._send(conn, (404, "Not Found"), "text/plain", b"forbidden")
            return
        if not target.exists():
            if is_asset:
                self._send(conn, (404, "Not Found"), "text/plain", b"not found")
                return
            target = server.dist / "index.html"
            if not target.exists():
                self._send(conn, (404, "Not Found"), "text/plain",
                           b"frontend not built - run: cd frontend && npm run build")
                return
        ctype = CONTENT_TYPES.get(target.suffix.lower(), "application/octet-stream")
        try:
            self._send(conn, (200, "OK"), ctype, target.read_bytes())
        except OSError:
            self._send(conn, (500, "Internal Server Error"), "text/plain", b"read error")


def main():
    port = 8765
    if "--port" in sys.argv:
        port = int(sys.argv[sys.argv.index("--port") + 1])
    root = Path(__file__).resolve().parent
    host = "0.0.0.0"
    server = ObservatoryServer((host, port), ObservatoryHandler, root)
    print("=" * 62)
    print("  NETWORK OBSERVATORY — watch the branches, join the network")
    print(f"  Portal:    http://localhost:{port}")
    print(f"  WebSocket: ws://localhost:{port}")
    print(f"  Network:   {server.network_dir}")
    print(f"  Local:     {server.nodes_dir}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nObservatory closed.")
        server.shutdown()


if __name__ == "__main__":
    main()
