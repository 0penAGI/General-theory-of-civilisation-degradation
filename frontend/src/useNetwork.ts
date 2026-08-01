import { useCallback, useEffect, useRef, useState } from "react";
import type { NetworkNode, NetworkPayload } from "./types";
import { OBSERVATORY_URL } from "./useObservatory";

export const API_BASE: string =
  (import.meta.env.VITE_API_BASE as string | undefined) ??
  (window.location.port === "8765"
    ? ""
    : "http://localhost:8765");

export interface NetworkState {
  conn: "connecting" | "online" | "offline";
  network: NetworkPayload | null;
  /** true when rendering the committed seed snapshot (observatory unreachable) */
  static: boolean;
  loading: boolean;
  error: string | null;
  refresh: () => void;
  createNode: (name: string) => Promise<NetworkNode>;
  forkNode: (
    id: string,
    name: string,
    statement: string,
  ) => Promise<NetworkNode>;
  adopt: (
    id: string,
    foreign: string,
    decision: string,
    statement: string,
  ) => Promise<NetworkNode>;
  seal: (id: string, statement: string, supersededBy: string) => Promise<NetworkNode>;
  pulse: (id: string, statement?: string) => Promise<NetworkNode>;
  exportBundle: (id: string) => void;
}

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, init);
  const body = (await res.json()) as T & { error?: string };
  if (!res.ok) {
    throw new Error(body?.error ?? `request failed (${res.status})`);
  }
  return body;
}

export function useNetwork(): NetworkState {
  const [conn, setConn] = useState<"connecting" | "online" | "offline">(
    "connecting",
  );
  const [network, setNetwork] = useState<NetworkPayload | null>(null);
  const [isStatic, setIsStatic] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  const applyLive = useCallback((payload: NetworkPayload) => {
    setNetwork(payload);
    setIsStatic(false);
    setLoading(false);
  }, []);

  const loadStaticSnapshot = useCallback(async () => {
    const res = await fetch("network.json");
    if (!res.ok) {
      throw new Error(`seed snapshot unavailable (${res.status})`);
    }
    return (await res.json()) as NetworkPayload;
  }, []);

  const reload = useCallback(() => {
    return api<NetworkPayload>("/api/network")
      .then(applyLive)
      .catch(() =>
        loadStaticSnapshot().then((payload) => {
          setNetwork(payload);
          setIsStatic(true);
          setLoading(false);
        }),
      )
      .catch((e) => setError(String(e)));
  }, [applyLive, loadStaticSnapshot]);

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
        }
        if (!cancelled) retry = setTimeout(connect, 2000);
      };
      ws.onmessage = (e) => {
        let msg: { type: string };
        try {
          msg = JSON.parse(e.data as string);
        } catch {
          return;
        }
        if (msg.type === "network") {
          applyLive((msg as unknown as { network: NetworkPayload }).network);
        } else if (msg.type === "hello") {
          const h = msg as { network?: NetworkPayload };
          if (h.network) applyLive(h.network);
        }
      };
    };

    // initial fetch (works even before WS is up; falls back to the committed
    // seed snapshot when the observatory is unreachable)
    reload().finally(() => setLoading(false));

    connect();
    return () => {
      cancelled = true;
      if (retry) clearTimeout(retry);
      ws?.close();
      wsRef.current = null;
    };
  }, [applyLive, reload]);

  const refresh = useCallback(() => {
    reload();
  }, [reload]);

  const createNode = useCallback(
    async (name: string) =>
      api<NetworkNode>("/api/nodes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name }),
      }),
    [],
  );

  const forkNode = useCallback(
    async (id: string, name: string, statement: string) =>
      api<NetworkNode>(`/api/nodes/${id}/fork`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, statement }),
      }),
    [],
  );

  const adopt = useCallback(
    async (id: string, foreign: string, decision: string, statement: string) =>
      api<NetworkNode>(`/api/nodes/${id}/adopt`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ foreign, decision, statement }),
      }),
    [],
  );

  const seal = useCallback(
    async (id: string, statement: string, supersededBy: string) =>
      api<NetworkNode>(`/api/nodes/${id}/seal`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ statement, superseded_by: supersededBy }),
      }),
    [],
  );

  const pulse = useCallback(
    async (id: string, statement = "crash-test of RULES.md") =>
      api<NetworkNode>(`/api/nodes/${id}/pulse`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ statement }),
      }),
    [],
  );

  const exportBundle = useCallback((id: string) => {
    window.open(`${API_BASE}/api/nodes/${id}/export`, "_blank");
  }, []);

  return {
    conn,
    network,
    static: isStatic,
    loading,
    error,
    refresh,
    createNode,
    forkNode,
    adopt,
    seal,
    pulse,
    exportBundle,
  };
}

export function nodeFingerprint(id: string): string {
  return id.slice(2, 10);
}
