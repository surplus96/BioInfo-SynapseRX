import argparse
from bio_knowledge_miner.__main__ import run_pipeline

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Bio-Knowledge Miner Pipeline. Collects data from PubMed, processes it, and builds a knowledge graph."
    )
    parser.add_argument(
        '--queries', 
        nargs='+', 
        required=True, 
        help='List of search queries for PubMed, enclosed in quotes. For example: "KRAS G12C inhibitors[Title/Abstract]" "Sotorasib mechanism of action[Title/Abstract]"'
    )
    args = parser.parse_args()
    
    run_pipeline(args.queries) 