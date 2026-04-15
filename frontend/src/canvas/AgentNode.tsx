import { Handle, Position } from "reactflow";
import type { NodeProps } from "reactflow";
import type { GraphNode } from "../api";

export interface AgentNodeData {
  agent: GraphNode;
  sentiment: number; // sentiment at the currently-viewed round
  isSelected: boolean;
}

// Diverging red→grey→green scale for sentiment in [-10, +10].
function sentimentColor(s: number): string {
  const t = Math.max(-10, Math.min(10, s)) / 10; // -1..1
  if (t >= 0) {
    // grey → green
    const r = Math.round(160 + (30 - 160) * t);
    const g = Math.round(160 + (190 - 160) * t);
    const b = Math.round(160 + (100 - 160) * t);
    return `rgb(${r},${g},${b})`;
  }
  const r = Math.round(160 + (200 - 160) * -t);
  const g = Math.round(160 + (60 - 160) * -t);
  const b = Math.round(160 + (70 - 160) * -t);
  return `rgb(${r},${g},${b})`;
}

// Size by influence: base 48px + 6px per conversion caused, capped.
function nodeSize(conversions: number): number {
  return Math.min(48 + conversions * 6, 96);
}

export function AgentNode({ data }: NodeProps<AgentNodeData>) {
  const { agent, sentiment, isSelected } = data;
  const size = nodeSize(agent.conversion_count);
  const bg = sentimentColor(sentiment);
  return (
    <div
      style={{
        width: size,
        height: size,
        borderRadius: "50%",
        background: bg,
        border: isSelected ? "3px solid #0af" : "2px solid #222",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontSize: 10,
        color: "#111",
        fontWeight: 600,
        textAlign: "center",
        padding: 4,
        boxSizing: "border-box",
        boxShadow: isSelected ? "0 0 16px #0af" : "0 2px 4px rgba(0,0,0,0.3)",
        cursor: "pointer",
      }}
      title={`${agent.name} — ${agent.archetype} — sentiment ${sentiment.toFixed(1)}`}
    >
      <Handle type="target" position={Position.Top} style={{ opacity: 0 }} />
      <Handle type="source" position={Position.Bottom} style={{ opacity: 0 }} />
      <div style={{ overflow: "hidden", lineHeight: 1.1 }}>
        <div style={{ fontSize: 9, fontWeight: 400 }}>{agent.archetype}</div>
        <div>{agent.name.split(" ")[0]}</div>
        <div style={{ fontSize: 9 }}>{sentiment.toFixed(1)}</div>
      </div>
    </div>
  );
}
