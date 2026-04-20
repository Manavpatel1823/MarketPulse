import { useCallback, useRef, useState } from "react";
import { createLiveWebSocket, startSimulation } from "../api";
import { useStore } from "../store";

export function StartSimulation() {
  const [productName, setProductName] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [agentCount, setAgentCount] = useState(25);
  const [rounds, setRounds] = useState(3);
  const [launching, setLaunching] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const startLive = useStore((s) => s.startLive);
  const setSimPhase = useStore((s) => s.setSimPhase);
  const addLiveNode = useStore((s) => s.addLiveNode);
  const updateNodeSentiment = useStore((s) => s.updateNodeSentiment);
  const addLiveEdge = useStore((s) => s.addLiveEdge);
  const setLiveRound = useStore((s) => s.setLiveRound);
  const setLiveReport = useStore((s) => s.setLiveReport);
  const setLiveError = useStore((s) => s.setLiveError);
  const setLiveMeanSentiment = useStore((s) => s.setLiveMeanSentiment);

  const handleLaunch = useCallback(async () => {
    if (!productName.trim() || launching) return;
    setLaunching(true);
    try {
      const res = await startSimulation(productName.trim(), file, agentCount, rounds);
      startLive(res.live_id, productName.trim(), agentCount, rounds);

      // Connect WebSocket
      const ws = createLiveWebSocket(res.live_id);
      let edgeCounter = 0;

      ws.onmessage = (msg) => {
        const event = JSON.parse(msg.data);
        const { type, data } = event;

        switch (type) {
          case "sim_started":
            setSimPhase("agents");
            break;

          case "agent_created":
            addLiveNode({
              id: data.persona_id,
              name: data.name,
              archetype: data.archetype,
              age: data.age,
              income_bracket: data.income_bracket,
              sentiment: null,
              initial_bias: data.initial_bias,
            });
            break;

          case "agents_ready":
            setSimPhase("opinions");
            break;

          case "opinion_formed":
            updateNodeSentiment(data.persona_id, data.sentiment);
            break;

          case "opinions_done":
            setSimPhase("debating");
            break;

          case "round_started":
            setLiveRound(data.round);
            setSimPhase("debating");
            break;

          case "debate_result":
            edgeCounter++;
            updateNodeSentiment(data.a.persona_id, data.a.sentiment_after);
            updateNodeSentiment(data.b.persona_id, data.b.sentiment_after);
            addLiveEdge({
              id: `e-${edgeCounter}`,
              round: data.round,
              source: data.a.persona_id,
              target: data.b.persona_id,
              a_name: data.a.name,
              b_name: data.b.name,
              a_stance: data.a.stance,
              b_stance: data.b.stance,
              a_argument: data.a.argument,
              b_argument: data.b.argument,
              a_shift: data.a.shift,
              b_shift: data.b.shift,
              a_converted: data.a.converted,
              b_converted: data.b.converted,
              a_sentiment_after: data.a.sentiment_after,
              b_sentiment_after: data.b.sentiment_after,
            });
            break;

          case "round_complete":
            setLiveRound(data.round);
            break;

          case "reflection_done":
            setSimPhase("reflection");
            break;

          case "report_started":
            setSimPhase("report");
            break;

          case "report_ready":
            setLiveReport(data.report);
            if (data.mean_sentiment != null) setLiveMeanSentiment(data.mean_sentiment);
            break;

          case "sim_complete":
            setSimPhase("complete");
            ws.close();
            break;

          case "sim_error":
            setLiveError(data.error);
            ws.close();
            break;
        }
      };

      ws.onerror = () => {
        setLiveError("WebSocket connection failed");
      };
    } catch (e: any) {
      setLiveError(e.message);
    } finally {
      setLaunching(false);
    }
  }, [productName, file, agentCount, rounds, launching]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files?.[0];
    if (f) setFile(f);
  }, []);

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        height: "100%",
        padding: 40,
      }}
    >
      <div
        style={{
          background: "#16161a",
          border: "1px solid #2a2a2e",
          borderRadius: 12,
          padding: 40,
          width: 520,
          maxWidth: "100%",
        }}
      >
        <h1 style={{ margin: "0 0 4px", fontSize: 24, fontWeight: 700 }}>
          MarketPulse
        </h1>
        <p style={{ margin: "0 0 28px", color: "#888", fontSize: 14 }}>
          AI multi-agent market simulation. Enter a product to analyze.
        </p>

        {/* Product name */}
        <label style={{ fontSize: 12, color: "#aaa", display: "block", marginBottom: 6 }}>
          Product Name
        </label>
        <input
          value={productName}
          onChange={(e) => setProductName(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") handleLaunch(); }}
          placeholder="e.g. Loop One, Tesla Model 3, iPhone 16..."
          style={{
            width: "100%",
            background: "#111",
            border: "1px solid #333",
            borderRadius: 8,
            padding: "12px 16px",
            color: "#eee",
            fontSize: 15,
            outline: "none",
            marginBottom: 20,
          }}
        />

        {/* File upload */}
        <label style={{ fontSize: 12, color: "#aaa", display: "block", marginBottom: 6 }}>
          Product Brief (optional — PDF or text file)
        </label>
        <div
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => fileRef.current?.click()}
          style={{
            border: `2px dashed ${dragOver ? "#2563eb" : "#333"}`,
            borderRadius: 8,
            padding: "20px 16px",
            textAlign: "center",
            cursor: "pointer",
            color: file ? "#eee" : "#666",
            fontSize: 13,
            marginBottom: 20,
            background: dragOver ? "rgba(37, 99, 235, 0.05)" : "transparent",
            transition: "all 0.15s",
          }}
        >
          {file ? (
            <span>
              {file.name}{" "}
              <span
                onClick={(e) => { e.stopPropagation(); setFile(null); }}
                style={{ color: "#f87171", cursor: "pointer", marginLeft: 8 }}
              >
                remove
              </span>
            </span>
          ) : (
            "Drop a PDF or text file here, or click to browse"
          )}
          <input
            ref={fileRef}
            type="file"
            accept=".pdf,.txt,.md"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            style={{ display: "none" }}
          />
        </div>

        {/* Config row */}
        <div style={{ display: "flex", gap: 16, marginBottom: 28 }}>
          <div style={{ flex: 1 }}>
            <label style={{ fontSize: 12, color: "#aaa", display: "block", marginBottom: 6 }}>
              Agents
            </label>
            <select
              value={agentCount}
              onChange={(e) => setAgentCount(Number(e.target.value))}
              style={{
                width: "100%",
                background: "#111",
                border: "1px solid #333",
                borderRadius: 8,
                padding: "10px 12px",
                color: "#eee",
                fontSize: 14,
              }}
            >
              <option value={10}>10</option>
              <option value={25}>25</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </div>
          <div style={{ flex: 1 }}>
            <label style={{ fontSize: 12, color: "#aaa", display: "block", marginBottom: 6 }}>
              Debate Rounds
            </label>
            <select
              value={rounds}
              onChange={(e) => setRounds(Number(e.target.value))}
              style={{
                width: "100%",
                background: "#111",
                border: "1px solid #333",
                borderRadius: 8,
                padding: "10px 12px",
                color: "#eee",
                fontSize: 14,
              }}
            >
              <option value={1}>1 round</option>
              <option value={2}>2 rounds</option>
              <option value={3}>3 rounds</option>
              <option value={5}>5 rounds</option>
            </select>
          </div>
        </div>

        {/* Launch button */}
        <button
          onClick={handleLaunch}
          disabled={!productName.trim() || launching}
          style={{
            width: "100%",
            padding: "14px 20px",
            background:
              !productName.trim() || launching
                ? "#333"
                : "linear-gradient(135deg, #2563eb, #7c3aed)",
            border: "none",
            borderRadius: 8,
            color: "#fff",
            fontSize: 16,
            fontWeight: 700,
            cursor: !productName.trim() || launching ? "not-allowed" : "pointer",
            letterSpacing: 0.5,
          }}
        >
          {launching ? "Launching..." : "Launch Simulation"}
        </button>
      </div>
    </div>
  );
}
