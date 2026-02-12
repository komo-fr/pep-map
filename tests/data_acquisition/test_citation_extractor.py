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
        content = "See :pep:`style guide <8>` and PEP 257 for details."
        result = extractor.extract_citations(content)
        assert result == [8, 257]

    # Phase 3: Additional citation patterns - URL PEP number tests (Red)

    def test_extract_pep_from_url(self, extractor):
        """Test extracting PEP citation from URL."""
        content = "See https://peps.python.org/pep-0257/ for details."
        result = extractor.extract_citations(content)
        assert result == [257]

        content = "See https://peps.python.org/pep-8001/ for details."
        result = extractor.extract_citations(content)
        assert result == [8001]

    def test_extract_pep_from_url_with_anchor(self, extractor):
        """Test extracting PEP citation from URL with anchor."""
        content = ".. _link: https://peps.python.org/pep-0445/#gil-free"
        result = extractor.extract_citations(content)
        assert result == [445]

    def test_extract_multiple_peps_from_urls(self, extractor):
        """Test extracting multiple PEP citations from URLs."""
        content = "See https://peps.python.org/pep-0008/ and https://peps.python.org/pep-0257/#specification for details."
        result = extractor.extract_citations(content)
        assert result == [8, 257]

    # Phase 3: Additional citation patterns - Requires field tests (Red)

    def test_extract_requires_single(self, extractor, parser):
        """Test extracting single PEP from Requires field."""
        content = """PEP: 1234
Title: Test PEP
Author: Test Author
Status: Draft
Type: Standards Track
Created: 01-Jan-2020
Requires: 532

Content here."""
        result = extractor.extract_requires_field(content, parser)
        assert result == [532]

    def test_extract_requires_multiple(self, extractor, parser):
        """Test extracting multiple PEPs from Requires field."""
        content = """PEP: 1234
Title: Test PEP
Author: Test Author
Status: Draft
Type: Standards Track
Created: 01-Jan-2020
Requires: 489, 573, 630

Content here."""
        result = extractor.extract_requires_field(content, parser)
        assert result == [489, 573, 630]

    def test_extract_requires_none(self, extractor, parser):
        """Test extracting from content without Requires field."""
        content = """PEP: 1234
Title: Test PEP
Author: Test Author
Status: Draft
Type: Standards Track
Created: 01-Jan-2020

Content here."""
        result = extractor.extract_requires_field(content, parser)
        assert result == []

    # Phase 3: Additional citation patterns - Replaces field tests (Red)

    def test_extract_replaces_single(self, extractor, parser):
        """Test extracting single PEP from Replaces field."""
        content = """PEP: 1234
Title: Test PEP
Author: Test Author
Status: Draft
Type: Standards Track
Created: 01-Jan-2020
Replaces: 123

Content here."""
        result = extractor.extract_replaces_field(content, parser)
        assert result == [123]

    def test_extract_replaces_multiple(self, extractor, parser):
        """Test extracting multiple PEPs from Replaces field."""
        content = """PEP: 1234
Title: Test PEP
Author: Test Author
Status: Draft
Type: Standards Track
Created: 01-Jan-2020
Replaces: 123, 456, 789

Content here."""
        result = extractor.extract_replaces_field(content, parser)
        assert result == [123, 456, 789]

    def test_extract_replaces_none(self, extractor, parser):
        """Test extracting from content without Replaces field."""
        content = """PEP: 1234
Title: Test PEP
Author: Test Author
Status: Draft
Type: Standards Track
Created: 01-Jan-2020

Content here."""
        result = extractor.extract_replaces_field(content, parser)
        assert result == []

    # Phase 4: File-based citation extraction tests (Red)

    def test_extract_from_file(self, extractor, parser, fixtures_dir):
        """Test extracting citations from a file."""
        file_path = fixtures_dir / "pep-with-citations.rst"
        result = extractor.extract_from_file(file_path, parser)

        # Expected citations from pep-with-citations.rst (PEP 9999):
        # - Requires: 489, 573
        # - Replaces: 123, 456
        # - Body citations: 8, 257, 20, 1, 3107, 484, 526, 445
        expected = {9999: [1, 8, 20, 123, 257, 445, 456, 484, 489, 526, 573, 3107]}

        assert 9999 in result
        # Compare as sorted lists to ignore order
        assert sorted(result[9999]) == sorted(expected[9999])

    def test_exclude_self_reference(self, extractor, parser, fixtures_dir):
        """Test that self-references are excluded from citations."""
        file_path = fixtures_dir / "pep-0008.rst"
        result = extractor.extract_from_file(file_path, parser)

        # PEP 8 should not cite itself even if "PEP 8" appears in the text
        assert 8 in result
        assert 8 not in result[8]
