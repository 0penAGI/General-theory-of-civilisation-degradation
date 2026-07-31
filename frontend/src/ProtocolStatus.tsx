import type { PulseMessage, VerdictMessage } from "./types";

interface LogEntry {
  pulse: number;
  text: string;
  kind: "normal" | "event" | "danger";
}

const EVENT_COLORS: Record<string, "event" | "danger"> = {
  agi_arrival: "danger",
  mass_unemployment: "event",
  metric_collapse: "danger",
};

interface Props {
  pulses: PulseMessage[];
  verdict: VerdictMessage["report"] | null;
  status: VerdictMessage["status"] | null;
}

export default function ProtocolStatus({ pulses, verdict, status }: Props) {
  const last = pulses.length > 0 ? pulses[pulses.length - 1] : null;
  const metrics = last?.metrics;

  const log: LogEntry[] = [];
  pulses.forEach((p) => {
    if (p.event !== "routine") {
      log.push({
        pulse: p.pulse,
        text: p.event,
        kind: EVENT_COLORS[p.event] ?? "event",
      });
    }
    (p.changes ?? []).forEach((c) => {
      const kind: LogEntry["kind"] = /protocol|measurer/.test(c) ? "event" : "normal";
      log.push({ pulse: p.pulse, text: c, kind });
    });
  });
  if (status && last) {
    log.push({
      pulse: last.pulse,
      text: `FINAL: ${status} — R=${String(verdict?.R)}`,
      kind: status === "SURVIVED" ? "normal" : "danger",
    });
  }
  const recent = log.slice(-16).reverse();

  const rules = last?.protocol_rules ?? null;

  return (
    <div>
      <div className="prot-stats">
        <div className="prot-stat">
          <div className="k">protocol generation</div>
          <div className="v">v{last?.protocol_gen ?? 1}</div>
        </div>
        <div className="prot-stat">
          <div className="k">capture</div>
          <div className="v" style={{ color: (metrics?.capture ?? 0) > 0.2 ? "#ff5d5d" : undefined }}>
            {(metrics?.capture ?? 0).toFixed(3)}
          </div>
        </div>
        <div className="prot-stat">
          <div className="k">update rate</div>
          <div className="v">{(metrics?.update_rate ?? 0).toFixed(2)}</div>
        </div>
      </div>

      {rules ? (
        <table className="prot-rule-table">
          <tbody>
            {Object.entries(rules)
              .slice(0, 6)
              .map(([k, v]) => (
                <tr key={k}>
                  <td>{k}</td>
                  <td>{typeof v === "number" ? v.toFixed(3) : String(v)}</td>
                </tr>
              ))}
          </tbody>
        </table>
      ) : null}

      <div className="log-list">
        {recent.length === 0 ? (
          <div className="empty-state">observation log — start a scenario</div>
        ) : (
          recent.map((e, i) => (
            <div className="log-row" key={`${e.pulse}-${i}`}>
              <span className="p">p{e.pulse}</span>
              <span className={`msg ${e.kind}`}>{e.text}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
