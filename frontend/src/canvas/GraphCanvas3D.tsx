import { useEffect, useMemo, useRef } from "react";
import ForceGraph3D from "react-force-graph-3d";
import * as THREE from "three";
import { useStore } from "../store";
import type { GraphEdge, GraphNode as ApiNode } from "../api";

interface FGNode {
  id: number;
  agent: ApiNode;
  sentiment: number;
}

interface FGLink {
  source: number;
  target: number;
  edge: GraphEdge;
}

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

function stanceColor(stance: string): string {
  if (stance === "agree") return "#2a9d54";
  if (stance === "partial") return "#d9a441";
  return "#c24b4b";
}

function roundRect(
  ctx: CanvasRenderingContext2D,
  x: number, y: number, w: number, h: number, r: number,
) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}

// Sphere + camera-facing text label sitting below it.
function makeLabelSprite(text: string, isSel: boolean): THREE.Sprite {
  const W = 512;
  const H = 96;
  const canvas = document.createElement("canvas");
  canvas.width = W;
  canvas.height = H;
  const ctx = canvas.getContext("2d")!;
  ctx.clearRect(0, 0, W, H);

  // Soft pill background so the label stays legible on dark space.
  ctx.globalAlpha = 0.75;
  roundRect(ctx, 8, 20, W - 16, H - 40, 28);
  ctx.fillStyle = "#101014";
  ctx.fill();
  ctx.globalAlpha = 1;
  ctx.lineWidth = isSel ? 3 : 1.5;
  ctx.strokeStyle = isSel ? "#0af" : "#333";
  ctx.stroke();

  ctx.fillStyle = isSel ? "#9cf" : "#eee";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.font = "600 34px -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";
  ctx.fillText(text, W / 2, H / 2);

  const texture = new THREE.CanvasTexture(canvas);
  texture.anisotropy = 8;
  texture.needsUpdate = true;
  const sprite = new THREE.Sprite(
    new THREE.SpriteMaterial({ map: texture, transparent: true, depthWrite: false }),
  );
  sprite.scale.set(24, 24 * (H / W), 1);
  return sprite;
}

function makeAgentNode(
  agent: ApiNode,
  sentiment: number,
  isSel: boolean,
  dim: boolean,
): THREE.Group {
  const group = new THREE.Group();

  const radius = 3 + Math.min(agent.conversion_count, 8) * 0.6;
  const geom = new THREE.SphereGeometry(radius, 20, 20);
  const mat = new THREE.MeshStandardMaterial({
    color: sentimentColor(sentiment),
    emissive: isSel ? new THREE.Color("#0af") : new THREE.Color("#000"),
    emissiveIntensity: isSel ? 0.6 : 0,
    roughness: 0.5,
    metalness: 0.05,
    transparent: true,
    opacity: dim ? 0.18 : 1,
  });
  const sphere = new THREE.Mesh(geom, mat);
  group.add(sphere);

  const firstName = (agent.name || "").split(" ")[0];
  const label = makeLabelSprite(`${firstName} · ${sentiment.toFixed(1)}`, isSel);
  label.position.set(0, -(radius + 4), 0);
  (label.material as THREE.SpriteMaterial).opacity = dim ? 0.25 : 1;
  group.add(label);

  return group;
}

export function GraphCanvas3D() {
  const graph = useStore((s) => s.graph);
  const currentRound = useStore((s) => s.currentRound);
  const selectedAgent = useStore((s) => s.selectedAgent);
  const setSelectedAgent = useStore((s) => s.setSelectedAgent);
  const archetypeFilter = useStore((s) => s.archetypeFilter);
  const fgRef = useRef<any>(null);
  const wrapRef = useRef<HTMLDivElement>(null);

  const data = useMemo(() => {
    if (!graph) return { nodes: [] as FGNode[], links: [] as FGLink[] };
    const nodes: FGNode[] = graph.nodes.map((a) => ({
      id: a.id,
      agent: a,
      sentiment:
        a.sentiment_by_round[currentRound] ??
        a.final_sentiment ??
        0,
    }));
    const links: FGLink[] = graph.edges
      .filter((e) => e.round_num <= currentRound)
      .map((e) => ({ source: e.source, target: e.target, edge: e }));
    return { nodes, links };
  }, [graph, currentRound]);

  useEffect(() => {
    if (!fgRef.current) return;
    fgRef.current.d3Force?.("charge")?.strength(-120);
  }, [graph]);

  useEffect(() => {
    fgRef.current?.refresh?.();
  }, [archetypeFilter, selectedAgent]);

  if (!graph) {
    return (
      <div style={{ flex: 1, display: "grid", placeItems: "center", color: "#888" }}>
        Select a run to view the agent panel.
      </div>
    );
  }

  return (
    <div ref={wrapRef} style={{ width: "100%", height: "100%" }}>
      <ForceGraph3D
        ref={fgRef}
        graphData={data as any}
        backgroundColor="#0e0e10"
        nodeLabel={(n: any) =>
          `${n.agent.name} (${n.agent.archetype}) — ${n.sentiment.toFixed(1)}`
        }
        nodeThreeObject={(n: any) => {
          const isSel = selectedAgent?.id === n.agent.id;
          const dim = archetypeFilter !== null && n.agent.archetype !== archetypeFilter;
          return makeAgentNode(n.agent, n.sentiment, isSel, dim);
        }}
        linkColor={(l: any) => {
          const stance =
            l.edge.a_stance === l.edge.b_stance ? l.edge.a_stance : "partial";
          return stanceColor(stance);
        }}
        linkWidth={(l: any) =>
          Math.max(0.3, Math.max(Math.abs(l.edge.a_shift), Math.abs(l.edge.b_shift)) * 0.6)
        }
        linkDirectionalArrowLength={(l: any) =>
          l.edge.a_convinced || l.edge.b_convinced ? 4 : 0
        }
        linkDirectionalArrowRelPos={0.9}
        linkOpacity={0.55}
        onNodeClick={(n: any) => {
          setSelectedAgent(n.agent);
          // Fly camera to the node (FPP-ish).
          const distance = 80;
          const dist = Math.hypot(n.x, n.y, n.z) || 1;
          fgRef.current?.cameraPosition(
            { x: (n.x * (dist + distance)) / dist, y: (n.y * (dist + distance)) / dist, z: (n.z * (dist + distance)) / dist },
            n,
            1000,
          );
        }}
        onBackgroundClick={() => setSelectedAgent(null)}
        controlType="orbit"
        enableNodeDrag={false}
        showNavInfo={false}
      />
    </div>
  );
}
