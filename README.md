# SynapseRX


[![Code License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 개요

의미 및 컨셉: 뇌의 신경세포 연결부인 '시냅스(Synapse)'처럼, 흩어진 생물의학 정보들을 연결하여 지식 그래프를 만들고, 이를 통해 새로운 통찰(후보 물질)을 얻어낸다는 의미를 담고 있습니다. 'RX'는 약학, 처방전을 상징하는 대표적인 기호

SynapseRX는 최신 AI 기술을 활용하여 신약 개발의 초기 단계, 특히 후보 물질 발굴 및 최적화 과정을 자동화하고 가속화하는 것을 목표로 하는 오픈소스 플랫폼입니다. 이 프로젝트는 크게 두 가지 핵심 모듈로 구성됩니다.

1.  **`bio_knowledge_miner`**: 방대한 생물학 및 화학 문헌, 데이터베이스에서 정보를 수집, 처리하고 지식 그래프(Knowledge Graph)를 구축하여 신약 개발에 필요한 지식을 체계적으로 축적합니다.
2.  **`auto_hypothesis_agent`**: 구축된 지식 그래프를 기반으로 특정 질병 타겟(예: KRAS G12C)에 대한 치료 가설을 설정하고, 가상 스크리닝(Virtual Screening) 파이프라인을 통해 유효 화합물을 발굴하며, 실험 계획을 자동 설계합니다.

본 프로젝트는 RAG(Retrieval-Augmented Generation) 기술과 LLM(Large Language Model) 에이전트를 활용하여 연구자들이 더 빠르고 정확하게 유망한 후보 물질을 찾아낼 수 있도록 지원합니다.

## 프로젝트 구조

```
BioInfo-SynapseRX/
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

<details>
<summary><b>1. bio_knowledge_miner</b></summary>

`bio_knowledge_miner`는 SynapseRX 프로젝트의 데이터 수집 및 지식 관리 백본(backbone)입니다. 이 모듈의 핵심 목표는 비정형 데이터(예: 과학 논문)와 정형 데이터(예: ChEMBL, PubChem)를 포함한 다양한 소스로부터 생물의학 정보를 추출, 처리하고, 이를 연결하여 거대한 지식 그래프(Knowledge Graph)를 구축하는 것입니다.

이 지식 그래프는 신약 개발 연구에 필요한 핵심적인 관계들(예: '유전자-질병 연관성', '화합물-단백질 상호작용', '치료제-부작용')을 명시적으로 표현하며, `auto_hypothesis_agent`가 가설을 생성하고 검증하는 데 필요한 기반 지식을 제공합니다.

 [README](https://github.com/surplus96/BioInfo-SynapseRX/tree/main/bio_knowledge_miner#readme)

</details>

<details>
<summary><b>2. auto_hypothesis_agent</b></summary>

`auto_hyphothesis_agent` 는 지식 그래프와 외부 데이터를 기반으로 가설을 설정하고, 전산 시뮬레이션을 통해 이를 검증하는 자동화 에이전트입니다. 이 프로젝트의 핵심인 화합물 가상 스크리닝 파이프라인이 이 모듈에 포함되어 있습니다.

 [README](https://github.com/surplus96/BioInfo-SynapseRX/blob/main/auto_hypothesis_agent/README.md)

</details>


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
    git clone https://github.com/surplus96/BioInfo-SynapseRX.git
    cd BioInfo-SynapseRX
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

    OPENAI_API_KEY=your_openai_api_key_here


    NEO4J_URI=bolt://localhost:7687
    NEO4J_USER=neo4j
    NEO4J_PASSWORD=password


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
    [Final_Result](https://github.com/surplus96/BioInfo-SynapseRX/blob/main/outputs/reports/screening_report_KRAS_KRAS_G12C_20250708134950.csv)
    

## 라이선스

이 프로젝트는 [MIT 라이선스](LICENSE)에 따라 배포됩니다.