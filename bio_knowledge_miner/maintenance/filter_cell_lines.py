"""
Filters the main gene-to-cell-line mapping file to create a specialized list
for a specific gene and mutation, based on keywords in the cell line name.

This script performs the following steps:
1. Reads the comprehensive `gene2cellline.csv` file.
2. Filters the data for a specified target gene (e.g., 'KRAS').
3. Further filters the results to select only cell lines whose names contain
   a specific mutation keyword (e.g., 'G12C').
4. Saves the cleaned, focused data to a new CSV file in the `outputs/reports`
   directory, which can then be used for downstream analysis pipelines.

Example Usage:
    python -m bio_knowledge_miner.maintenance.filter_cell_lines \
        --gene KRAS \
        --mutation G12C \
        --input_file auto_hypothesis_agent/resources/gene2cellline.csv
"""

import os
import argparse
import logging
import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def filter_cell_lines(gene: str, mutation: str, input_file: str) -> str | None:
    """
    Filters cell lines based on a target gene and mutation keyword.

    Args:
        gene: The target gene symbol (e.g., 'KRAS').
        mutation: The mutation keyword to search for (e.g., 'G12C').
        input_file: Path to the source `gene2cellline.csv` file.

    Returns:
        The path to the output file if successful, otherwise None.
    """
    logging.info(f"Reading data from {input_file}")
    try:
        df = pd.read_csv(input_file)
    except FileNotFoundError:
        logging.error(f"Input file not found: {input_file}")
        return None
    except Exception as e:
        logging.error(f"Failed to read CSV file: {e}")
        return None

    logging.info(f"Original data contains {len(df)} rows.")

    # 1. Filter by target gene
    gene_df = df[df['gene'].str.upper() == gene.upper()]
    logging.info(f"Found {len(gene_df)} rows for gene '{gene}'.")

    if gene_df.empty:
        logging.warning(f"No entries found for gene '{gene}'. No output file will be created.")
        return None

    # 2. Filter by mutation keyword in cell_line name (case-insensitive)
    mutation_df = gene_df[gene_df['cell_line'].str.contains(mutation, case=False, na=False)]
    logging.info(f"Found {len(mutation_df)} rows containing mutation keyword '{mutation}'.")
    
    if mutation_df.empty:
        logging.warning(f"No cell lines with mutation '{mutation}' found for gene '{gene}'. No output file will be created.")
        return None

    # 3. Prepare and save the output file
    output_dir = "outputs/reports"
    os.makedirs(output_dir, exist_ok=True)
    
    # Sanitize gene and mutation names for the filename
    safe_gene = "".join(c for c in gene if c.isalnum())
    safe_mutation = "".join(c for c in mutation if c.isalnum())
    timestamp = pd.Timestamp.now().strftime('%Y%m%d%H%M%S')
    
    output_filename = f"filtered_{safe_gene}_{safe_mutation}_cell_lines_{timestamp}.csv"
    output_path = os.path.join(output_dir, output_filename)

    try:
        mutation_df.to_csv(output_path, index=False)
        logging.info(f"Successfully saved filtered data to: {output_path}")
        return output_path
    except Exception as e:
        logging.error(f"Failed to save output file: {e}")
        return None


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Filter cell lines by gene and mutation keyword.")
    parser.add_argument(
        "--gene",
        type=str,
        required=True,
        help="Target gene symbol to filter by (e.g., KRAS)."
    )
    parser.add_argument(
        "--mutation",
        type=str,
        required=True,
        help="Mutation keyword to search for in the cell line name (e.g., G12C)."
    )
    parser.add_argument(
        "--input_file",
        type=str,
        default="auto_hypothesis_agent/resources/gene2cellline.csv",
        help="Path to the input gene-to-cell-line CSV file."
    )

    args = parser.parse_args()

    filter_cell_lines(args.gene, args.mutation, args.input_file) 