import os
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드 (존재하지 않아도 문제 없음)
load_dotenv()

# LLM Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()

# OpenAI Settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4-turbo")

# Ollama Settings (if used)
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3:8b")

# Anthropic API Key
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Google API Key
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Neo4j
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# 데이터 경로 설정 (This can be kept for other modules that use it)
DATA_PATH = "data/"
PDF_PATH = os.path.join(DATA_PATH, "pdfs")
EXTRACTION_PATH = os.path.join(DATA_PATH, "extractions")

# AlphaFold 3 API
ALPHAFOLD_API_KEY: str | None = os.getenv("ALPHAFOLD_API_KEY")
ALPHAFOLD_ENDPOINT: str | None = os.getenv("ALPHAFOLD_ENDPOINT")

# OmegaFold settings
OMEGAFOLD_BIN: str | None = os.getenv("OMEGAFOLD_BIN", "omegafold")
OMEGAFOLD_SUBBATCH_SIZE: int = int(os.getenv("OMEGAFOLD_SUBBATCH_SIZE", "64")) 