# Auto Hypothesis Agent

`auto_hypothesis_agent`는 지식 그래프와 외부 데이터를 기반으로 가설을 설정하고, 전산 시뮬레이션을 통해 이를 검증하는 자동화 에이전트입니다. 이 프로젝트의 핵심인 **화합물 가상 스크리닝 파이프라인**이 이 모듈에 포함되어 있습니다.

## 가상 스크리닝 파이프라인 (`pipelines/compound_screen_pipeline.py`)

이 파이프라인은 특정 단백질 타겟에 대한 저해제 후보 물질을 발굴하고 평가하는 전 과정을 자동화합니다.

### 파이프라인 단계

1.  **화합물 라이브러리 준비**
    -   `bio_knowledge_miner`가 구축한 지식 그래프에 쿼리하여, 특정 타겟(예: KRAS)과 관련된 화합물 목록을 동적으로 가져옵니다.
    -   가져온 화합물 정보를 임시 SDF 파일로 변환하여 다음 단계의 입력으로 사용합니다.

2.  **타겟 구조 및 결합 포켓 준비**
    -   타겟 단백질(예: KRAS G12C)의 PDB 구조 파일을 찾습니다.
    -   `fpocket`을 실행하여 단백질 표면의 결합 포켓(binding pocket)을 탐지하고, 도킹 시뮬레이션을 위한 3D 그리드 박스 좌표를 계산합니다.

3.  **ADMET 프로파일 예측**
    -   RDKit 기반 예측 모델을 사용하여 각 화합물의 약물로서의 기본적인 특성(용해도, 합성 용이성, 잠재적 독성 등)을 계산합니다.

4.  **분자 도킹 (Molecular Docking)**
    -   `AutoDock Vina`를 사용하여 준비된 화합물 라이브러리를 타겟 단백질의 결합 포켓에 도킹시킵니다.
    -   각 화합물에 대한 결합 에너지(`docking_score`)를 계산하여 결합력의 순위를 매깁니다.

5.  **결합 자유 에너지 계산 (MM/GBSA)**
    -   도킹된 복합체 구조에 대해 `OpenMM`을 사용하여 MM/GBSA(Molecular Mechanics/Generalized Born Surface Area) 계산을 수행합니다.
    -   이를 통해 더 정교한 방식의 결합 자유 에너지(`delta_g`)를 예측하여 도킹 점수를 보완합니다.

6.  **최종 리포트 생성**
    -   위 모든 단계에서 계산된 데이터(도킹 점수, 결합 에너지, ADMET 속성)를 하나의 CSV 파일로 통합합니다.
    -   결합력을 기준으로 후보 물질을 정렬하여 최종 스크리닝 리포트를 생성합니다.

## 주요 시뮬레이션 모듈 (`simulation/`)

-   `admet_predictor.py`: RDKit을 이용한 ADMET 속성 예측기.
-   `docking.py`: AutoDock Vina를 제어하는 도킹 실행기.
-   `binding_energy.py`: OpenMM과 OpenMM-ForceFields를 이용한 MM/GBSA 계산기.

# Auto-Hypothesis Agent 📈🔬

**목표:** `bio_knowledge_miner`가 구축한 지식 그래프를 입력으로 받아,  
LLM + Bayesian Optimization을 사용해 **새로운 생물학 가설을 생성**하고 **실험 설계**를 자동으로 제안합니다.

> 핵심 키워드: OMegaFold, CRISPick-v3

---

# 기능

1. **Hypothesis Generator (`hypothesis_generator.py`)**  
   • 지식 그래프를 질의해 관련 노드·관계를 추출 →  
   • LLM-prompt 템플릿으로 *가설 목록* 생성
2. **Bayesian Optimizer (`optimization/bo_optimizer.py`)**  
   • Ax 0.4 사용 · 목표 함수는 *예상 정보 이득*  
   • 실험 파라미터(예: 화합물 농도, 세포주, 변이체)를 제안
3. **Experiment Designer (`experiment_designer.py`)**  
   • **단백질 구조/기능 예측**: AlphaFold 3 API  
   • **CRISPR 가이드 설계**: CRISPick-v3 연동  
   • 결과를 Pydantic 모델로 구조화
4. **Protocol Generator (`protocol_generator.py`)**  
   • Protocol-GPT 프롬프트 ↔ LLM 호출  
   • SOP ⟶ Markdown + JSON-LD
5. **KG Feedback (`kg_interface.py`)**  
   • 설계 결과를 Neo4j에 다시 업서트 → RAG-Loop 지원

---
## 📂 폴더 구조 (제안)
```
auto_hypothesis_agent/
├── __init__.py
├── config.py                # API 키, 기본 파라미터
├── kg_interface.py          # Neo4j ↔ 그래프 질의/업데이트
├── hypothesis_generator.py  # LLM 기반 가설 생성
├── optimization/
│   └── bo_optimizer.py      # Ax Bayesian Opt 래퍼
├── experiment_designer.py   # 구조 예측·CRISPR 설계 통합
├── protocol_generator.py    # SOP 출력
├── pipelines/
│   └── auto_hypothesis_pipeline.py  # CLI & 전체 파이프라인
└── examples/
    └── demo.ipynb
```

---
## 🔑 주요 클래스 & 함수

| 모듈 | 클래스/함수 | 설명 |
|------|-------------|-----|
| `kg_interface` | `GraphClient` | Cypher 실행, `to_networkx()` 등 헬퍼 제공 |
| `hypothesis_generator` | `HypothesisGenerator` | `generate(topic:str)->List[Hypothesis]` |
| `optimization/bo_optimizer` | `BOOptimizer` | `suggest(hypothesis)->ExperimentPlan` |
| `experiment_designer` | `ExperimentDesigner` | AlphaFold3, CRISPick 호출 → `design(plan)` |
| `protocol_generator` | `ProtocolGenerator` | `render(experiment)->SOP` (MD, JSON-LD) |
| `pipelines/auto_hypothesis_pipeline` | `run(topic:str)` | 전체 흐름 One-shot 실행 CLI |

각 데이터 모델은 **Pydantic** 스키마(`models.py`)로 표준화해 단계 간 객체 전달을 명확히 합니다.

---
## 🔄 첫 번째 모듈 연동 방법

1. `bio_knowledge_miner` 실행 결과물
    - `neo4j` 데이터베이스 (Bolt URI)
    - `data/result/knowledge_graph.json` (옵션)
2. `auto_hypothesis_agent.config` 예시
```toml
KG_BOLT_URI = "bolt://localhost:7687"
KG_USER = "neo4j"
KG_PASSWORD = "<pwd>"
OPENAI_API_KEY = "sk-..."
GEMINI_MODEL = "gemini-2.5-flash-lite"
ALPHAFOLD_ENDPOINT = "https://api.af3.example.com/predict"
```
3. 파이프라인 사용 예
```bash
python -m auto_hypothesis_agent.pipelines.auto_hypothesis_pipeline --topic "KRAS G12C inhibitor" --n_hypo 1
```

---
## ⌛ 향후 로드맵
- [ ] 멀티-objective BO (정보 이득 + 비용)
- [ ] Wet-lab 로봇 통제 API 연동
- [ ] Streamlit UI로 Hypothesis Dashboard 제공

---
## 📝 라이선스
MIT 