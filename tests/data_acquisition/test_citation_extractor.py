"""Tests for citation extractor module."""

from pathlib import Path

import pytest

from src.data_acquisition.citation_extractor import CitationExtractor
from src.data_acquisition.rst_parser import RSTParser


class TestCitationExtractor:
    """Test cases for CitationExtractor class."""

    @pytest.fixture
    def extractor(self):
        """Create a CitationExtractor instance for testing."""
        return CitationExtractor()

    @pytest.fixture
    def parser(self):
        """Create an RSTParser instance for testing."""
        return RSTParser()

    @pytest.fixture
    def fixtures_dir(self):
        """Get the fixtures directory path."""
        return Path(__file__).parent.parent / "fixtures"

    # Phase 2: Basic citation extraction - :pep: pattern tests (Red)

    def test_extract_single_pep_role_citation(self, extractor):
        """Test extracting a single :pep: citation."""
        content = "See :pep:`8` for details."
        result = extractor.extract_citations(content)
        assert result == [8]

    def test_extract_multiple_pep_role_citations(self, extractor):
        """Test extracting multiple :pep: citations."""
        content = "See :pep:`8` and :pep:`257`."
        result = extractor.extract_citations(content)
        assert result == [8, 257]

    def test_extract_no_citations(self, extractor):
        """Test extracting from content with no citations."""
        content = "This is a PEP without any citations."
        result = extractor.extract_citations(content)
        assert result == []

    # Phase 3: Additional citation patterns - Custom text PEP role tests (Red)

    def test_extract_pep_role_with_custom_text(self, extractor):
        """Test extracting :pep: citation with custom text."""
        content = ":pep:`the style guide <8>` for details."
        result = extractor.extract_citations(content)
        assert result == [8]

    def test_extract_pep_role_with_anchor(self, extractor):
        """Test extracting :pep: citation with custom text and anchor."""
        content = ":pep:`PEP 1 <1#discussing-a-pep>` section"
        result = extractor.extract_citations(content)
        assert result == [1]

    def test_extract_multiple_custom_pep_roles(self, extractor):
        """Test extracting multiple :pep: citations with custom text."""
        content = ":pep:`style <8>` and :pep:`Type Hints <484>`"
        result = extractor.extract_citations(content)
        assert result == [8, 484]

    # Phase 3: Additional citation patterns - PEP NNN plain text tests (Red)

    def test_extract_pep_number_format(self, extractor):
        """Test extracting PEP citation in 'PEP NNN' format."""
        content = "See PEP 8 for guidelines."
        result = extractor.extract_citations(content)
        assert result == [8]

    def test_extract_pep_case_insensitive(self, extractor):
        """Test extracting PEP citation with case-insensitive matching."""
        content = "See pep 8 for guidelines."
        result = extractor.extract_citations(content)
        assert result == [8]

    def test_extract_mixed_pep_role_and_plain_text(self, extractor):
        """Test that plain text PEP citations are extracted but not from within :pep: roles."""
        content = "See :pep:`style guide <8>` and PEP 8 for details."
        result = extractor.extract_citations(content)
        assert result == [8, 8]
