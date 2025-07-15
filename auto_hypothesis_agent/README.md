# `auto_hypothesis_agent`

## Overview

The `auto_hypothesis_agent` is an automated agent that runs a full-cycle *in-silico* drug discovery campaign. It takes a protein target and a set of candidate compounds, and then executes a virtual screening pipeline to evaluate their potential as therapeutic agents.

Its primary input is a target protein structure (PDB file) and a list of candidate molecules (in a DataFrame). Its final output is a detailed report ranking the candidates based on their predicted efficacy and drug-likeness.

## Virtual Screening Pipeline (`pipelines/compound_screen_pipeline.py`)

This is the core workflow of the agent. It automates the entire process of evaluating a library of compounds against a specific protein target.

### Pipeline Stages

1.  **Receptor Preparation**:
    *   Takes a standard PDB file of the target protein.
    *   Converts the PDB file into the `PDBQT` format required by AutoDock Vina.

2.  **Ligand Preparation**:
    *   Accepts a list of candidate compounds as SMILES strings.
    *   Converts these 2D representations into 3D structures and saves them in an `SDF` file, ready for docking.

3.  **Automated Molecular Docking**:
    *   Uses **`fpocket`** to automatically detect potential binding pockets on the surface of the receptor.
    *   Runs **`AutoDock Vina`** to dock each candidate ligand into the most promising binding pocket.
    *   Calculates and records the binding affinity (`docking_score`) for each compound.

4.  **ADMET Prediction**:
    *   For each candidate, it calculates key drug-likeness properties (ADMET: Absorption, Distribution, Metabolism, Excretion, Toxicity) using **RDKit**. This includes metrics like:
        *   Solubility (`LogS`)
        *   Synthetic Accessibility (`SA_score`)
        *   hERG inhibition potential
        *   CYP450 inhibition potential

5.  **Ranking and Reporting**:
    *   Merges all the generated data (docking scores, ADMET properties, compound info) into a single DataFrame.
    *   Calculates a `composite` score based on docking affinity and synthetic accessibility to provide a holistic ranking.
    *   Generates a detailed **Markdown report** (`Reporter`) summarizing the results, highlighting the top-ranked candidates for further investigation.

## Project Layout

```
/auto_hypothesis_agent/
├── pipelines/
│   └── compound_screen_pipeline.py  # Main workflow orchestrator
├── simulation/
│   ├── docking.py           # Wrapper for AutoDock Vina and fpocket
│   ├── admet_predictor.py   # RDKit-based ADMET prediction
│   └── binding_energy.py    # (Future work) MM/GBSA calculations
├── reports/
│   └── reporter.py          # Generates the final Markdown summary
├── ligand_generation/
│   └── ai_ligand_generator.py # Generates novel candidate molecules
└── core_config.py           # Core configuration for paths and settings
```

## How It's Used

This module is not typically run directly. Instead, it is orchestrated by the main `run_drug_discovery.py` script in the project root.

```bash
# This command, run from the root, executes the auto_hypothesis_agent's pipeline
python run_drug_discovery.py --target_pdb_ids 5V90 --gene KRAS
```

The script will:
1.  Invoke the `LigandGenerator` from this module to get candidate molecules.
2.  Trigger the `compound_screen_pipeline` to run the full screening process.
3.  The pipeline then uses the `simulation` and `reports` components to complete the workflow.

---
## License
This project is licensed under the [MIT License](../../LICENSE). 