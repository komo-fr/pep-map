"""Tests for hash utility functions."""

import hashlib

import pytest

from src.utils.hash_utils import calculate_file_hash


class TestHashUtils:
    """Test cases for hash utility functions."""

    def test_calculate_file_hash_same_content(self, tmp_path):
        """Test that same content produces same hash."""
        # 同じ内容のファイルを2つ作成
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"

        content = "test content\n"
        file1.write_text(content, encoding="utf-8")
        file2.write_text(content, encoding="utf-8")

        hash1 = calculate_file_hash(file1)
        hash2 = calculate_file_hash(file2)

        assert hash1 == hash2
        # SHA256ハッシュは64文字の16進数文字列
        assert len(hash1) == 64
        assert all(c in "0123456789abcdef" for c in hash1)

    def test_calculate_file_hash_different_content(self, tmp_path):
        """Test that different content produces different hash."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"

        file1.write_text("content A\n", encoding="utf-8")
        file2.write_text("content B\n", encoding="utf-8")

        hash1 = calculate_file_hash(file1)
        hash2 = calculate_file_hash(file2)

        assert hash1 != hash2

    def test_calculate_file_hash_one_byte_difference(self, tmp_path):
        """Test that even 1 byte difference produces different hash."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"

        file1.write_text("test", encoding="utf-8")
        file2.write_text("tesx", encoding="utf-8")  # 1文字だけ違う

        hash1 = calculate_file_hash(file1)
        hash2 = calculate_file_hash(file2)

        assert hash1 != hash2

    def test_calculate_file_hash_empty_file(self, tmp_path):
        """Test that empty file can be hashed."""
        file = tmp_path / "empty.txt"
        file.write_text("", encoding="utf-8")

        hash_value = calculate_file_hash(file)

        # 空ファイルのSHA256ハッシュは既知の値
        expected = hashlib.sha256(b"").hexdigest()
        assert hash_value == expected

    def test_calculate_file_hash_csv_file(self, tmp_path):
        """Test that CSV file can be hashed."""
        csv_file = tmp_path / "test.csv"
        csv_content = "pep_number,title\n1,Test PEP\n8,Style Guide\n"
        csv_file.write_text(csv_content, encoding="utf-8")

        hash_value = calculate_file_hash(csv_file)

        assert len(hash_value) == 64

        # 同じ内容なら同じハッシュ
        csv_file2 = tmp_path / "test2.csv"
        csv_file2.write_text(csv_content, encoding="utf-8")
        hash_value2 = calculate_file_hash(csv_file2)

        assert hash_value == hash_value2

    def test_calculate_file_hash_file_not_found(self, tmp_path):
        """Test that FileNotFoundError is raised for non-existent file."""
        file = tmp_path / "nonexistent.txt"

        with pytest.raises(FileNotFoundError):
            calculate_file_hash(file)
