import { OBSERVATORY_URL, useObservatory } from "./useObservatory";
import CivilizationGraph from "./CivilizationGraph";
import PulseTimeline from "./PulseTimeline";
import FutureSpace from "./FutureSpace";
import ProtocolStatus from "./ProtocolStatus";

const SCENARIO_LABELS: Record<string, string> = {
  monolith: "Monolith",
  plural: "Plural",
  adaptive: "Adaptive",
  adaptive_h: "Adaptive H",
  meta: "Meta",
};

export default function App() {
  const obs = useObservatory();
  const lastPulse = obs.pulses.length > 0 ? obs.pulses[obs.pulses.length - 1] : null;

  return (
    <div className="obs-shell">
      <header className="obs-header">
        <div>
          <h1 className="obs-title">
            Civilization <span className="thin">Observatory</span>
          </h1>
          <div className="obs-tagline">
            {obs.hello ? obs.hello.protocol : "APP v5.4"} — observe, do not
            govern · no voting · no commands
          </div>
        </div>
        <div className="obs-ws">
          <span className={`status-dot ${obs.conn === "online" ? "online" : obs.conn === "connecting" ? "connecting" : ""}`} />
          <span>
            {obs.conn === "online"
              ? "stream live"
              : obs.conn === "connecting"
                ? "connecting…"
                : "offline — retrying"}
          </span>
          <span>{OBSERVATORY_URL}</span>
        </div>
      </header>

      <div className="obs-controls">
        {(obs.hello?.scenarios ?? [
          { id: "monolith", desc: "", immunity: false },
          { id: "plural", desc: "", immunity: false },
          { id: "adaptive", desc: "", immunity: true },
          { id: "adaptive_h", desc: "", immunity: true },
          { id: "meta", desc: "", immunity: true },
        ]).map((s) => (
          <button
            key={s.id}
            className={`scenario-btn ${obs.selectedScenario === s.id ? "active" : ""}`}
            disabled={obs.running}
            onClick={() => obs.selectScenario(s.id)}
            title={s.desc}
          >
            {SCENARIO_LABELS[s.id] ?? s.id}
          </button>
        ))}
        <button
          className="run-btn"
          disabled={obs.conn !== "online" || obs.running}
          onClick={() => obs.run(obs.selectedScenario, 1)}
        >
          {obs.running ? "running…" : "run scenario"}
        </button>
        <span className="obs-hint">
          {obs.running && lastPulse
            ? `pulse ${lastPulse.pulse} · ${lastPulse.event}`
            : obs.status
              ? `verdict: ${obs.status}`
              : "select a structure · observe its health"}
        </span>
      </div>

      {obs.status && lastPulse && (
        <div className="verdict-banner">
          <div>
            <div className="verdict-label">final verdict</div>
            <div className={`verdict-value ${obs.status.toLowerCase()}`}>
              {obs.status}
            </div>
          </div>
          <div className="verdict-stats">
            <div className="verdict-stat">
              <div className="k">R reachability</div>
              <div className="v">{String(obs.verdict?.R ?? "—")}</div>
            </div>
            <div className="verdict-stat">
              <div className="k">R median</div>
              <div className="v">{String(obs.verdict?.R_median ?? "—")}</div>
            </div>
            <div className="verdict-stat">
              <div className="k">contested</div>
              <div className="v">{String(obs.verdict?.contested ?? "—")}</div>
            </div>
            <div className="verdict-stat">
              <div className="k">protocol gen</div>
              <div className="v">v{String(obs.verdict?.protocol_gen ?? "1")}</div>
            </div>
            <div className="verdict-stat">
              <div className="k">scenario</div>
              <div className="v">
                {lastPulse.scenario.toUpperCase()}
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="obs-grid">
        <section className="panel">
          <div className="panel-head">
            <span className="panel-title">Civilization Graph</span>
            <span className="panel-sub">structures · inversion · generation</span>
          </div>
          <div className="panel-body">
            <CivilizationGraph
              institutions={lastPulse?.institutions ?? []}
              pulse={lastPulse?.pulse ?? 0}
            />
          </div>
        </section>

        <section className="panel">
          <div className="panel-head">
            <span className="panel-title">Future Space</span>
            <span className="panel-sub">R — measured reachability · meters R₁ R₂ R₃</span>
          </div>
          <div className="panel-body">
            <FutureSpace audit={lastPulse?.audit ?? null} pulse={lastPulse?.pulse ?? 0} />
          </div>
        </section>

        <section className="panel full">
          <div className="panel-head">
            <span className="panel-title">Pulse Timeline</span>
            <span className="panel-sub">ADI · CR · recoverability · economy</span>
          </div>
          <div className="panel-body">
            <PulseTimeline pulses={obs.pulses} />
          </div>
        </section>

        <section className="panel full">
          <div className="panel-head">
            <span className="panel-title">Protocol Status</span>
            <span className="panel-sub">immune architecture · replaceability</span>
          </div>
          <div className="panel-body">
            <ProtocolStatus
              pulses={obs.pulses}
              verdict={obs.verdict}
              status={obs.status}
            />
          </div>
        </section>
      </div>

      <footer className="obs-footer">
        <div className="note">
          The reader is not asked to govern the simulation. The reader is
          invited to observe its health — and then to break it.
        </div>
        <a
          href="https://github.com/0penAGI/General-theory-of-civilisation-degradation"
          target="_blank"
          rel="noreferrer"
        >
          Fork the future. Test the attractor.
        </a>
      </footer>
    </div>
  );
}
