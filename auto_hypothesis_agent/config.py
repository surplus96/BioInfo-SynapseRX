import os
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드 (존재하지 않아도 문제 없음)
load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Neo4j Credentials
NEO4J_BOLT_URI = os.getenv("NEO4J_BOLT_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# 데이터 경로 설정
DATA_PATH = "data/"
PDF_PATH = os.path.join(DATA_PATH, "pdfs")
EXTRACTION_PATH = os.path.join(DATA_PATH, "extractions")

# OpenAI Model
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

# AlphaFold 3 API
ALPHAFOLD_API_KEY: str | None = os.getenv("ALPHAFOLD_API_KEY")
ALPHAFOLD_ENDPOINT: str | None = os.getenv("ALPHAFOLD_ENDPOINT")

# OmegaFold settings
OMEGAFOLD_BIN: str | None = os.getenv("OMEGAFOLD_BIN", "omegafold")
OMEGAFOLD_SUBBATCH_SIZE: int = int(os.getenv("OMEGAFOLD_SUBBATCH_SIZE", "64"))  # 16GB VRAM 기준 권장값

# External tool paths (In Silico Simulation)
AUTODOCK_VINA_BIN: str | None = os.getenv("AUTODOCK_VINA_BIN", "vina")
GROMACS_BIN: str | None = os.getenv("GROMACS_BIN", "gmx")
OPENMM_PLATFORM: str | None = os.getenv("OPENMM_PLATFORM", "CUDA")
MMGBSA_SCRIPT: str | None = os.getenv("MMGBSA_SCRIPT", "MMPBSA.py")

# Pocket detection
FPOCKET_BIN: str | None = os.getenv("FPOCKET_BIN", "fpocket")

# Log configuration summary
print("[auto_hypothesis_agent] Config loaded. Neo4j URI:", NEO4J_BOLT_URI)

# Informative log: AlphaFold integration currently disabled; using OmegaFold.
if ALPHAFOLD_API_KEY:
    print("[auto_hypothesis_agent] AlphaFold API key detected (integration not currently used).")
else:
    print("[auto_hypothesis_agent] AlphaFold integration disabled — using OmegaFold only.") 