# MarketPulse

AI-powered market simulation. 25-100 consumer personas debate your product, shift opinions through argument, and produce a marketing intelligence report with risks, opportunities, and per-aspect breakdowns.

Give it a product name or upload a brief. It builds a panel of diverse consumers (skeptics, early adopters, bargain hunters, etc.), lets them argue for multiple rounds, and tells you what a real launch might look like — before you spend a dollar on marketing.

## What It Does

1. **Research** — Searches the web (DuckDuckGo) for product info, competitors, and market signals. Or accepts your own brief (text/PDF) for unreleased products.

2. **Knowledge Graph** — Extracts entities and relationships (companies, people, technologies, supply chains) from research data via LLM. Surfaces non-obvious insights like shared manufacturers or founder backgrounds.

3. **Agent Panel** — Generates 25-100 consumer personas across 10 archetypes. Each agent has a personality, income bracket, brand loyalty, and price sensitivity. Panel composition adapts to brand tier (incumbent vs. challenger vs. unknown).

4. **Domain-Adaptive Evaluation** — Agents evaluate products through category-specific criteria. Running shoes get rated on comfort, durability, fit, weight. Earbuds get rated on performance, battery, privacy, build quality. Each archetype prioritizes different aspects.

5. **Debate Rounds** — Agents are paired adversarially (most positive vs. most negative). They argue, present counter-arguments, and can genuinely change their minds. Persuasion uses hybrid LLM + deterministic math.

6. **Report** — A reasoning agent analyzes the full simulation and produces an actionable report: distribution analysis, company-specific risks, competitive positioning, aspect breakdown, and 5 concrete recommendations.

7. **Web UI** — Launch simulations from the browser, watch debates happen live via WebSocket, browse past runs as interactive graphs, and chat with agents post-simulation.

## Quick Start

### Prerequisites

- Python 3.12+
- PostgreSQL (for persistence and web UI)
- Node.js 18+ (for frontend)
- An LLM backend: [OpenRouter](https://openrouter.ai/) API key (recommended), local [Ollama](https://ollama.ai/), or Google Gemini

### Setup

```bash
# Clone
git clone https://github.com/Manavpatel1823/MarketPulse.git
cd MarketPulse

# Python dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your API key and database URL

# Create PostgreSQL database
createdb marketpulse

# Frontend
cd frontend && npm install && cd ..
```

### Run (CLI)

```bash
# Web search + simulation
python3 run.py "Fairphone 5"

# Use your own product brief
python3 run.py "MyProduct" --from-file brief.txt

# Use a product URL
python3 run.py "MyProduct" --from-url https://example.com/product

# Auto-confirm prompts (for scripting)
python3 run.py "Fairphone 5" -y

# Skip web research entirely
python3 run.py "MyProduct" --no-research
```

### Run (Web UI)

```bash
# Terminal 1: API server
python3 run.py --serve

# Terminal 2: Frontend dev server
cd frontend && npm run dev
```

Open `http://localhost:5173`. Enter a product name, optionally upload a PDF/text brief, choose agent count and rounds, and hit Launch.

### Inspect Past Runs

```bash
python3 run.py --list              # Recent runs
python3 run.py --show 7            # Full detail of run #7
python3 run.py --compare 3 7       # Side-by-side comparison
```

## Configuration

Copy `.env.example` to `.env` and edit:

| Variable | Default | Description |
|----------|---------|-------------|
| `BACKEND` | `openrouter` | LLM backend: `openrouter`, `ollama`, or `gemini` |
| `MARKETPULSE_API` | — | OpenRouter API key |
| `OPENROUTER_MODEL` | `deepseek/deepseek-chat-v3` | Model for OpenRouter |
| `OLLAMA_MODEL` | `qwen2.5:7b` | Model for local Ollama |
| `AGENT_COUNT` | `25` | Number of consumer agents (10-100) |
| `ROUNDS` | `3` | Debate rounds |
| `BATCH_SIZE` | `5` | Concurrent LLM calls |
| `DATABASE_URL` | — | PostgreSQL connection string |
| `PERSIST_DB` | `true` | Save runs to database |

## Tech Stack

- **Python 3.12+** with asyncio for concurrency
- **OpenRouter / Ollama / Gemini** — pluggable LLM backends
- **PostgreSQL + asyncpg** — run persistence
- **DuckDuckGo** — web research
- **NetworkX** — knowledge graph for entity relationships
- **FastAPI + WebSocket** — real-time simulation API
- **React + Zustand + Vite** — interactive frontend
- **Rich** — CLI terminal UI

## Sample Output

The report includes:

- **Executive Summary** with launch gate (PROCEED / CAUTION / HOLD / DO NOT)
- **Distribution Analysis** — sentiment shape, not just the mean
- **Company-Specific Risks** — names your product, features, and competitors
- **Competitive Positioning** — wins/losses vs. each named competitor
- **Aspect Breakdown** — per-dimension ratings (e.g., comfort: 7.2, value: 4.3)
- **Recommendations** — 5 specific actions tied to simulation data

## License

MIT
