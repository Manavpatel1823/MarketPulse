import asyncio

from rich.console import Console

from marketpulse.config import Settings
from marketpulse.llm.base import LLMBackend
from marketpulse.llm.ollama_backend import OllamaBackend
from marketpulse.llm.openrouter_backend import OpenRouterBackend
from marketpulse.memory.shared import SharedMemory, ProductInfo, CompetitorInfo
from marketpulse.simulation.engine import SimulationEngine

console = Console()


def build_llm(settings: Settings) -> LLMBackend:
    if settings.backend == "openrouter":
        if not settings.marketpulse_api:
            raise SystemExit("MARKETPULSE_API not set in .env — required for openrouter backend")
        console.print(f"[dim]Using OpenRouter backend ({settings.openrouter_model})[/dim]")
        return OpenRouterBackend(api_key=settings.marketpulse_api, model=settings.openrouter_model)
    # default: ollama
    console.print(f"[dim]Using Ollama backend ({settings.ollama_model})[/dim]")
    return OllamaBackend(model=settings.ollama_model, base_url=settings.ollama_base_url)


async def main():
    settings = Settings()

    llm = build_llm(settings)

    # Test case: Fairphone 5 — a genuinely obscure Dutch-made modular phone
    # (<1% US brand awareness) competing against iPhone + Samsung. Good test of
    # whether the panel has "big brand halo" bias vs. judging on features alone.
    shared = SharedMemory(
        product=ProductInfo(
            name="Fairphone 5",
            description=(
                "A modular, user-repairable Android smartphone from a small Dutch company "
                "focused on ethical sourcing and longevity. The entire phone can be "
                "disassembled with a single screwdriver; every major component (battery, "
                "screen, cameras, USB-C port) is user-replaceable. Backed by a 5-year warranty "
                "and 10 years of promised software support — vastly longer than mainstream rivals."
            ),
            price="$699",
            features=[
                "Qualcomm QCM6490 chip (mid-range, ~Snapdragon 778G performance)",
                "6.46\" 90Hz OLED display",
                "50MP main camera + 50MP ultrawide",
                "4,200 mAh USER-REPLACEABLE battery",
                "Fully modular — swap any part in under 10 minutes",
                "5-year hardware warranty",
                "10 years of Android security updates (until 2033)",
                "Fairtrade-certified gold, 70% recycled materials",
                "Carbon-neutral manufacturing and shipping",
                "No pre-installed bloatware; clean Android 13",
            ],
            category="Consumer Electronics / Smartphone",
        ),
        competitors=[
            CompetitorInfo(
                name="Apple iPhone 16",
                description=(
                    "Apple's flagship smartphone, dominant in the US premium segment. "
                    "Massive ecosystem, polished software, industry-leading camera system."
                ),
                price="$799",
                key_features=[
                    "A18 chip — top-tier performance",
                    "48MP Fusion camera with spatial video",
                    "6.1\" Super Retina XDR display, 120Hz ProMotion",
                    "iOS 18 with Apple Intelligence",
                    "Deep ecosystem integration (Mac, Watch, AirPods)",
                    "5+ years of iOS updates (typical)",
                    "Massive app ecosystem and accessory market",
                ],
            ),
            CompetitorInfo(
                name="Samsung Galaxy S24",
                description=(
                    "Samsung's mainstream flagship. Excellent hardware, strong Android "
                    "alternative, wide availability."
                ),
                price="$799",
                key_features=[
                    "Snapdragon 8 Gen 3 — flagship performance",
                    "50MP main + 10MP 3x telephoto + 12MP ultrawide",
                    "6.2\" Dynamic AMOLED 2X, 120Hz",
                    "7 years of OS + security updates",
                    "Samsung DeX, Galaxy AI features",
                    "Ubiquitous carrier availability in the US",
                ],
            ),
        ],
        market_context=(
            "The US smartphone market is dominated by Apple (~58%) and Samsung (~23%), with "
            "the remainder split among Google Pixel and small niche players. US consumers "
            "rarely consider non-US/non-Korean brands for phones. The 'right to repair' "
            "movement is growing but remains a niche concern. Sustainability-focused phones "
            "have <2% market share. Most buyers prioritize camera quality, ecosystem fit, "
            "and trade-in value — areas where small brands struggle. Fairphone has strong "
            "recognition in the Netherlands and Germany but near-zero awareness in the US."
        ),
    )

    engine = SimulationEngine(settings=settings, llm=llm)
    results = await engine.run(shared)


if __name__ == "__main__":
    asyncio.run(main())
