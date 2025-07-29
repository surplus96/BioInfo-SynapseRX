
[![Code License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## Overview

**SynapseRX** is an open-source platform designed to accelerate the early stages of drug discovery using AI. It automates the process of identifying and optimizing novel candidate compounds for specific protein targets. The name is inspired by the brain's 'synapse', reflecting the project's goal of connecting scattered biomedical data into a cohesive knowledge graph to generate new insights. The 'RX' is a nod to its pharmaceutical application.

The project is composed of two primary modules:

1.  **`bio_knowledge_miner`**: A data pipeline that harvests information from biomedical literature (like PubMed) and public databases. It uses NLP to extract entities (genes, diseases, compounds) and their relationships, building a structured Knowledge Graph in Neo4j.
2.  **`auto_hypothesis_agent`**: An automated agent that uses the Knowledge Graph to run a full-cycle *in-silico* drug discovery campaign. Given a target protein, it generates novel ligand candidates, runs a virtual screening pipeline (docking, ADMET prediction), and generates a final report ranking the most promising compounds.

This project leverages Large Language Models (LLMs) and standard bioinformatics tools to create a powerful, automated workflow for researchers.

## Core Features

-   **Automated Knowledge Graph Construction**: Crawls scientific literature, extracts key entities and relationships using LLMs, and populates a Neo4j graph database.
-   **AI-Powered Ligand Generation**: For a given gene target, it uses a generator to propose novel, relevant candidate compounds, going beyond what's already in the knowledge base.
-   **End-to-End Virtual Screening**: Fully automates a complex pipeline:
    1.  Downloads protein structures from RCSB PDB.
    2.  Identifies binding pockets using `fpocket`.
    3.  Prepares receptor and ligand molecules for simulation.
    4.  Performs molecular docking using `AutoDock Vina`.
    5.  Predicts ADMET properties (drug-likeness, toxicity) for each candidate.
-   **Comprehensive Reporting**: Generates a detailed Markdown report that ranks candidates by a composite score, including their docking energies, 3D complex structures, and predicted ADMET profiles.

<details>
<summary><b>Module 1: `bio_knowledge_miner`</b></summary>

The data backbone of the project. This module is responsible for building and maintaining the biomedical knowledge graph that powers the discovery process. It includes tools for data collection, entity extraction, and graph database management.

 [Click here for the `bio_knowledge_miner` README](./bio_knowledge_miner/README.md)

</details>

<details>
<summary><b>Module 2: `auto_hypothesis_agent`</b></summary>

The "brains" of the operation. This agent executes the virtual screening pipeline. It takes a protein target, generates or retrieves candidate compounds, and runs them through a series of simulations to evaluate their potential as drugs.

 [Click here for the `auto_hypothesis_agent` README](./auto_hypothesis_agent/README.md)

</details>


## Tech Stack

-   **Backend**: Python 3.10
-   **Database**: Neo4j
-   **AI / NLP**: LangChain, OpenAI (for entity extraction)
-   **Bio-simulation**: RDKit, `fpocket`, `AutoDock Vina`
-   **Data Handling**: Pandas, NumPy
-   **Infrastructure**: Docker, Conda


## Installation

1.  **Clone the project**
    ```bash
    git clone https://github.com/surplus96/BioInfo-SynapseRX.git
    cd BioInfo-SynapseRX
    ```

2.  **Set up Environment Variables**
    Create a `.env` file in the project root directory and add your credentials.
    ```env
    # OpenAI API (Required for bio_knowledge_miner)
    OPENAI_API_KEY=your_openai_api_key_here

    # Neo4j Settings (Must match docker-compose.yml)
    NEO4J_URI=bolt://localhost:7687
    NEO4J_USER=neo4j
    NEO4J_PASSWORD=your_secure_password
    ```

3.  **Run Neo4j Database**
    Requires Docker and Docker Compose.
    ```bash
    docker-compose up -d
    ```
    - The Neo4j Browser will be available at `http://localhost:7474`.

4.  **Create and Activate Conda Environment**
    This project uses Conda to manage its complex dependencies.
    ```bash
    conda env create -f environment.yml
    conda activate bio-info
    ```

5.  **Install External Tools (Optional)**
    If you plan to use the `DiffBindFR` tool, install it in editable mode.
    ```bash
    pip install -e external_tools/DiffBindFR
    ```

## Execution Guide

All scripts should be run from the project root directory.

### Step 1: Build the Knowledge Graph (Optional)

If you want to populate the Neo4j database with fresh data from PubMed, run the `bio_knowledge_miner` module. If you are using a pre-built database, you can skip this step.

```bash
# Extract entities from literature and build the graph
# You can provide multiple search queries.
python -m bio_knowledge_miner --queries "KRAS G12C inhibitors[Title/Abstract]" "Sotorasib mechanism of action[Title/Abstract]"

# Run maintenance scripts to refine the graph data
python -m bio_knowledge_miner.maintenance.clean_gene_nodes
python -m bio_knowledge_miner.maintenance.fill_compound_structures --gene KRAS
# ... and other maintenance scripts as needed
```

### Step 2: Run the Drug Discovery Pipeline

This is the main workflow of the project.

1.  **Find Target PDB IDs (Optional Helper)**
    If you're unsure which PDB structures to use, this script can search the RCSB database for you.
    ```bash
    python find_pdb_ids.py --query "KRAS G12C"
    ```
    *Look for structures with good resolution and relevant bound ligands.*

2.  **Execute the Main Pipeline**
    Provide one or more PDB IDs and a target gene name. The script will run the full virtual screening process for each PDB target.
    ```bash
    python run_drug_discovery.py --target_pdb_ids 5V90 6N2J --gene KRAS
    ```
    This command will:
    - Download the PDB files for `5V90` and `6N2J`.
    - Generate novel candidate molecules related to the `KRAS` gene.
    - Run the full screening pipeline (pocket detection, docking, ADMET) for each target.
    - Generate a final report for each target.


## Viewing Results

-   **Raw Simulation Data**: Intermediate and raw output files, such as downloaded PDBs, generated PDBQT files, and docking results, are stored in the `outputs/` directory.
-   **Final Analysis Reports**: Detailed Markdown reports are saved in `outputs/reports/`. Each report is named after its target (e.g., `report_5V90_YYYY-MM-DD.md`) and contains a ranked list of the top candidates with their scores and properties.

## 📄 License

This project is licensed under the [MIT License](LICENSE).