from __future__ import annotations
from pathlib import Path
from pydantic import BaseModel
from typing import Dict, Any, List

# --- Data models for Compound Screening Pipeline ---

class DockingInput(BaseModel):
    """Data model for a single docking job input."""
    pdb_file: Path
    smiles: str
    ligand_name: str

class DockingResult(BaseModel):
    """Data model for a single docking job result."""
    ligand_name: str
    pdbqt_file: Path
    affinity: float # Binding affinity in kcal/mol
    
class ScreeningResult(BaseModel):
    """Final result for a single screened compound."""
    ligand_name: str
    smiles: str
    docking_result: DockingResult
    admet_properties: Dict[str, Any]


class ExperimentPlan(BaseModel):
    """Bayesian Optimizer 가 제안한 단일 실험 플랜."""

    hypothesis: str
    parameters: Dict[str, Any]
    trial_index: int


# ---------------------------------------------------------------------------
# Down-stream 설계 결과 & SOP 모델


class ExperimentDesign(BaseModel):
    """In-silico 예측 및 설계 결과를 담는 모델."""

    plan: ExperimentPlan
    protein_structure_url: str | None = None  # AlphaFold 3 결과 (stub)
    crispr_guide_seq: str | None = None       # CRISPick 가이드 서열 (stub)


class SOP(BaseModel):
    """Protocol-GPT 로 생성된 SOP (Markdown + JSON-LD)."""

    markdown: str
    jsonld: Dict[str, Any] 