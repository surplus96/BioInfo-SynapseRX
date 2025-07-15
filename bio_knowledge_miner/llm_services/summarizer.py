import os
from typing import Optional, List, Dict, Any
from . import get_llm_client
from ..prompts import KOREAN_SUMMARY_PROMPT

def summarize_text(text: str, max_tokens: int = 500) -> str:
    """
    주어진 텍스트를 한국어로 요약합니다. (기존 함수 시그니처와 호환)
    """
    client = get_llm_client()
    prompt = KOREAN_SUMMARY_PROMPT.format(text=text)
    
    # kwargs를 통해 모델 특정 파라미터 전달
    kwargs = {'max_tokens': max_tokens}
    
    summary = client.generate(prompt, **kwargs)
    return summary 