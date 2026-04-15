import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from marketpulse.memory.shared import MarketSignals


# Panel composition — fixed ratio regardless of brand tier. Rationale: we
# evaluate the PRODUCT, not the brand. A startup with a great product should
# win this panel; an incumbent shipping a dud should lose it. Brand tier still
# flows into the briefing as context (market footprint), but it doesn't bend
# the jury. Ratio 4:3:3 (pos:neu:neg) gives a realistic mix — slightly more
# open-minded than hostile, with a strong skeptic minority.
DEFAULT_SKEW: tuple[float, float, float] = (0.40, 0.30, 0.30)


def _tier_fractions(skew: "MarketSignals | None") -> tuple[float, float, float]:
    return DEFAULT_SKEW

# Archetype classification (2 positive : 3 neutral : 5 negative)
# Real markets dominated by incumbents (Apple/Samsung ~81% phone share, etc.) skew
# skeptical toward newcomers. A balanced or positive-leaning panel produces
# unrealistically high scores for unknown brands. The 2:3:5 ratio reflects that
# most consumers default to "why would I switch?" when evaluating challengers.
ARCHETYPES = {
    # ===== POSITIVE (4) =====
    "early_adopter": {
        "tech_savviness": (0.7, 1.0),
        "brand_loyalty": (0.2, 0.5),
        "price_sensitivity": (0.1, 0.4),
        "initial_bias": (0.3, 0.8),
    },
    "brand_loyalist": {
        "tech_savviness": (0.3, 0.7),
        "brand_loyalty": (0.8, 1.0),
        "price_sensitivity": (0.1, 0.4),
        "initial_bias": (0.2, 0.6),
    },
    "tech_enthusiast": {
        "tech_savviness": (0.8, 1.0),
        "brand_loyalty": (0.3, 0.6),
        "price_sensitivity": (0.2, 0.5),
        "initial_bias": (0.4, 0.9),
    },
    "trend_follower": {
        "tech_savviness": (0.4, 0.7),
        "brand_loyalty": (0.2, 0.4),
        "price_sensitivity": (0.3, 0.6),
        "initial_bias": (0.1, 0.6),
    },

    # ===== NEUTRAL (3) =====
    "eco_conscious": {
        "tech_savviness": (0.4, 0.7),
        "brand_loyalty": (0.3, 0.6),
        "price_sensitivity": (0.2, 0.5),
        "initial_bias": (-0.3, 0.3),
    },
    "convenience_seeker": {
        "tech_savviness": (0.2, 0.5),
        "brand_loyalty": (0.4, 0.7),
        "price_sensitivity": (0.3, 0.6),
        "initial_bias": (-0.2, 0.3),
    },
    "quality_purist": {
        "tech_savviness": (0.5, 0.8),
        "brand_loyalty": (0.5, 0.8),
        "price_sensitivity": (0.1, 0.3),
        "initial_bias": (-0.2, 0.2),
    },

    # ===== NEGATIVE (3) =====
    "skeptic": {
        "tech_savviness": (0.4, 0.7),
        "brand_loyalty": (0.1, 0.3),
        "price_sensitivity": (0.3, 0.6),
        "initial_bias": (-0.8, -0.2),
    },
    "bargain_hunter": {
        "tech_savviness": (0.3, 0.6),
        "brand_loyalty": (0.1, 0.3),
        "price_sensitivity": (0.8, 1.0),
        "initial_bias": (-0.6, -0.1),
    },
    "pragmatist": {
        "tech_savviness": (0.4, 0.7),
        "brand_loyalty": (0.3, 0.5),
        "price_sensitivity": (0.4, 0.7),
        "initial_bias": (-0.5, 0.0),
    },
}

# Archetype tier map for quota-based procedural generation (see _generate_procedural)
ARCHETYPE_TIERS = {
    "positive": ["early_adopter", "brand_loyalist", "tech_enthusiast", "trend_follower"],
    "neutral": ["eco_conscious", "convenience_seeker", "quality_purist"],
    "negative": ["skeptic", "bargain_hunter", "pragmatist"],
}

NAMES = [
    "Alex", "Jordan", "Sam", "Taylor", "Morgan", "Casey", "Riley", "Quinn",
    "Avery", "Jamie", "Drew", "Skyler", "Reese", "Finley", "Dakota", "Blake",
    "Cameron", "Emery", "Hayden", "Kendall", "Logan", "Parker", "Rowan",
    "Sage", "Tatum", "Charlie", "Ellis", "Harper", "Jesse", "Kai",
]

AGE_RANGES = {
    "young_adult": (18, 29),
    "adult": (30, 44),
    "middle_aged": (45, 59),
    "senior": (60, 75),
}

INCOME_BRACKETS = ["low", "middle", "upper_middle", "high"]


@dataclass
class Persona:
    id: str
    name: str
    age: int
    income_bracket: str
    tech_savviness: float
    brand_loyalty: float
    price_sensitivity: float
    archetype: str
    personality_blurb: str
    initial_bias: float


def generate_personas(
    count: int,
    use_hardcoded: bool = True,
    skew: "MarketSignals | None" = None,
) -> list[Persona]:
    # Prefer hardcoded panel for determinism + faster startup. Tier ratio is
    # chosen from SKEW_BY_TIER via brand_tier — `unknown` (2:3:5) is the fallback.
    pos_frac, neu_frac, neg_frac = _tier_fractions(skew)
    if use_hardcoded:
        from .hardcoded_personas import HARDCODED_PERSONAS

        pos_n = max(1, round(count * pos_frac))
        neu_n = max(1, round(count * neu_frac))
        neg_n = count - pos_n - neu_n

        buckets = {
            tier: [p for p in HARDCODED_PERSONAS if p.archetype in archs]
            for tier, archs in ARCHETYPE_TIERS.items()
        }

        # Shuffle within each bucket using a fixed seed so income/age/demographic
        # spread is varied but the panel stays deterministic across runs. Without
        # this, slicing [:N] always picks the first N of each tier and misses
        # low-income personas that happen to sit later in the file.
        seeded = random.Random(42)
        for tier in buckets:
            seeded.shuffle(buckets[tier])

        selected: list[Persona] = []
        deficit = 0
        for tier, want in [("positive", pos_n), ("neutral", neu_n), ("negative", neg_n)]:
            take = min(want, len(buckets[tier]))
            selected.extend(buckets[tier][:take])
            deficit += want - take

        # If any tier ran out (e.g. big negative quota > hardcoded pool), pad
        # with procedural generation honoring the same skew.
        if deficit > 0:
            selected.extend(_generate_procedural(deficit, offset=len(selected), skew=skew))

        return selected

    return _generate_procedural(count, offset=0, skew=skew)


def _generate_procedural(
    count: int,
    offset: int = 0,
    skew: "MarketSignals | None" = None,
) -> list[Persona]:
    """Generate personas with tier-ratio quotas driven by brand_tier skew."""
    pos_frac, neu_frac, neg_frac = _tier_fractions(skew)
    pos_count = max(1, round(count * pos_frac))
    neu_count = max(1, round(count * neu_frac))
    neg_count = count - pos_count - neu_count

    sample_list: list[str] = []
    for i in range(pos_count):
        sample_list.append(ARCHETYPE_TIERS["positive"][i % len(ARCHETYPE_TIERS["positive"])])
    for i in range(neu_count):
        sample_list.append(ARCHETYPE_TIERS["neutral"][i % len(ARCHETYPE_TIERS["neutral"])])
    for i in range(neg_count):
        sample_list.append(ARCHETYPE_TIERS["negative"][i % len(ARCHETYPE_TIERS["negative"])])
    random.shuffle(sample_list)

    personas = []
    for i in range(count):
        archetype = sample_list[i]
        ranges = ARCHETYPES[archetype]

        age_group = random.choice(list(AGE_RANGES.keys()))
        age_lo, age_hi = AGE_RANGES[age_group]

        persona = Persona(
            id=f"agent_{offset + i:03d}",
            name=random.choice(NAMES),
            age=random.randint(age_lo, age_hi),
            income_bracket=random.choice(INCOME_BRACKETS),
            tech_savviness=round(random.uniform(*ranges["tech_savviness"]), 2),
            brand_loyalty=round(random.uniform(*ranges["brand_loyalty"]), 2),
            price_sensitivity=round(random.uniform(*ranges["price_sensitivity"]), 2),
            archetype=archetype,
            personality_blurb="",  # filled by LLM enrichment
            initial_bias=round(random.uniform(*ranges["initial_bias"]), 2),
        )
        personas.append(persona)

    return personas


async def enrich_personas(personas: list[Persona], llm) -> list[Persona]:
    """Enrich personas with LLM-generated personality blurbs in batches.

    Skips any persona that already has a non-empty blurb (e.g. hardcoded ones).
    """
    # Only enrich personas without a blurb — hardcoded personas come pre-filled.
    needs_enrichment = [p for p in personas if not p.personality_blurb]
    if not needs_enrichment:
        return personas

    batch_size = 10
    for i in range(0, len(needs_enrichment), batch_size):
        batch = needs_enrichment[i : i + batch_size]
        descriptions = []
        for p in batch:
            descriptions.append(
                f"- {p.name}, age {p.age}, {p.income_bracket} income, "
                f"{p.archetype} type, tech-savvy={p.tech_savviness:.1f}, "
                f"price-sensitive={p.price_sensitivity:.1f}"
            )

        system = (
            "You generate brief consumer personality descriptions. "
            "For each person listed, write a 2-sentence personality blurb "
            "that captures how they approach purchasing decisions. "
            "Return JSON: {\"blurbs\": [\"blurb1\", \"blurb2\", ...]}"
        )
        user = "Generate personality blurbs for:\n" + "\n".join(descriptions)

        result = await llm.generate_json(system, user)
        blurbs = result.get("blurbs", [])
        for j, persona in enumerate(batch):
            if j < len(blurbs):
                persona.personality_blurb = blurbs[j]
            else:
                persona.personality_blurb = (
                    f"A {persona.archetype} consumer who values "
                    f"{'affordability' if persona.price_sensitivity > 0.6 else 'quality'}."
                )

    return personas
