"""Build SharedMemory from user-provided product material (URL, file, raw text).

This is the bypass path for products that have no useful web footprint —
unreleased, internal, or pre-launch items where DDG would only return
marketing fluff (or nothing). The user hands us the source material directly
and one LLM call compresses it into the same SharedMemory shape that
`research.coordinator` produces.

Two entry points:
- `from_text(name, text, llm)` — raw paste (marketing copy, brief, transcript)
- `from_url(name, url, llm)` — fetch + strip HTML, then from_text

Output: a fully-populated SharedMemory (product + competitors + signals)
ready to feed straight into SimulationEngine. No web search performed.
"""
import re
from html.parser import HTMLParser
from typing import Any

from marketpulse.memory.shared import (
    CompetitorInfo,
    MarketSignals,
    ProductInfo,
    ResearchFinding,
    SharedMemory,
)
from marketpulse.research.parser import (
    VALID_MATURITY,
    VALID_PRICING,
    VALID_TIERS,
)

# Cap input text so the prompt stays under the 600-token convention even
# if the user pastes a 50-page brief.
MAX_INPUT_CHARS = 10000


class _TextExtractor(HTMLParser):
    """Stdlib-only HTML→text. Skips <script>/<style>; collapses whitespace later."""

    _SKIP = {"script", "style", "noscript", "head", "meta", "link"}

    def __init__(self) -> None:
        super().__init__()
        self._chunks: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):  # type: ignore[override]
        del attrs
        if tag in self._SKIP:
            self._skip_depth += 1

    def handle_endtag(self, tag: str):  # type: ignore[override]
        if tag in self._SKIP and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data: str):  # type: ignore[override]
        if self._skip_depth == 0:
            self._chunks.append(data)

    def text(self) -> str:
        return re.sub(r"\s+", " ", " ".join(self._chunks)).strip()


def _html_to_text(html: str) -> str:
    p = _TextExtractor()
    try:
        p.feed(html)
    except Exception:
        # Malformed HTML — fall back to a crude tag strip
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()
    return p.text()


async def _fetch_url(url: str, timeout: float = 15.0) -> str:
    # Lazy import: --from-file path doesn't need aiohttp.
    import aiohttp

    headers = {"User-Agent": "Mozilla/5.0 MarketPulse/1.0"}
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as r:
            r.raise_for_status()
            return await r.text()


def _signals_from_raw(raw: dict) -> MarketSignals:
    sig = raw.get("signals", {}) or {}
    bt = sig.get("brand_tier", "unknown")
    cm = sig.get("category_maturity", "established")
    pp = sig.get("price_position", "parity")
    return MarketSignals(
        brand_tier=bt if bt in VALID_TIERS else "unknown",
        category_maturity=cm if cm in VALID_MATURITY else "established",
        price_position=pp if pp in VALID_PRICING else "parity",
    )


async def from_text(name: str, text: str, llm) -> SharedMemory:
    """Compress raw product material into SharedMemory via one LLM call."""
    text = (text or "").strip()
    if not text:
        raise ValueError("uploader.from_text: empty input")
    if len(text) > MAX_INPUT_CHARS:
        text = text[:MAX_INPUT_CHARS]

    system = (
        "You are a market research analyst. The user has provided source material "
        "for a product (marketing copy, brief, or webpage text). Extract a structured "
        "JSON summary suitable for a consumer-panel simulation. Be honest — do NOT "
        "flatter the product. The source is likely written by the product's own team, "
        "so discount marketing language and infer realistic market position."
    )

    user = (
        f"Product name: {name}\n\n"
        f"Source material:\n{text}\n\n"
        "Extract and return JSON with EXACTLY these keys:\n"
        "{\n"
        '  "product": {"description": str, "detailed_description": str, "price": str, '
        '"features": [str, ...], "category": str, "risks": [str, ...], "target_audience": str},\n'
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
        "- description: 1-2 sentence neutral summary (NOT a tagline).\n"
        "- detailed_description: 4-6 sentence overview covering value proposition, "
        "what makes it differentiated, and the concrete use cases it serves. Pull real "
        "details from the source — do NOT paraphrase into marketing platitudes.\n"
        "- features: 8-15 concrete product features — be specific (specs, capabilities, "
        "build details), not marketing adjectives.\n"
        "- risks: 3-6 honest limitations, trade-offs, or weaknesses. Include ones "
        "explicitly named in the source AND ones a skeptic would raise. Each risk "
        "must be specific to this product (e.g. 'battery drains in cold weather', "
        "not 'quality concerns').\n"
        "- target_audience: 1-2 sentences on who this product is for.\n"
        "- competitors: 2-3 real products this would be cross-shopped against. "
        "Infer them from the product category — the source likely won't name them.\n"
        "- findings: 3-5 entries reflecting plausible third-party reactions to the "
        "described features (mix of sentiments, not all positive).\n"
        "- market_context: 2-3 sentences on the market this product enters.\n"
        "- brand_tier: judge from the PRODUCT NAME's real-world recognition "
        "(Tesla/Apple/Samsung = incumbent; OnePlus/Rivian = challenger; "
        "names you don't recognize = unknown). Do NOT infer tier from the "
        "source's tone — self-praise is not evidence of incumbency, but a "
        "well-known brand stays well-known regardless of how the source reads."
    )

    raw: dict[str, Any] = await llm.generate_json(system, user)

    p_raw = raw.get("product", {}) or {}
    product = ProductInfo(
        name=name,
        description=p_raw.get("description", "") or "",
        price=p_raw.get("price", "") or "",
        features=list(p_raw.get("features", []) or [])[:15],
        category=p_raw.get("category", "") or "",
        detailed_description=(p_raw.get("detailed_description") or "").strip(),
        risks=[r for r in (p_raw.get("risks") or []) if r][:6],
        target_audience=(p_raw.get("target_audience") or "").strip(),
    )

    competitors = []
    for c in (raw.get("competitors", []) or [])[:3]:
        competitors.append(
            CompetitorInfo(
                name=c.get("name", "Unknown") or "Unknown",
                description=c.get("description", "") or "",
                price=c.get("price", "") or "",
                key_features=list(c.get("key_features", []) or [])[:6],
            )
        )

    findings = []
    for f in (raw.get("findings", []) or [])[:8]:
        sent = f.get("sentiment", "neutral")
        if sent not in {"positive", "neutral", "negative"}:
            sent = "neutral"
        findings.append(
            ResearchFinding(
                source=f.get("source", "user-upload") or "user-upload",
                summary=f.get("summary", "") or "",
                sentiment=sent,
                category=f.get("category", "general") or "general",
            )
        )

    return SharedMemory(
        product=product,
        competitors=competitors,
        research_findings=findings,
        market_context=raw.get("market_context", "") or "",
        signals=_signals_from_raw(raw),
    )


async def from_url(name: str, url: str, llm) -> SharedMemory:
    """Fetch a URL, strip HTML, then run from_text on the extracted text."""
    html = await _fetch_url(url)
    text = _html_to_text(html)
    if not text:
        raise ValueError(f"uploader.from_url: no text extracted from {url}")
    return await from_text(name, text, llm)
