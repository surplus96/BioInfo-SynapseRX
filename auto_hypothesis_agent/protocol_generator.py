"""Protocol-GPT 기반 SOP 생성기 (Mock).

실제 GPT 호출 대신 간단한 Markdown 템플릿과 JSON-LD 메타데이터를 생성한다.
"""

from datetime import datetime

from auto_hypothesis_agent.models import ExperimentDesign, SOP


class ProtocolGenerator:
    """Render ExperimentDesign into SOP (Markdown + JSON-LD)."""

    def render(self, design: ExperimentDesign) -> SOP:
        md = (
            f"# SOP for Trial {design.plan.trial_index}\n\n"
            f"**Hypothesis:** {design.plan.hypothesis}\n\n"
            "## Parameters\n" + "\n".join(
                f"- **{k}**: {v}" for k, v in design.plan.parameters.items()
            )
            + "\n\n## Predicted Protein Structure\n"
            f"Download PDB: {design.protein_structure_url}\n\n"
            "## CRISPR Guide Sequence\n"
            f"`{design.crispr_guide_seq}`\n"
        )

        jsonld = {
            "@context": "https://schema.org/",
            "@type": "HowTo",
            "name": f"SOP Trial {design.plan.trial_index}",
            "dateCreated": datetime.utcnow().isoformat(),
            "hypothesis": design.plan.hypothesis,
            "parameters": design.plan.parameters,
            "proteinStructure": design.protein_structure_url,
            "crisprGuide": design.crispr_guide_seq,
            "cellLine": design.plan.parameters.get("cell_line"),
        }

        return SOP(markdown=md, jsonld=jsonld) 