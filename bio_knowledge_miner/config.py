import os
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

# LLM 설정
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")  # 'openai' 또는 'ollama'

# OpenAI 설정
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

# Ollama 설정
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "biomistral") # PMC-Llama, Llama3 등

# Neo4j 설정
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# 데이터 경로 설정
DATA_PATH = "data/"
PDF_PATH = os.path.join(DATA_PATH, "pdfs")
EXTRACTION_PATH = os.path.join(DATA_PATH, "extractions")

# 디렉토리 생성
os.makedirs(PDF_PATH, exist_ok=True)
os.makedirs(EXTRACTION_PATH, exist_ok=True)

print("Configuration loaded.") 