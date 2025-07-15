
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

## 🌟 주요 기능

-   **자동화된 지식 그래프 구축**: PubMed 등에서 논문을 크롤링하고, NLP 모델을 통해 유전자, 질병, 화합물 등의 관계를 추출하여 Neo4j 데이터베이스에 지식 그래프를 자동으로 구축합니다.
-   **AI 기반 후보물질 추천**: 특정 유전자(Target)를 지정하면, 지식 그래프 내의 관계 정보를 바탕으로 가장 유망한 화합물 후보군을 지능적으로 추천합니다.
-   **End-to-End In-Silico 스크리닝**: 추천된 후보물질에 대해 단백질-리간드 도킹(Docking), ADMET(흡수, 분포, 대사, 배설, 독성) 예측 등 복잡한 분자 시뮬레이션 파이프라인을 완전 자동으로 실행합니다.
-   **시각적 결과 리포팅**: 스크리닝 결과를 바탕으로 상위 후보물질의 순위, 결합 에너지, 약물성 예측치 등을 포함한 상세 분석 리포트(Markdown)를 자동으로 생성합니다.

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

## 🛠️ 기술 스택

-   **Backend**: Python 3.10
-   **Database**: Neo4j (그래프 데이터베이스)
-   **AI / Machine Learning**: PyTorch, LangChain, PaddleOCR
-   **Bio-simulation**: RDKit, OpenMM, MDAnalysis, OpenBabel
-   **Data Handling**: Pandas, NumPy
-   **Infrastructure**: Docker, Conda

## ⚙️ 설치 방법

1.  **프로젝트 클론**
    ```bash
    git clone <your-repository-url>
    cd Bio-Info
    ```

2.  **환경변수 설정**
    프로젝트 루트 디렉터리에 `.env` 파일을 생성하고 아래 내용을 채워넣으세요.
    ```env
    # OpenAI API (선택사항)
    OPENAI_API_KEY=your_openai_api_key_here

    # Neo4j 설정
    NEO4J_URI=bolt://localhost:7687
    NEO4J_USER=neo4j
    NEO4J_PASSWORD=password
    ```

3.  **Neo4j 데이터베이스 실행**
    Docker가 설치되어 있어야 합니다.
    ```bash
    docker-compose up -d
    ```
    - 브라우저에서 `http://localhost:7474` 에 접속하여 Neo4j 데이터베이스를 확인할 수 있습니다.

4.  **Conda 가상환경 생성 및 활성화**
    `environment.yml` 파일을 사용하여 Conda 가상환경을 생성합니다.
    ```bash
    conda env create -f environment.yml
    source activate bio-info
    ```
    > **참고**: `libstdcxx-ng`는 `scipy`와 `paddleocr` 실행 시 발생할 수 있는 GLIBCXX 버전 충돌을 방지하기 위해 포함되었습니다.

5.  **외부 도구(DiffBindFR) 설치**
    프로젝트에 포함된 단백질-리간드 결합 예측 도구 `DiffBindFR`을 설치합니다.
    ```bash
    pip install -e external_tools/DiffBindFR
    ```
    > `-e` 옵션은 패키지를 "편집 가능(editable)" 모드로 설치하여, 소스 코드를 수정하면 즉시 반영되도록 합니다.

## 🚀 실행 가이드

모든 스크립트는 프로젝트 루트 디렉터리에서 실행해야 합니다.

### 1단계: 지식 그래프 구축 및 정제

> **주의**: 이 단계는 새로운 문헌 정보를 데이터베이스에 추가하거나 초기 데이터베이스를 구축할 때 필요합니다. 이미 구축된 데이터베이스가 있다면 2단계로 건너뛸 수 있습니다.

```bash
# (1) PDF/PubMed 등에서 텍스트와 개체(Entity) 추출
python -m bio_knowledge_miner.main

# (2) 추출된 데이터를 바탕으로 그래프 노드 및 관계 생성/정제
python -m bio_knowledge_miner.maintenance.clean_gene_nodes
python -m bio_knowledge_miner.maintenance.fill_compound_structures --gene KRAS
python -m bio_knowledge_miner.maintenance.populate_cell_lines
python -m bio_knowledge_miner.maintenance.filter_cell_lines --gene KRAS --mutation G12C
python -m bio_knowledge_miner.maintenance.update_graph_from_filtered_cells --gene KRAS
python -m bio_knowledge_miner.maintenance.annotate_variants
```

### 2단계: 신약 후보물질 스크리닝 실행

1.  **타겟 단백질 구조(PDB ID) 탐색**
    RCSB PDB 데이터베이스에서 연구하려는 타겟(예: KRAS G12C)에 대한 PDB ID 목록을 확인합니다. 해상도(Resolution)가 높고 실험 조건이 연구 목적에 부합하는 PDB ID를 1개 이상 선택합니다.
    ```bash
    python find_pdb_ids.py --query "KRAS G12C"
    ```

2.  **메인 파이프라인 실행**
    위에서 선택한 PDB ID들과 타겟 유전자 이름을 인자로 전달하여 전체 스크리닝 파이프라인을 실행합니다.
    ```bash
    python run_drug_discovery.py --target_pdb_ids 5V90 6N2J 7YCE --gene KRAS
    ```
    > 이 스크립트는 내부적으로 Neo4j에서 `KRAS` 유전자 관련 화합물을 조회하고, 각 화합물을 `5V90`, `6N2J`, `7YCE` 단백질 구조와 도킹 시뮬레이션을 수행한 후, ADMET 예측을 거쳐 최종 리포트를 생성합니다.

## 📊 결과 확인

-   **시뮬레이션 결과 파일**: `outputs/` 디렉터리에 다운로드된 PDB 파일, 도킹 결과(PDBQT) 등이 저장됩니다.
-   **최종 분석 리포트**: `outputs/reports/` 디렉터리에 각 타겟 PDB ID별로 Markdown 형식의 상세 리포트가 생성됩니다. (예: `report_5V90_2025-07-15.md`)

## 예시 결과 해설

```
1. 최종 리포트 해설 (report_5V90_2025-07-15.md)

- run_compound_id: 이번 실행에서만 사용된 임시 ID.
- docking_score: 결합 에너지. 마이너스 값이 클수록 표적 단백질에 더 강하게 결합. (가장 중요한 효능 지표)
- complex_file: 3D 결합 구조 파일 경로. 
- compound_id: PubChem의 고유 ID. 이제 이 ID로 어떤 화합물인지 정확히 추적할 수 있습니다.
- name: 화합물의 이름. (예: irinotecan)
- smiles: 화합물의 2D 구조식.
- herg_ic50, cyp_inhibition, logS, sa_score: 이전과 동일한 안전성/약물성/개발 용이성 지표.
- composite: 종합 점수.

2. 결과 분석: Top 5 후보 심층 탐구

- 1위: Irinotecan (docking_score: -11.03)
    - 정체: 이리노테칸은 실제 임상에서 사용되는 항암제입니다 (주로 대장암).
    - 해석:
        강력한 결합력: -11.03 이라는 압도적인 수치는 이 화합물이 KRAS G12C 단백질의 특정 부위에 매우 안정적으로 결합할 수 있음을 의미합니다.
        새로운 가능성(Off-target 효과): 이리노테칸의 주된 작용 기전은 Topoisomerase I 억제이지, KRAS 직접 억제는 아닙니다. 우리 시뮬레이션은 기존에 알려지지 않았던 새로운 표적으로서의 KRAS G12C 가능성을 발견했을 수 있습니다. 이것이 바로 in silico 스크리닝의 묘미입니다.
        단점: hERG 수치가 5로 경계선에 있고, logS(용해도)가 다소 낮아 약물성 개선이 필요할 수 있습니다.

- 2위: Brimarafenib (docking_score: -10.43)
    - 정체: 이름의 '-rafenib' 접미사는 이 약물이 RAF 키나아제 억제제 계열임을 강력히 시사합니다. (예: 소라페닙, 베무라페닙)
    - 해석:
        매우 높은 생물학적 타당성: KRAS는 RAF를 활성화시키는 상위 신호 전달 단백질입니다. 즉, 이 화합물은 우리가 타겟하는 신호 전달 경로(MAPK pathway)에 직접 작용하는약물입니다. 우연히 찾은 것이 아니라, 매우 논리적인 후보입니다.
        훌륭한 프로파일: 결합력도 매우 높고, hERG 수치 30, CYP 억제 없음 등 안전성 프로파일이 1위인 이리노테칸보다 훨씬 우수합니다.
        결론: 효능(높은 결합력)과 안전성, 생물학적 타당성을 모두 고려했을 때, 이번 스크리닝에서 가장 유망한 선도물질(Lead Compound) 후보라고 할 수 있습니다.

- 3위: Penicillin-streptomycin (docking_score: -9.621)
    - 정체: 페니실린과 스트렙토마이신은 항생제입니다.
    - 해석 (매우 중요 - 함정 카드):
        이 결과는 거의 100% 시뮬레이션의 오류(Artifact)입니다.SMILES를 보면 두 분자가 .으로 연결된 혼합물이며, 분자량이 매우 크고 구조가 복잡합니다. 도킹 프로그램은 이런 거대하고 유연한 혼합물 구조를 정확히 계산하는 데 어려움을 겪어 - 비현실적으로 높은 점수를 내는 경우가 많습니다. 생물학적으로 항생제가 암세포의 KRAS를 억제할 가능성은 거의 없습니다. 이 후보는 분석에서 과감히 제외해야 합니다.

- 4위: RMC-9805 (docking_score: -9.475)
    - 정체: 'RMC'는 Revolution Medicines라는 회사의 약자로, 이 회사는 KRAS G12C를 포함한 RAS 단백질 표적 치료제 개발의 세계적인 선두주자입니다.
    - 해석:
        스크리닝 방법론 검증: 우리 파이프라인이 KRAS G12C를 전문적으로 연구하는 회사의 화합물을 찾아냈다는 사실은, 우리 스크리닝 방법이 매우 정확하고 유효하다는 것을 증명하는 강력한 증거입니다.
        단점: logS가 -10.13으로 매우 낮아 용해도가 심각한 수준이며, hERG 수치도 5로 좋지 않습니다. 실제 약물로 개발되기에는 큰 허들이 있습니다.

- 5위: HRS-4642 (docking_score: -9.441)
    - 정체: 비교적 최근에 연구되고 있는 분자 표적 항암제 후보물질 중 하나입니다.
    - 해석: 결합력은 우수하지만, cyp_inhibition이 True로 나와 약물 상호작용 위험이 있습니다. 2위 후보인 Brimarafenib에 비해 매력도가 떨어집니다.

```

## 📄 라이선스

이 프로젝트는 [MIT 라이선스](LICENSE)를 따릅니다.