from marketpulse.agents.persona import Persona
from marketpulse.llm.base import LLMBackend
from marketpulse.memory.individual import AgentMemory, Opinion, InteractionRecord
from marketpulse.memory.shared import SharedMemory


class Agent:
    def __init__(self, persona: Persona):
        self.persona = persona
        self.memory = AgentMemory(agent_id=persona.id)
        self.sentiment = persona.initial_bias * 5.0  # scale -1..1 to -5..5
        self.confidence = 0.8

    async def form_opinion(self, shared: SharedMemory, llm: LLMBackend) -> Opinion:
        system = (
            f"You are {self.persona.name}, age {self.persona.age}, "
            f"a {self.persona.archetype} consumer. "
            f"{self.persona.personality_blurb} "
            f"Rate products based on your values and personality."
        )
        user = (
            f"{shared.get_agent_briefing()}\n\n"
            f"Rate your sentiment toward '{shared.product.name}' from -10 (hate) to 10 (love). "
            f"List your top 3 concerns and top 3 positives.\n"
            f"Reply as JSON: {{\"sentiment\": <int>, \"concerns\": [\"...\", \"...\", \"...\"], "
            f"\"positives\": [\"...\", \"...\", \"...\"], \"reasoning\": \"...\"}}"
        )

        result = await llm.generate_json(system, user)

        opinion = Opinion(
            sentiment=float(result.get("sentiment", 0)),
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
            f"Do you agree, partially agree, or disagree? How does this change your view?\n"
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
