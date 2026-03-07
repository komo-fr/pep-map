"""Tests for citation change detector module."""

import pandas as pd
from pandas.testing import assert_frame_equal
import pytest

from src.utils.citation_change_detector import CitationChangeDetector


class TestCitationChangeDetectorDetectChanges:
    """Test cases for CitationChangeDetector.detect_changes() method."""

    @pytest.fixture
    def detector(self):
        """Create a CitationChangeDetector instance for testing."""
        return CitationChangeDetector()

    def test_detect_added_citations(self, detector):
        """Test detection of newly added citations."""
        # Arrange
        old_df = pd.DataFrame(
            {
                "citing": [1],
                "cited": [8],
                "count": [1],
            }
        )
        new_df = pd.DataFrame(
            {
                "citing": [1, 1],
                "cited": [8, 10],
                "count": [1, 2],
            }
        )

        # Act
        changes = detector.detect_changes(old_df, new_df)

        # Assert
        assert len(changes) == 1
        assert changes[0]["change_type"] == "Added"
        assert changes[0]["citing"] == 1
        assert changes[0]["cited"] == 10
        assert changes[0]["count_before"] is None
        assert changes[0]["count_after"] == 2

    def test_detect_deleted_citations(self, detector):
        """Test detection of deleted citations."""
        # Arrange
        old_df = pd.DataFrame(
            {
                "citing": [1, 1],
                "cited": [8, 10],
                "count": [1, 2],
            }
        )
        new_df = pd.DataFrame(
            {
                "citing": [1],
                "cited": [8],
                "count": [1],
            }
        )

        # Act
        changes = detector.detect_changes(old_df, new_df)

        # Assert
        assert len(changes) == 1
        assert changes[0]["change_type"] == "Deleted"
        assert changes[0]["citing"] == 1
        assert changes[0]["cited"] == 10
        assert changes[0]["count_before"] == 2
        assert changes[0]["count_after"] is None

    def test_detect_changed_count(self, detector):
        """Test detection of changed citation counts."""
        # Arrange
        old_df = pd.DataFrame(
            {
                "citing": [1],
                "cited": [8],
                "count": [1],
            }
        )
        new_df = pd.DataFrame(
            {
                "citing": [1],
                "cited": [8],
                "count": [3],
            }
        )

        # Act
        changes = detector.detect_changes(old_df, new_df)

        # Assert
        assert len(changes) == 1
        assert changes[0]["change_type"] == "Changed"
        assert changes[0]["citing"] == 1
        assert changes[0]["cited"] == 8
        assert changes[0]["count_before"] == 1
        assert changes[0]["count_after"] == 3

    def test_detect_multiple_changes(self, detector):
        """Test detection of multiple types of changes simultaneously."""
        # Arrange
        old_df = pd.DataFrame(
            {
                "citing": [1, 2],
                "cited": [8, 3],
                "count": [1, 2],
            }
        )
        new_df = pd.DataFrame(
            {
                "citing": [1, 1],
                "cited": [8, 10],
                "count": [3, 1],
            }
        )

        # Act
        changes = detector.detect_changes(old_df, new_df)

        # Assert
        assert len(changes) == 3

        # Find each change type
        changed = [c for c in changes if c["change_type"] == "Changed"]
        added = [c for c in changes if c["change_type"] == "Added"]
        deleted = [c for c in changes if c["change_type"] == "Deleted"]

        # Verify Changed
        assert len(changed) == 1
        assert changed[0]["citing"] == 1
        assert changed[0]["cited"] == 8
        assert changed[0]["count_before"] == 1
        assert changed[0]["count_after"] == 3

        # Verify Added
        assert len(added) == 1
        assert added[0]["citing"] == 1
        assert added[0]["cited"] == 10
        assert added[0]["count_before"] is None
        assert added[0]["count_after"] == 1

        # Verify Deleted
        assert len(deleted) == 1
        assert deleted[0]["citing"] == 2
        assert deleted[0]["cited"] == 3
        assert deleted[0]["count_before"] == 2
        assert deleted[0]["count_after"] is None

    def test_detect_no_changes(self, detector):
        """Test that no changes are detected when DataFrames are identical."""
        # Arrange
        old_df = pd.DataFrame(
            {
                "citing": [1, 2],
                "cited": [8, 3],
                "count": [1, 2],
            }
        )
        new_df = pd.DataFrame(
            {
                "citing": [1, 2],
                "cited": [8, 3],
                "count": [1, 2],
            }
        )

        # Act
        changes = detector.detect_changes(old_df, new_df)

        # Assert
        assert len(changes) == 0
        assert changes == []

    def test_detect_empty_old_dataframe(self, detector):
        """Test detection when old DataFrame is empty."""
        # Arrange
        old_df = pd.DataFrame(columns=["citing", "cited", "count"])
        new_df = pd.DataFrame(
            {
                "citing": [1],
                "cited": [8],
                "count": [1],
            }
        )

        # Act
        changes = detector.detect_changes(old_df, new_df)

        # Assert
        assert len(changes) == 1
        assert changes[0]["change_type"] == "Added"
        assert changes[0]["citing"] == 1
        assert changes[0]["cited"] == 8
        assert changes[0]["count_before"] is None
        assert changes[0]["count_after"] == 1

    def test_detect_empty_new_dataframe(self, detector):
        """Test detection when new DataFrame is empty."""
        # Arrange
        old_df = pd.DataFrame(
            {
                "citing": [1],
                "cited": [8],
                "count": [1],
            }
        )
        new_df = pd.DataFrame(columns=["citing", "cited", "count"])

        # Act
        changes = detector.detect_changes(old_df, new_df)

        # Assert
        assert len(changes) == 1
        assert changes[0]["change_type"] == "Deleted"
        assert changes[0]["citing"] == 1
        assert changes[0]["cited"] == 8
        assert changes[0]["count_before"] == 1
        assert changes[0]["count_after"] is None

    def test_detect_both_empty(self, detector):
        """Test detection when both DataFrames are empty."""
        # Arrange
        old_df = pd.DataFrame(columns=["citing", "cited", "count"])
        new_df = pd.DataFrame(columns=["citing", "cited", "count"])

        # Act
        changes = detector.detect_changes(old_df, new_df)

        # Assert
        assert len(changes) == 0
        assert changes == []


class TestCitationChangeDetectorCreateChangelogEntry:
    """Test cases for CitationChangeDetector.create_changelog_entry() method."""

    @pytest.fixture
    def detector(self):
        """Create a CitationChangeDetector instance for testing."""
        return CitationChangeDetector()

    def test_create_changelog_entry_with_detected_at(self, detector):
        """Test that detected_at is correctly set in all entries."""
        # Arrange
        changes = [
            {
                "change_type": "Added",
                "citing": 1,
                "cited": 10,
                "count_before": None,
                "count_after": 2,
            },
            {
                "change_type": "Changed",
                "citing": 1,
                "cited": 8,
                "count_before": 1,
                "count_after": 3,
            },
        ]
        detected_at = "2026-03-01T12:00:00+00:00"

        # Act
        changelog_df = detector.create_changelog_entry(changes, detected_at)

        # Assert
        assert len(changelog_df) == 2
        assert all(changelog_df["detected_at"] == detected_at)
        assert changelog_df.iloc[0]["detected_at"] == detected_at
        assert changelog_df.iloc[1]["detected_at"] == detected_at

    def test_create_changelog_entry_columns(self, detector):
        """Test that columns are in the correct order."""
        # Arrange
        changes = [
            {
                "change_type": "Added",
                "citing": 1,
                "cited": 10,
                "count_before": None,
                "count_after": 2,
            }
        ]
        detected_at = "2026-03-01T12:00:00+00:00"

        # Act
        changelog_df = detector.create_changelog_entry(changes, detected_at)

        # Assert
        expected_columns = [
            "detected_at",
            "change_type",
            "citing",
            "cited",
            "count_before",
            "count_after",
        ]
        assert list(changelog_df.columns) == expected_columns

    def test_create_changelog_entry_dtypes(self, detector):
        """Test that data types are correct."""
        # Arrange
        changes = [
            {
                "change_type": "Added",
                "citing": 1,
                "cited": 10,
                "count_before": None,
                "count_after": 2,
            },
            {
                "change_type": "Changed",
                "citing": 2,
                "cited": 3,
                "count_before": 1,
                "count_after": 4,
            },
            {
                "change_type": "Deleted",
                "citing": 3,
                "cited": 5,
                "count_before": 1,
                "count_after": None,
            },
        ]
        detected_at = "2026-03-01T12:00:00+00:00"

        # Act
        changelog_df = detector.create_changelog_entry(changes, detected_at)

        # Assert
        # detected_at should be string
        assert pd.api.types.is_string_dtype(changelog_df["detected_at"])

        # change_type should be string
        assert pd.api.types.is_string_dtype(changelog_df["change_type"])

        # citing and cited should be int
        assert changelog_df["citing"].dtype == "int64"
        assert changelog_df["cited"].dtype == "int64"

        # count_before and count_after should be nullable integer (Int64)
        assert changelog_df["count_before"].dtype == pd.Int64Dtype()
        assert changelog_df["count_after"].dtype == pd.Int64Dtype()

        # Verify None values are properly represented as pd.NA
        assert pd.isna(changelog_df.iloc[0]["count_before"])
        assert pd.notna(changelog_df.iloc[1]["count_before"])
        assert pd.notna(changelog_df.iloc[2]["count_before"])
        assert pd.isna(changelog_df.iloc[2]["count_after"])


class TestCitationChangeDetectorAppendToChangelog:
    """Test cases for CitationChangeDetector.append_to_changelog() method."""

    @pytest.fixture
    def detector(self):
        """Create a CitationChangeDetector instance for testing."""
        return CitationChangeDetector()

    def test_append_to_new_file(self, detector, tmp_path):
        """Test appending to a new file includes header."""
        # Arrange
        changelog_path = tmp_path / "citation_changes.csv"
        changelog_df = pd.DataFrame(
            {
                "detected_at": ["2026-03-01T12:00:00+00:00"],
                "change_type": ["Added"],
                "citing": [1],
                "cited": [10],
                "count_before": pd.array([None], dtype=pd.Int64Dtype()),
                "count_after": pd.array([2], dtype=pd.Int64Dtype()),
            }
        )

        # Act
        detector.append_to_changelog(changelog_df, changelog_path)

        # Assert
        assert changelog_path.exists()

        # Read the file and verify content
        result_df = pd.read_csv(changelog_path)
        assert len(result_df) == 1
        assert list(result_df.columns) == [
            "detected_at",
            "change_type",
            "citing",
            "cited",
            "count_before",
            "count_after",
        ]
        assert result_df.iloc[0]["change_type"] == "Added"
        assert result_df.iloc[0]["citing"] == 1
        assert result_df.iloc[0]["cited"] == 10

    def test_append_to_existing_file(self, detector, tmp_path):
        """Test appending to an existing file."""
        # Arrange
        changelog_path = tmp_path / "citation_changes.csv"

        # Create existing file with initial data
        existing_df = pd.DataFrame(
            {
                "detected_at": ["2026-03-01T10:00:00+00:00"],
                "change_type": ["Added"],
                "citing": [1],
                "cited": [8],
                "count_before": pd.array([None], dtype=pd.Int64Dtype()),
                "count_after": pd.array([1], dtype=pd.Int64Dtype()),
            }
        )
        existing_df.to_csv(changelog_path, index=False)

        # New data to append
        new_df = pd.DataFrame(
            {
                "detected_at": ["2026-03-01T12:00:00+00:00"],
                "change_type": ["Changed"],
                "citing": [2],
                "cited": [3],
                "count_before": pd.array([1], dtype=pd.Int64Dtype()),
                "count_after": pd.array([2], dtype=pd.Int64Dtype()),
            }
        )

        # Act
        detector.append_to_changelog(new_df, changelog_path)

        # Assert
        result_df = pd.read_csv(changelog_path)
        assert len(result_df) == 2

        # Verify first row (existing data)
        assert result_df.iloc[0]["change_type"] == "Added"
        assert result_df.iloc[0]["citing"] == 1
        assert result_df.iloc[0]["cited"] == 8

        # Verify second row (new data)
        assert result_df.iloc[1]["change_type"] == "Changed"
        assert result_df.iloc[1]["citing"] == 2
        assert result_df.iloc[1]["cited"] == 3

    def test_append_empty_changes(self, detector, tmp_path):
        """Test that appending empty DataFrame does nothing."""
        # Arrange
        changelog_path = tmp_path / "citation_changes.csv"
        empty_df = pd.DataFrame(
            columns=[
                "detected_at",
                "change_type",
                "citing",
                "cited",
                "count_before",
                "count_after",
            ]
        )

        # Act
        detector.append_to_changelog(empty_df, changelog_path)

        # Assert
        # File should not be created
        assert not changelog_path.exists()

    def test_append_preserves_existing_data(self, detector, tmp_path):
        """Test that appending preserves all existing data using pandas.testing."""
        # Arrange
        changelog_path = tmp_path / "citation_changes.csv"

        # Create existing file with multiple rows
        existing_df = pd.DataFrame(
            {
                "detected_at": [
                    "2026-03-01T10:00:00+00:00",
                    "2026-03-01T11:00:00+00:00",
                ],
                "change_type": ["Added", "Deleted"],
                "citing": [1, 2],
                "cited": [8, 9],
                "count_before": pd.array([None, 1], dtype=pd.Int64Dtype()),
                "count_after": pd.array([1, None], dtype=pd.Int64Dtype()),
            }
        )
        existing_df.to_csv(changelog_path, index=False)

        # New data to append
        new_df = pd.DataFrame(
            {
                "detected_at": ["2026-03-01T12:00:00+00:00"],
                "change_type": ["Changed"],
                "citing": [3],
                "cited": [4],
                "count_before": pd.array([2], dtype=pd.Int64Dtype()),
                "count_after": pd.array([5], dtype=pd.Int64Dtype()),
            }
        )

        # Act
        detector.append_to_changelog(new_df, changelog_path)

        # Assert
        result_df = pd.read_csv(changelog_path)

        # Read the existing data portion
        existing_portion = result_df.iloc[:2].reset_index(drop=True)

        # Convert dtypes for comparison (CSV reads as float for nullable columns)
        existing_df_compare = existing_df.copy()
        existing_df_compare["count_before"] = existing_df_compare[
            "count_before"
        ].astype(float)
        existing_df_compare["count_after"] = existing_df_compare["count_after"].astype(
            float
        )

        # Use assert_frame_equal to compare
        assert_frame_equal(
            existing_portion,
            existing_df_compare,
            check_dtype=False,  # Ignore dtype differences
        )
