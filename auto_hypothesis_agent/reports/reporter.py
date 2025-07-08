import os
import pandas as pd
from datetime import datetime

class Reporter:
    """Markdown 리포트 생성기(스켈레톤)."""

    def __init__(self, out_dir: str = "outputs/reports"):
        self.out_dir = out_dir
        os.makedirs(self.out_dir, exist_ok=True)

    def markdown_table(self, df: pd.DataFrame) -> str:
        return df.to_markdown(index=False)

    def render(self, gene: str, comparison_df: pd.DataFrame) -> str:
        ts = datetime.now().strftime("%Y-%m-%d")
        md = f"# {gene} Compound Evaluation Report ({ts})\n\n"

        # Identify top 5 candidates by composite score
        top_candidates = (
            comparison_df[comparison_df["set"] == "candidate"]
            .sort_values("composite", ascending=False)
            .head(5)
        )

        md += "## Top 5 Candidates (Composite Score)\n\n"
        md += self.markdown_table(top_candidates) + "\n\n"

        md += "## Detailed Summary (Baseline vs Candidate)\n\n" + self.markdown_table(comparison_df) + "\n"

        md += "---\nGenerated automatically by **Bio-Info Pipeline**. Composite score = mean(Z\_Dock, Z\_ΔG, Z\_SA).\n"

        # 그래프·추가 분석은 향후 구현
        path = os.path.join(self.out_dir, f"report_{gene}_{ts}.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(md)
        return path 