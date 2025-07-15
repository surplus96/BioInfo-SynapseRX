"""
End-to-End Drug Discovery Pipeline Runner

This script orchestrates the entire "TO-BE" drug discovery workflow:
1.  Takes a target protein PDB ID as input.
2.  Calls the AI Ligand Generator to create novel candidate molecules (SMILES).
3.  Runs the Compound Screening Pipeline to perform docking and ADMET prediction.
4.  Outputs the final results.
"""

import argparse
import logging
import os
import requests
from pathlib import Path

from auto_hypothesis_agent.utils import setup_logging
from bio_knowledge_miner.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
from auto_hypothesis_agent.core_config import DOCKING_OUTPUT_PATH, OUTPUTS_PATH
from auto_hypothesis_agent.ligand_generation.ai_ligand_generator import LigandGenerator
from auto_hypothesis_agent.pipelines.compound_screen_pipeline import run_screening_pipeline
from auto_hypothesis_agent.simulation.admet_predictor import ADMETPredictor
from auto_hypothesis_agent.reports.reporter import Reporter

def _fetch_pdb_from_rcsb(pdb_id: str) -> Path | None:
    """
    Downloads a PDB file from the RCSB database.

    Args:
        pdb_id: The 4-character PDB ID.

    Returns:
        The path to the downloaded PDB file, or None if download fails.
    """
    pdb_url = f"https://files.rcsb.org/download/{pdb_id}.pdb"
    
    # Ensure the output directory exists
    pdb_dir = Path(OUTPUTS_PATH)
    pdb_dir.mkdir(parents=True, exist_ok=True)
    
    pdb_path = pdb_dir / f"{pdb_id}.pdb"

    logging.info(f"Downloading PDB file for '{pdb_id}' from {pdb_url}...")
    try:
        response = requests.get(pdb_url)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        with open(pdb_path, "w") as f:
            f.write(response.text)
            
        logging.info(f"Successfully saved PDB file to: {pdb_path}")
        return pdb_path
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to download PDB file for {pdb_id}: {e}")
        return None

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Run the full drug discovery pipeline.")
    parser.add_argument(
        "--target_pdb_ids",
        nargs="+",
        required=True,
        help="One or more target PDB IDs to process."
    )
    parser.add_argument(
        "--gene",
        type=str,
        required=True,
        help="The target gene name (e.g., KRAS) for retrieving candidate compounds."
    )
    parser.add_argument(
        "--num_candidates",
        type=int,
        default=100,
        help="Number of candidate molecules to generate/retrieve."
    )
    args = parser.parse_args()

    setup_logging()

    # Create the main output directory if it doesn't exist
    os.makedirs(OUTPUTS_PATH, exist_ok=True)

    # Initialize tools once
    ligand_generator = LigandGenerator()
    admet_predictor = ADMETPredictor()
    reporter = Reporter()

    for pdb_id in args.target_pdb_ids:
        logging.info(f"--- Starting Drug Discovery Pipeline for Target: {pdb_id} ---")
        
        # 1. Download PDB file
        pdb_path = _fetch_pdb_from_rcsb(pdb_id)
        if not pdb_path:
            continue

        # 2. Generate candidate molecules for the specified gene
        logging.info(f"Generating candidate molecules for target gene {args.gene}...")
        candidates_df = ligand_generator.generate_candidates(
            target_gene=args.gene,
            num_candidates=args.num_candidates
        )
        
        if candidates_df.empty:
            logging.error(f"Could not generate any candidates for {pdb_id}. Skipping pipeline for this target.")
            continue

        logging.info(f"Generated {len(candidates_df)} candidates.")

        # 3. Run the screening pipeline with the downloaded PDB and generated molecules
        run_screening_pipeline(
            target_pdb_path=pdb_path,
            candidates_df=candidates_df
        )

        logging.info(f"--- Completed Drug Discovery Pipeline for Target: {pdb_id} ---")

    logging.info("All target processing complete.")


if __name__ == "__main__":
    main() 