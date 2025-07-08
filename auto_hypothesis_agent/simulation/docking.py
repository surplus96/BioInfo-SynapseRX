"""DockingRunner – AutoDock Vina 기반 대량 도킹 래퍼.

설치된 Vina 실행 파일(`AUTODOCK_VINA_BIN`)이 감지되면 실제 도킹을 수행하고,
없으면 이전 데모 모드(무작위 점수 생성)로 자동 폴백한다.

Pipeline 호출 예시::

    runner = DockingRunner(grid_center=(10, 12, 34), grid_size=(22, 22, 22))
    df = runner.run("KRAS_G12C.pdbqt", "library.sdf", top_k=200)

※ 리간드 준비는 Meeko(`pip install meeko`)가 설치되어 있으면 자동으로 SMILES→PDBQT 변환을 수행.
   그렇지 않으면 SDF → PDBQT 변환을 위해 OpenBabel(`obabel`) CLI가 필요합니다.
"""

from __future__ import annotations

import os
import random
import string
import subprocess
import tempfile
from pathlib import Path
from typing import List, Sequence, Tuple
import re

import pandas as pd
from rdkit import Chem
from rdkit.Chem import AllChem

from auto_hypothesis_agent.config import AUTODOCK_VINA_BIN, FPOCKET_BIN

_RNG = random.Random(42)


class DockingRunner:
    def __init__(
        self,
        grid_center: Tuple[float, float, float] | None = None,
        grid_size: Tuple[float, float, float] | None = None,
        pocket_mode: str = "auto",  # 'auto', 'bbox', 'fpocket'
    ) -> None:
        """grid_center/size 는 (x,y,z) Å 단위.

        • 지정하지 않으면 수용체 bbox 기반으로 자동 계산(느슨한 큐브).
        • 실제 포켓 좌표를 알고 있으면 명시하는 것을 권장.
        """

        self.grid_center = grid_center
        self.grid_size = grid_size

        self.pocket_mode = pocket_mode

        self.vina_available = _binary_exists(AUTODOCK_VINA_BIN)

        # Detect fpocket availability
        self._fpocket_available = _binary_exists(FPOCKET_BIN)

        # 확인 로그
        if self.vina_available:
            print(f"[DockingRunner] Using AutoDock Vina at '{AUTODOCK_VINA_BIN}'.")
        else:
            print("[DockingRunner] Vina not found – falling back to random scoring mode.")

        if pocket_mode == "fpocket" and not self._fpocket_available:
            print("[DockingRunner] Requested pocket_mode='fpocket' but fpocket binary not found – using bbox.")
            self.pocket_mode = "bbox"
        elif pocket_mode == "auto" and self._fpocket_available:
            self.pocket_mode = "fpocket"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(
        self,
        receptor_pdbqt: str,
        library_sdf: str,
        out_dir: str = "outputs/docking",
        top_k: int = 500,
    ) -> pd.DataFrame:
        """Dock all ligands in *library_sdf* against *receptor_pdbqt*.

        Returns a DataFrame[compound_id, docking_score].
        """

        os.makedirs(out_dir, exist_ok=True)

        if not self.vina_available:
            receptor_name = Path(receptor_pdbqt).stem.split("_")[0]
            df = _generate_random_scores(top_k, Path(out_dir), receptor_name)
        else:
            df = self._dock_with_vina(Path(receptor_pdbqt), Path(library_sdf), Path(out_dir))

        df = df.sort_values("docking_score")[:top_k]
        df.to_csv(Path(out_dir) / "docking_results.csv", index=False)
        return df

    # ------------------------------------------------------------------
    # Vina back-end
    # ------------------------------------------------------------------

    def _dock_with_vina(self, receptor: Path, sdf_file: Path, out_dir: Path) -> pd.DataFrame:
        # Prepare ligand list
        suppl = Chem.SDMolSupplier(str(sdf_file), removeHs=False)
        rows = []
        for mol_idx, mol in enumerate(suppl):
            if mol is None:
                continue
            cid = mol.GetProp(_get_title_prop(mol)) if mol.HasProp("_Name") else f"LIG_{mol_idx}"

            with tempfile.TemporaryDirectory() as tmp:
                lig_pdbqt = Path(tmp) / f"{cid}.pdbqt"
                out_pdbqt = out_dir / f"{Path(receptor).stem}_{cid}_out.pdbqt"
                _mol_to_pdbqt(mol, lig_pdbqt)

                # Auto grid if not set
                if self.grid_center is None or self.grid_size is None:
                    if self.pocket_mode == "fpocket":
                        center, size = _calc_grid_fpocket(receptor)
                        if center is None:
                            center, size = _calc_grid_from_receptor(receptor)
                    else:
                        center, size = _calc_grid_from_receptor(receptor)
                else:
                    center, size = self.grid_center, self.grid_size

                cmd = [
                    AUTODOCK_VINA_BIN,
                    "--receptor",
                    str(receptor),
                    "--ligand",
                    str(lig_pdbqt),
                    "--center_x",
                    f"{center[0]:.3f}",
                    "--center_y",
                    f"{center[1]:.3f}",
                    "--center_z",
                    f"{center[2]:.3f}",
                    "--size_x",
                    f"{size[0]:.3f}",
                    "--size_y",
                    f"{size[1]:.3f}",
                    "--size_z",
                    f"{size[2]:.3f}",
                    "--exhaustiveness",
                    "8",
                    "--num_modes",
                    "1",
                    "--out",
                    str(out_pdbqt),
                ]

                try:
                    out = subprocess.run(cmd, capture_output=True, text=True, check=True)
                    score = _parse_vina_affinity(out.stdout)
                    complex_file = str(out_pdbqt)
                except subprocess.CalledProcessError as e:
                    print(f"[DockingRunner] Vina failed for {cid}: {e.stderr[:120]}")
                    score = None
                    complex_file = None

            rows.append({
                "compound_id": cid,
                "docking_score": score if score is not None else 0.0,
                "complex_file": complex_file,
            })

        return pd.DataFrame(rows)


# -----------------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------------


def _binary_exists(cmd_name: str | None) -> bool:
    if cmd_name is None:
        return False
    from shutil import which

    return which(cmd_name) is not None


def _generate_random_scores(n: int, out_dir: Path, receptor_name: str) -> pd.DataFrame:
    records = []
    for _ in range(n):
        cid = "CAND_" + "".join(_RNG.choices(string.ascii_uppercase + string.digits, k=6))
        score = round(_RNG.uniform(-12, -4), 2)

        # Create a dummy PDB file for the complex
        complex_pdb_path = out_dir / f"{receptor_name}_{cid}.pdb"
        with open(complex_pdb_path, "w") as f:
            f.write("REMARK Fallback dummy file\n")
            f.write(f"REMARK DUMMY COMPLEX FOR {cid}\n")
            f.write("END\n")

        records.append({
            "compound_id": cid,
            "docking_score": score,
            "complex_file": str(complex_pdb_path),
        })
    return pd.DataFrame(records)


def _mol_to_pdbqt(mol: Chem.Mol, out_path: Path) -> None:
    """Convert RDKit Mol → PDBQT using Meeko if available, else OpenBabel."""

    try:
        from meeko import MoleculePreparation  # type: ignore

        prep = MoleculePreparation()
        pdbqt_str: str = prep.prepare(mol)["pdbqt_string"]  # type: ignore[index]
        out_path.write_text(pdbqt_str, encoding="utf-8")
        return
    except ImportError:
        pass

    # Fallback: write to PDB then use obabel
    tmp_pdb = out_path.with_suffix(".pdb")
    Chem.MolToPDBFile(mol, str(tmp_pdb))
    subprocess.run(["obabel", str(tmp_pdb), "-O", str(out_path), "--partialcharge", "gasteiger"], check=True)
    tmp_pdb.unlink(missing_ok=True)


def _calc_grid_from_receptor(receptor_pdbqt: Path) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
    """Very naive grid computation: bounding box of all atoms + 8 Å margin."""

    xs, ys, zs = [], [], []
    with receptor_pdbqt.open() as f:
        for line in f:
            if line.startswith("ATOM") or line.startswith("HETATM"):
                xs.append(float(line[30:38]))
                ys.append(float(line[38:46]))
                zs.append(float(line[46:54]))

    center = (sum(xs) / len(xs), sum(ys) / len(ys), sum(zs) / len(zs))
    size = (
        max(xs) - min(xs) + 8,
        max(ys) - min(ys) + 8,
        max(zs) - min(zs) + 8,
    )
    return center, size


def _parse_vina_affinity(output: str) -> float | None:
    """Extract best affinity (kcal/mol) from vina stdout."""
    best_score = None
    for line in output.splitlines():
        # Vina's output table starts with mode number
        # Example:
        #   1      -7.5         0.000      0.000
        if line.strip().startswith("1 "):
            try:
                best_score = float(line.split()[1])
                break  # Found the first and best score
            except (ValueError, IndexError):
                continue
    return best_score


def _get_title_prop(mol: Chem.Mol) -> str:
    # sdf vs mol2, get the title line property
    return mol.GetPropNames()[0] if mol.GetPropNames() else "_Name"


# -----------------------------------------------------------------------------
# fpocket grid helper
# -----------------------------------------------------------------------------


def _calc_grid_fpocket(receptor_pdbqt: Path):
    """Run fpocket to detect binding pocket center and approximate size.

    Returns (center, size) or (None, None) if fpocket fails.
    """

    if not _binary_exists(FPOCKET_BIN):
        return None, None

    # Convert PDBQT to PDB (fpocket requires PDB) – remove charges columns simply copy.
    tmp_receptor = receptor_pdbqt.with_suffix(".pdb")
    try:
        # crude conversion: copy lines up to END, replace element columns same.
        with open(receptor_pdbqt) as inp, open(tmp_receptor, "w") as out:
            for ln in inp:
                if ln.startswith("ATOM") or ln.startswith("HETATM") or ln.startswith("TER"):
                    out.write(ln[:66] + "\n")
        # Run fpocket
        subprocess.run([FPOCKET_BIN, "-f", str(tmp_receptor)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)

        out_dir = tmp_receptor.stem + "_out"
        info_path = Path(out_dir) / "pockets" / "pocket0" / "pocket0_info.txt"
        if not info_path.exists():
            # new version maybe pockets/info.txt
            info_path = Path(out_dir) / "pockets" / "info.txt"
        if not info_path.exists():
            return None, None

        center = None
        radius = None
        with open(info_path) as f:
            for ln in f:
                if "center" in ln.lower():
                    vals = re.findall(r"[-+]?[0-9]*\.?[0-9]+", ln)
                    if len(vals) >= 3:
                        center = tuple(float(x) for x in vals[:3])
                if "radius" in ln.lower():
                    m = re.search(r"([-+]?[0-9]*\.?[0-9]+)", ln)
                    if m:
                        radius = float(m.group(1))
        if center and radius:
            size = (radius * 2 + 4, radius * 2 + 4, radius * 2 + 4)
            return center, size
    except Exception:
        return None, None
    finally:
        tmp_receptor.unlink(missing_ok=True)

    return None, None 