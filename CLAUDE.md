# MarketPulse

## Project Overview
AI multi-agent market simulation. 25+ consumer personas debate a product's merits, shift opinions through persuasion, and produce a detailed marketing report highlighting risks and blind spots.

## Tech Stack
- Python 3.12+, asyncio for concurrency
- **OpenRouter (deepseek/deepseek-chat-v3)** — primary LLM, paid
- Ollama (Qwen 2.5:7b) — local fallback
- Google Gemini API — optional cloud fallback
- DuckDuckGo (`ddgs`) for web research
- **PostgreSQL via asyncpg** for persistence (formerly SQLite — switched in Phase 3)
- aiohttp for `--from-url` fetching
- Rich for CLI UI; Streamlit reserved for Phase 4 dashboard

## Running
```bash
# Default — web search + simulation, with gate + confirmation prompt
python3 run.py "Fairphone 5"

# Skip web search, use a brief file (compresses brief → ProductInfo via LLM,
# then web-searches the inferred CATEGORY for real competitors)
python3 run.py "MyProduct" --from-file brief.txt

# Skip web search, fetch a URL instead
python3 run.py "MyProduct" --from-url https://example.com/product

# Offline / deterministic stub (no LLM research at all)
python3 run.py "MyProduct" --no-research

# Bypass the "is research worthwhile?" gate
python3 run.py "Fairphone 5" --force-research

# Auto-confirm the findings prompt (CI/scripting)
python3 run.py "Fairphone 5" -y

# DB inspection (no sim)
python3 run.py --list                 # recent runs
python3 run.py --show 7               # full detail of run #7
python3 run.py --compare 3 7          # side-by-side (2+ run IDs)
```

## Configuration (.env)
- `BACKEND` — `"openrouter"` (default in current .env), `"ollama"`, or `"gemini"`
- `MARKETPULSE_API` — OpenRouter API key (required when BACKEND=openrouter)
- `OPENROUTER_MODEL` — default `deepseek/deepseek-chat-v3`
- `OLLAMA_MODEL` — e.g. `qwen2.5:7b`
- `OLLAMA_BASE_URL` — default `http://localhost:11434`
- `AGENT_COUNT` — number of agents (25 in current .env; can scale to 100+)
- `ROUNDS` — debate rounds (default 3)
- `BATCH_SIZE` — concurrent LLM calls (5 on OpenRouter; keep 2-3 for Ollama on 8GB RAM)
- `DATABASE_URL` — Postgres DSN, e.g. `postgresql://user:pass@localhost:5432/marketpulse`
- `PERSIST_DB` — `true`/`false` (default true). Set false to skip DB writes.

## Key Architecture
- `marketpulse/llm/` — `LLMBackend` ABC + Ollama, OpenRouter, Gemini implementations
- `marketpulse/agents/` — Persona generation (50 hardcoded + procedural padding), Agent logic, AgentPool batching, `SKEW_BY_TIER` for dynamic panel composition
- `marketpulse/memory/` — `SharedMemory` (product + research + `MarketSignals`) and `AgentMemory` (per-agent, fresh per run)
- `marketpulse/simulation/` — Engine (run → initialize → opinion → debate rounds → report), adversarial pairing, sentiment/persuasion math
- `marketpulse/research/`
  - `searcher.py` — async DDG wrapper (sequential queries, throttled — DDG silently rate-limits parallels)
  - `parser.py` — one LLM call: snippets → `ProductInfo` + competitors + findings + `MarketSignals`
  - `coordinator.py` — `research_product()` (name-based) + `augment_with_category_competitors()` (category-based, used after upload)
  - `gate.py` — "is web research worthwhile?" pre-check; heuristics + LLM fallback. Snippet must mention product name to count as third-party signal.
  - `uploader.py` — `from_text()` / `from_url()` for unreleased/private products
- `marketpulse/reporting/analyzer.py` — final reasoning agent. **Two non-negotiable rules:** (1) lead with distribution shape, not mean; (2) concerns must name product/feature/competitor (no generic "limited brand recognition")
- `marketpulse/storage/`
  - `db.py` — asyncpg pool + `CREATE TABLE IF NOT EXISTS` schema bootstrap + 6 write functions
  - `queries.py` — `list_runs`, `get_run`, `compare_runs`
  - `cli.py` — Rich rendering for `--list / --show / --compare`

## Database Schema (Phase 3)
5 tables in PostgreSQL: `runs`, `shared_memory`, `agents`, `opinions`, `reports`. Schema is created on first connect (idempotent, no migration framework). Mid-run crash leaves `finished_at` NULL → visible as "incomplete" in `--list`. JSONB columns for `distribution`, `concerns_json`, `positives_json`, `settings_json`, etc. — never queried inside, only blob-loaded.

## Implementation Status
- [x] Phase 1: Vertical slice (config, LLM backends, agents, simulation engine, CLI)
- [x] Phase 2a: Web research (searcher / parser / coordinator) + scale to 25 agents
- [x] Phase 2b: Dynamic panel composition via `MarketSignals` + `SKEW_BY_TIER`
- [x] Phase 2c: Distributions over averages; conditional web search (gate); product upload path; company-specific concerns
- [x] Phase 3: PostgreSQL persistence + `--list/--show/--compare` CLI
- [ ] Phase 4: Streamlit dashboard ← **NEXT**
- [ ] Phase 5: Refinement (recurring personas, social networks, product iteration mode, `--reuse-panel` for fair comparisons)

---

## Design Principles (keep in mind for all phases)
- **Prompts stay <600 tokens** — critical for 7B model speed and OpenRouter cost
- **All LLM outputs use JSON mode** where parseable (opinions, debates, research extraction, gate, uploader)
- **Free-form text only for the final report** (reasoning agent)
- **Semaphore-based batching** — never fire more than `BATCH_SIZE` concurrent LLM calls
- **Memory is passed as argument**, not global — `SharedMemory` flows `run → engine → agent`
- **Deterministic math on top of LLM outputs** — persuasion mechanics live in `sentiment.py`, not in prompts
- **DDG queries run sequentially**, never in parallel (silent rate-limiting on the same IP)
- **Distribution before mean** in any user-facing summary (a 6/10 mean from broad mild approval and from a polarized split are completely different marketing situations)
- **Concerns must be company-specific** — no generic "limited brand recognition"; cite features, named competitors, or specific market positions
- **DB persistence is opt-out, never required** — `if conn:` guards mean a DB outage doesn't break a run
