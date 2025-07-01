import re
from typing import List, Dict
from .summarizer import _get_client
from .. import config

GENE_PATTERN = re.compile(r"\b[A-Z0-9]{3,}\b")


def regex_extract(text: str) -> List[str]:
    """단순 정규식으로 유전자/단백질 후보 토큰 추출"""
    return list(set(GENE_PATTERN.findall(text)))


def llm_extract_entities(text: str, max_entities: int = 10) -> Dict[str, List[str]]:
    """LLM에게 주요 엔터티(유전자, 질병, 화합물)를 추출하도록 요청"""
    prompt = (
        "아래 텍스트에서 유전자/단백질, 질병, 화합물(약물) 엔터티를 최대 10개씩 추출하여,"
        " JSON 형식({'gene':[], 'disease':[], 'compound':[]})으로만 답하세요. 다른 말은 쓰지 마세요.\n\n" + text[:3500]
    )
    try:
        client = _get_client()
        res = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.2,
        )
        import json

        return json.loads(res.choices[0].message.content)
    except Exception as e:
        print(f"[EntityExtractor] LLM error: {e}")
        # fallback
        return {"gene": regex_extract(text)[:max_entities], "disease": [], "compound": []} 