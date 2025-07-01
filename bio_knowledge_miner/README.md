# Bio-Knowledge-Miner

End-to-end **Literature ➜ Knowledge-Graph** pipeline powered by AI.

---
## Features
| Stage | Directory | Description |
|-------|-----------|-------------|
| 1. Collection | `data_collection/` | Harvest PubMed metadata → auto-download open-access PDFs via Unpaywall / Crossref / Europe PMC |
| 2. Text Extraction | `text_processing/` | Extract full text from PDFs with **PyMuPDF** |
| 3. Summarize & NER | `llm_services/` | Generate Korean summaries + extract **Gene / Disease / Compound** entities using **OpenAI GPT-4-Turbo** (regex fallback) |
| 4. Graph Build | `knowledge_graph/` | Upsert nodes & relationships into **Neo4j 5** via Bolt; helper for simple Cypher search |
| 5. Output | `data/pdf_entities_summary/` | Store per-PDF result to `pdf_entities_summary.json` (file path, summary, entities) |

---
## Project Layout
```
/bio-knowledge-miner/
├── main.py                 # 파이프라인을 실행하는 메인 스크립트
├── config.py               # API 키, DB 접속 정보, 파일 경로 등 설정 관리
├── requirements.txt        # 프로젝트에 필요한 모든 파이썬 라이브러리 목록
├── .env                    # (Git 무시) 실제 API 키와 비밀번호 저장
|
├── data_collection/        # 1. 데이터 수집 모듈
│   ├── __init__.py
│   ├── api_clients.py      # PubMed, Semantic Scholar 등 외부 API 연동 로직
│   └── crawler.py          # 수집 실행 및 데이터 저장 로직
|
├── text_processing/        # 2. 문서 처리 모듈
│   ├── __init__.py
│   ├── pdf_parser.py       # PDF 파일 파싱 (텍스트, 이미지 추출)
│   └── ocr_handler.py      # 이미지에서 OCR 수행
|
├── llm_services/           # 3. LLM 연동 모듈
│   ├── __init__.py
│   ├── summarizer.py       # 문서 요약 및 키워드 태깅
│   └── entity_extractor.py # 텍스트에서 지식(Node, Relationship) 추출
|
└── knowledge_graph/        # 4. 지식 그래프 모듈
    ├── __init__.py
    ├── neo4j_connector.py  # Neo4j 데이터베이스 연결 및 쿼리 실행
    ├── kg_builder.py       # 추출된 지식을 DB에 저장(구축)
    └── graph_rag_query.py  # 자연어 질의를 Cypher 쿼리로 변환 및 응답 생성
```

---
## Quick Start
```bash
# 1) virtual env
python -m venv .venv && source .venv/bin/activate

# 2) dependencies
pip install -r bio_knowledge_miner_pkg/requirements.txt

# 3) Neo4j via Docker (change password as you like)
cat > docker-compose.yml <<EOF
services:
  neo4j:
    image: neo4j:5.18
    container_name: bio-kg-neo4j
    restart: unless-stopped
    environment:
      NEO4J_AUTH: "neo4j/<PASSWORD>"
      NEO4J_server_memory_heap_initial__size: 1G
      NEO4J_server_memory_heap_max__size: 2G
    ports:
      - "7474:7474"   # Browser
      - "7687:7687"   # Bolt
    volumes:
      - ./neo4j_data:/data   # 로컬 퍼시스턴스
EOF

docker compose up -d
```

### .env template
```
OPENAI_API_KEY=
NCBI_API_KEY=
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=<PASSWORD>
APP_EMAIL=test@example.com   # for Unpaywall
```

### Run the pipeline
```bash
python run.py
```
Execution flow:
1. Fetch PubMed papers (keywords in `search_queries`) → download PDFs  
2. Extract text → summarise + entity extraction  
3. Save results to `data/pdf_entities_summary/pdf_entities_summary.json`  
4. Load nodes/relationships into Neo4j (open http://localhost:7474)

---
## Neo4j Query Examples
```cypher
// list genes targeted by a compound
MATCH (c:Compound)-[:TARGETS]->(g:Gene)
RETURN c,g LIMIT 20;

// KRAS-related diseases
MATCH (g:Gene {name:'KRAS'})-[:ASSOCIATED_WITH]->(d:Disease)
RETURN d;
```

Python helper:
```python
from bio_knowledge_miner_pkg.knowledge_graph.graph_rag_query import search_by_keyword
print(search_by_keyword("KRAS"))
```

---
## License
MIT 