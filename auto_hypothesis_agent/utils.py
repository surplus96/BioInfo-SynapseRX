import logging
import sys

def setup_logging(level=logging.INFO):
    """
    Set up a shared logging configuration for the project.
    
    Logs will be sent to stdout and formatted to include timestamp,
    log level, and the message.
    """
    # Get the root logger
    root_logger = logging.getLogger()
    
    # Remove any existing handlers to avoid duplicate logs
    if root_logger.handlers:
        for handler in root_logger.handlers:
            root_logger.removeHandler(handler)
            
    # Configure the logger
    logging.basicConfig(
        level=level,
        format="[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout
    )
    logging.info("Logging configured.")


import subprocess
from pathlib import Path
import re

def run_fpocket(pdb_path: Path) -> Path | None:
    """Runs fpocket on a given PDB file and returns the output directory."""
    if not pdb_path.exists():
        logging.error(f"PDB file not found at: {pdb_path}")
        return None

    output_dir = pdb_path.parent / f"{pdb_path.stem}_out"
    
    # Always re-run fpocket for fresh results. Remove old directory if it exists.
    if output_dir.exists():
        logging.info(f"Removing existing fpocket output directory: {output_dir}")
        import shutil
        shutil.rmtree(output_dir)

    # Add -C flag to ensure Center of Mass is calculated and present in the output
    command = ["fpocket", "-f", str(pdb_path), "-C"]
    logging.info(f"Running fpocket command: {' '.join(command)}")
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        logging.info("fpocket executed successfully.")
        logging.debug(f"fpocket stdout: {result.stdout}")
        return output_dir
    except FileNotFoundError:
        logging.error("fpocket command not found. Is it installed and in your PATH?")
        return None
    except subprocess.CalledProcessError as e:
        logging.error(f"fpocket failed with exit code {e.returncode}.")
        logging.error(f"fpocket stderr: {e.stderr}")
        return None


def _parse_fpocket_info(info_file: Path) -> list[dict]:
    """Parses the fpocket info file to extract pocket properties."""
    pockets = []
    if not info_file.exists():
        return pockets

    with open(info_file, 'r') as f:
        content = f.read()

    # Regex to find pocket blocks, robust to single or double newlines
    pocket_blocks = re.findall(r"Pocket\s*(\d+)\s*:\s*\n(.*?)(?=\n\nPocket|\Z)", content, re.DOTALL)

    for pocket_num_str, block_content in pocket_blocks:
        pocket_num = int(pocket_num_str)
        properties = {'pocket_number': pocket_num}
        
        for line in block_content.strip().split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower().replace(' ', '_')
                value = value.strip()
                try:
                    properties[key] = float(value)
                except ValueError:
                    properties[key] = value
        
        if properties:
            pockets.append(properties)
            
    return pockets


def get_best_pocket(pdb_path: Path) -> tuple[int, Path] | None:
    """
    Runs fpocket and returns the pocket number and PDB file of the most druggable pocket.
    
    Returns:
        A tuple (pocket_number, pocket_pdb_path), or None if failed.
    """
    fpocket_out_dir = run_fpocket(pdb_path)
    if not fpocket_out_dir:
        return None

    info_file = fpocket_out_dir / f"{pdb_path.stem}_info.txt"
    pockets = _parse_fpocket_info(info_file)

    if not pockets:
        logging.error(f"No pockets found or parsed from {info_file.name}.")
        return None

    # Sort pockets by "Druggability Score" in descending order
    pockets.sort(key=lambda p: p.get('druggability_score', p.get('score', 0)), reverse=True)

    best_pocket = pockets[0]
    pocket_number = best_pocket.get('pocket_number')
    
    if pocket_number is None:
        logging.error(f"Could not determine pocket number for the best pocket in {pdb_path.name}.")
        return None
        
    pocket_pdb_path = fpocket_out_dir / "pockets" / f"pocket{pocket_number}_atm.pdb"

    if not pocket_pdb_path.exists():
        logging.error(f"Best pocket PDB file not found at: {pocket_pdb_path}")
        return None

    logging.info(f"Found best pocket {pocket_number} with druggability score {best_pocket.get('druggability_score', 'N/A')}.")
    return int(pocket_number), pocket_pdb_path 