# Bio-Info: AI 기반 신약 개발 플랫폼

[![Code License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 개요

Bio-Info는 최신 AI 기술을 활용하여 신약 개발의 초기 단계, 특히 후보 물질 발굴 및 최적화 과정을 자동화하고 가속화하는 것을 목표로 하는 오픈소스 플랫폼입니다. 이 프로젝트는 크게 두 가지 핵심 모듈로 구성됩니다.

1.  **`bio_knowledge_miner`**: 방대한 생물학 및 화학 문헌, 데이터베이스에서 정보를 수집, 처리하고 지식 그래프(Knowledge Graph)를 구축하여 신약 개발에 필요한 지식을 체계적으로 축적합니다.
2.  **`auto_hypothesis_agent`**: 구축된 지식 그래프를 기반으로 특정 질병 타겟(예: KRAS G12C)에 대한 치료 가설을 설정하고, 가상 스크리닝(Virtual Screening) 파이프라인을 통해 유효 화합물을 발굴하며, 실험 계획을 자동 설계합니다.

본 프로젝트는 RAG(Retrieval-Augmented Generation) 기술과 LLM(Large Language Model) 에이전트를 활용하여 연구자들이 더 빠르고 정확하게 유망한 후보 물질을 찾아낼 수 있도록 지원합니다.

## 프로젝트 구조

```
Bio-Info/
├── auto_hypothesis_agent/     # 가설 생성 및 검증 에이전트
│   ├── pipelines/             # 화합물 스크리닝 등 자동화 파이프라인
│   ├── simulation/            # 분자 도킹, 결합 에너지 계산 등 시뮬레이션
│   └── ...
├── bio_knowledge_miner/       # 생물학 데이터 수집 및 지식 그래프 구축 모듈
│   ├── data_collection/       # 논문, 데이터베이스 등에서 데이터 수집
│   ├── knowledge_graph/       # Neo4j 지식 그래프 구축 및 쿼리
│   └── ...
├── data/                      # 각종 데이터 (PDF 논문, 추출된 정보 등)
├── outputs/                   # 스크리닝 결과, 리포트 등 출력 폴더
├── docker-compose.yml         # Neo4j 등 외부 서비스 실행을 위한 설정
├── requirements.txt           # Python 패키지 의존성
└── README.md                  # 프로젝트 최상위 README
```

## 주요 기능

*   **지식 그래프 구축**: PubMed 등에서 논문을 자동으로 크롤링하고, LLM을 이용해 핵심 엔티티(유전자, 질병, 화합물 등)를 추출하여 Neo4j 지식 그래프로 구축합니다.
*   **화합물 스크리닝 파이프라인**: 특정 단백질 타겟(예: KRAS G12C)과 지식 그래프에 저장된 화합물 라이브러리를 사용하여, 포켓 탐색 (`fpocket`), 분자 도킹 (`Vina`), 결합 자유 에너지 계산 (`OpenMM`)을 포함한 전체 가상 스크리닝 과정을 자동화합니다.
*   **ADMET 예측**: 화합물의 흡수, 분포, 대사, 배설, 독성(ADMET) 프로필을 예측하여 초기 단계에서 약물로서의 가능성을 평가합니다.
*   **결과 보고**: 스크리닝 결과를 CSV 파일로 생성하고, 결합 친화도와 ADMET 점수를 종합하여 유망 후보 물질의 순위를 매깁니다.

## 시작하기

### 요구사항

*   **OS**: Linux 또는 WSL2 (Ubuntu 22.04 권장)
*   **Python**: `setup_pip_env.sh` 스크립트를 통해 Python 3.10이 자동 설치됩니다.
*   **필수 도구**: `git`, `curl`, `build-essential`
    ```bash
    sudo apt-get update && sudo apt-get install -y git curl build-essential
    ```
*   **Docker**: Neo4j 데이터베이스 구동을 위해 [Docker](https://docs.docker.com/engine/install/) 및 [Docker Compose](https://docs.docker.com/compose/install/)가 필요합니다.
*   **GPU**: 분자 시뮬레이션 및 딥러닝 모델(예: OmegaFold) 가속을 위해 NVIDIA GPU(VRAM 10GB 이상) 및 CUDA 12.1 호환 드라이버 설치를 권장합니다.

### 설치

프로젝트 설정의 모든 과정은 `setup_pip_env.sh` 스크립트에 자동화되어 있습니다.

1.  **프로젝트 클론:**
    ```bash
    git clone https://github.com/your-username/Bio-Info.git
    cd Bio-Info
    ```

2.  **설치 스크립트 실행:**
    스크립트를 실행하여 Python 가상환경(`bio-info-pip`)을 생성하고 모든 필수 패키지 및 외부 도구를 설치합니다.
    ```bash
    bash setup_pip_env.sh
    ```
    > **참고**: 이 스크립트는 다음 작업을 수행합니다:
    > *   Python 3.10 및 가상환경 설정
    > *   PyTorch (CUDA 12.1), `requirements.txt` 패키지 설치
    > *   단백질 구조 예측을 위한 `OmegaFold` 및 모델 가중치 설치
    > *   단백질 포켓 분석을 위한 `fpocket` 소스 코드 컴파일 및 설치

### 실행

1.  **가상환경 활성화:**
    터미널 세션을 새로 시작할 때마다 다음 명령어를 실행하여 가상환경을 활성화해야 합니다.
    ```bash
    source bio-info-pip/bin/activate
    ```

2.  **Neo4j 데이터베이스 실행:**
    프로젝트 루트 디렉터리에서 Docker Compose를 사용하여 Neo4j 컨테이너를 실행합니다.
    ```bash
    docker-compose up -d
    ```

3.  **환경 변수 설정:**
    프로젝트 루트 디렉터리에 `.env` 파일을 생성하고 아래 내용을 채워넣으세요.
    ```bash
    cat > .env << EOF
# OpenAI API
OPENAI_API_KEY=your_openai_api_key_here

# Neo4j 설정
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# 외부 도구 경로 (선택사항, setup_pip_env.sh가 자동 설정 시도)
AUTODOCK_VINA_BIN=/usr/local/bin/vina
OMEGAFOLD_BIN=/usr/local/bin/omegafold
EOF
    ```

4.  **전체 파이프라인 실행:**
    다음 스크립트를 순서대로 실행하여 전체 워크플로우를 진행합니다.

    *   **1단계: 지식 수집 및 그래프 구축**
        ```bash
        # PubMed 등에서 문헌 데이터를 수집하고 LLM으로 엔티티를 추출하여 지식 그래프에 저장
        python run_bio_knowledge_miner.py
        
        # 지식 그래프의 유전자 노드 정보 보강
        python bio_knowledge_miner/maintenance/clean_gene_nodes.py
        python -m bio_knowledge_miner.maintenance.annotate_variants
        
        # 특정 유전자 관련 화합물 구조 정보 채우기
        python -m bio_knowledge_miner.maintenance.fill_compound_structures --gene KRAS
        ```

    *   **2단계: 가설 생성 및 가상 스크리닝**
        ```bash
        # KRAS G12C 저해제에 대한 가설 생성 및 구조 예측
        python run_auto_hypothesis_agent.py --topic "KRAS G12C inhibitor" --n_hypo 1
        
        # 생성된 가설을 바탕으로 화합물 스크리닝 파이프라인 실행
        python -m auto_hypothesis_agent.pipelines.compound_screen_pipeline --gene KRAS
        ```

5.  **결과 확인:**
    스크리닝 결과, 예측된 단백질 구조, 최종 리포트 등은 `outputs/` 디렉터리에서 확인할 수 있습니다.
    ```bash
    ls -R outputs/
    ```

## 라이선스

이 프로젝트는 [MIT 라이선스](LICENSE)에 따라 배포됩니다.