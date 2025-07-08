# `bio_knowledge_miner`

## 개요

`bio_knowledge_miner`는 Bio-Info 프로젝트의 데이터 수집 및 지식 관리 백본(backbone)입니다. 이 모듈의 핵심 목표는 비정형 데이터(예: 과학 논문)와 정형 데이터(예: ChEMBL, PubChem)를 포함한 다양한 소스로부터 생물의학 정보를 추출, 처리하고, 이를 연결하여 거대한 지식 그래프(Knowledge Graph)를 구축하는 것입니다.

이 지식 그래프는 신약 개발 연구에 필요한 핵심적인 관계들(예: '유전자-질병 연관성', '화합물-단백질 상호작용', '치료제-부작용')을 명시적으로 표현하며, `auto_hypothesis_agent`가 가설을 생성하고 검증하는 데 필요한 기반 지식을 제공합니다.

## 주요 기능 및 파이프라인

1.  **데이터 수집 (`data_collection`)**:
    *   PubMed API 클라이언트를 이용해 특정 키워드(예: 'KRAS G12C inhibitors')와 관련된 논문의 초록 및 메타데이터를 대량으로 수집합니다.
    *   PDF 파서(`pdf_parser`)를 통해 논문 전체 텍스트를 추출하고, OCR 핸들러(`ocr_handler`)를 이용해 이미지 내 텍스트까지 처리합니다.

2.  **정보 추출 (`llm_services`)**:
    *   LLM(Large Language Model)을 기반으로 한 엔티티 추출기(`entity_extractor`)가 텍스트에서 'Gene', 'Disease', 'Compound', 'Mutation' 등 미리 정의된 유형의 생물의학 엔티티를 식별하고 정규화합니다.
    *   추출된 엔티티 간의 관계를 추론하고, 긴 텍스트를 요약하여 지식 그래프의 노드와 엣지에 필요한 정보를 생성합니다.

3.  **지식 그래프 구축 (`knowledge_graph`)**:
    *   추출된 엔티티와 관계를 사용하여 Neo4j 데이터베이스에 지식 그래프를 구축(`kg_builder`)합니다.
    *   그래프에 저장된 노드(예: 화합물)의 정보를 외부 데이터베이스와 연동하여 보강합니다(예: `fill_compound_structures`).
    *   그래프 기반의 RAG(Retrieval-Augmented Generation) 쿼리 엔진(`graph_rag_query`)을 통해 자연어 질문에 대한 답변을 지식 그래프에서 찾아 제공합니다.

4.  **유지보수 (`maintenance`)**:
    *   그래프 데이터의 일관성과 품질을 유지하기 위한 다양한 스크립트(예: 유전자 이름 정제, 화합물 구조 정보 채우기)를 포함합니다.

## 실행 방법

`bio_knowledge_miner`의 각 기능은 독립적으로 실행될 수 있습니다. 예를 들어, 특정 주제에 대한 논문을 수집하고 지식 그래프를 구축하려면 다음 단계를 따를 수 있습니다.

```bash
# (Bio-Info 프로젝트 루트에서 실행)

# 1. PubMed에서 'KRAS G12C' 관련 논문 초록 수집
python -m bio_knowledge_miner.data_collection.collect_pubmed_data --query "KRAS G12C" --max_papers 100

# 2. 수집된 텍스트에서 엔티티 추출 및 지식 그래프에 노드로 추가
python -m bio_knowledge_miner.llm_services.entity_extractor

# 3. 지식 그래프의 노드 간 관계 추론 및 엣지 추가
python -m bio_knowledge_miner.knowledge_graph.kg_builder
```

End-to-end **Literature ➜ Knowledge-Graph** pipeline powered by AI.

<p align="center">
  <img src="https://raw.githubusercontent.com/Neo4j-GraphAcademy/graphgists/master/images/knowledge-graph.png" width="550"/>
</p>

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
MATCH (c:Compound)-[:TARGETS]->(g:Gene)-[:ASSOCIATED_WITH]->(d:Disease)
RETURN c,g,d

// KRAS-related diseases
MATCH (g:Gene {name:'KRAS'})-[:ASSOCIATED_WITH]->(d:Disease)
RETURN d;
```

```
<img src="https://github.com/surplus96/BioInfo-SynapseRX/blob/main/data/results/Neo4j-DataResult-KRAS-Example-01.png"> 


<img src="https://github.com/surplus96/BioInfo-SynapseRX/blob/main/data/results/Neo4j-DataResult-KRAS-Example-02.png"> 

---
## License
MIT 