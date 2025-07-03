"""Bayesian Optimization 래퍼.

`ax-platform` 라이브러리를 사용해 연속 · 범주형 파라미터 공간에서 실험 Trial 을 제안한다.

현재는 *가설 텍스트* 에 따라 동일한 파라미터 공간을 사용하며, 실제 목표 함수(실험 결과)는 아직
없기 때문에 Trial 제안까지만 수행하고 관측은 하지 않는다.
"""

from __future__ import annotations

from typing import List
import re
from pathlib import Path
import functools

from ax.service.ax_client import AxClient

from auto_hypothesis_agent.models import ExperimentPlan


# -----------------------------------------------------------------------------
# Helper for building search space
# -----------------------------------------------------------------------------

def _base_numeric_parameters():
    """Return numeric/continuous parameters shared across all experiments."""
    return [
        {
            "name": "concentration",
            "type": "range",
            "bounds": [0.1, 10.0],
            "log_scale": True,
        },
        {
            "name": "incubation_time",
            "type": "range",
            "bounds": [1, 72],
        },
    ]


# ------------------------------------------------------------------
# Load HGNC whitelist once at module import
# ------------------------------------------------------------------

@functools.lru_cache(maxsize=1)
def _load_hgnc_set() -> set[str]:
    path = Path(__file__).parent / "../resources/hgnc_symbols.txt"
    if path.exists():
        return {ln.strip().upper() for ln in path.read_text().splitlines() if ln.strip()}
    return set()

HGNC_SET = _load_hgnc_set()


class BOOptimizer:
    """Suggest experiment plans for a given hypothesis.

    `graph_client` 를 받아 가설과 연관된 **세포주(cell_line)** 후보를 Knowledge Graph 에서
    동적으로 조회해 파라미터 공간에 반영한다.
    """

    def __init__(self, graph_client):
        self.graph = graph_client

    # ------------------------------------------------------------
    def suggest(self, hypothesis, n_trials: int = 5) -> List[ExperimentPlan]:
        """Return *n_trials* experiment plans for the given hypothesis."""

        ax_client = AxClient(enforce_sequential_optimization=False)

        # ---------------- dynamic parameter build ----------------
        genes = self._fetch_genes(hypothesis.text)
        compounds = self._fetch_compounds(hypothesis.text)

        if not genes:
            raise ValueError("No candidate genes found for hypothesis; cannot build search space.")

        if not compounds:
            # fallback generic inhibitor
            compounds = ["generic_inhibitor"]

        search_space = _base_numeric_parameters() + [
            {
                "name": "gene",
                "type": "choice",
                "values": genes,
            },
            {
                "name": "compound",
                "type": "choice",
                "values": compounds,
            },
        ]

        try:
            ax_client.create_experiment(
                name=f"exp_{hash(hypothesis.text) & 0xFFFF}",
                parameters=search_space,
                objective_name="dummy",
                minimize=False,
            )
        except TypeError:
            # ax-platform 버전에 따라 objective_name 매개변수가 없을 수 있음
            ax_client.create_experiment(
                name=f"exp_{hash(hypothesis.text) & 0xFFFF}",
                parameters=search_space,
            )

        plans: List[ExperimentPlan] = []
        for _ in range(n_trials):
            params, trial_index = ax_client.get_next_trial()
            # Ax returns parameter dict in native types; no transformation needed.
            plans.append(
                ExperimentPlan(
                    hypothesis=hypothesis.text,
                    parameters=params,
                    trial_index=trial_index,
                )
            )

        return plans

    # -----------------------------------------------------------------
    def _fetch_genes(self, text: str) -> List[str]:
        """Return Gene node names that appear in text (case-insensitive contains)."""
        # ----------------------------------------------
        # 1) Tokenize hypothesis text to upper-case words/digits (3-10 chars)
        raw_tokens = re.findall(r"[A-Za-z0-9]{3,10}", text)
        processed: set[str] = set()
        for tok in raw_tokens:
            # Strip mutation suffix (letters before first digit)
            m = re.match(r"([A-Za-z]+)[0-9]", tok)
            if m:
                tok = m.group(1)
            # Upper-case symbol
            processed.add(tok.upper())

        if not processed:
            return []

        # 2) Query graph for symbols that actually exist
        cypher = (
            "UNWIND $cands AS sym\n"
            "MATCH (g:Gene {name: sym})\n"
            "RETURN DISTINCT g.name AS name"
        )
        try:
            rows = self.graph.run(cypher, cands=list(processed))
            symbols = [r["name"] for r in rows if r.get("name")]
        except Exception:
            symbols = []

        # 3) If none matched, fallback to previous fuzzy search (contains)
        if not symbols:
            alt_cypher = (
                "MATCH (g:Gene) WHERE toLower($text) CONTAINS toLower(g.name)\n"
                "RETURN DISTINCT g.name AS name LIMIT 20"
            )
            try:
                rows = self.graph.run(alt_cypher, text=text.lower())
                symbols = [r["name"] for r in rows if r.get("name")]
            except Exception:
                symbols = []

        # 4) Apply HGNC whitelist if available
        if HGNC_SET:
            symbols = [s for s in symbols if s.upper() in HGNC_SET]

        # 5) Relationship-based filtering: ensure gene is linked to at least one compound or disease
        rel_filtered: List[str] = []
        for sym in symbols:
            rel_cypher = (
                "MATCH (g:Gene {name:$sym})\n"
                "WHERE (g)<-[:TARGETS]-(:Compound) OR (g)-[:ASSOCIATED_WITH]->(:Disease)\n"
                "RETURN g LIMIT 1"
            )
            try:
                rows = self.graph.run(rel_cypher, sym=sym)
                if rows:
                    rel_filtered.append(sym)
            except Exception:
                pass

        # keep max 10
        return rel_filtered[:10]

    # -----------------------------------------------------------------
    def _fetch_compounds(self, text: str) -> List[str]:
        cypher = (
            "MATCH (c:Compound) \n"
            "WHERE toLower($t) CONTAINS toLower(c.name) \n"
            "RETURN DISTINCT c.name AS name LIMIT 20"
        )
        try:
            rows = self.graph.run(cypher, t=text)
            return [r["name"] for r in rows if r.get("name")]
        except Exception:
            return [] 