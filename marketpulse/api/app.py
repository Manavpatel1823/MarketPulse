"""FastAPI service — simulation launcher, live WebSocket, and post-run agent chat.

Endpoints:
- GET  /runs                                -> list_runs()
- GET  /runs/{run_id}                       -> get_run()
- GET  /runs/{run_id}/graph                 -> get_run_graph()
- GET  /runs/{run_id}/agents                -> list agents for chat selector
- POST /runs/{run_id}/agents/{agent_id}/chat -> chat with an agent post-run
- POST /simulate                            -> launch a new simulation (returns run_id)
- WS   /ws/live/{run_id}                    -> stream live events during simulation

The Vite dev server proxies /api/* here.
"""
from __future__ import annotations

import asyncio
import io
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from marketpulse.config import Settings
from marketpulse.llm.base import LLMBackend
from marketpulse.simulation.events import EventBus, EventType, SimEvent
from marketpulse.storage import db as storage
from marketpulse.storage import queries as db_queries


def _build_llm(settings: Settings) -> LLMBackend:
    """Build the LLM backend from server config."""
    if settings.backend == "openrouter":
        from marketpulse.llm.openrouter_backend import OpenRouterBackend
        if not settings.marketpulse_api:
            raise HTTPException(status_code=500, detail="MARKETPULSE_API not configured in .env")
        return OpenRouterBackend(api_key=settings.marketpulse_api, model=settings.openrouter_model)
    if settings.backend == "gemini":
        from marketpulse.llm.gemini_backend import GeminiBackend
        if not settings.gemini_api_key:
            raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured in .env")
        return GeminiBackend(api_key=settings.gemini_api_key, model=settings.model)
    from marketpulse.llm.ollama_backend import OllamaBackend
    return OllamaBackend(model=settings.ollama_model, base_url=settings.ollama_base_url)


# Active event buses keyed by run_id — allows WebSocket subscribers to
# connect to a running simulation.
_active_buses: dict[int, EventBus] = {}


def _extract_pdf_text(data: bytes) -> str:
    """Extract text from a PDF file using pymupdf."""
    import pymupdf
    doc = pymupdf.open(stream=data, filetype="pdf")
    pages = []
    for page in doc:
        pages.append(page.get_text())
    doc.close()
    return "\n".join(pages).strip()


async def _run_simulation(
    settings: Settings,
    llm: LLMBackend,
    product_name: str,
    brief_text: str | None,
    event_bus: EventBus,
) -> None:
    """Run a full simulation as a background task. Emits events via the bus."""
    from marketpulse.memory.shared import ProductInfo, SharedMemory
    from marketpulse.research.coordinator import (
        augment_with_category_competitors,
        enrich_competitor_briefs,
        research_product,
    )
    from marketpulse.research.uploader import from_text as upload_from_text
    from marketpulse.simulation.engine import SimulationEngine

    try:
        # Build SharedMemory from brief or web research
        if brief_text:
            shared = await upload_from_text(product_name, brief_text, llm)
            if shared.product.category:
                shared = await augment_with_category_competitors(shared, llm)
            shared = await enrich_competitor_briefs(shared, llm)
        else:
            shared = await research_product(product_name, llm)
            shared = await enrich_competitor_briefs(shared, llm)

        engine = SimulationEngine(settings, llm, event_bus=event_bus)
        await engine.run(shared)
    except Exception as e:
        await event_bus.emit(SimEvent(EventType.SIM_ERROR, {
            "error": f"{type(e).__name__}: {e}",
        }))


@asynccontextmanager
async def _lifespan(app: FastAPI):
    settings = Settings()
    if settings.database_url:
        app.state.pool = await storage.get_pool(settings.database_url)
    else:
        app.state.pool = None
    app.state.settings = settings
    try:
        yield
    finally:
        await storage.close_pool()


app = FastAPI(title="MarketPulse API", lifespan=_lifespan)

# CORS origins from env var (comma-separated) or dev defaults.
_cors_origins = Settings().cors_origins.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _cors_origins if o.strip()],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/runs")
async def list_runs(limit: int = 50):
    rows = await db_queries.list_runs(app.state.pool, limit=limit)
    # Serialize datetimes — FastAPI handles this, but make it explicit for the frontend.
    return {"runs": rows}


@app.get("/runs/{run_id}")
async def get_run(run_id: int):
    run = await db_queries.get_run(app.state.pool, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"run {run_id} not found")
    return run


@app.get("/runs/{run_id}/graph")
async def get_run_graph(run_id: int):
    graph = await db_queries.get_run_graph(app.state.pool, run_id)
    if graph is None:
        raise HTTPException(status_code=404, detail=f"run {run_id} not found")
    return graph


@app.get("/runs/{run_id}/agents")
async def list_agents(run_id: int):
    agents = await db_queries.list_agents(app.state.pool, run_id)
    if agents is None:
        raise HTTPException(status_code=404, detail=f"run {run_id} not found")
    return {"agents": agents}


class ChatRequest(BaseModel):
    message: str


@app.post("/runs/{run_id}/agents/{agent_id}/chat")
async def chat_with_agent(
    run_id: int,
    agent_id: int,
    body: ChatRequest,
):
    """Chat with an agent post-run. Reconstructs their full persona and
    history, then generates an in-character response via the LLM."""
    ctx = await db_queries.get_agent_chat_context(
        app.state.pool, run_id, agent_id,
    )
    if ctx is None:
        raise HTTPException(status_code=404, detail="agent or run not found")

    agent = ctx["agent"]
    product_name = ctx["product_name"]

    # Build the agent's memory narrative
    opinion_narrative = []
    for op in ctx["opinions"]:
        label = "Initial opinion" if op["round_num"] == 0 else f"After round {op['round_num']}"
        opinion_narrative.append(
            f"{label}: sentiment {op['sentiment']:+.1f}/10\n"
            f"  Reasoning: {op['reasoning']}\n"
            f"  Concerns: {', '.join(op['concerns']) or 'none'}\n"
            f"  Positives: {', '.join(op['positives']) or 'none'}"
        )

    debate_narrative = []
    for ix in ctx["interactions"]:
        debate_narrative.append(
            f"Round {ix['round_num']}: debated {ix['opponent_name']} ({ix['opponent_archetype']})\n"
            f"  Their argument: \"{ix['opponent_argument']}\"\n"
            f"  Your response ({ix['my_stance']}): \"{ix['my_argument']}\"\n"
            f"  Sentiment shift: {ix['my_shift']:+.1f}, "
            f"{'convinced to change stance' if ix['was_convinced'] else 'held ground'}"
        )

    # Graph context for competitive intelligence
    graph_ctx = ""
    if ctx.get("graph"):
        from marketpulse.knowledge.graph import KnowledgeGraph
        kg = KnowledgeGraph.from_dict(ctx["graph"])
        graph_ctx = kg.get_agent_graph_context(product_name, agent["archetype"])
        if graph_ctx:
            graph_ctx = f"\nCompetitive intelligence you were aware of:\n{graph_ctx}"

    system = (
        f"You are {agent['name']}, age {agent['age'] or 'unknown'}, "
        f"a {agent['archetype']} consumer. You just finished participating in "
        f"a market simulation about '{product_name}'.\n\n"
        f"Your full journey:\n"
        f"{''.join(chr(10) + o for o in opinion_narrative)}\n\n"
        f"Your debates:\n"
        f"{''.join(chr(10) + d for d in debate_narrative)}\n\n"
        f"Final sentiment: {agent['final_sentiment']}/10 "
        f"(started at {agent['initial_sentiment']})\n"
        f"Times you changed your mind: {agent['conversion_count'] or 0}\n"
        f"{graph_ctx}\n\n"
        f"STAY IN CHARACTER as {agent['name']}. Answer questions from your "
        f"perspective — what you experienced, why you feel the way you do, "
        f"what arguments moved you or failed to. Be specific and reference "
        f"actual debates and arguments from your history. Be honest about "
        f"what convinced you and what didn't."
    )

    llm = _build_llm(app.state.settings)
    response = await llm.generate(system, body.message)

    return {
        "agent_name": agent["name"],
        "archetype": agent["archetype"],
        "response": response,
    }


@app.post("/simulate")
async def start_simulation(
    product_name: str = Form(...),
    file: UploadFile | None = File(None),
    agent_count: int = Form(25),
    rounds: int = Form(3),
):
    """Launch a new simulation. Accepts product name + optional file (PDF/text).
    Returns immediately with a live_id; connect to /ws/live/{live_id} for events."""
    settings: Settings = app.state.settings
    settings.agent_count = agent_count
    settings.rounds = rounds

    llm = _build_llm(settings)

    # Extract text from uploaded file if provided
    brief_text: str | None = None
    if file is not None:
        raw = await file.read()
        if file.filename and file.filename.lower().endswith(".pdf"):
            brief_text = _extract_pdf_text(raw)
        else:
            brief_text = raw.decode("utf-8", errors="replace")
        if not brief_text.strip():
            raise HTTPException(status_code=400, detail="Uploaded file is empty")

    # Create an event bus for this simulation
    event_bus = EventBus()
    placeholder_id = len(_active_buses) + 9000
    _active_buses[placeholder_id] = event_bus

    # Run the simulation in the background
    async def _wrapper():
        try:
            await _run_simulation(
                settings, llm, product_name, brief_text, event_bus,
            )
        finally:
            _active_buses.pop(placeholder_id, None)

    asyncio.create_task(_wrapper())

    return {"status": "started", "live_id": placeholder_id}


@app.websocket("/ws/live/{live_id}")
async def websocket_live(websocket: WebSocket, live_id: int):
    """Stream simulation events in real-time."""
    await websocket.accept()

    bus = _active_buses.get(live_id)
    if bus is None:
        await websocket.send_json({"type": "error", "data": {"error": "No active simulation with this ID"}})
        await websocket.close()
        return

    queue = bus.subscribe()
    try:
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=120.0)
                await websocket.send_text(event.to_json())
                if event.type in (EventType.SIM_COMPLETE, EventType.SIM_ERROR):
                    break
            except asyncio.TimeoutError:
                # Send keepalive ping
                await websocket.send_json({"type": "ping", "data": {}})
    except WebSocketDisconnect:
        pass
    finally:
        bus.unsubscribe(queue)
        await websocket.close()


@app.get("/health")
async def health():
    return {"ok": True}
