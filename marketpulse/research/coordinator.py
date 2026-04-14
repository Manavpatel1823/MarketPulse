"""Orchestrate web research: fire queries in parallel, parse once."""
import asyncio

from marketpulse.memory.shared import (
    CompetitorInfo,
    ProductInfo,
    ResearchFinding,
    SharedMemory,
)
from marketpulse.research import parser, searcher


def _product_from_extracted(name: str, raw: dict) -> ProductInfo:
    # Defensive defaults for any missing field — the extractor is best-effort.
    return ProductInfo(
        name=name,
        description=raw.get("description", "") or "",
        price=raw.get("price", "") or "",
        features=list(raw.get("features", []) or [])[:10],
        category=raw.get("category", "") or "",
    )


def _competitor_from_extracted(raw: dict) -> CompetitorInfo:
    return CompetitorInfo(
        name=raw.get("name", "Unknown") or "Unknown",
        description=raw.get("description", "") or "",
        price=raw.get("price", "") or "",
        key_features=list(raw.get("key_features", []) or [])[:6],
    )


def _finding_from_extracted(raw: dict) -> ResearchFinding:
    sentiment = raw.get("sentiment", "neutral")
    if sentiment not in {"positive", "neutral", "negative"}:
        sentiment = "neutral"
    return ResearchFinding(
        source=raw.get("source", "web") or "web",
        summary=raw.get("summary", "") or "",
        sentiment=sentiment,
        category=raw.get("category", "general") or "general",
    )


async def research_product(name: str, llm) -> SharedMemory:
    """Search → extract → assemble SharedMemory. 2 DDG calls + 1 LLM call.

    Queries run SEQUENTIALLY (not parallel). DDG aggressively rate-limits
    parallel requests from the same IP — firing both at once triggers silent
    hangs. Sequential + small pause is reliable.

    Each search is wrapped in a timeout so one stuck query can't block the run;
    if DDG fails entirely we fall back to a stub product.
    """
    queries = [
        f"{name} review vs competitors",
        f"{name} specifications price market share",
    ]
    snippets = []
    for q in queries:
        try:
            batch = await asyncio.wait_for(
                searcher.search(q, max_results=4),
                timeout=12.0,
            )
            snippets.extend(batch)
        except asyncio.TimeoutError:
            print(f"  [search timeout] {q!r} — continuing with partial results")
        await asyncio.sleep(0.5)  # avoid back-to-back throttle

    if not snippets:
        # No network / DDG rate-limited — return a stub so the sim can still run.
        return SharedMemory(
            product=ProductInfo(
                name=name,
                description=f"(research unavailable — running with minimal info)",
                price="",
                features=[],
                category="",
            )
        )

    extracted = await parser.extract(snippets, name, llm)

    return SharedMemory(
        product=_product_from_extracted(name, extracted.product),
        competitors=[_competitor_from_extracted(c) for c in extracted.competitors],
        research_findings=[_finding_from_extracted(f) for f in extracted.findings],
        market_context=extracted.market_context,
        signals=extracted.signals,
    )


async def augment_with_category_competitors(
    shared: SharedMemory,
    llm,
    max_extra: int = 3,
) -> SharedMemory:
    """For brief-uploaded products: search the web by CATEGORY (not name)
    to find real competitors. The brief tells us what the product *is*;
    the web tells us who it competes against in that space.

    No-op if the brief had no category, or already has 3+ competitors.
    Modifies and returns `shared` for caller convenience.
    """
    category = (shared.product.category or "").strip()
    if not category:
        return shared
    if len(shared.competitors) >= 3:
        return shared

    queries = [
        f"top {category} brands 2026",
        f"best {category} review comparison",
    ]
    snippets = []
    for q in queries:
        try:
            batch = await asyncio.wait_for(
                searcher.search(q, max_results=4),
                timeout=12.0,
            )
            snippets.extend(batch)
        except asyncio.TimeoutError:
            print(f"  [search timeout] {q!r}")
        await asyncio.sleep(0.5)

    if not snippets:
        return shared

    # One small LLM call: extract competitors from category snippets,
    # excluding the product itself.
    snippet_block = "\n".join(
        f"[{i}] {s.title} — {(s.snippet or '')[:160]}"
        for i, s in enumerate(snippets[:8], 1)
    )
    existing = {c.name.lower() for c in shared.competitors}
    existing.add(shared.product.name.lower())

    system = (
        "You extract real competitor brands/products from web search snippets. "
        "Be conservative — only list names that consumers would actually "
        "cross-shop. Skip aggregators, listicles-as-brands, and irrelevant hits."
    )
    user = (
        f"Category: {category}\n"
        f"Excluded (already known or is the product itself): "
        f"{', '.join(sorted(existing))}\n\n"
        f"Snippets:\n{snippet_block}\n\n"
        f"Return JSON: {{\"competitors\": ["
        '{"name": str, "price": str, "key_features": [str], "description": str}, ...'
        f"]}}\n"
        f"Limit to {max_extra} entries. Skip anything in the excluded list."
    )

    try:
        raw = await llm.generate_json(system, user)
    except Exception as e:
        print(f"  [augment_competitors] LLM call failed: {e}")
        return shared

    new_competitors = []
    for c in (raw.get("competitors", []) or [])[:max_extra]:
        nm = (c.get("name") or "").strip()
        if not nm or nm.lower() in existing:
            continue
        new_competitors.append(_competitor_from_extracted(c))
        existing.add(nm.lower())

    shared.competitors.extend(new_competitors)
    return shared
