"""Tests for metadata manager module."""

import json
from datetime import datetime

import pytest

from src.utils.metadata_manager import MetadataManager


class TestMetadataManager:
    """Test cases for MetadataManager class."""

    @pytest.fixture
    def manager(self):
        """Create a MetadataManager instance for testing."""
        return MetadataManager()

    @pytest.fixture
    def sample_metadata(self):
        """Create sample metadata for testing."""
        return {
            "fetched_at": "2026-02-14T15:25:50.027772+00:00",
            "checked_at": "2026-02-20T10:00:00.000000+00:00",
            "source_url": "https://github.com/python/peps/archive/refs/heads/main.zip",
            "data_hashes": {
                "peps_metadata": "abc123",
                "citations": "def456",
            },
        }

    def test_load_metadata_existing_file(self, manager, tmp_path, sample_metadata):
        """Test loading existing metadata.json."""
        metadata_path = tmp_path / "metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(sample_metadata, f)

        loaded = manager.load_metadata(metadata_path)

        assert loaded == sample_metadata
        assert loaded["fetched_at"] == "2026-02-14T15:25:50.027772+00:00"
        assert loaded["data_hashes"]["peps_metadata"] == "abc123"

    def test_load_metadata_file_not_found(self, manager, tmp_path):
        """Test loading metadata when file doesn't exist."""
        metadata_path = tmp_path / "nonexistent.json"

        loaded = manager.load_metadata(metadata_path)

        # 空の辞書を返す
        assert loaded == {}

    def test_save_metadata(self, manager, tmp_path, sample_metadata):
        """Test saving metadata to JSON file."""
        metadata_path = tmp_path / "metadata.json"

        manager.save_metadata(sample_metadata, metadata_path)

        # ファイルが作成されたか確認
        assert metadata_path.exists()

        # 内容を確認
        with open(metadata_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)

        assert loaded == sample_metadata
        assert "fetched_at" in loaded
        assert "checked_at" in loaded
        assert "data_hashes" in loaded

    def test_has_data_changed_hashes_match(self, manager, sample_metadata):
        """Test has_data_changed returns False when hashes match."""
        new_hashes = {
            "peps_metadata": "abc123",
            "citations": "def456",
        }

        result = manager.has_data_changed(new_hashes, sample_metadata)

        assert result is False

    def test_has_data_changed_hashes_differ(self, manager, sample_metadata):
        """Test has_data_changed returns True when hashes differ."""
        new_hashes = {
            "peps_metadata": "different_hash",
            "citations": "def456",
        }

        result = manager.has_data_changed(new_hashes, sample_metadata)

        assert result is True

    def test_has_data_changed_no_previous_hashes(self, manager):
        """Test has_data_changed returns True when no previous hashes exist (first run)."""
        new_hashes = {
            "peps_metadata": "abc123",
            "citations": "def456",
        }
        old_metadata = {}  # 初回実行

        result = manager.has_data_changed(new_hashes, old_metadata)

        assert result is True

    def test_update_checked_at_immutable(self, manager, sample_metadata):
        """Test that update_checked_at doesn't modify original metadata."""
        original = sample_metadata.copy()
        original_checked_at = original["checked_at"]

        updated = manager.update_checked_at(sample_metadata)

        # 元のmetadataは変更されていない
        assert sample_metadata["checked_at"] == original_checked_at

        # 新しいmetadataが返される
        assert updated is not sample_metadata
        assert updated["checked_at"] != original_checked_at

        # checked_at以外は同じ
        assert updated["fetched_at"] == sample_metadata["fetched_at"]
        assert updated["source_url"] == sample_metadata["source_url"]

    def test_update_fetched_at_immutable(self, manager, sample_metadata):
        """Test that update_fetched_at doesn't modify original metadata."""
        original_fetched_at = sample_metadata["fetched_at"]

        updated = manager.update_fetched_at(sample_metadata)

        # 元のmetadataは変更されていない
        assert sample_metadata["fetched_at"] == original_fetched_at

        # 新しいmetadataが返される
        assert updated is not sample_metadata
        assert updated["fetched_at"] != original_fetched_at

        # fetched_at以外は同じ
        assert updated["checked_at"] == sample_metadata["checked_at"]
        assert updated["source_url"] == sample_metadata["source_url"]

    def test_update_data_hashes_immutable(self, manager, sample_metadata):
        """Test that update_data_hashes doesn't modify original metadata."""
        original_hashes = sample_metadata["data_hashes"].copy()
        new_hashes = {
            "peps_metadata": "new_hash_1",
            "citations": "new_hash_2",
        }

        updated = manager.update_data_hashes(sample_metadata, new_hashes)

        # 元のmetadataは変更されていない
        assert sample_metadata["data_hashes"] == original_hashes

        # 新しいmetadataが返される
        assert updated is not sample_metadata
        assert updated["data_hashes"] == new_hashes

        # data_hashes以外は同じ
        assert updated["fetched_at"] == sample_metadata["fetched_at"]
        assert updated["checked_at"] == sample_metadata["checked_at"]

    def test_update_checked_at_timestamp_format(self, manager, sample_metadata):
        """Test that update_checked_at uses correct ISO format timestamp."""
        updated = manager.update_checked_at(sample_metadata)

        # ISO 8601形式であることを確認
        checked_at = updated["checked_at"]
        # パースできることを確認
        dt = datetime.fromisoformat(checked_at.replace("+00:00", "+00:00"))
        assert dt.tzinfo is not None  # タイムゾーン情報がある
