import argparse
import glob
import logging
import os
import pandas as pd

from bio_knowledge_miner.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
from bio_knowledge_miner.knowledge_graph.neo4j_connector import get_driver, close_driver

logging.basicConfig(level=logging.INFO, format='[%(asctime)s - %(levelname)s] %(message)s')

def get_latest_filtered_file(gene_symbol: str) -> str | None:
    """Find the most recent filtered cell line file for a given gene."""
    search_pattern = f"outputs/reports/filtered_{gene_symbol}_*_cell_lines_*.csv"
    files = glob.glob(search_pattern)
    if not files:
        logging.warning(f"No filtered cell line files found for gene '{gene_symbol}' with pattern: {search_pattern}")
        return None
    
    latest_file = max(files, key=os.path.getctime)
    logging.info(f"Found latest filtered file: {latest_file}")
    return latest_file

def update_graph_relationships(driver, gene_symbol: str, valid_cell_lines: list[str]):
    """
    Updates the graph by removing old cell line relationships for a gene
    and creating new ones based on the provided valid list.
    """
    # 1. Delete all existing [:HAS_CELL_LINE] relationships for the specified gene.
    # This ensures a clean slate and removes any outdated or incorrect connections.
    delete_query = """
    MATCH (g:Gene {name: $gene_symbol})-[r:HAS_CELL_LINE]->(c:CellLine)
    DELETE r
    """
    logging.info(f"Deleting existing HAS_CELL_LINE relationships for gene: {gene_symbol}")
    with driver.session() as session:
        session.run(delete_query, gene_symbol=gene_symbol)

    # 2. Create new relationships based on the filtered, valid list.
    # This query iterates through the list of valid cell line names, finds the corresponding
    # Gene and CellLine nodes, and creates a new :HAS_CELL_LINE relationship between them.
    # MERGE is used for nodes to avoid creating duplicates if they already exist.
    # The relationship is created with CREATE to ensure it's new.
    create_query = """
    UNWIND $cell_lines AS cell_line_name
    MERGE (g:Gene {name: $gene_symbol})
    MERGE (c:CellLine {name: cell_line_name})
    CREATE (g)-[:HAS_CELL_LINE]->(c)
    """
    logging.info(f"Creating {len(valid_cell_lines)} new HAS_CELL_LINE relationships for gene: {gene_symbol}")
    with driver.session() as session:
        session.run(create_query, gene_symbol=gene_symbol, cell_lines=valid_cell_lines)
    logging.info("Graph update complete.")


def main():
    parser = argparse.ArgumentParser(description="Update the knowledge graph with filtered cell line data.")
    parser.add_argument("--gene", type=str, required=True, help="The gene symbol to process (e.g., KRAS).")
    args = parser.parse_args()

    # Find and read the filtered data
    filtered_csv_path = get_latest_filtered_file(args.gene)
    if not filtered_csv_path:
        return
    
    try:
        df = pd.read_csv(filtered_csv_path)
        if "cell_line" not in df.columns:
            raise ValueError("CSV file must have a 'cell_line' column.")
        valid_cell_lines = df["cell_line"].unique().tolist()
    except Exception as e:
        logging.error(f"Failed to read or process {filtered_csv_path}: {e}")
        return
        
    if not valid_cell_lines:
        logging.warning("No valid cell lines found in the filtered file. No updates will be made to the graph.")
        return

    # Connect to the graph and perform the update
    driver = None
    try:
        driver = get_driver()
        update_graph_relationships(driver, args.gene, valid_cell_lines)
    except Exception as e:
        logging.error(f"An error occurred during graph connection or update: {e}")
    finally:
        if driver:
            close_driver()

if __name__ == "__main__":
    main() 