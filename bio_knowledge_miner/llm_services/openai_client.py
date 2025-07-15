from typing import Optional, Any
from openai import OpenAI

from .base_client import BaseLLMClient
from .. import config

class OpenAIClient(BaseLLMClient):
    """
    OpenAI API와 상호작용하여 텍스트 생성을 수행하는 클라이언트입니다.
    """
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o"):
        self.api_key = api_key or config.OPENAI_API_KEY
        self.model = model
        self.client = OpenAI(api_key=self.api_key)

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """
        OpenAI API를 호출하여 주어진 프롬프트로부터 텍스트를 생성합니다.

        Args:
            prompt (str): LLM에 전달할 프롬프트.
            **kwargs: OpenAI ChatCompletion에 전달될 추가 파라미터.

        Returns:
            str: 생성된 텍스트 응답.
        """
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model=self.model,
                **kwargs,
            )
            content = chat_completion.choices[0].message.content
            return content.strip() if content else ""
        except Exception as e:
            print(f"OpenAI API 호출 중 오류 발생: {e}")
            return f"Error: OpenAI API call failed." 