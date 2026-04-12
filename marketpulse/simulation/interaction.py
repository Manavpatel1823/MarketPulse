from marketpulse.agents.agent import Agent


def adversarial_pairing(
    agents: list[Agent], previous_pairs: set[tuple[str, str]]
) -> list[tuple[Agent, Agent]]:
    """Pair agents adversarially: most positive with most negative."""
    sorted_agents = sorted(agents, key=lambda a: a.sentiment, reverse=True)

    pairs = []
    used = set()
    n = len(sorted_agents)

    # Try pairing from extremes inward
    left, right = 0, n - 1
    while left < right:
        a = sorted_agents[left]
        b = sorted_agents[right]

        pair_key = tuple(sorted((a.persona.id, b.persona.id)))

        if a.persona.id not in used and b.persona.id not in used:
            # Deprioritize repeated pairs but still allow them if no alternatives
            if pair_key not in previous_pairs:
                pairs.append((a, b))
                used.add(a.persona.id)
                used.add(b.persona.id)
                left += 1
                right -= 1
            else:
                # Try next candidate on the right
                right -= 1
        else:
            if a.persona.id in used:
                left += 1
            if b.persona.id in used:
                right -= 1

    # If some agents weren't paired due to deduplication, pair remaining
    remaining = [a for a in sorted_agents if a.persona.id not in used]
    for i in range(0, len(remaining) - 1, 2):
        pairs.append((remaining[i], remaining[i + 1]))

    return pairs
