"""Citation change detection for tracking PEP citation updates."""

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


class CitationChangeDetector:
    """Detect and track changes in PEP citation relationships."""

    # Changelog DataFrame columns
    CHANGELOG_COLUMNS = [
        "detected_at",
        "change_type",
        "citing",
        "cited",
        "count_before",
        "count_after",
    ]

    def detect_changes(self, old_df: pd.DataFrame, new_df: pd.DataFrame) -> list[dict]:
        """
        Detect changes between old and new citation DataFrames.

        Args:
            old_df: Old citations DataFrame with columns [citing, cited, count]
            new_df: New citations DataFrame with columns [citing, cited, count]

        Returns:
            List of change dictionaries with keys:
            - change_type: "Added" | "Deleted" | "Changed"
            - citing: PEP number that is citing
            - cited: PEP number that is cited
            - count_before: Count before change (None for Added)
            - count_after: Count after change (None for Deleted)
        """
        changes = []

        # Merge with indicator to detect additions/deletions
        merged = pd.merge(
            old_df,
            new_df,
            on=["citing", "cited"],
            how="outer",
            suffixes=("_before", "_after"),
            indicator=True,
        )

        # Added: only in new DataFrame
        added = merged[merged["_merge"] == "right_only"]
        for _, row in added.iterrows():
            changes.append(
                {
                    "change_type": "Added",
                    "citing": int(row["citing"]),
                    "cited": int(row["cited"]),
                    "count_before": None,
                    "count_after": int(row["count_after"]),
                }
            )

        # Deleted: only in old DataFrame
        deleted = merged[merged["_merge"] == "left_only"]
        for _, row in deleted.iterrows():
            changes.append(
                {
                    "change_type": "Deleted",
                    "citing": int(row["citing"]),
                    "cited": int(row["cited"]),
                    "count_before": int(row["count_before"]),
                    "count_after": None,
                }
            )

        # Changed: in both but count differs
        both = merged[merged["_merge"] == "both"]
        changed = both[both["count_before"] != both["count_after"]]
        for _, row in changed.iterrows():
            changes.append(
                {
                    "change_type": "Changed",
                    "citing": int(row["citing"]),
                    "cited": int(row["cited"]),
                    "count_before": int(row["count_before"]),
                    "count_after": int(row["count_after"]),
                }
            )

        logger.info(f"Detected {len(changes)} citation changes")
        return changes

    def create_changelog_entry(
        self, changes: list[dict], detected_at: str
    ) -> pd.DataFrame:
        """
        Convert change list to changelog DataFrame.

        Args:
            changes: List of change dictionaries from detect_changes()
            detected_at: Detection timestamp (ISO 8601 format)

        Returns:
            Changelog DataFrame with columns:
            [detected_at, change_type, citing, cited, count_before, count_after]
        """
        # Handle empty changes list
        if not changes:
            # Return empty DataFrame with correct structure
            return pd.DataFrame(columns=self.CHANGELOG_COLUMNS)

        # Create DataFrame from changes list
        df = pd.DataFrame(changes)

        # Add detected_at column
        df["detected_at"] = detected_at

        # Reorder columns
        df = df[self.CHANGELOG_COLUMNS]

        # Convert count columns to nullable integer type
        df["count_before"] = df["count_before"].astype(pd.Int64Dtype())
        df["count_after"] = df["count_after"].astype(pd.Int64Dtype())

        logger.info(f"Created changelog entry with {len(df)} records")
        return df

    def append_to_changelog(
        self, changelog_df: pd.DataFrame, changelog_path: Path
    ) -> None:
        """
        Append changelog DataFrame to CSV file.

        Args:
            changelog_df: Changelog DataFrame to append
            changelog_path: Path to citation_changes.csv
        """
        # Skip if DataFrame is empty
        if len(changelog_df) == 0:
            logger.info("No changes to append to changelog")
            return

        # Create parent directory if it doesn't exist
        changelog_path.parent.mkdir(parents=True, exist_ok=True)

        # Check if file exists
        file_exists = changelog_path.exists()

        if file_exists:
            # Append without header
            changelog_df.to_csv(changelog_path, mode="a", header=False, index=False)
            logger.info(f"Appended {len(changelog_df)} records to {changelog_path}")
        else:
            # Create new file with header
            changelog_df.to_csv(changelog_path, index=False)
            logger.info(
                f"Created new changelog file with {len(changelog_df)} records at {changelog_path}"
            )

    def load_old_citations(self, citations_path: Path) -> pd.DataFrame | None:
        """
        Load existing citations.csv file.

        Args:
            citations_path: Path to citations.csv

        Returns:
            DataFrame with columns [citing, cited, count], or None if file doesn't exist
        """
        # Check if file exists
        if not citations_path.exists():
            logger.info(f"Citations file not found: {citations_path}")
            return None

        try:
            # Load CSV file
            df = pd.read_csv(citations_path)

            # Validate required columns
            required_columns = {"citing", "cited", "count"}
            if not required_columns.issubset(df.columns):
                logger.error(
                    f"Unexpected columns in {citations_path}: {df.columns.tolist()}. "
                    f"Expected columns: {sorted(required_columns)}"
                )
                return None

            logger.info(f"Loaded {len(df)} citations from {citations_path}")
            return df
        except Exception as e:
            logger.error(f"Failed to load citations from {citations_path}: {e}")
            return None
