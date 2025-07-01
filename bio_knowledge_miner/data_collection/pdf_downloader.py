import os
import time
from typing import Optional
import requests
from .. import config

HEADERS = {"User-Agent": "BioKnowledgeMiner/0.1"}


def download_file(url: str, dest_path: str) -> bool:
    """주어진 URL에서 PDF를 다운로드하여 dest_path에 저장."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        if r.status_code == 200 and "application/pdf" in r.headers.get("content-type", ""):
            with open(dest_path, "wb") as f:
                f.write(r.content)
            print(f"✅ PDF saved → {dest_path}")
            return True
        else:
            print(f"PDF download failed ({r.status_code}): {url}")
    except Exception as e:
        print(f"PDF download error: {e}")
    return False


def _query_unpaywall(doi: str) -> Optional[str]:
    endpoint = f"https://api.unpaywall.org/v2/{doi}?email=test@example.com"
    try:
        r = requests.get(endpoint, headers=HEADERS, timeout=10)
        if r.ok:
            data = r.json()
            loc = data.get("best_oa_location") or {}
            return loc.get("url_for_pdf")
    except Exception:
        pass
    return None


def _query_crossref(doi: str) -> Optional[str]:
    endpoint = f"https://api.crossref.org/works/{doi}"
    try:
        r = requests.get(endpoint, headers=HEADERS, timeout=10)
        if r.ok:
            for link in r.json().get("message", {}).get("link", []):
                if link.get("content-type") == "application/pdf":
                    return link.get("URL")
    except Exception:
        pass
    return None


def _query_europe_pmc(pmid: str) -> Optional[str]:
    endpoint = f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=EXT_ID:{pmid}&resultType=core&format=json"
    try:
        r = requests.get(endpoint, headers=HEADERS, timeout=10)
        if r.ok:
            result = r.json().get("resultList", {}).get("result", [])
            if result:
                full_list = result[0].get("fullTextUrlList", {}).get("fullTextUrl", [])
                for item in full_list:
                    if item.get("documentStyle") == "pdf":
                        return item.get("url")
    except Exception:
        pass
    return None


def find_pdf_url(pmid: str, doi: Optional[str]) -> Optional[str]:
    """여러 API를 통해 무료 PDF URL을 탐색."""
    # 1) Unpaywall
    if doi:
        url = _query_unpaywall(doi)
        if url:
            return url
    # 2) Crossref
    if doi:
        url = _query_crossref(doi)
        if url:
            return url
    # 3) Europe PMC
    url = _query_europe_pmc(pmid)
    return url 