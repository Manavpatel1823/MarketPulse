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


async def get_resume_state(
    pool: asyncpg.Pool, run_id: int
) -> dict[str, Any] | None:
    """Pull everything needed to resume a crashed run.

    Shape:
        {
          "run": {id, product_name, folder_name, agent_count, rounds,
                  backend, model, settings_json, finished_at},
          "shared_memory": {product, competitors, findings, market_context, signals},
          "agents": [
            {agent_db_id, persona_id, name, archetype, age, income_bracket,
             initial_bias, sentiment_history: [..], latest_opinion: {...} | None,
             conversion_count: int}
          ],
          "last_round": int | None  # max round_num in opinions, None if empty
        }
    """
    async with pool.acquire() as conn:
        run = await conn.fetchrow(
            """
            SELECT id, product_name, folder_name, agent_count, rounds,
                   backend, model, settings_json, finished_at
              FROM runs WHERE id = $1
            """,
            run_id,
        )
        if not run:
            return None
        sm = await conn.fetchrow(
            "SELECT * FROM shared_memory WHERE run_id = $1", run_id
        )
        agents = await conn.fetch(
            """
            SELECT id, persona_id, name, archetype, age, income_bracket,
                   initial_bias
              FROM agents
             WHERE run_id = $1
             ORDER BY id
            """,
            run_id,
        )
        opinions = await conn.fetch(
            """
            SELECT agent_id, round_num, sentiment, reasoning,
                   concerns_json, positives_json
              FROM opinions
             WHERE run_id = $1
             ORDER BY agent_id, round_num
            """,
            run_id,
        )
        conv_rows = await conn.fetch(
            """
            SELECT agent_a_id, a_convinced, agent_b_id, b_convinced
              FROM interactions
             WHERE run_id = $1
            """,
            run_id,
        )
        max_round = await conn.fetchval(
            "SELECT MAX(round_num) FROM opinions WHERE run_id = $1", run_id,
        )

    # Aggregate opinions and conversions per agent.
    by_agent_ops: dict[int, list[dict]] = {}
    for o in opinions:
        by_agent_ops.setdefault(o["agent_id"], []).append({
            "round_num": o["round_num"],
            "sentiment": o["sentiment"],
            "reasoning": o["reasoning"],
            "concerns": json.loads(o["concerns_json"] or "[]"),
            "positives": json.loads(o["positives_json"] or "[]"),
        })

    conv_counts: dict[int, int] = {}
    for r in conv_rows:
        if r["a_convinced"]:
            conv_counts[r["agent_a_id"]] = conv_counts.get(r["agent_a_id"], 0) + 1
        if r["b_convinced"]:
            conv_counts[r["agent_b_id"]] = conv_counts.get(r["agent_b_id"], 0) + 1

    agent_blocks = []
    for a in agents:
        aid = a["id"]
        ops = by_agent_ops.get(aid, [])
        # sentiment_history comes straight out of the opinions table in round order
        hist = [o["sentiment"] for o in ops]
        latest = ops[-1] if ops else None
        agent_blocks.append({
            "agent_db_id": aid,
            "persona_id": a["persona_id"],
            "name": a["name"],
            "archetype": a["archetype"],
            "age": a["age"],
            "income_bracket": a["income_bracket"],
            "initial_bias": a["initial_bias"],
            "sentiment_history": hist,
            "latest_opinion": latest,
            "conversion_count": conv_counts.get(aid, 0),
        })

    sm_block = None
    if sm:
        sm_dict = _decode(dict(sm), "product_json", "competitors_json",
                          "findings_json", "signals_json", "graph_json")
        sm_block = {
            "product": sm_dict.get("product_json"),
            "competitors": sm_dict.get("competitors_json") or [],
            "findings": sm_dict.get("findings_json") or [],
            "market_context": sm_dict.get("market_context"),
            "signals": sm_dict.get("signals_json"),
            "graph": sm_dict.get("graph_json"),
        }

    run_dict = _decode(dict(run), "settings_json")
    return {
        "run": run_dict,
        "shared_memory": sm_block,
        "agents": agent_blocks,
        "last_round": max_round,  # None if no opinions yet
    }


async def delete_future_opinions(
    pool: asyncpg.Pool, run_id: int, keep_through_round: int
) -> None:
    """Trim any opinions/interactions beyond keep_through_round.

    Defensive: if a prior crash left orphan rows from a partially-written round,
    drop them before resuming so we don't double-write or break uniqueness.
    """
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                "DELETE FROM opinions WHERE run_id = $1 AND round_num > $2",
                run_id, keep_through_round,
            )
            await conn.execute(
                "DELETE FROM interactions WHERE run_id = $1 AND round_num > $2",
                run_id, keep_through_round,
            )


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


async def list_agents(pool: asyncpg.Pool, run_id: int) -> list[dict[str, Any]] | None:
    """List all agents in a run with summary info for the chat selector."""
    async with pool.acquire() as conn:
        run = await conn.fetchval("SELECT id FROM runs WHERE id = $1", run_id)
        if run is None:
            return None
        agents = await conn.fetch(
            """
            SELECT id, persona_id, name, archetype, age, income_bracket,
                   initial_bias, initial_sentiment, final_sentiment,
                   conversion_count
              FROM agents
             WHERE run_id = $1
             ORDER BY final_sentiment DESC NULLS LAST
            """,
            run_id,
        )
    return [dict(a) for a in agents]


async def get_agent_chat_context(
    pool: asyncpg.Pool, run_id: int, agent_db_id: int
) -> dict[str, Any] | None:
    """Pull everything needed to chat with an agent post-run.

    Returns the agent's persona, full opinion history across rounds,
    all debate interactions (arguments, stances, shifts), and the
    knowledge graph if available.
    """
    async with pool.acquire() as conn:
        agent = await conn.fetchrow(
            """
            SELECT id, persona_id, name, archetype, age, income_bracket,
                   initial_bias, initial_sentiment, final_sentiment,
                   conversion_count
              FROM agents
             WHERE run_id = $1 AND id = $2
            """,
            run_id, agent_db_id,
        )
        if not agent:
            return None

        run = await conn.fetchrow(
            "SELECT product_name, rounds FROM runs WHERE id = $1", run_id,
        )

        # Full opinion history (all rounds)
        opinions = await conn.fetch(
            """
            SELECT round_num, sentiment, reasoning, concerns_json, positives_json
              FROM opinions
             WHERE run_id = $1 AND agent_id = $2
             ORDER BY round_num
            """,
            run_id, agent_db_id,
        )

        # All debate interactions this agent participated in
        interactions = await conn.fetch(
            """
            SELECT i.round_num,
                   CASE WHEN i.agent_a_id = $2 THEN b.name ELSE a.name END AS opponent_name,
                   CASE WHEN i.agent_a_id = $2 THEN b.archetype ELSE a.archetype END AS opponent_archetype,
                   CASE WHEN i.agent_a_id = $2 THEN i.a_stance ELSE i.b_stance END AS my_stance,
                   CASE WHEN i.agent_a_id = $2 THEN i.b_stance ELSE i.a_stance END AS opponent_stance,
                   CASE WHEN i.agent_a_id = $2 THEN i.a_argument ELSE i.b_argument END AS my_argument,
                   CASE WHEN i.agent_a_id = $2 THEN i.b_argument ELSE i.a_argument END AS opponent_argument,
                   CASE WHEN i.agent_a_id = $2 THEN i.a_shift ELSE i.b_shift END AS my_shift,
                   CASE WHEN i.agent_a_id = $2 THEN i.a_convinced ELSE i.b_convinced END AS was_convinced
              FROM interactions i
              JOIN agents a ON a.id = i.agent_a_id
              JOIN agents b ON b.id = i.agent_b_id
             WHERE i.run_id = $1
               AND (i.agent_a_id = $2 OR i.agent_b_id = $2)
             ORDER BY i.round_num, i.id
            """,
            run_id, agent_db_id,
        )

        # Shared memory for product context
        sm = await conn.fetchrow(
            "SELECT product_json, graph_json FROM shared_memory WHERE run_id = $1",
            run_id,
        )

        # Final report (for context)
        report = await conn.fetchval(
            "SELECT markdown FROM reports WHERE run_id = $1", run_id,
        )

    opinion_list = []
    for o in opinions:
        opinion_list.append({
            "round_num": o["round_num"],
            "sentiment": o["sentiment"],
            "reasoning": o["reasoning"],
            "concerns": json.loads(o["concerns_json"] or "[]"),
            "positives": json.loads(o["positives_json"] or "[]"),
        })

    interaction_list = [dict(i) for i in interactions]

    product_json = None
    graph_json = None
    if sm:
        sm_decoded = _decode(dict(sm), "product_json", "graph_json")
        product_json = sm_decoded.get("product_json")
        graph_json = sm_decoded.get("graph_json")

    return {
        "agent": dict(agent),
        "product_name": run["product_name"] if run else "",
        "total_rounds": run["rounds"] if run else 0,
        "opinions": opinion_list,
        "interactions": interaction_list,
        "product": product_json,
        "graph": graph_json,
        "report_summary": (report or "")[:500] if report else None,
    }
