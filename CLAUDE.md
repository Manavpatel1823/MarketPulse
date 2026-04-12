# MarketPulse

## Project Overview
AI multi-agent market simulation. 100+ consumer personas debate a product's merits, shift opinions through persuasion, and produce a detailed marketing report highlighting risks and blind spots.

## Tech Stack
- Python 3.12, asyncio for concurrency
- Ollama (Qwen 2.5:7b) for local LLM (primary)
- Google Gemini API (optional cloud fallback)
- DuckDuckGo for web research, SQLite for persistence
- Rich for CLI UI, Streamlit for web dashboard

## Running
```bash
python3 run.py
```

## Configuration (.env)
- `BACKEND` — "ollama" (default) or "gemini"
- `OLLAMA_MODEL` — e.g. `qwen2.5:7b`
- `OLLAMA_BASE_URL` — default `http://localhost:11434`
- `AGENT_COUNT` — number of agents (3 for testing, scale to 100+)
- `ROUNDS` — debate rounds
- `BATCH_SIZE` — concurrent LLM calls (keep 3 for 8GB RAM)

## Key Architecture
- `marketpulse/llm/` — LLMBackend ABC with Ollama and Gemini implementations
- `marketpulse/agents/` — Persona generation, Agent logic, AgentPool batching
- `marketpulse/memory/` — SharedMemory (product+research) and AgentMemory (per-agent)
- `marketpulse/simulation/` — Engine, adversarial pairing, sentiment/persuasion math
- `marketpulse/research/` — Web search + LLM extraction (Phase 2)
- `marketpulse/reporting/` — Final reasoning agent + report renderer (Phase 3)
- `marketpulse/storage/` — SQLite schema + CRUD (Phase 3)

## Gemini Free Tier Limits
- 5 RPM / 20 RPD for gemini-2.5-flash
- Use BATCH_SIZE=2 and AGENT_COUNT=3 for testing on free tier
- For production runs, use Ollama or paid Gemini API

## Implementation Status
- [x] Phase 1: Vertical slice (config, LLM backends, agents, simulation engine, CLI)
- [ ] Phase 2: Web research + scale to 10+ agents ← **NEXT**
- [ ] Phase 3: Reporting + SQLite persistence
- [ ] Phase 4: Rich CLI + Streamlit dashboard
- [ ] Phase 5: Refinement (social networks, product iteration mode)

---

## Phase 2 Plan — Web Research + Scale

**Goal**: Replace hardcoded product info in `run.py` with real-world data auto-collected from the web. Agents should read competitor reviews, pricing, and market sentiment found via DuckDuckGo.

### New files
- `marketpulse/research/searcher.py`
  - `async def search(query: str, max_results: int = 5) -> list[SearchResult]`
  - Uses `duckduckgo-search` (no API key required)
  - Returns list of `{title, url, snippet}`
- `marketpulse/research/parser.py`
  - `async def extract_findings(results: list[SearchResult], llm: LLMBackend) -> list[ResearchFinding]`
  - Single LLM call summarizes all snippets into structured findings (competitors, price points, consumer pain points)
  - Feeds into `SharedMemory.research_findings`
- `marketpulse/research/coordinator.py`
  - Orchestrates: builds queries like `"{product} reviews"`, `"{product} vs competitors"`, `"{product} price comparison"`
  - Calls searcher → parser → populates SharedMemory before opinion phase

### Modifications
- `run.py` — take product name/description via CLI args (argparse) instead of hardcoded AirPods
- `engine.py` — add `research_phase(shared)` called BEFORE `opinion_phase()`
- `memory/shared.py` — already has `ResearchFinding` and `CompetitorInfo`; wire `get_agent_briefing()` to include research summary
- `requirements.txt` — add `duckduckgo-search`

### Scale testing
- Test with AGENT_COUNT=10, BATCH_SIZE=3 on Ollama
- Measure: total runtime, LLM call count, memory usage
- Target: 10 agents × 3 rounds should complete in <10 min on M3 8GB

### Acceptance criteria
1. `python3 run.py "Tesla Model Y" "Electric SUV"` kicks off research, shows found competitors + findings, then runs normal simulation
2. Agents reference real competitors/prices in their debates (visible in Rich output)
3. No regressions on 3-agent default flow

---

## Phase 3 Plan — Reporting + Persistence (sketch)

- `marketpulse/storage/db.py` — aiosqlite schema for `runs`, `agents`, `opinions`, `interactions`, `reports`
- `marketpulse/reporting/renderer.py` — render report as Markdown file with run metadata
- `engine.run()` saves full simulation to SQLite at end; can re-load for comparison

---

## Design Principles (keep in mind for all phases)
- **Prompts stay <600 tokens** — critical for 7B model speed on 8GB RAM
- **All LLM outputs use JSON mode** where parseable (opinions, debates, research extraction)
- **Free-form text only for final report** (reasoning agent)
- **Semaphore-based batching** — never fire more than BATCH_SIZE concurrent LLM calls
- **Memory is passed as argument**, not global — SharedMemory flows run → engine → agent
- **Deterministic math on top of LLM outputs** — persuasion mechanics live in `sentiment.py`, not in prompts
