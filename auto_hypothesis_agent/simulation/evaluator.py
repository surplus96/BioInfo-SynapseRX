import pandas as pd

class CompoundEvaluator:
    """Baseline 대비 Z-score 및 composite 점수를 계산."""

    def __init__(self, gene: str):
        self.gene = gene.upper()

    def _zscore(self, series: pd.Series) -> pd.Series:
        return (series - series.mean()) / series.std(ddof=0)

    def load_baseline(self) -> pd.DataFrame:
        """Load baseline compounds for the target gene.

        1) CSV `resources/baseline_compounds.csv` 에 gene 필드가 일치하는 행 사용.
        2) 없으면 더미 baseline 3개 반환.
        """

        import os

        csv_path = os.path.join(os.path.dirname(__file__), "../resources/baseline_compounds.csv")
        csv_path = os.path.abspath(csv_path)

        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            df = df[df["gene"].str.upper() == self.gene]
            if not df.empty:
                df = df.drop(columns=["gene"], errors="ignore")
                df["set"] = "baseline"
                return df.reset_index(drop=True)

        # Fallback dummy
        data = {
            "compound_id": ["REF1", "REF2", "REF3"],
            "docking_score": [-8.5, -9.2, -7.8],
            "delta_g": [-45.2, -50.1, -40.3],
            "sa_score": [3.5, 4.0, 3.8],
            "set": ["baseline"] * 3,
        }
        return pd.DataFrame(data)

    def compare(self, candidates: pd.DataFrame) -> pd.DataFrame:
        base = self.load_baseline()
        cand = candidates.copy()
        cand["set"] = "candidate"
        merged = pd.concat([base, cand], ignore_index=True)

        for col in ["docking_score", "delta_g", "sa_score"]:
            merged[f"z_{col}"] = self._zscore(merged[col])

        merged["composite"] = merged[[f"z_{c}" for c in ["docking_score", "delta_g", "sa_score"]]].mean(axis=1)

        # ΔScore = candidate - baseline 평균
        baseline_mean = merged.loc[merged["set"] == "baseline", "composite"].mean()
        merged["delta_score"] = merged["composite"] - baseline_mean
        return merged 