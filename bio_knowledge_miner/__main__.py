from . import config
from .data_collection.crawler import run_pubmed_crawler
from .text_processing.pdf_parser import process_all_pdfs_in_directory
from .llm_services.summarizer import summarize_text
from .llm_services.entity_extractor import llm_extract_entities
from .knowledge_graph.kg_builder import ingest_document_entities
import json, os
from datetime import datetime
# global variable to share between steps
extracted_pdf_data_cache = []
current_time = datetime.now().strftime("%Y%m%d")
OUTPUT_JSON = os.path.join(config.EXTRACTION_PATH, f"pdf_entities_summary_{current_time}.json")

def step_1_collect_data():
    """논문 및 특허 데이터 수집"""
    print("--- Step 1: Collecting data from PubMed ---")
    
    # 크롤링할 검색어와 개수 설정
    search_queries = [
        "KRAS G12C inhibitors[Title/Abstract]",
        "Sotorasib mechanism of action[Title/Abstract]",
        "KRAS mutations in pancreatic cancer[Title/Abstract]"
    ]
    max_results = 20 # 각 쿼리당 20개
    
    run_pubmed_crawler(search_queries, max_results)
    
    print("Data collection complete.")
    print("-" * 30)

def step_2_process_text():
    """PDF 파싱 및 OCR 수행"""
    print("--- Step 2: Processing text from documents ---")
    
    # pdfs 폴더에 있는 모든 PDF 파일의 텍스트를 추출합니다.
    global extracted_pdf_data_cache
    extracted_pdf_data_cache = process_all_pdfs_in_directory()
    
    # 이후 단계에서 사용하기 위해 이 데이터를 변수로 가지고 있거나 파일로 저장할 수 있습니다.
    # 지금은 추출된 파일 개수만 출력합니다.
    if extracted_pdf_data_cache:
        print(f"Successfully extracted text from {len(extracted_pdf_data_cache)} PDF(s).")

    print("Text processing complete.")
    print("-" * 30)

def step_3_extract_entities():
    """LLM을 이용해 지식 추출"""
    print("--- Step 3: Extracting knowledge with LLM ---")
    if not extracted_pdf_data_cache:
        print("No extracted PDF data to process.")
        return

    for item in extracted_pdf_data_cache:
        content = item["content"]
        summary = summarize_text(content)
        entities = llm_extract_entities(content)
        # 저장
        item["summary"] = summary
        item["entities"] = entities

        print("\n[SUMMARY]")
        print(summary)
        print("[ENTITIES]")
        print(entities)

    # 모든 결과를 JSON 파일로 저장
    try:
        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            json.dump(extracted_pdf_data_cache, f, ensure_ascii=False, indent=2)
        print(f"\n📝 Saved detailed results to {OUTPUT_JSON}")
    except Exception as e:
        print(f"Could not write result json: {e}")

    print("Knowledge extraction complete.")
    print("-" * 30)

def step_4_build_knowledge_graph():
    """추출된 지식으로 그래프 DB 구축"""
    print("--- Step 4: Building Knowledge Graph ---")
    if not extracted_pdf_data_cache:
        print("No data to ingest into KG")
        return

    for item in extracted_pdf_data_cache:
        entities = item.get("entities")
        if entities:
            ingest_document_entities(entities)

    print("Knowledge Graph build complete.")
    print("-" * 30)

def main():
    """전체 파이프라인 실행"""
    print("🚀 Starting Bio-Knowledge Miner Pipeline...")
    
    step_1_collect_data()
    step_2_process_text()
    step_3_extract_entities()
    step_4_build_knowledge_graph()
    
    print("✅ Pipeline finished successfully!")

if __name__ == "__main__":
    main() 