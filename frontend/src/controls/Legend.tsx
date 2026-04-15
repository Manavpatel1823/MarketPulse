import { useMemo } from "react";
import { useStore } from "../store";

const SCALE = [-10, -5, 0, 5, 10];

function sentimentColor(s: number): string {
  const t = Math.max(-10, Math.min(10, s)) / 10;
  if (t >= 0) {
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

export function Legend() {
  const graph = useStore((s) => s.graph);
  const filter = useStore((s) => s.archetypeFilter);
  const setFilter = useStore((s) => s.setArchetypeFilter);

  const archetypes = useMemo(() => {
    if (!graph) return [] as { name: string; count: number }[];
    const m = new Map<string, number>();
    for (const n of graph.nodes) m.set(n.archetype, (m.get(n.archetype) ?? 0) + 1);
    return Array.from(m.entries())
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => b.count - a.count);
  }, [graph]);

  if (!graph) return null;

  return (
    <div
      style={{
        position: "absolute",
        top: 16,
        left: 16,
        background: "rgba(17,17,20,0.92)",
        border: "1px solid #2a2a30",
        borderRadius: 8,
        padding: 12,
        zIndex: 20,
        boxShadow: "0 6px 24px rgba(0,0,0,0.5)",
        backdropFilter: "blur(6px)",
        maxWidth: 280,
      }}
    >
      <div style={{ fontSize: 10, color: "#888", textTransform: "uppercase", letterSpacing: 0.5, marginBottom: 6 }}>
        Sentiment
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 4, marginBottom: 10 }}>
        {SCALE.map((s) => (
          <div key={s} style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 2 }}>
            <div
              style={{
                width: 28,
                height: 12,
                background: sentimentColor(s),
                borderRadius: 2,
              }}
            />
            <span style={{ fontSize: 9, color: "#888" }}>{s > 0 ? `+${s}` : s}</span>
          </div>
        ))}
      </div>

      <div style={{ fontSize: 10, color: "#888", textTransform: "uppercase", letterSpacing: 0.5, marginBottom: 6 }}>
        Archetypes {filter && <span style={{ color: "#0af" }}>(filtered)</span>}
      </div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
        {archetypes.map((a) => {
          const active = filter === a.name;
          return (
            <button
              key={a.name}
              onClick={() => setFilter(active ? null : a.name)}
              style={{
                background: active ? "#0af" : "#1b1b1f",
                color: active ? "#111" : "#ccc",
                border: "1px solid " + (active ? "#0af" : "#333"),
                padding: "3px 8px",
                borderRadius: 12,
                fontSize: 11,
                cursor: "pointer",
                fontWeight: active ? 700 : 500,
              }}
            >
              {a.name} · {a.count}
            </button>
          );
        })}
      </div>
    </div>
  );
}
