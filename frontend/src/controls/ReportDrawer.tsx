import { useCallback } from "react";
import ReactMarkdown from "react-markdown";
import { useStore } from "../store";

function downloadMarkdown(text: string, filename: string) {
  const blob = new Blob([text], { type: "text/markdown" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function ReportDrawer() {
  const detail = useStore((s) => s.detail);
  const open = useStore((s) => s.reportOpen);
  const setOpen = useStore((s) => s.setReportOpen);

  const handleDownload = useCallback(() => {
    if (!detail?.report) return;
    const name = detail.product_name.replace(/[^a-zA-Z0-9]+/g, "-").toLowerCase();
    downloadMarkdown(detail.report.markdown, `${name}-report.md`);
  }, [detail]);

  if (!open || !detail?.report) return null;

  return (
    <>
      <div
        onClick={() => setOpen(false)}
        style={{
          position: "fixed",
          inset: 0,
          background: "rgba(0,0,0,0.5)",
          zIndex: 50,
        }}
      />
      <div
        style={{
          position: "fixed",
          top: 0,
          right: 0,
          bottom: 0,
          width: "min(720px, 90vw)",
          background: "#111114",
          borderLeft: "1px solid #2a2a30",
          zIndex: 51,
          display: "flex",
          flexDirection: "column",
          boxShadow: "-12px 0 40px rgba(0,0,0,0.6)",
        }}
      >
        <div
          style={{
            padding: "14px 20px",
            borderBottom: "1px solid #2a2a30",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <div>
            <div style={{ fontSize: 16, fontWeight: 700, color: "#fff" }}>
              {detail.product_name} · Report
            </div>
            <div style={{ fontSize: 11, color: "#888" }}>
              Generated {new Date(detail.report.generated_at).toLocaleString()}
            </div>
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <button
              onClick={handleDownload}
              style={{
                background: "#2563eb",
                color: "#fff",
                border: "none",
                padding: "6px 12px",
                borderRadius: 4,
                fontSize: 12,
                cursor: "pointer",
                fontWeight: 600,
              }}
            >
              Download .md
            </button>
            <button
              onClick={() => setOpen(false)}
              style={{
                background: "#1b1b1f",
                color: "#eee",
                border: "1px solid #333",
                padding: "6px 12px",
                borderRadius: 4,
                fontSize: 12,
                cursor: "pointer",
              }}
            >
              Close
            </button>
          </div>
        </div>
        <div
          style={{
            flex: 1,
            overflow: "auto",
            padding: "20px 28px",
            color: "#ddd",
            fontSize: 14,
            lineHeight: 1.6,
          }}
          className="report-md"
        >
          <ReactMarkdown>{detail.report.markdown}</ReactMarkdown>
        </div>
      </div>
    </>
  );
}
