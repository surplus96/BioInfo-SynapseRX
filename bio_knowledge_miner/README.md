# `bio_knowledge_miner`

## Overview

`bio_knowledge_miner` is the data collection and knowledge management backbone of the SynapseRX project. Its core purpose is to build a comprehensive biomedical Knowledge Graph by extracting, processing, and connecting information from diverse sources, including scientific literature and public databases.

This Knowledge Graph serves as the foundation for the `auto_hypothesis_agent`, providing the structured data (e.g., gene-disease associations, compound-protein interactions) needed to generate and validate novel therapeutic hypotheses.

## Core Components

1.  **Data Collection (`data_collection`)**:
    *   Uses API clients for sources like **PubMed** to fetch metadata and abstracts based on search queries (e.g., "KRAS G12C inhibitors").
    *   Includes a `crawler` to systematically download and manage data.

2.  **Text Processing & NLP (`text_processing`, `llm_services`)**:
    *   Parses full-text from PDF documents using tools like **PyMuPDF**.
    *   Leverages Large Language Models (LLMs) via `entity_extractor` to identify and normalize key biomedical entities: **Genes, Diseases, Compounds, and Mutations**.
    *   Infers relationships between these entities to be stored as graph edges.

3.  **Knowledge Graph (`knowledge_graph`)**:
    *   The `kg_builder` takes the extracted entities and relationships and upserts them into a **Neo4j** graph database.
    *   Nodes in the graph can be enriched with additional information from external sources (e.g., filling in compound structures using the `fill_compound_structures` maintenance script).
    *   Includes a `graph_rag_query` engine to enable querying the graph using natural language questions.

4.  **Maintenance (`maintenance`)**:
    *   A collection of scripts dedicated to cleaning, enriching, and ensuring the quality of the graph data. Examples include `clean_gene_nodes.py`, `populate_cell_lines.py`, and `annotate_variants.py`.

## How to Run

The scripts within this module are designed to be run as part of a sequential pipeline to build and refine the knowledge graph.

```bash
# All commands should be run from the project's root directory.

# 1. Collect data from external sources (e.g., PubMed)
# (Specific collection scripts are in `data_collection`)
python -m bio_knowledge_miner.main 

# 2. Run maintenance scripts to process and load data into Neo4j
# Note: These should be run in a logical order.

# Clean up gene names for consistency
python -m bio_knowledge_miner.maintenance.clean_gene_nodes

# Enrich compound nodes with structural data from PubChem
python -m bio_knowledge_miner.maintenance.fill_compound_structures --gene KRAS

# Populate the graph with cell line data
python -m bio_knowledge_miner.maintenance.populate_cell_lines

# Filter cell lines for a specific mutation
python -m bio_knowledge_miner.maintenance.filter_cell_lines --gene KRAS --mutation G12C

# Update the graph based on the filtered cell lines
python -m bio_knowledge_miner.maintenance.update_graph_from_filtered_cells --gene KRAS

# Annotate variants in the graph
python -m bio_knowledge_miner.maintenance.annotate_variants
```

---
## Project Layout
```
/bio_knowledge_miner/
├── main.py                 # Main entry point to run the data collection pipeline
├── config.py               # Configuration for API keys, DB connections, and paths
|
├── data_collection/        # Modules for fetching data from external APIs (PubMed, etc.)
│   ├── api_clients.py
│   └── crawler.py
|
├── text_processing/        # Tools for parsing documents (PDFs) and handling text
│   ├── pdf_parser.py
│   └── ocr_handler.py
|
├── llm_services/           # Services for interacting with LLMs (e.g., entity extraction)
│   └── entity_extractor.py
|
├── knowledge_graph/        # Modules for building and querying the Neo4j graph
│   ├── kg_builder.py
│   └── graph_rag_query.py
|
└── maintenance/            # Scripts for cleaning, enriching, and maintaining graph data
    ├── clean_gene_nodes.py
    ├── fill_compound_structures.py
    └── ...

```

---
## Neo4j Query Examples

Once the graph is built, you can query it directly in the Neo4j Browser.

```cypher
// Find diseases associated with the KRAS gene
MATCH (g:Gene {name:'KRAS'})-[:ASSOCIATED_WITH]->(d:Disease)
RETURN d.name as Disease;

// Find compounds that target KRAS
MATCH (c:Compound)-[:TARGETS]->(g:Gene {name: 'KRAS'})
RETURN c.name as Compound, c.pubchem_id as PubChemID;
```
---

<p align="center">
  <img src="https://github.com/surplus96/BioInfo-SynapseRX/blob/main/data/result/Neo4j_screenshot_01.png" width="820"/>
</p>

<p align="center">
  <img src="https://github.com/surplus96/BioInfo-SynapseRX/blob/main/data/result/Neo4j_screenshot_02.png" width="820"/>
</p>


## License
This project is licensed under the [MIT License](../../LICENSE). 