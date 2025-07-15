from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseLLMClient(ABC):
    """
    모든 LLM 서비스 클라이언트를 위한 추상 기반 클래스입니다.
    """
    @abstractmethod
    def generate(self, prompt: str, **kwargs: Any) -> str:
        """
        주어진 프롬프트를 기반으로 텍스트를 생성합니다.

        Args:
            prompt (str): LLM에 전달할 프롬프트.
            **kwargs: 모델 특정 파라미터 (예: temperature, max_tokens).

        Returns:
            str: 생성된 텍스트.
        """
        pass 