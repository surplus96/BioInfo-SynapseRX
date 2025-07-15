"""Fill missing SMILES / InChI for Compound nodes in Neo4j.

Usage
-----
# Fill all compounds with missing structures
$ python -m bio_knowledge_miner.maintenance.fill_compound_structures --limit 100

# Fill only compounds linked to a specific gene
$ python -m bio_knowledge_miner.maintenance.fill_compound_structures --gene KRAS
"""

from __future__ import annotations

import argparse
import requests
import re
from typing import Optional, Dict
from urllib.parse import quote_plus

from bio_knowledge_miner.knowledge_graph.neo4j_connector import get_driver, close_driver

# -----------------------------------------------------------------------------
# PubChem helper (stabilized version)
# -----------------------------------------------------------------------------

def _fetch_compound_info_pubchem(name: str) -> Optional[Dict[str, str | int]]:
    """Fetch CID, Canonical SMILES, and InChIKey for a compound from PubChem."""
    name = name.strip()
    encoded = quote_plus(name)
    info = {}

    try:
        url_name = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{encoded}/JSON"
        resp_name = requests.get(url_name, timeout=15)
        if resp_name.status_code == 200:
            data = resp_name.json()
            cid = data.get("PC_Compounds", [{}])[0].get("id", {}).get("id", {}).get("cid")
            if cid:
                info["pubchem_cid"] = cid
    except Exception:
        return None

    if not info.get("pubchem_cid"):
        return None

    cid = info["pubchem_cid"]
    try:
        url_sdf = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/SDF"
        resp_sdf = requests.get(url_sdf, timeout=15)
        if resp_sdf.status_code == 200:
            smiles_match = re.search(r"> <PUBCHEM_SMILES>\n(.*?)\n", resp_sdf.text)
            if smiles_match:
                info["smiles"] = smiles_match.group(1).strip()

        url_inchi = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/property/InChIKey/TXT"
        resp_inchi = requests.get(url_inchi, timeout=15)
        if resp_inchi.status_code == 200 and resp_inchi.text.strip():
            info["inchi_key"] = resp_inchi.text.strip().splitlines()[0]

        return info if info.get("smiles") else None
    except Exception:
        return None

# -----------------------------------------------------------------------------
# Main logic
# -----------------------------------------------------------------------------

def main(limit: int = 1000, gene: str | None = None):
    driver = get_driver()
    with driver.session() as sess:
        if gene:
            match_clause = "MATCH (c:Compound)-[:TARGETS]->(:Gene {name: $geneName})"
            params = {"geneName": gene.upper(), "lim": limit}
        else:
            match_clause = "MATCH (c:Compound)"
            params = {"lim": limit}

        query = (
            f"{match_clause} "
            "WHERE c.smiles IS NULL "
            "RETURN elementId(c) AS eid, c.name AS name "
            "LIMIT $lim"
        )
        
        print(f"[INFO] Running query: {query.replace('$lim', str(limit))}")
        nodes = sess.run(query, params)
        updated = 0
        
        nodes_to_process = list(nodes)
        print(f"[INFO] Found {len(nodes_to_process)} compound(s) to update.")

        for rec in nodes_to_process:
            node_eid = rec["eid"]
            name = rec.get("name")
            if not name:
                continue

            print(f"[INFO] Processing: {name}")
            info = _fetch_compound_info_pubchem(name)

            if not info:
                print(f"[WARN] Could not fetch info for '{name}'. Deleting node.")
                sess.run("MATCH (c) WHERE elementId(c)=$eid DETACH DELETE c", eid=node_eid)
                continue

            sess.run(
                "MATCH (c) WHERE elementId(c)=$eid "
                "SET c.smiles = $smi, "
                "    c.inchi_key = $ikey, "
                "    c.pubchem_cid = $cid",
                eid=node_eid,
                smi=info.get("smiles"),
                ikey=info.get("inchi_key"),
                cid=info.get("pubchem_cid"),
            )
            updated += 1
            print(f"[INFO] Successfully updated '{name}'.")

        print(f"\n[fill_compound_structures] Updated {updated} Compound nodes with structure data.")
    close_driver()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fill SMILES/InChI for Compound nodes")
    parser.add_argument("--limit", type=int, default=1000)
    parser.add_argument("--gene", type=str, help="Optional: Target only compounds linked to this gene.")
    args = parser.parse_args()
    main(limit=args.limit, gene=args.gene) 