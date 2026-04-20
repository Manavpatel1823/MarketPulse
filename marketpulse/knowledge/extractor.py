"""LLM-based entity and relationship extraction from raw text.

One LLM call takes unstructured text (product briefs, PDFs, market reports)
and extracts entities (people, companies, products, technologies, features)
and relationships between them as structured triples.

This is the "GraphRAG" step — turning prose into a queryable knowledge graph.
The prompt is kept under 600 tokens (per project convention) by truncating
input and requesting a tight JSON schema.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from marketpulse.llm.base import LLMBackend

# Cap input so prompt stays manageable — even long PDFs get trimmed.
MAX_INPUT_CHARS = 12000


@dataclass
class ExtractedEntity:
    name: str
    entity_type: str  # person, company, product, technology, feature, market, location
    description: str = ""


@dataclass
class ExtractedRelationship:
    source: str       # entity name
    target: str       # entity name
    relation: str     # verb/label (e.g. "founded", "competes_with", "manufactures")
    detail: str = ""  # optional context (e.g. "$18M", "since 2023")


@dataclass
class ExtractionResult:
    entities: list[ExtractedEntity]
    relationships: list[ExtractedRelationship]


async def extract_entities(
    text: str,
    product_name: str,
    llm: LLMBackend,
) -> ExtractionResult:
    """Extract entities and relationships from raw text via one LLM call."""
    text = (text or "").strip()
    if not text:
        return ExtractionResult(entities=[], relationships=[])
    if len(text) > MAX_INPUT_CHARS:
        text = text[:MAX_INPUT_CHARS]

    system = (
        "You are a knowledge graph extraction engine. Given raw text about a "
        "product, extract ALL entities (people, companies, products, technologies, "
        "features, markets, locations) and the relationships between them. "
        "Be thorough — capture supply chain links, team backgrounds, partnerships, "
        "patent/licensing, manufacturing, funding, and competitive relationships. "
        "Every relationship must connect two named entities from your entity list."
    )

    user = (
        f"Product under study: {product_name}\n\n"
        f"Source text:\n{text}\n\n"
        "Extract and return JSON with EXACTLY this shape:\n"
        "{\n"
        '  "entities": [\n'
        '    {"name": str, "type": "person"|"company"|"product"|"technology"|"feature"|"market"|"location", "description": str},\n'
        "    ...\n"
        "  ],\n"
        '  "relationships": [\n'
        '    {"source": str, "target": str, "relation": str, "detail": str},\n'
        "    ...\n"
        "  ]\n"
        "}\n\n"
        "Guidelines:\n"
        "- entities: 10-30 entities. Include the product itself, all competitors "
        "mentioned, all people named, all companies (including suppliers, "
        "manufacturers, investors), technologies, and specific features.\n"
        "- relationships: 15-50 relationships. Use clear verb labels:\n"
        "  founded, co_founded, formerly_at, invested_in, manufactures, "
        "  supplies_to, competes_with, licenses_to, partners_with, uses, "
        "  has_feature, priced_at, targets_audience, has_weakness, "
        "  better_than, worse_than, acquired, employs, located_in\n"
        "- detail: short context (dollar amounts, dates, percentages, specs)\n"
        "- Every entity in a relationship MUST appear in the entities list\n"
        "- Extract implicit relationships too — if text says 'GoerTek builds "
        "for Anker', that's (GoerTek, manufactures, Anker)"
    )

    raw: dict[str, Any] = await llm.generate_json(system, user)

    entities = []
    for e in raw.get("entities", []) or []:
        name = (e.get("name") or "").strip()
        if not name:
            continue
        etype = (e.get("type") or "product").strip().lower()
        valid_types = {"person", "company", "product", "technology", "feature", "market", "location"}
        if etype not in valid_types:
            etype = "product"
        entities.append(ExtractedEntity(
            name=name,
            entity_type=etype,
            description=(e.get("description") or "").strip(),
        ))

    relationships = []
    entity_names = {e.name.lower() for e in entities}
    for r in raw.get("relationships", []) or []:
        src = (r.get("source") or "").strip()
        tgt = (r.get("target") or "").strip()
        rel = (r.get("relation") or "").strip()
        if not src or not tgt or not rel:
            continue
        # Only keep relationships where both entities exist
        if src.lower() not in entity_names or tgt.lower() not in entity_names:
            continue
        relationships.append(ExtractedRelationship(
            source=src,
            target=tgt,
            relation=rel.lower().replace(" ", "_"),
            detail=(r.get("detail") or "").strip(),
        ))

    return ExtractionResult(entities=entities, relationships=relationships)
