"""50 hand-crafted consumer personas for deterministic, comparable simulations.

Using hardcoded personas means:
  - No LLM enrichment call at startup (saves calls + wait time)
  - Same panel debates every product → results are comparable across runs
  - Richer, more realistic personalities than one-shot LLM generation

Pool: 50 hand-crafted personas across 10 archetypes. Stored 20 positive / 15 neutral
/ 15 negative, but `generate_personas` re-selects from this pool with a 2:3:5
(positive:neutral:negative) ratio to reflect real-world skepticism in
incumbent-dominated markets. For count=25 → 5 pos / 8 neu / 12 neg.

For counts that exceed a tier's pool (e.g. >15 negatives), `_generate_procedural`
pads the deficit while honoring the same 2:3:5 target.
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
]


assert len(HARDCODED_PERSONAS) == 50, f"Expected 50 personas, got {len(HARDCODED_PERSONAS)}"
