import { useStore } from "../store";

function verdict(mean: number | null, pol: number | null): { label: string; color: string } {
  if (mean == null) return { label: "—", color: "#666" };
  if (mean < 0) return { label: "REJECTED", color: "#c24b4b" };
  if ((pol ?? 0) >= 3 && mean >= 2) return { label: "POLARIZED", color: "#d9a441" };
  if (mean >= 5) return { label: "BROAD APPROVAL", color: "#2a9d54" };
  if (mean >= 2) return { label: "CAUTIOUS", color: "#8a9dc9" };
  return { label: "LUKEWARM", color: "#888" };
}

export function ProductHeader() {
  const detail = useStore((s) => s.detail);
  const setReportOpen = useStore((s) => s.setReportOpen);
  if (!detail) return null;

  const v = verdict(detail.mean_sentiment, detail.polarization);

  const stat = (label: string, value: string) => (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-start" }}>
      <span style={{ fontSize: 10, color: "#888", textTransform: "uppercase", letterSpacing: 0.5 }}>
        {label}
      </span>
      <span style={{ fontSize: 14, color: "#eee", fontWeight: 600 }}>{value}</span>
    </div>
  );

  return (
    <div
      style={{
        position: "absolute",
        top: 16,
        right: 16,
        background: "rgba(17,17,20,0.92)",
        border: "1px solid #2a2a30",
        borderRadius: 8,
        padding: "12px 16px",
        display: "flex",
        gap: 20,
        alignItems: "center",
        zIndex: 20,
        boxShadow: "0 6px 24px rgba(0,0,0,0.5)",
        backdropFilter: "blur(6px)",
      }}
    >
      <div style={{ display: "flex", flexDirection: "column" }}>
        <span style={{ fontSize: 11, color: "#888" }}>Run #{detail.id}</span>
        <span style={{ fontSize: 16, color: "#fff", fontWeight: 700 }}>{detail.product_name}</span>
      </div>
      {stat("Tier", detail.brand_tier ?? "?")}
      {stat("Agents", String(detail.agent_count))}
      {stat("Rounds", String(detail.rounds))}
      {stat("Mean", detail.mean_sentiment?.toFixed(2) ?? "—")}
      {stat("Polarization", detail.polarization?.toFixed(2) ?? "—")}
      {stat("Conversions", String(detail.total_conversions ?? 0))}
      <div
        style={{
          background: v.color,
          color: "#111",
          fontSize: 11,
          fontWeight: 700,
          padding: "4px 10px",
          borderRadius: 4,
          letterSpacing: 0.5,
        }}
      >
        {v.label}
      </div>
      {detail.report && (
        <button
          onClick={() => setReportOpen(true)}
          style={{
            background: "#0af",
            color: "#111",
            border: "none",
            padding: "6px 12px",
            borderRadius: 4,
            fontSize: 12,
            fontWeight: 700,
            cursor: "pointer",
          }}
        >
          Report
        </button>
      )}
    </div>
  );
}
