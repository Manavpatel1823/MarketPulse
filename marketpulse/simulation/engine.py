import json
import re
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from marketpulse.agents.agent import Agent
from marketpulse.agents.persona import generate_personas, enrich_personas
from marketpulse.agents.pool import AgentPool
from marketpulse.config import Settings
from marketpulse.llm.base import LLMBackend
from marketpulse.memory.shared import SharedMemory
from marketpulse.reporting.analyzer import generate_report
from marketpulse.simulation.interaction import adversarial_pairing
from marketpulse.simulation.sentiment import apply_persuasion

# record=True lets us export everything printed as plain text / HTML at end of run.
# Zero runtime cost, zero LLM token cost.
console = Console(record=True)


class SimulationEngine:
    def __init__(self, settings: Settings, llm: LLMBackend):
        self.settings = settings
        self.llm = llm
        self.pool = AgentPool(batch_size=settings.batch_size)
        self.agents: list[Agent] = []
        self.previous_pairs: set[tuple[str, str]] = set()

    async def initialize_agents(self) -> None:
        """Generate and enrich agent personas."""
        console.print("\n[bold cyan]═══ GENERATING AGENT PERSONAS ═══[/bold cyan]")
        personas = generate_personas(
            self.settings.agent_count,
            use_hardcoded=self.settings.use_hardcoded_personas,
        )

        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Enriching personas with LLM...", total=None)
            personas = await enrich_personas(personas, self.llm)
            progress.update(task, completed=True)

        self.agents = [Agent(p) for p in personas]

        # Show each agent's personality
        for a in self.agents:
            p = a.persona
            console.print(Panel(
                f"[bold]{p.name}[/bold] (age {p.age}, {p.income_bracket} income)\n"
                f"[dim]Archetype:[/dim] [magenta]{p.archetype}[/magenta]\n"
                f"[dim]Tech Savvy:[/dim] {p.tech_savviness:.1f} | "
                f"[dim]Brand Loyalty:[/dim] {p.brand_loyalty:.1f} | "
                f"[dim]Price Sensitive:[/dim] {p.price_sensitivity:.1f}\n"
                f"[dim]Initial Bias:[/dim] {p.initial_bias:+.2f}\n\n"
                f"[italic]{p.personality_blurb}[/italic]",
                title=f"[cyan]{p.id}[/cyan]",
                border_style="cyan",
            ))

        console.print(f"\n[green]Created {len(self.agents)} agents[/green]")

    async def opinion_phase(self, shared: SharedMemory) -> None:
        """Each agent forms their initial opinion."""
        console.print("\n[bold cyan]═══ OPINION PHASE ═══[/bold cyan]")
        console.print("[dim]Each agent reads the product info and forms their initial opinion...[/dim]\n")

        tasks = [
            lambda a=agent: a.form_opinion(shared, self.llm)
            for agent in self.agents
        ]

        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
            BarColumn(), TextColumn("{task.completed}/{task.total}"),
            console=console,
        ) as progress:
            ptask = progress.add_task("Forming opinions", total=len(tasks))
            results = []
            for i in range(0, len(tasks), self.settings.batch_size):
                batch = tasks[i : i + self.settings.batch_size]
                batch_results = await self.pool.execute_batch(batch)
                results.extend(batch_results)
                progress.update(ptask, completed=len(results))

        # Show each agent's opinion in detail
        for a in self.agents:
            op = a.memory.latest_opinion
            if not op:
                continue

            score = op.sentiment
            if score > 3:
                color = "green"
            elif score < -3:
                color = "red"
            else:
                color = "yellow"

            concerns_str = "\n".join(f"  [red]- {c}[/red]" for c in op.concerns) if op.concerns else "  None"
            positives_str = "\n".join(f"  [green]+ {p}[/green]" for p in op.positives) if op.positives else "  None"

            console.print(Panel(
                f"[bold {color}]Sentiment: {score:+.1f}/10[/bold {color}]\n\n"
                f"[bold]Reasoning:[/bold]\n  {op.reasoning}\n\n"
                f"[bold]Concerns:[/bold]\n{concerns_str}\n\n"
                f"[bold]Positives:[/bold]\n{positives_str}",
                title=f"[cyan]{a.persona.name}[/cyan] ({a.persona.archetype})",
                border_style=color,
            ))

        self._print_sentiment_table("Initial Sentiment Summary")

    async def debate_round(self, shared: SharedMemory, round_num: int) -> None:
        """Run one round of debates with full conversation display."""
        pairs = adversarial_pairing(self.agents, self.previous_pairs)
        console.print(
            f"\n[bold cyan]═══ DEBATE ROUND {round_num + 1} ═══[/bold cyan]"
        )
        console.print(f"[dim]{len(pairs)} pairs debating...[/dim]\n")

        # Track pairs
        for a, b in pairs:
            self.previous_pairs.add(tuple(sorted((a.persona.id, b.persona.id))))

        conversions = 0

        for pair_idx, (a, b) in enumerate(pairs):
            console.print(f"[bold]── Debate {pair_idx + 1}: "
                          f"{a.persona.name} ({a.persona.archetype}) vs "
                          f"{b.persona.name} ({b.persona.archetype}) ──[/bold]")

            # Get their current positions
            a_opinion = a.memory.latest_opinion
            a_argument = a_opinion.reasoning if a_opinion else "I have no strong opinion yet."
            b_opinion = b.memory.latest_opinion
            b_argument = b_opinion.reasoning if b_opinion else "I have no strong opinion yet."

            # Show opening positions
            console.print(f"\n  [cyan]{a.persona.name}[/cyan] (sentiment {a.sentiment:+.1f}):")
            console.print(f"  [italic]\"{a_argument}\"[/italic]")
            console.print(f"\n  [magenta]{b.persona.name}[/magenta] (sentiment {b.sentiment:+.1f}):")
            console.print(f"  [italic]\"{b_argument}\"[/italic]")

            # Both debate each other's arguments
            a_result = await a.debate(b.persona.id, b_argument, shared, self.llm, round_num)
            b_result = await b.debate(a.persona.id, a_argument, shared, self.llm, round_num)

            # Show responses
            console.print(f"\n  [cyan]{a.persona.name}[/cyan] responds ({a_result['stance']}):")
            console.print(f"  [italic]\"{a_result['counter_argument']}\"[/italic]")
            console.print(f"  [dim]Sentiment shift: {a_result['sentiment_shift']:+.0f} | "
                          f"Convinced: {'Yes' if a_result['convinced'] else 'No'}[/dim]")

            console.print(f"\n  [magenta]{b.persona.name}[/magenta] responds ({b_result['stance']}):")
            console.print(f"  [italic]\"{b_result['counter_argument']}\"[/italic]")
            console.print(f"  [dim]Sentiment shift: {b_result['sentiment_shift']:+.0f} | "
                          f"Convinced: {'Yes' if b_result['convinced'] else 'No'}[/dim]")

            # Apply persuasion mechanics
            a_old = a.sentiment
            b_old = b.sentiment
            a_converted = apply_persuasion(a, a_result, b.sentiment, round_num, self.settings.persuasion_threshold)
            b_converted = apply_persuasion(b, b_result, a.sentiment, round_num, self.settings.persuasion_threshold)

            if a_converted:
                conversions += 1
                console.print(f"\n  [bold yellow]*** {a.persona.name} CONVERTED! "
                              f"{a_old:+.1f} → {a.sentiment:+.1f} ***[/bold yellow]")
            if b_converted:
                conversions += 1
                console.print(f"\n  [bold yellow]*** {b.persona.name} CONVERTED! "
                              f"{b_old:+.1f} → {b.sentiment:+.1f} ***[/bold yellow]")

            # Show post-debate sentiment
            console.print(f"\n  [dim]After debate: {a.persona.name} {a_old:+.1f}→{a.sentiment:+.1f} | "
                          f"{b.persona.name} {b_old:+.1f}→{b.sentiment:+.1f}[/dim]")
            console.print()

        console.print(f"[yellow]Round {round_num + 1} conversions: {conversions}[/yellow]")
        self._print_sentiment_table(f"After Round {round_num + 1}")

    async def run(self, shared: SharedMemory) -> dict:
        """Run the full simulation."""
        console.print("[bold magenta]╔══════════════════════════════════════╗[/bold magenta]")
        console.print("[bold magenta]║      MarketPulse Simulation          ║[/bold magenta]")
        console.print("[bold magenta]╚══════════════════════════════════════╝[/bold magenta]")
        console.print(f"Product: [bold]{shared.product.name}[/bold]")
        console.print(f"Agents: {self.settings.agent_count} | Rounds: {self.settings.rounds}")
        console.print(f"Backend: {self.settings.backend} ({self.settings.ollama_model})")

        # Phase 1: Initialize agents
        await self.initialize_agents()

        # Phase 2: Form initial opinions
        await self.opinion_phase(shared)

        # Phase 3: Debate rounds
        for round_num in range(self.settings.rounds):
            await self.debate_round(shared, round_num)

        # Collect results
        results = self._collect_results(shared)
        self._print_final_summary(results)

        # Phase 4: Generate marketing report
        console.print("\n[bold cyan]═══ GENERATING MARKETING REPORT ═══[/bold cyan]")
        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            ptask = progress.add_task("Reasoning agent analyzing all data...", total=None)
            report = await generate_report(results, self.llm)
            progress.update(ptask, completed=True)

        console.print("\n[bold magenta]╔══════════════════════════════════════════╗[/bold magenta]")
        console.print("[bold magenta]║   MARKETING INTELLIGENCE REPORT          ║[/bold magenta]")
        console.print("[bold magenta]╚══════════════════════════════════════════╝[/bold magenta]\n")
        console.print(report)
        results["report"] = report

        # Save run outputs to disk (debate transcript, report, structured summary)
        self._save_run_outputs(shared, results, report)

        return results

    def _save_run_outputs(self, shared: SharedMemory, results: dict, report: str) -> None:
        """Persist the run to a timestamped folder under runs/.

        Creates three files:
          - debate.txt  : full terminal transcript (all rounds, all debates)
          - report.md   : the final marketing report as markdown
          - summary.json: structured results for later analysis / comparison
        """
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        product_slug = re.sub(r"[^a-zA-Z0-9]+", "-", shared.product.name).strip("-")
        run_dir = Path("runs") / f"{timestamp}_{product_slug}"
        run_dir.mkdir(parents=True, exist_ok=True)

        # 1. Full transcript (plain text, no ANSI color codes)
        (run_dir / "debate.txt").write_text(console.export_text(), encoding="utf-8")

        # 2. Final marketing report as markdown
        report_md = f"# Marketing Report — {shared.product.name}\n\n_Generated {timestamp}_\n\n{report}\n"
        (run_dir / "report.md").write_text(report_md, encoding="utf-8")

        # 3. Structured results as JSON
        (run_dir / "summary.json").write_text(
            json.dumps(results, indent=2, default=str), encoding="utf-8"
        )

        console.print(f"\n[bold green]✓ Run saved to:[/bold green] {run_dir}/")
        console.print(f"  [dim]- debate.txt   (full transcript)[/dim]")
        console.print(f"  [dim]- report.md    (marketing report)[/dim]")
        console.print(f"  [dim]- summary.json (structured data)[/dim]")

    def _collect_results(self, shared: SharedMemory) -> dict:
        sentiments = [a.sentiment for a in self.agents]
        avg = sum(sentiments) / len(sentiments) if sentiments else 0

        all_concerns = []
        all_positives = []
        for a in self.agents:
            if a.memory.latest_opinion:
                all_concerns.extend(a.memory.latest_opinion.concerns)
                all_positives.extend(a.memory.latest_opinion.positives)

        concern_freq = {}
        for c in all_concerns:
            concern_freq[c] = concern_freq.get(c, 0) + 1
        positive_freq = {}
        for p in all_positives:
            positive_freq[p] = positive_freq.get(p, 0) + 1

        total_conversions = sum(
            len(a.memory.conversion_events) for a in self.agents
        )

        archetype_sentiments = {}
        for a in self.agents:
            arch = a.persona.archetype
            if arch not in archetype_sentiments:
                archetype_sentiments[arch] = []
            archetype_sentiments[arch].append(a.sentiment)

        return {
            "product": shared.product.name,
            "agent_count": len(self.agents),
            "rounds": self.settings.rounds,
            "average_sentiment": round(avg, 2),
            "sentiment_range": (round(min(sentiments), 2), round(max(sentiments), 2)),
            "total_conversions": total_conversions,
            "top_concerns": sorted(concern_freq.items(), key=lambda x: -x[1])[:5],
            "top_positives": sorted(positive_freq.items(), key=lambda x: -x[1])[:5],
            "archetype_sentiments": {
                k: round(sum(v) / len(v), 2)
                for k, v in archetype_sentiments.items()
            },
            "agents": [
                {
                    "id": a.persona.id,
                    "name": a.persona.name,
                    "archetype": a.persona.archetype,
                    "initial_sentiment": a.memory.sentiment_history[0] if a.memory.sentiment_history else 0,
                    "final_sentiment": round(a.sentiment, 2),
                    "conversions": len(a.memory.conversion_events),
                }
                for a in self.agents
            ],
        }

    def _print_sentiment_table(self, title: str) -> None:
        table = Table(title=title, show_lines=False)
        table.add_column("Agent", style="cyan")
        table.add_column("Archetype", style="magenta")
        table.add_column("Sentiment", justify="right")

        for a in sorted(self.agents, key=lambda x: x.sentiment, reverse=True):
            score = a.sentiment
            if score > 3:
                style = "green"
            elif score < -3:
                style = "red"
            else:
                style = "yellow"
            bar = "█" * int(abs(score)) + "░" * (10 - int(abs(score)))
            sign = "+" if score >= 0 else ""
            table.add_row(
                f"{a.persona.name} ({a.persona.id})",
                a.persona.archetype,
                f"[{style}]{sign}{score:.1f} {bar}[/{style}]",
            )

        console.print(table)

    def _print_final_summary(self, results: dict) -> None:
        console.print("\n[bold magenta]═══ SIMULATION COMPLETE ═══[/bold magenta]")
        console.print(f"Average Sentiment: [bold]{results['average_sentiment']}/10[/bold]")
        console.print(
            f"Range: {results['sentiment_range'][0]} to {results['sentiment_range'][1]}"
        )
        console.print(f"Total Conversions: {results['total_conversions']}")

        if results["top_concerns"]:
            console.print("\n[bold red]Top Concerns:[/bold red]")
            for concern, count in results["top_concerns"]:
                console.print(f"  - {concern} (x{count})")

        if results["top_positives"]:
            console.print("\n[bold green]Top Positives:[/bold green]")
            for positive, count in results["top_positives"]:
                console.print(f"  - {positive} (x{count})")

        console.print("\n[bold]Sentiment by Archetype:[/bold]")
        for arch, avg in sorted(results["archetype_sentiments"].items(), key=lambda x: -x[1]):
            console.print(f"  {arch}: {avg:+.1f}")
