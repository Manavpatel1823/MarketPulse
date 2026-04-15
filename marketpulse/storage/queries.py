"""Read-only queries powering --list / --show / --compare."""
from __future__ import annotations

import json
from typing import Any

import asyncpg


def _decode(row: dict, *json_keys: str) -> dict:
    """asyncpg returns JSONB as str; decode the keys we care about."""
    out = dict(row)
    for k in json_keys:
        v = out.get(k)
        if isinstance(v, str):
            try:
                out[k] = json.loads(v)
            except Exception:
                pass
    return out


async def list_runs(pool: asyncpg.Pool, limit: int = 20) -> list[dict[str, Any]]:
    sql = """
        SELECT id, started_at, finished_at, product_name,
               brand_tier, mean_sentiment, polarization,
               agent_count, rounds, total_conversions
          FROM runs
         ORDER BY started_at DESC
         LIMIT $1
    """
    async with pool.acquire() as conn:
        rows = await conn.fetch(sql, limit)
    return [dict(r) for r in rows]


async def get_run(pool: asyncpg.Pool, run_id: int) -> dict[str, Any] | None:
    """Full detail: run + shared_memory + report + agent summary."""
    async with pool.acquire() as conn:
        run = await conn.fetchrow("SELECT * FROM runs WHERE id = $1", run_id)
        if not run:
            return None
        sm = await conn.fetchrow(
            "SELECT * FROM shared_memory WHERE run_id = $1", run_id
        )
        rep = await conn.fetchrow(
            "SELECT markdown, generated_at FROM reports WHERE run_id = $1",
            run_id,
        )
        agents = await conn.fetch(
            """
            SELECT persona_id, name, archetype, age, income_bracket,
                   initial_bias, initial_sentiment, final_sentiment,
                   conversion_count
              FROM agents
             WHERE run_id = $1
             ORDER BY final_sentiment DESC NULLS LAST
            """,
            run_id,
        )
    out = _decode(dict(run), "distribution", "settings_json")
    out["shared_memory"] = (
        _decode(dict(sm), "product_json", "competitors_json",
                "findings_json", "signals_json")
        if sm else None
    )
    out["report"] = dict(rep) if rep else None
    out["agents"] = [dict(a) for a in agents]
    return out


async def get_run_graph(
    pool: asyncpg.Pool, run_id: int
) -> dict[str, Any] | None:
    """Return a run in node-graph shape for the visualization frontend.

    Shape:
        {
          "run_id": int, "product_name": str, "rounds": int,
          "nodes": [
            {"id": int, "persona_id": str, "name": str, "archetype": str,
             "initial_sentiment": float, "final_sentiment": float,
             "conversion_count": int,
             "sentiment_by_round": {round_num: sentiment, ...}}
          ],
          "edges": [
            {"id": int, "round_num": int,
             "source": agent_a_db_id, "target": agent_b_db_id,
             "a_stance": str, "b_stance": str,
             "a_shift": float, "b_shift": float,
             "a_convinced": bool, "b_convinced": bool,
             "a_argument": str, "b_argument": str}
          ]
        }

    Returns None if the run does not exist.
    """
    async with pool.acquire() as conn:
        run = await conn.fetchrow(
            "SELECT id, product_name, rounds FROM runs WHERE id = $1", run_id,
        )
        if not run:
            return None
        agents = await conn.fetch(
            """
            SELECT id, persona_id, name, archetype, age, income_bracket,
                   initial_bias, initial_sentiment, final_sentiment,
                   conversion_count
              FROM agents
             WHERE run_id = $1
            """,
            run_id,
        )
        # Per-round sentiment timeline straight from opinions.
        opinions = await conn.fetch(
            """
            SELECT agent_id, round_num, sentiment
              FROM opinions
             WHERE run_id = $1
             ORDER BY agent_id, round_num
            """,
            run_id,
        )
        interactions = await conn.fetch(
            """
            SELECT id, round_num, agent_a_id, agent_b_id,
                   a_stance, b_stance, a_shift, b_shift,
                   a_convinced, b_convinced, a_argument, b_argument
              FROM interactions
             WHERE run_id = $1
             ORDER BY round_num, id
            """,
            run_id,
        )

    by_agent: dict[int, dict[int, float]] = {}
    for o in opinions:
        by_agent.setdefault(o["agent_id"], {})[o["round_num"]] = o["sentiment"]

    nodes = []
    for a in agents:
        nodes.append({
            "id": a["id"],
            "persona_id": a["persona_id"],
            "name": a["name"],
            "archetype": a["archetype"],
            "age": a["age"],
            "income_bracket": a["income_bracket"],
            "initial_bias": a["initial_bias"],
            "initial_sentiment": a["initial_sentiment"],
            "final_sentiment": a["final_sentiment"],
            "conversion_count": a["conversion_count"] or 0,
            "sentiment_by_round": by_agent.get(a["id"], {}),
        })

    edges = []
    for e in interactions:
        edges.append({
            "id": e["id"],
            "round_num": e["round_num"],
            "source": e["agent_a_id"],
            "target": e["agent_b_id"],
            "a_stance": e["a_stance"],
            "b_stance": e["b_stance"],
            "a_shift": e["a_shift"],
            "b_shift": e["b_shift"],
            "a_convinced": e["a_convinced"],
            "b_convinced": e["b_convinced"],
            "a_argument": e["a_argument"],
            "b_argument": e["b_argument"],
        })

    return {
        "run_id": run["id"],
        "product_name": run["product_name"],
        "rounds": run["rounds"],
        "nodes": nodes,
        "edges": edges,
    }


async def compare_runs(
    pool: asyncpg.Pool, run_ids: list[int]
) -> list[dict[str, Any]]:
    """Pull the comparison-relevant slice for N runs.

    For each run: distribution (decoded), top concerns, top positives,
    plus the headline scalars. Top concerns/positives are recomputed from
    the latest opinion of each agent (round = max round in that run).
    """
    out: list[dict[str, Any]] = []
    async with pool.acquire() as conn:
        for rid in run_ids:
            run = await conn.fetchrow(
                """
                SELECT id, started_at, product_name, brand_tier,
                       mean_sentiment, polarization, distribution,
                       agent_count, rounds, total_conversions
                  FROM runs
                 WHERE id = $1
                """,
                rid,
            )
            if not run:
                continue
            row = _decode(dict(run), "distribution")

            # Final-round opinions for top concerns/positives
            opinions = await conn.fetch(
                """
                WITH last_round AS (
                    SELECT MAX(round_num) AS r FROM opinions WHERE run_id = $1
                )
                SELECT concerns_json, positives_json
                  FROM opinions, last_round
                 WHERE opinions.run_id = $1
                   AND opinions.round_num = last_round.r
                """,
                rid,
            )
            concerns: dict[str, int] = {}
            positives: dict[str, int] = {}
            for o in opinions:
                for c in json.loads(o["concerns_json"] or "[]"):
                    concerns[c] = concerns.get(c, 0) + 1
                for p in json.loads(o["positives_json"] or "[]"):
                    positives[p] = positives.get(p, 0) + 1
            row["top_concerns"] = sorted(
                concerns.items(), key=lambda x: -x[1]
            )[:3]
            row["top_positives"] = sorted(
                positives.items(), key=lambda x: -x[1]
            )[:3]
            out.append(row)
    return out
