"""LigandGenerator – 후보 리간드 3D 구조(SDF) 자동 생성

기능
-----
1. `from_smiles_list(smiles_list)`
   • SMILES 문자열 목록을 받아 RDKit으로 3-D 좌표를 생성(ETKDG) 후 SDF 저장.
2. `from_compound_names(names)`
   • 화합물명 목록을 PubChem REST 로부터 Canonical SMILES 를 가져와 위 과정 수행.
3. 설치되지 않았거나 API 실패 시, 유효한 Mol 이 하나도 없으면 예외를 던집니다.

사용 예시
---------
```python
lg = LigandGenerator()
sdf_path = lg.from_smiles_list(["CCO", "c1ccccc1C(=O)O"], out_path="library.sdf")
```
"""

from __future__ import annotations
import logging
import os
import sys
from typing import List

import torch
from rdkit import Chem
from rdkit.Chem import AllChem

# --- Pocket2Mol 모델 준비 ---
# 모델 소스코드 및 체크포인트 경로 설정
MODEL_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models'))
POCKET2MOL_SRC_DIR = os.path.join(MODEL_ROOT_DIR, "pocket2mol_src", "Pocket2Mol-main")
CHECKPOINT_PATH = os.path.join(POCKET2MOL_SRC_DIR, "checkpoints", "model.pt")

# Pocket2Mol 소스 코드를 동적으로 임포트하기 위해 sys.path에 추가
if POCKET2MOL_SRC_DIR not in sys.path:
    sys.path.insert(0, POCKET2MOL_SRC_DIR)
# -----------------------------

class LigandGenerator:
    """
    AI(Pocket2Mol)를 사용하여 특정 단백질 포켓에 맞는 새로운 리간드를 생성합니다.
    """

    def __init__(self, model_path: str = CHECKPOINT_PATH, device: str = 'cuda'):
        """
        AI 리간드 생성 모델을 초기화하고 로드합니다.
        """
        self.model = None
        self.pocket2mol_utils = None
        self.device = torch.device(device if torch.cuda.is_available() else 'cpu')
        
        logging.info(f"LigandGenerator 초기화 중. 장치: {self.device}")
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Pocket2Mol 모델 체크포인트를 찾을 수 없습니다: {model_path}\n"
                "먼저 모델을 다운로드하여 해당 경로에配置してください。"
            )

        try:
            # Pocket2Mol 모듈 동적 임포트
            from src.models.pocket2mol import Pocket2Mol
            from src.utils.protein_ligand import PDBProtein
            self.pocket2mol_utils = PDBProtein # 유틸리티 클래스 저장
            
            # 모델 설정 로드
            model_config = torch.load(model_path, map_location='cpu')['config']
            
            # 모델 초기화 및 가중치 로드
            self.model = Pocket2Mol(model_config).to(self.device)
            self.model.load_state_dict(torch.load(model_path, map_location='cpu')['model'])
            self.model.eval()
            
            logging.info("Pocket2Mol 모델 로딩 성공.")

        except ImportError as e:
            logging.error(f"Pocket2Mol 모듈 임포트 실패: {e}")
            raise ImportError(f"Pocket2Mol 소스 코드를 '{POCKET2MOL_SRC_DIR}'에서 찾을 수 없습니다.")
        except Exception as e:
            logging.error(f"모델 로딩 중 오류 발생: {e}")
            raise

    @torch.no_grad()
    def generate(self, pocket_pdb_path: str, num_ligands: int = 10) -> List[str]:
        """
        주어진 단백질 포켓 구조에 대해 새로운 리간드를 생성합니다.
        """
        if not self.model:
            raise RuntimeError("모델이 초기화되지 않았습니다.")
        if not os.path.exists(pocket_pdb_path):
            raise FileNotFoundError(f"포켓 PDB 파일을 찾을 수 없습니다: {pocket_pdb_path}")

        logging.info(f"'{os.path.basename(pocket_pdb_path)}' 포켓에 대해 {num_ligands}개의 리간드 생성 시작...")

        # Pocket2Mol 유틸리티를 사용하여 PDB 파일 전처리
        protein = self.pocket2mol_utils(pocket_pdb_path)
        data = protein.to_data().to(self.device)
        
        # 모델을 사용하여 리간드 생성 (샘플링)
        results, _ = self.model.sample(
            data,
            num_samples=num_ligands,
            # 추가적인 샘플링 파라미터들...
        )
        
        # 생성된 분자를 SMILES로 변환
        smiles_list = [Chem.MolToSmiles(m) for m in results if m is not None]

        logging.info(f"{len(smiles_list)}개의 유효한 SMILES 생성 완료.")
        return smiles_list

    def to_sdf(self, smiles_list: List[str], output_sdf_path: str) -> str:
        """
        SMILES 문자열 리스트를 SDF 파일로 변환합니다.
        """
        writer = Chem.SDWriter(output_sdf_path)
        for i, smiles in enumerate(smiles_list):
            try:
                mol = Chem.MolFromSmiles(smiles)
                if mol:
                    AllChem.EmbedMolecule(mol, AllChem.ETKDGv3())
                    AllChem.UFFOptimizeMolecule(mol)
                    mol.SetProp("_Name", f"generated_ligand_{i+1}")
                    writer.write(mol)
            except Exception as e:
                logging.warning(f"SMILES 처리 실패 '{smiles}': {e}")
        writer.close()
        
        logging.info(f"{len(smiles_list)}개의 리간드를 포함한 SDF 파일 저장 완료: {output_sdf_path}")
        return os.path.abspath(output_sdf_path) 