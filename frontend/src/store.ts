import { create } from "zustand";
import type { GraphNode, RunDetail, RunGraph, RunSummary } from "./api";

interface State {
  runs: RunSummary[];
  selectedRunId: number | null;
  graph: RunGraph | null;
  detail: RunDetail | null;
  currentRound: number; // 0 = initial opinions, 1..N = post-debate round N
  selectedAgent: GraphNode | null;
  loading: boolean;
  error: string | null;
  viewMode: "2d" | "3d";
  reportOpen: boolean;
  archetypeFilter: string | null; // null = all

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
}

export const useStore = create<State>((set) => ({
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
}));
