from dataclasses import dataclass, field


@dataclass
class Opinion:
    sentiment: float  # -10.0 to 10.0
    concerns: list[str]
    positives: list[str]
    reasoning: str


@dataclass
class InteractionRecord:
    round_num: int
    opponent_id: str
    opponent_argument: str
    own_stance: str  # "agree" | "partial" | "disagree"
    sentiment_shift: float
    converted: bool


@dataclass
class ConversionEvent:
    round_num: int
    triggered_by: str  # agent_id of persuader
    old_sentiment: float
    new_sentiment: float
    reason: str


@dataclass
class AgentMemory:
    agent_id: str
    opinions: list[Opinion] = field(default_factory=list)
    interactions: list[InteractionRecord] = field(default_factory=list)
    sentiment_history: list[float] = field(default_factory=list)
    conversion_events: list[ConversionEvent] = field(default_factory=list)

    @property
    def latest_opinion(self) -> Opinion | None:
        return self.opinions[-1] if self.opinions else None

    @property
    def recent_interactions(self) -> list[InteractionRecord]:
        return self.interactions[-2:]

    def get_context_for_prompt(self) -> str:
        lines = []
        if self.latest_opinion:
            op = self.latest_opinion
            lines.append(f"Your current sentiment: {op.sentiment}/10")
            lines.append(f"Your concerns: {', '.join(op.concerns)}")
            lines.append(f"Your positives: {', '.join(op.positives)}")
        if self.recent_interactions:
            lines.append("\nRecent debates:")
            for ir in self.recent_interactions:
                lines.append(
                    f"- vs {ir.opponent_id}: you {ir.own_stance}d, "
                    f"shift={ir.sentiment_shift:+.1f}"
                )
        return "\n".join(lines)
