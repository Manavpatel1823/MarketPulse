"""One LLM call that turns raw search snippets into structured research.

Returns ProductInfo fields, competitors, findings, market_context, and
the crucial MarketSignals (brand_tier etc.) used to pick panel composition.

Prompt stays under 600 tokens per project convention.
"""
from dataclasses import dataclass
from typing import Any

from marketpulse.memory.shared import MarketSignals
from marketpulse.research.searcher import SearchResult


@dataclass
class ExtractedResearch:
    product: dict           # description, price, features, category
    competitors: list[dict] # name, price, key_features, description
    findings: list[dict]    # source, summary, sentiment, category
    market_context: str
    signals: MarketSignals


VALID_TIERS = {"incumbent", "challenger", "unknown", "controversial"}
VALID_MATURITY = {"emerging", "established", "saturated"}
VALID_PRICING = {"premium", "parity", "budget"}


def _snippet_block(snippets: list[SearchResult], limit: int = 10) -> str:
    lines = []
    for i, s in enumerate(snippets[:limit], 1):
        # Trim each snippet so the prompt stays compact (faster LLM parse)
        body = (s.snippet or "")[:180]
        lines.append(f"[{i}] {s.title} — {body}")
    return "\n".join(lines)


async def extract(
    snippets: list[SearchResult],
    product_name: str,
    llm,
) -> ExtractedResearch:
    system = (
        "You are a market research analyst. Given raw web search snippets about a product, "
        "produce a structured JSON summary. Be honest — do NOT flatter the product. "
        "Classify `brand_tier` from evidence in the snippets (market share, review counts, "
        "mainstream coverage), not from the product's own marketing."
    )

    user = (
        f"Product: {product_name}\n\n"
        f"Raw search snippets:\n{_snippet_block(snippets)}\n\n"
        "Extract and return JSON with EXACTLY these keys:\n"
        "{\n"
        '  "product": {"description": str, "price": str, "features": [str, ...], "category": str},\n'
        '  "competitors": [{"name": str, "price": str, "key_features": [str], "description": str}, ...],\n'
        '  "findings": [{"source": str, "summary": str, "sentiment": "positive"|"neutral"|"negative", "category": str}, ...],\n'
        '  "market_context": str,\n'
        '  "signals": {\n'
        '    "brand_tier": "incumbent"|"challenger"|"unknown"|"controversial",\n'
        '    "category_maturity": "emerging"|"established"|"saturated",\n'
        '    "price_position": "premium"|"parity"|"budget"\n'
        "  }\n"
        "}\n\n"
        "Guidance:\n"
        "- 2-3 competitors max; real products that consumers would cross-shop.\n"
        "- 5-8 findings covering a mix of sentiments.\n"
        "- market_context: 2-3 sentences on the market this product enters.\n"
        "- brand_tier: 'incumbent' (top 1-2 in category, e.g. Apple/Samsung), "
        "'challenger' (established but not dominant, e.g. Rivian/OnePlus), "
        "'unknown' (niche/small brand, <5% awareness), "
        "'controversial' (actively mistrusted — safety, ethics, or scam concerns)."
    )

    raw: dict[str, Any] = await llm.generate_json(system, user)

    sig_raw = raw.get("signals", {}) or {}
    brand_tier = sig_raw.get("brand_tier", "unknown")
    maturity = sig_raw.get("category_maturity", "established")
    pricing = sig_raw.get("price_position", "parity")
    signals = MarketSignals(
        brand_tier=brand_tier if brand_tier in VALID_TIERS else "unknown",
        category_maturity=maturity if maturity in VALID_MATURITY else "established",
        price_position=pricing if pricing in VALID_PRICING else "parity",
    )

    return ExtractedResearch(
        product=raw.get("product", {}) or {},
        competitors=(raw.get("competitors", []) or [])[:3],
        findings=(raw.get("findings", []) or [])[:8],
        market_context=raw.get("market_context", "") or "",
        signals=signals,
    )
