"""Metadata management for PEP data updates."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


class MetadataManager:
    """Manage metadata.json for tracking data updates."""

    def load_metadata(self, path: Path) -> dict:
        """
        Load metadata from JSON file.

        Args:
            path: Path to metadata.json

        Returns:
            Metadata dictionary. Returns empty dict if file doesn't exist.
        """
        if not path.exists():
            logger.info(f"Metadata file not found: {path}. Returning empty dict.")
            return {}

        with open(path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        logger.info(f"Loaded metadata from {path}")
        return metadata

    def save_metadata(self, metadata: dict, path: Path) -> None:
        """
        Save metadata to JSON file.

        Args:
            metadata: Metadata dictionary to save
            path: Path to metadata.json
        """
        # ディレクトリが存在しない場合は作成
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
            f.write("\n")  # 末尾改行を追加

        logger.info(f"Saved metadata to {path}")

    def update_checked_at(self, metadata: dict) -> dict:
        """
        Update checked_at timestamp to current time.

        Args:
            metadata: Original metadata dictionary

        Returns:
            New metadata dictionary with updated checked_at (immutable)
        """
        new_metadata = metadata.copy()
        new_metadata["checked_at"] = datetime.now(timezone.utc).isoformat()
        return new_metadata

    def update_fetched_at(self, metadata: dict) -> dict:
        """
        Update fetched_at timestamp to current time.

        Args:
            metadata: Original metadata dictionary

        Returns:
            New metadata dictionary with updated fetched_at (immutable)
        """
        new_metadata = metadata.copy()
        new_metadata["fetched_at"] = datetime.now(timezone.utc).isoformat()
        return new_metadata

    def update_data_hashes(self, metadata: dict, hashes: dict) -> dict:
        """
        Update data_hashes in metadata.

        Args:
            metadata: Original metadata dictionary
            hashes: New hash values (e.g., {"peps_metadata": "abc123", "citations": "def456"})

        Returns:
            New metadata dictionary with updated data_hashes (immutable)
        """
        new_metadata = metadata.copy()
        new_metadata["data_hashes"] = hashes
        return new_metadata

    def has_data_changed(self, new_hashes: dict, old_metadata: dict) -> bool:
        """
        Check if data has changed by comparing hashes.

        Args:
            new_hashes: New hash values
            old_metadata: Previous metadata dictionary

        Returns:
            True if data has changed, False otherwise.
            Returns True if no previous hashes exist (first run).
        """
        # 初回実行（data_hashesが存在しない）
        if "data_hashes" not in old_metadata:
            logger.info(
                "No previous hashes found. Treating as first run (data changed)."
            )
            return True

        old_hashes = old_metadata["data_hashes"]

        # ハッシュ値を比較
        for key in new_hashes:
            if key not in old_hashes:
                logger.info(f"New hash key '{key}' not in old hashes. Data changed.")
                return True

            if new_hashes[key] != old_hashes[key]:
                logger.info(f"Hash mismatch for '{key}'. Data changed.")
                logger.debug(f"  Old: {old_hashes[key]}")
                logger.debug(f"  New: {new_hashes[key]}")
                return True

        logger.info("All hashes match. No data changes detected.")
        return False
