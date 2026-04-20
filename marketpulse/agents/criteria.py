"""Domain-adaptive evaluation criteria — category-aware agent reasoning.

Maps a free-form product category (e.g. "running shoes", "smart earbuds")
to a broad category family, then builds a short criteria paragraph for
injection into agent prompts. Each archetype gets different priority
aspects so a bargain_hunter evaluates "value per comfort-dollar" for shoes
but "value per spec-dollar" for electronics — without rewriting agents.

Zero extra LLM calls. The paragraph rides along in the existing prompts.
"""
from __future__ import annotations


# ── Category families ──────────────────────────────────────────────────
# Each family has keywords (for matching) and 6-8 evaluation aspects.
# Aspect descriptions are one-liners injected into agent prompts.

CATEGORY_FAMILIES: dict[str, dict] = {
    "electronics": {
        "keywords": [
            "earbuds", "headphones", "speaker", "laptop", "phone", "tablet",
            "smartwatch", "wearable", "camera", "monitor", "gaming", "console",
            "tv", "router", "drone", "keyboard", "mouse", "gpu", "cpu",
        ],
        "aspects": {
            "performance": "speed, power, responsiveness for core tasks",
            "build_quality": "materials, durability, craftsmanship",
            "battery": "battery life, charging speed, power efficiency",
            "audio_visual": "sound or display quality for the product type",
            "ecosystem": "compatibility with other devices and platforms",
            "privacy": "data handling, tracking, security features",
            "comfort": "fit, weight, ease of extended use",
            "value": "what you get per dollar vs alternatives",
        },
    },
    "footwear": {
        "keywords": [
            "shoe", "shoes", "sneaker", "boot", "sandal", "running",
            "hiking", "trainer", "cleat", "slipper", "footwear",
        ],
        "aspects": {
            "comfort": "cushioning, arch support, out-of-box feel",
            "durability": "outsole wear, upper longevity, midsole lifespan",
            "fit": "sizing accuracy, width options, break-in period",
            "weight": "heaviness on foot, impact on fatigue over distance",
            "traction": "grip on target surfaces — road, trail, gym, wet",
            "breathability": "ventilation, moisture wicking, heat management",
            "style": "appearance, colorway range, everyday versatility",
            "value": "price relative to lifespan and performance",
        },
    },
    "software": {
        "keywords": [
            "app", "software", "saas", "platform", "tool", "ide",
            "browser", "plugin", "extension", "subscription", "cloud",
        ],
        "aspects": {
            "usability": "learning curve, UI clarity, workflow fit",
            "performance": "speed, responsiveness, resource usage",
            "reliability": "uptime, crash rate, data integrity",
            "features": "breadth and depth of capabilities",
            "integration": "works with existing tools and workflows",
            "privacy": "data handling, permissions, vendor lock-in risk",
            "support": "documentation, community, response time",
            "value": "pricing model fairness relative to alternatives",
        },
    },
    "food_beverage": {
        "keywords": [
            "food", "drink", "beverage", "snack", "coffee", "tea",
            "beer", "wine", "supplement", "protein", "meal", "sauce",
        ],
        "aspects": {
            "taste": "flavor profile, enjoyment, aftertaste",
            "ingredients": "quality, sourcing, transparency",
            "nutrition": "macros, additives, health claims accuracy",
            "convenience": "prep time, portability, shelf life",
            "packaging": "sustainability, portion sizing, freshness",
            "value": "cost per serving vs alternatives",
        },
    },
    "automotive": {
        "keywords": [
            "car", "suv", "truck", "ev", "electric vehicle", "sedan",
            "motorcycle", "scooter", "van", "hybrid",
        ],
        "aspects": {
            "performance": "acceleration, handling, driving feel",
            "range_efficiency": "range (EV) or fuel economy (ICE)",
            "safety": "crash ratings, driver assists, build integrity",
            "comfort": "ride quality, cabin noise, seating, climate",
            "technology": "infotainment, connectivity, OTA updates",
            "reliability": "expected maintenance, brand track record",
            "style": "exterior and interior design, presence",
            "value": "total cost of ownership vs segment competitors",
        },
    },
    "apparel": {
        "keywords": [
            "jacket", "shirt", "pants", "dress", "hoodie", "coat",
            "shorts", "jeans", "sweater", "activewear", "clothing",
        ],
        "aspects": {
            "comfort": "fabric feel, stretch, breathability",
            "fit": "sizing accuracy, silhouette, range of sizes",
            "durability": "wash resistance, pilling, seam quality",
            "style": "design, versatility, trend relevance",
            "materials": "fabric quality, sustainability, sourcing",
            "value": "price relative to quality and longevity",
        },
    },
    "home_appliance": {
        "keywords": [
            "vacuum", "washer", "dryer", "fridge", "oven", "microwave",
            "dishwasher", "air purifier", "heater", "fan", "blender",
            "coffee maker", "robot", "thermostat",
        ],
        "aspects": {
            "performance": "cleaning power, heating speed, core job quality",
            "noise": "operating volume during normal use",
            "energy": "power consumption, efficiency rating",
            "build_quality": "materials, expected lifespan, repairability",
            "ease_of_use": "controls, setup, maintenance burden",
            "smart_features": "app control, automation, voice assistant",
            "value": "upfront cost + running cost vs alternatives",
        },
    },
    "general": {
        "keywords": [],
        "aspects": {
            "quality": "overall build and finish quality",
            "usability": "ease of use, learning curve",
            "durability": "expected lifespan under normal use",
            "design": "aesthetics, ergonomics, form factor",
            "features": "capability breadth and depth",
            "support": "warranty, customer service, community",
            "value": "price justified by what you get",
        },
    },
}


# ── Archetype priorities ───────────────────────────────────────────────
# Each archetype boosts 2 aspects and optionally deprioritizes 1.
# Uses canonical aspect names — silently skips if a family lacks one.

ARCHETYPE_PRIORITIES: dict[str, dict[str, list[str]]] = {
    "early_adopter":      {"boost": ["performance", "features"],    "cut": ["value"]},
    "brand_loyalist":     {"boost": ["ecosystem", "build_quality"], "cut": []},
    "tech_enthusiast":    {"boost": ["performance", "privacy"],     "cut": ["style"]},
    "trend_follower":     {"boost": ["style", "design"],            "cut": ["durability"]},
    "eco_conscious":      {"boost": ["durability", "materials"],    "cut": ["performance"]},
    "convenience_seeker": {"boost": ["comfort", "ease_of_use"],     "cut": ["privacy"]},
    "quality_purist":     {"boost": ["build_quality", "durability"],"cut": ["value"]},
    "skeptic":            {"boost": ["value", "durability"],        "cut": ["style"]},
    "bargain_hunter":     {"boost": ["value"],                      "cut": ["build_quality", "ecosystem"]},
    "pragmatist":         {"boost": ["value", "comfort"],           "cut": ["style"]},
}


def resolve_family(category: str) -> tuple[str, dict[str, str]]:
    """Map a free-form product category to a family name + its aspects.

    Returns ("general", {...}) if no keyword matches.
    """
    if not category:
        return "general", CATEGORY_FAMILIES["general"]["aspects"]
    cat_lower = category.lower()
    for family, config in CATEGORY_FAMILIES.items():
        if family == "general":
            continue
        if any(kw in cat_lower for kw in config["keywords"]):
            return family, config["aspects"]
    return "general", CATEGORY_FAMILIES["general"]["aspects"]


def build_criteria_paragraph(category: str, archetype: str) -> str:
    """Build a short paragraph telling an agent what aspects to evaluate.

    Returns ~80 tokens of natural-language instruction for injection into
    the opinion/debate prompt. The paragraph names 4 aspects (2 boosted
    by archetype + 2 from remaining) with one-line descriptions, and asks
    the agent to rate each 1-10.
    """
    family, aspects = resolve_family(category)
    priors = ARCHETYPE_PRIORITIES.get(archetype, {"boost": ["value"], "cut": []})

    available = list(aspects.keys())
    # Pick boosted aspects that exist in this family
    focus = [a for a in priors["boost"] if a in available][:2]
    depri = set(priors.get("cut", []))
    # Fill to 4 with remaining aspects (skip deprioritized)
    remaining = [a for a in available if a not in focus and a not in depri]
    focus.extend(remaining[: 4 - len(focus)])

    aspect_descriptions = [
        f"{a.replace('_', ' ')} ({aspects[a]})" for a in focus
    ]

    return (
        f"Evaluate this {family.replace('_', ' ')} product on these aspects: "
        f"{', '.join(aspect_descriptions)}. "
        f"Focus especially on {' and '.join(a.replace('_', ' ') for a in focus[:2])}. "
        f"Rate each aspect 1-10 in your response."
    )
