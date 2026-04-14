"""'Is web research worth it?' gate — Phase 2c #2.

Fires ONE quick DDG query (3 results) before committing to the full 2-query
+ 1 LLM-parse pipeline. Decides whether the snippets contain real
third-party signal (reviews, comparisons, discussion) or just the product's
own marketing pages.

Why: For freshly-launched / internal products, DDG returns founder-friendly
copy, the parser dutifully extracts flattering features, and the panel
debates fiction. Better to stop early and tell the user to upload a brief.

Cost: 1 DDG call + at most 1 small JSON LLM call. Saves the downstream
2 DDG + 1 LLM parse + entire simulation when there's no useful coverage.
"""
import asyncio
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from marketpulse.research import searcher


@dataclass
class GateDecision:
    worth_it: bool
    reason: str
    snippet_count: int


# Domains that are "the product's own voice" — finding only these means
# we have marketing, not third-party signal.
_OWN_VOICE_HINTS = (
    "store", "shop", "buy", ".io", "official",
)
# Domains that strongly indicate real third-party discussion exist.
_THIRD_PARTY_HINTS = (
    "reddit.com", "ycombinator.com", "techcrunch.com", "theverge.com",
    "arstechnica.com", "wired.com", "engadget.com", "tomshardware.com",
    "rtings.com", "wirecutter.com", "consumerreports.org",
    "trustpilot.com", "g2.com", "capterra.com",
    "youtube.com", "medium.com", "substack.com",
    "wikipedia.org",
)


def _domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return ""


def _heuristic(snippets: list, product_name: str) -> tuple[bool | None, str]:
    """Cheap rules. Returns (decision, reason) or (None, '') if inconclusive.

    `decision` is True/False if the heuristic is confident, None to defer
    to the LLM check.
    """
    if not snippets:
        return False, "DDG returned 0 results — no public coverage exists."

    domains = [_domain(s.url) for s in snippets]
    name_lower = product_name.lower()
    name_slug = name_lower.replace(" ", "")

    # Strong third-party signal: domain is a known third-party site AND the
    # snippet/title actually mentions the product name. Without the name
    # check, random Yahoo Finance / YouTube hits passed the gate even when
    # they had nothing to do with the product (e.g. searching a ticker-like
    # made-up name returned unrelated finance pages).
    def _mentions_product(s) -> bool:
        text = f"{s.title or ''} {s.snippet or ''}".lower()
        return name_lower in text or (len(name_slug) > 3 and name_slug in text)

    third_party_hits = sum(
        1 for s, d in zip(snippets, domains)
        if any(h in d for h in _THIRD_PARTY_HINTS) and _mentions_product(s)
    )
    if third_party_hits >= 1:
        return True, f"Found {third_party_hits} third-party source(s) that name the product."

    # Every result domain contains the product name → likely all the
    # product's own marketing properties (productname.com, shop.productname...)
    own_voice_hits = sum(
        1 for d in domains
        if name_slug and name_slug in d.replace("-", "").replace(".", "")
    )
    if own_voice_hits == len(snippets):
        return False, "All results are from the product's own domains — only marketing copy available."

    # If no snippet mentions the product name at all, DDG returned unrelated
    # results (often happens for short / ticker-like names). Don't even bother
    # with the LLM check.
    any_mention = any(_mentions_product(s) for s in snippets)
    if not any_mention:
        return False, "No search result mentions the product name — DDG returned unrelated content."

    return None, ""


async def is_research_worthwhile(name: str, llm) -> GateDecision:
    """Decide whether to run the full research pipeline for this product."""
    try:
        snippets = await asyncio.wait_for(
            searcher.search(name, max_results=3),
            timeout=10.0,
        )
    except asyncio.TimeoutError:
        # If pre-check itself times out, don't block — let the main pipeline
        # try (it has its own timeouts and stub fallback).
        return GateDecision(
            worth_it=True,
            reason="Pre-check timed out; deferring to main research pipeline.",
            snippet_count=0,
        )

    decision, reason = _heuristic(snippets, name)
    if decision is not None:
        return GateDecision(decision, reason, len(snippets))

    # Heuristic inconclusive — ask the LLM to judge the snippets.
    # One small JSON call. Schema deliberately tiny.
    snippet_block = "\n".join(
        f"[{i}] {s.title} ({_domain(s.url)}) — {(s.snippet or '')[:160]}"
        for i, s in enumerate(snippets, 1)
    )
    system = (
        "You judge whether web search results contain enough third-party signal "
        "(real reviews, comparisons, user discussion) to support market research, "
        "or whether they are just the product's own marketing copy."
    )
    user = (
        f"Product: {name}\n\n"
        f"Top {len(snippets)} search results:\n{snippet_block}\n\n"
        "Return JSON: "
        '{"third_party_signal": true|false, "reason": "one short sentence"}\n\n'
        "true = at least one independent review, comparison, or discussion. "
        "false = only marketing pages, store listings, or no real coverage."
    )
    try:
        raw: dict[str, Any] = await llm.generate_json(system, user)
        worth_it = bool(raw.get("third_party_signal", False))
        reason = raw.get("reason", "(no reason given)") or "(no reason given)"
    except Exception as e:
        # If the LLM check fails, default to TRUE — the main pipeline has
        # its own fallbacks; better to try than block.
        return GateDecision(True, f"LLM gate-check failed ({e}); deferring.", len(snippets))

    return GateDecision(worth_it, reason, len(snippets))
