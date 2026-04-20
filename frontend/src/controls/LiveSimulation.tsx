import { useMemo } from "react";
import { useStore } from "../store";
import type { LiveEdge, LiveNode } from "../store";

const ARCHETYPE_COLORS: Record<string, string> = {
  early_adopter: "#22d3ee",
  tech_enthusiast: "#818cf8",
  brand_loyalist: "#a78bfa",
  impulse_buyer: "#f472b6",
  pragmatist: "#94a3b8",
  bargain_hunter: "#facc15",
  skeptic: "#f87171",
  contrarian: "#fb923c",
  eco_warrior: "#4ade80",
  luxury_seeker: "#c084fc",
};

function sentimentColor(s: number | null): string {
  if (s === null) return "#555";
  if (s > 5) return "#22c55e";
  if (s > 2) return "#86efac";
  if (s > -2) return "#facc15";
  if (s > -5) return "#fb923c";
  return "#ef4444";
}

function phaseLabel(phase: string, round: number, total: number): string {
  switch (phase) {
    case "starting": return "Starting simulation...";
    case "agents": return "Creating agent personas...";
    case "opinions": return "Agents forming initial opinions...";
    case "debating": return `Debate Round ${round} of ${total}`;
    case "reflection": return `Agents reflecting after round ${round}...`;
    case "report": return "Generating marketing report...";
    case "complete": return "Simulation complete";
    case "error": return "Simulation failed";
    default: return "";
  }
}

/**
 * Spread nodes across the canvas using concentric rings + jitter so they
 * never overlap even at 100 agents.  Outer padding keeps labels visible.
 */
function layoutNodes(nodes: LiveNode[]): { x: number; y: number }[] {
  const n = nodes.length;
  if (n === 0) return [];

  const W = 900, H = 600;
  const cx = W / 2, cy = H / 2;
  const pad = 40; // keep nodes away from edges

  if (n === 1) return [{ x: cx, y: cy }];

  // Distribute across concentric rings.
  // Ring 0 (centre) holds 1 node, ring 1 holds 6, ring 2 holds 12, etc.
  // Each successive ring has 6*ring slots.
  const positions: { x: number; y: number }[] = [];
  let placed = 0;
  let ring = 0;

  // Max radius we can use inside the padded area
  const maxR = Math.min(cx - pad, cy - pad);

  // Determine how many rings we need
  const ringsNeeded = (() => {
    let count = 0, r = 0;
    while (count < n) {
      count += r === 0 ? 1 : 6 * r;
      r++;
    }
    return r;
  })();

  const ringSpacing = maxR / Math.max(ringsNeeded, 1);

  // Deterministic seed for jitter
  const jitter = (i: number) => {
    const s = Math.sin(i * 9301 + 4927) * 0.5;
    return s * ringSpacing * 0.2;
  };

  while (placed < n) {
    if (ring === 0) {
      positions.push({ x: cx, y: cy });
      placed++;
    } else {
      const slots = 6 * ring;
      const r = ring * ringSpacing;
      for (let s = 0; s < slots && placed < n; s++) {
        const angle = (2 * Math.PI * s) / slots - Math.PI / 2 + ring * 0.3;
        positions.push({
          x: cx + (r + jitter(placed)) * Math.cos(angle),
          y: cy + (r + jitter(placed + 1000)) * Math.sin(angle),
        });
        placed++;
      }
    }
    ring++;
  }

  return positions;
}

export function LiveSimulation() {
  const phase = useStore((s) => s.simPhase);
  const nodes = useStore((s) => s.liveNodes);
  const edges = useStore((s) => s.liveEdges);
  const liveRound = useStore((s) => s.liveRound);
  const liveRounds = useStore((s) => s.liveRounds);
  const productName = useStore((s) => s.liveProductName);
  const liveReport = useStore((s) => s.liveReport);
  const liveError = useStore((s) => s.liveError);
  const meanSentiment = useStore((s) => s.liveMeanSentiment);
  const resetLive = useStore((s) => s.resetLive);

  const positions = useMemo(() => layoutNodes(nodes), [nodes.length]);

  // Build a persona_id -> index lookup
  const idxMap = useMemo(() => {
    const m: Record<string, number> = {};
    nodes.forEach((n, i) => { m[n.id] = i; });
    return m;
  }, [nodes]);

  const opinionsFormed = nodes.filter((n) => n.sentiment !== null).length;

  return (
    <div style={{ height: "100%", display: "flex", flexDirection: "column" }}>
      {/* Status bar */}
      <div
        style={{
          padding: "10px 20px",
          background: "#16161a",
          borderBottom: "1px solid #2a2a2e",
          display: "flex",
          alignItems: "center",
          gap: 16,
          fontSize: 13,
        }}
      >
        <span style={{ fontWeight: 700 }}>{productName}</span>
        <span style={{ color: "#888" }}>
          {phaseLabel(phase, liveRound, liveRounds)}
        </span>
        <div style={{ flex: 1 }} />
        <span style={{ color: "#888" }}>
          {nodes.length} agents · {edges.length} debates
          {opinionsFormed > 0 && opinionsFormed < nodes.length && ` · ${opinionsFormed}/${nodes.length} opinions`}
        </span>
        {meanSentiment !== null && (
          <span style={{ color: sentimentColor(meanSentiment) }}>
            Mean: {meanSentiment.toFixed(1)}
          </span>
        )}
        {phase === "complete" && (
          <button
            onClick={resetLive}
            style={{
              background: "#2563eb",
              border: "none",
              borderRadius: 6,
              padding: "6px 14px",
              color: "#fff",
              fontSize: 12,
              cursor: "pointer",
              fontWeight: 600,
            }}
          >
            New Simulation
          </button>
        )}
      </div>

      {/* Main canvas area */}
      <div style={{ flex: 1, position: "relative", overflow: "hidden" }}>
        <svg
          width="100%"
          height="100%"
          viewBox="0 0 900 600"
          style={{ background: "#0e0e10" }}
        >
          {/* Edges */}
          {edges.map((e) => {
            const si = idxMap[e.source];
            const ti = idxMap[e.target];
            if (si === undefined || ti === undefined) return null;
            const sp = positions[si];
            const tp = positions[ti];
            if (!sp || !tp) return null;
            const hasConversion = e.a_converted || e.b_converted;
            return (
              <line
                key={e.id}
                x1={sp.x}
                y1={sp.y}
                x2={tp.x}
                y2={tp.y}
                stroke={hasConversion ? "#facc15" : "#333"}
                strokeWidth={hasConversion ? 2 : 1}
                opacity={0.6}
              >
                <title>
                  {`R${e.round}: ${e.a_name} (${e.a_stance}) vs ${e.b_name} (${e.b_stance})`}
                </title>
              </line>
            );
          })}

          {/* Nodes */}
          {nodes.map((node, i) => {
            const pos = positions[i];
            if (!pos) return null;
            const color = sentimentColor(node.sentiment);
            const r = node.sentiment !== null ? 8 : 5;
            return (
              <g key={node.id}>
                <circle
                  cx={pos.x}
                  cy={pos.y}
                  r={r}
                  fill={color}
                  stroke={ARCHETYPE_COLORS[node.archetype] || "#666"}
                  strokeWidth={2}
                  opacity={node.sentiment !== null ? 1 : 0.4}
                >
                  <title>
                    {`${node.name} (${node.archetype})${node.sentiment !== null ? ` — ${node.sentiment.toFixed(1)}` : ""}`}
                  </title>
                </circle>
                {nodes.length <= 100 && (
                  <text
                    x={pos.x}
                    y={pos.y + 18}
                    textAnchor="middle"
                    fill="#888"
                    fontSize={8}
                  >
                    {node.name.split(" ")[0]}
                  </text>
                )}
              </g>
            );
          })}
        </svg>

        {/* Loading spinner overlay for waiting phases */}
        {(phase === "starting" || phase === "report") && (
          <div
            style={{
              position: "absolute",
              inset: 0,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              background: "rgba(0,0,0,0.5)",
              fontSize: 16,
              color: "#aaa",
            }}
          >
            {phase === "starting" ? "Starting simulation..." : "Generating report..."}
          </div>
        )}

        {/* Error overlay */}
        {liveError && (
          <div
            style={{
              position: "absolute",
              inset: 0,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              background: "rgba(0,0,0,0.7)",
            }}
          >
            <div style={{ background: "#1b1b1f", padding: 24, borderRadius: 8, maxWidth: 400 }}>
              <div style={{ color: "#f87171", fontWeight: 600, marginBottom: 8 }}>
                Simulation Error
              </div>
              <div style={{ color: "#ccc", fontSize: 13 }}>{liveError}</div>
              <button
                onClick={resetLive}
                style={{
                  marginTop: 16,
                  background: "#2563eb",
                  border: "none",
                  borderRadius: 6,
                  padding: "8px 16px",
                  color: "#fff",
                  cursor: "pointer",
                }}
              >
                Try Again
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Live debate feed at the bottom */}
      {edges.length > 0 && (
        <div
          style={{
            height: 140,
            borderTop: "1px solid #2a2a2e",
            background: "#16161a",
            overflowY: "auto",
            padding: "8px 16px",
            fontSize: 12,
          }}
        >
          {edges
            .slice(-8)
            .reverse()
            .map((e) => (
              <div
                key={e.id}
                style={{
                  padding: "6px 0",
                  borderBottom: "1px solid #1e1e22",
                  display: "flex",
                  gap: 8,
                }}
              >
                <span style={{ color: "#888", minWidth: 30 }}>R{e.round}</span>
                <span style={{ color: sentimentColor(e.a_sentiment_after) }}>
                  {e.a_name}
                </span>
                <span style={{ color: "#555" }}>
                  ({e.a_stance}) vs
                </span>
                <span style={{ color: sentimentColor(e.b_sentiment_after) }}>
                  {e.b_name}
                </span>
                <span style={{ color: "#555" }}>({e.b_stance})</span>
                {(e.a_converted || e.b_converted) && (
                  <span style={{ color: "#facc15", fontWeight: 600 }}>CONVERSION</span>
                )}
              </div>
            ))}
        </div>
      )}

      {/* Report drawer when complete */}
      {liveReport && phase === "complete" && (
        <div
          style={{
            position: "absolute",
            bottom: 0,
            left: 0,
            right: 0,
            maxHeight: "60vh",
            background: "#1b1b1f",
            borderTop: "2px solid #2563eb",
            overflowY: "auto",
            padding: "24px 32px",
            zIndex: 20,
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
            <h2 style={{ margin: 0, fontSize: 18 }}>Marketing Report</h2>
            <button
              onClick={resetLive}
              style={{
                background: "#333",
                border: "none",
                borderRadius: 6,
                padding: "6px 14px",
                color: "#eee",
                cursor: "pointer",
                fontSize: 12,
              }}
            >
              New Simulation
            </button>
          </div>
          <pre
            style={{
              whiteSpace: "pre-wrap",
              fontFamily: "inherit",
              fontSize: 13,
              lineHeight: 1.7,
              color: "#ddd",
            }}
          >
            {liveReport}
          </pre>
        </div>
      )}
    </div>
  );
}
