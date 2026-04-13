"""Thin async wrapper over duckduckgo-search.

DDGS itself is sync; we run it in a thread so the asyncio loop isn't blocked
while multiple queries fire in parallel.
"""
import asyncio
from dataclasses import dataclass

from ddgs import DDGS


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str


def _search_sync(query: str, max_results: int) -> list[SearchResult]:
    with DDGS() as ddgs:
        raw = list(ddgs.text(query, max_results=max_results))
    return [
        SearchResult(
            title=r.get("title", ""),
            url=r.get("href", ""),
            snippet=r.get("body", ""),
        )
        for r in raw
    ]


async def search(query: str, max_results: int = 5) -> list[SearchResult]:
    try:
        return await asyncio.to_thread(_search_sync, query, max_results)
    except Exception as e:
        # Rate limits, network hiccups — degrade to empty so the coordinator
        # can still proceed with partial data.
        print(f"  [search error] {query!r}: {e}")
        return []
