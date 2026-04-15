import { GraphCanvas } from "./canvas/GraphCanvas";
import { GraphCanvas3D } from "./canvas/GraphCanvas3D";
import { AgentDetail } from "./controls/AgentDetail";
import { Legend } from "./controls/Legend";
import { ProductHeader } from "./controls/ProductHeader";
import { ReportDrawer } from "./controls/ReportDrawer";
import { RunPicker } from "./controls/RunPicker";
import { Timeline } from "./controls/Timeline";
import { ViewToggle } from "./controls/ViewToggle";
import { useStore } from "./store";

export default function App() {
  const loading = useStore((s) => s.loading);
  const error = useStore((s) => s.error);
  const graph = useStore((s) => s.graph);
  const viewMode = useStore((s) => s.viewMode);

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">MarketPulse Space</div>
        <RunPicker />
        <div className="spacer" />
        {loading && <span style={{ color: "#888" }}>loading…</span>}
        {error && <span style={{ color: "#c24b4b" }}>{error}</span>}
        {graph && (
          <span style={{ color: "#888", fontSize: 12 }}>
            {graph.nodes.length} agents · {graph.edges.length} debate edges
          </span>
        )}
      </header>
      <main className="canvas-wrap">
        {viewMode === "2d" ? <GraphCanvas /> : <GraphCanvas3D />}
        <ProductHeader />
        <Legend />
        <AgentDetail />
        <ViewToggle />
      </main>
      <Timeline />
      <ReportDrawer />
    </div>
  );
}
