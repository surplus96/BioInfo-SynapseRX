import os
import json
import time
from .api_clients import PubMedClient
from .. import config
from .pdf_downloader import find_pdf_url, download_file

def save_articles_to_json(articles: list, query: str):
    """
    수집된 논문 목록을 JSON 파일로 저장합니다.
    파일 이름은 쿼리를 기반으로 생성됩니다.
    """
    if not articles:
        print("No articles to save.")
        return

    # 파일 이름으로 사용하기 어려운 문자들을 제거
    sanitized_query = "".join(c for c in query if c.isalnum() or c in (' ', '_')).rstrip()
    filename = f"pubmed_{sanitized_query.replace(' ', '_')}.json"
    filepath = os.path.join(config.EXTRACTION_PATH, filename)

    print(f"Saving {len(articles)} articles to {filepath}...")

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(articles, f, ensure_ascii=False, indent=4)
    
    print("Save complete.")

def run_pubmed_crawler(search_queries: list, max_results_per_query: int = 10):
    """
    주어진 검색어 목록으로 PubMed 크롤링을 실행합니다.

    Args:
        search_queries (list): 검색할 쿼리 문자열의 리스트.
        max_results_per_query (int): 각 쿼리당 수집할 최대 논문 수.
    """
    pubmed_client = PubMedClient()

    for query in search_queries:
        print(f"\n----- Processing query: '{query}' -----")
        articles = pubmed_client.search_articles(query, max_results=max_results_per_query)
        
        if articles:
            # PDF 탐색 및 다운로드
            for art in articles:
                pmid = art["pmid"]
                doi = art.get("doi")
                pdf_url = find_pdf_url(pmid, doi)
                if pdf_url:
                    dest_path = os.path.join(config.PDF_PATH, f"{pmid}.pdf")
                    if not os.path.exists(dest_path):
                        downloaded = download_file(pdf_url, dest_path)
                        # polite delay
                        time.sleep(1)
                    else:
                        downloaded = True
                    if downloaded:
                        art["local_pdf"] = dest_path

            save_articles_to_json(articles, query)
        
        print("-" * (len(query) + 25))

if __name__ == '__main__':
    # 이 파일을 직접 실행할 경우 테스트 코드
    
    # 설정할 검색어 목록
    # 좀 더 구체적인 검색을 위해 "[Title/Abstract]" 태그를 사용합니다.
    QUERIES = [
        "KRAS G12C inhibitors[Title/Abstract]",
        "Sotorasib mechanism of action[Title/Abstract]",
        "KRAS mutations in pancreatic cancer[Title/Abstract]"
    ]
    
    run_pubmed_crawler(search_queries=QUERIES, max_results_per_query=15) 