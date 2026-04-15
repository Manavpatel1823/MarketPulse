import { useStore } from "../store";

export function ViewToggle() {
  const viewMode = useStore((s) => s.viewMode);
  const setViewMode = useStore((s) => s.setViewMode);

  const btn = (mode: "2d" | "3d", label: string) => {
    const active = viewMode === mode;
    return (
      <button
        onClick={() => setViewMode(mode)}
        style={{
          background: active ? "#0af" : "#1b1b1f",
          color: active ? "#111" : "#eee",
          border: "1px solid " + (active ? "#0af" : "#333"),
          padding: "6px 18px",
          fontSize: 13,
          fontWeight: 600,
          cursor: "pointer",
          borderRadius: 0,
        }}
      >
        {label}
      </button>
    );
  };

  return (
    <div
      style={{
        position: "absolute",
        bottom: 76,
        left: 16,
        display: "flex",
        zIndex: 20,
        boxShadow: "0 4px 16px rgba(0,0,0,0.5)",
        borderRadius: 6,
        overflow: "hidden",
      }}
    >
      {btn("2d", "2D")}
      {btn("3d", "3D · FPP")}
    </div>
  );
}
