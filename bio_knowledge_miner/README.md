# `bio_knowledge_miner`

## Overview

`bio_knowledge_miner` is the data collection and knowledge management backbone of the Bio-Info project. The core goal of this module is to extract, process, and connect biomedical information from various sources, including unstructured data (e.g., scientific papers) and structured data (e.g., ChEMBL, PubChem), to build a massive Knowledge Graph.

This knowledge graph explicitly represents key relationships necessary for drug discovery research (e.g., 'gene-disease association', 'compound-protein interaction', 'drug-side effect') and provides the foundational knowledge needed for the `auto_hypothesis_agent` to generate and validate hypotheses.

## Key Features and Pipeline

1.  **Data Collection (`data_collection`)**:
    *   Uses a PubMed API client to bulk-collect abstracts and metadata of papers related to specific keywords (e.g., 'KRAS G12C inhibitors').
    *   Extracts the full text of papers through a PDF parser (`pdf_parser`) and processes text within images using an OCR handler (`ocr_handler`).

2.  **Information Extraction (`llm_services`)**:
    *   An entity extractor (`entity_extractor`) based on a Large Language Model (LLM) identifies and normalizes predefined types of biomedical entities from the text, such as 'Gene', 'Disease', 'Compound', and 'Mutation'.
    *   Infers relationships between extracted entities and summarizes long texts to generate the necessary information for the nodes and edges of the knowledge graph.

3.  **Knowledge Graph Construction (`knowledge_graph`)**:
    *   Builds a knowledge graph in a Neo4j database using the extracted entities and relationships (`kg_builder`).
    *   Enriches the information of nodes stored in the graph (e.g., compounds) by linking to external databases (e.g., `fill_compound_structures`).
    *   Provides answers to natural language questions from the knowledge graph through a graph-based Retrieval-Augmented Generation (RAG) query engine (`graph_rag_query`).

4.  **Maintenance (`maintenance`)**:
    *   Includes various scripts to maintain the consistency and quality of the graph data (e.g., cleaning gene names, filling in compound structure information).

## How to Run

Each function of `bio_knowledge_miner` can be run independently. For example, to collect papers on a specific topic and build a knowledge graph, you can follow these steps:

```bash
# (Run from the Bio-Info project root)

# 1. Collect abstracts of papers related to 'KRAS G12C' from PubMed
python -m bio_knowledge_miner.data_collection.collect_pubmed_data --query "KRAS G12C" --max_papers 100

# 2. Extract entities from the collected text and add them as nodes to the knowledge graph
python -m bio_knowledge_miner.llm_services.entity_extractor

# 3. Infer relationships between nodes in the knowledge graph and add edges
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
/bio_knowledge_miner/
├── main.py                 # Main script to run the pipeline
├── config.py               # Manages settings like API keys, DB connection info, file paths
├── requirements.txt        # List of all Python libraries required for the project
├── .env                    # (Git ignored) Stores actual API keys and passwords
|
├── data_collection/        # 1. Data Collection Module
│   ├── __init__.py
│   ├── api_clients.py      # Logic for interfacing with external APIs like PubMed, Semantic Scholar
│   └── crawler.py          # Logic for executing collection and saving data
|
├── text_processing/        # 2. Document Processing Module
│   ├── __init__.py
│   ├── pdf_parser.py       # Parsing PDF files (extracting text, images)
│   └── ocr_handler.py      # Performing OCR on images
|
├── llm_services/           # 3. LLM Integration Module
│   ├── __init__.py
│   ├── summarizer.py       # Document summarization and keyword tagging
│   └── entity_extractor.py # Extracting knowledge (Nodes, Relationships) from text
|
└── knowledge_graph/        # 4. Knowledge Graph Module
    ├── __init__.py
    ├── neo4j_connector.py  # Connecting to and querying the Neo4j database
    ├── kg_builder.py       # Saving (building) extracted knowledge into the DB
    └── graph_rag_query.py  # Converting natural language queries to Cypher and generating responses
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
      - ./neo4j_data:/data   # Local persistence
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

Python helper:
```python
from bio_knowledge_miner_pkg.knowledge_graph.graph_rag_query import search_by_keyword
print(search_by_keyword("KRAS"))
```

---
## License
MIT 