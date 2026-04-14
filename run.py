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
from marketpulse.research.coordinator import (
    augment_with_category_competitors,
    research_product,
)
from marketpulse.research.gate import is_research_worthwhile
from marketpulse.research.uploader import from_text as upload_from_text
from marketpulse.research.uploader import from_url as upload_from_url
from marketpulse.simulation.engine import SimulationEngine
from marketpulse.storage import db as storage
from marketpulse.storage import queries as db_queries
from marketpulse.storage.cli import (
    render_comparison,
    render_run_detail,
    render_run_list,
)

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


def _confirm_proceed(shared: SharedMemory, auto_yes: bool) -> bool:
    """Show findings and ask user to confirm before the (expensive) sim runs.

    Cheap insurance: even when the gate passes, the parsed product/competitors
    might still look wrong to a human eye. Better to bail here than after
    25 agents have debated nonsense.
    """
    if auto_yes:
        return True
    try:
        ans = input("\nProceed with simulation using these findings? [Y/n]: ").strip().lower()
    except EOFError:
        # Non-interactive (piped/CI) and no --yes — be conservative, don't run.
        console.print("[yellow]No TTY and --yes not set; aborting.[/yellow]")
        return False
    if ans in ("", "y", "yes"):
        return True
    console.print(
        "\n[yellow]Aborted.[/yellow] To re-run with different inputs:\n"
        f"  [cyan]python3 run.py \"{shared.product.name}\" --from-file brief.txt[/cyan]\n"
        f"  [cyan]python3 run.py \"{shared.product.name}\" --from-url https://...[/cyan]"
    )
    return False


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
    ap.add_argument(
        "product",
        nargs="?",
        help="Product name to research (e.g. 'Fairphone 5'). "
             "Omit when using --list / --show / --compare.",
    )
    # DB-backed inspection commands. Mutually exclusive with running a sim.
    ap.add_argument("--list", dest="list_runs", action="store_true",
                    help="List recent runs from the database and exit.")
    ap.add_argument("--show", type=int, metavar="RUN_ID",
                    help="Show full detail for one run from the database and exit.")
    ap.add_argument("--compare", type=int, nargs="+", metavar="RUN_ID",
                    help="Compare 2+ runs side-by-side and exit.")
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
    ap.add_argument(
        "--force-research",
        action="store_true",
        help="Skip the 'is research worthwhile?' gate and run web research no matter what",
    )
    ap.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Auto-confirm the research findings prompt (skip Y/n, useful for scripting)",
    )
    args = ap.parse_args()
    settings = Settings()

    # ── DB inspection mode (no sim, no LLM) ────────────────────────────
    if args.list_runs or args.show is not None or args.compare:
        try:
            pool = await storage.get_pool(settings.database_url)
        except Exception as e:
            raise SystemExit(f"DB connection failed: {type(e).__name__}: {e}")
        try:
            if args.list_runs:
                rows = await db_queries.list_runs(pool)
                render_run_list(rows)
            elif args.show is not None:
                run = await db_queries.get_run(pool, args.show)
                if not run:
                    raise SystemExit(f"No run with id={args.show}")
                render_run_detail(run)
            elif args.compare:
                if len(args.compare) < 2:
                    raise SystemExit("--compare needs at least 2 run IDs")
                runs = await db_queries.compare_runs(pool, args.compare)
                render_comparison(runs)
        finally:
            await storage.close_pool()
        return

    if not args.product:
        raise SystemExit("error: 'product' is required unless using --list/--show/--compare")

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
            progress.add_task(f"Finding {shared.product.category or 'category'} competitors on web...", total=None)
            shared = await augment_with_category_competitors(shared, llm)
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
            progress.add_task(f"Finding {shared.product.category or 'category'} competitors on web...", total=None)
            shared = await augment_with_category_competitors(shared, llm)
        _print_research_summary(shared)
    else:
        # Phase 2c #2: gate the full pipeline behind a "worth it?" pre-check.
        # Skipped if --force-research, since the user has explicitly opted in.
        if not args.force_research:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True,
            ) as progress:
                progress.add_task(f"Pre-checking web coverage for '{args.product}'...", total=None)
                gate = await is_research_worthwhile(args.product, llm)
            if not gate.worth_it:
                console.print(
                    f"\n[bold yellow]No useful web coverage for "
                    f"\"{args.product}\".[/bold yellow]"
                )
                console.print(f"[dim]Reason: {gate.reason}[/dim]")
                console.print(
                    "\nThis product looks unreleased, internal, or otherwise "
                    "off-the-grid. Pick one of:\n"
                )
                console.print(
                    f"  [cyan]python3 run.py \"{args.product}\" --from-file brief.txt[/cyan]\n"
                    f"  [cyan]python3 run.py \"{args.product}\" --from-url https://...[/cyan]\n"
                    f"  [cyan]python3 run.py \"{args.product}\" --no-research[/cyan]   "
                    f"[dim](run on stub anyway)[/dim]\n"
                    f"  [cyan]python3 run.py \"{args.product}\" --force-research[/cyan] "
                    f"[dim](skip this gate, search anyway)[/dim]\n"
                )
                raise SystemExit(0)
            console.print(f"[dim][gate] {gate.reason}[/dim]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            progress.add_task(f"Researching '{args.product}' (2 searches + 1 LLM parse)...", total=None)
            shared = await research_product(args.product, llm)
        _print_research_summary(shared)

    # Confirmation gate (skipped for --no-research since there's nothing
    # to confirm — the user already opted into a stub).
    if not args.no_research:
        if not _confirm_proceed(shared, auto_yes=args.yes):
            raise SystemExit(0)

    engine = SimulationEngine(settings=settings, llm=llm)
    try:
        await engine.run(shared)
    finally:
        await storage.close_pool()


if __name__ == "__main__":
    asyncio.run(main())
