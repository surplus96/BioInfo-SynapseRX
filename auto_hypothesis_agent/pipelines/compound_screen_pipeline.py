"""Compound screening & evaluation pipeline."""

from __future__ import annotations

import logging
import pandas as pd
from typing import List
from pathlib import Path
import tempfile
import os

from auto_hypothesis_agent.simulation.docking import DockingRunner, prepare_receptor
from auto_hypothesis_agent.simulation.admet_predictor import ADMETPredictor
from auto_hypothesis_agent.reports.reporter import Reporter
from auto_hypothesis_agent.core_config import DOCKING_OUTPUT_PATH
from rdkit import Chem
from rdkit.Chem import AllChem


def run_screening_pipeline(
    target_pdb_path: Path,
    candidates_df: pd.DataFrame,
    n_workers: int = -1,
):
    """
    Runs the full compound screening pipeline for a given target and a DataFrame of candidates.
    This function now acts as a high-level coordinator.
    """
    target_pdb_id = target_pdb_path.stem
    logging.info(f"Starting compound screening pipeline for target: {target_pdb_id}")

    # Create a temporary compound_id for this specific run, to avoid clashes if the same compound
    # is docked against multiple targets.
    candidates_df['run_compound_id'] = [f"{target_pdb_id}_candidate_{i+1:04d}" for i in range(len(candidates_df))]

    # 1. Prepare receptor PDB -> PDBQT
    receptor_pdbqt_path = prepare_receptor(target_pdb_path)
    if not receptor_pdbqt_path:
        logging.error(f"Failed to prepare receptor for {target_pdb_id}. Aborting.")
        return

    # 2. Prepare ligands in a temporary SDF file for the DockingRunner
    # DockingRunner's current implementation expects an SDF file.
    with tempfile.NamedTemporaryFile(mode="w", suffix=".sdf", delete=False) as tmp_sdf:
        writer = Chem.SDWriter(tmp_sdf.name)
        for _, row in candidates_df.iterrows():
            mol = Chem.MolFromSmiles(row['smiles'])
            if mol:
                mol.SetProp("_Name", row['run_compound_id'])
                AllChem.EmbedMolecule(mol)
                AllChem.MMFFOptimizeMolecule(mol)
                writer.write(mol)
        writer.close()
        ligand_sdf_path = tmp_sdf.name
    
    logging.info(f"Prepared {len(candidates_df)} ligands in temporary SDF file: {ligand_sdf_path}")

    # 3. Instantiate and run the docking process
    # The runner will handle pocket detection and receptor preparation internally.
    runner = DockingRunner(pocket_mode="fpocket")  # Use fpocket to find the pocket
    docking_results_df = runner.run(
        receptor_pdbqt=str(receptor_pdbqt_path),
        library_sdf=ligand_sdf_path,
        out_dir=DOCKING_OUTPUT_PATH
    )

    # Clean up the temporary SDF file
    os.remove(ligand_sdf_path)

    if docking_results_df.empty:
        logging.error("Docking process failed to produce results. Aborting pipeline.")
        return

    # The docking result has 'compound_id', which is our temporary 'run_compound_id'.
    # Rename it to merge with the original candidates_df.
    docking_results_df.rename(columns={'compound_id': 'run_compound_id'}, inplace=True)
    merged_df = pd.merge(docking_results_df, candidates_df, on="run_compound_id")

    # 4. Predict ADMET properties
    admet_predictor = ADMETPredictor()
    admet_results_df = admet_predictor.predict_from_df(merged_df, smiles_col='smiles', name_col='run_compound_id')

    # 5. Merge results
    # ADMET results also use 'run_compound_id' as 'compound_id'. Rename for merging.
    admet_results_df.rename(columns={'compound_id': 'run_compound_id'}, inplace=True)
    final_df = pd.merge(merged_df, admet_results_df, on="run_compound_id", how="left")
    
    # Add the 'set' column to identify these as candidate results
    final_df['set'] = 'candidate'
    
    # Calculate composite score for ranking.
    # Lower docking_score is better, and lower SA_score is better.
    # We convert them to Z-scores and invert them so that a higher composite score is better.
    if 'docking_score' in final_df.columns and 'Synthetic Accessibility' in final_df.columns:
        # Fill NaN values that might cause issues with Z-score calculation
        final_df['docking_score'].fillna(final_df['docking_score'].mean(), inplace=True)
        final_df['Synthetic Accessibility'].fillna(final_df['Synthetic Accessibility'].mean(), inplace=True)

        final_df['docking_z'] = (final_df['docking_score'] - final_df['docking_score'].mean()) / final_df['docking_score'].std()
        final_df['sa_z'] = (final_df['Synthetic Accessibility'] - final_df['Synthetic Accessibility'].mean()) / final_df['Synthetic Accessibility'].std()
        
        # The reporter expects a higher composite score to be better.
        final_df['composite'] = (final_df['docking_z'] * -1 + final_df['sa_z'] * -1) / 2
        logging.info("Calculated composite score from docking score and synthetic accessibility.")
    elif 'docking_score' in final_df.columns:
        # Fallback to using only docking score if SA is not available
        final_df['docking_score'].fillna(final_df['docking_score'].mean(), inplace=True)
        final_df['composite'] = final_df['docking_score'] * -1
        logging.warning("Using inverted 'docking_score' as a fallback composite score.")
    else:
        # If no scores are available, create a dummy composite score to avoid crashing.
        final_df['composite'] = 0.0
        logging.error("Could not find any scores to calculate a composite score.")

    # 6. Generate final report
    if final_df is not None and not final_df.empty:
        logging.info("Generating final report...")
        reporter = Reporter() # Use default output directory
        report_path = reporter.render(
            gene=target_pdb_id, # Use PDB ID as a stand-in for gene name
            comparison_df=final_df
        )
        logging.info(f"Screening report saved to: {report_path}")
        return report_path
    else:
        logging.warning("No results to report, skipping report generation.")
        return None


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='[%(asctime)s - %(levelname)s] %(message)s')

    # Example usage (replace with actual arguments)
    target_pdb_path = Path("outputs/docking/4AKE.pdb") # Example PDB path
    candidate_smiles = [
        "CCO", "CC(=O)O", "C1=CC=C(C=C1)C(=O)O", "C1=CC=C(C=C1)C(=O)O",
        "C1=CC=C(C=C1)C(=O)O", "C1=CC=C(C=C1)C(=O)O", "C1=CC=C(C=C1)C(=O)O",
        "C1=CC=C(C=C1)C(=O)O", "C1=CC=C(C=C1)C(=O)O", "C1=CC=C(C=C1)C(=O)O"
    ] # Example SMILES list

    run_screening_pipeline(
        target_pdb_path=target_pdb_path,
        candidate_smiles=candidate_smiles,
        n_workers=1, # Example number of workers
    )