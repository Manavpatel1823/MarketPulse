"""Read-only FastAPI service for the Phase 4 visualization frontend.

Three endpoints:
- GET /runs                  -> list_runs()
- GET /runs/{run_id}         -> get_run() (full detail + report markdown)
- GET /runs/{run_id}/graph   -> get_run_graph() (nodes + edges for the canvas)

No writes, no auth — localhost tool. The Vite dev server proxies /api/* here.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from marketpulse.config import Settings
from marketpulse.storage import db as storage
from marketpulse.storage import queries as db_queries


@asynccontextmanager
async def _lifespan(app: FastAPI):
    settings = Settings()
    app.state.pool = await storage.get_pool(settings.database_url)
    try:
        yield
    finally:
        await storage.close_pool()


app = FastAPI(title="MarketPulse API", lifespan=_lifespan)

# Vite dev server default + common local ports. Loosen only on localhost.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ],
    allow_credentials=False,
    allow_methods=["GET"],
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


@app.get("/health")
async def health():
    return {"ok": True}
