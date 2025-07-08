"""Minimal Ensembl REST client to fetch CDS (coding DNA sequence) for a gene symbol (human, GRCh38).
Note: real implementation should handle species & isoform selection robustly.
"""
from __future__ import annotations

import requests
from functools import lru_cache

SERVER = "https://rest.ensembl.org"
HEADERS = {"Content-Type": "text/plain"}

@lru_cache(maxsize=256)
def fetch_cds(gene_symbol: str) -> str | None:
    """Return CDS DNA sequence (uppercase A/C/G/T) or None."""
    # Step 1: get gene id
    url = f"{SERVER}/xrefs/symbol/homo_sapiens/{gene_symbol}?"  # species fixed to human
    try:
        j = requests.get(url, headers={"Content-Type": "application/json"}, timeout=10).json()
    except Exception:
        return None
    if not j:
        return None
    # pick first gene match
    gene_id = j[0]["id"]
    # Step 2: get canonical transcript
    url_t = f"{SERVER}/lookup/id/{gene_id}?expand=1"
    try:
        info = requests.get(url_t, headers={"Content-Type": "application/json"}, timeout=10).json()
    except Exception:
        return None
    transcripts = info.get("Transcript", [])
    if not transcripts:
        return None
    canonical = transcripts[0]["id"]
    # Step 3: CDS sequence
    seq_url = f"{SERVER}/sequence/id/{canonical}?type=cds"
    try:
        cds = requests.get(seq_url, headers=HEADERS, timeout=10).text.strip()
    except Exception:
        return None
    if cds.startswith(">"):
        cds = "".join(cds.splitlines()[1:])
    return cds.upper() if cds else None 