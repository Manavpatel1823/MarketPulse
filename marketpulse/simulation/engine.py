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
from marketpulse.storage import db as storage

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
        # DB state — populated in run() if persist_db=True. None means "no DB".
        self._db_pool = None
        self._run_id: int | None = None
        self._agent_db_ids: dict[str, int] = {}

    async def initialize_agents(self, shared: SharedMemory | None = None) -> None:
        """Generate and enrich agent personas. Panel ratio reflects shared.signals."""
        console.print("\n[bold cyan]═══ GENERATING AGENT PERSONAS ═══[/bold cyan]")
        skew = shared.signals if shared is not None else None
        personas = generate_personas(
            self.settings.agent_count,
            use_hardcoded=self.settings.use_hardcoded_personas,
            skew=skew,
        )

        # Surface which panel ratio was chosen so the user can sanity-check it.
        from collections import Counter
        from marketpulse.agents.persona import ARCHETYPE_TIERS
        tier_of = {a: t for t, archs in ARCHETYPE_TIERS.items() for a in archs}
        tier_counts = Counter(tier_of.get(p.archetype, "?") for p in personas)
        console.print(
            f"[dim]Panel (4:3:3 fixed): "
            f"{tier_counts.get('positive', 0)} pos / "
            f"{tier_counts.get('neutral', 0)} neu / "
            f"{tier_counts.get('negative', 0)} neg[/dim]"
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
        interaction_rows: list[tuple] = []

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

            # Capture the pair for persistence. Round is 1-indexed in the DB so it
            # aligns with the opinions table (round 0 = initial, 1..N = post-debate).
            a_db = self._agent_db_ids.get(a.persona.id)
            b_db = self._agent_db_ids.get(b.persona.id)
            if a_db is not None and b_db is not None:
                interaction_rows.append((
                    round_num + 1, a_db, b_db,
                    a_result.get("stance", ""), b_result.get("stance", ""),
                    float(a_result.get("sentiment_shift", 0.0)),
                    float(b_result.get("sentiment_shift", 0.0)),
                    bool(a_result.get("convinced", False)),
                    bool(b_result.get("convinced", False)),
                    a_result.get("counter_argument", ""),
                    b_result.get("counter_argument", ""),
                ))

        console.print(f"[yellow]Round {round_num + 1} conversions: {conversions}[/yellow]")
        self._print_sentiment_table(f"After Round {round_num + 1}")

        if self._db_pool and self._run_id and interaction_rows:
            await storage.insert_interactions_batch(
                self._db_pool, self._run_id, interaction_rows,
            )

    async def run(self, shared: SharedMemory) -> dict:
        """Run the full simulation."""
        console.print("[bold magenta]╔══════════════════════════════════════╗[/bold magenta]")
        console.print("[bold magenta]║      MarketPulse Simulation          ║[/bold magenta]")
        console.print("[bold magenta]╚══════════════════════════════════════╝[/bold magenta]")
        console.print(f"Product: [bold]{shared.product.name}[/bold]")
        console.print(f"Agents: {self.settings.agent_count} | Rounds: {self.settings.rounds}")
        # Show the model string for whichever backend is actually active
        active_model = {
            "openrouter": self.settings.openrouter_model,
            "ollama": self.settings.ollama_model,
            "gemini": getattr(self.settings, "gemini_model", "gemini-2.5-flash"),
        }.get(self.settings.backend, self.settings.ollama_model)
        console.print(f"Backend: {self.settings.backend} ({active_model})")

        # Pre-compute the folder name now so DB and disk agree on the slug.
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        product_slug = re.sub(r"[^a-zA-Z0-9]+", "-", shared.product.name).strip("-")
        folder_name = f"{timestamp}_{product_slug}"

        # Open DB + create run row up-front so even partial runs are recorded.
        if self.settings.persist_db:
            try:
                self._db_pool = await storage.get_pool(self.settings.database_url)
                self._run_id = await storage.insert_run(
                    self._db_pool,
                    product_name=shared.product.name,
                    folder_name=folder_name,
                    agent_count=self.settings.agent_count,
                    rounds=self.settings.rounds,
                    backend=self.settings.backend,
                    model=active_model,
                    settings_dict=self.settings.model_dump(mode="json", exclude={"marketpulse_api", "gemini_api_key", "database_url"}),
                )
                await storage.insert_shared_memory(self._db_pool, self._run_id, shared)
                console.print(f"[dim][db] Persisting as run #{self._run_id}[/dim]")
            except Exception as e:
                console.print(f"[yellow][db] Disabled — {type(e).__name__}: {e}[/yellow]")
                self._db_pool = None
                self._run_id = None

        try:
            # Phase 1: Initialize agents
            await self.initialize_agents(shared)
            if self._db_pool and self._run_id:
                self._agent_db_ids = await storage.insert_agents(
                    self._db_pool, self._run_id, self.agents
                )

            # Phase 2: Form initial opinions
            await self.opinion_phase(shared)
            await self._persist_round_opinions(round_num=0)

            # Phase 3: Debate rounds
            for round_num in range(self.settings.rounds):
                await self.debate_round(shared, round_num)
                await self._persist_round_opinions(round_num=round_num + 1)

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
                report = await generate_report(results, shared, self.llm)
                progress.update(ptask, completed=True)

            console.print("\n[bold magenta]╔══════════════════════════════════════════╗[/bold magenta]")
            console.print("[bold magenta]║   MARKETING INTELLIGENCE REPORT          ║[/bold magenta]")
            console.print("[bold magenta]╚══════════════════════════════════════════╝[/bold magenta]\n")
            console.print(report)
            results["report"] = report

            # Save run outputs to disk (debate transcript, report, structured summary)
            self._save_run_outputs(shared, results, report, folder_name)

            # Finalize DB row last — only "complete" if everything succeeded.
            await self._finalize_db(results)

            return results
        finally:
            # Connection pool stays alive for the process; nothing to close
            # per-run. close_pool() is the program-exit hook.
            pass

    async def _persist_round_opinions(self, round_num: int) -> None:
        if not (self._db_pool and self._run_id):
            return
        rows = []
        for a in self.agents:
            db_id = self._agent_db_ids.get(a.persona.id)
            if db_id is None:
                continue
            rows.append((db_id, round_num, a.memory.latest_opinion))
        await storage.insert_opinions_batch(self._db_pool, self._run_id, rows)

    async def _finalize_db(self, results: dict) -> None:
        if not (self._db_pool and self._run_id):
            return
        agent_finals: dict[int, tuple[float, int, float]] = {}
        for a in self.agents:
            db_id = self._agent_db_ids.get(a.persona.id)
            if db_id is None:
                continue
            init = a.memory.sentiment_history[0] if a.memory.sentiment_history else 0.0
            agent_finals[db_id] = (
                round(a.sentiment, 2),
                len(a.memory.conversion_events),
                round(init, 2),
            )
        dist = results.get("distribution", {})
        await storage.finalize_run(
            self._db_pool,
            self._run_id,
            mean_sentiment=results["average_sentiment"],
            polarization=dist.get("polarization_index", 0.0),
            distribution=dist,
            total_conversions=results["total_conversions"],
            brand_tier=(results.get("brand_tier")),
            agent_finals=agent_finals,
        )
        if results.get("report"):
            await storage.insert_report(self._db_pool, self._run_id, results["report"])

    def _save_run_outputs(
        self, shared: SharedMemory, results: dict, report: str,
        folder_name: str | None = None,
    ) -> None:
        """Persist the run to a timestamped folder under runs/.

        Creates three files:
          - debate.txt  : full terminal transcript (all rounds, all debates)
          - report.md   : the final marketing report as markdown
          - summary.json: structured results for later analysis / comparison
        """
        if folder_name is None:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            product_slug = re.sub(r"[^a-zA-Z0-9]+", "-", shared.product.name).strip("-")
            folder_name = f"{timestamp}_{product_slug}"
        run_dir = Path("runs") / folder_name
        run_dir.mkdir(parents=True, exist_ok=True)
        timestamp = folder_name.split("_", 1)[0]

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

    @staticmethod
    def _distribution(sentiments: list[float]) -> dict:
        """Bucket sentiments into 5 bands + compute polarization.

        Buckets follow the -10..+10 sentiment scale used everywhere else.
        polarization_index = fraction of agents at the extremes (|s| >= 7).
        A high mean with high polarization is a marketing red flag —
        "love-it-or-hate-it" hides behind a moderate average.
        """
        if not sentiments:
            return {"buckets": {}, "polarization_index": 0.0, "quartiles": []}
        bands = [
            ("hostile (-10..-7)", -10, -7),
            ("negative (-7..-3)", -7, -3),
            ("neutral (-3..+3)", -3, 3),
            ("positive (+3..+7)", 3, 7),
            ("enthusiast (+7..+10)", 7, 10.0001),  # inclusive upper
        ]
        buckets = {}
        n = len(sentiments)
        for label, lo, hi in bands:
            count = sum(1 for s in sentiments if lo <= s < hi)
            buckets[label] = {"count": count, "pct": round(100 * count / n, 1)}
        extreme = sum(1 for s in sentiments if abs(s) >= 7)
        polarization = round(100 * extreme / n, 1)
        srt = sorted(sentiments)
        q = lambda f: round(srt[min(len(srt) - 1, int(len(srt) * f))], 2)
        return {
            "buckets": buckets,
            "polarization_index": polarization,
            "quartiles": [q(0.25), q(0.50), q(0.75)],
        }

    def _collect_results(self, shared: SharedMemory) -> dict:
        sentiments = [a.sentiment for a in self.agents]
        avg = sum(sentiments) / len(sentiments) if sentiments else 0
        distribution = self._distribution(sentiments)

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
            "brand_tier": shared.signals.brand_tier if shared.signals else None,
            "agent_count": len(self.agents),
            "rounds": self.settings.rounds,
            "average_sentiment": round(avg, 2),
            "sentiment_range": (round(min(sentiments), 2), round(max(sentiments), 2)),
            "distribution": distribution,
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
        # Distribution leads, mean is supplementary — see Phase 2c #1.
        dist = results.get("distribution", {})
        if dist.get("buckets"):
            console.print("[bold]Sentiment Distribution:[/bold]")
            for label, info in dist["buckets"].items():
                bar = "█" * int(info["pct"] / 4)
                console.print(f"  {label:<22} {info['count']:>3} agents ({info['pct']:>4.1f}%) {bar}")
            q = dist.get("quartiles", [])
            if q:
                console.print(f"[dim]Quartiles (Q1/median/Q3): {q[0]} / {q[1]} / {q[2]}[/dim]")
            console.print(f"[dim]Polarization index: {dist['polarization_index']}% at extremes (|s|≥7)[/dim]")
        console.print(f"\nMean (supplementary): {results['average_sentiment']}/10  "
                      f"[dim]range {results['sentiment_range'][0]} to {results['sentiment_range'][1]}[/dim]")
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
