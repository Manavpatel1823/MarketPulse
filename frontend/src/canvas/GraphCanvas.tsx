import { useMemo } from "react";
import ReactFlow, {
  Background,
  Controls,
  MarkerType,
  type Edge,
  type Node,
} from "reactflow";
import { useStore } from "../store";
import { AgentNode, type AgentNodeData } from "./AgentNode";
import { radialLayout } from "./layout";

const nodeTypes = { agent: AgentNode };

function stanceColor(stance: string): string {
  if (stance === "agree") return "#2a9d54";
  if (stance === "partial") return "#d9a441";
  return "#c24b4b"; // disagree / unknown
}

export function GraphCanvas() {
  const graph = useStore((s) => s.graph);
  const currentRound = useStore((s) => s.currentRound);
  const selectedAgent = useStore((s) => s.selectedAgent);
  const setSelectedAgent = useStore((s) => s.setSelectedAgent);
  const archetypeFilter = useStore((s) => s.archetypeFilter);

  const positions = useMemo(
    () => (graph ? radialLayout(graph.nodes) : {}),
    [graph],
  );

  const nodes: Node<AgentNodeData>[] = useMemo(() => {
    if (!graph) return [];
    return graph.nodes.map((a) => {
      const s =
        a.sentiment_by_round[currentRound] ??
        a.sentiment_by_round[Object.keys(a.sentiment_by_round).length - 1] ??
        a.final_sentiment ??
        0;
      const pos = positions[a.id] ?? { x: 0, y: 0 };
      const dim = archetypeFilter !== null && a.archetype !== archetypeFilter;
      return {
        id: String(a.id),
        type: "agent",
        position: pos,
        style: { opacity: dim ? 0.2 : 1 },
        data: {
          agent: a,
          sentiment: s,
          isSelected: selectedAgent?.id === a.id,
        },
      };
    });
  }, [graph, currentRound, positions, selectedAgent, archetypeFilter]);

  const edges: Edge[] = useMemo(() => {
    if (!graph) return [];
    return graph.edges
      .filter((e) => e.round_num <= currentRound)
      .map((e) => {
        const convinced = e.a_convinced || e.b_convinced;
        const maxShift = Math.max(Math.abs(e.a_shift), Math.abs(e.b_shift));
        const stance =
          e.a_stance === e.b_stance ? e.a_stance : "partial";
        return {
          id: `e${e.id}`,
          source: String(e.source),
          target: String(e.target),
          animated: convinced,
          style: {
            stroke: stanceColor(stance),
            strokeWidth: Math.max(1, maxShift * 1.2),
            opacity: e.round_num === currentRound ? 0.9 : 0.35,
          },
          markerEnd: convinced
            ? { type: MarkerType.ArrowClosed, color: stanceColor(stance) }
            : undefined,
          data: e,
        } as Edge;
      });
  }, [graph, currentRound]);

  if (!graph) {
    return (
      <div style={{ flex: 1, display: "grid", placeItems: "center", color: "#888" }}>
        Select a run to view the agent panel.
      </div>
    );
  }

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      nodeTypes={nodeTypes}
      onNodeClick={(_, node) => {
        const found = graph.nodes.find((n) => String(n.id) === node.id) ?? null;
        setSelectedAgent(found);
      }}
      onPaneClick={() => setSelectedAgent(null)}
      fitView
      minZoom={0.1}
      maxZoom={2}
    >
      <Background color="#333" gap={24} />
      <Controls />
    </ReactFlow>
  );
}
