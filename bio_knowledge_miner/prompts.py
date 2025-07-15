KOREAN_SUMMARY_PROMPT = """
다음 텍스트의 핵심 내용을 한국어로 5~7줄로 요약해 주세요. 주요 연구 결과, 사용된 방법론, 그리고 결론을 명확히 포함해야 합니다.

[텍스트 시작]
{text}
[텍스트 끝]

요약:
"""

ENTITY_EXTRACTION_PROMPT = """
당신은 텍스트에서 정보를 추출하여 JSON으로 변환하는 로봇입니다. 다음 텍스트에서 유전자/단백질(gene), 질병(disease), 화합물/약물(compound) 엔티티를 모두 찾으세요.

[출력 규칙]
- 오직 JSON 객체 하나만 출력해야 합니다. 다른 어떤 텍스트도 포함하지 마세요.
- JSON의 키는 반드시 "gene", "disease", "compound" 여야 합니다.
- 각 키의 값은 텍스트에서 찾은 엔티티 이름(string)의 배열(list)이어야 합니다.
- 만약 특정 종류의 엔티티를 찾지 못했다면, 빈 배열 `[]`을 값으로 사용하세요.
- 예시 출력: `{{ "gene": ["KRAS", "EGFR"], "disease": ["colorectal cancer"], "compound": ["Sotorasib"] }}`

[원본 텍스트]
{text}
[원본 텍스트 끝]

JSON 출력:
""" 