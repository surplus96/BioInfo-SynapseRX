"""Utility script to purge non-HGNC Gene nodes from Neo4j.
Run: python -m bio_knowledge_miner.maintenance.clean_gene_nodes
"""

from pathlib import Path
import sys

from bio_knowledge_miner.knowledge_graph.neo4j_connector import get_driver

HGNC_PATH = Path(__file__).parent.parent.parent / "auto_hypothesis_agent" / "resources" / "hgnc_symbols.txt"
if not HGNC_PATH.exists():
    print("HGNC symbol list not found:", HGNC_PATH, file=sys.stderr)
    sys.exit(1)

HGNC_SET = {ln.strip().upper() for ln in HGNC_PATH.read_text().splitlines() if ln.strip()}

CYPHER = (
    "MATCH (g:Gene) WHERE NOT toUpper(g.name) IN $whitelist "
    "DETACH DELETE g"
)

def main():
    driver = get_driver()
    with driver.session() as sess:
        result = sess.run("MATCH (g:Gene) RETURN count(g) AS total")
        total_before = result.single()["total"]
        sess.run(CYPHER, whitelist=list(HGNC_SET))
        total_after = sess.run("MATCH (g:Gene) RETURN count(g) AS total").single()["total"]
        print(f"Purged Gene nodes: {total_before - total_after}. Remaining: {total_after}")

if __name__ == "__main__":
    main() 