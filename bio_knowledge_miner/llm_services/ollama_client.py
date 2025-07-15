import requests
import json
from typing import Optional, Dict, Any

from .base_client import BaseLLMClient
from .. import config

class OllamaClient(BaseLLMClient):
    """
    Ollama API와 상호작용하여 텍스트 생성을 수행하는 클라이언트입니다.
    """
    def __init__(self, host: Optional[str] = None, model: Optional[str] = None):
        self.host = host or config.OLLAMA_HOST
        self.model = model or config.OLLAMA_MODEL

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """
        Ollama API를 호출하여 주어진 프롬프트로부터 텍스트를 생성합니다.

        Args:
            prompt (str): LLM에 전달할 프롬프트.
            **kwargs: 추가 Ollama 파라미터 (예: 'format': 'json').

        Returns:
            str: 생성된 텍스트 응답.
        """
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                **kwargs
            }
            api_url = f"{self.host}/api/generate"
            
            response = requests.post(api_url, json=payload)
            response.raise_for_status()
            
            response_json = response.json()
            return response_json.get("response", "").strip()

        except requests.exceptions.RequestException as e:
            print(f"Ollama API 호출 중 오류 발생: {e}")
            return f"Error: Could not connect to Ollama at {self.host}"
        except json.JSONDecodeError:
            print(f"Ollama API 응답을 파싱하는 중 오류 발생: {response.text}")
            return "Error: Failed to parse response from Ollama" 