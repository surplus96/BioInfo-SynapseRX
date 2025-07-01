import os
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Neo4j Credentials
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