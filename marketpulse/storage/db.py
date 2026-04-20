"""PostgreSQL persistence — schema bootstrap + write paths.

Phase 3, trimmed-schema variant. We persist:
- runs (one per simulation invocation)
- shared_memory (the product/competitors/signals as seen by the panel)
- agents (one per persona in the run; structured columns only, no JSON dump)
- opinions (one per agent per round; round 0 = initial, 1..N = post-debate)
- reports (the final markdown report)

Schema is created with CREATE TABLE IF NOT EXISTS on first connect; no
migration framework yet (deliberately — see Phase 3 plan, Out of Scope).

All writes use the connection pool. Engine acquires a single connection
for the lifetime of the run and reuses it inside one transaction-per-phase
so a mid-run crash leaves a coherent partial state (finished_at NULL ⇒
visible as 'incomplete' in --list).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import asyncpg

from marketpulse.memory.individual import Opinion
from marketpulse.memory.shared import SharedMemory


# Single shared pool, lazily initialized.
_pool: asyncpg.Pool | None = None


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS runs (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    started_at      TIMESTAMPTZ NOT NULL,
    finished_at     TIMESTAMPTZ,
    product_name    TEXT NOT NULL,
    folder_name     TEXT NOT NULL,
    agent_count     INTEGER NOT NULL,
    rounds          INTEGER NOT NULL,
    backend         TEXT NOT NULL,
    model           TEXT NOT NULL,
    brand_tier      TEXT,
    mean_sentiment  DOUBLE PRECISION,
    polarization    DOUBLE PRECISION,
    distribution    JSONB,
    total_conversions INTEGER,
    settings_json   JSONB
);

CREATE TABLE IF NOT EXISTS shared_memory (
    run_id          BIGINT PRIMARY KEY REFERENCES runs(id) ON DELETE CASCADE,
    product_json    JSONB NOT NULL,
    competitors_json JSONB,
    findings_json   JSONB,
    market_context  TEXT,
    signals_json    JSONB,
    graph_json      JSONB
);

CREATE TABLE IF NOT EXISTS agents (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id          BIGINT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    persona_id      TEXT NOT NULL,
    name            TEXT NOT NULL,
    archetype       TEXT NOT NULL,
    age             INTEGER,
    income_bracket  TEXT,
    initial_bias    DOUBLE PRECISION,
    initial_sentiment DOUBLE PRECISION,
    final_sentiment DOUBLE PRECISION,
    conversion_count INTEGER
);

CREATE TABLE IF NOT EXISTS opinions (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id          BIGINT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    agent_id        BIGINT NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    round_num       INTEGER NOT NULL,
    sentiment       DOUBLE PRECISION NOT NULL,
    reasoning       TEXT,
    concerns_json   JSONB,
    positives_json  JSONB,
    aspect_ratings_json JSONB
);

CREATE TABLE IF NOT EXISTS reports (
    run_id          BIGINT PRIMARY KEY REFERENCES runs(id) ON DELETE CASCADE,
    markdown        TEXT NOT NULL,
    generated_at    TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS interactions (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id          BIGINT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    round_num       INTEGER NOT NULL,
    agent_a_id      BIGINT NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    agent_b_id      BIGINT NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    a_stance        TEXT,
    b_stance        TEXT,
    a_shift         DOUBLE PRECISION,
    b_shift         DOUBLE PRECISION,
    a_convinced     BOOLEAN,
    b_convinced     BOOLEAN,
    a_argument      TEXT,
    b_argument      TEXT
);

-- Phase 4.5: add graph_json column if missing (idempotent migration)
DO $$ BEGIN
    ALTER TABLE shared_memory ADD COLUMN IF NOT EXISTS graph_json JSONB;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;

-- Phase 5: add aspect_ratings_json column to opinions (idempotent migration)
DO $$ BEGIN
    ALTER TABLE opinions ADD COLUMN IF NOT EXISTS aspect_ratings_json JSONB;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;

CREATE INDEX IF NOT EXISTS idx_runs_product  ON runs(product_name);
CREATE INDEX IF NOT EXISTS idx_runs_started  ON runs(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_opinions_run_round ON opinions(run_id, round_num);
CREATE INDEX IF NOT EXISTS idx_agents_run    ON agents(run_id);
CREATE INDEX IF NOT EXISTS idx_interactions_run_round ON interactions(run_id, round_num);
"""


async def get_pool(dsn: str) -> asyncpg.Pool:
    """Lazily create and return the global pool. Min 1, max 4 — this is a
    single-user CLI, no need for a big pool."""
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(dsn=dsn, min_size=1, max_size=4)
        async with _pool.acquire() as conn:
            await conn.execute(SCHEMA_SQL)
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _j(obj: Any) -> str:
    """Serialize a Python value for a JSONB column.

    asyncpg with JSONB columns expects either a json-encoded string OR a
    decoded value with explicit codec setup. Easiest: serialize ourselves.
    """
    return json.dumps(obj, default=str)


# ─────────────────────────────────────────────────────────────────────────
# Write paths — engine.py calls these in order through one phase per call.
# ─────────────────────────────────────────────────────────────────────────


async def insert_run(
    pool: asyncpg.Pool,
    *,
    product_name: str,
    folder_name: str,
    agent_count: int,
    rounds: int,
    backend: str,
    model: str,
    settings_dict: dict,
) -> int:
    sql = """
        INSERT INTO runs (
            started_at, product_name, folder_name,
            agent_count, rounds, backend, model, settings_json
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb)
        RETURNING id
    """
    async with pool.acquire() as conn:
        return await conn.fetchval(
            sql, _now(), product_name, folder_name,
            agent_count, rounds, backend, model, _j(settings_dict),
        )


async def insert_shared_memory(
    pool: asyncpg.Pool, run_id: int, shared: SharedMemory
) -> None:
    p = shared.product
    product = {
        "name": p.name, "description": p.description, "price": p.price,
        "features": p.features, "category": p.category,
        "detailed_description": p.detailed_description,
        "risks": p.risks,
        "target_audience": p.target_audience,
    }
    competitors = [
        {"name": c.name, "description": c.description,
         "price": c.price, "key_features": c.key_features,
         "positioning": c.positioning}
        for c in shared.competitors
    ]
    findings = [
        {"source": f.source, "summary": f.summary,
         "sentiment": f.sentiment, "category": f.category}
        for f in shared.research_findings
    ]
    signals = None
    if shared.signals:
        signals = {
            "brand_tier": shared.signals.brand_tier,
            "category_maturity": shared.signals.category_maturity,
            "price_position": shared.signals.price_position,
        }
    graph_data = None
    if shared.knowledge_graph is not None:
        graph_data = _j(shared.knowledge_graph.to_dict())
    sql = """
        INSERT INTO shared_memory
            (run_id, product_json, competitors_json, findings_json, market_context, signals_json, graph_json)
        VALUES ($1, $2::jsonb, $3::jsonb, $4::jsonb, $5, $6::jsonb, $7::jsonb)
        ON CONFLICT (run_id) DO NOTHING
    """
    async with pool.acquire() as conn:
        await conn.execute(
            sql, run_id, _j(product), _j(competitors),
            _j(findings), shared.market_context,
            _j(signals) if signals else None,
            graph_data,
        )


async def insert_agents(
    pool: asyncpg.Pool, run_id: int, agents: list
) -> dict[str, int]:
    """Insert all agents, return persona_id → agents.id map."""
    sql = """
        INSERT INTO agents (
            run_id, persona_id, name, archetype, age, income_bracket, initial_bias
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING id, persona_id
    """
    out: dict[str, int] = {}
    async with pool.acquire() as conn:
        async with conn.transaction():
            for a in agents:
                p = a.persona
                row = await conn.fetchrow(
                    sql, run_id, p.id, p.name, p.archetype,
                    p.age, p.income_bracket, p.initial_bias,
                )
                out[p.id] = row["id"]
    return out


async def insert_opinion(
    pool: asyncpg.Pool, run_id: int, agent_db_id: int,
    round_num: int, opinion: Opinion | None,
) -> None:
    if opinion is None:
        return
    sql = """
        INSERT INTO opinions
            (run_id, agent_id, round_num, sentiment, reasoning, concerns_json, positives_json, aspect_ratings_json)
        VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7::jsonb, $8::jsonb)
    """
    async with pool.acquire() as conn:
        await conn.execute(
            sql, run_id, agent_db_id, round_num,
            opinion.sentiment, opinion.reasoning,
            _j(opinion.concerns), _j(opinion.positives),
            _j(opinion.aspect_ratings) if opinion.aspect_ratings else None,
        )


async def insert_opinions_batch(
    pool: asyncpg.Pool, run_id: int,
    rows: list[tuple[int, int, Opinion | None]],  # (agent_db_id, round_num, opinion)
) -> None:
    """Bulk-insert opinions for one phase (faster than N round-trips)."""
    payload = []
    for agent_db_id, round_num, op in rows:
        if op is None:
            continue
        payload.append((
            run_id, agent_db_id, round_num, op.sentiment,
            op.reasoning, _j(op.concerns), _j(op.positives),
            _j(op.aspect_ratings) if op.aspect_ratings else None,
        ))
    if not payload:
        return
    sql = """
        INSERT INTO opinions
            (run_id, agent_id, round_num, sentiment, reasoning, concerns_json, positives_json, aspect_ratings_json)
        VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7::jsonb, $8::jsonb)
    """
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.executemany(sql, payload)


async def finalize_run(
    pool: asyncpg.Pool,
    run_id: int,
    *,
    mean_sentiment: float,
    polarization: float,
    distribution: dict,
    total_conversions: int,
    brand_tier: str | None,
    agent_finals: dict[int, tuple[float, int, float]],
    # agent_finals: agent_db_id → (final_sentiment, conversion_count, initial_sentiment)
) -> None:
    """Mark the run complete and stamp per-agent final numbers."""
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                """
                UPDATE runs
                   SET finished_at = $2,
                       mean_sentiment = $3,
                       polarization = $4,
                       distribution = $5::jsonb,
                       total_conversions = $6,
                       brand_tier = $7
                 WHERE id = $1
                """,
                run_id, _now(), mean_sentiment, polarization,
                _j(distribution), total_conversions, brand_tier,
            )
            await conn.executemany(
                """
                UPDATE agents
                   SET final_sentiment = $2,
                       conversion_count = $3,
                       initial_sentiment = $4
                 WHERE id = $1
                """,
                [
                    (aid, fin, conv, init)
                    for aid, (fin, conv, init) in agent_finals.items()
                ],
            )


async def insert_interactions_batch(
    pool: asyncpg.Pool,
    run_id: int,
    rows: list[tuple[int, int, int, str, str, float, float, bool, bool, str, str]],
) -> None:
    """Bulk-insert one round's debate pairs.

    Row tuple: (round_num, agent_a_db_id, agent_b_db_id,
                a_stance, b_stance, a_shift, b_shift,
                a_convinced, b_convinced, a_argument, b_argument)
    """
    if not rows:
        return
    payload = [(run_id, *r) for r in rows]
    sql = """
        INSERT INTO interactions (
            run_id, round_num, agent_a_id, agent_b_id,
            a_stance, b_stance, a_shift, b_shift,
            a_convinced, b_convinced, a_argument, b_argument
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
    """
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.executemany(sql, payload)


async def insert_report(pool: asyncpg.Pool, run_id: int, markdown: str) -> None:
    sql = """
        INSERT INTO reports (run_id, markdown, generated_at)
        VALUES ($1, $2, $3)
        ON CONFLICT (run_id) DO UPDATE
            SET markdown = EXCLUDED.markdown,
                generated_at = EXCLUDED.generated_at
    """
    async with pool.acquire() as conn:
        await conn.execute(sql, run_id, markdown, _now())
