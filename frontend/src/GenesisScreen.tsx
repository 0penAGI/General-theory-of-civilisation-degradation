import { useState } from "react";
import type { NetworkNode } from "./types";
import { useNetwork, nodeFingerprint } from "./useNetwork";

const PRINCIPLE =
  "We create not a society that knows the right answer, but a society that cannot get permanently stuck on the wrong one.";

const STAGES = ["NODE", "FORK", "EVIDENCE", "REVISION", "NEW NODE"];

interface Props {
  onEntered: (node: NetworkNode) => void;
}

export default function GenesisScreen({ onEntered }: Props) {
  const net = useNetwork();
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [created, setCreated] = useState<NetworkNode | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const create = async () => {
    setBusy(true);
    setErr(null);
    try {
      const node = await net.createNode(name.trim() || "unnamed");
      setCreated(node);
    } catch (e) {
      setErr(String(e));
    } finally {
      setBusy(false);
    }
  };

  if (created) {
    const audit = created.last_audit;
    return (
      <div className="genesis-shell">
        <div className="genesis-card">
          <div className="gen-kicker">APP NETWORK — NODE BORN</div>
          <h1 className="gen-title">{created.name}</h1>
          <div className="gen-id">
            <span className="gen-id-label">node id</span>
            <span className="gen-id-value">{created.id}</span>
            <span className="gen-fingerprint">
              confirm out-of-band: fingerprint {nodeFingerprint(created.id)}
            </span>
          </div>

          <div className="gen-first-audit">
            <div className="gen-label">first crash-test</div>
            {audit ? (
              <div className="gen-audit-row">
                <span className={`gen-verdict ${(audit.status ?? "").toLowerCase()}`}>
                  {audit.status}
                </span>
                <span className="gen-r">R = {String(audit.R)}</span>
                <span className="gen-meta">
                  {audit.scenario} · contested={String(audit.contested)}
                </span>
              </div>
            ) : (
              <div className="gen-empty">no audit yet</div>
            )}
          </div>

          <div className="gen-principle">“{PRINCIPLE}”</div>

          <div className="gen-note">
            Your node knows nothing yet — and that is the point. It has an
            identity, a ledger, and a set of laws it will now have to prove.
            Everything it signs lives in{" "}
            <code className="gen-code">nodes/{created.id}</code> on this
            machine. That directory is your sovereignty: back it up, or export
            it before you leave. No server holds your key.
          </div>

          <div className="gen-actions">
            <button className="gen-btn" onClick={() => onEntered(created)}>
              enter the network
            </button>
          </div>
          <div className="gen-temp">
            this branch is temporary. yours will be too.
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="genesis-shell">
      <div className="genesis-card">
        <div className="gen-kicker">APP NETWORK — GENESIS</div>
        <h1 className="gen-slogan">
          Civilization is not a state.
          <br />
          It is a protocol for remaining replaceable.
        </h1>

        <div className="gen-schema">
          {STAGES.map((s, i) => (
            <span key={s} className={`gen-stage stage-${i}`}>
              {s}
            </span>
          ))}
        </div>

        <div className="gen-principle">“{PRINCIPLE}”</div>

        <div className="gen-form">
          <input
            className="gen-input"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="name your branch"
            maxLength={40}
            onKeyDown={(e) => e.key === "Enter" && !busy && create()}
            autoFocus
          />
          <button
            className="gen-btn"
            onClick={create}
            disabled={busy || net.conn === "offline"}
          >
            {busy ? "forging…" : "create your node"}
          </button>
        </div>

        {err && <div className="gen-error">{err}</div>}
        {net.conn === "offline" && (
          <div className="gen-error">
            observatory offline — run <code className="gen-code">python
            observatory.py</code> first
          </div>
        )}

        <div className="gen-note">
          The first node knows nothing. It does not inherit a conclusion — it
          inherits a test. Whatever you name it, it starts with one identity,
          one signed declaration, and a law it has not yet proven. This machine
          holds the key; <em>you</em> hold this directory.
        </div>
        <div className="gen-temp">
          this branch is temporary. yours will be too.
        </div>
      </div>
    </div>
  );
}
