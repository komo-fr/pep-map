"""Tests for GitHub fetcher module."""

import tempfile
import zipfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import requests

from src.data_acquisition.github_fetcher import PEPFetcher
from scripts.fetch_peps import PEP_REPO_URL


class TestPEPFetcher:
    """Test cases for PEPFetcher class."""

    @pytest.fixture
    def fetcher(self):
        """Create a PEPFetcher instance for testing."""
        return PEPFetcher()

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def sample_zip(self, temp_dir):
        """Create a sample zip file with mock PEP files."""
        # Create a temporary directory structure
        pep_dir = temp_dir / "peps-main" / "peps"
        pep_dir.mkdir(parents=True)

        # Create sample PEP files
        (pep_dir / "pep-0001.rst").write_text("PEP: 1\nTitle: Test PEP")
        (pep_dir / "pep-0008.rst").write_text("PEP: 8\nTitle: Style Guide")
        (pep_dir / "pep-0020.rst").write_text("PEP: 20\nTitle: Zen of Python")
        (pep_dir / "README.md").write_text("# README")  # Non-PEP file

        # Create zip file
        zip_path = temp_dir / "test.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            for file in pep_dir.rglob("*"):
                if file.is_file():
                    arcname = file.relative_to(temp_dir)
                    zf.write(file, arcname)

        return zip_path

    def test_download_peps_repo_success(self, fetcher, temp_dir):
        """Test successful download of PEP repository zip."""
        url = PEP_REPO_URL
        output_path = temp_dir / "peps.zip"

        # Mock the requests.get call
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"fake zip content"
        mock_response.raise_for_status = Mock()

        with patch("requests.get", return_value=mock_response) as mock_get:
            result = fetcher.download_repo(url, output_path)

            # Verify the download was called correctly
            mock_get.assert_called_once()
            assert mock_get.call_args[0][0] == url

            # Verify the file was created
            assert result == output_path
            assert output_path.exists()
            assert output_path.read_bytes() == b"fake zip content"

    def test_download_peps_repo_invalid_url(self, fetcher, temp_dir):
        """Test download with invalid URL raises error."""
        url = "https://invalid-url.example.com/nonexistent.zip"
        output_path = temp_dir / "peps.zip"

        # Mock requests.get to raise an exception
        with patch(
            "requests.get", side_effect=requests.RequestException("Connection error")
        ):
            with pytest.raises(requests.RequestException):
                fetcher.download_repo(url, output_path)

    def test_extract_zip_success(self, fetcher, sample_zip, temp_dir):
        """Test successful extraction of zip file."""
        extract_to = temp_dir / "extracted"

        result = fetcher.extract_zip(sample_zip, extract_to)

        # Verify extraction was successful
        assert result.exists()
        assert (result / "peps-main" / "peps" / "pep-0001.rst").exists()
        assert (result / "peps-main" / "peps" / "pep-0008.rst").exists()
        assert (result / "peps-main" / "peps" / "pep-0020.rst").exists()

    def test_extract_zip_invalid_file(self, fetcher, temp_dir):
        """Test extraction with invalid zip file raises error."""
        # Create a non-zip file
        invalid_zip = temp_dir / "invalid.zip"
        invalid_zip.write_text("This is not a zip file")

        extract_to = temp_dir / "extracted"

        with pytest.raises(zipfile.BadZipFile):
            fetcher.extract_zip(invalid_zip, extract_to)

    def test_get_pep_files(self, fetcher, sample_zip, temp_dir):
        """Test getting list of PEP files from extracted repository."""
        # Extract the sample zip
        extract_to = temp_dir / "extracted"
        fetcher.extract_zip(sample_zip, extract_to)

        # Get PEP files
        repo_path = extract_to / "peps-main" / "peps"
        pep_files = fetcher.get_pep_files(repo_path)

        # Verify we got the correct PEP files
        assert len(pep_files) == 3
        pep_numbers = {int(f.stem.split("-")[1]) for f in pep_files}
        assert pep_numbers == {1, 8, 20}

        # Verify all returned files exist and have .rst extension
        for pep_file in pep_files:
            assert pep_file.exists()
            assert pep_file.suffix == ".rst"
            assert pep_file.name.startswith("pep-")

    def test_get_pep_files_excludes_pep_0(self, fetcher, temp_dir):
        """Test that PEP 0 (table of contents) is excluded from the list."""
        # Create a directory with PEP files including PEP 0
        pep_dir = temp_dir / "peps"
        pep_dir.mkdir()

        (pep_dir / "pep-0000.rst").write_text("PEP: 0\nTitle: Index")
        (pep_dir / "pep-0001.rst").write_text("PEP: 1\nTitle: Test")

        pep_files = fetcher.get_pep_files(pep_dir)

        # Verify PEP 0 is excluded
        assert len(pep_files) == 1
        assert pep_files[0].name == "pep-0001.rst"

    def test_cleanup_temp_files(self, fetcher, temp_dir):
        """Test cleanup of temporary files and directories."""
        # Create some test files and directories
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")

        test_subdir = temp_dir / "subdir"
        test_subdir.mkdir()
        (test_subdir / "nested.txt").write_text("nested content")

        # Verify files exist before cleanup
        assert test_file.exists()
        assert test_subdir.exists()
        assert (test_subdir / "nested.txt").exists()

        # Clean up
        fetcher.cleanup(temp_dir)

        # Verify cleanup was successful
        assert not temp_dir.exists()

    def test_cleanup_nonexistent_path(self, fetcher, temp_dir):
        """Test cleanup with non-existent path doesn't raise error."""
        nonexistent = temp_dir / "nonexistent"

        # Should not raise an error
        fetcher.cleanup(nonexistent)

    def test_download_with_timeout(self, fetcher, temp_dir):
        """Test download with timeout setting."""
        url = PEP_REPO_URL
        output_path = temp_dir / "peps.zip"

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"content"
        mock_response.raise_for_status = Mock()

        with patch("requests.get", return_value=mock_response) as mock_get:
            fetcher.download_repo(url, output_path, timeout=30)

            # Verify timeout was passed
            assert "timeout" in mock_get.call_args[1]
            assert mock_get.call_args[1]["timeout"] == 30

    def test_extract_zip_prevents_path_traversal(self, fetcher, temp_dir):
        """Test that path traversal in zip files is blocked (Zip Slip protection)."""
        # Create a malicious zip file with path traversal attempts
        malicious_zip = temp_dir / "malicious.zip"
        extract_to = temp_dir / "extracted"

        with zipfile.ZipFile(malicious_zip, "w") as zf:
            # Try to write outside the extraction directory using relative paths
            zf.writestr("../../../etc/passwd", "malicious content")
            zf.writestr("normal.txt", "normal content")

        # Should raise ValueError when detecting path traversal
        with pytest.raises(ValueError, match="path traversal"):
            fetcher.extract_zip(malicious_zip, extract_to)

    def test_extract_zip_prevents_absolute_path(self, fetcher, temp_dir):
        """Test that absolute paths in zip files are blocked."""
        # Create a malicious zip file with absolute path
        malicious_zip = temp_dir / "malicious_absolute.zip"
        extract_to = temp_dir / "extracted"

        with zipfile.ZipFile(malicious_zip, "w") as zf:
            # Try to write to an absolute path
            zf.writestr("/tmp/malicious.txt", "malicious content")

        # Should raise ValueError when detecting path traversal
        with pytest.raises(ValueError, match="path traversal"):
            fetcher.extract_zip(malicious_zip, extract_to)

    def test_extract_zip_allows_safe_nested_paths(self, fetcher, temp_dir):
        """Test that safe nested paths within extraction directory are allowed."""
        # Create a zip file with safe nested paths
        safe_zip = temp_dir / "safe.zip"
        extract_to = temp_dir / "extracted"

        with zipfile.ZipFile(safe_zip, "w") as zf:
            # These should all be safe paths within the extraction directory
            zf.writestr("peps-main/peps/pep-0001.rst", "PEP content")
            zf.writestr("peps-main/peps/subfolder/file.txt", "nested content")
            zf.writestr("file.txt", "root file")

        # Should extract successfully without raising errors
        result = fetcher.extract_zip(safe_zip, extract_to)

        # Verify extraction was successful
        assert result.exists()
        assert (result / "peps-main" / "peps" / "pep-0001.rst").exists()
        assert (result / "peps-main" / "peps" / "subfolder" / "file.txt").exists()
        assert (result / "file.txt").exists()

    def test_extract_zip_prevents_symlink_path_traversal(self, fetcher, temp_dir):
        """Test that symlinks attempting path traversal are blocked."""
        # Note: This test may behave differently on different platforms
        # Some zip implementations normalize symlinks, others preserve them
        malicious_zip = temp_dir / "malicious_symlink.zip"
        extract_to = temp_dir / "extracted"

        with zipfile.ZipFile(malicious_zip, "w") as zf:
            # Try to create a file with a name that looks like a symlink traversal
            zf.writestr("link/../../../etc/passwd", "malicious content")

        # Should raise ValueError when detecting path traversal
        with pytest.raises(ValueError, match="path traversal"):
            fetcher.extract_zip(malicious_zip, extract_to)
