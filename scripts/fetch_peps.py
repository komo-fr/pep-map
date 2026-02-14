"""Fetch and parse PEP metadata from GitHub repository."""

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.data_acquisition.citation_extractor import CitationExtractor
from src.data_acquisition.github_fetcher import PEPFetcher
from src.data_acquisition.pep_parser import PEPParser

logger = logging.getLogger(__name__)

PEP_REPO_URL = "https://github.com/python/peps/archive/refs/heads/main.zip"


def save_metadata_json(metadata: dict, output_path: Path) -> None:
    """
    Save metadata to JSON file.

    Args:
        metadata: Dictionary containing metadata (fetched_at, source_url, etc.)
        output_path: Path where to save the JSON file

    Note:
        JSON is formatted with indentation for readability.
    """
    logger.info(f"Saving metadata to {output_path}")

    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write JSON file with indentation
    with open(output_path, "w", encoding="utf-8") as jsonfile:
        json.dump(metadata, jsonfile, indent=2, ensure_ascii=False)

    logger.info(f"Successfully saved metadata to {output_path}")


def parse_arguments(args: Optional[list[str]] = None) -> argparse.Namespace:
    """
    Parse command-line arguments.

    Args:
        args: List of arguments to parse (defaults to sys.argv)

    Returns:
        Parsed arguments as Namespace object
    """
    parser = argparse.ArgumentParser(
        description="Fetch and parse PEP metadata from GitHub repository"
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/processed",
        help="Output directory for processed CSV file (default: data/processed)",
    )

    parser.add_argument(
        "--keep-raw",
        action="store_true",
        help="Keep raw downloaded files (default: delete after processing)",
    )

    parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose logging output"
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
        level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    logger.info("Starting PEP metadata fetch and parse")

    try:
        # Initialize components
        fetcher = PEPFetcher()
        parser = PEPParser()
        citation_extractor = CitationExtractor()

        # Set up paths
        project_root = Path(__file__).parent.parent
        raw_dir = project_root / "data" / "raw"
        output_dir = project_root / args.output_dir

        # Create directories
        raw_dir.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate timestamp for raw files (still need this for temp files)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        zip_path = raw_dir / f"peps_{timestamp}.zip"
        extract_dir = raw_dir / f"peps_extracted_{timestamp}"

        # Fixed output filenames (no timestamp)
        csv_path = output_dir / "peps_metadata.csv"
        citations_path = output_dir / "citations.csv"
        metadata_path = output_dir / "metadata.json"

        # Step 1: Download PEP repository
        logger.info("Step 1/5: Downloading PEP repository...")
        fetcher.download_repo(PEP_REPO_URL, zip_path)
        logger.info(f"Downloaded to {zip_path}")

        # Step 2: Extract zip file
        logger.info("Step 2/5: Extracting zip file...")
        fetcher.extract_zip(zip_path, extract_dir)
        logger.info(f"Extracted to {extract_dir}")

        # Step 3: Find and parse PEP files
        logger.info("Step 3/5: Finding PEP files...")
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

        # Step 4: Extract citations
        logger.info("Step 4/5: Extracting citations...")
        citations_df = citation_extractor.extract_from_multiple_files(pep_files)
        logger.info(f"Extracted {len(citations_df)} citation records")

        # Step 5: Save all data
        logger.info("Step 5/5: Saving data...")

        # Save PEP metadata CSV
        logger.info("Saving PEP metadata CSV...")
        parser.save_to_csv(pep_metadata, csv_path)

        # Save citations CSV
        logger.info("Saving citations CSV...")
        citation_extractor.save_to_csv(citations_df, citations_path)

        # Create and save metadata JSON
        logger.info("Saving metadata JSON...")
        metadata = {
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
        save_metadata_json(metadata, metadata_path)

        # Clean up raw files if not keeping
        if not args.keep_raw:
            logger.info("Cleaning up temporary files...")
            fetcher.cleanup(zip_path)
            fetcher.cleanup(extract_dir)
            logger.info("Cleanup complete")
        else:
            logger.info("Keeping raw files (--keep-raw flag set)")
            logger.info(f"  Zip file: {zip_path}")
            logger.info(f"  Extracted: {extract_dir}")

        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("SUCCESS: PEP metadata fetch complete")
        logger.info("=" * 60)
        logger.info(f"Total PEPs processed: {len(pep_metadata)}")
        logger.info(f"Total citations extracted: {len(citations_df)}")
        logger.info(f"PEP metadata CSV: {csv_path}")
        logger.info(f"Citations CSV: {citations_path}")
        logger.info(f"Metadata JSON: {metadata_path}")
        logger.info(f"Fetched at: {metadata['fetched_at']}")
        logger.info("=" * 60)

        return 0

    except Exception as e:
        logger.error(f"Failed to fetch and parse PEPs: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
