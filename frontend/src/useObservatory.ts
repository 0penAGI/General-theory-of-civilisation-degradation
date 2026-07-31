import { useCallback, useEffect, useRef, useState } from "react";
import type {
  HelloMessage,
  PulseMessage,
  ServerMessage,
  VerdictMessage,
} from "./types";

export const OBSERVATORY_URL: string =
  (import.meta.env.VITE_OBSERVATORY_URL as string | undefined) ??
  "ws://localhost:8765";

export interface ObservatoryState {
  conn: "connecting" | "online" | "offline";
  hello: HelloMessage | null;
  pulses: PulseMessage[];
  verdict: VerdictMessage["report"] | null;
  status: VerdictMessage["status"] | null;
  running: boolean;
  scenario: string;
  selectedScenario: string;
  selectScenario: (id: string) => void;
  run: (scenario: string, seed?: number) => void;
  reset: () => void;
}

export function useObservatory(): ObservatoryState {
  const [conn, setConn] = useState<"connecting" | "online" | "offline">(
    "connecting",
  );
  const [hello, setHello] = useState<HelloMessage | null>(null);
  const [pulses, setPulses] = useState<PulseMessage[]>([]);
  const [verdict, setVerdict] = useState<VerdictMessage["report"] | null>(null);
  const [status, setStatus] = useState<VerdictMessage["status"] | null>(null);
  const [running, setRunning] = useState(false);
  const [scenario, setScenario] = useState("adaptive");
  const [selectedScenario, setSelectedScenario] = useState("adaptive");
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    let ws: WebSocket | null = null;
    let retry: ReturnType<typeof setTimeout> | undefined;
    let cancelled = false;

    const connect = () => {
      if (cancelled) return;
      setConn("connecting");
      try {
        ws = new WebSocket(OBSERVATORY_URL);
      } catch {
        setConn("offline");
        retry = setTimeout(connect, 2000);
        return;
      }
      wsRef.current = ws;
      ws.onopen = () => setConn("online");
      ws.onclose = () => {
        if (wsRef.current === ws) {
          setConn("offline");
          setRunning(false);
        }
        if (!cancelled) retry = setTimeout(connect, 2000);
      };
      ws.onmessage = (e) => {
        let msg: ServerMessage;
        try {
          msg = JSON.parse(e.data as string) as ServerMessage;
        } catch {
          return;
        }
        switch (msg.type) {
          case "hello":
            setHello(msg);
            if (msg.current) {
              setScenario(msg.current.scenario);
              setSelectedScenario(msg.current.scenario);
            }
            break;
          case "replay":
            if (msg.history.length > 0) setPulses(msg.history);
            if (msg.verdict) setVerdict(msg.verdict);
            break;
          case "run_start":
            setRunning(true);
            setVerdict(null);
            setStatus(null);
            setScenario(msg.scenario);
            setSelectedScenario(msg.scenario);
            setPulses([]);
            break;
          case "pulse":
            setPulses((prev) => [...prev, msg].slice(-400));
            break;
          case "verdict":
            setVerdict(msg.report);
            setStatus(msg.status);
            setRunning(false);
            break;
          case "error":
            console.warn("[observatory]", msg.message);
            break;
          default:
            break;
        }
      };
    };

    connect();
    return () => {
      cancelled = true;
      if (retry) clearTimeout(retry);
      ws?.close();
      wsRef.current = null;
    };
  }, []);

  const run = useCallback((scenarioId: string, seed = 1) => {
    const ws = wsRef.current;
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ action: "run", scenario: scenarioId, seed }));
    }
  }, []);

  const selectScenario = useCallback((id: string) => {
    setSelectedScenario(id);
  }, []);

  const reset = useCallback(() => {
    setPulses([]);
    setVerdict(null);
    setStatus(null);
    setRunning(false);
  }, []);

  return {
    conn,
    hello,
    pulses,
    verdict,
    status,
    running,
    scenario,
    selectedScenario,
    selectScenario,
    run,
    reset,
  };
}
