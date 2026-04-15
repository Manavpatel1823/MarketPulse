const BASE = "/api";

export interface RunSummary {
  id: number;
  started_at: string;
  finished_at: string | null;
  product_name: string;
  brand_tier: string | null;
  mean_sentiment: number | null;
  polarization: number | null;
  agent_count: number;
  rounds: number;
  total_conversions: number | null;
}

export interface GraphNode {
  id: number;
  persona_id: string;
  name: string;
  archetype: string;
  age: number | null;
  income_bracket: string | null;
  initial_bias: number | null;
  initial_sentiment: number | null;
  final_sentiment: number | null;
  conversion_count: number;
  sentiment_by_round: Record<number, number>;
}

export interface GraphEdge {
  id: number;
  round_num: number;
  source: number;
  target: number;
  a_stance: string;
  b_stance: string;
  a_shift: number;
  b_shift: number;
  a_convinced: boolean;
  b_convinced: boolean;
  a_argument: string;
  b_argument: string;
}

export interface RunGraph {
  run_id: number;
  product_name: string;
  rounds: number;
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export async function fetchRuns(): Promise<RunSummary[]> {
  const r = await fetch(`${BASE}/runs`);
  if (!r.ok) throw new Error(`runs ${r.status}`);
  const data = await r.json();
  return data.runs;
}

export async function fetchRunGraph(runId: number): Promise<RunGraph> {
  const r = await fetch(`${BASE}/runs/${runId}/graph`);
  if (!r.ok) throw new Error(`graph ${r.status}`);
  return r.json();
}

export interface RunDetail {
  id: number;
  product_name: string;
  brand_tier: string | null;
  mean_sentiment: number | null;
  polarization: number | null;
  agent_count: number;
  rounds: number;
  total_conversions: number | null;
  distribution: any;
  shared_memory: {
    product_json: any;
    competitors_json: any[];
    signals_json: any;
    market_context: string | null;
  } | null;
  report: { markdown: string; generated_at: string } | null;
  agents: any[];
}

export async function fetchRunDetail(runId: number): Promise<RunDetail> {
  const r = await fetch(`${BASE}/runs/${runId}`);
  if (!r.ok) throw new Error(`detail ${r.status}`);
  return r.json();
}
