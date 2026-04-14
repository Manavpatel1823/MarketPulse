# MarketPulse - AI Multi-Agent Market Simulation

Simulate 100+ diverse consumer personas debating your product before launch. Agents form opinions, argue with each other, shift sentiments, and produce a marketing intelligence report that reveals blind spots humans miss.

## How It Works

```
User Input (product info)
        |
        v
[Persona Generation] --> 10 archetypes, LLM-enriched personalities
        |
        v
[Opinion Phase] --> Each agent reads product info, forms opinion via LLM
        |
        v
[Debate Rounds] --> Adversarial pairing (most positive vs most negative)
   |                 Agents argue, shift sentiments, some get converted
   | (repeats N rounds)
        |
        v
[Report Generation] --> Reasoning agent analyzes all data
        |
        v
[Marketing Report] --> Executive summary, risks, opportunities, recommendations
```

## Quick Start

### Prerequisites
- Python 3.12+
- Ollama installed and running

### Setup
```bash
# Install Ollama (macOS)
brew install ollama
brew services start ollama
ollama pull qwen2.5:7b

# Install Python dependencies
pip install -r requirements.txt

# Run simulation
python3 run.py
```

### Configuration (.env)
```
OLLAMA_MODEL=qwen2.5:7b
OLLAMA_BASE_URL=http://localhost:11434
BACKEND=ollama
ROUNDS=3
AGENT_COUNT=3
BATCH_SIZE=3
```

- `AGENT_COUNT` - Number of consumer agents (start with 3-10, scale to 100+)
- `ROUNDS` - Number of debate rounds
- `BATCH_SIZE` - Concurrent LLM calls (keep 3-5 for 8GB RAM)
- `BACKEND` - "ollama" for local or "gemini" for Google API

### Stop Ollama (free up ~5GB RAM)
```bash
brew services stop ollama
```

---

## CLI Commands

`run.py` takes a product name (positional) plus optional flags that control how product context is sourced and how the simulation starts.

### Running a Simulation

| Command | What it does |
|---------|--------------|
| `python3 run.py "Fairphone 5"` | Default run. Checks the research **gate** (is web research worthwhile?), then uses DuckDuckGo to pull snippets, builds `SharedMemory`, and pauses for a confirmation prompt before the simulation starts. |
| `python3 run.py "MyProduct" --from-file brief.txt` | Skip web search for the product. One LLM call compresses your brief into `ProductInfo` + competitors + signals. The inferred **category** is then web-searched for real competitors. Use for unreleased / pre-launch / internal products with no web footprint. |
| `python3 run.py "MyProduct" --from-url https://example.com/product` | Same as `--from-file` but fetches a URL, strips HTML, then compresses. Good for official product pages, press releases, or Wikipedia entries. |
| `python3 run.py "MyProduct" --no-research` | Fully offline. No LLM research at all — uses a deterministic stub product. Fastest path for testing the simulation engine itself. |
| `python3 run.py "Fairphone 5" --force-research` | Bypass the research gate and always run the web search, even if the gate would have skipped it. |
| `python3 run.py "Fairphone 5" -y` | Auto-confirm the "proceed with these findings?" prompt. Use in CI or scripting. |

Flags can be combined, e.g. `python3 run.py "Fairphone 5" --force-research -y`.

### Inspecting Past Runs (no simulation)

These read from Postgres (Phase 3 persistence layer) — no LLM calls.

| Command | What it does |
|---------|--------------|
| `python3 run.py --list` | Show recent runs: ID, product, agent count, mean sentiment, timestamp. Incomplete (crashed mid-run) entries are flagged. |
| `python3 run.py --show 7` | Full detail of run #7: product info, signals, sentiment distribution, concerns, final report. |
| `python3 run.py --compare 3 7` | Side-by-side comparison of two or more run IDs. Useful for A/B comparing product variants or re-runs. |

### Flag Reference

| Flag | Purpose |
|------|---------|
| `--from-file PATH` | Use a local text file as the product source (skips product-name web search). |
| `--from-url URL` | Fetch a URL and use its text content as the product source. |
| `--no-research` | Disable all LLM-driven research; run with a minimal stub product. |
| `--force-research` | Skip the gate's "is research worthwhile?" pre-check. |
| `-y` | Auto-confirm prompts (non-interactive). |
| `--list` | List past runs from the database, then exit. |
| `--show ID` | Show a single past run in detail, then exit. |
| `--compare ID [ID ...]` | Compare 2+ past runs, then exit. |

---

## Project Structure & File Guide

```
MarketPulse/
|
|-- run.py                              # Entry point
|
|-- marketpulse/
|   |-- config.py                       # Settings loader
|   |
|   |-- llm/                            # LLM backends
|   |   |-- base.py                     # Abstract interface
|   |   |-- ollama_backend.py           # Local Ollama
|   |   |-- gemini_backend.py           # Google Gemini API
|   |
|   |-- memory/                         # Data structures
|   |   |-- shared.py                   # Product info (all agents see this)
|   |   |-- individual.py              # Per-agent memory
|   |
|   |-- agents/                         # Agent system
|   |   |-- persona.py                  # Personality generation
|   |   |-- agent.py                    # Core agent logic
|   |   |-- pool.py                     # Batch execution
|   |
|   |-- simulation/                     # Simulation logic
|   |   |-- sentiment.py                # Persuasion math
|   |   |-- interaction.py              # Agent pairing
|   |   |-- engine.py                   # Main orchestrator
|   |
|   |-- reporting/                      # Output
|   |   |-- analyzer.py                 # Report generation
|   |
|   |-- research/                       # (Phase 2 - web search)
|   |-- storage/                        # (Phase 3 - SQLite persistence)
```

---

## File-by-File Explanation

### `run.py` - Entry Point
**What:** The main script you execute. Creates settings, initializes Ollama backend, sets up product info, and kicks off the simulation.
**Why needed:** Every application needs a single entry point. This keeps startup logic (what product to simulate, which LLM to use) separate from the simulation engine itself.
**Why this approach:** Using `asyncio.run()` because all LLM calls are async I/O operations. Product info is hardcoded for now; Phase 2 adds user input and web search.

---

### `marketpulse/config.py` - Settings Loader
**What:** Loads configuration from `.env` file into a typed Python object using Pydantic.
**Why needed:** Centralizes all configuration (model name, agent count, batch size, API keys) in one place. Change `.env` to switch between Ollama and Gemini without touching code.
**Why Pydantic:** Gives type validation, default values, and automatic `.env` parsing. If you set `AGENT_COUNT=abc` it errors immediately instead of crashing mid-simulation.

---

### `marketpulse/llm/base.py` - LLM Abstract Interface
**What:** Defines `LLMBackend` abstract class with two methods: `generate()` (text) and `generate_json()` (structured JSON).
**Why needed:** The simulation engine doesn't care if you're using Ollama, Gemini, or any future LLM. It only calls `generate()` and `generate_json()`. This lets you swap backends by changing one line in `.env`.
**Why two methods:** Agents need structured JSON for opinions/debates (parseable data), but the final report needs free-form text (readable prose).

---

### `marketpulse/llm/ollama_backend.py` - Local Ollama Backend
**What:** Implements `LLMBackend` using Ollama's async client. Sends prompts to locally running Qwen 2.5:7b model.
**Why needed:** Local inference = free, unlimited, no rate limits, no internet required. On Mac Mini M3 with 8GB RAM, Qwen 2.5:7b (4.7GB Q4 quantized) fits in memory.
**Why Ollama:** Simplest way to run open-source models locally. One command to install, one command to pull a model. The `AsyncClient` lets us queue multiple requests without blocking.

### `marketpulse/memory/shared.py` - Shared Memory (Product Info)
**What:** Dataclasses for product info, competitor info, research findings, and a SharedMemory container. Has `get_agent_briefing()` that compresses everything into a text summary for agent prompts.
**Why needed:** All agents need the same product context. Instead of passing raw product data into every prompt, SharedMemory pre-formats it into a concise briefing. This keeps prompts under 600 tokens (critical for fast inference on 7B models).
**Why dataclasses:** Lightweight, no ORM overhead. The data is created once and read many times during the simulation.

---

### `marketpulse/memory/individual.py` - Individual Agent Memory
**What:** Per-agent memory tracking: opinions formed, debate interactions, sentiment history, and conversion events. Provides `get_context_for_prompt()` to inject recent history into prompts.
**Why needed:** Each agent needs to remember their past opinions and recent debates. Without memory, agents would give the same response every round regardless of what happened. The `get_context_for_prompt()` method only injects the latest opinion and last 2 interactions to keep prompts small.
**Why not a database:** During simulation, agent memory is hot state accessed every LLM call. In-memory dataclasses are instant. SQLite persistence comes in Phase 3 for saving results after simulation ends.

---

### `marketpulse/agents/persona.py` - Personality Generation
**What:** Defines 10 consumer archetypes (early_adopter, skeptic, bargain_hunter, etc.) with trait ranges. Procedurally generates diverse personas with randomized demographics, then uses a single batched LLM call to create personality blurbs for groups of 10.
**Why needed:** The whole point of the simulation is diverse perspectives. 10 archetypes with randomized traits (age, income, tech_savviness, brand_loyalty, price_sensitivity) produce agents that think differently. A skeptic evaluates products differently than an early adopter.
**Why batched enrichment:** Generating 100 individual personality blurbs = 100 LLM calls. Batching 10 at a time = 10 LLM calls. Same quality, 10x fewer API calls.

---

### `marketpulse/agents/agent.py` - Core Agent Logic
**What:** The `Agent` class with two key methods: `form_opinion()` (reads product info, returns structured opinion) and `debate()` (responds to another agent's argument, returns stance + sentiment shift).
**Why needed:** This is the brain of each consumer agent. It constructs persona-aware prompts that make the LLM roleplay as a specific consumer type, then parses structured JSON responses into trackable data.
**Why JSON-mode for all outputs:** Qwen 2.5:7b sometimes produces inconsistent freeform text. Forcing JSON output (`{"sentiment": 7, "concerns": [...]}`) makes parsing deterministic. No regex, no string splitting, no parsing failures.

---

### `marketpulse/agents/pool.py` - Batch Execution Pool
**What:** `AgentPool` uses `asyncio.Semaphore` to control how many LLM calls run concurrently. All tasks are launched as coroutines but only `batch_size` execute at once.
**Why needed:** With 100 agents, you can't fire 100 simultaneous requests at Ollama (it processes one at a time) or Gemini (rate limited). The semaphore keeps a pipeline of requests flowing without overwhelming the backend.
**Why semaphore over chunking:** Chunked batching (process 5, wait, process 5, wait) has idle gaps between batches. Semaphore-based concurrency starts the next request the moment one finishes, keeping the LLM pipeline 100% utilized.

---

### `marketpulse/simulation/sentiment.py` - Persuasion Math
**What:** `apply_persuasion()` function that takes debate results and applies deterministic math to update agent sentiment. Brand loyalty reduces shift impact, strong arguments decay confidence, and low confidence + convinced = conversion.
**Why needed:** The LLM suggests sentiment shifts, but raw LLM numbers would be unpredictable. This layer applies consistent rules: a brand-loyal agent resists persuasion (shift * 0.3), repeated strong arguments erode confidence (confidence * 0.85), and conversion only happens when confidence drops below threshold.
**Why hybrid (LLM + math):** Pure LLM sentiment tracking would be noisy and non-reproducible. Pure math would miss natural language nuance. The hybrid approach gets the best of both: LLM provides reasoning quality, math provides consistency.

---

### `marketpulse/simulation/interaction.py` - Agent Pairing Strategy
**What:** `adversarial_pairing()` sorts agents by sentiment and pairs most positive with most negative. Tracks previous pairs to avoid repetition.
**Why needed:** Random pairing produces many low-value debates (two agents who agree just reinforce each other). Adversarial pairing maximizes disagreement, which produces the most useful insights for the marketing report.
**Why this matters:** This is what makes 3 rounds sufficient instead of 10+. Every debate is high-information because the agents have genuinely opposing views.

---

### `marketpulse/simulation/engine.py` - Main Orchestrator
**What:** `SimulationEngine` ties everything together: generates personas, runs opinion phase, executes debate rounds with live conversation display, collects results, and triggers report generation. Displays rich terminal output with panels, tables, and progress bars.
**Why needed:** This is the conductor. Without it, you'd need to manually wire up persona generation -> opinion formation -> pairing -> debating -> persuasion -> reporting. The engine handles all sequencing, error handling, and progress display.
**Why Rich library for output:** Marketing teams need to see what's happening. Live sentiment tables, debate conversations in panels, and progress bars make a 20-minute simulation transparent instead of a black box.

---

### `marketpulse/reporting/analyzer.py` - Report Generation
**What:** `generate_report()` aggregates all simulation data (sentiments, concerns, conversions, archetype breakdowns) into a structured summary, then uses a single LLM call as a "senior marketing strategist" to produce a 7-section report.
**Why needed:** Raw simulation data (sentiment numbers, debate logs) isn't actionable. The reasoning agent synthesizes patterns across all agents into an executive summary, risk analysis, and 5 specific recommendations.
**Why one LLM call:** The structured summary is pre-computed from simulation data (~1500 tokens). The LLM only needs to reason over this summary, not re-process 100 agent conversations. One call, high quality output.

---

## Dependency Graph

```
                          run.py
                            |
              +-------------+-------------+
              |             |             |
          config.py    ollama_backend  engine.py
                            |             |
                         base.py    +-----+-----+-----+-----+-----+
                                    |     |     |     |     |     |
                                 Agent  persona pool  sentiment interaction analyzer
                                    |                     |         |          |
                              +-----+-----+              Agent    Agent     base.py
                              |     |     |
                          Persona  base  AgentMemory
                                   .py   Opinion
                                         InteractionRecord
                                         SharedMemory
```

### Detailed Call Graph

```
run.py
  |
  +--> config.Settings()                          # Load .env
  +--> ollama_backend.OllamaBackend()             # Create LLM client
  +--> shared.SharedMemory(ProductInfo(...))       # Create product data
  +--> engine.SimulationEngine(settings, llm)      # Create engine
         |
         +--> engine.run(shared)
                |
                +--> [1] initialize_agents()
                |      +--> persona.generate_personas(count)
                |      +--> persona.enrich_personas(personas, llm)
                |      |      +--> llm.generate_json()  -----> Ollama API
                |      +--> Agent(persona) for each
                |
                +--> [2] opinion_phase(shared)
                |      +--> pool.execute_batch(tasks)
                |      |      +--> asyncio.Semaphore(batch_size)
                |      |      +--> agent.form_opinion(shared, llm)
                |      |             +--> shared.get_agent_briefing()
                |      |             +--> llm.generate_json()  -----> Ollama API
                |      |             +--> memory.opinions.append()
                |      +--> _print_sentiment_table()
                |
                +--> [3] debate_round(shared, round) x N rounds
                |      +--> interaction.adversarial_pairing(agents, prev_pairs)
                |      +--> for each pair (a, b):
                |      |      +--> a.debate(b_arg, shared, llm)
                |      |      |      +--> memory.get_context_for_prompt()
                |      |      |      +--> llm.generate_json()  -----> Ollama API
                |      |      +--> b.debate(a_arg, shared, llm)
                |      |      |      +--> llm.generate_json()  -----> Ollama API
                |      |      +--> sentiment.apply_persuasion(a, result)
                |      |      +--> sentiment.apply_persuasion(b, result)
                |      +--> _print_sentiment_table()
                |
                +--> [4] _collect_results(shared)
                +--> [5] _print_final_summary(results)
                +--> [6] analyzer.generate_report(results, llm)
                       +--> llm.generate()  -----> Ollama API
                       +--> return marketing report text
```

### Import Dependency Map (which file imports which)

```
                    +------------------+
                    |     run.py       |
                    +------------------+
                      |    |    |    |
                      v    |    |    v
               config.py   |    |  engine.py
                           v    v     |
                  ollama_backend.py   |
                        |             |
                        v             |
                     base.py <--------+-----+-----------+
                                      |     |           |
                        +-------------+     |           |
                        |         |         |           |
                        v         v         v           v
                    persona.py  agent.py  pool.py   analyzer.py
                                  |
                        +---------+---------+
                        |         |         |
                        v         v         v
                    Persona   AgentMemory  SharedMemory
                   (persona)  Opinion      ProductInfo
                              InterRecord  CompetitorInfo
                              (individual)  (shared)
                                  ^
                                  |
                           sentiment.py
                           interaction.py
```

### Layer Architecture

```
+================================================================+
|                        ENTRY LAYER                              |
|  run.py (entry point) + config.py (settings)                   |
+================================================================+
                              |
                              v
+================================================================+
|                     INFRASTRUCTURE LAYER                        |
|  llm/base.py (interface)                                       |
|  llm/ollama_backend.py (local)  llm/gemini_backend.py (cloud)  |
|  agents/pool.py (concurrency)                                  |
+================================================================+
                              |
                              v
+================================================================+
|                        DATA LAYER                               |
|  memory/shared.py (product info, research)                     |
|  memory/individual.py (agent opinions, history)                 |
|  agents/persona.py (archetypes, demographics)                  |
+================================================================+
                              |
                              v
+================================================================+
|                        LOGIC LAYER                              |
|  agents/agent.py (opinion + debate via LLM)                    |
|  simulation/sentiment.py (persuasion math)                     |
|  simulation/interaction.py (adversarial pairing)               |
+================================================================+
                              |
                              v
+================================================================+
|                     ORCHESTRATION LAYER                         |
|  simulation/engine.py (runs full simulation pipeline)          |
+================================================================+
                              |
                              v
+================================================================+
|                        OUTPUT LAYER                             |
|  reporting/analyzer.py (LLM reasoning agent -> marketing report)|
+================================================================+
```

---

## Tech Stack & Why Each Choice

| Tool | Why This |
|------|----------|
| **Python 3.12** | Best LLM ecosystem, async support, already on your machine |
| **Ollama + Qwen 2.5:7b** | Free local inference, no rate limits, 4.7GB fits in 8GB RAM |
| **asyncio** | All work is I/O-bound (waiting on LLM). Async handles 100+ agents efficiently on a single thread |
| **Pydantic** | Type-safe config from .env, catches errors early |
| **Rich** | Beautiful terminal output - panels, tables, progress bars. Makes 20-min simulations transparent |
| **dataclasses** | Lightweight data containers, no ORM overhead for in-memory state |

### Why NOT these alternatives

| Rejected | Why |
|----------|-----|
| LangChain / CrewAI | Heavy frameworks for a well-defined flow. Adds abstraction overhead without benefit |
| Redis | Adds a service dependency. SQLite + in-memory dicts handle this scale fine |
| Vector DB | Shared memory is small (~20 items). No retrieval problem to solve |
| Threading | LLM calls are I/O-bound. asyncio is simpler and more efficient than threads |
| FastAPI | Marketing teams need forms + charts, not an API. Streamlit (Phase 4) fits better |
