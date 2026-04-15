import { useStore } from "../store";

export function AgentDetail() {
  const agent = useStore((s) => s.selectedAgent);
  const graph = useStore((s) => s.graph);
  const setSelectedAgent = useStore((s) => s.setSelectedAgent);

  if (!agent || !graph) return null;

  const debates = graph.edges.filter(
    (e) => e.source === agent.id || e.target === agent.id,
  );
  const timeline = Object.entries(agent.sentiment_by_round)
    .map(([r, s]) => [Number(r), s as number] as [number, number])
    .sort((a, b) => a[0] - b[0]);

  return (
    <div
      style={{
        position: "absolute",
        top: 70,
        right: 16,
        width: 380,
        maxHeight: "calc(100vh - 160px)",
        background: "#1b1b1f",
        border: "1px solid #333",
        borderRadius: 6,
        color: "#eee",
        padding: 16,
        overflowY: "auto",
        fontSize: 13,
        zIndex: 10,
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between" }}>
        <div>
          <div style={{ fontSize: 16, fontWeight: 600 }}>{agent.name}</div>
          <div style={{ color: "#aaa", fontSize: 12 }}>
            {agent.archetype} · age {agent.age ?? "?"} · {agent.income_bracket ?? "?"}
          </div>
        </div>
        <button
          onClick={() => setSelectedAgent(null)}
          style={{
            background: "transparent",
            border: "1px solid #444",
            color: "#aaa",
            borderRadius: 4,
            padding: "2px 8px",
            cursor: "pointer",
          }}
        >
          ×
        </button>
      </div>

      <div style={{ marginTop: 12 }}>
        <div style={{ fontSize: 11, color: "#888" }}>SENTIMENT BY ROUND</div>
        <div style={{ display: "flex", gap: 8, marginTop: 4, flexWrap: "wrap" }}>
          {timeline.map(([r, s]) => (
            <div
              key={r}
              style={{
                background: "#111",
                border: "1px solid #333",
                padding: "4px 8px",
                borderRadius: 4,
                fontSize: 12,
              }}
            >
              R{r}: <b>{s.toFixed(2)}</b>
            </div>
          ))}
        </div>
      </div>

      <div style={{ marginTop: 12 }}>
        <div style={{ fontSize: 11, color: "#888" }}>
          DEBATES ({debates.length})
        </div>
        {debates.length === 0 ? (
          <div style={{ color: "#666", fontSize: 12, marginTop: 6 }}>
            No debate records for this agent.
          </div>
        ) : (
          debates.map((d) => {
            const mine =
              d.source === agent.id
                ? { stance: d.a_stance, shift: d.a_shift, conv: d.a_convinced, arg: d.a_argument }
                : { stance: d.b_stance, shift: d.b_shift, conv: d.b_convinced, arg: d.b_argument };
            return (
              <div
                key={d.id}
                style={{
                  marginTop: 8,
                  padding: 8,
                  background: "#111",
                  border: "1px solid #2a2a2e",
                  borderRadius: 4,
                }}
              >
                <div style={{ fontSize: 11, color: "#888" }}>
                  Round {d.round_num} · {mine.stance} · shift{" "}
                  {mine.shift >= 0 ? "+" : ""}
                  {mine.shift.toFixed(1)}
                  {mine.conv ? " · CONVERTED" : ""}
                </div>
                <div style={{ fontSize: 12, marginTop: 4, fontStyle: "italic" }}>
                  “{mine.arg}”
                </div>
              </div>
            );
          })
        )}
      </div>

      <div style={{ marginTop: 12, fontSize: 11, color: "#666" }}>
        Conversions caused: <b>{agent.conversion_count}</b> · Initial bias:{" "}
        {agent.initial_bias?.toFixed(2) ?? "—"}
      </div>
    </div>
  );
}
