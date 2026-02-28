"""Fetch and parse PEP metadata from GitHub repository."""

import argparse
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
        Exit code:
        - 0: Success, no data changes
        - 1: Error occurred
        - 2: Success, data has changed
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
        # Set up paths
        project_root = Path(__file__).parent.parent
        raw_dir = project_root / "data" / "raw"
        output_dir = project_root / args.output_dir

        # Create directories
        raw_dir.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Fixed output filenames
        csv_path = output_dir / "peps_metadata.csv"
        citations_path = output_dir / "citations.csv"
        metadata_path = output_dir / "metadata.json"

        # ===== STEP 0: Load existing metadata (before fetching) =====
        from src.utils.metadata_manager import MetadataManager

        metadata_manager = MetadataManager()
        old_metadata = metadata_manager.load_metadata(metadata_path)

        # ===== STEP 1-4: Fetch and parse PEP data =====
        # Initialize components
        fetcher = PEPFetcher()
        parser = PEPParser()
        citation_extractor = CitationExtractor()

        # Generate timestamp for raw files
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        zip_path = raw_dir / f"peps_{timestamp}.zip"
        extract_dir = raw_dir / f"peps_extracted_{timestamp}"

        # Download PEP repository
        logger.info("Step 1/5: Downloading PEP repository...")
        fetcher.download_repo(PEP_REPO_URL, zip_path)
        logger.info(f"Downloaded to {zip_path}")

        # Extract zip file
        logger.info("Step 2/5: Extracting zip file...")
        fetcher.extract_zip(zip_path, extract_dir)
        logger.info(f"Extracted to {extract_dir}")

        # Find and parse PEP files
        logger.info("Step 3/5: Finding PEP files...")
        pep_dir = extract_dir / "peps-main" / "peps"

        if not pep_dir.exists():
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

        # Extract citations
        logger.info("Step 4/5: Extracting citations...")
        citations_df = citation_extractor.extract_from_multiple_files(pep_files)
        logger.info(f"Extracted {len(citations_df)} citation records")

        # Save CSVs (with sorting)
        logger.info("Step 5/5: Saving data...")
        parser.save_to_csv(pep_metadata, csv_path)
        citation_extractor.save_to_csv(citations_df, citations_path)

        # ===== STEP 6: Calculate hashes =====
        from src.utils.hash_utils import calculate_file_hash

        logger.info("Calculating file hashes...")
        new_hashes = {
            "peps_metadata": calculate_file_hash(csv_path),
            "citations": calculate_file_hash(citations_path),
        }
        logger.info(f"peps_metadata hash: {new_hashes['peps_metadata']}")
        logger.info(f"citations hash: {new_hashes['citations']}")

        # ===== STEP 7: Check if data changed =====
        data_changed = metadata_manager.has_data_changed(new_hashes, old_metadata)

        # ===== STEP 8: Update metadata =====
        if data_changed:
            logger.info("Data has changed. Updating fetched_at and data_hashes.")
            # 初期化（source_urlは保持）
            new_metadata = {
                "source_url": PEP_REPO_URL,
            }
            # fetched_atとchecked_atを更新
            new_metadata = metadata_manager.update_fetched_at(new_metadata)
            new_metadata = metadata_manager.update_checked_at(new_metadata)
            # data_hashesを更新
            new_metadata = metadata_manager.update_data_hashes(new_metadata, new_hashes)
        else:
            logger.info("No data changes. Updating checked_at only.")
            # checked_atだけ更新
            new_metadata = old_metadata.copy()
            new_metadata = metadata_manager.update_checked_at(new_metadata)

        # ===== STEP 9: Save metadata =====
        metadata_manager.save_metadata(new_metadata, metadata_path)

        # ===== STEP 10: Clean up raw files =====
        if not args.keep_raw:
            logger.info("Cleaning up temporary files...")
            fetcher.cleanup(zip_path)
            fetcher.cleanup(extract_dir)
            logger.info("Cleanup complete")
        else:
            logger.info("Keeping raw files (--keep-raw flag set)")

        # ===== Summary =====
        logger.info("\n" + "=" * 60)
        logger.info("SUCCESS: PEP metadata fetch complete")
        logger.info("=" * 60)
        logger.info(f"Total PEPs processed: {len(pep_metadata)}")
        logger.info(f"Total citations extracted: {len(citations_df)}")
        logger.info(f"Data changed: {data_changed}")
        logger.info(f"PEP metadata CSV: {csv_path}")
        logger.info(f"Citations CSV: {citations_path}")
        logger.info(f"Metadata JSON: {metadata_path}")
        logger.info("=" * 60)

        # ===== Return exit code =====
        if data_changed:
            logger.info("Exit code: 2 (data changed)")
            return 2
        else:
            logger.info("Exit code: 0 (no changes)")
            return 0

    except Exception as e:
        logger.error(f"Failed to fetch and parse PEPs: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
