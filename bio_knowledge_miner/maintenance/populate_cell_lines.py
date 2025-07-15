"""
Populate Cell Line data from the Cellosaurus API.

This script queries the Cellosaurus API for cell lines associated with gene symbols
found in the local Neo4j database. It then creates CellLine nodes and establishes
'EXPRESSED_IN' relationships between the corresponding Gene and CellLine nodes.

Workflow:
1. Connect to Neo4j.
2. Fetch all existing Gene symbols.
3. For each gene, query the Cellosaurus API.
4. Parse the response to get cell line names.
5. For each cell line:
   a. Create a 'CellLine' node if it doesn't exist.
   b. Create an 'EXPRESSED_IN' relationship from the Gene to the CellLine
      if it doesn't already exist.

To run:
- Ensure NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD environment variables are set.
- Execute from the project root:
  python -m bio_knowledge_miner.maintenance.populate_cell_lines
"""
import os
import time
import requests
import pandas as pd
from neo4j import GraphDatabase
import logging
import math

from bio_knowledge_miner import config # 중앙 설정 파일 임포트

# 올바른 API 엔드포인트로 수정
CELLOSAURUS_API_URL = "https://api.cellosaurus.org/search/cell-line"

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_all_gene_names(driver) -> list:
    """Fetches all gene names from the Neo4j database, sorted for consistent processing."""
    logging.info("Fetching all gene names from the database...")
    with driver.session() as session:
        result = session.run("MATCH (g:Gene) WHERE g.name IS NOT NULL RETURN g.name AS name")
        # 정렬하여 처리 순서를 일관되게 만듦
        symbols = sorted([record["name"] for record in result if record["name"]])
        logging.info(f"Found {len(symbols)} unique gene names.")
        return symbols

def search_cellosaurus(gene_name: str) -> list:
    """Queries the Cellosaurus API for a given gene name with robust error handling."""
    # 가장 단순한 쿼리 방식 유지
    params = {"q": gene_name, "format": "json"}
    try:
        response = requests.get(CELLOSAURUS_API_URL, params=params, timeout=30)
        response.raise_for_status()
        
        if not response.text:
            logging.warning(f"Empty response from Cellosaurus for '{gene_name}'")
            return []
            
        data = response.json()
        
        # 중첩된 JSON 구조를 올바르게 파싱하도록 수정
        cellosaurus_data = data.get("Cellosaurus", {})
        cell_lines_list = cellosaurus_data.get("cell-line-list", [])
        
        # name-list에서 identifier 값을 정확히 추출
        names = []
        for item in cell_lines_list:
            # 각 cell line의 name-list를 가져옴
            name_list = item.get("name-list", [])
            if name_list:
                # 첫 번째 identifier를 이름으로 사용
                names.append(name_list[0].get("value"))

        return [name for name in names if name] # None 이나 빈 문자열 제거
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Error querying Cellosaurus for '{gene_name}': {e}")
        return []
    except ValueError:
        logging.error(f"Could not decode JSON for gene '{gene_name}'. Response: {response.text[:200]}...")
        return []


def add_cell_line_data(driver, gene_name: str, cell_lines: list):
    """
    Creates CellLine nodes and relationships for a given gene.
    This function uses a single transaction to add all cell lines for a gene.
    """
    if not cell_lines:
        return

    query = """
    MATCH (g:Gene {name: $gene_name})
    UNWIND $cell_lines AS cell_line_name
    MERGE (cl:CellLine {name: cell_line_name})
    MERGE (g)-[:EXPRESSED_IN]->(cl)
    """
    with driver.session() as session:
        result = session.run(query, gene_name=gene_name, cell_lines=cell_lines)
        summary = result.consume()
        # summary.counters provides info on nodes_created, relationships_created etc.
        nodes_created = summary.counters.nodes_created
        rels_created = summary.counters.relationships_created
        if nodes_created > 0 or rels_created > 0:
            logging.info(f"  - For gene '{gene_name}': Added {nodes_created} nodes and {rels_created} relationships.")


def export_gene_cellline_data(driver):
    """
    Exports the Gene-CellLine relationships to a CSV file.
    """
    logging.info("\nExporting gene-to-cell-line data...")
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'auto_hypothesis_agent', 'resources'))
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'gene2cellline.csv')

    query = """
    MATCH (g:Gene)-[:EXPRESSED_IN]->(cl:CellLine)
    RETURN g.name AS gene, cl.name AS cell_line
    """
    try:
        with driver.session() as session:
            result = session.run(query)
            df = pd.DataFrame([record.data() for record in result])
        
        if not df.empty:
            df.to_csv(output_path, index=False, header=True)
            logging.info(f"Successfully exported {len(df)} records to {output_path}")
        else:
            logging.info("No gene-to-cell-line data found to export.")
            # Create an empty file with header if it doesn't exist
            if not os.path.exists(output_path):
                pd.DataFrame(columns=['gene', 'cell_line']).to_csv(output_path, index=False)
    except Exception as e:
        logging.error(f"Failed to export gene-to-cell-line data: {e}")


def main():
    """Main function to orchestrate fetching, populating, and exporting cell line data."""
    # 환경 변수 대신 중앙 config 파일에서 접속 정보 로드
    uri = config.NEO4J_URI
    user = config.NEO4J_USER
    password = config.NEO4J_PASSWORD
    
    driver = None
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        driver.verify_connectivity()
        logging.info("Successfully connected to Neo4j.")

        gene_names = get_all_gene_names(driver)
        
        if not gene_names:
            logging.warning("No gene names found in the database. Exiting.")
            return

        total_genes = len(gene_names)
        batch_size = 100  # 100개 유전자마다 잠시 휴식
        num_batches = math.ceil(total_genes / batch_size)
        
        logging.info(f"Starting to query Cellosaurus for {total_genes} genes in {num_batches} batches...")

        for i, name in enumerate(gene_names):
            logging.info(f"({i+1}/{total_genes}) Processing: {name}")
            
            cell_lines = search_cellosaurus(name)
            if cell_lines:
                logging.info(f"  - Found {len(cell_lines)} potential cell lines for '{name}'.")
                add_cell_line_data(driver, name, cell_lines)
            else:
                logging.info(f"  - No cell lines found for '{name}'.")

            # API 요청 속도 제어
            time.sleep(0.2) # 개별 요청 사이의 짧은 대기
            if (i + 1) % batch_size == 0 and i + 1 < total_genes:
                logging.info(f"--- Completed batch { (i + 1) // batch_size }/{num_batches}. Taking a short break... ---")
                time.sleep(5) # 배치 처리 후 긴 대기

        export_gene_cellline_data(driver)

    except Exception as e:
        logging.error(f"An unexpected error occurred in main: {e}", exc_info=True)
    finally:
        if driver:
            driver.close()
            logging.info("Neo4j connection closed.")

if __name__ == "__main__":
    # 스크립트 실행을 print 대신 logging으로 변경
    logging.info("Starting cell line population script...")
    main()
    logging.info("Cell line population script finished.") 