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

import random
from typing import List

import requests
from rdkit import Chem
from rdkit.Chem import AllChem
from urllib.parse import quote_plus

_RNG = random.Random(1234)


class LigandGenerator:
    """SMILES 또는 화합물명 → 3-D SDF 파일 변환기."""

    def __init__(self, max_confs: int = 1):
        self.max_confs = max_confs

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def from_smiles_list(self, smiles_list: List[str], out_path: str = "compound_library.sdf") -> str:
        """Return path to SDF containing 3-D molecules generated from *smiles_list*."""

        writer = Chem.SDWriter(str(out_path))
        n_ok = 0
        for idx, smi in enumerate(smiles_list):
            mol = self._smiles_to_3d_mol(smi)
            if mol is None:
                continue
            # Naming
            name = mol.GetProp("_Name") if mol.HasProp("_Name") else f"LIG_{idx}"
            mol.SetProp("_Name", name)
            writer.write(mol)
            n_ok += 1
        writer.close()

        if n_ok == 0:
            raise ValueError("LigandGenerator: no valid molecules were generated from provided SMILES list.")

        return str(out_path)

    # ------------------------------------------------------------------
    def from_compound_names(self, names: List[str], out_path: str = "compound_library.sdf") -> str:
        """Query PubChem for *names* → SMILES, then delegate to `from_smiles_list`."""
        smiles: List[str] = []
        for nm in names:
            smi = self._fetch_smiles_pubchem(nm)
            if smi:
                smiles.append(smi)
            else:
                print(f"[LigandGenerator] WARN: could not fetch SMILES for '{nm}'.")
        if not smiles:
            raise ValueError("LigandGenerator: no SMILES retrieved from PubChem for provided names.")
        return self.from_smiles_list(smiles, out_path=out_path)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _smiles_to_3d_mol(self, smi: str):
        mol = Chem.MolFromSmiles(smi)
        if mol is None:
            return None
        mol = Chem.AddHs(mol)
        ok = AllChem.EmbedMolecule(mol, AllChem.ETKDG())
        if ok != 0:
            return None
        AllChem.UFFOptimizeMolecule(mol, maxIters=200)
        return mol

    # ------------------------------------------------------------------
    def _fetch_smiles_pubchem(self, name: str) -> str | None:
        """Fetch Canonical SMILES for *name* from PubChem with fallback."""

        name = name.strip()
        encoded = quote_plus(name)

        url = (
            "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/"
            f"{encoded}/property/CanonicalSMILES/TXT"
        )
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200 and resp.text.strip():
                return resp.text.splitlines()[0].strip()

            # Fallback – JSON search to resolve CID, then fetch by CID
            resp_json = requests.get(
                "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/"
                f"{encoded}/JSON",
                timeout=10,
            )
            if resp_json.status_code == 200:
                data = resp_json.json()
                cid = data.get("PC_Compounds", [{}])[0].get("id", {}).get("id", {}).get("cid")
                if cid:
                    resp_cid = requests.get(
                        "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/"
                        f"{cid}/property/CanonicalSMILES/TXT",
                        timeout=10,
                    )
                    if resp_cid.status_code == 200 and resp_cid.text.strip():
                        return resp_cid.text.splitlines()[0].strip()
        except Exception:  # pylint: disable=broad-except
            pass
        return None

    # ------------------------------------------------------------------
    @staticmethod
    def random_smiles(n: int = 10) -> List[str]:
        """Generate *n* trivial random alkane SMILES (for demo)."""
        smiles = []
        for _ in range(n):
            length = _RNG.randint(3, 8)
            smiles.append("C" * length)
        return smiles

    # ------------------------------------------------------------------
    # KG integration helpers
    # ------------------------------------------------------------------

    def from_kg_targets(
        self,
        graph_client,  # auto_hypothesis_agent.kg_interface.GraphClient 인스턴스
        gene: str,
        out_path: str = "compound_library.sdf",
        rel: str = "TARGETS",
    ) -> str:
        """Query Neo4j KG for compounds targeting *gene* and build SDF.

        Parameters
        ----------
        graph_client : GraphClient
            Neo4j 연결 객체.
        gene : str
            HGNC gene symbol (대소문자 무관).
        out_path : str, default "compound_library.sdf"
            저장할 SDF 경로.
        rel : str, default "TARGETS"
            Compound→Gene 관계 타입. Variant 지원이 필요하면 MATCH 절을 수정하세요.
        """

        cypher = (
            f"MATCH (c:Compound)-[:{rel}]->(g:Gene {{name:$g}}) "
            "RETURN DISTINCT c.smiles AS smi"
        )
        rows = graph_client.run(cypher, g=gene.upper())
        smiles = [r["smi"] for r in rows if r.get("smi")]

        if not smiles:
            raise ValueError(f"No SMILES found in KG for gene '{gene}'.")

        return self.from_smiles_list(smiles, out_path=out_path) 