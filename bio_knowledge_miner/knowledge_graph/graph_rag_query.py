from typing import List
from .neo4j_connector import get_driver


def search_by_keyword(keyword: str) -> List[dict]:
    cypher = (
        "MATCH (n) WHERE toLower(n.name) CONTAINS toLower($kw) "
        "RETURN labels(n)[0] AS label, n.name AS name LIMIT 20"
    )
    with get_driver().session() as s:
        res = s.run(cypher, kw=keyword)
        return [r.data() for r in res] 