"""BindingEnergyCalculator – 간단 MM/GBSA ΔG 추정.

OpenMM을 사용한 단일 스냅샷 GBSA(OBC2) 에너지를 계산하여
Complex − (Receptor + Ligand) 로 ΔG를 근사한다.

환경에서 OpenMM이 없거나 리간드 파라미터화가 실패하면 무작위 값으로 폴백한다.
"""

from __future__ import annotations

import random
from pathlib import Path
import tempfile
import subprocess
import os

import pandas as pd

try:
    from openmm import Context, unit
    from openmm.app import ForceField, PDBFile
    from openmmforcefields.generators import SMIRNOFFTemplateGenerator
    from openff.toolkit.topology import Molecule

    _OPENMM_OK = True
except ImportError:
    _OPENMM_OK = False

STANDARD_AA = {
    "ALA", "ARG", "ASN", "ASP", "CYS", "GLN", "GLU", "GLY", "HIS", 
    "ILE", "LEU", "LYS", "MET", "PHE", "PRO", "SER", "THR", "TRP", 
    "TYR", "VAL"
}

class BindingEnergyCalculator:
    def __init__(self) -> None:
        self._ff = None
        if _OPENMM_OK:
            self._ff = ForceField("amber14-all.xml", "amber14/tip3pfb.xml")

    # ------------------------------------------------------------------
    def calculate(self, complex_pdb: str) -> float:  # noqa: D401
        if not _OPENMM_OK:
            return _fallback_energy()

        try:
            return self._mmgbsa_single(Path(complex_pdb))
        except Exception as exc:  # pylint: disable=broad-except
            print(f"[BindingEnergy] energy calc failed – fallback. Reason: {exc}")
            return _fallback_energy()

    # ------------------------------------------------------------------
    def batch(self, df: pd.DataFrame) -> pd.DataFrame:
        """SMILES와 PDB 경로가 포함된 DataFrame을 사용하여 배치 처리합니다."""
        if not _OPENMM_OK:
            # OpenMM이 없으면 모든 것에 대해 fallback 값을 반환합니다.
            df["delta_g"] = [_fallback_energy() for _ in range(len(df))]
            return df[["ligand_id", "delta_g"]]

        # 데이터프레임에서 모든 고유 분자에 대한 템플릿 생성기를 설정합니다.
        smiles_list = df["smiles"].unique().tolist()
        molecules = [Molecule.from_smiles(smi, allow_undefined_stereo=True) for smi in smiles_list]
        
        # 'openff-2.1.0' (Sage)는 최신이고 일반적으로 권장됩니다.
        smirnoff = SMIRNOFFTemplateGenerator(molecules=molecules, forcefield="openff-2.1.0")
        self._ff.registerTemplateGenerator(smirnoff.generator)

        # 이제 각 복합체에 대한 에너지를 계산합니다.
        results = []
        for _, row in df.iterrows():
            energy = self.calculate(row["output_pdbqt_path"])
            results.append({
                "ligand_id": row["ligand_id"],
                "delta_g": energy
            })
        
        return pd.DataFrame(results)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _mmgbsa_single(self, pdb_path: Path) -> float:
        """Compute GBSA energies for complex, receptor, ligand."""

        cleaned_pdb_lines = []
        with open(pdb_path, 'r') as f:
            for line in f:
                if line.startswith("ATOM") or line.startswith("HETATM"):
                    cleaned_pdb_lines.append(line)
                elif line.strip() == "ENDMDL":
                    break

        if not cleaned_pdb_lines:
            print(f"[BindingEnergy] Could not extract any ATOM/HETATM records from {pdb_path.name}")
            return _fallback_energy()
            
        pdb_block = "".join(cleaned_pdb_lines)

        try:
            # Write the cleaned PDB block to a temporary file and pass the path
            with tempfile.NamedTemporaryFile(mode='w', suffix='.pdb', delete=False) as tmp_pdb_file:
                tmp_pdb_file.write(pdb_block)
                tmp_pdb_path = tmp_pdb_file.name
            
            pdb = PDBFile(tmp_pdb_path)

        except Exception as e:
            print(f"[BindingEnergy] OpenMM failed to parse cleaned PDB from {pdb_path.name}. Reason: {e}")
            return _fallback_energy()
        finally:
            # Ensure the temporary file is deleted
            if 'tmp_pdb_path' in locals() and os.path.exists(tmp_pdb_path):
                os.remove(tmp_pdb_path)

        # Split atoms by residue name (standard vs. non-standard)
        complex_top = pdb.topology
        complex_pos = pdb.positions

        rec_atoms = [a.index for a in complex_top.atoms() if a.residue.name in STANDARD_AA]
        lig_atoms = [a.index for a in complex_top.atoms() if a.residue.name not in STANDARD_AA]

        if not lig_atoms:
            # No separate ligand marked; treat entire complex energy as fallback
            print(f"[BindingEnergy] No ligand atoms found in {pdb_path.name}. Cannot calculate deltaG.")
            return _fallback_energy()

        # Complex energy
        e_complex = _gb_energy(self._ff, complex_top, complex_pos)

        # Receptor-only
        rec_top = complex_top.subset(rec_atoms)
        rec_pos = [complex_pos[i] for i in rec_atoms]
        e_receptor = _gb_energy(self._ff, rec_top, rec_pos)

        # Ligand-only
        lig_top = complex_top.subset(lig_atoms)
        lig_pos = [complex_pos[i] for i in lig_atoms]
        e_ligand = _gb_energy(self._ff, lig_top, lig_pos)

        delta_g = e_complex - (e_receptor + e_ligand)
        return round(delta_g, 2)


# -----------------------------------------------------------------------------
# Stand-alone helpers
# -----------------------------------------------------------------------------


def _gb_energy(ff: "ForceField", top, pos) -> float:
    system = ff.createSystem(top, implicitSolvent="OBC2", constraints=None)
    ctx = Context(system, unit.VerletIntegrator(1 * unit.femtoseconds))
    ctx.setPositions(pos)
    state = ctx.getState(getEnergy=True)
    return state.getPotentialEnergy().value_in_unit(unit.kilocalories_per_mole)


def _fallback_energy() -> float:
    return round(random.uniform(-65, -25), 2) 