"""GitHub fetcher for downloading and extracting PEP repository."""

import logging
import shutil
import zipfile
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 60


class PEPFetcher:
    """Fetcher for downloading and extracting PEP files from GitHub."""

    def __init__(self):
        """Initialize PEPFetcher."""
        pass

    def download_repo(
        self, url: str, output_path: Path, timeout: int = DEFAULT_TIMEOUT
    ) -> Path:
        """
        Download PEP repository zip file from GitHub.

        Args:
            url: URL of the zip file to download
            output_path: Path where to save the downloaded zip file
            timeout: Timeout for the request in seconds (default: 60)

        Returns:
            Path to the downloaded zip file

        Raises:
            requests.RequestException: If download fails
        """
        logger.info(f"Downloading PEP repository from {url}")

        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()

            # Ensure parent directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Write content to file
            output_path.write_bytes(response.content)

            logger.info(f"Downloaded {len(response.content)} bytes to {output_path}")
            return output_path

        except requests.RequestException as e:
            logger.error(f"Failed to download from {url}: {e}")
            raise

    def extract_zip(self, zip_path: Path, extract_to: Path) -> Path:
        """
        Extract zip file to specified directory with path traversal protection.

        Args:
            zip_path: Path to the zip file
            extract_to: Directory where to extract the contents

        Returns:
            Path to the extraction directory

        Raises:
            zipfile.BadZipFile: If the file is not a valid zip file
            ValueError: If the zip file contains path traversal attempts (Zip Slip attack)
        """
        logger.info(f"Extracting {zip_path} to {extract_to}")

        try:
            # Ensure extraction directory exists
            extract_to.mkdir(parents=True, exist_ok=True)

            # Resolve the extraction directory to its absolute path
            extract_to_resolved = extract_to.resolve()

            # Validate all file paths before extraction (Zip Slip protection)
            with zipfile.ZipFile(zip_path, "r") as zf:
                for member in zf.namelist():
                    # Resolve the full path and check it's within extract_to
                    member_path = (extract_to / member).resolve()

                    # Check if the resolved path is within the extraction directory
                    # Use os.sep to ensure proper path separator handling
                    try:
                        member_path.relative_to(extract_to_resolved)
                    except ValueError:
                        # relative_to() raises ValueError if member_path is not relative to extract_to_resolved
                        logger.error(f"Path traversal attempt detected: {member}")
                        raise ValueError(
                            f"Attempted path traversal in zip file: {member}"
                        )

                # If all paths are safe, extract
                zf.extractall(extract_to)

            logger.info(f"Successfully extracted to {extract_to}")
            return extract_to

        except zipfile.BadZipFile as e:
            logger.error(f"Invalid zip file {zip_path}: {e}")
            raise

    def get_pep_files(self, repo_path: Path) -> list[Path]:
        """
        Get list of PEP RST files from the repository directory.

        Args:
            repo_path: Path to the directory containing PEP files

        Returns:
            List of paths to PEP RST files (excluding PEP 0)

        Note:
            PEP 0 is excluded as it's the table of contents, not an actual PEP.
        """
        logger.info(f"Searching for PEP files in {repo_path}")

        # Find all pep-*.rst files
        pep_files = []
        for file_path in repo_path.glob("pep-*.rst"):
            # Extract PEP number from filename (e.g., pep-0001.rst -> 1)
            try:
                pep_number = int(file_path.stem.split("-")[1])
                # Exclude PEP 0 (table of contents)
                if pep_number != 0:
                    pep_files.append(file_path)
            except (IndexError, ValueError):
                logger.warning(f"Skipping file with invalid name: {file_path}")
                continue

        # Sort by PEP number
        pep_files.sort(key=lambda p: int(p.stem.split("-")[1]))

        logger.info(f"Found {len(pep_files)} PEP files")
        return pep_files

    def cleanup(self, path: Path) -> None:
        """
        Remove temporary files and directories.

        Args:
            path: Path to the file or directory to remove

        Note:
            If the path doesn't exist, this method does nothing.
        """
        if not path.exists():
            logger.debug(f"Path {path} does not exist, nothing to clean up")
            return

        try:
            if path.is_file():
                path.unlink()
                logger.info(f"Removed file: {path}")
            elif path.is_dir():
                shutil.rmtree(path)
                logger.info(f"Removed directory: {path}")
        except Exception as e:
            logger.error(f"Failed to clean up {path}: {e}")
            raise
