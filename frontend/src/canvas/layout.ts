import type { GraphNode } from "../api";

// Radial-by-archetype layout. Cheap, deterministic, no extra deps.
// Archetype groups are placed around a big circle; agents inside each group
// sit on a smaller ring. Produces visible clusters that mirror the panel
// composition, so segment patterns pop on the canvas.

const RING_RADIUS = 650;
const CLUSTER_RADIUS = 150;

export function radialLayout(
  nodes: GraphNode[],
): Record<number, { x: number; y: number }> {
  const groups = new Map<string, GraphNode[]>();
  for (const n of nodes) {
    const key = n.archetype || "unknown";
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key)!.push(n);
  }
  const archs = Array.from(groups.keys()).sort();
  const pos: Record<number, { x: number; y: number }> = {};

  archs.forEach((arch, ai) => {
    const groupAngle = (2 * Math.PI * ai) / archs.length;
    const gx = Math.cos(groupAngle) * RING_RADIUS;
    const gy = Math.sin(groupAngle) * RING_RADIUS;
    const members = groups.get(arch)!;
    members.forEach((n, mi) => {
      const memberAngle = (2 * Math.PI * mi) / Math.max(members.length, 1);
      const r =
        members.length === 1
          ? 0
          : CLUSTER_RADIUS * (0.5 + 0.5 * (members.length > 4 ? 1 : 0));
      pos[n.id] = {
        x: gx + Math.cos(memberAngle) * r,
        y: gy + Math.sin(memberAngle) * r,
      };
    });
  });
  return pos;
}
