from dataclasses import dataclass, field

from marketpulse.agents.agent import Agent
from marketpulse.memory.individual import ConversionEvent


@dataclass
class SentimentState:
    score: float = 0.0  # -10.0 to 10.0
    confidence: float = 0.8  # 0.0 to 1.0
    weights: dict = field(default_factory=lambda: {
        "price": 0.2,
        "quality": 0.2,
        "features": 0.2,
        "brand": 0.2,
        "convenience": 0.2,
    })


def apply_persuasion(
    agent: Agent,
    debate_result: dict,
    opponent_sentiment: float,
    round_num: int,
    persuasion_threshold: float = 0.7,
) -> bool:
    """Apply persuasion mechanics after a debate. Returns True if converted."""
    shift = debate_result["sentiment_shift"]
    convinced = debate_result["convinced"]

    # Modulate shift by brand loyalty (resistance)
    effective_shift = shift * (1.0 - agent.persona.brand_loyalty * 0.7)

    # Apply shift
    old_sentiment = agent.sentiment
    agent.sentiment = max(-10, min(10, agent.sentiment + effective_shift))

    # Confidence decay on strong counterarguments
    if abs(shift) > 2:
        agent.confidence *= 0.85

    # Conversion check
    converted = False
    if convinced and agent.confidence < persuasion_threshold:
        # Move 60% toward opponent's sentiment
        agent.sentiment = agent.sentiment + 0.6 * (opponent_sentiment - agent.sentiment)
        agent.confidence = 0.5  # reset confidence after conversion
        converted = True

        agent.memory.conversion_events.append(ConversionEvent(
            round_num=round_num,
            triggered_by="opponent",
            old_sentiment=old_sentiment,
            new_sentiment=agent.sentiment,
            reason=debate_result.get("counter_argument", ""),
        ))

    agent.memory.sentiment_history.append(agent.sentiment)
    return converted
