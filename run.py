import asyncio

from rich.console import Console

from marketpulse.config import Settings
from marketpulse.llm.ollama_backend import OllamaBackend
from marketpulse.memory.shared import SharedMemory, ProductInfo
from marketpulse.simulation.engine import SimulationEngine

console = Console()


async def main():
    settings = Settings()

    # Verify Ollama is reachable
    llm = OllamaBackend(model=settings.ollama_model, base_url=settings.ollama_base_url)

    # Example product for testing (no competitors — web search will find them in Phase 2)
    shared = SharedMemory(
        product=ProductInfo(
            name="AirPods Pro 3",
            description="Apple's next-gen wireless earbuds with advanced noise cancellation, spatial audio, and health monitoring features",
            price="$249",
            features=[
                "Active Noise Cancellation 3.0",
                "Spatial Audio with head tracking",
                "Heart rate monitoring",
                "Hearing aid mode",
                "USB-C charging",
                "6 hours battery life",
            ],
            category="Consumer Electronics / Audio",
        ),
        market_context=(
            "The TWS earbuds market is highly competitive. "
            "Health features are an emerging differentiator. Price sensitivity is increasing "
            "as consumers face economic uncertainty in 2026."
        ),
    )

    engine = SimulationEngine(settings=settings, llm=llm)
    results = await engine.run(shared)


if __name__ == "__main__":
    asyncio.run(main())
