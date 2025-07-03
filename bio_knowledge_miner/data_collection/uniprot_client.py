"""Simple UniProt REST client to fetch canonical FASTA sequence for a gene symbol.
Light-weight wrapper (no external deps beyond requests).
"""

from __future__ import annotations

import requests
from functools import lru_cache

BASE = "https://rest.uniprot.org/uniprotkb/search"

@lru_cache(maxsize=256)
def fetch_fasta(gene_symbol: str) -> str | None:
    """Return amino-acid sequence string (uppercase letters A-Z) or None if not found."""
    query = f"gene_exact:{gene_symbol} AND reviewed:true"
    params = {
        "query": query,
        "format": "fasta",
        "size": 1,
        "fields": "accession,sequence",
    }
    try:
        resp = requests.get(BASE, params=params, timeout=10)
        resp.raise_for_status()
    except requests.RequestException:
        return None

    text = resp.text.strip()
    if not text.startswith(">"):
        return None
    lines = text.splitlines()
    seq = "".join(lines[1:])
    return seq if seq else None 