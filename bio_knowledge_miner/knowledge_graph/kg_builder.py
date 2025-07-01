from typing import Dict, List
from .neo4j_connector import get_driver


def _prepare_constraints():
    queries = [
        "CREATE CONSTRAINT IF NOT EXISTS "
        "FOR (g:Gene) REQUIRE g.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS "
        "FOR (d:Disease) REQUIRE d.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS "
        "FOR (c:Compound) REQUIRE c.name IS UNIQUE",
    ]
    with get_driver().session() as s:
        for q in queries:
            s.run(q)

_prepare_constraints()


def upsert_entities(entities: Dict[str, List[str]]):
    """노드 upsert"""
    with get_driver().session() as session:
        for g in entities.get("gene", []):
            session.run("MERGE (:Gene {name:$n})", n=g)
        for d in entities.get("disease", []):
            session.run("MERGE (:Disease {name:$n})", n=d)
        for c in entities.get("compound", []):
            session.run("MERGE (:Compound {name:$n})", n=c)


def create_basic_relationships(entities: Dict[str, List[str]]):
    """간단한 휴리스틱 관계 생성"""
    genes = entities.get("gene", [])
    diseases = entities.get("disease", [])
    compounds = entities.get("compound", [])
    with get_driver().session() as s:
        for g in genes:
            for d in diseases:
                s.run(
                    "MATCH (g:Gene {name:$g}), (d:Disease {name:$d}) "
                    "MERGE (g)-[:ASSOCIATED_WITH]->(d)",
                    g=g,
                    d=d,
                )
        for c in compounds:
            for g in genes:
                s.run(
                    "MATCH (c:Compound {name:$c}), (g:Gene {name:$g}) "
                    "MERGE (c)-[:TARGETS]->(g)",
                    c=c,
                    g=g,
                )


def ingest_document_entities(entities: Dict[str, List[str]]):
    upsert_entities(entities)
    create_basic_relationships(entities) 