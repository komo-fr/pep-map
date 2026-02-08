"""Manual test script for GitHub fetcher."""

import logging
from datetime import datetime
from pathlib import Path

from src.data_acquisition.github_fetcher import PEPFetcher

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Test downloading and extracting PEP repository."""
    # Initialize fetcher
    fetcher = PEPFetcher()

    # Set up paths
    project_root = Path(__file__).parent.parent
    raw_dir = project_root / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Generate timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_path = raw_dir / f"peps_{timestamp}.zip"
    extract_dir = raw_dir / f"peps_extracted_{timestamp}"

    try:
        # Download PEP repository
        logger.info("Starting PEP repository download...")
        url = "https://github.com/python/peps/archive/refs/heads/main.zip"
        fetcher.download_repo(url, zip_path)
        logger.info(f"Download complete: {zip_path}")

        # Extract zip file
        logger.info("Extracting zip file...")
        fetcher.extract_zip(zip_path, extract_dir)
        logger.info(f"Extraction complete: {extract_dir}")

        # Find PEP files
        logger.info("Finding PEP files...")
        # The extracted directory structure is typically: peps-main/peps/
        pep_dir = extract_dir / "peps-main" / "peps"

        if not pep_dir.exists():
            # Try alternative structure
            possible_dirs = list(extract_dir.glob("*/peps"))
            if possible_dirs:
                pep_dir = possible_dirs[0]
                logger.info(f"Found PEP directory: {pep_dir}")
            else:
                logger.error(f"Could not find peps directory in {extract_dir}")
                return

        pep_files = fetcher.get_pep_files(pep_dir)
        logger.info(f"Found {len(pep_files)} PEP files")

        # Show first 10 PEP files as sample
        logger.info("Sample PEP files:")
        for pep_file in pep_files[:10]:
            logger.info(f"  - {pep_file.name}")

        if len(pep_files) > 10:
            logger.info(f"  ... and {len(pep_files) - 10} more files")

        logger.info("\nTest completed successfully!")
        logger.info(f"Downloaded zip: {zip_path}")
        logger.info(f"Extracted to: {extract_dir}")
        logger.info(f"Total PEP files: {len(pep_files)}")

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
