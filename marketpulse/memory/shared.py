from dataclasses import dataclass, field


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

    def get_agent_briefing(self) -> str:
        lines = [
            f"Product: {self.product.name} — {self.product.description}",
        ]
        if self.product.detailed_description:
            lines.append(f"Overview: {self.product.detailed_description}")
        lines.append(f"Price: {self.product.price}")
        lines.append(f"Features: {', '.join(self.product.features)}")
        if self.product.target_audience:
            lines.append(f"Target audience: {self.product.target_audience}")
        if self.product.risks:
            lines.append("Known risks / limitations:")
            for r in self.product.risks:
                lines.append(f"- {r}")
        if self.competitors:
            lines.append("\nCompetitors:")
            for c in self.competitors:
                lines.append(f"- {c.name} ({c.price}): {', '.join(c.key_features)}")
                if c.positioning:
                    lines.append(f"  positioning: {c.positioning}")
        if self.research_findings:
            lines.append("\nKey Research Findings:")
            for f in self.research_findings[:10]:
                lines.append(f"- [{f.sentiment}] {f.summary}")
        if self.market_context:
            lines.append(f"\nMarket Context: {self.market_context}")
        if self.signals:
            tier_notes = {
                "incumbent":
                    "Brand footprint: established market leader with wide distribution "
                    "and proven support. Factor this into risk, not into product quality.",
                "challenger":
                    "Brand footprint: rising competitor with some traction but not yet "
                    "dominant — may need to out-market incumbents to win shelf space.",
                "unknown":
                    "Brand footprint: early-stage / low recognition — discovery and trust "
                    "will need heavy marketing investment, regardless of product merit.",
                "controversial":
                    "Brand footprint: carries baggage (past incidents, quality complaints, "
                    "or PR issues). Consumers may discount claims even on a strong product.",
            }
            note = tier_notes.get(self.signals.brand_tier)
            if note:
                lines.append(f"\n{note}")
        return "\n".join(lines)
