"""In-memory knowledge graph built from SharedMemory research data.

Extracts entities (product, competitors, features, risks, findings) and
their relationships into a networkx DiGraph.  Agents can query the graph
for multi-hop context — e.g. "which competitors share feature X?" or
"what risks relate to this competitor's strength?" — rather than reading
flat text blobs.

The graph is lightweight (typically <200 nodes for a single product brief)
and serializable to/from JSON for DB persistence.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import networkx as nx

from marketpulse.memory.shared import (
    CompetitorInfo,
    ProductInfo,
    ResearchFinding,
    SharedMemory,
)


# ── Node types ──────────────────────────────────────────────────────────

NODE_PRODUCT = "product"
NODE_COMPETITOR = "competitor"
NODE_FEATURE = "feature"
NODE_RISK = "risk"
NODE_FINDING = "finding"
NODE_CATEGORY = "category"
NODE_AUDIENCE = "audience"
NODE_PERSON = "person"
NODE_COMPANY = "company"
NODE_TECHNOLOGY = "technology"
NODE_MARKET = "market"
NODE_LOCATION = "location"

# ── Edge types ──────────────────────────────────────────────────────────

EDGE_HAS_FEATURE = "has_feature"
EDGE_HAS_RISK = "has_risk"
EDGE_COMPETES_WITH = "competes_with"
EDGE_IN_CATEGORY = "in_category"
EDGE_TARGETS = "targets"
EDGE_FINDING_ABOUT = "finding_about"
EDGE_SHARED_FEATURE = "shared_feature"  # competitor also has this feature
EDGE_PRICED_AGAINST = "priced_against"


def _node_id(node_type: str, name: str) -> str:
    """Deterministic node ID from type + name."""
    return f"{node_type}:{name.lower().strip()}"


class KnowledgeGraph:
    """Lightweight knowledge graph over product research data."""

    def __init__(self) -> None:
        self.g: nx.DiGraph = nx.DiGraph()

    # ── Build from SharedMemory ─────────────────────────────────────────

    @classmethod
    def from_shared_memory(cls, shared: SharedMemory) -> "KnowledgeGraph":
        """Build a graph from an existing SharedMemory object."""
        kg = cls()
        kg._add_product(shared.product)
        for comp in shared.competitors:
            kg._add_competitor(shared.product, comp)
        for finding in shared.research_findings:
            kg._add_finding(shared.product, finding)
        return kg

    def _add_product(self, product: ProductInfo) -> None:
        pid = _node_id(NODE_PRODUCT, product.name)
        self.g.add_node(pid, type=NODE_PRODUCT, name=product.name,
                        description=product.description,
                        price=product.price,
                        detailed_description=product.detailed_description)

        # Category
        if product.category:
            cid = _node_id(NODE_CATEGORY, product.category)
            self.g.add_node(cid, type=NODE_CATEGORY, name=product.category)
            self.g.add_edge(pid, cid, rel=EDGE_IN_CATEGORY)

        # Target audience
        if product.target_audience:
            aid = _node_id(NODE_AUDIENCE, product.target_audience[:80])
            self.g.add_node(aid, type=NODE_AUDIENCE,
                            name=product.target_audience)
            self.g.add_edge(pid, aid, rel=EDGE_TARGETS)

        # Features
        for feat in product.features:
            fid = _node_id(NODE_FEATURE, feat)
            self.g.add_node(fid, type=NODE_FEATURE, name=feat)
            self.g.add_edge(pid, fid, rel=EDGE_HAS_FEATURE)

        # Risks
        for risk in product.risks:
            rid = _node_id(NODE_RISK, risk)
            self.g.add_node(rid, type=NODE_RISK, name=risk)
            self.g.add_edge(pid, rid, rel=EDGE_HAS_RISK)

    def _add_competitor(self, product: ProductInfo, comp: CompetitorInfo) -> None:
        pid = _node_id(NODE_PRODUCT, product.name)
        cid = _node_id(NODE_COMPETITOR, comp.name)
        self.g.add_node(cid, type=NODE_COMPETITOR, name=comp.name,
                        description=comp.description, price=comp.price,
                        positioning=comp.positioning)
        self.g.add_edge(pid, cid, rel=EDGE_COMPETES_WITH)
        self.g.add_edge(cid, pid, rel=EDGE_COMPETES_WITH)

        # Price relationship
        if comp.price and product.price:
            self.g.add_edge(cid, pid, rel=EDGE_PRICED_AGAINST,
                            competitor_price=comp.price,
                            product_price=product.price)

        # Category link
        if product.category:
            cat_id = _node_id(NODE_CATEGORY, product.category)
            self.g.add_edge(cid, cat_id, rel=EDGE_IN_CATEGORY)

        # Competitor features — link shared ones to the product's feature nodes
        product_features_lower = {f.lower().strip() for f in product.features}
        for feat in comp.key_features:
            feat_id = _node_id(NODE_FEATURE, feat)
            if not self.g.has_node(feat_id):
                self.g.add_node(feat_id, type=NODE_FEATURE, name=feat)
            self.g.add_edge(cid, feat_id, rel=EDGE_HAS_FEATURE)

            # Check for shared/overlapping features (fuzzy: substring match)
            for pf in product_features_lower:
                if (feat.lower().strip() in pf or pf in feat.lower().strip()):
                    pf_id = _node_id(NODE_FEATURE, pf)
                    if self.g.has_node(pf_id):
                        self.g.add_edge(cid, pf_id, rel=EDGE_SHARED_FEATURE)
                    break

    def _add_finding(self, product: ProductInfo, finding: ResearchFinding) -> None:
        # Use source + summary hash for unique ID
        fid = _node_id(NODE_FINDING, f"{finding.source}:{finding.summary[:50]}")
        self.g.add_node(fid, type=NODE_FINDING, source=finding.source,
                        summary=finding.summary, sentiment=finding.sentiment,
                        category=finding.category)
        pid = _node_id(NODE_PRODUCT, product.name)
        self.g.add_edge(fid, pid, rel=EDGE_FINDING_ABOUT)

    # ── Enrich from LLM extraction ────────────────────────────────────

    def enrich_from_extraction(self, extraction) -> None:
        """Merge LLM-extracted entities and relationships into the graph.

        `extraction` is an ExtractionResult from knowledge.extractor.
        This adds deeper nodes (people, companies, technologies, locations)
        and multi-hop relationships that the structured ProductInfo can't
        capture (e.g. founder→formerly_at→Google, manufacturer→also_makes→AirPods).
        """
        TYPE_MAP = {
            "person": NODE_PERSON,
            "company": NODE_COMPANY,
            "product": NODE_PRODUCT,
            "technology": NODE_TECHNOLOGY,
            "feature": NODE_FEATURE,
            "market": NODE_MARKET,
            "location": NODE_LOCATION,
        }

        # Add all extracted entities as nodes (skip duplicates)
        for entity in extraction.entities:
            node_type = TYPE_MAP.get(entity.entity_type, entity.entity_type)
            nid = _node_id(node_type, entity.name)
            if not self.g.has_node(nid):
                self.g.add_node(nid, type=node_type, name=entity.name,
                                description=entity.description)
            elif entity.description and not self.g.nodes[nid].get("description"):
                # Enrich existing node with description
                self.g.nodes[nid]["description"] = entity.description

        # Add all extracted relationships as edges
        for rel in extraction.relationships:
            # Find source and target nodes — try all type prefixes
            src_node = self._find_node_by_name(rel.source)
            tgt_node = self._find_node_by_name(rel.target)
            if src_node and tgt_node:
                self.g.add_edge(src_node, tgt_node, rel=rel.relation,
                                detail=rel.detail)

    def _find_node_by_name(self, name: str) -> str | None:
        """Find a node ID by entity name, trying all type prefixes."""
        name_lower = name.lower().strip()
        # Try common prefixes
        for prefix in (NODE_PRODUCT, NODE_COMPANY, NODE_PERSON, NODE_COMPETITOR,
                       NODE_TECHNOLOGY, NODE_FEATURE, NODE_MARKET, NODE_LOCATION,
                       NODE_CATEGORY, NODE_RISK, NODE_FINDING, NODE_AUDIENCE):
            nid = f"{prefix}:{name_lower}"
            if self.g.has_node(nid):
                return nid
        return None

    # ── Query methods ───────────────────────────────────────────────────

    def get_competitors(self, product_name: str) -> list[dict]:
        """All competitors and their attributes."""
        pid = _node_id(NODE_PRODUCT, product_name)
        result = []
        for _, target, data in self.g.out_edges(pid, data=True):
            if data.get("rel") == EDGE_COMPETES_WITH:
                node = self.g.nodes[target]
                if node.get("type") == NODE_COMPETITOR:
                    result.append(dict(node))
        return result

    def get_shared_features(self, product_name: str, competitor_name: str) -> list[str]:
        """Features that both the product and a competitor share."""
        cid = _node_id(NODE_COMPETITOR, competitor_name)
        shared = []
        for _, target, data in self.g.out_edges(cid, data=True):
            if data.get("rel") == EDGE_SHARED_FEATURE:
                node = self.g.nodes.get(target, {})
                if node.get("name"):
                    shared.append(node["name"])
        return shared

    def get_competitor_advantages(self, product_name: str) -> list[dict]:
        """For each competitor, list features they have that the product lacks."""
        pid = _node_id(NODE_PRODUCT, product_name)
        product_features = {
            target for _, target, d in self.g.out_edges(pid, data=True)
            if d.get("rel") == EDGE_HAS_FEATURE
        }
        advantages = []
        for comp in self.get_competitors(product_name):
            cid = _node_id(NODE_COMPETITOR, comp["name"])
            comp_only = []
            for _, target, d in self.g.out_edges(cid, data=True):
                if d.get("rel") == EDGE_HAS_FEATURE and target not in product_features:
                    node = self.g.nodes.get(target, {})
                    if node.get("name"):
                        comp_only.append(node["name"])
            if comp_only:
                advantages.append({
                    "competitor": comp["name"],
                    "unique_features": comp_only,
                })
        return advantages

    def get_findings_by_sentiment(self, sentiment: str) -> list[dict]:
        """All findings matching a sentiment (positive/negative/neutral)."""
        return [
            dict(self.g.nodes[n])
            for n in self.g.nodes
            if self.g.nodes[n].get("type") == NODE_FINDING
            and self.g.nodes[n].get("sentiment") == sentiment
        ]

    def get_risks_related_to_competitors(self, product_name: str) -> list[dict]:
        """Risks that relate to areas where competitors are strong."""
        pid = _node_id(NODE_PRODUCT, product_name)
        risks = []
        for _, target, d in self.g.out_edges(pid, data=True):
            if d.get("rel") == EDGE_HAS_RISK:
                risk_node = self.g.nodes[target]
                risk_text = risk_node.get("name", "").lower()
                # Check if any competitor's feature/positioning overlaps
                related_comps = []
                for comp in self.get_competitors(product_name):
                    cid = _node_id(NODE_COMPETITOR, comp["name"])
                    for _, ft, fd in self.g.out_edges(cid, data=True):
                        if fd.get("rel") == EDGE_HAS_FEATURE:
                            feat_name = self.g.nodes.get(ft, {}).get("name", "").lower()
                            # Simple keyword overlap check
                            risk_words = set(risk_text.split())
                            feat_words = set(feat_name.split())
                            if risk_words & feat_words - {"the", "a", "and", "or", "for", "in", "of", "to", "with"}:
                                related_comps.append(comp["name"])
                                break
                risks.append({
                    "risk": risk_node.get("name", ""),
                    "related_competitors": related_comps,
                })
        return risks

    def get_agent_graph_context(self, product_name: str, archetype: str) -> str:
        """Render graph-derived context tailored to an agent's archetype.

        Different archetypes get different graph traversals:
        - skeptic/bargain_hunter: competitor advantages, risks, negative findings
        - early_adopter/tech_enthusiast: unique features, positive findings
        - brand_loyalist: brand positioning, category context
        - pragmatist/neutral: balanced view with shared features + risks
        """
        lines = []
        competitors = self.get_competitors(product_name)
        advantages = self.get_competitor_advantages(product_name)

        if archetype in ("skeptic", "bargain_hunter", "contrarian"):
            # Emphasize competitor strengths and product risks
            if advantages:
                lines.append("Competitor advantages you should consider:")
                for adv in advantages:
                    lines.append(f"  - {adv['competitor']} has: {', '.join(adv['unique_features'][:3])}")
            neg = self.get_findings_by_sentiment("negative")
            if neg:
                lines.append("Negative signals from research:")
                for f in neg[:3]:
                    lines.append(f"  - {f.get('summary', '')}")
            risk_comps = self.get_risks_related_to_competitors(product_name)
            exploitable = [r for r in risk_comps if r["related_competitors"]]
            if exploitable:
                lines.append("Risks where competitors do better:")
                for r in exploitable[:3]:
                    lines.append(f"  - {r['risk']} (vs {', '.join(r['related_competitors'])})")

        elif archetype in ("early_adopter", "tech_enthusiast", "impulse_buyer"):
            # Emphasize unique features and positive signals
            pos = self.get_findings_by_sentiment("positive")
            if pos:
                lines.append("Positive signals from research:")
                for f in pos[:3]:
                    lines.append(f"  - {f.get('summary', '')}")
            if competitors:
                for comp in competitors[:2]:
                    shared = self.get_shared_features(product_name, comp["name"])
                    if shared:
                        lines.append(f"  Features also in {comp['name']}: {', '.join(shared[:3])}")

        else:
            # Balanced view for pragmatist, brand_loyalist, etc.
            if advantages:
                lines.append("Key competitive landscape:")
                for adv in advantages[:2]:
                    lines.append(f"  - {adv['competitor']} uniquely offers: {', '.join(adv['unique_features'][:2])}")
            risk_comps = self.get_risks_related_to_competitors(product_name)
            exploitable = [r for r in risk_comps if r["related_competitors"]]
            if exploitable[:2]:
                lines.append("Risks to weigh:")
                for r in exploitable[:2]:
                    lines.append(f"  - {r['risk']}")

        # Multi-hop insights from extracted entities (available for all archetypes)
        multi_hop = self.get_multi_hop_insights(product_name, archetype)
        if multi_hop:
            lines.append("Deep insights:")
            for insight in multi_hop[:4]:
                lines.append(f"  - {insight}")

        return "\n".join(lines) if lines else ""

    def get_multi_hop_insights(self, product_name: str, archetype: str) -> list[str]:
        """Traverse 2-3 hop paths to surface non-obvious relationships.

        Examples of multi-hop insights:
        - Product → manufactured_by → GoerTek → also_manufactures → AirPods
        - Product → founded_by → Person → formerly_at → Google
        - Product → uses → Technology → licensed_from → Shokz
        """
        insights: list[str] = []
        product_node = self._find_node_by_name(product_name)
        if not product_node:
            return insights

        # Find the company node for this product
        company_node = None
        for _, tgt, d in self.g.out_edges(product_node, data=True):
            if self.g.nodes.get(tgt, {}).get("type") == NODE_COMPANY:
                company_node = tgt
                break
        # Also check incoming edges
        if not company_node:
            for src, _, d in self.g.in_edges(product_node, data=True):
                if self.g.nodes.get(src, {}).get("type") == NODE_COMPANY:
                    company_node = src
                    break

        search_roots = [product_node]
        if company_node:
            search_roots.append(company_node)

        for root in search_roots:
            root_name = self.g.nodes[root].get("name", root)

            # Collect all 1-hop neighbors (both directions)
            neighbors: list[tuple[str, str, str]] = []  # (mid_node_id, rel, detail)
            for _, mid, d in self.g.out_edges(root, data=True):
                neighbors.append((mid, d.get("rel", ""), d.get("detail", "")))
            for mid, _, d in self.g.in_edges(root, data=True):
                neighbors.append((mid, d.get("rel", ""), d.get("detail", "")))

            # 2-hop: root ↔ mid → target (or mid ← target)
            for mid, rel1, detail1 in neighbors:
                mid_node = self.g.nodes.get(mid, {})
                mid_name = mid_node.get("name", mid)
                mid_type = mid_node.get("type", "")

                # Follow outgoing edges from mid
                for _, target, d2 in self.g.out_edges(mid, data=True):
                    if target == root or target in search_roots:
                        continue
                    rel2 = d2.get("rel", "")
                    tgt_node = self.g.nodes.get(target, {})
                    tgt_name = tgt_node.get("name", target)
                    tgt_type = tgt_node.get("type", "")
                    detail2 = d2.get("detail", "")

                    insight = self._format_multi_hop(
                        root_name, rel1, mid_name, mid_type,
                        rel2, tgt_name, tgt_type,
                        detail1, detail2, archetype,
                    )
                    if insight and insight not in insights:
                        insights.append(insight)

        return insights

    def _format_multi_hop(
        self, root: str, rel1: str, mid: str, mid_type: str,
        rel2: str, target: str, tgt_type: str,
        detail1: str, detail2: str, archetype: str,
    ) -> str | None:
        """Format a 2-hop path into a readable insight, filtered by relevance."""
        det1 = f" ({detail1})" if detail1 else ""
        det2 = f" ({detail2})" if detail2 else ""
        r1 = rel1.replace("_", " ")
        r2 = rel2.replace("_", " ")

        # Supply chain: manufacturer → also makes → competitor
        if rel1 in ("manufactures", "manufactured_by", "supplies_to") and \
           rel2 in ("manufactures", "supplies_to"):
            return f"{mid} {r1} {root}{det1} and also {r2} {target}{det2}"

        # Team background: founder → formerly at → big company
        if rel1 in ("founded", "co_founded", "founded_by", "employs") and \
           rel2 in ("formerly_at", "worked_at"):
            return f"{mid} ({r1} {root}) was formerly at {target}{det2}"

        # Investor connections
        if rel1 in ("invested_in", "funded", "funded_by") and \
           rel2 in ("invested_in", "funded"):
            return f"{mid} funded {root}{det1} and also invested in {target}{det2}"

        # Technology licensing
        if rel1 in ("uses", "licenses_from", "licenses_to") and \
           rel2 in ("licenses_to", "uses", "developed"):
            return f"{root} uses technology from {mid}, which also serves {target}{det2}"

        # Competitor relationships via shared supplier
        if mid_type == NODE_COMPANY and tgt_type in (NODE_PRODUCT, NODE_COMPETITOR):
            if rel2 in ("manufactures", "supplies_to"):
                return f"{mid} supplies both {root} and {target}"

        # Person expertise paths (relevant for credibility assessment)
        if mid_type == NODE_PERSON and archetype in ("skeptic", "pragmatist", "brand_loyalist"):
            if rel2 == "formerly_at":
                return f"{mid} (from {root}'s team) previously worked at {target}{det2}"

        # Price/feature comparison via shared category
        if rel1 == "competes_with" and rel2 in ("priced_at", "has_feature"):
            if archetype in ("bargain_hunter", "skeptic"):
                return f"Competitor {mid}: {r2} {target}{det2}"

        return None

    # ── Serialization ───────────────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        """Serialize the graph to a JSON-friendly dict."""
        nodes = []
        for nid, attrs in self.g.nodes(data=True):
            nodes.append({"id": nid, **attrs})
        edges = []
        for src, tgt, attrs in self.g.edges(data=True):
            edges.append({"source": src, "target": tgt, **attrs})
        return {"nodes": nodes, "edges": edges}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "KnowledgeGraph":
        """Reconstruct a graph from its serialized dict."""
        kg = cls()
        for node in data.get("nodes", []):
            nid = node.pop("id")
            kg.g.add_node(nid, **node)
        for edge in data.get("edges", []):
            src = edge.pop("source")
            tgt = edge.pop("target")
            kg.g.add_edge(src, tgt, **edge)
        return kg

    # ── Stats ───────────────────────────────────────────────────────────

    @property
    def node_count(self) -> int:
        return self.g.number_of_nodes()

    @property
    def edge_count(self) -> int:
        return self.g.number_of_edges()

    def summary(self) -> str:
        by_type: dict[str, int] = {}
        for _, attrs in self.g.nodes(data=True):
            t = attrs.get("type", "unknown")
            by_type[t] = by_type.get(t, 0) + 1
        parts = [f"{count} {t}" for t, count in sorted(by_type.items())]
        return f"KnowledgeGraph: {self.node_count} nodes ({', '.join(parts)}), {self.edge_count} edges"
