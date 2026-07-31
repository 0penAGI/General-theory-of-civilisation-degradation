#!/usr/bin/env python3
"""Civilization Observatory — a WebSocket server that streams live states of
the APP civilization simulator.

The reader is not asked to govern the simulation. The reader is invited to
observe its health. This server only observes and reports; it never accepts
commands that change the state of the world.

Standard library only (Python >= 3.10). No dependencies.

    python observatory.py            # ws://0.0.0.0:8765
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
except ImportError:
    from adaptive_pluralism_protocol import (
        build_scenario,
        default_events,
        CivilizationEngine,
        RealityEvent,
        scenario_report,
    )
    from adaptive_pluralism_protocol.civilization_simulator import compute_metrics

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

    def handshake(self):
        header = b""
        while b"\r\n\r\n" not in header:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise ConnectionError("handshake failed")
            header += chunk
        headers = {}
        for line in header.decode("latin-1").split("\r\n")[1:]:
            if ":" in line:
                k, v = line.split(":", 1)
                headers[k.strip().lower()] = v.strip()
        key = headers.get("sec-websocket-key", "")
        accept = base64.b64encode(
            hashlib.sha1((key + WS_MAGIC).encode()).digest()
        ).decode()
        self.sock.sendall(
            (
                "HTTP/1.1 101 Switching Protocols\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n"
                f"Sec-WebSocket-Accept: {accept}\r\n"
                "\r\n"
            ).encode()
        )

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

    def __init__(self, addr, handler):
        super().__init__(addr, handler)
        self.clients = set()
        self.lock = threading.Lock()
        self.running = False
        self.current = None
        self.history = []
        self.verdict = None
        self._stop = threading.Event()

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
            "name": "CIVILIZATION OBSERVATORY",
            "protocol": "APP v5.4",
            "pulses": PULSES,
            "agi_at": AGI_AT,
            "scenarios": [
                {"id": k, "desc": v["desc"], "immunity": v["immunity"]}
                for k, v in SCENARIOS.items()
            ],
            "running": self.running,
            "current": self.current,
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
    def handle(self):
        conn = WebSocketConnection(self.request, self.client_address)
        server = self.server
        try:
            conn.handshake()
        except (ConnectionError, OSError):
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
                elif action == "ping":
                    conn.send_text(json.dumps({"type": "pong"}))
        except (ConnectionError, OSError):
            pass
        finally:
            conn.close()
            with server.lock:
                server.clients.discard(conn)


def main():
    port = 8765
    if "--port" in sys.argv:
        port = int(sys.argv[sys.argv.index("--port") + 1])
    host = "0.0.0.0"
    server = ObservatoryServer((host, port), ObservatoryHandler)
    print("=" * 62)
    print("  CIVILIZATION OBSERVATORY — observe, do not govern")
    print(f"  WebSocket: ws://localhost:{port}")
    print("  Scenarios: " + ", ".join(SCENARIOS.keys()))
    print("=" * 62)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nObservatory closed.")
        server.shutdown()


if __name__ == "__main__":
    main()
