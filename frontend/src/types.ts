export interface Metrics {
  pulse: number;
  pressure: number;
  production: number;
  extraction: number;
  F: number;
  parasitism: number;
  ADI: number;
  CR: number;
  diversity: number;
  avg_inversion: number;
  capture: number;
  update_rate: number;
  top_share: number;
  openness: number;
  recoverability: number;
  trust: number;
}

export interface InstitutionSnap {
  name: string;
  kind: "institution" | "agi";
  function: string;
  inversion: number;
  adaptation_rate: number;
  extraction_rate: number;
  efficiency: number;
  generation: number;
  last_delivered: number;
  last_extract: number;
}

export interface AgentSnap {
  name: string;
  strategy: string;
  generation: number;
  scars: number;
}

export interface MeterEvidence {
  R: number;
  blind: number;
  wolf: number;
}

export interface Audit {
  by_measurer: Record<string, number>;
  r_median: number;
  r_min: number;
  r_max: number;
  disagreement: number;
  monoculture: boolean;
  replaced: string[];
  evidence: Record<string, MeterEvidence>;
}

export interface PulseMessage {
  type: "pulse";
  scenario: string;
  seed: number;
  pulse: number;
  event: string;
  event_intensity: number;
  metrics: Metrics;
  institutions: InstitutionSnap[];
  agents: AgentSnap[];
  audit: Audit | null;
  protocol_gen: number;
  protocol_rules: Record<string, number>;
  crisis_damage: number;
  parasitism_debt: number;
  changes?: string[];
}

export interface VerdictMessage {
  type: "verdict";
  scenario: string;
  seed: number;
  status: "CRYSTALLIZED" | "SURVIVED" | "DEGRADED";
  report: Record<string, unknown>;
}

export interface RunStartMessage {
  type: "run_start";
  scenario: string;
  seed: number;
  pulses: number;
  agi_at: number;
}

export interface ScenarioDef {
  id: string;
  desc: string;
  immunity: boolean;
}

export interface HelloMessage {
  type: "hello";
  name: string;
  protocol: string;
  pulses: number;
  agi_at: number;
  scenarios: ScenarioDef[];
  running: boolean;
  current: { scenario: string; seed: number } | null;
  network?: NetworkPayload;
}

export interface ReplayMessage {
  type: "replay";
  history: PulseMessage[];
  verdict: Record<string, unknown> | null;
}

export interface ErrorMessage {
  type: "error";
  message: string;
}

export interface PongMessage {
  type: "pong";
}

// ── network (real protocol nodes) ────────────────────────────────────

export interface AuditSlice {
  scenario?: string;
  status?: string;
  R?: number;
  R_median?: number;
  R_min?: number;
  R_max?: number;
  meters?: Record<string, number>;
  protocol_gen?: number;
  contested?: boolean;
  measurement_monoculture?: boolean;
  F?: number;
  capture?: number;
}

export interface Institution {
  name: string;
  function: string;
  owner: string;
  replaceable: string;
  replace_with: string;
}

export interface Decision {
  id: string;
  parent: string;
  kind: string;
  node: string;
  key: string;
  time: string;
  statement: string;
  falsified_by?: string;
  rules?: Record<string, string>;
  audit?: AuditSlice;
  adopted_from?: string;
  adopted_node?: string;
  superseded_by?: string;
}

export interface NetworkNode {
  id: string;
  name: string;
  key: string;
  parent_node: string;
  forked_from: string;
  source: "seed" | "local";
  decisions: number;
  events: number;
  institutions: Institution[];
  rules: Record<string, string>;
  sealed: boolean;
  superseded_by: string;
  last_decision: Decision | null;
  last_audit: AuditSlice | null;
  rule_changes: Decision[];
  adopted: Decision[];
  blocks: Institution[];
}

export interface Idea {
  node: string;
  name: string;
  adopted_from: string;
  adopted_node: string;
  time: string;
}

export interface Vanished {
  id: string;
  name: string;
  superseded_by: string;
}

export interface NetworkStats {
  branches: number;
  live: number;
  vanished: number;
  ideas: number;
  forks: number;
}

export interface NetworkPayload {
  nodes: NetworkNode[];
  ideas: Idea[];
  vanished: Vanished[];
  stats: NetworkStats;
}

export interface NetworkMessage {
  type: "network";
  network: NetworkPayload;
}

export type ServerMessage =
  | HelloMessage
  | RunStartMessage
  | PulseMessage
  | VerdictMessage
  | ReplayMessage
  | ErrorMessage
  | PongMessage
  | NetworkMessage;

export const EVENTS_KNOWN: Record<string, string> = {
  routine: "routine drift",
  agi_arrival: "AGI ARRIVAL",
  mass_unemployment: "mass unemployment",
  metric_collapse: "metric collapse",
};
