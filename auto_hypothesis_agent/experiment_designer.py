"""In silico 실험 설계 모듈 (스켈레톤)."""

# TODO: AlphaFold 3 / CRISPick 연동

from auto_hypothesis_agent.models import ExperimentPlan, ExperimentDesign
from auto_hypothesis_agent.config import OMEGAFOLD_BIN, OMEGAFOLD_SUBBATCH_SIZE
from bio_knowledge_miner.data_collection.uniprot_client import fetch_fasta

import subprocess, tempfile, os, shutil, csv, functools


class ExperimentDesigner:
    """Design experiments based on a hypothesis & parameters (stub)."""

    def design(self, plan: ExperimentPlan) -> ExperimentDesign:
        """Mock AlphaFold / CRISPick calls and return design object."""

        # Derive cell line from gene (very naive mapping)
        gene = plan.parameters.get("gene") if plan.parameters else None
        compound = plan.parameters.get("compound") if plan.parameters else None

        @functools.lru_cache(maxsize=1)
        def _load_mapping() -> dict[str, str]:
            mapping: dict[str, str] = {}
            csv_path = os.path.join(os.path.dirname(__file__), "resources", "gene2cellline.csv")
            if os.path.exists(csv_path):
                with open(csv_path, newline="") as f:
                    for row in csv.reader(f):
                        if len(row) >= 2:
                            mapping[row[0].strip().upper()] = row[1].strip()
            else:
                # fallback minimal mapping
                mapping = {
                    "KRAS": "HCT116",
                    "EGFR": "A431",
                    "BRAF": "HT29",
                }
            return mapping

        gene_to_cell = _load_mapping()
        cell_line = gene_to_cell.get(gene.upper() if gene else "", "HeLa")

        # Fetch protein sequence
        seq = None
        if gene:
            seq = fetch_fasta(gene)
        if not seq:
            seq = "M" * 100  # fallback

        # Simple CRISPR guide: first NGG pam
        pam_index = seq.find("GG")
        if pam_index >= 20:
            guide_seq = seq[pam_index-20:pam_index]
        else:
            guide_seq = seq[:20]

        # Placeholder for predicted structure URL; set to None until populated
        protein_url: str | None = None

        # AlphaFold 3 API call (mock)
        if shutil.which(OMEGAFOLD_BIN):
            try:
                with tempfile.TemporaryDirectory() as tmp:
                    fasta_path = os.path.join(tmp, "input.fasta")
                    with open(fasta_path, "w") as f:
                        f.write(">prot\n" + seq + "\n")
                    out_path = os.path.join(tmp, "out.pdb")
                    cmd = [OMEGAFOLD_BIN, fasta_path, out_path]
                    # 16GB VRAM 메모리 사용량을 고려하여 subbatch_size 조정
                    if OMEGAFOLD_SUBBATCH_SIZE:
                        cmd.extend(["--subbatch_size", str(OMEGAFOLD_SUBBATCH_SIZE)])

                    subprocess.run(cmd, check=True)
                    if os.path.exists(out_path):
                        # For demonstration, move to project output
                        dest = os.path.join("outputs", f"omegafold_{plan.trial_index}.pdb")
                        os.makedirs("outputs", exist_ok=True)
                        shutil.copy(out_path, dest)
                        protein_url = dest
            except Exception:
                protein_url = None

        if protein_url is None:
            # fallback mock URL
            protein_url = f"https://example.com/alphafold/{plan.hypothesis.replace(' ', '_')}.pdb"

        return ExperimentDesign(
            plan=plan,
            protein_structure_url=protein_url,
            crispr_guide_seq=guide_seq,
        ) 