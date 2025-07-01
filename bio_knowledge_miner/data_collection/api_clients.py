import requests
import time
from typing import List, Dict, Optional
import xml.etree.ElementTree as ET

class PubMedClient:
    """
    NCBI E-utilities API를 사용하여 PubMed에서 논문 정보를 가져오는 클라이언트.
    """
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

    def __init__(self, api_key: Optional[str] = None):
        """
        클라이언트를 초기화합니다.
        
        Args:
            api_key (Optional[str]): NCBI API 키. 사용 시 요청 제한이 완화됩니다.
        """
        self.api_key = api_key

    def search_articles(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        주어진 쿼리로 PubMed에서 논문을 검색하고 상세 정보를 반환합니다.

        Args:
            query (str): 검색어 (예: "pancreatic cancer[Title/Abstract]")
            max_results (int): 가져올 최대 논문 수.

        Returns:
            List[Dict]: 각 논문의 상세 정보가 담긴 딕셔너리 리스트.
        """
        print(f"Searching PubMed for query: '{query}'...")
        
        # 1. ESearch: 쿼리로 PubMed ID (PMID) 목록 검색
        search_params = {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "usehistory": "y",
        }
        if self.api_key:
            search_params["api_key"] = self.api_key
            
        try:
            search_response = requests.get(self.BASE_URL + "esearch.fcgi", params=search_params)
            search_response.raise_for_status() # HTTP 오류 발생 시 예외 발생
        except requests.exceptions.RequestException as e:
            print(f"Error during ESearch request: {e}")
            return []

        # 검색 결과에서 WebEnv와 QueryKey 추출 (대량 데이터 처리에 필요)
        root = ET.fromstring(search_response.content)
        id_list = [id_elem.text for id_elem in root.findall(".//Id")]
        
        if not id_list:
            print("No articles found for the query.")
            return []
            
        print(f"Found {len(id_list)} PMIDs. Fetching details...")

        # 2. EFetch: PMID 목록으로 논문 상세 정보 가져오기
        fetch_params = {
            "db": "pubmed",
            "id": ",".join(id_list),
            "rettype": "xml",
            "retmode": "text",
        }
        if self.api_key:
            fetch_params["api_key"] = self.api_key
        
        # API 요청 간에 약간의 딜레이를 주어 서버 부담 감소
        time.sleep(0.5)

        try:
            fetch_response = requests.get(self.BASE_URL + "efetch.fcgi", params=fetch_params)
            fetch_response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error during EFetch request: {e}")
            return []
            
        # 3. XML 파싱하여 정보 추출
        articles = self._parse_article_xml(fetch_response.text)
        
        print(f"Successfully fetched details for {len(articles)} articles.")
        return articles

    def _parse_article_xml(self, xml_data: str) -> List[Dict]:
        """
        EFetch로부터 받은 XML 데이터를 파싱하여 논문 정보를 추출합니다.
        """
        articles = []
        try:
            root = ET.fromstring(xml_data)
            for article_elem in root.findall(".//PubmedArticle"):
                pmid = article_elem.find(".//PMID")
                title = article_elem.find(".//ArticleTitle")
                abstract = article_elem.find(".//Abstract/AbstractText")
                journal = article_elem.find(".//Journal/Title")
                # DOI는 ArticleIdList 내 IdType="doi" 태그에 존재
                doi_elem = article_elem.find(".//ArticleIdList/ArticleId[@IdType='doi']")
                
                authors = []
                author_list = article_elem.findall(".//Author")
                for author in author_list:
                    lastname = author.find("LastName")
                    forename = author.find("ForeName")
                    if lastname is not None and forename is not None:
                        authors.append(f"{forename.text} {lastname.text}")

                article_data = {
                    "pmid": pmid.text if pmid is not None else "N/A",
                    "title": title.text if title is not None else "No Title",
                    "abstract": abstract.text if abstract is not None else "No Abstract",
                    "authors": authors,
                    "journal": journal.text if journal is not None else "N/A",
                    "doi": doi_elem.text if doi_elem is not None else None,
                }
                articles.append(article_data)
        except ET.ParseError as e:
            print(f"Error parsing XML: {e}")

        return articles

if __name__ == '__main__':
    # 이 파일을 직접 실행할 경우 테스트 코드
    print("--- Testing PubMedClient ---")
    pubmed_client = PubMedClient()
    
    # "AI in drug discovery"를 주제로 최신 논문 5개 검색
    test_query = "AI in drug discovery[Title/Abstract]"
    results = pubmed_client.search_articles(test_query, max_results=5)
    
    if results:
        print(f"\n--- Top 5 search results for '{test_query}' ---")
        for i, article in enumerate(results, 1):
            print(f"\n[{i}] PMID: {article['pmid']}")
            print(f"  Title: {article['title']}")
            print(f"  Journal: {article['journal']}")
            print(f"  Abstract: {article['abstract'][:150]}...")
    else:
        print("\nTest search returned no results.") 