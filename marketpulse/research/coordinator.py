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
        features=list(raw.get("features", []) or [])[:15],
        category=raw.get("category", "") or "",
        detailed_description=(raw.get("detailed_description") or "").strip(),
        risks=[r for r in (raw.get("risks") or []) if r][:6],
        target_audience=(raw.get("target_audience") or "").strip(),
    )


def _competitor_from_extracted(raw: dict) -> CompetitorInfo:
    return CompetitorInfo(
        name=raw.get("name", "Unknown") or "Unknown",
        description=raw.get("description", "") or "",
        price=raw.get("price", "") or "",
        key_features=list(raw.get("key_features", []) or [])[:6],
        positioning=(raw.get("positioning") or "").strip(),
    )


async def enrich_competitor_briefs(shared: SharedMemory, llm) -> SharedMemory:
    """Search each competitor on the web, then run ONE LLM call that writes
    comparative positioning briefs grounded in the real snippets.

    For every competitor without a positioning: 1 DDG search (sequential,
    throttled — DDG rate-limits parallels). Snippets feed the LLM so the
    brief references real features/prices/reviews, not hallucinated ones.
    Skips any competitor that already has a positioning string.
    """
    todo = [c for c in shared.competitors if not c.positioning]
    if not todo:
        return shared

    category = shared.product.category or ""
    snippets_by_name: dict[str, list] = {}
    for c in todo:
        query = f"{c.name} {category} features review price".strip()
        try:
            batch = await asyncio.wait_for(
                searcher.search(query, max_results=3),
                timeout=10.0,
            )
            snippets_by_name[c.name] = batch
        except asyncio.TimeoutError:
            print(f"  [enrich_competitors] search timeout for {c.name!r}")
            snippets_by_name[c.name] = []
        await asyncio.sleep(0.5)  # DDG politeness

    def _snip_block(c: CompetitorInfo) -> str:
        ss = snippets_by_name.get(c.name, [])
        if not ss:
            return "  (no web snippets available)"
        return "\n".join(
            f"  [{i}] {s.title} — {(s.snippet or '')[:200]}"
            for i, s in enumerate(ss, 1)
        )

    comp_block = "\n".join(
        f"== {c.name} ({c.price or 'price unknown'}) ==\n"
        f"  declared features: {', '.join(c.key_features) or c.description or 'none listed'}\n"
        f"  web snippets:\n{_snip_block(c)}"
        for c in todo
    )
    system = (
        "You write competitor positioning briefs for a market-research panel. "
        "Ground every brief in the web snippets — cite concrete features, specs, "
        "or prices from the snippets where available. Name trade-offs bluntly; "
        "no marketing fluff, no hedges."
    )
    user = (
        f"Product under study: {shared.product.name} "
        f"({category or 'unknown category'}).\n"
        f"Our product's features: {', '.join(shared.product.features[:10]) or 'unspecified'}.\n\n"
        f"Competitors to brief:\n{comp_block}\n\n"
        'Return JSON: {"briefs": [{"name": str, "positioning": str, '
        '"overlapping_features": [str, ...]}, ...]}\n'
        "For each competitor:\n"
        "- positioning: 60-90 words covering strengths, weaknesses, target buyer, "
        "and price anchor vs. the category. Be comparative — call out where this "
        "competitor beats or loses to the product under study on specific features.\n"
        "- overlapping_features: 2-5 concrete features this competitor shares with "
        "the product under study (so debaters can argue 'X already has this for less')."
    )

    try:
        raw = await llm.generate_json(system, user)
    except Exception as e:
        print(f"  [enrich_competitors] LLM call failed: {e}")
        return shared

    by_name = {
        (b.get("name") or "").strip().lower(): b
        for b in (raw.get("briefs") or [])
    }
    for c in todo:
        entry = by_name.get(c.name.strip().lower())
        if not entry:
            continue
        pos = (entry.get("positioning") or "").strip()
        if pos:
            c.positioning = pos
        overlap = [f for f in (entry.get("overlapping_features") or []) if f][:5]
        if overlap:
            # Merge overlap into key_features without dupes, preserving order.
            existing = {f.lower() for f in c.key_features}
            for f in overlap:
                if f.lower() not in existing:
                    c.key_features.append(f)
                    existing.add(f.lower())
    # Rebuild graph with enriched competitor positioning
    shared.build_knowledge_graph()
    return shared


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

    shared = SharedMemory(
        product=_product_from_extracted(name, extracted.product),
        competitors=[_competitor_from_extracted(c) for c in extracted.competitors],
        research_findings=[_finding_from_extracted(f) for f in extracted.findings],
        market_context=extracted.market_context,
        signals=extracted.signals,
    )
    shared.build_knowledge_graph()
    return shared


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
    # Rebuild graph with the newly discovered competitors
    shared.build_knowledge_graph()
    return shared
