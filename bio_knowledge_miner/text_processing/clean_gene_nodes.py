"""Utility script to purge non-HGNC Gene nodes from Neo4j by checking against the official HGNC REST API.
Run: python -m bio_knowledge_miner.maintenance.clean_gene_nodes
"""
import os
import requests
import time
from typing import Set
from neo4j import GraphDatabase

from bio_knowledge_miner.knowledge_graph.neo4j_connector import get_driver

HGNC_API_BASE_URL = "https://rest.genenames.org"

def get_all_gene_symbols_from_db() -> Set[str]:
    """Fetch all gene symbols currently in the Neo4j database."""
    cypher = "MATCH (g:Gene) RETURN g.symbol AS symbol"
    with get_driver().session() as sess:
        results = sess.run(cypher)
        return {record["symbol"] for record in results}

def get_valid_hgnc_symbols(symbols_to_check: Set[str]) -> Set[str]:
    """Check a list of symbols against the HGNC API and return the set of valid, approved symbols."""
    valid_symbols = set()
    print(f"Checking {len(symbols_to_check)} symbols against HGNC API...")
    for i, symbol in enumerate(symbols_to_check):
        try:
            # Rate limiting: 10 requests per second
            if i > 0 and i % 9 == 0:
                time.sleep(1)
            
            headers = {"Accept": "application/json"}
            url = f"{HGNC_API_BASE_URL}/fetch/symbol/{symbol}"
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                # Check if the gene is an approved symbol
                if data['response']['numFound'] > 0 and data['response']['docs'][0]['status'] == 'Approved':
                    valid_symbols.add(symbol.upper())
            elif response.status_code != 404: # Ignore 404s (not found), but log other errors
                 print(f"Warning: HGNC API returned status {response.status_code} for symbol {symbol}")

        except requests.exceptions.RequestException as e:
            print(f"Error checking symbol {symbol}: {e}")
            continue
    print(f"Found {len(valid_symbols)} valid HGNC symbols.")
    return valid_symbols

def fetch_approved_hgnc_symbols(driver) -> Set[str]:
    """
    Fetches all gene symbols from the database and validates them against the HGNC API.
    Returns a set of approved gene symbols.
    """
    print("Fetching all gene names from the database...")
    db_names = set()
    with driver.session() as session:
        # Corrected to use g.name and filter out None values
        result = session.run("MATCH (g:Gene) RETURN g.name AS name")
        for record in result:
            if record["name"]:
                db_names.add(record["name"])
    
    if not db_names:
        print("No gene names found in the database to validate.")
        return set()
    print(f"Found {len(db_names)} unique gene names to validate.")

    # 2. Get the official list of valid symbols from the HGNC API
    valid_hgnc_symbols = get_valid_hgnc_symbols(db_names)

    # 3. Determine which symbols to delete
    # We need to compare them case-insensitively
    db_names_upper = {s.upper() for s in db_names}
    symbols_to_delete_upper = db_names_upper - {s.upper() for s in valid_hgnc_symbols}
    
    # Find the original-cased symbols to delete
    symbols_to_delete = [s for s in db_names if s.upper() in symbols_to_delete_upper]

    if not symbols_to_delete:
        print("All gene nodes are valid. No cleanup needed.")
        return set()
        
    print(f"Found {len(symbols_to_delete)} gene(s) to be purged: {symbols_to_delete[:10]}...") # Print first 10

    # 4. Delete the invalid nodes
    cypher_delete = "MATCH (g:Gene) WHERE g.symbol IN $symbols_to_delete DETACH DELETE g"
    with get_driver().session() as sess:
        result = sess.run(cypher_delete, symbols_to_delete=symbols_to_delete)
        summary = result.consume()
        print(f"Purged {summary.counters.nodes_deleted} Gene nodes.")

    return valid_hgnc_symbols

def clean_invalid_gene_nodes(driver, approved_symbols: Set[str]):
    """
    Deletes gene nodes from the database that are not in the provided approved gene symbol list.
    """
    print(f"Cleaning database, keeping {len(approved_symbols)} approved gene names.")
    # Corrected to use g.name
    query = "MATCH (g:Gene) WHERE NOT g.name IN $names DETACH DELETE g"
    
    with driver.session() as session:
        result = session.run(query, names=list(approved_symbols))
        summary = result.consume()
        print(f"Deleted {summary.counters.nodes_deleted} invalid gene nodes.")

def main():
    """
    Main function to run the gene cleaning process.
    """
    uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    user = os.environ.get("NEO4J_USERNAME", "neo4j")
    password = os.environ.get("NEO4J_PASSWORD", "password")
    
    driver = None
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        driver.verify_connectivity()
        print("Successfully connected to Neo4j.")

        approved_gene_symbols = fetch_approved_hgnc_symbols(driver)
        if approved_gene_symbols:
            clean_invalid_gene_nodes(driver, approved_gene_symbols)
        
        # Removed the export_graph_data(driver) call

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if driver:
            driver.close()
            print("Neo4j connection closed.")

if __name__ == "__main__":
    main() 