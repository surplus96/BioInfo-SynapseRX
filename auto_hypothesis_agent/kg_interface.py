"""Neo4j 그래프 인터페이스 모듈 (스켈레톤).

`bio_knowledge_miner` 가 구축한 데이터베이스에 연결해 질의/업데이트 기능을 제공합니다.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Dict, Iterable, List

try:
    from neo4j import GraphDatabase, Driver, Session
except ImportError:  # pragma: no cover
    GraphDatabase = None  # type: ignore
    Driver = Session = None  # type: ignore


class GraphClient:
    """가벼운 Neo4j 래퍼.

    사용 예:
    ```python
    from auto_hypothesis_agent.kg_interface import GraphClient
    gc = GraphClient("bolt://localhost:7687", "neo4j", "pw")
    for record in gc.run("MATCH (n) RETURN n LIMIT 5"):
        print(record)
    ```
    """

    def __init__(self, uri: str | None, user: str | None, password: str | None):
        if GraphDatabase is None:
            raise ImportError("Install neo4j-driver: pip install neo4j>=5")

        if uri is None:
            raise ValueError("Neo4j URI must be provided")

        self._driver: Driver = GraphDatabase.driver(uri, auth=(user, password))

    @contextmanager
    def session(self):
        session: Session = self._driver.session()
        try:
            yield session
        finally:
            session.close()

    def run(self, cypher: str, **params) -> List[Dict[str, Any]]:
        """Execute Cypher and return list of dictionaries."""
        with self.session() as sess:
            result = sess.run(cypher, params)
            return [r.data() for r in result]

    def close(self):
        self._driver.close() 