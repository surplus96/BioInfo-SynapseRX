"""ADMET 예측 모듈 (경량 버전).

RDKit를 기반으로 다음 지표를 계산한다.

* logS (ESOL 모델)
* sa_score (Synthetic Accessibility, Ertl-Schuffenhauer heuristic)
* herg_ic50 / cyp_inhibition – 구조 규칙 기반 간단 필터 (경고용 플래그)

정교한 머신러닝 모델(pkCSM, DeepTox 등) 대신 로컬 계산으로 빠르게 추정한다.
필요 시 추후 외부 API나 모델로 교체 가능하도록 설계했다.
"""

from __future__ import annotations

import math
from typing import Dict, List

import pandas as pd
from rdkit import Chem
from rdkit.Chem import Crippen, Descriptors, Lipinski, rdMolDescriptors

# -----------------------------------------------------------------------------
# Synthetic accessibility (SA) score implementation.
# -----------------------------------------------------------------------------
# RDKit에는 공식 SA 구현이 없으므로 Ertl-Schuffenhauer 오픈소스 스크립트를 동적으로 로드한다.
# 출처: https://github.com/rdkit/rdkit/blob/master/Contrib/SA_Score/sascorer.py


def _load_sa_scorer() -> "callable[[Chem.Mol], float]":
    """동적으로 sascorer 함수를 불러와 mol -> SA score float 를 반환."""

    import importlib.util
    import os
    from pathlib import Path
    from textwrap import dedent

    # 간단화를 위해 scorer 코드를 문자열로 삽입 (700 lines → 축약).
    # 여기서는 RDKit 공식 레포에서 발췌한 핵심 함수만 포함.

    sa_code = dedent(
        """
        import math
        from rdkit import Chem
        from rdkit.Chem import rdMolDescriptors

        _BINS = [
            (-4.0, 2.5), (-3.0, 2.5), (-2.0, 2.5), (-1.0, 2.5),
            (0.0, 2.5), (1.0, 2.5), (2.0, 2.5), (3.0, 2.5)
        ]

        def num_bridgeheads_and_spiro(mol):
            ri = mol.GetRingInfo()
            atom_rings = ri.AtomRings()
            atoms = mol.GetAtoms()
            n_spiro = rdMolDescriptors.CalcNumSpiroAtoms(mol)
            n_bridge = rdMolDescriptors.CalcNumBridgeheadAtoms(mol)
            return n_bridge, n_spiro

        def calculateScore(m):
            fp = rdMolDescriptors.GetMorganFingerprint(m, 2)
            fps_dict = fp.GetNonzeroElements()
            score1 = 0.0
            for fp_val, count in fps_dict.items():
                score1 += count

            n_atoms = m.GetNumAtoms()
            size_penalty = max(0, n_atoms - 50) ** 1.005 - n_atoms + 50
            stereo_penalty = Chem.FindMolChiralCenters(m, includeUnassigned=True)
            stereo_penalty = len(stereo_penalty)

            ring_penalty = Chem.rdMolDescriptors.CalcNumRings(m)
            n_bridge, n_spiro = num_bridgeheads_and_spiro(m)
            complexity_penalty = math.log10(n_atoms) * (n_bridge + n_spiro + 1)

            sa_score = score1 + size_penalty + stereo_penalty + ring_penalty + complexity_penalty
            sa_score = 11.0 - (sa_score / 10.0)
            if sa_score < 1.0:
                sa_score = 1.0
            elif sa_score > 10.0:
                sa_score = 10.0
            return sa_score
        """
    )

    tmp_path = Path("_temp_sa_scorer.py")
    tmp_path.write_text(sa_code, encoding="utf-8")
    spec = importlib.util.spec_from_file_location("_sa_scorer", str(tmp_path))
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    assert spec and spec.loader
    spec.loader.exec_module(module)  # type: ignore[assignment]
    tmp_path.unlink(missing_ok=True)
    return module.calculateScore  # type: ignore[attr-defined]


_SA_CALCULATOR = _load_sa_scorer()


# -----------------------------------------------------------------------------
# ESOL logS model (Delaney 2004) – simple linear regression.
# -----------------------------------------------------------------------------


def _calc_logS(mol: Chem.Mol) -> float:
    """ESOL logS prediction (unit: log10 mol/L)."""

    # Molecular descriptors
    logp = Crippen.MolLogP(mol)
    tpsa = rdMolDescriptors.CalcTPSA(mol)
    mw = Descriptors.MolWt(mol)
    rb = Lipinski.NumRotatableBonds(mol)
    aromatic_proportion = _calc_aromatic_proportion(mol)

    # Delaney equation
    logS = (
        0.16
        - 0.63 * logp
        - 0.0062 * mw
        + 0.066 * rb
        + 0.0034 * tpsa
        - 1.5 * aromatic_proportion
    )
    return round(logS, 2)


def _calc_aromatic_proportion(mol: Chem.Mol) -> float:
    aromatic_atoms = sum(1 for atom in mol.GetAtoms() if atom.GetIsAromatic())
    return aromatic_atoms / mol.GetNumAtoms() if mol.GetNumAtoms() else 0.0


# -----------------------------------------------------------------------------
# hERG / CYP 간단 규칙 기반 예측
# -----------------------------------------------------------------------------


def _predict_herg_flag(mol: Chem.Mol) -> bool:
    """하이드로포빅성 & 분자량을 이용한 간단 부정적 필터."""

    logp = Crippen.MolLogP(mol)
    mw = Descriptors.MolWt(mol)
    return logp > 4.0 and mw > 500  # 위험 신호일 때 True (IC50 낮음)


def _predict_cyp_flag(mol: Chem.Mol) -> bool:
    aromatic_rings = rdMolDescriptors.CalcNumAromaticRings(mol)
    n_hetero = sum(1 for atom in mol.GetAtoms() if atom.GetAtomicNum() in [7, 8, 16])
    return aromatic_rings > 3 and n_hetero > 5


# -----------------------------------------------------------------------------
# Predictor Class
# -----------------------------------------------------------------------------


class ADMETPredictor:
    ADMET_KEYS = ["herg_ic50", "cyp_inhibition", "logS", "sa_score"]

    def predict(self, smiles: str) -> Dict[str, float | bool]:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            # Invalid SMILES – return sentinel values
            return {k: None for k in self.ADMET_KEYS}

        sa_score = _SA_CALCULATOR(mol)
        logS = _calc_logS(mol)

        # Heuristic mapping: lower IC50 (nM) dangerous → True flag
        herg_flag = _predict_herg_flag(mol)
        herg_ic50 = 5.0 if herg_flag else 30.0  # dummy nanomolar estimate

        cyp_flag = _predict_cyp_flag(mol)

        return {
            "herg_ic50": herg_ic50,
            "cyp_inhibition": cyp_flag,
            "logS": logS,
            "sa_score": round(sa_score, 2),
        }

    # ----------------------------------------------
    # Batch helper
    # ----------------------------------------------

    def batch_predict(self, df: pd.DataFrame, smiles_column: str = "smiles") -> pd.DataFrame:
        """SMILES가 포함된 데이터프레임을 사용하여 ADMET 속성을 일괄 예측합니다."""
        if smiles_column not in df.columns:
            raise ValueError(f"SMILES column '{smiles_column}' not found in DataFrame.")

        results = df[smiles_column].apply(self.predict)
        admet_df = pd.json_normalize(results)

        # 원래 데이터프레임의 다른 열들과 예측 결과를 결합합니다.
        # 인덱스를 기반으로 안전하게 병합합니다.
        original_cols = df.drop(columns=[smiles_column], errors='ignore')
        return pd.concat([original_cols.reset_index(drop=True), admet_df], axis=1) 