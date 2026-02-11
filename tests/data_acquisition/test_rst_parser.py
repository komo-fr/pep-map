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

    def test_parse_pep_number_from_metadata(self, parser, fixtures_dir):
        """Test extracting PEP number from document metadata (PEP: field)."""
        pep_file = fixtures_dir / "pep-0001.rst"
        content = pep_file.read_text(encoding="utf-8")
        pep_number = parser.extract_pep_number(content)
        assert pep_number == 1

        pep_file = fixtures_dir / "pep-0008.rst"
        content = pep_file.read_text(encoding="utf-8")
        pep_number = parser.extract_pep_number(content)
        assert pep_number == 8

        pep_file = fixtures_dir / "pep-9999.rst"
        content = pep_file.read_text(encoding="utf-8")
        pep_number = parser.extract_pep_number(content)
        assert pep_number == 9999

    def test_parse_pep_number_from_metadata_missing(self, parser):
        """Test extracting PEP number when PEP: field is missing raises error."""
        content = "Title: Some PEP\nAuthor: Someone\nStatus: Draft\n"
        with pytest.raises(ValueError, match="Missing or empty"):
            parser.extract_pep_number(content)

    def test_parse_pep_number_from_metadata_invalid(self, parser):
        """Test extracting PEP number when PEP: value is not a number raises error."""
        content = "PEP: not-a-number\nTitle: Test\nAuthor: X\nStatus: Draft\n"
        with pytest.raises(ValueError, match="Could not parse PEP number"):
            parser.extract_pep_number(content)

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

    def test_parse_topic_single(self, parser, fixtures_dir):
        """Test parsing PEP with single topic."""
        pep_file = fixtures_dir / "pep-with-topic-single.rst"
        metadata = parser.parse_pep_file(pep_file)

        assert metadata.topic is not None
        assert len(metadata.topic) == 1
        assert "Governance" in metadata.topic

    def test_parse_topic_multiple(self, parser, fixtures_dir):
        """Test parsing PEP with multiple topics."""
        pep_file = fixtures_dir / "pep-with-topic-multiple.rst"
        metadata = parser.parse_pep_file(pep_file)

        assert metadata.topic is not None
        assert len(metadata.topic) == 2
        assert "Governance" in metadata.topic
        assert "Packaging" in metadata.topic

    def test_parse_topic_not_present(self, parser, fixtures_dir):
        """Test parsing PEP without Topic field returns None."""
        pep_file = fixtures_dir / "pep-0001.rst"
        metadata = parser.parse_pep_file(pep_file)

        # Topicフィールドがない場合はNoneが返される
        assert metadata.topic is None

    def test_parse_topics_method(self, parser):
        """Test _parse_topics method parses topic string correctly."""
        # 単一トピック
        topics = parser._parse_topics("Governance")
        assert topics == ["Governance"]

        # 複数トピック（カンマとスペース区切り）
        topics = parser._parse_topics("Governance, Packaging")
        assert topics == ["Governance", "Packaging"]

        # 複数トピック（前後に余分なスペースがある場合）
        topics = parser._parse_topics("  Governance  ,  Typing  ")
        assert topics == ["Governance", "Typing"]

        # 空文字列
        topics = parser._parse_topics("")
        assert topics == []

    def test_pep_metadata_with_topic(self):
        """Test PEPMetadata dataclass with topic field."""
        metadata = PEPMetadata(
            pep_number=8001,
            title="Test PEP",
            status="Draft",
            type="Process",
            created="01-Jan-2020",
            authors=["Test Author"],
            topic=["Governance", "Packaging"],
        )

        assert metadata.topic == ["Governance", "Packaging"]

    def test_pep_metadata_without_topic(self):
        """Test PEPMetadata dataclass without topic field."""
        metadata = PEPMetadata(
            pep_number=1,
            title="Test PEP",
            status="Draft",
            type="Process",
            created="01-Jan-2020",
            authors=["Test Author"],
            topic=None,
        )

        assert metadata.topic is None
