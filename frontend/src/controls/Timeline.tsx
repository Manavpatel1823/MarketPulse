import { useStore } from "../store";

export function Timeline() {
  const graph = useStore((s) => s.graph);
  const currentRound = useStore((s) => s.currentRound);
  const setCurrentRound = useStore((s) => s.setCurrentRound);

  if (!graph) return null;
  const max = graph.rounds;

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 12,
        padding: "8px 16px",
        background: "#16161a",
        borderTop: "1px solid #2a2a2e",
      }}
    >
      <div style={{ fontSize: 12, color: "#aaa", minWidth: 90 }}>
        Round: <b style={{ color: "#eee" }}>{currentRound}</b> / {max}
      </div>
      <input
        type="range"
        min={0}
        max={max}
        value={currentRound}
        step={1}
        onChange={(e) => setCurrentRound(Number(e.target.value))}
        style={{ flex: 1 }}
      />
      <div style={{ fontSize: 11, color: "#666", minWidth: 140 }}>
        {currentRound === 0 ? "Initial opinions" : `After debate round ${currentRound}`}
      </div>
    </div>
  );
}
