import { useEffect, useState } from "react";
import { fetchRunDetail, fetchRunGraph, fetchRuns } from "../api";
import { useStore } from "../store";

export function RunPicker() {
  const runs = useStore((s) => s.runs);
  const selectedRunId = useStore((s) => s.selectedRunId);
  const setRuns = useStore((s) => s.setRuns);
  const setSelectedRunId = useStore((s) => s.setSelectedRunId);
  const setGraph = useStore((s) => s.setGraph);
  const setDetail = useStore((s) => s.setDetail);
  const setLoading = useStore((s) => s.setLoading);
  const setError = useStore((s) => s.setError);
  const [refreshing, setRefreshing] = useState(false);

  async function refreshRuns() {
    setRefreshing(true);
    try {
      const rs = await fetchRuns();
      setRuns(rs);
      setError(null);
    } catch (e) {
      setError(String(e));
    } finally {
      setRefreshing(false);
    }
  }

  useEffect(() => {
    refreshRuns();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function pick(id: number) {
    setSelectedRunId(id);
    if (id < 0) return;
    setLoading(true);
    setError(null);
    try {
      const [g, d] = await Promise.all([fetchRunGraph(id), fetchRunDetail(id)]);
      setGraph(g);
      setDetail(d);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
      <label style={{ fontSize: 13, color: "#aaa" }}>Run:</label>
      <select
        value={selectedRunId ?? -1}
        onChange={(e) => pick(Number(e.target.value))}
        style={{
          background: "#1b1b1f",
          color: "#eee",
          border: "1px solid #333",
          padding: "6px 10px",
          borderRadius: 4,
          minWidth: 380,
        }}
      >
        <option value={-1}>— pick a run —</option>
        {runs.map((r) => (
          <option key={r.id} value={r.id}>
            #{r.id} · {r.product_name}
            {r.finished_at ? "" : " · INCOMPLETE"}
          </option>
        ))}
      </select>
      <button
        onClick={refreshRuns}
        disabled={refreshing}
        title="Reload run list from database"
        style={{
          background: "#1b1b1f",
          color: "#eee",
          border: "1px solid #333",
          padding: "6px 12px",
          borderRadius: 4,
          cursor: refreshing ? "wait" : "pointer",
          fontSize: 13,
        }}
      >
        {refreshing ? "…" : "↻ Refresh"}
      </button>
    </div>
  );
}
