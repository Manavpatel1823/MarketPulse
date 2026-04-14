"""Rich-rendered terminal output for the storage CLI commands."""
from __future__ import annotations

from rich.console import Console
from rich.table import Table

console = Console()


def _fmt_dt(dt) -> str:
    if not dt:
        return "—"
    return dt.strftime("%Y-%m-%d %H:%M")


def _fmt_num(v, places: int = 2, default: str = "—") -> str:
    if v is None:
        return default
    return f"{v:.{places}f}"


def render_run_list(rows: list[dict]) -> None:
    if not rows:
        console.print("[yellow]No runs in database yet.[/yellow]")
        return
    t = Table(title=f"Recent runs ({len(rows)})", show_lines=False)
    t.add_column("ID", justify="right")
    t.add_column("Started")
    t.add_column("Product")
    t.add_column("Tier", style="magenta")
    t.add_column("Mean", justify="right")
    t.add_column("Polariz.", justify="right")
    t.add_column("Agents", justify="right")
    t.add_column("Conv.", justify="right")
    t.add_column("Status")
    for r in rows:
        status = "[green]complete[/green]" if r.get("finished_at") else "[red]incomplete[/red]"
        t.add_row(
            str(r["id"]),
            _fmt_dt(r["started_at"]),
            r["product_name"],
            r.get("brand_tier") or "—",
            _fmt_num(r.get("mean_sentiment")),
            _fmt_num(r.get("polarization"), places=1) + ("%" if r.get("polarization") is not None else ""),
            str(r.get("agent_count") or "—"),
            str(r.get("total_conversions") or 0),
            status,
        )
    console.print(t)


def render_run_detail(run: dict) -> None:
    console.print(f"\n[bold cyan]Run #{run['id']} — {run['product_name']}[/bold cyan]")
    console.print(f"[dim]{_fmt_dt(run['started_at'])} → {_fmt_dt(run.get('finished_at'))}[/dim]")
    console.print(
        f"Backend: {run['backend']} ({run['model']})  |  "
        f"Agents: {run['agent_count']}  |  Rounds: {run['rounds']}"
    )
    console.print(
        f"Mean: [bold]{_fmt_num(run.get('mean_sentiment'))}[/bold]  |  "
        f"Polarization: {_fmt_num(run.get('polarization'), 1)}%  |  "
        f"Conversions: {run.get('total_conversions') or 0}"
    )
    if run.get("brand_tier"):
        console.print(f"Brand tier: [magenta]{run['brand_tier']}[/magenta]")

    dist = run.get("distribution") or {}
    if dist.get("buckets"):
        console.print("\n[bold]Distribution:[/bold]")
        for label, info in dist["buckets"].items():
            bar = "█" * int(info["pct"] / 4)
            console.print(f"  {label:<22} {info['count']:>3} ({info['pct']:>4.1f}%) {bar}")

    sm = run.get("shared_memory") or {}
    comps = sm.get("competitors_json") or []
    if comps:
        console.print("\n[bold]Competitors:[/bold]")
        for c in comps:
            console.print(f"  - {c.get('name', '?')} ({c.get('price', '?')})")

    if run.get("agents"):
        console.print(f"\n[bold]Agents ({len(run['agents'])}):[/bold]")
        t = Table(show_lines=False)
        t.add_column("Persona")
        t.add_column("Archetype", style="magenta")
        t.add_column("Init", justify="right")
        t.add_column("Final", justify="right")
        t.add_column("Δ", justify="right")
        t.add_column("Conv.", justify="right")
        for a in run["agents"]:
            init = a.get("initial_sentiment") or 0.0
            fin = a.get("final_sentiment") or 0.0
            delta = fin - init
            color = "green" if delta > 0.5 else ("red" if delta < -0.5 else "white")
            t.add_row(
                a["name"], a["archetype"],
                _fmt_num(init), _fmt_num(fin),
                f"[{color}]{delta:+.1f}[/{color}]",
                str(a.get("conversion_count") or 0),
            )
        console.print(t)

    rep = run.get("report")
    if rep and rep.get("markdown"):
        md = rep["markdown"]
        excerpt = md[:1200] + ("\n... [truncated, see runs/ folder for full report]" if len(md) > 1200 else "")
        console.print("\n[bold]Report excerpt:[/bold]")
        console.print(excerpt)


def render_comparison(runs: list[dict]) -> None:
    if not runs:
        console.print("[yellow]No matching runs found.[/yellow]")
        return

    bucket_labels = list((runs[0].get("distribution") or {}).get("buckets", {}).keys())

    t = Table(title=f"Comparing {len(runs)} runs", show_lines=True)
    t.add_column("Field", style="bold")
    for r in runs:
        t.add_column(f"#{r['id']} — {r['product_name']}", justify="right")

    def add_row(label: str, get):
        t.add_row(label, *[str(get(r)) for r in runs])

    add_row("Date",          lambda r: _fmt_dt(r["started_at"]))
    add_row("Brand tier",    lambda r: r.get("brand_tier") or "—")
    add_row("Agents/Rounds", lambda r: f"{r['agent_count']}/{r['rounds']}")
    add_row("Mean",          lambda r: _fmt_num(r.get("mean_sentiment")))
    add_row("Polarization",  lambda r: f"{_fmt_num(r.get('polarization'), 1)}%")
    add_row("Conversions",   lambda r: str(r.get("total_conversions") or 0))

    for label in bucket_labels:
        def getter(r, lbl=label):
            b = (r.get("distribution") or {}).get("buckets", {}).get(lbl, {})
            return f"{b.get('count', 0)} ({b.get('pct', 0):.1f}%)"
        add_row(label, getter)

    add_row(
        "Top concerns",
        lambda r: "\n".join(f"- {c} (x{n})" for c, n in r.get("top_concerns", [])) or "—",
    )
    add_row(
        "Top positives",
        lambda r: "\n".join(f"+ {p} (x{n})" for p, n in r.get("top_positives", [])) or "—",
    )

    console.print(t)
