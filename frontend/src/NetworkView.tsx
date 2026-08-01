import { useEffect, useMemo, useState } from "react";
import type { NetworkNode } from "./types";
import LineageGraph from "./LineageGraph";
import { nodeFingerprint, useNetwork } from "./useNetwork";

interface Props {
  myId: string | null;
}

export default function NetworkView({ myId }: Props) {
  const net = useNetwork();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [msg, setMsg] = useState<{ kind: "ok" | "err"; text: string } | null>(
    null,
  );

  // form states
  const [forkName, setForkName] = useState("");
  const [forkStatement, setForkStatement] = useState(
    "fork to test a hypothesis",
  );
  const [adoptStatement, setAdoptStatement] = useState("");
  const [sealStatement, setSealStatement] = useState("");
  const [sealSupersedes, setSealSupersedes] = useState("");

  const nodes = net.network?.nodes ?? [];
  const stats = net.network?.stats;
  const selected = nodes.find((n) => n.id === selectedId) ?? null;

  useEffect(() => {
    if (!selectedId && nodes.length > 0) {
      const mine = nodes.find((n) => n.id === myId);
      setSelectedId(mine?.id ?? nodes[0].id);
    }
  }, [nodes, selectedId, myId]);

  const run = async (kind: string, fn: () => Promise<unknown>) => {
    setBusy(kind);
    setMsg(null);
    try {
      await fn();
      setMsg({ kind: "ok", text: `${kind} signed and verified` });
      net.refresh();
    } catch (e) {
      setMsg({ kind: "err", text: String(e) });
    } finally {
      setBusy(null);
    }
  };

  const ideaHistory = useMemo(() => {
    return (net.network?.ideas ?? []).map((idea) => ({
      ...idea,
      byName: nodes.find((n) => n.id === idea.node)?.name ?? idea.node,
      fromName: nodes.find((n) => n.id === idea.adopted_node)?.name ?? idea.adopted_node,
    }));
  }, [net.network, nodes]);

  if (net.loading && !net.network) {
    return <div className="empty-state">observing the network…</div>;
  }
  if (net.error && !net.network) {
    return <div className="empty-state">offline — {net.error}</div>;
  }

  return (
    <div className="network-view">
      <div className="nw-stats">
        <div className="nw-stat">
          <div className="k">branches</div>
          <div className="v">{stats?.branches ?? 0}</div>
        </div>
        <div className="nw-stat">
          <div className="k">live</div>
          <div className="v">{stats?.live ?? 0}</div>
        </div>
        <div className="nw-stat">
          <div className="k">vanished</div>
          <div className="v">{stats?.vanished ?? 0}</div>
        </div>
        <div className="nw-stat">
          <div className="k">forks</div>
          <div className="v">{stats?.forks ?? 0}</div>
        </div>
        <div className="nw-stat">
          <div className="k">ideas accepted</div>
          <div className="v">{stats?.ideas ?? 0}</div>
        </div>
      </div>

      <div className="nw-legend">
        <span className="lg-legend-item fork">fork</span>
        <span className="lg-legend-item adopt">accepted idea</span>
        <span className="lg-legend-item seal">retirement</span>
        <span className="lg-legend-item seed">committed seed</span>
        <span className="lg-legend-item local">your branch</span>
        <span className="lg-legend-item vanished">vanished</span>
        {myId && (
          <span className="nw-you">you · {nodeFingerprint(myId)}</span>
        )}
      </div>

      {msg && (
        <div className={`nw-msg ${msg.kind}`}>
          {msg.text}
          <button className="nw-msg-close" onClick={() => setMsg(null)}>
            ×
          </button>
        </div>
      )}

      <div className="nw-body">
        <section className="panel">
          <div className="panel-head">
            <span className="panel-title">Network Observatory</span>
            <span className="panel-sub">
              lineage · forks · accepted ideas · vanished branches
            </span>
          </div>
          <div className="panel-body nw-graph">
            <LineageGraph
              network={net.network!}
              selectedId={selectedId}
              myId={myId}
              onSelect={setSelectedId}
            />
          </div>
        </section>

        <aside className="panel nw-detail">
          <div className="panel-head">
            <span className="panel-title">branch detail</span>
            <span className="panel-sub">
              {selected ? selected.name : "select a branch"}
            </span>
          </div>
          <div className="panel-body">
            {!selected ? (
              <div className="empty-state">click a branch</div>
            ) : (
              <NodeDetail
                node={selected}
                mine={selected.id === myId}
                busy={busy}
                forkName={forkName}
                setForkName={setForkName}
                forkStatement={forkStatement}
                setForkStatement={setForkStatement}
                adoptStatement={adoptStatement}
                setAdoptStatement={setAdoptStatement}
                sealStatement={sealStatement}
                setSealStatement={setSealStatement}
                sealSupersedes={sealSupersedes}
                setSealSupersedes={setSealSupersedes}
                onPulse={() =>
                  run("pulse", () => net.pulse(selected.id))
                }
                onFork={() =>
                  run("fork", () =>
                    net.forkNode(selected.id, forkName, forkStatement),
                  )
                }
                onAdopt={(foreign) =>
                  run("adopt", () =>
                    net.adopt(
                      selected.id,
                      foreign.id,
                      foreign.last_decision?.id ?? "",
                      adoptStatement || `accept ${foreign.name}'s laws`,
                    ),
                  )
                }
                onSeal={() =>
                  run("seal", () =>
                    net.seal(selected.id, sealStatement, sealSupersedes),
                  )
                }
                onExport={() => net.exportBundle(selected.id)}
              />
            )}
          </div>
        </aside>
      </div>

      <div className="nw-bottom">
        <section className="panel">
          <div className="panel-head">
            <span className="panel-title">accepted ideas</span>
            <span className="panel-sub">
              ideas adopted across branches · their lineage is signed
            </span>
          </div>
          <div className="panel-body">
            {ideaHistory.length === 0 ? (
              <div className="empty-state">no idea has crossed branches yet</div>
            ) : (
              ideaHistory.map((idea, i) => (
                <div className="idea-row" key={i}>
                  <div className="idea-name">“{idea.name}”</div>
                  <div className="idea-line">
                    adopted by {idea.byName} ← {idea.fromName} ·{" "}
                    {new Date(idea.time).toLocaleString()}
                  </div>
                </div>
              ))
            )}
          </div>
        </section>

        <section className="panel">
          <div className="panel-head">
            <span className="panel-title">vanished branches</span>
            <span className="panel-sub">
              retired by their own laws — history kept, leadership ended
            </span>
          </div>
          <div className="panel-body">
            {(net.network?.vanished ?? []).length === 0 ? (
              <div className="empty-state">no branch has retired yet</div>
            ) : (
              (net.network?.vanished ?? []).map((v) => (
                <div className="idea-row" key={v.id}>
                  <div className="idea-name dim">“{v.name}” — sealed</div>
                  <div className="idea-line">
                    {v.superseded_by
                      ? `superseded by ${v.superseded_by.slice(2, 10)}`
                      : "sealed itself"}{" "}
                    · {v.id}
                  </div>
                </div>
              ))
            )}
          </div>
        </section>
      </div>

      <div className="nw-footer-temp">
        every branch here is temporary. the network exists so that replacement
        is never a crisis.
      </div>
    </div>
  );
}

interface NodeDetailProps {
  node: NetworkNode;
  mine: boolean;
  busy: string | null;
  forkName: string;
  setForkName: (v: string) => void;
  forkStatement: string;
  setForkStatement: (v: string) => void;
  adoptStatement: string;
  setAdoptStatement: (v: string) => void;
  sealStatement: string;
  setSealStatement: (v: string) => void;
  sealSupersedes: string;
  setSealSupersedes: (v: string) => void;
  onPulse: () => void;
  onFork: () => void;
  onAdopt: (foreign: NetworkNode) => void;
  onSeal: () => void;
  onExport: () => void;
}

function NodeDetail(p: NodeDetailProps) {
  const n = p.node;
  const a = n.last_audit;
  return (
    <div className="nd">
      <div className="nd-head">
        <div className="nd-name">{n.name}</div>
        <div className="nd-source">
          {n.source === "local" ? "your branch" : "committed seed"} ·{" "}
          {n.sealed ? "VANISHED" : "live"}
        </div>
        {n.superseded_by && (
          <div className="nd-superseded">
            superseded by {n.superseded_by.slice(2, 10)}
          </div>
        )}
      </div>

      <div className="nd-id">{n.id}</div>
      <div className="nd-fp">fingerprint {nodeFingerprint(n.id)}</div>

      <div className="nd-audit">
        <div className="nd-label">last crash-test</div>
        {a ? (
          <>
            <div className="nd-audit-row">
              <span className={`nd-verdict ${(a.status ?? "").toLowerCase()}`}>
                {a.status}
              </span>
              <span className="nd-r">R = {String(a.R)}</span>
            </div>
            <div className="nd-meta">
              {a.scenario} · R median {String(a.R_median)} · contested{" "}
              {String(a.contested)} · prot v{a.protocol_gen}
            </div>
          </>
        ) : (
          <div className="nd-meta">no crash-test yet</div>
        )}
      </div>

      {n.blocks.length > 0 && (
        <div className="nd-blocks">
          <div className="nd-label danger">replaceability BLOCKS</div>
          {n.blocks.map((b) => (
            <div className="nd-block" key={b.name}>
              {b.name} ({b.function}) cannot be replaced
            </div>
          ))}
        </div>
      )}

      {n.rule_changes.length > 0 && (
        <div className="nd-section">
          <div className="nd-label">rule changes</div>
          {n.rule_changes.map((d) => (
            <div className="nd-row" key={d.id}>
              <span className="nd-kind">{d.kind}</span>
              <span className="nd-stmt">{d.statement}</span>
            </div>
          ))}
        </div>
      )}

      {n.institutions.length > 0 && (
        <div className="nd-section">
          <div className="nd-label">institutions</div>
          {n.institutions.map((i) => (
            <div className="nd-row" key={i.name}>
              <span className="nd-kind">{i.name}</span>
              <span className="nd-stmt">
                {i.function} · replaceable {i.replaceable}
              </span>
            </div>
          ))}
        </div>
      )}

      <div className="nd-actions">
        {p.mine && !n.sealed && (
          <>
            <button
              className="nw-btn"
              onClick={p.onPulse}
              disabled={p.busy !== null}
            >
              {p.busy === "pulse" ? "crash-testing…" : "crash-test"}
            </button>

            <div className="nd-form">
              <input
                className="nw-input"
                placeholder="fork name"
                value={p.forkName}
                onChange={(e) => p.setForkName(e.target.value)}
              />
              <input
                className="nw-input"
                placeholder="statement"
                value={p.forkStatement}
                onChange={(e) => p.setForkStatement(e.target.value)}
              />
              <button
                className="nw-btn ghost"
                onClick={p.onFork}
                disabled={p.busy !== null}
              >
                {p.busy === "fork" ? "forking…" : "fork this branch"}
              </button>
            </div>

            <div className="nd-form">
              <input
                className="nw-input"
                placeholder="seal statement"
                value={p.sealStatement}
                onChange={(e) => p.setSealStatement(e.target.value)}
              />
              <input
                className="nw-input"
                placeholder="superseded by (node id, optional)"
                value={p.sealSupersedes}
                onChange={(e) => p.setSealSupersedes(e.target.value)}
              />
              <button
                className="nw-btn danger"
                onClick={p.onSeal}
                disabled={p.busy !== null}
              >
                {p.busy === "seal" ? "sealing…" : "seal (retire)"}
              </button>
            </div>

            <button className="nw-btn ghost" onClick={p.onExport}>
              export bundle
            </button>
          </>
        )}
        {!p.mine && (
          <div className="nd-form">
            <input
              className="nw-input"
              placeholder={`statement — adopt ${n.name}'s laws`}
              value={p.adoptStatement}
              onChange={(e) => p.setAdoptStatement(e.target.value)}
            />
            <button
              className="nw-btn"
              onClick={() => p.onAdopt(n)}
              disabled={p.busy !== null || !n.last_decision}
            >
              {p.busy === "adopt" ? "adopting…" : `adopt ${n.name}'s laws`}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
