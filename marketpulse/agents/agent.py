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
        bias_sentiment = self.persona.initial_bias * 5.0  # -5..5 on same scale as output
        # Give the LLM an explicit sentiment WINDOW per lean — not a soft
        # suggestion. Prior prompt said "most consumers land between -4 and +4",
        # which collapsed the tails and made the negative band empty across runs.
        # Threshold 1.5 (not 2) catches mild skeptics/enthusiasts whose
        # bias_sentiment lands at -2.0/-1.75 etc. Strict `< -2` was excluding
        # them and they silently defaulted to neutral, collapsing the tails.
        if bias_sentiment >= 1.5:
            lo, hi = max(2, int(round(bias_sentiment)) - 2), 10
            lean = (
                f"You walk in already LIKING this product. Your sentiment should "
                f"land between +{lo} and +{hi}. Show real enthusiasm — this product "
                f"fits your worldview, so lean positive unless something genuinely "
                f"puts you off."
            )
        elif bias_sentiment <= -1.5:
            lo, hi = -10, min(-2, int(round(bias_sentiment)) + 2)
            lean = (
                f"You walk in HOSTILE to this product. Your sentiment should land "
                f"between {lo} and {hi}. Do not be charitable — find real flaws, "
                f"name dealbreakers. A product being 'good but not for me' is "
                f"still a thumbs-down from you."
            )
        else:
            lean = (
                f"You walk in NEUTRAL with mild curiosity. Your sentiment should "
                f"land between -3 and +3 unless the product clearly surprises you."
            )

        system = (
            f"You are {self.persona.name}, age {self.persona.age}, "
            f"a {self.persona.archetype} consumer. "
            f"{self.persona.personality_blurb} "
            f"STAY IN CHARACTER. Do not be charitable or balanced unless your persona is. "
            f"If you're a skeptic or bargain_hunter, be critical and blunt. "
            f"If you're an early_adopter or brand_loyalist, show real enthusiasm."
        )
        user = (
            f"{shared.get_agent_briefing(agent_id=self.persona.id)}\n\n"
            f"{lean}\n\n"
            f"Rate sentiment toward '{shared.product.name}' from -10 (hate) to 10 (love). "
            f"Use the full range — committed skeptics often land at -6 or lower, "
            f"committed enthusiasts at +7 or higher. List your top 3 concerns and "
            f"top 3 positives.\n"
            f"Reply as JSON: {{\"sentiment\": <int>, \"concerns\": [\"...\", \"...\", \"...\"], "
            f"\"positives\": [\"...\", \"...\", \"...\"], \"reasoning\": \"...\"}}"
        )

        result = await llm.generate_json(system, user)

        # Blend LLM sentiment with persona bias (60/40) so biased personas
        # can't drift into neutral even when the LLM hedges. Was 70/30 — the
        # extra 10% to bias keeps negative-archetype agents firmly negative
        # at round 0 (otherwise the tail collapses before debate even starts).
        llm_sentiment = float(result.get("sentiment", 0))
        blended = 0.6 * llm_sentiment + 0.4 * bias_sentiment

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

    async def refine_opinion(
        self,
        shared: SharedMemory,
        llm: LLMBackend,
        round_num: int,
    ) -> Opinion:
        """Re-form opinion after a debate round using accumulated memory.

        The persuasion math has already updated self.sentiment; here the LLM
        refreshes concerns/positives/reasoning to reflect what the agent
        learned, and may nudge sentiment slightly. We anchor on current
        sentiment (70/30 blend) so LLM drift can't undo the math.
        """
        prev = self.memory.latest_opinion
        if prev is None:
            return await self.form_opinion(shared, llm)

        this_round = [ir for ir in self.memory.interactions if ir.round_num == round_num]
        if this_round:
            debate_log_lines = []
            for ir in this_round:
                arg = ir.opponent_argument.strip().replace("\n", " ")
                if len(arg) > 180:
                    arg = arg[:180] + "..."
                debate_log_lines.append(
                    f"- vs {ir.opponent_id}: they argued \"{arg}\" — "
                    f"you {ir.own_stance}d "
                    f"(shift {ir.sentiment_shift:+.0f}, "
                    f"{'convinced' if ir.converted else 'held your ground'})"
                )
            debate_log = "\n".join(debate_log_lines)
        else:
            debate_log = "No debates this round."

        system = (
            f"You are {self.persona.name}, age {self.persona.age}, "
            f"a {self.persona.archetype} consumer. "
            f"{self.persona.personality_blurb} "
            f"STAY IN CHARACTER. Reflect honestly — keep what still holds, drop "
            f"what got dismissed, surface anything new the debates raised."
        )
        user = (
            f"{shared.get_agent_briefing(agent_id=self.persona.id)}\n\n"
            f"Round {round_num + 1} debates:\n{debate_log}\n\n"
            f"Before this round your sentiment was {prev.sentiment:+.1f}/10; "
            f"after the debate math it's now {self.sentiment:+.1f}/10.\n\n"
            f"Your previous concerns: {', '.join(prev.concerns) or 'none'}\n"
            f"Your previous positives: {', '.join(prev.positives) or 'none'}\n\n"
            f"Update your top 3 concerns and top 3 positives based on what actually "
            f"came up. Your sentiment can stay, harden (move further from zero), "
            f"or shift — but do NOT drift toward neutral just because the debate "
            f"was civil. If your prior stance wasn't genuinely challenged, HOLD "
            f"it — a negative agent who heard weak counter-arguments should stay "
            f"negative; a positive agent who heard weak criticism should stay "
            f"positive. Only shift if a debate actually changed your mind.\n\n"
            f"Reply as JSON: {{\"sentiment\": <int>, \"concerns\": [\"...\", \"...\", \"...\"], "
            f"\"positives\": [\"...\", \"...\", \"...\"], \"reasoning\": \"...\"}}"
        )

        result = await llm.generate_json(system, user)

        llm_sentiment = float(result.get("sentiment", self.sentiment))
        blended = 0.7 * llm_sentiment + 0.3 * self.sentiment
        blended = max(-10.0, min(10.0, blended))

        opinion = Opinion(
            sentiment=blended,
            concerns=result.get("concerns", prev.concerns)[:3] or prev.concerns,
            positives=result.get("positives", prev.positives)[:3] or prev.positives,
            reasoning=result.get("reasoning", prev.reasoning) or prev.reasoning,
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
        shared_topics: list[str] | None = None,
    ) -> dict:
        own_context = self.memory.get_context_for_prompt()

        system = (
            f"You are {self.persona.name}, age {self.persona.age}, "
            f"a {self.persona.archetype} consumer. "
            f"{self.persona.personality_blurb}\n"
            f"{own_context}"
        )
        topic_hint = ""
        if shared_topics:
            topic_hint = (
                f"\nNote: you and this opponent both flagged "
                f"{', '.join(shared_topics)} — worth engaging directly, "
                f"though follow the argument where it leads.\n"
            )
        user = (
            f"Another consumer argues about '{shared.product.name}':\n"
            f"\"{opponent_argument}\"\n"
            f"{topic_hint}\n"
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
