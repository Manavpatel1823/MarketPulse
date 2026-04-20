import re

from marketpulse.agents.agent import Agent


# Words stripped before computing topical overlap — generic filler that shows 
# up in nearly every opinion and would inflate overlap scores meaninglessly.
_STOPWORDS = { 
    "the", "and", "for", "with", "that", "this", "but", "not", "you", "are",
    "have", "has", "had", "will", "would", "could", "should", "from", "about",
    "their", "there", "which", "what", "when", "where", "more", "less", "than",
    "into", "over", "under", "some", "most", "they", "them", "then", "been",
    "being", "very", "just", "like", "product", "good", "great", "bad",
    "really", "feels", "seems", "still", "much", "even", "only", "also",
}


def _topical_tokens(agent: Agent) -> set[str]:
    op = agent.memory.latest_opinion
    if not op:
        return set()
    text = " ".join(op.concerns + op.positives).lower()
    tokens = re.findall(r"[a-z][a-z'-]+", text)
    return {t for t in tokens if len(t) > 3 and t not in _STOPWORDS}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


# Below this jaccard score we don't inject a topic hint into the debate — the
# overlap is too shallow to be a real shared concern. Threshold found empirically:
# <0.15 is usually coincidental wording (both mention "price" in different senses),
# ≥0.15 is a genuine shared frame.
TOPIC_HINT_THRESHOLD = 0.15
# Cap the hint to a few tokens. More than ~3 and the debate starts to feel
# scripted — we're suggesting a frame, not writing the argument.
TOPIC_HINT_MAX_TOKENS = 3


def adversarial_pairing(
    agents: list[Agent], previous_pairs: set[tuple[str, str]]
) -> list[tuple[Agent, Agent, list[str]]]:
    """Pair agents for sharp, focused disagreement.

    Returns (a, b, shared_topics) — shared_topics is a small list of tokens
    both agents flagged, used by the debate prompt to nudge the argument
    toward substance. Empty list means "no hint, let the debate roam".

    Scoring: (sentiment_gap × (1 + topical_overlap)). Previously-seen pairs
    are softly penalized (×0.3), not banned, so small panels still pair.
    Topic hint tokens are ranked by *rarity across the panel* — a token
    only a few agents use is specific (e.g. "multipoint", "ldac"); a token
    most agents mention is generic filler ("active", "after", "price").
    """
    tokens_by_id = {a.persona.id: _topical_tokens(a) for a in agents}

    # Document frequency per token across the panel. Used below to prefer
    # specific tokens over generic ones when picking the hint.
    df: dict[str, int] = {}
    for toks in tokens_by_id.values():
        for t in toks:
            df[t] = df.get(t, 0) + 1
    n_agents = max(1, len(agents))
    # Cut tokens that appear in > 60% of agents — they're panel-wide filler,
    # not a shared *frame*. "price" showing up in 20/25 opinions is not a hint.
    generic_cutoff = 0.6 * n_agents

    candidates: list[tuple[float, float, Agent, Agent]] = []
    n = len(agents)
    for i in range(n):
        for j in range(i + 1, n):
            a, b = agents[i], agents[j]
            pair_key = tuple(sorted((a.persona.id, b.persona.id)))
            sentiment_gap = abs(a.sentiment - b.sentiment)
            overlap = _jaccard(tokens_by_id[a.persona.id], tokens_by_id[b.persona.id])
            score = sentiment_gap * (1.0 + overlap)
            if pair_key in previous_pairs:
                score *= 0.3
            candidates.append((score, overlap, a, b))

    candidates.sort(key=lambda x: -x[0])

    pairs: list[tuple[Agent, Agent, list[str]]] = []
    used: set[str] = set()
    for _, overlap, a, b in candidates:
        if a.persona.id in used or b.persona.id in used:
            continue
        shared: list[str] = []
        if overlap >= TOPIC_HINT_THRESHOLD:
            shared_tokens = tokens_by_id[a.persona.id] & tokens_by_id[b.persona.id]
            # Drop tokens that are panel-wide filler (in >60% of agents)
            specific = [t for t in shared_tokens if df.get(t, 0) <= generic_cutoff]
            # Rank by rarity (lowest DF first = most specific), break ties by
            # length desc (prefer longer/more meaningful tokens), then alpha
            specific.sort(key=lambda t: (df[t], -len(t), t))
            shared = specific[:TOPIC_HINT_MAX_TOKENS]
        pairs.append((a, b, shared))
        used.add(a.persona.id)
        used.add(b.persona.id)

    remaining = [a for a in agents if a.persona.id not in used]
    for i in range(0, len(remaining) - 1, 2):
        pairs.append((remaining[i], remaining[i + 1], []))

    return pairs
