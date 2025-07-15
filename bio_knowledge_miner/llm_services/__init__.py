from typing import Optional
from .base_client import BaseLLMClient
from .. import config

_client: Optional[BaseLLMClient] = None

def get_llm_client() -> BaseLLMClient:
    """
    설정 파일(config.py)에 따라 적절한 LLM 클라이언트의 싱글톤 인스턴스를 반환합니다.

    Returns:
        BaseLLMClient: LLM 클라이언트 인스턴스.
    
    Raises:
        ValueError: 지원하지 않는 LLM_PROVIDER일 경우 발생합니다.
    """
    global _client
    if _client is None:
        provider = config.LLM_PROVIDER.lower()
        if provider == "openai":
            from .openai_client import OpenAIClient
            _client = OpenAIClient(model=config.OPENAI_MODEL)
        elif provider == "ollama":
            from .ollama_client import OllamaClient
            _client = OllamaClient(host=config.OLLAMA_HOST, model=config.OLLAMA_MODEL)
        else:
            raise ValueError(f"지원하지 않는 LLM 제공자입니다: {config.LLM_PROVIDER}")
    return _client 