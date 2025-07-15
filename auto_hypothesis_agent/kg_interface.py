"""Neo4j 그래프 인터페이스 모듈 (스켈레톤).

`bio_knowledge_miner` 가 구축한 데이터베이스에 연결해 질의/업데이트 기능을 제공합니다.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

# --- 데이터베이스 연결 방식 통일 ---
# bio_knowledge_miner 모듈의 표준 커넥터를 직접 임포트하여 사용합니다.
# 이렇게 하면 프로젝트 전체의 DB 연결 포인트가 일원화되어 안정성이 높아집니다.
from bio_knowledge_miner.knowledge_graph.neo4j_connector import get_driver, close_driver
# -----------------------------------


class GraphClient:
    """
    지식 그래프(Neo4j)와의 상호작용을 관리하는 클라이언트.
    프로젝트의 표준 연결 방식인 get_driver()를 사용하도록 리팩토링되었습니다.
    """

    def __init__(self):
        """GraphClient를 초기화합니다."""
        self.driver = None
        logging.info("GraphClient 초기화. get_driver()를 통해 연결을 가져옵니다.")
        try:
            self.driver = get_driver()
            logging.info("데이터베이스 드라이버를 성공적으로 가져왔습니다.")
        except Exception as e:
            logging.error(f"데이터베이스 드라이버를 가져오는 데 실패했습니다: {e}")
            raise

    def run(self, cypher: str, **kwargs: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        주어진 Cypher 쿼리를 데이터베이스에 대해 실행합니다.

        Args:
            cypher (str): 실행할 Cypher 쿼리 문자열.
            **kwargs: 쿼리에 전달할 파라미터.

        Returns:
            List[Dict[str, Any]]: 쿼리 결과 레코드의 리스트.
        """
        if not self.driver:
            raise RuntimeError("데이터베이스 드라이버가 초기화되지 않았습니다. 클라이언트가 잘못 생성되었습니다.")
            
        try:
            with self.driver.session() as session:
                result = session.run(cypher, **kwargs)
                # seralizable dict로 변환
                return [r.data() for r in result]
        except Exception as e:
            logging.error(f"Cypher 쿼리 실행 실패: {e}\nQuery: {cypher}\nParams: {kwargs}")
            return []  # 오류 발생 시 빈 리스트 반환

    def close(self):
        """
        전역 드라이버 연결을 닫습니다.
        애플리케이션 종료 시 호출됩니다.
        """
        logging.info("GraphClient가 전역 드라이버 연결 종료를 요청합니다.")
        close_driver() 