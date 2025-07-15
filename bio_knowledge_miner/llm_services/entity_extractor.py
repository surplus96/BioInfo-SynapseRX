import json
import re
from typing import Dict, Any

from . import get_llm_client
from ..prompts import ENTITY_EXTRACTION_PROMPT

def _extract_json_block(text: str) -> str:
    """텍스트 블록에서 첫 '{'와 마지막 '}' 사이의 내용을 추출합니다."""
    # Find the first '{' and the last '}'
    start_index = text.find('{')
    end_index = text.rfind('}')

    if start_index != -1 and end_index != -1 and start_index < end_index:
        return text[start_index:end_index + 1]
    
    # Fallback for code blocks like ```json ... ```
    match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        return match.group(1)

    return text # Return original text if no clear JSON block is found

def llm_extract_entities(text: str) -> Dict[str, Any]:
    """
    LLM을 사용하여 텍스트에서 유전자, 질병, 화합물 엔티티를 추출합니다.
    (강화된 JSON 파싱 및 오류 처리 포함)
    """
    client = get_llm_client()
    prompt = ENTITY_EXTRACTION_PROMPT.format(text=text)

    # Ollama 사용 시 JSON 포맷으로 응답을 받도록 요청하고, 온도를 낮춰 예측 가능성 높임
    kwargs = {'temperature': 0.1} # 온도를 낮춰서 일관된 출력을 유도
    if 'ollama' in client.__class__.__name__.lower():
        kwargs['format'] = 'json'

    response_str = client.generate(prompt, **kwargs)
    
    # LLM 응답에서 순수 JSON 부분만 추출
    json_str = _extract_json_block(response_str)

    try:
        # LLM이 생성한 JSON 문자열을 파이썬 딕셔너리로 파싱
        entities = json.loads(json_str)
        # kg_builder가 기대하는 간단한 리스트 형태인지 추가로 확인
        if not all(isinstance(v, list) for k, v in entities.items() if k in ["gene", "disease", "compound"]):
             raise ValueError("Extracted JSON does not have lists as values for expected keys.")
        return entities
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Warning: LLM did not return valid JSON in the expected format. Error: {e}")
        print(f"--- Raw LLM Output ---\n{response_str}\n--------------------")
        # 실패 시, 파싱하지 않은 원본 문자열이나 빈 딕셔너리를 반환할 수 있습니다.
        return {"error": "Failed to decode or validate JSON from LLM response", "raw_output": response_str}
    except Exception as e:
        print(f"An unexpected error occurred during entity extraction: {e}")
        return {"error": str(e), "raw_output": response_str} 