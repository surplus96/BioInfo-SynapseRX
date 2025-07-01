import os
from typing import Optional
from openai import OpenAI
from .. import config

_client: Optional[OpenAI] = None

def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=config.OPENAI_API_KEY)
    return _client


def summarize_text(text: str, max_tokens: int = 150) -> str:
    """LLM을 사용해 긴 텍스트를 요약합니다."""
    if not text:
        return ""
    prompt = (
        "아래 논문 본문의 핵심 내용을 한국어로 5~7줄 이내로 요약하세요.\n\n" + text[:3500]
    )
    try:
        client = _get_client()
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[Summarizer] LLM error: {e}")
        return "" 