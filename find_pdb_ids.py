"""
PDB Finder Helper Script

This script helps researchers find relevant PDB IDs for a given target
by querying the RCSB PDB database.

It takes a search query as input and returns a list of the most relevant
PDB entries with their key metadata, allowing the researcher to make an
informed decision on which PDB ID to use in the main drug discovery pipeline.
"""
import argparse
import requests
import logging
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

def get_pdb_ids_from_search(query: str, top_n: int) -> List[str]:
    """
    Step 1: Use the Search API to get a list of relevant PDB IDs.
    """
    logging.info(f"Searching for PDB IDs related to '{query}'...")
    search_url = "https://search.rcsb.org/rcsbsearch/v2/query"
    api_query = {
        "query": {
            "type": "group",
            "logical_operator": "and",
            "nodes": [
                {
                    "type": "terminal",
                    "service": "text",
                    "parameters": {"attribute": "struct.title", "operator": "contains_phrase", "value": query}
                },
                 {
                    "type": "terminal",
                    "service": "text",
                    "parameters": {"attribute": "rcsb_entry_info.resolution_combined", "operator": "exists"}
                }
            ],
        },
        "return_type": "entry",
        "request_options": {
            "paginate": {"start": 0, "rows": top_n},
            "sort": [{"sort_by": "score", "direction": "desc"}],
            "results_content_type": ["experimental"]
        }
    }
    
    try:
        response = requests.post(search_url, json=api_query)
        response.raise_for_status()
        results = response.json()
        
        pdb_ids = [item["identifier"] for item in results.get("result_set", [])]
        if not pdb_ids:
            logging.warning("No PDB IDs found for the query.")
            return []
            
        logging.info(f"Found {len(pdb_ids)} relevant PDB IDs. Now fetching details...")
        return pdb_ids

    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to query RCSB Search API: {e}")
        return []

def get_details_for_pdb_ids(pdb_ids: List[str]) -> List[Dict[str, Any]]:
    """
    Step 2: Use the Data API (GraphQL) to fetch detailed information for the given PDB IDs.
    """
    if not pdb_ids:
        return []

    data_url = "https://data.rcsb.org/graphql"
    graphql_query = """
    query($entry_ids: [String!]!) {
      entries(entry_ids: $entry_ids) {
        rcsb_id
        struct {
          title
        }
        rcsb_entry_info {
          resolution_combined
        }
        rcsb_accession_info {
          initial_release_date
        }
      }
    }
    """
    variables = {"entry_ids": pdb_ids}

    try:
        response = requests.post(data_url, json={"query": graphql_query, "variables": variables})
        response.raise_for_status()

        # Handle cases where the response body might be empty
        if not response.content:
            logging.error("Data API returned an empty response body.")
            return []
            
        results = response.json()

        # Check for errors in the GraphQL response
        if "errors" in results and results["errors"]:
            error_message = results["errors"][0].get("message", "Unknown GraphQL error")
            logging.error(f"GraphQL API returned an error: {error_message}")
            return []
        
        # The GraphQL API returns results in the order they were requested, which is helpful.
        return results.get("data", {}).get("entries", [])

    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to query RCSB Data API: {e}")
        return []

def print_results_table(results: List[Dict[str, Any]]):
    """
    Prints the final results in a formatted table.
    """
    if not results:
        logging.info("No detailed information to display.")
        return

    # Header
    print("\n--- PDB Search Results ---")
    print(f"{'PDB ID':<10} | {'Resolution':<12} | {'Release Date':<15} | {'Title'}")
    print("-" * 80)

    # Rows
    for entry in results:
        if not entry: continue
        pdb_id = entry.get('rcsb_id', 'N/A')
        
        # Safely access nested dictionary keys
        title = entry.get('struct', {}).get('title', 'N/A')
        
        entry_info = entry.get('rcsb_entry_info', {})
        resolution_list = entry_info.get('resolution_combined', [None])
        resolution = f"{resolution_list[0]:.2f}" if resolution_list and resolution_list[0] is not None else "N/A"
        
        accession_info = entry.get('rcsb_accession_info', {})
        release_date = accession_info.get('initial_release_date', 'N/A')
        if release_date and 'T' in release_date:
            release_date = release_date.split('T')[0] # Keep only the date part

        # Truncate title if it's too long to fit in one line
        if len(title) > 60:
            title = title[:57] + "..."

        print(f"{pdb_id:<10} | {resolution:<12} | {release_date:<15} | {title}")
    
    print("-" * 80)

def find_pdb_ids(query: str, top_n: int = 10):
    """
    Main workflow: 
    1. Get PDB IDs from Search API.
    2. Get details for those IDs from Data API.
    3. Print the results.
    """
    pdb_ids = get_pdb_ids_from_search(query, top_n)
    if pdb_ids:
        detailed_results = get_details_for_pdb_ids(pdb_ids)
        print_results_table(detailed_results)

def main():
    """Main function to parse arguments."""
    parser = argparse.ArgumentParser(description="Find relevant PDB IDs from the RCSB database.")
    parser.add_argument(
        "--query",
        type=str,
        required=True,
        help="The search query (e.g., 'KRAS G12C', 'EGFR L858R')."
    )
    parser.add_argument(
        "--top_n",
        type=int,
        default=10,
        help="Number of top results to display."
    )
    args = parser.parse_args()
    
    find_pdb_ids(args.query, args.top_n)

if __name__ == "__main__":
    main() 