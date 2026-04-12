import json

from marketpulse.llm.base import LLMBackend


async def generate_report(results: dict, llm: LLMBackend) -> str:
    """Use a reasoning agent to produce a detailed marketing report from simulation results."""

    # Build structured summary for the reasoning agent
    summary_lines = [
        f"Product: {results['product']}",
        f"Simulation: {results['agent_count']} consumer agents, {results['rounds']} debate rounds",
        f"Overall Sentiment: {results['average_sentiment']}/10",
        f"Sentiment Range: {results['sentiment_range'][0]} to {results['sentiment_range'][1]}",
        f"Total Opinion Conversions: {results['total_conversions']}",
    ]

    if results["top_concerns"]:
        summary_lines.append("\nTop Consumer Concerns:")
        for concern, count in results["top_concerns"]:
            summary_lines.append(f"  - {concern} (raised by {count} agents)")

    if results["top_positives"]:
        summary_lines.append("\nTop Consumer Positives:")
        for positive, count in results["top_positives"]:
            summary_lines.append(f"  - {positive} (raised by {count} agents)")

    summary_lines.append("\nSentiment by Consumer Archetype:")
    for arch, avg in sorted(results["archetype_sentiments"].items(), key=lambda x: -x[1]):
        summary_lines.append(f"  - {arch}: {avg:+.1f}/10")

    # Individual agent journeys
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
        "You analyze consumer simulation data to provide actionable insights. "
        "Be specific, data-driven, and direct. No fluff."
    )

    user = (
        f"Analyze this consumer sentiment simulation and produce a detailed marketing report.\n\n"
        f"{structured_summary}\n\n"
        f"Produce a report with these sections:\n"
        f"1. EXECUTIVE SUMMARY (3-4 sentences, the most critical takeaway)\n"
        f"2. SENTIMENT OVERVIEW (overall score interpretation, distribution analysis)\n"
        f"3. KEY RISKS (top concerns, which demographics are hostile, what could kill adoption)\n"
        f"4. KEY OPPORTUNITIES (strongest positives, most enthusiastic segments, growth levers)\n"
        f"5. COMPETITIVE POSITIONING (how the product stands vs alternatives based on agent reactions)\n"
        f"6. CONVERSION ANALYSIS (what arguments changed minds, what this reveals about messaging)\n"
        f"7. RECOMMENDATIONS (5 specific, actionable items for the marketing team)\n\n"
        f"Be specific to this product and these results. Reference actual numbers from the data."
    )

    report = await llm.generate(system, user)
    return report
