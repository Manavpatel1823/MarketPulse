import { useCallback, useRef, useState } from "react";
import { chatWithAgent } from "../api";
import { useStore } from "../store";

interface ChatMessage {
  role: "user" | "agent";
  text: string;
}

export function AgentDetail() {
  const agent = useStore((s) => s.selectedAgent);
  const graph = useStore((s) => s.graph);
  const selectedRunId = useStore((s) => s.selectedRunId);
  const setSelectedAgent = useStore((s) => s.setSelectedAgent);

  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [chatOpen, setChatOpen] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  const sendMessage = useCallback(async () => {
    if (!chatInput.trim() || !agent || !selectedRunId || chatLoading) return;
    const msg = chatInput.trim();
    setChatInput("");
    setChatMessages((prev) => [...prev, { role: "user", text: msg }]);
    setChatLoading(true);
    try {
      const res = await chatWithAgent(selectedRunId, agent.id, msg);
      setChatMessages((prev) => [...prev, { role: "agent", text: res.response }]);
    } catch (e: any) {
      setChatMessages((prev) => [
        ...prev,
        { role: "agent", text: `Error: ${e.message}` },
      ]);
    } finally {
      setChatLoading(false);
      setTimeout(() => chatEndRef.current?.scrollIntoView({ behavior: "smooth" }), 50);
    }
  }, [chatInput, agent, selectedRunId, chatLoading]);

  if (!agent || !graph) return null;

  const debates = graph.edges.filter(
    (e) => e.source === agent.id || e.target === agent.id,
  );
  const timeline = Object.entries(agent.sentiment_by_round)
    .map(([r, s]) => [Number(r), s as number] as [number, number])
    .sort((a, b) => a[0] - b[0]);

  const sentimentColor = (s: number | null) => {
    if (s === null) return "#888";
    if (s > 3) return "#4ade80";
    if (s < -3) return "#f87171";
    return "#facc15";
  };

  return (
    <div
      style={{
        position: "absolute",
        top: 70,
        right: 16,
        width: 400,
        maxHeight: "calc(100vh - 100px)",
        background: "#1b1b1f",
        border: "1px solid #333",
        borderRadius: 8,
        color: "#eee",
        display: "flex",
        flexDirection: "column",
        fontSize: 13,
        zIndex: 10,
        overflow: "hidden",
      }}
    >
      {/* Header */}
      <div style={{ padding: "14px 16px 10px", borderBottom: "1px solid #2a2a2e" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
          <div>
            <div style={{ fontSize: 16, fontWeight: 600 }}>{agent.name}</div>
            <div style={{ color: "#aaa", fontSize: 12 }}>
              {agent.archetype} · age {agent.age ?? "?"} · {agent.income_bracket ?? "?"}
            </div>
          </div>
          <button
            onClick={() => { setSelectedAgent(null); setChatMessages([]); setChatOpen(false); }}
            style={{
              background: "transparent",
              border: "1px solid #444",
              color: "#aaa",
              borderRadius: 4,
              padding: "2px 8px",
              cursor: "pointer",
            }}
          >
            x
          </button>
        </div>
        <div style={{ display: "flex", gap: 12, marginTop: 8, fontSize: 12 }}>
          <span>
            Final:{" "}
            <b style={{ color: sentimentColor(agent.final_sentiment) }}>
              {agent.final_sentiment?.toFixed(1) ?? "?"}
            </b>
          </span>
          <span>
            Start:{" "}
            <b>{agent.initial_sentiment?.toFixed(1) ?? "?"}</b>
          </span>
          <span>Conversions: <b>{agent.conversion_count}</b></span>
        </div>
      </div>

      {/* Scrollable content area */}
      <div style={{ flex: 1, overflowY: "auto", padding: "0 16px 12px" }}>
        {/* Sentiment timeline */}
        <div style={{ marginTop: 12 }}>
          <div style={{ fontSize: 11, color: "#888" }}>SENTIMENT BY ROUND</div>
          <div style={{ display: "flex", gap: 6, marginTop: 4, flexWrap: "wrap" }}>
            {timeline.map(([r, s]) => (
              <div
                key={r}
                style={{
                  background: "#111",
                  border: "1px solid #333",
                  padding: "3px 8px",
                  borderRadius: 4,
                  fontSize: 12,
                }}
              >
                R{r}:{" "}
                <b style={{ color: sentimentColor(s) }}>{s.toFixed(1)}</b>
              </div>
            ))}
          </div>
        </div>

        {/* Debates */}
        <div style={{ marginTop: 12 }}>
          <div style={{ fontSize: 11, color: "#888" }}>
            DEBATES ({debates.length})
          </div>
          {debates.length === 0 ? (
            <div style={{ color: "#666", fontSize: 12, marginTop: 6 }}>
              No debate records.
            </div>
          ) : (
            debates.slice(0, 6).map((d) => {
              const mine =
                d.source === agent.id
                  ? { stance: d.a_stance, shift: d.a_shift, conv: d.a_convinced, arg: d.a_argument }
                  : { stance: d.b_stance, shift: d.b_shift, conv: d.b_convinced, arg: d.b_argument };
              return (
                <div
                  key={d.id}
                  style={{
                    marginTop: 6,
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
                  <div style={{ fontSize: 12, marginTop: 4, fontStyle: "italic", color: "#ccc" }}>
                    "{mine.arg}"
                  </div>
                </div>
              );
            })
          )}
          {debates.length > 6 && (
            <div style={{ fontSize: 11, color: "#666", marginTop: 4 }}>
              +{debates.length - 6} more debates
            </div>
          )}
        </div>

        {/* Chat section */}
        <div style={{ marginTop: 16 }}>
          {!chatOpen ? (
            <button
              onClick={() => setChatOpen(true)}
              style={{
                width: "100%",
                padding: "10px 12px",
                background: "linear-gradient(135deg, #2563eb, #7c3aed)",
                border: "none",
                borderRadius: 6,
                color: "#fff",
                fontSize: 13,
                fontWeight: 600,
                cursor: "pointer",
                letterSpacing: 0.3,
              }}
            >
              Chat with {agent.name}
            </button>
          ) : (
            <>
              <div style={{ fontSize: 11, color: "#888", marginBottom: 6 }}>
                CHAT WITH {agent.name.toUpperCase()}
              </div>
              {/* Messages */}
              <div
                style={{
                  maxHeight: 250,
                  overflowY: "auto",
                  display: "flex",
                  flexDirection: "column",
                  gap: 8,
                }}
              >
                {chatMessages.length === 0 && (
                  <div style={{ color: "#555", fontSize: 12, padding: "8px 0" }}>
                    Ask {agent.name} about their opinions, what arguments convinced
                    them, or why they feel the way they do.
                  </div>
                )}
                {chatMessages.map((m, i) => (
                  <div
                    key={i}
                    style={{
                      padding: "8px 12px",
                      borderRadius: 8,
                      fontSize: 12,
                      lineHeight: 1.5,
                      maxWidth: "90%",
                      ...(m.role === "user"
                        ? {
                            alignSelf: "flex-end",
                            background: "#2563eb",
                            color: "#fff",
                            borderBottomRightRadius: 2,
                          }
                        : {
                            alignSelf: "flex-start",
                            background: "#2a2a2e",
                            color: "#ddd",
                            borderBottomLeftRadius: 2,
                          }),
                    }}
                  >
                    {m.role === "agent" && (
                      <div style={{ fontSize: 10, color: "#888", marginBottom: 3 }}>
                        {agent.name} ({agent.archetype})
                      </div>
                    )}
                    {m.text}
                  </div>
                ))}
                {chatLoading && (
                  <div
                    style={{
                      alignSelf: "flex-start",
                      background: "#2a2a2e",
                      padding: "8px 12px",
                      borderRadius: 8,
                      fontSize: 12,
                      color: "#888",
                    }}
                  >
                    {agent.name} is thinking...
                  </div>
                )}
                <div ref={chatEndRef} />
              </div>
            </>
          )}
        </div>
      </div>

      {/* Chat input — pinned to bottom */}
      {chatOpen && (
        <div
          style={{
            padding: "10px 16px",
            borderTop: "1px solid #2a2a2e",
            background: "#16161a",
            display: "flex",
            gap: 8,
          }}
        >
          <input
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") sendMessage(); }}
            placeholder={`Ask ${agent.name} something...`}
            disabled={chatLoading}
            style={{
              flex: 1,
              background: "#111",
              border: "1px solid #333",
              borderRadius: 6,
              padding: "8px 12px",
              color: "#eee",
              fontSize: 13,
              outline: "none",
            }}
          />
          <button
            onClick={sendMessage}
            disabled={chatLoading || !chatInput.trim()}
            style={{
              background: chatLoading || !chatInput.trim() ? "#333" : "#2563eb",
              border: "none",
              borderRadius: 6,
              padding: "8px 14px",
              color: "#fff",
              fontSize: 13,
              cursor: chatLoading || !chatInput.trim() ? "not-allowed" : "pointer",
              fontWeight: 600,
            }}
          >
            Send
          </button>
        </div>
      )}
    </div>
  );
}
