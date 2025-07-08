# Bio-Info: AI 기반 신약 개발 플랫폼

[![Code License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 개요

SynapseRX (시냅스알엑스)

의미 및 컨셉: 뇌의 신경세포 연결부인 '시냅스(Synapse)'처럼, 흩어진 생물의학 정보들을 연결하여 지식 그래프를 만들고, 이를 통해 새로운 통찰(후보 물질)을 얻어낸다는 의미를 담고 있습니다. 'RX'는 약학, 처방전을 상징하는 대표적인 기호

SynapseRX는 최신 AI 기술을 활용하여 신약 개발의 초기 단계, 특히 후보 물질 발굴 및 최적화 과정을 자동화하고 가속화하는 것을 목표로 하는 오픈소스 플랫폼입니다. 이 프로젝트는 크게 두 가지 핵심 모듈로 구성됩니다.

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

*   Python 3.9+
*   Docker 및 Docker Compose (Neo4j 데이터베이스 구동용)
*   분자 시뮬레이션을 위한 외부 도구:
    *   [fpocket](https://github.com/Discngine/fpocket)
    *   [AutoDock Vina](https://vina.scripps.edu/)
    *   [Open Babel](http://openbabel.org/)

### 설치

1.  **프로젝트 클론:**
    ```bash
    git clone https://github.com/your-username/Bio-Info.git
    cd Bio-Info
    ```

2.  **Python 가상환경 생성 및 활성화:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/macOS
    # venv\Scripts\activate  # Windows
    ```

3.  **필요한 패키지 설치:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **외부 도구 설치:**
    시스템에 `fpocket`, `vina`, `obabel`을 설치하고, 환경 변수 `PATH`에 해당 실행 파일이 있는 경로를 추가해야 합니다.

    *   **conda를 사용하는 경우 (권장):**
        ```bash
        conda install -c conda-forge vina openbabel fpocket
        ```

### 실행

1.  **Neo4j 데이터베이스 실행:**
    프로젝트 루트 디렉터리에서 Docker Compose를 사용하여 Neo4j 컨테이너를 실행합니다.
    ```bash
    docker-compose up -d
    ```

2.  **화합물 스크리닝 파이프라인 실행:**
    `auto_hypothesis_agent` 모듈의 메인 파이프라인을 실행하여 KRAS G12C 저해제 스크리닝을 시작할 수 있습니다.
    ```bash
    python -m auto_hypothesis_agent.pipelines.compound_screen_pipeline
    ```
    스크리닝이 완료되면 결과는 `outputs/reports/` 디렉터리에 CSV 파일로 저장됩니다.

## 라이선스

이 프로젝트는 [MIT 라이선스](LICENSE)에 따라 배포됩니다.

## 1. 시스템 요구 사항
* **OS**: Linux / WSL2 Ubuntu 22.04
* **GPU**: NVIDIA CUDA-호환 (10 GB VRAM 이상 권장)
* **드라이버 & CUDA**: NVIDIA Driver 535+, CUDA Toolkit 12.x
* **Conda**: Miniconda3 또는 Anaconda3 (conda >= 23)

## 2. 환경 구축 (Conda)
```bash
# 레포 클론 후
cd Bio-Info

# ① 새 환경 생성
conda env create -f environment.yml

# ② 활성화
conda activate bio-info

# ③ 로컬 패키지 editable 설치(이미 environment.yml에 포함되어 있으므로 생략 가능)
# pip install -e .

# ④ 외부 바이너리 설치 (필요 시)
# AutoDock Vina
wget https://github.com/ccsb-scripps/AutoDock-Vina/releases/download/v1.2.5/vina_1.2.5_linux_x86_64 -O vina
chmod +x vina && sudo mv vina /usr/local/bin/

# GROMACS (GPU) — 상세 명령은 docs/gromacs_install.md 참고
# AmberTools
conda install -c conda-forge ambertools -y
```

## 3. 환경 변수 설정
`.env` 파일을 프로젝트 루트에 두고 다음과 같이 채워주세요.
```dotenv
AUTODOCK_VINA_BIN=/usr/local/bin/vina
GROMACS_BIN=gmx
MMGBSA_SCRIPT=MMPBSA.py
OPENMM_PLATFORM=CUDA

NEO4J_BOLT_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```

## 4. 파이프라인 실행 예시
### 4-1. 가설 + 구조/CRISPR
```bash
python run_auto_hypothesis_agent.py --topic "KRAS" --n_hypo 3
```

### 4-2. Compound 스크리닝 & 비교 리포트
```bash
python auto_hypothesis_agent/pipelines/compound_screen_pipeline.py \
       --gene KRAS \
       --library_sdf data/libraries/zinc_leads.sdf \
       --top_k 500 --md_ns 50
```

리포트는 `outputs/reports/report_KRAS_YYYY-MM-DD.md` 로 저장됩니다.

## 5. Troubleshooting
* **Conda 설치 중 충돌**: `--no-channel-priority` 옵션 시도.
* **OpenMM가 GPU를 인식하지 못함**: `OPENMM_PLATFORM=CPU` 로 임시 변경.
* **GROMACS `libcuda.so` 오류**: NVIDIA 드라이버 버전을 확인하고 재시작.

---
라이선스: MIT  
문의: Issues 탭 또는 maintainer@example.com 