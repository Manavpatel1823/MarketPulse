import argparse
import asyncio
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from marketpulse.config import Settings
from marketpulse.llm.base import LLMBackend
from marketpulse.llm.ollama_backend import OllamaBackend
from marketpulse.llm.openrouter_backend import OpenRouterBackend
from marketpulse.memory.shared import ProductInfo, SharedMemory
from marketpulse.research.coordinator import research_product
from marketpulse.research.uploader import from_text as upload_from_text
from marketpulse.research.uploader import from_url as upload_from_url
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


def _build_stub(name: str) -> SharedMemory:
    """Bare-bones SharedMemory when --no-research is used."""
    return SharedMemory(
        product=ProductInfo(
            name=name,
            description=f"(no research — running with just the name '{name}')",
            price="unknown",
            features=[],
            category="unknown",
        )
    )


def _print_research_summary(shared: SharedMemory) -> None:
    console.print("\n[bold cyan]═══ RESEARCH FINDINGS ═══[/bold cyan]")
    p = shared.product
    console.print(f"[bold]{p.name}[/bold] — {p.category} — {p.price}")
    if p.description:
        console.print(f"[dim]{p.description}[/dim]")
    if p.features:
        console.print(f"[dim]Features:[/dim] {', '.join(p.features[:5])}")

    if shared.competitors:
        console.print("\n[bold]Competitors:[/bold]")
        for c in shared.competitors:
            console.print(f"  - {c.name} ({c.price})")

    if shared.signals:
        s = shared.signals
        console.print(
            f"\n[bold]Market signals:[/bold] "
            f"brand_tier=[magenta]{s.brand_tier}[/magenta], "
            f"maturity={s.category_maturity}, "
            f"pricing={s.price_position}"
        )
    if shared.research_findings:
        console.print(f"[dim]{len(shared.research_findings)} findings extracted[/dim]")


async def main():
    ap = argparse.ArgumentParser(description="MarketPulse — AI consumer panel simulation")
    ap.add_argument("product", help="Product name to research (e.g. 'Fairphone 5')")
    src = ap.add_mutually_exclusive_group()
    src.add_argument(
        "--no-research",
        action="store_true",
        help="Skip web research; use a minimal stub (for offline/deterministic testing)",
    )
    src.add_argument(
        "--from-url",
        metavar="URL",
        help="Skip web search; fetch this URL, compress its text into ProductInfo via LLM",
    )
    src.add_argument(
        "--from-file",
        metavar="PATH",
        help="Skip web search; read this file's text and compress into ProductInfo via LLM",
    )
    args = ap.parse_args()

    settings = Settings()
    llm = build_llm(settings)

    if args.no_research:
        console.print("[dim]Skipping web research — using stub product.[/dim]")
        shared = _build_stub(args.product)
    elif args.from_url:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            progress.add_task(f"Fetching {args.from_url} and extracting product info...", total=None)
            shared = await upload_from_url(args.product, args.from_url, llm)
        _print_research_summary(shared)
    elif args.from_file:
        path = Path(args.from_file)
        if not path.is_file():
            raise SystemExit(f"--from-file: {path} not found or not a file")
        text = path.read_text(encoding="utf-8", errors="replace")
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            progress.add_task(f"Compressing {path.name} into ProductInfo (1 LLM call)...", total=None)
            shared = await upload_from_text(args.product, text, llm)
        _print_research_summary(shared)
    else:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            progress.add_task(f"Researching '{args.product}' (2 searches + 1 LLM parse)...", total=None)
            shared = await research_product(args.product, llm)
        _print_research_summary(shared)

    engine = SimulationEngine(settings=settings, llm=llm)
    await engine.run(shared)


if __name__ == "__main__":
    asyncio.run(main())
