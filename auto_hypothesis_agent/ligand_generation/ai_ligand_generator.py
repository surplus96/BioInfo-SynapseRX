"""
AI-based Ligand Generator (Skeleton)

This module is responsible for generating novel ligand structures (SMILES)
for a given protein target.

For now, it contains a placeholder function that returns a pre-defined list
of known inhibitors for testing the pipeline.
"""
from __future__ import annotations
import logging
from typing import List
from pathlib import Path
import pandas as pd

from bio_knowledge_miner.knowledge_graph.neo4j_connector import get_driver, close_driver


class LigandGenerator:
    """
    Retrieves candidate ligands from the knowledge graph for a given target gene.
    This version replaces the Pocket2Mol-based generation approach.
    """

    def __init__(self):
        """
        Initializes the generator. No external dependencies needed.
        """
        logging.info("LigandGenerator initialized (Neo4j-based candidate retrieval).")
        pass

    def generate_candidates(
        self, target_gene: str, num_candidates: int = 100
    ) -> pd.DataFrame:
        """
        Retrieves candidate compounds (SMILES and names) from the Neo4j database
        that are linked to the target gene.

        Args:
            target_gene: The official gene symbol (e.g., 'KRAS').
            num_candidates: The maximum number of compounds to retrieve.

        Returns:
            A pandas DataFrame with 'compound_id', 'name', and 'smiles' columns.
            Returns an empty DataFrame if no candidates are found.
        """
        gene_name = target_gene.upper()
        
        logging.info(f"Retrieving candidate ligands for gene '{gene_name}' from Neo4j.")

        driver = get_driver()
        records = []
        try:
            with driver.session() as session:
                query = (
                    "MATCH (g:Gene {name: $gene_name})<-[:TARGETS]-(c:Compound) "
                    "WHERE c.smiles IS NOT NULL AND c.pubchem_cid IS NOT NULL AND c.name IS NOT NULL "
                    "RETURN c.pubchem_cid AS compound_id, c.name AS name, c.smiles AS smiles "
                    "LIMIT $limit"
                )
                result = session.run(query, gene_name=gene_name, limit=num_candidates)
                records = [
                    {"compound_id": r["compound_id"], "name": r["name"], "smiles": r["smiles"]}
                    for r in result
                ]
        except Exception as e:
            logging.error(f"Failed to retrieve candidates from Neo4j: {e}")
            return pd.DataFrame()
        finally:
            close_driver()

        if not records:
            logging.warning(f"No candidate compounds with SMILES found for gene '{gene_name}' in the database.")
            return pd.DataFrame()

        df = pd.DataFrame(records)
        # Use compound_id as name if name is missing
        df['name'] = df['name'].fillna(df['compound_id'])

        logging.info(f"Successfully retrieved {len(df)} candidate compounds for {gene_name}.")
        return df 