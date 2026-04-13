from dataclasses import dataclass, field


@dataclass
class ProductInfo:
    name: str
    description: str
    price: str
    features: list[str]
    category: str


@dataclass
class CompetitorInfo:
    name: str
    description: str
    price: str
    key_features: list[str]


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
            f"Product: {self.product.name} - {self.product.description}",
            f"Price: {self.product.price}",
            f"Features: {', '.join(self.product.features)}",
        ]
        if self.competitors:
            lines.append("\nCompetitors:")
            for c in self.competitors:
                lines.append(f"- {c.name} ({c.price}): {', '.join(c.key_features)}")
        if self.research_findings:
            lines.append("\nKey Research Findings:")
            for f in self.research_findings[:10]:
                lines.append(f"- [{f.sentiment}] {f.summary}")
        if self.market_context:
            lines.append(f"\nMarket Context: {self.market_context}")
        return "\n".join(lines)
