import { create } from "zustand";
import type { GraphNode, RunDetail, RunGraph, RunSummary } from "./api";

export type SimPhase =
  | "idle"
  | "starting"
  | "agents"
  | "opinions"
  | "debating"
  | "reflection"
  | "report"
  | "complete"
  | "error";

export interface LiveNode {
  id: string; // persona_id
  name: string;
  archetype: string;
  age?: number;
  income_bracket?: string;
  sentiment: number | null;
  initial_bias?: number;
}

export interface LiveEdge {
  id: string;
  round: number;
  source: string; // persona_id of a
  target: string; // persona_id of b
  a_name: string;
  b_name: string;
  a_stance: string;
  b_stance: string;
  a_argument: string;
  b_argument: string;
  a_shift: number;
  b_shift: number;
  a_converted: boolean;
  b_converted: boolean;
  a_sentiment_after: number;
  b_sentiment_after: number;
}

interface State {
  // Run browser mode
  runs: RunSummary[];
  selectedRunId: number | null;
  graph: RunGraph | null;
  detail: RunDetail | null;
  currentRound: number;
  selectedAgent: GraphNode | null;
  loading: boolean;
  error: string | null;
  viewMode: "2d" | "3d";
  reportOpen: boolean;
  archetypeFilter: string | null;

  // Live simulation mode
  simPhase: SimPhase;
  liveId: number | null;
  liveNodes: LiveNode[];
  liveEdges: LiveEdge[];
  liveRound: number;
  liveReport: string | null;
  liveProductName: string | null;
  liveAgentCount: number;
  liveRounds: number;
  liveMeanSentiment: number | null;
  liveError: string | null;

  // Actions — run browser
  setRuns: (r: RunSummary[]) => void;
  setSelectedRunId: (id: number | null) => void;
  setGraph: (g: RunGraph | null) => void;
  setDetail: (d: RunDetail | null) => void;
  setCurrentRound: (n: number) => void;
  setSelectedAgent: (a: GraphNode | null) => void;
  setLoading: (b: boolean) => void;
  setError: (e: string | null) => void;
  setViewMode: (v: "2d" | "3d") => void;
  setReportOpen: (b: boolean) => void;
  setArchetypeFilter: (a: string | null) => void;

  // Actions — live simulation
  startLive: (liveId: number, productName: string, agentCount: number, rounds: number) => void;
  setSimPhase: (p: SimPhase) => void;
  addLiveNode: (n: LiveNode) => void;
  updateNodeSentiment: (personaId: string, sentiment: number) => void;
  addLiveEdge: (e: LiveEdge) => void;
  setLiveRound: (r: number) => void;
  setLiveReport: (r: string) => void;
  setLiveError: (e: string) => void;
  setLiveMeanSentiment: (s: number) => void;
  resetLive: () => void;
}

export const useStore = create<State>((set) => ({
  // Run browser
  runs: [],
  selectedRunId: null,
  graph: null,
  detail: null,
  currentRound: 0,
  selectedAgent: null,
  loading: false,
  error: null,
  viewMode: "3d",
  reportOpen: false,
  archetypeFilter: null,

  // Live simulation
  simPhase: "idle",
  liveId: null,
  liveNodes: [],
  liveEdges: [],
  liveRound: 0,
  liveReport: null,
  liveProductName: null,
  liveAgentCount: 0,
  liveRounds: 0,
  liveMeanSentiment: null,
  liveError: null,

  // Run browser actions
  setRuns: (runs) => set({ runs }),
  setSelectedRunId: (selectedRunId) =>
    set({
      selectedRunId,
      graph: null,
      detail: null,
      currentRound: 0,
      selectedAgent: null,
      archetypeFilter: null,
      reportOpen: false,
    }),
  setGraph: (graph) => set({ graph, currentRound: graph?.rounds ?? 0 }),
  setDetail: (detail) => set({ detail }),
  setCurrentRound: (currentRound) => set({ currentRound }),
  setSelectedAgent: (selectedAgent) => set({ selectedAgent }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  setViewMode: (viewMode) => set({ viewMode }),
  setReportOpen: (reportOpen) => set({ reportOpen }),
  setArchetypeFilter: (archetypeFilter) => set({ archetypeFilter }),

  // Live simulation actions
  startLive: (liveId, productName, agentCount, rounds) =>
    set({
      simPhase: "starting",
      liveId,
      liveProductName: productName,
      liveAgentCount: agentCount,
      liveRounds: rounds,
      liveNodes: [],
      liveEdges: [],
      liveRound: 0,
      liveReport: null,
      liveError: null,
      liveMeanSentiment: null,
      // Clear run browser state
      selectedRunId: null,
      graph: null,
      detail: null,
    }),
  setSimPhase: (simPhase) => set({ simPhase }),
  addLiveNode: (n) =>
    set((s) => ({ liveNodes: [...s.liveNodes, n] })),
  updateNodeSentiment: (personaId, sentiment) =>
    set((s) => ({
      liveNodes: s.liveNodes.map((n) =>
        n.id === personaId ? { ...n, sentiment } : n,
      ),
    })),
  addLiveEdge: (e) =>
    set((s) => ({ liveEdges: [...s.liveEdges, e] })),
  setLiveRound: (liveRound) => set({ liveRound }),
  setLiveReport: (liveReport) => set({ liveReport, simPhase: "complete" }),
  setLiveError: (liveError) => set({ liveError, simPhase: "error" }),
  setLiveMeanSentiment: (liveMeanSentiment) => set({ liveMeanSentiment }),
  resetLive: () =>
    set({
      simPhase: "idle",
      liveId: null,
      liveNodes: [],
      liveEdges: [],
      liveRound: 0,
      liveReport: null,
      liveProductName: null,
      liveAgentCount: 0,
      liveRounds: 0,
      liveMeanSentiment: null,
      liveError: null,
    }),
}));
