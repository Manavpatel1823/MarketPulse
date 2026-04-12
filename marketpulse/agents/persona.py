import random
from dataclasses import dataclass

ARCHETYPES = {
    "early_adopter": {
        "tech_savviness": (0.7, 1.0),
        "brand_loyalty": (0.2, 0.5),
        "price_sensitivity": (0.1, 0.4),
        "initial_bias": (0.3, 0.8),
    },
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
        "initial_bias": (-0.3, 0.3),
    },
    "brand_loyalist": {
        "tech_savviness": (0.3, 0.7),
        "brand_loyalty": (0.8, 1.0),
        "price_sensitivity": (0.1, 0.4),
        "initial_bias": (0.2, 0.6),
    },
    "eco_conscious": {
        "tech_savviness": (0.4, 0.7),
        "brand_loyalty": (0.3, 0.6),
        "price_sensitivity": (0.2, 0.5),
        "initial_bias": (-0.2, 0.4),
    },
    "tech_enthusiast": {
        "tech_savviness": (0.8, 1.0),
        "brand_loyalty": (0.3, 0.6),
        "price_sensitivity": (0.2, 0.5),
        "initial_bias": (0.4, 0.9),
    },
    "convenience_seeker": {
        "tech_savviness": (0.2, 0.5),
        "brand_loyalty": (0.4, 0.7),
        "price_sensitivity": (0.3, 0.6),
        "initial_bias": (0.0, 0.4),
    },
    "quality_purist": {
        "tech_savviness": (0.5, 0.8),
        "brand_loyalty": (0.5, 0.8),
        "price_sensitivity": (0.1, 0.3),
        "initial_bias": (-0.1, 0.5),
    },
    "trend_follower": {
        "tech_savviness": (0.4, 0.7),
        "brand_loyalty": (0.2, 0.4),
        "price_sensitivity": (0.3, 0.6),
        "initial_bias": (0.1, 0.6),
    },
    "pragmatist": {
        "tech_savviness": (0.4, 0.7),
        "brand_loyalty": (0.3, 0.5),
        "price_sensitivity": (0.4, 0.7),
        "initial_bias": (-0.2, 0.3),
    },
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


def generate_personas(count: int) -> list[Persona]:
    archetypes = list(ARCHETYPES.keys())
    personas = []

    for i in range(count):
        archetype = archetypes[i % len(archetypes)]
        ranges = ARCHETYPES[archetype]

        age_group = random.choice(list(AGE_RANGES.keys()))
        age_lo, age_hi = AGE_RANGES[age_group]

        persona = Persona(
            id=f"agent_{i:03d}",
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
    """Enrich personas with LLM-generated personality blurbs in batches."""
    batch_size = 10
    for i in range(0, len(personas), batch_size):
        batch = personas[i : i + batch_size]
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
