"""LLM 기반 가설 생성기 (스켈레톤)."""

from __future__ import annotations

from typing import List

import os

try:
    import openai
except ImportError:  # pragma: no cover
    openai = None  # type: ignore

class Hypothesis:
    """도메인 가설 오브젝트."""

    def __init__(self, text: str):
        self.text = text.strip()

    def __repr__(self) -> str:  # pragma: no cover
        return f"Hypothesis(text={self.text!r})"

class HypothesisGenerator:
    """지식 그래프 컨텍스트를 기반으로 가설을 생성한다."""

    DEFAULT_PROMPT_TMPL = (
        "You are a biomedical research assistant. Based on the following context from a knowledge "
        "graph, propose {n} novel, specific and testable biological hypotheses that *target disease-driving "
        "genomic elements* (for example: oncogenic gene mutations such as KRAS G12C, or viral genomic "
        "regions such as SARS-CoV-2 ORF1ab) related to the topic '{topic}'. "
        "When referring to human genes use official HGNC symbols, and prefer HGVS nomenclature for variants. "
        "Each hypothesis should be a single sentence that explicitly mentions the genomic element being targeted. "
        "Return the hypotheses as a numbered list.\n\n"  # noqa: E501
        "--- CONTEXT ---\n{context}\n----------------\n"
    )

    def __init__(self, graph_client, model: str | None = None):
        if openai is None:
            raise ImportError("Install openai: pip install openai>=1")

        from auto_hypothesis_agent.config import OPENAI_API_KEY, OPENAI_MODEL

        openai.api_key = os.getenv("OPENAI_API_KEY", OPENAI_API_KEY)
        self.model = model or OPENAI_MODEL
        self.graph_client = graph_client

    # --------------------- internal helpers ---------------------
    def _fetch_context(self, topic: str, limit: int = 20) -> str:
        """간단한 Cypher로 관련 노드·관계 텍스트를 수집해 컨텍스트 문자열 생성."""
        cypher = (
            "MATCH path = (n)-[r*1..2]-(m) "
            "WHERE any(x IN nodes(path) WHERE toLower(x.name) CONTAINS toLower($topic)) "
            "WITH path LIMIT $limit "
            "UNWIND nodes(path) AS nd RETURN DISTINCT nd.name AS name LIMIT $limit"
        )
        try:
            rows = self.graph_client.run(cypher, topic=topic, limit=limit)
        except Exception:  # pragma: no cover
            rows = []
        return "\n".join(r["name"] for r in rows if r.get("name"))

    def _call_llm(self, prompt: str) -> str:
        """LLM 호출 (openai 패키지 v1 이상 호환)."""
        # openai>=1.0.0 API
        if hasattr(openai, "OpenAI"):
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY") or self.graph_client)
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
            )
            return response.choices[0].message.content  # type: ignore

        # openai<1.0.0 (legacy)
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        return response["choices"][0]["message"]["content"]  # type: ignore

    # ----------------------- public API -------------------------
    def generate(self, topic: str, n: int = 5) -> List[Hypothesis]:
        context = self._fetch_context(topic)
        prompt = self.DEFAULT_PROMPT_TMPL.format(topic=topic, n=n, context=context)
        raw = self._call_llm(prompt)

        # 숫자 리스트 파싱
        lines = [ln.lstrip("0123456789). ").strip() for ln in raw.splitlines() if ln.strip()]
        hypotheses = [Hypothesis(txt) for txt in lines[:n]]
        return hypotheses 