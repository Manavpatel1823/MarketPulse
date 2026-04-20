"""Final reasoning agent: turns simulation results into a marketing report.

Two Phase 2c rules drive this file:

1. Distribution over averages. A 6/10 mean from "everyone moderately likes it"
   and "half love / half hate" are completely different marketing situations.
   The report leads with the distribution; the mean is supplementary.

2. Company-specific concerns only. Generic concerns ("limited brand
   recognition", "competitive market") are unactionable. The reasoning
   agent must cite the actual product, named competitors, specific
   features, or specific market positions from the research data.
"""
from marketpulse.llm.base import LLMBackend
from marketpulse.memory.shared import SharedMemory


def _distribution_block(distribution: dict) -> str:
    """Render the distribution as a compact text block for the LLM."""
    if not distribution or not distribution.get("buckets"):
        return "(no distribution data)"
    lines = []
    for label, info in distribution["buckets"].items():
        lines.append(f"  {label:<22} {info['count']:>3} agents ({info['pct']:>4.1f}%)")
    q = distribution.get("quartiles", [])
    if q:
        lines.append(f"  Quartiles (Q1/median/Q3): {q[0]} / {q[1]} / {q[2]}")
    lines.append(f"  Polarization (|s|≥7): {distribution['polarization_index']}% of agents at extremes")
    return "\n".join(lines)


def _classify_verdict(distribution: dict, mean: float) -> tuple[str, str]:
    """Deterministic market verdict from distribution shape.

    Returns (label, launch_gate) where launch_gate is the explicit instruction
    the LLM must honor. Prevents "everyone-likes-it" narratives from a handful
    of moderate positives when the full distribution is weak or polarized.
    """
    buckets = distribution.get("buckets", {}) if distribution else {}
    if not buckets:
        return ("insufficient-data", "HOLD — not enough signal to recommend launch.")

    pct = {lbl: info["pct"] for lbl, info in buckets.items()}
    hostile = pct.get("hostile (-10..-7)", 0.0)
    negative = pct.get("negative (-7..-3)", 0.0)
    neutral = pct.get("neutral (-3..+3)", 0.0)
    positive = pct.get("positive (+3..+7)", 0.0)
    enthusiast = pct.get("enthusiast (+7..+10)", 0.0)
    polarization = distribution.get("polarization_index", 0.0)
    negative_total = hostile + negative
    positive_total = positive + enthusiast

    if negative_total >= 40:
        return ("rejected",
                "DO NOT launch. Fix the named concerns before any GTM spend.")
    if polarization >= 30 and hostile >= 10:
        return ("polarized-love-hate",
                "DO NOT launch broadly. Polarization hides rejection behind a moderate mean — "
                "either niche-launch to enthusiasts only, or resolve the hostile cluster's concerns first.")
    if enthusiast >= 20 and negative_total >= 20:
        return ("niche-enthusiasm",
                "CAUTION. Real enthusiast base exists but alongside real rejection. "
                "Niche/segmented launch only — not a broad-market product yet.")
    if neutral >= 50 and positive_total < 25:
        return ("broad-lukewarm",
                "HOLD. Broad indifference is worse than polarization — no organic pull. "
                "Re-position or sharpen differentiation before launch.")
    if positive_total >= 50 and negative_total <= 15 and polarization < 25:
        return ("broad-approval",
                "PROCEED with launch, but still address the named concerns in messaging.")
    if mean > 0 and negative_total >= 25:
        return ("mixed-lean-positive",
                "CAUTION. Positive lean but meaningful detractor cluster — launch with "
                "explicit mitigation for the top 3 concerns.")
    return ("mixed",
            "CAUTION. No clear consensus — treat any positive mean as soft and address concerns explicitly.")


def _weighted_concerns_block(results: dict) -> str:
    """Show concerns/positives as % of panel so a few loud voices don't dominate."""
    n = max(1, results.get("agent_count", 1))
    lines = []
    concerns = results.get("top_concerns", []) or []
    if concerns:
        lines.append("Top Concerns (panel coverage):")
        for concern, count in concerns:
            pct = round(100 * count / n, 1)
            lines.append(f"  - {concern} — raised by {count}/{n} agents ({pct}% of panel)")
    positives = results.get("top_positives", []) or []
    if positives:
        lines.append("\nTop Positives (panel coverage):")
        for positive, count in positives:
            pct = round(100 * count / n, 1)
            lines.append(f"  - {positive} — raised by {count}/{n} agents ({pct}% of panel)")
    return "\n".join(lines) if lines else "(no concerns or positives captured)"


def _product_context_block(shared: SharedMemory) -> str:
    """The specific facts the analyzer must anchor concerns to."""
    p = shared.product
    lines = [
        f"Product: {p.name}",
        f"Category: {p.category or '(unspecified)'}",
        f"Price: {p.price or '(unspecified)'}",
        f"Description: {p.description or '(none)'}",
    ]
    if p.detailed_description:
        lines.append(f"Detail: {p.detailed_description}")
    if p.features:
        lines.append(f"Features: {', '.join(p.features[:8])}")
    if p.risks:
        lines.append(
            "Known weaknesses (USE THESE for the risks section — "
            "they are the brief's honest trade-offs):"
        )
        for r in p.risks[:6]:
            lines.append(f"  - {r}")
    if p.target_audience:
        lines.append(f"Target audience: {p.target_audience}")
    if shared.competitors:
        lines.append(
            "Competitors (USE THESE NAMES IN THE REPORT; the Positioning line "
            "is authoritative on strengths/weaknesses — do NOT contradict it):"
        )
        for c in shared.competitors:
            lines.append(f"  - {c.name} ({c.price}): {', '.join(c.key_features[:4])}")
            if c.positioning:
                lines.append(f"    Positioning: {c.positioning}")
    if shared.signals:
        s = shared.signals
        lines.append(
            f"Market signals: brand_tier={s.brand_tier}, "
            f"category_maturity={s.category_maturity}, price_position={s.price_position}"
        )
    if shared.market_context:
        lines.append(f"Market context: {shared.market_context}")
    return "\n".join(lines)


async def generate_report(results: dict, shared: SharedMemory, llm: LLMBackend) -> str:
    """Use a reasoning agent to produce a detailed marketing report."""

    distribution_text = _distribution_block(results.get("distribution", {}))
    product_text = _product_context_block(shared)
    verdict_label, launch_gate = _classify_verdict(
        results.get("distribution", {}),
        results.get("average_sentiment", 0.0),
    )
    weighted_concerns_text = _weighted_concerns_block(results)

    summary_lines = [
        f"Simulation: {results['agent_count']} consumer agents, {results['rounds']} debate rounds",
        "",
        "SENTIMENT DISTRIBUTION (lead the report with this — NOT the mean):",
        distribution_text,
        "",
        f"DETERMINISTIC VERDICT: {verdict_label}",
        f"LAUNCH GATE (must be honored in Executive Summary): {launch_gate}",
        "",
        f"Mean sentiment (supplementary, do not lead with this): {results['average_sentiment']}/10",
        f"Range: {results['sentiment_range'][0]} to {results['sentiment_range'][1]}",
        f"Total Opinion Conversions: {results['total_conversions']}",
        "",
        weighted_concerns_text,
    ]

    summary_lines.append("\nSentiment by Consumer Archetype:")
    for arch, avg in sorted(results["archetype_sentiments"].items(), key=lambda x: -x[1]):
        summary_lines.append(f"  - {arch}: {avg:+.1f}/10")

    if results.get("aspect_ratings"):
        summary_lines.append("\nAspect Ratings (panel average, 1-10 scale):")
        for aspect, avg in sorted(results["aspect_ratings"].items(), key=lambda x: -x[1]):
            flag = " ⚠ WEAK" if avg < 5.0 else (" ★ STRONG" if avg >= 7.0 else "")
            summary_lines.append(f"  - {aspect.replace('_', ' ')}: {avg}/10{flag}")
        if results.get("aspect_by_archetype"):
            summary_lines.append("\nAspect Ratings by Archetype:")
            for arch, aspects in sorted(results["aspect_by_archetype"].items()):
                ratings_str = ", ".join(f"{a}: {v}" for a, v in sorted(aspects.items()))
                summary_lines.append(f"  {arch}: {ratings_str}")

    summary_lines.append("\nAgent Sentiment Journeys:")
    for agent in results["agents"]:
        direction = "improved" if agent["final_sentiment"] > agent["initial_sentiment"] else "declined"
        summary_lines.append(
            f"  - {agent['name']} ({agent['archetype']}): "
            f"{agent['initial_sentiment']:+.1f} → {agent['final_sentiment']:+.1f} ({direction}), "
            f"{agent['conversions']} conversion(s)"
        )

    structured_summary = "\n".join(summary_lines)

    system = (
        "You are a senior marketing strategist with 20 years of experience. "
        "You analyze consumer simulation data to produce ACTIONABLE intelligence. "
        "Four rules you NEVER break:\n"
        "1. Lead every analysis with the SHAPE of the distribution, not the mean. "
        "A 6/10 mean from broad mild approval and a 6/10 mean from a polarized "
        "love/hate split require completely different marketing strategies. "
        "Always describe the spread first, then mention the mean as context.\n"
        "2. Concerns must be COMPANY-SPECIFIC. Reject generic phrases like "
        "'limited brand recognition', 'competitive market', 'consumer trust', "
        "'pricing concerns'. Replace each generic concern with one that names "
        "this product's specific features, named competitors, or specific market "
        "position. If raw data only gives generic concerns, INFER the specific "
        "version from the product context.\n"
        "3. HONOR THE LAUNCH GATE. The simulation data includes a deterministic "
        "verdict and launch gate computed from the full distribution. You MUST "
        "echo that gate in the Executive Summary verbatim in intent — do NOT "
        "recommend launch when the gate says HOLD, DO NOT, or CAUTION. A few "
        "enthusiastic agents do not override widespread concerns or polarization. "
        "Downside must be surfaced even when the mean is positive.\n"
        "4. NO FABRICATED NUMBERS. Every specific number (price, weight, battery "
        "hours, nits, resolution, framerate) must come from the PRODUCT CONTEXT "
        "block. Do NOT invent plausible-sounding specs for competitors. If the "
        "context doesn't give you a number to compare against, say 'better battery "
        "than ROG Ally X' — do NOT say 'vs. ROG Ally X's 4-6 hours' unless that "
        "figure is literally in the context. Fabricated specs ship as fact into "
        "a marketing deck; this is the worst failure mode."
    )

    user = (
        f"PRODUCT CONTEXT (use these names and facts in the report):\n"
        f"{product_text}\n\n"
        f"SIMULATION RESULTS:\n"
        f"{structured_summary}\n\n"
        f"Produce a marketing report with these sections:\n\n"
        f"1. EXECUTIVE SUMMARY (3-4 sentences)\n"
        f"   - First sentence MUST describe distribution shape "
        f"(e.g. 'polarized: 30% enthusiasts, 45% hostile' or "
        f"'broad mild approval clustered in the +3 to +5 band').\n"
        f"   - Second sentence MUST state the LAUNCH GATE verdict from the data "
        f"(PROCEED / CAUTION / HOLD / DO NOT launch) and the single biggest reason.\n"
        f"   - Then state what this distribution implies for go-to-market.\n"
        f"   - Mean is mentioned only as supporting detail, not as the headline.\n"
        f"   - If the gate is CAUTION / HOLD / DO NOT, you MUST name the top 2 "
        f"concerns by panel coverage (%) as the reason.\n\n"
        f"2. DISTRIBUTION ANALYSIS\n"
        f"   - Walk through each band; call out the polarization index explicitly.\n"
        f"   - State which marketing situation this is "
        f"('niche enthusiasm', 'broad lukewarm', 'love-it-or-hate-it', 'rejected').\n\n"
        f"3. KEY RISKS — COMPANY-SPECIFIC\n"
        f"   - Each risk must NAME this product, a feature, OR a specific competitor.\n"
        f"   - Order risks by PANEL COVERAGE (%), not by how severely any single "
        f"agent phrased them. A concern raised by 30% of the panel outranks "
        f"one raised loudly by 2 agents.\n"
        f"   - Include concerns raised by positive agents too — those are the "
        f"strongest signals (even fans see these issues).\n"
        f"   - BAD example: 'limited brand recognition'.\n"
        f"   - GOOD example for an EV: 'Range of 280mi falls below "
        f"the Tesla Model Y at 330mi — segment-specific gap, not a generic concern'.\n"
        f"   - Replace any generic raw concern with its specific version.\n\n"
        f"4. KEY OPPORTUNITIES — COMPANY-SPECIFIC\n"
        f"   - Same rule. Name the segment, the feature, the competitor "
        f"this product wins against.\n\n"
        f"5. COMPETITIVE POSITIONING\n"
        f"   - Name each competitor from the product context. For each one, "
        f"frame from THIS PRODUCT's perspective:\n"
        f"     • 'Steam Deck OLED wins vs X on: ...' (concrete advantages)\n"
        f"     • 'Steam Deck OLED loses vs X on: ...' (concrete gaps)\n"
        f"   - Never phrase a competitor's advantage as the competitor 'losing' "
        f"something — that reads as nonsense (e.g. 'Switch loses PC game library' "
        f"is wrong; it should be 'this product wins vs Switch on: PC game library').\n"
        f"   - Use only specs that appear in the PRODUCT CONTEXT. If you don't "
        f"have a comparable number, make the point qualitatively.\n\n"
        f"6. CONVERSION ANALYSIS\n"
        f"   - What types of arguments moved the needle? "
        f"What does this say about messaging?\n\n"
        f"7. RECOMMENDATIONS (5 specific actions)\n"
        f"   - Each must reference a specific feature, competitor, "
        f"or distribution band. No 'invest in brand awareness' filler.\n\n"
        f"8. ASPECT BREAKDOWN\n"
        f"   - For each rated aspect in the data, state the panel average and what it means.\n"
        f"   - Flag any aspect below 5.0 as a specific weakness worth addressing.\n"
        f"   - Flag any aspect at 7.0+ as a strength to leverage in messaging.\n"
        f"   - Cross-reference: which archetype types rate which aspects lowest/highest?\n"
        f"   - If no aspect data is available, skip this section.\n\n"
        f"Use the actual numbers and named entities. No filler."
    )

    report = await llm.generate(system, user)
    return report
