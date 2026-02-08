"""Fetch and parse PEP metadata from GitHub repository."""

import argparse
import csv
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List

# Add parent directory to path to import src modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_acquisition.github_fetcher import PEPFetcher
from src.data_acquisition.rst_parser import PEPMetadata, RSTParser

logger = logging.getLogger(__name__)


def save_to_csv(data: List[PEPMetadata], output_path: Path) -> None:
    """
    Save PEP metadata to CSV file.

    Args:
        data: List of PEPMetadata objects to save
        output_path: Path where to save the CSV file

    Note:
        Multiple authors are joined with semicolons (;).
        Empty created fields are saved as empty strings.
    """
    logger.info(f"Saving {len(data)} PEPs to {output_path}")

    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Define CSV headers
    fieldnames = ['pep_number', 'title', 'status', 'type', 'created', 'authors']

    # Write CSV file
    with open(output_path, 'w', encoding='utf-8', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for pep in data:
            # Join multiple authors with semicolon
            authors_str = '; '.join(pep.authors)

            # Handle None created field
            created_str = pep.created if pep.created is not None else ''

            writer.writerow({
                'pep_number': pep.pep_number,
                'title': pep.title,
                'status': pep.status,
                'type': pep.type,
                'created': created_str,
                'authors': authors_str
            })

    logger.info(f"Successfully saved to {output_path}")


def parse_arguments(args: List[str] = None) -> argparse.Namespace:
    """
    Parse command-line arguments.

    Args:
        args: List of arguments to parse (defaults to sys.argv)

    Returns:
        Parsed arguments as Namespace object
    """
    parser = argparse.ArgumentParser(
        description='Fetch and parse PEP metadata from GitHub repository'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        default='data/processed',
        help='Output directory for processed CSV file (default: data/processed)'
    )

    parser.add_argument(
        '--keep-raw',
        action='store_true',
        help='Keep raw downloaded files (default: delete after processing)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging output'
    )

    return parser.parse_args(args)


def main() -> int:
    """
    Main function to fetch and parse PEP metadata.

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    # Parse command-line arguments
    args = parse_arguments()

    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info("Starting PEP metadata fetch and parse")

    try:
        # Initialize components
        fetcher = PEPFetcher()
        parser = RSTParser()

        # Set up paths
        project_root = Path(__file__).parent.parent
        raw_dir = project_root / "data" / "raw"
        output_dir = project_root / args.output_dir

        # Create directories
        raw_dir.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate timestamped filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_path = raw_dir / f"peps_{timestamp}.zip"
        extract_dir = raw_dir / f"peps_extracted_{timestamp}"
        csv_path = output_dir / f"peps_metadata_{timestamp}.csv"

        # Step 1: Download PEP repository
        logger.info("Step 1/4: Downloading PEP repository...")
        url = "https://github.com/python/peps/archive/refs/heads/main.zip"
        fetcher.download_repo(url, zip_path)
        logger.info(f"Downloaded to {zip_path}")

        # Step 2: Extract zip file
        logger.info("Step 2/4: Extracting zip file...")
        fetcher.extract_zip(zip_path, extract_dir)
        logger.info(f"Extracted to {extract_dir}")

        # Step 3: Find and parse PEP files
        logger.info("Step 3/4: Finding PEP files...")
        # The extracted directory structure is typically: peps-main/peps/
        pep_dir = extract_dir / "peps-main" / "peps"

        if not pep_dir.exists():
            # Try to find the peps directory
            possible_dirs = list(extract_dir.glob("*/peps"))
            if possible_dirs:
                pep_dir = possible_dirs[0]
                logger.info(f"Found PEP directory: {pep_dir}")
            else:
                logger.error(f"Could not find peps directory in {extract_dir}")
                return 1

        pep_files = fetcher.get_pep_files(pep_dir)
        logger.info(f"Found {len(pep_files)} PEP files")

        logger.info("Parsing PEP metadata...")
        pep_metadata = parser.parse_multiple_peps(pep_files)
        logger.info(f"Successfully parsed {len(pep_metadata)} PEPs")

        # Step 4: Save to CSV
        logger.info("Step 4/4: Saving to CSV...")
        save_to_csv(pep_metadata, csv_path)

        # Clean up raw files if not keeping
        if not args.keep_raw:
            logger.info("Cleaning up temporary files...")
            fetcher.cleanup(zip_path)
            fetcher.cleanup(extract_dir)
            logger.info("Cleanup complete")
        else:
            logger.info(f"Keeping raw files (--keep-raw flag set)")
            logger.info(f"  Zip file: {zip_path}")
            logger.info(f"  Extracted: {extract_dir}")

        # Summary
        logger.info("\n" + "="*60)
        logger.info("SUCCESS: PEP metadata fetch complete")
        logger.info("="*60)
        logger.info(f"Total PEPs processed: {len(pep_metadata)}")
        logger.info(f"Output CSV file: {csv_path}")
        logger.info("="*60)

        return 0

    except Exception as e:
        logger.error(f"Failed to fetch and parse PEPs: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
