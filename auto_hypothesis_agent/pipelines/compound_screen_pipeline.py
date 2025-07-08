"""Compound screening & evaluation pipeline (스켈레톤)."""

from __future__ import annotations
import argparse
import glob
import logging
import os
import subprocess
from pathlib import Path
from typing import List

import pandas as pd
from rdkit import Chem

from auto_hypothesis_agent import config
from auto_hypothesis_agent.kg_interface import GraphClient
from auto_hypothesis_agent.simulation.admet_predictor import ADMETPredictor
from auto_hypothesis_agent.simulation.binding_energy import BindingEnergyCalculator
from auto_hypothesis_agent.simulation.docking import DockingRunner


def _get_grid_from_pocket(pocket_pdb_file: str) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    """Reads a pocket PDB file from fpocket and calculates the grid box for docking."""
    coords = []
    try:
        with open(pocket_pdb_file) as f:
            for line in f:
                if line.startswith("ATOM") or line.startswith("HETATM"):
                    try:
                        x = float(line[30:38].strip())
                        y = float(line[38:46].strip())
                        z = float(line[46:54].strip())
                        coords.append((x, y, z))
                    except (ValueError, IndexError):
                        logging.warning(f"Could not parse coordinates from line in {pocket_pdb_file}: {line.strip()}")
                        continue
    except OSError as e:
        raise IOError(f"Could not read pocket file {pocket_pdb_file}") from e

    if not coords:
        raise ValueError(f"No pocket atoms (ATOM/HETATM) found in {pocket_pdb_file}")

    min_x = min(c[0] for c in coords)
    max_x = max(c[0] for c in coords)
    min_y = min(c[1] for c in coords)
    max_y = max(c[1] for c in coords)
    min_z = min(c[2] for c in coords)
    max_z = max(c[2] for c in coords)

    center_x = (max_x + min_x) / 2
    center_y = (max_y + min_y) / 2
    center_z = (max_z + min_z) / 2

    # Add 8A margin
    size_x = (max_x - min_x) + 8
    size_y = (max_y - min_y) + 8
    size_z = (max_z - min_z) + 8

    logging.info(f"Calculated grid from pocket: center=({center_x:.2f}, {center_y:.2f}, {center_z:.2f}), size=({size_x:.2f}, {size_y:.2f}, {size_z:.2f})")
    return (center_x, center_y, center_z), (size_x, size_y, size_z)


def run_compound_screen(target_protein: str, target_variant: str, library_sdf: str | None, top_k: int) -> pd.DataFrame:
    """Runs the full compound screening pipeline."""
    logging.info(f"Starting compound screen for {target_protein} ({target_variant})")
    
    temp_sdf_path = None
    try:
        # 1. Find receptor PDB and pocket files
        receptor_glob_pattern = f"outputs/{target_variant}*.pdb"
        receptor_pdb_files = glob.glob(receptor_glob_pattern)
        if not receptor_pdb_files:
            raise FileNotFoundError(f"Receptor PDB not found for variant {target_variant} in outputs/")

        receptor_pdb = receptor_pdb_files[0]
        logging.info(f"Found receptor PDB: {receptor_pdb}")

        receptor_stem = Path(receptor_pdb).stem
        pocket_glob_pattern = f"outputs/{receptor_stem}_out/pockets/*_atm.pdb"
        pocket_files = glob.glob(pocket_glob_pattern)
        if not pocket_files:
            logging.info(f"Pocket PDB file not found in derived path: {os.path.dirname(pocket_glob_pattern)}")

        pocket_file = pocket_files[0]
        logging.info(f"Found pocket file: {pocket_file}")

        # 2. 화합물 라이브러리 가져오기 및 ADMET 예측
        # --------------------------------------------------------------------------
        if library_sdf:
            logging.info(f"Loading compounds from provided SDF: {library_sdf}")
            # SDF에서 화합물 ID와 SMILES 로드
            mols = [m for m in Chem.SDMolSupplier(library_sdf) if m]
            compounds_data = [{
                "ligand_id": m.GetProp("_Name") if m.HasProp("_Name") else f"lig_{i}",
                "smiles": Chem.MolToSmiles(m)
            } for i, m in enumerate(mols)]
            compounds_df = pd.DataFrame(compounds_data)
            
        else:
            logging.info("SDF library not provided. Fetching compounds from Knowledge Graph.")
            client = GraphClient(config.NEO4J_BOLT_URI, config.NEO4J_USER, config.NEO4J_PASSWORD)
            cypher = (
                "MATCH (c:Compound)-[:TARGETS]->(g:Gene) "
                "WHERE g.name STARTS WITH $gene_name AND c.name IS NOT NULL AND c.smiles IS NOT NULL "
                "RETURN c.name AS ligand_id, c.smiles AS smiles"
            )
            results = client.run(cypher, gene_name=target_protein)
            client.close()

            if not results:
                logging.error(f"No compounds found for target {target_protein} in Knowledge Graph.")
                return pd.DataFrame()
            
            compounds_df = pd.DataFrame(results)

            # 임시 SDF 생성
            os.makedirs("outputs/docking", exist_ok=True)
            temp_sdf_path = f"outputs/docking/temp_kg_library_{target_protein}.sdf"
            with Chem.SDWriter(temp_sdf_path) as writer:
                for _, row in compounds_df.iterrows():
                    mol = Chem.MolFromSmiles(row["smiles"])
                    if mol:
                        mol.SetProp("_Name", str(row["ligand_id"]))
                        writer.write(mol)
            library_sdf = temp_sdf_path

        logging.info(f"Predicting ADMET properties for {len(compounds_df)} compounds.")
        admet_predictor = ADMETPredictor()
        admet_df = admet_predictor.batch_predict(df=compounds_df.copy(), smiles_column="smiles")

        # 3. 도킹 실행
        # --------------------------------------------------------------------------
        receptor_pdbqt_path = Path(receptor_pdb).with_suffix(".pdbqt").as_posix()
        if not Path(receptor_pdbqt_path).exists():
            logging.info(f"Receptor PDBQT file not found. Generating from {receptor_pdb}...")
            cmd = [
                "obabel", "-ipdb", receptor_pdb, "-opdbqt", "-O",
                receptor_pdbqt_path, "--partialcharge", "gasteiger", "-xr",
            ]
            subprocess.run(cmd, check=True)

        center, size = _get_grid_from_pocket(pocket_file)
        docking_runner = DockingRunner(grid_center=center, grid_size=size)
        docking_results_df = docking_runner.run(
            receptor_pdbqt=receptor_pdbqt_path,
            library_sdf=library_sdf,
            top_k=top_k
        )

        if docking_results_df.empty:
            logging.warning("Docking returned no results. Aborting.")
            return pd.DataFrame()
        
        # 열 이름 통일: 'compound_id' -> 'ligand_id'
        if "compound_id" in docking_results_df.columns:
            docking_results_df = docking_results_df.rename(columns={"compound_id": "ligand_id"})
        
        # 4. 결과 병합 및 결합 에너지 계산
        # --------------------------------------------------------------------------
        # 도킹 결과와 ADMET 예측 병합
        results_df = pd.merge(docking_results_df, admet_df, on="ligand_id", how="left")

        dg_calculator = BindingEnergyCalculator()
        logging.info(f"Calculating binding energy for {len(results_df)} docked complexes.")
        energy_df = dg_calculator.batch(df=results_df)

        # 최종 결과 병합
        final_results_df = pd.merge(results_df, energy_df, on="ligand_id", how="left")

        # 7. 최종 결과 저장
        report_dir = "outputs/reports"
        os.makedirs(report_dir, exist_ok=True)
        report_path = os.path.join(report_dir, f"screening_report_{target_variant}_{pd.Timestamp.now():%Y%m%d%H%M%S}.csv")
        final_results_df = final_results_df.sort_values(by="docking_score", ascending=True)
        
        # 불필요한 열 제거
        final_results_df = final_results_df.drop(columns=['complex_file'], errors='ignore')
        
        final_results_df.to_csv(report_path, index=False)
        logging.info(f"Screening report saved to {report_path}")

        return final_results_df

    except Exception as e:
        logging.error(f"Compound screening pipeline failed: {e}", exc_info=True)
        return pd.DataFrame()
    finally:
        # Clean up temporary SDF file if created
        if temp_sdf_path and os.path.exists(temp_sdf_path):
            os.remove(temp_sdf_path)
            logging.info(f"Removed temporary SDF file: {temp_sdf_path}")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='[%(asctime)s - %(levelname)s] %(message)s')

    run_compound_screen(
        target_protein="KRAS",
        target_variant="KRAS_KRAS_G12C",
        library_sdf=None,
        top_k=50,
    )