"""Variant / Viral Genome Annotation Script

Knowledge Graph(Neo4j)에 변이(Variant) 혹은 바이러스 유전체 Segment 노드를 추가하고
해당 Gene·질병 노드와 관계를 생성한다.

사용 예시
---------
$ python -m bio_knowledge_miner.maintenance.annotate_variants \
          --input variant_records.tsv

입력 TSV 필드: id, description, gene, disease
지정하지 않으면 KRAS_G12C · SARS2_ORF1ab 2건을 데모로 삽입한다.
"""

from __future__ import annotations

import argparse
import csv
from typing import Dict, List
import requests

from bio_knowledge_miner.knowledge_graph.neo4j_connector import get_driver, close_driver

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------


def _load_records(tsv_path: str) -> List[Dict[str, str]]:
    """Load TSV into list of dicts."""
    records: List[Dict[str, str]] = []
    with open(tsv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            records.append({k.strip(): (v or "").strip() for k, v in row.items()})
    return records


def _default_records() -> List[Dict[str, str]]:
    """Return minimal demo records when no input provided."""
    return [
        {
            "id": "KRAS_G12C",
            "description": "Oncogenic missense mutation G12C in KRAS gene",
            "gene": "KRAS",
            "disease": "Non-Small Cell Lung Cancer",
        },
        {
            "id": "SARS2_ORF1ab",
            "description": "ORF1ab polyprotein of SARS-CoV-2 viral genome",
            "gene": "ORF1ab",
            "disease": "COVID-19",
        },
    ]


# -----------------------------------------------------------------------------
# External annotation helpers (VEP / ClinVar)
# -----------------------------------------------------------------------------


def _fetch_vep_consequence(hgvs: str) -> str | None:
    """Call Ensembl VEP REST to obtain most severe consequence term.

    hgvs 예시: "KRAS:p.Gly12Cys".  Returns e.g. "missense_variant".
    """

    url = f"https://rest.ensembl.org/vep/human/hgvs/{hgvs}?content-type=application/json"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data and "most_severe_consequence" in data[0]:
                return data[0]["most_severe_consequence"]
    except Exception:  # pragma: no cover
        pass
    return None


def _fetch_clinvar_significance(term: str) -> str | None:
    """Query NCBI ClinVar E-utilities for clinical significance.

    *term* can be HGVS or gene+protein change string.
    Returns first clinical significance description (e.g. "Pathogenic").
    """

    base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    try:
        esearch = requests.get(
            f"{base}/esearch.fcgi",
            params={"db": "clinvar", "term": term, "retmax": 1, "retmode": "json"},
            timeout=10,
        ).json()
        ids = esearch.get("esearchresult", {}).get("idlist", [])
        if not ids:
            return None

        uid = ids[0]
        esummary = requests.get(
            f"{base}/esummary.fcgi",
            params={"db": "clinvar", "id": uid, "retmode": "json"},
            timeout=10,
        ).json()
        docsum = esummary.get("result", {}).get(uid, {})
        clin_sig = docsum.get("clinical_significance", {}).get("description")
        return clin_sig
    except Exception:  # pragma: no cover
        return None


# -----------------------------------------------------------------------------
# Main Annotation Logic
# -----------------------------------------------------------------------------


def _ingest(records: List[Dict[str, str]]):
    driver = get_driver()
    with driver.session() as session:
        for rec in records:
            # Build simple protein HGVS like 'KRAS:p.G12C' from id 'KRAS_G12C'
            hgvs_protein = f"{rec['gene']}:p.{rec['id'].split('_')[1]}" if '_' in rec['id'] else rec['id']

            vep_cons = _fetch_vep_consequence(hgvs_protein) or "unknown"
            clin_sig = _fetch_clinvar_significance(hgvs_protein) or "not_provided"

            session.run(
                """
                MERGE (v:Variant {id:$id})
                SET v.description=$desc,
                    v.clin_sig=$clin_sig,
                    v.vep_consequence=$vep
                WITH v
                MERGE (d:Disease {name:$disease})
                MERGE (v)-[:ASSOCIATED_WITH]->(d)
                WITH v
                MATCH (g:Gene {name:$gene})
                MERGE (v)-[:DERIVED_FROM]->(g)
                """,
                id=rec["id"],
                desc=rec["description"],
                gene=rec["gene"],
                disease=rec["disease"],
                clin_sig=clin_sig,
                vep=vep_cons,
            )
    close_driver()


def main() -> None:
    parser = argparse.ArgumentParser(description="Annotate Variant / Viral Genome nodes into Neo4j KG.")
    parser.add_argument("--input", help="TSV path with id,description,gene,disease columns", required=False)
    args = parser.parse_args()

    if args.input:
        records = _load_records(args.input)
    else:
        records = _default_records()

    if not records:
        print("[annotate_variants] No records to insert – exiting.")
        return

    _ingest(records)
    print(f"[annotate_variants] Imported {len(records)} records into Neo4j.")


if __name__ == "__main__":
    main() 