from marketpulse.agents.persona import Persona
from marketpulse.llm.base import LLMBackend
from marketpulse.memory.individual import AgentMemory, Opinion, InteractionRecord
from marketpulse.memory.shared import SharedMemory


# Brand-tier skew applied on top of persona.initial_bias (-1..1 scale).
# Rationale: an Apple launch walks in with reputation equity a no-name startup
# lacks — the same persona evaluates them with a different prior. Kept small
# (<=0.2) so strong research negatives can still override it.
_BRAND_TIER_BIAS = {
    "incumbent": 0.20,
    "challenger": 0.10,
    "unknown": 0.00,
    "controversial": -0.20,
}


class Agent:
    def __init__(self, persona: Persona):
        self.persona = persona
        self.memory = AgentMemory(agent_id=persona.id)
        self.sentiment = persona.initial_bias * 5.0  # scale -1..1 to -5..5
        self.confidence = 0.8

    async def form_opinion(self, shared: SharedMemory, llm: LLMBackend) -> Opinion:
        tier = shared.signals.brand_tier if shared.signals else "unknown"
        tier_skew = _BRAND_TIER_BIAS.get(tier, 0.0)
        effective_bias = max(-1.0, min(1.0, self.persona.initial_bias + tier_skew))
        bias_sentiment = effective_bias * 5.0  # -5..5 on same scale as output
        if bias_sentiment > 2:
            lean = f"You walk in already LIKING this product (starting lean: +{bias_sentiment:.1f})."
        elif bias_sentiment < -2:
            lean = f"You walk in already SKEPTICAL of this product (starting lean: {bias_sentiment:.1f})."
        else:
            lean = f"You walk in NEUTRAL with mild curiosity (starting lean: {bias_sentiment:+.1f})."

        if tier == "incumbent":
            lean += " The brand is a proven incumbent — reputation earns it the benefit of the doubt on quality, but hold the line on price and over-promising."
        elif tier == "controversial":
            lean += " The brand carries real baggage — be blunt about past issues, don't let marketing language paper over them."
        elif tier == "unknown":
            lean += " The brand is unproven — no reputation to lean on, so judge strictly on what the product actually delivers."

        system = (
            f"You are {self.persona.name}, age {self.persona.age}, "
            f"a {self.persona.archetype} consumer. "
            f"{self.persona.personality_blurb} "
            f"STAY IN CHARACTER. Do not be charitable or balanced unless your persona is. "
            f"If you're a skeptic or bargain_hunter, be critical and blunt. "
            f"If you're an early_adopter or brand_loyalist, show real enthusiasm."
        )
        user = (
            f"{shared.get_agent_briefing()}\n\n"
            f"{lean} Your final sentiment should usually be within 2 points of that lean "
            f"unless the product clearly surprises you.\n\n"
            f"Rate sentiment toward '{shared.product.name}' from -10 (hate) to 10 (love). "
            f"Most consumers land between -4 and +4 — scores above +7 should be rare and earned. "
            f"List your top 3 concerns and top 3 positives.\n"
            f"Reply as JSON: {{\"sentiment\": <int>, \"concerns\": [\"...\", \"...\", \"...\"], "
            f"\"positives\": [\"...\", \"...\", \"...\"], \"reasoning\": \"...\"}}"
        )

        result = await llm.generate_json(system, user)

        # Blend LLM sentiment with persona bias (70/30) so the bias actually anchors.
        llm_sentiment = float(result.get("sentiment", 0))
        blended = 0.7 * llm_sentiment + 0.3 * bias_sentiment

        opinion = Opinion(
            sentiment=blended,
            concerns=result.get("concerns", [])[:3],
            positives=result.get("positives", [])[:3],
            reasoning=result.get("reasoning", ""),
        )
        self.sentiment = opinion.sentiment
        self.memory.opinions.append(opinion)
        self.memory.sentiment_history.append(self.sentiment)
        return opinion

    async def debate(
        self,
        opponent_id: str,
        opponent_argument: str,
        shared: SharedMemory,
        llm: LLMBackend,
        round_num: int,
    ) -> dict:
        own_context = self.memory.get_context_for_prompt()

        system = (
            f"You are {self.persona.name}, age {self.persona.age}, "
            f"a {self.persona.archetype} consumer. "
            f"{self.persona.personality_blurb}\n"
            f"{own_context}"
        )
        user = (
            f"Another consumer argues about '{shared.product.name}':\n"
            f"\"{opponent_argument}\"\n\n"
            f"Do you agree, partially agree, or disagree? How does this change your view?\n\n"
            f"Set `convinced: true` ONLY if the argument genuinely flipped your stance "
            f"(e.g. you were negative and now lean positive, or vice versa). It's okay — "
            f"and realistic — for ~10-20% of strong arguments to flip a consumer's mind. "
            f"Don't default to false just to seem consistent; real consumers do change their minds.\n"
            f"Reply as JSON: {{\"stance\": \"agree|partial|disagree\", "
            f"\"counter_argument\": \"your response in 2-3 sentences\", "
            f"\"sentiment_shift\": <int from -3 to 3>, \"convinced\": <true/false>}}"
        )

        result = await llm.generate_json(system, user)

        stance = result.get("stance", "disagree")
        shift = float(result.get("sentiment_shift", 0))
        convinced = bool(result.get("convinced", False))

        # Record interaction
        record = InteractionRecord(
            round_num=round_num,
            opponent_id=opponent_id,
            opponent_argument=opponent_argument,
            own_stance=stance,
            sentiment_shift=shift,
            converted=convinced,
        )
        self.memory.interactions.append(record)

        return {
            "stance": stance,
            "counter_argument": result.get("counter_argument", ""),
            "sentiment_shift": shift,
            "convinced": convinced,
        }
