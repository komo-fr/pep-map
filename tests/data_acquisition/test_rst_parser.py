"""Tests for RST parser module."""

from pathlib import Path

import pytest

from src.data_acquisition.rst_parser import PEPMetadata, RSTParser


class TestRSTParser:
    """Test cases for RSTParser class."""

    @pytest.fixture
    def parser(self):
        """Create an RSTParser instance for testing."""
        return RSTParser()

    @pytest.fixture
    def fixtures_dir(self):
        """Get the fixtures directory path."""
        return Path(__file__).parent.parent / "fixtures"

    def test_parse_pep_metadata_success(self, parser, fixtures_dir):
        """Test successful parsing of a normal PEP file."""
        pep_file = fixtures_dir / "pep-0001.rst"
        metadata = parser.parse_pep_file(pep_file)

        assert metadata.pep_number == 1
        assert metadata.title == "PEP Purpose and Guidelines"
        assert metadata.status == "Active"
        assert metadata.type == "Process"
        assert metadata.created == "13-Jun-2000"
        assert len(metadata.authors) == 4
        assert "Barry Warsaw" in metadata.authors
        assert "Jeremy Hylton" in metadata.authors
        assert "David Goodger" in metadata.authors
        assert "Nick Coghlan" in metadata.authors

    def test_parse_pep_metadata_no_created(self, parser, fixtures_dir):
        """Test parsing PEP with empty Created field."""
        pep_file = fixtures_dir / "pep-0020.rst"
        metadata = parser.parse_pep_file(pep_file)

        assert metadata.pep_number == 20
        assert metadata.title == "The Zen of Python"
        assert metadata.status == "Active"
        assert metadata.type == "Informational"
        assert metadata.created is None or metadata.created == ""
        assert len(metadata.authors) == 1
        assert "Tim Peters" in metadata.authors

    def test_parse_pep_metadata_missing_fields(self, parser, fixtures_dir):
        """Test parsing PEP with missing required fields raises error."""
        pep_file = fixtures_dir / "pep-malformed.rst"

        with pytest.raises((ValueError, KeyError)):
            parser.parse_pep_file(pep_file)

    def test_parse_pep_number_from_filename(self, parser, fixtures_dir):
        """Test extracting PEP number from filename."""
        pep_file = fixtures_dir / "pep-0001.rst"
        pep_number = parser.extract_pep_number(pep_file)
        assert pep_number == 1

        pep_file = fixtures_dir / "pep-0008.rst"
        pep_number = parser.extract_pep_number(pep_file)
        assert pep_number == 8

        pep_file = fixtures_dir / "pep-9999.rst"
        pep_number = parser.extract_pep_number(pep_file)
        assert pep_number == 9999

    def test_parse_pep_number_from_filename_invalid(self, parser, fixtures_dir):
        """Test extracting PEP number from invalid filename raises error."""
        invalid_file = fixtures_dir / "invalid-name.rst"

        with pytest.raises((ValueError, IndexError)):
            parser.extract_pep_number(invalid_file)

    def test_parse_multiple_authors(self, parser, fixtures_dir):
        """Test parsing PEP with multiple authors."""
        pep_file = fixtures_dir / "pep-0008.rst"
        metadata = parser.parse_pep_file(pep_file)

        assert len(metadata.authors) == 3
        assert "Guido van Rossum" in metadata.authors
        assert "Barry Warsaw" in metadata.authors
        assert "Alyssa Coghlan" in metadata.authors

    def test_parse_single_author(self, parser, fixtures_dir):
        """Test parsing PEP with single author."""
        pep_file = fixtures_dir / "pep-9999.rst"
        metadata = parser.parse_pep_file(pep_file)

        assert len(metadata.authors) == 1
        assert "Test Author" in metadata.authors

    def test_parse_all_peps(self, parser, fixtures_dir):
        """Test parsing multiple PEP files at once."""
        pep_files = [
            fixtures_dir / "pep-0001.rst",
            fixtures_dir / "pep-0008.rst",
            fixtures_dir / "pep-9999.rst",
        ]

        results = parser.parse_multiple_peps(pep_files)

        assert len(results) == 3
        pep_numbers = {metadata.pep_number for metadata in results}
        assert pep_numbers == {1, 8, 9999}

    def test_parse_all_peps_with_errors(self, parser, fixtures_dir):
        """Test parsing multiple PEPs skips malformed files and continues."""
        pep_files = [
            fixtures_dir / "pep-0001.rst",
            fixtures_dir / "pep-malformed.rst",  # This should be skipped
            fixtures_dir / "pep-0008.rst",
        ]

        results = parser.parse_multiple_peps(pep_files)

        # Should successfully parse 2 out of 3 files
        assert len(results) == 2
        pep_numbers = {metadata.pep_number for metadata in results}
        assert pep_numbers == {1, 8}

    def test_parse_header_field(self, parser):
        """Test extracting specific header field from content."""
        content = """PEP: 1
Title: Test PEP
Author: Test Author
Status: Draft
Type: Process
Created: 01-Jan-2020

Content here
"""
        # Test extracting different fields
        title = parser.parse_header_field(content, "Title")
        assert title == "Test PEP"

        status = parser.parse_header_field(content, "Status")
        assert status == "Draft"

        author = parser.parse_header_field(content, "Author")
        assert author == "Test Author"

    def test_parse_header_field_not_found(self, parser):
        """Test parsing header field that doesn't exist returns None."""
        content = """PEP: 1
Title: Test PEP

Content here
"""
        result = parser.parse_header_field(content, "NonExistent")
        assert result is None

    def test_parse_header_field_multiline(self, parser):
        """Test parsing header field that spans multiple lines."""
        content = """PEP: 1
Title: Test PEP
Author: First Author,
        Second Author,
        Third Author
Status: Draft

Content here
"""
        author = parser.parse_header_field(content, "Author")
        assert "First Author" in author
        assert "Second Author" in author
        assert "Third Author" in author

    def test_pep_metadata_dataclass(self):
        """Test PEPMetadata dataclass creation."""
        metadata = PEPMetadata(
            pep_number=1,
            title="Test PEP",
            status="Draft",
            type="Process",
            created="01-Jan-2020",
            authors=["Author One", "Author Two"],
        )

        assert metadata.pep_number == 1
        assert metadata.title == "Test PEP"
        assert metadata.status == "Draft"
        assert metadata.type == "Process"
        assert metadata.created == "01-Jan-2020"
        assert metadata.authors == ["Author One", "Author Two"]

    def test_pep_metadata_with_empty_created(self):
        """Test PEPMetadata with empty created date."""
        metadata = PEPMetadata(
            pep_number=20,
            title="Test PEP",
            status="Active",
            type="Informational",
            created=None,
            authors=["Author"],
        )

        assert metadata.created is None

    def test_parse_draft_status(self, parser, fixtures_dir):
        """Test parsing PEP with Draft status."""
        pep_file = fixtures_dir / "pep-9999.rst"
        metadata = parser.parse_pep_file(pep_file)

        assert metadata.status == "Draft"
        assert metadata.type == "Standards Track"
