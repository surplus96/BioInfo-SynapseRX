
[![Code License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## Overview

Meaning and Concept: Like 'Synapse', the connection point of nerve cells in the brain, this project aims to connect scattered biomedical information to create a knowledge graph, thereby deriving new insights (candidate compounds). 'RX' is a representative symbol for pharmacy and prescriptions.

SynapseRX is an open-source platform that aims to automate and accelerate the early stages of drug discovery, particularly candidate compound discovery and optimization, using the latest AI technologies. This project consists of two main core modules:

1.  **`bio_knowledge_miner`**: Collects and processes information from vast biological and chemical literature and databases to build a Knowledge Graph, systematically accumulating knowledge necessary for drug development.
2.  **`auto_hypothesis_agent`**: Based on the constructed knowledge graph, it establishes therapeutic hypotheses for specific disease targets (e.g., KRAS G12C), discovers effective compounds through a Virtual Screening pipeline, and automatically designs experimental plans.

This project utilizes Retrieval-Augmented Generation (RAG) technology and Large Language Model (LLM) agents to help researchers find promising candidate compounds faster and more accurately.


## Project Structure

```
BioInfo-SynapseRX/
├── auto_hypothesis_agent/     # Hypothesis generation and validation agent
│   ├── pipelines/             # Automation pipelines for compound screening, etc.
│   ├── simulation/            # Simulations like molecular docking, binding energy calculation
│   └── ...
├── bio_knowledge_miner/       # Module for collecting biological data and building knowledge graph
│   ├── data_collection/       # Data collection from papers, databases, etc.
│   ├── knowledge_graph/       # Neo4j knowledge graph construction and querying
│   └── ...
├── data/                      # Various data (PDF papers, extracted information, etc.)
├── outputs/                   # Output folder for screening results, reports, etc.
├── docker-compose.yml         # Configuration for running external services like Neo4j
├── requirements.txt           # Python package dependencies
└── README.md                  # Project root README
```

## Key Features

-   **Automated Knowledge Graph Construction**: Crawls papers from PubMed and other sources, and uses NLP models to extract relationships between genes, diseases, compounds, etc., to automatically build a knowledge graph in a Neo4j database.
-   **AI-based Candidate Compound Recommendation**: When a specific target gene is specified, it intelligently recommends the most promising candidate compound group based on the relationship information within the knowledge graph.
-   **End-to-End In-Silico Screening**: Automatically executes complex molecular simulation pipelines, including protein-ligand docking and ADMET (Absorption, Distribution, Metabolism, Excretion, Toxicity) prediction, for recommended candidate compounds.
-   **Visual Result Reporting**: Automatically generates detailed analysis reports (in Markdown) including the ranking of top candidate compounds, binding energies, and drug-likeness predictions based on screening results.

<details>
<summary><b>1. bio_knowledge_miner</b></summary>

`bio_knowledge_miner` is the data collection and knowledge management backbone of the SynapseRX project. The core goal of this module is to extract, process, and connect biomedical information from various sources, including unstructured data (e.g., scientific papers) and structured data (e.g., ChEMBL, PubChem), to build a massive Knowledge Graph.

This knowledge graph explicitly represents key relationships necessary for drug discovery research (e.g., 'gene-disease association', 'compound-protein interaction', 'drug-side effect') and provides the foundational knowledge needed for the `auto_hypothesis_agent` to generate and validate hypotheses.

 [README](https://github.com/surplus96/BioInfo-SynapseRX/tree/main/bio_knowledge_miner#readme)

</details>

<details>
<summary><b>2. auto_hypothesis_agent</b></summary>

The `auto_hypothesis_agent` is an automated agent that establishes hypotheses based on the knowledge graph and external data, and validates them through computational simulations. The core virtual screening pipeline for compounds in this project is included in this module.

 [README](https://github.com/surplus96/BioInfo-SynapseRX/blob/main/auto_hypothesis_agent/README.md)

</details>


## Tech Stack

-   **Backend**: Python 3.10
-   **Database**: Neo4j (Graph Database)
-   **AI / Machine Learning**: PyTorch, LangChain, PaddleOCR
-   **Bio-simulation**: RDKit, OpenMM, MDAnalysis, OpenBabel
-   **Data Handling**: Pandas, NumPy
-   **Infrastructure**: Docker, Conda


## Installation

1.  **Clone the project**
    ```bash
    git clone <your-repository-url>
    cd Bio-Info
    ```

2.  **Set up environment variables**
    Create a `.env` file in the project root directory and fill in the following content.
    ```env
    # OpenAI API (Optional)
    OPENAI_API_KEY=your_openai_api_key_here

    # Neo4j Settings
    NEO4J_URI=bolt://localhost:7687
    NEO4J_USER=neo4j
    NEO4J_PASSWORD=password
    ```

3.  **Run Neo4j Database**
    Docker must be installed.
    ```bash
    docker-compose up -d
    ```
    - You can access the Neo4j database by navigating to `http://localhost:7474` in your browser.

4.  **Create and activate Conda virtual environment**
    Create a Conda virtual environment using the `environment.yml` file.
    ```bash
    conda env create -f environment.yml
    source activate bio-info
    ```
    > **Note**: `libstdcxx-ng` is included to prevent potential GLIBCXX version conflicts that can occur when running `scipy` and `paddleocr`.

5.  **Install external tools (DiffBindFR)**
    Install the protein-ligand binding prediction tool `DiffBindFR` included in the project.
    ```bash
    pip install -e external_tools/DiffBindFR
    ```
    > The `-e` option installs the package in "editable" mode, so any changes to the source code are immediately reflected.


## Execution Guide

All scripts should be run from the project root directory.

### Step 1: Build and Refine the Knowledge Graph

> **Caution**: This step is necessary when adding new literature information to the database or building the initial database. If you have an already built database, you can skip to Step 2.

```bash
# (1) Extract text and entities from PDF/PubMed, etc.
python -m bio_knowledge_miner.main

# (2) Create/refine graph nodes and relationships based on the extracted data
python -m bio_knowledge_miner.maintenance.clean_gene_nodes
python -m bio_knowledge_miner.maintenance.fill_compound_structures --gene KRAS
python -m bio_knowledge_miner.maintenance.populate_cell_lines
python -m bio_knowledge_miner.maintenance.filter_cell_lines --gene KRAS --mutation G12C
python -m bio_knowledge_miner.maintenance.update_graph_from_filtered_cells --gene KRAS
python -m bio_knowledge_miner.maintenance.annotate_variants
```

### Step 2: Run Drug Candidate Screening

1.  **Search for Target Protein Structure (PDB ID)**
    Check the list of PDB IDs for the target you want to study (e.g., KRAS G12C) from the RCSB PDB database. Select one or more PDB IDs with high resolution and experimental conditions that match your research objectives.
    ```bash
    python find_pdb_ids.py --query "KRAS G12C"
    ```

2.  **Run the Main Pipeline**
    Execute the entire screening pipeline by passing the selected PDB IDs and the target gene name as arguments.
    ```bash
    python run_drug_discovery.py --target_pdb_ids 5V90 6N2J 7YCE --gene KRAS
    ```
    > This script internally queries Neo4j for compounds related to the `KRAS` gene, performs docking simulations of each compound with the `5V90`, `6N2J`, and `7YCE` protein structures, and then generates a final report after ADMET prediction.



## Result Verification

-   **Simulation Result Files**: Downloaded PDB files, docking results (PDBQT), etc., are saved in the `outputs/` directory.
-   **Final Analysis Report**: A detailed report in Markdown format is generated for each target PDB ID in the `outputs/reports/` directory (e.g., `report_5V90_2025-07-15.md`).


## Example Result Explanation

```
1. Final Report Explanation (report_5V90_2025-07-15.md)

- run_compound_id: A temporary ID used only for this run.
- docking_score: Binding energy. The more negative the value, the stronger the binding to the target protein. (The most important efficacy indicator)
- complex_file: Path to the 3D binding structure file.
- compound_id: Unique ID from PubChem. With this ID, you can now accurately track which compound it is.
- name: The name of the compound. (e.g., irinotecan)
- smiles: The 2D structural formula of the compound.
- herg_ic50, cyp_inhibition, logS, sa_score: Safety/drug-likeness/developability indicators, same as before.
- composite: Composite score.

2. Results Analysis: In-depth exploration of the Top 5 candidates

- 1st Place: Irinotecan (docking_score: -11.03)
    - Identity: Irinotecan is an anticancer drug used in actual clinical practice (mainly for colorectal cancer).
    - Interpretation:
        Strong Binding Affinity: An outstanding score of -11.03 indicates that this compound can bind very stably to a specific site on the KRAS G12C protein.
        New Possibility (Off-target effect): The main mechanism of action of irinotecan is Topoisomerase I inhibition, not direct KRAS inhibition. Our simulation may have discovered a previously unknown potential as a new target, KRAS G12C. This is the beauty of in silico screening.
        Drawbacks: The hERG value is on the borderline at 5, and the logS (solubility) is somewhat low, suggesting that drug-likeness improvement may be needed.

- 2nd Place: Brimarafenib (docking_score: -10.43)
    - Identity: The '-rafenib' suffix in the name strongly suggests that this drug belongs to the RAF kinase inhibitor family (e.g., sorafenib, vemurafenib).
    - Interpretation:
        Very High Biological Plausibility: KRAS is an upstream signaling protein that activates RAF. In other words, this compound is a drug that acts directly on the signaling pathway we are targeting (MAPK pathway). It is not a coincidental find, but a very logical candidate.
        Excellent Profile: It has a very high binding affinity, and its safety profile, with a hERG value of 30 and no CYP inhibition, is much better than the 1st place candidate, irinotecan.
        Conclusion: Considering efficacy (high binding affinity), safety, and biological plausibility, it can be said to be the most promising lead compound candidate in this screening.

- 3rd Place: Penicillin-streptomycin (docking_score: -9.621)
    - Identity: Penicillin and streptomycin are antibiotics.
    - Interpretation (Very Important - Trap Card):
        This result is almost 100% a simulation artifact. Looking at the SMILES, it is a mixture of two molecules connected by a '.', and its molecular weight is very large and the structure is complex. Docking programs have difficulty accurately calculating such large and flexible mixture structures, often resulting in unrealistically high scores. The biological possibility of an antibiotic inhibiting KRAS in cancer cells is almost nil. This candidate should be boldly excluded from the analysis.

- 4th Place: RMC-9805 (docking_score: -9.475)
    - Identity: 'RMC' is the abbreviation for Revolution Medicines, a company that is a global leader in the development of targeted therapies for RAS proteins, including KRAS G12C.
    - Interpretation:
        Validation of Screening Methodology: The fact that our pipeline found a compound from a company that specializes in researching KRAS G12C is strong evidence that our screening method is very accurate and valid.
        Drawbacks: The logS is very low at -10.13, indicating a serious solubility problem, and the hERG value is also not good at 5. There are major hurdles for it to be developed into an actual drug.

- 5th Place: HRS-4642 (docking_score: -9.441)
    - Identity: It is one of the molecular targeted anticancer drug candidates that have been studied relatively recently.
    - Interpretation: The binding affinity is excellent, but cyp_inhibition is True, indicating a risk of drug-drug interactions. It is less attractive than the 2nd place candidate, Brimarafenib.

```

## 📄 License

This project is licensed under the [MIT License](LICENSE).