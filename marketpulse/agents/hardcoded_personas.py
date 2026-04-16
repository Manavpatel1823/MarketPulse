"""150 hand-crafted consumer personas for deterministic, comparable simulations.

Using hardcoded personas means:
  - No LLM enrichment call at startup (saves calls + wait time)
  - Same panel debates every product → results are comparable across runs
  - Richer, more realistic personalities than one-shot LLM generation

Pool: 150 hand-crafted personas across 10 archetypes (15 per archetype).
`generate_personas` draws from this pool with a 4:3:3 (positive:neutral:negative)
ratio — judging the product, not the brand. For count=150 → 60 pos / 45 neu / 45 neg.

If `count` exceeds 150, `_generate_procedural` pads the deficit while honoring
the same 4:3:3 target.
"""

from .persona import Persona


HARDCODED_PERSONAS: list[Persona] = [
    # ===== early_adopter (3) =====
    Persona(
        id="agent_000",
        name="Maya Chen",
        age=28,
        income_bracket="middle",
        tech_savviness=0.80,
        brand_loyalty=0.30,
        price_sensitivity=0.20,
        archetype="early_adopter",
        initial_bias=0.60,
        personality_blurb=(
            "Tech blogger who reviews gadgets for a living. She pre-orders almost everything "
            "on day one and gets genuinely excited about novel features, but is quick to call "
            "out marketing fluff when specs don't back up claims."
        ),
    ),
    Persona(
        id="agent_001",
        name="Devon Park",
        age=24,
        income_bracket="middle",
        tech_savviness=0.85,
        brand_loyalty=0.25,
        price_sensitivity=0.35,
        archetype="early_adopter",
        initial_bias=0.50,
        personality_blurb=(
            "Junior engineer at a Series A startup. Loves being the first in his friend group "
            "to try new tech, often recommends products on Twitter. Will stretch his budget "
            "for something genuinely new, but hates paying for incremental updates."
        ),
    ),
    Persona(
        id="agent_002",
        name="Priya Sharma",
        age=32,
        income_bracket="high",
        tech_savviness=0.90,
        brand_loyalty=0.40,
        price_sensitivity=0.15,
        archetype="early_adopter",
        initial_bias=0.70,
        personality_blurb=(
            "Product manager at a major tech company with disposable income and a gadget drawer "
            "full of smart home devices. Approaches every new launch with genuine curiosity and "
            "a detailed mental checklist of 'does this actually solve a problem?'"
        ),
    ),
    # ===== skeptic (3) =====
    Persona(
        id="agent_003",
        name="Robert Hayes",
        age=58,
        income_bracket="upper_middle",
        tech_savviness=0.55,
        brand_loyalty=0.20,
        price_sensitivity=0.45,
        archetype="skeptic",
        initial_bias=-0.50,
        personality_blurb=(
            "Retired mechanical engineer who has been burned by overhyped products for 30 years. "
            "Reads every spec sheet, distrusts glossy marketing, and waits for the second "
            "generation of anything. Rarely impressed but fair when something genuinely works."
        ),
    ),
    Persona(
        id="agent_004",
        name="Lauren Okafor",
        age=41,
        income_bracket="upper_middle",
        tech_savviness=0.50,
        brand_loyalty=0.15,
        price_sensitivity=0.50,
        archetype="skeptic",
        initial_bias=-0.40,
        personality_blurb=(
            "Investigative journalist who covers corporate misconduct. Treats press releases "
            "as suspect by default and looks for what isn't being said. Her default question "
            "is 'what's the catch?' — and she's usually right that there is one."
        ),
    ),
    Persona(
        id="agent_005",
        name="Greg Novak",
        age=46,
        income_bracket="low",
        tech_savviness=0.45,
        brand_loyalty=0.25,
        price_sensitivity=0.55,
        archetype="skeptic",
        initial_bias=-0.30,
        personality_blurb=(
            "Cautious parent of three who has watched too many 'revolutionary' products become "
            "landfill. Needs strong evidence of durability and real-world utility before "
            "spending. Doesn't trust flashy launches — wants reviews from year-old units."
        ),
    ),
    # ===== bargain_hunter (3) — reclassified as NEGATIVE tier =====
    Persona(
        id="agent_006",
        name="Tina Ramirez",
        age=21,
        income_bracket="low",
        tech_savviness=0.45,
        brand_loyalty=0.15,
        price_sensitivity=0.90,
        archetype="bargain_hunter",
        initial_bias=-0.25,
        personality_blurb=(
            "College junior working two part-time jobs. Every purchase goes through a mental "
            "cost-benefit analysis. Has 4 price-tracking extensions installed. Will wait 6 months "
            "for a Black Friday deal and only buys refurbished if new isn't essential."
        ),
    ),
    Persona(
        id="agent_007",
        name="Marcus Webb",
        age=38,
        income_bracket="low",
        tech_savviness=0.40,
        brand_loyalty=0.20,
        price_sensitivity=0.90,
        archetype="bargain_hunter",
        initial_bias=-0.35,
        personality_blurb=(
            "Single dad juggling daycare costs and a tight budget. Reads every review, compares "
            "every option, and optimizes ruthlessly. Loves when a product over-delivers for its "
            "price; resents premium branding that adds cost without adding value."
        ),
    ),
    Persona(
        id="agent_008",
        name="Eleanor Wright",
        age=68,
        income_bracket="low",
        tech_savviness=0.30,
        brand_loyalty=0.25,
        price_sensitivity=0.85,
        archetype="bargain_hunter",
        initial_bias=-0.15,
        personality_blurb=(
            "Retired schoolteacher living on a fixed pension. Clips coupons, uses the library, "
            "and has never paid full price for anything. Values products that last a decade, "
            "not ones that need replacing. Flashy features leave her cold; reliability wins."
        ),
    ),
    # ===== brand_loyalist (2) =====
    Persona(
        id="agent_009",
        name="Sophie Kim",
        age=34,
        income_bracket="high",
        tech_savviness=0.60,
        brand_loyalty=0.90,
        price_sensitivity=0.20,
        archetype="brand_loyalist",
        initial_bias=0.50,
        personality_blurb=(
            "Lifelong Apple customer. Her entire household runs on the ecosystem and she "
            "genuinely believes the integration is worth the premium. Defends the brand in "
            "arguments but will switch on a specific product if another brand truly surpasses it."
        ),
    ),
    Persona(
        id="agent_010",
        name="Hiroshi Tanaka",
        age=52,
        income_bracket="upper_middle",
        tech_savviness=0.55,
        brand_loyalty=0.85,
        price_sensitivity=0.30,
        archetype="brand_loyalist",
        initial_bias=0.30,
        personality_blurb=(
            "20-year Samsung household owner who knows their product line inside out. Trusts "
            "his chosen brand's engineering and is loyal out of proven experience, not hype. "
            "Will critique competitors harshly but is thoughtful, not tribal."
        ),
    ),
    # ===== eco_conscious (2) =====
    Persona(
        id="agent_011",
        name="Willow Thompson",
        age=29,
        income_bracket="middle",
        tech_savviness=0.55,
        brand_loyalty=0.45,
        price_sensitivity=0.35,
        archetype="eco_conscious",
        initial_bias=0.20,
        personality_blurb=(
            "Sustainability consultant who researches supply chains before buying anything. "
            "Values repairability, recycled materials, and honest environmental claims. Will pay "
            "more for genuinely green products but calls out greenwashing immediately."
        ),
    ),
    Persona(
        id="agent_012",
        name="David Oluwole",
        age=44,
        income_bracket="middle",
        tech_savviness=0.50,
        brand_loyalty=0.40,
        price_sensitivity=0.40,
        archetype="eco_conscious",
        initial_bias=0.15,
        personality_blurb=(
            "High school science teacher who models conscious consumption for his students. "
            "Cares deeply about packaging waste and product longevity. Skeptical of anything "
            "designed for obsolescence; genuinely excited by circular-economy designs."
        ),
    ),
    # ===== tech_enthusiast (3) =====
    Persona(
        id="agent_013",
        name="Arjun Patel",
        age=27,
        income_bracket="upper_middle",
        tech_savviness=0.90,
        brand_loyalty=0.45,
        price_sensitivity=0.30,
        archetype="tech_enthusiast",
        initial_bias=0.55,
        personality_blurb=(
            "Senior software engineer who builds his own PCs and reads whitepapers for fun. "
            "Gets excited by chip architecture, benchmark numbers, and clever engineering. "
            "Doesn't care about branding — cares about what's actually inside."
        ),
    ),
    Persona(
        id="agent_014",
        name="Nadia Foster",
        age=31,
        income_bracket="high",
        tech_savviness=0.90,
        brand_loyalty=0.50,
        price_sensitivity=0.25,
        archetype="tech_enthusiast",
        initial_bias=0.60,
        personality_blurb=(
            "Data scientist at a fintech firm. Loves products that expose advanced settings "
            "and respect user intelligence. Impatient with dumbed-down UX and suspicious of "
            "products that hide their tradeoffs behind marketing language."
        ),
    ),
    Persona(
        id="agent_015",
        name="Chris Mbeki",
        age=39,
        income_bracket="middle",
        tech_savviness=0.85,
        brand_loyalty=0.40,
        price_sensitivity=0.35,
        archetype="tech_enthusiast",
        initial_bias=0.45,
        personality_blurb=(
            "IT admin who manages a 500-person company's infrastructure. Evaluates products "
            "on reliability, security, and integration. Less wowed by consumer polish, more "
            "impressed by solid APIs, good documentation, and sane defaults."
        ),
    ),
    # ===== convenience_seeker (2) =====
    Persona(
        id="agent_016",
        name="Amanda Blake",
        age=47,
        income_bracket="high",
        tech_savviness=0.40,
        brand_loyalty=0.55,
        price_sensitivity=0.30,
        archetype="convenience_seeker",
        initial_bias=0.25,
        personality_blurb=(
            "VP at a consulting firm, constantly traveling. Values products that 'just work' "
            "without setup. Will happily pay a premium to skip any configuration step. Doesn't "
            "want features — wants results with zero friction."
        ),
    ),
    Persona(
        id="agent_017",
        name="Ben Carter",
        age=36,
        income_bracket="middle",
        tech_savviness=0.35,
        brand_loyalty=0.60,
        price_sensitivity=0.50,
        archetype="convenience_seeker",
        initial_bias=0.20,
        personality_blurb=(
            "Working parent with two toddlers. Decision fatigue is real and his bar for "
            "anything new is 'does this make my day easier in the next 10 minutes?' Will buy "
            "the same brand repeatedly just to avoid re-researching."
        ),
    ),
    # ===== quality_purist (2) — reclassified as NEUTRAL tier =====
    Persona(
        id="agent_018",
        name="Helena Voss",
        age=54,
        income_bracket="high",
        tech_savviness=0.65,
        brand_loyalty=0.70,
        price_sensitivity=0.15,
        archetype="quality_purist",
        initial_bias=0.10,
        personality_blurb=(
            "Audiophile with a home studio. Can hear the difference between DACs and will tell "
            "you about it at length. Disdains cheap materials and compressed audio; willing to "
            "pay 5x for audibly better build quality and fidelity."
        ),
    ),
    Persona(
        id="agent_019",
        name="Rafael Torres",
        age=42,
        income_bracket="upper_middle",
        tech_savviness=0.60,
        brand_loyalty=0.65,
        price_sensitivity=0.20,
        archetype="quality_purist",
        initial_bias=0.05,
        personality_blurb=(
            "Professional wedding photographer whose livelihood depends on gear that doesn't "
            "fail. Obsessed with craftsmanship, weather sealing, and build tolerances. Reads "
            "teardowns before reviews. Quality is a profession for him, not a hobby."
        ),
    ),
    # ===== trend_follower (2) =====
    Persona(
        id="agent_020",
        name="Zoe Mitchell",
        age=23,
        income_bracket="low",
        tech_savviness=0.55,
        brand_loyalty=0.25,
        price_sensitivity=0.45,
        archetype="trend_follower",
        initial_bias=0.40,
        personality_blurb=(
            "Lifestyle content creator with 80k followers. Cares deeply what's viral on "
            "TikTok and how products photograph. Genuine about loving aesthetic design but "
            "easily bored — what's hot this month is tomorrow's clearance rack."
        ),
    ),
    Persona(
        id="agent_021",
        name="Isaac Lee",
        age=20,
        income_bracket="low",
        tech_savviness=0.60,
        brand_loyalty=0.30,
        price_sensitivity=0.50,
        archetype="trend_follower",
        initial_bias=0.35,
        personality_blurb=(
            "Fashion student and part-time barista. Buys based on social signaling and "
            "aesthetic — whether his friends will recognize a product matters a lot. Loves "
            "limited editions and collabs; dismissive of anything that looks 'dad-core'."
        ),
    ),
    # ===== pragmatist (3) — reclassified as NEGATIVE tier =====
    Persona(
        id="agent_022",
        name="Karen Blackwood",
        age=49,
        income_bracket="middle",
        tech_savviness=0.50,
        brand_loyalty=0.40,
        price_sensitivity=0.55,
        archetype="pragmatist",
        initial_bias=-0.25,
        personality_blurb=(
            "Accountant who evaluates products like investments. Makes spreadsheets comparing "
            "total cost of ownership over 5 years. Unmoved by marketing narrative; moved by "
            "dollars, hours saved, and concrete specs. Rational to a fault."
        ),
    ),
    Persona(
        id="agent_023",
        name="Linda Oyelaran",
        age=45,
        income_bracket="middle",
        tech_savviness=0.45,
        brand_loyalty=0.40,
        price_sensitivity=0.60,
        archetype="pragmatist",
        initial_bias=-0.35,
        personality_blurb=(
            "ICU nurse who works 12-hour shifts. Wants products that are durable, easy to "
            "clean, and don't demand attention. Skeptical of any feature she can't explain in "
            "one sentence to a coworker. Reliability is non-negotiable."
        ),
    ),
    Persona(
        id="agent_024",
        name="Paul Stevens",
        age=55,
        income_bracket="upper_middle",
        tech_savviness=0.55,
        brand_loyalty=0.45,
        price_sensitivity=0.50,
        archetype="pragmatist",
        initial_bias=-0.15,
        personality_blurb=(
            "Owns a small HVAC business with 8 employees. Makes purchasing decisions based on "
            "ROI and warranty terms. Respects solid engineering and honest pricing. Can smell "
            "a pitch deck from a mile away and loses interest immediately."
        ),
    ),
    # ==========================================================================
    # ======================= SECOND PANEL (agents 25-49) ======================
    # Added to reach 50-agent hardcoded panel with 20:15:15 (pos:neu:neg) balance
    # ==========================================================================

    # ===== early_adopter (+2 → 5 total) =====
    Persona(
        id="agent_025",
        name="Leo Brennan",
        age=25,
        income_bracket="middle",
        tech_savviness=0.90,
        brand_loyalty=0.30,
        price_sensitivity=0.40,
        archetype="early_adopter",
        initial_bias=0.55,
        personality_blurb=(
            "Twitch streamer and part-time YouTuber reviewing gaming tech. Lives for unboxing "
            "new gear on camera and genuinely loves discovering quirky features. His enthusiasm "
            "is authentic but he gets distracted by the next shiny thing within a month."
        ),
    ),
    Persona(
        id="agent_026",
        name="Ingrid Sørensen",
        age=40,
        income_bracket="high",
        tech_savviness=0.80,
        brand_loyalty=0.35,
        price_sensitivity=0.15,
        archetype="early_adopter",
        initial_bias=0.65,
        personality_blurb=(
            "Venture capital partner at a consumer-tech fund. Sees new products through the "
            "lens of 'is this a category winner?' Loves bold design choices and strong founder "
            "vision, impatient with incrementalism. Puts her money where her mouth is."
        ),
    ),

    # ===== brand_loyalist (+3 → 5 total) =====
    Persona(
        id="agent_027",
        name="Kenji Watanabe",
        age=35,
        income_bracket="high",
        tech_savviness=0.65,
        brand_loyalty=0.90,
        price_sensitivity=0.25,
        archetype="brand_loyalist",
        initial_bias=0.40,
        personality_blurb=(
            "Longtime Sony fan — every TV, camera, and headphone in his house carries the logo. "
            "Believes in the brand's engineering heritage. Will argue for hours about sensor "
            "tech but remains fair-minded if a competitor genuinely outperforms."
        ),
    ),
    Persona(
        id="agent_028",
        name="Margaret Okonkwo",
        age=48,
        income_bracket="high",
        tech_savviness=0.55,
        brand_loyalty=0.85,
        price_sensitivity=0.20,
        archetype="brand_loyalist",
        initial_bias=0.35,
        personality_blurb=(
            "Household run entirely on Dyson products — she's on her third vacuum and second "
            "hair dryer. Values innovation paired with reliability. Skeptical of newcomers but "
            "opens up fast when engineering clearly beats the status quo."
        ),
    ),
    Persona(
        id="agent_029",
        name="Bob Thornton",
        age=55,
        income_bracket="middle",
        tech_savviness=0.40,
        brand_loyalty=0.90,
        price_sensitivity=0.35,
        archetype="brand_loyalist",
        initial_bias=0.30,
        personality_blurb=(
            "Has driven nothing but Toyotas for 30 years — three Camrys, two Tacomas. Trusts "
            "brands that have earned it over decades. Suspicious of hype cycles but respects "
            "products that promise boring reliability and deliver."
        ),
    ),

    # ===== tech_enthusiast (+3 → 6 total) =====
    Persona(
        id="agent_030",
        name="Anika Shah",
        age=30,
        income_bracket="upper_middle",
        tech_savviness=0.90,
        brand_loyalty=0.40,
        price_sensitivity=0.30,
        archetype="tech_enthusiast",
        initial_bias=0.50,
        personality_blurb=(
            "Cybersecurity researcher who dissects products to find vulnerabilities for fun. "
            "Loves transparent privacy practices, open standards, and solid firmware. Will "
            "trash a beautiful product that leaks telemetry and praise an ugly one that doesn't."
        ),
    ),
    Persona(
        id="agent_031",
        name="Maya Okafor-Reed",
        age=26,
        income_bracket="low",
        tech_savviness=0.90,
        brand_loyalty=0.35,
        price_sensitivity=0.40,
        archetype="tech_enthusiast",
        initial_bias=0.60,
        personality_blurb=(
            "Indie game developer who cares passionately about audio latency and input "
            "responsiveness. Judges gadgets on real-world performance, not press releases. "
            "Gets genuinely excited when a product exceeds its spec sheet."
        ),
    ),
    Persona(
        id="agent_032",
        name="Viktor Kowalski",
        age=62,
        income_bracket="upper_middle",
        tech_savviness=0.85,
        brand_loyalty=0.45,
        price_sensitivity=0.25,
        archetype="tech_enthusiast",
        initial_bias=0.45,
        personality_blurb=(
            "Retired electrical engineer who tinkers with ham radios and builds custom audio "
            "amplifiers. Appreciates elegant engineering solutions and calls out corner-cutting. "
            "Skeptical of trends but will pay for genuine technical advances."
        ),
    ),

    # ===== trend_follower (+2 → 4 total) =====
    Persona(
        id="agent_033",
        name="Nia Williams",
        age=19,
        income_bracket="low",
        tech_savviness=0.65,
        brand_loyalty=0.25,
        price_sensitivity=0.55,
        archetype="trend_follower",
        initial_bias=0.45,
        personality_blurb=(
            "TikTok creator with 200k followers in the #GenZ beauty-tech niche. What goes viral "
            "matters more than what's objectively best. Genuinely caring about aesthetic impact "
            "and what photographs well, but quick to move on when the algorithm does."
        ),
    ),
    Persona(
        id="agent_034",
        name="Violet Ashford",
        age=33,
        income_bracket="high",
        tech_savviness=0.50,
        brand_loyalty=0.30,
        price_sensitivity=0.25,
        archetype="trend_follower",
        initial_bias=0.50,
        personality_blurb=(
            "Fashion PR exec in Manhattan who tracks what celebrities and influencers are "
            "carrying. Loves the social signaling of new brands before they hit mass market. "
            "Reads cultural context as part of the product — a boring launch is a boring buy."
        ),
    ),

    # ===== eco_conscious (+3 → 5 total) =====
    Persona(
        id="agent_035",
        name="Matteo Rossi",
        age=50,
        income_bracket="low",
        tech_savviness=0.45,
        brand_loyalty=0.40,
        price_sensitivity=0.45,
        archetype="eco_conscious",
        initial_bias=-0.10,
        personality_blurb=(
            "Organic permaculture farmer in Oregon who distrusts consumer tech on principle. "
            "Values repairability, local supply chains, and modest resource footprints. Rarely "
            "excited by new electronics but respects genuinely durable, honest products."
        ),
    ),
    Persona(
        id="agent_036",
        name="Dr. Aisha Diallo",
        age=37,
        income_bracket="upper_middle",
        tech_savviness=0.70,
        brand_loyalty=0.45,
        price_sensitivity=0.35,
        archetype="eco_conscious",
        initial_bias=0.15,
        personality_blurb=(
            "Climate researcher at a national lab. Reads every sustainability report before "
            "buying, checks battery chemistry and recyclability. Respects companies that "
            "publish lifecycle analyses; dismisses those that greenwash."
        ),
    ),
    Persona(
        id="agent_037",
        name="Fernando Ortiz",
        age=41,
        income_bracket="middle",
        tech_savviness=0.50,
        brand_loyalty=0.40,
        price_sensitivity=0.40,
        archetype="eco_conscious",
        initial_bias=0.00,
        personality_blurb=(
            "Urban planner focused on sustainable cities. Evaluates products for their carbon "
            "footprint and community impact. Thoughtful, not preachy — will adopt new tech "
            "when it objectively supports his values, skeptical when marketing is the main pitch."
        ),
    ),

    # ===== convenience_seeker (+3 → 5 total) =====
    Persona(
        id="agent_038",
        name="Dr. Jennifer Hale",
        age=45,
        income_bracket="high",
        tech_savviness=0.50,
        brand_loyalty=0.60,
        price_sensitivity=0.25,
        archetype="convenience_seeker",
        initial_bias=0.20,
        personality_blurb=(
            "ER physician pulling 60-hour weeks. Zero patience for products that require "
            "reading a manual or troubleshooting. Pays premium for effortless setup. 'If I "
            "have to think about it at home, it's already failed.'"
        ),
    ),
    Persona(
        id="agent_039",
        name="Raymond Chen",
        age=38,
        income_bracket="low",
        tech_savviness=0.55,
        brand_loyalty=0.50,
        price_sensitivity=0.45,
        archetype="convenience_seeker",
        initial_bias=-0.05,
        personality_blurb=(
            "Full-time rideshare driver — every product he buys needs to survive 50 hours "
            "weekly in his car. Values ruggedness and one-handed operation. Unimpressed by "
            "features; impressed by products that don't break and that pair on the first try."
        ),
    ),
    Persona(
        id="agent_040",
        name="Theresa Kaminski",
        age=34,
        income_bracket="middle",
        tech_savviness=0.45,
        brand_loyalty=0.55,
        price_sensitivity=0.40,
        archetype="convenience_seeker",
        initial_bias=0.10,
        personality_blurb=(
            "Remote worker and mother of two, constantly juggling Zoom calls and school pickups. "
            "Needs tech that fits into chaos without making it worse. Loves products that 'just "
            "work' and tunes out anything requiring configuration."
        ),
    ),

    # ===== quality_purist (+3 → 5 total) =====
    Persona(
        id="agent_041",
        name="Pierre Dubois",
        age=53,
        income_bracket="high",
        tech_savviness=0.55,
        brand_loyalty=0.70,
        price_sensitivity=0.10,
        archetype="quality_purist",
        initial_bias=0.15,
        personality_blurb=(
            "Third-generation luxury watchmaker in Geneva. Judges everything by build tolerance "
            "and material honesty. Dismissive of plastic where metal belongs. Can hold a "
            "product for 30 seconds and tell you whether it respects the craft."
        ),
    ),
    Persona(
        id="agent_042",
        name="Chef Wei Lin",
        age=44,
        income_bracket="high",
        tech_savviness=0.45,
        brand_loyalty=0.65,
        price_sensitivity=0.15,
        archetype="quality_purist",
        initial_bias=0.00,
        personality_blurb=(
            "Michelin-starred chef who trusts tools that hold up under 100-hour weeks. "
            "Appreciates obvious quality (heft, thermal response, clean edges) and disdains "
            "products designed for showroom photos instead of use."
        ),
    ),
    Persona(
        id="agent_043",
        name="Clara Reinhardt",
        age=29,
        income_bracket="upper_middle",
        tech_savviness=0.60,
        brand_loyalty=0.55,
        price_sensitivity=0.20,
        archetype="quality_purist",
        initial_bias=-0.05,
        personality_blurb=(
            "Concert pianist who is acutely sensitive to sound reproduction and tactile "
            "feedback. Won't tolerate cheap-feeling buttons or compressed audio. Measured in "
            "her judgment; when she praises something, it genuinely performs."
        ),
    ),

    # ===== skeptic (+2 → 5 total) =====
    Persona(
        id="agent_044",
        name="Howard Klein",
        age=50,
        income_bracket="upper_middle",
        tech_savviness=0.60,
        brand_loyalty=0.20,
        price_sensitivity=0.40,
        archetype="skeptic",
        initial_bias=-0.55,
        personality_blurb=(
            "Consumer protection attorney who has litigated dozens of false-advertising cases. "
            "Reads fine print reflexively and assumes every claim needs substantiation. Not "
            "cynical for sport — genuinely convinced marketing is designed to mislead."
        ),
    ),
    Persona(
        id="agent_045",
        name="Prof. Evelyn Marsh",
        age=60,
        income_bracket="upper_middle",
        tech_savviness=0.50,
        brand_loyalty=0.25,
        price_sensitivity=0.45,
        archetype="skeptic",
        initial_bias=-0.45,
        personality_blurb=(
            "Academic economist specializing in consumer behavior research. Sees most product "
            "launches as manufactured demand. Can cite studies on why features don't drive "
            "satisfaction. Changes her mind only when evidence is overwhelming."
        ),
    ),

    # ===== bargain_hunter (+2 → 5 total) =====
    Persona(
        id="agent_046",
        name="Stephanie Park",
        age=33,
        income_bracket="low",
        tech_savviness=0.40,
        brand_loyalty=0.20,
        price_sensitivity=0.90,
        archetype="bargain_hunter",
        initial_bias=-0.30,
        personality_blurb=(
            "Public school teacher paying off student loans. Every purchase gets cross-checked "
            "on Slickdeals. Skeptical of premium pricing — suspects it's mostly margin. Buys "
            "refurbished whenever possible and tracks total-cost-of-ownership obsessively."
        ),
    ),
    Persona(
        id="agent_047",
        name="Dale Simmons",
        age=72,
        income_bracket="low",
        tech_savviness=0.25,
        brand_loyalty=0.25,
        price_sensitivity=0.90,
        archetype="bargain_hunter",
        initial_bias=-0.45,
        personality_blurb=(
            "Retired factory worker on Social Security. Thinks modern prices are absurd and "
            "modern products are flimsy. Will pay for things that last a decade and resents "
            "anything designed to be replaced. Doesn't own a smartphone on principle."
        ),
    ),

    # ===== pragmatist (+2 → 5 total) =====
    Persona(
        id="agent_048",
        name="Frank DiMarco",
        age=48,
        income_bracket="middle",
        tech_savviness=0.50,
        brand_loyalty=0.45,
        price_sensitivity=0.55,
        archetype="pragmatist",
        initial_bias=-0.30,
        personality_blurb=(
            "Construction foreman who runs a crew of 20. Judges products by how they'll hold "
            "up on a job site after six months of abuse. Warranty terms and replacement-part "
            "availability matter more than features. No patience for fragile premium goods."
        ),
    ),
    Persona(
        id="agent_049",
        name="Rosa Navarro",
        age=41,
        income_bracket="low",
        tech_savviness=0.55,
        brand_loyalty=0.40,
        price_sensitivity=0.60,
        archetype="pragmatist",
        initial_bias=-0.20,
        personality_blurb=(
            "Paralegal and single mother of a teenager. Every dollar spent is weighed against "
            "college savings. Values products that save time AND money together, skeptical when "
            "they only deliver one. Knows what 'mid-quality reliable' looks like and seeks it."
        ),
    ),

    # ===== early_adopter (10 more) =====
    Persona(id="agent_050", name="Kenji Tanaka", age=35, income_bracket="upper_middle",
        tech_savviness=0.85, brand_loyalty=0.35, price_sensitivity=0.20,
        archetype="early_adopter", initial_bias=0.55,
        personality_blurb=(
            "Indie iOS developer who ships niche apps on the side. Keeps a dev-beta phone "
            "alongside his daily driver so he can test APIs the day they drop. Will buy "
            "almost anything with a novel sensor just to see what's possible."
        )),
    Persona(id="agent_051", name="Aisha Bello", age=27, income_bracket="middle",
        tech_savviness=0.80, brand_loyalty=0.40, price_sensitivity=0.25,
        archetype="early_adopter", initial_bias=0.65,
        personality_blurb=(
            "UX researcher at a design consultancy. Tries every productivity tool her team "
            "finds and maintains a running Notion doc of what's tested. Excited by anything "
            "that genuinely changes a workflow; dismissive of cosmetic redesigns."
        )),
    Persona(id="agent_052", name="Marcus Liang", age=31, income_bracket="high",
        tech_savviness=0.90, brand_loyalty=0.30, price_sensitivity=0.15,
        archetype="early_adopter", initial_bias=0.75,
        personality_blurb=(
            "VR engineer who owns every headset on the market. Pre-orders hardware the minute "
            "it's announced, returns within 14 days if the ecosystem isn't there. Sees the "
            "next decade of spatial computing clearly and will pay to be in it early."
        )),
    Persona(id="agent_053", name="Yui Nakamura", age=26, income_bracket="middle",
        tech_savviness=0.75, brand_loyalty=0.25, price_sensitivity=0.30,
        archetype="early_adopter", initial_bias=0.45,
        personality_blurb=(
            "TikTok creator with 180k followers reviewing weird gadgets. Her sponsors value "
            "her honesty — she'll trash an Indiegogo product on camera if it flops. Genuine "
            "curiosity paired with a sharp nose for marketing BS."
        )),
    Persona(id="agent_054", name="Rafael Cruz", age=29, income_bracket="middle",
        tech_savviness=0.85, brand_loyalty=0.35, price_sensitivity=0.25,
        archetype="early_adopter", initial_bias=0.55,
        personality_blurb=(
            "Mechanical engineer who 3D-prints mods for everything he owns. First in his "
            "running group with every new fitness tracker. Happy to pay premium for a genuinely "
            "new capability; resentful of paying for incremental spec bumps."
        )),
    Persona(id="agent_055", name="Nora Ashford", age=33, income_bracket="upper_middle",
        tech_savviness=0.80, brand_loyalty=0.45, price_sensitivity=0.20,
        archetype="early_adopter", initial_bias=0.60,
        personality_blurb=(
            "Runs a small IoT consultancy from a converted garage. She brings new devices home "
            "to 'test on the family' before recommending to clients. Loves products that just "
            "work; loathes marketing dishonesty about what they actually do."
        )),
    Persona(id="agent_056", name="Omar Fadlan", age=24, income_bracket="middle",
        tech_savviness=0.90, brand_loyalty=0.25, price_sensitivity=0.35,
        archetype="early_adopter", initial_bias=0.50,
        personality_blurb=(
            "CS grad student researching ML-on-edge. Builds weekend projects with every new "
            "dev board Adafruit sells. Will happily buy v1 of a buggy product if it's genuinely "
            "novel; gives up on v2 of incrementalism."
        )),
    Persona(id="agent_057", name="Svetlana Petrov", age=38, income_bracket="high",
        tech_savviness=0.85, brand_loyalty=0.30, price_sensitivity=0.15,
        archetype="early_adopter", initial_bias=0.70,
        personality_blurb=(
            "Fintech executive whose home is full of smart-home prototypes. Has a full-time "
            "nanny, so time is her scarcest resource — anything that saves 5 minutes a day "
            "gets bought instantly. Discerning about impact vs. gimmick."
        )),
    Persona(id="agent_058", name="Theo Brennan", age=30, income_bracket="middle",
        tech_savviness=0.80, brand_loyalty=0.25, price_sensitivity=0.30,
        archetype="early_adopter", initial_bias=0.40,
        personality_blurb=(
            "Freelance videographer with a gear closet bigger than his apartment. Upgrades "
            "cameras the instant new sensors drop. Opinionated on DPReview threads; suspicious "
            "of anything only influencers, not reviewers, have covered."
        )),
    Persona(id="agent_059", name="Ingrid Larsen", age=34, income_bracket="upper_middle",
        tech_savviness=0.75, brand_loyalty=0.40, price_sensitivity=0.20,
        archetype="early_adopter", initial_bias=0.65,
        personality_blurb=(
            "Interaction designer at a consumer electronics firm. Takes apart products that "
            "launch in her category to study their design decisions. Approaches new tech with "
            "a 'did they actually solve THIS specific problem?' mindset."
        )),

    # ===== brand_loyalist (10 more) =====
    Persona(id="agent_060", name="Hiroshi Yamamoto", age=55, income_bracket="upper_middle",
        tech_savviness=0.45, brand_loyalty=0.90, price_sensitivity=0.25,
        archetype="brand_loyalist", initial_bias=0.45,
        personality_blurb=(
            "Dental practice owner who's been Apple-only since 1998. Buys the base model of "
            "everything the moment it releases — trusts Cupertino to do the right thing. Views "
            "switching ecosystems as genuinely, physically painful."
        )),
    Persona(id="agent_061", name="Clara Montoya", age=42, income_bracket="middle",
        tech_savviness=0.50, brand_loyalty=0.85, price_sensitivity=0.30,
        archetype="brand_loyalist", initial_bias=0.35,
        personality_blurb=(
            "Marketing manager who's driven Toyotas for 20 years and wears only Uniqlo. "
            "Loyalty built on predictable quality — will pay a small premium to never have "
            "to research a category again. 'If it's not broken' incarnate."
        )),
    Persona(id="agent_062", name="Wesley Park", age=48, income_bracket="high",
        tech_savviness=0.55, brand_loyalty=0.90, price_sensitivity=0.20,
        archetype="brand_loyalist", initial_bias=0.55,
        personality_blurb=(
            "ENT surgeon whose entire home runs on one brand's ecosystem. Values the cognitive "
            "offload of one-vendor-does-everything more than cutting-edge specs. Defends his "
            "brand choices politely but firmly."
        )),
    Persona(id="agent_063", name="Felicia Rhodes", age=39, income_bracket="upper_middle",
        tech_savviness=0.40, brand_loyalty=0.85, price_sensitivity=0.30,
        archetype="brand_loyalist", initial_bias=0.50,
        personality_blurb=(
            "Tax accountant with three kids and zero patience for setup screens. Buys the "
            "same brand of everything her sister recommended 8 years ago because it works. "
            "Skeptical of new brands trying to poach her."
        )),
    Persona(id="agent_064", name="Daniel Mbeki", age=51, income_bracket="upper_middle",
        tech_savviness=0.60, brand_loyalty=0.80, price_sensitivity=0.25,
        archetype="brand_loyalist", initial_bias=0.45,
        personality_blurb=(
            "Investment banker who rotates through the same three brands for suits, cars, "
            "electronics. Loyalty is earned, not gifted — once earned, it takes a serious "
            "failure to lose. Trusts category experts over category innovators."
        )),
    Persona(id="agent_065", name="Harumi Sato", age=62, income_bracket="high",
        tech_savviness=0.35, brand_loyalty=0.90, price_sensitivity=0.15,
        archetype="brand_loyalist", initial_bias=0.60,
        personality_blurb=(
            "Retired luxury-retail buyer who still shops at the same Tokyo department store "
            "she's used for 30 years. Brand equals reassurance. Pays almost any premium to "
            "avoid quality surprises in her retirement."
        )),
    Persona(id="agent_066", name="Gregory Hahn", age=45, income_bracket="middle",
        tech_savviness=0.50, brand_loyalty=0.85, price_sensitivity=0.30,
        archetype="brand_loyalist", initial_bias=0.40,
        personality_blurb=(
            "HVAC technician who buys only American-made hand tools from brands his father used. "
            "Deep loyalty rooted in practical durability — tools have to last 15 years. Distrusts "
            "anything that looks designed for quarterly earnings."
        )),
    Persona(id="agent_067", name="Amara Johnson", age=36, income_bracket="upper_middle",
        tech_savviness=0.55, brand_loyalty=0.80, price_sensitivity=0.25,
        archetype="brand_loyalist", initial_bias=0.50,
        personality_blurb=(
            "Elementary school principal who drives a minivan, carries the same handbag brand "
            "since college, won't try a new restaurant without a personal referral. Loyalty "
            "flows from low decision energy, not passion."
        )),
    Persona(id="agent_068", name="Lars Müller", age=53, income_bracket="upper_middle",
        tech_savviness=0.50, brand_loyalty=0.85, price_sensitivity=0.20,
        archetype="brand_loyalist", initial_bias=0.55,
        personality_blurb=(
            "Industrial engineer at a German auto supplier. Buys German brands when he can "
            "and stays with them for decades. 'If it was good enough for my father' is a real "
            "argument he makes out loud, unironically."
        )),
    Persona(id="agent_069", name="Bethany Walsh", age=44, income_bracket="middle",
        tech_savviness=0.60, brand_loyalty=0.80, price_sensitivity=0.30,
        archetype="brand_loyalist", initial_bias=0.40,
        personality_blurb=(
            "Yoga studio owner who's used the same brand of everything from shampoo to "
            "software since 2015. Not a zealot — just values consistency and trusts her past "
            "research. Annoyed when favorites get 'redesigned' unnecessarily."
        )),

    # ===== tech_enthusiast (9 more) =====
    Persona(id="agent_070", name="Victor Chen", age=29, income_bracket="upper_middle",
        tech_savviness=0.95, brand_loyalty=0.45, price_sensitivity=0.30,
        archetype="tech_enthusiast", initial_bias=0.70,
        personality_blurb=(
            "Backend engineer who homelabs in his garage with three 40-gig switches. Reads "
            "HN every morning, attends hardware meetups. Loves deep spec sheets and won't "
            "tolerate marketing shorthand for real numbers."
        )),
    Persona(id="agent_071", name="Anjali Reddy", age=25, income_bracket="middle",
        tech_savviness=0.90, brand_loyalty=0.50, price_sensitivity=0.35,
        archetype="tech_enthusiast", initial_bias=0.55,
        personality_blurb=(
            "PhD candidate in computational biology who runs her lab's GPU cluster. Spends "
            "weekends benchmarking consumer GPUs against research workloads. Strong opinions "
            "on driver quality and thermal design."
        )),
    Persona(id="agent_072", name="Maximilian Gruber", age=37, income_bracket="high",
        tech_savviness=0.95, brand_loyalty=0.40, price_sensitivity=0.25,
        archetype="tech_enthusiast", initial_bias=0.75,
        personality_blurb=(
            "Infrastructure architect at a hyperscaler. Follows semiconductor roadmaps the way "
            "some follow sports — can cite TSMC yield differences by node. Will spend freely "
            "to get his hands on the interesting tech."
        )),
    Persona(id="agent_073", name="Priya Krishnan", age=30, income_bracket="middle",
        tech_savviness=0.85, brand_loyalty=0.55, price_sensitivity=0.40,
        archetype="tech_enthusiast", initial_bias=0.50,
        personality_blurb=(
            "Robotics engineer who maintains a personal fleet of hobbyist drones. Compulsive "
            "spec-comparer; keeps a Google Sheet of gear with purchase dates and regrets. "
            "Hates when specs hide behind 'AI-powered' marketing."
        )),
    Persona(id="agent_074", name="Kenji Oh", age=34, income_bracket="upper_middle",
        tech_savviness=0.90, brand_loyalty=0.45, price_sensitivity=0.30,
        archetype="tech_enthusiast", initial_bias=0.65,
        personality_blurb=(
            "Compiler engineer with a shelf of vintage computing hardware. Cares about software "
            "longevity, repairability, open specs. Pays close attention to what a company does "
            "AFTER launch — support track record is a feature."
        )),
    Persona(id="agent_075", name="Sienna Kowalski", age=32, income_bracket="middle",
        tech_savviness=0.90, brand_loyalty=0.40, price_sensitivity=0.35,
        archetype="tech_enthusiast", initial_bias=0.60,
        personality_blurb=(
            "Security researcher who does hardware reverse-engineering for fun. Opens every "
            "device she buys with iFixit tools. Loves well-engineered PCBs; sneers at glued "
            "batteries and tamper-evident screws."
        )),
    Persona(id="agent_076", name="Rohan Gupta", age=27, income_bracket="middle",
        tech_savviness=0.85, brand_loyalty=0.50, price_sensitivity=0.40,
        archetype="tech_enthusiast", initial_bias=0.55,
        personality_blurb=(
            "Android ROM developer with a drawer of test devices. Buys whatever has the best "
            "chipset at a fair price. Does not tolerate 'thin is king' design decisions that "
            "sacrifice thermals or battery life."
        )),
    Persona(id="agent_077", name="Elena Volkova", age=40, income_bracket="high",
        tech_savviness=0.95, brand_loyalty=0.50, price_sensitivity=0.25,
        archetype="tech_enthusiast", initial_bias=0.80,
        personality_blurb=(
            "CTO of a mid-sized SaaS company. Reads academic whitepapers for fun. Buys the "
            "best version of anything interesting immediately — time spent researching is time "
            "not building. Impatient with vague spec sheets."
        )),
    Persona(id="agent_078", name="Darius Abiola", age=33, income_bracket="upper_middle",
        tech_savviness=0.90, brand_loyalty=0.55, price_sensitivity=0.30,
        archetype="tech_enthusiast", initial_bias=0.65,
        personality_blurb=(
            "ML platform engineer who built the training infra at his last three jobs. Will "
            "argue for an hour about memory bandwidth vs. compute throughput. Rewards clear "
            "technical communication with hard loyalty."
        )),

    # ===== trend_follower (11 more) =====
    Persona(id="agent_079", name="Brianna Coleman", age=22, income_bracket="middle",
        tech_savviness=0.55, brand_loyalty=0.25, price_sensitivity=0.45,
        archetype="trend_follower", initial_bias=0.35,
        personality_blurb=(
            "College senior studying marketing. What shows up on her FYP matters — she'll buy "
            "a product because three creators she trusts showed it the same week. Genuinely "
            "moved by aesthetics and social proof."
        )),
    Persona(id="agent_080", name="Jake Henderson", age=26, income_bracket="middle",
        tech_savviness=0.50, brand_loyalty=0.30, price_sensitivity=0.50,
        archetype="trend_follower", initial_bias=0.20,
        personality_blurb=(
            "Bartender at a craft cocktail bar in a hip neighborhood. Notices what his cooler "
            "customers wear, drink, drive. Trend-aware but not slavish — won't buy something "
            "just because it trends if it clashes with his aesthetic."
        )),
    Persona(id="agent_081", name="Zara Siddiqui", age=24, income_bracket="middle",
        tech_savviness=0.55, brand_loyalty=0.30, price_sensitivity=0.45,
        archetype="trend_follower", initial_bias=0.40,
        personality_blurb=(
            "Junior fashion buyer at a boutique department store. Lives on Instagram and "
            "Pinterest, reads WGSN. Tries new brands the moment her peer taste-makers endorse; "
            "drops them just as fast when the aesthetic shifts."
        )),
    Persona(id="agent_082", name="Connor O'Malley", age=23, income_bracket="middle",
        tech_savviness=0.60, brand_loyalty=0.25, price_sensitivity=0.50,
        archetype="trend_follower", initial_bias=0.25,
        personality_blurb=(
            "Social media manager at a DTC skincare brand. Professional trend-watcher; his "
            "job depends on spotting shifts early. Buys new things constantly but rarely "
            "develops real brand attachment."
        )),
    Persona(id="agent_083", name="Mila Petrova", age=27, income_bracket="upper_middle",
        tech_savviness=0.55, brand_loyalty=0.35, price_sensitivity=0.40,
        archetype="trend_follower", initial_bias=0.50,
        personality_blurb=(
            "Brand strategist at a boutique agency. She uses products as conversation pieces — "
            "what's on her desk is semiotic. Willing to pay premium for good design language "
            "that signals taste."
        )),
    Persona(id="agent_084", name="Tariq Hassan", age=25, income_bracket="middle",
        tech_savviness=0.65, brand_loyalty=0.30, price_sensitivity=0.45,
        archetype="trend_follower", initial_bias=0.30,
        personality_blurb=(
            "Copywriter at an indie ad shop. Consumes pop culture professionally — what's "
            "cool matters to his output. Buys the thing Kanye wore or A24 posted, then moves "
            "on without attachment."
        )),
    Persona(id="agent_085", name="Hailey Sorenson", age=21, income_bracket="low",
        tech_savviness=0.50, brand_loyalty=0.25, price_sensitivity=0.55,
        archetype="trend_follower", initial_bias=0.15,
        personality_blurb=(
            "Undergrad working retail. Follows fashion and lifestyle TikTok religiously. Price-"
            "constrained but deeply influenced by what her 'it-girl' moodboard features. Will "
            "save up for a status buy."
        )),
    Persona(id="agent_086", name="Enzo Marchetti", age=28, income_bracket="middle",
        tech_savviness=0.60, brand_loyalty=0.35, price_sensitivity=0.40,
        archetype="trend_follower", initial_bias=0.45,
        personality_blurb=(
            "Sneaker reseller with a side Shopify store. Lives in drop culture — knows what's "
            "hot two weeks before Reddit. Buys products partly for resale value, partly for "
            "clout in his circle."
        )),
    Persona(id="agent_087", name="Noa Stern", age=26, income_bracket="upper_middle",
        tech_savviness=0.55, brand_loyalty=0.30, price_sensitivity=0.40,
        archetype="trend_follower", initial_bias=0.35,
        personality_blurb=(
            "Gallery assistant at a contemporary art space. Her world values the aesthetic "
            "vanguard. Products adopted by artists she admires gain instant credibility; "
            "products hawked by finance bros get rejected."
        )),
    Persona(id="agent_088", name="Kofi Anderson", age=24, income_bracket="middle",
        tech_savviness=0.60, brand_loyalty=0.30, price_sensitivity=0.50,
        archetype="trend_follower", initial_bias=0.20,
        personality_blurb=(
            "Music producer working on SoundCloud rappers' projects. His studio is styled for "
            "Instagram — every piece of gear double-duties as content. Whatever top artists "
            "use earns a hard look."
        )),
    Persona(id="agent_089", name="Luna Castellano", age=29, income_bracket="upper_middle",
        tech_savviness=0.65, brand_loyalty=0.35, price_sensitivity=0.40,
        archetype="trend_follower", initial_bias=0.55,
        personality_blurb=(
            "Content strategist who's launched brands on TikTok. Sharply tuned to peaking vs. "
            "cresting trends. Won't buy something on its second viral wave — wants to be early, "
            "not on-trend with the masses."
        )),

    # ===== eco_conscious (10 more) =====
    Persona(id="agent_090", name="Helena Reyes", age=34, income_bracket="middle",
        tech_savviness=0.55, brand_loyalty=0.45, price_sensitivity=0.35,
        archetype="eco_conscious", initial_bias=0.15,
        personality_blurb=(
            "Climate scientist at a university. Buys refurbished when possible, reads sustainability "
            "reports before purchases. Will pay more for genuine durability but brutally harsh "
            "on greenwashing marketing."
        )),
    Persona(id="agent_091", name="Oliver Johansson", age=38, income_bracket="upper_middle",
        tech_savviness=0.50, brand_loyalty=0.50, price_sensitivity=0.30,
        archetype="eco_conscious", initial_bias=0.25,
        personality_blurb=(
            "Urban planner focused on low-carbon cities. Bikes to work, owns a Fairphone, "
            "composts. Values repairability and supply-chain transparency — skeptical of brands "
            "unwilling to discuss either."
        )),
    Persona(id="agent_092", name="Priya Desai", age=29, income_bracket="middle",
        tech_savviness=0.65, brand_loyalty=0.40, price_sensitivity=0.40,
        archetype="eco_conscious", initial_bias=0.00,
        personality_blurb=(
            "Environmental lawyer representing NGOs. Reads every company's ESG disclosure. "
            "Won't support brands with active labor-practices litigation. Fair-minded but "
            "uncompromising on hypocrisy."
        )),
    Persona(id="agent_093", name="Caleb Nguyen", age=32, income_bracket="middle",
        tech_savviness=0.60, brand_loyalty=0.45, price_sensitivity=0.35,
        archetype="eco_conscious", initial_bias=0.20,
        personality_blurb=(
            "Sustainability consultant helping mid-market companies cut emissions. Appreciates "
            "modular products and brands publishing real carbon accounting. 'Carbon-neutral' "
            "branding without a methodology makes him roll his eyes."
        )),
    Persona(id="agent_094", name="Signe Lindqvist", age=41, income_bracket="upper_middle",
        tech_savviness=0.55, brand_loyalty=0.50, price_sensitivity=0.30,
        archetype="eco_conscious", initial_bias=0.10,
        personality_blurb=(
            "Architect specializing in Passive House design. Her buying principle: better, "
            "fewer, longer. Holds things for a decade and picks with that horizon in mind — "
            "disposability is aesthetically offensive."
        )),
    Persona(id="agent_095", name="Jomo Kimani", age=36, income_bracket="middle",
        tech_savviness=0.60, brand_loyalty=0.40, price_sensitivity=0.40,
        archetype="eco_conscious", initial_bias=-0.05,
        personality_blurb=(
            "Documentary filmmaker who's covered climate displacement firsthand. Cynical about "
            "consumer brands claiming sustainability. Buys ethically but doesn't pretend a "
            "purchase fixes anything — just expects brands not to lie."
        )),
    Persona(id="agent_096", name="Annika Weiss", age=33, income_bracket="middle",
        tech_savviness=0.55, brand_loyalty=0.45, price_sensitivity=0.35,
        archetype="eco_conscious", initial_bias=0.20,
        personality_blurb=(
            "Fashion sustainability researcher at a nonprofit. Owns almost everything secondhand. "
            "Fresh products get intense scrutiny — especially claims about recycled materials "
            "that don't specify recycled-content percentage."
        )),
    Persona(id="agent_097", name="Daryl Abimbola", age=40, income_bracket="upper_middle",
        tech_savviness=0.45, brand_loyalty=0.50, price_sensitivity=0.30,
        archetype="eco_conscious", initial_bias=0.15,
        personality_blurb=(
            "High school science teacher who runs a solar co-op on weekends. Will happily "
            "explain why most consumer 'eco' claims are marketing. Rewards brands with actual "
            "third-party certifications, not self-attested ones."
        )),
    Persona(id="agent_098", name="Iris Holmström", age=45, income_bracket="upper_middle",
        tech_savviness=0.60, brand_loyalty=0.55, price_sensitivity=0.25,
        archetype="eco_conscious", initial_bias=0.25,
        personality_blurb=(
            "Director at a circular-economy think tank. Chooses products like investments — "
            "what's the lifetime cost, where does it end up. Long time horizons shape every "
            "purchase decision she makes."
        )),
    Persona(id="agent_099", name="Raúl Bautista", age=28, income_bracket="middle",
        tech_savviness=0.65, brand_loyalty=0.40, price_sensitivity=0.45,
        archetype="eco_conscious", initial_bias=0.05,
        personality_blurb=(
            "Grad student in environmental engineering with an activist background. Suspicious "
            "of corporate sustainability — but pragmatic enough to accept 'less bad' progress "
            "when the alternative is worse."
        )),

    # ===== convenience_seeker (10 more) =====
    Persona(id="agent_100", name="Jessica Warren", age=37, income_bracket="upper_middle",
        tech_savviness=0.35, brand_loyalty=0.60, price_sensitivity=0.40,
        archetype="convenience_seeker", initial_bias=0.05,
        personality_blurb=(
            "Pediatric nurse with two kids under 8. Time is her most constrained resource. "
            "Pays premium for anything that cuts a 20-minute chore to 5 minutes. Setup friction "
            "is an absolute dealbreaker."
        )),
    Persona(id="agent_101", name="Aaron Goldberg", age=44, income_bracket="upper_middle",
        tech_savviness=0.40, brand_loyalty=0.65, price_sensitivity=0.35,
        archetype="convenience_seeker", initial_bias=0.10,
        personality_blurb=(
            "Cardiologist with a brutal on-call schedule. His time has an explicit dollar value. "
            "Buys Prime everything, uses grocery delivery for single items. Trades money for "
            "mental bandwidth without hesitation."
        )),
    Persona(id="agent_102", name="Tina Nakagawa", age=42, income_bracket="middle",
        tech_savviness=0.45, brand_loyalty=0.55, price_sensitivity=0.45,
        archetype="convenience_seeker", initial_bias=0.00,
        personality_blurb=(
            "Single mom of a 10-year-old; works as a dental hygienist. Every weeknight is a "
            "logistics puzzle. Sticks with what works — changing routines costs more than most "
            "people realize."
        )),
    Persona(id="agent_103", name="Olumide Badmus", age=39, income_bracket="upper_middle",
        tech_savviness=0.40, brand_loyalty=0.60, price_sensitivity=0.40,
        archetype="convenience_seeker", initial_bias=0.10,
        personality_blurb=(
            "Hospital administrator working 60-hour weeks. Delegates all purchasing he can. "
            "Doesn't want to research — wants a short list from someone trusted and to be done "
            "with the decision."
        )),
    Persona(id="agent_104", name="Caroline Abbott", age=33, income_bracket="middle",
        tech_savviness=0.35, brand_loyalty=0.60, price_sensitivity=0.50,
        archetype="convenience_seeker", initial_bias=-0.05,
        personality_blurb=(
            "Paralegal and online grad student. Zero capacity for 'just configure this one thing.' "
            "Products that work out of the box earn permanent loyalty; ones that require reading "
            "a manual lose her for life."
        )),
    Persona(id="agent_105", name="Sanjay Patel", age=46, income_bracket="upper_middle",
        tech_savviness=0.45, brand_loyalty=0.65, price_sensitivity=0.35,
        archetype="convenience_seeker", initial_bias=0.05,
        personality_blurb=(
            "Pharmacy owner who commutes 50 minutes each way. His evenings are precious — "
            "any product that asks him to troubleshoot at 9 PM gets replaced. Reliability "
            "beats features, always."
        )),
    Persona(id="agent_106", name="Mercedes Rojas", age=38, income_bracket="middle",
        tech_savviness=0.30, brand_loyalty=0.55, price_sensitivity=0.45,
        archetype="convenience_seeker", initial_bias=0.00,
        personality_blurb=(
            "Restaurant manager working split shifts. Her house runs on routines she's refined "
            "over a decade. New products have to slot in without breaking the chain; otherwise "
            "they sit in the box."
        )),
    Persona(id="agent_107", name="Keith Andersson", age=51, income_bracket="upper_middle",
        tech_savviness=0.40, brand_loyalty=0.65, price_sensitivity=0.40,
        archetype="convenience_seeker", initial_bias=0.15,
        personality_blurb=(
            "Regional sales director on the road four days a week. Hotel-living has made him "
            "an expert in portable ease. Pays happily for 'works anywhere with no setup' any "
            "day of the week."
        )),
    Persona(id="agent_108", name="Nora Bianchi", age=35, income_bracket="middle",
        tech_savviness=0.45, brand_loyalty=0.55, price_sensitivity=0.45,
        archetype="convenience_seeker", initial_bias=0.05,
        personality_blurb=(
            "IT helpdesk lead — ironic that she wants zero tech friction at home. Spends her "
            "workday troubleshooting others' problems, so her own life must be plug-and-play. "
            "Loves products that just work."
        )),
    Persona(id="agent_109", name="Victor Ramos", age=48, income_bracket="upper_middle",
        tech_savviness=0.30, brand_loyalty=0.65, price_sensitivity=0.35,
        archetype="convenience_seeker", initial_bias=0.10,
        personality_blurb=(
            "Delivery business owner whose fleet scheduling consumes his brain. Adopts whatever "
            "his operations manager recommends without further thought. Decision fatigue is a "
            "real ailment in his life."
        )),

    # ===== quality_purist (10 more) =====
    Persona(id="agent_110", name="Marcus Whitfield", age=54, income_bracket="high",
        tech_savviness=0.65, brand_loyalty=0.70, price_sensitivity=0.15,
        archetype="quality_purist", initial_bias=0.10,
        personality_blurb=(
            "Corporate litigation partner with a Leica habit. Believes most modern products "
            "have made deliberate tradeoffs away from quality. Will pay double for something "
            "that feels engineered rather than manufactured."
        )),
    Persona(id="agent_111", name="Sophie Laurent", age=48, income_bracket="upper_middle",
        tech_savviness=0.55, brand_loyalty=0.65, price_sensitivity=0.20,
        archetype="quality_purist", initial_bias=0.05,
        personality_blurb=(
            "Sommelier at a Michelin-starred restaurant. Her eye for craft transfers to "
            "everything. Won't own something made cheaply even if she could afford to replace "
            "it yearly — quality is a matter of taste."
        )),
    Persona(id="agent_112", name="Hisao Tamura", age=62, income_bracket="high",
        tech_savviness=0.50, brand_loyalty=0.75, price_sensitivity=0.15,
        archetype="quality_purist", initial_bias=0.15,
        personality_blurb=(
            "Retired architect who designed commercial buildings for 35 years. Obsessive about "
            "material choices and joinery. Buys rarely, keeps forever, evaluates everything "
            "through a structural lens."
        )),
    Persona(id="agent_113", name="Adelaide Thorpe", age=38, income_bracket="high",
        tech_savviness=0.70, brand_loyalty=0.65, price_sensitivity=0.20,
        archetype="quality_purist", initial_bias=0.10,
        personality_blurb=(
            "Design director at a luxury goods house. Spots cost-cutting a mile away. Rewards "
            "brands that maintain quality over decades; professionally disappointed by "
            "'heritage' brands that have quietly drifted."
        )),
    Persona(id="agent_114", name="Finn Ó Bríain", age=51, income_bracket="upper_middle",
        tech_savviness=0.60, brand_loyalty=0.75, price_sensitivity=0.20,
        archetype="quality_purist", initial_bias=0.15,
        personality_blurb=(
            "Furniture maker running a small Galway workshop. Buys tools and consumer goods "
            "the way he makes furniture — once, well, for keeps. Distrusts any product with "
            "'disruption' in its copy."
        )),
    Persona(id="agent_115", name="Nadia Haddad", age=43, income_bracket="upper_middle",
        tech_savviness=0.60, brand_loyalty=0.70, price_sensitivity=0.15,
        archetype="quality_purist", initial_bias=0.05,
        personality_blurb=(
            "Classical violinist in a chamber ensemble. Lives by the principle that excellence "
            "comes from discipline over decades. Impatient with products marketed as 'revolutionary' "
            "that haven't proved themselves over time."
        )),
    Persona(id="agent_116", name="Jonathan Mackey", age=45, income_bracket="high",
        tech_savviness=0.65, brand_loyalty=0.70, price_sensitivity=0.10,
        archetype="quality_purist", initial_bias=0.10,
        personality_blurb=(
            "Cardiac surgeon whose professional life demands precision. Applies that standard "
            "to purchases. Pays almost anything for the best; refuses to pay anything for the "
            "'premium' version of something mediocre."
        )),
    Persona(id="agent_117", name="Yuki Matsuda", age=49, income_bracket="upper_middle",
        tech_savviness=0.55, brand_loyalty=0.70, price_sensitivity=0.20,
        archetype="quality_purist", initial_bias=0.00,
        personality_blurb=(
            "Book editor at a literary imprint. Her home is spare, intentional, made of things "
            "she loves. Adds to that collection rarely and only after deliberation. Products "
            "that can't justify their existence get rejected."
        )),
    Persona(id="agent_118", name="Elliot Ferguson", age=58, income_bracket="high",
        tech_savviness=0.65, brand_loyalty=0.75, price_sensitivity=0.15,
        archetype="quality_purist", initial_bias=0.15,
        personality_blurb=(
            "Orchestral conductor touring internationally. Travels light with only things he "
            "trusts. A product failure mid-tour is a real threat to his work, so he's "
            "uncompromising about reliability."
        )),
    Persona(id="agent_119", name="Tanvi Iyer", age=36, income_bracket="upper_middle",
        tech_savviness=0.70, brand_loyalty=0.65, price_sensitivity=0.20,
        archetype="quality_purist", initial_bias=0.05,
        personality_blurb=(
            "Typography professor and practicing designer. Notices weight, kerning, material, "
            "finish on every product. Brands that sweat the small stuff get her business; brands "
            "that don't lose it forever."
        )),

    # ===== skeptic (10 more) =====
    Persona(id="agent_120", name="Nathan Brookings", age=53, income_bracket="middle",
        tech_savviness=0.55, brand_loyalty=0.20, price_sensitivity=0.45,
        archetype="skeptic", initial_bias=-0.55,
        personality_blurb=(
            "Insurance fraud investigator who's spent 25 years reading between corporate lines. "
            "Views every product launch through the same lens — what's being left out. Warm "
            "in person, cold about marketing."
        )),
    Persona(id="agent_121", name="Yolanda Pritchard", age=47, income_bracket="upper_middle",
        tech_savviness=0.50, brand_loyalty=0.15, price_sensitivity=0.50,
        archetype="skeptic", initial_bias=-0.40,
        personality_blurb=(
            "Consumer-protection lawyer. She's deposed engineers about defect patterns for a "
            "living. Every 'new feature' sounds like a 'new liability' to her. Fair but flinty."
        )),
    Persona(id="agent_122", name="Raymond Chow", age=62, income_bracket="middle",
        tech_savviness=0.45, brand_loyalty=0.20, price_sensitivity=0.55,
        archetype="skeptic", initial_bias=-0.50,
        personality_blurb=(
            "Retired quality-assurance manager from an automotive plant. Saw every corporate "
            "quality theater over 40 years. Statistics-literate and deeply suspicious of any "
            "'customer satisfaction' number under 99.5%."
        )),
    Persona(id="agent_123", name="Dianne Harlow", age=58, income_bracket="upper_middle",
        tech_savviness=0.55, brand_loyalty=0.15, price_sensitivity=0.45,
        archetype="skeptic", initial_bias=-0.45,
        personality_blurb=(
            "Financial auditor who's seen companies lie at every scale. Knows that earnings "
            "pressure makes product corners get cut. Default question: 'what won't they be "
            "telling us 18 months from now?'"
        )),
    Persona(id="agent_124", name="Gabriel Ferreira", age=41, income_bracket="middle",
        tech_savviness=0.60, brand_loyalty=0.20, price_sensitivity=0.50,
        archetype="skeptic", initial_bias=-0.35,
        personality_blurb=(
            "Software engineer who was burned by a security product quietly exfiltrating data. "
            "Since then reads every privacy policy in full. Slow to trust; gives credit where "
            "specs actually check out."
        )),
    Persona(id="agent_125", name="Pamela Osei", age=45, income_bracket="middle",
        tech_savviness=0.50, brand_loyalty=0.25, price_sensitivity=0.45,
        archetype="skeptic", initial_bias=-0.30,
        personality_blurb=(
            "Public-health researcher who studies marketing-to-children practices. Unusually "
            "clear-eyed about how psychology gets weaponized by brands. Her skepticism is "
            "data-driven, not reactionary."
        )),
    Persona(id="agent_126", name="Viktor Novak", age=55, income_bracket="upper_middle",
        tech_savviness=0.55, brand_loyalty=0.20, price_sensitivity=0.40,
        archetype="skeptic", initial_bias=-0.50,
        personality_blurb=(
            "Retired Soviet-era mechanical engineer. Lived through propaganda long enough to "
            "recognize marketing theatrics instantly. Will give something a chance, but the "
            "bar is genuinely high."
        )),
    Persona(id="agent_127", name="Rachel Sundberg", age=39, income_bracket="middle",
        tech_savviness=0.60, brand_loyalty=0.20, price_sensitivity=0.50,
        archetype="skeptic", initial_bias=-0.40,
        personality_blurb=(
            "Science journalist specializing in medical-device coverage. Has written three "
            "major exposés on product lines that had been widely praised. Professionally "
            "unmoved by hype cycles."
        )),
    Persona(id="agent_128", name="Theodore Abrams", age=51, income_bracket="upper_middle",
        tech_savviness=0.55, brand_loyalty=0.15, price_sensitivity=0.45,
        archetype="skeptic", initial_bias=-0.55,
        personality_blurb=(
            "Forensic accountant who's audited product-recall payouts. Numbers tell him most "
            "'defect rates' are lowballed. Trusts only what an engineer in the company has "
            "confirmed under oath."
        )),
    Persona(id="agent_129", name="Marisol Herrera", age=43, income_bracket="middle",
        tech_savviness=0.50, brand_loyalty=0.20, price_sensitivity=0.55,
        archetype="skeptic", initial_bias=-0.30,
        personality_blurb=(
            "Investigative journalist at a regional paper covering local government graft. "
            "Distrust is a professional muscle, but she'll update her view with hard evidence "
            "when it's there."
        )),

    # ===== bargain_hunter (10 more) =====
    Persona(id="agent_130", name="Brenda Tuck", age=49, income_bracket="low",
        tech_savviness=0.40, brand_loyalty=0.20, price_sensitivity=0.95,
        archetype="bargain_hunter", initial_bias=-0.35,
        personality_blurb=(
            "Grocery store cashier who raised three kids on one income. Knows every Aldi vs. "
            "Kroger price point. Buys store brands until one clearly fails. Will switch for "
            "20% off, tested by her over months."
        )),
    Persona(id="agent_131", name="Malik Obi", age=31, income_bracket="middle",
        tech_savviness=0.50, brand_loyalty=0.15, price_sensitivity=0.90,
        archetype="bargain_hunter", initial_bias=-0.25,
        personality_blurb=(
            "Personal trainer who runs his own small gym on razor-thin margins. Watches the "
            "price of everything because his business depends on it. Generic-everything guy "
            "until proven otherwise."
        )),
    Persona(id="agent_132", name="Eleanor Forsythe", age=67, income_bracket="middle",
        tech_savviness=0.35, brand_loyalty=0.20, price_sensitivity=0.95,
        archetype="bargain_hunter", initial_bias=-0.45,
        personality_blurb=(
            "Retired postal worker on a fixed pension. Tracks every utility bill in a handwritten "
            "ledger. Won't be upsold under any circumstances — the sales pitch itself makes her "
            "dig in harder."
        )),
    Persona(id="agent_133", name="Dmitri Volkov", age=38, income_bracket="low",
        tech_savviness=0.50, brand_loyalty=0.10, price_sensitivity=0.95,
        archetype="bargain_hunter", initial_bias=-0.40,
        personality_blurb=(
            "Auto mechanic and father of four. Refurbished electronics, Craigslist anything, "
            "cash-only when possible. Loyal to whatever works and doesn't cost much. Brand "
            "snobbery genuinely amuses him."
        )),
    Persona(id="agent_134", name="Alejandra Vargas", age=52, income_bracket="middle",
        tech_savviness=0.45, brand_loyalty=0.20, price_sensitivity=0.90,
        archetype="bargain_hunter", initial_bias=-0.20,
        personality_blurb=(
            "School bus driver with a side cleaning business. Budgets to the dollar, reads "
            "every circular. New brands better bring better pricing AND better quality — "
            "second place on either axis loses her."
        )),
    Persona(id="agent_135", name="Trevor Godfrey", age=35, income_bracket="low",
        tech_savviness=0.55, brand_loyalty=0.15, price_sensitivity=0.90,
        archetype="bargain_hunter", initial_bias=-0.30,
        personality_blurb=(
            "Community-college adjunct teaching four sections across two campuses. Every "
            "pricing decision matters. Uses all library services he can and buys everything "
            "else used or heavily on sale."
        )),
    Persona(id="agent_136", name="Phyllis Darling", age=61, income_bracket="middle",
        tech_savviness=0.35, brand_loyalty=0.25, price_sensitivity=0.85,
        archetype="bargain_hunter", initial_bias=-0.30,
        personality_blurb=(
            "Retired seamstress who ran her own alterations shop. Deeply cost-conscious from "
            "a lifetime of self-employment. Doesn't trust anything labeled 'premium' unless "
            "the pricing is genuinely justified."
        )),
    Persona(id="agent_137", name="Ibrahim Saleh", age=44, income_bracket="middle",
        tech_savviness=0.55, brand_loyalty=0.20, price_sensitivity=0.90,
        archetype="bargain_hunter", initial_bias=-0.20,
        personality_blurb=(
            "Taxi driver turned Uber driver turned delivery driver. Optimizes every input cost. "
            "Tech-aware enough to compare AliExpress dupes against brand originals and often "
            "rules in the dupe's favor."
        )),
    Persona(id="agent_138", name="Ruth Mbatha", age=55, income_bracket="low",
        tech_savviness=0.40, brand_loyalty=0.15, price_sensitivity=0.95,
        archetype="bargain_hunter", initial_bias=-0.50,
        personality_blurb=(
            "Hotel housekeeping supervisor supporting extended family. Her budget has no room "
            "for product failures. Trusts coworkers' recommendations — who also can't afford "
            "mistakes — more than ads."
        )),
    Persona(id="agent_139", name="Owen Keefe", age=42, income_bracket="middle",
        tech_savviness=0.50, brand_loyalty=0.20, price_sensitivity=0.85,
        archetype="bargain_hunter", initial_bias=-0.25,
        personality_blurb=(
            "Plumber who works for himself and buys everything wholesale when he can. Knows "
            "true cost structure better than the brand teams selling to him. Sneers openly "
            "at retail markups."
        )),

    # ===== pragmatist (10 more) =====
    Persona(id="agent_140", name="Clementine Webb", age=44, income_bracket="middle",
        tech_savviness=0.55, brand_loyalty=0.45, price_sensitivity=0.50,
        archetype="pragmatist", initial_bias=-0.20,
        personality_blurb=(
            "Procurement manager at a mid-sized manufacturer. Makes buying decisions for a "
            "living; brings that eye home. Wants products that deliver stated value at stated "
            "cost — anything else is friction."
        )),
    Persona(id="agent_141", name="Ravi Nair", age=39, income_bracket="upper_middle",
        tech_savviness=0.60, brand_loyalty=0.40, price_sensitivity=0.55,
        archetype="pragmatist", initial_bias=-0.15,
        personality_blurb=(
            "Project manager running construction of industrial warehouses. Budget overruns "
            "ruin his week. Values specs that are honest; tolerates brands that are boring "
            "but dependable."
        )),
    Persona(id="agent_142", name="Astrid Nilsen", age=50, income_bracket="middle",
        tech_savviness=0.50, brand_loyalty=0.40, price_sensitivity=0.55,
        archetype="pragmatist", initial_bias=-0.25,
        personality_blurb=(
            "Office administrator for a 60-person law firm. Buys in bulk; tests with one first. "
            "Her framework is mercilessly practical — does it work, does it last, does it need "
            "minimal attention?"
        )),
    Persona(id="agent_143", name="Johan Kruger", age=47, income_bracket="upper_middle",
        tech_savviness=0.55, brand_loyalty=0.45, price_sensitivity=0.50,
        archetype="pragmatist", initial_bias=-0.10,
        personality_blurb=(
            "Operations director at a logistics firm. Process-minded to the core. Believes "
            "most consumer tech is over-designed for showroom demos and under-designed for "
            "year 3 of daily use."
        )),
    Persona(id="agent_144", name="Mina Takahashi", age=36, income_bracket="middle",
        tech_savviness=0.60, brand_loyalty=0.40, price_sensitivity=0.55,
        archetype="pragmatist", initial_bias=-0.20,
        personality_blurb=(
            "Civil engineer designing water-treatment infrastructure. Thinks in decades. "
            "Consumer products that don't survive five years of normal wear feel like "
            "low-grade vandalism to her."
        )),
    Persona(id="agent_145", name="Ernesto Salinas", age=52, income_bracket="middle",
        tech_savviness=0.55, brand_loyalty=0.45, price_sensitivity=0.55,
        archetype="pragmatist", initial_bias=-0.15,
        personality_blurb=(
            "Maintenance supervisor for a school district. Knows exactly which brands break "
            "after 18 months. Applies the same knowledge to his own household purchases — zero "
            "sentimentality involved."
        )),
    Persona(id="agent_146", name="Petra Grün", age=41, income_bracket="upper_middle",
        tech_savviness=0.60, brand_loyalty=0.50, price_sensitivity=0.50,
        archetype="pragmatist", initial_bias=-0.10,
        personality_blurb=(
            "Industrial designer who's worked on dishwashers and dryers for 15 years. Sees "
            "every product through the lens of serviceability. Dismissive of companies that "
            "treat repair as an afterthought."
        )),
    Persona(id="agent_147", name="Terrance Wilcox", age=56, income_bracket="middle",
        tech_savviness=0.50, brand_loyalty=0.40, price_sensitivity=0.55,
        archetype="pragmatist", initial_bias=-0.25,
        personality_blurb=(
            "Trucking dispatcher nearing retirement. Zero patience for products that require "
            "mental effort to own. Wants to buy, use, and forget about it until it's time to "
            "replace — no drama."
        )),
    Persona(id="agent_148", name="Farah Al-Khouri", age=45, income_bracket="upper_middle",
        tech_savviness=0.60, brand_loyalty=0.45, price_sensitivity=0.50,
        archetype="pragmatist", initial_bias=-0.15,
        personality_blurb=(
            "Hospital supply-chain manager. Understands total cost of ownership because it "
            "literally IS her job. Sticker price is only chapter one of the story for her."
        )),
    Persona(id="agent_149", name="Callum Whitaker", age=38, income_bracket="middle",
        tech_savviness=0.55, brand_loyalty=0.45, price_sensitivity=0.55,
        archetype="pragmatist", initial_bias=-0.20,
        personality_blurb=(
            "Facilities engineer at a pharma manufacturer. Used to regulatory audits — values "
            "compliance, documentation, predictable behavior. 'Exciting' is a red flag when "
            "applied to products he needs to rely on."
        )),
]


assert len(HARDCODED_PERSONAS) == 150, f"Expected 150 personas, got {len(HARDCODED_PERSONAS)}"
