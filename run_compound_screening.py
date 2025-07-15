"""
Compound Screening Pipeline Runner

This script runs the compound screening pipeline which includes:
1. Loading compounds from a specified CSV file.
2. Preparing the target protein structure (PDB).
3. Running molecular docking for each compound.
4. Predicting ADMET properties.
5. Generating a final screening report.
"""

import argparse
import os
from auto_hypothesis_agent.pipelines.compound_screen_pipeline import run_screening_pipeline
from auto_hypothesis_agent.config import setup_logging

def main():
    """Main function to parse arguments and run the pipeline."""
    parser = argparse.ArgumentParser(description="Run the compound screening pipeline.")
    parser.add_argument(
        "--target_pdb_id",
        type=str,
        required=True,
        help="The PDB ID of the target protein (e.g., '6O24'). The script will download it."
    )
    parser.add_argument(
        "--compounds_csv",
        type=str,
        required=True,
        help="Path to the CSV file containing compounds to screen. Must have 'name' and 'smiles' columns."
    )
    parser.add_argument(
        "--n_workers",
        type=int,
        default=-1,
        help="Number of parallel workers for docking. Defaults to all available CPU cores."
    )
    args = parser.parse_args()

    # Setup project logging
    setup_logging()

    # Check if the compounds file exists
    if not os.path.exists(args.compounds_csv):
        print(f"[ERROR] The specified compounds CSV file does not exist: {args.compounds_csv}")
        return

    # Run the screening pipeline
    run_screening_pipeline(
        target_pdb_id=args.target_pdb_id,
        compounds_csv_path=args.compounds_csv,
        n_workers=args.n_workers
    )

if __name__ == "__main__":
    main() 