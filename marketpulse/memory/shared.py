from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from marketpulse.knowledge.graph import KnowledgeGraph


@dataclass
class ProductInfo:
    name: str
    description: str
    price: str
    features: list[str]
    category: str
    detailed_description: str = ""  # 3-5 sentence value prop + differentiators
    risks: list[str] = field(default_factory=list)  # limitations / weaknesses agents should debate
    target_audience: str = ""  # who this is for (1-2 sentences)


@dataclass
class CompetitorInfo:
    name: str
    description: str
    price: str
    key_features: list[str]
    positioning: str = ""  # ~50-word strengths/weaknesses/target brief, filled by enrich step


@dataclass
class ResearchFinding:
    source: str
    summary: str
    sentiment: str  # "positive" | "negative" | "neutral"
    category: str  # "price" | "quality" | "features" | "support" | etc.


@dataclass
class MarketSignals:
    """How the market treats this product — drives panel composition.

    `brand_tier` is the only field v1 uses for panel skew. The other two are
    stored for future work (archetype-within-tier weighting).
    """
    brand_tier: str        # "incumbent" | "challenger" | "unknown" | "controversial"
    category_maturity: str # "emerging" | "established" | "saturated"
    price_position: str    # "premium" | "parity" | "budget"


@dataclass
class SharedMemory:
    product: ProductInfo
    competitors: list[CompetitorInfo] = field(default_factory=list)
    research_findings: list[ResearchFinding] = field(default_factory=list)
    market_context: str = ""
    signals: MarketSignals | None = None
    knowledge_graph: KnowledgeGraph | None = None

    # Raw source text — kept for entity extraction. Set by uploader/from_text
    # but not persisted or sent to agents. None for web-research path.
    _raw_source_text: str | None = field(default=None, repr=False)

    def build_knowledge_graph(self) -> None:
        """Build (or rebuild) the knowledge graph from current research data."""
        from marketpulse.knowledge.graph import KnowledgeGraph
        self.knowledge_graph = KnowledgeGraph.from_shared_memory(self)

    async def enrich_graph_from_text(self, llm) -> None:
        """Run LLM entity extraction on raw source text and merge into graph.

        Only runs if _raw_source_text is available (i.e. from-file or from-url
        path, not web research). Builds the base graph first if needed.
        """
        if not self._raw_source_text:
            return
        if self.knowledge_graph is None:
            self.build_knowledge_graph()
        from marketpulse.knowledge.extractor import extract_entities
        extraction = await extract_entities(
            self._raw_source_text, self.product.name, llm,
        )
        if extraction.entities:
            self.knowledge_graph.enrich_from_extraction(extraction)

    def get_agent_briefing(self, agent_id: str | None = None, archetype: str | None = None) -> str:
        """Render the briefing. If agent_id is given, the feature list and
        research findings are shuffled with a per-agent deterministic seed
        so primacy bias doesn't push every agent toward the same first
        feature. The shuffle is stable across rounds for one agent (their
        worldview is consistent) but varies across agents in the panel.
        """
        if agent_id is not None:
            rng = random.Random(agent_id)
            features = list(self.product.features)
            rng.shuffle(features)
            findings = list(self.research_findings)
            rng.shuffle(findings)
        else:
            features = self.product.features
            findings = self.research_findings

        lines = [
            f"Product: {self.product.name} - {self.product.description}",
            f"Price: {self.product.price}",
            f"Features: {', '.join(features)}",
        ]
        # Risks were being silently discarded from agent briefings; this meant
        # agents had to re-derive weaknesses from findings alone. Surface them
        # directly so skeptics get to name real trade-offs, not generic ones.
        if self.product.risks:
            risks = list(self.product.risks)
            if agent_id is not None:
                rng = random.Random(f"risks-{agent_id}")
                rng.shuffle(risks)
            lines.append(f"Known weaknesses / trade-offs: {'; '.join(risks)}")
        if self.competitors:
            lines.append("\nCompetitors:")
            for c in self.competitors:
                lines.append(f"- {c.name} ({c.price}): {', '.join(c.key_features)}")
                if c.positioning:
                    lines.append(f"  Positioning: {c.positioning}")
        if findings:
            lines.append("\nKey Research Findings:")
            for f in findings[:10]:
                lines.append(f"- [{f.sentiment}] {f.summary}")
        if self.market_context:
            lines.append(f"\nMarket Context: {self.market_context}")
        # Graph-derived competitive intelligence, tailored to archetype
        if self.knowledge_graph is not None and archetype:
            graph_ctx = self.knowledge_graph.get_agent_graph_context(
                self.product.name, archetype,
            )
            if graph_ctx:
                lines.append(f"\nCompetitive Intelligence:\n{graph_ctx}")
        return "\n".join(lines)
