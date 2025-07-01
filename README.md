# BioInfo-Projects

### ** 프로젝트 소개**
🕛 개발 기간 : 2025.06.30 ~
<br>

이 프로젝트는 2025년 기준 최신 기술 및 도구를 이용하여 AI 기반 바이오 신약 개발 통합 프로세스를 구현하는 프로젝트이다.

<br>


</div>

### ** 기능 소개**

<details>
<summary><b>1. Bio-Knowledge-miner</b></summary>

[README](https://github.com/surplus96/BioInfo-Projects/blob/main/bio_knowledge_miner/README.md)

이 단계의 핵심 목표는 전 세계에 흩어져 있는 비정형(Unstructured) 생물학 데이터(논문, 특허 등)를 자동으로 수집하고, AI를 통해 정제하여, 연구자가 쉽게 탐색할 수 있는 상호 연결된 지식 네트워크, 즉 지식 그래프(Knowledge Graph)로 변환하는 것입니다.

워크플로우:

데이터 수집 (Crawling): PubMed, Semantic Scholar, Google Patents 등 주요 학술/특허 데이터베이스에 API 또는 웹 크롤러로 접근하여 특정 키워드(예: 'Alzheimer's', 'pancreatic cancer', 'GPCR')와 관련된 최신 문헌과 특허 데이터를 대량으로 수집합니다.

데이터 전처리 (Preprocessing): 수집된 데이터는 대부분 PDF 또는 HTML 형태입니다. 여기서 텍스트를 추출하고, 특히 PDF 내의 표나 그림은 OCR(광학 문자 인식) 기술을 사용해 텍스트 데이터로 변환합니다.

AI 기반 분석 및 요약 (AI Analysis & Summarization): 추출된 텍스트를 GPT-4o, Claude 3.5와 같은 거대 언어 모델(LLM)에 전달합니다. LLM은 각 문서의 핵심 내용을 요약하고, 주요 키워드(유전자, 질병, 화합물 등)를 자동으로 태깅합니다.

지식 추출 및 그래프 구축 (Knowledge Extraction & Graph Construction): 이 단계가 가장 중요합니다. LLM을 사용하여 정제된 텍스트에서 "A라는 유전자는 B라는 질병과 관련 있다 (`GENE`-`ASSOCIATED_WITH`-`DISEASE`)"와 같은 `주체-관계-객체` 형태의 지식(Triplets)을 추출합니다. 이 정보들을 Neo4j와 같은 그래프 데이터베이스에 노드(Node)와 엣지(Edge) 형태로 저장하여 거대한 지식 네트워크를 구축합니다.

</details>

